---
title: "Expectation, Variance, the LLN, and the CLT"
date: 2026-11-10T11:00:00+05:30
draft: true
topics: ["math", "ml"]
tags: ["interview", "building-block", "probability"]
summary: "From a weighted average to uncertainty in a sample mean: the role of covariance, conditional expectation, concentration bounds, and the distinct promises of the LLN and CLT."
references:
  - id: mit-probability
    text: 'Dimitri P. Bertsekas and John N. Tsitsiklis. "Introduction to Probability, Second Edition: Selected Summary Material." MIT OpenCourseWare, 2018.'
    url: https://ocw.mit.edu/courses/res-6-012-introduction-to-probability-spring-2018/d973b10c2587781f86ca4f2aff49098f_MITRES_6_012S18_Textbook.pdf
  - id: mit-limits
    text: 'MIT 18.655. "Limit Theorems," lecture notes, Spring 2016.'
    url: https://ocw.mit.edu/courses/18-655-mathematical-statistics-spring-2016/6c41b4096a836ff41f8de46cf54b5b7c_MIT18_655S16_LecNote15.pdf
  - id: psu-sampling
    text: 'Penn State STAT 555. "Numerical Summaries: Sampling Distribution of the Mean."'
    url: https://online.stat.psu.edu/stat555/node/34/
  - id: berkeley-bounds
    text: 'Philip B. Stark. "Statistics 240 Lecture Notes," section on Markov, Chebyshev, and Hoeffding inequalities. UC Berkeley, 2010.'
    url: https://www.stat.berkeley.edu/~stark/Teach/S240/Notes/ch1.pdf
---

When I average a metric over users, I want two answers: what quantity is the average trying to estimate, and how much should I trust the number I got? Expectation answers the first question. Variance, dependence, and sampling theory answer the second. The law of large numbers (LLN) and central limit theorem (CLT) are often quoted as if they were interchangeable assurances that “enough data fixes it.” They are more precise, and more useful, than that.

I will build the chain from one random variable to a sample mean. Along the way, a three-outcome example separates expectation from typical outcome, and a repeated-observation example shows why counting rows is not the same as counting independent evidence. The formulas also tell us exactly when familiar standard errors and tail bounds apply.

## Expectation is a weighted average

A random variable $X$ assigns a number to each possible outcome. If $X$ takes values $x_j$ with probabilities $p_j$, its expectation is

$$
\mathbb E[X]=\sum_jx_jp_j.
$$

For a continuous variable with density $f$, replace the sum with $\int x f(x)\,dx$. I need $\mathbb E[|X|]<\infty$ to call this a finite, well-defined mean. An apparently symmetric density can still have undefined expectation when positive and negative tails each contribute an infinite amount; canceling two infinities does not define a mean.

Consider a payoff $X$ that is $-1,0,2$ with probabilities $1/4,1/2,1/4$. Its expectation is $(-1)(1/4)+0(1/2)+2(1/4)=1/4$. That value is not one of the possible payoffs. It is the long-run target of an average under suitable repeated sampling, not a claim about what one trial will return. The payoff $0$ is the most likely single outcome, while $1/4$ balances the whole distribution.

Linearity is the first rule I would use in an interview:

$$
\mathbb E[aX+bY]=a\mathbb E[X]+b\mathbb E[Y].
$$

It does **not** require independence. It follows by distributing a sum or integral over the joint distribution, provided the expectations exist. If two teams record the same event twice, the expectation of the sum is still twice the event's expectation. Whether the records are independent matters when I ask about the *variance* of that sum. {{< cite "mit-probability" >}}

