---
title: "Multivariate Gaussians: Geometry, Conditioning, and Precision"
date: 2026-11-10T12:30:00+05:30
draft: true
topics: ["math", "ml"]
tags: ["interview", "probability", "gaussian"]
summary: "A covariance matrix shapes Gaussian probability ellipses and determines exactly how one observation changes another. Derive the conditional law, read precision zeros, and compute with stable solves."
references:
  - id: stanford-probability
    text: 'Stanford CS229. "Probability Theory Review and Reference," sections on multivariate Gaussian marginals and conditionals.'
    url: https://cs229.stanford.edu/lectures-spring2022/cs229-probability_review.pdf
  - id: mit-gaussian
    text: 'MIT 6.436J. "Multivariate Normal Distributions Continued; Characteristic Functions," Lecture 15, 2018.'
    url: https://ocw.mit.edu/courses/6-436j-fundamentals-of-probability-fall-2018/87422049e8f05459ee857eb475f3a667_MIT6_436JF18_lec15.pdf
  - id: cmu-graphical
    text: 'Cosma Rohilla Shalizi. "Advanced Data Analysis from an Elementary Point of View," section 21.4 on Gaussian graphical models.'
    url: https://www.stat.cmu.edu/~cshalizi/uADA/12/lectures/ADAfaEPoV.pdf
  - id: scipy-normal
    text: 'SciPy documentation. "scipy.stats.multivariate_normal."'
    url: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.multivariate_normal.html
  - id: scipy-chi2
    text: 'SciPy documentation. "scipy.stats.chi2."'
    url: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2.html
  - id: numpy-cholesky
    text: 'NumPy documentation. "numpy.linalg.cholesky."'
    url: https://numpy.org/doc/stable/reference/generated/numpy.linalg.cholesky.html
---

A one-dimensional Gaussian needs a mean and a variance. In several dimensions, I also need to know which coordinates move together. The covariance matrix supplies that relationship: it rotates and stretches probability contours, tells me how an observation in one coordinate updates another, and reveals when a density calculation will be numerically fragile. A diagonal covariance gives independent coordinates **if the vector is jointly Gaussian**. That last condition is easy to say too quickly, so I will make it explicit.

I will use a two-dimensional example throughout. It makes the conditional formula and the geometry visible without hiding either behind matrix notation. The same blocks generalize to many coordinates. This article builds on [probability distributions and their properties](/blog/probability-distributions-properties/) and on the distinction between covariance and dependence in [expectation, variance, the LLN, and the CLT](/blog/expectation-variance-lln-clt/).

## A valid covariance is more than a table of variances

For a random vector $X\in\mathbb R^d$ with mean $\mu$, define

$$
\Sigma=\operatorname{Cov}(X)
=\mathbb E[(X-\mu)(X-\mu)^\top].
$$

Its diagonal entries are variances; entry $\Sigma_{ij}$ is the covariance of coordinates $i$ and $j$. It is symmetric. More importantly, for every vector $a$, $a^\top\Sigma a=\operatorname{Var}(a^\top X)\geq0$. Thus a valid covariance is **positive semidefinite** (PSD). A matrix with a negative eigenvalue cannot be a covariance matrix, even if its diagonal entries look reasonable. If $\Sigma$ is **positive definite** (PD), all nonzero linear combinations have positive variance and the ordinary full-dimensional Gaussian density exists. If it is PSD but singular, a Gaussian vector can still exist, but it lies on a lower-dimensional affine set and has no ordinary density with respect to $d$-dimensional volume.

For two coordinates with variances $\sigma_A^2$ and $\sigma_B^2$, write $\Sigma_{AB}=\rho\sigma_A\sigma_B$. Validity requires $|\rho|\leq1$; strict inequality gives a nonsingular two-dimensional covariance when both variances are positive. At $\rho=1$ or $-1$, one standardized coordinate is an exact linear function of the other. A tiny positive eigenvalue is not singular, but it warns me that inverse-based calculations may amplify measurement or rounding error.

One definition of a jointly Gaussian vector is that **every** linear combination $a^\top X$ is univariate Gaussian, allowing a degenerate constant. Equivalently, it can be written $X=\mu+AZ$ for a vector $Z$ of independent standard normals and a suitable matrix $A$. Each coordinate is then Gaussian, but the converse fails. Let $Z\sim\mathcal N(0,1)$ and let $S$ be an independent fair sign, $+1$ or $-1$. Set $A=Z$ and $B=SZ$. Both marginals are standard normal and $\operatorname{Cov}(A,B)=\mathbb E[SZ^2]=0$, yet $|A|=|B|$ always. They are dependent; $A+B$ even has a point mass at zero when $S=-1$, so the pair is not jointly Gaussian. Marginal normality, or even marginal normality plus zero covariance, does not license the joint-Gaussian formulas below.

