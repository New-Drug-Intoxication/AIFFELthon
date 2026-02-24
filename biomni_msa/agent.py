from __future__ import annotations

import json
import importlib.util
import os
import re
import sys
from dataclasses import asdict
from io import StringIO
from pathlib import Path
from typing import Any, Callable

from biomni_msa.config import AgentRuntimeConfig, MSAPaths
from biomni_msa.core.execution import (
    inject_repl_scope,
    run_python_repl,
    run_with_timeout,
)
from biomni_msa.data_lake import ensure_data_lake_files
from biomni_msa.graph import build_msa_graph
from biomni_msa.llm_backend import LLMBackend
from biomni_msa.prompt_store import PromptStore
from biomni_msa.resource_store import ResourceStore
from biomni_msa.schemas import (
    MSAState,
    MessageEvent,
    RouterOutput,
    StepSpec,
    VerifierOutput,
    VerifierStatus,
    WorkflowState,
)


DOMAINS = [
    "Biochemistry",
    "Bioengineering",
    "Biophysics",
    "Cell Biology",
    "Synthetic Biology",
    "Genetics",
    "Genomics",
    "Microbiology",
    "Molecular Biology",
    "Pathology",
    "Pharmacology",
    "Physiology",
    "Common",
]


class MSAAgent:
    def __init__(
        self,
        paths: MSAPaths | None = None,
        runtime: AgentRuntimeConfig | None = None,
        llm_model: str | None = None,
        event_callback: Callable[[dict[str, Any]], None] | None = None,
    ):
        self.paths = paths or MSAPaths.default()
        self.runtime = runtime or AgentRuntimeConfig()
        self.prompts = PromptStore(self.paths.prompt_root)
        self.resources = ResourceStore(
            self.paths.repo_root, self.paths.resource_index_file
        )
        self.domain_profiles = self._load_domain_profiles()
        self.domain_runtime: dict[str, dict[str, Any]] = {}
        resolved_model = llm_model or os.getenv("MSA_LLM") or os.getenv("MSA_LLM_MODEL")
        self.llm = LLMBackend(model_name=resolved_model)
        self.graph = build_msa_graph(self)
        self.event_callback = event_callback

    def go(
        self, query: str, verbose: bool | None = None, stream: bool = False
    ) -> dict[str, Any]:
        normalized_query = str(query).strip()
        show_trace = self.runtime.verbose_default if verbose is None else verbose
        state = MSAState(user_query=normalized_query)
        self.llm.reset_usage()
        final_answer = ""
        try:
            if not normalized_query:
                self._set_state(state, WorkflowState.S_ROUTER)
                router_out = RouterOutput(
                    selected_agents=[],
                    route_reason="empty_user_query",
                    act_required=False,
                    domain_scores={},
                )
                state.router_output = router_out
                self._emit(
                    state,
                    "[Router Message]",
                    "selected=[], act_required=False (empty query)",
                    asdict(router_out),
                    stream,
                )
                self._set_state(state, WorkflowState.S_SYNTHESIZER)
                final_answer = (
                    "입력된 쿼리가 없습니다. 질의를 입력한 뒤 다시 실행해 주세요."
                )
                self._emit(state, "[Synthesizer Message]", final_answer, None, stream)
                self._sync_token_usage(state)
                if stream:
                    totals = state.token_usage_total
                    print(
                        "[Token Summary] "
                        f"input token: {int(totals.get('input', 0))}, "
                        f"output token: {int(totals.get('output', 0))}, "
                        f"total token: {int(totals.get('total', 0))}"
                    )
                return self._result(state, final_answer, show_trace)

            result_state = self.graph.invoke({"msa_state": state, "stream": stream})
            final_answer = str(result_state.get("final_answer", ""))
            self._sync_token_usage(state)
            if stream:
                totals = state.token_usage_total
                print(
                    "[Token Summary] "
                    f"input token: {int(totals.get('input', 0))}, "
                    f"output token: {int(totals.get('output', 0))}, "
                    f"total token: {int(totals.get('total', 0))}"
                )
            return self._result(state, final_answer, show_trace)
        except Exception:
            self._sync_token_usage(state)
            raise

    def _run_plan_pipeline(
        self,
        state: MSAState,
        selected_agents: list[str],
        stream: bool,
    ) -> None:
        domain_r2_outputs: list[dict[str, Any]] = []
        domain_r3_outputs: list[dict[str, Any]] = []
        self.domain_runtime = {}

        for domain in selected_agents:
            self._set_state(state, WorkflowState.S_PLAN_R1)
            r1 = self._plan_r1(domain, state.user_query)
            self._emit(
                state,
                f"[Plan-R1 | {domain} Message]",
                f"selected IDs: tools={len(r1['tools'])}, data={len(r1['data_lake'])}, libs={len(r1['libraries'])}, know_how={len(r1['know_how'])}",
                r1,
                stream,
            )
            self._set_state(state, WorkflowState.S_PLAN_R2)
            r2 = self._plan_r2(domain, state.user_query, r1)
            self.domain_runtime[domain] = {
                "r1": r1,
                "resolved": self.resources.resolve_selected(
                    r1["tools"],
                    r1["data_lake"],
                    r1["libraries"],
                    r1["know_how"],
                ),
            }
            domain_r2_outputs.append({"domain": domain, **r2})
            self._emit(
                state,
                f"[Plan-R2 | {domain} Message]",
                f"steps={len(r2.get('checklist_steps', []))}",
                r2,
                stream,
            )

        self._set_state(state, WorkflowState.S_PLAN_R21)
        draft_plan = self._orchestrator_r21(domain_r2_outputs, state.user_query)
        state.draft_master_plan = draft_plan
        self._emit(
            state,
            "[Orchestrator R2.1 Message]",
            f"draft steps={len(draft_plan)}",
            {"draft_master_plan": [asdict(x) for x in draft_plan]},
            stream,
        )

        for domain in selected_agents:
            self._set_state(state, WorkflowState.S_PLAN_R3)
            critique = self._plan_r3(domain, draft_plan, state.user_query)
            domain_r3_outputs.append({"agent": domain, **critique})
            self._emit(
                state,
                f"[Plan-R3 | {domain} Message]",
                critique.get("critique", ""),
                critique,
                stream,
            )

        self._set_state(state, WorkflowState.S_PLAN_R31)
        final_plan = self._orchestrator_r31(
            draft_plan,
            domain_r3_outputs,
            query=state.user_query,
            allowed_owners=set(selected_agents) | {"Common"},
        )
        state.final_master_plan = final_plan
        self._emit(
            state,
            "[Orchestrator R3.1 Message]",
            f"final steps={len(final_plan)}",
            {"final_master_plan": [asdict(x) for x in final_plan]},
            stream,
        )

    def _router_stage(self, state: MSAState) -> RouterOutput:
        cutoff = 0.8
        prompt = self._inject_prompt(
            self.prompts.router(),
            {"user_query": state.user_query},
        )
        payload = self.llm.complete_json_strict(
            prompt,
            required_keys=[
                "selected_agents",
                "route_reason",
                "act_required",
                "domain_scores",
            ],
            retries=self.runtime.json_retries,
            stage="router",
        )
        selected = payload.get("selected_agents", [])
        if not isinstance(selected, list) or not selected:
            raise RuntimeError("Router returned invalid selected_agents")
        domain_scores = {
            str(k): max(0.0, min(1.0, float(v)))
            for k, v in payload.get("domain_scores", {}).items()
        }
        selected_norm = [
            str(x)
            for x in selected
            if str(x) in DOMAINS and float(domain_scores.get(str(x), 0.0)) >= cutoff
        ]
        if not selected_norm:
            # Keep pipeline moving: if cutoff removes all, keep the highest-scored
            # originally selected domain as a fallback.
            original_selected = [str(x) for x in selected if str(x) in DOMAINS]
            if not original_selected:
                raise RuntimeError(
                    "Router selected_agents became empty after policy enforcement"
                )
            best = max(
                original_selected,
                key=lambda d: float(domain_scores.get(d, 0.0)),
            )
            selected_norm = [best]
        return RouterOutput(
            selected_agents=selected_norm,
            route_reason=str(payload.get("route_reason", "")),
            act_required=bool(payload.get("act_required", False)),
            domain_scores=domain_scores,
        )

    def _plan_r1(self, domain: str, query: str) -> dict[str, Any]:
        domain_slug = domain.lower().replace(" ", "_")
        indexed = self.resources.list_for_domain(domain_slug)
        profile = self.domain_profiles.get(domain, {})
        section = self.prompts.domain_round(
            "1 Round - Tool Retriever",
            ["2 Round - Planner", "3 Round - Critique", "Excution"],
        )
        prompt = self._inject_prompt(
            section,
            {
                "domain": domain,
                "domain_description": str(profile.get("description", "")),
                "domain_functions": self._format_domain_functions(
                    profile.get("functions", [])
                ),
                "user_query": query,
                "selected_tools_with_desc": self._format_resources_for_plan_prompt(
                    indexed["tools"], include_index=True, include_id=False
                ),
                "selected_data_lake_with_desc": self._format_resources_for_plan_prompt(
                    indexed["data_lake"], include_index=True, include_id=False
                ),
                "selected_libraries_with_desc": self._format_resources_for_plan_prompt(
                    indexed["libraries"], include_index=True, include_id=False
                ),
                "selected_know_how_section": self._format_plan_optional_section(
                    "사용 가능한 KNOW-HOW",
                    self._format_resources_for_plan_prompt(
                        indexed.get("know_how", []),
                        include_index=True,
                        include_id=False,
                    ),
                ),
            },
        )
        payload = self.llm.complete_json_strict(
            prompt,
            required_keys=["tools", "data_lake", "libraries", "know_how"],
            retries=self.runtime.json_retries,
            stage=f"plan_r1:{domain}",
            validator=lambda d: self._validate_r1_indices_with_reason(
                d,
                sizes={
                    "tools": len(indexed["tools"]),
                    "data_lake": len(indexed["data_lake"]),
                    "libraries": len(indexed["libraries"]),
                    "know_how": len(indexed.get("know_how", [])),
                },
            ),
        )
        return {
            "tools": self._indices_or_ids_to_ids(
                self._to_int_list(payload.get("tools", [])),
                indexed["tools"],
            ),
            "data_lake": self._indices_or_ids_to_ids(
                self._to_int_list(payload.get("data_lake", [])),
                indexed["data_lake"],
            ),
            "libraries": self._indices_or_ids_to_ids(
                self._to_int_list(payload.get("libraries", [])),
                indexed["libraries"],
            ),
            "know_how": self._indices_or_ids_to_ids(
                self._to_int_list(payload.get("know_how", [])),
                indexed.get("know_how", []),
            ),
        }

    def _plan_r2(
        self,
        domain: str,
        query: str,
        r1: dict[str, Any],
        revision_instruction: str = "",
    ) -> dict[str, Any]:
        resolved = self.resources.resolve_selected(
            r1["tools"], r1["data_lake"], r1["libraries"], r1.get("know_how", [])
        )
        profile = self.domain_profiles.get(domain, {})
        section = self.prompts.domain_round(
            "2 Round - Planner",
            ["3 Round - Critique", "Excution"],
        )
        prompt = self._inject_prompt(
            section,
            {
                "domain": domain,
                "domain_description": str(profile.get("description", "")),
                "domain_functions": self._format_domain_functions(
                    profile.get("functions", [])
                ),
                "user_query": query,
                "round1_selected_resources": self._format_round1_selection(r1),
                "selected_tools_with_desc": self._format_resources_for_plan_prompt(
                    resolved["tools"], include_index=False, include_id=False
                ),
                "selected_data_lake_with_desc": self._format_resources_for_plan_prompt(
                    resolved["data_lake"], include_index=False, include_id=False
                ),
                "selected_libraries_with_desc": self._format_resources_for_plan_prompt(
                    resolved["libraries"], include_index=False, include_id=False
                ),
                "selected_know_how_section": self._format_plan_optional_section(
                    "KNOW-HOW",
                    self._format_resources_for_plan_prompt(
                        resolved.get("know_how", []),
                        include_index=False,
                        include_id=False,
                    ),
                ),
                "revision_instruction": revision_instruction,
            },
        )
        text = self.llm.complete(prompt, stage=f"plan_r2_text:{domain}").text
        parsed = self._parse_checkbox_steps(
            text,
            stage=f"plan_r2:{domain}",
            default_owner=domain,
            require_owner=False,
        )
        checklist_steps = []
        checklist = []
        for i, item in enumerate(parsed, start=1):
            step_text = str(item.get("step", "")).strip()
            if not step_text:
                continue
            checklist_steps.append(
                {
                    "step_id": i,
                    "step": step_text,
                    "owner_agent": None,
                    "success_criteria": str(item.get("success_criteria", "")).strip()
                    or "done",
                }
            )
            checklist.append(f"[ ] {step_text}")
        if not checklist_steps:
            raise RuntimeError(f"plan_r2 missing checklist steps for domain={domain}")
        return {
            "checklist": checklist,
            "checklist_steps": checklist_steps,
            "note": "",
            "domain_thinking": "",
        }

    def _orchestrator_r21(
        self, domain_r2_outputs: list[dict[str, Any]], user_query: str
    ) -> list[StepSpec]:
        combined: list[StepSpec] = []
        criteria_map: dict[tuple[str, str], str] = {}
        seen: set[tuple[str, str]] = set()
        sid = 1
        for out in domain_r2_outputs:
            domain = out["domain"]
            for srow in out.get("checklist_steps", []):
                stext = str(srow.get("step", "")).strip().lower()
                scrit = str(srow.get("success_criteria", "")).strip()
                if stext and scrit:
                    criteria_map[(domain, stext)] = scrit
            for step in out.get("checklist_steps", []):
                text = str(step.get("step", "")).strip()
                if not text:
                    continue
                key = (domain, text.lower())
                if key in seen:
                    continue
                seen.add(key)
                combined.append(
                    StepSpec(
                        step_id=sid,
                        step=text,
                        owner_agent=domain,
                        success_criteria=criteria_map.get(
                            (domain, text.lower()), "done"
                        ),
                    )
                )
                sid += 1
        if not combined:
            raise RuntimeError(
                "orchestrator_r21 requires non-empty checklist_steps from domains"
            )
        section = self.prompts.orchestrator_module("Orchestrator Module 1", [])
        prompt = self._inject_prompt(
            section,
            {
                "user_query": user_query,
                "all_agent_round_2_responses": self._format_round2_responses(
                    domain_r2_outputs
                ),
            },
        )
        allowed_owners = {str(x.get("domain", "")).strip() for x in domain_r2_outputs}
        allowed_owners.discard("")
        allowed_owners.add("Common")
        prompt += (
            "\n\nAllowed owner agents for this run (use ONLY these values): "
            + ", ".join(sorted(allowed_owners))
        )
        text = self.llm.complete(prompt, stage="orchestrator_r21_text").text
        rows = self._parse_checkbox_steps(
            text,
            stage="orchestrator_r21",
            default_owner="Common",
            require_owner=True,
        )
        out = []
        for i, row in enumerate(rows, start=1):
            owner = self._resolve_owner_agent(
                str(row.get("owner_agent", "Common")),
                allowed=allowed_owners,
            )
            step_text = str(row.get("step", "")).strip() or f"draft step {i}"
            out.append(
                StepSpec(
                    step_id=i,
                    step=step_text,
                    owner_agent=owner,
                    success_criteria=criteria_map.get(
                        (owner, step_text.lower()),
                        str(row.get("success_criteria", "done")) or "done",
                    ),
                )
            )
        if not out:
            raise RuntimeError("orchestrator_r21 returned empty draft_master_plan")
        return out

    def _plan_r3(
        self, domain: str, draft_plan: list[StepSpec], user_query: str
    ) -> dict[str, Any]:
        section = self.prompts.domain_round("3 Round - Critique", ["Excution"])
        prompt = self._inject_prompt(
            section,
            {
                "domain": domain,
                "user_query": user_query,
                "draft_master_plan": self._format_plan_steps_for_prompt(draft_plan),
            },
        )
        payload = self.llm.complete_json_strict(
            prompt,
            required_keys=["critique", "recommended_changes"],
            retries=self.runtime.json_retries,
            stage=f"plan_r3:{domain}",
        )
        if not isinstance(payload.get("recommended_changes"), list):
            raise RuntimeError(
                f"plan_r3 invalid recommended_changes for domain={domain}"
            )
        return payload

    def _orchestrator_r31(
        self,
        draft: list[StepSpec],
        critiques: list[dict[str, Any]],
        query: str,
        allowed_owners: set[str] | None = None,
    ) -> list[StepSpec]:
        normalized: list[StepSpec] = []
        extra_steps: list[StepSpec] = []
        for i, step in enumerate(draft, start=1):
            normalized.append(
                StepSpec(
                    step_id=i,
                    step=step.step,
                    owner_agent=step.owner_agent,
                    success_criteria=step.success_criteria or "done",
                )
            )
        sid = len(normalized) + 1
        for row in critiques:
            agent = str(row.get("agent", "Common"))
            for change in row.get("recommended_changes", []) or []:
                text = str(change).strip()
                if not text:
                    continue
                extra_steps.append(
                    StepSpec(
                        step_id=sid,
                        step=f"Critique update: {text}",
                        owner_agent=agent,
                        success_criteria="critique-resolved",
                    )
                )
                sid += 1
        normalized.extend(extra_steps)
        section = self.prompts.orchestrator_module("Orchestrator Module 2", [])
        prompt = self._inject_prompt(
            section,
            {
                "user_query": query,
                "draft_master_plan": self._format_plan_steps_for_prompt(draft),
                "all_agent_round_3_critiques": self._format_critiques_for_prompt(
                    critiques
                ),
            },
        )
        valid_owners = allowed_owners or (set(DOMAINS) | {"Common"})
        prompt += (
            "\n\nAllowed owner agents for this run (use ONLY these values): "
            + ", ".join(sorted(valid_owners))
        )
        text = self.llm.complete(prompt, stage="orchestrator_r31_text").text
        rows = self._parse_checkbox_steps(
            text,
            stage="orchestrator_r31",
            default_owner="Common",
            require_owner=True,
        )
        out = []
        for i, row in enumerate(rows, start=1):
            owner = self._resolve_owner_agent(
                str(row.get("owner_agent", "Common")),
                allowed=valid_owners,
            )
            out.append(
                StepSpec(
                    step_id=i,
                    step=str(row.get("step", "")).strip() or f"final step {i}",
                    owner_agent=owner,
                    success_criteria=str(row.get("success_criteria", "done")) or "done",
                )
            )
        if not out:
            raise RuntimeError("orchestrator_r31 returned empty final_master_plan")
        return out

    @staticmethod
    def _parse_checkbox_steps(
        text: str,
        stage: str,
        default_owner: str = "Common",
        require_owner: bool = False,
    ) -> list[dict[str, str]]:
        lines = text.splitlines()
        rows: list[dict[str, str]] = []
        for line in lines:
            m = re.match(r"^\s*\d+\.\s*\[[ ✓✗]\]\s*(.+?)\s*$", line)
            if not m:
                continue
            body = m.group(1).strip()
            if not body:
                continue
            owner = default_owner
            owner_match = re.match(r"^\[(.+?)\]\s*(.+)$", body)
            if owner_match:
                owner = owner_match.group(1).strip() or default_owner
                body = owner_match.group(2).strip()
            elif require_owner:
                continue
            success = "done"
            sc_match = re.match(
                r"^(.*?)\s*\|\s*success_criteria\s*:\s*(.+)\s*$",
                body,
                flags=re.IGNORECASE,
            )
            if sc_match:
                body = sc_match.group(1).strip()
                success = sc_match.group(2).strip() or "done"
            if not body:
                continue
            rows.append(
                {
                    "step": body,
                    "owner_agent": owner,
                    "success_criteria": success,
                }
            )
        if not rows:
            raise RuntimeError(f"{stage} returned no checkbox steps")
        return rows

    def _execution_loop(self, state: MSAState, stream: bool) -> str:
        del state, stream
        raise RuntimeError(
            "_execution_loop is deprecated. Execution flow is managed by LangGraph nodes."
        )

    def _run_code(self, code: str, tool_scope: dict[str, Any]) -> str:
        try:
            inject_repl_scope(tool_scope)
            return str(
                run_with_timeout(
                    run_python_repl,
                    args=[code],
                    timeout=self.runtime.timeout_seconds,
                )
            )
        except Exception as e:
            return f"Error: execution runtime failure before run_with_timeout: {e}"

    def _generate_execution_step(
        self,
        step: StepSpec,
        user_query: str,
        context_handoff: dict[str, Any] | None,
        data_catalog: list[dict[str, Any]],
    ) -> tuple[str, str]:
        section = self.prompts.domain_round("1 Round - Write and run code", [])
        profile = self.domain_profiles.get(step.owner_agent, {})
        runtime_ctx = self.domain_runtime.get(step.owner_agent, {})
        resolved = runtime_ctx.get("resolved", {})
        tool_bindings = self._build_tool_bindings(
            step.owner_agent, resolved.get("tools", [])
        )
        allowed_tool_names = [x["name"] for x in tool_bindings]
        resolved_for_prompt = resolved
        catalog_for_prompt = data_catalog
        prompt = self._inject_prompt(
            section,
            {
                "domain": step.owner_agent,
                "domain_description": str(profile.get("description", "")),
                "domain_functions": self._format_domain_functions(
                    profile.get("functions", [])
                ),
                "user_query": user_query,
                "current_step_description": step.step,
                "success_criteria": step.success_criteria,
                "context_handoff_from_orchestrator": self._format_context_handoff_for_prompt(
                    context_handoff
                ),
                "selected_tools_with_desc": self._format_tool_specs_for_exec_prompt(
                    tool_bindings, limit=80
                ),
                "selected_data_lake_with_desc": self._format_data_resources_for_exec_prompt(
                    resolved_for_prompt.get("data_lake", []), limit=80
                ),
                "selected_libraries_with_desc": self._format_library_resources_for_exec_prompt(
                    resolved_for_prompt.get("libraries", []), limit=80
                ),
                "allowed_tools_for_exec": self._format_allowed_tools_for_prompt(
                    allowed_tool_names
                ),
                "data_file_candidates": self._format_data_catalog_lines(
                    catalog_for_prompt
                ),
            },
        )
        prompt += (
            "\n\n[Runtime Tool Binding Rule]\n"
            "- Tool functions are pre-injected into runtime scope.\n"
            "- Call tool functions directly by function name.\n"
            "- Do not import tool modules manually.\n"
            "- DO NOT use `import tools`, `from tools import ...`, or `from msa_tools ...`.\n"
            f"- Allowed tool names:\n{self._format_allowed_tools_for_prompt(allowed_tool_names)}\n"
        )
        retries = max(2, self.runtime.json_retries + 2)
        last_reason = "execute_block_missing"
        for attempt in range(retries):
            attempt_prompt = prompt
            if attempt > 0:
                attempt_prompt += (
                    "\n\n반드시 하나의 <execute>...</execute> 블록만 출력하십시오."
                    "\n설명문, JSON, 마크다운은 금지합니다."
                    f"\n직전 실패 사유: {last_reason}"
                )
            resp = self.llm.complete(
                attempt_prompt,
                stage=f"exec_r1:{step.owner_agent}:step{step.step_id}",
            ).text
            ok, payload = self._extract_execute_block_with_reason(resp)
            if ok:
                valid, reason = self._validate_exec_code_with_reason(
                    payload,
                    allowed_tool_names=set(allowed_tool_names),
                )
                if not valid:
                    last_reason = reason
                    continue
                return "", payload
            last_reason = payload
        raise RuntimeError(
            f"Execution R1 code generation failed at step {step.step_id}: {last_reason}"
        )

    @staticmethod
    def _format_domain_functions(functions: Any) -> str:
        if not isinstance(functions, list):
            return str(functions)
        lines = []
        for i, item in enumerate(functions, start=1):
            text = str(item).strip()
            if text:
                lines.append(f"{i}. {text}")
        return "\n".join(lines)

    @staticmethod
    def _format_round1_selection(r1: dict[str, Any]) -> str:
        tools = ", ".join(str(x) for x in r1.get("tools", [])) or "-"
        data_lake = ", ".join(str(x) for x in r1.get("data_lake", [])) or "-"
        libraries = ", ".join(str(x) for x in r1.get("libraries", [])) or "-"
        know_how = ", ".join(str(x) for x in r1.get("know_how", [])) or "-"
        return (
            f"tools: {tools}\n"
            f"data_lake: {data_lake}\n"
            f"libraries: {libraries}\n"
            f"know_how: {know_how}"
        )

    @staticmethod
    def _format_round2_responses(domain_r2_outputs: list[dict[str, Any]]) -> str:
        chunks: list[str] = []
        for row in domain_r2_outputs:
            domain = str(row.get("domain", ""))
            checklist = row.get("checklist", [])
            thinking = str(row.get("domain_thinking", "")).strip()
            lines = [f"[Agent] {domain}"]
            if isinstance(checklist, list) and checklist:
                lines.append("checklist:")
                for i, item in enumerate(checklist, start=1):
                    lines.append(f"  {i}. {str(item)}")
            else:
                lines.append("checklist: -")
            if thinking:
                lines.append(f"domain_thinking: {thinking[:1200]}")
            chunks.append("\n".join(lines))
        return "\n\n".join(chunks)

    @staticmethod
    def _format_plan_steps_for_prompt(steps: list[StepSpec]) -> str:
        if not steps:
            return "-"
        rows: list[str] = []
        for s in steps:
            rows.append(
                f"{s.step_id}. [{s.owner_agent}] {s.step} | success_criteria: {s.success_criteria}"
            )
        return "\n".join(rows)

    @staticmethod
    def _format_critiques_for_prompt(critiques: list[dict[str, Any]]) -> str:
        if not critiques:
            return "-"
        rows: list[str] = []
        for idx, c in enumerate(critiques, start=1):
            agent = str(c.get("agent", "Common"))
            critique = str(c.get("critique", "")).strip()
            changes = c.get("recommended_changes", [])
            rows.append(f"[{idx}] agent={agent}")
            rows.append(f"  critique: {critique if critique else '-'}")
            valid_changes: list[str] = []
            if isinstance(changes, list):
                for change in changes:
                    text = str(change).strip()
                    if text:
                        valid_changes.append(text)
            if valid_changes:
                rows.append("  recommended_changes:")
                item_no = 1
                for text in valid_changes:
                    rows.append(f"    {item_no}. {text}")
                    item_no += 1
        return "\n".join(rows)

    @staticmethod
    def _format_step_for_prompt(step: StepSpec) -> str:
        return (
            f"step_id: {step.step_id}\n"
            f"owner_agent: {step.owner_agent}\n"
            f"step: {step.step}\n"
            f"success_criteria: {step.success_criteria}"
        )

    @staticmethod
    def _format_verifier_for_prompt(verifier: VerifierOutput) -> str:
        return (
            f"status: {verifier.status.value}\n"
            f"reason: {verifier.reason}\n"
            f"immediate_action: {verifier.immediate_action}\n"
            f"observe_output: {verifier.observe_output[:1200]}"
        )

    @staticmethod
    def _format_router_output_for_prompt(router_output: RouterOutput | None) -> str:
        if router_output is None:
            return "-"
        selected = ", ".join(router_output.selected_agents)
        return (
            f"selected_agents: {selected}\n"
            f"act_required: {router_output.act_required}\n"
            f"route_reason: {router_output.route_reason}"
        )

    @staticmethod
    def _format_execution_history_for_prompt(history: list[dict[str, Any]]) -> str:
        if not history:
            return "-"
        rows: list[str] = []
        for row in history:
            sid = row.get("step_id", "")
            owner = row.get("owner_agent", "")
            verifier = row.get("verifier", {}) if isinstance(row, dict) else {}
            status = verifier.get("status", "") if isinstance(verifier, dict) else ""
            reason = verifier.get("reason", "") if isinstance(verifier, dict) else ""
            observe = str(row.get("observe_output", ""))[:400]
            rows.append(
                f"step={sid} owner={owner} status={status} reason={reason}\nobserve={observe}"
            )
        return "\n\n".join(rows)

    @staticmethod
    def _format_context_handoff_for_prompt(
        context_handoff: dict[str, Any] | None,
    ) -> str:
        if not context_handoff:
            return "- 없음 (첫 단계)"
        sid = context_handoff.get("previous_step_id", "")
        status = str(context_handoff.get("previous_step_status", "")).strip()
        reason = str(context_handoff.get("previous_step_reason", "")).strip()
        obs = str(context_handoff.get("previous_step_observe_output", "")).strip()
        action = str(context_handoff.get("orchestrator_instruction", "")).strip()
        lines: list[str] = []
        lines.append(f"1. previous_step_id: {sid if sid != '' else '-'}")
        if status:
            lines.append(f"2. previous_step_status: {status}")
        if reason:
            lines.append(f"3. previous_step_reason: {reason[:400]}")
        if action:
            lines.append(f"4. orchestrator_instruction: {action[:500]}")
        if obs:
            lines.append("5. previous_step_observe_output:")
            for row in obs[:1200].splitlines():
                text = row.strip()
                if text:
                    lines.append(f"   - {text}")
        if len(lines) == 1 and "previous_step_id" in lines[0]:
            lines.append("2. previous_step_observe_output: -")
        return "\n".join(lines)

    @staticmethod
    def _format_data_catalog_lines(data_catalog: list[dict[str, Any]]) -> str:
        if not data_catalog:
            return "-"
        rows: list[str] = []
        for i, row in enumerate(data_catalog, start=1):
            name = str(row.get("name", "")).strip()
            ext = str(row.get("ext", "")).strip()
            size = row.get("size", 0)
            cols = row.get("columns", [])
            col_preview = ", ".join(str(c) for c in cols[:8])
            rows.append(
                f"{i}. {name} ({ext}, size={size})"
                + (f" | columns: {col_preview}" if col_preview else "")
            )
        return "\n".join(rows)

    @staticmethod
    def _format_allowed_tools_for_prompt(tool_names: list[str]) -> str:
        if not tool_names:
            return "-"
        return "\n".join(f"- {name}" for name in tool_names if name)

    @staticmethod
    def _format_allowed_import_map_for_prompt(
        allowed_import_map: dict[str, set[str]],
    ) -> str:
        if not allowed_import_map:
            return "-"
        lines: list[str] = []
        for module in sorted(allowed_import_map.keys()):
            funcs = sorted(x for x in allowed_import_map.get(module, set()) if x)
            if not funcs:
                continue
            lines.append(f"- {module}: {', '.join(funcs)}")
        return "\n".join(lines) if lines else "-"

    @staticmethod
    def _format_required_map_for_prompt(required_map: dict[str, list[str]]) -> str:
        if not required_map:
            return "-"
        lines: list[str] = []
        for tool, reqs in required_map.items():
            if not tool:
                continue
            required = ", ".join([x for x in reqs if x]) if reqs else "(none)"
            lines.append(f"- {tool}: {required}")
        return "\n".join(lines) if lines else "-"

    def _orchestrator_exec_decide(
        self,
        state: MSAState,
        step: StepSpec,
        verifier: VerifierOutput,
        retry_count: int,
        plan_revision_count: int,
    ) -> dict[str, Any]:
        section = self.prompts.orchestrator_module("Orchestrator Module 3", [])
        prompt = section + "\n\nReturn JSON only with schema: "
        prompt += '{"action":"NEXT|RETRY|PLAN_REVISION|FULL_RESET","instruction":str,"target_step_id":int}.\n'
        prompt += (
            f"Current step:\n{self._format_step_for_prompt(step)}\n"
            f"Verifier:\n{self._format_verifier_for_prompt(verifier)}\n"
            f"Retry count: {retry_count}\n"
            f"Plan revision count: {plan_revision_count}\n"
            f"Progress: {len(state.execution_history)}/{len(state.final_master_plan)}\n"
        )
        return self.llm.complete_json_strict(
            prompt,
            required_keys=["action", "instruction", "target_step_id"],
            retries=self.runtime.json_retries,
            stage=f"orchestrator_exec:{step.owner_agent}:step{step.step_id}",
            validator=lambda d: str(d.get("action", ""))
            in {"NEXT", "RETRY", "PLAN_REVISION", "FULL_RESET"},
        )

    def _verify_step(
        self, step: StepSpec, code: str, observe_output: str
    ) -> VerifierOutput:
        section = self.prompts.domain_round("2 Round - Verifier", [])
        profile = self.domain_profiles.get(step.owner_agent, {})
        runtime_hint = ""
        if "Error:" in observe_output or "ERROR:" in observe_output:
            runtime_hint = "Runtime error marker detected in observation."
        prompt = (
            self._inject_prompt(
                section,
                {
                    "domain": step.owner_agent,
                    "domain_description": str(profile.get("description", "")),
                    "domain_functions": self._format_domain_functions(
                        profile.get("functions", [])
                    ),
                    "assigned_step_description": step.step,
                    "success_criteria": step.success_criteria,
                    "executed_code": code,
                    "observation_output": observe_output,
                },
            )
            + f"\n\nAdditional runtime hint: {runtime_hint}"
        )
        payload = self.llm.complete_json_strict(
            prompt,
            required_keys=["status", "reason", "immediate_action"],
            retries=self.runtime.json_retries,
            validator=lambda d: str(d.get("status", ""))
            in {"SUCCESS", "FAILURE", "PLAN_REVISION"},
            stage=f"verifier:{step.owner_agent}:step{step.step_id}",
        )
        if ("Error:" in observe_output or "ERROR:" in observe_output) and str(
            payload.get("status", "")
        ) == "PLAN_REVISION":
            payload["status"] = "FAILURE"
            payload["reason"] = "Runtime execution error must be FAILURE by policy"
            payload["immediate_action"] = "retry same step"
        return VerifierOutput(
            status=VerifierStatus(str(payload["status"])),
            reason=str(payload["reason"]),
            immediate_action=str(payload["immediate_action"]),
            observe_output=str(payload.get("observe_output", observe_output)),
        )

    def _synthesize_no_act(self, state: MSAState) -> str:
        return f"No ACT path selected. Query answered directly: {state.user_query}"

    def _synthesize_act(self, state: MSAState, last_output: str) -> str:
        return (
            "MSA execution completed. "
            f"steps={len(state.execution_history)}, replans={len(state.replan_history)}. "
            f"Last observe excerpt: {last_output[:200]}"
        )

    def _synthesize_final(
        self,
        state: MSAState,
        mode: str,
        execution_answer: str,
    ) -> str:
        if mode == "no_act":
            prompt = (
                "You are Synthesizer Agent.\n"
                "Answer the user's request directly and concisely.\n"
                "Follow explicit format constraints from the user (for example sentence count).\n"
                "Do not mention internal pipeline state, router output, missing logs, or caveat boilerplate unless explicitly requested.\n"
                f"user_query={state.user_query}\n"
            )
        else:
            router_text = self._format_router_output_for_prompt(state.router_output)
            plan_text = self._format_plan_steps_for_prompt(state.final_master_plan)
            history_text = self._format_execution_history_for_prompt(
                state.execution_history[-3:]
            )
            prompt_lines = [
                "You are Synthesizer Agent. Return final answer aligned with user_query.",
                "Use plan and execution evidence; include caveats if evidence is weak.",
                f"mode={mode}",
                f"user_query={state.user_query}",
            ]
            if router_text != "-":
                prompt_lines.append(f"router_output={router_text}")
            if plan_text != "-":
                prompt_lines.append(f"final_master_plan=\n{plan_text}")
            if history_text != "-":
                prompt_lines.append(f"execution_history=\n{history_text}")
            if execution_answer:
                prompt_lines.append(f"execution_summary={execution_answer}")
            prompt = "\n".join(prompt_lines) + "\n"
        stage = "synth_no_act" if mode == "no_act" else "synth_act"
        text = self.llm.complete(prompt, stage=stage).text.strip()
        if not text:
            raise RuntimeError("Synthesizer returned empty response")
        return text

    def _partial_replan(
        self,
        state: MSAState,
        target_step_id: int,
        reason: str,
        immediate_action: str,
        stream: bool,
    ) -> bool:
        selected_agents = (
            state.router_output.selected_agents if state.router_output else []
        )
        if not selected_agents:
            return False
        domain_r2_outputs: list[dict[str, Any]] = []
        domain_r3_outputs: list[dict[str, Any]] = []
        use_r1 = self._needs_replan_r1(reason, immediate_action)
        preserved_prefix = state.final_master_plan[: max(0, target_step_id - 1)]
        revision_instruction = (
            f"reason={reason}\n"
            f"immediate_action={immediate_action}\n"
            f"target_step_id={target_step_id}\n"
            f"preserve_prefix_steps:\n{self._format_plan_steps_for_prompt(preserved_prefix)}"
        )
        for domain in selected_agents:
            runtime_ctx = self.domain_runtime.get(domain, {})
            r1 = runtime_ctx.get("r1")
            if r1 is None or use_r1:
                r1 = self._plan_r1(domain, state.user_query)
            r2 = self._plan_r2(
                domain,
                state.user_query,
                r1,
                revision_instruction=revision_instruction,
            )
            domain_r2_outputs.append({"domain": domain, **r2})
        draft = self._orchestrator_r21(domain_r2_outputs, state.user_query)
        for domain in selected_agents:
            critique = self._plan_r3(domain, draft, state.user_query)
            domain_r3_outputs.append({"agent": domain, **critique})
        revised = self._orchestrator_r31(
            draft,
            domain_r3_outputs,
            query=state.user_query,
            allowed_owners=set(selected_agents) | {"Common"},
        )

        prefix = [
            StepSpec(
                step_id=x.step_id,
                step=x.step,
                owner_agent=x.owner_agent,
                success_criteria=x.success_criteria,
            )
            for x in preserved_prefix
        ]
        if len(revised) < len(prefix):
            return False
        tail_start = max(0, target_step_id - 1)
        tail = revised[tail_start:]
        if not tail:
            return False
        for i, step in enumerate(prefix + tail, start=1):
            step.step_id = i
        state.final_master_plan = prefix + tail
        state.replan_history.append(
            {
                "target_step": target_step_id,
                "reason": reason,
                "immediate_action": immediate_action,
                "replan_entry": "R1" if use_r1 else "R2",
                "applied": True,
                "new_tail_steps": len(tail),
            }
        )
        self._emit(
            state,
            "[Plan Revision Message]",
            f"target_step={target_step_id}, new_tail_steps={len(tail)}",
            None,
            stream,
        )
        return True

    def _ensure_data_lake(self, domain: str) -> None:
        runtime_ctx = self.domain_runtime.get(domain, {})
        resolved = runtime_ctx.get("resolved", {})
        selected = resolved.get("data_lake", [])
        names = [
            str(x.get("name", "")).strip()
            for x in selected
            if str(x.get("name", "")).strip()
        ]
        if not names:
            return
        self.paths.data_lake_root.mkdir(parents=True, exist_ok=True)
        missing = [n for n in names if not (self.paths.data_lake_root / n).exists()]
        if not missing:
            return
        if not self.runtime.s3_bucket_url:
            return
        try:
            ensure_data_lake_files(
                missing,
                data_lake_root=self.paths.data_lake_root,
                s3_bucket_url=self.runtime.s3_bucket_url,
                folder="data_lake",
            )
        except Exception:
            return

    def _result(
        self, state: MSAState, final_answer: str, show_trace: bool
    ) -> dict[str, Any]:
        base = {
            "final_answer": final_answer,
            "router_output": asdict(state.router_output)
            if state.router_output
            else None,
            "final_master_plan": [asdict(x) for x in state.final_master_plan],
            "execution_history": state.execution_history,
            "replan_history": state.replan_history,
            "current_state": state.current_state.value,
            "state_transition_history": state.state_transition_history,
            "token_usage_by_stage": state.token_usage_by_stage,
            "token_usage_total": state.token_usage_total,
        }
        if show_trace:
            base["messages"] = [asdict(x) for x in state.messages]
        return base

    def _sync_token_usage(self, state: MSAState) -> None:
        usage = self.llm.get_usage_snapshot()
        state.token_usage_by_stage = usage.get("by_stage", {})
        state.token_usage_total = usage.get(
            "total", {"input": 0, "output": 0, "total": 0}
        )

    def _load_domain_profiles(self) -> dict[str, dict[str, Any]]:
        fp = self.paths.resource_index_root / "domain_profiles.json"
        if not fp.exists():
            return {}
        return json.loads(fp.read_text(encoding="utf-8"))

    @staticmethod
    def _inject_prompt(template: str, values: dict[str, Any]) -> str:
        out = template
        for key, value in values.items():
            out = out.replace("{" + key + "}", "" if value is None else str(value))
        return MSAAgent._prune_empty_prompt_lines(out)

    @staticmethod
    def _prune_empty_prompt_lines(text: str) -> str:
        lines = text.splitlines()
        out: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=", stripped):
                i += 1
                continue
            if stripped.endswith(":"):
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j >= len(lines):
                    i = j
                    continue
                next_line = lines[j].strip()
                if next_line.startswith("---") or next_line.startswith("["):
                    i = j
                    continue
            out.append(line)
            i += 1
        return "\n".join(out)

    def _set_state(self, state: MSAState, next_state: WorkflowState) -> None:
        state.current_state = next_state
        state.state_transition_history.append(next_state.value)

    @staticmethod
    def _needs_replan_r1(reason: str, immediate_action: str) -> bool:
        t = f"{reason}\n{immediate_action}".lower()
        reselection = (
            "reselect" in t
            or "resel" in t
            or "재선정" in t
            or "미선정" in t
            or "잘못된 선정" in t
            or "round 1" in t
            or "r1" in t
        )
        resource_issue = (
            "resource" in t
            or "리소스" in t
            or "tool" in t
            or "library" in t
            or "data" in t
            or "dataset" in t
        )
        availability_issue = (
            "missing" in t
            or "unavailable" in t
            or "not found" in t
            or "누락" in t
            or "없음" in t
        )
        return reselection or (resource_issue and availability_issue)

    @staticmethod
    def _validate_owner_agent(owner_agent: str, allowed: set[str]) -> str:
        owner = owner_agent.strip()
        if not owner:
            raise RuntimeError("owner_agent must be non-empty")
        if owner not in DOMAINS:
            raise RuntimeError(f"owner_agent is not in supported domains: {owner}")
        if owner not in allowed:
            raise RuntimeError(f"owner_agent is not allowed by current route: {owner}")
        return owner

    @staticmethod
    def _resolve_owner_agent(owner_agent: str, allowed: set[str]) -> str:
        owner = owner_agent.strip()
        if not owner:
            return "Common" if "Common" in allowed else sorted(allowed)[0]
        domain_by_lower = {d.lower(): d for d in DOMAINS}
        canonical = domain_by_lower.get(owner.lower(), owner)
        if canonical in allowed and canonical in DOMAINS:
            return canonical

        if canonical == "Genomics" and "Genetics" in allowed:
            return "Genetics"
        if canonical == "Genetics" and "Genomics" in allowed:
            return "Genomics"

        if "Common" in allowed:
            return "Common"
        for domain in DOMAINS:
            if domain in allowed:
                return domain
        return canonical if canonical in DOMAINS else "Common"

    @staticmethod
    def _is_full_reset_exception(reason: str) -> bool:
        t = reason.lower()
        return (
            "핵심 입력 데이터" in reason
            or "오염" in reason
            or ("input" in t and "data" in t and ("missing" in t or "corrupt" in t))
            or "잘못된 도메인 라우팅" in reason
            or ("route" in t and "invalid" in t)
            or "안전" in reason
            or "윤리" in reason
            or "정책 위반" in reason
            or "safety" in t
            or "policy violation" in t
        )

    def _emit(
        self,
        state: MSAState,
        label: str,
        content: str,
        data: dict[str, Any] | None,
        stream: bool,
    ) -> None:
        event = MessageEvent(label=label, content=content, data=data)
        state.messages.append(event)
        stage_snapshot = {}
        if hasattr(self.llm, "get_last_stage_usage_snapshot"):
            stage_snapshot = self.llm.get_last_stage_usage_snapshot() or {}
        usage = stage_snapshot.get("usage", {})
        if isinstance(usage, dict):
            in_tok = int(usage.get("input", 0))
            out_tok = int(usage.get("output", 0))
            total_tok = int(usage.get("total", in_tok + out_tok))
        else:
            in_tok = 0
            out_tok = 0
            total_tok = 0
        callback_payload = {
            "label": label,
            "content": content,
            "data": data,
            "workflow_state": state.current_state.value,
            "stage": str(stage_snapshot.get("stage", "")).strip(),
            "token_usage": {
                "input": in_tok,
                "output": out_tok,
                "total": total_tok,
            },
        }
        if self.event_callback is not None:
            try:
                self.event_callback(callback_payload)
            except Exception:
                pass
        if stream:
            stage = str(stage_snapshot.get("stage", "")).strip()
            print(
                f"{label} {content} "
                f"(stage: {stage or '-'}, input token: {in_tok}, output token: {out_tok}, total token: {total_tok})"
            )

    @staticmethod
    def _coerce_int(value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            return int(text)
        except Exception:
            pass
        try:
            f = float(text)
        except Exception:
            return None
        if f.is_integer():
            return int(f)
        return None

    @staticmethod
    def _to_int_list(value: Any) -> list[int]:
        if not isinstance(value, list):
            return []
        out: list[int] = []
        for item in value:
            parsed = MSAAgent._coerce_int(item)
            if parsed is None:
                continue
            out.append(parsed)
        return out

    @staticmethod
    def _indices_or_ids_to_ids(
        selected: list[int], items: list[dict[str, Any]]
    ) -> list[int]:
        # R1 prompt shows local indices (0..n-1). Convert to stable resource IDs.
        # Keep compatibility if model occasionally returns IDs directly.
        out: list[int] = []
        seen: set[int] = set()
        id_set: set[int] = set()
        for row in items:
            parsed = MSAAgent._coerce_int(row.get("id"))
            if parsed is None:
                continue
            id_set.add(parsed)
        for v in selected:
            resolved: int | None = None
            if 0 <= v < len(items):
                resolved = MSAAgent._coerce_int(items[v].get("id"))
            elif v in id_set:
                resolved = v
            if resolved is None or resolved in seen:
                continue
            seen.add(resolved)
            out.append(resolved)
        return out

    @staticmethod
    def _short_desc_with_index(items: list[dict[str, Any]], limit: int = 25) -> str:
        lines: list[str] = []
        for i, x in enumerate(items[:limit]):
            name = str(x.get("name", "")).strip()
            desc = str(x.get("short_description", "")).strip()
            lines.append(f"{i}: {name} | {desc}")
        return "\n".join(lines)

    @staticmethod
    def _short_desc(items: list[dict[str, Any]], limit: int = 25) -> str:
        lines: list[str] = []
        for x in items[:limit]:
            rid = x.get("id", "")
            name = str(x.get("name", "")).strip()
            desc = str(x.get("short_description", "")).strip()
            lines.append(f"{rid}: {name} | {desc}")
        return "\n".join(lines)

    @staticmethod
    def _short_desc_no_id(items: list[dict[str, Any]], limit: int = 25) -> str:
        lines: list[str] = []
        for x in items[:limit]:
            name = str(x.get("name", "")).strip()
            desc = str(x.get("short_description", "")).strip()
            lines.append(f"{name} | {desc}")
        return "\n".join(lines)

    @staticmethod
    def _format_resources_for_plan_prompt(
        items: list[dict[str, Any]],
        include_index: bool = True,
        include_id: bool = False,
        limit: int = 25,
    ) -> str:
        if not items:
            return "-"
        lines: list[str] = []
        for i, row in enumerate(items[:limit]):
            name = str(row.get("name", "")).strip() or "(unnamed)"
            short = str(row.get("short_description", "")).strip()
            full = str(row.get("description", "")).strip()
            desc = short or full or "-"
            prefix = f"{i}." if include_index else "-"
            lines.append(f"{prefix} {name}")
            lines.append(f"   - description: {desc}")
        return "\n".join(lines)

    @staticmethod
    def _format_plan_optional_section(title: str, body: str) -> str:
        body_text = str(body or "").strip()
        if not body_text or body_text == "-":
            return ""
        return f"{title}:\n{body_text}"

    def _build_tool_bindings(
        self,
        domain: str,
        tools: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        del domain
        rows: list[dict[str, Any]] = []
        for tool in tools:
            name = str(tool.get("name", "")).strip()
            rel_path = str(tool.get("tool_file", "")).strip()
            if not name or not rel_path:
                continue
            rows.append(
                {
                    "name": name,
                    "short_description": str(tool.get("short_description", "")).strip(),
                    "required_parameters": tool.get("required_parameters", []),
                    "optional_parameters": tool.get("optional_parameters", []),
                    "tool_file": rel_path,
                }
            )
        return rows

    @staticmethod
    def _format_tool_specs_for_exec_prompt(
        tool_bindings: list[dict[str, Any]],
        limit: int = 80,
    ) -> str:
        if not tool_bindings:
            return "-"
        lines: list[str] = []
        for i, row in enumerate(tool_bindings[:limit], start=1):
            name = str(row.get("name", "")).strip()
            desc = str(row.get("short_description", "")).strip()
            required = row.get("required_parameters", [])
            optional = row.get("optional_parameters", [])
            lines.append(f"{i}. {name}")
            lines.append(f"   - description: {desc if desc else '-'}")
            lines.append("   - required_parameters:")
            req_count = 0
            if isinstance(required, list):
                for p in required:
                    if not isinstance(p, dict):
                        continue
                    pn = str(p.get("name", "")).strip()
                    pt = str(p.get("type", "")).strip()
                    pd = str(p.get("description", "")).strip()
                    if not pn:
                        continue
                    req_count += 1
                    lines.append(
                        f"     - {pn} ({pt if pt else 'any'}): {pd if pd else '-'}"
                    )
            if req_count == 0:
                lines.append("     - (none)")
            lines.append("   - optional_parameters:")
            opt_count = 0
            if isinstance(optional, list):
                for p in optional:
                    if not isinstance(p, dict):
                        continue
                    pn = str(p.get("name", "")).strip()
                    pt = str(p.get("type", "")).strip()
                    pd = str(p.get("description", "")).strip()
                    dv = p.get("default", None)
                    if not pn:
                        continue
                    opt_count += 1
                    lines.append(
                        f"     - {pn} ({pt if pt else 'any'}, default={dv}): {pd if pd else '-'}"
                    )
            if opt_count == 0:
                lines.append("     - (none)")
            lines.append(f"   - source: {row.get('tool_file', '')}")
            if i < min(limit, len(tool_bindings)):
                lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _format_data_resources_for_exec_prompt(
        items: list[dict[str, Any]], limit: int = 80
    ) -> str:
        if not items:
            return "-"

        def _clean(text: Any) -> str:
            return " ".join(str(text or "").split()).strip()

        lines: list[str] = []
        for i, x in enumerate(items[:limit], start=1):
            src = _clean(x.get("source_file", ""))
            raw_name = _clean(x.get("name", ""))
            fallback_name = Path(src).name if src else ""
            name = raw_name or fallback_name or "(unnamed_data)"
            desc = (
                _clean(x.get("description", ""))
                or _clean(x.get("short_description", ""))
                or "-"
            )
            lines.append(f"{i}. {name}")
            lines.append(f"   - description: {desc if desc else '-'}")
            if i < min(limit, len(items)):
                lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _format_library_resources_for_exec_prompt(
        items: list[dict[str, Any]], limit: int = 80
    ) -> str:
        if not items:
            return "-"

        def _clean(text: Any) -> str:
            return " ".join(str(text or "").split()).strip()

        lines: list[str] = []
        for i, x in enumerate(items[:limit], start=1):
            src = _clean(x.get("source_file", ""))
            raw_name = _clean(x.get("name", ""))
            fallback_name = Path(src).name if src else ""
            name = raw_name or fallback_name or "(unnamed_library)"
            desc = (
                _clean(x.get("description", ""))
                or _clean(x.get("short_description", ""))
                or "-"
            )
            lines.append(f"{i}. {name}")
            lines.append(f"   - description: {desc if desc else '-'}")
            if src:
                lines.append(f"   - source: {src}")
            if i < min(limit, len(items)):
                lines.append("")
        return "\n".join(lines)

    def _load_tool_scope(self, domain: str) -> dict[str, Any]:
        runtime_ctx = self.domain_runtime.get(domain, {})
        tools = self._build_tool_bindings(
            domain, runtime_ctx.get("resolved", {}).get("tools", [])
        )
        scope: dict[str, Any] = {}
        loaded_modules: dict[str, Any] = {}
        failed_modules: dict[str, str] = {}
        for tool in tools:
            name = str(tool.get("name", "")).strip()
            rel_path = str(tool.get("tool_file", "")).strip()
            if not name or not rel_path:
                continue
            if rel_path in failed_modules:
                scope[name] = self._missing_tool_stub(
                    name=name,
                    domain=domain,
                    rel_path=rel_path,
                    error=failed_modules[rel_path],
                )
                continue
            abs_path = self.paths.repo_root / rel_path
            if not abs_path.exists():
                continue
            module = loaded_modules.get(rel_path)
            if module is None:
                spec = importlib.util.spec_from_file_location(abs_path.stem, abs_path)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                except Exception as exc:
                    failed_modules[rel_path] = str(exc)
                    print(
                        f"[ToolScope] skip module load failed: domain={domain} file={rel_path} error={exc}"
                    )
                    scope[name] = self._missing_tool_stub(
                        name=name,
                        domain=domain,
                        rel_path=rel_path,
                        error=str(exc),
                    )
                    continue
                loaded_modules[rel_path] = module
            fn = getattr(module, name, None)
            if callable(fn):
                scope[name] = fn
        return scope

    @staticmethod
    def _missing_tool_stub(
        name: str,
        domain: str,
        rel_path: str,
        error: str,
    ):
        def _stub(*args: Any, **kwargs: Any) -> str:
            del args, kwargs
            return (
                f"Tool '{name}' is unavailable in domain '{domain}'. "
                f"module='{rel_path}'. load_error='{error}'. "
                "Install missing dependency and retry."
            )

        _stub.__name__ = name
        return _stub

    def _build_data_catalog(self, domain: str) -> list[dict[str, Any]]:
        runtime_ctx = self.domain_runtime.get(domain, {})
        selected = runtime_ctx.get("resolved", {}).get("data_lake", [])
        root = self.paths.data_lake_root
        root.mkdir(parents=True, exist_ok=True)
        catalog: list[dict[str, Any]] = []
        for item in selected:
            nm = str(item.get("name", "")).strip()
            if not nm:
                continue
            f = root / nm
            ext = f.suffix.lower() if f.exists() else Path(nm).suffix.lower()
            size = f.stat().st_size if f.exists() and f.is_file() else 0
            row: dict[str, Any] = {
                "path": str(f),
                "name": f.name if f.exists() else Path(nm).name,
                "ext": ext,
                "size": size,
                "columns": [],
            }
            if f.exists() and f.is_file() and ext in {".csv", ".tsv"}:
                try:
                    with f.open("r", encoding="utf-8", errors="ignore") as fp:
                        header = fp.readline().strip()
                        sep = "," if ext == ".csv" else "\t"
                        row["columns"] = [
                            x.strip() for x in header.split(sep) if x.strip()
                        ]
                except Exception:
                    pass
            catalog.append(row)
        return catalog

    @staticmethod
    def _extract_execute_block_with_reason(text: str) -> tuple[bool, str]:
        raw = str(text or "").strip()
        if not raw:
            return False, "empty_response"
        matches = re.findall(r"<execute>([\s\S]*?)</execute>", raw, flags=re.IGNORECASE)
        if len(matches) != 1:
            return False, "execute_block_count_not_one"
        code = str(matches[0]).strip()
        if not code:
            return False, "execute_block_empty"
        return True, code

    @staticmethod
    def _validate_exec_code_with_reason(
        code: str,
        allowed_tool_names: set[str] | None = None,
        allowed_import_map: dict[str, set[str]] | None = None,
    ) -> tuple[bool, str]:
        del allowed_tool_names, allowed_import_map
        src = str(code or "")
        if re.search(r"(?m)^\s*from\s+tools\s+import\s+", src):
            return False, "forbidden_import_from_tools"
        if re.search(r"(?m)^\s*import\s+tools\b", src):
            return False, "forbidden_import_tools_module"
        if re.search(r"(?m)^\s*from\s+msa_tools(\.|\\b)", src):
            return False, "forbidden_import_from_msa_tools"
        if re.search(r"(?m)^\s*import\s+msa_tools(\.|\\b)?", src):
            return False, "forbidden_import_msa_tools_module"
        return True, "ok"

    @staticmethod
    def _validate_calls_json(
        payload: dict[str, Any],
        allowed_tools: set[str],
        required_map: dict[str, list[str]],
    ) -> bool:
        ok, _ = MSAAgent._validate_calls_json_with_reason(
            payload, allowed_tools, required_map
        )
        return ok

    @staticmethod
    def _validate_calls_json_with_reason(
        payload: dict[str, Any],
        allowed_tools: set[str],
        required_map: dict[str, list[str]],
    ) -> tuple[bool, str]:
        calls = payload.get("calls")
        if not isinstance(calls, list) or not calls:
            return False, "calls_empty"
        for row in calls:
            if not isinstance(row, dict):
                return False, "call_not_dict"
            tool = str(row.get("tool_name", "")).strip()
            args = row.get("arguments")
            if tool not in allowed_tools:
                return False, f"unknown_tool:{tool or 'empty'}"
            if not isinstance(args, dict):
                return False, f"arguments_not_dict:{tool}"
            required = required_map.get(tool, [])
            for req in required:
                if req and req not in args:
                    return False, f"missing_required:{tool}.{req}"
        return True, "ok"

    @staticmethod
    def _validate_r1_indices_with_reason(
        payload: dict[str, Any],
        sizes: dict[str, int],
    ) -> tuple[bool, str]:
        for key in ("tools", "data_lake", "libraries", "know_how"):
            val = payload.get(key, [])
            if not isinstance(val, list):
                return False, f"{key}_not_list"
            max_size = int(sizes.get(key, 0))
            for i, raw in enumerate(val):
                try:
                    idx = int(raw)
                except Exception:
                    return False, f"{key}[{i}]_not_int"
                if idx < 0 or idx >= max_size:
                    return False, f"{key}[{i}]_out_of_range_0_to_{max(0, max_size - 1)}"
        return True, "ok"

    def _render_code_from_calls(self, calls: list[dict[str, Any]]) -> str:
        lines = ["print('MSA Step Execution')"]
        for i, row in enumerate(calls, start=1):
            tool = str(row.get("tool_name", "")).strip()
            args = row.get("arguments", {})
            if not tool or not isinstance(args, dict):
                continue
            kwargs = []
            for k, v in args.items():
                kwargs.append(f"{k}={self._py_literal(v)}")
            call = f"{tool}({', '.join(kwargs)})" if kwargs else f"{tool}()"
            lines.append("try:")
            lines.append(f"    result_{i} = {call}")
            lines.append(f"    print('{tool} ok')")
            lines.append(f"    print(result_{i})")
            lines.append("except Exception as e:")
            lines.append(f"    print('{tool} failed:', e)")
        if len(lines) == 1:
            raise RuntimeError("No executable tool call generated from LLM call plan")
        return "\n".join(lines)

    @staticmethod
    def _py_literal(value: Any) -> str:
        if isinstance(value, str):
            return repr(value)
        if isinstance(value, bool):
            return "True" if value else "False"
        if value is None:
            return "None"
        if isinstance(value, (int, float)):
            return repr(value)
        if isinstance(value, list):
            return "[" + ", ".join(MSAAgent._py_literal(x) for x in value) + "]"
        if isinstance(value, dict):
            items = [
                f"{MSAAgent._py_literal(k)}: {MSAAgent._py_literal(v)}"
                for k, v in value.items()
            ]
            return "{" + ", ".join(items) + "}"
        return repr(str(value))

    @staticmethod
    def _guess_domains(query: str) -> list[str]:
        q = query.lower()
        hits: list[str] = []
        mapping = {
            "genome": "Genomics",
            "variant": "Genetics",
            "single-cell": "Cell Biology",
            "drug": "Pharmacology",
            "pathway": "Molecular Biology",
            "protein": "Biochemistry",
            "microbe": "Microbiology",
        }
        for token, domain in mapping.items():
            if token in q and domain not in hits:
                hits.append(domain)
        if "Common" not in hits:
            hits.append("Common")
        return hits[:3]
