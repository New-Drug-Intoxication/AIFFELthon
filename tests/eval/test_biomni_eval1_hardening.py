from biomni.eval.biomni_eval1 import BiomniEval1


def _evaluator_without_init() -> BiomniEval1:
    return BiomniEval1.__new__(BiomniEval1)


def test_compute_reward_accepts_list_input_for_string_tasks():
    evaluator = _evaluator_without_init()
    user_answer = [{"type": "text", "text": "a"}]
    score = evaluator._compute_reward("crispr_delivery", user_answer, "A")
    assert score == 1.0


def test_compute_reward_accepts_list_input_for_json_tasks():
    evaluator = _evaluator_without_init()
    user_answer = [{"type": "text", "text": '{"causal_gene": ["ENSG00000161011"]}'}]
    score = evaluator._compute_reward("patient_gene_detection", user_answer, "ENSG00000161011")
    assert score == 1.0


def test_compute_reward_string_comparison_behavior_is_preserved():
    evaluator = _evaluator_without_init()
    assert evaluator._compute_reward("screen_gene_retrieval", "vmp1", "VMP1") == 1.0
    assert evaluator._compute_reward("gwas_variant_prioritization", "rs1", "rs2") == 0.0
