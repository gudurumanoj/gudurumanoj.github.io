"""Original teaching trace: retained agent KV versus interleaving width.

This counts uncached input tokens, NOT latency, FLOPs, or GPU throughput.
Session IDs stand in for distinct exact token histories. Entries contain a
whole session's reusable prefix; eviction is deliberately coarser than paged KV.
The budget covers retained state between calls, not active execution memory.
No tool durations, scheduling fairness, cross-session sharing, or network model.

Run: python3 workload_cache.py
Plot (requires matplotlib): python3 workload_cache.py --plot
"""

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
import argparse


@dataclass(frozen=True)
class Workload:
    sessions: int = 12
    turns: int = 5
    first_prompt: int = 8192
    output: int = 256
    tool_result: int = 512

    def __post_init__(self):
        if min(self.sessions, self.turns, self.first_prompt, self.output) < 1:
            raise ValueError("sessions, turns, first_prompt and output must be positive")
        if self.tool_result < 0:
            raise ValueError("tool_result cannot be negative")

    def prompt(self, turn):
        return self.first_prompt + turn * (self.output + self.tool_result)


def replay(width, capacity, workload=Workload()):
    """Run cohorts in turn order; calls execute sequentially, not in parallel."""
    if width < 1 or capacity < 0:
        raise ValueError("width must be positive and capacity nonnegative")
    retained = OrderedDict()
    resident = peak = total_input = uncached = 0
    for start in range(0, workload.sessions, width):
        cohort = range(start, min(start + width, workload.sessions))
        for turn in range(workload.turns):
            for session in cohort:
                prompt = workload.prompt(turn)
                hit = retained.pop(session, 0)
                resident -= hit
                assert 0 <= hit <= prompt
                total_input += prompt
                uncached += prompt - hit

                # Prefill produces the first sample. Ordinary autoregressive
                # decoding processes output-1 further input tokens. The final
                # sampled token gets its KV on the next call in this model.
                entry = prompt + workload.output - 1
                # A finished program has no future reuse in our trace.
                if turn == workload.turns - 1 or entry > capacity:
                    continue
                while retained and resident + entry > capacity:
                    _, old = retained.popitem(last=False)
                    resident -= old
                retained[session] = entry
                resident += entry
                peak = max(peak, resident)
                assert resident <= capacity

    ideal = workload.sessions * (
        workload.first_prompt + (workload.turns - 1) * (workload.tool_result + 1)
    )
    assert ideal <= uncached <= total_input
    assert resident == 0 and not retained
    return {"uncached": uncached, "ideal": ideal, "input": total_input,
            "extra_recomputed": uncached - ideal, "peak_retained": peak}


def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    widths = [1, 2, 3, 4, 6, 8, 12]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "svg.fonttype": "none", "svg.hashsalt": "manlog-workload-v1"})
    fig, ax = plt.subplots(figsize=(10, 5.5), layout="constrained")
    fig.patch.set_facecolor("#fdfcf8")
    ax.set_facecolor("#fdfcf8")
    for capacity, color in [(32768, "#a66b4f"), (65536, "#547b75"),
                            (131072, "#74669b")]:
        values = [replay(w, capacity)["uncached"] / replay(w, capacity)["ideal"]
                  for w in widths]
        ax.plot(widths, values, marker="o", color=color, linewidth=2,
                label=f"{capacity:,} retained KV tokens")
    no_cache = replay(12, 0)
    ax.axhline(no_cache["input"] / no_cache["ideal"], color="#817b71",
               linestyle="--", linewidth=1, label="No reuse")
    ax.set(xlabel="Programs interleaved per cohort (sequential call trace)",
           ylabel="Uncached input tokens / perfect-reuse lower bound",
           title="Same 60 calls, different retained working sets", xticks=widths,
           ylim=(0.75, 5.25))
    ax.grid(axis="y", alpha=.2)
    ax.spines[["right", "top"]].set_visible(False)
    ax.legend(loc="upper left", fontsize=9)
    fig.suptitle("Teaching model: whole-session LRU; no latency or GPU simulation",
                 fontsize=10, color="#665f55")
    fig.savefig(Path(__file__).with_name("agent-working-set.svg"),
                metadata={"Date": None})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()
    for width in (1, 2, 3, 4, 6, 8, 12):
        result = replay(width, 65536)
        print(f"window={width:2d} uncached={result['uncached']:6d} "
              f"extra={result['extra_recomputed']:6d} "
              f"work_ratio={result['uncached']/result['ideal']:.3f}")
    assert replay(12, 0)["uncached"] == 583680
    assert replay(12, 131072)["uncached"] == 122928
    assert replay(1, 16384)["extra_recomputed"] == 0
    assert replay(12, 0, Workload(turns=1))["extra_recomputed"] == 0
    assert replay(12, 131072, Workload(tool_result=0))["uncached"] == 98352
    if args.plot:
        plot()


if __name__ == "__main__":
    main()
