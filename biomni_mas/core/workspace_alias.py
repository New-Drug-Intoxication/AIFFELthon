from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class WorkspaceAliasResult:
    status: str
    alias_path: str
    target_path: str
    changed: bool
    note: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, str | bool]:
        return asdict(self)


def _normalized_target(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _readlink_resolved(path: Path) -> Path:
    raw = path.readlink()
    if raw.is_absolute():
        return raw.resolve(strict=False)
    return (path.parent / raw).resolve(strict=False)


def ensure_workspace_data_lake_alias(
    workspace_root: Path, data_lake_root: Path
) -> WorkspaceAliasResult:
    workspace_root.mkdir(parents=True, exist_ok=True)
    alias_path = workspace_root / "data_lake"
    target_path = _normalized_target(data_lake_root)

    try:
        if alias_path.is_symlink():
            current_target = _readlink_resolved(alias_path)
            if current_target != target_path:
                alias_path.unlink()
                alias_path.symlink_to(target_path, target_is_directory=True)
                return WorkspaceAliasResult(
                    status="wrong_target_relinked",
                    alias_path=str(alias_path),
                    target_path=str(target_path),
                    changed=True,
                    note=f"previous_target={current_target}",
                )
            if not target_path.exists():
                return WorkspaceAliasResult(
                    status="broken_expected_target_missing",
                    alias_path=str(alias_path),
                    target_path=str(target_path),
                    changed=False,
                    note="target_missing",
                )
            return WorkspaceAliasResult(
                status="ok_existing",
                alias_path=str(alias_path),
                target_path=str(target_path),
                changed=False,
            )

        if alias_path.exists():
            return WorkspaceAliasResult(
                status="conflict_non_symlink",
                alias_path=str(alias_path),
                target_path=str(target_path),
                changed=False,
                note="existing_path_is_not_symlink",
            )

        alias_path.symlink_to(target_path, target_is_directory=True)
        return WorkspaceAliasResult(
            status="created",
            alias_path=str(alias_path),
            target_path=str(target_path),
            changed=True,
        )
    except OSError as exc:
        return WorkspaceAliasResult(
            status="error",
            alias_path=str(alias_path),
            target_path=str(target_path),
            changed=False,
            error=str(exc),
        )


def compact_text(text: str, max_chars: int = 320, max_lines: int = 2) -> str:
    raw = " ".join(str(text or "").replace("\r", "\n").split())
    if not raw:
        return ""
    parts = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", raw) if x.strip()]
    if parts:
        limited = " ".join(parts[: max(1, max_lines)])
    else:
        limited = raw
    if len(limited) > max_chars:
        return limited[: max(0, max_chars - 3)].rstrip() + "..."
    return limited


def inject_prompt(template: str, values: dict[str, Any]) -> str:
    out = template
    for key, value in values.items():
        out = out.replace("{" + key + "}", "" if value is None else str(value))
    return prune_empty_prompt_lines(out)


def prune_empty_prompt_lines(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=", stripped):
            i += 1
            continue
        if stripped.endswith(":"):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j >= len(lines):
                i = j
                continue
            next_line = lines[j].strip()
            if next_line.startswith("---") or next_line.startswith("["):
                i = j
                continue
        out.append(line)
        i += 1
    return "\n".join(out)


def coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except Exception:
        pass
    try:
        f = float(text)
    except Exception:
        return None
    if f.is_integer():
        return int(f)
    return None


def to_int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    out: list[int] = []
    for item in value:
        parsed = coerce_int(item)
        if parsed is None:
            continue
        out.append(parsed)
    return out


def indices_or_ids_to_ids(
    selected: list[int], items: list[dict[str, Any]]
) -> list[int]:
    out: list[int] = []
    seen: set[int] = set()
    id_set: set[int] = set()
    for row in items:
        parsed = coerce_int(row.get("id"))
        if parsed is None:
            continue
        id_set.add(parsed)
    for v in selected:
        resolved: int | None = None
        if 0 <= v < len(items):
            resolved = coerce_int(items[v].get("id"))
        elif v in id_set:
            resolved = v
        if resolved is None or resolved in seen:
            continue
        seen.add(resolved)
        out.append(resolved)
    return out


def py_literal(value: Any) -> str:
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return "None"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(py_literal(x) for x in value) + "]"
    if isinstance(value, dict):
        items = [f"{py_literal(k)}: {py_literal(v)}" for k, v in value.items()]
        return "{" + ", ".join(items) + "}"
    return repr(str(value))
