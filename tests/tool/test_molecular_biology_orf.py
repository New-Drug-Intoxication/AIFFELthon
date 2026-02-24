from biomni.tool.molecular_biology import annotate_open_reading_frames


def test_annotate_open_reading_frames_orf_supports_get():
    result = annotate_open_reading_frames("ATGAAATTTTAG", min_length=9, search_reverse=False)
    orfs = result["orfs"]
    assert orfs, "Expected at least one ORF to be detected"

    orf = orfs[0]
    assert orf.get("start") == 0
    assert orf.get("end") == 12
    assert orf.get("frame") in (1, -1, 2, 3, -2, -3)
    assert orf["start"] == orf.start
    assert orf["end"] == orf.end
    assert orf["sequence"] == orf.sequence
    assert orf.get("missing", "fallback") == "fallback"
