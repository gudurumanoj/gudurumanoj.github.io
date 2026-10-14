---
title: "Softmax and Numerical Stability"
date: 2026-10-05T10:00:00+05:30
draft: false
topics: ["ml", "math"]
tags: ["building-block"]
summary: "Why naive softmax returns NaN, why subtracting the max fixes it exactly, and the related tricks: log-sum-exp, log-softmax, cross-entropy from logits, low-precision accumulation, masked rows, and the online softmax behind FlashAttention."
references:
  - id: milakov
    text: 'Maxim Milakov, Natalia Gimelshein. "Online normalizer calculation for softmax." 2018.'
    url: https://arxiv.org/abs/1805.02867
  - id: flashattn
    text: 'Tri Dao, Daniel Y. Fu, Stefano Ermon, Atri Rudra, Christopher Ré. "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness." 2022.'
    url: https://arxiv.org/abs/2205.14135
  - id: vaswani
    text: 'Ashish Vaswani et al. "Attention Is All You Need." 2017.'
    url: https://arxiv.org/abs/1706.03762
---

Softmax turns a vector of arbitrary real numbers (logits) into a probability distribution.
It sits at the end of every classifier, inside every attention layer, and in every sampling
step of a language model. Written the way the textbook defines it, it also returns `NaN` on
perfectly reasonable inputs.

This post covers why that happens, the one-line fix, and the family of tricks around it that
every ML framework uses quietly: log-sum-exp, log-softmax, cross-entropy that takes logits,
float32 accumulation, masked attention rows, and the streaming "online" softmax that makes
FlashAttention possible.

## The definition

For logits $z \in \mathbb{R}^K$, softmax is

$$
\sigma(z)_i = \frac{e^{z_i}}{\sum_{j=1}^{K} e^{z_j}}.
$$

Every output is positive and they sum to 1. Exponentiating makes the largest logit dominate:
a logit that is larger by 1 gets $e \approx 2.7\times$ the weight, larger by 10 gets
$22{,}000\times$. That sharpness is what makes softmax useful, and it is also the problem.

## The problem: exp falls off a cliff

$e^x$ grows so fast that floating-point numbers run out of range almost immediately. The
largest finite value of a format is reached at $x = \ln(\text{max})$:

| Format | Largest finite value | $e^x$ overflows to `inf` at | $e^x$ underflows to 0 at |
|--------|----------------------|------------------------------|---------------------------|
| float16 | 65504 | $x \approx 11.1$ | $x \approx -16.6$ |
| bfloat16 | $\approx 3.4 \times 10^{38}$ | $x \approx 88.7$ | $x \approx -92$ |
| float32 | $\approx 3.4 \times 10^{38}$ | $x \approx 88.7$ | $x \approx -103.3$ |
| float64 | $\approx 1.8 \times 10^{308}$ | $x \approx 709.8$ | $x \approx -744.4$ |

The underflow column is where $e^x$ drops below the smallest subnormal number and becomes
exactly 0.[^subnormal]

[^subnormal]: Subnormals are the tiny numbers below a format's smallest "normal" value, stored with reduced precision. For float32 the normal range ends near $e^{-87.3}$ and subnormals reach down to $e^{-103.3}$. Some GPU modes flush subnormals to zero, which moves the cliff to the normal limit.

That gives two ways for the naive formula to fail:

- **Overflow.** One large logit makes its $e^{z_i}$ equal `inf`. The sum is `inf`, and
  `inf / inf` is `NaN`.
- **Underflow.** All logits are very negative, so every $e^{z_j}$ becomes 0, and `0 / 0` is
  `NaN`.

```python
import numpy as np

def softmax_naive(z):
    e = np.exp(z)
    return e / e.sum()

z = np.array([1000.0, 1001.0, 1002.0], dtype=np.float32)
print(softmax_naive(z))          # e^1000 = inf, and inf / inf = nan

z = np.array([-1000.0, -1001.0, -1002.0], dtype=np.float32)
print(softmax_naive(z))          # every e^z rounds to 0, and 0 / 0 = nan

z = np.array([10.0, 11.0, 12.0], dtype=np.float16)
print(softmax_naive(z))          # e^12 is already too big for float16
```

