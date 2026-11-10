"""Exact two-stratum causal example and a reproducible Monte Carlo check."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

P_X = np.array([0.5, 0.5])
Y0 = np.array([0.10, 0.60])
Y1 = Y0 + 0.10
E_OBS = np.array([0.90, 0.10])  # P(A=1 | X), observational assignment


def exact(e):
    """Return observable cell masses and identified contrasts when e has overlap."""
    mass1, mass0 = P_X * e, P_X * (1 - e)
    treated = np.sum(mass1 * Y1) / np.sum(mass1)
    control = np.sum(mass0 * Y0) / np.sum(mass0)
    standardized = np.sum(P_X * (Y1 - Y0))
    # Horvitz-Thompson population expectations; divisions need positivity.
    ipw1 = np.sum(mass1 * Y1 / e)
    ipw0 = np.sum(mass0 * Y0 / (1 - e))
    return treated, control, standardized, ipw1 - ipw0


print(f"True ATE: {np.sum(P_X * (Y1 - Y0)):+.2f}")
for label, propensity in [("Observational", E_OBS),
                          ("Randomized", np.array([0.5, 0.5]))]:
    t, c, std, ipw = exact(propensity)
    print(f"{label}: E[Y|A=1]={t:.2f}, E[Y|A=0]={c:.2f}, "
          f"crude={t-c:+.2f}, standardized={std:+.2f}, IPW={ipw:+.2f}")

rng = np.random.default_rng(20261110)
n = 200_000
x = rng.integers(0, 2, n)
a = rng.binomial(1, E_OBS[x])
y = rng.binomial(1, np.where(a == 1, Y1[x], Y0[x]))
crude = y[a == 1].mean() - y[a == 0].mean()
std = sum(P_X[k] * (y[(x == k) & (a == 1)].mean()
                    - y[(x == k) & (a == 0)].mean()) for k in (0, 1))
ipw_ht = np.mean(a * y / E_OBS[x] - (1 - a) * y / (1 - E_OBS[x]))
ipw_normalized = (np.sum(a * y / E_OBS[x]) / np.sum(a / E_OBS[x])
                  - np.sum((1-a) * y / (1-E_OBS[x])) / np.sum((1-a)/(1-E_OBS[x])))
print(f"Sample: crude={crude:+.3f}, standardized={std:+.3f}, "
      f"IPW-HT={ipw_ht:+.3f}, IPW-normalized={ipw_normalized:+.3f}")

fig, ax = plt.subplots(figsize=(8, 4.6))
labels = ["Low intent", "High intent", "All users\n(observed mix)",
          "All users\n(standardized)"]
treated, control, *_ = exact(E_OBS)
v0 = [Y0[0], Y0[1], control, np.dot(P_X, Y0)]
v1 = [Y1[0], Y1[1], treated, np.dot(P_X, Y1)]
pos = np.arange(4)
ax.bar(pos - .18, v0, .36, label="Control", color="#a66b4f")
ax.bar(pos + .18, v1, .36, label="Treated", color="#487c80")
ax.set_xticks(pos, labels)
ax.set_ylim(0, .82)
ax.set_ylabel("Probability of purchase")
ax.set_title("A positive effect in each stratum reverses in the observed mix")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(Path(__file__).with_name("simpson.svg"), format="svg")