<figure class="ml-diagram">
<svg viewBox="0 0 860 230" role="img" aria-label="Expectation uses weighted outcomes; variance measures spread; covariance enters when outcomes are averaged together">
  <defs><marker id="ml-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>
  <rect class="box blue" x="35" y="60" width="230" height="85" rx="10"/>
  <text class="name" x="150" y="91">Expectation</text>
  <text class="note blue" x="150" y="119">weighted center</text>
  <rect class="box violet" x="315" y="60" width="230" height="85" rx="10"/>
  <text class="name" x="430" y="91">Variance</text>
  <text class="note violet" x="430" y="119">squared spread</text>
  <rect class="box green" x="595" y="60" width="230" height="85" rx="10"/>
  <text class="name" x="710" y="91">Sample mean</text>
  <text class="note green" x="710" y="119">spread also needs covariance</text>
  <line class="arrow" x1="268" y1="103" x2="309" y2="103"/>
  <line class="arrow" x1="548" y1="103" x2="589" y2="103"/>
</svg>
<figcaption>Knowing the center is not enough to know the uncertainty of an average.</figcaption>
</figure>

## Variance, covariance, and independence

With $\mu=\mathbb E[X]$, variance measures expected *squared* deviation:

$$
\operatorname{Var}(X)=\mathbb E[(X-\mu)^2]
=\mathbb E[X^2]-\mu^2.
$$

The first expression explains the idea; the second is often easier to calculate. For the payoff above, $\mathbb E[X^2]=1/4+4/4=5/4$, so $\operatorname{Var}(X)=5/4-(1/4)^2=19/16$. Its standard deviation is $\sqrt{19}/4\approx1.09$, back in payoff units. Variance has squared units. Adding a constant changes the mean but not the variance; multiplying by $a$ multiplies variance by $a^2$.

Covariance asks whether two deviations tend to move together:

$$
\operatorname{Cov}(X,Y)=\mathbb E[(X-\mathbb EX)(Y-\mathbb EY)],
\quad
\operatorname{Var}(X+Y)=\operatorname{Var}(X)+\operatorname{Var}(Y)+2\operatorname{Cov}(X,Y).
$$

Independent variables have zero covariance when the needed moments exist, but zero covariance does not imply independence. Let $X$ be uniform on $\{-1,0,1\}$ and let $Y=X^2$. Symmetry gives $\mathbb E[X]=\mathbb E[X^3]=0$, hence $\operatorname{Cov}(X,Y)=0$. Yet $Y$ is completely determined by $X$: learning $X=0$ tells us $Y=0$. Correlation, which rescales covariance by the two standard deviations, misses this nonlinear dependence too. {{< cite "mit-probability" >}}

This distinction enters every average. For $\bar X_n=n^{-1}\sum_{i=1}^nX_i$,

$$
\operatorname{Var}(\bar X_n)=\frac{1}{n^2}
\left(\sum_i\operatorname{Var}(X_i)+2\sum_{i<j}\operatorname{Cov}(X_i,X_j)\right).
$$

If observations are independent and each has variance $\sigma^2$, the covariance terms vanish, leaving $\sigma^2/n$. If every observation is an exact copy of the first, $\bar X_n=X_1$ and its variance never shrinks. Between those extremes, positive serial or within-group correlation reduces the amount of new information in each row. A convenient “effective sample size” can summarize this for a particular variance calculation, but there is no universal replacement of $n$ that works for every dependence pattern.

For a transparent special case, suppose every pair of distinct observations has the same correlation $\rho$ and every observation has variance $\sigma^2$. Then the formula becomes $\operatorname{Var}(\bar X_n)=\sigma^2[1+(n-1)\rho]/n$. This is not a model I would casually impose on real logs, but it shows why a small positive correlation matters when $n$ is large. If $\rho$ stays positive as $n$ grows, the variance approaches $\rho\sigma^2$ instead of zero. A variance formula cannot be repaired by simply collecting more copies of the same signal. Of course, a valid equal-correlation model constrains which negative values of $\rho$ are possible; the point here is the positive-correlation effect.

## Conditioning splits uncertainty into two pieces

Suppose $G$ labels a group. The conditional expectation $m(G)=\mathbb E[X\mid G]$ is a random variable: before seeing $G$, I do not know which group mean applies. The *tower property* says

$$
\mathbb E[X]=\mathbb E[\mathbb E[X\mid G]].
$$

