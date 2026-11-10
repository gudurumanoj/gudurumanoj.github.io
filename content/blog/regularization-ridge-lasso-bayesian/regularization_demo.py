"""Normalized ridge/lasso example; writes regularization_spectrum.svg."""

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


SEED = 20261110


def make_design(rng, n):
    latent = rng.normal(size=(n, 3))
    jitter = rng.normal(size=(n, 12))
    return np.column_stack(
        (latent[:, 0] + 0.04 * jitter[:, 0],
         latent[:, 0] + 0.04 * jitter[:, 1],
         latent[:, 1], latent[:, 2], jitter[:, 4:])
    )


def soft(z, threshold):
    return np.sign(z) * max(abs(z) - threshold, 0.0)


def coordinate_fit(x, y, lam1, lam2=0.0, tol=1e-11, max_sweeps=30000):
    """Minimize ||y-Xw||^2/(2n) + lam1*||w||_1 + lam2*||w||^2/2.

    Columns of x have unit mean square. The caller centers y and x.
    """
    n, p = x.shape
    w = np.zeros(p)
    residual = y.copy()
    column_norms = np.sum(x * x, axis=0) / n
    for sweep in range(max_sweeps):
        largest_change = 0.0
        for j in range(p):
            residual += x[:, j] * w[j]
            z = x[:, j] @ residual / n
            new = soft(z, lam1) / (column_norms[j] + lam2)
            residual -= x[:, j] * new
            largest_change = max(largest_change, abs(new - w[j]))
            w[j] = new
        if largest_change < tol:
            return w, sweep + 1
    raise RuntimeError("Coordinate descent did not converge")


def main():
    rng = np.random.default_rng(SEED)
    n_train, n_test = 35, 4000
    raw_train = make_design(rng, n_train)
    raw_test = make_design(rng, n_test)
    true_w = np.array([2.0, 0.0, -1.5, 1.0] + [0.0] * 8)
    intercept = 1.25
    signal_train = intercept + raw_train @ true_w
    signal_test = intercept + raw_test @ true_w
    y_train = signal_train + rng.normal(scale=2.0, size=n_train)

    # Fit preprocessing on training rows alone; leave the intercept unpenalized.
    feature_mean = raw_train.mean(axis=0)
    feature_scale = raw_train.std(axis=0)
    assert np.all(feature_scale > 0)
    x = (raw_train - feature_mean) / feature_scale
    xt = (raw_test - feature_mean) / feature_scale
    y_mean = y_train.mean()
    yc = y_train - y_mean
    n, p = x.shape
    gram = x.T @ x / n
    rhs = x.T @ yc / n

    def ridge(lam):
        return np.linalg.solve(gram + lam * np.eye(p), rhs)

    def excess_mse(w):
        return np.mean((y_mean + xt @ w - signal_test) ** 2)

    ols = np.linalg.lstsq(x, yc, rcond=None)[0]
    lambdas = np.array([0.01, 0.03, 0.1, 0.3, 1.0])
    ridge_fits = [ridge(lam) for lam in lambdas]
    lasso_fits = [coordinate_fit(x, yc, lam)[0] for lam in lambdas]
    elastic_w, sweeps = coordinate_fit(x, yc, lam1=0.1, lam2=0.1)
    ridge_errors = [excess_mse(w) for w in ridge_fits]
    lasso_errors = [excess_mse(w) for w in lasso_fits]

    # KKT check for the lasso solution at lambda=0.1.
    w = lasso_fits[2]
    score = x.T @ (yc - x @ w) / n
    active = abs(w) > 1e-8
    assert np.max(abs(score[active] - 0.1 * np.sign(w[active]))) < 1e-7
    assert np.max(abs(score[~active])) <= 0.1 + 1e-7

    print(f"train n={n_train}, features={p}, held-out n={n_test}")
    print(f"OLS excess MSE={excess_mse(ols):.4f}, coeffs x0/x1={ols[:2].round(3)}")
    for i, lam in enumerate(lambdas):
        print(f"lambda={lam:.2f}: ridge={ridge_errors[i]:.4f}, "
              f"lasso={lasso_errors[i]:.4f}, "
              f"ridge x0/x1={ridge_fits[i][:2].round(3)}, "
              f"lasso x0/x1={lasso_fits[i][:2].round(3)}, "
              f"lasso active={np.count_nonzero(abs(lasso_fits[i]) > 1e-8)}")
    print(f"lambda1=lambda2=0.1: elastic net excess MSE={excess_mse(elastic_w):.4f}, "
          f"coeffs x0/x1={elastic_w[:2].round(3)}, sweeps={sweeps}")

    d = np.linalg.svd(x, compute_uv=False)
    eig = d * d / n
    assert np.all(eig > 0)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    colors = ["#3b6f8e", "#a66b4f", "#6d5a9a"]
    for lam, color in zip((0.03, 0.1, 1.0), colors):
        factors = eig / (eig + lam)
        axes[0].plot(range(1, p + 1), factors, "o-", color=color,
                     label=f"λ={lam:g}, df={factors.sum():.1f}")
    axes[0].set(xlabel="singular direction (strong to weak)",
                ylabel="ridge retention factor", ylim=(-0.05, 1.05),
                title="Weak directions shrink first")
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].plot(lambdas, ridge_errors, "o-", color=colors[0], label="ridge")
    axes[1].plot(lambdas, lasso_errors, "s-", color=colors[1], label="lasso")
    axes[1].axhline(excess_mse(ols), color="#777777", ls="--", label="OLS")
    axes[1].set_xscale("log")
    axes[1].set(xlabel="λ in mean-loss objective", ylabel="held-out excess MSE",
                title="One simulated split, not a guarantee")
    axes[1].legend(frameon=False, fontsize=8)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.2)
    svg = Path(__file__).with_name("regularization_spectrum.svg")
    fig.savefig(svg, bbox_inches="tight")
    if len(sys.argv) == 3 and sys.argv[1] == "--png":
        fig.savefig(sys.argv[2], dpi=180, bbox_inches="tight")
    print(f"wrote {svg.name}")


if __name__ == "__main__":
    main()
