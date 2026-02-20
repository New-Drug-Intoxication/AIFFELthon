from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX_FILE = ROOT / "resources" / "index" / "master_index.json"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_ids(value: str) -> list[int]:
    if not value:
        return []
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def resolve_know_how_spec(item: dict) -> dict:
    src = ROOT / item["source_path"]
    text = src.read_text(encoding="utf-8")
    return {
        "id": item["id"],
        "rid": item["rid"],
        "kind": "know_how",
        "domain": item.get("domain", "common"),
        "name": item["name"],
        "description": item.get("short_description", ""),
        "content": text,
        "source_file": item["source_path"],
    }


def resolve_tool_spec(item: dict) -> dict:
    src = ROOT / item["source_path"]
    mod = load_module(src)
    name = item["name"]
    for entry in getattr(mod, "description", []):
        if isinstance(entry, dict) and entry.get("name") == name:
            rid_parts = item["rid"].split(":", 2)[-1].split(".", 1)
            module_name = rid_parts[0]
            return {
                "id": item["id"],
                "rid": item["rid"],
                "kind": "tool",
                "domain": item["domain"],
                "name": name,
                "required_parameters": entry.get("required_parameters", []),
                "optional_parameters": entry.get("optional_parameters", []),
                "description_file": item["source_path"],
                "tool_file": str(
                    (src.parents[1] / "tools" / f"{module_name}.py").relative_to(ROOT)
                ),
            }
    raise KeyError(f"Tool spec not found for {item['rid']}")


def resolve_env_spec(item: dict, key: str) -> dict:
    src = ROOT / item["source_path"]
    mod = load_module(src)
    mapping = getattr(mod, key, {})
    return {
        "id": item["id"],
        "rid": item["rid"],
        "kind": item["kind"],
        "domain": item["domain"],
        "name": item["name"],
        "description": mapping.get(item["name"], item["short_description"]),
        "source_file": item["source_path"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tools", default="", help="Comma-separated tool IDs")
    parser.add_argument("--data", default="", help="Comma-separated data_lake IDs")
    parser.add_argument("--libraries", default="", help="Comma-separated library IDs")
    parser.add_argument("--know-how", default="", help="Comma-separated know_how IDs")
    args = parser.parse_args()

    data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    tools_by_id = {x["id"]: x for x in data["resources"]["tools"]}
    data_by_id = {x["id"]: x for x in data["resources"]["data_lake"]}
    libs_by_id = {x["id"]: x for x in data["resources"]["libraries"]}
    know_by_id = {x["id"]: x for x in data["resources"].get("know_how", [])}

    selected_tool_ids = parse_ids(args.tools)
    selected_data_ids = parse_ids(args.data)
    selected_lib_ids = parse_ids(args.libraries)
    selected_know_how_ids = parse_ids(args.know_how)

    resolved = {
        "selected_resources_spec": {
            "tools": [resolve_tool_spec(tools_by_id[i]) for i in selected_tool_ids],
            "data_lake": [
                resolve_env_spec(data_by_id[i], "data_lake_dict")
                for i in selected_data_ids
            ],
            "libraries": [
                resolve_env_spec(libs_by_id[i], "library_content_dict")
                for i in selected_lib_ids
            ],
            "know_how": [
                resolve_know_how_spec(know_by_id[i])
                for i in selected_know_how_ids
                if i in know_by_id
            ],
        }
    }
    print(json.dumps(resolved, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
