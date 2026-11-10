---
title: "Regularization as Shrinkage, Selection, and a Prior"
date: 2026-11-10T12:00:00+05:30
draft: true
topics: ["math", "ml"]
tags: ["interview", "regularization", "regression"]
summary: "A single loss convention makes ridge, lasso, elastic net, and their Bayesian interpretations comparable. Follow the singular directions, KKT conditions, and a reproducible held-out example."
references:
  - id: ridge-original
    text: 'Arthur E. Hoerl and Robert W. Kennard. "Ridge Regression: Biased Estimation for Nonorthogonal Problems." Technometrics, 1970.'
    url: https://homepages.math.uic.edu/~lreyzin/papers/ridge.pdf
  - id: lasso-original
    text: 'Robert Tibshirani. "Regression Shrinkage and Selection via the Lasso." JRSS B, 1996.'
    url: https://rss.onlinelibrary.wiley.com/doi/pdf/10.1111/j.2517-6161.1996.tb02080.x
  - id: elastic-original
    text: 'Hui Zou and Trevor Hastie. "Regularization and Variable Selection via the Elastic Net." JRSS B, 2005.'
    url: https://sites.stat.washington.edu/courses/stat527/s14/readings/zouhastie05.pdf
  - id: stanford-priors
    text: 'Stanford CME 250. "Lecture 3," Bayesian prior for ridge and lasso.'
    url: https://web.stanford.edu/class/cme250/files/cme250_lecture3.pdf
  - id: adamw-paper
    text: 'Ilya Loshchilov and Frank Hutter. "Decoupled Weight Decay Regularization." ICLR, 2019.'
    url: https://arxiv.org/abs/1711.05101
---

A model can fit the training sample beautifully and still be unstable. If two predictors are almost copies, a tiny change in the data can make their individual least-squares coefficients swing in opposite directions. Regularization asks a deliberate question: how much training fit am I willing to trade for a more constrained estimate? Ridge spreads and shrinks coefficients; lasso can remove them; elastic net combines both. These are statements about an **estimator**, not guarantees that every penalized fit predicts better.

The [linear and logistic regression article](/blog/linear-and-logistic-regression/) develops these methods in a broader regression tour, and [optimizers and generalization](/blog/optimizers-and-generalization/) covers weight decay and training dynamics. Here I want one statistical thread: use a fixed loss normalization, inspect which directions are unstable, and connect the penalty to an explicit prior. That thread prevents the most common interview mistake, which is to recite a formula while silently changing what $\lambda$ means.

## First fix the objective and the units

Let $X\in\mathbb R^{n\times p}$ contain **training-centered and training-scaled** feature columns, $y\in\mathbb R^n$ be centered training targets, and $w\in\mathbb R^p$. For now the intercept has been removed by centering; when fitting a raw response I add its training mean back at prediction time. I use

$$
L_0(w)=\frac{1}{2n}\lVert y-Xw\rVert_2^2.
$$

Ridge minimizes $L_0(w)+(\lambda_2/2)\lVert w\rVert_2^2$. Lasso minimizes $L_0(w)+\lambda_1\lVert w\rVert_1$. My elastic-net convention uses **both** terms. The half makes derivatives tidy; the division by $n$ makes the loss an average per row. Papers and libraries may instead use a sum of squares or put a half in the penalty. A quoted value of $\lambda$ is meaningless until the convention is clear. If another objective is $\lVert y-Xw\rVert^2+\alpha\lVert w\rVert^2$, multiplying my ridge objective by $2n$ shows $\alpha=n\lambda_2$. The coefficients agree only after that conversion.

The penalty also depends on feature units. Replacing a column measured in meters by centimeters divides its fitted coefficient by 100 while leaving predictions the same, but it changes that coefficient's L1 and L2 cost. I therefore learn means and scales **on each training fold only**, transform validation rows with those values, and usually leave the intercept unpenalized. This is a concrete instance of the [data leakage](/blog/cross-validation-and-data-leakage/) problem. Standardizing does not make coefficients causal or magically comparable when features are near duplicates; it makes the penalty's units interpretable. {{< cite "ridge-original" "lasso-original" >}}

