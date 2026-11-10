---
title: "Clustering: K-Means, Gaussian Mixtures, and EM"
date: 2026-11-10T09:00:00+05:30
draft: true
topics: ["ml", "math"]
tags: ["interview", "clustering", "building-block"]
summary: "Why nearest-center clustering and probabilistic mixtures look similar, where their objectives differ, and how EM turns unknown memberships into tractable updates."
references:
  - id: kmeanspp
    text: 'David Arthur and Sergei Vassilvitskii. "k-means++: The Advantages of Careful Seeding." SODA, 2007.'
    url: https://research.google/pubs/k-means-the-advantages-of-careful-seeding/
  - id: em1977
    text: 'A. P. Dempster, N. M. Laird, and D. B. Rubin. "Maximum Likelihood from Incomplete Data via the EM Algorithm." Journal of the Royal Statistical Society B, 1977.'
    url: https://academic.oup.com/jrsssb/article/39/1/1/7027539
  - id: sklearn-clustering
    text: 'scikit-learn developers. "Clustering" user guide: k-means, DBSCAN, and silhouette analysis.'
    url: https://scikit-learn.org/stable/modules/clustering.html
  - id: sklearn-mixture
    text: 'scikit-learn developers. "Gaussian mixture models" user guide.'
    url: https://scikit-learn.org/stable/modules/mixture.html
  - id: dbscan1996
    text: 'Martin Ester, Hans-Peter Kriegel, Jörg Sander, and Xiaowei Xu. "A Density-Based Algorithm for Discovering Clusters in Large Spatial Databases with Noise." KDD, 1996.'
    url: https://file.biolab.si/papers/1996-DBSCAN-KDD.pdf
  - id: sklearn-dbscan
    text: 'scikit-learn developers. "DBSCAN" API reference, including the min_samples counting convention.'
    url: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html
  - id: smallvariance
    text: 'Jörg Lücke and Dennis Forster. "k-means as a variational EM approximation of Gaussian mixture models." Pattern Recognition Letters, 2019.'
    url: https://arxiv.org/abs/1704.04812
---

Clustering asks which observations belong together before we have target labels. The answer depends on what “together” means. K-means says nearby points should share a center. A Gaussian mixture says each point could have come from several overlapping probability distributions. DBSCAN says a cluster is a connected region of sufficiently dense neighborhoods. Those are three different questions, so I would choose the question before choosing the algorithm.

The distinction matters in interviews because the algorithms can draw similar pictures while optimizing different quantities. A hard assignment from a Gaussian mixture may resemble a k-means partition, but its boundary can bend with covariance and prior weight. A visually tidy cluster need not correspond to a class label. I will build the two center-based methods from their objectives, then use DBSCAN to expose where “center” is the wrong abstraction.

## K-means: commit to one center

Let $x_1,\ldots,x_n\in\mathbb R^d$ be observations, $z_i\in\{1,\ldots,K\}$ their assignments, and $\mu_k$ the centers. K-means minimizes the within-cluster sum of squares, also called *inertia*:

$$
J(z,\mu)=\sum_{i=1}^n\|x_i-\mu_{z_i}\|_2^2.
$$

For fixed centers, every term is independent of the other assignments. The best $z_i$ is therefore the index of the nearest center. For fixed assignments, let $C_k$ contain the points assigned to $k$. The center-dependent part is $\sum_{i\in C_k}\|x_i-\mu_k\|^2$. Differentiate with respect to $\mu_k$:

$$
\nabla_{\mu_k}J=2|C_k|\mu_k-2\sum_{i\in C_k}x_i=0
\quad\Longrightarrow\quad
\mu_k=\frac{1}{|C_k|}\sum_{i\in C_k}x_i.
$$

The mean is not an arbitrary choice of representative. It is the minimizer of *squared Euclidean* error. If the loss were absolute distance in one dimension, the median would be the minimizer. Alternating nearest-center assignment and mean update is Lloyd's algorithm. Each exact step cannot increase $J$; after assignments stop changing, the algorithm has reached a fixed point. That is a local result. The global optimum may be elsewhere, and ties or an early stopping tolerance complicate statements about strict decrease. {{< cite "sklearn-clustering" >}}

