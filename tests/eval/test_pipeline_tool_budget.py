from __future__ import annotations

from typing import Any

from biomni.eval.pipeline import EvaluationPipeline


class _StubBenchmark:
    def get_tasks(self):
        return ["gwas_variant_prioritization"]

    def get_instances(self, task_name: str, split: str):
        return []

    def evaluate_result(self, task_name: str, instance: dict[str, Any], prediction: Any):
        return 0.0


class _StubLogger:
    def log_config(self, config):
        pass

    def log_result(self, result):
        pass

    def log_metrics(self, metrics):
        pass

    def finish(self):
        pass


class _DummyAgent:
    def __init__(self):
        self.received_tool_call_limit = None
        self.received_tool_call_count = None

    def go(self, prompt: str):
        self.received_tool_call_limit = getattr(self, "_task_tool_call_limit", None)
        self.received_tool_call_count = getattr(self, "_task_tool_call_count", None)
        return ["ok"], "ok"


def test_pipeline_configures_task_level_budget_for_gwas_variant():
    benchmark = _StubBenchmark()
    pipeline = EvaluationPipeline(benchmark, lambda: None, _StubLogger())
    pipeline.gwas_variant_tool_call_limit = 12

    instance = {"instance_id": "1", "prompt": "some gwas prompt", "ground_truth": "rs1"}
    agent = _DummyAgent()
    result = pipeline._process_instance(agent, "gwas_variant_prioritization", instance)

    assert result["task_name"] == "gwas_variant_prioritization"
    assert result["metrics"]["normalized_prediction_len"] >= 0
    assert agent.received_tool_call_limit == 12
    assert agent.received_tool_call_count == 0


def test_pipeline_clears_task_tool_budget_for_non_gwas_tasks():
    benchmark = _StubBenchmark()
    pipeline = EvaluationPipeline(benchmark, lambda: None, _StubLogger())
    pipeline.gwas_variant_tool_call_limit = 12

    instance = {"instance_id": "2", "prompt": "some prompt", "ground_truth": "A"}
    agent = _DummyAgent()
    _ = pipeline._process_instance(agent, "patient_gene_detection", instance)

    assert agent.received_tool_call_limit is None
    assert agent.received_tool_call_count == 0
