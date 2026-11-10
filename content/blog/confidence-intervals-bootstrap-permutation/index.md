---
title: "Confidence Intervals, Bootstrap, and Permutation Tests"
date: 2026-11-10T09:15:00+05:30
draft: true
topics: ["math", "ml"]
tags: ["building-block", "interview", "resampling"]
summary: "What a confidence interval covers, how bootstrap and permutation resampling answer different questions, and how dependence changes both procedures."
references:
  - id: nist-ci
    text: 'NIST/SEMATECH. "What are confidence intervals?" Engineering Statistics Handbook.'
    url: https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm
  - id: nist-t
    text: 'NIST/SEMATECH. "Confidence Limits for the Mean." Engineering Statistics Handbook.'
    url: https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm
  - id: scipy-ttest
    text: 'SciPy 1.11.4 documentation. "scipy.stats.ttest_ind."'
    url: https://docs.scipy.org/doc/scipy-1.11.4/reference/generated/scipy.stats.ttest_ind.html
  - id: scipy-bootstrap
    text: 'SciPy 1.11.4 documentation. "scipy.stats.bootstrap."'
    url: https://docs.scipy.org/doc/scipy-1.11.4/reference/generated/scipy.stats.bootstrap.html
  - id: efron-bca
    text: 'Bradley Efron. "Better Bootstrap Confidence Intervals." Journal of the American Statistical Association 82, 1987.'
    url: https://doi.org/10.1080/01621459.1987.10478410
  - id: scipy-permutation
    text: 'SciPy 1.11.4 documentation. "scipy.stats.permutation_test."'
    url: https://docs.scipy.org/doc/scipy-1.11.4/reference/generated/scipy.stats.permutation_test.html
  - id: phipson-smyth
    text: 'Belinda Phipson and Gordon K. Smyth. "Permutation P-values Should Never Be Zero." Statistical Applications in Genetics and Molecular Biology 9, 2010.'
    url: https://gksmyth.github.io/pubs/PermPValuesPreprint.pdf
---

An estimate answers “how much?” An uncertainty interval tells me how precisely the available data answer it. A test asks whether a chosen null model makes the observed statistic surprising. These are related questions, but I would not collapse them into one number. A small p-value can accompany a tiny effect; a broad interval can leave both benefit and harm plausible.

I will use the same two independent groups as in [the hypothesis-testing post](/blog/hypothesis-testing-p-values-power/) so the calculation has a concrete target: the difference in population means $\Delta=\mu_A-\mu_B$. First I will build a model-based interval. Then I will resample the observations two different ways. The bootstrap approximates an estimate's sampling variation; a permutation test constructs a reference distribution **under a null assignment rule**. The figure below makes their centers visibly different.

## What 95% coverage means

A confidence-interval procedure takes random data $X$ and returns endpoints $L(X),U(X)$. It has 95% coverage for a parameter $\theta$ under its model if

$$
P_{\theta}\{L(X)\le\theta\le U(X)\}=0.95
$$

or approximately 0.95 when the method is approximate. Imagine repeatedly sampling from the same population and constructing a fresh interval each time: about 95% of those intervals contain the fixed parameter. After I observe one sample, its numerical interval either contains that fixed parameter or it does not. A classical 95% interval is not a posterior statement that $\theta$ has a 95% probability of lying inside these particular endpoints. {{< cite "nist-ci" >}}

A **Bayesian credible interval** can express 95% probability for $\theta$ conditional on the observed data, because a posterior distribution treats the unknown parameter probabilistically. That probability depends on the likelihood and prior. Neither interpretation automatically makes an interval more useful if the sampling model is wrong. The [Bayesian priors and posteriors post](/blog/bayesian-priors-posteriors-predictive/) handles the posterior construction.

The word **standard deviation** usually describes variation among individual observations. **Standard error** describes variation of an estimator across repeated samples. For an independent sample mean with sample standard deviation $s$ and size $n$, the estimated standard error is $s/\sqrt n$. If observations are correlated, that formula can be too small because $n$ is no longer the effective count of independent pieces of information. The distinction is why a plot of raw values and an interval around their mean show different uncertainty.

## Model-based t intervals

For independent observations $x_1,\ldots,x_n$ from an approximately normal population with unknown variance, the familiar two-sided mean interval is

