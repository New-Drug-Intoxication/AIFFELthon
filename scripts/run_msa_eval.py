from __future__ import annotations

import argparse
import json
from statistics import mean
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from biomni_msa import MSAAgent
from biomni_msa.eval import BiomniEval1


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

    agent = MSAAgent(llm_model=args.llm_model or None)
    results: list[dict] = []
    for _, row in rows.iterrows():
        task_name = str(row["task_name"])
        task_instance_id = int(row["task_instance_id"])
        prompt = str(row["prompt"])
        run = agent.go(prompt, verbose=False, stream=False)
        final_answer = str(run.get("final_answer", ""))
        score = evaluator.evaluate(task_name, task_instance_id, final_answer)
        results.append(
            {
                "task_name": task_name,
                "task_instance_id": task_instance_id,
                "score": score,
                "final_answer": final_answer,
            }
        )

    report = {
        "count": len(results),
        "mean_score": mean([x["score"] for x in results]) if results else 0.0,
        "results": results,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