There is another way to see the update. If $\bar x_k$ is the mean of $C_k$, then

$$
\sum_{i\in C_k}\|x_i-\mu_k\|^2
=\sum_{i\in C_k}\|x_i-\bar x_k\|^2
+|C_k|\|\mu_k-\bar x_k\|^2.
$$

The second term is nonnegative and vanishes only at the mean. This identity also explains why a center may sit between all its observations: it minimizes their aggregate squared error, even if no observation occupies that location. K-means centers are not necessarily representative data points. If I need actual observations as representatives, I would use a medoid-based method instead.

Take the six one-dimensional points $[0,1,2,4,5,6]$ and $K=2$. Starting with centers at $0$ and $6$ assigns the first three points left and the last three right. Their means become $1$ and $5$. The squared errors are $1+0+1$ on each side, so $J=4$. A new assignment step changes nothing. The midpoint $3$ is a decision boundary, not an observed point and not a learned probability threshold.

<figure class="ml-diagram">
<svg viewBox="0 0 860 220" role="img" aria-label="Six points on a line split by k-means into two groups with centers at one and five and boundary at three">
  <defs><marker id="ml-arrow" viewBox="0,0 10,10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>
  <rect class="box blue" x="65" y="38" width="330" height="100" rx="12"/>
  <rect class="box rose" x="465" y="38" width="330" height="100" rx="12"/>
  <text class="name" x="230" y="70">0   1   2</text>
  <text class="note blue" x="230" y="105">mean = 1, SSE = 2</text>
  <text class="name" x="630" y="70">4   5   6</text>
  <text class="note rose" x="630" y="105">mean = 5, SSE = 2</text>
  <line class="arrow dashed plain" x1="430" y1="25" x2="430" y2="156"/>
  <text class="label" x="430" y="185">boundary = 3</text>
</svg>
<figcaption>Once assignments are fixed, each center moves to the mean of its three points.</figcaption>
</figure>

### Initialization, scale, and choosing $K$

The first centers matter because the objective has many local minima. K-means++ picks one data point, then samples later seeds with probability proportional to $D(x)^2$, the squared distance to the nearest seed already chosen. It spreads the initial centers without promising that Lloyd's iterations find the global optimum. I would run several independent initializations and keep the solution with the lowest final $J$. {{< cite "kmeanspp" >}}

Distance also encodes a feature choice. If income is measured in thousands and age in years, raw Euclidean distance can let the numerical scale decide the grouping. Standardizing features can help when comparable variation should matter across them; blindly standardizing can erase meaningful units. The same judgment applies after [PCA](/blog/pca-derived/): PCA rotates or compresses a representation, whereas clustering partitions its points. Principal components need scaling and a reason to retain particular directions. Neither PCA nor k-means discovers semantic labels automatically.

Outliers are expensive under squared error, so a faraway point can pull a center or consume a whole cluster. Empty clusters can appear after an update or with poor seeds; the mean of an empty set is undefined. An implementation must reinitialize that center, split a cluster, or reject the run. Duplicate points and $K$ larger than the number of distinct locations deserve explicit attention. Finally, Euclidean k-means favors compact, roughly round groups separated by straight nearest-center boundaries. Two crescents can be obvious to a human and still be awkward for this objective.

This means preprocessing is part of the clustering definition. If I remove outliers, change a distance metric, or embed text into vectors, I have changed what counts as close. An apparently stable numerical optimum may still be semantically poor. Conversely, a few isolated points may be the observations I care about most, so deleting them to make the clusters look cleaner could defeat the analysis. I would examine those points before deciding whether they are measurement errors, rare valid cases, or a separate group.

How many clusters? The globally optimal inertia cannot increase as $K$ grows, because another center can always mimic an old one. A fitted run can still return higher inertia if it lands in a worse local solution. The “elbow” is a judgment about diminishing returns, not a mathematical optimum. The silhouette score compares a point's average distance to its own group, $a(i)$, with its smallest average distance to another group, $b(i)$:

