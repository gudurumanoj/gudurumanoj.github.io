"""A reproducible Welch two-sample t test; requires NumPy and SciPy."""

import numpy as np
from scipy import stats


group_a = np.array([12, 11, 13, 12, 14, 10, 13, 15], dtype=float)
group_b = np.array([10, 11, 12, 10, 9, 13, 8, 12, 11, 13, 9, 11], dtype=float)

n_a, n_b = len(group_a), len(group_b)
mean_difference = group_a.mean() - group_b.mean()
var_a = group_a.var(ddof=1)
var_b = group_b.var(ddof=1)
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
