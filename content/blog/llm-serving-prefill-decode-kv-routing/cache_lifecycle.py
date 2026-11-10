"""Tiny local prefix-cache model; no GPU, network, or engine dependencies.

Run: python3 cache_lifecycle.py
The four-token block size and two-block capacity are teaching choices, not
vLLM or SGLang defaults. Requests are processed sequentially except for one
deliberate allocation failure while A is active.
"""

from dataclasses import dataclass, field


BLOCK_SIZE = 4


class OutOfBlocks(RuntimeError):
    pass


@dataclass
class Block:
    block_id: int
    tokens: list[int] = field(default_factory=list)
    key: tuple | None = None  # Set only when the block becomes full.
    pins: int = 0
    last_use: int = 0


@dataclass
class Request:
    scope: str
    parent: tuple
    blocks: list[int] = field(default_factory=list)
    hit_tokens: int = 0
    tail_id: int | None = None


class LocalBlockCache:
    def __init__(self, capacity: int):
        self.blocks = [Block(i) for i in range(capacity)]
        self.index: dict[tuple, int] = {}
        self.clock = 0

    def _touch(self, block: Block) -> None:
        self.clock += 1
        block.last_use = self.clock

    def open(self, token_ids: list[int], scope: str) -> Request:
        """Pin consecutive completed blocks matching this exact context."""
        req = Request(scope=scope, parent=(scope,))
        for start in range(0, len(token_ids), BLOCK_SIZE):
            chunk = tuple(token_ids[start : start + BLOCK_SIZE])
            if len(chunk) != BLOCK_SIZE:
                break
            key = (req.parent, chunk)
            block_id = self.index.get(key)
            if block_id is None:
                break
            block = self.blocks[block_id]
            assert block.key == key and len(block.tokens) == BLOCK_SIZE
            block.pins += 1
            self._touch(block)
            req.blocks.append(block_id)
            req.parent = key
            req.hit_tokens += BLOCK_SIZE
        return req

    def _allocate(self) -> Block:
        free = next((b for b in self.blocks if b.pins == 0 and not b.tokens), None)
        if free is None:
            candidates = [b for b in self.blocks if b.pins == 0 and b.key is not None]
            if not candidates:
                raise OutOfBlocks("all physical blocks are pinned")
            free = min(candidates, key=lambda b: b.last_use)
            del self.index[free.key]
            free.tokens.clear()
            free.key = None
        free.pins = 1
        self._touch(free)
        return free

    def append(self, req: Request, new_tokens: list[int]) -> None:
        """Compute and append uncached tokens; never mutate an indexed block."""
        for token in new_tokens:
            if req.tail_id is None:
                block = self._allocate()
                req.blocks.append(block.block_id)
                req.tail_id = block.block_id
            block = self.blocks[req.tail_id]
            assert block.pins == 1 and block.key is None
            block.tokens.append(token)
            if len(block.tokens) == BLOCK_SIZE:
                key = (req.parent, tuple(block.tokens))
                assert key not in self.index  # This toy omits concurrent duplicate fills.
                block.key = key
                self.index[key] = block.block_id
                req.parent = key
                req.tail_id = None

    def close(self, req: Request) -> None:
        for block_id in req.blocks:
            block = self.blocks[block_id]
            assert block.pins > 0
            block.pins -= 1
            if block.pins == 0 and block.key is None:
                block.tokens.clear()  # Drop an incomplete, non-shareable tail.


def main() -> None:
    cache = LocalBlockCache(capacity=2)
    scope = "weights-v1/tokenizer-v1/tenant-A"
    a = [10, 11, 12, 13, 20, 21, 22]
    b = [10, 11, 12, 13, 20, 21, 99, 30]

    request_a = cache.open(a, scope)
    cache.append(request_a, a[request_a.hit_tokens :])
    assert request_a.hit_tokens == 0
    assert len(cache.index) == 1 and cache.blocks[request_a.tail_id].tokens == [20, 21, 22]
    print("A: computed 7 tokens; 4 indexed, 3 in a mutable tail")

    unrelated = cache.open([90, 91, 92, 93], scope)
    try:
        cache.append(unrelated, [90, 91, 92, 93])
    except OutOfBlocks:
        print("While A is active: allocation refused; both blocks are pinned")
    else:
        raise AssertionError("a pinned block was overwritten")
    cache.close(unrelated)
    assert all(cache.blocks[i].pins == 1 for i in request_a.blocks)

    cache.close(request_a)
    assert len(cache.index) == 1 and sum(bool(x.tokens) for x in cache.blocks) == 1
    request_b = cache.open(b, scope)
    assert request_b.hit_tokens == 4  # Token-level common prefix is 6, but only 4 are indexed.
    cache.append(request_b, b[request_b.hit_tokens :])
    print("B: 6-token common prefix, 4-token block hit, 4 tokens recomputed")
    cache.close(request_b)

    request_c = cache.open(b + [40], scope)
    assert request_c.hit_tokens == 8
    try:
        cache.append(request_c, [40])
    except OutOfBlocks:
        print("C: 8-token hit, but no free block for the next token")
    else:
        raise AssertionError("a pinned cached block was overwritten")
    cache.close(request_c)

    isolated = cache.open(b, "weights-v1/tokenizer-v1/tenant-B")
    assert isolated.hit_tokens == 0
    print("Same tokens, different cache scope: 0-token hit")
    cache.close(isolated)
    assert all(block.pins == 0 for block in cache.blocks)

    previous_keys = set(cache.index)
    replacement_tokens = [90, 91, 92, 93]
    replacement = cache.open(replacement_tokens, scope)
    cache.append(replacement, replacement_tokens)
    assert len(cache.index) == 2 and len(previous_keys & set(cache.index)) == 1
    print("After release: one unpinned cached block is evicted and reused")
    cache.close(replacement)

    # The same second block's IDs after a different first block are not shared.
    context_cache = LocalBlockCache(capacity=4)
    first = [1, 2, 3, 4, 5, 6, 7, 8]
    second = [9, 2, 3, 4, 5, 6, 7, 8]
    r1 = context_cache.open(first, scope)
    context_cache.append(r1, first)
    first_last_key = r1.parent
    context_cache.close(r1)
    r2 = context_cache.open(second, scope)
    assert r2.hit_tokens == 0
    context_cache.append(r2, second)
    assert first_last_key != r2.parent
    assert first_last_key[1] == r2.parent[1] == (5, 6, 7, 8)
    print("Same second-block tokens after different parents: distinct keys")
    context_cache.close(r2)


if __name__ == "__main__":
    main()