$$
\bar x\ \pm\ t_{1-\alpha/2,n-1}\frac{s}{\sqrt n}.
$$

Here $s$ uses $n-1$ in its sample-variance denominator. The $t$ critical value accounts for estimating the standard deviation; it is wider than the corresponding normal critical value for small $n$. Exact coverage needs the normal sampling model. In larger, well-behaved samples it can serve as an approximation, but skewness, heavy tails, selection, or dependence can defeat a casual appeal to “large enough.” {{< cite "nist-t" >}}

For two **independent** samples, the Welch interval for the difference in population means is

$$
(\bar x_A-\bar x_B)\ \pm\ t_{1-\alpha/2,\nu}
\sqrt{\frac{s_A^2}{n_A}+\frac{s_B^2}{n_B}},
$$

where $\nu$ is the Welch–Satterthwaite approximate degrees of freedom given in the [test derivation](/blog/hypothesis-testing-p-values-power/). It does not require equal population variances, though it still requires independent sampling units and a suitable approximation for the means. SciPy exposes the same interval through `ttest_ind(..., equal_var=False).confidence_interval()`. {{< cite "scipy-ttest" >}}

The [runnable file](resampling_demo.py) uses A $=[12,11,13,12,14,10,13,15]$ and B $=[10,11,12,10,9,13,8,12,11,13,9,11]$. Here $\bar x_A-\bar x_B=1.75$, the estimated standard error is $0.7317$, and $\nu=15.1506$. The 95% Welch interval is **$(0.1917,3.3083)$ outcome units**. It excludes zero, matching the two-sided Welch test's $p=0.030175$ at level 0.05 because they invert the *same* reference distribution. That correspondence is not a promise that every interval and every test with similar labels must agree.

If each observation in A is matched to one in B, I instead form differences $d_i=x_{A,i}-x_{B,i}$ and make a one-sample $t$ interval for their mean: $\bar d\pm t_{1-\alpha/2,n-1}s_d/\sqrt n$. In the attached example, six paired differences are $[2,3,0,4,1,5]$, giving a mean of $2.5$ and a 95% paired interval $(0.5367,4.4633)$. Treating the two columns as independent would discard the design and generally change the uncertainty estimate. Pairing is about the unit of random variation, not just matching array lengths.

## Bootstrap: resample to approximate estimator variation

The nonparametric bootstrap uses the empirical data distribution as a stand-in for the population. To estimate uncertainty for the independent-group mean difference, I sample $n_A$ observations **with replacement from A** and $n_B$ **with replacement from B**, then recalculate the difference. Repeating that $B$ times gives bootstrap estimates $\hat\Delta_1^*,\ldots,\hat\Delta_B^*$. The sample standard deviation of those estimates approximates the estimator's standard error. The **percentile interval** takes, for example, their 2.5th and 97.5th percentiles for a nominal 95% interval. {{< cite "scipy-bootstrap" >}}

On these observations with 20,000 seeded resamples, the percentile interval is **$(0.4167,3.0833)$**. It is different from Welch's $(0.1917,3.3083)$ because the procedures use different approximations. Neither interval becomes “validated” by being narrower. In small samples, the empirical distribution may omit important tail behavior; percentile intervals can have poor coverage for skewed or biased estimators, boundary parameters, or nonsmooth statistics such as extrema. A bootstrap cannot manufacture information missing from the data. For example, a resampled maximum can never exceed the observed maximum, even though the population may generate larger future observations; this boundary needs more care than an ordinary smooth mean estimate. {{< cite "scipy-bootstrap" >}}

The **BCa** interval adjusts percentile cutoffs for estimated bias and acceleration (a measure of how the estimate changes across observations). It often improves coverage but is still approximate, can fail for degenerate bootstrap distributions, and still needs a resampling scheme that respects the data. SciPy provides `method="BCa"`; its documentation calls out degenerate cases. The original method is due to Efron. {{< cite "efron-bca" "scipy-bootstrap" >}}

