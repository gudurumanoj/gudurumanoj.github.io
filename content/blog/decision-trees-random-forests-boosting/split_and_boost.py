"""Reproduce the worked split and one logistic XGBoost step in the post.

Requires only NumPy. Run: python split_and_boost.py
"""

import numpy as np


def gini(labels):
    if len(labels) == 0:
        return 0.0
    proportions = np.bincount(labels, minlength=2) / len(labels)
    return 1.0 - np.sum(proportions**2)


x = np.arange(1, 9)
y = np.array([0, 0, 1, 0, 1, 1, 1, 1])
parent = gini(y)
for threshold in (2.5, 4.5):
    left, right = y[x <= threshold], y[x > threshold]
    children = (len(left) * gini(left) + len(right) * gini(right)) / len(y)
    print(f"threshold={threshold:.1f}, weighted Gini={children:.6f}, gain={parent - children:.6f}")

# Four rows with binary labels, all at the same initial logit F=0.
labels = np.array([0, 0, 1, 1])
probability = 1 / (1 + np.exp(-np.zeros(4)))
gradients = probability - labels
hessians = probability * (1 - probability)
regularization, split_penalty = 1.0, 0.1


def score(index):
    G, H = gradients[index].sum(), hessians[index].sum()
    return G**2 / (H + regularization), -G / (H + regularization)


left_score, left_weight = score(np.array([0, 1]))
right_score, right_weight = score(np.array([2, 3]))
parent_score, _ = score(np.arange(4))
gain = 0.5 * (left_score + right_score - parent_score) - split_penalty
print(f"boost gain={gain:.6f}, leaf weights=({left_weight:.6f}, {right_weight:.6f})")
