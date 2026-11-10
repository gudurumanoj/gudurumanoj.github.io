---
title: "Support Vector Machines and the Kernel Trick"
date: 2026-11-10T09:00:00+05:30
draft: true
topics: ["ml", "math"]
tags: ["interview", "support-vector-machines"]
summary: "From the geometry of a margin to soft-margin hinge loss, the dual, kernels, and the practical C–gamma tradeoff, with a checked NumPy example and interview questions."
references:
  - id: cortes-vapnik
    text: 'Corinna Cortes and Vladimir Vapnik. "Support-Vector Networks." Machine Learning 20, 1995, pp. 273–297.'
    url: https://doi.org/10.1007/BF00994018
  - id: sklearn-svm
    text: 'Scikit-learn developers. "Support Vector Machines." User Guide.'
    url: https://scikit-learn.org/stable/modules/svm.html
  - id: sklearn-calibration
    text: 'Scikit-learn developers. "Probability Calibration." User Guide.'
    url: https://scikit-learn.org/stable/modules/calibration.html
---

A support vector machine asks a geometric question: among the lines that separate two classes, which one leaves the widest empty corridor between them? The answer depends on the nearby examples, not on a class average. I find that picture more useful than memorising the dual objective. Once the corridor is clear, the hinge loss, the parameter $C$, and kernels all have a job to do.

I will use binary labels $y_i\in\{-1,+1\}$ and a score $f(x)=w^\top x+b$. A positive score predicts $+1$; a negative score predicts $-1$. The score is a signed quantity, but it is **not** automatically a probability. The original support-vector network combined maximum-margin separation, slack for nonseparable data, and nonlinear feature spaces. {{< cite "cortes-vapnik" >}}

## The corridor and its scale

<figure class="ml-diagram">
<svg viewBox="0 0 860 260" role="img" aria-label="Vertical decision boundary with parallel margin lines and support vectors on the margins">
  <defs><marker id="svm-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>
  <line class="arrow dashed plain" x1="300" y1="25" x2="300" y2="220"/>
  <line class="arrow plain" x1="430" y1="25" x2="430" y2="220"/>
  <line class="arrow dashed plain" x1="560" y1="25" x2="560" y2="220"/>
  <circle cx="155" cy="72" r="10" class="box rose"/><circle cx="230" cy="145" r="10" class="box rose"/><circle cx="300" cy="88" r="12" class="box rose"/>
  <circle cx="560" cy="165" r="12" class="box green"/><circle cx="660" cy="75" r="10" class="box green"/><circle cx="730" cy="170" r="10" class="box green"/>
  <text class="label" x="300" y="235">f = -1</text><text class="label" x="430" y="235">f = 0</text><text class="label" x="560" y="235">f = +1</text>
  <text class="note violet" x="430" y="18">full corridor width: 2 / norm(w)</text>
</svg>
<figcaption>The two large points touch the margin. Moving either one can move the fitted boundary; distant points often cannot.</figcaption>
</figure>

For a point $x$, the perpendicular signed distance to the line $f(x)=0$ is $f(x)/\lVert w\rVert$. Its **functional margin** is $y_i f(x_i)$; its **geometric margin** is $y_i f(x_i)/\lVert w\rVert$. The latter is the actual distance with a sign indicating whether the point is correctly classified. Multiplying both $w$ and $b$ by any positive constant leaves the decision boundary and geometric distances unchanged, but multiplies every functional margin. So maximising the raw score would be meaningless.

For separable data I fix the arbitrary scale by setting the smallest functional margin to one. Then $y_i(w^\top x_i+b)\geq1$ for every training point. The planes $f=-1$ and $f=+1$ are $2/\lVert w\rVert$ apart; each is $1/\lVert w\rVert$ from the boundary. Maximising that width is equivalent to

$$
\min_{w,b}\quad \tfrac12\lVert w\rVert^2\qquad\text{subject to }y_i(w^\top x_i+b)\geq1.\tag{1}
$$

The factor $1/2$ makes derivatives tidy. A point satisfying equality is on a margin plane. The hard-margin problem has no feasible solution if the classes overlap or a single contradictory label occurs at an identical $x$. Even when it is feasible, a mislabeled outlier may make the corridor unhelpfully narrow.

## Let points violate the corridor

For each point introduce slack $\xi_i\geq0$ and require $y_if(x_i)\geq1-\xi_i$. A point with $\xi_i=0$ is on or outside its correct margin. If $0<\xi_i<1$, it is correctly classified but inside the corridor. At $\xi_i=1$ it lies on the boundary; when $\xi_i>1$ it is misclassified. At the optimum $\xi_i=\max(0,1-y_if(x_i))$, giving the hinge loss $\ell_i=\max(0,1-y_if(x_i))$ and the soft-margin objective

