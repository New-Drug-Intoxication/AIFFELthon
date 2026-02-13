from biomni.eval.pipeline import normalize_prediction_for_scoring


def test_list_content_block_is_flattened_and_mapped_to_candidate_gene():
    prompt = "GWAS phenotype: Type 2 diabetes\nGenes in locus: {HNF1A},{PPARG},{RAF1}"
    prediction = [{"type": "text", "text": "HNF1A", "annotations": []}]
    normalized = normalize_prediction_for_scoring("gwas_causal_gene_opentargets", prompt, prediction)
    assert normalized == "HNF1A"


def test_answer_tag_extraction_for_letter_tasks():
    prompt = "The following is a multiple choice question."
    prediction = "[ANSWER]c[/ANSWER]"
    normalized = normalize_prediction_for_scoring("lab_bench_dbqa", prompt, prediction)
    assert normalized == "C"


def test_solution_block_extraction():
    prompt = "Candidate genes: TMEM37, VMP1, TRIM16"
    prediction = "Reasoning...\n<solution>VMP1</solution>"
    normalized = normalize_prediction_for_scoring("screen_gene_retrieval", prompt, prediction)
    assert normalized == "VMP1"


def test_variant_canonicalization_prefers_prompt_candidates():
    prompt = "Variants: rs7700133, rs4253311, rs855791"
    prediction = "Top associated variant: rs4253311 because of p-value."
    normalized = normalize_prediction_for_scoring("gwas_variant_prioritization", prompt, prediction)
    assert normalized == "rs4253311"


def test_gene_candidate_mapping_from_free_text():
    prompt = "Candidate genes: TMEM37, VMP1, TRIM16"
    prediction = "The strongest perturbation effect is expected for TRIM16 in this context."
    normalized = normalize_prediction_for_scoring("screen_gene_retrieval", prompt, prediction)
    assert normalized == "TRIM16"