For a genuine joint Gaussian, affine transforms preserve Gaussianity: $CX+b\sim\mathcal N(C\mu+b,C\Sigma C^\top)$. Selecting some coordinates is a special case, so every marginal is Gaussian with the corresponding mean entries and covariance submatrix. Conversely, that property of marginals alone does not establish the joint law. Stanford's probability notes state the affine, marginal, and conditional rules for a joint Gaussian. {{< cite "stanford-probability" >}}

## Density contours are Mahalanobis circles after whitening

When $\Sigma$ is PD, the $d$-dimensional density is

$$
p(x)=\frac{\exp\!\left[-\tfrac12(x-\mu)^\top\Sigma^{-1}(x-\mu)\right]}
{(2\pi)^{d/2}|\Sigma|^{1/2}}.
$$

The quadratic term $D^2(x)=(x-\mu)^\top\Sigma^{-1}(x-\mu)$ is the **squared Mahalanobis distance**. The determinant in the denominator measures overall volume: spreading the same probability over a larger region lowers density. Equal-density contours have equal $D^2$. If $\Sigma=LL^\top$ is a Cholesky factorization, set $z=L^{-1}(x-\mu)$; then $D^2=\lVert z\rVert^2$. Ellipses in original coordinates are circles in these whitened coordinates. This is a geometric statement about the assumed Gaussian model, not a guarantee that observed data form perfect ellipses. {{< cite "stanford-probability" "numpy-cholesky" >}}

There is a trap in calling a contour “one sigma.” In **one** dimension, $|Z|\leq1$ has about 68.3% normal probability. In **two** dimensions, $D^2(X)$ has a $\chi^2$ distribution with two degrees of freedom, so $P(D^2\leq1)=1-e^{-1/2}\approx0.393469$. A 95% probability ellipse uses $D^2\leq\chi^2_{2,0.95}\approx5.991465$, not radius one. The dimension matters: for a $d$-dimensional nonsingular Gaussian, $D^2\sim\chi_d^2$. These ellipses enclose **future observations under known parameters**; they are not confidence regions for an estimated mean. The attached code computes the cutoffs with SciPy's chi-square distribution. {{< cite "scipy-chi2" >}}

## Conditioning: subtract what the observed block explains

Partition a joint Gaussian into target $A$ and observed block $B$:

$$
\begin{pmatrix}A\\B\end{pmatrix}\sim\mathcal N\!\left(
\begin{pmatrix}\mu_A\\\mu_B\end{pmatrix},
\begin{pmatrix}\Sigma_{AA}&\Sigma_{AB}\\\Sigma_{BA}&\Sigma_{BB}\end{pmatrix}
\right).
$$

Assume $\Sigma_{BB}$ is invertible. The conditional distribution after observing $B=b$ is

$$
A\mid B=b\sim\mathcal N\!\left(
\mu_A+\Sigma_{AB}\Sigma_{BB}^{-1}(b-\mu_B),
\Sigma_{AA}-\Sigma_{AB}\Sigma_{BB}^{-1}\Sigma_{BA}
\right).
$$

The first term is a **linear update** from the observed deviation $b-\mu_B$. The second is the **Schur complement**, the uncertainty left after that information is used. In this Gaussian model it does not depend on the particular value $b$; different observed values shift the center but have the same conditional covariance. In a non-Gaussian model, either feature can fail. Stanford's notes give this block formula. {{< cite "stanford-probability" >}}

I find a residual derivation easier to remember than completing a large quadratic square. Define $K=\Sigma_{AB}\Sigma_{BB}^{-1}$ and $R=A-\mu_A-K(B-\mu_B)$. Then

$$
\operatorname{Cov}(R,B)=\Sigma_{AB}-K\Sigma_{BB}=0.
$$

Both $R$ and $B$ are affine transforms of the **joint Gaussian**, so zero cross-covariance makes them independent. Therefore observing $B=b$ leaves the distribution of $R$ unchanged and merely replaces $B$ by $b$ in $A=\mu_A+K(B-\mu_B)+R$. Expanding $\operatorname{Cov}(R)$ gives $\Sigma_{AA}-\Sigma_{AB}\Sigma_{BB}^{-1}\Sigma_{BA}$. The Schur complement must be PSD because it is a covariance matrix. This proof exposes exactly where joint normality is needed: zero covariance alone would not establish independence for my $Z,SZ$ counterexample. MIT's multivariate-normal lecture also uses zero covariance and Gaussianity to establish independence after whitening. {{< cite "mit-gaussian" >}}

