import json
import re
from typing import Any

try:
    import tiktoken
except Exception:  # pragma: no cover - optional dependency fallback
    tiktoken = None


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        try:
            return int(float(value))
        except Exception:
            return 0


def _flatten_content(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                    continue
                content = item.get("content")
                if isinstance(content, str):
                    parts.append(content)
                    continue
            parts.append(_flatten_content(item))
        return "\n".join(part for part in parts if part)

    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str):
            return text
        content = value.get("content")
        if isinstance(content, str):
            return content
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            return str(value)

    content = getattr(value, "content", None)
    if content is not None:
        return _flatten_content(content)

    text = getattr(value, "text", None)
    if text is not None:
        return _flatten_content(text)

    return str(value)


def _serialize_prompt_payload(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            return str(value)

    if isinstance(value, list):
        lines: list[str] = []
        for item in value:
            role = getattr(item, "type", None) or getattr(item, "role", None) or item.__class__.__name__
            content = _flatten_content(getattr(item, "content", item))
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    content = getattr(value, "content", None)
    if content is not None:
        role = getattr(value, "type", None) or getattr(value, "role", None) or value.__class__.__name__
        return f"{role}: {_flatten_content(content)}"

    return str(value)


class TokenUsageTracker:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name
        self.reset()

    def reset(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.by_component: dict[str, dict[str, int]] = {}
        self.total = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def get_snapshot(self) -> dict[str, Any]:
        return {
            "calls": list(self.calls),
            "by_component": {key: dict(value) for key, value in self.by_component.items()},
            "total": dict(self.total),
        }

    def record_call(
        self,
        component: str,
        prompt_payload: Any,
        response: Any,
        *,
        model_name: str | None = None,
    ) -> dict[str, int]:
        resolved_model = model_name or getattr(response, "model_name", None) or self.model_name
        usage = self._extract_usage(response)
        estimated = False
        if not (usage["prompt_tokens"] or usage["completion_tokens"] or usage["total_tokens"]):
            usage = self._estimate_usage(prompt_payload, response, model_name=resolved_model)
            estimated = True
        self._record_usage(component=component, usage=usage, model_name=resolved_model, estimated=estimated)
        return usage

    @classmethod
    def _extract_usage(cls, response: Any) -> dict[str, int]:
        usage = getattr(response, "usage_metadata", None)
        if not isinstance(usage, dict):
            response_metadata = getattr(response, "response_metadata", None)
            if isinstance(response_metadata, dict):
                maybe = response_metadata.get("token_usage") or response_metadata.get("usage")
                if isinstance(maybe, dict):
                    usage = maybe
        if not isinstance(usage, dict) and isinstance(response, dict):
            maybe = response.get("usage") or response.get("response_metadata", {}).get("token_usage")
            if isinstance(maybe, dict):
                usage = maybe
        if not isinstance(usage, dict):
            additional_kwargs = getattr(response, "additional_kwargs", None)
            if isinstance(additional_kwargs, dict):
                maybe = additional_kwargs.get("usage")
                if isinstance(maybe, dict):
                    usage = maybe
        if not isinstance(usage, dict):
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        prompt_tokens = _to_int(
            usage.get("input_tokens")
            or usage.get("prompt_tokens")
            or usage.get("inputTokenCount")
            or usage.get("input")
        )
        completion_tokens = _to_int(
            usage.get("output_tokens")
            or usage.get("completion_tokens")
            or usage.get("outputTokenCount")
            or usage.get("output")
        )
        total_tokens = _to_int(
            usage.get("total_tokens")
            or usage.get("totalTokenCount")
            or usage.get("total")
        )
        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    def _estimate_usage(self, prompt_payload: Any, response: Any, model_name: str | None = None) -> dict[str, int]:
        prompt_text = _serialize_prompt_payload(prompt_payload)
        response_text = _flatten_content(response)
        prompt_tokens = self._estimate_tokens(prompt_text, model_name=model_name)
        completion_tokens = self._estimate_tokens(response_text, model_name=model_name)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    def _record_usage(
        self,
        *,
        component: str,
        usage: dict[str, int],
        model_name: str | None = None,
        estimated: bool = False,
    ) -> None:
        key = (component or "").strip() or "unknown"
        bucket = self.by_component.setdefault(
            key,
            {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )
        bucket["calls"] += 1
        bucket["prompt_tokens"] += int(usage.get("prompt_tokens", 0))
        bucket["completion_tokens"] += int(usage.get("completion_tokens", 0))
        bucket["total_tokens"] += int(usage.get("total_tokens", 0))

        self.total["prompt_tokens"] += int(usage.get("prompt_tokens", 0))
        self.total["completion_tokens"] += int(usage.get("completion_tokens", 0))
        self.total["total_tokens"] += int(usage.get("total_tokens", 0))

        self.calls.append(
            {
                "call": len(self.calls) + 1,
                "component": key,
                "model": model_name or self.model_name,
                "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                "completion_tokens": int(usage.get("completion_tokens", 0)),
                "total_tokens": int(usage.get("total_tokens", 0)),
                "estimated": bool(estimated),
            }
        )

    @staticmethod
    def _encoding_name_for_model(model_name: str | None) -> str:
        model = str(model_name or "").lower()
        if "gpt-4o" in model or "gpt-5" in model:
            return "o200k_base"
        return "cl100k_base"

    @classmethod
    def _estimate_tokens(cls, text: str, model_name: str | None = None) -> int:
        if not text:
            return 0

        if tiktoken is not None:
            try:
                encoding = tiktoken.get_encoding(cls._encoding_name_for_model(model_name))
                return len(encoding.encode(text))
            except Exception:
                pass

        return max(1, len(re.findall(r"\S+", text)))