$$
\min_{w,b}\quad \tfrac12\lVert w\rVert^2+C\sum_{i=1}^n\max(0,1-y_if(x_i)).\tag{2}
$$

$C$ is the price of a unit of corridor violation relative to a larger norm. Larger $C$ pushes harder to fit the training labels; smaller $C$ permits more violations and favours a wider corridor. It is *inverse* regularisation strength in this convention. If I write the loss as a **mean**, $\tfrac12\lVert w\rVert^2+C_{\rm mean}\tfrac1n\sum_i\ell_i$, the same solution has $C_{\rm mean}=nC$ from (2). Another common form is $\tfrac\lambda2\lVert w\rVert^2+\tfrac1n\sum_i\ell_i$, where $\lambda=1/(nC)$. This bookkeeping matters when comparing libraries, papers, or datasets of different sizes.

Hinge loss is flat for $y_if(x_i)>1$ and linear when $y_if(x_i)<1$. Away from the kink, the subgradient of one loss with respect to $w$ is $0$ outside the margin and $-y_ix_i$ inside. At exactly one it is any vector on the segment from $0$ to $-y_ix_i$; with respect to $b$ the corresponding values are $0$ and $-y_i$. Optimisers can use a valid subgradient at the kink. A mistake to avoid: hinge loss penalises *low margin*, including correctly classified examples, not only wrong predictions.

The points that constrain the solution are support vectors. In a nondegenerate soft-margin solution, a point outside the margin has dual weight $\alpha_i=0$; a point exactly on the margin may have $0<\alpha_i<C$; and a point strictly inside it has $\alpha_i=C$. Equalities can be degenerate, so “every point on the margin has positive weight” is too strong. A support vector may itself be misclassified. The phrase **margin error** means $\xi_i>0$, which also includes correctly classified points inside the corridor.

## Why a kernel can replace a dot product

The training objective looks like a problem in $w$, but its solution can be written using training points. The stationarity condition of the soft-margin Lagrangian gives

$$
w=\sum_i\alpha_i y_ix_i,\qquad \sum_i\alpha_i y_i=0,\qquad 0\leq\alpha_i\leq C.\tag{3}
$$

Substitute the first equality into the Lagrangian. The remaining maximisation is

$$
\max_\alpha\quad \sum_i\alpha_i-\tfrac12\sum_{i,j}\alpha_i\alpha_jy_iy_j(x_i^\top x_j),\tag{4}
$$

with the last two constraints in (3). The bias $b$ has no penalty, which is why its derivative imposes $\sum_i\alpha_i y_i=0$. The box bound comes from the nonnegative slack variables. This is the useful part of the derivation: training and prediction depend on dot products, and prediction is

$$
f(x)=\sum_{i:\alpha_i>0}\alpha_i y_i(x_i^\top x)+b.\tag{5}
$$

<details><summary>Maths: the short Lagrangian calculation</summary>

$$
L=\tfrac12\lVert w\rVert^2+C\sum_i\xi_i-\sum_i\alpha_i[y_i(w^\top x_i+b)-1+\xi_i]-\sum_i\mu_i\xi_i.
$$

Here $\alpha_i,\mu_i\geq0$. Setting derivatives with respect to $w,b,\xi_i$ to zero gives $w=\sum_i\alpha_iy_ix_i$, $\sum_i\alpha_iy_i=0$, and $C-\alpha_i-\mu_i=0$. The last equality implies $0\leq\alpha_i\leq C$. Substitute these into $L$ to get (4). Complementary slackness says $\alpha_i[y_if(x_i)-1+\xi_i]=0$ and $(C-\alpha_i)\xi_i=0$, explaining the support-vector cases above.

</details>

Now imagine a feature map $\phi(x)$ that makes a curved separation look linear in a new space. Replace $x_i^\top x_j$ by $K(x_i,x_j)=\phi(x_i)^\top\phi(x_j)$, and the same dual calculation works without constructing $\phi$ explicitly. The input-space boundary can be curved even though it is a hyperplane in feature space. “Kernel trick” means exactly this substitution in an algorithm whose calculations need only inner products. {{< cite "sklearn-svm" >}}

