#!/usr/bin/env bash
# RENDERED, do not edit by hand. Source of truth: fleet/topology.py pillar.
# Low-latency tuning for trade-02 (role: trading).
set -euo pipefail

# Pin the hot trading thread to an isolated core so the scheduler never
# migrates it mid-tick (migration = cold cache = a latency spike).
HOT_CPU=5

# Steer NIC interrupts to housekeeping cores so they never interrupt the hot
# core while it's processing a tick.
IRQ_CPUS="0,1"

echo "would pin trading thread to CPU ${HOT_CPU} on eth0"
echo "would steer IRQs to CPUs ${IRQ_CPUS}"
# Real commands (shown, not run in the sandbox):
#   taskset -c ${HOT_CPU} <trading-binary>
#   for irq in $(grep eth0 /proc/interrupts | awk '{print $1}' | tr -d :); do
#     echo <mask-for-${IRQ_CPUS}> > /proc/irq/${irq}/smp_affinity_list
#   done
