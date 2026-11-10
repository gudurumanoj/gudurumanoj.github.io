#include <algorithm>
#include <cassert>
#include <iostream>
#include <string>
#include <utility>
#include <vector>
using namespace std;

struct Item { int weight; long long value; string name; };

pair<long long, vector<int>> knapsack_full(const vector<Item>& items, int cap) {
    int n = static_cast<int>(items.size());
    vector<vector<long long>> dp(n + 1, vector<long long>(cap + 1, 0));
    for (int i = 1; i <= n; ++i) {
        const auto& item = items[i - 1];
        assert(item.weight > 0);
        for (int c = 0; c <= cap; ++c) {
            dp[i][c] = dp[i - 1][c];
            if (c >= item.weight)
                dp[i][c] = max(dp[i][c], item.value + dp[i - 1][c - item.weight]);
        }
    }
    vector<int> chosen;
    for (int i = n, c = cap; i > 0; --i) {
        if (dp[i][c] != dp[i - 1][c]) {
            chosen.push_back(i - 1);
            c -= items[i - 1].weight;
        }
    }
    reverse(chosen.begin(), chosen.end());
    return {dp[n][cap], chosen};
}

long long knapsack_compressed(const vector<Item>& items, int cap) {
    vector<long long> dp(cap + 1, 0);
    for (const auto& item : items) {
        assert(item.weight > 0);
        for (int c = cap; c >= item.weight; --c)
            dp[c] = max(dp[c], item.value + dp[c - item.weight]);
    }
    return dp[cap];
}

long long brute_knapsack(const vector<Item>& items, int cap) {
    assert(items.size() <= 20);
    long long best = 0;
    for (unsigned mask = 0; mask < (1u << items.size()); ++mask) {
        long long weight = 0;
        long long value = 0;
        for (size_t i = 0; i < items.size(); ++i)
            if (mask & (1u << i)) {
                weight += items[i].weight;
                value += items[i].value;
            }
        if (weight <= cap) best = max(best, value);
    }
    return best;
}

int edit_distance(const string& a, const string& b) {
    int n = static_cast<int>(a.size()), m = static_cast<int>(b.size());
    vector<vector<int>> dp(n + 1, vector<int>(m + 1));
    for (int i = 0; i <= n; ++i) dp[i][0] = i;
    for (int j = 0; j <= m; ++j) dp[0][j] = j;
    for (int i = 1; i <= n; ++i)
        for (int j = 1; j <= m; ++j)
            dp[i][j] = min({dp[i - 1][j] + 1, dp[i][j - 1] + 1,
                            dp[i - 1][j - 1] + (a[i - 1] != b[j - 1])});
    return dp[n][m];
}

int main() {
    vector<Item> items = {{2, 3, "A"}, {3, 4, "B"}, {4, 5, "C"}, {5, 8, "D"}};
    for (int c = 0; c <= 8; ++c) {
        assert(knapsack_full(items, c).first == brute_knapsack(items, c));
        assert(knapsack_compressed(items, c) == brute_knapsack(items, c));
    }
    assert(knapsack_full({}, 8).first == 0);
    assert(edit_distance("", "abc") == 3);
    assert(edit_distance("abc", "abc") == 0);

    auto [best, chosen] = knapsack_full(items, 8);
    cout << "capacity=8 optimum=" << best << " items=";
    for (size_t k = 0; k < chosen.size(); ++k)
        cout << (k ? "," : "") << items[chosen[k]].name;
    cout << "\ncompressed=" << knapsack_compressed(items, 8) << '\n';
    cout << "density greedy=11 (D,A)\n";

    vector<long long> forward(9, 0);
    for (int c = 2; c <= 8; ++c) forward[c] = max(forward[c], 3 + forward[c - 2]);
    cout << "forward-one-item=" << forward[8]
         << " 0/1-one-item=" << knapsack_compressed({items[0]}, 8) << '\n';
    cout << "edit kitten -> sitting=" << edit_distance("kitten", "sitting") << '\n';
}
