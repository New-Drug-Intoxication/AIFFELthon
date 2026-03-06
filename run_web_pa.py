"""Biomni Evaluation Web Monitor — Parallel Worker UI

Extends run_web.py with a multi-worker card view.
Each worker slot shows an independent scrollable card in the browser,
making it easy to watch several tasks run concurrently.

All evaluation logic (EvaluationPipeline, make_agent_factory, BiomniEval1Adapter)
is inherited unchanged from run_web.py — this file only adds UI.

Port : 8083 (default)
Usage: python run_web_pa.py [--host 0.0.0.0] [--port 8083]
"""
from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import ThreadingHTTPServer

import run_web as _base
from run_web import BiomniWebHandler, _BUILD


# ---------------------------------------------------------------------------
# PA HTML — injects worker-card grid into base HTML_PAGE
# ---------------------------------------------------------------------------

_PA_STYLE = """
<style id="pa-style">
  :root {
    --wcard-w: 520px;
    --wcard-h: 600px;
  }
  #workerGrid {
    display: none;
    flex-direction: row;
    flex-wrap: nowrap;
    gap: 10px;
    flex: 1;
    overflow-x: auto;
    overflow-y: hidden;
    align-items: stretch;
  }
  .wcard {
    flex: 0 0 var(--wcard-w);
    width: var(--wcard-w);
    height: var(--wcard-h);
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--panel);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    resize: both;
  }
  .wcard-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 10px;
    border-bottom: 1px solid var(--border);
    font-size: 12px;
    font-weight: 700;
    flex-shrink: 0;
  }
  .wcard-badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 999px;
    background: #e2e8f0;
    color: var(--muted);
    font-weight: 400;
  }
  .wcard-body {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .wcard-event {
    border-left: 3px solid var(--accent);
    padding: 4px 8px;
    font-size: 11px;
    line-height: 1.4;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    word-break: break-word;
  }
  .wcard-event.correct  { border-left-color: var(--correct); }
  .wcard-event.partial  { border-left-color: var(--warn); }
  .wcard-event.incorrect{ border-left-color: var(--err); }
  .wcard-event .ev-title{ font-weight: 700; margin-bottom: 2px; }
</style>
"""

