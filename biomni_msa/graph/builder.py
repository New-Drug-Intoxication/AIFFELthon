from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from biomni_msa.graph.edges import (
    route_after_exec_step,
    route_after_plan,
    route_after_router,
)
from biomni_msa.graph.nodes import MSAGraphNodes
from biomni_msa.graph.state import GraphState


def build_msa_graph(agent):
    nodes = MSAGraphNodes(agent)
    graph = StateGraph(GraphState)

    graph.add_node("router", nodes.router)
    graph.add_node("plan", nodes.plan)
    graph.add_node("exec_step", nodes.exec_step)
    graph.add_node("synth_no_act", nodes.synth_no_act)
    graph.add_node("synth_act", nodes.synth_act)

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {"plan": "plan", "synth_no_act": "synth_no_act"},
    )
    graph.add_conditional_edges("plan", route_after_plan, {"exec_step": "exec_step"})
    graph.add_conditional_edges(
        "exec_step",
        route_after_exec_step,
        {
            "exec_step": "exec_step",
            "router": "router",
            "synth_no_act": "synth_no_act",
            "synth_act": "synth_act",
        },
    )
    graph.add_edge("synth_no_act", END)
    graph.add_edge("synth_act", END)
    return graph.compile()
