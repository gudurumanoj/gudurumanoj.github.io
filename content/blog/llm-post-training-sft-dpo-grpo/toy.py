"""CPU-only loss checks and reproducible SVG plot for the companion post.

Run from this folder: python3 -B toy.py
Requires numpy and matplotlib only for plotting; loss arithmetic uses stdlib.
"""

from math import exp, log, log1p, sqrt


def softplus(x):
    return max(x, 0.0) + log1p(exp(-abs(x)))


def sft_loss(log_probs, mask):
    assert len(log_probs) == len(mask) and sum(mask) > 0
    return -sum(lp for lp, use in zip(log_probs, mask) if use) / sum(mask)


def dpo_loss(chosen, rejected, ref_chosen, ref_rejected, beta):
    assert beta > 0
    margin = (chosen - rejected) - (ref_chosen - ref_rejected)
    return softplus(-beta * margin)


def ppo_surrogate(ratio, advantage, epsilon=0.2):
    clipped = min(max(ratio, 1 - epsilon), 1 + epsilon)
    return min(ratio * advantage, clipped * advantage)


def group_advantages(rewards):
    mean = sum(rewards) / len(rewards)
    std = sqrt(sum((r - mean) ** 2 for r in rewards) / len(rewards))
    return [(r - mean) / std for r in rewards] if std > 0 else [0.0] * len(rewards)


def main():
    # Prompt and padding positions must not contribute to completion-only SFT.
    assert abs(sft_loss([-10.0, -0.2, -0.4, -100.0], [0, 1, 1, 0]) - 0.3) < 1e-12
    before = dpo_loss(-2.0, -1.0, -2.0, -1.0, 0.5)
    after = dpo_loss(-1.0, -2.0, -2.0, -1.0, 0.5)
    assert after < before
    assert abs(before - log(2)) < 1e-12
    assert abs(ppo_surrogate(1.5, 1.0) - 1.2) < 1e-12
    assert abs(ppo_surrogate(0.5, -1.0) + 0.8) < 1e-12
    assert abs(ppo_surrogate(1.5, -1.0) + 1.5) < 1e-12
    assert group_advantages([1.0, 1.0, 1.0]) == [0.0] * 3
    print(f"SFT masked loss={sft_loss([-10, -.2, -.4, -100], [0, 1, 1, 0]):.3f}")
    print(f"DPO before={before:.6f} after={after:.6f}")
    print(f"PPO A=+1 r=1.5: {ppo_surrogate(1.5, 1.0):.3f}")
    print(f"PPO A=-1 r=0.5: {ppo_surrogate(0.5, -1.0):.3f}")
    print(f"GRPO equal rewards: {group_advantages([1, 1, 1])}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    margins = np.linspace(-6, 6, 301)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), constrained_layout=True)
    axes[0].plot(margins, [dpo_loss(m, 0, 0, 0, 0.5) for m in margins], color="#a66b4f", lw=2)
    axes[0].set(xlabel="Policy preference margin minus reference margin", ylabel="DPO loss", title="DPO, beta = 0.5")
    axes[0].axvline(0, color="#777", lw=1)
    ratios = np.linspace(0.4, 1.6, 301)
    for advantage, color in [(1, "#437f68"), (-1, "#8a5eae")]:
        axes[1].plot(ratios, [ppo_surrogate(r, advantage) for r in ratios], color=color, lw=2, label=f"A = {advantage:+d}")
    axes[1].axvline(0.8, color="#777", ls="--", lw=1)
    axes[1].axvline(1.2, color="#777", ls="--", lw=1)
    axes[1].set(xlabel="New / old policy probability ratio", ylabel="Clipped surrogate (maximize)", title="PPO, epsilon = 0.2")
    axes[1].legend(frameon=False)
    fig.savefig("losses.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
