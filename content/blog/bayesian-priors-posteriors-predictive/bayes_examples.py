"""Exact conjugate calculations for the accompanying article.

Run: python3 bayes_examples.py
Requires NumPy and SciPy. The displayed observations are illustrative inputs.
"""

import numpy as np
from scipy.special import betaln, gammaln
from scipy.stats import beta, betabinom, norm


def beta_binomial_update(alpha: float, beta_shape: float,
                         successes: int, failures: int) -> tuple[float, float]:
    if not (np.isfinite(alpha) and np.isfinite(beta_shape)
            and alpha > 0 and beta_shape > 0):
        raise ValueError("Beta shapes must be finite and positive")
    if any(not isinstance(c, (int, np.integer)) or c < 0
           for c in (successes, failures)):
        raise ValueError("Counts must be nonnegative integers")
    return alpha + successes, beta_shape + failures


def predictive_count(k: int, m: int, alpha: float, beta_shape: float) -> float:
    """P(K=k | data), integrating a shared Bernoulli probability over its Beta posterior."""
    if not isinstance(m, (int, np.integer)) or m < 0:
        raise ValueError("Number of future trials must be a nonnegative integer")
    if not (np.isfinite(alpha) and np.isfinite(beta_shape)
            and alpha > 0 and beta_shape > 0):
        raise ValueError("Beta shapes must be finite and positive")
    if not isinstance(k, (int, np.integer)):
        raise ValueError("Success count must be an integer")
    if not 0 <= k <= m:
        return 0.0
    log_choose = gammaln(m + 1) - gammaln(k + 1) - gammaln(m - k + 1)
    return float(np.exp(log_choose +
                        betaln(alpha + k, beta_shape + m - k) -
                        betaln(alpha, beta_shape)))


def main() -> None:
    a, b = beta_binomial_update(2, 2, successes=7, failures=3)
    posterior_mean = a / (a + b)
    posterior_map = (a - 1) / (a + b - 2)  # Only valid for a,b > 1.
    predictive = [predictive_count(k, 2, a, b) for k in range(3)]
    assert np.allclose(predictive, betabinom.pmf([0, 1, 2], 2, a, b))
    assert np.isclose(sum(predictive), 1)
    assert np.isclose(beta.cdf(beta.ppf(.975, a, b), a, b) -
                      beta.cdf(beta.ppf(.025, a, b), a, b), .95)

    # A different order of the same conditionally independent observations.
    sequence = [1, 0, 1, 1, 0, 1, 1, 0, 1, 1]
    sequential_a, sequential_b = 2., 2.
    for observation in sequence:
        sequential_a, sequential_b = beta_binomial_update(
            sequential_a, sequential_b, observation, 1 - observation)
    assert (sequential_a, sequential_b) == (a, b)

    print(f"Posterior Beta({a:.0f}, {b:.0f})")
    print(f"Posterior mean={posterior_mean:.6f}, MAP={posterior_map:.6f}")
    print(f"95% equal-tail credible interval=({beta.ppf(.025, a, b):.6f}, "
          f"{beta.ppf(.975, a, b):.6f})")
    print("Next two successes count probabilities=" +
          ", ".join(f"P(K={k})={prob:.6f}" for k, prob in enumerate(predictive)))
    print(f"P(two successes): predictive={predictive[2]:.6f}, "
          f"plug-in mean^2={posterior_mean**2:.6f}")
    for prior_a, prior_b in [(1, 1), (2, 2), (20, 20)]:
        updated_a, updated_b = beta_binomial_update(prior_a, prior_b, 7, 3)
        print(f"Prior Beta({prior_a}, {prior_b}) -> posterior mean="
              f"{updated_a/(updated_a+updated_b):.6f}")

    # Normal prior on a mean; known observation variance.
    observations = np.array([1., 2., 3.])
    prior_mean, prior_variance, observation_variance = 0., 4., 1.
    precision = 1 / prior_variance + len(observations) / observation_variance
    posterior_variance = 1 / precision
    normal_posterior_mean = posterior_variance * (
        prior_mean / prior_variance + observations.sum() / observation_variance)
    predictive_variance = observation_variance + posterior_variance
    assert np.isclose(norm.var(loc=normal_posterior_mean,
                               scale=np.sqrt(predictive_variance)),
                      predictive_variance)
    print(f"Normal posterior mean={normal_posterior_mean:.6f}, "
          f"variance={posterior_variance:.6f}")
    print(f"Next-observation predictive variance={predictive_variance:.6f}")


if __name__ == "__main__":
    main()
