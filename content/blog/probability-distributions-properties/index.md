---
title: "Probability Distributions: Properties That Actually Help You Choose One"
date: 2026-11-10T09:00:00+05:30
draft: true
topics: ["math", "ml"]
tags: ["building-block", "interview", "probability"]
summary: "A practical map from counts, waiting times, proportions, and test statistics to distributions, with the assumptions and transformations behind the formulas."
references:
  - id: psu-discrete
    text: 'Penn State STAT 504. "Lesson 1: Introduction to Discrete Data."'
    url: https://online.stat.psu.edu/stat504/Lesson01
  - id: psu-gamma
    text: 'Penn State STAT 414. "Lesson 15: Exponential, Gamma and Chi-Square Distributions."'
    url: https://online.stat.psu.edu/stat414/Lesson15
  - id: psu-t
    text: 'Penn State STAT 414. "Lesson 26: Random Functions Associated with Normal Distributions."'
    url: https://online.stat.psu.edu/stat414/Lesson26
  - id: nist-t
    text: 'NIST/SEMATECH. "Student t Distribution," Engineering Statistics Handbook.'
    url: https://itl.nist.gov/div898/handbook/eda/section3/eda3664.htm
  - id: scipy-t
    text: 'SciPy documentation. "scipy.stats.t."'
    url: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html
  - id: scipy-gamma
    text: 'SciPy documentation. "scipy.stats.gamma."'
    url: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.gamma.html
  - id: mit-poisson
    text: 'MIT OpenCourseWare, 6.041SC. "Poisson Processes," Lecture 14.'
    url: https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/9135c378ced3fd5f2709ab80d7d67818_MIT6_041SCF13_L14.pdf
---

A distribution is more than a familiar curve. It says what values a variable can take, how probability is allocated over those values, and which assumptions connect the variable to a process. When someone says “the average is three,” I still cannot tell whether the variable counts successes in twelve trials, counts arrivals in an interval, or measures the time until a third arrival. Those models can have the same mean and very different tails.

I find it more useful to ask four questions first: **What is the support? What is being counted or measured? What remains fixed across repetitions? Which aspects of the process are plausible?** The name of a distribution should be an answer to those questions, not a starting incantation.

## The probability object comes first

For a discrete random variable, a **probability mass function** (PMF) assigns a probability to each possible value: $p(k)=P(X=k)$, with $p(k)\geq0$ and $\sum_k p(k)=1$. For a continuous random variable, a **probability density function** (PDF) satisfies $f(x)\geq0$ and integrates to one. Probability is an *area*:

$$
P(a<X\leq b)=\int_a^b f(x)\,dx.
$$

A density may exceed one; it has units of inverse $x$-units. The probability of one exact value is zero for a continuous distribution, so $f(2)$ is not $P(X=2)$. The **CDF**, $F(x)=P(X\leq x)$, works for both discrete and continuous variables; it is nondecreasing and approaches zero and one at the two ends. The **survival function**, $S(x)=P(X>x)=1-F(x)$, is natural for “has the event happened yet?” questions. In numerical software, a direct survival-function implementation can be more accurate than subtracting a CDF very close to one.

Support matters just as much as shape. A Normal model can produce negative values. A Beta variable cannot leave $[0,1]$. A Poisson variable is a nonnegative integer. Parameters specify a member of a family *after* the family and its conventions are clear. “Gamma$(3,2)$” is ambiguous unless I say whether $2$ is a rate or a scale. The table below uses **rate** throughout.

## Counts and categories

These families answer different questions even when their outputs look like integers. The Bernoulli, binomial, categorical, multinomial, and Poisson definitions here follow their standard counting experiments. {{< cite "psu-discrete" >}}

