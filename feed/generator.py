"""A rate-paced synthetic feed.

The one non-obvious thing about load generation: pacing. If you just loop as
fast as you can, you measure the generator's speed, not the target's response
under a KNOWN load. So we compute an inter-tick interval from the target rate
and schedule each send against an absolute clock — never 'sleep(interval)',
which drifts. This absolute-schedule pacing is also what protects us from
coordinated omission in the benchmark (a later step leans on it).
"""
from __future__ import annotations

import argparse
import time

from feed.tick import Tick

SYMBOLS = 200


def generate(rate: int, seconds: float):
    """Yield ticks paced at `rate` msgs/sec for `seconds`, using an ABSOLUTE
    schedule so slow consumers don't let us silently under-produce."""
    interval_ns = 1_000_000_000 // rate
    start = time.perf_counter_ns()
    seq = 0
    # The scheduled send time of the NEXT tick, on an absolute timeline.
    next_ns = start
    end = start + int(seconds * 1_000_000_000)

    while True:
        now = time.perf_counter_ns()
        if now >= end:
            return
        # Busy-wait to the scheduled instant. On the hot path we do NOT sleep:
        # sleep granularity (~1ms) is far coarser than our microsecond budget.
        if now < next_ns:
            continue
        tick = Tick(
            symbol_id=seq % SYMBOLS,
            seq=seq,
            sent_ns=next_ns,          # the SCHEDULED time, not 'now' — key for
            price_e4=1_000_0 + (seq % 500),   # coordinated-omission correctness
        )
        yield tick
        seq += 1
        next_ns += interval_ns        # advance the absolute schedule


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=int, default=50_000)
    ap.add_argument("--seconds", type=float, default=2.0)
    args = ap.parse_args()

    count = 0
    for _ in generate(args.rate, args.seconds):
        count += 1
    achieved = count / args.seconds
    print(f"target={args.rate}/s  produced={count}  achieved={achieved:,.0f}/s")


if __name__ == "__main__":
    main()
