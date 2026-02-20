from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "resources" / "source"
KNOW_HOW_ROOT = ROOT / "biomni_msa" / "know_how"
OUT_DIR = ROOT / "resources" / "index"
OUT_FILE = OUT_DIR / "master_index.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(rid: str) -> int:
    h = hashlib.sha256(rid.encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def domain_slug(domain_dir: str) -> str:
    return domain_dir.split("_", 1)[1]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "snapshots").mkdir(parents=True, exist_ok=True)

    domain_dirs = sorted(
        p for p in SOURCE_ROOT.iterdir() if p.is_dir() and p.name[:2].isdigit()
    )

    tools: list[dict] = []
    data_lake: list[dict] = []
    libraries: list[dict] = []
    know_how: list[dict] = []
    domain_profiles: list[dict] = []

    for domain_dir in domain_dirs:
        slug = domain_slug(domain_dir.name)
        tool_count = 0
        data_count = 0
        library_count = 0

        desc_dir = domain_dir / "descriptions"
        for desc_file in sorted(desc_dir.glob("*.py")):
            desc_mod = load_module(desc_file)
            items = getattr(desc_mod, "description", [])
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                if not name:
                    continue
                rid = f"tool:{slug}:{desc_file.stem}.{name}"
                tools.append(
                    {
                        "id": stable_id(rid),
                        "rid": rid,
                        "kind": "tool",
                        "domain": slug,
                        "name": name,
                        "short_description": item.get("description", ""),
                        "source_path": str(desc_file.relative_to(ROOT)),
                        "symbol": f"description[name={name}]",
                    }
                )
                tool_count += 1

        env_file = domain_dir / "env_desc.py"
        env_mod = load_module(env_file)

        for name, desc in sorted(getattr(env_mod, "data_lake_dict", {}).items()):
            rid = f"data:{slug}:{name}"
            data_lake.append(
                {
                    "id": stable_id(rid),
                    "rid": rid,
                    "kind": "data",
                    "domain": slug,
                    "name": name,
                    "short_description": desc,
                    "source_path": str(env_file.relative_to(ROOT)),
                    "symbol": f"data_lake_dict[{name}]",
                }
            )
            data_count += 1

        for name, desc in sorted(getattr(env_mod, "library_content_dict", {}).items()):
            rid = f"lib:{slug}:{name}"
            libraries.append(
                {
                    "id": stable_id(rid),
                    "rid": rid,
                    "kind": "library",
                    "domain": slug,
                    "name": name,
                    "short_description": desc,
                    "source_path": str(env_file.relative_to(ROOT)),
                    "symbol": f"library_content_dict[{name}]",
                }
            )
            library_count += 1

        domain_profiles.append(
            {
                "domain": slug,
                "tool_count": tool_count,
                "data_count": data_count,
                "library_count": library_count,
            }
        )

    tools.sort(key=lambda x: x["rid"])
    data_lake.sort(key=lambda x: x["rid"])
    libraries.sort(key=lambda x: x["rid"])
    if KNOW_HOW_ROOT.exists():
        for doc_path in sorted(KNOW_HOW_ROOT.glob("*.md")):
            if doc_path.stem.upper() in {"README", "QUICK_START"}:
                continue
            rid = f"know_how:common:{doc_path.stem}"
            first_line = doc_path.read_text(encoding="utf-8").splitlines()[0:1]
            title = first_line[0].lstrip("# ").strip() if first_line else doc_path.stem
            know_how.append(
                {
                    "id": stable_id(rid),
                    "rid": rid,
                    "kind": "know_how",
                    "domain": "common",
                    "name": title or doc_path.stem,
                    "short_description": f"Know-how guide: {doc_path.stem}",
                    "source_path": str(doc_path.relative_to(ROOT)),
                    "symbol": "markdown_document",
                }
            )
    know_how.sort(key=lambda x: x["rid"])
    domain_profiles.sort(key=lambda x: x["domain"])

    payload = {
        "meta": {
            "generated_at": now_iso(),
            "version": "v2-master",
            "source_root": str(SOURCE_ROOT.relative_to(ROOT)),
            "index_mode": "single_file_with_lazy_resolution",
        },
        "router_profile": domain_profiles,
        "resources": {
            "tools": tools,
            "data_lake": data_lake,
            "libraries": libraries,
            "know_how": know_how,
        },
    }

    OUT_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )

    index_hash = sha256_file(OUT_FILE)
    snapshot = {
        "meta": {
            "snapshot_id": "plan_demo_rev_1",
            "created_at": now_iso(),
            "index_file": str(OUT_FILE.relative_to(ROOT)),
            "index_sha256": index_hash,
        },
        "selected_ids": {
            "tools": [],
            "data_lake": [],
            "libraries": [],
            "know_how": [],
        },
    }
    snapshot_path = OUT_DIR / "snapshots" / "plan_demo_rev_1.json"
    snapshot_path.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    build()