| Family | Support and parameters | Process or useful properties |
|---|---|---|
| Bernoulli$(p)$ | $x\in\{0,1\}$, $0\leq p\leq1$ | One success indicator; $E[X]=p$, $\operatorname{Var}(X)=p(1-p)$. |
| Binomial$(n,p)$ | $k=0,\ldots,n$; integer $n\geq0$, $0\leq p\leq1$ | Successes in $n$ independent, equal-$p$ Bernoulli trials; mean $np$, variance $np(1-p)$. |
| Categorical$(p_1,\ldots,p_c)$ | One label from $c$ categories, $p_j\geq0$, $\sum_jp_j=1$ | One draw; the indicator for category $j$ has mean $p_j$. A category label is not inherently a numerical measurement. |
| Multinomial$(n,\boldsymbol p)$ | Count vector $\boldsymbol k$, $\sum_jk_j=n$; integer $n\geq0$, $p_j\geq0$, $\sum_jp_j=1$ | Counts from $n$ independent categorical draws; $E[K_j]=np_j$, $\operatorname{Cov}(K_i,K_j)=-np_ip_j$ for $i\ne j$. |
| Poisson$(\lambda)$ | $k=0,1,\ldots$, $\lambda>0$ | Events in a fixed interval under a homogeneous Poisson-process model; mean and variance both $\lambda$. |
| Geometric$(p)$ | $k=1,2,\ldots$, $0<p\leq1$ | **Number of trials through the first success**; $P(X=k)=(1-p)^{k-1}p$, mean $1/p$, variance $(1-p)/p^2$. |

The geometric convention deserves attention. Some books define $Y$ as *failures before* the first success, so $Y=X-1$ has support $0,1,\ldots$ and mean $(1-p)/p$. The two conventions describe the same experiment but shift every answer by one. I state mine before doing arithmetic.

The binomial assumption is stronger than “I counted successes.” It requires a fixed number of independent trials with the same $p$. Counts per hour are not automatically Poisson either: a Poisson process assumes a constant rate, independent increments, and suitable behavior over short intervals. If counts are clustered or the rate changes, the variance can differ substantially from the mean. Observing mean approximately equal to variance is a clue, not proof of the process.

There is a clean bridge between binomial and Poisson. Suppose $X_n\sim\operatorname{Binomial}(n,\lambda/n)$, so the expected count stays at $\lambda$ while each trial becomes rare. For fixed $k$,

$$
P(X_n=k)=\frac{n(n-1)\cdots(n-k+1)}{k!}\left(\frac{\lambda}{n}\right)^k\left(1-\frac{\lambda}{n}\right)^{n-k}
\longrightarrow e^{-\lambda}\frac{\lambda^k}{k!}.
$$

The first product contributes $\lambda^k/k!$ in the limit and the last factor contributes $e^{-\lambda}$. This is a *rare-event limit*, not a statement that every binomial is well approximated by a Poisson. The binomial variance $\lambda(1-\lambda/n)$ approaches $\lambda$ as well. It also explains the left panel below: Binomial$(12,0.25)$ and Poisson$(3)$ both have mean $3$, but their variances are $2.25$ and $3$.

## Waiting times, proportions, and real-valued measurements

The continuous families are easier to remember if I group them by role. In the Gamma row I use shape $a$ and rate $\lambda$, meaning scale $\theta=1/\lambda$; SciPy's `gamma` uses `scale`, so the code passes `scale=1/rate`. {{< cite "psu-gamma" "scipy-gamma" >}}

| Family | Support and parameters | Mean and variance, when defined |
|---|---|---|
| Uniform$(a,b)$ | $a\leq x\leq b$, $a<b$; constant density $1/(b-a)$ | $(a+b)/2$; $(b-a)^2/12$. |
| Exponential$(\lambda)$ | $t\geq0$, rate $\lambda>0$; density $\lambda e^{-\lambda t}$ | $1/\lambda$; $1/\lambda^2$. |
| Gamma$(a,\lambda)$ | $t>0$, shape $a>0$, **rate** $\lambda>0$ | $a/\lambda$; $a/\lambda^2$. Shape $1$ is Exponential$(\lambda)$. |
| Beta$(a,b)$ | $0<x<1$, $a,b>0$ | $a/(a+b)$; $ab/[(a+b)^2(a+b+1)]$. Endpoint behavior depends on shapes. |
| Normal$(\mu,\sigma^2)$ | $x\in\mathbb R$, $\sigma>0$ | $\mu$; $\sigma^2$. |
| Lognormal$(\mu,\sigma^2)$ | $x>0$ when $\log X\sim N(\mu,\sigma^2)$ | $e^{\mu+\sigma^2/2}$; $(e^{\sigma^2}-1)e^{2\mu+\sigma^2}$. |
| Student $t_\nu$ | $x\in\mathbb R$, degrees of freedom $\nu>0$ | Mean $0$ only if $\nu>1$; variance $\nu/(\nu-2)$ only if $\nu>2$. |
| Chi-square $\chi^2_\nu$ | $x\geq0$, $\nu>0$ | $\nu$; $2\nu$. It is Gamma(shape $\nu/2$, rate $1/2$). |

