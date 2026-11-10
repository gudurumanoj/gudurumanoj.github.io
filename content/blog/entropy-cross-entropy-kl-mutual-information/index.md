---
title: "Entropy, Cross-Entropy, KL Divergence, and Mutual Information"
date: 2026-11-10T11:30:00+05:30
draft: true
topics: ["math", "ml"]
tags: ["interview", "building-block", "information-theory"]
summary: "Four related information measures, one binary worked example, and the precise links to log loss, distribution mismatch, feature information, and data processing."
references:
  - id: mit-entropy
    text: 'Yury Polyanskiy and Yihong Wu. "Information Theory, Chapter 1: Information Measures: Entropy and Divergence." MIT 6.441 lecture notes, 2016.'
    url: https://ocw.mit.edu/courses/6-441-information-theory-spring-2016/resources/mit6_441s16_chapter_1/
  - id: mit-mi
    text: 'Yury Polyanskiy and Yihong Wu. "Information Theory, Chapter 2: Mutual Information." MIT 6.441 lecture notes, 2016.'
    url: https://ocw.mit.edu/courses/6-441-information-theory-spring-2016/resources/mit6_441s16_chapter_2/
  - id: mit-dpi
    text: 'Yury Polyanskiy and Yihong Wu. "Information Theory, Chapter 3: Sufficient Statistics and Data Processing." MIT 6.441 lecture notes, 2016.'
    url: https://ocw.mit.edu/courses/6-441-information-theory-spring-2016/resources/mit6_441s16_chapter_3/
  - id: proper-score
    text: 'Tilmann Gneiting and Adrian E. Raftery. "Strictly Proper Scoring Rules, Prediction, and Estimation." Journal of the American Statistical Association, 2007.'
    url: https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf
  - id: stanford-vi
    text: 'Rafael Rafailov. "Variational Inference" tutorial. Stanford CS330, 2021.'
    url: https://cs330.stanford.edu/fall2021/material/Variational%20Inference%20Tutorial.pdf
  - id: label-smoothing
    text: 'Christian Szegedy et al. "Rethinking the Inception Architecture for Computer Vision." CVPR, 2016, section on label smoothing.'
    url: https://arxiv.org/abs/1512.00567
---

Four formulas appear close together in ML interviews, often with nearly identical logarithms. They answer different questions. Entropy asks how uncertain a distribution is about its own outcome. Cross-entropy asks how costly outcomes from one distribution are when I predict with another. KL divergence is the extra cross-entropy caused by the mismatch. Mutual information asks how much observing one variable reduces uncertainty about another.

I find it easiest to keep track of **which distribution generates the outcome** and **which distribution supplies the log probability**. That simple bookkeeping explains why cross-entropy is a loss, why swapping the arguments of KL changes the result, and why mutual information can detect dependence that correlation misses.

## An outcome's surprise and a distribution's entropy

If an event has probability $p(x)>0$, its self-information is $-\log p(x)$. Rare outcomes are more surprising because their negative log probability is larger. The log base sets the unit: base two gives **bits**, while the natural log gives **nats**. One nat is $1/\ln 2$ bits. An event with probability $1/8$ has $3$ bits of self-information; one with probability $1/2$ has $1$ bit.

The word “information” here is a mathematical quantity, not a judgment about an event's usefulness. A rare random string can be surprising without being meaningful to a reader. In idealized coding, a model that assigns probability $q(x)$ suggests a code length near $-\log_2 q(x)$ bits. Actual one-symbol prefix codes have integer lengths and overhead; long-block coding is where expected log length becomes an operational limit. {{< cite "mit-entropy" >}}

I use finite alphabets for the discrete formulas below; the continuous case appears separately near the end. For a discrete distribution $p$ over outcomes $x$, Shannon entropy averages self-information under that *same* distribution:

$$
H(p)=-\sum_xp(x)\log p(x)
=\mathbb E_{X\sim p}[-\log p(X)].
$$

