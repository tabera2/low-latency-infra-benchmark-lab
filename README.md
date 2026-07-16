# Hudson River Trading | Low-Latency Trading Infra Benchmark Lab

An advanced infrastructure capstone that mirrors the real Hudson River Trading Junior Trading Systems Engineer role — the person who keeps a 24/7 low-latency machine fast and up, NOT the quant gauntlet. You declaratively provision and configure a multi-node Linux fleet with a config-management approach modeled as Python plus Jinja templates (SaltStack/Ansible-shaped, but runnable — the fleet is simulated as local processes so it actually runs). You deploy a synthetic high-rate market-data feed to load the box, apply OS-level low-latency tuning (CPU pinning, IRQ affinity, kernel and network sysctls) and explain WHY each knob helps, then build a Python benchmark harness that measures p50/p99 tick-to-response latency and network round-trips. The spine of the project is the "not feels faster, IS faster, with a number" discipline — a before/after latency diff tool that proves the tuning moved the tail, plus TCP/IP debugging, a where-the-logs-live troubleshooting drill, and an on-call runbook. Because a real kernel-tuning fleet can't fully run in a browser sandbox, the runnable code is centered on the benchmark harness, the config-as-code renderer, and the measurement/diff tooling; the OS tuning is taught conceptually with the exact real commands shown.

Built step-by-step with [KhwajaLabs Build](https://khwajalabs.com).

## Stack
- Linux
- Python
- Bash
- benchmarking
- config management
