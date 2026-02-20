from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from biomni_msa.core.llm import get_llm


@dataclass
class LLMResponse:
    text: str


class LLMBackend:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name
        self._llm = None
        self.last_json_meta: dict[str, Any] = {
            "stage": "",
            "used_fallback": False,
            "reason": "",
            "attempts": 0,
        }
        try:
            self._llm = get_llm(model=model_name) if model_name else get_llm()
        except Exception:
            self._llm = None

    def complete(self, prompt: str) -> LLMResponse:
        if self._llm is None:
            return LLMResponse(text="")
        result = self._llm.invoke(prompt)
        text = getattr(result, "content", "")
        if isinstance(text, list):
            chunks: list[str] = []
            for item in text:
                if isinstance(item, str):
                    chunks.append(item)
                    continue
                if isinstance(item, dict):
                    if isinstance(item.get("text"), str):
                        chunks.append(item["text"])
                        continue
                    if item.get("type") == "text" and isinstance(
                        item.get("content"), str
                    ):
                        chunks.append(item["content"])
                        continue
                maybe_text = getattr(item, "text", None)
                if isinstance(maybe_text, str):
                    chunks.append(maybe_text)
                else:
                    chunks.append(str(item))
            text = "\n".join(chunks)
        return LLMResponse(text=str(text))

    def complete_json(self, prompt: str) -> dict[str, Any]:
        resp = self.complete(prompt)
        if not resp.text.strip():
            raise RuntimeError("LLM returned empty response")
        parsed = self._extract_json(resp.text)
        if parsed is None:
            raise RuntimeError("Failed to parse JSON from LLM response")
        return parsed

    def complete_json_strict(
        self,
        prompt: str,
        required_keys: list[str],
        retries: int = 2,
        validator: Any = None,
        stage: str = "",
    ) -> dict[str, Any]:
        total = max(1, retries + 1)
        last_reason = ""
        for i in range(total):
            attempt_prompt = prompt
            if i > 0:
                keys = ", ".join(required_keys)
                attempt_prompt = (
                    prompt
                    + "\n\nReturn JSON only."
                    + f" Required keys: {keys}."
                    + " No markdown, no extra text."
                )
            resp = self.complete(attempt_prompt)
            if not resp.text.strip():
                data = None
                last_reason = "empty_response"
            else:
                parsed = self._extract_json(resp.text)
                if parsed is None:
                    data = None
                    last_reason = "json_parse_failed"
                else:
                    data = parsed

            if not isinstance(data, dict):
                last_reason = "not_dict"
                continue
            missing = [k for k in required_keys if k not in data]
            if missing:
                last_reason = f"missing_keys:{','.join(missing)}"
                continue
            if validator is not None:
                try:
                    verdict = validator(data)
                    if isinstance(verdict, tuple):
                        ok = bool(verdict[0])
                        detail = str(verdict[1]) if len(verdict) > 1 else ""
                    else:
                        ok = bool(verdict)
                        detail = ""
                    if not ok:
                        last_reason = detail or "validator_failed"
                        continue
                except Exception:
                    last_reason = "validator_exception"
                    continue
            self.last_json_meta = {
                "stage": stage,
                "used_fallback": False,
                "reason": "ok",
                "attempts": i + 1,
            }
            return data
        self.last_json_meta = {
            "stage": stage,
            "used_fallback": False,
            "reason": last_reason or "strict_validation_failed",
            "attempts": total,
        }
        raise RuntimeError(
            f"LLM strict JSON generation failed at stage '{stage}': {self.last_json_meta['reason']}"
        )

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | None:
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            pass
        fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fenced:
            inner = fenced.group(1).strip()
            try:
                parsed = json.loads(inner)
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                pass
        candidate = LLMBackend._first_balanced_object(text)
        if candidate is None:
            return None
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    @staticmethod
    def _first_balanced_object(text: str) -> str | None:
        start = text.find("{")
        if start < 0:
            return None
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return None
