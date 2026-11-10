"""A deterministic control-plane toy, not a GPU or engine benchmark.

Run: python3 routing_demo.py
"""

from dataclasses import dataclass, field
import hashlib
import json


def block_keys(scope, token_chunks):
    """Make a prefix chain from an explicit compatibility scope and token IDs."""
    parent = hashlib.sha256(json.dumps(scope).encode()).digest()
    keys = []
    for chunk in token_chunks:
        payload = json.dumps(chunk, separators=(",", ":")).encode()
        parent = hashlib.sha256(parent + payload).digest()
        keys.append(parent.hex())
    return keys


def prefix_len(keys, held):
    matched = 0
    for key in keys:
        if key not in held:
            break
        matched += 1
    return matched


@dataclass
class Worker:
    name: str
    queue_ms: int
    actual: set[str] = field(default_factory=set)
    healthy: bool = True


@dataclass
class View:
    epoch: int = 0
    seq: int = 0
    known: bool = False
    advertised: set[str] = field(default_factory=set)


class Index:
    """An illustrative protocol; no cited project is claimed to implement it."""

    def __init__(self, names):
        self.views = {name: View() for name in names}

    def apply(self, name, epoch, seq, kind, keys=()):
        view = self.views[name]
        if epoch < view.epoch:
            return "old epoch ignored"
        if epoch > view.epoch:
            view.epoch, view.seq, view.known = epoch, 0, False
            view.advertised.clear()
        if kind == "snapshot":
            # A delayed snapshot must not roll a same-epoch view backward.
            # When the view is unknown, an equal-sequence snapshot can repair it.
            if seq < view.seq or (view.known and seq == view.seq):
                return "stale snapshot ignored"
            view.seq = seq
            view.advertised = set(keys)
            view.known = True
            return "snapshot installed"
        if seq <= view.seq:
            return "old sequence ignored"
        if not view.known:
            view.seq = seq  # Keep a high-water mark for snapshot recovery.
            return "unknown until snapshot"
        if seq != view.seq + 1:
            view.seq = seq
            view.known = False
            view.advertised.clear()
            return "sequence gap: view invalidated"
        view.seq = seq
        if kind == "store":
            view.advertised.update(keys)
        elif kind == "remove":
            view.advertised.difference_update(keys)
        elif kind == "clear":
            view.advertised.clear()
        else:
            raise ValueError(kind)
        return "event applied"

    def predicted_hits(self, name, keys):
        view = self.views[name]
        return prefix_len(keys, view.advertised) if view.known else 0


def choose(workers, index, keys, block_ms=4, restore_ms=None):
    """Score costs in invented milliseconds; a real router estimates these."""
    restore_ms = restore_ms or {}
    choices = []
    for worker in workers:
        if not worker.healthy:
            continue
        hits = index.predicted_hits(worker.name, keys)
        estimated = worker.queue_ms + (len(keys) - hits) * block_ms
        estimated += restore_ms.get(worker.name, 0)
        choices.append((estimated, worker.name, hits, worker))
    if not choices:
        raise RuntimeError("no healthy workers")
    estimated, _, advertised_hits, chosen = min(choices)
    # The worker, not the metadata index, decides what can really be reused.
    real_hits = prefix_len(keys, chosen.actual)
    actual_cost = chosen.queue_ms + (len(keys) - real_hits) * block_ms
    actual_cost += restore_ms.get(chosen.name, 0)
    return chosen.name, advertised_hits, real_hits, estimated, actual_cost


def main():
    scope = ("tenant-7", "model-v3", "tokenizer-v2", "base-adapter")
    chunks = [list(range(4 * i, 4 * i + 4)) for i in range(5)]
    keys = block_keys(scope, chunks)
    assert keys != block_keys(("tenant-7", "model-v4", "tokenizer-v2", "base-adapter"), chunks)
    assert prefix_len(keys, {keys[0], keys[1], keys[3]}) == 2

    hot = Worker("A", queue_ms=18, actual=set(keys[:3]))
    cold = Worker("B", queue_ms=2)
    workers = [hot, cold]
    index = Index([w.name for w in workers])
    assert index.apply("A", 1, 0, "snapshot", keys[:3]) == "snapshot installed"
    assert index.apply("B", 1, 0, "snapshot") == "snapshot installed"

    result = choose(workers, index, keys)
    assert result == ("B", 0, 0, 22, 22)
    print("Busy hot replica:", result)

    hot.queue_ms = 5
    result = choose(workers, index, keys)
    assert result == ("A", 3, 3, 13, 13)
    print("Quiet hot replica:", result)

    hot.actual.clear()  # Removal event has not reached this router.
    result = choose(workers, index, keys)
    assert result == ("A", 3, 0, 13, 25)
    print("Stale advertisement; worker misses safely:", result)

    message = index.apply("A", 1, 2, "remove", keys[:3])  # Expected seq=1.
    assert message == "sequence gap: view invalidated"
    assert index.predicted_hits("A", keys) == 0
    print("Gap handling:", message)
    assert index.apply("A", 1, 1, "snapshot", keys[:3]) == "stale snapshot ignored"
    assert index.apply("A", 1, 2, "snapshot") == "snapshot installed"
    assert index.predicted_hits("A", keys) == 0

    # Same-epoch delayed snapshots must not replace newer placement state.
    rewind = Index(["X"])
    assert rewind.apply("X", 1, 5, "snapshot", keys[:3]) == "snapshot installed"
    assert rewind.apply("X", 1, 2, "snapshot", keys[3:]) == "stale snapshot ignored"
    assert rewind.predicted_hits("X", keys) == 3
    print("Delayed same-epoch snapshot: ignored")

    assert index.apply("A", 2, 0, "snapshot") == "snapshot installed"
    assert index.apply("A", 1, 3, "store", keys[:3]) == "old epoch ignored"
    assert index.predicted_hits("A", keys) == 0
    print("Old event after reset: ignored")

    # An assignment reservation can guide a sibling request before any store
    # event, but it must not be counted as resident KV.
    reservation = {tuple(keys): "A"}
    assert reservation[tuple(keys)] == "A"
    assert index.predicted_hits("A", keys) == 0
    print("Reserved for A; advertised prefix blocks:", index.predicted_hits("A", keys))


if __name__ == "__main__":
    main()
