"""Check Gaussian conditioning and draw probability ellipses; writes SVG."""

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import chi2, multivariate_normal, norm


def conditional(mean, cov, observed_index, observed_value):
    """Condition a 2D nonsingular Gaussian on its other scalar coordinate."""
    target_index = 1 - observed_index
    gain = cov[target_index, observed_index] / cov[observed_index, observed_index]
    location = mean[target_index] + gain * (observed_value - mean[observed_index])
    variance = cov[target_index, target_index] - gain * cov[observed_index, target_index]
    return location, variance


def main():
    mean = np.array([1.0, -1.0])
    cov = np.array([[4.0, 1.2], [1.2, 1.0]])
    chol = np.linalg.cholesky(cov)
    assert np.all(np.linalg.eigvalsh(cov) > 0)
    observed_b = 0.0
    cond_mean, cond_var = conditional(mean, cov, 1, observed_b)
    assert np.isclose(cond_mean, 2.2) and np.isclose(cond_var, 2.56)

    point = np.array([cond_mean, observed_b])
    delta = point - mean
    whitened = np.linalg.solve(chol, delta)
    mahal_sq = whitened @ whitened
    logdet = 2 * np.log(np.diag(chol)).sum()
    logpdf = -0.5 * (2 * np.log(2 * np.pi) + logdet + mahal_sq)
    reference_logpdf = multivariate_normal(mean, cov).logpdf(point)
    assert np.isclose(logpdf, reference_logpdf)

    # p(A=a | B=b) = p(A=a,B=b) / p(B=b), checked at the conditional mode.
    ratio = np.exp(reference_logpdf - norm.logpdf(observed_b, mean[1], np.sqrt(cov[1, 1])))
    conditional_density = norm.pdf(cond_mean, cond_mean, np.sqrt(cond_var))
    assert np.isclose(ratio, conditional_density)

    rng = np.random.default_rng(20261110)
    samples = rng.normal(size=(100_000, 2)) @ chol.T + mean
    empirical_mean = samples.mean(axis=0)
    empirical_cov = np.cov(samples, rowvar=False)
    assert np.max(np.abs(empirical_cov - cov)) < 0.03

    # X1=X2+e1, X3=X2+e3: X1 and X3 correlate marginally but are
    # independent given X2; the (1,3) entry of precision is zero.
    chain_cov = np.array([[2., 1., 1.], [1., 1., 1.], [1., 1., 2.]])
    chain_precision = np.linalg.solve(chain_cov, np.eye(3))
    assert np.isclose(chain_precision[0, 2], 0)

    ninety_five = chi2.ppf(0.95, df=2)
    inner_mass = chi2.cdf(1, df=2)
    print(f"conditional A|B=0: mean={cond_mean:.3f}, variance={cond_var:.3f}")
    print(f"log p(A=2.2,B=0)={logpdf:.6f}; SciPy={reference_logpdf:.6f}")
    print(f"conditional density ratio={ratio:.6f}; normal pdf={conditional_density:.6f}")
    print(f"2D squared-radius 1 mass={inner_mass:.6f}; 95% cutoff={ninety_five:.6f}")
    print(f"sample mean={empirical_mean.round(3)}")
    print(f"sample covariance={np.round(empirical_cov, 3).tolist()}")
    print(f"chain precision (1,3)={chain_precision[0, 2]:.1f}")

    eigvals, eigvecs = np.linalg.eigh(cov)
    angle = np.linspace(0, 2 * np.pi, 400)
    circle = np.vstack((np.cos(angle), np.sin(angle)))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    colors = ("#3b6f8e", "#a66b4f")
    for radius_sq, label, color in ((1.0, "39.3% mass", colors[0]),
                                    (ninety_five, "95% mass", colors[1])):
        ellipse = mean[:, None] + eigvecs @ (np.sqrt(eigvals * radius_sq)[:, None] * circle)
        axes[0].plot(ellipse[0], ellipse[1], color=color, lw=2, label=label)
    axes[0].axhline(observed_b, color="#6d5a9a", ls="--", label="condition B=0")
    axes[0].scatter(*mean, color="#2d2a23", zorder=3)
    axes[0].set(xlabel="A", ylabel="B", title="Probability ellipses in 2D",
                xlim=(-4.5, 6.5), ylim=(-4.0, 2.0))
    axes[0].set_aspect("equal", adjustable="box")
    axes[0].legend(frameon=False, fontsize=8, loc="lower right")
    grid = np.linspace(-5.0, 7.0, 500)
    axes[1].plot(grid, norm.pdf(grid, mean[0], np.sqrt(cov[0, 0])),
                 color=colors[0], lw=2, label="marginal A: N(1, 4)")
    axes[1].plot(grid, norm.pdf(grid, cond_mean, np.sqrt(cond_var)),
                 color=colors[1], lw=2, label="A | B=0: N(2.2, 2.56)")
    axes[1].set(xlabel="A", ylabel="density", title="Observing B shifts and narrows A")
    axes[1].legend(frameon=False, fontsize=8)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.18)
    svg = Path(__file__).with_name("gaussian_conditioning.svg")
    fig.savefig(svg, bbox_inches="tight")
    if len(sys.argv) == 3 and sys.argv[1] == "--png":
        fig.savefig(sys.argv[2], dpi=180, bbox_inches="tight")
    print(f"wrote {svg.name}")


if __name__ == "__main__":
    main()
