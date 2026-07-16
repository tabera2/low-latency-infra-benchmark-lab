"""Render the declared fleet into a concrete artifact tree, one dir per node.

This is the 'apply' half of config-as-code, minus the SSH. For each node we
look up its role's artifacts and render each template with that node's pillar.
Output goes to build/<hostname>/. Rendering is a PURE FUNCTION of the topology:
same topology in, byte-identical tree out. That's what makes 'config drift'
detectable — you re-render and diff against what's deployed.
"""
from __future__ import annotations

import pathlib

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from fleet.topology import FLEET
from fleet.roles import artifacts_for

TEMPLATE_DIR = pathlib.Path(__file__).parent / "templates"
BUILD_DIR = pathlib.Path("build")

# StrictUndefined: referencing a pillar key that doesn't exist is an ERROR, not
# a silently-empty string. A blank sysctl value is a production incident.
_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)


def render_node(node) -> dict[str, str]:
    """Render every artifact for one node. Returns {output_name: contents}."""
    out: dict[str, str] = {}
    for tmpl_name in artifacts_for(node):
        template = _env.get_template(tmpl_name)
        rendered = template.render(node=node)
        # Drop the .j2 extension for the output filename.
        out_name = tmpl_name[:-3] if tmpl_name.endswith(".j2") else tmpl_name
        out[out_name] = rendered
    return out


def render_all() -> None:
    """Render the whole fleet to build/<hostname>/. Idempotent: re-running
    overwrites with identical bytes, so nothing 'drifts' from a second run."""
    for node in FLEET:
        node_dir = BUILD_DIR / node.hostname
        node_dir.mkdir(parents=True, exist_ok=True)
        for name, contents in render_node(node).items():
            (node_dir / name).write_text(contents)
        print(f"rendered {len(artifacts_for(node))} artifacts -> {node_dir}")


if __name__ == "__main__":
    render_all()