$$
s(i)=\frac{b(i)-a(i)}{\max\{a(i),b(i)\}}.
$$

A larger average silhouette suggests separated, compact groups for the chosen distance. It can prefer convex clusters and miss density-shaped structure; it also has edge cases such as singleton groups and is not defined for $K=1$. I would inspect stability across seeds, cluster sizes, and whether the groups answer the downstream question. If labels exist for evaluation, that becomes an external validation problem, with the distinctions in [ML and NLP metrics](/blog/ml-nlp-metrics/) relevant. {{< cite "sklearn-clustering" >}}

## Gaussian mixtures: allow uncertainty

In a Gaussian mixture model (GMM), each observation has an unobserved component $z_i$. Component $k$ has weight $\pi_k>0$, mean $\mu_k$, and positive-definite covariance $\Sigma_k$, with $\sum_k\pi_k=1$. The model first draws $z_i\sim\mathrm{Categorical}(\pi)$, then draws $x_i\mid z_i=k\sim\mathcal N(\mu_k,\Sigma_k)$. We only observe $x_i$, so its density sums over possible origins:

$$
p(x_i\mid\theta)=\sum_{k=1}^K\pi_k\mathcal N(x_i\mid\mu_k,\Sigma_k),
\qquad
\ell(\theta)=\sum_{i=1}^n\log p(x_i\mid\theta).
$$

This is a *density model* rather than just a partition. A covariance gives each component a shape: spherical covariance gives round contours; diagonal covariance permits different axis widths; full covariance permits rotated ellipses. A full $d\times d$ covariance has $d(d+1)/2$ free entries per component and needs enough effective data to estimate them. Diagonal covariance uses only $d$ variance entries but cannot model correlation within a component. Mixture components can overlap, and a single real-world group may need several Gaussians. The component index is therefore a model construct, not a guaranteed class name. {{< cite "sklearn-mixture" >}}

For a point $x_i$, Bayes' rule gives its *responsibility*:

$$
r_{ik}=P(z_i=k\mid x_i,\theta)
=\frac{\pi_k\mathcal N(x_i\mid\mu_k,\Sigma_k)}
{\sum_j\pi_j\mathcal N(x_i\mid\mu_j,\Sigma_j)}.
$$

Every row of $r$ sums to one. These are posterior probabilities *under the fitted model*, conditional on the chosen $K$ and Gaussian assumptions. They are not calibrated probabilities that a human label is correct. For the six-point example, choose equal weights, means $1$ and $5$, and equal variance $4$. The responsibility of the left component for $x=2$ is

$$
\frac{e^{-(2-1)^2/8}}{e^{-(2-1)^2/8}+e^{-(2-5)^2/8}}
=\frac{1}{1+e^{-1}}\approx 0.7311.
$$

K-means assigns $x=2$ left with no uncertainty attached. The mixture says that, under its current broad components, a right origin remains possible. Moving the means changes both methods; changing variance changes only the mixture's softness here.

The weights and covariances can also move the boundary. With a shared spherical covariance $\sigma^2I$, choosing the component with highest posterior probability is equivalent to minimizing $\|x-\mu_k\|^2-2\sigma^2\log\pi_k$. A larger prior weight can win even when its center is farther away. With unequal full covariances, comparing Gaussian log densities introduces different quadratic forms and log determinants, so a hard maximum-posterior boundary can be curved. This is why a mixture can express elongated or unevenly sized clouds that nearest-center k-means tends to split awkwardly. It is still a Gaussian model: a crescent or ring may require multiple components and an interpretation of how those components combine.

{{< embed src="hard-soft.html" height="435" caption="Drag a center, move the probe, and change the shared standard deviation. Both panels use equal component weights and spherical covariance." >}}

## EM: alternate inference and fitting