<figure class="ml-diagram">
<svg viewBox="0 0 860 220" role="img" aria-label="Bootstrap samples within groups; permutation reassigns labels across pooled observations">
  <defs><marker id="ml-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>
  <rect class="box violet" x="25" y="20" width="245" height="68" rx="8"/><text class="name" x="147" y="53">Observed A and B</text><text class="note violet" x="147" y="75">estimate: A mean − B mean</text>
  <rect class="box green" x="350" y="20" width="470" height="70" rx="8"/><text class="name" x="585" y="53">Bootstrap, with replacement</text><text class="note green" x="585" y="75">draw A from A, B from B</text>
  <rect class="box blue" x="350" y="128" width="470" height="70" rx="8"/><text class="name" x="585" y="161">Permutation, without replacement</text><text class="note blue" x="585" y="183">pool, then reassign A/B labels</text>
  <line class="arrow" x1="274" y1="54" x2="345" y2="54"/>
  <path class="arrow" d="M147,92 V162 H345"/>
</svg>
<figcaption>The bootstrap keeps group identities to estimate variation around the observed difference. Permutation erases them to ask what differences occur under exchangeable labels.</figcaption>
</figure>

The [runnable Python file](resampling_demo.py) makes both distributions and generates the figure below. Its core is short:

```python {title="Core resampling steps"}
rng = np.random.default_rng(2026)
B, M = 20000, 9999
ia = rng.integers(len(a), size=(B, len(a)))
ib = rng.integers(len(b), size=(B, len(b)))
boot = a[ia].mean(axis=1) - b[ib].mean(axis=1)
percentile_ci = tuple(np.quantile(boot, [0.025, 0.975]))

pool = np.concatenate([a, b])
permuted = np.empty(M)
for i in range(M):
    shuffled = rng.permutation(pool)
    permuted[i] = shuffled[:len(a)].mean() - shuffled[len(a):].mean()
extreme = np.count_nonzero(np.abs(permuted) >= abs(observed) - 1e-12)
mc_p = (extreme + 1) / (M + 1)
```

The small tolerance is for floating-point comparisons at a theoretically tied boundary. For a production analysis I would inspect the statistic and ties instead of assuming an arbitrary tolerance is always appropriate. The complete file includes the source arrays, model-based intervals, an exhaustive small permutation calculation, assertions, and figure generation.

{{< figure src="resampling-distributions.svg" caption="Bootstrap mean differences cluster around the observed 1.75; dashed lines mark percentile endpoints. Permuted differences cluster near zero under exchangeable labels; vertical lines mark the observed statistic and its opposite tail. This is seeded simulated output, not measured data." >}}

## Permutation: build a null distribution

An independent-sample permutation test pools observations, assigns $n_A$ of them to A and the rest to B, and recomputes the statistic. If assignment is randomized or observations are exchangeable under the null, each allowed labeling has the appropriate null probability. This is a **null** distribution, unlike the bootstrap distribution centered near the observed estimate. For our statistic, I count assignments with $|\hat\Delta^{\pi}|\ge|1.75|$. {{< cite "scipy-permutation" >}}

The observed samples admit ${20\choose8}=125{,}970$ distinct group assignments. The script draws 9,999 randomized assignments, finds 381 at least as extreme, and reports the common Monte Carlo correction $(381+1)/(9999+1)=0.0382$. Adding the observed arrangement prevents an estimated p-value of zero and makes the randomized-test calculation conservative under the usual exchangeability setup. The exact conditional p-value would count all 125,970 assignments, **including** the observed arrangement, and divide by 125,970; it does not use a plus-one correction on top of exhaustive enumeration. See Phipson and Smyth for the finite-permutation reasoning. {{< cite "phipson-smyth" >}}

A tiny exhaustive example shows the distinction without simulation. Take A $=[7,8,9]$ and B $=[1,2,3]$. There are ${6\choose3}=20$ possible assignments of three values to A. Exactly two assignments produce an absolute mean difference at least as large as the observed $6$, so the two-sided exact permutation p-value is $2/20=0.10$. With only three observations per group, this particular exact two-sided procedure cannot return a smaller p-value, even though the samples do not overlap.

**Exchangeability is the key assumption.** Under a null of identical independent distributions, shuffling labels is justified. A randomized experiment under a sharp no-effect null also gives a randomization interpretation based on its assignment mechanism. A bare null of equal means, with different variances or different shapes, does not generally make individual observations exchangeable; simply permuting raw labels can then miscalibrate a mean-difference test. This is a reason to separate the Welch model-based calculation from the permutation calculation rather than treat their p-values as two implementations of one test.

