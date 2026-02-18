import pandas as pd

from biomni.tool.support_tools import preview, reset_python_repl_namespace, run_python_repl, summarize_df, summarize_dict


def test_summarize_df_includes_shape_columns_and_head():
    df = pd.DataFrame({"gene": [f"G{i}" for i in range(10)], "score": list(range(10))})
    text = summarize_df(df, head_rows=5, max_chars=1000)
    assert "shape=(10, 2)" in text
    assert "columns(2)" in text
    assert "head(5)" in text
    assert "G0" in text


def test_summarize_dict_limits_items_and_truncates_values():
    data = {f"k{i}": ("x" * 800 if i == 0 else i) for i in range(30)}
    text = summarize_dict(data, top_n=20, max_chars=500)
    assert "total_keys=30" in text
    assert "showing_top=20" in text
    assert "k19" in text
    assert "k20" not in text
    assert "truncated" in text


def test_preview_summarizes_list_and_dict():
    list_text = preview(list(range(30)), list_top_n=20, max_chars=200)
    assert "list summary: size=30, showing_top=20" in list_text
    assert "... 10 more items omitted" in list_text

    dict_text = preview({f"k{i}": i for i in range(25)}, dict_top_n=20, max_chars=200)
    assert "dict summary: total_keys=25, showing_top=20" in dict_text
    assert "... 5 more keys omitted" in dict_text


def test_preview_is_available_from_repl_namespace():
    reset_python_repl_namespace(preload_defaults=True)
    output = run_python_repl(
        "df = pd.DataFrame({'a': list(range(10)), 'b': list(range(10))})\n"
        "print(preview(df))"
    )
    assert "DataFrame summary: shape=(10, 2)" in output
    assert "head(5)" in output