By continuity, $0\log0$ contributes zero. An impossible outcome never occurs when sampling from $p$, so it contributes no expected surprise. A deterministic distribution has entropy zero. A uniform distribution over $m$ outcomes has entropy $\log m$, the largest entropy among distributions on that same finite set. These are statements about the chosen alphabet: adding impossible outcomes does not change entropy, but changing how outcomes are grouped or represented can.

For a binary variable with $p=(0.8,0.2)$, entropy in bits is $-0.8\log_2(0.8)-0.2\log_2(0.2)\approx0.721928$. That is below the one bit of a fair coin because the first outcome is more predictable. It does **not** mean that each observed label contains exactly $0.721928$ bits: the common outcome has about $0.322$ bits of self-information and the rare one about $2.322$ bits. Entropy is their weighted average.

<figure class="ml-diagram">
<svg viewBox="0 0 860 230" role="img" aria-label="Entropy samples and scores with p; cross entropy samples from p and scores with q; KL subtracts entropy; mutual information compares joint distribution with product of marginals">
  <defs><marker id="ml-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>
  <rect class="box blue" x="35" y="45" width="230" height="95" rx="10"/>
  <text class="name" x="150" y="78">Entropy</text>
  <text class="note blue" x="150" y="110">sample p, score p</text>
  <rect class="box violet" x="315" y="45" width="230" height="95" rx="10"/>
  <text class="name" x="430" y="78">Cross-entropy</text>
  <text class="note violet" x="430" y="110">sample p, score q</text>
  <rect class="box green" x="595" y="45" width="230" height="95" rx="10"/>
  <text class="name" x="710" y="78">KL divergence</text>
  <text class="note green" x="710" y="110">extra score cost</text>
  <line class="arrow" x1="268" y1="92" x2="309" y2="92"/>
  <line class="arrow" x1="548" y1="92" x2="589" y2="92"/>
  <text class="label" x="430" y="190">Mutual information is KL(joint || product of marginals)</text>
</svg>
<figcaption>The left argument of cross-entropy and KL is the distribution used for averaging.</figcaption>
</figure>

## Cross-entropy: score $p$'s outcomes with $q$

Suppose nature draws outcomes from $p$, while a model reports probabilities $q$. The model's expected negative log probability is

$$
H(p,q)=-\sum_xp(x)\log q(x).
$$

This is cross-entropy. If $q(x)=0$ for an outcome with $p(x)>0$, then $H(p,q)=+\infty$: the model declared a possible event impossible. If $p(x)=0$, that term contributes zero even if $q(x)=0$. The support convention is a part of the definition, not a numerical nuisance to hide with an arbitrary epsilon.

For $p=(0.8,0.2)$ and a less accurate prediction $q=(0.6,0.4)$, the expected log loss is $H(p,q)=-0.8\log_2(0.6)-0.2\log_2(0.4)\approx0.853958$ bits. A model using $q=p$ would achieve $H(p)\approx0.721928$ bits. The difference is the cost of predicting $0.6$ instead of the true $0.8$ for the first class.

For an individual labeled example with one-hot target $y$, the familiar classification cross-entropy is $-\sum_k y_k\log q_k=-\log q_{\text{observed class}}$. Averaging many such losses estimates an expectation under the data-generating distribution. In most ML software the log is natural, so the loss is in nats; multiplying by a positive constant to switch units does not change the optimizer. [Softmax numerical stability](/blog/softmax-numerical-stability/) explains how to calculate those log probabilities without overflow, while [ML and NLP metrics](/blog/ml-nlp-metrics/) compares this loss with accuracy and ranking metrics.

## KL divergence is the excess cross-entropy

Subtract the best achievable expected log score under $p$:

$$
D_{\mathrm{KL}}(p\|q)
=\sum_xp(x)\log\frac{p(x)}{q(x)}
=H(p,q)-H(p).
$$

The same support rules apply: a positive $p(x)$ with zero $q(x)$ makes KL infinite. KL is nonnegative. One short proof uses Jensen's inequality for the convex function $-\log$. If $q$ is positive wherever $p$ is positive, then

