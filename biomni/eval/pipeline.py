import re
import time
import traceback
from typing import Any, Dict, List, Optional

from tqdm import tqdm

from biomni.eval.benchmark import Benchmark
from biomni.eval.logger import BaseLogger
from biomni.tool.support_tools import reset_python_repl_namespace


def _flatten_content_blocks(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                    continue
                content = item.get("content")
                if isinstance(content, str):
                    parts.append(content)
                    continue
            parts.append(str(item))
        return "\n".join(parts)

    return str(value)


def _extract_solution_text(text: str) -> str:
    match = re.search(r"<solution>(.*?)</solution>", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return text
    return match.group(1).strip()


def _extract_answer_tag(text: str) -> str | None:
    match = re.search(r"\[ANSWER\]\s*([A-Za-z])\s*\[/ANSWER\]", text, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).upper()


def _extract_candidate_variants(prompt: str) -> list[str]:
    found = re.findall(r"\brs\d+\b", prompt, flags=re.IGNORECASE)
    dedup: list[str] = []
    seen: set[str] = set()
    for item in found:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)
    return dedup


def _extract_candidate_genes(prompt: str) -> list[str]:
    candidates: list[str] = []

    for value in re.findall(r"\{([^{}]+)\}", prompt):
        token = value.strip().strip("'\"")
        if token:
            candidates.append(token)

    line_matches = re.findall(r"(?im)^(?:Candidate genes|Genes in locus):\s*(.+)$", prompt)
    for line in line_matches:
        for raw in line.split(","):
            token = raw.strip().strip("'\"").strip("{}")
            if token:
                candidates.append(token)

    dedup: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        key = item.upper()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)
    return dedup


def _contains_token(text: str, token: str) -> bool:
    pattern = rf"(?<![A-Za-z0-9_.-]){re.escape(token)}(?![A-Za-z0-9_.-])"
    if re.search(pattern, text, flags=re.IGNORECASE):
        return True
    return token.lower() in text.lower()


def _canonicalize_letter_answer(task_name: str, text: str) -> str:
    answer_tag = _extract_answer_tag(text)
    if answer_tag:
        return answer_tag

    stripped = text.strip()
    if len(stripped) == 1 and stripped.isalpha():
        return stripped.upper()

    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    for line in reversed(lines):
        if len(line) <= 6:
            match = re.fullmatch(r"[\[\(\{]?\s*([A-Za-z])\s*[\]\)\}]?", line)
            if match:
                return match.group(1).upper()

    pattern = r"\b([A-Fa-f])\b" if task_name == "crispr_delivery" else r"\b([A-Za-z])\b"
    match = re.search(pattern, stripped)
    if match:
        return match.group(1).upper()

    return stripped


def _canonicalize_variant_answer(text: str, prompt: str) -> str:
    prompt_candidates = _extract_candidate_variants(prompt)
    prompt_map = {item.lower(): item for item in prompt_candidates}
    text_candidates = re.findall(r"\brs\d+\b", text, flags=re.IGNORECASE)

    for item in text_candidates:
        if item.lower() in prompt_map:
            return prompt_map[item.lower()]

    if prompt_candidates:
        for candidate in prompt_candidates:
            if re.search(rf"\b{re.escape(candidate)}\b", text, flags=re.IGNORECASE):
                return candidate

    if text_candidates:
        return text_candidates[0]

    return text.strip()


def _canonicalize_gene_answer(text: str, prompt: str) -> str:
    candidates = _extract_candidate_genes(prompt)
    if not candidates:
        return text.strip()

    for candidate in candidates:
        if _contains_token(text, candidate):
            return candidate

    return text.strip()


def normalize_prediction_for_scoring(task_name: str, prompt: str, prediction: Any) -> str:
    text = _flatten_content_blocks(prediction).strip()
    if not text:
        return ""

    text = _extract_solution_text(text).strip()
    answer_tag = _extract_answer_tag(text)
    if answer_tag:
        text = answer_tag

    if task_name in {"crispr_delivery", "hle"} or task_name.startswith("lab_bench"):
        return _canonicalize_letter_answer(task_name, text)

    if task_name == "gwas_variant_prioritization":
        return _canonicalize_variant_answer(text, prompt)

    if task_name.startswith("gwas_causal_gene") or task_name == "screen_gene_retrieval":
        return _canonicalize_gene_answer(text, prompt)

    return text.strip()


def _count_tool_calls_from_trajectory(trajectory: list[Any]) -> int:
    """Estimate tool calls from serialized trajectory entries."""
    count = 0
    for step in trajectory:
        text = ""
        if isinstance(step, dict):
            text = str(step.get("content", ""))
        else:
            text = str(step)
        if not text:
            continue

        execute_hits = len(re.findall(r"<execute>", text, flags=re.IGNORECASE))
        if execute_hits:
            count += execute_hits
            continue

        if "Tool:" in text or "Invoking:" in text or "tool call" in text.lower():
            count += 1
    return count


def _count_tool_calls_from_agent_state(agent: Any) -> int:
    """Fallback tool-call counting using the agent's final conversation state."""
    state = getattr(agent, "_conversation_state", None)
    if not isinstance(state, dict):
        return 0

    messages = state.get("messages", [])
    if not isinstance(messages, list):
        return 0

    count = 0
    for message in messages:
        content = getattr(message, "content", message)
        text = str(content)
        observation_hits = len(re.findall(r"<observation>", text, flags=re.IGNORECASE))
        if observation_hits:
            # One observation is emitted per execute call.
            count += observation_hits
            continue

        # Fallback for cases where observation messages are missing.
        count += len(re.findall(r"<execute>", text, flags=re.IGNORECASE))
    return count


