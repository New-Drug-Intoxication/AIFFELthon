from __future__ import annotations

from typing import Any


def route_after_router(state: dict[str, Any]) -> str:
    action = str(state.get("route_action", ""))
    if action == "plan":
        return "plan"
    return "synth_no_act"


def route_after_plan(state: dict[str, Any]) -> str:
    del state
    return "exec_step"


def route_after_exec_step(state: dict[str, Any]) -> str:
    route = str(state.get("exec_route", ""))
    if route == "continue":
        return "exec_step"
    if route == "router":
        return "router"
    if route == "synth_no_act":
        return "synth_no_act"
    if route == "synth_act":
        return "synth_act"
    raise RuntimeError(f"Unknown exec_route: {route!r}")
