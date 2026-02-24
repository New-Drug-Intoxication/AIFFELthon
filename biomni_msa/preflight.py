from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from biomni_msa.config import MSAPaths


_PIP_NAME_MAP = {
    "Bio": "biopython",
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "esm": "fair-esm",
    "googlesearch":"googlesearch-python"
}


def _to_domain_slug(text: str) -> str:
    return str(text or "").strip().lower().replace(" ", "_")


def _tool_rows_from_index(paths: MSAPaths, domain_slugs: set[str] | None) -> list[dict[str, Any]]:
    raw = json.loads(paths.resource_index_file.read_text(encoding="utf-8"))
    rows = raw.get("resources", {}).get("tools", [])
    out: list[dict[str, Any]] = []
    for row in rows:
        domain = _to_domain_slug(row.get("domain", ""))
        if domain_slugs and domain not in domain_slugs:
            continue
        out.append(row)
    return out


def scan_missing_tool_dependencies(
    paths: MSAPaths,
    domains: list[str] | None = None,
) -> dict[str, Any]:
    domain_slugs = {_to_domain_slug(x) for x in (domains or []) if str(x).strip()}
    tool_rows = _tool_rows_from_index(paths, domain_slugs if domain_slugs else None)
    unique_files = sorted(
        {str(row.get("source_path", "")).strip().replace("descriptions", "tools").replace(".py", ".py") for row in tool_rows}
    )

    checked_files: list[str] = []
    missing_by_module: dict[str, list[str]] = {}
    missing_modules: set[str] = set()
    load_failures: list[dict[str, str]] = []

    for rel in unique_files:
        if not rel or "/tools/" not in rel:
            continue
        abs_path = paths.repo_root / rel
        if not abs_path.exists():
            continue
        checked_files.append(rel)
        spec = importlib.util.spec_from_file_location(abs_path.stem, abs_path)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except ModuleNotFoundError as exc:
            mod_name = str(getattr(exc, "name", "") or "").strip() or "unknown"
            missing_modules.add(mod_name)
            missing_by_module.setdefault(mod_name, []).append(rel)
            load_failures.append({"file": rel, "error": f"No module named '{mod_name}'"})
        except Exception as exc:
            load_failures.append({"file": rel, "error": str(exc)})

    pip_packages = sorted({_PIP_NAME_MAP.get(x, x) for x in missing_modules if x})
    return {
        "checked_tool_files": checked_files,
        "missing_python_modules": sorted(missing_modules),
        "suggested_pip_packages": pip_packages,
        "missing_by_module": {k: sorted(v) for k, v in missing_by_module.items()},
        "load_failures": load_failures,
    }


def install_packages(packages: list[str]) -> int:
    pkg = [str(x).strip() for x in packages if str(x).strip()]
    if not pkg:
        return 0
    cmd = [sys.executable, "-m", "pip", "install", *pkg]
    proc = subprocess.run(cmd)
    return int(proc.returncode)