## Ridge: shrink most where the data are weakest

Differentiate the ridge objective and set the gradient to zero:

$$
-\frac{1}{n}X^\top(y-Xw)+\lambda_2w=0
\quad\Longrightarrow\quad
(X^\top X+n\lambda_2I)\hat w=X^\top y.
$$

For $\lambda_2>0$, the matrix on the left is positive definite even when columns of $X$ are dependent. I solve the linear system; I do not form an inverse in code. To understand what the system does, write a thin singular-value decomposition $X=UDV^\top$. For a positive singular value $d_j$, the unpenalized least-squares coefficient along $v_j$ is $(u_j^\top y)/d_j$. Ridge multiplies it by

$$
f_j(\lambda_2)=\frac{d_j^2}{d_j^2+n\lambda_2}.
$$

Large $d_j$ means a well-supported direction in the **design matrix**, not necessarily a large effect on $y$; its factor stays near one for moderate $\lambda_2$. Small $d_j$ means a weak or nearly redundant design direction; its factor approaches zero sooner. A direction with $d_j=0$ has no information in $X$ and ridge sets its coefficient to zero. This is why ridge stabilizes collinearity without claiming to discover which of two duplicate features is the true cause. Hoerl and Kennard introduced the diagonal adjustment to least squares in precisely the setting of nonorthogonal predictors. {{< cite "ridge-original" >}}

There is a useful statistical count hidden in those factors. The fitted training response is $\hat y=H_\lambda y$, where $H_\lambda=X(X^\top X+n\lambda_2I)^{-1}X^\top$ for centered data. Its trace,

$$
\operatorname{df}_{\mathrm{ridge}}(\lambda_2)=\operatorname{tr}(H_\lambda)
=\sum_{j:d_j>0}\frac{d_j^2}{d_j^2+n\lambda_2},
$$

is one common **effective degrees of freedom** measure. It slides continuously from the rank of $X$ toward zero as the penalty rises. An independently fitted, unpenalized intercept adds one to this count. It is not the literal number of nonzero coefficients: ridge can have twelve nonzero coefficients but fewer than six effective degrees of freedom under this definition.

Why might shrinkage help? In an ideal fixed-design model $y=Xw_*+\varepsilon$ with independent noise of variance $\sigma^2$, the unpenalized coefficient in singular direction $j$ has noise variance $\sigma^2/d_j^2$. A tiny $d_j$ amplifies noise. Ridge multiplies that noisy coordinate by $f_j$, reducing its variance by $f_j^2$ while introducing bias $(f_j-1)$ times the true coordinate; the bias magnitude is $(1-f_j)$ times its absolute magnitude. The best balance depends on the unknown signal, noise, design, and prediction target. A penalty can reduce variance and still lose because it erases a strong real effect. The [expectation and variance article](/blog/expectation-variance-lln-clt/) supplies the underlying bias–variance language; the factors above show exactly where it enters this linear model.

## Lasso: a corner at zero changes the answer

The L1 penalty has a sharp corner at zero. Let $r=y-Xw$ and $g_j=X_j^\top r/n$, the training residual's score for feature $j$. The lasso optimum obeys the coordinate-wise subgradient condition

$$
w_j\ne0:\quad g_j=\lambda_1\operatorname{sign}(w_j),
\qquad
w_j=0:\quad |g_j|\leq\lambda_1.
$$

The interval at zero is the mechanism for exact sparsity. If a feature's remaining correlation with the residual is too small to clear the threshold, zero is optimal. A smooth L2 derivative equals zero at $w_j=0$, so ridge generally shrinks continuously rather than selecting exact zeros. If the centered columns are orthogonal and $X_j^\top X_j/n=1$, set $z_j=X_j^\top y/n$ and solve the one-coordinate problem. The result is **soft thresholding**:

$$
\hat w_j=\operatorname{sign}(z_j)\max(|z_j|-\lambda_1,0).
$$

For example, $z_j=0.7$ and $\lambda_1=0.2$ give $\hat w_j=0.5$; $z_j=0.1$ gives zero. On correlated columns, each coordinate must use a partial residual that removes the other current terms, but the same threshold appears. The lasso's zeros can make a model easier to describe, yet they do not certify that omitted features have no effect. With nearly identical predictors, small sample changes can change which one gets selected. With exactly duplicated columns, the L1 objective can have multiple coefficient allocations yielding the same fitted values. {{< cite "lasso-original" >}}

