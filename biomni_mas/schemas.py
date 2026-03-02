from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class VerifierStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PLAN_REVISION = "PLAN_REVISION"


class WorkflowState(str, Enum):
    S_ROUTER = "S_ROUTER"
    S_PLAN_R1 = "S_PLAN_R1"
    S_PLAN_R2 = "S_PLAN_R2"
    S_PLAN_R21 = "S_PLAN_R21"
    S_PLAN_R3 = "S_PLAN_R3"
    S_PLAN_R31 = "S_PLAN_R31"
    S_EXEC_R1 = "S_EXEC_R1"
    S_EXEC_R2 = "S_EXEC_R2"
    S_SYNTHESIZER = "S_SYNTHESIZER"


@dataclass
class MessageEvent:
    label: str
    content: str
    data: dict[str, Any] | None = None


@dataclass
class StepSpec:
    step_id: int
    step: str
    owner_agent: str
    success_criteria: str | None = None


@dataclass
class RouterOutput:
    selected_agents: list[str]
    route_reason: str
    act_required: bool
    domain_scores: dict[str, float]


@dataclass
class VerifierOutput:
    status: VerifierStatus
    reason: str
    immediate_action: str
    observe_output: str


@dataclass
class MASState:
    user_query: str
    current_state: WorkflowState = WorkflowState.S_ROUTER
    router_output: RouterOutput | None = None
    draft_master_plan: list[StepSpec] = field(default_factory=list)
    final_master_plan: list[StepSpec] = field(default_factory=list)
    current_step_index: int = 0
    execution_history: list[dict[str, Any]] = field(default_factory=list)
    replan_history: list[dict[str, Any]] = field(default_factory=list)
    state_transition_history: list[str] = field(default_factory=list)
    messages: list[MessageEvent] = field(default_factory=list)
    token_usage_by_stage: dict[str, dict[str, int]] = field(default_factory=dict)
    token_usage_total: dict[str, int] = field(
        default_factory=lambda: {"input": 0, "output": 0, "total": 0}
    )
    query_to_final_ms: int = 0
    retry_count: int = 0
    plan_revision_count: int = 0
    full_reset_count: int = 0
