"""Two evaluation traps on synthetic data. Requires NumPy only."""

import numpy as np


def group_overlap_demo():
    rng = np.random.default_rng(17)
    groups = np.repeat(np.arange(100), 10)
    group_labels = rng.integers(0, 2, size=100)
    y = group_labels[groups]
    order = rng.permutation(len(y))
    splits = {
        "random rows": (order[:800], order[800:]),
        "unseen groups": (
            np.flatnonzero(groups < 80),
            np.flatnonzero(groups >= 80),
        ),
    }

    for name, (train, valid) in splits.items():
        remembered = {
            int(g): int(y[train][groups[train] == g].mean() >= 0.5)
            for g in np.unique(groups[train])
        }
        fallback = int(y[train].mean() >= 0.5)
        pred = np.array([remembered.get(int(g), fallback) for g in groups[valid]])
        shared = len(set(groups[train]) & set(groups[valid]))
        accuracy = np.mean(pred == y[valid])
        if name == "unseen groups":
            assert shared == 0
        else:
            assert accuracy == 1.0
        print(f"{name}: accuracy={accuracy:.3f}, shared groups={shared}")


def feature_selection_demo():
    rng = np.random.default_rng(23)
    X = rng.normal(size=(400, 2000))
    y = rng.choice([-1.0, 1.0], size=400)
    train, valid = np.arange(200), np.arange(200, 400)

    def evaluate(selection_rows):
        # Unnormalized feature/label association, used only to rank columns.
        associations = np.abs(X[selection_rows].T @ y[selection_rows])
        columns = np.argsort(associations)[-25:]
        A, B = X[train][:, columns], X[valid][:, columns]
        center, target_mean = A.mean(axis=0), y[train].mean()
        A = A - center
        # A ridge least-squares classifier; all fitting uses training rows.
        weights = np.linalg.solve(
            A.T @ A + np.eye(25), A.T @ (y[train] - target_mean)
        )
        pred = np.where((B - center) @ weights + target_mean >= 0, 1.0, -1.0)
        return np.mean(pred == y[valid])

    print(f"selection sees validation labels: accuracy={evaluate(np.arange(400)):.3f}")
    print(f"selection uses training only: accuracy={evaluate(train):.3f}")


if __name__ == "__main__":
    group_overlap_demo()
    feature_selection_demo()
