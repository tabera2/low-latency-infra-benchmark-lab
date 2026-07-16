"""Measure TCP round-trip time to a node — the network half of latency.

Tick-to-response measures OUR compute; RTT measures the wire. When a box is
'slow' you must know WHICH half moved. This opens a TCP connection, sends a
timestamp, reads the echo, and records connect time + round-trip per probe,
then reduces with the SAME percentile tooling as the compute benchmark.
"""
from __future__ import annotations

import argparse
import socket
import time

from bench.stats import summarize


def probe_once(host: str, port: int, timeout: float = 1.0) -> tuple[int, int]:
    """Return (connect_ns, roundtrip_ns) for one probe. Separating connect from
    round-trip matters: a slow CONNECT points at SYN/handshake/backlog issues;
    a slow ROUND-TRIP after connect points at the path or the peer's response."""
    t0 = time.perf_counter_ns()
    s = socket.create_connection((host, port), timeout=timeout)
    # TCP_NODELAY: disable Nagle so our tiny probe isn't buffered waiting for
    # more data — Nagle adds up to 40ms of delay to small, latency-sensitive
    # messages. On a trading path Nagle is always OFF.
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    t_connected = time.perf_counter_ns()

    payload = str(time.perf_counter_ns()).encode()
    s.sendall(payload)
    _ = s.recv(64)                       # the echo
    t_done = time.perf_counter_ns()
    s.close()
    return (t_connected - t0, t_done - t_connected)


def run(host: str, port: int, count: int) -> None:
    connects, rtts = [], []
    for _ in range(count):
        c, r = probe_once(host, port)
        connects.append(c)
        rtts.append(r)
    print("connect time:")
    print(summarize(connects).render())
    print("round-trip time:")
    print(summarize(rtts).render())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9099)
    ap.add_argument("--count", type=int, default=20)
    args = ap.parse_args()
    run(args.host, args.port, args.count)


if __name__ == "__main__":
    main()
