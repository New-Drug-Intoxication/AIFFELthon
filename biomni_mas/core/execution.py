from __future__ import annotations

import queue
import time
import sys
import threading
from io import StringIO
from typing import Any


_stdout_lock = threading.Lock()


def inject_repl_scope(scope: dict[str, Any], namespace: dict[str, Any]) -> None:
    if not isinstance(scope, dict) or not scope:
        return
    namespace.update(scope)


def run_python_repl(
    command: str,
    namespace: dict[str, Any],
    stdout_lock: threading.Lock | None = None,
    cancel_event: threading.Event | None = None,
) -> str:
    lock = stdout_lock or _stdout_lock
    with lock:
        old_stdout = sys.stdout
        sys.stdout = buffer = StringIO()
        old_trace = sys.gettrace()
        try:
            if cancel_event is not None:
                # Cooperative cancellation: interrupt Python bytecode execution
                # when timeout thread signals cancellation.
                def _trace(frame, event, arg):  # type: ignore[no-untyped-def]
                    del frame, event, arg
                    if cancel_event.is_set():
                        raise TimeoutError("Execution canceled due to timeout")
                    return _trace

                sys.settrace(_trace)
            source = command.strip("```").strip()
            exec(source, namespace)
            return buffer.getvalue()
        except Exception as e:
            return f"Error: {e}"
        finally:
            sys.settrace(old_trace)
            sys.stdout = old_stdout


def run_with_timeout(func, args=None, kwargs=None, timeout: int = 600):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    result_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
    cancel_event = threading.Event()
    kwargs = dict(kwargs)
    kwargs.setdefault("cancel_event", cancel_event)

    def _worker() -> None:
        try:
            result_queue.put(("success", func(*args, **kwargs)))
        except Exception as e:
            result_queue.put(("error", str(e)))

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        cancel_event.set()
        thread.join(1.0)
        if thread.is_alive():
            # Cannot hard-kill Python threads safely; report and return.
            return (
                f"TIMEOUT: Code execution timed out after {timeout} seconds "
                "(cancellation requested; worker may still be stopping)"
            )
        # Give worker a tiny window to flush result after cooperative cancellation.
        time.sleep(0.01)
    try:
        status, payload = result_queue.get_nowait()
    except queue.Empty:
        return "Error: No result returned"
    if status == "error":
        return f"Error: {payload}"
    return payload
