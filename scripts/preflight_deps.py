from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from biomni_msa.config import MSAPaths
from biomni_msa.preflight import install_packages, scan_missing_tool_dependencies


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--domains",
        default="",
        help="Optional comma-separated domain names/slugs for preflight scope",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install missing packages with pip",
    )
    args = parser.parse_args()

    paths = MSAPaths.default()
    domains = [x.strip() for x in str(args.domains).split(",") if x.strip()]
    report = scan_missing_tool_dependencies(paths=paths, domains=domains or None)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    missing = report.get("suggested_pip_packages", [])
    if args.install and missing:
        rc = install_packages(missing)
        if rc != 0:
            raise SystemExit(rc)
    elif missing:
        print(
            "Missing dependencies found. Run with --install to install automatically.",
            file=sys.stderr,
        )
        raise SystemExit(2)


if __name__ == "__main__":
    main()
