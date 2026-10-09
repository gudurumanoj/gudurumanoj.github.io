---
title: "Prefix Sums, Once and For All"
date: 2026-10-03T10:00:00+05:30
draft: true
tags: ["cp", "building-block"]
summary: "Range-sum queries in O(1) after O(n) preprocessing, plus the 2D version and difference arrays."
---

## 1D prefix sums

```cpp
vector<long long> pre(n + 1, 0);
for (int i = 0; i < n; i++) pre[i + 1] = pre[i] + a[i];
// sum of a[l..r] (inclusive)
auto query = [&](int l, int r) { return pre[r + 1] - pre[l]; };
```

## 2D prefix sums

$$
S_{i,j} = a_{i,j} + S_{i-1,j} + S_{i,j-1} - S_{i-1,j-1}
$$

## Difference arrays

Add $v$ to every element of $[l, r]$ in $O(1)$: `d[l] += v; d[r + 1] -= v;`, then take a
prefix sum at the end.

This is a placeholder draft; replace it with your own notes.
