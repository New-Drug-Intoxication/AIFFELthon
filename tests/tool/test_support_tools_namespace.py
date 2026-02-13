from biomni.tool.support_tools import reset_python_repl_namespace, run_python_repl


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
    output = run_python_repl("print(pd.__name__)\nprint(np.__name__)\nprint(os.__name__)")
    assert "pandas" in output
    assert "numpy" in output
    assert "os" in output