If $\Sigma_{BB}$ is singular, I cannot insert a literal inverse. Some observed values may be impossible, and conditional laws on the support need a more careful generalized treatment. Adding a small diagonal term is a **modeling choice** that changes the covariance, not a proof that the singular formula was valid. In normal numerical work I solve $\Sigma_{BB}u=b-\mu_B$ or $\Sigma_{BB}V=\Sigma_{BA}$ rather than compute $\Sigma_{BB}^{-1}$ explicitly.

## A two-dimensional update I can check by hand

Let the coordinates be $A,B$ with

$$
\mu=\begin{pmatrix}1\\-1\end{pmatrix},\qquad
\Sigma=\begin{pmatrix}4&1.2\\1.2&1\end{pmatrix}.
$$

The marginal $A\sim\mathcal N(1,4)$ has standard deviation two. The marginal $B\sim\mathcal N(-1,1)$ has standard deviation one, and their correlation is $1.2/(2\cdot1)=0.6$. Observe $B=0$, one standard deviation above its mean. The conditional gain is $1.2/1=1.2$, so the conditional center is $1+1.2(0-(-1))=2.2$. Its variance is $4-1.2^2/1=2.56$, giving standard deviation $1.6$. Thus

$$
A\mid B=0\sim\mathcal N(2.2,2.56).
$$

The conditional mean shifts right and the distribution narrows; it does **not** become a point mass, because $B$ does not determine $A$. The point $(A,B)=(2.2,0)$ has squared Mahalanobis distance one from $\mu$ and lies on the inner ellipse below. The script independently checks the conditional density at that point by dividing the SciPy joint density by the marginal density of $B$. That ratio equals the one-dimensional $\mathcal N(2.2,2.56)$ density, about $0.249339$. Conditioning on an exact continuous value is understood through a conditional density, not as dividing by the probability of the zero-probability event $B=0$.

{{< figure src="gaussian_conditioning.svg" caption="Left: two probability ellipses for the known 2D Gaussian, with the observation B=0. Right: the marginal density of A and the conditional density A given B=0. The inner ellipse contains 39.3% of the joint mass, not 68%." width="100%" >}}

## Covariance and precision answer different independence questions

For a jointly Gaussian pair, $\Sigma_{AB}=0$ means **marginal** independence: knowing $A$ alone does not change the distribution of $B$. In a larger nonsingular Gaussian vector, let $\Omega=\Sigma^{-1}$ be the **precision matrix**. A zero off-diagonal entry $\Omega_{ij}=0$ means coordinates $i$ and $j$ are independent **conditional on all the other coordinates**. It does not in general mean they are marginally independent, or independent given an arbitrary smaller set. Gaussian graphical models use this distinction to encode conditional relationships. {{< cite "cmu-graphical" >}}

A three-variable construction makes it concrete. Let independent standard normals be $U,E_1,E_3$, and set $X_2=U$, $X_1=U+E_1$, $X_3=U+E_3$. Then $\operatorname{Cov}(X_1,X_3)=1$: they move together because both see $U$. Given $X_2$, the remaining noises $E_1,E_3$ are independent. In the order $(X_1,X_2,X_3)$, the covariance and precision matrices are

$$
\Sigma=\begin{pmatrix}2&1&1\\1&1&1\\1&1&2\end{pmatrix},\qquad
\Omega=\begin{pmatrix}1&-1&0\\-1&3&-1\\0&-1&1\end{pmatrix}.
$$

The $(1,3)$ covariance is one, while the $(1,3)$ precision entry is zero. This is a structural statement under a joint Gaussian assumption, not a rule for arbitrary data with a zero in an estimated inverse covariance.

## Computation: solve, sample, then distrust a thin covariance estimate

The [attached Python script](gaussian_conditioning.py) generates the SVG, samples from the specified Gaussian by Cholesky, and checks the analytic density and conditional law with SciPy. The key numerical calculation solves a triangular system and uses a log determinant:

