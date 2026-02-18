import pandas as pd

from biomni.tool.support_tools import (
    ensure_unique_columns,
    infer_ensembl_gene_id_column,
    preview,
    reset_python_repl_namespace,
    run_python_repl,
    safe_concat,
    safe_reindex,
    summarize_df,
    summarize_dict,
)


def test_namespace_persists_within_instance():
    reset_python_repl_namespace(preload_defaults=True)
    first = run_python_repl("df = pd.DataFrame({'x': [1, 2]})\nprint(df.shape)")
    second = run_python_repl("print(df['x'].sum())")
    assert "Error:" not in first
    assert "3" in second


def test_namespace_resets_between_instances():
    reset_python_repl_namespace(preload_defaults=True)
    run_python_repl("tmp_var = 123")
    reset_python_repl_namespace(preload_defaults=True)
    output = run_python_repl("print('tmp_var' in globals())")
    assert "False" in output


def test_default_aliases_are_preloaded():
    reset_python_repl_namespace(preload_defaults=True)
    output = run_python_repl(
        "print(pd.__name__)\n"
        "print(np.__name__)\n"
        "print(os.__name__)\n"
        "print(callable(infer_ensembl_gene_id_column))\n"
        "print(callable(safe_concat))\n"
        "print(callable(preview))\n"
        "print(callable(summarize_df))\n"
        "print(callable(summarize_dict))"
    )
    assert "pandas" in output
    assert "numpy" in output
    assert "os" in output
    assert "True" in output


def test_infer_ensembl_gene_id_column_handles_variants():
    df = pd.DataFrame({"Ensembl Gene ID": ["ENSG000001", "ENSG000002"], "value": [1, 2]})
    assert infer_ensembl_gene_id_column(df) == "Ensembl Gene ID"


def test_safe_helpers_handle_duplicate_columns_and_index():
    left = pd.DataFrame([[1, 2]], columns=["A", "A"])
    right = pd.DataFrame([[3, 4]], columns=["A", "B"])
    combined = safe_concat([left, right], dedup_columns=True)
    assert combined.columns.is_unique

    dup_index_df = pd.DataFrame({"x": [10, 20]}, index=[0, 0])
    reindexed = safe_reindex(dup_index_df, [0], dedup_index=True)
    assert list(reindexed.index) == [0]

    deduped = ensure_unique_columns(left)
    assert deduped.columns.is_unique


def test_print_is_not_overridden_in_repl():
    reset_python_repl_namespace(preload_defaults=True)
    output = run_python_repl("import builtins\nprint(print.__name__)\nprint(print is builtins.print)")
    assert "print" in output
    assert "True" in output
