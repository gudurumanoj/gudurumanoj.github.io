---
title: "Hypothesis Testing: p-values, Power, and Choosing a Test"
date: 2026-11-10T09:00:00+05:30
draft: true
topics: ["math", "ml"]
tags: ["building-block", "interview", "hypothesis-testing"]
summary: "Build a hypothesis test from an estimand and sampling model, interpret its p-value correctly, compare common tests, and see how power and multiple testing change decisions."
references:
  - id: asa-p
    text: 'Ronald L. Wasserstein and Nicole A. Lazar. "The ASA’s Statement on p-Values: Context, Process, and Purpose." The American Statistician, 2016.'
    url: https://doi.org/10.1080/00031305.2016.1154108
  - id: nist-tests
    text: 'NIST/SEMATECH. "Quantitative Techniques: Hypothesis Testing." Engineering Statistics Handbook.'
    url: https://www.itl.nist.gov/div898/handbook/eda/section3/eda35.htm
  - id: scipy-welch
    text: 'SciPy 1.11.4 documentation. "scipy.stats.ttest_ind."'
    url: https://docs.scipy.org/doc/scipy-1.11.4/reference/generated/scipy.stats.ttest_ind.html
  - id: scipy-mwu
    text: 'SciPy 1.11.4 documentation. "scipy.stats.mannwhitneyu."'
    url: https://docs.scipy.org/doc/scipy-1.11.4/reference/generated/scipy.stats.mannwhitneyu.html
  - id: scipy-fisher
    text: 'SciPy 1.11.4 documentation. "scipy.stats.fisher_exact."'
    url: https://docs.scipy.org/doc/scipy-1.11.4/reference/generated/scipy.stats.fisher_exact.html
  - id: holm
    text: 'Sture Holm. "A Simple Sequentially Rejective Multiple Test Procedure." Scandinavian Journal of Statistics 6, 1979.'
    url: https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf
  - id: bh
    text: 'Yoav Benjamini and Yosef Hochberg. "Controlling the False Discovery Rate: a Practical and Powerful Approach to Multiple Testing." JRSS B 57, 1995.'
    url: https://www.math.tau.ac.il/~ybenja/MyPapers/benjamini_hochberg1995.pdf
  - id: scipy-fdr
    text: 'SciPy 1.11.4 documentation. "scipy.stats.false_discovery_control."'
    url: https://docs.scipy.org/doc/scipy-1.11.4/reference/generated/scipy.stats.false_discovery_control.html
---

A p-value is a statement about a test statistic **under a specified null model**. It is not a probability that the null hypothesis is true. That distinction sounds small, but it controls almost every decision that follows: which test I choose, which direction counts as surprising, and what I can conclude from a result.

I find it useful to build a test in this order: name the population quantity I want, state a null and an alternative, choose a statistic that responds to the difference, work out its behavior under the null, and only then look at the observed statistic. The calculation can be one line of code. The reasoning is the actual work. The American Statistical Association makes the same practical point: scientific conclusions should not rest only on whether one p-value crosses a threshold. {{< cite "asa-p" >}}

## Start with the estimand, not a test name

Suppose two independently sampled groups receive methods A and B. The **estimand** might be the population mean difference

$$
\Delta=\mu_A-\mu_B.
$$

If larger outcomes are better, $\Delta>0$ is an improvement. An analysis of medians, a difference in the probability of a positive outcome, and an average treatment effect are different questions even if all involve the same two groups. A test has to match the estimand and the sampling design.

For a two-sided mean comparison I might state $H_0:\Delta=0$ against $H_1:\Delta\ne0$. A one-sided alternative is $H_1:\Delta>0$ (with a corresponding null covering $\Delta\le0$). One-sided tests have more power for a prespecified direction, but they do not count a large effect in the other direction as evidence for that particular alternative. Choosing the side after seeing the data silently changes the test. If harm in either direction matters, I would specify two-sided analysis before collecting data.

The **test statistic** turns data into a number. For independent means, a standardized difference is a natural choice: observed difference divided by an estimated standard error. Its **null distribution** describes what statistic values would occur across repeated samples if the null model held. A p-value is the null probability of a statistic at least as extreme as the observed one, where “extreme” is defined by the alternative. For a symmetric two-sided $t$ reference distribution,

$$
p=P_{H_0}(|T|\ge |t_{\mathrm{obs}}|).
$$

For a one-sided greater-than test it is $P_{H_0}(T\ge t_{\mathrm{obs}})$. Discrete tests need care with ties and attainable tail probabilities; composite nulls may require a worst-case probability over null parameter values. This is why “probability of these exact data” is too loose a definition.

