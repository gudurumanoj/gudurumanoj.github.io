---
title: "Bayesian Priors, Posteriors, and Predictive Distributions"
date: 2026-11-10T09:30:00+05:30
draft: true
topics: ["math", "ml"]
tags: ["building-block", "interview", "bayesian-inference"]
summary: "Bayes' rule as a probability update, from beta-binomial and normal conjugacy to prediction, prior sensitivity, and credible intervals."
references:
  - id: mit-conjugate
    text: 'MIT OpenCourseWare, 18.05. "Class 15: Conjugate Priors: Beta and Normal." 2022.'
    url: https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/resources/mit18_05_s22_lec15_pdf/
  - id: psu-bayes
    text: 'Penn State STAT 504. "Bayesian Inference for Categorical Data."'
    url: https://online.stat.psu.edu/onlinecourses/sites/stat504/files/lesson03/bayes.pdf
  - id: scipy-betabinom
    text: 'SciPy documentation. "scipy.stats.betabinom."'
    url: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.betabinom.html
  - id: cmu-credible
    text: 'Brian Junker, Carnegie Mellon University, 36-724. "Simulation, Conjugacy, Posterior Summaries." 2006.'
    url: https://www.stat.cmu.edu/~brian/724/week02/lec04-sim-conj.pdf
  - id: stan-ppc
    text: 'Stan User’s Guide. "Posterior and Prior Predictive Checks."'
    url: https://mc-stan.org/docs/stan-users-guide/posterior-predictive-checks.html
---

Bayesian inference is a rule for updating uncertainty about an unknown quantity when data arrive. It is especially clear when the likelihood and prior have compatible forms: I can see the entire posterior, not just a point estimate, and then use that distribution to predict new observations. The simple examples below are useful precisely because they expose the steps that larger Bayesian models still have to perform.

I will use a probability $p$ for repeated binary observations and then an unknown mean $\mu$ for Normal observations. The first example has a Beta prior; the second has a Normal prior. Both are **conjugate** updates, meaning the posterior belongs to the same distribution family as the prior. Conjugacy makes the algebra short. It is not a requirement of Bayes' rule. The [distribution guide](/blog/probability-distributions-properties/) defines these families; the [MLE/MAP discussion](/blog/naive-bayes-mle-map/) compares point estimates more generally.

## Bayes' rule is a normalized update

For parameter $\theta$ and data $D$, Bayes' rule for continuous $\theta$ is

$$
p(\theta\mid D)=\frac{p(D\mid\theta)p(\theta)}{p(D)},
\qquad p(D)=\int p(D\mid\theta)p(\theta)\,d\theta.
$$

The **prior** $p(\theta)$ describes uncertainty before these data. The **likelihood** $p(D\mid\theta)$ is the data model viewed as a function of $\theta$ with $D$ fixed. It need not integrate to one over $\theta$; it is not automatically a distribution for the parameter. The denominator, often called the **evidence** or marginal likelihood, makes the posterior integrate to one. For discrete parameters, the integral becomes a sum.

In a single-model update I often write $p(\theta\mid D)\propto p(D\mid\theta)p(\theta)$ and normalize later. That proportionality is safe only when the omitted factor does not depend on $\theta$. The evidence matters if I want actual posterior probabilities or compare fully specified models, and it depends on both the prior and the probability model for the data. A proper prior integrates to one; a proper likelihood and positive finite evidence then give a proper posterior. Some methods use improper priors, but they require extra care, especially for model comparison. I will keep the priors proper here.

The data model remains an assumption. If the observations are dependent, treating them as conditionally independent Bernoulli trials is an error that no elegant posterior formula repairs. The posterior is conditional on the chosen likelihood and prior, not a guarantee that either describes reality.

## A Beta prior and Bernoulli data

Let $X_i\mid p\overset{\mathrm{iid}}{\sim}\operatorname{Bernoulli}(p)$ and choose a prior $p\sim\operatorname{Beta}(\alpha,\beta)$, with $\alpha,\beta>0$. If $s$ of $n$ observations are successes and $f=n-s$ are failures, the likelihood for the ordered sequence is proportional to $p^s(1-p)^f$. For the aggregated count $S=s$, its binomial likelihood includes $\binom ns$; that factor is constant with respect to $p$, so both representations yield the same posterior:

$$
p(p\mid D)\propto p^s(1-p)^f\,p^{\alpha-1}(1-p)^{\beta-1}
=p^{\alpha+s-1}(1-p)^{\beta+f-1}.
$$

The normalized result is

$$
p\mid D\sim\operatorname{Beta}(\alpha+s,\beta+f).
$$

