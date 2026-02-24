#!/usr/bin/env python3
import argparse
import sqlite3
import os
import sys
import re
import difflib
from pathlib import Path
from typing import Callable

# Ensure the biomni package is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from biomni.agent import A1
from biomni.config import default_config
from biomni.eval.benchmark import BixBenchAdapter, BiomniEval1Adapter, LabBenchAdapter
from biomni.eval.logger import MultiLogger, SQLiteLogger, WandBLogger
from biomni.eval.pipeline import EvaluationPipeline


DEFAULT_DB_PATH = str(Path("data") / "biomni_eval.db")


def _resolve_db_path(cli_db_path: str | None) -> str:
    return cli_db_path or DEFAULT_DB_PATH


def _load_completed_instance_ids(db_path: str, benchmark_id: str, tasks: list[str] | None, experiment_id: int | None = None) -> dict[str, set[str]]:
    """Load already completed instance IDs from a previous SQLite experiment.

    Returns a mapping of task_name -> set(instance_id).
    """
    if not os.path.exists(db_path):
        return {}

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        if experiment_id is None:
            query = "SELECT id FROM experiments WHERE benchmark_id = ? ORDER BY id DESC LIMIT 1"
            cursor.execute(query, (benchmark_id,))
            row = cursor.fetchone()
            if row is None:
                return {}
            experiment_id = int(row[0])

        if tasks:
            placeholders = ",".join("?" for _ in tasks)
            cursor.execute(
                f"SELECT task_name, instance_id FROM results WHERE experiment_id = ? AND task_name IN ({placeholders})",
                [experiment_id] + tasks,
            )
        else:
            cursor.execute(
                "SELECT task_name, instance_id FROM results WHERE experiment_id = ?",
                (experiment_id,),
            )

        completed: dict[str, set[str]] = {}
        for task_name, instance_id in cursor.fetchall():
            completed.setdefault(task_name, set()).add(str(instance_id))

        return completed

def get_benchmark(benchmark_id: str):
    if benchmark_id == "biomni_eval1":
        return BiomniEval1Adapter()
    elif benchmark_id == "lab_bench":
        return LabBenchAdapter(local_root=default_config.path)
    elif benchmark_id == "bixbench":
        return BixBenchAdapter()
    else:
        raise ValueError(f"Unknown benchmark: {benchmark_id}")


def _normalize_task_name(task_name: str) -> str:
    """Normalize user-provided task names."""
    return re.sub(r"_+", "_", task_name.strip().replace("-", "_").lower())


def _normalize_tasks(task_names: list[str] | None, valid_tasks: list[str] | None = None) -> tuple[list[str] | None, list[str]]:
    if task_names is None:
        return None, []

    normalized = [_normalize_task_name(task) for task in task_names]
    if valid_tasks is None:
        return normalized, []

    valid = set(valid_tasks)
    kept: list[str] = []
    unknown: list[str] = []
    for original, normalized_task in zip(task_names, normalized):
        if normalized_task in valid:
            if normalized_task not in kept:
                kept.append(normalized_task)
        else:
            unknown.append(original)

    return kept, unknown


def _print_task_help(requested: list[str], unknown: list[str], valid_tasks: list[str], benchmark_id: str) -> None:
    if not unknown:
        return
    print(f"Warning: invalid task name(s) for benchmark '{benchmark_id}':")
    for name in unknown:
        normalized = _normalize_task_name(name)
        suggestion = difflib.get_close_matches(normalized, valid_tasks, n=1, cutoff=0.5)
        suggestion_text = f" | suggestion: {suggestion[0]}" if suggestion else ""
        print(f"  - {name} -> {normalized}{suggestion_text}")
    print("Valid tasks:")
    for task in valid_tasks:
        print(f"  - {task}")


def _normalize_path_for_a1(path: str) -> str:
    # A1 appends "biomni_data" internally; if caller already provides ".../biomni_data",
    # pass the parent directory to avoid ending up with ".../biomni_data/biomni_data".
    normalized = os.path.normpath(path)
    if os.path.basename(normalized) == "biomni_data":
        parent = os.path.dirname(normalized)
        return parent if parent else "."
    return path


def make_agent_factory(llm: str, path: str, timeout_seconds: int | None = None) -> Callable[[], A1]:
    a1_path = _normalize_path_for_a1(path)

    def factory():
        return A1(path=a1_path, llm=llm, timeout_seconds=timeout_seconds)

    return factory