$$
D_{\mathrm{KL}}(p\|q)
=\mathbb E_p\!\left[-\log\frac{q(X)}{p(X)}\right]
\geq-\log\!\left(\sum_{x:p(x)>0}q(x)\right)
\geq0.
$$

The final sum can be below one if $q$ wastes probability on outcomes impossible under $p$. Equality requires $p=q$ on the whole alphabet. Thus, if I can choose any distribution $q$, minimizing cross-entropy under a fixed true $p$ uniquely chooses $q=p$. If my model family cannot express $p$, optimization chooses the best approximation *within that family* according to this divergence. {{< cite "mit-entropy" >}}

KL is not a metric. In the binary example, $D_{\mathrm{KL}}(p\|q)\approx0.132030$ bits, while $D_{\mathrm{KL}}(q\|p)\approx0.150978$ bits. Swapping the arguments changes which outcomes are weighted in the expectation. KL also need not obey the triangle inequality. Calling it “distance” in casual conversation is harmless only if I remember these missing properties.

| Measure, in bits | $p=(0.8,0.2)$ and $q=(0.6,0.4)$ | What is averaged? |
|---|---:|---|
| $H(p)$ | $0.721928$ | $-\log_2 p(X)$ under $X\sim p$ |
| $H(p,q)$ | $0.853958$ | $-\log_2 q(X)$ under $X\sim p$ |
| $D_{\rm KL}(p\|q)$ | $0.132030$ | $\log_2[p(X)/q(X)]$ under $X\sim p$ |
| $D_{\rm KL}(q\|p)$ | $0.150978$ | $\log_2[q(X)/p(X)]$ under $X\sim q$ |

### Why log loss rewards honest probabilities

Suppose the true conditional chance of class A for an input is $0.8$. Reporting $q(A)=0.6$ or $q(A)=0.8$ makes the same hard class prediction, A. Both therefore have the same expected zero-one error, $0.2$, under this one-input example. Their expected log losses differ: $0.853958$ versus $0.721928$ bits. Log loss cares whether a probability report matches the actual uncertainty, not only whether its largest entry names the right class.

This is why logarithmic scoring is called **strictly proper**: when outcomes really follow $p$, the unique best probability report in expectation is $p$, assuming the allowable reports include it. The proof is the cross-entropy identity and KL nonnegativity above. It does not say a trained model automatically discovers $p$ from finite or biased data, nor that a low log loss on one dataset certifies calibration in every subgroup. It says the *population scoring rule* has the right incentive. Proper scoring rules formalize that distinction. {{< cite "proper-score" >}}

If I replace the true $p$ by an empirical frequency $\hat p$ from a finite dataset, minimizing average log loss over an unrestricted, constant categorical prediction gives $q=\hat p$. That is a statement about fitting the observed sample. Generalization to the true distribution depends on sample design and model assumptions. In conditional classification, the target is $p(y\mid x)$ for each relevant $x$, not one global class frequency. The [naive Bayes, MLE, and MAP](/blog/naive-bayes-mle-map/) article separates those probabilities; I do not need its model-specific derivation to understand why log loss scores them.

Label smoothing makes the target explicit rather than pretending the observed one-hot label is a complete probability law. With $K$ classes, one common choice is $t=(1-\varepsilon)y+\varepsilon(1/K,\ldots,1/K)$ for a one-hot $y$. Training then minimizes $H(t,q)$, which equals $D_{\rm KL}(t\|q)+H(t)$ for that fixed target. The optimum for a single unrestricted example is $q=t$, so smoothing deliberately changes the training target and discourages a probability of exactly one on its observed class. It may be useful as regularization, but it is not evidence that the true conditional label probability equals $t$. Evaluation against real outcomes still needs the unsmoothed task and its intended probability interpretation. {{< cite "label-smoothing" >}}

## Forward and reverse KL under a limited model family

