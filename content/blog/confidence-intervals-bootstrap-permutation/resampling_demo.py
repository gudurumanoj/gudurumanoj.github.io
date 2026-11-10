"""Intervals and two resampling distributions; requires NumPy, SciPy, Matplotlib."""

from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


a = np.array([12, 11, 13, 12, 14, 10, 13, 15], dtype=float)
b = np.array([10, 11, 12, 10, 9, 13, 8, 12, 11, 13, 9, 11], dtype=float)
observed = a.mean() - b.mean()

# Model-based Welch 95% interval for independent population means.
va, vb = a.var(ddof=1), b.var(ddof=1)
ua, ub = va / len(a), vb / len(b)
se = np.sqrt(ua + ub)
df = (ua + ub) ** 2 / (ua**2 / (len(a) - 1) + ub**2 / (len(b) - 1))
critical = stats.t.ppf(0.975, df)
welch_ci = (observed - critical * se, observed + critical * se)
assert np.allclose(welch_ci, stats.ttest_ind(a, b, equal_var=False).confidence_interval())

# Paired units: the independent units are differences, not columns.
before = np.array([14, 12, 18, 11, 17, 15], dtype=float)
after = np.array([12, 9, 18, 7, 16, 10], dtype=float)
differences = before - after
paired_se = differences.std(ddof=1) / np.sqrt(len(differences))
paired_margin = stats.t.ppf(0.975, len(differences) - 1) * paired_se
paired_ci = (differences.mean() - paired_margin, differences.mean() + paired_margin)

# Bootstrap: resample within each original group, with replacement.
B = 20000
rng = np.random.default_rng(2026)
ia = rng.integers(len(a), size=(B, len(a)))
ib = rng.integers(len(b), size=(B, len(b)))
boot = a[ia].mean(axis=1) - b[ib].mean(axis=1)
percentile_ci = tuple(np.quantile(boot, [0.025, 0.975]))

# Permutation: shuffle labels without replacement under exchangeability.
M = 9999
pool = np.concatenate([a, b])
permuted = np.empty(M)
for i in range(M):
    shuffled = rng.permutation(pool)
    permuted[i] = shuffled[: len(a)].mean() - shuffled[len(a) :].mean()
extreme = np.count_nonzero(np.abs(permuted) >= abs(observed) - 1e-12)
mc_p = (extreme + 1) / (M + 1)  # include the observed arrangement
assert 0 < mc_p <= 1

# Exhaustive small example: 20 equally likely assignments, two extreme.
toy = np.array([7, 8, 9, 1, 2, 3], dtype=float)
toy_observed = toy[:3].mean() - toy[3:].mean()
toy_null = []
for selected in combinations(range(6), 3):
    mask = np.zeros(6, dtype=bool)
    mask[list(selected)] = True
    toy_null.append(toy[mask].mean() - toy[~mask].mean())
toy_null = np.array(toy_null)
toy_extreme = np.count_nonzero(np.abs(toy_null) >= abs(toy_observed) - 1e-12)
exact_p = toy_extreme / len(toy_null)
assert (len(toy_null), toy_extreme, exact_p) == (20, 2, 0.1)

print(f"difference = {observed:.4f}")
print(f"Welch 95% CI = ({welch_ci[0]:.4f}, {welch_ci[1]:.4f})")
print(f"paired mean difference = {differences.mean():.4f}")
print(f"paired t 95% CI = ({paired_ci[0]:.4f}, {paired_ci[1]:.4f})")
print(f"bootstrap percentile 95% CI = ({percentile_ci[0]:.4f}, {percentile_ci[1]:.4f})")
print(f"permutation extremes = {extreme} / {M}; Monte Carlo p = {mc_p:.4f}")
print(f"toy exact p = {toy_extreme} / {len(toy_null)} = {exact_p:.3f}")

plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})
fig, axes = plt.subplots(1, 2, figsize=(10.8, 3.7), constrained_layout=True)
fig.patch.set_facecolor("#fdfcf8")
for ax in axes:
    ax.set_facecolor("#fdfcf8")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlabel("mean difference (A − B)")
    ax.set_ylabel("resamples")

axes[0].hist(boot, bins=38, color="#a66b4f", alpha=0.85)
axes[0].axvline(observed, color="#2d2a23", lw=1.5, label="observed estimate")
for edge in percentile_ci:
    axes[0].axvline(edge, color="#6d4831", ls="--", lw=1.4)
axes[0].set_title("Bootstrap: uncertainty around estimate")
axes[0].legend(frameon=False, loc="upper left", fontsize=8)

axes[1].hist(permuted, bins=38, color="#356b84", alpha=0.85)
axes[1].axvline(observed, color="#2d2a23", lw=1.5, label="observed statistic")
axes[1].axvline(-observed, color="#2d2a23", lw=1.5, ls="--", label="opposite tail")
axes[1].set_title("Permutation: null with reassigned labels")
axes[1].legend(frameon=False, loc="upper left", fontsize=8)

destination = Path(__file__).with_name("resampling-distributions.svg")
fig.savefig(destination, format="svg")
plt.close(fig)
