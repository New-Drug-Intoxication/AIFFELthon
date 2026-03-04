from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
import queue
import statistics
import threading
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import run_mas_web as base
from biomni_mas import MASAgent
from biomni_mas.eval import BiomniEval1, normalize_answer_for_task


CASE_TIMEOUT_SEC = 20 * 60


def _build_pa_html() -> str:
    html = base.HTML_PAGE
    html = html.replace("Biomni MAS Web Monitor", "Biomni MAS Web Monitor (PA)", 1)
    html = html.replace(
        '<h3 style="margin-top:0">Node Timeline</h3>',
        '<h3 style="margin-top:0">Worker Timelines</h3>',
        1,
    )
    marker = '<div class="control">\n            <label for="evalSplit">Split</label>'
    inject = (
        '<div class="control">\n'
        '            <label for="evalParallelism">Parallel workers</label>\n'
        '            <input id="evalParallelism" type="number" min="1" max="32" value="10" style="padding:6px 8px; border:1px solid #d1d5db; border-radius:8px;" />\n'
        "          </div>\n"
    )
    if marker in html:
        html = html.replace(marker, inject + marker, 1)

    # Ensure base stream request carries eval_parallelism when PA control exists.
    html = html.replace(
        '        eval_selected_tasks: selectedTasks.join(","),\n      });',
        '        eval_selected_tasks: selectedTasks.join(","),\n'
        '        eval_parallelism: String(((document.getElementById("evalParallelism") || {}).value || "10")),\n'
        "      });",
        1,
    )

    # Let PA layer consume node payload first; fallback to base renderer if not handled.
    html = html.replace(
        '      es.addEventListener("node", (ev) => {\n'
        "        const payload = JSON.parse(ev.data);\n"
        "        const tok = payload.token_usage || {};\n"
        "        const inTok = tok.input || 0;\n"
        "        const outTok = tok.output || 0;\n"
        "        const totalTok = tok.total || (inTok + outTok);\n"
        '        const meta = `workflow=${payload.workflow_state || "-"}, stage=${payload.stage || "-"}, tokens(in/out/total)=${inTok}/${outTok}/${totalTok}`;\n'
        '        addEvent(payload.label || "Event", payload.content || "", meta, payload.data || null);\n'
        "      });",
        '      es.addEventListener("node", (ev) => {\n'
        "        const payload = JSON.parse(ev.data);\n"
        "        if (window.__paHandleNode && window.__paHandleNode(payload) === true) {\n"
        "          return;\n"
        "        }\n"
        "        const tok = payload.token_usage || {};\n"
        "        const inTok = tok.input || 0;\n"
        "        const outTok = tok.output || 0;\n"
        "        const totalTok = tok.total || (inTok + outTok);\n"
        '        const meta = `workflow=${payload.workflow_state || "-"}, stage=${payload.stage || "-"}, tokens(in/out/total)=${inTok}/${outTok}/${totalTok}`;\n'
        '        addEvent(payload.label || "Event", payload.content || "", meta, payload.data || null);\n'
        "      });",
        1,
    )

    addon = """
<style id="pa-worker-style">
  :root {
    --worker-box-width: 560px;
    --worker-box-height: 640px;
  }
  #workerGrid {
    display: none;
    flex-direction: row;
    flex-wrap: nowrap;
    align-items: stretch;
    gap: 10px;
    width: 100%;
    min-height: var(--worker-box-height);
    max-height: 92vh;
    overflow-x: auto;
    overflow-y: hidden;
  }
  .worker-card {
    border: 1px solid #d1d5db;
    border-radius: 10px;
    background: #fff;
    padding: 8px;
    width: var(--worker-box-width);
    min-width: var(--worker-box-width);
    height: var(--worker-box-height);
    min-height: 320px;
    display: flex;
    flex-direction: column;
    overflow: auto;
    resize: both;
    flex: 0 0 auto;
  }
  .worker-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 700;
    font-size: 12px;
    margin-bottom: 6px;
  }
  .worker-state {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 999px;
    background: #e5e7eb;
    color: #111827;
  }
  .worker-events {
    flex: 1 1 auto;
    border-top: 1px dashed #d1d5db;
    padding-top: 6px;
    overflow: auto;
    font-size: 12px;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    word-break: break-word;
  }
  .worker-event {
    border-left: 3px solid #0f766e;
    padding-left: 6px;
    margin-bottom: 6px;
  }
  .worker-case-divider {
    margin: 8px 0 10px;
    padding: 4px 8px;
    border-radius: 6px;
    background: #ecfeff;
    border: 1px solid #99f6e4;
    color: #134e4a;
    font-size: 11px;
    font-weight: 700;
  }
  .worker-event .label {
    font-weight: 600;
    margin-bottom: 2px;
  }
  .worker-event .text {
    margin-bottom: 4px;
  }
  .worker-event .code-label {
    margin-top: 4px;
    margin-bottom: 2px;
    font-size: 11px;
    font-weight: 700;
    color: #334155;
  }
  .worker-event pre.code-box {
    margin: 0 0 6px;
    padding: 8px;
    border-radius: 8px;
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    color: #0f172a;
    overflow-x: auto;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 11px;
    line-height: 1.45;
  }
</style>
<script>
(() => {
  const timeline = document.getElementById("timeline");
  const runBtn = document.getElementById("runBtn");
  const stopBtn = document.getElementById("stopBtn");
  const eval1Mode = document.getElementById("eval1Mode");
  const evalControls = document.getElementById("evalControls");
  if (!timeline || !runBtn || !stopBtn || !eval1Mode || !evalControls) return;

  function ensureParallelInput() {
    let input = document.getElementById("evalParallelism");
    if (input) return input;
    const div = document.createElement("div");
    div.className = "control";
    div.innerHTML = '<label for="evalParallelism">Parallel workers</label><input id="evalParallelism" type="number" min="1" max="32" value="10" style="padding:6px 8px; border:1px solid #d1d5db; border-radius:8px;" />';
    evalControls.insertBefore(div, evalControls.children[1] || null);
    return document.getElementById("evalParallelism");
  }

  const parallelInput = ensureParallelInput();
  if (!parallelInput) return;

  function ensureBoxSizeControls() {
    let w = document.getElementById("workerBoxWidth");
    let h = document.getElementById("workerBoxHeight");
    if (!w) {
      const divW = document.createElement("div");
      divW.className = "control";
      divW.innerHTML = '<label for="workerBoxWidth">Worker box width</label><input id="workerBoxWidth" type="number" min="280" max="1600" step="20" value="560" style="padding:6px 8px; border:1px solid #d1d5db; border-radius:8px;" />';
      evalControls.insertBefore(divW, evalControls.children[2] || null);
      w = document.getElementById("workerBoxWidth");
    }
    if (!h) {
      const divH = document.createElement("div");
      divH.className = "control";
      divH.innerHTML = '<label for="workerBoxHeight">Worker box height</label><input id="workerBoxHeight" type="number" min="320" max="1400" step="20" value="640" style="padding:6px 8px; border:1px solid #d1d5db; border-radius:8px;" />';
      evalControls.insertBefore(divH, evalControls.children[3] || null);
      h = document.getElementById("workerBoxHeight");
    }
    return { w, h };
  }
  const sizeInputs = ensureBoxSizeControls();
  const boxWidthInput = sizeInputs.w;
  const boxHeightInput = sizeInputs.h;
  if (!boxWidthInput || !boxHeightInput) return;

  function loadStored(key, fallback) {
    try {
      const v = localStorage.getItem(key);
      return v || fallback;
    } catch (_e) {
      return fallback;
    }
  }

  function saveStored(key, val) {
    try { localStorage.setItem(key, String(val)); } catch (_e) {}
  }

  function applyBoxSize() {
    const wRaw = parseInt(boxWidthInput.value || "560", 10);
    const hRaw = parseInt(boxHeightInput.value || "640", 10);
    const w = Number.isFinite(wRaw) ? Math.min(1600, Math.max(280, wRaw)) : 560;
    const h = Number.isFinite(hRaw) ? Math.min(1400, Math.max(320, hRaw)) : 640;
    boxWidthInput.value = String(w);
    boxHeightInput.value = String(h);
    document.documentElement.style.setProperty("--worker-box-width", `${w}px`);
    document.documentElement.style.setProperty("--worker-box-height", `${h}px`);
    saveStored("mas.worker_box_width", w);
    saveStored("mas.worker_box_height", h);
  }

  function clampParallel() {
    const raw = parseInt(parallelInput.value || "10", 10);
    const v = Number.isFinite(raw) ? Math.min(32, Math.max(1, raw)) : 10;
    parallelInput.value = String(v);
    return v;
  }

  function getGrid() {
    let grid = document.getElementById("workerGrid");
    if (grid) return grid;
    grid = document.createElement("div");
    grid.id = "workerGrid";
    const section = timeline.closest("section");
    if (section) section.appendChild(grid);
    return grid;
  }

  function ensureCards(count) {
    const n = Math.max(1, count);
    const grid = getGrid();
    const existing = grid.querySelectorAll(".worker-card").length;
    if (existing === n) return grid;
    grid.innerHTML = "";
    for (let i = 1; i <= n; i += 1) {
      const card = document.createElement("div");
      card.className = "worker-card";
      card.dataset.workerSlot = String(i);
      card.innerHTML = `<div class="worker-head"><span>Worker ${i}</span><span class="worker-state">idle</span></div><div class="worker-events"></div>`;
      grid.appendChild(card);
    }
    return grid;
  }

  function setWorkerMode(enabled) {
    const title = timeline.closest("section")?.querySelector("h3");
    const grid = getGrid();
    if (enabled) {
      if (title) title.textContent = "Worker Timelines";
      timeline.style.display = "none";
      grid.style.display = "flex";
    } else {
      if (title) title.textContent = "Node Timeline";
      grid.style.display = "none";
      timeline.style.display = "flex";
    }
  }

  const caseToSlot = new Map();

  function appendContentWithCodeBlocks(root, rawText) {
    const text = String(rawText || "");
    const re = /```([a-zA-Z0-9_-]+)?\\n([\\s\\S]*?)```/g;
    let lastIdx = 0;
    let match = re.exec(text);
    while (match) {
      const start = match.index;
      const full = match[0] || "";
      const lang = String(match[1] || "").trim().toLowerCase();
      const code = String(match[2] || "").replace(/\\s+$/, "");

      if (start > lastIdx) {
        const plain = text.slice(lastIdx, start).trim();
        if (plain) {
          const plainDiv = document.createElement("div");
          plainDiv.className = "text";
          plainDiv.textContent = plain;
          root.appendChild(plainDiv);
        }
      }

      const codeLabel = document.createElement("div");
      codeLabel.className = "code-label";
      codeLabel.textContent = lang ? `code (${lang})` : "code";
      root.appendChild(codeLabel);

      const pre = document.createElement("pre");
      pre.className = "code-box";
      pre.textContent = code || "(empty code block)";
      root.appendChild(pre);

      lastIdx = start + full.length;
      match = re.exec(text);
    }

    const tail = text.slice(lastIdx).trim();
    if (tail || root.children.length === 0) {
      const tailDiv = document.createElement("div");
      tailDiv.className = "text";
      tailDiv.textContent = tail || "(empty)";
      root.appendChild(tailDiv);
    }
  }

  function appendWorkerEvent(payload) {
    if (!payload || typeof payload !== "object") return false;
    const d = payload.data && typeof payload.data === "object" ? payload.data : {};
    const caseId = String(payload.case_id || d.case_id || "");
    const mapped = caseId ? Number(caseToSlot.get(caseId) || 0) : 0;
    const slotRaw = Number(payload.worker_slot || d.worker_slot || mapped || 0);
    const slot = Math.max(1, Number.isFinite(slotRaw) ? slotRaw : 1);

    const wantCards = Math.max(clampParallel(), slot);
    ensureCards(wantCards);
    const grid = getGrid();
    const card = grid.querySelector(`.worker-card[data-worker-slot="${slot}"]`);
    if (!card) return false;
    const events = card.querySelector(".worker-events");
    const badge = card.querySelector(".worker-state");
    if (!events || !badge) return false;

    const isCaseStart = String(payload.label || "").includes("Eval1 Case Start");
    const prevCase = String(events.dataset.currentCase || "");
    if (isCaseStart && caseId && prevCase !== caseId) {
      const divider = document.createElement("div");
      divider.className = "worker-case-divider";
      divider.textContent = `Case Start: ${caseId}`;
      events.appendChild(divider);
    }
    if (caseId) {
      events.dataset.currentCase = caseId;
      caseToSlot.set(caseId, slot);
      badge.textContent = caseId;
    }

    const item = document.createElement("div");
    item.className = "worker-event";
    const label = document.createElement("div");
    label.className = "label";
    label.textContent = String(payload.label || "event");
    item.appendChild(label);
    appendContentWithCodeBlocks(item, payload.content || "");
    events.appendChild(item);
    events.scrollTop = events.scrollHeight;
    return true;
  }

  window.__paHandleNode = function(payload) {
    if (!eval1Mode.checked) return false;
    setWorkerMode(true);
    return appendWorkerEvent(payload);
  };

  parallelInput.addEventListener("change", () => {
    const n = clampParallel();
    if (eval1Mode.checked) ensureCards(n);
  });
  boxWidthInput.addEventListener("change", applyBoxSize);
  boxHeightInput.addEventListener("change", applyBoxSize);

  eval1Mode.addEventListener("change", () => {
    if (eval1Mode.checked) {
      ensureCards(clampParallel());
      setWorkerMode(true);
    } else {
      setWorkerMode(false);
    }
  });

  runBtn.addEventListener("click", () => {
    caseToSlot.clear();
    if (!eval1Mode.checked) {
      setWorkerMode(false);
      return;
    }
    const grid = ensureCards(clampParallel());
    for (const ev of grid.querySelectorAll(".worker-events")) {
      ev.innerHTML = "";
      ev.dataset.currentCase = "";
    }
    for (const badge of grid.querySelectorAll(".worker-state")) {
      badge.textContent = "idle";
    }
    setWorkerMode(true);
  }, true);

  stopBtn.addEventListener("click", () => {
    fetch("/api/stop", { method: "POST" }).catch(() => {});
  }, true);

  boxWidthInput.value = loadStored("mas.worker_box_width", boxWidthInput.value || "560");
  boxHeightInput.value = loadStored("mas.worker_box_height", boxHeightInput.value || "640");
  applyBoxSize();

  if (eval1Mode.checked) {
    ensureCards(clampParallel());
    setWorkerMode(true);
  } else {
    setWorkerMode(false);
  }
})();
</script>
"""
    return html.replace("</body>", addon + "\n</body>")