The phrase “forward KL covers modes, reverse KL seeks modes” describes a common *constrained approximation* pattern, not a theorem about every optimizer. Forward KL, $D(p\|q)$, averages under $p$ and charges an infinite cost if $q$ misses a positive-probability region entirely. Reverse KL, $D(q\|p)$, averages under $q$; if $q$ places no mass in one of $p$'s regions, that region contributes nothing directly, while placing $q$ mass where $p$ is tiny is costly. A narrow approximating family may therefore make different tradeoffs. If $q$ can equal $p$, both directions have the same unique optimum. {{< cite "stanford-vi" >}}

Here is a finite illustration. Let $p=(0.499,0.002,0.499)$ have two high-probability outcomes separated by a rare one. Imagine the model is restricted to two candidates: $q_{\rm cover}=(0.25,0.50,0.25)$ and $q_{\rm focus}=(0.98,0.01,0.01)$. The cover candidate allocates mass to both high-probability outcomes but wastes half on the rare middle. The focus candidate concentrates on the first outcome and nearly misses the other. For this *specified pair of candidates*, forward KL prefers cover: about $0.979$ versus $2.324$ bits. Reverse KL prefers focus: about $0.921$ versus $3.484$ bits. Those numbers illustrate the averaging direction. They are not a universal claim that reverse KL always collapses, nor that forward KL always covers every mode well.

In generative modeling, data negative log likelihood can be viewed as forward KL from the data distribution plus a constant when the data distribution is fixed. Variational inference commonly optimizes a reverse KL from an approximating posterior to a target posterior, often through an evidence lower bound. The details depend on what is held fixed and which family is optimized. I would state those arguments before using the shorthand.

## Mutual information measures dependence

For discrete variables $X$ and $Y$ with joint distribution $p(x,y)$, mutual information is the KL divergence between the joint law and the law they would have *if independent*:

$$
I(X;Y)=D_{\mathrm{KL}}(p_{XY}\|p_Xp_Y)
=\sum_{x,y}p(x,y)\log\frac{p(x,y)}{p(x)p(y)}.
$$

Equivalently, $I(X;Y)=H(Y)-H(Y\mid X)=H(X)-H(X\mid Y)$. For discrete variables it is nonnegative, symmetric, and zero exactly when $X$ and $Y$ are independent. The conditional-entropy form means that observing $X$ reduces the *average* uncertainty about $Y$ by $I(X;Y)$. It does not guarantee that every possible observed $x$ reduces uncertainty by the same amount. Mutual information is a property of a joint distribution, not of an isolated pair of numerical values. {{< cite "mit-mi" >}}

An XOR example makes the distinction from correlation sharp. Let $X$ and $Y$ be independent fair bits, and set $Z=X\oplus Y$. The four pairs $(X,Y)$ each have probability $1/4$, and each pair determines $Z$. Consequently $I((X,Y);Z)=H(Z)=1$ bit. But if I reveal only $X$, the unknown fair $Y$ keeps $Z$ fair, so $I(X;Z)=0$; the same holds for $I(Y;Z)$. Neither feature alone says anything about the target, while the pair says everything. A univariate feature screen based only on mutual information with the label can miss that interaction.

Information cannot be manufactured by processing that has no new access to the target. If $T$ is computed from $X$ without separately observing $Y$, then $Y\to X\to T$ is a Markov chain and the data-processing inequality gives $I(Y;T)\leq I(Y;X)$. A lossy compression can discard target information; an invertible transform preserves it. This does **not** say a model trained on $T$ must predict worse than a finite model trained on raw $X$: a simpler representation can make estimation and optimization easier. It says the representation cannot contain more information about $Y$ than its source under that Markov assumption. This is a useful lens for [PCA and dimensionality reduction](/blog/pca-derived/), while remembering that PCA optimizes variance preservation rather than mutual information with a label. {{< cite "mit-dpi" >}}

## Continuous variables need a careful word about entropy

For a continuous density $f$, *differential entropy* is $h(X)=-\int f(x)\log f(x)\,dx$. It is not the discrete entropy above. A uniform variable on an interval of width $a$ has differential entropy $\log a$, which is negative when $a<1$ in the chosen units. If $Y=cX$ for nonzero $c$, then $h(Y)=h(X)+\log|c|$. Changing measurement units changes the number; calling a negative value “negative uncertainty” would be a category error.

