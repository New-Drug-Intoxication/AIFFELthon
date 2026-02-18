from abc import ABC, abstractmethod
import json
from pathlib import Path
import ast
from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd

from biomni.eval.biomni_eval1 import BiomniEval1


class Benchmark(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @abstractmethod
    def get_tasks(self) -> List[str]:
        """Return a list of task names."""
        pass

    @abstractmethod
    def get_instances(self, task_name: str, split: str = "val") -> List[Dict[str, Any]]:
        """Return a list of instances for a given task."""
        pass

    @abstractmethod
    def evaluate_result(self, task_name: str, instance: Dict[str, Any], prediction: Any) -> float:
        """Evaluate a single result and return a score (0.0 to 1.0)."""
        pass


class BiomniEval1Adapter(Benchmark):
    def __init__(self):
        self.evaluator = BiomniEval1()
        self._id = "biomni_eval1"

    @property
    def id(self) -> str:
        return self._id

    def get_tasks(self) -> List[str]:
        return self.evaluator.list_tasks()

    def get_instances(self, task_name: str, split: str = "val") -> List[Dict[str, Any]]:
        # BiomniEval1 dataframe has columns: instance_id, task_instance_id, task_name, split, prompt, answer
        df = self.evaluator.get_instances_by_task(task_name, split)
        instances = []
        for _, row in df.iterrows():
            instances.append(
                {
                    "instance_id": row["instance_id"],  # Global ID
                    "task_instance_id": row["task_instance_id"],  # Task-local ID needed for evaluate()
                    "prompt": row["prompt"],
                    "ground_truth": row["answer"],
                    "task_name": row["task_name"],
                }
            )
        return instances

    def evaluate_result(self, task_name: str, instance: Dict[str, Any], prediction: Any) -> float:
        # BiomniEval1.evaluate takes (task_name, task_instance_id, user_answer)
        return self.evaluator.evaluate(task_name, instance["task_instance_id"], prediction)


# Placeholder for future benchmarks
class LabBenchAdapter(Benchmark):
    _CANARY_OPTION = "Insufficient information to answer the question."
    _PROMPT_TEMPLATE = """The following is a multiple choice question about biology.
Please answer by responding with the letter of the correct answer.

Question: {question}
Options:
{options}

You MUST include the letter of the correct answer within the following tags:
[ANSWER] and [/ANSWER]. For example, '[ANSWER]<answer>[/ANSWER]',
where <answer> is the correct letter. Always answer in exactly this format
of a single letter between the two tags, even if you are unsure.
We require this because we use automatic parsing.
            """

    _LOCAL_FILE_MAP = {
        "train": "train-00000-of-00001.parquet",
        "validation": "train-00000-of-00001_test.parquet",
        "val": "train-00000-of-00001_test.parquet",
        "test": "train-00000-of-00001_test.parquet",
    }

    _SUBSETS = ("CloningScenarios", "DbQA", "FigQA", "LitQA2", "ProtocolQA", "SeqQA", "SuppQA", "TableQA")

    def __init__(
        self,
        dataset_id: str = "futurehouse/lab-bench",
        local_root: str = "./data/biomni_data",
        subsets: list[str] | tuple[str, ...] | None = None,
        prefer_remote: bool = True,
    ):
        if subsets is None:
            subsets = self._SUBSETS

        if not subsets:
            raise ValueError("subsets must not be empty")

        self.dataset_id = dataset_id
        self.local_root = Path(local_root)
        self.prefer_remote = prefer_remote
        self._loaded_subsets: dict[tuple[str, str], pd.DataFrame] = {}
        self.subsets = self._normalize_subsets(subsets)
        self._rng = np.random.RandomState(42)

    @property
    def id(self) -> str:
        return "lab_bench"

    @classmethod
    def _normalize_subsets(cls, subsets: Iterable[str]) -> list[str]:
        normalized = []
        for subset in subsets:
            canonical = cls._normalize_subset_name(subset)
            if canonical in normalized:
                continue
            normalized.append(canonical)

        if not normalized:
            raise ValueError("subsets must include at least one supported lab-bench subset")

        return normalized

    @classmethod
    def _normalize_subset_name(cls, subset: str) -> str:
        key = "".join(ch for ch in (subset or "").strip().lower() if ch.isalnum())
        aliases = {
            "dbqa": "DbQA",
            "seqqa": "SeqQA",
            "cloningscenarios": "CloningScenarios",
            "cloningscenario": "CloningScenarios",
            "cloningscenari": "CloningScenarios",
            "figqa": "FigQA",
            "litqa2": "LitQA2",
            "litqa": "LitQA2",
            "protocolqa": "ProtocolQA",
            "suppqa": "SuppQA",
            "tableqa": "TableQA",
        }
        if key in aliases:
            return aliases[key]
        raise ValueError(f"Unsupported lab bench subset: {subset}")

    @classmethod
    def _task_from_subset(cls, subset: str) -> str:
        key = "".join(ch for ch in subset if ch.isalnum()).lower()
        suffix = {
            "cloningscenarios": "cloningscenarios",
            "dbqa": "dbqa",
            "seqqa": "seqqa",
            "figqa": "figqa",
            "litqa2": "litqa2",
            "protocolqa": "protocolqa",
            "suppqa": "suppqa",
            "tableqa": "tableqa",
        }
        if key in suffix:
            return f"lab_bench_{suffix[key]}"
        raise ValueError(f"Unsupported lab bench subset: {subset}")

    @classmethod
    def _subset_from_task(cls, task_name: str) -> str:
        if not task_name.startswith("lab_bench_"):
            raise ValueError(f"Invalid lab-bench task name: {task_name}")

        task_suffix = "".join(
            ch for ch in task_name[len("lab_bench_") :].strip().lower() if ch.isalnum()
        )
        aliases = {
            "dbqa": "DbQA",
            "seqqa": "SeqQA",
            "cloningscenarios": "CloningScenarios",
            "figqa": "FigQA",
            "litqa2": "LitQA2",
            "litqa": "LitQA2",
            "protocolqa": "ProtocolQA",
            "suppqa": "SuppQA",
            "tableqa": "TableQA",
        }
        if task_suffix in aliases:
            return aliases[task_suffix]
        raise ValueError(f"Unsupported lab-bench task name: {task_name}")

    @staticmethod
    def _coerce_content_blocks(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, str):
            return value

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

    @classmethod
    def _coerce_sequence(cls, value: Any) -> list[str]:
        if value is None:
            return []

        if isinstance(value, float) and pd.isna(value):
            return []

        if isinstance(value, list):
            return [str(item) for item in value]

        if isinstance(value, tuple | np.ndarray):
            return [str(item) for item in list(value)]

        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []

            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except Exception:
                pass

            try:
                parsed = ast.literal_eval(stripped)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except Exception:
                pass

            return [stripped]

        return [str(value)]

    @staticmethod
    def _normalize_split(split: str) -> str:
        if split is None:
            split = "val"
        split = split.lower().strip()
        if split not in {"train", "val", "validation", "test", "dev"}:
            raise ValueError(f"Unsupported split: {split}")
        return split

    @classmethod
    def _local_file_name(cls, split: str) -> str:
        return cls._LOCAL_FILE_MAP.get(split, "train-00000-of-00001_test.parquet")

    @classmethod
    def _remote_split_name(cls, split: str) -> str:
        # The remote HF split for lab-bench is commonly exposed as train.
        return "train"

    def _load_remote_split(self, subset: str, split: str) -> pd.DataFrame:
        if not self.prefer_remote:
            raise RuntimeError("Remote loading disabled by adapter configuration")

        try:
            from datasets import load_dataset
        except Exception as exc:
            raise RuntimeError(f"Failed to import datasets library: {exc}")

        try:
            remote_split = self._remote_split_name(split)
            dataset = load_dataset(self.dataset_id, subset, split=remote_split)
            if hasattr(dataset, "to_pandas"):
                return dataset.to_pandas()

            # Fallback for odd dataset object structures.
            return pd.DataFrame(dataset)
        except Exception as exc:
            raise RuntimeError(f"Failed to load HF subset={subset} split={split}: {exc}")

    def _local_file_path(self, subset: str, split: str) -> Path:
        split_file = self._local_file_name(split)
        return self.local_root / "benchmark" / subset / split_file

    def _load_local_split(self, subset: str, split: str) -> pd.DataFrame:
        file_path = self._local_file_path(subset, split)
        if not file_path.exists():
            raise FileNotFoundError(f"Local lab-bench file not found: {file_path}")

        return pd.read_parquet(file_path)

    def _load_split(self, subset: str, split: str) -> pd.DataFrame:
        normalized_split = self._normalize_split(split)
        cache_key = (subset, normalized_split)
        if cache_key in self._loaded_subsets:
            return self._loaded_subsets[cache_key]

        # Try remote first, with graceful fallback to local files.
        df: pd.DataFrame
        if self.prefer_remote:
            try:
                df = self._load_remote_split(subset, normalized_split)
            except Exception:
                df = self._load_local_split(subset, normalized_split)
        else:
            df = self._load_local_split(subset, normalized_split)

        self._loaded_subsets[cache_key] = df
        return df

    def get_tasks(self) -> List[str]:
        tasks: list[str] = []
        for subset in self.subsets:
            tasks.append(self._task_from_subset(subset))
        return tasks

    def get_instances(self, task_name: str, split: str = "val") -> List[Dict[str, Any]]:
        subset = self._subset_from_task(task_name)
        df = self._load_split(subset, split)

        instances: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            question = str(row["question"])
            ideal = str(row["ideal"])
            canary = str(row.get("canary", self._CANARY_OPTION))
            distractors = self._coerce_sequence(row["distractors"])

            options = distractors + [ideal] + [canary]
            self._rng.shuffle(options)

            options_arr = np.array(options)
            if ideal not in options_arr:
                raise ValueError(f"Ideal answer not found in options for instance {row['id']}")

            answer_idx = int(np.where(options_arr == ideal)[0][0])
            letter_answer = chr(ord("A") + answer_idx)

            prompt = self._PROMPT_TEMPLATE.format(
                question=question,
                options="\n".join([chr(ord("A") + i) + "." + item for i, item in enumerate(options_arr)]),
            )

            instance: Dict[str, Any] = {
                "instance_id": str(row["id"]),
                "prompt": prompt,
                "ground_truth": letter_answer,
                "task_name": task_name,
            }

            if "subtask" in df.columns:
                instance["subtask"] = row["subtask"]

            instances.append(instance)

        return instances

    def evaluate_result(self, task_name: str, instance: Dict[str, Any], prediction: Any) -> float:
        # Ensure task-name is recognized for early failure rather than silent pass-through.
        self._subset_from_task(task_name)

        predicted = self._coerce_content_blocks(prediction).strip().upper()
        truth = self._coerce_content_blocks(instance.get("ground_truth")).strip().upper()

        if not truth:
            return 0.0

        return 1.0 if predicted == truth else 0.0


class BixBenchAdapter(Benchmark):
    @property
    def id(self) -> str:
        return "bixbench"

    def get_tasks(self) -> List[str]:
        raise NotImplementedError("BixBench not yet implemented")

    def get_instances(self, task_name: str, split: str = "val") -> List[Dict[str, Any]]:
        raise NotImplementedError("BixBench not yet implemented")

    def evaluate_result(self, task_name: str, instance: Dict[str, Any], prediction: Any) -> float:
        raise NotImplementedError("BixBench not yet implemented")
