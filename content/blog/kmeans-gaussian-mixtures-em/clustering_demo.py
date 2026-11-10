"""A small, dependency-light comparison of Lloyd's algorithm and 1D GMM EM."""

import numpy as np


X = np.array([0., 1., 2., 4., 5., 6.])


def logsumexp(a, axis=1):
    m = np.max(a, axis=axis, keepdims=True)
    return np.squeeze(m + np.log(np.sum(np.exp(a - m), axis=axis, keepdims=True)), axis=axis)


def kmeans(x, centers, max_iter=100):
    centers = np.asarray(centers, dtype=float).copy()
    for _ in range(max_iter):
        labels = np.argmin((x[:, None] - centers[None, :]) ** 2, axis=1)
        if any(not np.any(labels == k) for k in range(len(centers))):
            raise ValueError("empty cluster: choose different initial centers")
        new_centers = np.array([x[labels == k].mean() for k in range(len(centers))])
        if np.array_equal(centers, new_centers):
            break
        centers = new_centers
    labels = np.argmin((x[:, None] - centers[None, :]) ** 2, axis=1)
    sse = np.sum((x - centers[labels]) ** 2)
    return centers, labels, sse


def log_joint(x, weights, means, variances):
    return (np.log(weights)[None, :]
            - 0.5 * np.log(2 * np.pi * variances)[None, :]
            - 0.5 * (x[:, None] - means[None, :]) ** 2 / variances[None, :])


def gmm_em(x, means, variances, max_iter=200, tol=1e-10):
    x = np.asarray(x, dtype=float)
    means = np.asarray(means, dtype=float).copy()
    variances = np.asarray(variances, dtype=float).copy()
    if (x.ndim != 1 or not x.size or means.ndim != 1 or not means.size
            or variances.shape != means.shape
            or not np.all(np.isfinite(x)) or not np.all(np.isfinite(means))
            or not np.all(np.isfinite(variances)) or np.any(variances <= 0)):
        raise ValueError("need finite 1D data, means, and matching positive variances")
    weights = np.full(len(means), 1.0 / len(means))
    history = []
    for _ in range(max_iter):
        scores = log_joint(x, weights, means, variances)
        normalizer = logsumexp(scores)
        if not np.all(np.isfinite(normalizer)):
            raise ValueError("nonfinite likelihood: rescale data or reinitialize")
        history.append(float(np.sum(normalizer)))
        responsibilities = np.exp(scores - normalizer[:, None])

        mass = responsibilities.sum(axis=0)
        if not np.all(np.isfinite(mass)) or np.any(mass <= 0):
            raise ValueError("numerically empty component: reinitialize")
        new_weights = mass / len(x)
        new_means = (responsibilities * x[:, None]).sum(axis=0) / mass
        new_variances = (responsibilities * (x[:, None] - new_means) ** 2).sum(axis=0) / mass
        if (not np.all(np.isfinite(new_means))
                or not np.all(np.isfinite(new_variances))
                or np.any(new_variances <= 0)):
            raise ValueError("singular component: reinitialize or constrain variance")
        weights, means, variances = new_weights, new_means, new_variances
        new_ll = float(logsumexp(log_joint(x, weights, means, variances)).sum())
        if not np.isfinite(new_ll):
            raise ValueError("nonfinite likelihood: rescale data or reinitialize")
        if abs(new_ll - history[-1]) < tol:
            history.append(new_ll)
            break
    else:
        history.append(float(logsumexp(log_joint(x, weights, means, variances)).sum()))
    return weights, means, variances, np.array(history)


if __name__ == "__main__":
    centers, labels, sse = kmeans(X, [0., 6.])
    initial_scores = log_joint(X, np.array([.5, .5]), np.array([1., 5.]), np.array([4., 4.]))
    initial_resp = np.exp(initial_scores - logsumexp(initial_scores)[:, None])
    weights, means, variances, ll = gmm_em(X, [1., 5.], [4., 4.])
    final_scores = log_joint(X, weights, means, variances)
    final_resp = np.exp(final_scores - logsumexp(final_scores)[:, None])
    assert np.all(np.diff(ll) >= -1e-12)
    print("k-means centers:", centers)
    print("k-means labels:", labels)
    print("k-means SSE:", round(sse, 6))
    print("initial GMM P(left | x=2):", round(initial_resp[2, 0], 6))
    print("final GMM weights:", np.round(weights, 6))
    print("final GMM means:", np.round(means, 6))
    print("final GMM variances:", np.round(variances, 6))
    print("final GMM P(left | x=2):", round(final_resp[2, 0], 6))
    print("GMM log-likelihood: %.6f -> %.6f" % (ll[0], ll[-1]))
    print("nondecreasing likelihood:", bool(np.all(np.diff(ll) >= -1e-12)))