A Beta distribution models an unknown probability or a random proportion, but it is not the distribution of a binary observation itself. A Bernoulli observation is zero or one; a Beta-distributed parameter is continuous between zero and one. This separation becomes central in [Bayesian priors and posteriors](/blog/bayesian-priors-posteriors-predictive/). A Normal is a convenient additive-noise model, while a lognormal is often a candidate for strictly positive quantities created by multiplicative effects. Neither is automatically justified by the sign of the data alone.

The chi-square and Student $t$ families also arise as *sampling distributions*, not just as possible raw-data shapes. If $Z\sim N(0,1)$ and $U\sim\chi^2_\nu$ are independent, then $Z/\sqrt{U/\nu}\sim t_\nu$. The random denominator makes the tails heavier than Normal tails. The mean fails to exist for $\nu\leq1$; the variance fails to be finite for $\nu\leq2$. Thus a table that simply prints “variance $\nu/(\nu-2)$” without a condition is misleading. {{< cite "psu-t" "nist-t" >}} {{< cite "scipy-t" >}}

## Why the exponential forgets

For $T\sim\operatorname{Exponential}(\lambda)$, the survival function is $S(t)=e^{-\lambda t}$. Therefore, for $s,t\geq0$,

$$
P(T>s+t\mid T>s)=\frac{S(s+t)}{S(s)}=e^{-\lambda t}=P(T>t).
$$

Surviving $s$ units of time does not change the distribution of the *additional* wait. This memoryless property is precise; it does not mean waiting time is predictable. It is appropriate when the event rate is constant in the process model. If a machine ages or demand follows a daily cycle, the assumption deserves scrutiny.

A sum of $m$ independent Exponential$(\lambda)$ waits follows Gamma$(m,\lambda)$: the wait for the $m$th event in a homogeneous Poisson process. With $m=3$ and $\lambda=3$, its mean is one, just like Exponential$(1)$, but its variance is $1/3$ rather than one. The Gamma density initially rises from zero because three events cannot usually occur instantly. The exponential density is highest at time zero. These are different process stories, visible in the middle panel. {{< cite "mit-poisson" >}}

## Transformations explain shapes

A transformation can change support, units, and density. For a smooth, one-to-one transformation $Y=g(X)$, a density must account for how intervals stretch:

$$
f_Y(y)=f_X(g^{-1}(y))\left|\frac{d}{dy}g^{-1}(y)\right|.
$$

The absolute derivative is the one-dimensional **Jacobian**. If $Z\sim N(\mu,\sigma^2)$ and $Y=e^Z$, then $z=\log y$ and $dz/dy=1/y$. Thus $Y$ is lognormal with $f_Y(y)=f_Z(\log y)/y$ for $y>0$. Omitting $1/y$ would not preserve probability. A Normal transformed affinely instead remains Normal: $aZ+b\sim N(a\mu+b,a^2\sigma^2)$ for $a\ne0$. The variance uses $a^2$, even when $a$ is negative.

The lognormal's parameters $\mu$ and $\sigma$ describe $\log Y$, not the mean and standard deviation of $Y$. Using the Normal exponential moment $E[e^{tZ}]=e^{\mu t+\sigma^2t^2/2}$ gives

$$
E[Y]=e^{\mu+\sigma^2/2},\qquad
\operatorname{Var}(Y)=E[e^{2Z}]-E[e^Z]^2=(e^{\sigma^2}-1)e^{2\mu+\sigma^2}.
$$

For $\mu=0$ and $\sigma=0.5$, the mean is about $1.133$, not $e^0=1$. The latter is the median. This difference is a compact reminder that transformation and expectation do not generally commute.

## Compare quantities, then inspect the fit

{{< figure src="distribution-comparison.svg" caption="Analytic PMFs and PDFs with matched means in the first two panels. The third compares a standard Normal with a Student t distribution with three degrees of freedom. Curves are model calculations, not fitted data." width="100%" >}}

The tails can matter more than the center. Here $P(X\geq5)$ is about $0.157644$ for the binomial count and $0.184737$ for the Poisson count. For $|X|>3$, the standard Normal probability is about $0.002700$, while $t_3$ gives about $0.057669$. I would not choose a distribution by matching one summary statistic, or by declaring that all bell-shaped observations are Normal.

