"""Discrete information measures with explicit zero-support handling (base 2)."""

import numpy as np


def distribution(values):
    a = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(a)) or np.any(a < 0):
        raise ValueError("Expected nonnegative probabilities summing to one")
    total = a.sum()
    if not np.isclose(total, 1.0, rtol=1e-5, atol=1e-8):
        raise ValueError("Expected nonnegative probabilities summing to one")
    return a / total  # Remove roundoff from an otherwise normalized input.


def entropy(p):
    p = distribution(p)
    positive = p > 0
    return -float(np.sum(p[positive] * np.log2(p[positive])))


def cross_entropy(p, q):
    p, q = distribution(p), distribution(q)
    if p.shape != q.shape:
        raise ValueError("Distributions must have the same shape")
    positive = p > 0
    if np.any(q[positive] == 0):
        return float("inf")
    return -float(np.sum(p[positive] * np.log2(q[positive])))


def kl(p, q):
    p, q = distribution(p), distribution(q)
    if p.shape != q.shape:
        raise ValueError("Distributions must have the same shape")
    positive = p > 0
    if np.any(q[positive] == 0):
        return float("inf")
    log_ratio = np.log2(p[positive]) - np.log2(q[positive])
    return float(np.sum(p[positive] * log_ratio))


def mutual_information(joint):
    joint = distribution(joint)
    if joint.ndim != 2:
        raise ValueError("Expected a 2D joint distribution")
    row_mass, col_mass = joint.sum(axis=1), joint.sum(axis=0)
    rows, cols = np.nonzero(joint)
    mass = joint[rows, cols]
    # Avoid underflow from multiplying two tiny marginal probabilities.
    log_ratio = np.log2(mass) - np.log2(row_mass[rows]) - np.log2(col_mass[cols])
    return float(np.sum(mass * log_ratio))


if __name__ == "__main__":
    p = np.array([0.8, 0.2])
    q = np.array([0.6, 0.4])
    print(f"H(p): {entropy(p):.6f} bits")
    print(f"H(p,q): {cross_entropy(p, q):.6f} bits")
    print(f"KL(p||q): {kl(p, q):.6f} bits")
    print(f"KL(q||p): {kl(q, p):.6f} bits")
    print(f"H(p,q) - H(p): {cross_entropy(p, q) - entropy(p):.6f} bits")
    print("KL([1,0]||[0,1]):", kl([1, 0], [0, 1]))

    multimodal = [0.499, 0.002, 0.499]
    cover = [0.25, 0.50, 0.25]
    focus = [0.98, 0.01, 0.01]
    print("limited family, forward (cover, focus):",
          np.round([kl(multimodal, cover), kl(multimodal, focus)], 6))
    print("limited family, reverse (cover, focus):",
          np.round([kl(cover, multimodal), kl(focus, multimodal)], 6))

    # Rows: (X,Y) = 00, 01, 10, 11. Columns: Z = X XOR Y = 0, 1.
    pair_z = np.array([[0.25, 0.0], [0.0, 0.25],
                       [0.0, 0.25], [0.25, 0.0]])
    x_z = pair_z.reshape(2, 2, 2).sum(axis=1)
    y_z = pair_z.reshape(2, 2, 2).sum(axis=0)
    print(f"I(X;Z): {mutual_information(x_z):.6f} bits")
    print(f"I(Y;Z): {mutual_information(y_z):.6f} bits")
    print(f"I((X,Y);Z): {mutual_information(pair_z):.6f} bits")