There is a condition behind it. A valid real kernel must be symmetric and **positive semidefinite**: for every finite set of points and every vector $c$, $\sum_{i,j}c_ic_jK(x_i,x_j)\geq0$. Equivalently, every Gram matrix $K(x_i,x_j)$ has nonnegative eigenvalues, up to numerical roundoff. This permits an inner-product interpretation and makes the usual dual a concave maximisation. A hand-made similarity score need not satisfy it. Testing one Gram matrix is a useful diagnostic, not a proof for every possible dataset.

## The RBF kernel and the $C$–$\gamma$ pair

The radial basis function kernel is $K(x,z)=\exp(-\gamma\lVert x-z\rVert^2)$, with $\gamma>0$. A large $\gamma$ makes similarity fall rapidly with distance, so each support vector influences a small neighbourhood. A small $\gamma$ makes influence broad, often producing a smoother boundary. At extremely small $\gamma$, the Gram matrix can approach an all-ones matrix and lose useful distinctions; at extremely large $\gamma$, distinct training points can look nearly orthogonal. These are intuitions, not monotonic guarantees about test error.

$C$ and $\gamma$ interact. A flexible, narrow RBF with large $C$ can fit very local quirks. Reducing $C$ may leave more margin violations even with the same kernel. Tune both on validation folds, not on the final test set. Scale numeric features first: multiplying all coordinates by $a$ has the same RBF distances as multiplying $\gamma$ by $a^2$. An unscaled high-range feature can dominate $\lVert x-z\rVert^2$. Fit each scaler on its training fold, then apply it to that fold's validation split. The leakage issue is the same one discussed in [cross-validation and data leakage](/blog/cross-validation-and-data-leakage/); its practical effect is especially visible when distance defines the model. {{< cite "sklearn-svm" >}}

The default $\gamma$ formula in a library is a starting point, not a feature-scale invariant constant. One-hot dimensions, outliers, and a change of scaler alter distances and therefore the effective kernel. A validation curve across a log-spaced grid of $C$ and $\gamma$ is more informative than a single “best” pair without nearby scores.

## A small check in NumPy

Four collinear points make the geometry inspectable. The closest negative and positive points sit at $x_1=-1$ and $x_1=+1$. The hard-margin separator $w=(1,0)$, $b=0$ has geometric margin one on each side. Then I halve $w$: the two closest points remain correctly classified, but incur hinge loss because their functional margins are only $0.5$. Finally I calculate an RBF Gram matrix and a toy kernel expansion. The expansion coefficients illustrate prediction; they are **not** the result of fitting an SVM.

```python {title="margin_and_kernel.py"}
import numpy as np

X = np.array([[-2., 0.], [-1., 0.], [1., 0.], [2., 0.]])
y = np.array([-1., -1., 1., 1.])
w = np.array([1., 0.])
b = 0.

functional = y * (X @ w + b)
geometric = functional / np.linalg.norm(w)
print("functional:", functional)
print("closest distance:", geometric.min())
print("corridor width:", 2 / np.linalg.norm(w))

w_small = 0.5 * w
hinge = np.maximum(0., 1. - y * (X @ w_small + b))
active = y * (X @ w_small + b) < 1.
subgradient = w_small - (y[active, None] * X[active]).sum(axis=0) / len(X)
print("hinge:", hinge)
print("objective at C_mean=1:", 0.5 * w_small @ w_small + hinge.mean())
print("subgradient there:", subgradient)

def rbf(A, B, gamma=0.5):
    squared = ((A[:, None, :] - B[None, :, :]) ** 2).sum(axis=2)
    return np.exp(-gamma * squared)

K = rbf(X, X)
print("K(-1,+1):", round(K[1, 2], 6))
print("smallest Gram eigenvalue:", round(np.linalg.eigvalsh(K).min(), 6))
support = X[[1, 2]]
signed_alpha = np.array([-0.5, 0.5])
print("toy scores at 0 and 2:",
      np.round(rbf(np.array([[0., 0.], [2., 0.]]), support) @ signed_alpha, 6))
```

```text {title="Output"}
functional: [2. 1. 1. 2.]
closest distance: 1.0
corridor width: 2.0
hinge: [0.  0.5 0.5 0. ]
objective at C_mean=1: 0.375
subgradient there: [0. 0.]
K(-1,+1): 0.135335
smallest Gram eigenvalue: 0.332929
toy scores at 0 and 2: [0.       0.297711]
```

The zero subgradient is for the *mean-loss* objective at this particular $w$ and $C_{\rm mean}=1$; it does not claim those toy kernel coefficients are optimal. The Gram eigenvalue check is only for these four points. The function computes a fresh array of pairwise squared distances, which is clear for a tiny example but needs more careful memory handling at scale.

