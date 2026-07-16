"""The fleet, declared as data.

This is the config-management mindset: you do NOT write a script that SSHes in
and runs commands step by step. You DECLARE the desired end state — which nodes
exist, what role each plays, what data each needs — and a renderer turns that
declaration into concrete config artifacts. SaltStack calls the per-node data
'pillar' and the role logic 'states'; Ansible calls them 'vars' and 'roles'.
We model the same split in plain Python so it runs and you can reason about it.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Node:
    """One machine in the fleet. Frozen: the DECLARATION is immutable; the
    running state is what the renderer + apply loop drive toward it."""
    hostname: str
    role: str                       # which role definition applies
    cpu_count: int                  # cores available for pinning decisions
    nic: str = "eth0"               # the interface the feed/traffic rides on
    # Per-node overrides ("pillar"): data that differs machine to machine.
    pillar: dict = field(default_factory=dict)


# The desired fleet. Change THIS, re-render, and the artifacts change. There is
# exactly one place the topology is defined — the single source of truth.
FLEET: list[Node] = [
    Node(
        hostname="md-feed-01",
        role="feed",
        cpu_count=8,
        pillar={"tick_rate": 50_000, "symbols": 200},
    ),
    Node(
        hostname="trade-01",
        role="trading",
        cpu_count=16,
        # This node is the one we tune hardest: pin the hot thread, steer IRQs.
        pillar={"hot_cpu": 3, "irq_cpus": [0, 1], "busy_poll_us": 50},
    ),
    Node(
        hostname="trade-02",
        role="trading",
        cpu_count=16,
        pillar={"hot_cpu": 5, "irq_cpus": [0, 1], "busy_poll_us": 50},
    ),
    Node(
        hostname="metrics-01",
        role="metrics",
        cpu_count=4,
        pillar={"retention_days": 7},
    ),
]


def nodes_with_role(role: str) -> list[Node]:
    """Query the desired fleet by role. Renderers iterate these."""
    return [n for n in FLEET if n.role == role]
