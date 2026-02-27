from __future__ import annotations

from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    mas_state: Any
    stream: bool
    execution_answer: str
    final_answer: str
    route_action: str
    exec_route: str
    idx: int
    retries: dict[int, int]
    revision_count: int
    full_reset_count: int
    full_reset_pending: dict[str, Any] | None
    last_output: str
    previous_handoff: dict[str, Any] | None