For a discrete $G$, this is just $\sum_gP(G=g)\mathbb E[X\mid G=g]$. Conditioning first lets me solve an easier within-group problem, then average the group answers. It does not mean that $\mathbb E[X\mid G]$ equals $\mathbb E[X]$ for each group.

Variance has a matching decomposition:

$$
\operatorname{Var}(X)=
\mathbb E[\operatorname{Var}(X\mid G)]
+\operatorname{Var}(\mathbb E[X\mid G]).
$$

To see why, write $X-\mu=(X-m(G))+(m(G)-\mu)$ and square it. The cross term vanishes after conditioning on $G$ because $\mathbb E[X-m(G)\mid G]=0$. The remaining terms are average *within-group* variance and variance *between group means*. This proof is more useful than memorizing the names: it tells me what information a feature $G$ can explain. {{< cite "mit-probability" >}}

For a numerical check, let $G=0$ or $1$ with equal probability, and let $X\mid G=0$ be Bernoulli with success probability $0.2$, while $X\mid G=1$ has success probability $0.8$. The tower gives $\mathbb E[X]=(0.2+0.8)/2=0.5$. Each conditional variance is $0.2(0.8)=0.16$, and the two conditional means $0.2,0.8$ have variance $0.09$. Their sum is $0.25$, exactly the variance of a marginal Bernoulli$(0.5)$. The group reveals part of the uncertainty without changing the total.

There is also a prediction interpretation. If I must predict $X$ using only $G$ and squared-error loss, the best possible prediction is $m(G)=\mathbb E[X\mid G]$. Any alternative prediction $a(G)$ has expected squared error equal to $\mathbb E[\operatorname{Var}(X\mid G)]+\mathbb E[(m(G)-a(G))^2]$. The second term is a penalty for missing the conditional mean. The first is uncertainty left even with the best predictor using $G$. This does not make $G$ causal; it only describes what information it carries about $X$ under the joint distribution.

## LLN: an average settles near its mean

The *weak* law of large numbers says that for iid $X_i$ with finite $\mathbb E[|X_i|]$ and mean $\mu$, $\bar X_n$ converges **in probability** to $\mu$: for every $\varepsilon>0$,

$$
P(|\bar X_n-\mu|>\varepsilon)\longrightarrow0.
$$

This is a statement about the probability of a fixed-size error as sample size grows. It does not promise that every next observation is close to $\mu$, or that the running average moves monotonically toward it. A familiar proof under the stronger finite-variance assumption uses $\operatorname{Var}(\bar X_n)=\sigma^2/n$ and Chebyshev's inequality. More general iid laws of large numbers need only a finite absolute mean. {{< cite "mit-limits" >}}

Convergence in probability is deliberately modest. It says that if I repeat the *whole $n$-observation experiment*, the fraction of replications whose mean misses by more than a fixed tolerance tends to zero. It does not say that a single observed mean equals the population mean, and it gives no numerical sample-size threshold without more information. The strong law makes a different, almost-sure statement about an infinite sequence; the weak law is enough for the basic consistency claim here. In practice, I still need the data collection process to resemble the theorem's assumptions.

The caveat has teeth. A standard Cauchy random variable has no finite mean. The average of iid standard Cauchy variables is again standard Cauchy for every $n$; it does not concentrate around zero. The symmetric-looking center is not an expectation that LLN can recover. In other heavy-tailed models the mean may exist while variance does not, so an LLN may hold but the familiar $\sigma/\sqrt n$ CLT formula may fail. Do not use “heavy tail” as a single diagnosis: check which moment and theorem the argument needs. {{< cite "mit-limits" >}}

## CLT: the shape of repeated averages

The elementary central limit theorem assumes iid observations with finite mean $\mu$ and finite, positive variance $\sigma^2$. It says the *standardized sample mean* approaches a standard normal distribution:

$$
\frac{\bar X_n-\mu}{\sigma/\sqrt n}
\ \xrightarrow{\ d\ }\ \mathcal N(0,1).
$$

