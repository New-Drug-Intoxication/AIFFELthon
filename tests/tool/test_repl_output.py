from biomni.tool.support_tools import (
    MAX_OUTPUT_CHARS,
    _compress_repeated_lines,
    _postprocess_output,
    _structural_summarize,
    run_python_repl,
)


def test_postprocess_pass_through_short_output():
    raw = "hello\nworld\n" * 50
    assert len(raw) < 3000
    assert _postprocess_output(raw) == raw


def test_compress_repeated_lines_keeps_head_tail():
    lines = [f"{i:04d} ABC-DEF 123.45" for i in range(500)]
    compressed = _compress_repeated_lines(lines, head=5, tail=2)
    assert "0000 ABC-DEF 123.45" in compressed
    assert "0004 ABC-DEF 123.45" in compressed
    assert "0498 ABC-DEF 123.45" in compressed
    assert "0499 ABC-DEF 123.45" in compressed
    assert "more rows with same structure" in compressed


def test_structural_summarize_large_dict_repr():
    raw = "payload=" + "{" + ", ".join([f"'k{i}': '{'x'*40}'" for i in range(200)]) + "}"
    summarized = _structural_summarize(raw)
    assert len(summarized) < len(raw)
    assert "chars total" in summarized or "... (omitted)" in summarized


def test_postprocess_final_guard_applies_head_tail():
    raw = "\n".join([f"line-{i}: {'x'*80}" for i in range(1000)])
    processed = _postprocess_output(raw)
    assert len(processed) <= MAX_OUTPUT_CHARS + 200
    # Depending on compression effectiveness, either structured compression or final guard may trigger.
    assert "chars total, truncated" in processed or "more rows with same structure" in processed
    assert "line-0" in processed
    assert "line-999" in processed


def test_run_python_repl_applies_postprocess():
    code = "for i in range(1200):\n    print('row', i, 'value', i * 0.01)"
    output = run_python_repl(code)
    assert len(output) <= MAX_OUTPUT_CHARS + 200
    assert "more rows with same structure" in output or "chars total, truncated" in output
