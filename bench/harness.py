"""The benchmark harness: drive the feed through a 'trading' work function and
record tick-to-response latency for every message.

Two correctness rules baked in:
  1) tick-to-response = response_time - tick.sent_ns, and sent_ns is the
     SCHEDULED send time (from the generator). This is the coordinated-omission
     guard: if our work function stalls, the backlog shows up in the latency.
  2) A warmup phase whose samples we DISCARD, so cold caches / JIT-ish warmup
     don't pollute the steady-state distribution we care about.
"""
from __future__ import annotations

import argparse
import time

from feed.generator import generate
from feed.tick import Tick


def trading_work(tick: Tick) -> int:
    """Stand-in for the hot path: decode a tick and 'decide'. Cheap and
    deterministic so the harness measures the SYSTEM around it, not this."""
    mid = tick.price_e4
    # A trivial, branch-light computation — the real thing would price/quote.
    return (mid * 1103515245 + tick.seq) & 0xFFFF


def run(rate: int, seconds: float, warmup_s: float = 0.5) -> list[int]:
    """Return a list of tick-to-response latencies in nanoseconds, warmup
    samples excluded. One sample per tick — we store them all and reduce later,
    never averaging on the fly (averaging early destroys the tail)."""
    latencies_ns: list[int] = []
    warmup_ns = int(warmup_s * 1_000_000_000)
    start = time.perf_counter_ns()

    for tick in generate(rate, seconds):
        _ = trading_work(tick)
        done = time.perf_counter_ns()
        # COORDINATED-OMISSION GUARD: measure from the tick's SCHEDULED send
        # time, so if trading_work fell behind, the queueing delay is counted.
        latency = done - tick.sent_ns
        if (done - start) >= warmup_ns:      # drop warmup samples
            latencies_ns.append(latency)

    return latencies_ns


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=int, default=50_000)
    ap.add_argument("--seconds", type=float, default=3.0)
    ap.add_argument("--out", default=None, help="write raw samples to this file")
    args = ap.parse_args()

    samples = run(args.rate, args.seconds)
    print(f"collected {len(samples):,} steady-state samples")
    if args.out:
        with open(args.out, "w") as f:
            f.write("\n".join(str(s) for s in samples))
        print(f"wrote raw samples -> {args.out}")


if __name__ == "__main__":
    main()