This is the Beta-binomial conjugate update. The posterior shape parameters add observed success and failure counts to prior shape parameters. Calling $\alpha$ and $\beta$ “pseudo-counts” can be a mnemonic, but I do not interpret every prior as literal previously observed data. The prior encodes a probability distribution, and its concentration $\alpha+\beta$ controls how strongly it affects the update. {{< cite "mit-conjugate" "psu-bayes" >}}

Take the illustrative prior $\operatorname{Beta}(2,2)$ and ten trials with seven successes and three failures. The posterior is $\operatorname{Beta}(9,5)$, with mean

$$
E[p\mid D]=\frac{9}{14}\approx0.642857,
\qquad
\operatorname{Var}(p\mid D)=\frac{9\cdot5}{14^2\cdot15}\approx0.015306.
$$

The raw sample proportion is $7/10=0.7$. The posterior mean lies between it and the prior mean $1/2$. I can write that mean as a weighted average:

$$
\frac{\alpha+s}{\alpha+\beta+n}
=\frac{\alpha+\beta}{\alpha+\beta+n}\frac{\alpha}{\alpha+\beta}
+\frac{n}{\alpha+\beta+n}\frac{s}{n},
$$

for $n>0$. This is exact algebra, not a claim that the data were literally enlarged by $\alpha+\beta$ observations. More data lower the relative weight of a fixed prior, but they do not fix a wrong likelihood.

## Mean, mode, and the boundary trap

The posterior **mean** $E[p\mid D]$ is $9/14$. The posterior **mode** (the MAP estimate) is $8/12=2/3$, because the mode of Beta$(a,b)$ is $(a-1)/(a+b-2)$ when **both** $a>1$ and $b>1$. The estimates answer different questions: the mean averages over parameter uncertainty; MAP chooses a density maximum. MAP is not automatically the best prediction of the next Bernoulli outcome.

The conditions on that mode formula matter. For Beta$(1,1)$, the density is flat: every point in $[0,1]$ is a mode, so a unique MAP does not exist. For Beta$(1,b)$ with $b>1$, the mode is at zero; for Beta$(a,1)$ with $a>1$, it is at one. When both shapes are below one, density rises without bound at both endpoints, and an interior formula is invalid. With continuous parameters, a mode is a density statement, not positive posterior probability at one exact $p$. This boundary behavior is one reason I would never apply the interior formula mechanically after zero or all-success observations. The [MLE/MAP article](/blog/naive-bayes-mle-map/) develops the optimization viewpoint separately.

The same observations also illustrate prior sensitivity:

| Prior | Posterior after $7$ successes and $3$ failures | Posterior mean |
|---|---|---:|
| Beta$(1,1)$ | Beta$(8,4)$ | $0.666667$ |
| Beta$(2,2)$ | Beta$(9,5)$ | $0.642857$ |
| Beta$(20,20)$ | Beta$(27,23)$ | $0.540000$ |

All three priors have mean $1/2$, but the last one is much more concentrated around it. With ten observations the difference remains material. The table is a sensitivity analysis for an illustrative dataset, not evidence that one prior is correct. I would choose priors from plausible values on the measurement scale and check their implications before fitting, especially when data are sparse.

{{< embed src="beta-update-demo.html" height="570" caption="Change the Beta prior and observed success/failure counts. The curves show uncertainty about the probability parameter, while the cards show predictive probabilities." >}}

The demo restricts prior shapes to positive integers at least one, keeping its plotted densities finite at the endpoints. The analytic formulas in the article apply to all positive shapes.

## Prediction integrates parameter uncertainty

The posterior is about $p$, while a posterior predictive distribution is about *future data*. For one new trial $X_{n+1}$,

$$
P(X_{n+1}=1\mid D)=\int_0^1 P(X_{n+1}=1\mid p)\,p(p\mid D)\,dp
=E[p\mid D]=\frac{a}{a+b},
$$

where $a=\alpha+s$ and $b=\beta+f$. For a single Bernoulli outcome, plugging in the posterior mean gives the same success probability. The difference appears when future outcomes share the same uncertain $p$. If $K$ counts successes in the next $m$ conditionally independent trials, then

$$
P(K=k\mid D)=\int_0^1\binom mk p^k(1-p)^{m-k}\operatorname{Beta}(p;a,b)\,dp
=\binom mk\frac{B(a+k,b+m-k)}{B(a,b)}.
$$

This is the **beta-binomial** predictive distribution. For $a=9,b=5$ and $m=2$, the probabilities for $K=0,1,2$ are $0.142857$, $0.428571$, and $0.428571$. In particular,

