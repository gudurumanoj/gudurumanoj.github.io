"""Reproducible Monte Carlo check of independent and block-dependent means."""

import numpy as np


SEED = 20261110
P = 0.1
REPETITIONS = 20_000
rng = np.random.default_rng(SEED)


def report(name, means, theoretical_variance):
    empirical_variance = np.var(means, ddof=0)
    print(
        f"{name}: mean={means.mean():.5f}, "
        f"MC variance={empirical_variance:.6f}, "
        f"theory={theoretical_variance:.6f}, "
        f"5/95% quantiles={np.quantile(means, [0.05, 0.95])}"
    )


if __name__ == "__main__":
    for n in (20, 200):
        draws = rng.binomial(1, P, size=(REPETITIONS, n))
        means = draws.mean(axis=1)
        report(f"iid n={n}", means, P * (1 - P) / n)

    block_size = 5
    blocks = 200 // block_size
    independent_blocks = rng.binomial(1, P, size=(REPETITIONS, blocks))
    repeated_draws = np.repeat(independent_blocks, block_size, axis=1)
    dependent_means = repeated_draws.mean(axis=1)
    assert repeated_draws.shape[1] == 200
    assert np.allclose(dependent_means, independent_blocks.mean(axis=1))
    report("5x repeated blocks, n=200", dependent_means, P * (1 - P) / blocks)

    eps, delta = 0.1, 0.05
    n_needed = int(np.ceil(np.log(2 / delta) / (2 * eps**2)))
    print(f"Hoeffding: n >= {n_needed} gives P(|mean-p| >= {eps}) <= {delta}")
