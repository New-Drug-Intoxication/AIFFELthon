import pandas as pd
from pathlib import Path

import pytest

from biomni.eval.benchmark import LabBenchAdapter


def _write_rows(root, subset: str, split: str, rows: list[dict]):
    file_name = {
        "train": "train-00000-of-00001.parquet",
        "val": "train-00000-of-00001_test.parquet",
        "validation": "train-00000-of-00001_test.parquet",
        "test": "train-00000-of-00001_test.parquet",
    }[split]

    path = root / "benchmark" / subset / file_name
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def test_labbench_get_tasks_from_local(tmp_path):
    _write_rows(
        tmp_path,
        "DbQA",
        "test",
        [
            {
                "id": "d1",
                "question": "Which gene is associated with A?",
                "ideal": "GENE_A",
                "distractors": ["GENE_X", "GENE_Y"],
                "canary": "Insufficient information to answer the question.",
                "subtask": "taskA",
            }
        ],
    )
    _write_rows(
        tmp_path,
        "SeqQA",
        "test",
        [
            {
                "id": "s1",
                "question": "Which residue at position 1?",
                "ideal": "A",
                "distractors": ["G", "V"],
                "canary": "Insufficient information to answer the question.",
                "subtask": "taskB",
            }
        ],
    )

    adapter = LabBenchAdapter(local_root=str(tmp_path), prefer_remote=False, subsets=("DbQA", "SeqQA"))
    assert adapter.get_tasks() == ["lab_bench_dbqa", "lab_bench_seqqa"]


def test_labbench_default_get_tasks_includes_all_subsets():
    adapter = LabBenchAdapter(local_root=str(Path("/tmp")), prefer_remote=False)
    assert adapter.get_tasks() == [
        "lab_bench_cloningscenarios",
        "lab_bench_dbqa",
        "lab_bench_figqa",
        "lab_bench_litqa2",
        "lab_bench_protocolqa",
        "lab_bench_seqqa",
        "lab_bench_suppqa",
        "lab_bench_tableqa",
    ]


def test_labbench_get_instances_builds_prompt_and_letter_gt(tmp_path):
    _write_rows(
        tmp_path,
        "DbQA",
        "val",
        [
            {
                "id": "d2",
                "question": "Which gene is most likely contained in the set?",
                "ideal": "GENE_B",
                "distractors": ["GENE_A", "GENE_C"],
                "canary": "Insufficient information to answer the question.",
                "subtask": "subset_x",
            }
        ],
    )

    adapter = LabBenchAdapter(local_root=str(tmp_path), prefer_remote=False)
    instances = adapter.get_instances("lab_bench_dbqa", split="val")

    assert len(instances) == 1
    instance = instances[0]

    prompt = instance["prompt"]
    assert "The following is a multiple choice question about biology." in prompt
    assert "[ANSWER]" in prompt
    assert "[/ANSWER]" in prompt
    assert instance["ground_truth"] in {"A", "B", "C", "D"}
    assert instance["subtask"] == "subset_x"


def test_labbench_evaluate_result_case_insensitive(tmp_path):
    adapter = LabBenchAdapter(local_root=str(tmp_path), prefer_remote=False)
    instance = {"ground_truth": "c"}

    assert adapter.evaluate_result("lab_bench_dbqa", instance, "C") == 1.0
    assert adapter.evaluate_result("lab_bench_dbqa", instance, " c ") == 1.0
    assert adapter.evaluate_result("lab_bench_dbqa", instance, [{"text": "c"}]) == 1.0
    assert adapter.evaluate_result("lab_bench_dbqa", instance, "b") == 0.0


def test_labbench_split_mapping_val_uses_local_test_file(tmp_path):
    _write_rows(
        tmp_path,
        "DbQA",
        "train",
        [
            {
                "id": "d3",
                "question": "train question",
                "ideal": "GENE_A",
                "distractors": ["GENE_X", "GENE_Y"],
                "canary": "Insufficient information to answer the question.",
            }
        ],
    )
    _write_rows(
        tmp_path,
        "DbQA",
        "val",
        [
            {
                "id": "d4",
                "question": "test question",
                "ideal": "GENE_B",
                "distractors": ["GENE_X", "GENE_Y"],
                "canary": "Insufficient information to answer the question.",
            }
        ],
    )

    adapter = LabBenchAdapter(local_root=str(tmp_path), prefer_remote=False)
    instances = adapter.get_instances("lab_bench_dbqa", split="val")

    assert instances[0]["instance_id"] == "d4"
    assert "test question" in instances[0]["prompt"]


def test_labbench_fallback_local_without_datasets(monkeypatch, tmp_path):
    _write_rows(
        tmp_path,
        "DbQA",
        "test",
        [
            {
                "id": "d5",
                "question": "Which gene is best?",
                "ideal": "GENE_Z",
                "distractors": ["GENE_X", "GENE_Y"],
                "canary": "Insufficient information to answer the question.",
            }
        ],
    )

    adapter = LabBenchAdapter(local_root=str(tmp_path), prefer_remote=True)

    def _fail_remote(*_args, **_kwargs):
        raise RuntimeError("HF unavailable")

    # Remote fails, local exists: should still return results.
    monkeypatch.setattr(adapter, "_load_remote_split", _fail_remote)
    instances = adapter.get_instances("lab_bench_dbqa", split="test")
    assert len(instances) == 1
    assert instances[0]["instance_id"] == "d5"

    # Remote fails, local missing: should surface local filesystem error.
    with pytest.raises(FileNotFoundError, match="Local lab-bench file not found"):
        broken_adapter = LabBenchAdapter(local_root=str(tmp_path / "missing"), prefer_remote=True)
        monkeypatch.setattr(broken_adapter, "_load_remote_split", _fail_remote)
        broken_adapter.get_instances("lab_bench_dbqa", split="test")