Crucially, $P(\text{data or more extreme}\mid H_0)$ does not become $P(H_0\mid\text{data})$ by reversing the condition. The latter is a Bayesian posterior probability and requires a prior plus a likelihood. The companion [priors and posteriors post](/blog/bayesian-priors-posteriors-predictive/) develops that distinction. A large p-value also does not establish $H_0$: the data may be noisy or the test may have little power to detect the effect that matters.

## A worked Welch test

Here are two small, independent sets of outcomes. I will estimate $\Delta$ with $\bar x_A-\bar x_B$ and allow the groups to have different population variances. Welch's test is the usual two-sample $t$ choice for that situation. It still needs independent observations and a reasonable sampling distribution for the means; unequal-variance support is not a cure for clustered data or severe selection bias. {{< cite "scipy-welch" >}}

For sample sizes $n_A,n_B$ and sample variances $s_A^2,s_B^2$,

$$
SE=\sqrt{\frac{s_A^2}{n_A}+\frac{s_B^2}{n_B}},\qquad
t=\frac{(\bar x_A-\bar x_B)-0}{SE}.
$$

Welch's approximate degrees of freedom are

$$
\nu=\frac{(s_A^2/n_A+s_B^2/n_B)^2}
{(s_A^2/n_A)^2/(n_A-1)+(s_B^2/n_B)^2/(n_B-1)}.
$$

The full runnable file is [welch_example.py](welch_example.py):

```python {title="welch_example.py"}
import numpy as np
from scipy import stats

group_a = np.array([12, 11, 13, 12, 14, 10, 13, 15], dtype=float)
group_b = np.array([10, 11, 12, 10, 9, 13, 8, 12, 11, 13, 9, 11], dtype=float)

n_a, n_b = len(group_a), len(group_b)
mean_difference = group_a.mean() - group_b.mean()
var_a, var_b = group_a.var(ddof=1), group_b.var(ddof=1)
term_a, term_b = var_a / n_a, var_b / n_b
standard_error = np.sqrt(term_a + term_b)
t_statistic = mean_difference / standard_error
degrees_freedom = (term_a + term_b) ** 2 / (
    term_a**2 / (n_a - 1) + term_b**2 / (n_b - 1)
)
p_value = 2 * stats.t.sf(abs(t_statistic), degrees_freedom)

check = stats.ttest_ind(group_a, group_b, equal_var=False)
assert np.isclose(t_statistic, check.statistic)
assert np.isclose(degrees_freedom, check.df)
assert np.isclose(p_value, check.pvalue)

print(f"mean difference = {mean_difference:.4f}")
print(f"standard error = {standard_error:.4f}")
print(f"Welch t = {t_statistic:.4f}, df = {degrees_freedom:.4f}")
print(f"two-sided p = {p_value:.6f}")
print(f"SciPy agrees = {np.isclose(p_value, check.pvalue)}")
```

```text {title="Output"}
mean difference = 1.7500
standard error = 0.7317
Welch t = 2.3916, df = 15.1506
two-sided p = 0.030175
SciPy agrees = True
```

The sample mean difference is $1.75$ outcome units. Under the model and a prespecified two-sided $\alpha=0.05$, the p-value is below the threshold. I would still report the estimate, its units, an interval, sample sizes, and assumptions. The p-value alone does not say whether $1.75$ is large enough to matter. The [confidence-interval post](/blog/confidence-intervals-bootstrap-permutation/) calculates the uncertainty around this same estimate.

## Errors, power, and the size of an effect

A **Type I error** rejects a true null. If a valid test has size $\alpha=0.05$, its long-run false-rejection probability under the null is at most 5% for the specified procedure. It does not mean 5% of reported significant results are false. A **Type II error** fails to reject a false null at a particular alternative; its probability is $\beta$. **Power** is $1-\beta$, the probability of rejection at that particular alternative. There is no single power number without naming an effect size and sampling model. {{< cite "nist-tests" >}}

<figure class="ml-diagram">
<svg viewBox="0 0 860 235" role="img" aria-label="Decision table for a test: Type I and Type II errors">
  <defs><marker id="ml-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>
  <rect class="box blue" x="220" y="25" width="280" height="70" rx="8"/><text class="name" x="360" y="62">Null is true</text>
  <rect class="box violet" x="525" y="25" width="280" height="70" rx="8"/><text class="name" x="665" y="62">Alternative is true</text>
  <rect class="box green" x="15" y="110" width="185" height="45" rx="8"/><text class="name" x="107" y="139">Do not reject</text>
  <rect class="box rose" x="15" y="171" width="185" height="45" rx="8"/><text class="name" x="107" y="200">Reject</text>
  <text class="note blue" x="360" y="138">Correct: at least 1 − α</text>
  <text class="note violet" x="665" y="138">Type II error: β</text>
  <text class="note rose" x="360" y="198">Type I error: at most α</text>
  <text class="note green" x="665" y="198">Power: 1 − β</text>