$$
P(K=2\mid D)=E[p^2\mid D]=\frac{a(a+1)}{(a+b)(a+b+1)}
=\frac{90}{210}\approx0.428571.
$$

Using one fixed plug-in probability $E[p\mid D]=9/14$ instead gives $(9/14)^2\approx0.413265$. The difference is exactly $\operatorname{Var}(p\mid D)$, since $E[p^2]=E[p]^2+\operatorname{Var}(p)$. Conditional on $p$, the future trials are independent; after integrating out a shared uncertain $p$, they are positively dependent. The beta-binomial formula is also implemented in SciPy, which I use as a check on the worked example. {{< cite "scipy-betabinom" >}}

The variance shows the same idea. Let $q=E[p\mid D]$. For the next $m$ trials,

$$
\operatorname{Var}(K\mid D)=m q(1-q)+m(m-1)\operatorname{Var}(p\mid D).
$$

The second term is zero for $m=1$ but grows for a batch: uncertainty about a shared rate makes extreme counts more likely than a Binomial$(m,q)$ plug-in model predicts. This is one concrete instance of the [law of total variance](/blog/expectation-variance-lln-clt/).

## Updates can arrive sequentially

If I see one success, Beta$(\alpha,\beta)$ becomes Beta$(\alpha+1,\beta)$. A following failure gives Beta$(\alpha+1,\beta+1)$. Under the same conditionally iid Bernoulli model, ten one-at-a-time updates with seven successes and three failures end at Beta$(\alpha+7,\beta+3)$ regardless of order. Multiplication of likelihood factors is commutative, and the Beta parameters keep the sufficient counts.

This coherence does **not** say that order never matters in real data. A time-varying $p$, adaptive collection, missingness depending on outcomes, or correlated observations changes the model and possibly the likelihood. In that setting, a model with a single static $p$ has thrown away relevant structure.

## A Normal prior for an unknown Normal mean

Conjugacy is not specific to proportions. Suppose $Y_i\mid\mu\overset{\mathrm{iid}}{\sim}N(\mu,\sigma^2)$ with **known** observation variance $\sigma^2$, and choose $\mu\sim N(\mu_0,\tau_0^2)$. Completing the square in $\mu$ yields a Normal posterior. It is cleanest to write it in precisions, which are reciprocal variances:

$$
\tau_n^{-2}=\tau_0^{-2}+n\sigma^{-2},
\qquad
\mu_n=\tau_n^2\left(\mu_0\tau_0^{-2}+n\bar y\sigma^{-2}\right).
$$

The posterior mean is a precision-weighted average of the prior mean and sample mean. More observations increase data precision $n/\sigma^2$; a tighter prior increases prior precision $1/\tau_0^2$. The **known-variance** assumption is essential to this exact Normal-Normal form. If $\sigma^2$ is also unknown, I need a joint prior and a different update. {{< cite "mit-conjugate" >}}

For $\mu_0=0$, $\tau_0^2=4$, $\sigma^2=1$, and illustrative observations $1,2,3$, posterior precision is $1/4+3=3.25$. Thus $\mu_n=6/3.25\approx1.846154$ and $\tau_n^2=1/3.25\approx0.307692$. For a new observation, the Normal posterior predictive distribution has mean $\mu_n$ and variance

$$
\operatorname{Var}(Y_{\mathrm{new}}\mid D)=\sigma^2+\tau_n^2
=1.307692.
$$

The first term is observation noise; the second is uncertainty about $\mu$. A plug-in prediction using only $\mu_n$ has variance one and misses the second term. This is the continuous counterpart of integrating over uncertain $p$. For a vector mean and covariance, the same precision logic extends through matrices; see [multivariate Gaussian conditioning](/blog/multivariate-gaussian-conditioning/).

## Intervals, checks, and limits

A **95% credible interval** for $p$ is an interval containing 95% of the posterior probability under the stated model and prior. For Beta$(9,5)$, the equal-tail interval is approximately $(0.385738,0.861421)$; each tail has posterior probability 2.5%. That statement conditions on the observed data. A **95% confidence interval** instead names a procedure whose intervals cover a fixed parameter in 95% of repeated samples under its assumptions; it is not generally a 95% posterior probability statement about this realized interval. They can coincide in special cases, but the interpretations differ. See [confidence intervals, bootstrap, and permutation](/blog/confidence-intervals-bootstrap-permutation/) for the repeated-sampling viewpoint. {{< cite "cmu-credible" >}}