def main():
    parser = argparse.ArgumentParser(description="Biomni Evaluation Runner")
    parser.add_argument(
        "--benchmark",
        type=str,
        default="biomni_eval1",
        choices=["biomni_eval1", "lab_bench", "bixbench"],
        help="Benchmark to run",
    )
    parser.add_argument("--tasks", type=str, nargs="+", help="Specific tasks to run (default: all)")
    parser.add_argument("--split", type=str, default="val", help="Dataset split (train/val/test)")
    parser.add_argument("--llm", type=str, default=None, help="LLM model name (overrides default_config)")
    parser.add_argument("--path", type=str, default=None, help="Data path (overrides default_config)")
    parser.add_argument("--wandb-project", type=str, default="biomni-eval", help="WandB project name")
    parser.add_argument("--wandb-entity", type=str, default=None, help="WandB entity/username")
    parser.add_argument("--wandb-name", type=str, default=None, help="WandB run name")
    parser.add_argument("--no-wandb", action="store_true", help="Disable WandB logging")
    parser.add_argument(
        "--db-path",
        type=str,
        default=DEFAULT_DB_PATH,
        help="SQLite database path (default: data/biomni_eval.db)",
    )
    parser.add_argument("--max-instances", type=int, default=None, help="Max instances per task (for testing)")
    parser.add_argument(
        "--agent-timeout-seconds",
        type=int,
        default=120,
        help="Timeout for whole A1 execution per instance in seconds (default: 120, recommended 120~180).",
    )

    # A1 Configuration Arguments
    parser.add_argument("--self-critic", action="store_true", help="Enable A1 self-critic mode")
    parser.add_argument(
        "--test-time-scale-round",
        type=int,
        default=0,
        help="Number of extra self-critic rounds for A1 (default: 0)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip instances already logged in a prior sqlite experiment",
    )
    parser.add_argument(
        "--resume-experiment-id",
        type=int,
        default=None,
        help="Experiment id to resume from in the sqlite DB (default: latest for selected benchmark)",
    )

    args = parser.parse_args()

    # Update default config if arguments provided
    if args.llm:
        default_config.llm = args.llm
    if args.path:
        default_config.path = args.path
    if args.agent_timeout_seconds is not None:
        default_config.timeout_seconds = args.agent_timeout_seconds

    loggers = []

    db_path = _resolve_db_path(args.db_path)
    sqlite_logger = SQLiteLogger(
        db_path=db_path, experiment_name=args.wandb_name or f"{args.benchmark}_{args.llm or 'default'}"
    )
    loggers.append(sqlite_logger)

    if not args.no_wandb:
        try:
            wandb_logger = WandBLogger(
                project=args.wandb_project, entity=args.wandb_entity, name=args.wandb_name, config=vars(args)
            )
            loggers.append(wandb_logger)
        except ImportError:
            print("WandB not installed or failed to initialize. Skipping WandB logging.")
        except Exception as e:
            print(f"WandB initialization failed: {e}. Skipping.")

    combined_logger = MultiLogger(loggers)

    try:
        benchmark = get_benchmark(args.benchmark)
    except Exception as e:
        print(f"Error loading benchmark: {e}")
        return

    normalized_tasks, unknown_tasks = _normalize_tasks(args.tasks, benchmark.get_tasks())
    _print_task_help(args.tasks or [], unknown_tasks, benchmark.get_tasks(), args.benchmark)

    completed_instances: dict[str, set[str]] = {}
    if args.resume:
        completed_instances = _load_completed_instance_ids(
            db_path=db_path,
            benchmark_id=args.benchmark,
            tasks=normalized_tasks,
            experiment_id=args.resume_experiment_id,
        )
        if completed_instances:
            print(f"Resuming from DB: skipping {sum(len(v) for v in completed_instances.values())} instances")
        else:
            print("Resume requested but no completed rows found; running full remaining set.")

    agent_factory = make_agent_factory(
        llm=default_config.llm,
        path=default_config.path,
        timeout_seconds=default_config.timeout_seconds,
    )

    agent_config = {
        "self_critic": args.self_critic,
        "test_time_scale_round": args.test_time_scale_round,
        "agent_timeout_seconds": args.agent_timeout_seconds,
    }

    pipeline = EvaluationPipeline(
        benchmark=benchmark,
        agent_factory=agent_factory,
        logger=combined_logger,
        max_instances=args.max_instances,
        agent_config=agent_config,
        completed_instance_ids=completed_instances,
    )

    pipeline.run(tasks=normalized_tasks, split=args.split)


if __name__ == "__main__":
    main()