_PA_SCRIPT = """
<script id="pa-script">
(() => {
  // ── Size controls ────────────────────────────────────
  const sidebar    = document.querySelector(".sidebar-inner");
  const ctrlsEl    = document.getElementById("evalControls");
  const wGrid      = document.getElementById("workerGrid");
  const timeline   = document.getElementById("timeline");
  const mainHeader = document.getElementById("mainHeader");

  function addSizeControl(id, label, defaultVal, min, max, step, cssVar) {
    if (document.getElementById(id)) return document.getElementById(id);
    const div = document.createElement("div");
    div.className = "ctrl";
    div.innerHTML = `<label>${label}</label><input type="number" id="${id}"
      value="${defaultVal}" min="${min}" max="${max}" step="${step}"
      style="padding:6px 8px;border:1px solid var(--border);border-radius:8px;font-size:13px;width:100%;background:#f8fafc">`;
    ctrlsEl.appendChild(div);
    const inp = document.getElementById(id);
    inp.addEventListener("change", () => applySize());
    return inp;
  }

  const ls = { get: k => { try { return localStorage.getItem(k) } catch { return null } },
               set: (k,v) => { try { localStorage.setItem(k,String(v)) } catch {} } };

  const wInput = addSizeControl("workerBoxW", "Worker card width (px)",  520, 280, 1400, 20, "--wcard-w");
  const hInput = addSizeControl("workerBoxH", "Worker card height (px)", 600, 240, 1200, 20, "--wcard-h");

  function applySize() {
    const w = Math.min(1400, Math.max(280, parseInt(wInput.value)||520));
    const h = Math.min(1200, Math.max(240, parseInt(hInput.value)||600));
    wInput.value = w; hInput.value = h;
    document.documentElement.style.setProperty("--wcard-w", w+"px");
    document.documentElement.style.setProperty("--wcard-h", h+"px");
    ls.set("bw.wcard_w", w); ls.set("bw.wcard_h", h);
  }

  const savedW = ls.get("bw.wcard_w"); if (savedW) wInput.value = savedW;
  const savedH = ls.get("bw.wcard_h"); if (savedH) hInput.value = savedH;
  applySize();

  // ── Worker card management ───────────────────────────
  const slotMap = new Map(); // slot → { card, body, badge }

  function ensureCard(slot) {
    if (slotMap.has(slot)) return slotMap.get(slot);
    const card = document.createElement("div");
    card.className = "wcard";
    card.innerHTML = `
      <div class="wcard-head">
        <span>Worker ${slot}</span>
        <span class="wcard-badge">idle</span>
      </div>
      <div class="wcard-body"></div>`;
    wGrid.appendChild(card);
    const entry = { card, body: card.querySelector(".wcard-body"), badge: card.querySelector(".wcard-badge") };
    slotMap.set(slot, entry);
    return entry;
  }

  function setWorkerMode(on) {
    if (on) {
      timeline.style.display = "none";
      wGrid.style.display    = "flex";
      mainHeader.textContent = "Worker Timelines";
    } else {
      timeline.style.display = "";
      wGrid.style.display    = "none";
      mainHeader.textContent = "Case Timeline";
    }
  }

  // Pre-create worker cards when parallelism input changes
  const parallelismEl = document.getElementById("parallelism");
  function refreshCards() {
    const n = Math.min(32, Math.max(1, parseInt(parallelismEl.value)||1));
    for (let i = 1; i <= n; i++) ensureCard(i);
  }
  if (parallelismEl) parallelismEl.addEventListener("change", refreshCards);

  // ── Hook: task_start ──────────────────────────────────
  window.__paHandleTaskStart = (p) => {
    const slot = p.worker_slot || 1;
    const { badge } = ensureCard(slot);
    setWorkerMode(true);
    badge.textContent = p.task_name;
    badge.style.background = "#dbeafe";
    badge.style.color = "#1e40af";
  };

  // ── Hook: task_done ───────────────────────────────────
  window.__paHandleTaskDone = (p) => {
    const slot = p.worker_slot || 1;
    if (!slotMap.has(slot)) return;
    const { badge } = slotMap.get(slot);
    badge.textContent = "done";
    badge.style.background = "#dcfce7";
    badge.style.color = "#166534";
  };

  // ── Hook: case_done (intercept from timeline) ─────────
  window.__paHandleCase = (payload) => {
    const slot = payload.worker_slot || 1;
    const { body, badge } = ensureCard(slot);
    setWorkerMode(true);

    badge.textContent = payload.task_name + " #" + payload.instance_id;

    const ev = document.createElement("div");
    ev.className = "wcard-event " + (payload.grade || "incorrect");
    const lines = [
      `${payload.task_name} #${payload.instance_id}`,
      `${payload.grade}  score=${payload.score}  ${payload.latency}s`,
      payload.prompt       ? "Q: " + payload.prompt       : "",
      payload.prediction   ? "A: " + payload.prediction   : "",
      payload.ground_truth ? "GT: "+ payload.ground_truth : "",
      payload.error        ? "Err: "+ payload.error        : "",
    ].filter(Boolean);

    const title = document.createElement("div");
    title.className = "ev-title";
    title.textContent = lines[0];
    ev.appendChild(title);

    const rest = document.createElement("div");
    rest.textContent = lines.slice(1).join("\\n");
    ev.appendChild(rest);

    body.appendChild(ev);
    body.scrollTop = body.scrollHeight;
    return true; // consumed — don't add to main timeline
  };

  // ── Hook: reset on Run ────────────────────────────────
  window.__paResetWorkers = () => {
    const n = Math.min(32, Math.max(1, parseInt(parallelismEl?.value)||1));
    wGrid.innerHTML = "";
    slotMap.clear();
    for (let i = 1; i <= n; i++) ensureCard(i);
    setWorkerMode(true);
  };

  // Init
  setWorkerMode(false);
  refreshCards();
})();
</script>
"""


def _build_pa_html() -> str:
    html = _base.HTML_PAGE
    html = html.replace("Biomni Eval Monitor", "Biomni Eval Monitor (PA)", 1)
    html = html.replace(
        f"build: {_BUILD}",
        f"build: {_BUILD} &nbsp;|&nbsp; PA",
        1,
    )
    html = html.replace("</body>", _PA_STYLE + _PA_SCRIPT + "\n</body>", 1)
    return html


# ---------------------------------------------------------------------------
# Handler — overrides _serve_ui only; all eval logic inherited from base
# ---------------------------------------------------------------------------

class ParallelBiomniWebHandler(BiomniWebHandler):
    server_version = "BiomniWebPA/1.0"

    def _serve_ui(self) -> None:
        body = _build_pa_html().encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    _base.load_env()
    parser = argparse.ArgumentParser(description="Biomni Eval Monitor (Parallel Worker UI)")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8083, help="Bind port (default: 8083)")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), ParallelBiomniWebHandler)
    print(f"Biomni Eval Monitor (PA): http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