</svg>
<figcaption>These probabilities describe repeated decisions under a specified sampling model, not the probability that a hypothesis is true after this dataset.</figcaption>
</figure>

To see the geometry without estimating variance, move the controls below. This is **not** the Welch calculation above. It is an exact known-$\sigma$ illustration for two independent normal groups with $n$ observations per group. With effect $d=\Delta/\sigma$, the z statistic has mean shift $\delta=d\sqrt{n/2}$ under the chosen alternative. For a two-sided threshold $c=z_{1-\alpha/2}$,

$$
\operatorname{power}(d,n,\alpha)=\Phi(-c-\delta)+1-\Phi(c-\delta).
$$

{{< embed src="power-demo.html" height="740" caption="Known-variance z-test model. The shaded alternative tails are the probability of rejection when the specified effect is real." >}}

The demo evaluates normal probabilities with a numerical CDF approximation and rounds displayed percentages to one decimal place. Larger $n$ separates the statistic distributions for the same standardized effect. Tightening $\alpha$ moves the rejection lines outward and reduces false positives, but generally also reduces power. Very large samples can make a trivial difference statistically detectable; small samples can miss a meaningful difference. Effect size and uncertainty keep either result in context.

## Which test matches which question?

This table is a starting point, not a substitute for specifying how observations were sampled. In particular, “nonparametric” does not mean “assumption-free.”

| Data and question | Common test | Null and important conditions |
|---|---|---|
| One or two means with known population variance | z test | Standardized mean has a normal null distribution; known variance or justified large-sample approximation. |
| One mean, or two independent means with estimated variance | one-sample $t$; Welch two-sample $t$ | Mean equals a target, or mean difference is zero; independent units, approximate normality of mean statistics. Welch allows unequal variances. |
| Before/after values on the same units | paired $t$ | Mean **within-pair difference** is zero; independent pairs, with approximately normal mean difference. Do not treat the two columns as independent. |
| More than two independent group means | one-way ANOVA $F$ | All group means equal; classical $F$ assumes independent observations, approximately normal errors and common variance. A significant omnibus result does not say which groups differ. |
| Two categorical variables in a contingency table | Pearson chi-square | Independence of categories, with independent counts and a reliable large-sample approximation (adequate expected counts). |
| Small $2\times2$ table with fixed margins | Fisher's exact test | Under the conditional null, odds ratio is one / variables are independent given margins; uses a hypergeometric reference distribution. {{< cite "scipy-fisher" >}} |
| Two independent ordinal or continuous samples | Mann–Whitney $U$ | Under the usual exact null, the distributions are the same; rank-based alternatives address stochastic ordering. Calling it a generic “median test” is wrong unless additional shape assumptions make a location shift interpretable. {{< cite "scipy-mwu" >}} |

A test of two proportions uses a binomial/contingency-table model, not the mean of arbitrary numerical scores. A paired categorical outcome needs a paired-data method. If units share users, households, sessions, or dates, the independence assumption in a row above can be more important than whether its formula uses $t$ or $z$. The [data-leakage and validation post](/blog/cross-validation-and-data-leakage/) discusses analogous grouping and time constraints in predictive evaluation.

## Multiple questions and repeated looks

Suppose I test 20 independent true nulls at 0.05. The probability of **at least one** false rejection is $1-(1-0.05)^{20}\approx0.642$. Independence makes that number easy to compute; the broader lesson does not depend on independence. A family of questions needs a declared error target.

**Family-wise error rate (FWER)** is $P(V\ge1)$, where $V$ is the number of false rejections. Bonferroni rejects individual p-values at $\alpha/m$, controlling FWER by the union bound even with dependence, if each p-value is valid. Holm sorts p-values and compares the $i$th smallest to $\alpha/(m-i+1)$, stopping at the first failure. It controls FWER under arbitrary dependence and is never less powerful than simple Bonferroni for the same family. {{< cite "holm" >}}

**False discovery rate (FDR)** is $E[V/\max(R,1)]$, where $R$ is the number of rejections. Benjamini–Hochberg (BH) sorts p-values $p_{(1)}\le\cdots\le p_{(m)}$, finds the largest $k$ with $p_{(k)}\le kq/m$, then rejects the first $k$. Its original guarantee is for independent valid tests; certain positive-dependence structures also work, but arbitrary dependence needs further care. FDR is a useful target for discovery screening, while FWER is stricter when even one false claim is costly. {{< cite "bh" >}}

