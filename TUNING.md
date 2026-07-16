# OS Low-Latency Tuning — the real knobs, and WHY each one helps

> These commands need root on a real box and can't run in the sandbox. The
> benchmark models their EFFECT (bench/tuning_model.py); here is the ground
> truth a TSE actually applies, and the reason each one moves the tail.

## 1. CPU pinning + core isolation
```bash
# Isolate cores 3-7 from the scheduler at boot (kernel cmdline), so nothing
# general-purpose ever runs there:
#   isolcpus=3-7 nohz_full=3-7 rcu_nocbs=3-7
# Then pin the trading process to an isolated core:
taskset -c 3 ./trading-engine
```
**Why:** if the scheduler is free to migrate your hot thread to another core, it
lands on a COLD cache — L1/L2 are empty for it there — and that one tick pays
tens of microseconds of cache-miss penalty. That's a classic p99.9 spike.
Pinning + isolation means the hot thread owns a core; nothing evicts its cache.

## 2. IRQ affinity — keep NIC interrupts off the hot core
```bash
# Find the NIC's IRQs, then steer them to housekeeping cores 0-1:
for irq in $(grep eth0 /proc/interrupts | awk -F: '{print $1}'); do
  echo 0-1 > /proc/irq/${irq}/smp_affinity_list
done
```
**Why:** every arriving packet raises a hardware interrupt. If that interrupt
fires on the SAME core running your trading thread, it preempts you mid-tick.
Steering IRQs to dedicated housekeeping cores means the hot core is never
interrupted by network I/O — it just processes ticks.

## 3. Network sysctls
```bash
sysctl -w net.core.busy_poll=50        # busy-poll the socket 50us before yield
sysctl -w net.core.busy_read=50
sysctl -w net.ipv4.tcp_slow_start_after_idle=0   # no re-slowstart after a lull
sysctl -w net.core.rmem_max=16777216   # bigger buffers absorb bursts
```
**Why:** `busy_poll` trades CPU for latency — instead of sleeping and eating a
wakeup when a packet arrives, the socket spins briefly and grabs it immediately.
`tcp_slow_start_after_idle=0` stops a quiet connection from resetting its
congestion window, which otherwise makes the first tick after a lull crawl.

## 4. NUMA locality
```bash
numactl --cpunodebind=0 --membind=0 ./trading-engine
```
**Why:** on a multi-socket box, memory attached to a DIFFERENT socket than your
core costs extra nanoseconds per access (a cross-socket hop). Bind the process
to the NUMA node whose memory AND NIC it uses, and every access stays local.

## The tradeoff, stated plainly
Almost every knob here trades **throughput or CPU efficiency for lower, more
predictable latency**. Busy-poll burns a core spinning. Isolation strands cores
from general work. This is the RIGHT trade for a trading box and the WRONG trade
for a batch server. Tuning is never "better" in the abstract — it's "better for
THIS box's job." Always know which job you're tuning for.
