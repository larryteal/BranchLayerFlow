"""Walk a BLF flow's static structure and emit Mermaid.

Important caveat: BLF's *runtime* topology is decided by `handoff` and
can be data-dependent (LLM-driven dispatch, dynamic team summoning).
What we render here is the *static* declared `successors` graph plus
the `branches` of every nested Flow.
"""

from typing import Set


def render_mermaid(root) -> str:
    seen_nodes: Set[int] = set()
    seen_edges: Set[tuple] = set()
    lines = ["flowchart TD"]

    def node_id(agent) -> str:
        return f"n{id(agent)}"

    def add_node(agent) -> None:
        if id(agent) in seen_nodes:
            return
        seen_nodes.add(id(agent))
        is_flow = hasattr(agent, "branches")
        shape = ("[[", "]]") if is_flow else ("(", ")")
        lines.append(f"  {node_id(agent)}{shape[0]}{agent.meta.name}{shape[1]}")
        # successors are static peer registrations (`>>`)
        for succ in agent.successors.values():
            add_node(succ)
            edge = (id(agent), id(succ))
            if edge not in seen_edges:
                seen_edges.add(edge)
                lines.append(f"  {node_id(agent)} --> {node_id(succ)}")
        # branches show containment for Flows
        if is_flow:
            for br in agent.branches:
                add_node(br)
                edge = (id(agent), id(br), "contains")
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    lines.append(f"  {node_id(agent)} -.->|contains| {node_id(br)}")

    add_node(root)
    return "\n".join(lines)
