"""Biomni Evaluation Web Monitor

Real-time browser interface for Biomni Eval1 evaluations.
Evaluation logic is identical to biomni/eval/run_eval.py (baseline A1 single-agent).

Architecture:
  - EvaluationPipeline (biomni/eval/pipeline.py)  — unchanged baseline
  - make_agent_factory  (biomni/eval/run_eval.py)  — unchanged baseline
  - BiomniEval1Adapter  (biomni/eval/benchmark.py)  — unchanged baseline
  - _WebSSELogger(BaseLogger)                       — streams results to browser via SSE

Parallelism: task-level (up to N tasks run concurrently; instances within each task
are sequential). Safe because EvaluationPipeline resets the global Python REPL
namespace between instances.

Port : 8082 (default)
Usage: python run_web.py [--host 0.0.0.0] [--port 8082]
"""
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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from biomni.config import default_config
from biomni.eval.benchmark import BiomniEval1Adapter
from biomni.eval.logger import BaseLogger
from biomni.eval.pipeline import EvaluationPipeline
from biomni.eval.run_eval import _normalize_path_for_a1, make_agent_factory

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BUILD = "biomni-web-1.0"

_EVAL1_TASKS: List[str] = [
    "crispr_delivery",
    "gwas_causal_gene_gwas_catalog",
    "gwas_causal_gene_opentargets",
    "gwas_causal_gene_pharmaprojects",
    "gwas_variant_prioritization",
    "lab_bench_dbqa",
    "lab_bench_seqqa",
    "patient_gene_detection",
    "rare_disease_diagnosis",
    "screen_gene_retrieval",
]


# ---------------------------------------------------------------------------
# Env loader
# ---------------------------------------------------------------------------

def load_env() -> None:
    """Load .env from cwd or any parent directory (best effort)."""
    cur = Path.cwd()
    for d in [cur] + list(cur.parents):
        env_file = d / ".env"
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(str(env_file), override=False)
            except Exception:
                pass
            return


def _json_default(value: Any) -> str:
    return str(value)


def _append_jsonl(path: Path, payload: Any) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, default=_json_default) + "\n")


def _write_json_artifact(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )


def _safe_log_name(value: Any) -> str:
    text = str(value or "unknown").strip() or "unknown"
    for sep in (os.sep, os.altsep):
        if sep:
            text = text.replace(sep, "_")
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in text)
    return (safe[:200] or "unknown")


# ---------------------------------------------------------------------------
# SSE logger — replaces SQLiteLogger for the web session
# ---------------------------------------------------------------------------

