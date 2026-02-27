from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Any


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ResourceStore:
    def __init__(self, workspace_root: Path, index_file: Path):
        self.workspace_root = workspace_root
        self.index_file = index_file
        if not index_file.exists():
            raise FileNotFoundError(f"Resource index not found: {index_file}")
        self.index_data = json.loads(index_file.read_text(encoding="utf-8"))

    def list_for_domain(self, domain: str) -> dict[str, list[dict[str, Any]]]:
        resources = self.index_data["resources"]
        know_how = resources.get("know_how", [])
        return {
            "tools": [x for x in resources["tools"] if x["domain"] == domain],
            "data_lake": [x for x in resources["data_lake"] if x["domain"] == domain],
            "libraries": [x for x in resources["libraries"] if x["domain"] == domain],
            "know_how": [
                x
                for x in know_how
                if x.get("domain") == domain or x.get("domain") == "common"
            ],
        }

    def resolve_selected(
        self,
        tools: list[int],
        data_lake: list[int],
        libraries: list[int],
        know_how: list[int] | None = None,
    ) -> dict[str, Any]:
        resources = self.index_data["resources"]
        tool_by_id = {x["id"]: x for x in resources["tools"]}
        data_by_id = {x["id"]: x for x in resources["data_lake"]}
        lib_by_id = {x["id"]: x for x in resources["libraries"]}
        know_by_id = {x["id"]: x for x in resources.get("know_how", [])}
        return {
            "tools": [
                self._resolve_tool(tool_by_id[i]) for i in tools if i in tool_by_id
            ],
            "data_lake": [
                self._resolve_env(data_by_id[i], "data_lake_dict")
                for i in data_lake
                if i in data_by_id
            ],
            "libraries": [
                self._resolve_env(lib_by_id[i], "library_content_dict")
                for i in libraries
                if i in lib_by_id
            ],
            "know_how": [
                self._resolve_know_how(know_by_id[i])
                for i in (know_how or [])
                if i in know_by_id
            ],
        }

    def _resolve_tool(self, item: dict[str, Any]) -> dict[str, Any]:
        src = self.workspace_root / item["source_path"]
        mod = _load_module(src)
        name = item["name"]
        entry = None
        for row in getattr(mod, "description", []):
            if isinstance(row, dict) and row.get("name") == name:
                entry = row
                break
        if entry is None:
            raise KeyError(f"Tool spec not found for {item['rid']}")
        module_name = item["rid"].split(":", 2)[-1].split(".", 1)[0]
        return {
            "id": item["id"],
            "rid": item["rid"],
            "kind": "tool",
            "domain": item["domain"],
            "name": item["name"],
            "short_description": item.get("short_description", ""),
            "required_parameters": entry.get("required_parameters", []),
            "optional_parameters": entry.get("optional_parameters", []),
            "description_file": item["source_path"],
            "tool_file": str(
                (src.parents[1] / "tools" / f"{module_name}.py").relative_to(
                    self.workspace_root
                )
            ),
        }

    def _resolve_env(self, item: dict[str, Any], key: str) -> dict[str, Any]:
        src = self.workspace_root / item["source_path"]
        mod = _load_module(src)
        mapping = getattr(mod, key, {})
        return {
            "id": item["id"],
            "rid": item["rid"],
            "kind": item["kind"],
            "domain": item["domain"],
            "name": item["name"],
            "short_description": item.get("short_description", ""),
            "description": mapping.get(item["name"], item.get("short_description", "")),
            "source_file": item["source_path"],
        }

    def _resolve_know_how(self, item: dict[str, Any]) -> dict[str, Any]:
        src = self.workspace_root / item["source_path"]
        text = src.read_text(encoding="utf-8")
        return {
            "id": item["id"],
            "rid": item["rid"],
            "kind": "know_how",
            "domain": item.get("domain", "common"),
            "name": item["name"],
            "short_description": item.get("short_description", ""),
            "content": text,
            "content_without_metadata": self._strip_metadata(text),
            "source_file": item["source_path"],
        }

    @staticmethod
    def _strip_metadata(text: str) -> str:
        pattern = re.compile(r"\n## Metadata\n[\s\S]*?(\n## |$)")
        replaced = pattern.sub(
            lambda m: "\n" + (m.group(1) if m.group(1).startswith("\n## ") else ""),
            text,
        )
        return replaced.strip()
