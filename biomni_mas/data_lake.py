from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from biomni_mas.core.data_utils import check_and_download_s3_files


def load_data_lake_catalog(index_file: Path) -> list[dict[str, Any]]:
    data = json.loads(index_file.read_text(encoding="utf-8"))
    resources = data.get("resources", {})
    return list(resources.get("data_lake", []))


def select_data_lake_files(
    catalog: list[dict[str, Any]],
    domains: list[str] | None = None,
    ids: list[int] | None = None,
    names: list[str] | None = None,
    select_all: bool = False,
) -> list[str]:
    wanted_domains = {x.strip().lower() for x in (domains or []) if x.strip()}
    wanted_ids = set(ids or [])
    wanted_names = {x.strip() for x in (names or []) if x.strip()}

    selected: list[str] = []
    seen: set[str] = set()
    for row in catalog:
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        row_domain = str(row.get("domain", "")).strip().lower()
        row_id = row.get("id")
        match = (
            select_all
            or row_id in wanted_ids
            or name in wanted_names
            or row_domain in wanted_domains
        )
        if not match:
            continue
        if name in seen:
            continue
        seen.add(name)
        selected.append(name)

    if wanted_names:
        for name in sorted(wanted_names):
            if name not in seen:
                selected.append(name)

    return selected


def find_missing_files(file_names: list[str], root: Path) -> list[str]:
    return [name for name in file_names if not (root / name).exists()]


def ensure_data_lake_files(
    file_names: list[str],
    data_lake_root: Path,
    s3_bucket_url: str,
    folder: str = "data_lake",
) -> dict[str, bool]:
    data_lake_root.mkdir(parents=True, exist_ok=True)
    pending = find_missing_files(file_names, data_lake_root)
    if not pending:
        return {}
    if not s3_bucket_url:
        raise RuntimeError("MAS_S3_BUCKET_URL is empty. Cannot download missing files.")

    try:
        return check_and_download_s3_files(
            s3_bucket_url=s3_bucket_url,
            local_data_lake_path=str(data_lake_root),
            expected_files=pending,
            folder=folder,
        )
    except Exception:
        return _download_missing_with_urllib(
            pending,
            data_lake_root=data_lake_root,
            s3_bucket_url=s3_bucket_url,
            folder=folder,
        )


def _download_missing_with_urllib(
    file_names: list[str],
    data_lake_root: Path,
    s3_bucket_url: str,
    folder: str,
) -> dict[str, bool]:
    results: dict[str, bool] = {}
    base = s3_bucket_url.rstrip("/") + "/" + folder.strip("/") + "/"
    for name in file_names:
        target = data_lake_root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        url = urllib.parse.urljoin(base, name)
        ok = _download_file(url, target)
        results[name] = ok
        if ok:
            print(f"Downloaded: {name}")
        else:
            print(f"Failed: {name}")
    return results


def _download_file(url: str, target: Path) -> bool:
    tmp_target = Path(str(target) + ".tmp")
    try:
        with urllib.request.urlopen(url) as response, open(tmp_target, "wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        os.replace(tmp_target, target)
        return True
    except (OSError, urllib.error.URLError, urllib.error.HTTPError):
        if tmp_target.exists():
            tmp_target.unlink(missing_ok=True)
        return False