class ParallelMASWebHandler(base.MASWebHandler):
    server_version = "BiomniMASWebPA/1.0"
    _cancel_lock = threading.Lock()
    _active_cancellations: set[threading.Event] = set()

    @classmethod
    def _register_cancel_event(cls, ev: threading.Event) -> None:
        with cls._cancel_lock:
            cls._active_cancellations.add(ev)

    @classmethod
    def _unregister_cancel_event(cls, ev: threading.Event) -> None:
        with cls._cancel_lock:
            cls._active_cancellations.discard(ev)

    @classmethod
    def _cancel_all_runs(cls) -> int:
        with cls._cancel_lock:
            events = list(cls._active_cancellations)
        for ev in events:
            ev.set()
        return len(events)

    def _send_html(self, html: str) -> None:  # type: ignore[override]
        body = _build_pa_html().encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/stop":
            canceled = self._cancel_all_runs()
            self._send_json({"ok": True, "canceled_runs": canceled})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def _handle_stream(self, raw_query: str) -> None:  # type: ignore[override]
        params = parse_qs(raw_query)
        query = (params.get("query", [""])[0] or "").strip()
        use_sc_raw = (
            (params.get("use_success_criteria", ["1"])[0] or "").strip().lower()
        )
        use_success_criteria = use_sc_raw in {"1", "true", "yes", "on"}
        eval_mode_raw = (params.get("eval1_mode", ["0"])[0] or "").strip().lower()
        eval1_mode = eval_mode_raw in {"1", "true", "yes", "on"}
        eval_limit_raw = (params.get("eval_task_limit", ["3"])[0] or "3").strip()
        eval_split = (params.get("eval_split", ["val"])[0] or "val").strip()
        eval_task_scope = (params.get("eval_task_scope", ["all"])[0] or "all").strip()
        eval_start_task = (params.get("eval_start_task", [""])[0] or "").strip()
        eval_selected_tasks_raw = (
            params.get("eval_selected_tasks", [""])[0] or ""
        ).strip()
        eval_parallelism_raw = (
            params.get("eval_parallelism", ["10"])[0] or "10"
        ).strip()
        eval_selected_tasks = [
            x.strip() for x in eval_selected_tasks_raw.split(",") if x.strip()
        ]
        if eval_task_scope not in {"all", "start_from", "selected"}:
            eval_task_scope = "all"
        try:
            eval_task_limit = max(1, int(eval_limit_raw))
        except ValueError:
            eval_task_limit = 3
        try:
            eval_parallelism = max(1, min(32, int(eval_parallelism_raw)))
        except ValueError:
            eval_parallelism = 10

        if not query and not eval1_mode:
            self._send_json({"error": "query parameter is required"}, status=400)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        def send_event(name: str, payload: dict[str, Any]) -> None:
            msg = (
                f"event: {name}\n"
                + "data: "
                + json.dumps(payload, ensure_ascii=False)
                + "\n\n"
            )
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()

        event_queue: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=512)
        cancel_event = threading.Event()
        self._register_cancel_event(cancel_event)

        def enqueue(item: dict[str, Any]) -> None:
            try:
                event_queue.put_nowait(item)
            except queue.Full:
                try:
                    event_queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    event_queue.put_nowait(item)
                except queue.Full:
                    return

        def on_node_event(payload: dict[str, Any]) -> None:
            enqueue({"type": "node", "payload": payload})

        def run_agent() -> None:
            try:
                if eval1_mode:
                    report = self._run_eval1_mode_parallel(
                        query=query,
                        use_success_criteria=use_success_criteria,
                        eval_task_limit=eval_task_limit,
                        eval_split=eval_split,
                        eval_task_scope=eval_task_scope,
                        eval_start_task=eval_start_task,
                        eval_selected_tasks=eval_selected_tasks,
                        eval_parallelism=eval_parallelism,
                        enqueue=enqueue,
                        cancel_event=cancel_event,
                    )
                    enqueue({"type": "done", "payload": report})
                else:
                    agent = MASAgent(
                        event_callback=on_node_event,
                        use_success_criteria=use_success_criteria,
                    )
                    result = agent.go(query, verbose=True, stream=False)
                    enqueue(
                        {
                            "type": "done",
                            "payload": {
                                "mode": "single",
                                "final_answer": result.get("final_answer", ""),
                                "token_usage_total": result.get(
                                    "token_usage_total", {}
                                ),
                                "current_state": result.get("current_state", ""),
                                "replan_history": result.get("replan_history", []),
                                "query_to_final_ms": result.get("query_to_final_ms", 0),
                                "retry_count": result.get("retry_count", 0),
                                "plan_revision_count": result.get(
                                    "plan_revision_count", 0
                                ),
                                "full_reset_count": result.get("full_reset_count", 0),
                                "step_latency_summary": result.get(
                                    "step_latency_summary", {}
                                ),
                                "use_success_criteria": result.get(
                                    "use_success_criteria", use_success_criteria
                                ),
                            },
                        }
                    )
            except Exception as exc:
                enqueue({"type": "run_error", "payload": {"error": str(exc)}})
            finally:
                enqueue({"type": "eof", "payload": {}})

        try:
            mode = (
                f"eval1(limit={eval_task_limit}, split={eval_split}, parallel={eval_parallelism})"
                if eval1_mode
                else ("criteria" if use_success_criteria else "intent")
            )
            send_event("status", {"message": f"Run started ({mode} mode)"})
            worker = threading.Thread(target=run_agent, daemon=True)
            worker.start()
            while True:
                if cancel_event.is_set():
                    send_event("run_error", {"error": "Run canceled by user"})
                    break
                try:
                    item = event_queue.get(timeout=10)
                except queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                    continue

                item_type = str(item.get("type", ""))
                payload = item.get("payload", {})
                if item_type in {"node", "done", "run_error", "eval_progress"}:
                    payload_dict = payload if isinstance(payload, dict) else {}
                    send_event(item_type, payload_dict)
                    continue
                if item_type == "eof":
                    break
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:
            try:
                send_event("run_error", {"error": str(exc)})
            except Exception:
                return
        finally:
            cancel_event.set()
            self._unregister_cancel_event(cancel_event)

    def _run_eval1_mode_parallel(
        self,
        *,
        query: str,
        use_success_criteria: bool,
        eval_task_limit: int,
        eval_split: str,
        eval_task_scope: str,
        eval_start_task: str,
        eval_selected_tasks: list[str],
        eval_parallelism: int,
        enqueue,
        cancel_event: threading.Event,
    ) -> dict[str, Any]:
        if cancel_event.is_set():
            raise RuntimeError("Run canceled by user")
        del query
        enqueue(
            {
                "type": "node",
                "payload": {
                    "label": "[Eval1 Init]",
                    "content": "Loading Eval1 dataset...",
                    "workflow_state": "EVAL1",
                    "stage": "eval1_init",
                    "token_usage": {},
                    "data": {"parallelism": eval_parallelism},
                },
            }
        )
        evaluator = BiomniEval1()
        instances = evaluator.get_instances(split=eval_split or None)
        if len(instances) == 0:
            raise RuntimeError(f"No Eval1 instances found for split='{eval_split}'")

        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path.cwd() / "eval1_test" / f"run_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        run_config = {
            "mode": "eval1_parallel",
            "split": eval_split,
            "per_task_limit": eval_task_limit,
            "parallelism": eval_parallelism,
            "task_scope": eval_task_scope,
            "start_task": eval_start_task,
            "selected_tasks": eval_selected_tasks,
            "use_success_criteria": use_success_criteria,
            "started_at": dt.datetime.now().isoformat(timespec="seconds"),
        }
        (run_dir / "run_config.json").write_text(
            json.dumps(run_config, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        grouped: dict[str, list[dict[str, Any]]] = {}
        for _, row in instances.iterrows():
            task_name = str(row["task_name"])
            grouped.setdefault(task_name, []).append(
                {
                    "task_name": task_name,
                    "task_instance_id": int(row["task_instance_id"]),
                    "instance_id": int(row["instance_id"]),
                    "prompt": str(row["prompt"]),
                    "answer": row["answer"],
                }
            )

        available_tasks = sorted(grouped)
        task_available_by_name = {
            name: int(len(grouped[name])) for name in available_tasks
        }
        task_filter_text = "all"
        scoped_tasks: list[str] = list(available_tasks)
        if eval_task_scope == "start_from":
            if not eval_start_task:
                raise RuntimeError(
                    "eval_task_scope=start_from requires eval_start_task"
                )
            if eval_start_task not in grouped:
                raise RuntimeError(
                    f"eval_start_task='{eval_start_task}' not found in split='{eval_split}'"
                )
            start_idx = available_tasks.index(eval_start_task)
            scoped_tasks = available_tasks[start_idx:]
            task_filter_text = f"start_from={eval_start_task}"
        elif eval_task_scope == "selected":
            if not eval_selected_tasks:
                raise RuntimeError(
                    "eval_task_scope=selected requires eval_selected_tasks"
                )
            unknown_tasks = [x for x in eval_selected_tasks if x not in grouped]
            if unknown_tasks:
                raise RuntimeError(
                    "Unknown eval_selected_tasks: " + ",".join(unknown_tasks)
                )
            scoped_tasks = []
            seen_tasks: set[str] = set()
            for name in eval_selected_tasks:
                if name in seen_tasks:
                    continue
                seen_tasks.add(name)
                scoped_tasks.append(name)
            task_filter_text = "selected=" + ",".join(scoped_tasks)

        task_effective_limit_by_name = {
            name: int(min(eval_task_limit, task_available_by_name.get(name, 0)))
            for name in scoped_tasks
        }
        selected: list[dict[str, Any]] = []
        for task_name in scoped_tasks:
            if cancel_event.is_set():
                raise RuntimeError("Run canceled by user")
            selected.extend(
                grouped[task_name][: task_effective_limit_by_name[task_name]]
            )
        total = len(selected)
        if total == 0:
            raise RuntimeError("No Eval1 rows selected after per-task limit")

        task_summary: dict[str, dict[str, Any]] = {}
        run_index_rows: list[dict[str, Any]] = []
        completed_cases = 0
        workers = max(1, min(int(eval_parallelism), total))
        worker_slot_lock = threading.Lock()
        worker_slot_by_name: dict[str, int] = {}
        next_worker_slot = 1

        def resolve_worker_slot() -> int:
            nonlocal next_worker_slot
            name = threading.current_thread().name
            with worker_slot_lock:
                slot = worker_slot_by_name.get(name)
                if slot is not None:
                    return slot
                slot = next_worker_slot
                next_worker_slot += 1
                if next_worker_slot > workers:
                    next_worker_slot = 1
                worker_slot_by_name[name] = slot
                return slot

        def build_progress_tasks() -> list[dict[str, Any]]:
            rows: list[dict[str, Any]] = []
            for name in sorted(task_summary):
                entry = task_summary[name]
                lat = [float(x) for x in entry.get("latencies_sec", [])]
                toks = [float(x) for x in entry.get("tokens_total", [])]
                rows.append(
                    {
                        "task_name": name,
                        "executed": int(entry.get("executed", 0)),
                        "effective_limit": int(
                            entry.get("effective_limit", eval_task_limit)
                        ),
                        "available": int(entry.get("available", 0)),
                        "limit": int(entry.get("effective_limit", eval_task_limit)),
                        "correct": int(entry.get("correct", 0)),
                        "partial": int(entry.get("partial", 0)),
                        "incorrect": int(entry.get("incorrect", 0)),
                        "avg_time_sec": self._safe_mean(lat),
                        "std_time_sec": float(statistics.pstdev(lat))
                        if len(lat) > 1
                        else 0.0,
                        "avg_total_tokens": self._safe_mean(toks),
                        "std_total_tokens": float(statistics.pstdev(toks))
                        if len(toks) > 1
                        else 0.0,
                    }
                )
            return rows

        def run_case(idx: int, row: dict[str, Any]) -> dict[str, Any]:
            if cancel_event.is_set():
                raise RuntimeError("Run canceled by user")
            task_name = str(row["task_name"])
            task_instance_id = int(row["task_instance_id"])
            prompt = str(row["prompt"])
            ground_truth = row["answer"]
            case_id = f"{task_name}#{task_instance_id}"
            worker_slot = resolve_worker_slot()
            task_dir = run_dir / task_name
            task_dir.mkdir(parents=True, exist_ok=True)
            case_events: list[dict[str, Any]] = []

            def on_event(payload: dict[str, Any]) -> None:
                if cancel_event.is_set():
                    return
                wrapped = dict(payload)
                wrapped["eval_task_name"] = task_name
                wrapped["eval_task_instance_id"] = task_instance_id
                wrapped["case_id"] = case_id
                wrapped["worker_slot"] = worker_slot
                wrapped_data = wrapped.get("data")
                if not isinstance(wrapped_data, dict):
                    wrapped_data = {}
                wrapped_data["worker_slot"] = worker_slot
                wrapped_data["case_id"] = case_id
                wrapped["data"] = wrapped_data
                case_events.append(wrapped)
                enqueue({"type": "node", "payload": wrapped})

            enqueue(
                {
                    "type": "node",
                    "payload": {
                        "label": "[Eval1 Case Start]",
                        "content": f"task={task_name}, task_instance_id={task_instance_id}, progress={idx}/{total}\nquery={prompt}",
                        "workflow_state": "EVAL1",
                        "stage": "eval1_case_start",
                        "token_usage": {},
                        "data": {
                            "task": task_name,
                            "task_instance_id": task_instance_id,
                            "progress": [idx, total],
                            "query": prompt,
                            "case_id": case_id,
                            "worker_slot": worker_slot,
                        },
                    },
                }
            )

            agent = MASAgent(
                event_callback=on_event, use_success_criteria=use_success_criteria
            )
            agent_query = self._build_eval1_solution_contract_query(prompt)
            run_error = ""
            result: dict[str, Any] = {}
            final_answer_raw = ""
            final_answer = ""
            solution_tag_found = False
            started_at = dt.datetime.now()
            finished_at = started_at
            try:
                case_ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                try:
                    fut = case_ex.submit(agent.go, agent_query, True, False)
                    waited = 0.0
                    poll = 0.5
                    while True:
                        if cancel_event.is_set():
                            fut.cancel()
                            raise RuntimeError("Run canceled by user")
                        try:
                            result = fut.result(timeout=poll)
                            break
                        except concurrent.futures.TimeoutError:
                            waited += poll
                            if waited >= CASE_TIMEOUT_SEC:
                                raise
                finally:
                    case_ex.shutdown(wait=False, cancel_futures=True)
                final_answer_raw = str(result.get("final_answer", ""))
                final_answer, solution_tag_found = self._extract_solution_only(
                    final_answer_raw
                )
                grade, reason = self._classify_eval1_answer(
                    task_name, final_answer, ground_truth
                )
                finished_at = dt.datetime.now()
            except concurrent.futures.TimeoutError:
                run_error = f"case_timeout_{CASE_TIMEOUT_SEC}s"
                grade = "incorrect"
                reason = run_error
                finished_at = dt.datetime.now()
            except RuntimeError as exc:
                if str(exc) == "Run canceled by user":
                    raise
                run_error = str(exc)
                grade = "incorrect"
                reason = f"case_exception: {run_error}"
                finished_at = dt.datetime.now()
            except Exception as exc:
                run_error = str(exc)
                grade = "incorrect"
                reason = f"case_exception: {run_error}"
                finished_at = dt.datetime.now()

            measured_ms = (finished_at - started_at).total_seconds() * 1000.0
            reported_ms = float(result.get("query_to_final_ms", 0) or 0)
            query_to_final_ms = reported_ms if reported_ms > 0 else measured_ms
            latency_sec = query_to_final_ms / 1000.0

            case_payload = {
                "task_name": task_name,
                "task_instance_id": task_instance_id,
                "instance_id": int(row["instance_id"]),
                "prompt": prompt,
                "agent_query": agent_query,
                "ground_truth": ground_truth,
                "final_answer_raw": final_answer_raw,
                "final_answer": final_answer,
                "solution_tag_found": solution_tag_found,
                "grade": grade,
                "grade_reason": reason,
                "run_error": run_error,
                "timestamps": {
                    "query_start_ts": started_at.isoformat(timespec="milliseconds"),
                    "final_answer_ts": finished_at.isoformat(timespec="milliseconds"),
                },
                "metrics": {
                    "query_to_final_ms": query_to_final_ms,
                    "retry_count": int(result.get("retry_count", 0) or 0),
                    "plan_revision_count": int(
                        result.get("plan_revision_count", 0) or 0
                    ),
                    "full_reset_count": int(result.get("full_reset_count", 0) or 0),
                    "case_timeout_sec": CASE_TIMEOUT_SEC,
                },
                "step_latency_summary": result.get("step_latency_summary", {}),
                "events": list(case_events),
            }
            case_stem = f"case_{task_instance_id:04d}"
            case_file = task_dir / f"{case_stem}.py"
            self._write_case_log_py(case_file, case_payload)

            case_summary = {
                "task_name": task_name,
                "task_instance_id": task_instance_id,
                "instance_id": int(row["instance_id"]),
                "query": prompt,
                "final_answer": final_answer,
                "ground_truth": self._coerce_text(ground_truth),
                "grade": grade,
                "grade_reason": reason,
                "query_to_final_ms": query_to_final_ms,
                "query_to_final_sec": latency_sec,
                "run_error": run_error,
                "query_start_ts": started_at.isoformat(timespec="milliseconds"),
                "final_answer_ts": finished_at.isoformat(timespec="milliseconds"),
            }
            (task_dir / f"{case_stem}.summary.json").write_text(
                json.dumps(case_summary, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            execution_trace = {
                "task_name": task_name,
                "task_instance_id": task_instance_id,
                "query": prompt,
                "result_keys": sorted(list(result.keys())),
                "execution_history": result.get("execution_history", []),
                "replan_history": result.get("replan_history", []),
                "state_transition_history": result.get("state_transition_history", []),
                "messages": result.get("messages", []),
                "router_output": result.get("router_output", {}),
            }
            (task_dir / f"{case_stem}.trace.json").write_text(
                json.dumps(execution_trace, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            raw_events_path = task_dir / f"{case_stem}.raw_events.jsonl"
            with raw_events_path.open("w", encoding="utf-8") as fp:
                for ev in case_events:
                    fp.write(json.dumps(ev, ensure_ascii=False) + "\n")

            token_usage_total = result.get("token_usage_total", {})
            token_total = 0
            if isinstance(token_usage_total, dict):
                token_total = int(token_usage_total.get("total", 0) or 0)
                if token_total <= 0:
                    token_total = int(
                        (token_usage_total.get("input", 0) or 0)
                        + (token_usage_total.get("output", 0) or 0)
                    )

            return {
                "task_name": task_name,
                "task_instance_id": task_instance_id,
                "instance_id": int(row["instance_id"]),
                "grade": grade,
                "grade_reason": reason,
                "query": prompt,
                "final_answer": final_answer,
                "ground_truth": self._coerce_text(ground_truth),
                "latency_sec": latency_sec,
                "query_to_final_ms": query_to_final_ms,
                "total_tokens": token_total,
                "case_file": str(case_file.relative_to(run_dir)),
                "summary_file": str(
                    (task_dir / f"{case_stem}.summary.json").relative_to(run_dir)
                ),
                "trace_file": str(
                    (task_dir / f"{case_stem}.trace.json").relative_to(run_dir)
                ),
                "raw_events_file": str(raw_events_path.relative_to(run_dir)),
                "worker_slot": worker_slot,
                "case_id": case_id,
            }

        ex: concurrent.futures.ThreadPoolExecutor | None = None
        try:
            ex = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
            iterator = iter(enumerate(selected, start=1))
            pending: set[concurrent.futures.Future[dict[str, Any]]] = set()
            future_meta: dict[
                concurrent.futures.Future[dict[str, Any]], tuple[int, dict[str, Any]]
            ] = {}

            for _ in range(workers):
                try:
                    idx, row = next(iterator)
                except StopIteration:
                    break
                fut = ex.submit(run_case, idx, row)
                pending.add(fut)
                future_meta[fut] = (idx, row)

            while pending:
                if cancel_event.is_set():
                    for pf in list(pending):
                        pf.cancel()
                    raise RuntimeError("Run canceled by user")

                done, pending = concurrent.futures.wait(
                    pending,
                    timeout=0.5,
                    return_when=concurrent.futures.FIRST_COMPLETED,
                )
                if not done:
                    continue

                for fut in done:
                    future_meta.pop(fut, None)
                    if cancel_event.is_set():
                        raise RuntimeError("Run canceled by user")
                    item = fut.result()
                    completed_cases += 1
                    task_name = str(item["task_name"])
                    summary = task_summary.setdefault(
                        task_name,
                        {
                            "task_name": task_name,
                            "executed": 0,
                            "effective_limit": task_effective_limit_by_name.get(
                                task_name, eval_task_limit
                            ),
                            "available": task_available_by_name.get(task_name, 0),
                            "limit": task_effective_limit_by_name.get(
                                task_name, eval_task_limit
                            ),
                            "correct": 0,
                            "partial": 0,
                            "incorrect": 0,
                            "latencies_sec": [],
                            "tokens_total": [],
                            "cases": [],
                        },
                    )
                    summary["executed"] += 1
                    summary[item["grade"]] += 1
                    summary["latencies_sec"].append(float(item["latency_sec"]))
                    summary["tokens_total"].append(int(item["total_tokens"]))
                    summary["cases"].append(
                        {
                            "task_instance_id": item["task_instance_id"],
                            "instance_id": item["instance_id"],
                            "grade": item["grade"],
                            "grade_reason": item["grade_reason"],
                            "case_file": item["case_file"],
                            "summary_file": item["summary_file"],
                            "trace_file": item["trace_file"],
                            "raw_events_file": item["raw_events_file"],
                            "query_to_final_sec": item["latency_sec"],
                            "total_tokens": item["total_tokens"],
                        }
                    )
                    run_index_rows.append(
                        {
                            "task_name": task_name,
                            "task_instance_id": item["task_instance_id"],
                            "instance_id": item["instance_id"],
                            "grade": item["grade"],
                            "grade_reason": item["grade_reason"],
                            "query_to_final_ms": item["query_to_final_ms"],
                            "query_to_final_sec": item["latency_sec"],
                            "total_tokens": item["total_tokens"],
                            "case_dir": task_name,
                            "summary_file": item["summary_file"],
                            "trace_file": item["trace_file"],
                            "raw_events_file": item["raw_events_file"],
                        }
                    )

                    enqueue(
                        {
                            "type": "eval_progress",
                            "payload": {
                                "split": eval_split,
                                "per_task_limit": eval_task_limit,
                                "parallelism": workers,
                                "task_filter": task_filter_text,
                                "completed_cases": completed_cases,
                                "total_cases": total,
                                "tasks": build_progress_tasks(),
                                "current_status": "completed",
                                "current_task": task_name,
                                "current_task_instance_id": item["task_instance_id"],
                                "current_query": item["query"],
                                "current_grade": item["grade"],
                                "current_reason": item["grade_reason"],
                                "current_final_answer": item["final_answer"],
                                "current_ground_truth": item["ground_truth"],
                                "current_latency_sec": item["latency_sec"],
                            },
                        }
                    )

                    if not cancel_event.is_set():
                        try:
                            next_idx, next_row = next(iterator)
                        except StopIteration:
                            continue
                        next_fut = ex.submit(run_case, next_idx, next_row)
                        pending.add(next_fut)
                        future_meta[next_fut] = (next_idx, next_row)
        finally:
            if ex is not None:
                ex.shutdown(wait=False, cancel_futures=True)

        if cancel_event.is_set():
            raise RuntimeError("Run canceled by user")

        all_tasks: list[dict[str, Any]] = []
        for task_name in sorted(task_summary):
            entry = task_summary[task_name]
            lat = [float(x) for x in entry.get("latencies_sec", [])]
            toks = [float(x) for x in entry.get("tokens_total", [])]
            avg_time = self._safe_mean(lat)
            std_time = float(statistics.pstdev(lat)) if len(lat) > 1 else 0.0
            avg_total_tokens = self._safe_mean(toks)
            std_total_tokens = float(statistics.pstdev(toks)) if len(toks) > 1 else 0.0
            (run_dir / task_name / "task_summary.json").write_text(
                json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            all_tasks.append(
                {
                    "task_name": task_name,
                    "executed": entry["executed"],
                    "effective_limit": entry["effective_limit"],
                    "available": entry["available"],
                    "limit": entry["effective_limit"],
                    "correct": entry["correct"],
                    "partial": entry["partial"],
                    "incorrect": entry["incorrect"],
                    "avg_time_sec": avg_time,
                    "std_time_sec": std_time,
                    "avg_total_tokens": avg_total_tokens,
                    "std_total_tokens": std_total_tokens,
                }
            )

        root_summary = {
            "mode": "eval1_parallel",
            "split": eval_split,
            "per_task_limit": eval_task_limit,
            "parallelism": workers,
            "task_scope": eval_task_scope,
            "start_task": eval_start_task,
            "selected_tasks": eval_selected_tasks,
            "task_filter": task_filter_text,
            "applied_tasks": scoped_tasks,
            "task_count": len(all_tasks),
            "tasks": all_tasks,
        }
        (run_dir / "summary_all_tasks.json").write_text(
            json.dumps(root_summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (run_dir / "run_index.json").write_text(
            json.dumps(
                {
                    "mode": "eval1_parallel",
                    "split": eval_split,
                    "per_task_limit": eval_task_limit,
                    "parallelism": workers,
                    "task_scope": eval_task_scope,
                    "start_task": eval_start_task,
                    "selected_tasks": eval_selected_tasks,
                    "task_filter": task_filter_text,
                    "applied_tasks": scoped_tasks,
                    "started_at": run_config.get("started_at"),
                    "finished_at": dt.datetime.now().isoformat(timespec="seconds"),
                    "cases": run_index_rows,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        lines = [
            f"# Eval1 Parallel Summary ({timestamp})",
            "",
            f"- split: {eval_split}",
            f"- per_task_limit: {eval_task_limit}",
            f"- parallelism: {workers}",
            f"- task_filter: {task_filter_text}",
            f"- output_dir: {run_dir}",
            "",
            "| Task | Executed | Effective | Available | Correct | Partial | Incorrect | Avg ± Std Tokens |",
            "|------|---------:|----------:|----------:|--------:|--------:|----------:|-----------------:|",
        ]
        for item in all_tasks:
            lines.append(
                "| {task_name} | {executed} | {effective_limit} | {available} | {correct} | {partial} | {incorrect} | {avg_tok:.1f} ± {std_tok:.1f} |".format(
                    avg_tok=float(item.get("avg_total_tokens", 0.0)),
                    std_tok=float(item.get("std_total_tokens", 0.0)),
                    **item,
                )
            )
        summary_md = "\n".join(lines) + "\n"
        (run_dir / "summary_all_tasks.md").write_text(summary_md, encoding="utf-8")

        return {
            "mode": "eval1",
            "output_dir": str(run_dir),
            "summary": root_summary,
            "summary_text": summary_md,
            "use_success_criteria": use_success_criteria,
        }


def main() -> None:
    base.load_env_from_repo_root()
    parser = argparse.ArgumentParser(
        description="Run Biomni MAS web monitor (parallel eval)"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ParallelMASWebHandler)
    print(f"Biomni MAS parallel web monitor: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
