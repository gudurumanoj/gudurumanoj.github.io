#include <algorithm>
#include <cassert>
#include <climits>
#include <deque>
#include <functional>
#include <iostream>
#include <queue>
#include <string>
#include <utility>
#include <vector>
using namespace std;

using ll = long long;
const ll INF = LLONG_MAX / 4;
struct Edge { int u, v; ll w; };
struct Result {
    vector<ll> dist;
    vector<int> parent;
    vector<char> neg;  // reachable from a reachable negative cycle
};

void check_input(int n, const vector<Edge>& edges, int s) {
    assert(1 <= n && n <= 100000 && 0 <= s && s < n);
    for (auto e : edges) {
        assert(0 <= e.u && e.u < n && 0 <= e.v && e.v < n);
        assert(-1000000000LL <= e.w && e.w <= 1000000000LL);
    }
}

vector<vector<pair<int, ll>>> adjacency(int n, const vector<Edge>& edges) {
    vector<vector<pair<int, ll>>> adj(n);
    for (auto e : edges) adj[e.u].push_back({e.v, e.w});
    return adj;
}

vector<ll> bfs_unit(int n, const vector<Edge>& edges, int s) {
    check_input(n, edges, s);
    for (auto e : edges) assert(e.w == 1);
    auto adj = adjacency(n, edges);
    vector<ll> dist(n, INF);
    queue<int> q;
    dist[s] = 0;
    q.push(s);
    while (!q.empty()) {
        int u = q.front(); q.pop();
        for (auto [v, w] : adj[u]) {
            if (dist[v] != INF) continue;
            dist[v] = dist[u] + w;
            q.push(v);
        }
    }
    return dist;
}

vector<ll> zero_one_bfs(int n, const vector<Edge>& edges, int s) {
    check_input(n, edges, s);
    for (auto e : edges) assert(e.w == 0 || e.w == 1);
    auto adj = adjacency(n, edges);
    vector<ll> dist(n, INF);
    deque<pair<ll, int>> dq;
    dist[s] = 0;
    dq.push_front({0, s});
    while (!dq.empty()) {
        auto [d, u] = dq.front(); dq.pop_front();
        if (d != dist[u]) continue;
        for (auto [v, w] : adj[u]) {
            if (d + w >= dist[v]) continue;
            dist[v] = d + w;
            if (w == 0) dq.push_front({dist[v], v});
            else dq.push_back({dist[v], v});
        }
    }
    return dist;
}

Result dijkstra(int n, const vector<Edge>& edges, int s) {
    check_input(n, edges, s);
    for (auto e : edges) assert(e.w >= 0);
    auto adj = adjacency(n, edges);
    Result out{vector<ll>(n, INF), vector<int>(n, -1), vector<char>(n, 0)};
    priority_queue<pair<ll, int>, vector<pair<ll, int>>, greater<pair<ll, int>>> pq;
    out.dist[s] = 0;
    pq.push({0, s});
    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        if (d != out.dist[u]) continue;  // discard an obsolete heap entry
        for (auto [v, w] : adj[u]) {
            if (d + w >= out.dist[v]) continue;
            out.dist[v] = d + w;
            out.parent[v] = u;
            pq.push({out.dist[v], v});
        }
    }
    return out;
}

