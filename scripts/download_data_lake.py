from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from biomni_mas.config import MASPaths
from biomni_mas.data_lake import (
    ensure_data_lake_files,
    find_missing_files,
    load_data_lake_catalog,
    select_data_lake_files,
)


def _csv_to_list(raw: str) -> list[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def _csv_to_ints(raw: str) -> list[int]:
    out: list[int] = []
    for token in _csv_to_list(raw):
        out.append(int(token))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all", action="store_true", help="Download all data lake files"
    )
    parser.add_argument(
        "--domain",
        action="append",
        default=[],
        help="Domain name from index (repeatable, e.g. --domain Genomics)",
    )
    parser.add_argument("--ids", default="", help="Comma-separated data_lake IDs")
    parser.add_argument(
        "--files", default="", help="Comma-separated explicit file names"
    )
    parser.add_argument(
        "--data-lake-root",
        default=os.getenv("MAS_DATA_LAKE_ROOT", ""),
        help="Override local data lake root path",
    )
    parser.add_argument(
        "--s3-bucket-url",
        default=os.getenv("MAS_S3_BUCKET_URL", ""),
        help="Override S3 bucket URL",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selection and missing files without downloading",
    )
    args = parser.parse_args()

    paths = MASPaths.default()
    data_lake_root = (
        Path(args.data_lake_root).expanduser()
        if args.data_lake_root
        else paths.data_lake_root
    )

    catalog = load_data_lake_catalog(paths.resource_index_file)
    selected = select_data_lake_files(
        catalog,
        domains=args.domain,
        ids=_csv_to_ints(args.ids),
        names=_csv_to_list(args.files),
        select_all=args.all,
    )

    if not selected:
        raise SystemExit(
            "No data lake files selected. Use --all, --domain, --ids, or --files."
        )

    missing = find_missing_files(selected, data_lake_root)
    print(f"Selected files: {len(selected)}")
    print(f"Already present: {len(selected) - len(missing)}")
    print(f"Missing: {len(missing)}")

    if args.dry_run:
        for name in missing:
            print(name)
        return

    if not missing:
        print("Nothing to download.")
        return

    results = ensure_data_lake_files(
        selected,
        data_lake_root=data_lake_root,
        s3_bucket_url=args.s3_bucket_url,
        folder="data_lake",
    )
    failed = [name for name, ok in results.items() if not ok]
    if failed:
        print(f"Download failed for {len(failed)} files.")
        for name in failed:
            print(name)
        raise SystemExit(1)

    print("Download completed.")


if __name__ == "__main__":
    main()
