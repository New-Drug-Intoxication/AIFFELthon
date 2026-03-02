from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any

from biomni_mas.core.llm import get_llm


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
        self.token_usage_by_stage: dict[str, dict[str, int]] = {}
        self.token_usage_total: dict[str, int] = {
            "input": 0,
            "output": 0,
            "total": 0,
        }
        self.last_stage: str = ""
        try:
            self._llm = get_llm(model=model_name) if model_name else get_llm()
        except Exception:
            self._llm = None

    def reset_usage(self) -> None:
        self.token_usage_by_stage = {}
        self.token_usage_total = {"input": 0, "output": 0, "total": 0}
        self.last_stage = ""

    def get_usage_snapshot(self) -> dict[str, Any]:
        return {
            "by_stage": {
                k: {
                    "input": int(v.get("input", 0)),
                    "output": int(v.get("output", 0)),
                    "total": int(v.get("total", 0)),
                }
                for k, v in self.token_usage_by_stage.items()
            },
            "total": {
                "input": int(self.token_usage_total.get("input", 0)),
                "output": int(self.token_usage_total.get("output", 0)),
                "total": int(self.token_usage_total.get("total", 0)),
            },
        }

    def get_stage_usage(self, stage: str) -> dict[str, int]:
        bucket = self.token_usage_by_stage.get(stage, {})
        return {
            "input": int(bucket.get("input", 0)),
            "output": int(bucket.get("output", 0)),
            "total": int(bucket.get("total", 0)),
        }

    def get_last_stage_usage_snapshot(self) -> dict[str, Any]:
        stage = self.last_stage
        return {"stage": stage, "usage": self.get_stage_usage(stage) if stage else {}}

    def complete(self, prompt: str, stage: str = "") -> LLMResponse:
        if self._llm is None:
            return LLMResponse(text="")
        self.last_stage = stage.strip() or "unstaged"
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
        text_str = str(text)
        usage = self._extract_usage(result)
        if not (usage["input"] or usage["output"] or usage["total"]):
            usage = self._estimate_usage(prompt, text_str)
        if usage["input"] or usage["output"] or usage["total"]:
            self._record_usage(stage=stage, usage=usage)
        return LLMResponse(text=text_str)

    def complete_json(self, prompt: str, stage: str = "") -> dict[str, Any]:
        resp = self.complete(prompt, stage=stage)
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
            resp = self.complete(attempt_prompt, stage=stage)
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

            if data is None:
                continue
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
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
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

    @staticmethod
    def _to_int(value: Any) -> int:
        try:
            return int(value)
        except Exception:
            try:
                return int(float(value))
            except Exception:
                return 0

    @classmethod
    def _extract_usage(cls, result: Any) -> dict[str, int]:
        usage = getattr(result, "usage_metadata", None)
        if not isinstance(usage, dict):
            response_metadata = getattr(result, "response_metadata", None)
            if isinstance(response_metadata, dict):
                maybe = response_metadata.get("token_usage") or response_metadata.get(
                    "usage"
                )
                if isinstance(maybe, dict):
                    usage = maybe
        if not isinstance(usage, dict):
            additional_kwargs = getattr(result, "additional_kwargs", None)
            if isinstance(additional_kwargs, dict):
                maybe = additional_kwargs.get("usage")
                if isinstance(maybe, dict):
                    usage = maybe
        if not isinstance(usage, dict):
            return {"input": 0, "output": 0, "total": 0}

        input_tokens = cls._to_int(
            usage.get("input_tokens")
            or usage.get("prompt_tokens")
            or usage.get("inputTokenCount")
            or usage.get("input")
        )
        output_tokens = cls._to_int(
            usage.get("output_tokens")
            or usage.get("completion_tokens")
            or usage.get("outputTokenCount")
            or usage.get("output")
        )
        total_tokens = cls._to_int(
            usage.get("total_tokens")
            or usage.get("totalTokenCount")
            or usage.get("total")
        )
        if total_tokens == 0:
            total_tokens = input_tokens + output_tokens
        return {"input": input_tokens, "output": output_tokens, "total": total_tokens}

    def _record_usage(self, stage: str, usage: dict[str, int]) -> None:
        key = stage.strip() or "unstaged"
        bucket = self.token_usage_by_stage.setdefault(
            key, {"input": 0, "output": 0, "total": 0}
        )
        bucket["input"] += int(usage.get("input", 0))
        bucket["output"] += int(usage.get("output", 0))
        bucket["total"] += int(usage.get("total", 0))
        self.token_usage_total["input"] += int(usage.get("input", 0))
        self.token_usage_total["output"] += int(usage.get("output", 0))
        self.token_usage_total["total"] += int(usage.get("total", 0))

    def _estimate_usage(self, prompt: str, text: str) -> dict[str, int]:
        input_tokens = self._estimate_tokens(str(prompt))
        output_tokens = self._estimate_tokens(str(text))
        total_tokens = input_tokens + output_tokens
        return {"input": input_tokens, "output": output_tokens, "total": total_tokens}

    def _estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        try:
            import tiktoken  # type: ignore

            model = self.model_name or "gpt-4o"
            try:
                enc = tiktoken.encoding_for_model(model)
            except Exception:
                enc = tiktoken.get_encoding("cl100k_base")
            return int(len(enc.encode(text)))
        except Exception:
            return max(1, int(math.ceil(len(text) / 4)))
