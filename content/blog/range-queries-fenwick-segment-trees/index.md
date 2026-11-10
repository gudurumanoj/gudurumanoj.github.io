---
title: "Range Queries: Fenwick Trees, Segment Trees, and Lazy Updates"
date: 2026-11-10T10:00:00+05:30
draft: true
topics: ["cp", "cpp"]
tags: ["range-queries", "data-structures", "interview"]
summary: "A single invariant explains each tree: Fenwick nodes store suffix-sized blocks, segment nodes store interval folds, and lazy tags summarize work deferred to children."
references:
  - id: fenwick-paper
    text: 'Peter M. Fenwick. "A New Data Structure for Cumulative Frequency Tables." Software: Practice and Experience 24(3), 327–336, 1994.'
    url: https://doi.org/10.1002/spe.4380240306
  - id: acl-bit
    text: 'AtCoder Library. "Fenwick Tree" documentation.'
    url: https://atcoder.github.io/ac-library/production/document_en/fenwicktree.html
  - id: acl-seg
    text: 'AtCoder Library. "Segtree" documentation.'
    url: https://atcoder.github.io/ac-library/production/document_en/segtree.html
  - id: acl-lazy
    text: 'AtCoder Library. "Lazy Segtree" documentation.'
    url: https://atcoder.github.io/ac-library/production/document_en/lazysegtree.html
---

A static prefix-sum array makes `sum(l, r)` almost trivial: precompute $P[k]=a_0+\cdots+a_{k-1}$ and return $P[r]-P[l]$. The trouble starts when values change. Replacing one $a_i$ changes every later prefix, so a straightforward prefix array costs $O(n)$ per update. I want the same half-open public interface, $[l,r)$, while balancing updates and queries at $O(\log n)$.

Fenwick and segment trees do this by storing sums of selected intervals. Their useful differences come from *which* intervals they store and *which algebraic operations* they support. I find it easier to remember the invariant than the loop indices. Below I use one array of signed 64-bit integers, zero-based positions in every public method, and half-open ranges throughout. I assume the inputs and intermediate sums fit in `int64_t`; signed overflow is not part of the intended domain.

If prefix sums are new, [the prefix-sums post](/blog/prefix-sums/) develops them first. The decision to store just enough reusable state resembles [dynamic programming state transitions](/blog/dynamic-programming-state-transitions/): each stored value has a precise meaning, and every update must restore that meaning.

## Begin with the update/query tradeoff

There is no magic in a tree. A plain array gives $O(1)$ point assignment and $O(n)$ range sum. A prefix array gives $O(1)$ range sum but $O(n)$ point assignment. The trees introduce $O(n)$ storage and make each operation logarithmic. That is a good trade if I expect many interleaved updates and queries; for read-only data, prefix sums are simpler and faster.

| Structure | Point assignment | Sum $[l,r)$ | Range addition | Typical reason to choose it |
|:--|--:|--:|--:|:--|
| Prefix sums | $O(n)$ | $O(1)$ | $O(n)$ | No or very few updates |
| Fenwick tree | $O(\log n)$ via delta | $O(\log n)$ | Two trees for range sum | Compact code for additive data |
| Segment tree | $O(\log n)$ | $O(\log n)$ | Lazy propagation | Other associative folds or rich updates |

The table is about *these implementations*. An $O(n)$ Fenwick build is possible, while the attached simple implementation initializes zero and adds values one at a time for $O(n\log n)$ if starting from a nonzero array. Its segment-tree constructor builds bottom-up in $O(n)$. Both use $O(n)$ memory. Fenwick's original paper addressed cumulative frequency tables; AtCoder's library documents the familiar point-add and interval-sum interface. {{< cite "fenwick-paper" "acl-bit" >}}

## Fenwick: every node owns one binary interval

The internal Fenwick array is one-based. Let `lowbit(i) = i & -i`, the value of the least significant set bit. Internal node $i$ stores the sum of the original values at one-based positions

$$
[i-\operatorname{lowbit}(i)+1,\ i].
$$

For example, node 12 has `lowbit(12)=4`, so it owns positions 9 through 12. Node 8 owns positions 1 through 8. The binary form of $i$ explains the interval length: clearing its lowest one bit jumps to the end of the previous disjoint block. A prefix query at internal endpoint $i$ takes node $i$, then moves to $i-\operatorname{lowbit}(i)$. Those blocks exactly partition positions 1 through $i$, without gaps or overlaps. Each step clears one set bit, so there are at most $O(\log n)$ steps.