```text {title="Output"}
[nan nan nan]
[nan nan nan]
[ 0.  0. nan]
```

The last case is the scary one. Logits of 10 to 12 are completely normal for a trained
classifier, and in float16 they already break the naive formula.

## The fix: subtract the max

Softmax doesn't change if you add the same constant $c$ to every logit, because the factor
$e^{-c}$ cancels between numerator and denominator:

$$
\frac{e^{z_i - c}}{\sum_j e^{z_j - c}}
= \frac{e^{-c}\, e^{z_i}}{e^{-c} \sum_j e^{z_j}}
= \frac{e^{z_i}}{\sum_j e^{z_j}}.
$$

Choose $c = \max_j z_j$. This isn't an approximation; the result is mathematically identical.
What changes is the range of every intermediate value:

- Every exponent $z_j - c$ is $\le 0$, so every $e^{z_j - c}$ lies in $(0, 1]$. **Nothing
  can overflow.**
- The largest logit contributes exactly $e^0 = 1$, so the denominator lies in $[1, K]$. **It
  can never be 0**, so no `0 / 0`.
- A term can still underflow to 0, but only if its logit is about 100 below the maximum
  (in float32), which means its true probability is below $e^{-100}$. Rounding that to 0 is
  the correct answer to float32 precision.

```python
def softmax(z, axis=-1):
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=axis, keepdims=True)

print(softmax(np.array([1000.0, 1001.0, 1002.0], dtype=np.float32)))
print(softmax(np.array([-1000.0, -1001.0, -1002.0], dtype=np.float32)))
print(softmax(np.array([10.0, 11.0, 12.0], dtype=np.float16)))
```

```text {title="Output"}
[0.09003057 0.24472846 0.66524094]
[0.66524094 0.24472846 0.09003057]
[0.0901 0.2448 0.6655]
```

All three inputs have the same gaps between logits (1 apart), so they give the same
distribution, as they should. `axis` and `keepdims` make the function work row by row on a
batch, e.g. a `(batch, classes)` matrix.

## Log-sum-exp and log-softmax

Training rarely needs the probabilities themselves; it needs their logarithms. The obvious
route, `np.log(softmax(z))`, loses everything the max trick saved:

```python
def logsumexp(z, axis=-1):
    c = z.max(axis=axis, keepdims=True)
    return c + np.log(np.exp(z - c).sum(axis=axis, keepdims=True))

def log_softmax(z, axis=-1):
    return z - logsumexp(z, axis=axis)

z = np.array([0.0, 200.0], dtype=np.float32)
print(np.log(softmax(z)))   # softmax gives [0, 1] (e^-200 underflows), then log(0) = -inf
print(log_softmax(z))       # the true answer
```

```text {title="Output"}
[-inf   0.]
[-200.    0.]
```

The probability $e^{-200}$ isn't representable in float32, but its logarithm, $-200$, is
an ordinary number. So compute in log space from the start. Taking the log of softmax:

$$
\log \sigma(z)_i = z_i - \log \sum_j e^{z_j} = z_i - \operatorname{LSE}(z).
$$

The log-sum-exp function $\operatorname{LSE}$ gets the same shift:

$$
\operatorname{LSE}(z) = \log \sum_j e^{z_j} = c + \log \sum_j e^{z_j - c}, \qquad c = \max_j z_j.
$$

Inside the log the sum is in $[1, K]$, so the log is in $[0, \log K]$. That also gives a nice
bound:

$$
\max_j z_j \;\le\; \operatorname{LSE}(z) \;\le\; \max_j z_j + \log K.
$$

LSE is a **smooth maximum**: it is never more than $\log K$ above the true max, and unlike
`max` it is differentiable everywhere. Its gradient is exactly softmax:
$\partial \operatorname{LSE} / \partial z_i = \sigma(z)_i$. Softmax really is a "soft argmax".

## Cross-entropy from logits

For a single example with true class $y$, the cross-entropy loss is $-\log \sigma(z)_y$.
With the identity above it becomes

$$
L = \operatorname{LSE}(z) - z_y,
$$