Here is a small, **illustrative** family of p-values: $[0.004,0.012,0.018,0.04,0.2]$. At level $0.05$, Bonferroni's cutoff is $0.01$, so it rejects only hypothesis 1. Holm passes its first two ordered cutoffs ($0.01$, then $0.0125$) and stops when $0.018>0.05/3$. BH's largest passing rank is 4, because $0.04=4(0.05)/5$, so it rejects the first four. The [complete checked file](multiple_testing_example.py) also verifies BH decisions against SciPy's adjusted p-values. {{< cite "scipy-fdr" >}}

```python {title="Multiple-testing decisions"}
import numpy as np
from scipy import stats

p = np.array([0.004, 0.012, 0.018, 0.04, 0.2])
alpha, m = 0.05, len(p)
order = np.argsort(p)
ranked = p[order]

bonferroni = p <= alpha / m
holm_ranked = np.zeros(m, dtype=bool)
for i, value in enumerate(ranked):
    if value > alpha / (m - i):
        break
    holm_ranked[i] = True
holm = np.zeros(m, dtype=bool)
holm[order] = holm_ranked

passing = np.flatnonzero(ranked <= alpha * np.arange(1, m + 1) / m)
bh_ranked = np.arange(m) < (passing[-1] + 1 if len(passing) else 0)
bh = np.zeros(m, dtype=bool)
bh[order] = bh_ranked
assert np.array_equal(bh, stats.false_discovery_control(p, method="bh") <= alpha)

for name, decisions in (("Bonferroni", bonferroni), ("Holm", holm), ("BH", bh)):
    print(name, (np.flatnonzero(decisions) + 1).tolist())
```

```text {title="Output"}
Bonferroni [1]
Holm [1, 2]
BH [1, 2, 3, 4]
```

These are decisions on five numbers, not evidence that any particular rejection is true or false. The FWER and FDR guarantees are repeated-experiment properties of valid p-values under each procedure's assumptions; they do not bound the realized false-discovery fraction in this one illustrative family.

Multiple testing is not only a list of columns. Repeatedly checking a running experiment and stopping the first time $p<0.05$ changes the distribution of the final p-value. So does trying many outcomes, filters, or one-sided directions and reporting only the smallest. A fixed sample size, a declared stopping rule, or a valid sequential design makes the reported error rate interpretable. Merely saying “we looked at the data often” does not repair an ordinary fixed-sample p-value after the fact.

## Interview questions and follow-ups

**1. What is a p-value?** The probability, under a specified null model, of a test statistic at least as extreme as the observed statistic in the prespecified direction. It is not $P(H_0\mid\text{data})$.

**2. What does $p=0.03$ mean?** If the null model and test design hold, results this extreme or more extreme occur with probability 0.03 under that null. It does not say there is a 3% chance the null is true, nor that the effect is practically important.

**3. Can a large p-value prove no effect?** No. A low-power test can often fail to reject a real effect. To argue that an effect is small, define a meaningful bound and examine an interval or an equivalence test designed for it.

**4. When would you choose Welch over the pooled two-sample $t$ test?** When comparing independent means without a justified equal-population-variance assumption. Welch estimates the standard error from each group and uses approximate degrees of freedom; it does not fix dependence between observations.

**5. Why is a paired $t$ test different?** It tests the mean of within-unit differences. Pairing removes between-unit variation from the comparison when that structure is present. Discarding the pairing changes the standard error and the question.

**6. Is Mann–Whitney a test of medians?** Not generally. Its usual null is equality of distributions, and its rank statistic can respond to shape or spread differences. A median/location-shift interpretation needs extra assumptions.

**7. What is the difference between Type I error and FDR?** Type I error describes false rejection for one test; FDR concerns the expected fraction of false discoveries among rejections across a chosen family. FWER instead protects against even one false rejection in the family.

**8. Does $\alpha=0.05$ imply 95% power?** No. Alpha constrains false rejection under the null. Power is computed under a particular alternative and depends on effect size, variance, sample size, and design.

**9. Why can a tiny effect have a tiny p-value?** Standard errors often shrink with sample size. With enough data, a small departure from the null can be measured precisely; practical impact still requires an effect-size judgment.

**10. What changes if I choose one-sided analysis after observing the sign?** The stated tail no longer describes the prespecified procedure. I have effectively given myself a choice among analyses, which can inflate false-positive risk.

**11. What is wrong with checking $p<0.05$ every day until it happens?** The final p-value follows a stopping rule unlike the fixed-sample null distribution. Use a prespecified sequential method or analyze at the declared endpoint.

**12. What should accompany a test result?** The estimand, estimate and units, uncertainty interval, sample sizes, sampling design, test direction, p-value, and any multiplicity or stopping plan. That lets a reader judge both statistical evidence and practical size.

{{< references >}}
