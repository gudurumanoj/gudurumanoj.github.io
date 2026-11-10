"""Seeded CPU arithmetic and plot for the companion Monte Carlo article.

Run: python3 -B toy.py (requires Matplotlib for the plot).
This is a teaching example, not a production sampler or diagnostic package.
"""

from math import exp, log, pi, sqrt
import random


def mean(xs):
    return sum(xs) / len(xs)


def sample_var(xs):
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def log_normal(x, mu=0.0, sigma=1.0):
    return -0.5 * ((x - mu) / sigma) ** 2 - log(sigma * sqrt(2 * pi))


def logsumexp(a, b):
    m = max(a, b)
    return m + log(exp(a - m) + exp(b - m))


def log_mixture(x):
    return logsumexp(log_normal(x, -4.0), log_normal(x, 4.0)) - log(2)


def mh(log_target, start, width, steps, rng):
    x, accepted = start, 0
    out = []
    for _ in range(steps):
        proposal = x + rng.gauss(0, width)
        # Symmetric random walk: proposal-density ratio cancels.
        if rng.random() < exp(min(0.0, log_target(proposal) - log_target(x))):
            x, accepted = proposal, accepted + 1
        out.append(x)  # Rejection repeats the current state.
    return out, accepted / steps


def batch_means_mcse(xs, batch_size=100):
    k = len(xs) // batch_size
    assert k >= 2
    means = [mean(xs[i * batch_size:(i + 1) * batch_size]) for i in range(k)]
    return sqrt(sample_var(means) / k)


def check_detailed_balance():
    target = [0.2, 0.5, 0.3]
    proposal = [[0.2, 0.7, 0.1], [0.3, 0.2, 0.5], [0.4, 0.2, 0.4]]
    transition = [[0.0] * 3 for _ in range(3)]
    for i in range(3):
        assert abs(sum(proposal[i]) - 1) < 1e-12
        for j in range(3):
            if i == j:
                continue
            transition[i][j] = proposal[i][j] * min(
                1.0, target[j] * proposal[j][i] / (target[i] * proposal[i][j])
            )
        transition[i][i] = 1.0 - sum(transition[i][j] for j in range(3) if j != i)
        assert abs(sum(transition[i]) - 1) < 1e-12
        assert transition[i][i] >= 0
    for i in range(3):
        for j in range(3):
            assert abs(target[i] * transition[i][j] - target[j] * transition[j][i]) < 1e-12
    for j in range(3):
        assert abs(sum(target[i] * transition[i][j] for i in range(3)) - target[j]) < 1e-12
    print("finite-grid detailed balance: pass")


def main():
    check_detailed_balance()
    rng = random.Random(20261110)
    n = 30_000
    direct = [rng.gauss(0, 1) for _ in range(n)]
    direct_x2 = mean([x * x for x in direct])
    direct_mcse = sqrt(sample_var([x * x for x in direct]) / n)
    assert abs(direct_x2 - 1) < 0.05  # Loose seeded teaching check, not proof.

    # Importance sample E_p[X^2] with p=N(0,1), q=N(0,2^2).
    qdraws = [rng.gauss(0, 2) for _ in range(n)]
    logw = [log_normal(x) - log_normal(x, 0, 2) for x in qdraws]
    # Subtract max before exponentiation: stable normalized weights.
    pivot = max(logw)
    scaled = [exp(w - pivot) for w in logw]
    total_scaled = sum(scaled)
    normalized = [w / total_scaled for w in scaled]
    snis = sum(w * x * x for w, x in zip(normalized, qdraws))
    # This known normalized p permits an unbiased, non-self-normalized estimate.
    is_plain = mean([exp(w) * x * x for w, x in zip(logw, qdraws)])
    weight_ess = 1 / sum(w * w for w in normalized)

    # Control variate for E[X^4]=3: E[X^2]=1 and optimal population c=6.
    raw_x4 = mean([x ** 4 for x in direct])
    controlled_x4 = mean([x ** 4 - 6 * (x * x - 1) for x in direct])
    assert abs(controlled_x4 - 3) < 0.2

    print(f"direct E[X^2]={direct_x2:.5f} iid MCSE={direct_mcse:.5f}")
    print(f"IS E[X^2]={is_plain:.5f} SNIS={snis:.5f} weight ESS={weight_ess:.0f}/{n}")
    print(f"E[X^4] direct={raw_x4:.5f} control={controlled_x4:.5f} exact=3")

    # Separate seeds keep the two chains reproducible and independent.
    chains = []
    for width, seed in [(0.3, 31), (4.0, 47)]:
        draws, acceptance = mh(log_mixture, -4.0, width, 13_000, random.Random(seed))
        kept = draws[1_000:]
        chain_mean = mean(kept)
        mcse = batch_means_mcse(kept)
        right = mean([x > 0 for x in kept])
        print(f"RW width={width:.1f} acceptance={acceptance:.3f} mean={chain_mean:.3f} batch MCSE={mcse:.3f} right fraction={right:.3f}")
        chains.append(kept)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.2), sharex=True, constrained_layout=True)
    for ax, chain, width in zip(axes, chains, [0.3, 4.0]):
        ax.plot(range(2_000), chain[:2_000], lw=0.55, color="#a66b4f")
        ax.axhline(-4, color="#777", ls="--", lw=0.8)
        ax.axhline(4, color="#777", ls="--", lw=0.8)
        ax.set(ylabel="State x", title=f"Symmetric random walk proposal width {width}")
    axes[-1].set_xlabel("Retained iteration (first 2,000 shown)")
    fig.savefig("traces.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
