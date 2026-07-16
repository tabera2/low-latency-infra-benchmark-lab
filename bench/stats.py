"""Reduce raw latency samples to the numbers a TSE actually reports.

Percentile method matters. We sort once and index with the 'nearest-rank on a
0..1 fraction' method, which is unambiguous and matches what most latency tools
report. We expose p50/p90/p99/p99.9 and max — the shape of the tail — plus a
jitter measure (p99 - p50), because 'how consistent' is as important as 'how
fast' for a trading box.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass
class Summary:
    count: int
    p50_us: float
    p90_us: float
    p99_us: float
    p999_us: float
    max_us: float
    jitter_us: float          # p99 - p50: the spread of the bad cases

    def render(self) -> str:
        return (
            f"n={self.count:,}\n"
            f"  p50   = {self.p50_us:8.2f} us\n"
            f"  p90   = {self.p90_us:8.2f} us\n"
            f"  p99   = {self.p99_us:8.2f} us\n"
            f"  p99.9 = {self.p999_us:8.2f} us\n"
            f"  max   = {self.max_us:8.2f} us\n"
            f"  jitter(p99-p50) = {self.jitter_us:8.2f} us"
        )


def percentile_ns(sorted_ns: list[int], frac: float) -> float:
    """Nearest-rank percentile on an already-SORTED list. frac in [0,1].
    Index = ceil(frac * n) - 1, clamped. Unambiguous and monotonic."""
    if not sorted_ns:
        return 0.0
    n = len(sorted_ns)
    rank = max(1, min(n, int(frac * n + 0.9999999)))
    return float(sorted_ns[rank - 1])


def summarize(latencies_ns: list[int]) -> Summary:
    """Sort ONCE, then pull every percentile from the sorted list."""
    s = sorted(latencies_ns)
    to_us = 1_000.0
    p50 = percentile_ns(s, 0.50) / to_us
    p99 = percentile_ns(s, 0.99) / to_us
    return Summary(
        count=len(s),
        p50_us=p50,
        p90_us=percentile_ns(s, 0.90) / to_us,
        p99_us=p99,
        p999_us=percentile_ns(s, 0.999) / to_us,
        max_us=percentile_ns(s, 1.0) / to_us,
        jitter_us=p99 - p50,
    )


def main() -> None:
    path = sys.argv[1]
    with open(path) as f:
        samples = [int(line) for line in f if line.strip()]
    print(summarize(samples).render())


if __name__ == "__main__":
    main()