A credible interval is only as meaningful as the likelihood and prior that produce it. I would compare plausible priors, look at the implied *prior predictive* distribution before seeing data, and compare replicated data from the *posterior predictive* distribution with observed features that matter: perhaps zeros, upper tails, or variation across groups. A posterior predictive check can flag a poor fit; it does not prove a model true, and reusing the data for fitting and checking affects how to interpret any check statistic. {{< cite "stan-ppc" >}}

Conjugate families are teaching tools and efficient computational choices, not a boundary on Bayesian modeling. In a nonconjugate model, the posterior may need numerical integration, approximation, or sampling such as Markov chain Monte Carlo. A sampler produces draws from a target posterior only when its algorithm and convergence conditions are handled adequately; it does not rescue an implausible data model. I prefer to carry the simple exact updates far enough to see what a more complex method must approximate: normalization, uncertainty over parameters, and integration for predictions.

A [runnable NumPy/SciPy example](bayes_examples.py) checks the Beta posterior and predictive PMF against SciPy, verifies a sequential update, computes an equal-tail interval, and performs the Normal precision update. The core calculation can be written without a sampler:

```python
from scipy.stats import beta, betabinom

a, b = 2 + 7, 2 + 3                 # Beta prior + observed counts
next_success = a / (a + b)        # 0.642857...
next_two = betabinom.pmf(2, 2, a, b)  # 0.428571...
interval = beta.ppf([.025, .975], a, b)
```

## Interview questions

**1. What is the difference between a likelihood and a posterior?** A likelihood is $p(D\mid\theta)$ viewed as a function of $\theta$ for fixed data and need not normalize over $\theta$. A posterior is a probability distribution over $\theta$, formed by multiplying likelihood and prior and dividing by the evidence.

**2. Why is the evidence an integral?** It sums or integrates over all parameter values that could produce the observed data: $p(D)=\int p(D\mid\theta)p(\theta)d\theta$. That normalization makes the posterior integrate to one. Its value depends on the prior as well as the likelihood.

**3. How do you derive the Beta-binomial update?** Multiply $p^s(1-p)^f$ by the Beta prior kernel $p^{\alpha-1}(1-p)^{\beta-1}$; the exponents become $\alpha+s-1$ and $\beta+f-1$. Normalization gives Beta$(\alpha+s,\beta+f)$.

**4. Is the Beta posterior mean always the MAP estimate?** No. The mean is $a/(a+b)$, while the interior mode is $(a-1)/(a+b-2)$ only when $a,b>1$. Boundary and uniform cases need their own analysis. For Beta$(9,5)$, they are about $0.643$ and $0.667$.

**5. Why can MAP be at a boundary despite zero probability at that exact value?** MAP maximizes a *density* for a continuous parameter. A density may peak or even diverge at an endpoint while the probability of the singleton endpoint remains zero. Modes and point probabilities are different objects.

**6. Does posterior uncertainty matter for one future Bernoulli trial?** Its marginal success probability is $E[p\mid D]$, exactly the posterior-mean plug-in value. Parameter uncertainty matters for joint predictions of several trials sharing $p$, producing extra dependence and count variance.

**7. What is the predictive probability of two successes under Beta$(a,b)$?** It is $E[p^2\mid D]=a(a+1)/[(a+b)(a+b+1)]$. Squaring $E[p\mid D]$ is smaller by $\operatorname{Var}(p\mid D)$ unless the posterior has zero variance.

**8. Can I update in any order?** Yes for a fixed prior and a conditionally iid likelihood: likelihood factors multiply, so the final Beta shapes depend only on total successes and failures. If the success probability changes over time or observations are dependent, that model must change.

**9. Why are Normal-Normal updates precision-weighted?** The prior and each Normal likelihood contribute quadratic terms in $\mu$; their coefficients are reciprocal variances. Completing the square adds those precisions, and the posterior mean weights each source by its precision.

**10. How does a posterior predictive interval differ from a credible interval?** A credible interval covers a parameter under the posterior. A posterior predictive interval covers a future observation under the predictive distribution, incorporating both parameter uncertainty and observation noise.

**11. Is a 95% credible interval a 95% confidence interval?** Not by definition. The former has 95% posterior probability conditional on the realized data and model. The latter comes from a repeated-sampling procedure with 95% coverage under its assumptions. Numerical intervals can sometimes match while their meanings differ.

**12. What should you check before trusting a conjugate result?** The sampling model, conditional independence, measurement scale, prior implications, and posterior predictive behavior. Exact algebra removes computational error but cannot validate the assumptions. If a nonconjugate model is needed, numerical methods introduce additional approximation and diagnostic questions.

{{< references >}}