which never forms a probability at all. Its gradient is also simple:

$$
\frac{\partial L}{\partial z_j} = \sigma(z)_j - [j = y],
$$

the predicted distribution minus the one-hot target. Every entry is in $[-1, 1]$, so nothing
explodes.

This is why PyTorch's `F.cross_entropy` takes **raw logits** and not probabilities: it fuses
`log_softmax` and the loss to use exactly this formula. Applying `softmax` yourself and then
passing the result to a loss that expects logits, or taking `log` of probabilities, are two
of the most common sources of silent training bugs.[^torch-names]

[^torch-names]: The stable building blocks under their usual names: `torch.logsumexp`, `F.log_softmax`, `F.cross_entropy`, `nn.BCEWithLogitsLoss`; in SciPy, `scipy.special.logsumexp` and `scipy.special.log_softmax`.

The binary case has the same trap. Sigmoid is softmax over two logits $(0, x)$, and binary
cross-entropy needs $\log(1 + e^{x})$ (softplus), whose naive form overflows for $x \gtrsim 89$
in float32. The stable version splits off the max the same way:

$$
\log(1 + e^{x}) = \max(x, 0) + \log\!\left(1 + e^{-|x|}\right),
$$

computed with `log1p` for the second term. That's what `BCEWithLogitsLoss` does internally,
and the reason to prefer it over `sigmoid` followed by `BCELoss`.

## The backward pass

If you write softmax by hand (in a custom kernel, say), the backward pass needs care too.
The Jacobian of $s = \sigma(z)$ is

$$
\frac{\partial s_i}{\partial z_j} = s_i\,(\delta_{ij} - s_j),
\qquad\text{i.e.}\qquad
J = \operatorname{diag}(s) - s\,s^\top.
$$

Never build that $K \times K$ matrix. Given the upstream gradient $g = \partial L / \partial s$,
the product collapses to

$$
\frac{\partial L}{\partial z} = s \odot \big(g - \langle g, s \rangle\big),
$$

one dot product and an elementwise multiply, $O(K)$ work. It only uses the softmax output
$s$, which is already in $[0, 1]$, so it inherits the stability of the forward pass.

## Low precision: the range is only half the story

The max trick solves overflow, but float16 has a second weakness: only 10 bits of mantissa.
Once a running sum gets large, adding small terms to it changes nothing, because they are
smaller than half the gap between neighbouring float16 values.[^ulp]

[^ulp]: Between 256 and 512, adjacent float16 values are 0.25 apart. Adding anything below 0.125 to 256 rounds straight back to 256.

```python
rng = np.random.default_rng(0)
z = rng.standard_normal(50_000).astype(np.float16)
e = np.exp(z - z.max())

total = np.float16(0)
for v in e:                       # what a naive float16 kernel does
    total = np.float16(total + v)

print(total)                      # float16 accumulator
print(e.astype(np.float32).sum()) # float32 accumulator
```

```text {title="Output"}
247.4
729.2226
```

The float16 sum is off by a factor of three. The sum stopped growing once it got big enough,
and every probability computed from it would be inflated. The fix is to **accumulate in
float32** even when inputs and outputs are float16, which is what fused softmax kernels do.
PyTorch's autocast goes further and runs softmax, log-softmax and cross-entropy entirely in
float32 under mixed precision.

bfloat16 has float32's exponent range (so the same 88.7 overflow point) but only 7 mantissa
bits, so the accumulation problem is even worse there. Same fix.

## Masking: the fully masked row

Attention masks out positions (padding, future tokens) by setting their scores to $-\infty$
before softmax, so $e^{-\infty} = 0$ and they get zero weight. That works until a row has
**every** position masked, which happens with all-padding rows or some sliding-window and
block-sparse masks:

```python
scores = np.array([-np.inf, -np.inf, -np.inf], dtype=np.float32)   # every key masked
print(softmax(scores))
```

```text {title="Output"}
[nan nan nan]
```

The max is $-\infty$, and the shift computes $-\infty - (-\infty) = $ `NaN`. In a transformer
that `NaN` then spreads through the next matmul to the whole batch. Common fixes:

