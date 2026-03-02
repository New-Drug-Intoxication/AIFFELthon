from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
import queue
import re
import statistics
import threading
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from biomni_mas import MASAgent
from biomni_mas.env_loader import load_env_from_repo_root
from biomni_mas.eval import BiomniEval1, normalize_answer_for_task


UI_BUILD_ID = "2026-03-01-04"


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
      width: 100%;
      max-width: 1800px;
      margin: 0 auto;
      padding: 24px;
      display: grid;
      gap: 16px;
      grid-template-columns: minmax(420px, 34%) 1fr;
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
      max-height: 92vh;
      min-height: 72vh;
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
      max-height: 30vh;
      overflow: auto;
    }
    #evalSummary {
      margin-top: 10px;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #f8fafc;
      font-size: 13px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      word-break: break-word;
      max-height: 26vh;
      overflow: auto;
    }
    #evalControls {
      display: flex;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 6px;
      padding: 0;
      border: 0;
      opacity: 1;
      transition: opacity 0.15s ease;
    }
    #evalControls .control {
      display: flex;
      align-items: center;
      gap: 6px;
      flex: 1 1 240px;
      min-width: 0;
    }
    #evalControls .control.col {
      align-items: flex-start;
      flex-direction: column;
    }
    #evalControls label {
      min-width: 0 !important;
      flex-shrink: 0;
    }
    #evalControls input[type="number"],
    #evalControls input[type="text"],
    #evalControls select {
      width: 100%;
      min-width: 0;
    }
    #evalSelectedTasks {
      width: 100%;
      min-width: 0;
      max-height: 180px;
      overflow: auto;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      padding: 6px 8px;
      background: #fff;
    }
    #evalSelectedTasks .opt {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      margin: 2px 0;
    }
    #evalControls.off {
      opacity: 0.55;
      pointer-events: none;
    }
    #evalCurrent {
      margin-top: 10px;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #f8fafc;
      font-size: 13px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      word-break: break-word;
      max-height: 24vh;
      overflow: auto;
    }
    .err { color: var(--danger); }
    @media (max-width: 980px) {
      .wrap { grid-template-columns: 1fr; }
      #timeline {
        max-height: 60vh;
        min-height: 46vh;
      }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"card\">
      <h1>Biomni MAS Web Monitor</h1>
      <p style="margin:4px 0 8px; font-size:12px; color:#6b7280;">UI build: 2026-03-01-04</p>
      <p>Run query and watch node-level logs in real time.</p>
      <textarea id=\"query\" placeholder=\"Type a query...\">Plan a genomics analysis for variant prioritization</textarea>
      <div class=\"row\">
        <button id=\"runBtn\" type=\"button\">Run</button>
        <button id=\"stopBtn\" type=\"button\">Stop</button>
      </div>
      <div style=\"margin-top:8px; font-size:13px; color:#374151;\">
        <label style=\"display:flex; align-items:center; gap:8px;\">
          <input id=\"useSC\" type=\"checkbox\" checked />
          Use success_criteria verification
        </label>
        <label style=\"display:flex; align-items:center; gap:8px; margin-top:6px;\">
          <input id=\"eval1Mode\" type=\"checkbox\" />
          Eval1 mode (task-wise batch)
        </label>
        <fieldset id=\"evalControls\" disabled>
          <div class=\"control\">
            <label for=\"evalTaskLimit\">Per-task limit</label>
            <input id=\"evalTaskLimit\" type=\"number\" min=\"1\" value=\"3\" disabled style=\"padding:6px 8px; border:1px solid #d1d5db; border-radius:8px;\" />
          </div>
          <div class=\"control\">
            <label for=\"evalSplit\">Split</label>
            <input id=\"evalSplit\" type=\"text\" value=\"val\" disabled style=\"padding:6px 8px; border:1px solid #d1d5db; border-radius:8px;\" />
            <span style=\"color:#6b7280; font-size:12px;\">val only</span>
          </div>
          <div class=\"control\">
            <label for=\"evalTaskScope\">Task scope</label>
            <select id=\"evalTaskScope\" disabled style=\"padding:6px 8px; border:1px solid #d1d5db; border-radius:8px;\">
              <option value=\"all\">All tasks</option>
              <option value=\"start_from\">Start from task</option>
              <option value=\"selected\">Only selected tasks</option>
            </select>
          </div>
          <div class=\"control\">
            <label for=\"evalStartTask\">Start task</label>
            <select id=\"evalStartTask\" disabled style=\"padding:6px 8px; border:1px solid #d1d5db; border-radius:8px;\">
              <option value=\"\">-- choose task --</option>
              <option value=\"crispr_delivery\">crispr_delivery</option>
              <option value=\"gwas_causal_gene_gwas_catalog\">gwas_causal_gene_gwas_catalog</option>
              <option value=\"gwas_causal_gene_opentargets\">gwas_causal_gene_opentargets</option>
              <option value=\"gwas_causal_gene_pharmaprojects\">gwas_causal_gene_pharmaprojects</option>
              <option value=\"gwas_variant_prioritization\">gwas_variant_prioritization</option>
              <option value=\"lab_bench_dbqa\">lab_bench_dbqa</option>
              <option value=\"lab_bench_seqqa\">lab_bench_seqqa</option>
              <option value=\"patient_gene_detection\">patient_gene_detection</option>
              <option value=\"rare_disease_diagnosis\">rare_disease_diagnosis</option>
              <option value=\"screen_gene_retrieval\">screen_gene_retrieval</option>
            </select>
          </div>
          <div class=\"control col\">
            <label for=\"evalSelectedTasks\">Selected tasks (click to toggle)</label>
            <div id=\"evalSelectedTasks\" aria-label=\"Selected tasks\">
              <label class=\"opt\"><input type=\"checkbox\" value=\"crispr_delivery\" /><span data-task=\"crispr_delivery\">crispr_delivery</span></label>
              <label class=\"opt\"><input type=\"checkbox\" value=\"gwas_causal_gene_gwas_catalog\" /><span data-task=\"gwas_causal_gene_gwas_catalog\">gwas_causal_gene_gwas_catalog</span></label>
              <label class=\"opt\"><input type=\"checkbox\" value=\"gwas_causal_gene_opentargets\" /><span data-task=\"gwas_causal_gene_opentargets\">gwas_causal_gene_opentargets</span></label>
              <label class=\"opt\"><input type=\"checkbox\" value=\"gwas_causal_gene_pharmaprojects\" /><span data-task=\"gwas_causal_gene_pharmaprojects\">gwas_causal_gene_pharmaprojects</span></label>
              <label class=\"opt\"><input type=\"checkbox\" value=\"gwas_variant_prioritization\" /><span data-task=\"gwas_variant_prioritization\">gwas_variant_prioritization</span></label>
              <label class=\"opt\"><input type=\"checkbox\" value=\"lab_bench_dbqa\" /><span data-task=\"lab_bench_dbqa\">lab_bench_dbqa</span></label>
              <label class=\"opt\"><input type=\"checkbox\" value=\"lab_bench_seqqa\" /><span data-task=\"lab_bench_seqqa\">lab_bench_seqqa</span></label>
              <label class=\"opt\"><input type=\"checkbox\" value=\"patient_gene_detection\" /><span data-task=\"patient_gene_detection\">patient_gene_detection</span></label>
              <label class=\"opt\"><input type=\"checkbox\" value=\"rare_disease_diagnosis\" /><span data-task=\"rare_disease_diagnosis\">rare_disease_diagnosis</span></label>
              <label class=\"opt\"><input type=\"checkbox\" value=\"screen_gene_retrieval\" /><span data-task=\"screen_gene_retrieval\">screen_gene_retrieval</span></label>
            </div>
          </div>
        </fieldset>
      </div>
      <div id=\"status\">Idle</div>
      <h3>Eval1 Progress</h3>
      <div id=\"evalSummary\">Eval1 mode is off.</div>
      <h3>Current Eval1 Case</h3>
      <div id=\"evalCurrent\">Eval1 mode is off.</div>
      <h3>Final Answer</h3>
      <div id=\"finalBox\"></div>
    </section>

    <section class=\"card\">
      <h3 style=\"margin-top:0\">Node Timeline</h3>
      <div id=\"timeline\"></div>
    </section>
  </div>

  <script>
    (() => {
    const bootStatusEl = document.getElementById("status");
    function bootFail(err) {
      const msg = (err && err.message) ? err.message : String(err || "unknown");
      if (bootStatusEl) {
        bootStatusEl.textContent = `UI init error: ${msg}`;
        bootStatusEl.className = "err";
      }
      try {
        console.error("MAS Web UI init failed", err);
      } catch (_e) {
        return;
      }
    }

    try {
    let es = null;
    let streamActive = false;
    let streamTerminal = false;
    const runBtn = document.getElementById("runBtn");
    const stopBtn = document.getElementById("stopBtn");
    const q = document.getElementById("query");
    const statusEl = document.getElementById("status");
    const timeline = document.getElementById("timeline");
    const finalBox = document.getElementById("finalBox");
    const evalSummary = document.getElementById("evalSummary");
    const evalCurrent = document.getElementById("evalCurrent");
    const useSC = document.getElementById("useSC");
    const eval1Mode = document.getElementById("eval1Mode");
    const evalControls = document.getElementById("evalControls");
    const evalTaskLimit = document.getElementById("evalTaskLimit");
    const evalSplit = document.getElementById("evalSplit");
    const evalTaskScope = document.getElementById("evalTaskScope");
    const evalStartTask = document.getElementById("evalStartTask");
    const evalSelectedTasks = document.getElementById("evalSelectedTasks");
    if (!runBtn || !stopBtn || !q || !statusEl || !timeline || !finalBox || !evalSummary || !evalCurrent || !useSC || !eval1Mode || !evalControls || !evalTaskLimit || !evalSplit || !evalTaskScope || !evalStartTask || !evalSelectedTasks) {
      throw new Error("UI element binding failed");
    }
    function getStored(key) {
      try {
        return localStorage.getItem(key);
      } catch (_e) {
        return null;
      }
    }

    function setStored(key, value) {
      try {
        localStorage.setItem(key, value);
      } catch (_e) {
        return;
      }
    }

    function setSelectedTaskValues(values) {
      const selected = new Set(Array.isArray(values) ? values : []);
      const boxes = Array.from(
        evalSelectedTasks.querySelectorAll('input[type="checkbox"]')
      );
      for (const cb of boxes) {
        cb.checked = selected.has(String(cb.value || ""));
      }
    }

    function getSelectedTaskValues() {
      return Array.from(
        evalSelectedTasks.querySelectorAll('input[type="checkbox"]:checked')
      )
        .map((x) => String(x.value || "").trim())
        .filter(Boolean);
    }

    async function refreshEvalTaskCounts() {
      const split = (evalSplit.value || "val").trim() || "val";
      let payload = null;
      try {
        const resp = await fetch(`/api/eval1_meta?split=${encodeURIComponent(split)}`, {
          cache: "no-store",
        });
        if (!resp.ok) {
          return;
        }
        payload = await resp.json();
      } catch (_e) {
        return;
      }
      if (!payload || typeof payload !== "object") {
        return;
      }
      const counts = (payload.task_counts && typeof payload.task_counts === "object")
        ? payload.task_counts
        : {};
      for (const span of Array.from(evalSelectedTasks.querySelectorAll("span[data-task]"))) {
        const task = String(span.getAttribute("data-task") || "");
        const n = Number(counts[task] || 0);
        span.textContent = `${task} (${n})`;
      }
      for (const opt of Array.from(evalStartTask.options || [])) {
        const task = String(opt.value || "");
        if (!task) {
          continue;
        }
        const n = Number(counts[task] || 0);
        opt.textContent = `${task} (${n})`;
      }
    }

    const savedUseSC = getStored("mas.use_success_criteria");
    if (savedUseSC === "0") {
      useSC.checked = false;
    }
    const savedEval1Mode = getStored("mas.eval1_mode");
    if (savedEval1Mode === "1") {
      eval1Mode.checked = true;
    }
    const savedEvalTaskLimit = getStored("mas.eval1_task_limit");
    if (savedEvalTaskLimit) {
      evalTaskLimit.value = savedEvalTaskLimit;
    }
    const savedEvalSplit = getStored("mas.eval1_split");
    if (savedEvalSplit) {
      evalSplit.value = savedEvalSplit;
    }
    const savedEvalTaskScope = getStored("mas.eval1_task_scope");
    if (savedEvalTaskScope) {
      evalTaskScope.value = savedEvalTaskScope;
    }
    const savedEvalStartTask = getStored("mas.eval1_start_task");
    if (savedEvalStartTask) {
      evalStartTask.value = savedEvalStartTask;
    }
    const savedEvalSelectedTasks = getStored("mas.eval1_selected_tasks");
    if (savedEvalSelectedTasks) {
      setSelectedTaskValues(
        String(savedEvalSelectedTasks)
          .split(",")
          .map((x) => x.trim())
          .filter(Boolean)
      );
    }

    function setScopeDependentControlsEnabled(enabled) {
      const scope = String(evalTaskScope.value || "all");
      evalStartTask.disabled = !enabled || scope !== "start_from";
      const selectedEnabled = enabled && scope === "selected";
      const boxes = Array.from(
        evalSelectedTasks.querySelectorAll('input[type="checkbox"]')
      );
      for (const cb of boxes) {
        cb.disabled = !selectedEnabled;
      }
      evalSelectedTasks.style.opacity = selectedEnabled ? "1" : "0.6";
    }

    function setEval1ControlsEnabled(enabled) {
      evalControls.disabled = !enabled;
      evalTaskLimit.disabled = !enabled;
      evalSplit.disabled = !enabled;
      evalTaskScope.disabled = !enabled;
      setScopeDependentControlsEnabled(enabled);
      evalControls.classList.toggle("off", !enabled);
      if (!enabled) {
        evalCurrent.textContent = "Eval1 mode is off.";
      }
    }
    setEval1ControlsEnabled(eval1Mode.checked);
    eval1Mode.addEventListener("change", () => {
      setEval1ControlsEnabled(eval1Mode.checked);
    });
    evalTaskScope.addEventListener("change", () => {
      setScopeDependentControlsEnabled(eval1Mode.checked);
    });
    evalSplit.addEventListener("change", () => {
      refreshEvalTaskCounts();
    });
    refreshEvalTaskCounts();

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

      function firstLine(text) {
        return String(text || "")
          .split("\\n")
          .map((x) => x.trim())
          .filter(Boolean)[0] || "";
      }

      function summarizeEvent(labelText, contentText, data) {
        const l = String(labelText || "");
        const c = firstLine(contentText);
        if (l.includes("Router")) {
          const selected = Array.isArray(data?.selected_agents) ? data.selected_agents.join(", ") : "-";
          return `Route selected: ${selected || "-"} · act_required=${data?.act_required === true ? "yes" : "no"}`;
        }
        if (l.includes("Plan-R2") || l.includes("Plan-R3") || l.includes("Orchestrator")) {
          return c || "Planning update";
        }
        if (l.includes("Execution-R1")) {
          return c.replace(/^Executing:\\s*/i, "") || "Step execution started";
        }
        if (l.includes("Execution-R2") || l.includes("Verifier")) {
          const s = data?.status || "";
          const r = data?.reason || c;
          return `Verifier: ${s || "UNKNOWN"}${r ? ` · ${r}` : ""}`;
        }
        if (l.includes("Synthesizer")) {
          return c || "Final synthesis";
        }
        if (l.includes("Eval1")) {
          return c || "Eval1 event";
        }
        return c || "Event";
      }

      const rawContent = String(content || "");
      const visibleContent =
        String(label || "").includes("Synthesizer")
          ? rawContent
          : rawContent.replace(/<solution>[\\s\\S]*?<\\/solution>/gi, "").trim();
      const isExecR1 = String(label || "").includes("Execution-R1");
      let mainContent = visibleContent;
      let execCodeFromContent = "";
      if (isExecR1) {
        const marker = "\\nexecuted_code\\n";
        const markerIdx = rawContent.indexOf(marker);
        if (markerIdx >= 0) {
          mainContent = rawContent.slice(0, markerIdx).trim();
          execCodeFromContent = rawContent.slice(markerIdx + marker.length).trim();
        }
      }
      const summary = summarizeEvent(label, content, dataObj);
      const contentDiv = document.createElement("div");
      contentDiv.className = "content";
      // Never hide server-provided message text from users.
      contentDiv.textContent = mainContent || summary;
      div.appendChild(contentDiv);

      if (String(label || "").includes("Eval1 Case Start")) {
        const qText =
          (dataObj && typeof dataObj === "object" && dataObj.query)
            ? String(dataObj.query)
            : "";
        if (qText) {
          const qDiv = document.createElement("div");
          qDiv.className = "content";
          qDiv.textContent = `Query: ${qText}`;
          div.appendChild(qDiv);
        }
      }

      if (isExecR1) {
        const codeText =
          execCodeFromContent
            ? execCodeFromContent
            : (
                (dataObj && typeof dataObj === "object" && dataObj.executed_code)
                  ? String(dataObj.executed_code)
                  : ""
              );
        if (codeText) {
          const codeTitle = document.createElement("div");
          codeTitle.className = "meta";
          codeTitle.textContent = "executed_code";
          div.appendChild(codeTitle);
          const pre = document.createElement("pre");
          pre.textContent = codeText;
          div.appendChild(pre);
        }
      }

      timeline.appendChild(div);
      timeline.scrollTop = timeline.scrollHeight;
    }

    function closeStream() {
      if (es) {
        es.close();
        es = null;
      }
      streamActive = false;
    }

    function renderEvalProgress(payload) {
      if (!payload || typeof payload !== "object") {
        return;
      }
      const lines = [];
      lines.push(`Progress: ${payload.completed_cases || 0}/${payload.total_cases || 0}`);
      lines.push(`Split: ${payload.split || "-"} · Per-task limit: ${payload.per_task_limit || "-"}`);
      lines.push(`Task filter: ${payload.task_filter || "all"}`);
      lines.push("");
      lines.push("Task | Executed/Effective | Available | Correct | Partial | Incorrect | Avg ± Std Time(s) | Avg ± Std Tokens");
      lines.push("-----|--------------------|-----------|---------|---------|-----------|------------------|------------------");
      const tasks = Array.isArray(payload.tasks) ? payload.tasks : [];
      for (const t of tasks) {
        const avgTime = Number.isFinite(t.avg_time_sec) ? t.avg_time_sec.toFixed(2) : "-";
        const stdTime = Number.isFinite(t.std_time_sec) ? t.std_time_sec.toFixed(2) : "-";
        const avgTok = Number.isFinite(t.avg_total_tokens) ? t.avg_total_tokens.toFixed(1) : "-";
        const stdTok = Number.isFinite(t.std_total_tokens) ? t.std_total_tokens.toFixed(1) : "-";
        const effective = Number.isFinite(t.effective_limit) ? t.effective_limit : t.limit;
        const available = Number.isFinite(t.available) ? t.available : "-";
        lines.push(
          `${t.task_name} | ${t.executed}/${effective} | ${available} | ${t.correct} | ${t.partial} | ${t.incorrect} | ${avgTime} ± ${stdTime} | ${avgTok} ± ${stdTok}`
        );
      }
      evalSummary.textContent = lines.join("\\n");
    }

    function renderEvalCurrent(payload) {
      if (!payload || typeof payload !== "object") {
        return;
      }
      const lines = [];
      const status = payload.current_status || "-";
      lines.push(`Status: ${status}`);
      lines.push(`Task: ${payload.current_task || "-"}`);
      lines.push(`Task Instance ID: ${payload.current_task_instance_id || "-"}`);
      if (payload.current_grade) {
        lines.push(`Grade: ${payload.current_grade}`);
      }
      if (payload.current_reason) {
        lines.push(`Reason: ${payload.current_reason}`);
      }
      if (payload.current_latency_sec !== undefined && payload.current_latency_sec !== null) {
        lines.push(`Latency (s): ${Number(payload.current_latency_sec).toFixed(3)}`);
      }
      lines.push("");
      lines.push("Current Query:");
      lines.push(payload.current_query || "-");
      if (payload.current_final_answer || payload.current_ground_truth) {
        lines.push("");
        lines.push("Synthesizer Final Answer:");
        lines.push(payload.current_final_answer || "-");
        lines.push("");
        lines.push("Ground Truth:");
        lines.push(payload.current_ground_truth || "-");
      }
      evalCurrent.textContent = lines.join("\\n");
    }

    runBtn.addEventListener("click", () => {
      const query = q.value.trim();
      if (!query && !eval1Mode.checked) {
        setStatus("Query is empty", true);
        return;
      }
      closeStream();
      streamTerminal = false;
      timeline.innerHTML = "";
      finalBox.textContent = "";
      evalSummary.textContent = eval1Mode.checked ? "Eval1 run initializing..." : "Eval1 mode is off.";
      evalCurrent.textContent = eval1Mode.checked ? "Waiting for first Eval1 case..." : "Eval1 mode is off.";
      setStored("mas.use_success_criteria", useSC.checked ? "1" : "0");
      setStored("mas.eval1_mode", eval1Mode.checked ? "1" : "0");
      setStored("mas.eval1_task_limit", String(evalTaskLimit.value || "3"));
      setStored("mas.eval1_split", String((evalSplit.value || "val").trim()));
      setStored("mas.eval1_task_scope", String((evalTaskScope.value || "all").trim()));
      setStored("mas.eval1_start_task", String((evalStartTask.value || "").trim()));
      const selectedTasks = getSelectedTaskValues();
      setStored("mas.eval1_selected_tasks", selectedTasks.join(","));
      setStatus("Running...");

      const limit = Math.max(1, parseInt(evalTaskLimit.value || "3", 10) || 3);
      const split = (evalSplit.value || "val").trim() || "val";
      const taskScope = (evalTaskScope.value || "all").trim() || "all";
      const startTask = (evalStartTask.value || "").trim();
      const params = new URLSearchParams({
        query,
        use_success_criteria: useSC.checked ? "1" : "0",
        eval1_mode: eval1Mode.checked ? "1" : "0",
        eval_task_limit: String(limit),
        eval_split: split,
        eval_task_scope: taskScope,
        eval_start_task: startTask,
        eval_selected_tasks: selectedTasks.join(","),
      });
      es = new EventSource(`/api/stream?${params.toString()}`);
      streamActive = true;

      es.onopen = () => {
        setStatus("Connected. Running...");
      };

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
        streamTerminal = true;
        if ((payload.mode || "") === "eval1") {
          finalBox.textContent = payload.summary_text || "Eval1 run completed.";
          evalCurrent.textContent = "Eval1 run completed.";
          if (payload.summary && typeof payload.summary === "object") {
            const tasks = Array.isArray(payload.summary.tasks) ? payload.summary.tasks : [];
            const totalCases = tasks.reduce((a, x) => a + (x.executed || 0), 0);
            renderEvalProgress({
              split: payload.summary.split,
              per_task_limit: payload.summary.per_task_limit,
              task_filter: payload.summary.task_filter || "all",
              total_cases: totalCases,
              completed_cases: totalCases,
              tasks,
            });
          }
          setStatus(`Eval1 completed · output=${payload.output_dir || "eval1_test"}`);
        } else {
          finalBox.textContent = payload.final_answer || "";
          const mode = payload.use_success_criteria === false ? "intent" : "criteria";
          setStatus(`Completed (${mode} mode)`);
        }
        closeStream();
      });

      es.addEventListener("run_error", (ev) => {
        streamTerminal = true;
        try {
          const payload = JSON.parse(ev.data);
          const msg = payload.error || "Execution error";
          setStatus(msg, true);
          addEvent("Run Error", msg, "runtime", payload || null);
          evalCurrent.textContent = `Status: error\n\n${msg}`;
        } catch (_e) {
          setStatus("Connection closed", true);
        }
        closeStream();
      });

      es.onerror = () => {
        if (!streamActive || streamTerminal) {
          return;
        }
        setStatus("Connection error", true);
      };

      es.addEventListener("eval_progress", (ev) => {
        const payload = JSON.parse(ev.data);
        renderEvalProgress(payload);
        renderEvalCurrent(payload);
      });
    });

    stopBtn.addEventListener("click", () => {
      streamTerminal = true;
      closeStream();
      setStatus("Stopped");
    });
    setStatus("UI ready");
    } catch (err) {
      bootFail(err);
      // Fallback: keep buttons responsive even if full UI init fails.
      try {
        const rb = document.getElementById("runBtn");
        const sb = document.getElementById("stopBtn");
        const st = document.getElementById("status");
        if (rb) {
          rb.onclick = () => {
            if (st) {
              st.textContent = "UI init failed. Check status error message.";
              st.className = "err";
            }
          };
        }
        if (sb) {
          sb.onclick = () => {
            if (st) {
              st.textContent = "Stopped";
              st.className = "";
            }
          };
        }
      } catch (_e) {
        return;
      }
    }
    })();
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
            self._send_json({"ok": True, "ui_build": UI_BUILD_ID})
            return
        if parsed.path == "/api/stream":
            self._handle_stream(parsed.query)
            return
        if parsed.path == "/api/eval1_meta":
            self._handle_eval1_meta(parsed.query)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def log_message(self, format: str, *args: Any) -> None:
        del format, args

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Pragma", "no-cache")
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

    def _handle_eval1_meta(self, raw_query: str) -> None:
        params = parse_qs(raw_query)
        split = (params.get("split", ["val"])[0] or "val").strip()
        try:
            evaluator = BiomniEval1()
            df = evaluator.get_instances(split=split or None)
            task_counts: dict[str, int] = {}
            for _, row in df.iterrows():
                task = str(row["task_name"])
                task_counts[task] = int(task_counts.get(task, 0) + 1)
            self._send_json(
                {
                    "ok": True,
                    "split": split,
                    "total_cases": int(len(df)),
                    "task_counts": {
                        k: int(task_counts[k]) for k in sorted(task_counts.keys())
                    },
                }
            )
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc), "split": split}, status=500)

    def _handle_stream(self, raw_query: str) -> None:
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
        eval_selected_tasks = [
            x.strip()
            for x in eval_selected_tasks_raw.split(",")
            if x.strip()
        ]
        if eval_task_scope not in {"all", "start_from", "selected"}:
            eval_task_scope = "all"
        try:
            eval_task_limit = max(1, int(eval_limit_raw))
        except ValueError:
            eval_task_limit = 3
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
                if eval1_mode:
                    report = self._run_eval1_mode(
                        query=query,
                        use_success_criteria=use_success_criteria,
                        eval_task_limit=eval_task_limit,
                        eval_split=eval_split,
                        eval_task_scope=eval_task_scope,
                        eval_start_task=eval_start_task,
                        eval_selected_tasks=eval_selected_tasks,
                        enqueue=enqueue,
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
            if eval1_mode:
                mode = f"eval1(limit={eval_task_limit}, split={eval_split})"
            else:
                mode = "criteria" if use_success_criteria else "intent"
            send_event("status", {"message": f"Run started ({mode} mode)"})
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
                if item_type == "run_error":
                    send_event(
                        "run_error", payload if isinstance(payload, dict) else {}
                    )
                    continue
                if item_type == "eval_progress":
                    send_event(
                        "eval_progress", payload if isinstance(payload, dict) else {}
                    )
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

    @staticmethod
    def _coerce_text(value: Any) -> str:
        return str(value or "").strip()

    @staticmethod
    def _build_eval1_solution_contract_query(query: str) -> str:
        base_query = str(query or "").strip()
        contract = (
            "\n\n[Eval1 Answer Contract]\n"
            "- You may include brief notes outside tags.\n"
            "- Put the final answer in exactly one <solution>...</solution> block.\n"
            "- Inside <solution>, include only the final answer string.\n"
            "- Do not include extra tags inside <solution>.\n"
        )
        return base_query + contract

    @staticmethod
    def _extract_solution_only(answer_text: str) -> tuple[str, bool]:
        text = str(answer_text or "").strip()
        if not text:
            return "", False
        match = re.search(r"<solution>\s*([\s\S]*?)\s*</solution>", text, re.IGNORECASE)
        if not match:
            return text, False
        return str(match.group(1) or "").strip(), True

    def _classify_eval1_answer(
        self, task_name: str, final_answer: str, ground_truth: Any
    ) -> tuple[str, str]:
        raw_answer = self._coerce_text(final_answer)
        gt_text = self._coerce_text(ground_truth)
        normalized_user = normalize_answer_for_task(task_name, raw_answer)
        normalized_gt = normalize_answer_for_task(task_name, gt_text)

        if normalized_user != normalized_gt:
            return "incorrect", "normalized answer mismatch"

        if raw_answer == gt_text or raw_answer == normalized_gt:
            return "correct", "exact final string match"

        if normalized_gt and normalized_gt in raw_answer:
            return "partial", "contains correct answer with extra text"
        if gt_text and gt_text in raw_answer:
            return "partial", "contains ground truth with extra text"

        return "partial", "normalized match but non-exact final string"

    def _write_case_log_py(self, path: Path, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2)
        content = (
            "# Auto-generated Eval1 case log\n"
            "# Do not edit manually.\n\n"
            f"CASE_LOG = {body}\n"
        )
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _safe_mean(values: list[float]) -> float:
        if not values:
            return 0.0
        return float(sum(values) / len(values))

    def _run_eval1_mode(
        self,
        *,
        query: str,
        use_success_criteria: bool,
        eval_task_limit: int,
        eval_split: str,
        eval_task_scope: str,
        eval_start_task: str,
        eval_selected_tasks: list[str],
        enqueue,
    ) -> dict[str, Any]:
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
                    "data": {},
                },
            }
        )
        load_timeout_raw = os.getenv("MAS_EVAL1_LOAD_TIMEOUT_SEC", "25").strip()
        try:
            load_timeout_sec = max(5, int(load_timeout_raw))
        except ValueError:
            load_timeout_sec = 25
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(BiomniEval1)
                evaluator = fut.result(timeout=load_timeout_sec)
        except concurrent.futures.TimeoutError as exc:
            raise RuntimeError(
                f"Eval1 dataset load timed out after {load_timeout_sec}s; check network/HF access"
            ) from exc
        instances = evaluator.get_instances(split=eval_split or None)
        if len(instances) == 0:
            raise RuntimeError(f"No Eval1 instances found for split='{eval_split}'")

        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = Path.cwd() / "eval1_test"
        run_dir = base_dir / f"run_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)

        run_config = {
            "mode": "eval1",
            "split": eval_split,
            "per_task_limit": eval_task_limit,
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
        task_available_by_name = {name: int(len(grouped[name])) for name in available_tasks}
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
            selected.extend(grouped[task_name][: task_effective_limit_by_name[task_name]])

        total = len(selected)
        if total == 0:
            raise RuntimeError("No Eval1 rows selected after per-task limit")

        agent_context: dict[str, Any] = {
            "task_name": "",
            "task_instance_id": 0,
            "case_events": [],
        }

        def on_eval_node_event(payload: dict[str, Any]) -> None:
            wrapped = dict(payload)
            wrapped["eval_task_name"] = agent_context["task_name"]
            wrapped["eval_task_instance_id"] = agent_context["task_instance_id"]
            events = agent_context.get("case_events")
            if isinstance(events, list):
                events.append(wrapped)
            enqueue({"type": "node", "payload": wrapped})

        agent = MASAgent(
            event_callback=on_eval_node_event,
            use_success_criteria=use_success_criteria,
        )

        task_summary: dict[str, dict[str, Any]] = {}
        run_index_rows: list[dict[str, Any]] = []

        def build_progress_tasks() -> list[dict[str, int | str]]:
            progress_rows: list[dict[str, int | str]] = []
            for name in sorted(task_summary):
                entry = task_summary[name]
                lat = [float(x) for x in entry.get("latencies_sec", [])]
                avg_time = self._safe_mean(lat)
                std_time = float(statistics.pstdev(lat)) if len(lat) > 1 else 0.0
                toks = [float(x) for x in entry.get("tokens_total", [])]
                avg_total_tokens = self._safe_mean(toks)
                std_total_tokens = (
                    float(statistics.pstdev(toks)) if len(toks) > 1 else 0.0
                )
                progress_rows.append(
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
                        "avg_time_sec": avg_time,
                        "std_time_sec": std_time,
                        "avg_total_tokens": avg_total_tokens,
                        "std_total_tokens": std_total_tokens,
                    }
                )
            return progress_rows

        for idx, row in enumerate(selected, start=1):
            task_name = str(row["task_name"])
            task_instance_id = int(row["task_instance_id"])
            prompt = str(row["prompt"])
            agent_query = self._build_eval1_solution_contract_query(prompt)
            ground_truth = row["answer"]
            task_dir = run_dir / task_name
            task_dir.mkdir(parents=True, exist_ok=True)

            agent_context["task_name"] = task_name
            agent_context["task_instance_id"] = task_instance_id
            agent_context["case_events"] = []

            enqueue(
                {
                    "type": "node",
                    "payload": {
                        "label": "[Eval1 Case Divider]",
                        "content": "------------------------------",
                        "workflow_state": "EVAL1",
                        "stage": "eval1_case_divider",
                        "token_usage": {},
                        "data": {
                            "task": task_name,
                            "task_instance_id": task_instance_id,
                            "progress": [idx, total],
                        },
                    },
                }
            )

            enqueue(
                {
                    "type": "node",
                    "payload": {
                        "label": "[Eval1 Case Start]",
                        "content": (
                            f"task={task_name}, task_instance_id={task_instance_id}, "
                            f"progress={idx}/{total}\nquery={prompt}"
                        ),
                        "workflow_state": "EVAL1",
                        "stage": "eval1_case_start",
                        "token_usage": {},
                        "data": {
                            "task": task_name,
                            "task_instance_id": task_instance_id,
                            "progress": [idx, total],
                            "query": prompt,
                        },
                    },
                }
            )

            enqueue(
                {
                    "type": "eval_progress",
                    "payload": {
                        "split": eval_split,
                        "per_task_limit": eval_task_limit,
                        "task_filter": task_filter_text,
                        "completed_cases": idx - 1,
                        "total_cases": total,
                        "tasks": build_progress_tasks(),
                        "current_status": "running",
                        "current_task": task_name,
                        "current_task_instance_id": task_instance_id,
                        "current_query": prompt,
                    },
                }
            )

            run_error = ""
            result: dict[str, Any] = {}
            final_answer = ""
            final_answer_raw = ""
            solution_tag_found = False
            case_started_at = dt.datetime.now()
            case_finished_at = case_started_at
            try:
                result = agent.go(agent_query, verbose=True, stream=False)
                final_answer_raw = str(result.get("final_answer", ""))
                final_answer, solution_tag_found = self._extract_solution_only(
                    final_answer_raw
                )
                grade, reason = self._classify_eval1_answer(
                    task_name, final_answer, ground_truth
                )
                case_finished_at = dt.datetime.now()
            except Exception as exc:
                run_error = str(exc)
                grade = "incorrect"
                reason = f"case_exception: {run_error}"
                case_finished_at = dt.datetime.now()

            measured_ms = (case_finished_at - case_started_at).total_seconds() * 1000.0
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
                    "query_start_ts": case_started_at.isoformat(timespec="milliseconds"),
                    "final_answer_ts": case_finished_at.isoformat(timespec="milliseconds"),
                },
                "metrics": {
                    "query_to_final_ms": query_to_final_ms,
                    "retry_count": int(result.get("retry_count", 0) or 0),
                    "plan_revision_count": int(
                        result.get("plan_revision_count", 0) or 0
                    ),
                    "full_reset_count": int(result.get("full_reset_count", 0) or 0),
                },
                "step_latency_summary": result.get("step_latency_summary", {}),
                "events": list(agent_context.get("case_events") or []),
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
                "query_start_ts": case_started_at.isoformat(timespec="milliseconds"),
                "final_answer_ts": case_finished_at.isoformat(timespec="milliseconds"),
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
                json.dumps(execution_trace, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            raw_events_path = task_dir / f"{case_stem}.raw_events.jsonl"
            with raw_events_path.open("w", encoding="utf-8") as fp:
                for ev in list(agent_context.get("case_events") or []):
                    fp.write(json.dumps(ev, ensure_ascii=False) + "\n")

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
            summary[grade] += 1
            summary["latencies_sec"].append(latency_sec)
            token_usage_total = result.get("token_usage_total", {})
            token_total = 0
            if isinstance(token_usage_total, dict):
                token_total = int(token_usage_total.get("total", 0) or 0)
                if token_total <= 0:
                    token_total = int(
                        (token_usage_total.get("input", 0) or 0)
                        + (token_usage_total.get("output", 0) or 0)
                    )
            summary["tokens_total"].append(token_total)
            summary["cases"].append(
                {
                    "task_instance_id": task_instance_id,
                    "instance_id": int(row["instance_id"]),
                    "grade": grade,
                    "grade_reason": reason,
                    "case_file": str(case_file.relative_to(run_dir)),
                    "summary_file": str(
                        (task_dir / f"{case_stem}.summary.json").relative_to(run_dir)
                    ),
                    "trace_file": str(
                        (task_dir / f"{case_stem}.trace.json").relative_to(run_dir)
                    ),
                    "raw_events_file": str(raw_events_path.relative_to(run_dir)),
                    "query_to_final_sec": latency_sec,
                    "total_tokens": token_total,
                }
            )
            run_index_rows.append(
                {
                    "task_name": task_name,
                    "task_instance_id": task_instance_id,
                    "instance_id": int(row["instance_id"]),
                    "grade": grade,
                    "grade_reason": reason,
                    "query_to_final_ms": query_to_final_ms,
                    "query_to_final_sec": latency_sec,
                    "total_tokens": token_total,
                    "case_dir": str(task_dir.relative_to(run_dir)),
                    "summary_file": str(
                        (task_dir / f"{case_stem}.summary.json").relative_to(run_dir)
                    ),
                    "trace_file": str(
                        (task_dir / f"{case_stem}.trace.json").relative_to(run_dir)
                    ),
                    "raw_events_file": str(raw_events_path.relative_to(run_dir)),
                }
            )

            enqueue(
                {
                    "type": "node",
                    "payload": {
                        "label": "[Eval1 Answer Check]",
                        "content": f"ground_truth={self._coerce_text(ground_truth)}",
                        "workflow_state": "EVAL1",
                        "stage": "eval1_answer_check",
                        "token_usage": {},
                        "data": {
                            "query": prompt,
                            "model_final": final_answer,
                            "ground_truth": self._coerce_text(ground_truth),
                            "grade": grade,
                            "reason": reason,
                            "task_name": task_name,
                            "task_instance_id": task_instance_id,
                        },
                    },
                }
            )

            enqueue(
                {
                    "type": "eval_progress",
                    "payload": {
                        "split": eval_split,
                        "per_task_limit": eval_task_limit,
                        "task_filter": task_filter_text,
                        "completed_cases": idx,
                        "total_cases": total,
                        "tasks": build_progress_tasks(),
                        "current_status": "completed",
                        "current_task": task_name,
                        "current_task_instance_id": task_instance_id,
                        "current_query": prompt,
                        "current_grade": grade,
                        "current_reason": reason,
                        "current_final_answer": final_answer,
                        "current_ground_truth": self._coerce_text(ground_truth),
                        "current_latency_sec": latency_sec,
                    },
                }
            )

        all_tasks = []
        for task_name in sorted(task_summary):
            entry = task_summary[task_name]
            lat = [float(x) for x in entry.get("latencies_sec", [])]
            avg_time = self._safe_mean(lat)
            std_time = float(statistics.pstdev(lat)) if len(lat) > 1 else 0.0
            toks = [float(x) for x in entry.get("tokens_total", [])]
            avg_total_tokens = self._safe_mean(toks)
            std_total_tokens = float(statistics.pstdev(toks)) if len(toks) > 1 else 0.0
            task_json_path = run_dir / task_name / "task_summary.json"
            task_json_path.write_text(
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
            "mode": "eval1",
            "split": eval_split,
            "per_task_limit": eval_task_limit,
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
                    "mode": "eval1",
                    "split": eval_split,
                    "per_task_limit": eval_task_limit,
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
            f"# Eval1 Summary ({timestamp})",
            "",
            f"- split: {eval_split}",
            f"- per_task_limit: {eval_task_limit}",
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
                    **item
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
