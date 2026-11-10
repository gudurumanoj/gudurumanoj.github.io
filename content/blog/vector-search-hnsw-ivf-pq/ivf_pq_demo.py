"""Deterministic CPU teaching model of IVF, residual PQ, and exact recall.

Run: python3 ivf_pq_demo.py
Requires NumPy and Matplotlib. This is not a Faiss implementation or benchmark.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SEED = 17
N, D, NQ, K = 1800, 16, 100, 10
NLIST, NSUB, NCODE = 24, 4, 16
RNG = np.random.default_rng(SEED)


def sqdist(a, b):
    """Pairwise squared L2 distances, clipped for round-off."""
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    return np.maximum(0.0, ((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2))


def kmeans(x, count, rounds=18):
    """Small seeded Lloyd iteration; empty centers retain their previous value."""
    centers = x[RNG.choice(len(x), count, replace=False)].copy()
    for _ in range(rounds):
        labels = sqdist(x, centers).argmin(axis=1)
        for j in range(count):
            members = x[labels == j]
            if len(members):
                centers[j] = members.mean(axis=0)
    return centers


def topk(scores, k):
    # Stable ordering makes ties reproducible, at this toy scale.
    return np.argsort(scores, kind="stable")[:k]


# A mixture with correlated dimensions is a teaching dataset, not an embedding set.
population = RNG.normal(size=(9, D)) * 2
train = population[RNG.integers(0, len(population), 5000)] + RNG.normal(size=(5000, D)) * .7
x = population[RNG.integers(0, len(population), N)] + RNG.normal(size=(N, D)) * .7
queries = population[RNG.integers(0, len(population), NQ)] + RNG.normal(size=(NQ, D)) * .7

coarse = kmeans(train, NLIST)
train_assign = sqdist(train, coarse).argmin(axis=1)
assign = sqdist(x, coarse).argmin(axis=1)
train_residual = train - coarse[train_assign]
residual = x - coarse[assign]

# IVFADC: PQ learns and encodes residuals, not the original vectors.
width = D // NSUB
books = [kmeans(train_residual[:, m * width:(m + 1) * width], NCODE)
         for m in range(NSUB)]
codes = np.stack([
    sqdist(residual[:, m * width:(m + 1) * width], books[m]).argmin(axis=1)
    for m in range(NSUB)
], axis=1).astype(np.uint8)

truth = np.stack([topk(sqdist(q[None, :], x)[0], K) for q in queries])


def search(q, nprobe, compressed):
    cells = topk(sqdist(q[None, :], coarse)[0], nprobe)
    ids = np.flatnonzero(np.isin(assign, cells))
    if not len(ids):
        return np.array([], dtype=int), 0
    if compressed:
        # ADC: query remains full precision; one lookup table per probed cell.
        scores = np.empty(len(ids))
        for cell in cells:
            local = np.flatnonzero(assign[ids] == cell)
            if not len(local):
                continue
            qr = q - coarse[cell]
            tables = [sqdist(qr[None, m * width:(m + 1) * width], books[m])[0]
                      for m in range(NSUB)]
            scores[local] = sum(tables[m][codes[ids[local], m]] for m in range(NSUB))
    else:
        scores = sqdist(q[None, :], x[ids])[0]
    return ids[topk(scores, min(K, len(ids)))], len(ids)


probes = [1, 2, 4, 8, 16, NLIST]
curves = {}
for compressed in (False, True):
    label = "IVF + residual PQ" if compressed else "IVF + exact rerank"
    rows = []
    for p in probes:
        results = [search(q, p, compressed) for q in queries]
        recall = np.mean([len(set(found) & set(gold)) / K
                          for (found, _), gold in zip(results, truth)])
        candidates = np.mean([count for _, count in results])
        rows.append((recall, candidates))
        print(f"{label:20s} nprobe={p:2d} recall@{K}={recall:.3f} "
              f"candidates/query={candidates:.1f}")
    curves[label] = np.asarray(rows)

assert np.isclose(curves["IVF + exact rerank"][-1, 0], 1.0)
assert np.all(np.diff(curves["IVF + exact rerank"][:, 0]) >= -1e-12)
assert np.all(np.diff(curves["IVF + exact rerank"][:, 1]) >= -1e-12)

fig, ax = plt.subplots(figsize=(7.4, 4.3))
for label, values in curves.items():
    ax.plot(values[:, 1], values[:, 0], "o-", label=label)
    for p, (recall, candidates) in zip(probes, values):
        ax.annotate(str(p), (candidates, recall), xytext=(3, 4),
                    textcoords="offset points", fontsize=8)
ax.set(xlabel="Mean candidates scored per query", ylabel=f"Exact-set recall@{K}",
       ylim=(0, 1.06), title="Toy CPU IVF sweep (point labels are nprobe)")
ax.grid(alpha=.2)
ax.legend()
fig.tight_layout()
fig.savefig(Path(__file__).with_name("recall.svg"))