Elastic net adds $(\lambda_2/2)\lVert w\rVert_2^2$ to lasso. Its coordinate update divides the soft-thresholded score by $X_j^\top X_j/n+\lambda_2$. A positive L2 term makes the objective strictly convex in $w$, so the coefficient solution is unique even for duplicate columns; it also tends to keep correlated features together rather than forcing a single arbitrary winner. That is a tendency, not a promise that every pair receives identical coefficients. The original elastic-net work motivated this grouping behavior. {{< cite "elastic-original" >}}

## A prior gives the same algebra, with a scale attached

Suppose $y\mid w\sim\mathcal N(Xw,\sigma^2I)$ and, independently across coefficients, $w_j\sim\mathcal N(0,\tau^2)$. Ignoring terms constant in $w$, the negative log posterior is

$$
\frac{1}{2\sigma^2}\lVert y-Xw\rVert^2
+\frac{1}{2\tau^2}\lVert w\rVert^2.
$$

Multiply by $\sigma^2/n$. It becomes my mean-loss ridge objective with $\lambda_2=\sigma^2/(n\tau^2)$. If each coefficient instead has a Laplace prior with density proportional to $\exp(-|w_j|/b)$, its negative log prior is $\lVert w\rVert_1/b$, and the same multiplication gives $\lambda_1=\sigma^2/(nb)$. These are exact MAP correspondences under the stated Gaussian likelihood, priors, and normalization; the factor $n$ is easy to lose. Under fixed prior scales, the equivalent mean-loss penalty changes with sample size because the likelihood accumulates evidence. {{< cite "stanford-priors" >}}

The posterior story explains a preference for small coefficients, but it does not turn a point estimate into a posterior distribution. Gaussian likelihood plus Gaussian prior gives a Gaussian posterior whose mode and mean coincide; a Laplace-prior lasso mode does not by itself give uncertainty intervals or the posterior mean. I would use [Bayesian priors, posteriors, and predictive distributions](/blog/bayesian-priors-posteriors-predictive/) for that further distinction. If I standardize features, the simple independent prior applies to **standardized** coefficients. A prior on coefficients in the original physical units would be a different modeling choice.

## One reproducible split, including a failure at high penalty

The attached [NumPy script](regularization_demo.py) creates 35 noisy training rows with twelve features; the first two are near duplicates. Its 4,000 independent held-out rows share the same synthetic data-generating rule. Because this is a simulation, I can score predicted means against the **known noise-free conditional mean**. The number called “excess MSE” below excludes irreducible test-label noise; on real data I would have only observed labels. The script fits feature means and scales on training data, solves ridge, uses coordinate descent for lasso and elastic net, checks lasso's KKT conditions, and writes the plot. Here is its numerical core:

```python
gram = x.T @ x / n
rhs = x.T @ yc / n
ridge_w = np.linalg.solve(gram + lam * np.eye(p), rhs)

# One elastic-net coordinate, with residual excluding that coordinate:
residual += x[:, j] * w[j]
z = x[:, j] @ residual / n
w[j] = np.sign(z) * max(abs(z) - lam1, 0.0) / (column_norms[j] + lam2)
residual -= x[:, j] * w[j]
```

```bash
python3 regularization_demo.py
```

```text {title="Selected checked output"}
train n=35, features=12, held-out n=4000
OLS excess MSE=3.8068, coeffs x0/x1=[-1.159  2.604]
lambda=0.10: ridge=2.4912, lasso=2.0478, ridge x0/x1=[0.67  0.678], lasso x0/x1=[0.549 0.772], lasso active=9
lambda=0.30: ridge=1.8894, lasso=1.3854, ridge x0/x1=[0.61  0.598], lasso x0/x1=[1.135 0.   ], lasso active=5
lambda=1.00: ridge=2.4789, lasso=4.8160, ridge x0/x1=[0.454 0.445], lasso x0/x1=[0.388 0.   ], lasso active=2
lambda1=lambda2=0.1: elastic net excess MSE=1.7488, coeffs x0/x1=[0.629 0.604], sweeps=120
```

