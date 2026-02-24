from __future__ import annotations

from dataclasses import asdict
from typing import Any

from biomni_msa.schemas import RouterOutput, VerifierStatus, WorkflowState


class MSAGraphNodes:
    def __init__(self, agent: Any):
        self.agent = agent

    def router(self, state: dict[str, Any]) -> dict[str, Any]:
        msa_state = state["msa_state"]
        stream = bool(state.get("stream", False))
        full_reset_pending = state.get("full_reset_pending")

        self.agent._set_state(msa_state, WorkflowState.S_ROUTER)
        router_out = self.agent._router_stage(msa_state)
        msa_state.router_output = router_out
        reset_suffix = " (full reset)" if full_reset_pending else ""
        self.agent._emit(
            msa_state,
            "[Router Message]",
            f"selected={router_out.selected_agents}, act_required={router_out.act_required}{reset_suffix}",
            asdict(router_out),
            stream,
        )
        if isinstance(full_reset_pending, dict):
            reason = str(full_reset_pending.get("reason", ""))
            target_step = int(full_reset_pending.get("target_step", 0))
            note = "full_reset_to_no_act" if not router_out.act_required else "full_reset_applied"
            msa_state.replan_history.append(
                {
                    "target_step": target_step,
                    "reason": reason,
                    "applied": True,
                    "note": note,
                }
            )
        route_action = "plan" if router_out.act_required else "synth_no_act"
        return {
            "msa_state": msa_state,
            "route_action": route_action,
            "full_reset_pending": None,
        }

    def plan(self, state: dict[str, Any]) -> dict[str, Any]:
        msa_state = state["msa_state"]
        stream = bool(state.get("stream", False))
        router_out = msa_state.router_output or RouterOutput(
            selected_agents=[],
            route_reason="missing_router_output",
            act_required=False,
            domain_scores={},
        )
        self.agent._run_plan_pipeline(msa_state, router_out.selected_agents, stream)
        return {
            "msa_state": msa_state,
            "idx": int(state.get("idx", 0)),
            "retries": dict(state.get("retries", {})),
            "revision_count": int(state.get("revision_count", 0)),
            "full_reset_count": int(state.get("full_reset_count", 0)),
            "full_reset_pending": None,
            "last_output": str(state.get("last_output", "")),
            "previous_handoff": state.get("previous_handoff"),
        }

    def exec_step(self, state: dict[str, Any]) -> dict[str, Any]:
        msa_state = state["msa_state"]
        stream = bool(state.get("stream", False))

        idx = int(state.get("idx", 0))
        retries = dict(state.get("retries", {}))
        revision_count = int(state.get("revision_count", 0))
        full_reset_count = int(state.get("full_reset_count", 0))
        last_output = str(state.get("last_output", ""))
        previous_handoff = state.get("previous_handoff")
        full_reset_pending = state.get("full_reset_pending")

        if idx >= len(msa_state.final_master_plan):
            execution_answer = self.agent._synthesize_act(msa_state, last_output)
            return {
                "msa_state": msa_state,
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

        step = msa_state.final_master_plan[idx]
        self.agent._set_state(msa_state, WorkflowState.S_EXEC_R1)
        self.agent._ensure_data_lake(step.owner_agent)
        data_catalog = self.agent._build_data_catalog(step.owner_agent)
        execution_think, execution_code = self.agent._generate_execution_step(
            step,
            user_query=msa_state.user_query,
            context_handoff=previous_handoff,
            data_catalog=data_catalog,
        )
        tool_scope = self.agent._load_tool_scope(step.owner_agent)
        self.agent._emit(
            msa_state,
            f"[Execution-R1 | {step.owner_agent} | Step {step.step_id} Message]",
            f"Executing: {step.step}",
            {"execution_think": execution_think, "executed_code": execution_code},
            stream,
        )
        observe_output = self.agent._run_code(execution_code, tool_scope)
        observe_output = str(observe_output)[: self.agent.runtime.observation_max_chars]

        self.agent._set_state(msa_state, WorkflowState.S_EXEC_R2)
        verifier = self.agent._verify_step(step, execution_code, observe_output)
        self.agent._emit(
            msa_state,
            f"[Execution-R2 Verifier | {step.owner_agent} | Step {step.step_id} Message]",
            f"status={verifier.status.value}, reason={verifier.reason}",
            asdict(verifier),
            stream,
        )

        msa_state.execution_history.append(
            {
                "step_id": step.step_id,
                "owner_agent": step.owner_agent,
                "execution_think": execution_think,
                "executed_code": execution_code,
                "observe_output": observe_output,
                "verifier": asdict(verifier),
            }
        )
        last_output = observe_output
        previous_handoff = {
            "previous_step_id": step.step_id,
            "previous_step_observe_output": observe_output,
        }

        decision = self.agent._orchestrator_exec_decide(
            state=msa_state,
            step=step,
            verifier=verifier,
            retry_count=retries.get(step.step_id, 0),
            plan_revision_count=revision_count,
        )
        self.agent._emit(
            msa_state,
            "[Orchestrator Exec Message]",
            f"action={decision['action']} instruction={decision['instruction']}",
            decision,
            stream,
        )

        action = str(decision["action"])
        if action == "PLAN_REVISION" and verifier.status != VerifierStatus.PLAN_REVISION:
            action = "RETRY"
        if verifier.status == VerifierStatus.PLAN_REVISION and action != "PLAN_REVISION":
            action = "PLAN_REVISION"

        if action == "NEXT":
            return {
                "msa_state": msa_state,
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
            count = retries.get(step.step_id, 0)
            if count >= self.agent.runtime.step_retry_limit:
                msa_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "step_retry_limit_exceeded_without_plan_revision",
                    }
                )
                execution_answer = self.agent._synthesize_act(msa_state, last_output)
                return {
                    "msa_state": msa_state,
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
                "msa_state": msa_state,
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
            if verifier.status != VerifierStatus.PLAN_REVISION:
                msa_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "blocked_non_verifier_plan_revision",
                    }
                )
                execution_answer = self.agent._synthesize_act(msa_state, last_output)
                return {
                    "msa_state": msa_state,
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
                msa_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "plan_revision_limit_exceeded",
                    }
                )
                execution_answer = self.agent._synthesize_act(msa_state, last_output)
                return {
                    "msa_state": msa_state,
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
            target = step.step_id
            changed = self.agent._partial_replan(
                msa_state,
                target,
                verifier.reason,
                verifier.immediate_action,
                stream,
            )
            if not changed:
                execution_answer = self.agent._synthesize_act(msa_state, last_output)
                return {
                    "msa_state": msa_state,
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
                "msa_state": msa_state,
                "exec_route": "continue",
                "idx": max(0, target - 1),
                "retries": retries,
                "revision_count": revision_count,
                "full_reset_count": full_reset_count,
                "full_reset_pending": None,
                "last_output": last_output,
                "previous_handoff": previous_handoff,
            }

        if action == "FULL_RESET":
            if verifier.status != VerifierStatus.PLAN_REVISION:
                msa_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "blocked_non_verifier_full_reset",
                    }
                )
                retries[step.step_id] = retries.get(step.step_id, 0) + 1
                if retries[step.step_id] > self.agent.runtime.step_retry_limit:
                    execution_answer = self.agent._synthesize_act(msa_state, last_output)
                    return {
                        "msa_state": msa_state,
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
                    "msa_state": msa_state,
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
                msa_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "blocked_non_exception_full_reset",
                    }
                )
                retries[step.step_id] = retries.get(step.step_id, 0) + 1
                if retries[step.step_id] > self.agent.runtime.step_retry_limit:
                    execution_answer = self.agent._synthesize_act(msa_state, last_output)
                    return {
                        "msa_state": msa_state,
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
                    "msa_state": msa_state,
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
                msa_state.replan_history.append(
                    {
                        "target_step": step.step_id,
                        "reason": verifier.reason,
                        "applied": False,
                        "note": "full_reset_limit_exceeded",
                    }
                )
                execution_answer = self.agent._synthesize_act(msa_state, last_output)
                return {
                    "msa_state": msa_state,
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
            return {
                "msa_state": msa_state,
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
        msa_state = state["msa_state"]
        stream = bool(state.get("stream", False))
        self.agent._set_state(msa_state, WorkflowState.S_SYNTHESIZER)
        answer = self.agent._synthesize_final(
            msa_state,
            mode="no_act",
            execution_answer="",
        )
        self.agent._emit(msa_state, "[Synthesizer Message]", answer, None, stream)
        return {"msa_state": msa_state, "final_answer": answer}

    def synth_act(self, state: dict[str, Any]) -> dict[str, Any]:
        msa_state = state["msa_state"]
        stream = bool(state.get("stream", False))
        execution_answer = str(state.get("execution_answer", ""))
        self.agent._set_state(msa_state, WorkflowState.S_SYNTHESIZER)
        answer = self.agent._synthesize_final(
            msa_state,
            mode="act",
            execution_answer=execution_answer,
        )
        self.agent._emit(msa_state, "[Synthesizer Message]", answer, None, stream)
        return {"msa_state": msa_state, "final_answer": answer}