Directly differentiating $\ell$ is possible, but the logarithm of a sum entangles components. If the missing $z_i$ were known, estimating a Gaussian would be familiar weighted statistics. Expectation-maximization (EM) alternates between estimating those missing memberships and refitting parameters. Its general treatment and likelihood result go back to Dempster, Laird, and Rubin. {{< cite "em1977" >}}

The **E-step** computes $r_{ik}$ from the *current* parameters. To avoid underflow, work with log scores $a_{ik}=\log\pi_k+\log\mathcal N(x_i\mid\mu_k,\Sigma_k)$ and normalize using

$$
\operatorname{LSE}(a_{i1},\ldots,a_{iK})
=m_i+\log\sum_k e^{a_{ik}-m_i},\qquad m_i=\max_k a_{ik},
$$

so $r_{ik}=\exp(a_{ik}-\operatorname{LSE}(a_i))$. Subtracting $m_i$ keeps the exponentials at most one; it does not change their ratios. For a full covariance Gaussian, the log density includes $-\tfrac12\log|\Sigma_k|$ and the squared Mahalanobis distance $-\tfrac12(x_i-\mu_k)^\top\Sigma_k^{-1}(x_i-\mu_k)$. A numerical implementation should solve a linear system, often via Cholesky factorization, rather than explicitly invert $\Sigma_k$.

The **M-step** treats responsibilities as fractional counts. With $N_k=\sum_i r_{ik}$, maximum likelihood gives

$$
\pi_k^{\mathrm{new}}=\frac{N_k}{n},\qquad
\mu_k^{\mathrm{new}}=\frac{1}{N_k}\sum_i r_{ik}x_i,
$$

$$
\Sigma_k^{\mathrm{new}}=
\frac{1}{N_k}\sum_i r_{ik}(x_i-\mu_k^{\mathrm{new}})
(x_i-\mu_k^{\mathrm{new}})^\top.
$$

Notice the denominator $N_k$, not $N_k-1$: this is the maximum-likelihood covariance for weighted data. These equations also show a failure mode. If $N_k$ is tiny, the mean and covariance become unstable. If a Gaussian shrinks around one observation, its determinant can approach zero and the unconstrained mixture likelihood can grow without bound. One can constrain or regularize covariance, use a prior, enforce a minimum effective component size, and restart degenerate fits. These choices change the optimization problem and may change what monotonicity claim is valid. {{< cite "sklearn-mixture" >}}

For the six-point initialization, the left responsibilities are approximately $[0.953,0.881,0.731,0.269,0.119,0.047]$. They sum to $N_{\text{left}}=3$. The first M-step moves its mean from $1$ to about $1.433$ and its variance from $4$ to about $2.211$; symmetry gives a right mean near $4.567$. That first move is useful to notice: EM does not immediately assign the first three points left and the last three right. It averages all six points, each with its current fractional weight. Later iterations make those responsibilities sharper as the fitted variances shrink.

Why does exact EM improve likelihood? For arbitrary distributions $q_i(k)$ over the missing assignments, Jensen's inequality gives a lower bound

$$
\ell(\theta)\geq
\mathcal F(q,\theta)
=\sum_{i,k}q_i(k)\log\frac{\pi_k\mathcal N(x_i\mid\mu_k,\Sigma_k)}{q_i(k)}.
$$

More precisely, $\ell(\theta)=\mathcal F(q,\theta)+\sum_i\mathrm{KL}(q_i\|p(z_i\mid x_i,\theta))$. The E-step sets $q_i=r_i$ for the old parameters, making the bound tight. The M-step maximizes that bound with respect to $\theta$. Thus the next likelihood cannot be lower **when both steps are exact and optimize the same well-defined objective**. This says neither that EM finds the global optimum nor that the unregularized maximum exists. Approximate updates, numerical error, or ad hoc covariance floors can break the strict textbook guarantee for the original likelihood. The likelihood can also increase by making a component pathologically narrow, which is not the kind of progress we want.

### A runnable six-point check

