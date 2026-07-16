# Low-Latency Trading Infra Benchmark Lab — Architecture

## The job we're mirroring
A Trading Systems Engineer keeps a **24/7 low-latency machine fast and up**.
Not the quant who invents the signal — the engineer who makes sure the box the
signal runs on answers in microseconds, never falls over, and when it DOES
misbehave at 3am, gets diagnosed in minutes. The deliverable is not a feature.
The deliverable is **a latency number that stays low and a fleet that stays up.**

## The four moving parts of this lab
1. **The fleet** — several Linux nodes (a feed node, two trading nodes, a
   metrics node). We provision + configure them **declaratively, as code**:
   roles, per-node data ("pillar"), and rendered config artifacts. We SIMULATE
   the fleet as local processes so the whole thing runs in a sandbox, but the
   config-as-code shape is the real SaltStack/Ansible discipline.
2. **The feed** — a synthetic market-data generator that fires ticks at a
   controlled rate (e.g. 50k msg/s) to load a trading node the way a real
   exchange session does.
3. **The tuning surface** — the OS knobs that decide whether a tick is handled
   in 8µs or 80µs: CPU pinning, IRQ affinity, and kernel/network sysctls. We
   TEACH these with the exact real commands; the sandbox can't set them for
   real, so the harness measures the effect through a model we can reason about.
4. **The measurement** — a benchmark harness that records **tick-to-response**
   latency per message, computes p50/p99/p99.9, and a diff tool that compares a
   BEFORE run to an AFTER run so tuning is proven, not asserted.

## The one non-negotiable: prove it with a number
The theme of the whole project: **"not feels faster — IS faster, with a
number."** Every tuning claim ("pinning the hot thread cut the tail") must be
backed by a before/after percentile diff. A senior TSE never ships "I think it's
better." They ship "p99 went from 61µs to 22µs, here's the run."

## Why percentiles, not averages
Averages lie about latency. A box that answers in 5µs 99% of the time and 4ms
the other 1% has a great mean and is *unusable* for trading — that 1% is where
you get picked off. We live in the **tail**: p99, p99.9, and the max. The whole
harness is built to measure the tail correctly (including the coordinated-
omission trap that makes naive benchmarks lie).

## What actually runs here vs. what we teach
- **Runs** (real Python/Bash you execute): the config-as-code renderer, the
  synthetic feed, the benchmark harness, the percentile math, the before/after
  diff, the TCP round-trip prober.
- **Taught with real commands** (can't run in a browser sandbox as root):
  `taskset` CPU pinning, `/proc/irq/*/smp_affinity`, `sysctl` network/kernel
  knobs, `tuned-adm`. You'll see the exact command and WHY it moves latency.