```cpp
// Public end is exclusive and zero-based; internal i is one-based.
i64 prefix(int end) const {
    i64 result = 0;
    for (int i = end; i > 0; i -= i & -i) result += bit_[i];
    return result;
}
i64 sum(int l, int r) const { return prefix(r) - prefix(l); }
```

A point addition at zero-based `pos` starts at internal `pos + 1`. Every node that covers this position must change. Repeatedly adding `lowbit(i)` climbs to the next such enclosing block, until the index exceeds $n$. The number of steps is logarithmic. Point *assignment* is not the primitive: if a value changes from `old` to `new`, call `add(pos, new - old)` and maintain the old value separately, as the [attached test program](range_queries.cpp) does.

Why is the upward jump the right one? The current node ends at $i$ and covers a block whose length is its lowest set bit. Adding that length moves to the first later node whose stored block also includes the changed position. Repeating the jump visits every enclosing block that contributes to some future prefix query. This is the update-side dual of the query walk, which removes the current block and moves left. If I ever forget the direction, I draw the actual one-based intervals for a tiny array: queries peel blocks away toward zero, while updates climb through larger enclosing blocks. This interval proof is more reliable than memorizing the `i += i & -i` line alone.

```cpp
void add(int pos, i64 delta) {
    for (int i = pos + 1; i <= n_; i += i & -i) bit_[i] += delta;
}
```

The demonstration lets me change one value and query the same range through Fenwick's two prefix walks and a segment-tree cover. It shows the interval owned by each node, rather than just a final answer.

{{< embed src="demo.html" height="475" caption="Assign a point and query [l,r). The highlighted cells are included; both decompositions must sum to the same result." >}}

Fenwick relies on being able to subtract prefix aggregates to isolate $[l,r)$. That works for sums and, with suitable inverses, other group-like operations. It does **not** give arbitrary range minima as `min(prefix(r)) - min(prefix(l))`; there is no inverse for `min`. A segment tree is the natural next step when the desired fold lacks an inverse.

The two prefix walks may touch overlapping *stored* nodes across separate computations, but algebraically their results cancel the contribution of $[0,l)$. The cancellation is why negative values are fine for sums: the data need not be monotone. It is also why I keep the public endpoint exclusive. `prefix(0)` is exactly zero, `prefix(n)` covers the whole array, and `sum(l,l)` is zero without a special branch. One-based indexing stays an internal detail of the Fenwick representation; leaking it into callers is a frequent source of boundary bugs.

## Range addition with one or two Fenwick trees

A difference array makes the first extension intuitive. Define $D[0]=a[0]$ and $D[i]=a[i]-a[i-1]$ for $i>0$. To add $\delta$ to all values in $[l,r)$, change only $D[l]$ by $+\delta$ and $D[r]$ by $-\delta$ when $r<n$. A Fenwick tree over $D$ can therefore do **range add, point query**: the value at $p$ is the prefix sum of $D$ through $p$. This swaps the roles of query and update. It does not yet produce a range sum of the updated $a$ in one Fenwick query.

Two Fenwick trees recover **range add, range sum**. By reversing the order of summation,

$$P(k)=\sum_{j=0}^{k-1}a_j=\sum_{i=0}^{k-1}(k-i)D_i
= k\sum_{i=0}^{k-1}D_i-\sum_{i=0}^{k-1}iD_i.$$

Store $D_i$ in `b1` and $iD_i$ in `b2`. Then `prefix(k) = k*b1.prefix(k) - b2.prefix(k)`, and `sum(l,r)=prefix(r)-prefix(l)`. A range addition updates both trees at boundary $l$ and, if $r<n$, boundary $r$. When $r=n$, the negative difference sits just past the stored array and can be skipped. An empty range changes neither tree. In the code the public positions remain zero-based; accidentally using one-based coefficients in `b2` is a common off-by-one error.

```cpp
void boundary(int pos, i64 delta) {
    if (pos == n_) return;
    b1_.add(pos, delta);
    b2_.add(pos, delta * pos);
}
void add(int l, int r, i64 delta) {
    if (l == r) return;
    boundary(l, delta);
    boundary(r, -delta);
}
i64 prefix(int k) const { return k * b1_.prefix(k) - b2_.prefix(k); }
```

