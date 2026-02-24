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


def test_variant_extraction_last_rs_id_from_solution_and_text():
    prompt = "Gene locus: AFM, AFP, ALB"
    prediction = "<solution>rs12345</solution> ... and later rs67890"
    normalized = normalize_prediction_for_scoring("gwas_variant_prioritization", prompt, prediction)
    assert normalized == "rs67890"


def test_variant_extraction_from_solution_tag_only():
    prompt = "rs67890, rs11111"
    prediction = "<solution>rs67890</solution>"
    normalized = normalize_prediction_for_scoring("gwas_variant_prioritization", prompt, prediction)
    assert normalized == "rs67890"


def test_lab_bench_letter_validation_rejects_invalid_option():
    prompt = "1) Option A\n2) Option B\n3) Option C\n4) Option D"
    prediction = "[ANSWER]E[/ANSWER]"
    normalized = normalize_prediction_for_scoring("lab_bench_dbqa", prompt, prediction)
    assert normalized == ""


def test_lab_bench_letter_prefers_solution_answer_tag():
    prompt = "A) cat\nB) dog\nC) mouse"
    prediction = "<analysis>thinking...</analysis>[ANSWER]B[/ANSWER] I think it's B"
    normalized = normalize_prediction_for_scoring("lab_bench_dbqa", prompt, prediction)
    assert normalized == "B"


def test_patient_gene_handles_dict_payload():
    prompt = "{BRCA1}, {TP53}, {KRAS}"
    prediction = "{'causal_gene': 'TP53'}"
    normalized = normalize_prediction_for_scoring("patient_gene_detection", prompt, prediction)
    assert normalized == "TP53"


def test_patient_gene_handles_list_payload_and_ensg():
    prompt = "{BRCA1}, {TP53}, {KRAS}"
    list_prediction = '["ENSG00000141510", "TP53"]'
    normalized = normalize_prediction_for_scoring("patient_gene_detection", prompt, list_prediction)
    assert normalized == "ENSG00000141510"


def test_patient_gene_extracts_ensg_pattern_from_free_text():
    prompt = "{BRCA1}, {TP53}, {KRAS}"
    prediction = "Candidate causal gene symbol is ENSG00000141510 with supporting evidence."
    normalized = normalize_prediction_for_scoring("patient_gene_detection", prompt, prediction)
    assert normalized == "ENSG00000141510"


def test_rare_disease_omim_id_extraction_from_sentence():
    prompt = "Predict disease from symptoms"
    prediction = "Based on this, I select OMIM 617193 as best match."
    normalized = normalize_prediction_for_scoring("rare_disease_diagnosis", prompt, prediction)
    assert normalized == "{\"OMIM_ID\": \"617193\"}"


def test_rare_disease_omim_id_kept_if_six_digits_only():
    prompt = "Predict disease from symptoms"
    prediction = "616866"
    normalized = normalize_prediction_for_scoring("rare_disease_diagnosis", prompt, prediction)
    assert normalized == "{\"OMIM_ID\": \"616866\"}"
