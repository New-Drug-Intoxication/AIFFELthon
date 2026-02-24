import pandas as pd
from biomni.eval.pipeline import EvaluationPipeline


class _ScoringBenchmark:
    def __init__(self):
        self._evaluated = []

    def evaluate_result(self, task_name, instance, prediction):
        self._evaluated.append((task_name, instance["instance_id"], prediction))
        return 1.0 if prediction.get("causal_gene", [None])[0] in {"BRCA1", "ENSG00000141510"} else 0.0

    def get_tasks(self):
        return ["patient_gene_detection"]

    def get_instances(self, task_name: str, split: str):
        return []


class _DummyBenchmark:
    def __init__(self, tasks: list[str] | None = None):
        self._tasks = tasks or ["patient_gene_detection"]

    def get_tasks(self):
        return list(self._tasks)

    def get_instances(self, task_name: str, split: str):
        return []


class _DummyAgent:
    pass


class _DummyLogger:
    def log_config(self, config):
        pass

    def log_result(self, result):
        pass

    def log_metrics(self, metrics):
        pass

    def finish(self):
        pass


def _add_norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["x_name_norm"] = out["x_name"].fillna("").astype(str).str.lower().str.strip()
    out["y_name_norm"] = out["y_name"].fillna("").astype(str).str.lower().str.strip()
    return out


def _make_pipeline() -> EvaluationPipeline:
    pipeline = EvaluationPipeline(_DummyBenchmark(), lambda: None, _DummyLogger())
    pipeline._patient_gene_local_kg_resources.update(
        {
            "loaded": True,
            "load_error": None,
            "kg_df": _add_norm_cols(
                pd.DataFrame(
                [
                    {
                        "relation": "is_causal_gene_for",
                        "display_relation": "causal association",
                        "x_name": "BRCA1",
                        "y_name": "breast cancer",
                    },
                    {
                        "relation": "interacts_with",
                        "display_relation": "associated",
                        "x_name": "TP53",
                        "y_name": "lung cancer",
                    },
                ])),
            "gene_info_df": pd.DataFrame(
                [
                    {"ensembl_gene_id": "ENSG00000141510", "gene_name": "BRCA1"},
                    {"ensembl_gene_id": "ENSG00000141510", "gene_name": "BRCA1"},
                ]
            ),
            "ensg_to_symbol": {"ENSG00000141510": "BRCA1"},
            "symbol_to_ensg": {"BRCA1": "ENSG00000141510"},
        }
    )
    return pipeline


def test_local_patient_kg_solves_high_confidence_case():
    pipeline = _make_pipeline()
    prompt = "Patient has genes in locus: {BRCA1},{TP53},{EGFR}. Disease: breast cancer"
    solution = pipeline._solve_patient_gene_from_local_kg(prompt)

    assert solution is not None
    assert solution["solved"] is True
    assert solution["method"] == "local_kg"
    assert solution["confidence"] >= pipeline.patient_gene_local_kg_confidence
    assert isinstance(solution["prediction"], dict)
    assert set(solution["prediction"]["causal_gene"]) == {"BRCA1", "ENSG00000141510"}


def test_local_patient_kg_maps_ensembl_candidate_to_symbol():
    pipeline = _make_pipeline()
    pipeline._patient_gene_local_kg_resources["kg_df"] = _add_norm_cols(
        pd.DataFrame(
        [
            {
                "relation": "interacts",
                "display_relation": "causal association",
                "x_name": "ENSG00000141510",
                "y_name": "breast cancer",
            },
            {
                "relation": "coexpressed",
                "display_relation": "related_to",
                "x_name": "TP53",
                "y_name": "liver disorder",
            },
        ]))
    prompt = "Genes: {ENSG00000141510}, {TP53}. Disease: breast cancer"
    solution = pipeline._solve_patient_gene_from_local_kg(prompt)

    assert solution is not None
    assert solution["solved"] is True
    assert "BRCA1" in solution["prediction"]["causal_gene"]


def test_local_patient_kg_fallback_when_confidence_too_low():
    pipeline = _make_pipeline()
    pipeline.patient_gene_local_kg_confidence = 0.99
    pipeline._patient_gene_local_kg_resources["kg_df"] = _add_norm_cols(
        pd.DataFrame(
        [
            {
                "relation": "assoc",
                "display_relation": "associated",
                "x_name": "BRCA1",
                "y_name": "breast cancer",
            },
            {
                "relation": "assoc",
                "display_relation": "associated",
                "x_name": "TP53",
                "y_name": "breast cancer",
            },
        ]))
    prompt = "Genes: {BRCA1}, {TP53}. Disease: breast cancer"
    solution = pipeline._solve_patient_gene_from_local_kg(prompt)

    assert solution is not None
    assert solution["solved"] is False
    assert solution["method"] == "local_kg_fallback"
    assert solution["prediction"] is None


def test_process_instance_scores_local_kg_prediction_and_records_metadata():
    benchmark = _ScoringBenchmark()
    pipeline = EvaluationPipeline(benchmark, lambda: None, _DummyLogger())
    # Reuse existing KG fixture values.
    pipeline._patient_gene_local_kg_resources = _make_pipeline()._patient_gene_local_kg_resources
    pipeline.patient_gene_local_kg_enabled = True

    instance = {
        "instance_id": "1",
        "prompt": "Genes in locus: {BRCA1},{TP53},{EGFR}. Disease: breast cancer",
        "ground_truth": "BRCA1",
    }

    result = pipeline._process_instance(_DummyAgent(), "patient_gene_detection", instance)

    assert result["score"] == 1.0
    assert result["success"] is True
    assert result["metrics"]["patient_gene_local_kg_used"] is True
    assert len(benchmark._evaluated) == 1
    task_name, instance_id, prediction = benchmark._evaluated[0]
    assert task_name == "patient_gene_detection"
    assert instance_id == "1"
    assert set(prediction["causal_gene"]) == {"BRCA1", "ENSG00000141510"}