This is specific to additive updates and sums. It is compact once the identity for $P(k)$ is clear, but less flexible than a lazy segment tree. AtCoder's Fenwick documentation defines a related point-add/range-sum API; the two-tree extension here follows directly from the difference-array derivation. {{< cite "acl-bit" >}}

## Segment tree: fold an interval by parts

A segment tree stores an aggregate for each interval in a binary partition. The root owns $[0,n)$; each internal node splits its interval at a midpoint; leaves hold the individual values. Every internal aggregate equals `op(left, right)`. A range query visits only nodes needed to cover $[l,r)$, using at most two boundary nodes per level, so it costs $O(\log n)$. A point update changes one leaf and recomputes its ancestors in the same time. A bottom-up array representation pads to a power-of-two leaf count; fewer than $4n$ slots suffice for $n\ge1$, including the unused padded leaves.

The abstraction is a **monoid**: an associative operation `op` and an identity `e` such that `op(e,x)=op(x,e)=x`. Sum with zero, minimum with $+\infty$, and string concatenation with the empty string are examples. Associativity lets the tree regroup intervals. Commutativity is **not** required, but the order of left and right intervals must be preserved. AtCoder's segment-tree interface is specified in terms of a monoid for precisely this reason. {{< cite "acl-seg" >}}

This algebraic contract rules out some tempting operations. Subtraction is not associative: $(a-b)-c$ generally differs from $a-(b-c)$, so a tree of partial differences cannot answer an arbitrary range by regrouping its nodes. An operation may also be associative but have the wrong identity in code. For range minimum, initializing unused padded leaves to zero gives wrong answers when all real values are positive; the identity must behave like $+\infty$. For strings, an empty string is an identity and preserves order, but sorting the pieces before concatenation would change the requested operation. Stating the monoid first catches these mistakes before I write a tree.

In the iterative query, `left` collects pieces found from the left and `right` pieces found from the right. A newly found right piece must be **prepended** to `right`, and the final answer is `op(left,right)`. If I append right pieces in discovery order, sums conceal the bug but string concatenation exposes it.

```cpp
T fold(int l, int r) const {
    T left = identity_, right = identity_;
    for (l += size_, r += size_; l < r; l /= 2, r /= 2) {
        if (l & 1) left = op_(left, tree_[l++]);
        if (r & 1) right = op_(tree_[--r], right);
    }
    return op_(left, right);
}
```

The attached program tests this with strings as well as sums. For letters `a,b,c,d`, querying `[1,4)` must yield `bcd`, not `dcb`. A segment tree also answers range minimum after point updates: store the minimum for each node and use $+\infty$ as the identity. Fenwick's prefix subtraction cannot do that. This is a useful way to choose between the structures: ask whether the query can be recovered from invertible prefixes or should be folded from direct interval pieces.

## Lazy propagation: remember work at a covered node

A plain segment tree handles one changed leaf well. Adding $\delta$ to an entire range by updating every leaf costs $O((r-l)\log n)$. Lazy propagation keeps a **pending tag** at a fully covered node. For range addition and range sum, a node represents `(sum, length)`. Applying `add δ` to that node changes its sum by $\delta\cdot\text{length}$ and composes the pending add tag by addition. Its children are allowed to remain stale until a later operation needs to descend into them. AtCoder's lazy segment tree makes this relationship explicit through an aggregate operation, a mapping from tags to aggregates, and tag composition. {{< cite "acl-lazy" >}}

The invariant is not “every child is current.” It is: **the node's sum includes every update affecting its interval**, while its pending tag describes the effect still owed to its descendants. On a partial update or query, `push` applies the pending tag to the children, clears it on the parent, and then descends. After a partial update, `pull` recomputes the parent's sum from its children. A fully covered query can return the node sum immediately, without pushing. Each operation touches at most a constant number of nodes per level, hence $O(\log n)$.

The order of `push` and `pull` matters. Suppose a node covers four values and holds a pending `+2`. If I descend into its left child without first pushing, that child's old sum omits the addition. If I then recompute the parent from the two stale children, I erase the correct parent sum. The code pushes before any partial descent and pulls only after a partial update has finished. A full-cover update instead changes the node aggregate and tag in place. That is why a large range can be updated without visiting every leaf. For a query, pushing may change child aggregates but does not change the already-correct parent aggregate.

```cpp
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
```

