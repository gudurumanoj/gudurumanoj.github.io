---
title: "Softmax and Numerical Stability"
date: 2026-10-05T10:00:00+05:30
draft: true
tags: ["ml", "math", "building-block"]
summary: "Why subtracting the max before exponentiating keeps softmax from overflowing, and the log-sum-exp trick behind it."
---

## The problem

For logits $z \in \mathbb{R}^K$, softmax is

$$
\sigma(z)_i = \frac{e^{z_i}}{\sum_j e^{z_j}}.
$$

With FP32, $e^{89}$ already overflows to `inf`.

## The fix

Softmax is invariant to shifting all logits by a constant $c$:

$$
\frac{e^{z_i - c}}{\sum_j e^{z_j - c}} = \frac{e^{z_i}}{\sum_j e^{z_j}}.
$$

Choosing $c = \max_j z_j$ makes every exponent $\le 0$.

## Log-sum-exp

$$
\log \sum_j e^{z_j} = c + \log \sum_j e^{z_j - c}
$$

This is a placeholder draft; replace it with your own notes.
