"""Small retrieval/ranking example; requires only NumPy."""

import numpy as np

names = np.array(["A", "B", "C", "D", "E"])
query = np.array([1.0, 0.0])
items = np.array([
    [0.95, 0.0],
    [0.85, 0.2],
    [0.80, 0.1],
    [0.30, 0.9],
    [0.20, 1.0],
])
relevant = {"B", "E"}
ranker_score = np.array([0.2, 0.9, 0.1, 0.8, 1.5])

retrieval_score = items @ query
candidates = np.argsort(-retrieval_score, kind="stable")[:3]
K = 2
final = candidates[np.argsort(-ranker_score[candidates], kind="stable")[:K]]
full_catalog = np.argsort(-ranker_score, kind="stable")[:K]
relevant_candidates = len(set(names[candidates]) & relevant)
best_possible_recall = min(K, relevant_candidates) / len(relevant)


def recall(indices):
    return len(set(names[indices]) & relevant) / len(relevant)


print("retrieved:", ", ".join(names[candidates]))
print(f"candidate recall: {recall(candidates):.2f}")
print("ranked top 2:", ", ".join(names[final]))
print(f"final recall: {recall(final):.2f}")
print(f"best possible final recall from candidates: {best_possible_recall:.2f}")
print("full-catalog top 2:", ", ".join(names[full_catalog]))
print(f"full-catalog recall: {recall(full_catalog):.2f}")
