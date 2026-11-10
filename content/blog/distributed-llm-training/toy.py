"""CPU-only arithmetic checks for the companion distributed-training post.

Run: python3 toy.py
No torch, GPU, network, or third-party package is required.
"""

from math import isclose


def gradient(samples):
    # d/dw of mean((w*x-y)^2/2), at w=1.
    return sum((x - y) * x for x, y in samples) / len(samples)


def gib(nbytes):
    return nbytes / 1024**3


def state_bytes(parameters, ranks, shard_stage):
    # Explicit 2B weights, 2B gradients, 4B master weights, 8B Adam moments.
    divisor = lambda stage: ranks if shard_stage >= stage else 1
    return parameters * (2 / divisor(3) + 2 / divisor(2) + 12 / divisor(1))


def ring_allreduce(rows, pad=True):
    """Synchronous four-rank arithmetic trace, not an NCCL performance model."""
    ranks, count = len(rows), len(rows[0])
    assert ranks == 4 and all(len(row) == count for row in rows)
    chunk = (count + ranks - 1) // ranks
    padded = [row + [0] * (ranks * chunk - count) if pad else row[:] for row in rows]
    sizes = [chunk] * ranks if pad else [count // ranks + (i < count % ranks) for i in range(ranks)]
    offsets = [sum(sizes[:i]) for i in range(ranks)]
    pieces = [[row[offsets[i]:offsets[i] + sizes[i]] for i in range(ranks)] for row in padded]
    messages = []
    for step in range(ranks - 1):  # reduce-scatter
        sent = [(rank - step) % ranks for rank in range(ranks)]
        before = [[piece[:] for piece in rank_pieces] for rank_pieces in pieces]
        for rank in range(ranks):
            source = (rank - 1) % ranks
            idx = sent[source]
            pieces[rank][idx] = [a + b for a, b in zip(before[rank][idx], before[source][idx])]
        messages.append(f"RS{step + 1}: " + " ".join(f"{r}->{(r + 1) % ranks}:c{sent[r]}" for r in range(ranks)))
    # Rank r now owns reduced chunk (r+1) mod R.
    for rank in range(ranks):
        idx = (rank + 1) % ranks
        expected = [sum(padded[r][offsets[idx] + j] for r in range(ranks)) for j in range(sizes[idx])]
        assert pieces[rank][idx] == expected
    for step in range(ranks - 1):  # all-gather
        sent = [(rank + 1 - step) % ranks for rank in range(ranks)]
        before = [[piece[:] for piece in rank_pieces] for rank_pieces in pieces]
        for rank in range(ranks):
            source = (rank - 1) % ranks
            idx = sent[source]
            pieces[rank][idx] = before[source][idx][:]
        messages.append(f"AG{step + 1}: " + " ".join(f"{r}->{(r + 1) % ranks}:c{sent[r]}" for r in range(ranks)))
    expected = [sum(row[j] for row in rows) for j in range(count)]
    assert all([value for part in rank_pieces for value in part][:count] == expected for rank_pieces in pieces)
    return messages, expected, sizes


def main():
    a = [(1, 0), (2, 0)]
    b = [(3, 0)]
    global_gradient = gradient(a + b)
    wrong_rank_mean = (gradient(a) + gradient(b)) / 2
    weighted_rank_mean = (len(a) * gradient(a) + len(b) * gradient(b)) / (len(a) + len(b))
    assert isclose(global_gradient, weighted_rank_mean)
    assert not isclose(global_gradient, wrong_rank_mean)
    print(f"global={global_gradient:.6f} rank_mean={wrong_rank_mean:.6f} weighted={weighted_rank_mean:.6f}")

    n, ranks = 7_000_000_000, 8
    for stage in range(4):
        print(f"stage{stage} state={gib(state_bytes(n, ranks, stage)):.2f} GiB/rank")
    # fp16/bf16 parameter payload, idealized ring volumes per rank, per step.
    payload = 2 * n
    allreduce = 2 * (ranks - 1) / ranks * payload
    print(f"one full-gradient ring allreduce={gib(allreduce):.2f} GiB/rank")
    print(f"one allgather+reduce-scatter={gib(allreduce):.2f} GiB/rank")
    assert state_bytes(n, ranks, 3) < state_bytes(n, ranks, 2)

    rows = [[10 * rank + j for j in range(10)] for rank in range(4)]
    trace, result, sizes = ring_allreduce(rows)
    assert result == [60 + 4 * j for j in range(10)]
    print(f"ring simulator: 4 ranks x 10 values, padded to {sum(sizes)}; sum={result}")
    for line in trace:
        print(line)
    _, uneven_result, uneven_sizes = ring_allreduce(rows, pad=False)
    assert uneven_result == result and uneven_sizes == [3, 3, 2, 2]
    print(f"un-padded uneven chunks {uneven_sizes}: same sum, unequal per-rank byte volume")


if __name__ == "__main__":
    main()