class _WebSSELogger(BaseLogger):
    """Thread-safe BaseLogger that emits SSE events instead of writing to SQLite.

    Injected into EvaluationPipeline as the `logger` argument.
    Called by EvaluationPipeline._process_instance() after each case completes.
    """

    def __init__(
        self,
        enqueue: Callable[[Dict[str, Any]], None],
        total_cases: int,
        task_available: Dict[str, int],
        run_dir: Optional[Path] = None,
    ) -> None:
        self._enqueue = enqueue
        self._total = total_cases
        self._task_available = task_available
        self._completed = 0
        self._summary: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._run_dir = run_dir
        self._instance_results_path = run_dir / "instance_results.jsonl" if run_dir else None
        self._task_metrics_path = run_dir / "task_metrics.jsonl" if run_dir else None
        self._instances_dir = run_dir / "instances" if run_dir else None
        if self._instances_dir is not None:
            self._instances_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # BaseLogger interface
    # ------------------------------------------------------------------

    def log_config(self, config: Dict[str, Any]) -> None:
        pass  # not needed for SSE session

    def log_result(self, result: Dict[str, Any]) -> None:
        task        = str(result.get("task_name", ""))
        instance_id = str(result.get("instance_id", "-"))
        score       = float(result.get("score", 0.0))
        prediction  = str(result.get("prediction", ""))
        ground_truth = str(result.get("ground_truth", ""))
        prompt      = str(result.get("prompt", ""))
        error       = str(result.get("error") or "")
        latency     = float((result.get("metrics") or {}).get("latency", 0.0))
        token_total = int((result.get("metrics") or {}).get("token_total") or 0)
        worker_slot = int(result.get("_worker_slot", 1))

        grade = "correct" if score >= 1.0 else ("partial" if score > 0.0 else "incorrect")

        with self._lock:
            self._completed += 1
            s = self._summary.setdefault(task, {
                "done": 0, "correct": 0, "partial": 0, "incorrect": 0,
                "latencies": [], "tokens": [],
                "available": self._task_available.get(task, 0),
            })
            s["done"] += 1
            s[grade] += 1
            s["latencies"].append(latency)
            if token_total > 0:
                s["tokens"].append(token_total)
            completed  = self._completed
            tasks_snap = self._build_snapshot()
            self._persist_result_locked(result, worker_slot)

        self._enqueue({
            "type": "case_done",
            "payload": {
                "worker_slot":   worker_slot,
                "task_name":     task,
                "instance_id":   instance_id,
                "grade":         grade,
                "score":         round(score, 4),
                "latency":       round(latency, 1),
                "token_total":   token_total,
                "prompt":        prompt[:400],
                "prediction":    prediction[:400],
                "ground_truth":  ground_truth[:200],
                "error":         error,
                "completed":     completed,
                "total":         self._total,
                "tasks":         tasks_snap,
            },
        })

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        with self._lock:
            self._persist_metrics_locked(metrics, step=step)

    def finish(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_snapshot(self) -> List[Dict[str, Any]]:
        rows = []
        for name in sorted(self._summary):
            s   = self._summary[name]
            lat = s["latencies"]
            tok = s["tokens"]
            rows.append({
                "task_name":   name,
                "done":        s["done"],
                "available":   s["available"],
                "correct":     s["correct"],
                "partial":     s["partial"],
                "incorrect":   s["incorrect"],
                "accuracy":    round(s["correct"] / s["done"], 4) if s["done"] else 0.0,
                "avg_latency": round(sum(lat) / len(lat), 1) if lat else 0.0,
                "std_latency": round(statistics.pstdev(lat), 1) if len(lat) > 1 else 0.0,
                "avg_tokens":  round(sum(tok) / len(tok)) if tok else 0,
                "std_tokens":  round(statistics.pstdev(tok)) if len(tok) > 1 else 0,
            })
        return rows

    def _persist_result_locked(self, result: Dict[str, Any], worker_slot: int) -> None:
        if self._instance_results_path is None or self._instances_dir is None:
            return

        task_name = str(result.get("task_name", "unknown")) or "unknown"
        instance_id = str(result.get("instance_id", "unknown")) or "unknown"
        record = dict(result)
        record["task_name"] = task_name
        record["instance_id"] = instance_id
        record["worker_slot"] = worker_slot
        record["logged_at"] = dt.datetime.now().isoformat(timespec="seconds")
        record.pop("_worker_slot", None)

        _append_jsonl(self._instance_results_path, record)

        task_dir = self._instances_dir / _safe_log_name(task_name)
        task_dir.mkdir(parents=True, exist_ok=True)
        _write_json_artifact(task_dir / f"{_safe_log_name(instance_id)}.json", record)

    def _persist_metrics_locked(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        if self._task_metrics_path is None:
            return

        record = {
            "logged_at": dt.datetime.now().isoformat(timespec="seconds"),
            "step": step,
            "metrics": metrics,
        }
        _append_jsonl(self._task_metrics_path, record)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "completed": self._completed,
                "total":     self._total,
                "tasks":     self._build_snapshot(),
            }


# ---------------------------------------------------------------------------
# Browser UI (HTML)
# ---------------------------------------------------------------------------

_TASK_OPTIONS = "\n".join(
    f'            <label class="opt"><input type="checkbox" value="{t}"><span>{t}</span></label>'
    for t in _EVAL1_TASKS
)

_START_TASK_OPTIONS = "\n".join(
    f'            <option value="{t}">{t}</option>'
    for t in _EVAL1_TASKS
)

HTML_PAGE = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Biomni Eval Monitor</title>
  <style>
    :root {{
      --bg:#f1f5f9; --panel:#fff; --border:#e2e8f0;
      --accent:#0f766e; --accent-light:#ccfbf1;
      --warn:#b45309; --err:#b91c1c;
      --txt:#1e293b; --muted:#64748b;
      --correct:#15803d; --partial:#b45309; --incorrect:#b91c1c;
    }}
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:ui-sans-serif,-apple-system,sans-serif;background:var(--bg);color:var(--txt);min-height:100vh}}
    .layout{{display:grid;grid-template-columns:400px 1fr;height:100vh;overflow:hidden}}
    @media(max-width:860px){{.layout{{grid-template-columns:1fr;grid-template-rows:auto 1fr}}}}

    /* ── Sidebar ─────────────────────────────────────────────── */
    .sidebar{{
      background:var(--panel);border-right:1px solid var(--border);
      display:flex;flex-direction:column;overflow:hidden
    }}
    .sidebar-inner{{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:14px}}
    h1{{font-size:17px;font-weight:700}}
    .subtitle{{font-size:11px;color:var(--muted);margin-top:2px}}

    /* Controls */
    .section{{display:flex;flex-direction:column;gap:8px}}
    .section-title{{font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}}
    .ctrl{{display:flex;flex-direction:column;gap:3px}}
    .ctrl label{{font-size:12px;color:var(--muted)}}
    .ctrl input[type=number],.ctrl input[type=text],.ctrl select{{
      padding:6px 8px;border:1px solid var(--border);border-radius:8px;
      font-size:13px;width:100%;background:#f8fafc
    }}
    .ctrl-row{{display:flex;gap:8px}}
    .ctrl-row .ctrl{{flex:1}}
    .toggle-row{{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500}}
    .toggle-row input[type=checkbox]{{width:16px;height:16px;cursor:pointer;accent-color:var(--accent)}}
    .task-list{{
      max-height:140px;overflow-y:auto;border:1px solid var(--border);
      border-radius:8px;padding:6px 8px;background:#f8fafc
    }}
    .opt{{display:flex;align-items:center;gap:6px;font-size:12px;padding:2px 0}}
    .opt input{{accent-color:var(--accent)}}
    .btns{{display:flex;gap:8px}}
    button{{
      padding:9px 16px;border:none;border-radius:10px;
      font-weight:600;font-size:13px;cursor:pointer;transition:opacity .15s
    }}
    button:hover{{opacity:.85}}
    #runBtn{{background:var(--accent);color:#fff;flex:1}}
    #stopBtn{{background:#e2e8f0;color:var(--txt)}}
    #status{{
      padding:8px 10px;border-radius:8px;font-size:12px;
      background:var(--accent-light);color:#134e4a
    }}
    #status.err{{background:#fee2e2;color:var(--err)}}

    /* Progress table */
    .progress-header{{display:flex;justify-content:space-between;align-items:baseline}}
    .progress-bar-wrap{{height:6px;background:#e2e8f0;border-radius:3px;overflow:hidden}}
    .progress-bar-fill{{height:100%;background:var(--accent);border-radius:3px;transition:width .3s}}
    table{{width:100%;border-collapse:collapse;font-size:11px}}
    th{{text-align:left;padding:4px 6px;color:var(--muted);border-bottom:1px solid var(--border);font-weight:600}}
    td{{padding:4px 6px;border-bottom:1px solid #f1f5f9}}
    .grade-correct{{color:var(--correct);font-weight:600}}
    .grade-partial{{color:var(--partial);font-weight:600}}
    .grade-incorrect{{color:var(--incorrect)}}

    /* Current case */
    .case-box{{
      border:1px solid var(--border);border-radius:10px;padding:10px;
      background:#f8fafc;font-size:12px;display:flex;flex-direction:column;gap:6px
    }}
    .case-label{{font-size:11px;color:var(--muted);font-weight:600}}
    .case-value{{white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;
      max-height:80px;overflow-y:auto;font-size:12px;line-height:1.4}}

    /* ── Main timeline area ───────────────────────────────────── */
    .main{{display:flex;flex-direction:column;overflow:hidden;padding:16px;gap:10px}}
    .main-header{{font-size:14px;font-weight:700;flex-shrink:0}}
    #timeline{{
      flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:8px;
      padding-right:4px
    }}
    .event{{
      border:1px solid var(--border);border-left:4px solid var(--accent);
      border-radius:10px;padding:10px;background:#fff
    }}
    .event.correct{{border-left-color:var(--correct)}}
    .event.partial{{border-left-color:var(--warn)}}
    .event.incorrect{{border-left-color:var(--err)}}
    .event .ev-head{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px}}
    .event .ev-title{{font-weight:700;font-size:12px}}
    .event .ev-meta{{font-size:11px;color:var(--muted)}}
    .event .ev-body{{font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;line-height:1.4}}

    /* Worker grid (used by run_web_pa.py) */
    #workerGrid{{
      display:none;flex-direction:row;flex-wrap:nowrap;gap:10px;
      overflow-x:auto;overflow-y:hidden;flex:1
    }}
  </style>
