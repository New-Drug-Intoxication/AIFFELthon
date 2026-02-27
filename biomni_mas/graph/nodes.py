from __future__ import annotations

from dataclasses import asdict
from time import perf_counter
from typing import Any

from biomni_mas.schemas import RouterOutput, VerifierStatus, WorkflowState


class MASGraphNodes:
    def __init__(self, agent: Any):
        self.agent = agent

    @staticmethod
    def _completed_step_ids(mas_state: Any) -> set[int]:
        completed: set[int] = set()
        for row in getattr(mas_state, "execution_history", []):
            if not isinstance(row, dict):
                continue
            verifier = row.get("verifier", {})
            if not isinstance(verifier, dict):
                continue
            raw_status = verifier.get("status", "")
            status = str(getattr(raw_status, "value", raw_status)).strip().upper()
            if status.startswith("VERIFIERSTATUS."):
                status = status.split(".")[-1]
            if status != VerifierStatus.SUCCESS.value:
                continue
            try:
                completed.add(int(row.get("step_id", 0)))
            except Exception:
                continue
        return completed

    @staticmethod
    def _render_execution_checklist(mas_state: Any) -> str:
        plan = getattr(mas_state, "final_master_plan", []) or []
        if not plan:
            return "execution checklist unavailable (empty plan)"
        completed = MASGraphNodes._completed_step_ids(mas_state)
        lines: list[str] = []
        for idx, step in enumerate(plan, start=1):
            sid = int(getattr(step, "step_id", idx))
            mark = "V" if sid in completed else " "
            text = str(getattr(step, "step", "")).strip()
            owner = str(getattr(step, "owner_agent", "Common")).strip() or "Common"
            success = str(getattr(step, "success_criteria", "done")).strip() or "done"
            lines.append(
                f"{idx}. [{mark}] {text} | owner_agent: {owner} | success_criteria: {success}"
            )
        return "\n".join(lines)

    def router(self, state: dict[str, Any]) -> dict[str, Any]:
        mas_state = state["mas_state"]
        stream = bool(state.get("stream", False))
        full_reset_pending = state.get("full_reset_pending")

        self.agent._set_state(mas_state, WorkflowState.S_ROUTER)
        router_out = self.agent._router_stage(mas_state)
        mas_state.router_output = router_out
        reset_suffix = " (full reset)" if full_reset_pending else ""
        self.agent._emit(
            mas_state,
            "[Router Message]",
            f"selected={router_out.selected_agents}, act_required={router_out.act_required}{reset_suffix}",
            asdict(router_out),
            stream,
        )
        if isinstance(full_reset_pending, dict):
            reason = str(full_reset_pending.get("reason", ""))
            target_step = self.agent._safe_target_step(
                mas_state, full_reset_pending.get("target_step")
            )
            note = (
                "full_reset_to_no_act"
                if not router_out.act_required
                else "full_reset_applied"
            )
            mas_state.replan_history.append(
                {
                    "target_step": target_step,
                    "reason": reason,
                    "applied": True,
                    "note": note,
                }
            )
        route_action = "plan" if router_out.act_required else "synth_no_act"
        return {
            "mas_state": mas_state,
            "route_action": route_action,
            "full_reset_pending": None,
        }

    def plan(self, state: dict[str, Any]) -> dict[str, Any]:
        mas_state = state["mas_state"]
        stream = bool(state.get("stream", False))
        router_out = mas_state.router_output or RouterOutput(
            selected_agents=[],
            route_reason="missing_router_output",
            act_required=False,
            domain_scores={},
        )
        self.agent._run_plan_pipeline(mas_state, router_out.selected_agents, stream)
        return {
            "mas_state": mas_state,
            "idx": int(state.get("idx", 0)),
            "retries": dict(state.get("retries", {})),
            "revision_count": int(state.get("revision_count", 0)),
            "full_reset_count": int(state.get("full_reset_count", 0)),
            "full_reset_pending": None,
            "last_output": str(state.get("last_output", "")),
            "previous_handoff": state.get("previous_handoff"),
        }

    def exec_step(self, state: dict[str, Any]) -> dict[str, Any]:
        mas_state = state["mas_state"]
        stream = bool(state.get("stream", False))

        idx = int(state.get("idx", 0))
        retries = dict(state.get("retries", {}))
        revision_count = int(state.get("revision_count", 0))
        full_reset_count = int(state.get("full_reset_count", 0))
        mas_state.plan_revision_count = revision_count
        mas_state.full_reset_count = full_reset_count
        last_output = str(state.get("last_output", ""))
        previous_handoff = state.get("previous_handoff")
        full_reset_pending = state.get("full_reset_pending")

        if idx >= len(mas_state.final_master_plan):
            execution_answer = self.agent._synthesize_act(mas_state, last_output)
            return {
                "mas_state": mas_state,
                "execution_answer": execution_answer,
                "exec_route": "synth_act",
                "idx": idx,
                "retries": retries,
                "revision_count": revision_count,
                "full_reset_count": full_reset_count,
                "full_reset_pending": full_reset_pending,
                "last_output": last_output,
                "previous_handoff": previous_handoff,
            }

        step = mas_state.final_master_plan[idx]
        mas_state.current_step_index = self.agent._safe_target_step(
            mas_state, step.step_id
        )
        step_started_at = perf_counter()
        self.agent._set_state(mas_state, WorkflowState.S_EXEC_R1)
        self.agent._ensure_data_lake(mas_state, step.owner_agent, stream)
        data_catalog = self.agent._build_data_catalog(step.owner_agent)
        generate_started_at = perf_counter()
        execution_think, execution_code = self.agent._generate_execution_step(
            step,
            user_query=mas_state.user_query,
            context_handoff=previous_handoff,
            data_catalog=data_catalog,
        )
        generate_code_ms = (perf_counter() - generate_started_at) * 1000.0
        tool_scope = self.agent._load_tool_scope(step.owner_agent)
        self.agent._emit(
            mas_state,
            f"[Execution-R1 | {step.owner_agent} | Step {step.step_id} Message]",
            f"Executing: {step.step}",
            {"execution_think": execution_think, "executed_code": execution_code},
            stream,
        )
        run_started_at = perf_counter()
        observe_output = self.agent._run_code(execution_code, tool_scope)
        run_code_ms = (perf_counter() - run_started_at) * 1000.0
        observe_output = str(observe_output)[: self.agent.runtime.observation_max_chars]

        self.agent._set_state(mas_state, WorkflowState.S_EXEC_R2)
        verify_started_at = perf_counter()
        verifier = self.agent._verify_step(step, execution_code, observe_output)
        verify_ms = (perf_counter() - verify_started_at) * 1000.0
        step_total_ms = (perf_counter() - step_started_at) * 1000.0
        self.agent._emit(
            mas_state,
            f"[Execution-R2 Verifier | {step.owner_agent} | Step {step.step_id} Message]",
            f"status={verifier.status.value}, reason={verifier.reason}",
            asdict(verifier),
            stream,
        )

        mas_state.execution_history.append(
            {
                "step_id": step.step_id,
                "owner_agent": step.owner_agent,
                "execution_think": execution_think,
                "executed_code": execution_code,
                "observe_output": observe_output,
                "verifier": asdict(verifier),
                "generate_code_ms": round(generate_code_ms, 3),
                "run_code_ms": round(run_code_ms, 3),
                "verify_ms": round(verify_ms, 3),
                "step_total_ms": round(step_total_ms, 3),
            }
        )
        last_output = observe_output
        previous_handoff = {
            "previous_step_id": step.step_id,
            "previous_step_observe_output": observe_output,
        }

        if verifier.status == VerifierStatus.FAILURE:
            retry_count = retries.get(step.step_id, 0)
            if self.agent._should_escalate_failure_to_plan_revision(
                step=step,
                verifier=verifier,
                retry_count=retry_count,
                execution_history=mas_state.execution_history,
            ):
                instruction = self.agent._compact_text(
                    "Repeated schema/identifier mismatch detected. Revise step to define explicit data axis and identifier mapping before execution.",
                    max_chars=320,
                    max_lines=2,
                )
                decision = {
                    "action": "PLAN_REVISION",
                    "instruction": instruction,
                    "target_step_id": step.step_id,
                    "source": "verifier_escalation",
                }
            else:
                instruction = self.agent._compact_text(
                    str(verifier.immediate_action or "").strip()
                    or "Fix the code/runtime issue and retry this step.",
                    max_chars=320,
                    max_lines=2,
                )
                decision = {
                    "action": "RETRY",
                    "instruction": instruction,
                    "target_step_id": step.step_id,
                    "source": "verifier_fast_path",
                }
        else:
            decision = self.agent._orchestrator_exec_decide(
                state=mas_state,
                step=step,
                verifier=verifier,
                retry_count=retries.get(step.step_id, 0),
                plan_revision_count=revision_count,
            )
        action = str(decision["action"])
        escalation_sources = {"verifier_escalation", "orchestrator_escalation"}
        if (
            action == "PLAN_REVISION"
            and verifier.status != VerifierStatus.PLAN_REVISION
            and str(decision.get("source", "")) not in escalation_sources
        ):
            action = "RETRY"
        if verifier.status == VerifierStatus.PLAN_REVISION:
            if action not in {"PLAN_REVISION", "FULL_RESET"}:
                action = "PLAN_REVISION"
        decision["action"] = action
        decision_label = (
            "[Execution-R2 Fast Retry Message]"
            if str(decision.get("source", "")) == "verifier_fast_path"
            else "[Orchestrator Exec Message]"
        )
        self.agent._emit(
            mas_state,
            decision_label,
            f"action={decision['action']} instruction={decision['instruction']}",
            decision,
            stream,
        )
        checklist_content = self._render_execution_checklist(mas_state)
        self.agent._emit(
            mas_state,
            "[Execution Checklist Message]",
            checklist_content,
            {
                "action": action,
                "current_step_id": int(step.step_id),
                "completed_step_ids": sorted(self._completed_step_ids(mas_state)),
            },
            stream,
        )

        if action == "NEXT":
            mas_state.current_step_index = int(step.step_id) + 1
            return {
                "mas_state": mas_state,
                "exec_route": "continue",
                "idx": idx + 1,
                "retries": retries,
                "revision_count": revision_count,
                "full_reset_count": full_reset_count,
                "full_reset_pending": None,
                "last_output": last_output,
                "previous_handoff": previous_handoff,
            }

        if action == "RETRY":
            previous_handoff = {
                "previous_step_id": step.step_id,
                "previous_step_status": verifier.status.value,
                "previous_step_reason": verifier.reason,
                "previous_step_observe_output": observe_output,
                "orchestrator_instruction": self.agent._build_retry_guidance(
                    step=step,
                    verifier=verifier,
                    decision=decision,
                ),
            }
            mas_state.retry_count += 1
            count = retries.get(step.step_id, 0)
            if count >= self.agent.runtime.step_retry_limit:
                mas_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "step_retry_limit_exceeded_without_plan_revision",
                    }
                )
                execution_answer = self.agent._synthesize_act(mas_state, last_output)
                return {
                    "mas_state": mas_state,
                    "execution_answer": execution_answer,
                    "exec_route": "synth_act",
                    "idx": idx,
                    "retries": retries,
                    "revision_count": revision_count,
                    "full_reset_count": full_reset_count,
                    "full_reset_pending": None,
                    "last_output": last_output,
                    "previous_handoff": previous_handoff,
                }
            retries[step.step_id] = count + 1
            return {
                "mas_state": mas_state,
                "exec_route": "continue",
                "idx": idx,
                "retries": retries,
                "revision_count": revision_count,
                "full_reset_count": full_reset_count,
                "full_reset_pending": None,
                "last_output": last_output,
                "previous_handoff": previous_handoff,
            }

        if action == "PLAN_REVISION":
            if (
                verifier.status != VerifierStatus.PLAN_REVISION
                and str(decision.get("source", "")) not in escalation_sources
            ):
                mas_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "blocked_non_verifier_plan_revision",
                    }
                )
                execution_answer = self.agent._synthesize_act(mas_state, last_output)
                return {
                    "mas_state": mas_state,
                    "execution_answer": execution_answer,
                    "exec_route": "synth_act",
                    "idx": idx,
                    "retries": retries,
                    "revision_count": revision_count,
                    "full_reset_count": full_reset_count,
                    "full_reset_pending": None,
                    "last_output": last_output,
                    "previous_handoff": previous_handoff,
                }
            if revision_count >= self.agent.runtime.plan_revision_limit:
                mas_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "plan_revision_limit_exceeded",
                    }
                )
                execution_answer = self.agent._synthesize_act(mas_state, last_output)
                return {
                    "mas_state": mas_state,
                    "execution_answer": execution_answer,
                    "exec_route": "synth_act",
                    "idx": idx,
                    "retries": retries,
                    "revision_count": revision_count,
                    "full_reset_count": full_reset_count,
                    "full_reset_pending": None,
                    "last_output": last_output,
                    "previous_handoff": previous_handoff,
                }
            revision_count += 1
            mas_state.plan_revision_count = revision_count
            plan_len = len(mas_state.final_master_plan)
            target_raw = self.agent._coerce_int(decision.get("target_step_id"))
            target = target_raw if target_raw is not None else step.step_id
            if plan_len > 0:
                target = max(1, min(target, plan_len))
            else:
                target = 1
            changed = self.agent._partial_replan(
                mas_state,
                target,
                verifier.reason,
                verifier.immediate_action,
                stream,
            )
            if not changed:
                execution_answer = self.agent._synthesize_act(mas_state, last_output)
                return {
                    "mas_state": mas_state,
                    "execution_answer": execution_answer,
                    "exec_route": "synth_act",
                    "idx": idx,
                    "retries": retries,
                    "revision_count": revision_count,
                    "full_reset_count": full_reset_count,
                    "full_reset_pending": None,
                    "last_output": last_output,
                    "previous_handoff": previous_handoff,
                }
            previous_handoff = {
                "previous_step_id": step.step_id,
                "previous_step_status": verifier.status.value,
                "previous_step_reason": verifier.reason,
                "previous_step_observe_output": observe_output,
                "orchestrator_instruction": self.agent._build_revision_guidance(
                    step=step,
                    verifier=verifier,
                    decision=decision,
                ),
            }
            return {
                "mas_state": mas_state,
                "exec_route": "continue",
                "idx": min(
                    max(0, target - 1),
                    max(0, len(mas_state.final_master_plan) - 1),
                ),
                "retries": retries,
                "revision_count": revision_count,
                "full_reset_count": full_reset_count,
                "full_reset_pending": None,
                "last_output": last_output,
                "previous_handoff": previous_handoff,
            }

        if action == "FULL_RESET":
            if verifier.status != VerifierStatus.PLAN_REVISION:
                mas_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "blocked_non_verifier_full_reset",
                    }
                )
                mas_state.retry_count += 1
                retries[step.step_id] = retries.get(step.step_id, 0) + 1
                if retries[step.step_id] > self.agent.runtime.step_retry_limit:
                    execution_answer = self.agent._synthesize_act(
                        mas_state, last_output
                    )
                    return {
                        "mas_state": mas_state,
                        "execution_answer": execution_answer,
                        "exec_route": "synth_act",
                        "idx": idx,
                        "retries": retries,
                        "revision_count": revision_count,
                        "full_reset_count": full_reset_count,
                        "full_reset_pending": None,
                        "last_output": last_output,
                        "previous_handoff": previous_handoff,
                    }
                return {
                    "mas_state": mas_state,
                    "exec_route": "continue",
                    "idx": idx,
                    "retries": retries,
                    "revision_count": revision_count,
                    "full_reset_count": full_reset_count,
                    "full_reset_pending": None,
                    "last_output": last_output,
                    "previous_handoff": previous_handoff,
                }
            if not self.agent._is_full_reset_exception(verifier.reason):
                mas_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "blocked_non_exception_full_reset",
                    }
                )
                mas_state.retry_count += 1
                retries[step.step_id] = retries.get(step.step_id, 0) + 1
                if retries[step.step_id] > self.agent.runtime.step_retry_limit:
                    execution_answer = self.agent._synthesize_act(
                        mas_state, last_output
                    )
                    return {
                        "mas_state": mas_state,
                        "execution_answer": execution_answer,
                        "exec_route": "synth_act",
                        "idx": idx,
                        "retries": retries,
                        "revision_count": revision_count,
                        "full_reset_count": full_reset_count,
                        "full_reset_pending": None,
                        "last_output": last_output,
                        "previous_handoff": previous_handoff,
                    }
                return {
                    "mas_state": mas_state,
                    "exec_route": "continue",
                    "idx": idx,
                    "retries": retries,
                    "revision_count": revision_count,
                    "full_reset_count": full_reset_count,
                    "full_reset_pending": None,
                    "last_output": last_output,
                    "previous_handoff": previous_handoff,
                }
            if full_reset_count >= 1:
                mas_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "full_reset_limit_exceeded",
                    }
                )
                execution_answer = self.agent._synthesize_act(mas_state, last_output)
                return {
                    "mas_state": mas_state,
                    "execution_answer": execution_answer,
                    "exec_route": "synth_act",
                    "idx": idx,
                    "retries": retries,
                    "revision_count": revision_count,
                    "full_reset_count": full_reset_count,
                    "full_reset_pending": None,
                    "last_output": last_output,
                    "previous_handoff": previous_handoff,
                }

            full_reset_count += 1
            mas_state.full_reset_count = full_reset_count
            return {
                "mas_state": mas_state,
                "exec_route": "router",
                "idx": 0,
                "retries": {},
                "revision_count": 0,
                "full_reset_count": full_reset_count,
                "full_reset_pending": {
                    "target_step": step.step_id,
                    "reason": verifier.reason,
                },
                "last_output": last_output,
                "previous_handoff": None,
            }

        raise RuntimeError(f"Unknown orchestrator action: {action}")

    def synth_no_act(self, state: dict[str, Any]) -> dict[str, Any]:
        mas_state = state["mas_state"]
        stream = bool(state.get("stream", False))
        self.agent._set_state(mas_state, WorkflowState.S_SYNTHESIZER)
        answer = self.agent._synthesize_final(
            mas_state,
            mode="no_act",
            execution_answer="",
        )
        self.agent._emit(mas_state, "[Synthesizer Message]", answer, None, stream)
        return {"mas_state": mas_state, "final_answer": answer}

    def synth_act(self, state: dict[str, Any]) -> dict[str, Any]:
        mas_state = state["mas_state"]
        stream = bool(state.get("stream", False))
        execution_answer = str(state.get("execution_answer", ""))
        self.agent._set_state(mas_state, WorkflowState.S_SYNTHESIZER)
        answer = self.agent._synthesize_final(
            mas_state,
            mode="act",
            execution_answer=execution_answer,
        )
        self.agent._emit(mas_state, "[Synthesizer Message]", answer, None, stream)
        return {"mas_state": mas_state, "final_answer": answer}