## Which model should I reach for?

For a linear SVM, the primal score $w^\top x+b$ takes $O(d)$ dense work per prediction, or work proportional to nonzero features for sparse input. Linear solvers can process examples in passes and avoid an $n\times n$ Gram matrix. For a kernel SVM, a straightforward Gram matrix takes $O(n^2)$ memory, training can be much more expensive than a linear pass, and an RBF prediction evaluates the kernel against the support vectors: roughly $O(n_{\rm SV}d)$ dense work. If many points become support vectors, prediction is expensive too. Exact cost depends heavily on solver, cache, sparsity, and data; “SVMs are fast” is too broad. {{< cite "sklearn-svm" >}}

[Logistic regression](/blog/linear-and-logistic-regression/) also learns a linear boundary, but optimises log loss and gives a probabilistic model whose probabilities still deserve calibration checks. An SVM optimises margin-based hinge loss and gives a score. If the application needs a trustworthy probability, fit a calibration map using held-out or cross-validated training predictions, then evaluate calibration on untouched data. Fitting a calibrator on the same scores used to fit the classifier can be optimistic. Platt-style sigmoid calibration and isotonic calibration are common options; neither turns the raw signed margin into a probability by itself. {{< cite "sklearn-calibration" >}}

$k$-nearest neighbours is another useful comparison: it predicts from nearby stored examples rather than learning one maximum-margin boundary. It can handle local structure, but its notion of distance also depends on scaling, and prediction searches the training set or an index. An RBF SVM likewise uses distances, yet its learned support-vector coefficients and global optimisation are different from a neighbour vote. For high-dimensional sparse text, I would compare a linear SVM and logistic regression early; a nonlinear kernel should earn its added cost through validation.

## Interview questions I would rehearse

**1. Why does the closest point matter?** The maximum-margin boundary is constrained by the smallest geometric margins. Changing a faraway point usually leaves the optimum alone; moving a support vector can change it.

**2. Why set $y_if(x_i)\geq1$ rather than $\geq0$?** The zero threshold fixes classification only. Because scaling $w,b$ changes scores without changing the boundary, the one threshold fixes a canonical scale and makes the geometric margin $1/\lVert w\rVert$.

**3. Is the SVM margin $1/\lVert w\rVert$ or $2/\lVert w\rVert$?** The first is the distance from the boundary to either canonical margin plane. The second is the full width between the two planes. State which one you mean.

**4. What does $C$ do?** In the sum-loss objective it prices a unit of hinge violation against $\tfrac12\lVert w\rVert^2$. Larger $C$ usually reduces tolerated training violations; it does not guarantee better test accuracy.

**5. Can a support vector be on the wrong side of the boundary?** Yes. A soft-margin point with $\xi_i>1$ is misclassified and normally has $\alpha_i=C$. Support vectors are defined through their nonzero dual weights, not through correct predictions.

**6. What is the hinge-loss gradient at margin one?** There is no unique ordinary derivative. Any value between the outside and inside gradients is a valid subgradient; implementations use an admissible choice.

**7. Where does the kernel appear in the derivation?** Stationarity gives $w=\sum_i\alpha_iy_i\phi(x_i)$. Substitution leaves only inner products $\phi(x_i)^\top\phi(x_j)$, which a kernel computes directly.

**8. Can any similarity function be a kernel?** No. The usual kernel SVM needs a symmetric positive-semidefinite Gram matrix for every finite sample. An arbitrary similarity can produce an indefinite dual problem.

**9. What happens if I increase $\gamma$?** RBF similarity becomes more local, allowing a more detailed boundary. Its effect on generalisation depends on $C$, scale, and data, so I would inspect validation scores.

**10. Why scale features inside each fold?** Distances set RBF similarities, and validation statistics must not influence the training transform. Fit the scaler on each training split before tuning $C$ and $\gamma$.

**11. Is an SVM decision score a probability?** No. The score's sign determines a class and its magnitude relates to the fitted boundary; probabilities require separate calibration and evaluation.

**12. When would a linear SVM beat an RBF SVM operationally?** With many examples or high-dimensional sparse features, it avoids Gram-matrix storage and predicts with one dot product. I would compare held-out quality before accepting a nonlinear model's training and serving cost.

The chain I keep in mind is: fix score scale, maximise geometric margin, allow paid violations, then observe that the optimum depends on dot products. Kernels change those dot products; they do not remove the need to scale features, tune on training folds, or check what the score means.

{{< references >}}