{{< figure src="regularization_spectrum.svg" caption="Left: singular-direction retention and ridge effective degrees of freedom, excluding the intercept. Right: held-out excess prediction error for this one seeded experiment. The penalty is helpful here at intermediate values and harmful when too strong." width="100%" >}}

The raw generating coefficient for feature zero is two and for its near duplicate is zero. OLS nevertheless assigns their **standardized** coefficients opposite-looking values because the training sample barely distinguishes them. Ridge spreads their combined predictive effect; lasso's selected member changes along its path. At $\lambda=0.3$ both penalties beat this OLS fit on this holdout, but at $\lambda=1$ lasso has cut too aggressively. I would choose a penalty using training-only cross-validation and evaluate the chosen pipeline on a separate test set; I would not choose $0.3$ because I saw this test plot. The plot is a diagnostic demonstration of what can happen, not an estimate of a universal advantage.

Early stopping is another way training can favor simpler fits, but its filter is not generally the same as ridge's filter. Likewise, decoupled weight decay in an adaptive optimizer is not automatically the gradient of this L2-penalized objective. Those distinctions matter when transferring a statistical $\lambda$ into a neural-network training recipe; [optimizers and generalization](/blog/optimizers-and-generalization/) works through them, and the decoupled-decay paper states the optimizer distinction. {{< cite "adamw-paper" >}}

## Interview questions I would rehearse

1. **What exactly is being regularized here?** Slopes in a centered, standardized linear model. The intercept is fitted separately and left unpenalized. Changing feature units changes an L1 or L2 penalty unless the transformation is accounted for.

2. **Why does ridge remain solvable under collinearity?** With $\lambda_2>0$, $X^\top X+n\lambda_2I$ is positive definite. Solve that system; the data can still be uninformative about individual duplicate-feature effects.

3. **Which ridge directions shrink most?** The small-singular-value directions. Their factors $d_j^2/(d_j^2+n\lambda_2)$ fall toward zero first, reducing noise amplification.

4. **What does effective degrees of freedom count?** For centered ridge fitted values it is $\operatorname{tr}(H_\lambda)$, the sum of spectral retention factors. Add one for an unpenalized intercept. It is not a count of nonzero coefficients.

5. **Why can ridge predict better despite bias?** A little bias may buy a larger reduction in estimator variance. Whether it does so depends on signal, noise, design, and the target distribution.

6. **Why does lasso make exact zeros?** Its subgradient at zero spans $[-\lambda_1,\lambda_1]$. A residual score inside that interval makes zero optimal; the L2 derivative has no such interval.

7. **What is the lasso answer for one orthogonal standardized feature?** Soft-threshold $z=X_j^\top y/n$: return $\operatorname{sign}(z)(|z|-\lambda_1)_+$. A large coefficient is also biased toward zero, not merely selected.

8. **What if two columns are duplicates?** Their separate effects cannot be identified from these observations. Ridge yields a unique shared allocation; lasso may have multiple coefficient allocations with the same predictions. A positive L2 term in elastic net restores strict convexity.

9. **What prior corresponds to my ridge $\lambda_2$?** With Gaussian noise variance $\sigma^2$ and independent $\mathcal N(0,\tau^2)$ coefficient priors, $\lambda_2=\sigma^2/(n\tau^2)$ under the $1/(2n)$ loss convention.

10. **What prior corresponds to lasso?** Independent Laplace priors of scale $b$ give $\lambda_1=\sigma^2/(nb)$ for the same likelihood and normalization. The lasso solution is a posterior mode, not a full Bayesian uncertainty summary.

11. **How do I select $\lambda$ without optimistic reporting?** Learn scaling and choose $\lambda$ inside training-only folds, then score the entire chosen pipeline on untouched test data. Do not inspect the test curve to pick the winner.

12. **Is AdamW the same as adding this ridge penalty?** Not in general for adaptive optimization: decoupled decay is applied outside the loss-gradient preconditioning. Name the objective and update rule separately.

{{< references >}}