Result bellman_ford(int n, const vector<Edge>& edges, int s) {
    check_input(n, edges, s);
    Result out{vector<ll>(n, INF), vector<int>(n, -1), vector<char>(n, 0)};
    out.dist[s] = 0;
    for (int pass = 1; pass < n; ++pass) {
        auto next = out.dist;           // read only the previous pass
        auto next_parent = out.parent;
        bool changed = false;
        for (auto e : edges) {
            if (out.dist[e.u] == INF) continue;
            ll candidate = out.dist[e.u] + e.w;
            if (candidate < next[e.v]) {
                next[e.v] = candidate;
                next_parent[e.v] = e.u;
                changed = true;
            }
        }
        out.dist.swap(next);
        out.parent.swap(next_parent);
        if (!changed) break;
    }
    vector<vector<int>> adj(n);
    for (auto e : edges) adj[e.u].push_back(e.v);
    queue<int> q;
    for (auto e : edges) {
        if (out.dist[e.u] == INF) continue;
        if (out.dist[e.u] + e.w < out.dist[e.v] && !out.neg[e.v]) {
            out.neg[e.v] = 1;
            q.push(e.v);
        }
    }
    while (!q.empty()) {
        int u = q.front(); q.pop();
        for (int v : adj[u]) if (!out.neg[v]) {
            out.neg[v] = 1;
            q.push(v);
        }
    }
    return out;
}

vector<int> path_to(const Result& r, int s, int t) {
    assert(0 <= s && s < static_cast<int>(r.dist.size()));
    assert(0 <= t && t < static_cast<int>(r.dist.size()));
    if (r.dist[t] == INF || r.neg[t]) return {};
    vector<int> path;
    for (int v = t; v != -1; v = r.parent[v]) {
        path.push_back(v);
        if (v == s) {
            reverse(path.begin(), path.end());
            return path;
        }
        assert(path.size() <= r.dist.size());
    }
    return {};  // finite reachable vertices should never arrive here
}

void print_path(const vector<int>& path) {
    if (path.empty()) { cout << "no finite shortest path"; return; }
    for (size_t i = 0; i < path.size(); ++i)
        cout << (i ? "->" : "") << path[i];
}

int main() {
    vector<Edge> positive = {{0,1,4}, {0,2,1}, {2,1,2}, {1,3,1},
                             {2,3,5}, {3,4,3}, {2,4,10}};
    auto d = dijkstra(6, positive, 0);
    auto b_positive = bellman_ford(6, positive, 0);
    assert(d.dist == b_positive.dist && d.dist[4] == 7);
    assert(path_to(d, 0, 4) == vector<int>({0,2,1,3,4}));
    assert(path_to(d, 0, 5).empty());
    cout << "Dijkstra 0->4: distance=" << d.dist[4] << " path=";
    print_path(path_to(d, 0, 4)); cout << '\n';
    cout << "Dijkstra 0->5: "; print_path(path_to(d, 0, 5)); cout << '\n';

    vector<Edge> negative = {{0,1,4}, {0,2,5}, {1,2,-2},
                             {2,3,3}, {0,4,7}, {5,5,-1}};
    auto b = bellman_ford(6, negative, 0);
    assert(b.dist[3] == 5 && !b.neg[3]);
    assert(path_to(b, 0, 3) == vector<int>({0,1,2,3}));
    assert(b.dist[5] == INF && !b.neg[5]); // unreachable cycle is irrelevant
    cout << "Bellman-Ford 0->3: distance=" << b.dist[3] << " path=";
    print_path(path_to(b, 0, 3)); cout << '\n';

    negative.push_back({2,1,1}); // cycle 1->2->1 has weight -1
    auto cycle = bellman_ford(6, negative, 0);
    assert(!cycle.neg[0] && cycle.neg[1] && cycle.neg[2] && cycle.neg[3]);
    assert(!cycle.neg[4] && cycle.dist[4] == 7 && !cycle.neg[5]);
    assert(path_to(cycle, 0, 3).empty());
    cout << "reachable negative cycle: 1,2,3=-INF; 4=" << cycle.dist[4]
         << "; 5=unreachable\n";

    auto unit = bfs_unit(4, {{0,1,1},{0,2,1},{2,3,1}}, 0);
    auto binary = zero_one_bfs(4, {{0,1,1},{0,2,0},{2,1,0},{1,3,1}}, 0);
    assert(unit[3] == 2 && binary[3] == 1);
    cout << "BFS target=" << unit[3] << "; 0-1 BFS target=" << binary[3] << '\n';
}
