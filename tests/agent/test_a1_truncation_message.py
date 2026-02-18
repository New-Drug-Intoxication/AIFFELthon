from pathlib import Path


def test_truncation_message_recommends_preview_helpers():
    content = Path("biomni/agent/a1.py").read_text(encoding="utf-8")
    assert "The output is too long to be added to context and was truncated to the first 10K characters." in content
    assert "print(preview(df))" in content
    assert "print(summarize_df(df))" in content
    assert "print(preview(result_dict))" in content
