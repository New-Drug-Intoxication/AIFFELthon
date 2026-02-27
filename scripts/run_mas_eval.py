from __future__ import annotations

import argparse
import json
from statistics import mean
import math
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from biomni_mas import MASAgent
from biomni_mas.eval import BiomniEval1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="", help="Optional local parquet path")
    parser.add_argument("--task", default="", help="Optional task filter")
    parser.add_argument("--split", default="val", help="Split filter (train/val)")
    parser.add_argument("--limit", type=int, default=5, help="Maximum instances to run")
    parser.add_argument("--llm-model", default="", help="Override LLM model name")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List selected instances without running agent",
    )
    args = parser.parse_args()

    try:
        evaluator = BiomniEval1(dataset_path=args.dataset or None)
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing optional dependency for eval runner. Install pandas (and parquet engine) first."
        ) from exc
    instances = evaluator.get_instances(
        task_name=args.task or None, split=args.split or None
    )
    if len(instances) == 0:
        raise SystemExit("No instances found for given filters")

    rows = instances.head(max(1, args.limit))
    if args.dry_run:
        preview = rows[["task_name", "task_instance_id", "split"]].to_dict(
            orient="records"
        )
        print(json.dumps({"selected": preview, "count": len(preview)}, indent=2))
        return

    agent = MASAgent(llm_model=args.llm_model or None)
    results: list[dict[str, Any]] = []
    latency_values: list[float] = []
    retry_values: list[int] = []
    revision_values: list[int] = []
    reset_values: list[int] = []
    for _, row in rows.iterrows():
        task_name = str(row["task_name"])
        task_instance_id = int(row["task_instance_id"])
        prompt = str(row["prompt"])
        run = agent.go(prompt, verbose=False, stream=False)
        final_answer = str(run.get("final_answer", ""))
        score = evaluator.evaluate(task_name, task_instance_id, final_answer)
        query_to_final_ms = float(run.get("query_to_final_ms", 0) or 0)
        retry_count = int(run.get("retry_count", 0) or 0)
        plan_revision_count = int(run.get("plan_revision_count", 0) or 0)
        full_reset_count = int(run.get("full_reset_count", 0) or 0)
        latency_values.append(query_to_final_ms)
        retry_values.append(retry_count)
        revision_values.append(plan_revision_count)
        reset_values.append(full_reset_count)
        results.append(
            {
                "task_name": task_name,
                "task_instance_id": task_instance_id,
                "score": score,
                "final_answer": final_answer,
                "query_to_final_ms": query_to_final_ms,
                "retry_count": retry_count,
                "plan_revision_count": plan_revision_count,
                "full_reset_count": full_reset_count,
                "step_latency_summary": run.get("step_latency_summary", {}),
            }
        )

    latency_sorted = sorted(latency_values)
    latency_p95 = 0.0
    if latency_sorted:
        idx = max(0, int(math.ceil(len(latency_sorted) * 0.95) - 1))
        latency_p95 = float(latency_sorted[idx])
    report = {
        "count": len(results),
        "mean_score": mean([x["score"] for x in results]) if results else 0.0,
        "query_to_final_ms_mean": mean(latency_values) if latency_values else 0.0,
        "query_to_final_ms_p95": latency_p95,
        "retry_count_mean": mean(retry_values) if retry_values else 0.0,
        "plan_revision_count_mean": mean(revision_values) if revision_values else 0.0,
        "full_reset_count_mean": mean(reset_values) if reset_values else 0.0,
        "results": results,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