</head>
<body>
<div class="layout">

  <!-- ── Sidebar ───────────────────────────────────────── -->
  <aside class="sidebar">
    <div class="sidebar-inner">

      <div>
        <h1>Biomni Eval Monitor</h1>
        <div class="subtitle">A1 Single-Agent Baseline &nbsp;|&nbsp; build: {_BUILD}</div>
      </div>

      <!-- Eval1 toggle -->
      <div class="section">
        <div class="section-title">Mode</div>
        <label class="toggle-row">
          <input type="checkbox" id="eval1Mode" checked>
          Eval1 batch evaluation
        </label>
      </div>

      <!-- Controls -->
      <div class="section" id="evalControls">
        <div class="section-title">Settings</div>

        <div class="ctrl-row">
          <div class="ctrl">
            <label>Per-task limit (blank = all)</label>
            <input type="number" id="taskLimit" value="" min="1" max="999" placeholder="all">
          </div>
          <div class="ctrl">
            <label>Split</label>
            <input type="text" id="evalSplit" value="val">
          </div>
        </div>

        <div class="ctrl">
          <label>Parallel workers (task-level)</label>
          <input type="number" id="parallelism" value="1" min="1" max="32">
        </div>

        <div class="ctrl">
          <label>Task scope</label>
          <select id="taskScope">
            <option value="all">All tasks</option>
            <option value="start_from">Start from task</option>
            <option value="selected">Only selected tasks</option>
          </select>
        </div>

        <div class="ctrl" id="startTaskWrap" style="display:none">
          <label>Start from</label>
          <select id="startTask">
            <option value="">-- choose --</option>
{_START_TASK_OPTIONS}
          </select>
        </div>

        <div class="ctrl" id="selectedTasksWrap" style="display:none">
          <label>Selected tasks</label>
          <div class="task-list" id="selectedTasks">
{_TASK_OPTIONS}
          </div>
        </div>
      </div>

      <!-- Buttons + status -->
      <div class="section">
        <div class="btns">
          <button id="runBtn">&#9654; Run</button>
          <button id="stopBtn">&#9632; Stop</button>
        </div>
        <div id="status">Idle</div>
      </div>

      <!-- Progress -->
      <div class="section" id="progressSection" style="display:none">
        <div class="progress-header">
          <span class="section-title">Progress</span>
          <span id="progressText" style="font-size:11px;color:var(--muted)">0 / 0</span>
        </div>
        <div class="progress-bar-wrap"><div class="progress-bar-fill" id="progressFill" style="width:0%"></div></div>
        <table id="taskTable">
          <thead><tr><th>Task</th><th>Done</th><th>OK</th><th>Part</th><th>Fail</th><th>Acc</th><th>Avg(s)</th><th>Avg Tok</th></tr></thead>
          <tbody id="taskTableBody"></tbody>
        </table>
      </div>

      <!-- Current case -->
      <div class="section" id="currentSection" style="display:none">
        <div class="section-title">Last Case</div>
        <div class="case-box">
          <div><span class="case-label">Task / Instance</span>
            <div class="case-value" id="caseId">-</div></div>
          <div><span class="case-label">Grade</span>
            <div class="case-value" id="caseGrade">-</div></div>
          <div><span class="case-label">Prediction</span>
            <div class="case-value" id="casePred">-</div></div>
          <div><span class="case-label">Ground Truth</span>
            <div class="case-value" id="caseGT">-</div></div>
        </div>
      </div>

    </div><!-- /sidebar-inner -->
  </aside>

  <!-- ── Main ──────────────────────────────────────────── -->
  <main class="main">
    <div class="main-header" id="mainHeader">Case Timeline</div>
    <div id="timeline"></div>
    <div id="workerGrid"></div>
  </main>

