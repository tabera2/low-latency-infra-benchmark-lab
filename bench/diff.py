"""Compare two runs and render the delta. THIS is 'prove it with a number'.

We load two raw sample files (before/after), summarize each with the SAME
reducer, and print the per-percentile change. A negative delta on p99/p99.9 is
the win we're claiming; a positive delta anywhere is a regression to explain.
"""
from __future__ import annotations

import sys

from bench.stats import summarize, Summary


def _delta_line(label: str, before: float, after: float) -> str:
    delta = after - before
    pct = (delta / before * 100.0) if before else 0.0
    arrow = "IMPROVED" if delta < 0 else ("regressed" if delta > 0 else "flat")
    return f"  {label:6} {before:8.2f} -> {after:8.2f} us  ({delta:+7.2f}, {pct:+6.1f}%)  {arrow}"


def diff(before: Summary, after: Summary) -> str:
    lines = ["before -> after (microseconds):"]
    lines.append(_delta_line("p50", before.p50_us, after.p50_us))
    lines.append(_delta_line("p99", before.p99_us, after.p99_us))
    lines.append(_delta_line("p99.9", before.p999_us, after.p999_us))
    lines.append(_delta_line("max", before.max_us, after.max_us))
    lines.append(_delta_line("jitter", before.jitter_us, after.jitter_us))
    # The headline claim: what happened to the tail.
    tail_move = after.p999_us - before.p999_us
    verdict = "TUNING PROVEN" if tail_move < 0 else "NO TAIL IMPROVEMENT"
    lines.append(f"verdict: {verdict} (p99.9 moved {tail_move:+.2f} us)")
    return "\n".join(lines)


def _load(path: str) -> Summary:
    with open(path) as f:
        return summarize([int(x) for x in f if x.strip()])


def main() -> None:
    before_path, after_path = sys.argv[1], sys.argv[2]
    print(diff(_load(before_path), _load(after_path)))


if __name__ == "__main__":
    main()
