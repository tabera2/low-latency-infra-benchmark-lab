"""A transparent model of what each OS tuning knob does to latency.

We can't set smp_affinity or run taskset for real inside a browser sandbox. So
we model each knob's EFFECT as a latency transform we can reason about, grounded
in why the knob helps. This is honest: the point of the lab is the MEASUREMENT
and PROOF discipline, and the model lets you see a real before/after move. The
real commands are shown in the tuning step; here we quantify their effect.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class TuningProfile:
    """Which knobs are ON. Each removes a specific latency source."""
    cpu_pinned: bool = False       # taskset: no scheduler migration spikes
    irq_steered: bool = False      # smp_affinity: NIC IRQs off the hot core
    busy_poll: bool = False        # net.core.busy_poll: no wakeup latency
    slow_start_off: bool = False   # tcp_slow_start_after_idle=0: no re-slowstart


def apply_effect(base_ns: int, p: TuningProfile, rng: random.Random) -> int:
    """Transform a baseline latency sample given the active knobs. Each knob
    trims a well-understood source of delay — mostly TAIL sources (migrations,
    IRQ storms), which is why tuning helps p99 far more than p50."""
    latency = float(base_ns)

    # Scheduler migration causes occasional large spikes. Pinning removes the
    # ~2% of samples that would otherwise be migration-inflated.
    if not p.cpu_pinned and rng.random() < 0.02:
        latency += rng.uniform(20_000, 60_000)   # 20-60us tail spike

    # NIC IRQs landing on the hot core cause frequent smaller jitter.
    if not p.irq_steered and rng.random() < 0.10:
        latency += rng.uniform(3_000, 12_000)

    # Busy-poll shaves fixed wakeup latency off EVERY sample (helps p50 too).
    if p.busy_poll:
        latency -= 2_500

    # Slow-start-after-idle adds a spike after a lull; disabling removes it.
    if not p.slow_start_off and rng.random() < 0.01:
        latency += rng.uniform(15_000, 40_000)

    return max(1_000, int(latency))
