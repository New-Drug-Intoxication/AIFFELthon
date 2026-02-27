from __future__ import annotations

import argparse
import json
import queue
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from biomni_mas import MASAgent
from biomni_mas.env_loader import load_env_from_repo_root


HTML_PAGE = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Biomni MAS Monitor</title>
  <style>
    :root {
      --bg: #f2f5f9;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --line: #d1d5db;
      --accent: #0f766e;
      --accent-soft: #ccfbf1;
      --danger: #b91c1c;
      --code: #0b1020;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: radial-gradient(circle at top right, #dbeafe 0%, var(--bg) 45%, #eef2ff 100%);
      min-height: 100vh;
    }
    .wrap {
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
      display: grid;
      gap: 16px;
      grid-template-columns: 360px 1fr;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
      padding: 16px;
      min-width: 0;
    }
    h1 { margin: 0 0 8px; font-size: 20px; }
    p { margin: 0; color: var(--muted); }
    textarea {
      width: 100%;
      min-height: 180px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      font-size: 14px;
    }
    .row { display: flex; gap: 8px; margin-top: 10px; }
    button {
      border: 0;
      border-radius: 10px;
      padding: 10px 14px;
      font-weight: 600;
      cursor: pointer;
    }
    #runBtn { background: var(--accent); color: #fff; }
    #stopBtn { background: #e5e7eb; color: #111827; }
    #status {
      margin-top: 8px;
      padding: 8px;
      border-radius: 8px;
      background: var(--accent-soft);
      color: #115e59;
      font-size: 13px;
    }
    #timeline {
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-height: 68vh;
      overflow-y: auto;
      overflow-x: hidden;
      padding-right: 4px;
      min-width: 0;
    }
    .event {
      border: 1px solid var(--line);
      border-left: 4px solid var(--accent);
      border-radius: 10px;
      padding: 10px;
      background: #fff;
      min-width: 0;
    }
    .event .label {
      font-weight: 700;
      font-size: 13px;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .event .meta {
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .event .content {
      margin-top: 8px;
      font-size: 14px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      word-break: break-word;
      line-height: 1.45;
    }
    .event pre {
      margin: 8px 0 0;
      background: var(--code);
      color: #e5e7eb;
      padding: 10px;
      border-radius: 8px;
      overflow-x: auto;
      overflow-y: visible;
      font-size: 12px;
      max-height: none;
      max-width: 100%;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      word-break: break-word;
      line-height: 1.4;
    }
    #finalBox {
      margin-top: 10px;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #fafafa;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      word-break: break-word;
      min-height: 72px;
    }
    .err { color: var(--danger); }
    @media (max-width: 980px) {
      .wrap { grid-template-columns: 1fr; }
      #timeline { max-height: 52vh; }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"card\">
      <h1>Biomni MAS Web Monitor</h1>
      <p>Run query and watch node-level logs in real time.</p>
      <textarea id=\"query\" placeholder=\"Type a query...\">Plan a genomics analysis for variant prioritization</textarea>
      <div class=\"row\">
        <button id=\"runBtn\">Run</button>
        <button id=\"stopBtn\">Stop</button>
      </div>
      <div id=\"status\">Idle</div>
      <h3>Final Answer</h3>
      <div id=\"finalBox\"></div>
    </section>

    <section class=\"card\">
      <h3 style=\"margin-top:0\">Node Timeline</h3>
      <div id=\"timeline\"></div>
    </section>
  </div>

  <script>
    let es = null;
    const runBtn = document.getElementById("runBtn");
    const stopBtn = document.getElementById("stopBtn");
    const q = document.getElementById("query");
    const statusEl = document.getElementById("status");
    const timeline = document.getElementById("timeline");
    const finalBox = document.getElementById("finalBox");

    function setStatus(text, isError = false) {
      statusEl.textContent = text;
      statusEl.className = isError ? "err" : "";
    }

    function addEvent(label, content, meta, dataObj) {
      const div = document.createElement("div");
      div.className = "event";
      const labelDiv = document.createElement("div");
      labelDiv.className = "label";
      labelDiv.textContent = label || "Event";
      div.appendChild(labelDiv);

      if (meta) {
        const metaDiv = document.createElement("div");
        metaDiv.className = "meta";
        metaDiv.textContent = meta;
        div.appendChild(metaDiv);
      }

      const contentDiv = document.createElement("div");
      contentDiv.className = "content";
      contentDiv.textContent = content || "";
      div.appendChild(contentDiv);

      if (dataObj) {
        const pre = document.createElement("pre");
        pre.textContent = JSON.stringify(dataObj, null, 2);
        div.appendChild(pre);
      }
      timeline.appendChild(div);
      timeline.scrollTop = timeline.scrollHeight;
    }

    function closeStream() {
      if (es) {
        es.close();
        es = null;
      }
    }

    runBtn.addEventListener("click", () => {
      const query = q.value.trim();
      if (!query) {
        setStatus("Query is empty", true);
        return;
      }
      closeStream();
      timeline.innerHTML = "";
      finalBox.textContent = "";
      setStatus("Running...");

      es = new EventSource(`/api/stream?query=${encodeURIComponent(query)}`);

      es.addEventListener("status", (ev) => {
        const payload = JSON.parse(ev.data);
        setStatus(payload.message || "Running...");
      });

      es.addEventListener("node", (ev) => {
        const payload = JSON.parse(ev.data);
        const tok = payload.token_usage || {};
        const inTok = tok.input || 0;
        const outTok = tok.output || 0;
        const totalTok = tok.total || (inTok + outTok);
        const meta = `workflow=${payload.workflow_state || "-"}, stage=${payload.stage || "-"}, tokens(in/out/total)=${inTok}/${outTok}/${totalTok}`;
        addEvent(payload.label || "Event", payload.content || "", meta, payload.data || null);
      });

      es.addEventListener("done", (ev) => {
        const payload = JSON.parse(ev.data);
        finalBox.textContent = payload.final_answer || "";
        setStatus("Completed");
        closeStream();
      });

      es.addEventListener("error", (ev) => {
        try {
          const payload = JSON.parse(ev.data);
          setStatus(payload.error || "Execution error", true);
        } catch (_e) {
          setStatus("Connection closed", true);
        }
        closeStream();
      });
    });

    stopBtn.addEventListener("click", () => {
      closeStream();
      setStatus("Stopped");
    });
  </script>
</body>
</html>
"""


class MASWebHandler(BaseHTTPRequestHandler):
    server_version = "BiomniMASWeb/1.0"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(HTML_PAGE)
            return
        if parsed.path == "/health":
            self._send_json({"ok": True})
            return
        if parsed.path == "/api/stream":
            self._handle_stream(parsed.query)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def log_message(self, format: str, *args: Any) -> None:
        del format, args

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_stream(self, raw_query: str) -> None:
        params = parse_qs(raw_query)
        query = (params.get("query", [""])[0] or "").strip()
        if not query:
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

        event_queue: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=256)

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
                agent = MASAgent(event_callback=on_node_event)
                result = agent.go(query, verbose=True, stream=False)
                enqueue(
                    {
                        "type": "done",
                        "payload": {
                            "final_answer": result.get("final_answer", ""),
                            "token_usage_total": result.get("token_usage_total", {}),
                            "current_state": result.get("current_state", ""),
                            "replan_history": result.get("replan_history", []),
                            "query_to_final_ms": result.get("query_to_final_ms", 0),
                            "retry_count": result.get("retry_count", 0),
                            "plan_revision_count": result.get("plan_revision_count", 0),
                            "full_reset_count": result.get("full_reset_count", 0),
                            "step_latency_summary": result.get(
                                "step_latency_summary", {}
                            ),
                        },
                    }
                )
            except Exception as exc:
                enqueue({"type": "error", "payload": {"error": str(exc)}})
            finally:
                enqueue({"type": "eof", "payload": {}})

        try:
            send_event("status", {"message": "Run started"})
            worker = threading.Thread(target=run_agent, daemon=True)
            worker.start()
            while True:
                try:
                    item = event_queue.get(timeout=10)
                except queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                    continue

                item_type = str(item.get("type", ""))
                payload = item.get("payload", {})
                if item_type == "node":
                    send_event("node", payload if isinstance(payload, dict) else {})
                    continue
                if item_type == "done":
                    send_event("done", payload if isinstance(payload, dict) else {})
                    continue
                if item_type == "error":
                    send_event("error", payload if isinstance(payload, dict) else {})
                    continue
                if item_type == "eof":
                    break
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:
            try:
                send_event("error", {"error": str(exc)})
            except Exception:
                return


def main() -> None:
    load_env_from_repo_root()
    parser = argparse.ArgumentParser(description="Run Biomni MAS web monitor")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), MASWebHandler)
    print(f"Biomni MAS web monitor: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
