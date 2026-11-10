#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>

using i64 = std::int64_t;

// Public positions are zero-based; the Fenwick array is one-based.
class Fenwick {
    int n_;
    std::vector<i64> bit_;
public:
    explicit Fenwick(int n) : n_(n), bit_(n + 1) { assert(n >= 1); }
    void add(int pos, i64 delta) {
        assert(0 <= pos && pos < n_);
        for (int i = pos + 1; i <= n_; i += i & -i) bit_[i] += delta;
    }
    i64 prefix(int end) const { // sum [0,end)
        assert(0 <= end && end <= n_);
        i64 result = 0;
        for (int i = end; i > 0; i -= i & -i) result += bit_[i];
        return result;
    }
    i64 sum(int l, int r) const {
        assert(0 <= l && l <= r && r <= n_);
        return prefix(r) - prefix(l);
    }
};

// Range add and range sum with two Fenwick trees.
class RangeFenwick {
    int n_;
    Fenwick b1_, b2_;
    void boundary(int pos, i64 delta) {
        if (pos == n_) return; // difference-array sentinel is outside storage
        b1_.add(pos, delta);
        b2_.add(pos, delta * pos);
    }
public:
    explicit RangeFenwick(int n) : n_(n), b1_(n), b2_(n) {}
    void add(int l, int r, i64 delta) {
        assert(0 <= l && l <= r && r <= n_);
        if (l == r) return;
        boundary(l, delta);
        boundary(r, -delta);
    }
    i64 prefix(int end) const {
        assert(0 <= end && end <= n_);
        return end * b1_.prefix(end) - b2_.prefix(end);
    }
    i64 sum(int l, int r) const {
        assert(0 <= l && l <= r && r <= n_);
        return prefix(r) - prefix(l);
    }
};

// An iterative segment tree for any associative operation with identity.
// The left and right accumulators preserve order for noncommutative ops.
template <class T, class Op>
class SegTree {
    int n_, size_ = 1;
    T identity_;
    Op op_;
    std::vector<T> tree_;
public:
    SegTree(const std::vector<T>& input, T identity, Op op)
        : n_(static_cast<int>(input.size())), identity_(identity), op_(op) {
        assert(n_ >= 1);
        while (size_ < n_) size_ *= 2;
        tree_.assign(2 * size_, identity_);
        for (int i = 0; i < n_; ++i) tree_[size_ + i] = input[i];
        for (int i = size_ - 1; i > 0; --i)
            tree_[i] = op_(tree_[2*i], tree_[2*i+1]);
    }
    void set(int pos, T value) {
        assert(0 <= pos && pos < n_);
        int i = size_ + pos;
        tree_[i] = value;
        while (i > 1) {
            i /= 2;
            tree_[i] = op_(tree_[2*i], tree_[2*i+1]);
        }
    }
    T fold(int l, int r) const {
        assert(0 <= l && l <= r && r <= n_);
        T left = identity_, right = identity_;
        for (l += size_, r += size_; l < r; l /= 2, r /= 2) {
            if (l & 1) left = op_(left, tree_[l++]);
            if (r & 1) right = op_(tree_[--r], right);
        }
        return op_(left, right);
    }
};

// Range add and range sum. Each node owns [lo,hi), its sum, and a pending add.
class LazySum {
    struct Node { i64 sum = 0, add = 0; };
    int n_;
    std::vector<Node> t_;
    void apply(int p, int lo, int hi, i64 delta) {
        t_[p].sum += delta * (hi - lo);
        t_[p].add += delta;
    }
    void push(int p, int lo, int hi) {
        if (t_[p].add == 0 || hi - lo == 1) return;
        int mid = lo + (hi - lo)/2;
        apply(2*p, lo, mid, t_[p].add);
        apply(2*p+1, mid, hi, t_[p].add);
        t_[p].add = 0;
    }
    void add(int p, int lo, int hi, int l, int r, i64 delta) {
        if (r <= lo || hi <= l) return;
        if (l <= lo && hi <= r) { apply(p, lo, hi, delta); return; }
        push(p, lo, hi);
        int mid = lo + (hi - lo)/2;
        add(2*p, lo, mid, l, r, delta);
        add(2*p+1, mid, hi, l, r, delta);
        t_[p].sum = t_[2*p].sum + t_[2*p+1].sum;
    }
    i64 sum(int p, int lo, int hi, int l, int r) {
        if (r <= lo || hi <= l) return 0;
        if (l <= lo && hi <= r) return t_[p].sum;
        push(p, lo, hi);
        int mid = lo + (hi - lo)/2;
        return sum(2*p, lo, mid, l, r) + sum(2*p+1, mid, hi, l, r);
    }
public:
    explicit LazySum(int n) : n_(n), t_(4*n) { assert(n >= 1); }
    void add(int l, int r, i64 delta) {
        assert(0 <= l && l <= r && r <= n_);
        if (l < r) add(1, 0, n_, l, r, delta);
    }
    i64 sum(int l, int r) {
        assert(0 <= l && l <= r && r <= n_);
        return l == r ? 0 : sum(1, 0, n_, l, r);
    }
};

int main() {
    std::mt19937 rng(20261110);
    auto plus = [](i64 a, i64 b) { return a + b; };
    auto concat = [](const std::string& a, const std::string& b) { return a + b; };
    for (int n : {1, 7, 8, 13}) {
        std::vector<i64> point(n), range(n);
        std::vector<std::string> letters(n, "a");
        Fenwick bit(n);
        RangeFenwick two(n);
        SegTree<i64, decltype(plus)> seg(point, 0, plus);
        SegTree<std::string, decltype(concat)> words(letters, "", concat);
        LazySum lazy(n);
        for (int step = 0; step < 2500; ++step) {
            int pos = static_cast<int>(rng() % n);
            int l = static_cast<int>(rng() % (n + 1));
            int r = static_cast<int>(rng() % (n + 1));
            if (l > r) std::swap(l, r);
            i64 value = static_cast<int>(rng() % 41) - 20;
            if (step % 3 == 0) {
                i64 delta = value - point[pos];
                point[pos] = value;
                bit.add(pos, delta);
                seg.set(pos, value);
                letters[pos] = std::string(1, char('a' + (rng() % 26)));
                words.set(pos, letters[pos]);
            } else if (step % 3 == 1) {
                for (int i = l; i < r; ++i) range[i] += value;
                two.add(l, r, value);
                lazy.add(l, r, value);
            } else {
                i64 expected_point = std::accumulate(point.begin()+l, point.begin()+r, i64{0});
                i64 expected_range = std::accumulate(range.begin()+l, range.begin()+r, i64{0});
                assert(bit.sum(l, r) == expected_point);
                assert(seg.fold(l, r) == expected_point);
                assert(two.sum(l, r) == expected_range);
                assert(lazy.sum(l, r) == expected_range);
                std::string expected_words;
                for (int i = l; i < r; ++i) expected_words += letters[i];
                assert(words.fold(l, r) == expected_words);
            }
        }
        // Explicit whole, empty, and singleton ranges after mixed updates.
        for (int l = 0; l <= n; ++l) for (int r = l; r <= n; ++r) {
            assert(bit.sum(l, r) == std::accumulate(point.begin()+l, point.begin()+r, i64{0}));
            assert(seg.fold(l, r) == bit.sum(l, r));
            assert(two.sum(l, r) == std::accumulate(range.begin()+l, range.begin()+r, i64{0}));
            assert(lazy.sum(l, r) == two.sum(l, r));
        }
        std::cout << "n=" << n << ": checks passed\n";
    }
}