The LLN locates the average; the CLT describes the scale and approximate shape of its sampling fluctuations. Neither theorem says the raw $X_i$ become Gaussian. For a Bernoulli observation, the raw data remain zeros and ones at every sample size. The distribution of averages over many independent samples is what becomes approximately bell-shaped after centering and scaling. A normal population gives a normal sample mean even at $n=1$; a strongly skewed one can need far more than 30 observations for a useful approximation. There is no universal “$n=30$” switch. {{< cite "mit-limits" "psu-sampling" >}}

The standard deviation of the sampling distribution of $\bar X_n$ is its **standard error**, $\mathrm{SE}(\bar X_n)=\sigma/\sqrt n$ for iid finite-variance observations. The empirical standard deviation $s$ of the *individual observations* estimates $\sigma$; the plug-in standard error is $s/\sqrt n$. These are not interchangeable. If data are dependent, $s/\sqrt n$ generally misses the covariance terms above. If $\sigma$ is estimated, a confidence interval also needs its own conditions and a method appropriate to the design; the CLT alone is not a license to label every estimate “95% certain.”

For $n>1$, the familiar sample variance is $s^2=\sum_i(X_i-\bar X_n)^2/(n-1)$. Under iid sampling with finite variance, $s^2$ is unbiased for $\sigma^2$; $s$ itself is not generally an unbiased estimate of $\sigma$. The divisor $n-1$ addresses estimating the unknown center from the same observations. It does not compensate for serial correlation, selection bias, or a heavy tail without a finite second moment. Those are separate problems, even though they all appear later as uncertainty about an average.

| Question | LLN | CLT |
|---|---|---|
| What converges? | $\bar X_n$ to a constant $\mu$ | $(\bar X_n-\mu)/(\sigma/\sqrt n)$ to a distribution |
| Elementary iid assumptions here | finite absolute mean | finite positive variance |
| What does it help answer? | Does averaging stabilize? | How large and shaped are sampling errors? |
| What does it not say? | A finite-$n$ error rate by itself | Raw observations become normal |

## Bounds when a normal approximation is not the point

Markov's inequality starts with a nonnegative variable $Z$ and $a>0$. Since $Z\geq a$ on the event $Z\geq a$, $\mathbb E[Z]\geq aP(Z\geq a)$, hence

$$
P(Z\geq a)\leq\frac{\mathbb E[Z]}{a}.
$$

Apply that to $Z=(X-\mu)^2$ and $a=\varepsilon^2$ to obtain Chebyshev:

$$
P(|X-\mu|\geq\varepsilon)
\leq\frac{\operatorname{Var}(X)}{\varepsilon^2}.
$$

Chebyshev needs finite variance but no Gaussian shape. For an iid sample mean, substitute $\sigma^2/n$ on the right. It is usually conservative, but unlike a CLT approximation it is a finite-sample bound under its assumptions. {{< cite "berkeley-bounds" >}}

Bounded observations give a different guarantee. If $X_1,\ldots,X_n$ are independent and lie in $[0,1]$, Hoeffding's inequality gives

$$
P(|\bar X_n-\mathbb E\bar X_n|\geq\varepsilon)
\leq 2e^{-2n\varepsilon^2}.
$$

They need not have the same distribution for that form; for iid Bernoulli$(p)$, $\mathbb E\bar X_n=p$. To make the bound at most $\delta$, it suffices that $n\geq\log(2/\delta)/(2\varepsilon^2)$. For $\varepsilon=0.1$ and $\delta=0.05$, rounding up gives $n=185$. This is a conservative design bound on repeated independent samples, not a claim that a particular 185-observation dataset is accurate or that the observed error is known. Correlated clicks or repeated rows do not satisfy the independence premise. {{< cite "berkeley-bounds" >}}

## One reproducible simulation, three kinds of averages

The [NumPy script](sampling_means.py) draws 20,000 independent *replications* of each synthetic experiment with a fixed seed. Every raw draw is Bernoulli$(0.1)$, so the true mean is $0.1$ and variance is $0.09$. In the first two experiments, each replication averages $n$ independent draws. In the third, it draws 40 independent values and repeats each one five times, producing a row of 200 observations with only 40 independent blocks. All quantities labelled “MC” below are estimates from those 20,000 simulations; the “theory” column follows from the stated sampling process.