The figure and numbers come from a [runnable Python file](distribution_examples.py) using NumPy, SciPy, and Matplotlib. Its core comparison is small:

```python
from scipy.stats import binom, poisson, expon, gamma

print(binom.mean(12, .25), binom.var(12, .25))  # 3.0, 2.25
print(poisson.mean(3), poisson.var(3))           # 3.0, 3.0
print(expon.var(scale=1))                       # 1.0
print(gamma.var(a=3, scale=1/3))                # 1/3: rate is 3
```

When I fit a family to data, I check its support, process assumptions, and the quantities the decision actually uses: perhaps a survival probability, upper quantile, zero rate, or predictive interval. Histograms and empirical CDFs help reveal gross mismatch; residual or posterior predictive checks probe the model more directly. A distribution is a model of uncertainty under assumptions, not a certification that the physical process generated data exactly that way. [Expectation and variance](/blog/expectation-variance-lln-clt/) then tell me which summaries are stable, and [confidence intervals and resampling](/blog/confidence-intervals-bootstrap-permutation/) address uncertainty in estimates from finite data.

## Interview questions

**1. Can a PDF value be larger than one?** Yes. A density is probability per unit of $x$, and only its integral over an interval is a probability. Uniform$(0,0.1)$ has density $10$ on its support and total area one.

**2. How do PMF, PDF, CDF, and survival function differ?** A PMF gives point probabilities on discrete support. A PDF integrates to interval probabilities on continuous support. The CDF is $P(X\leq x)$ for either kind, and the survival function is $P(X>x)=1-F(x)$. For mixed distributions, a CDF still works even when one PDF does not describe all mass.

**3. When is a binomial count approximately Poisson?** In a rare-event regime with large $n$, small $p$, and moderate $np=\lambda$, the binomial PMF approaches Poisson$(\lambda)$. The exact limit keeps $\lambda$ fixed while $n\to\infty$ and $p=\lambda/n$. It is not an automatic approximation for an arbitrary $n,p$.

**4. Why can the Poisson variance equal its mean?** Its PMF yields both $E[X]$ and $\operatorname{Var}(X)$ equal to $\lambda$. In a homogeneous Poisson process this corresponds to independent event increments at a constant rate. A dataset with overdispersion suggests checking those assumptions or another count model.

**5. What does “geometric waiting time” count?** I use trials through first success, so support starts at one and mean is $1/p$. If someone uses failures before first success, support starts at zero and mean is $(1-p)/p$. State the convention.

**6. What is special about an exponential wait?** It is memoryless: conditional on still waiting at time $s$, the additional wait has the original Exponential$(\lambda)$ distribution. Its survival ratio proves this. General Gamma waits are not memoryless.

**7. How is Gamma related to chi-square?** Chi-square with $\nu$ degrees of freedom is Gamma with shape $\nu/2$ and rate $1/2$ (scale $2$). This yields mean $\nu$ and variance $2\nu$. Parameter conventions must be stated before comparing implementations.

**8. Is a Beta distribution the same as a Bernoulli distribution with a Beta prior?** No. Beta describes a continuous probability parameter $p$. Conditional on $p$, a Bernoulli observation is binary. Combining them yields a posterior distribution for $p$ after observing outcomes.

**9. Why does exponentiating a Normal require a Jacobian?** Exponentiation stretches intervals unevenly. Since $z=\log y$, a small $dy$ corresponds to $dz=dy/y$; hence $f_Y(y)=f_Z(\log y)/y$. That factor preserves probability and produces the lognormal density.

**10. Does Student $t$ always have a mean and variance?** No. A standard $t_\nu$ has mean zero only for $\nu>1$, and finite variance $\nu/(\nu-2)$ only for $\nu>2$. Its heavier tails are particularly consequential at low degrees of freedom.

**11. If two distributions have the same mean, are their tail probabilities close?** No. Binomial$(12,.25)$ and Poisson$(3)$ have mean three but different variances and upper tails. Comparing the quantity relevant to the decision is more informative than matching only a mean.

**12. What would make you reject a familiar family?** Impossible support, systematic mismatch in zeros or tails, or violated process assumptions. For example, a Normal cannot be a literal model for nonnegative counts, and a constant-rate Poisson process is doubtful if event intensity changes sharply over time.

{{< references >}}
