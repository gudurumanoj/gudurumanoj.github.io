"""Illustrative P/D KV handoff and decode-KV capacity calculator.

Run: python3 handoff_calculator.py
Requires NumPy and Matplotlib for the SVG plot; --no-plot uses only the standard library.
Every rate and queue delay is an input assumption, not a GPU benchmark.
GiB means 2**30 bytes. GiB/s is an EFFECTIVE shared-fabric budget.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from math import ceil, floor
from pathlib import Path

GIB = 2**30


@dataclass(frozen=True)
class Assumptions:
    gqa_layers: int = 40
    kv_heads: int = 8
    head_dim: int = 128
    mla_layers: int = 0
    mla_latent: int = 512
    mla_rope: int = 64
    bytes_per_value: int = 2
    block_tokens: int = 16
    reserved_decode_tokens: int = 512
    kv_pool_gib: float = 16.0
    effective_fabric_gibps: float = 25.0
    concurrent_transfers: int = 1
    wire_copies: int = 1
    setup_ms: float = 3.0
    overlap_ms: float = 0.0
    queue_aggregated_ms: float = 20.0
    queue_prefill_ms: float = 35.0
    queue_decode_ms: float = 10.0
    aggregated_us_per_token: float = 40.0
    disaggregated_us_per_token: float = 25.0
    aggregated_ns_per_token2: float = 1.0
    disaggregated_ns_per_token2: float = 0.7

    @property
    def bytes_per_token(self) -> int:
        conventional = self.gqa_layers * 2 * self.kv_heads * self.head_dim
        latent = self.mla_layers * (self.mla_latent + self.mla_rope)
        return (conventional + latent) * self.bytes_per_value

    def validate(self) -> None:
        positive_ints = (self.kv_heads, self.head_dim, self.mla_latent,
                         self.mla_rope, self.bytes_per_value, self.block_tokens,
                         self.concurrent_transfers, self.wire_copies)
        if any(v <= 0 for v in positive_ints):
            raise ValueError("heads, dimensions, bytes, blocks, flows, and copies must be positive")
        if min(self.gqa_layers, self.mla_layers, self.reserved_decode_tokens) < 0:
            raise ValueError("layer counts and reserved decode tokens cannot be negative")
        if self.gqa_layers + self.mla_layers == 0:
            raise ValueError("at least one attention layer is required")
        if self.kv_pool_gib <= 0 or self.effective_fabric_gibps <= 0:
            raise ValueError("KV pool and effective fabric bandwidth must be positive")
        delays = (self.setup_ms, self.overlap_ms, self.queue_aggregated_ms,
                  self.queue_prefill_ms, self.queue_decode_ms,
                  self.aggregated_us_per_token, self.disaggregated_us_per_token,
                  self.aggregated_ns_per_token2, self.disaggregated_ns_per_token2)
        if any(v < 0 for v in delays):
            raise ValueError("delay and work coefficients cannot be negative")


def calculate(prompt_tokens: int, a: Assumptions, flows: int | None = None) -> dict[str, float]:
    if prompt_tokens <= 0:
        raise ValueError("prompt_tokens must be positive")
    active_flows = a.concurrent_transfers if flows is None else flows
    if active_flows <= 0:
        raise ValueError("flows must be positive")
    logical_gib = prompt_tokens * a.bytes_per_token / GIB
    wire_gib = logical_gib * a.wire_copies
    blocks = ceil((prompt_tokens + a.reserved_decode_tokens) / a.block_tokens)
    reserved_gib = blocks * a.block_tokens * a.bytes_per_token / GIB
    transfer_ms = a.setup_ms + 1000 * wire_gib * active_flows / a.effective_fabric_gibps
    aggregated_prefill_ms = (prompt_tokens * a.aggregated_us_per_token / 1000 +
                             prompt_tokens**2 * a.aggregated_ns_per_token2 / 1e6)
    disaggregated_prefill_ms = (prompt_tokens * a.disaggregated_us_per_token / 1000 +
                                prompt_tokens**2 * a.disaggregated_ns_per_token2 / 1e6)
    aggregated_ready_ms = a.queue_aggregated_ms + aggregated_prefill_ms
    split_ready_ms = (a.queue_prefill_ms + disaggregated_prefill_ms +
                      a.queue_decode_ms + max(0.0, transfer_ms - a.overlap_ms))
    return {
        "logical_gib": logical_gib,
        "wire_gib": wire_gib,
        "blocks": float(blocks),
        "reserved_gib": reserved_gib,
        "max_contexts": float(floor(a.kv_pool_gib / reserved_gib)),
        "transfer_ms": transfer_ms,
        "aggregated_prefill_ms": aggregated_prefill_ms,
        "disaggregated_prefill_ms": disaggregated_prefill_ms,
        "aggregated_ready_ms": aggregated_ready_ms,
        "split_ready_ms": split_ready_ms,
        "saving_ms": aggregated_ready_ms - split_ready_ms,
        "ideal_fabric_rps": a.effective_fabric_gibps / wire_gib,
    }


def draw_figure(a: Assumptions, destination: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    lengths = np.arange(128, 8193, 128)
    single = [calculate(int(n), a, 1) for n in lengths]
    four = [calculate(int(n), a, 4) for n in lengths]
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 3.8), layout="constrained")
    fig.patch.set_facecolor("#fdfcf8")
    for ax in axes:
        ax.set_facecolor("#fdfcf8")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.18)
    axes[0].plot(lengths, [r["aggregated_ready_ms"] for r in single], lw=2,
                 color="#2d2a23", label="co-located")
    axes[0].plot(lengths, [r["split_ready_ms"] for r in single], lw=2,
                 color="#417e82", label="split, 1 active transfer")
    axes[0].plot(lengths, [r["split_ready_ms"] for r in four], lw=2,
                 color="#a66b4f", label="split, 4 sharing fabric")
    axes[0].set(xlabel="prompt tokens", ylabel="ready for next decode (ms)",
                title="A queue and shared-link tradeoff")
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].step(lengths, [r["max_contexts"] for r in single], where="post",
                 color="#a66b4f", lw=2)
    axes[1].set(xlabel="prompt tokens", ylabel="maximum reserved contexts",
                title="16 GiB decode KV pool; 512 future tokens reserved")
    fig.savefig(destination, bbox_inches="tight", metadata={
        "Title": "Illustrative prefill/decode readiness and KV capacity",
        "Description": "One-flow and four-flow transfer assumptions compared with co-located serving; a separate step curve shows destination KV capacity."
    })
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokens", type=int, default=4096)
    parser.add_argument("--gqa-layers", type=int, default=40)
    parser.add_argument("--kv-heads", type=int, default=8)
    parser.add_argument("--head-dim", type=int, default=128)
    parser.add_argument("--mla-layers", type=int, default=0)
    parser.add_argument("--mla-latent", type=int, default=512)
    parser.add_argument("--mla-rope", type=int, default=64)
    parser.add_argument("--bytes-per-value", type=int, default=2)
    parser.add_argument("--block-tokens", type=int, default=16)
    parser.add_argument("--reserve-decode-tokens", type=int, default=512)
    parser.add_argument("--kv-pool-gib", type=float, default=16)
    parser.add_argument("--effective-gibps", type=float, default=25)
    parser.add_argument("--concurrent-transfers", type=int, default=1)
    parser.add_argument("--wire-copies", type=int, default=1)
    parser.add_argument("--setup-ms", type=float, default=3)
    parser.add_argument("--overlap-ms", type=float, default=0)
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()
    a = Assumptions(
        gqa_layers=args.gqa_layers, kv_heads=args.kv_heads,
        head_dim=args.head_dim, mla_layers=args.mla_layers,
        mla_latent=args.mla_latent, mla_rope=args.mla_rope,
        bytes_per_value=args.bytes_per_value, block_tokens=args.block_tokens,
        reserved_decode_tokens=args.reserve_decode_tokens,
        kv_pool_gib=args.kv_pool_gib,
        effective_fabric_gibps=args.effective_gibps,
        concurrent_transfers=args.concurrent_transfers,
        wire_copies=args.wire_copies, setup_ms=args.setup_ms,
        overlap_ms=args.overlap_ms,
    )
    a.validate()
    result = calculate(args.tokens, a)
    assert a.bytes_per_token > 0 and result["reserved_gib"] >= result["logical_gib"]
    print("ILLUSTRATIVE INPUTS, not measured GPU results")
    print(f"KV bytes/token={a.bytes_per_token:,} ({a.bytes_per_token/1024:.1f} KiB)")
    copy_label = "copy" if a.wire_copies == 1 else "copies"
    print(f"prompt={args.tokens:,}; logical KV={result['logical_gib']:.6f} GiB; "
          f"wire={result['wire_gib']:.6f} GiB ({a.wire_copies} {copy_label})")
    print(f"destination reserve={int(result['blocks'])} blocks x {a.block_tokens} tokens "
          f"= {result['reserved_gib']:.6f} GiB/context")
    print(f"{a.kv_pool_gib:g} GiB KV pool fits at most {int(result['max_contexts'])} "
          "such reserved contexts (ignores shared prefixes and other allocations)")
    print(f"transfer={result['transfer_ms']:.3f} ms with "
          f"{a.concurrent_transfers} active transfer(s), "
          f"{a.effective_fabric_gibps:g} GiB/s effective SHARED fabric")
    print(f"next-decode-ready: co-located={result['aggregated_ready_ms']:.3f} ms; "
          f"split={result['split_ready_ms']:.3f} ms; "
          f"co-located minus split={result['saving_ms']:.3f} ms")
    print(f"ideal no-overhead fabric ceiling={result['ideal_fabric_rps']:.3f} "
          "same-size handoffs/s before other traffic")
    if not args.no_plot:
        destination = Path(__file__).with_name("handoff-tradeoff.svg")
        draw_figure(a, destination)
        print(f"wrote {destination.name}")


if __name__ == "__main__":
    main()