</div><!-- /layout -->

<script>
(() => {{
  // Elements
  const eval1Mode      = document.getElementById("eval1Mode");
  const evalControls   = document.getElementById("evalControls");
  const taskLimitEl    = document.getElementById("taskLimit");
  const evalSplitEl    = document.getElementById("evalSplit");
  const parallelismEl  = document.getElementById("parallelism");
  const taskScopeEl    = document.getElementById("taskScope");
  const startTaskWrap  = document.getElementById("startTaskWrap");
  const startTaskEl    = document.getElementById("startTask");
  const selTasksWrap   = document.getElementById("selectedTasksWrap");
  const selTasksEl     = document.getElementById("selectedTasks");
  const runBtn         = document.getElementById("runBtn");
  const stopBtn        = document.getElementById("stopBtn");
  const statusEl       = document.getElementById("status");
  const progressSec    = document.getElementById("progressSection");
  const progressText   = document.getElementById("progressText");
  const progressFill   = document.getElementById("progressFill");
  const taskTableBody  = document.getElementById("taskTableBody");
  const currentSec     = document.getElementById("currentSection");
  const caseIdEl       = document.getElementById("caseId");
  const caseGradeEl    = document.getElementById("caseGrade");
  const casePredEl     = document.getElementById("casePred");
  const caseGTEl       = document.getElementById("caseGT");
  const timeline       = document.getElementById("timeline");
  const workerGrid     = document.getElementById("workerGrid");
  const mainHeader     = document.getElementById("mainHeader");

  let es = null;

  // ── Persist settings ──────────────────────────────────
  const ls = {{ get: k => {{ try {{ return localStorage.getItem(k) }} catch {{ return null }} }},
                set: (k,v) => {{ try {{ localStorage.setItem(k,String(v)) }} catch {{}} }} }};

  function restore() {{
    if (ls.get("bw.limit"))      taskLimitEl.value   = ls.get("bw.limit");
    if (ls.get("bw.split"))      evalSplitEl.value   = ls.get("bw.split");
    if (ls.get("bw.parallel"))   parallelismEl.value = ls.get("bw.parallel");
    if (ls.get("bw.scope"))      taskScopeEl.value   = ls.get("bw.scope");
    if (ls.get("bw.start"))      startTaskEl.value   = ls.get("bw.start");
    const saved = ls.get("bw.selected");
    if (saved) {{
      const s = new Set(saved.split(","));
      selTasksEl.querySelectorAll("input").forEach(c => c.checked = s.has(c.value));
    }}
    updateScopeUI();
  }}
  restore();

  // ── Scope UI toggle ───────────────────────────────────
  function updateScopeUI() {{
    startTaskWrap.style.display = taskScopeEl.value === "start_from" ? "" : "none";
    selTasksWrap.style.display  = taskScopeEl.value === "selected"   ? "" : "none";
  }}
  taskScopeEl.addEventListener("change", updateScopeUI);

  // ── Task count refresh ────────────────────────────────
  async function refreshCounts() {{
    const split = (evalSplitEl.value || "val").trim();
    try {{
      const r = await fetch(`/api/eval1_meta?split=${{encodeURIComponent(split)}}`, {{cache:"no-store"}});
      if (!r.ok) return;
      const p = await r.json();
      const counts = p.task_counts || {{}};
      selTasksEl.querySelectorAll("span").forEach(sp => {{
        const t = sp.previousElementSibling?.value;
        if (t) sp.textContent = `${{t}} (${{counts[t] ?? 0}})`;
      }});
      for (const opt of startTaskEl.options) {{
        if (opt.value) opt.textContent = `${{opt.value}} (${{counts[opt.value] ?? 0}})`;
      }}
    }} catch {{}}
  }}
  evalSplitEl.addEventListener("change", refreshCounts);
  refreshCounts();

  // ── Status helper ─────────────────────────────────────
  function setStatus(msg, isErr=false) {{
    statusEl.textContent = msg;
    statusEl.className = isErr ? "err" : "";
  }}

  // ── Progress update ───────────────────────────────────
  function updateProgress(payload) {{
    const {{ completed, total, tasks }} = payload;
    progressSec.style.display = "";
    progressText.textContent = `${{completed}} / ${{total}}`;
    const pct = total > 0 ? Math.round(completed / total * 100) : 0;
    progressFill.style.width = pct + "%";

    // Rebuild task table
    taskTableBody.innerHTML = "";
    for (const t of (tasks || [])) {{
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-size:11px;word-break:break-all">${{t.task_name}}</td>
        <td>${{t.done}}/${{t.available}}</td>
        <td class="grade-correct">${{t.correct}}</td>
        <td class="grade-partial">${{t.partial}}</td>
        <td class="grade-incorrect">${{t.incorrect}}</td>
        <td>${{((t.accuracy || 0) * 100).toFixed(1)}}%</td>
        <td>${{t.avg_latency}}s</td>
        <td>${{t.avg_tokens > 0 ? t.avg_tokens.toLocaleString() : "-"}}</td>`;
      taskTableBody.appendChild(tr);
    }}
  }}

  // ── Current case update ───────────────────────────────
  function updateCurrentCase(payload) {{
    currentSec.style.display = "";
    caseIdEl.textContent    = `${{payload.task_name}} #${{payload.instance_id}}`;
    const grade = payload.grade || "-";
    caseGradeEl.textContent = `${{grade}}  (score=${{payload.score}}, ${{payload.latency}}s${{payload.error ? " | "+payload.error : ""}})`;
    caseGradeEl.className   = "case-value grade-" + grade;
    casePredEl.textContent  = payload.prediction || "-";
    caseGTEl.textContent    = payload.ground_truth || "-";
  }}

  // ── Timeline event ────────────────────────────────────
  function addTimelineEvent(payload) {{
    if (window.__paHandleCase && window.__paHandleCase(payload)) return;
    const grade = payload.grade || "incorrect";
    const div = document.createElement("div");
    div.className = `event ${{grade}}`;
    div.innerHTML = `
      <div class="ev-head">
        <span class="ev-title">${{payload.task_name}} #${{payload.instance_id}}</span>
        <span class="ev-meta">${{grade}} &nbsp; ${{payload.score}} &nbsp; ${{payload.latency}}s</span>
      </div>
      <div class="ev-body">${{[
        payload.prompt        ? "Q: " + payload.prompt       : "",
        payload.prediction    ? "A: " + payload.prediction   : "",
        payload.ground_truth  ? "GT: " + payload.ground_truth: "",
        payload.error         ? "Err: " + payload.error      : "",
      ].filter(Boolean).join("\\n")}}</div>`;
    timeline.appendChild(div);
    timeline.scrollTop = timeline.scrollHeight;
  }}

  // ── Run ───────────────────────────────────────────────
  runBtn.addEventListener("click", () => {{
    if (es) {{ es.close(); es = null; }}

    // Persist settings
    ls.set("bw.limit",    taskLimitEl.value);
    ls.set("bw.split",    evalSplitEl.value);
    ls.set("bw.parallel", parallelismEl.value);
    ls.set("bw.scope",    taskScopeEl.value);
    ls.set("bw.start",    startTaskEl.value);
    const selected = Array.from(selTasksEl.querySelectorAll("input:checked")).map(c => c.value);
    ls.set("bw.selected", selected.join(","));

    // Reset UI
    timeline.innerHTML = "";
    taskTableBody.innerHTML = "";
    progressSec.style.display   = "none";
    currentSec.style.display    = "none";
    progressFill.style.width    = "0%";
    progressText.textContent    = "0 / 0";
    if (window.__paResetWorkers) window.__paResetWorkers();

    setStatus("Connecting...");

    const params = new URLSearchParams({{
      eval_split:         (evalSplitEl.value||"val").trim()||"val",
      eval_parallelism:   String(Math.min(32, Math.max(1, parseInt(parallelismEl.value)||1))),
      eval_task_scope:    taskScopeEl.value||"all",
      eval_start_task:    startTaskEl.value||"",
      eval_selected_tasks: selected.join(","),
    }});
    const rawTaskLimit = String(taskLimitEl.value || "").trim();
    if (rawTaskLimit !== "") {{
      const parsedTaskLimit = parseInt(rawTaskLimit, 10);
      if (Number.isFinite(parsedTaskLimit) && parsedTaskLimit > 0) {{
        params.set("eval_task_limit", String(parsedTaskLimit));
      }}
    }}

    es = new EventSource(`/api/stream?${{params}}`);

    es.addEventListener("status", ev => {{
      const p = JSON.parse(ev.data);
      setStatus(p.message || "Running...");
    }});

    es.addEventListener("case_done", ev => {{
      const p = JSON.parse(ev.data);
      updateProgress(p);
      updateCurrentCase(p);
      addTimelineEvent(p);
    }});

    es.addEventListener("task_start", ev => {{
      const p = JSON.parse(ev.data);
      if (window.__paHandleTaskStart) window.__paHandleTaskStart(p);
    }});

    es.addEventListener("task_done", ev => {{
      const p = JSON.parse(ev.data);
      if (window.__paHandleTaskDone) window.__paHandleTaskDone(p);
    }});

    es.addEventListener("done", ev => {{
      const p = JSON.parse(ev.data);
      setStatus(`Done — output: ${{p.output_dir || "eval1_results"}}`);
      es.close(); es = null;
    }});

    es.addEventListener("run_error", ev => {{
      const p = JSON.parse(ev.data);
      setStatus(p.error || "Run error", true);
      es.close(); es = null;
    }});

    es.onerror = () => {{
      if (es && es.readyState === EventSource.CLOSED) {{
        setStatus("Connection closed", true);
        es = null;
      }}
    }};
  }});

  // ── Stop ──────────────────────────────────────────────
  stopBtn.addEventListener("click", () => {{
    if (es) {{ es.close(); es = null; }}
    fetch("/api/stop", {{method:"POST"}}).catch(()=>{{}});
    setStatus("Stopped");
  }});

}})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class BiomniWebHandler(BaseHTTPRequestHandler):
    server_version = "BiomniWeb/1.0"

    # Class-level cancellation registry (shared across all active runs)
    _cancel_lock: threading.Lock = threading.Lock()
    _active_cancels: set = set()

    @classmethod
    def _register(cls, ev: threading.Event) -> None:
        with cls._cancel_lock:
            cls._active_cancels.add(ev)

    @classmethod
    def _unregister(cls, ev: threading.Event) -> None:
        with cls._cancel_lock:
            cls._active_cancels.discard(ev)

    @classmethod
    def _cancel_all(cls) -> int:
        with cls._cancel_lock:
            evs = list(cls._active_cancels)
        for ev in evs:
            ev.set()
        return len(evs)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._serve_ui()
        elif parsed.path == "/health":
            self._send_json({"ok": True, "build": _BUILD})
        elif parsed.path == "/api/stream":
            self._handle_stream(parsed.query)
        elif parsed.path == "/api/eval1_meta":
            self._handle_meta(parsed.query)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/stop":
            n = self._cancel_all()
            self._send_json({"ok": True, "canceled": n})
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args: Any) -> None:
        pass  # suppress request logging

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    def _serve_ui(self) -> None:
        body = HTML_PAGE.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ------------------------------------------------------------------
    # /api/eval1_meta  — returns task instance counts for the given split
    # ------------------------------------------------------------------

    def _handle_meta(self, raw_query: str) -> None:
        params = parse_qs(raw_query)
        split  = (params.get("split", ["val"])[0] or "val").strip()
        try:
            bm = BiomniEval1Adapter()
            counts: Dict[str, int] = {}
            for task in bm.get_tasks():
                counts[task] = len(bm.get_instances(task, split))
            self._send_json({
                "ok": True, "split": split,
                "total_cases": sum(counts.values()),
                "task_counts": dict(sorted(counts.items())),
            })
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=500)

    # ------------------------------------------------------------------
    # /api/stream  — SSE endpoint
    # ------------------------------------------------------------------

    def _handle_stream(self, raw_query: str) -> None:
        params = parse_qs(raw_query)

        def _p(key: str, default: str = "") -> str:
            return (params.get(key, [default])[0] or default).strip()

        raw_task_limit = _p("eval_task_limit")
        task_limit: Optional[int] = None
        if raw_task_limit:
            try:
                task_limit = max(1, int(raw_task_limit))
            except ValueError:
                task_limit = None
        split       = _p("eval_split", "val") or "val"
        parallelism = max(1, min(32, int(_p("eval_parallelism", "1") or "1")))
        scope       = _p("eval_task_scope", "all")
        start_task  = _p("eval_start_task")
        sel_raw     = _p("eval_selected_tasks")

        if scope not in {"all", "start_from", "selected"}:
            scope = "all"
        selected_tasks = [x.strip() for x in sel_raw.split(",") if x.strip()]

        # Send SSE headers
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        def send_sse(name: str, payload: Any) -> None:
            msg = f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            self.wfile.write(msg.encode("utf-8"))
            self.wfile.flush()

        evq: queue.Queue = queue.Queue(maxsize=2048)
        cancel = threading.Event()
        self._register(cancel)

        def enqueue(item: Dict[str, Any]) -> None:
            try:
                evq.put_nowait(item)
            except queue.Full:
                try:
                    evq.get_nowait()
                    evq.put_nowait(item)
                except queue.Empty:
                    pass

        def bg_worker() -> None:
            try:
                report = self._run_eval1(
                    split=split,
                    task_limit=task_limit,
                    scope=scope,
                    start_task=start_task,
                    selected_tasks=selected_tasks,
                    parallelism=parallelism,
                    enqueue=enqueue,
                    cancel=cancel,
                )
                enqueue({"type": "done", "payload": report})
            except Exception as exc:
                enqueue({"type": "run_error", "payload": {"error": str(exc)}})
            finally:
                enqueue({"type": "_eof", "payload": {}})

        try:
            task_limit_label = "all" if task_limit is None else str(task_limit)
            send_sse(
                "status",
                {
                    "message": (
                        f"Starting eval1 (split={split}, tasks={scope}, "
                        f"parallel={parallelism}, per-task={task_limit_label})"
                    )
                },
            )
            t = threading.Thread(target=bg_worker, daemon=True)
            t.start()

            while True:
                if cancel.is_set():
                    send_sse("run_error", {"error": "Run canceled by user"})
                    break
                try:
                    item = evq.get(timeout=15)
                except queue.Empty:
                    # keep-alive comment
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                    continue

                typ = item.get("type", "")
                pl  = item.get("payload", {})
                if typ in {"case_done", "task_start", "task_done", "done", "run_error", "status"}:
                    send_sse(typ, pl)
                elif typ == "_eof":
                    break

        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as exc:
            try:
                send_sse("run_error", {"error": str(exc)})
            except Exception:
                pass
        finally:
            cancel.set()
            self._unregister(cancel)

    # ------------------------------------------------------------------
    # Core eval runner — uses EvaluationPipeline (identical to run_eval.py)
    # ------------------------------------------------------------------

    def _run_eval1(
        self, *,
        split: str,
        task_limit: Optional[int],
        scope: str,
        start_task: str,
        selected_tasks: List[str],
        parallelism: int,
        enqueue: Callable,
        cancel: threading.Event,
    ) -> Dict[str, Any]:
        """Run Eval1 using the baseline EvaluationPipeline.

        Parallelism is task-level: up to `parallelism` tasks run concurrently,
        each in its own EvaluationPipeline with sequential instances.
        This is safe because EvaluationPipeline.reset_python_repl_namespace()
        runs between instances, and task threads don't share REPL state.
        """
        if cancel.is_set():
            raise RuntimeError("Canceled")

        # ── Resolve task list ────────────────────────────────────────
        bm        = BiomniEval1Adapter()
        available = bm.get_tasks()

        if scope == "start_from":
            if not start_task or start_task not in available:
                raise RuntimeError(f"start_task '{start_task}' not in available tasks")
            scoped = available[available.index(start_task):]
        elif scope == "selected":
            if not selected_tasks:
                raise RuntimeError("scope='selected' requires at least one task")
            unknown = [t for t in selected_tasks if t not in available]
            if unknown:
                raise RuntimeError(f"Unknown tasks: {unknown}")
            seen: set = set()
            scoped = [t for t in selected_tasks if not (t in seen or seen.add(t))]  # type: ignore[func-returns-value]
        else:
            scoped = list(available)

        # ── Count instances ──────────────────────────────────────────
        task_available: Dict[str, int] = {}
        task_effective: Dict[str, int] = {}
        task_limit_label = "all" if task_limit is None else str(task_limit)
        for t in scoped:
            all_inst = bm.get_instances(t, split)
            task_available[t] = len(all_inst)
            task_effective[t] = (
                min(task_limit, len(all_inst))
                if isinstance(task_limit, int)
                else len(all_inst)
            )

        total_cases = sum(task_effective[t] for t in scoped)
        if total_cases == 0:
            raise RuntimeError("No instances found for the selected tasks/split")

        # ── Output directory ─────────────────────────────────────────
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir   = Path.cwd() / "eval1_results" / f"run_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run_config.json").write_text(json.dumps({
            "split":        split,
            "task_limit":   task_limit,
            "task_limit_label": task_limit_label,
            "parallelism":  parallelism,
            "scope":        scope,
            "start_task":   start_task,
            "selected":     selected_tasks,
            "tasks":        scoped,
            "total_cases":  total_cases,
            "started_at":   dt.datetime.now().isoformat(timespec="seconds"),
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        events_path = run_dir / "events.jsonl"
        event_lock = threading.Lock()

        def emit(item: Dict[str, Any]) -> None:
            event_record = {
                "logged_at": dt.datetime.now().isoformat(timespec="seconds"),
                "type": item.get("type", ""),
                "payload": item.get("payload", {}),
            }
            with event_lock:
                _append_jsonl(events_path, event_record)
            enqueue(item)

        emit({"type": "status", "payload": {
            "message": (
                f"Tasks: {scoped} | Total: {total_cases} | "
                f"Parallel: {parallelism} | Per-task: {task_limit_label}"
            ),
        }})

        # ── Shared SSE logger ────────────────────────────────────────
        sse_logger = _WebSSELogger(
            enqueue=emit,
            total_cases=total_cases,
            task_available=task_available,
            run_dir=run_dir,
        )

        # ── Agent factory (identical to run_eval.py) ─────────────────
        a1_path = _normalize_path_for_a1(default_config.path)
        agent_factory = make_agent_factory(
            llm=default_config.llm,
            path=a1_path,
            timeout_seconds=default_config.timeout_seconds,
        )

        # ── Task runner (one EvaluationPipeline per task) ────────────
        workers = max(1, min(parallelism, len(scoped)))

        def run_one_task(task_name: str, slot: int) -> None:
            if cancel.is_set():
                return

            emit({"type": "task_start", "payload": {
                "task_name":   task_name,
                "worker_slot": slot,
                "limit":       task_effective[task_name],
            }})

            # Wrap SSE logger to inject worker_slot into results
            class _SlottedLogger(BaseLogger):
                def log_config(self, c: Any) -> None:       pass
                def log_metrics(self, m: Any, step=None):
                    sse_logger.log_metrics(m, step=step)
                def finish(self) -> None:                   pass
                def log_result(self, result: Dict[str, Any]) -> None:
                    result["_worker_slot"] = slot
                    sse_logger.log_result(result)

            # EvaluationPipeline — exactly as run_eval.py uses it
            pipeline = EvaluationPipeline(
                benchmark=BiomniEval1Adapter(),  # fresh per task-thread
                agent_factory=agent_factory,
                logger=_SlottedLogger(),
                max_instances=task_effective[task_name],
            )
            pipeline.run(tasks=[task_name], split=split)

            emit({"type": "task_done", "payload": {
                "task_name":   task_name,
                "worker_slot": slot,
            }})

        # ── Thread pool ──────────────────────────────────────────────
        task_iter = iter(enumerate(scoped, start=1))
        slots     = list(range(1, workers + 1))
        ex: Optional[concurrent.futures.ThreadPoolExecutor] = None

        try:
            ex = concurrent.futures.ThreadPoolExecutor(max_workers=workers)

            futures: Dict[concurrent.futures.Future, Tuple] = {}
            for slot in slots:
                try:
                    idx, tname = next(task_iter)
                    futures[ex.submit(run_one_task, tname, slot)] = (tname, slot)
                except StopIteration:
                    break

            pending = set(futures)
            while pending:
                if cancel.is_set():
                    for f in pending:
                        f.cancel()
                    raise RuntimeError("Run canceled by user")

                done, pending = concurrent.futures.wait(
                    pending, timeout=0.5,
                    return_when=concurrent.futures.FIRST_COMPLETED,
                )
                for f in done:
                    tname, slot = futures.pop(f)
                    try:
                        f.result()
                    except Exception as exc:
                        emit({"type": "status", "payload": {
                            "message": f"Task {tname} failed: {exc}",
                        }})
                    if not cancel.is_set():
                        try:
                            _, nname = next(task_iter)
                            nf = ex.submit(run_one_task, nname, slot)
                            futures[nf] = (nname, slot)
                            pending.add(nf)
                        except StopIteration:
                            pass
        finally:
            if ex:
                ex.shutdown(wait=False, cancel_futures=True)

        if cancel.is_set():
            raise RuntimeError("Run canceled by user")

        # ── Save summary ─────────────────────────────────────────────
        snap = sse_logger.snapshot()
        summary = {
            "split": split, "task_limit": task_limit, "task_limit_label": task_limit_label, "parallelism": workers,
            "scope": scope, "tasks": scoped, "results": snap["tasks"],
        }
        (run_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8",
        )
        with event_lock:
            _append_jsonl(
                events_path,
                {
                    "logged_at": dt.datetime.now().isoformat(timespec="seconds"),
                    "type": "run_summary",
                    "payload": summary,
                },
            )

        lines = [
            f"# Eval1 Summary  ({timestamp})",
            f"split={split}  per_task_limit={task_limit_label}  parallelism={workers}",
            f"output_dir: {run_dir}", "",
            "| Task | Done | Correct | Partial | Incorrect | Acc | Avg(s) | Avg Tokens |",
            "|------|:----:|:-------:|:-------:|:---------:|:---:|:------:|:----------:|",
        ]
        for t in snap["tasks"]:
            acc = f"{t['accuracy'] * 100:.1f}%"
            avg = f"{t['avg_latency']:.1f}" if t["avg_latency"] else "-"
            avg_tok = f"{t['avg_tokens']:,}" if t.get("avg_tokens") else "-"
            lines.append(f"| {t['task_name']} | {t['done']} | {t['correct']} | {t['partial']} | {t['incorrect']} | {acc} | {avg} | {avg_tok} |")
        md = "\n".join(lines) + "\n"
        (run_dir / "summary.md").write_text(md, encoding="utf-8")

        return {
            "output_dir":   str(run_dir),
            "summary_text": md,
            "results":      snap["tasks"],
            "events_path": str(events_path),
            "instance_results_path": str(run_dir / "instance_results.jsonl"),
            "instances_dir": str(run_dir / "instances"),
            "task_metrics_path": str(run_dir / "task_metrics.jsonl"),
        }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    load_env()
    parser = argparse.ArgumentParser(description="Biomni Evaluation Web Monitor")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8082, help="Bind port (default: 8082)")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), BiomniWebHandler)
    print(f"Biomni Eval Monitor: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
