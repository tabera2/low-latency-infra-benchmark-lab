# When a node goes dark: TCP/IP triage + where the logs live

## The one rule: which HALF moved?
Latency = our compute (tick-to-response) + the wire (RTT). When someone says
"the box is slow," your first job is to split it: run the benchmark harness (our
half) AND net/rtt.py (the wire). One of them moved. Don't guess — measure both.

## TCP path triage, in order
```bash
ss -tanp state established '( dport = :9099 )'   # are we even connected?
ss -s                                            # socket summary: any surge?
ping -c 20 trade-01                              # ICMP RTT + packet loss
mtr -rwc 50 trade-01                             # per-hop loss/latency on the path
tcpdump -ni eth0 'tcp port 9099' -c 50           # see the actual packets
ethtool -S eth0 | grep -i drop                   # NIC-level drops (buffer full?)
```
- Slow CONNECT but fast round-trips once connected → SYN backlog, handshake,
  or a firewall dropping SYNs. Check `ss -s` and the listen backlog.
- Fast connect, slow round-trips → the path (see mtr) or the peer is slow to
  respond (its compute — go run the benchmark on the peer).
- Retransmits in tcpdump → packet loss; check `ethtool -S` and mtr for the hop.

## Where the logs live (memorize this map)
- **The service** — `journalctl -u trading-engine -f` (systemd unit logs, live).
  Older: `journalctl -u trading-engine --since "10 min ago"`.
- **The kernel** — `dmesg -T | tail -50`. This is where OOM-kills, NIC resets,
  and hardware errors surface. A node that "just died" often has the reason here.
- **Auth / who-touched-it** — `/var/log/auth.log` (Debian) or
  `journalctl _COMM=sshd`. Answers "did someone log in and change something?"
- **Config as deployed** — the rendered artifacts under build/<host>/ vs. what's
  live: re-render and diff to catch config drift.
- **Metrics** — the metrics node's retention window; the latency percentiles
  over time are the FIRST thing to check ("when did the tail start growing?").

## The 3am checklist
1. Is it up? `ping`, then `ss` for the port. 2. Which half? benchmark + rtt.
3. Kernel screaming? `dmesg -T`. 4. Service logs? `journalctl -u`. 5. Config
drifted? re-render + diff. 6. When did it start? metrics timeline. Escalate with
the NUMBER, never "it seems slow."