KL divergence between two densities, and hence mutual information defined as a KL divergence, remains nonnegative. If I apply the *same invertible, sufficiently regular* change of variables to both distributions, the Jacobian terms cancel in their density ratio, so their KL divergence is unchanged. This is why I use discrete entropy for the worked examples and specify the continuous version when needed. {{< cite "mit-entropy" >}}

## A NumPy check that keeps zero support visible

The [self-contained script](information_check.py) computes discrete measures with base-two logs. It treats $p(x)=0$ terms as zero but returns infinity when $p(x)>0$ and $q(x)=0$; it does not silently add an epsilon to change the mathematical question. It also builds the XOR joint table explicitly. Inputs must be finite, nonnegative, and sum to one within the stated floating-point tolerance; the script normalizes accepted inputs to remove the remaining discrepancy. KL uses differences of logs rather than forming a potentially overflowing ratio. Mutual information also works in logs so that multiplying tiny marginals cannot underflow to a false zero. Results can still have ordinary floating-point roundoff near zero.

The core calculations follow the definitions directly. The positive-support masks keep zero-probability terms out of logarithms.

```python {title="Information measures in NumPy"}
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
```

```bash
python3 information_check.py
```

```text {title="Output"}
H(p): 0.721928 bits
H(p,q): 0.853958 bits
KL(p||q): 0.132030 bits
KL(q||p): 0.150978 bits
H(p,q) - H(p): 0.132030 bits
KL([1,0]||[0,1]): inf
limited family, forward (cover, focus): [0.979186 2.324302]
limited family, reverse (cover, focus): [3.484336 0.921077]
I(X;Z): 0.000000 bits
I(Y;Z): 0.000000 bits
I((X,Y);Z): 1.000000 bits
```

## Interview questions I would rehearse

1. **What is the information in an event of probability $p$?** It is $-\log p$. Base two reports bits; the natural log reports nats. It measures surprise under that probability model, not practical value.

2. **Why is entropy an expectation?** $H(p)=\mathbb E_p[-\log p(X)]$: it averages the surprise of all outcomes according to how often they occur.

3. **What does $0\log0$ mean?** Its limiting contribution is zero. An impossible event does not contribute to an expectation under $p$; a positive-probability event assigned zero by $q$ makes cross-entropy and forward KL infinite.

4. **How does cross-entropy differ from entropy?** Entropy samples and scores with $p$; cross-entropy samples from $p$ but scores with $q$. The latter measures the expected log loss of using $q$ on $p$'s outcomes.

5. **Why is KL nonnegative?** It is cross-entropy minus the minimum possible cross-entropy. Jensen's inequality gives a direct proof, with equality only when $p=q$.

6. **Is KL a distance?** It is asymmetric and generally fails the triangle inequality, so it is not a metric. Its argument order says which distribution supplies the averaging weights.

7. **Why minimize cross-entropy for probabilistic classification?** In expectation under the true conditional distribution, it is uniquely minimized by reporting that distribution when the model can represent it. This is strict propriety, not a guarantee that finite-data training is perfectly calibrated.

8. **Can two models have identical accuracy but different log loss?** Yes. If the true binary probability is $0.8$, reports $0.6$ and $0.8$ choose the same class but receive different expected log losses.

9. **Does reverse KL always seek one mode?** No. That tendency arises when an approximating family cannot match a multimodal target; with an unrestricted family, either KL direction is minimized at the target itself.

10. **What is mutual information?** It is KL between the joint distribution and the product of its marginals, equivalently the average reduction in one variable's entropy after observing the other.

11. **Can each feature have zero MI with a label while the pair predicts it?** Yes. With independent fair bits $X,Y$ and $Z=X\oplus Y$, each alone has zero MI with $Z$, while $(X,Y)$ determines it and gives one bit.

12. **Can a transformation increase information about a label?** Under the Markov assumption $Y\to X\to T$, no: $I(Y;T)\leq I(Y;X)$. It can still help a limited learner use the available information better.

{{< references >}}