The complete [NumPy script](clustering_demo.py) implements both algorithms in one dimension with explicit initial values. It uses log-sum-exp for the E-step and no covariance regularizer so the displayed likelihood check refers to the exact objective on this well-behaved example. It rejects nonfinite likelihoods, numerically empty components, and invalid variances; it is a teaching example, not a production mixture fitter.

This is one E-step followed by one M-step on the same six points. The full script repeats these steps and checks the log-likelihood. Each row of `responsibilities` sums to one; each component mean uses its fractional membership mass.

```python {title="One EM update"}
import numpy as np

x = np.array([0., 1., 2., 4., 5., 6.])
weights = np.array([0.5, 0.5])
means = np.array([1., 5.])
variances = np.array([4., 4.])
scores = (np.log(weights)[None, :]
          - 0.5 * np.log(2 * np.pi * variances)[None, :]
          - 0.5 * (x[:, None] - means[None, :])**2 / variances[None, :])
shifted = np.exp(scores - scores.max(axis=1, keepdims=True))
responsibilities = shifted / shifted.sum(axis=1, keepdims=True)
mass = responsibilities.sum(axis=0)
weights = mass / x.size
means = (responsibilities * x[:, None]).sum(axis=0) / mass
variances = (responsibilities * (x[:, None] - means)**2).sum(axis=0) / mass
assert np.allclose(responsibilities.sum(axis=1), 1)
assert np.isclose(weights.sum(), 1)
```

```bash
python3 clustering_demo.py
```

```text {title="Output"}
k-means centers: [1. 5.]
k-means labels: [0 0 0 1 1 1]
k-means SSE: 4.0
initial GMM P(left | x=2): 0.731059
final GMM weights: [0.5 0.5]
final GMM means: [1.001774 4.998226]
final GMM variances: [0.673761 0.673761]
final GMM P(left | x=2): 0.997353
GMM log-likelihood: -13.353843 -> -11.450985
nondecreasing likelihood: True
```

The variance tightens as EM fits the six observations, so the same point becomes much less ambiguous. The GMM means finish near, but not exactly at, the k-means centers. Nothing in this output compares the numerical value of SSE with log-likelihood: they have different units and are different objectives. For choosing mixture components, raw training log-likelihood also tends to reward extra flexibility. I would use held-out log-likelihood, an information criterion with its assumptions stated, and a check that fitted covariances are sensible. Any preprocessing or choice of $K$ should be learned without seeing evaluation data; [cross-validation and data leakage](/blog/cross-validation-and-data-leakage/) gives the broader rule.

## When does a GMM become k-means?

Suppose every component has the **same fixed spherical covariance** $\Sigma_k=\sigma^2I$ and equal positive weight. Its responsibility is proportional to $\exp[-\|x_i-\mu_k\|^2/(2\sigma^2)]$. As $\sigma^2\to0$, the nearest mean gets responsibility approaching one and the others approach zero, provided there is a unique nearest mean. The weighted M-step for means then becomes the k-means mean update. At a distance tie, the limiting assignment needs a tie rule.

The objective connection is just as useful: for fixed centers and equal weights, multiplying the negative mixture log-likelihood by $2\sigma^2$ and taking this small-variance limit leaves $\sum_i\min_k\|x_i-\mu_k\|^2$. Terms involving Gaussian normalization and the fixed weights vanish under that scaling. This does **not** say that a general GMM is k-means with probabilities attached. Unequal or learned covariances change the geometry, finite variance keeps assignments soft, and free covariance can collapse. There are also variational formulations that connect Lloyd's algorithm to isotropic mixtures without a zero-variance limit; the limit here is the clean connection between the usual full-responsibility EM updates and hard nearest-center updates. {{< cite "smallvariance" >}}

This gives a useful interview shorthand: k-means learns centers for a squared-distance partition; a GMM learns a probability density with weights, centers, and shapes. Both are initialization-sensitive. Each optimization step moves its own objective in the right direction under its assumptions, much as the distinction between update rules and generalization matters in [optimizers and generalization](/blog/optimizers-and-generalization/).

## A different notion of cluster: DBSCAN

