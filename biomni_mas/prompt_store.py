from __future__ import annotations

from pathlib import Path


class PromptStore:
    def __init__(self, prompt_root: Path):
        self.prompt_root = prompt_root
        runtime = prompt_root / "runtime"
        self.router_text = (runtime / "router.system.txt").read_text(encoding="utf-8")
        self.domain_map = {
            "1 Round - Tool Retriever": (
                runtime / "domain.plan_r1.system.txt"
            ).read_text(encoding="utf-8"),
            "2 Round - Planner": (runtime / "domain.plan_r2.system.txt").read_text(
                encoding="utf-8"
            ),
            "3 Round - Critique": (runtime / "domain.plan_r3.system.txt").read_text(
                encoding="utf-8"
            ),
            "1 Round - Write and run code": (
                runtime / "domain.exec_r1.system.txt"
            ).read_text(encoding="utf-8"),
            "2 Round - Verifier": (runtime / "domain.exec_r2.system.txt").read_text(
                encoding="utf-8"
            ),
        }
        self.orch_map = {
            "Orchestrator Module 1": (runtime / "orch.r21.system.txt").read_text(
                encoding="utf-8"
            ),
            "Orchestrator Module 2": (runtime / "orch.r31.system.txt").read_text(
                encoding="utf-8"
            ),
            "Orchestrator Module 3": (
                runtime / "orch.exec_manager.system.txt"
            ).read_text(encoding="utf-8"),
        }

    def router(self) -> str:
        return self.router_text

    def domain_round(self, marker: str, next_markers: list[str]) -> str:
        del next_markers
        if marker not in self.domain_map:
            raise ValueError(f"Unknown domain round marker: {marker}")
        return self.domain_map[marker]

    def orchestrator_module(self, marker: str, next_markers: list[str]) -> str:
        del next_markers
        if marker not in self.orch_map:
            raise ValueError(f"Unknown orchestrator module marker: {marker}")
        return self.orch_map[marker]