Here is the full experiment. Repeating columns creates dependence without changing any individual observation's Bernoulli distribution.

```python {title="sampling_means.py"}
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
```

```bash
python3 sampling_means.py
```

```text {title="Output"}
iid n=20: mean=0.10019, MC variance=0.004491, theory=0.004500, 5/95% quantiles=[0.  0.2]
iid n=200: mean=0.09989, MC variance=0.000448, theory=0.000450, 5/95% quantiles=[0.065 0.135]
5x repeated blocks, n=200: mean=0.10000, MC variance=0.002274, theory=0.002250, 5/95% quantiles=[0.025 0.175]
Hoeffding: n >= 185 gives P(|mean-p| >= 0.1) <= 0.05
```

Increasing independent $n$ from 20 to 200 divides theoretical variance by ten. Repeating each of 40 independent draws five times gives 200 displayed values but variance $0.09/40=0.00225$, five times the iid-$n=200$ variance. The two runs with 200 columns are not equally informative. The finite-simulation variances differ slightly from theory because Monte Carlo itself has error. The quantiles also show why a skewed Bernoulli mean at $n=20$ is a poor place to assume a smooth normal approximation blindly.

This same discipline matters in ML evaluation. If I average a per-user metric, the unit of independent sampling may be users, not events; many events from one user are related. If I compare models over validation folds, those folds may share training data. A standard error built as if every logged row were iid can be too small. The split and preprocessing questions in [cross-validation and data leakage](/blog/cross-validation-and-data-leakage/) matter before I attach uncertainty to the [metrics](/blog/ml-nlp-metrics/) those splits produce.

## Interview questions I would rehearse

1. **Does linearity of expectation require independent variables?** No. It follows from summing or integrating the joint distribution. Independence becomes relevant for simplifying products and covariance terms.

2. **Can expectation be a value the variable never takes?** Yes. The payoff $-1,0,2$ above has expectation $1/4$. Expectation is a weighted center, not the mode or a guaranteed outcome.

3. **Why square deviations in variance?** Squaring prevents positive and negative deviations from canceling and weights large deviations strongly. It also leads to useful algebra, including variance of a sum with covariance terms.

4. **Does zero covariance prove independence?** No. For symmetric $X\in\{-1,0,1\}$ and $Y=X^2$, covariance is zero while $Y$ is determined by $X$. Independence implies zero covariance when moments exist, not the reverse.

5. **What is the tower property?** Average a conditional mean over the conditioning variable: $\mathbb E[\mathbb E[X\mid G]]=\mathbb E[X]$. It is a way to solve a problem in stages.

6. **What are the two terms in total variance?** Expected within-group variance and variance of group means. Expanding $X-\mu=(X-m(G))+(m(G)-\mu)$ makes the cross term disappear after conditioning.

7. **Why is $\operatorname{Var}(\bar X)=\sigma^2/n$ sometimes wrong?** It assumes the covariance terms vanish and the observations have common variance. Repeated or correlated data can retain much more variance.

8. **How do LLN and CLT differ?** LLN says the average approaches its mean in probability under iid finite-mean assumptions. The elementary CLT describes the limiting normal law of its standardized fluctuations under iid finite positive variance.

9. **Does the CLT make the data normal at $n=30$?** No. It concerns repeated-sample means, not individual observations, and approximation quality depends on skew, tails, and the sampling design.

10. **What is the standard error of the sample mean?** For iid observations with population SD $\sigma$, it is $\sigma/\sqrt n$. If $\sigma$ is unknown, $s/\sqrt n$ is a plug-in estimate, not the raw-data SD $s$ itself.

11. **When would you use Chebyshev instead of a CLT approximation?** If I need a finite-sample bound from variance alone, without a normal-shape approximation. It may be loose but states its assumptions clearly.

12. **Can averaging rescue a Cauchy sample?** The standard Cauchy has no finite mean and its iid sample mean remains Cauchy. Neither the finite-mean LLN nor the finite-variance CLT used here applies.

{{< references >}}