```python
chol = np.linalg.cholesky(cov)        # cov = L @ L.T, for positive definite cov
z = np.linalg.solve(chol, point - mean)
mahal_sq = z @ z
logdet = 2 * np.log(np.diag(chol)).sum()
logpdf = -0.5 * (2 * np.log(2 * np.pi) + logdet + mahal_sq)
samples = rng.normal(size=(100_000, 2)) @ chol.T + mean
```

This avoids forming $\Sigma^{-1}$ or multiplying tiny density factors. The SciPy `multivariate_normal.logpdf` call gives the same checked value. For a genuinely singular covariance, its `allow_singular` option uses a generalized convention; that does not make the ordinary PD formula above valid on all of $\mathbb R^d$. {{< cite "scipy-normal" "numpy-cholesky" >}}

```bash
python3 gaussian_conditioning.py
```

```text {title="Checked output"}
conditional A|B=0: mean=2.200, variance=2.560
log p(A=2.2,B=0)=-2.807881; SciPy=-2.807881
conditional density ratio=0.249339; normal pdf=0.249339
2D squared-radius 1 mass=0.393469; 95% cutoff=5.991465
sample mean=[ 0.999 -1.001]
sample covariance=[[4.006, 1.194], [1.194, 0.996]]
chain precision (1,3)=0.0
```

The sample mean and covariance are Monte Carlo estimates from 100,000 seeded draws, not identities. In a fitted model, the sample covariance has another limit: centering an $n\times d$ data matrix leaves rank at most $n-1$, so the empirical $d\times d$ covariance has rank at most $\min(n-1,d)$. If $d\geq n$, it is necessarily singular; collinear features can make it singular even when $d<n$. A positive diagonal regularizer or a structured covariance model can make downstream solves possible, but its strength must be chosen with the training data and the resulting conditional distribution belongs to the **modified** model. [PCA](/blog/pca-derived/) views the same small-eigenvalue issue from a dimensionality-reduction angle, while [Gaussian mixtures and EM](/blog/kmeans-gaussian-mixtures-em/) uses Gaussian component covariances whose collapse needs special care.

## Interview questions I would rehearse

1. **Why must a covariance matrix be PSD?** Every quadratic form $a^\top\Sigma a$ equals the variance of $a^\top X$ and cannot be negative. PD additionally rules out zero-variance linear combinations.

2. **Can a Gaussian have singular covariance?** Yes, as a degenerate Gaussian supported on a lower-dimensional affine set. The ordinary full-dimensional density and a standard Cholesky factorization require PD covariance.

3. **Do normal marginals imply a joint normal?** No. $Z$ and $SZ$ have normal marginals and zero covariance but share absolute value, so they are dependent and not jointly Gaussian.

4. **What does Mahalanobis distance change from Euclidean distance?** It rescales and rotates by covariance. With $\Sigma=LL^\top$, it is Euclidean distance after solving $Lz=x-\mu$.

5. **Does a radius-one ellipse contain 68% of a 2D Gaussian?** No. It contains $P(\chi_2^2\leq1)\approx39.3\%$. A 95% observation ellipse uses squared radius about $5.991$.

6. **What is the conditional mean after observing block $B=b$?** $\mu_A+\Sigma_{AB}\Sigma_{BB}^{-1}(b-\mu_B)$ when $\Sigma_{BB}$ is invertible. In code, solve a system rather than form that inverse.

7. **Why is the conditional covariance a Schur complement?** Remove the linear prediction of $A$ from $B$. The residual covariance is $\Sigma_{AA}-\Sigma_{AB}\Sigma_{BB}^{-1}\Sigma_{BA}$, and the residual is independent of $B$ under joint Gaussianity.

8. **Does conditional covariance depend on the observed value?** Not for a fixed nonsingular joint Gaussian partition. The conditional mean changes with $b$; its covariance is the same for every supported $b$.

9. **When does zero covariance imply independence?** For jointly Gaussian variables. It need not do so for merely normal marginals or arbitrary distributions.

10. **What does a zero precision entry mean?** For a nonsingular joint Gaussian, $\Omega_{ij}=0$ means coordinates $i,j$ are conditionally independent given all other coordinates, not necessarily marginally independent.

11. **Why prefer `solve` and `logpdf` to an inverse and raw density?** Solves avoid unnecessary explicit inversion; log density turns products and determinants into stable sums. Cholesky also exposes whether the PD assumption is numerically tenable.

12. **Why is sample covariance singular when features outnumber rows?** A centered $n\times d$ matrix has rank at most $n-1$, and its covariance cannot have higher rank. Regularization changes the model rather than manufacturing independent evidence.

{{< references >}}
