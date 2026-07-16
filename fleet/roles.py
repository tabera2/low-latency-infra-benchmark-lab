"""Role definitions: what config each KIND of node needs.

A 'role' is a reusable bundle of config decisions, parameterized by the node's
pillar. 'trading' nodes get low-latency tuning; 'feed' nodes get the generator;
'metrics' gets retention. This is the Ansible-role / Salt-state idea: write the
role once, apply it to every node that claims it. Idempotent by construction —
applying it twice yields the same desired state, never a doubled effect.
"""
from __future__ import annotations

from fleet.topology import Node

# Each role maps to the set of config artifacts it renders. The renderer (next
# file) walks these. Keeping the mapping declarative means "what does a trading
# node get?" is answerable by READING data, not tracing a script.
ROLE_ARTIFACTS: dict[str, list[str]] = {
    "feed":     ["feed.env.j2", "systemd-feed.service.j2"],
    "trading":  ["tuning.sh.j2", "sysctl-lowlat.conf.j2", "systemd-trade.service.j2"],
    "metrics":  ["metrics.env.j2"],
}


def artifacts_for(node: Node) -> list[str]:
    """The templates this node renders, by its role. Fail loud on an unknown
    role — a typo in topology.py must not silently render nothing."""
    if node.role not in ROLE_ARTIFACTS:
        raise KeyError(f"unknown role {node.role!r} on {node.hostname}")
    return ROLE_ARTIFACTS[node.role]