DBSCAN replaces centers with local density. Choose a radius $\varepsilon$ and a minimum neighborhood count `min_samples`. A *core* point has at least that many points within $\varepsilon$, counting itself. A *border* point is within $\varepsilon$ of a core point but is not core. A point reachable from no core point is *noise*. Connected chains of core neighborhoods form clusters; nearby border points attach to them. The method discovers the number of such regions from the settings rather than asking for $K$ first. It can represent nonconvex shapes and mark isolated observations as noise. {{< cite "dbscan1996" "sklearn-dbscan" >}}

It does not remove the need to define distance. The radius has the units of the features, so scaling and the distance metric matter. One global $\varepsilon$ struggles when one cluster is dense and another sparse; the same setting may fragment one or merge the other. In high dimensions, distances often become less informative, so neighborhood counts may cease to express the intended density. Border points touching two core-connected regions can be assigned ambiguously by an implementation. DBSCAN's “noise” is a result relative to its parameters, not proof that a point is an error.

For example, on two nested crescents, k-means will place straight nearest-center boundaries through curved groups. A GMM with a small number of ellipses may also slice across them; adding components can approximate the shape, but the component count no longer equals the visible group count. DBSCAN can follow the crescents when each has a continuous chain of dense neighborhoods and the gap is wider than the chosen radius. If the density drops along one crescent, however, that same radius may break it into pieces. The geometry and sampling density, not the algorithm's name, decide which result is useful.

## Interview questions I would be ready for

1. **Why is the k-means update a mean?** With assignments fixed, differentiating the sum of squared distances gives $2|C_k|\mu_k-2\sum_{i\in C_k}x_i=0$. For absolute one-dimensional distances, I would expect a median instead.

2. **Does k-means always converge to the best clustering?** No. Exact alternating updates lower or preserve SSE and end at a fixed assignment under ordinary finite-data conditions, but initialization can trap the run at a poor local solution. Repeats help search; they do not certify global optimality.

3. **What happens if a cluster becomes empty?** Its mean is undefined. A practical implementation needs an explicit policy such as reseeding the center, splitting a populated cluster, or discarding that initialization; the policy can affect the result.

4. **Why isn't the elbow an objective rule for $K$?** Inertia drops monotonically as centers are added. A bend is subjective and may be absent. Silhouette checks separation for a chosen distance but also reflects a preference for compact, often convex groups.

5. **How is a GMM assignment different from a k-means assignment?** A GMM computes a posterior responsibility for every component from weights, means, and covariances. A hard label can be produced by taking the largest responsibility, but that discards ambiguity.

6. **Where does log-sum-exp enter EM?** The E-step normalizes log component densities. Subtracting their maximum before exponentiating keeps the calculation stable when Gaussian densities are very small.

7. **What exactly makes EM's likelihood nondecreasing?** The E-step makes a Jensen lower bound equal the current likelihood; an exact M-step improves that same bound. The statement concerns that objective and exact steps, not arbitrary regularized or approximate code.

8. **Can a GMM's training likelihood be unbounded?** Yes. With freely learned covariance, a component can collapse onto a point while its covariance determinant tends to zero. Positive-definite constraints, regularization, priors, and fit diagnostics address this.

9. **When does GMM EM reduce to Lloyd's algorithm?** With common fixed spherical covariance tending to zero, finite positive weights, and unique nearest means, responsibilities become hard nearest-center assignments. The mean M-step then matches Lloyd's update.

10. **Why choose diagonal rather than full covariance?** Diagonal uses fewer parameters and may be more stable with limited data, but cannot model within-component correlations. Full covariance can rotate ellipses and needs much more effective data.

11. **Would DBSCAN find the same clusters as k-means?** Only by coincidence. It connects dense neighborhoods and can mark noise; k-means assigns every point to a center. DBSCAN needs a meaningful radius and struggles with varied densities.

12. **Do discovered clusters prove the existence of classes?** No. They reflect the features, metric, assumptions, and model settings. I would validate them against the intended use, external labels if available, and stability under reasonable preprocessing changes.

{{< references >}}
