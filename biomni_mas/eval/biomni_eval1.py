from __future__ import annotations

import ast
import json
import re
import sys
from typing import Any


DEFAULT_EVAL1_URI = "hf://datasets/biomni/Eval1/biomni_eval1_dataset.parquet"


def normalize_answer_for_task(task_name: str, user_answer: str) -> str:
    text = str(user_answer or "").strip()

    if task_name in {"crispr_delivery", "hle"} or task_name.startswith("lab_bench"):
        tagged = re.search(
            r"\[ANSWER\]\s*([A-Za-z])\s*\[/ANSWER\]", text, re.IGNORECASE
        )
        if tagged:
            return tagged.group(1).upper()
        letter = re.search(r"\b([A-Za-z])\b", text)
        return letter.group(1).upper() if letter else text.upper()

    if task_name.startswith("gwas_causal_gene") or task_name == "screen_gene_retrieval":
        return text.upper()

    if task_name == "gwas_variant_prioritization":
        return text

    if task_name in {"rare_disease_diagnosis", "patient_gene_detection"}:
        if not text:
            return text
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            try:
                payload = ast.literal_eval(text)
            except Exception:
                return text
        return json.dumps(payload, ensure_ascii=True, sort_keys=True)

    return text


class BiomniEval1:
    def __init__(self, dataset_path: str | None = None):
        pd = __import__("pandas")

        self.dataset_path = dataset_path or DEFAULT_EVAL1_URI
        if str(self.dataset_path).startswith("hf://"):
            try:
                __import__("huggingface_hub")
            except Exception as exc:
                raise RuntimeError(
                    "Eval1 requires huggingface_hub for hf:// dataset paths. "
                    f"python={sys.executable}, dataset_path={self.dataset_path}, import_error={exc}"
                ) from exc
        try:
            self.df = pd.read_parquet(self.dataset_path)
        except Exception as exc:
            msg = str(exc)
            if "Install huggingface_hub to access HfFileSystem" in msg:
                raise RuntimeError(
                    "Eval1 failed to read hf:// dataset because huggingface_hub is not "
                    "available in the running interpreter. "
                    f"python={sys.executable}, dataset_path={self.dataset_path}"
                ) from exc
            raise
        self.instance_map: dict[tuple[str, int], int] = {}
        for idx, row in self.df.iterrows():
            key = (str(row["task_name"]), int(row["task_instance_id"]))
            self.instance_map[key] = int(idx)

    def evaluate(
        self, task_name: str, task_instance_id: int, user_answer: str
    ) -> float:
        key = (task_name, int(task_instance_id))
        if key not in self.instance_map:
            raise ValueError(
                f"Instance not found: task={task_name}, task_instance_id={task_instance_id}"
            )
        row = self.df.iloc[self.instance_map[key]]
        ground_truth = row["answer"]
        normalized_answer = normalize_answer_for_task(task_name, user_answer)
        return float(self._compute_reward(task_name, normalized_answer, ground_truth))

    def get_instance(self, task_name: str, task_instance_id: int) -> dict[str, Any]:
        key = (task_name, int(task_instance_id))
        if key not in self.instance_map:
            raise ValueError(
                f"Instance not found: task={task_name}, task_instance_id={task_instance_id}"
            )
        row = self.df.iloc[self.instance_map[key]]
        return {
            "instance_id": int(row["instance_id"]),
            "task_instance_id": int(row["task_instance_id"]),
            "task_name": str(row["task_name"]),
            "split": str(row["split"]),
            "prompt": str(row["prompt"]),
            "answer": row["answer"],
        }

    def list_tasks(self) -> list[str]:
        return sorted(self.df["task_name"].astype(str).unique().tolist())

    def get_instances(
        self, task_name: str | None = None, split: str | None = None
    ) -> Any:
        df = self.df
        if task_name:
            df = df[df["task_name"] == task_name]
        if split:
            df = df[df["split"] == split]
        return df.copy()

    def _compute_reward(
        self, task_name: str, user_answer: str, ground_truth: Any
    ) -> float:
        gt = ground_truth
        if task_name == "crispr_delivery":
            return (
                1.0 if user_answer.strip().lower() == str(gt).strip().lower() else 0.0
            )
        if task_name.startswith("gwas_causal_gene"):
            return (
                1.0 if user_answer.strip().upper() == str(gt).strip().upper() else 0.0
            )
        if task_name == "gwas_variant_prioritization":
            return 1.0 if user_answer.strip() == str(gt).strip() else 0.0
        if task_name == "hle":
            return (
                1.0 if user_answer.strip().upper() == str(gt).strip().upper() else 0.0
            )
        if task_name.startswith("lab_bench"):
            return (
                1.0 if user_answer.strip().upper() == str(gt).strip().upper() else 0.0
            )
        if task_name == "rare_disease_diagnosis":
            try:
                user_dict = (
                    json.loads(user_answer)
                    if isinstance(user_answer, str)
                    else user_answer
                )
                gt_dict = json.loads(gt) if isinstance(gt, str) else gt
                return (
                    1.0 if user_dict.get("OMIM_ID") == gt_dict.get("OMIM_ID") else 0.0
                )
            except Exception:
                return 0.0
        if task_name == "screen_gene_retrieval":
            return (
                1.0 if user_answer.strip().upper() == str(gt).strip().upper() else 0.0
            )
        if task_name == "patient_gene_detection":
            try:
                user_dict = (
                    json.loads(user_answer)
                    if isinstance(user_answer, str)
                    else user_answer
                )
                predicted = user_dict.get("causal_gene", [])
                if not isinstance(predicted, list):
                    predicted = [predicted]
                gt_str = str(gt)
                true_genes = (
                    [x.strip() for x in gt_str.split(",")]
                    if "," in gt_str
                    else [gt_str]
                )
                return 1.0 if predicted and (set(predicted) & set(true_genes)) else 0.0
            except Exception:
                return 0.0
        raise ValueError(f"Unknown task: {task_name}")