## Resample the unit that was sampled

For paired measurements, bootstrap whole **pairs** or their differences, not each column independently. For a paired permutation test under a justified within-pair exchangeability null, swap A and B within pairs (equivalently, flip difference signs). Shuffling across people would break the pairing and test a different experiment. SciPy distinguishes independent, within-pair sample swaps, and pairings used for association tests. {{< cite "scipy-bootstrap" "scipy-permutation" >}}

For clustered data, resample or randomize at the cluster level if clusters are the independent assignment units. Sampling individual events from the same user as if they were independent makes intervals too optimistic. For time series, a naive shuffle destroys temporal structure; block or model-based resampling may preserve relevant dependence, and a time-directed experiment needs its actual assignment rule. The right scheme follows the data-generating process. The [cross-validation and leakage post](/blog/cross-validation-and-data-leakage/) applies the same logic to model evaluation splits.

Resampling also cannot fix biased recruitment, unrecorded confounding, or an estimand that changed after seeing the results. A narrow interval around the wrong target is still the wrong answer.

## Report the estimate and the design

For this example I would say: “The estimated independent-group mean difference A minus B is $1.75$ outcome units; the 95% Welch interval is $(0.19,3.31)$ under independent sampling and the Welch approximation.” If I also report a permutation p-value, I would state that its null assumes exchangeable labels, give the statistic, number of permutations, and Monte Carlo method. I would not silently swap one interval or p-value for another until a preferred result appears.

The interval shows a range of effects compatible with a model and procedure. Deciding whether that range is useful requires the outcome's units and a threshold for a meaningful change. Confidence intervals add information beyond a yes/no decision, but they do not replace thinking about the design.

## Interview questions and follow-ups

**1. What does a 95% confidence interval mean?** The procedure covers the fixed parameter in about 95% of repeated samples under its assumptions. It is not a 95% posterior probability for the parameter given this sample.

**2. How does a credible interval differ?** It summarizes a posterior probability distribution conditional on data, likelihood, and prior. Its interpretation is probabilistic about the parameter within that model.

**3. What is the difference between SD and SE?** SD describes spread among observations; SE describes sampling variation of an estimator. For independent observations, the mean's estimated SE is $s/\sqrt n$.

**4. When use a t critical value instead of z?** For the classic normal-sample mean interval when population variance is unknown and estimated from the sample. The $t$ reference accounts for that extra uncertainty.

**5. Why use Welch for two independent means?** It allows unequal group variances and uses a corresponding approximate degrees of freedom. It still needs the sampling units to be independent and the mean approximation to be suitable.

**6. What does the percentile bootstrap interval do?** It resamples observations under the chosen sampling design, recalculates an estimate repeatedly, and takes specified quantiles of those bootstrap estimates. It is approximate, not universally reliable.

**7. What does BCa change?** It adjusts bootstrap percentile cutoffs for estimated bias and acceleration. It can improve coverage in suitable settings but can fail with degenerate distributions or an invalid resampling design.

**8. Why is permutation different from bootstrap?** Bootstrap samples with replacement to approximate estimator variation around the observed data; permutation reassigns observations under a null exchangeability rule to make a null distribution.

**9. Can I permute to test equal means if variances differ?** Not automatically. Equality of means alone need not make raw observations exchangeable. The assignment mechanism or a stronger distributional null must justify the permutation scheme.

**10. Why add one to a Monte Carlo permutation p-value?** The observed assignment is an attainable null configuration. The simple $(b+1)/(M+1)$ correction avoids zero p-values and accounts for finite random sampling; exhaustive enumeration instead divides the full extreme count by the full number of assignments.

**11. How do paired or clustered samples change resampling?** Keep the unit intact: resample pairs or clusters, and randomize only at levels allowed by the null design. Breaking dependence can make uncertainty estimates misleading.

**12. What would you report with an interval?** The estimand and units, point estimate, interval method and level, sample sizes, independence or dependence structure, and any sensitivity to modeling choices. A number without its sampling design is hard to interpret.

{{< references >}}
