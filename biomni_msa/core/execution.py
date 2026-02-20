from __future__ import annotations

import queue
import sys
import threading
from io import StringIO
from typing import Any


_persistent_namespace: dict[str, Any] = {}


def inject_repl_scope(scope: dict[str, Any]) -> None:
    if not isinstance(scope, dict) or not scope:
        return
    _persistent_namespace.update(scope)


def run_python_repl(command: str) -> str:
    old_stdout = sys.stdout
    sys.stdout = buffer = StringIO()
    try:
        source = command.strip("```").strip()
        exec(source, _persistent_namespace)
        return buffer.getvalue()
    except Exception as e:
        return f"Error: {e}"
    finally:
        sys.stdout = old_stdout


def run_with_timeout(func, args=None, kwargs=None, timeout: int = 600):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    result_queue: queue.Queue[tuple[str, Any]] = queue.Queue()

    def _worker() -> None:
        try:
            result_queue.put(("success", func(*args, **kwargs)))
        except Exception as e:
            result_queue.put(("error", str(e)))

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return f"TIMEOUT: Code execution timed out after {timeout} seconds"
    try:
        status, payload = result_queue.get_nowait()
    except queue.Empty:
        return "Error: No result returned"
    if status == "error":
        return f"Error: {payload}"
    return payload