- Use a large finite negative number such as `torch.finfo(dtype).min` instead of $-\infty$.
  The row then comes out uniform (finite but meaningless), so zero it out afterwards.
- Guard the max: where the row max is $-\infty$, replace it with 0 before subtracting, and
  define an empty row's output as all zeros.

Fused attention kernels handle this case explicitly; a hand-written softmax often doesn't.

## Temperature and the √d scale

Two common transformations of the logits interact with all of this.

**Temperature** divides the logits before softmax: $\sigma(z / T)$. $T \to 0$ approaches a
one-hot argmax and $T \to \infty$ approaches uniform. A small $T$ like 0.1 multiplies every
logit by 10, which pushes naive softmax over the cliff ten times sooner; with the max trick
it's harmless.

**Scaled dot-product attention** divides scores by $\sqrt{d}$ (the head dimension) before
softmax{{< cite "vaswani" >}}. If query and key components are independent with mean 0 and
variance 1, their dot product has variance $d$, so with $d = 128$ the raw scores have a
standard deviation around 11. Softmax over scores that spread out is nearly one-hot, and its
gradients nearly vanish. Dividing by $\sqrt{d}$ brings the variance back to 1. This one is about
**saturation** (tiny gradients), not overflow, but it's the same lesson: softmax is only
well-behaved when logit differences are moderate.

## Online softmax: one pass instead of three

The stable softmax reads the input three times: once for the max, once for the sum of
exponentials, and once to normalise. For attention over long sequences, where each row of
scores is too big to keep on chip, those extra passes over memory are the bottleneck.

The fix is to keep a **running max** $m$ and a **running sum** $d$, and rescale the sum
whenever the max changes{{< cite "milakov" >}}. After seeing a new value $x$:

$$
m' = \max(m, x), \qquad d' = d \cdot e^{m - m'} + e^{x - m'}.
$$

The factor $e^{m - m'}$ re-expresses the old sum relative to the new max. It is always
$\le 1$, so the stability guarantee survives. Two partial results over different chunks merge
the same way, which means chunks can be processed independently and combined:

```python
import math

def online_softmax_stats(xs):
    m, d = -math.inf, 0.0                 # running max, running sum of e^(x - m)
    for x in xs:
        m_new = max(m, x)
        d = d * math.exp(m - m_new) + math.exp(x - m_new)
        m = m_new
    return m, d

def merge(a, b):
    (m1, d1), (m2, d2) = a, b
    m = max(m1, m2)
    return m, d1 * math.exp(m1 - m) + d2 * math.exp(m2 - m)

xs = np.random.default_rng(0).standard_normal(1000) * 50
m, d = online_softmax_stats(xs)
print(m == xs.max(), np.isclose(d, np.exp(xs - xs.max()).sum()))

m2, d2 = merge(online_softmax_stats(xs[:400]), online_softmax_stats(xs[400:]))
print(np.isclose(d2, d))
```

```text {title="Output"}
True True
True
```

FlashAttention{{< cite "flashattn" >}} builds on exactly this. It processes keys and values in
tiles that fit in fast on-chip memory, and also carries a running **output** $o$ (the
softmax-weighted sum of value vectors), rescaling it by the same factor:

$$
o' = o \cdot e^{m - m'} + e^{x - m'}\, v.
$$

At the end it divides by $d$ once. The full attention matrix is never written to memory, and
the result is still exact: the same identity as the max trick, applied one tile at a time.

## Checklist

When writing or reviewing anything that touches softmax:

- Subtract the row max before `exp`. Always, in every precision.
- Work in log space when you need logs: `log_softmax` and `logsumexp`, never
  `log(softmax(...))`.
- Feed losses **logits**: `cross_entropy`, `BCEWithLogitsLoss`.
- Accumulate sums in float32 even when the data is float16 or bfloat16.
- Decide what a fully masked row should produce, and make sure it isn't `NaN`.
- For long rows, use a fused or online implementation instead of three passes over memory.

All of these come back to one identity: shifting every logit by the same constant changes
nothing mathematically, but the right shift keeps every intermediate value in range.

{{< references >}}