class EvaluationPipeline:
    def __init__(
        self,
        benchmark: Benchmark,
        agent_factory,
        logger: BaseLogger,
        max_instances: Optional[int] = None,
        agent_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            benchmark: The benchmark adapter to use.
            agent_factory: A function/callable that returns a fresh agent instance.
            logger: The logger to use.
            max_instances: Max instances per task to evaluate (for debugging/testing).
            agent_config: Configuration dictionary for the agent.
        """
        self.benchmark = benchmark
        self.agent_factory = agent_factory
        self.logger = logger
        self.max_instances = max_instances
        self.agent_config = agent_config or {}

    def run(self, tasks: Optional[List[str]] = None, split: str = "val"):
        """
        Run the evaluation pipeline.

        Args:
            tasks: List of task names to evaluate. If None, runs all tasks.
            split: Dataset split to use (e.g., 'val', 'test').
        """
        available_tasks = self.benchmark.get_tasks()

        if tasks is None:
            tasks = available_tasks
        else:
            tasks = [t for t in tasks if t in available_tasks]
            if not tasks:
                print("No valid tasks found to evaluate.")
                return

        config = {
            "benchmark_id": self.benchmark.id,
            "tasks": tasks,
            "split": split,
            "max_instances": self.max_instances,
            "timestamp": time.time(),
        }
        self.logger.log_config(config)

        total_instances = 0
        for task_name in tasks:
            task_instances = len(self.benchmark.get_instances(task_name, split))
            if self.max_instances is not None:
                total_instances += min(task_instances, self.max_instances)
            else:
                total_instances += task_instances

        print(f"Starting evaluation on {len(tasks)} tasks: {tasks}")
        print(f"Total instances to evaluate: {total_instances}")

        with tqdm(total=total_instances, desc="Overall Progress", unit="inst") as pbar:
            for task_name in tasks:
                self._evaluate_task(task_name, split, pbar)

        self.logger.finish()

    def _evaluate_task(self, task_name: str, split: str, pbar: tqdm):
        pbar.write(f"\n=== Evaluating Task: {task_name} ===")
        instances = self.benchmark.get_instances(task_name, split)

        if self.max_instances is not None:
            instances = instances[: self.max_instances]

        success_count = 0
        total_score = 0.0

        for i, instance in enumerate(instances):
            pbar.write(f"[{task_name}] Processing instance {i + 1}/{len(instances)} (ID: {instance['instance_id']})")

            # Create a fresh agent for each instance to avoid state leakage.
            agent = self.agent_factory()

            # Reset shared Python REPL namespace so one instance does not leak to another.
            reset_python_repl_namespace(preload_defaults=True)

            if self.agent_config:
                agent.configure(**self.agent_config)

            result_data = self._process_instance(agent, task_name, instance)
            self.logger.log_result(result_data)

            if result_data["success"]:
                success_count += 1
            total_score += result_data["score"]
            pbar.update(1)

        if instances:
            task_metrics = {
                f"{task_name}/accuracy": success_count / len(instances),
                f"{task_name}/avg_score": total_score / len(instances),
                f"{task_name}/count": len(instances),
            }
            self.logger.log_metrics(task_metrics)
            pbar.write(f"Task {task_name} finished. Accuracy: {task_metrics[f'{task_name}/accuracy']:.2f}")

    def _process_instance(self, agent: Any, task_name: str, instance: Dict[str, Any]) -> Dict[str, Any]:
        prompt = instance["prompt"]
        start_time = time.time()

        raw_response: Any = None
        prediction = ""
        trajectory: list[str] = []
        error = None
        score = 0.0

        try:
            log, raw_response = agent.go(prompt)
            trajectory = log
            prediction = normalize_prediction_for_scoring(task_name=task_name, prompt=prompt, prediction=raw_response)

            try:
                score = self.benchmark.evaluate_result(task_name, instance, prediction)
            except Exception as eval_error:
                preview = prediction[:240].replace("\n", "\\n")
                print(f"Evaluation error for {task_name}/{instance['instance_id']}: {eval_error}")
                print(
                    "Debug:"
                    f" raw_response_type={type(raw_response).__name__},"
                    f" normalized_prediction_len={len(prediction)},"
                    f" normalized_prediction_preview={preview}"
                )
                traceback.print_exc()
                error = str(eval_error)
                score = 0.0

        except Exception as exc:
            error = str(exc)
            traceback.print_exc()
            prediction = "ERROR"
            score = 0.0

        end_time = time.time()
        success = score == 1.0

        tool_calls = _count_tool_calls_from_trajectory(trajectory)
        if tool_calls == 0:
            tool_calls = _count_tool_calls_from_agent_state(agent)

        return {
            "task_name": task_name,
            "instance_id": instance["instance_id"],
            "prompt": prompt,
            "prediction": prediction,
            "ground_truth": instance["ground_truth"],
            "score": score,
            "success": success,
            "error": error,
            "trajectory": trajectory,
            "metrics": {
                "latency": end_time - start_time,
                "tool_calls": tool_calls,
                "raw_response_type": type(raw_response).__name__,
                "normalized_prediction_len": len(prediction),
            },
        }
