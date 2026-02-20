import pandas as pd
from pathlib import Path

from biomni.eval.benchmark import BixBenchAdapter


def _write_rows(root: Path, split: str, rows: list[dict]):
    file_name = {
        "train": "train-00000-of-00001.parquet",
        "val": "train-00000-of-00001_test.parquet",
        "validation": "train-00000-of-00001_test.parquet",
        "test": "train-00000-of-00001_test.parquet",
    }[split]

    path = root / "benchmark" / "bixbench" / file_name
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def test_bixbench_get_tasks_singleton():
    adapter = BixBenchAdapter(local_root=str(Path("/tmp")), prefer_remote=False)
    assert adapter.get_tasks() == ["bixbench"]


def test_bixbench_get_instances_open_answer_prompt_and_fields(tmp_path):
    _write_rows(
        tmp_path,
        "test",
        [
            {
                "id": "q-open",
                "question": "What mutation is present?",
                "ideal": "BRAF V600E",
                "distractors": ["KRAS G12D", "EGFR L858R"],
                "eval_mode": "open_answer",
                "canary": "Insufficient information to answer the question.",
            }
        ],
    )

    adapter = BixBenchAdapter(local_root=str(tmp_path), prefer_remote=False)
    instances = adapter.get_instances("bixbench", split="test")

    assert len(instances) == 1
    instance = instances[0]
    assert instance["eval_mode"] == "open_answer"
    assert instance["instance_id"] == "q-open"
    assert instance["ground_truth"] == "BRAF V600E"
    assert instance["ground_truth"] != "A"
    assert "[ANSWER]" in instance["prompt"]
    assert "exact text" in instance["prompt"].lower()


def test_bixbench_infer_open_answer_from_verifier_flags(tmp_path):
    _write_rows(
        tmp_path,
        "test",
        [
            {
                "id": "q-open-flag",
                "question": "Which gene family is mutated?",
                "ideal": "APOE",
                "distractors": ["TP53", "BRCA1", "EGFR"],
                "llm_verifier": True,
                "range_verifier": False,
                "str_verifier": False,
            }
        ],
    )

    adapter = BixBenchAdapter(local_root=str(tmp_path), prefer_remote=False)
    instance = adapter.get_instances("bixbench", split="test")[0]

    assert instance["eval_mode"] == "open_answer"
    assert "exact text" in instance["prompt"].lower()
    assert instance["ground_truth"] == "APOE"


def test_bixbench_infer_open_answer_from_verifier_name(tmp_path):
    _write_rows(
        tmp_path,
        "test",
        [
            {
                "id": "q-open-flag2",
                "question": "Give a gene symbol.",
                "ideal": "BRCA1",
                "distractors": ["TP53", "KRAS", "EGFR"],
                "verifier": "range_verifier",
            }
        ],
    )

    adapter = BixBenchAdapter(local_root=str(tmp_path), prefer_remote=False)
    instance = adapter.get_instances("bixbench", split="test")[0]

    assert instance["eval_mode"] == "open_answer"
    assert instance["ground_truth"] == "BRCA1"


def test_bixbench_open_answer_scoring_text_match(tmp_path):
    _write_rows(
        tmp_path,
        "test",
        [
            {
                "id": "q-open-2",
                "question": "What mutation is present?",
                "ideal": "BRAF V600E",
                "distractors": ["KRAS G12D", "EGFR L858R"],
                "eval_mode": "open_answer",
            }
        ],
    )

    adapter = BixBenchAdapter(local_root=str(tmp_path), prefer_remote=False)
    instance = adapter.get_instances("bixbench", split="test")[0]

    assert adapter.evaluate_result("bixbench", instance, "[ANSWER]BRAF  V600E[/ANSWER]") == 1.0
    assert adapter.evaluate_result("bixbench", instance, "[ANSWER]braf v600e[/ANSWER]") == 1.0
    assert adapter.evaluate_result("bixbench", instance, "[ANSWER]KRAS G12D[/ANSWER]") == 0.0
    assert adapter.evaluate_result("bixbench", instance, "[ANSWER]A[/ANSWER]") == 0.0


def test_bixbench_bool_answer_infers_open_answer(tmp_path):
    _write_rows(
        tmp_path,
        "val",
        [
            {
                "id": "q-bool",
                "question": "Is this statement true: BRCA1 is a known breast cancer gene?",
                "answer": True,
                "distractors": [],
            }
        ],
    )

    adapter = BixBenchAdapter(local_root=str(tmp_path), prefer_remote=False)
    instance = adapter.get_instances("bixbench", split="val")[0]

    assert instance["eval_mode"] == "open_answer"
    assert instance["ground_truth"] == "true"
    assert adapter.evaluate_result("bixbench", instance, "[ANSWER] TRUE [/ANSWER]") == 1.0
    assert adapter.evaluate_result("bixbench", instance, "[ANSWER] false [/ANSWER]") == 0.0


def test_bixbench_canary_not_in_options(tmp_path):
    _write_rows(
        tmp_path,
        "val",
        [
            {
                "id": "q-canary",
                "question": "Which gene is most likely associated?",
                "ideal": "GENE_A",
                "distractors": ["GENE_B", "GENE_C"],
                "canary": "Insufficient information to answer the question.",
            }
        ],
    )

    adapter = BixBenchAdapter(local_root=str(tmp_path), prefer_remote=False)
    instance = adapter.get_instances("bixbench", split="val")[0]

    assert instance["has_canary"] is True
    assert "Insufficient information to answer the question." not in instance["prompt"]


def test_bixbench_mcq_still_works(tmp_path):
    _write_rows(
        tmp_path,
        "val",
        [
            {
                "id": "q-mcq",
                "question": "Which option is correct?",
                "ideal": "Option B",
                "distractors": ["Option A", "Option C"],
            }
        ],
    )

    adapter = BixBenchAdapter(local_root=str(tmp_path), prefer_remote=False)
    instance = adapter.get_instances("bixbench", split="val")[0]

    assert instance["eval_mode"] == "mcq"
    assert instance["ground_truth"] in {"A", "B", "C", "D", "E"}
    pred = f"[ANSWER]{instance['ground_truth']}[/ANSWER]"
    assert adapter.evaluate_result("bixbench", instance, pred) == 1.0
    assert adapter.evaluate_result("bixbench", instance, "[ANSWER]A[/ANSWER]") == (1.0 if instance["ground_truth"] == "A" else 0.0)
