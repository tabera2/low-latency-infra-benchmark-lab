# Trading Systems On-Call Runbook

## What we alert on (the tail, not the mean)
Alerts fire on PERCENTILES, because a mean can't page you for a tail problem:
- `p99.9 tick-to-response > 100us for 60s`  -> PAGE (latency regression)
- `feed achieved_rate < 90% of target for 30s` -> PAGE (feed can't keep up)
- `node RTT p99 > 500us` -> WARN (network path degrading)
- `dmesg shows OOM or NIC reset` -> PAGE (something died or is dying)

## Runbook: "p99.9 latency alert"
1. Confirm it's real: pull the metrics timeline — did the tail actually step up,
   or is it one noisy sample? (One sample is not a trend.)
2. Split the halves: run the benchmark harness AND net/rtt.py on the node.
   Compute regressed -> go to step 3. Wire regressed -> go to step 4.
3. Compute regressed:
   - Did config drift? Re-render fleet config and diff against live. A hand-edit
     that un-pinned the hot thread or reset a sysctl is the usual culprit.
   - Check `taskset -cp <pid>` — is the hot thread still on its isolated core?
   - Check `/proc/irq/*/smp_affinity_list` — did IRQs wander back to the hot core?
4. Wire regressed:
   - `mtr` the path for a bad hop; `ethtool -S` for NIC drops.
   - Check the peer isn't itself slow (run its benchmark).

## Runbook: "feed can't keep up"
- The achieved rate dropping below target means backpressure somewhere. Check
  the trading node isn't stalling (that backs up the feed). Split compute vs wire
  as above. The coordinated-omission guard means a stall shows in the tail — look
  there first.

## Escalation
Escalate with the NUMBER and the DIFF, always:
  "p99.9 stepped from 22us to 180us at 02:14; config diff shows trade-01's hot
   thread un-pinned; re-pinning restored it to 24us."
That sentence is the entire job: a number, a cause, a fix, proven by a diff.

## The daily loop (steady state)
1. Read the overnight latency timeline — did the tail move?
2. Any config drift across the fleet? Re-render + diff.
3. Feed keeping up at target rate?
4. Any WARN-level trends creeping toward PAGE thresholds?
Nothing on fire is the goal. A boring on-call shift is a well-tuned fleet.
