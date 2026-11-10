"""Compare three multiplicity rules on illustrative p-values."""

import numpy as np
from scipy import stats


p = np.array([0.004, 0.012, 0.018, 0.04, 0.2])
alpha = 0.05
m = len(p)
order = np.argsort(p)
ranked = p[order]

bonferroni = p <= alpha / m

holm_ranked = np.zeros(m, dtype=bool)
for i, value in enumerate(ranked):
    if value > alpha / (m - i):
        break  # Holm stops at the first failure.
    holm_ranked[i] = True
holm = np.zeros(m, dtype=bool)
holm[order] = holm_ranked

bh_pass = ranked <= alpha * np.arange(1, m + 1) / m
k = np.flatnonzero(bh_pass)
bh_ranked = np.arange(m) < (k[-1] + 1 if len(k) else 0)
bh = np.zeros(m, dtype=bool)
bh[order] = bh_ranked

# SciPy's adjusted BH p-values independently check our step-up decisions.
bh_adjusted = stats.false_discovery_control(p, method="bh")
assert np.array_equal(bh, bh_adjusted <= alpha)

for name, decisions in (
    ("Bonferroni", bonferroni),
    ("Holm", holm),
    ("BH", bh),
):
    print(f"{name}: hypotheses {(np.flatnonzero(decisions) + 1).tolist()}")
print(f"SciPy BH agrees: {np.array_equal(bh, bh_adjusted <= alpha)}")
