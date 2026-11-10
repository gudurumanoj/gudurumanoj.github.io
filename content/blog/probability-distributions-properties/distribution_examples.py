"""Analytic distribution comparisons used in the accompanying post.

Run: python3 distribution_examples.py
Requires NumPy, SciPy, and Matplotlib. No sampled data are used.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binom, expon, gamma, norm, poisson, t


def main() -> None:
    output = Path(__file__).resolve().parent
    k = np.arange(0, 13)
    x = np.linspace(0, 3.5, 401)
    z = np.linspace(-4, 4, 401)

    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.7), layout="constrained")
    fig.patch.set_facecolor("#fdfcf8")
    for ax in axes:
        ax.set_facecolor("#fdfcf8")
        ax.spines[["top", "right"]].set_visible(False)

    axes[0].bar(k - 0.18, binom.pmf(k, 12, 0.25), width=0.36,
                color="#a66b4f", label="Binomial(12, .25)")
    axes[0].bar(k + 0.18, poisson.pmf(k, 3), width=0.36,
                color="#417e82", alpha=0.85, label="Poisson(3)")
    axes[0].set(title="Counts: same mean, different spread", xlabel="count k", ylabel="probability mass")
    axes[0].legend(frameon=False, fontsize=8)

    axes[1].plot(x, expon.pdf(x, scale=1), color="#a66b4f", lw=2,
                 label="Exponential(rate 1)")
    axes[1].plot(x, gamma.pdf(x, a=3, scale=1 / 3), color="#417e82", lw=2,
                 label="Gamma(shape 3, rate 3)")
    axes[1].set(title="Waits: same mean, different shape", xlabel="time", ylabel="density")
    axes[1].legend(frameon=False, fontsize=8)

    axes[2].plot(z, norm.pdf(z), color="#a66b4f", lw=2, label="Normal(0, 1)")
    axes[2].plot(z, t.pdf(z, df=3), color="#417e82", lw=2, label="Student t(3)")
    axes[2].set(title="Tails: t(3) is heavier", xlabel="value", ylabel="density")
    axes[2].legend(frameon=False, fontsize=8)

    fig.savefig(output / "distribution-comparison.svg", bbox_inches="tight")
    fig.savefig(output / "distribution-comparison-preview.png", dpi=160,
                bbox_inches="tight")
    plt.close(fig)

    print(f"Binomial mean={binom.mean(12, .25):.3f}, variance={binom.var(12, .25):.3f}")
    print(f"Poisson mean={poisson.mean(3):.3f}, variance={poisson.var(3):.3f}")
    print(f"P(count >= 5): Binomial={binom.sf(4, 12, .25):.6f}, Poisson={poisson.sf(4, 3):.6f}")
    print(f"Exponential mean={expon.mean(scale=1):.3f}, variance={expon.var(scale=1):.3f}")
    print(f"Gamma mean={gamma.mean(a=3, scale=1/3):.3f}, variance={gamma.var(a=3, scale=1/3):.3f}")
    conditional = expon.sf(3, scale=1) / expon.sf(2, scale=1)
    print(f"P(T > 3 | T > 2)={conditional:.6f}; P(T > 1)={expon.sf(1, scale=1):.6f}")
    print(f"P(|X| > 3): Normal={2*norm.sf(3):.6f}, t(3)={2*t.sf(3, df=3):.6f}")
    sigma = 0.5
    lognormal_mean = np.exp(sigma**2 / 2)
    lognormal_var = (np.exp(sigma**2) - 1) * np.exp(sigma**2)
    print(f"Lognormal(mu=0, sigma=.5) mean={lognormal_mean:.6f}, variance={lognormal_var:.6f}")


if __name__ == "__main__":
    main()
