from __future__ import annotations

import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


def parse_hpo_obo(file_path: str) -> dict[str, str]:
    hp_dict: dict[str, str] = {}
    current_id: str | None = None
    current_name: str | None = None

    with open(file_path, encoding="utf-8") as file:
        for line in file:
            item = line.strip()
            if item.startswith("[Term]"):
                if current_id and current_name:
                    hp_dict[current_id] = current_name
                current_id = None
                current_name = None
            elif item.startswith("id: HP:"):
                current_id = item.split(": ", 1)[1]
            elif item.startswith("name:"):
                current_name = item.split(": ", 1)[1]
        if current_id and current_name:
            hp_dict[current_id] = current_name

    return hp_dict


def check_and_download_s3_files(
    s3_bucket_url: str,
    local_data_lake_path: str,
    expected_files: list[str],
    folder: str = "data_lake",
) -> dict[str, bool]:
    os.makedirs(local_data_lake_path, exist_ok=True)
    if folder == "benchmark":
        return _download_benchmark_zip(
            s3_bucket_url, local_data_lake_path, expected_files
        )

    results: dict[str, bool] = {}
    base = s3_bucket_url.rstrip("/") + "/" + folder.strip("/") + "/"
    for filename in expected_files:
        local_file_path = Path(local_data_lake_path) / filename
        if local_file_path.exists():
            results[filename] = True
            continue
        local_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_url = urllib.parse.urljoin(base, filename)
        results[filename] = _download_file(file_url, local_file_path)
    return results


def _download_benchmark_zip(
    s3_bucket_url: str,
    local_data_lake_path: str,
    expected_files: list[str],
) -> dict[str, bool]:
    zip_url = urllib.parse.urljoin(s3_bucket_url.rstrip("/") + "/", "benchmark.zip")
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
            tmp_path = Path(tmp_zip.name)
        if not _download_file(zip_url, tmp_path):
            return dict.fromkeys(expected_files, False)
        with zipfile.ZipFile(tmp_path, "r") as zip_ref:
            zip_ref.extractall(local_data_lake_path)
        return dict.fromkeys(expected_files, True)
    except Exception:
        return dict.fromkeys(expected_files, False)
    finally:
        try:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


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