For addition alone, composing tags is just adding numbers, so order seems irrelevant. That stops being true when updates include assignment. Think of a tag as a function $f(x)=ax+b$: adding $d$ uses $(a,b)=(1,d)$, assigning $v$ uses $(0,v)$. If an old tag $f$ is followed by new tag $g$, the combined tag is $g\circ f$, with coefficients $(a_g a_f,\ a_g b_f+b_g)$. Assign 5 then add 3 gives 8; add 3 then assign 5 gives 5. Swapping composition order silently changes the result. The node-sum mapping is likewise $S\mapsto aS+b\cdot\text{length}$. My attached implementation supports range addition, so its tag is only `add`; the function view explains how to extend it safely rather than pretending all lazy tags commute.

A related advanced operation is segment-tree `max_right`: walk down to find the greatest endpoint whose prefix fold satisfies a predicate. The predicate must be true at the identity and **monotone** as the range grows in the intended direction. For nonnegative sums, “sum $\le K$” is monotone; with negative values, it is not. A logarithmic tree walk cannot fix a predicate whose truth can flip back and forth. AtCoder documents this condition for its search interface. {{< cite "acl-seg" >}}

## Run and check the implementations

The [complete C++17 file](range_queries.cpp) contains a Fenwick tree, the two-tree range-add variant, an order-preserving generic segment tree, and a lazy range-add/range-sum tree. It compares every result with an ordinary vector after seeded random operations. It deliberately uses sizes 1, 7, 8, and 13 to catch both degenerate and non-power-of-two cases. The operations include negative values, repeated point assignments, range additions, empty ranges, and exhaustive final range checks. The string test checks noncommutative fold order. Compile and run it with:

```bash
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic range_queries.cpp -o range_queries
./range_queries
```

```text
n=1: checks passed
n=7: checks passed
n=8: checks passed
n=13: checks passed
```

These checks verify many examples against a simple reference; they are not a proof for every input. The proof rests on each node's interval invariant, the algebraic requirements of the fold, and the order in which pending tags are composed. The file uses `assert` for preconditions and testing; compile it without `-DNDEBUG` if you want those checks. Production code would need a deliberate policy for invalid indices and arithmetic bounds.

My choice among the structures starts with the workload. If I need only point assignments and additive sums, Fenwick is compact and its two prefix walks are easy to audit. If I need a minimum, an order-sensitive concatenation, or a tree search driven by an associative fold, I choose a segment tree. If the *updates themselves* cover ranges, I decide whether the difference-array identity handles exactly those updates; otherwise I use a lazy tree with explicitly defined mapping and composition. This decision avoids paying the conceptual cost of lazy propagation for a static sum query, while keeping room for richer operations when the problem actually calls for them.

## Questions I would ask in an interview

1. **When do prefix sums beat both trees?** When the array is static or updates are rare enough that $O(n)$ rebuilds are acceptable; queries are then $O(1)$.
2. **What does Fenwick node $i$ store?** The one-based interval from $i-\operatorname{lowbit}(i)+1$ through $i$.
3. **Why does a Fenwick prefix walk terminate in logarithmic steps?** Each subtraction clears the lowest set bit of the endpoint.
4. **How do I turn point assignment into a Fenwick update?** Keep the old value and add `new-old` to the tree.
5. **How does range add, point query use a difference array?** Add at $l$, subtract at $r$ if $r<n$, then take the difference-array prefix through the queried point.
6. **Where does the second Fenwick tree come from?** Expanding $P(k)$ yields $k\sum_{i<k}D_i-\sum_{i<k}iD_i$; each sum has its own tree.
7. **Why can't I subtract two prefix minima?** Minimum has no inverse that removes earlier elements from an aggregate.
8. **What properties does a segment-tree operation need?** Associativity and an identity; commutativity is optional if interval order is kept.
9. **Why does an iterative fold need two accumulators?** Right-edge pieces are discovered in reverse order, so they must be prepended before combining with left pieces.
10. **What exactly is lazy at a node?** Its aggregate is current, while its children may still need the node's pending mapping applied.
11. **Why does tag composition order matter?** Assignment and addition do not commute: assign 5 then add 3 yields 8, while the reverse yields 5.
12. **When is `max_right` with a sum threshold unsafe?** When negative numbers let a growing prefix cross the threshold and later cross back; the predicate is not monotone.

{{< references >}}
