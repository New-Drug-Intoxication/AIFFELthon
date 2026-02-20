import time

from biomni.utils import run_with_timeout


def test_run_with_timeout_returns_function_result():
    def quick():
        return "ok"

    assert run_with_timeout(quick, timeout=1) == "ok"


def test_run_with_timeout_returns_timeout_error():
    def slow():
        time.sleep(0.2)
        return "done"

    result = run_with_timeout(slow, timeout=0.01)
    assert result.startswith("ERROR:")
    assert "timed out" in result


def test_run_with_timeout_includes_source_meta():
    def slow():
        time.sleep(0.2)
        return "done"

    result = run_with_timeout(slow, timeout=0.01)
    assert "source=run_with_timeout" in result
    assert "elapsed=" in result


def test_run_with_timeout_error_contains_meta():
    def boom():
        raise RuntimeError("broken")

    result = run_with_timeout(boom, timeout=1)
    assert result.startswith("Error in execution:")
    assert "func=boom" in result
    assert "source=run_with_timeout" in result
