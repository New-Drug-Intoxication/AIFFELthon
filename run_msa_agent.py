from __future__ import annotations

import argparse
import json

from biomni_msa import MSAAgent
from biomni_msa.config import MSAPaths
from biomni_msa.env_loader import load_env_from_repo_root
from biomni_msa.preflight import install_packages, scan_missing_tool_dependencies


def main() -> None:
    load_env_from_repo_root()
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="User query")
    parser.add_argument(
        "--stream", action="store_true", help="Print stage messages while running"
    )
    parser.add_argument(
        "--no-trace", action="store_true", help="Hide messages from return payload"
    )
    parser.add_argument(
        "--preflight-deps",
        action="store_true",
        help="Scan tool-module dependencies before running the agent",
    )
    parser.add_argument(
        "--preflight-install",
        action="store_true",
        help="Install missing preflight packages automatically (pip)",
    )
    parser.add_argument(
        "--preflight-domains",
        default="",
        help="Optional comma-separated domain names/slugs for preflight scope",
    )
    parser.add_argument(
        "--preflight-continue-on-missing",
        action="store_true",
        help="Continue agent run even if missing deps are found",
    )
    args = parser.parse_args()

    if args.preflight_deps:
        paths = MSAPaths.default()
        domains = [
            x.strip() for x in str(args.preflight_domains).split(",") if x.strip()
        ]
        report = scan_missing_tool_dependencies(paths=paths, domains=domains or None)
        missing = report.get("suggested_pip_packages", [])
        print(
            json.dumps(
                {
                    "preflight_checked_files": len(
                        report.get("checked_tool_files", [])
                    ),
                    "missing_python_modules": report.get("missing_python_modules", []),
                    "suggested_pip_packages": missing,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        if missing and args.preflight_install:
            rc = install_packages(missing)
            if rc != 0:
                raise SystemExit(rc)
        elif missing and not args.preflight_continue_on_missing:
            print(
                "Preflight found missing dependencies. Re-run with --preflight-install "
                "or --preflight-continue-on-missing."
            )
            raise SystemExit(2)

    agent = MSAAgent()
    result = agent.go(args.query, verbose=not args.no_trace, stream=args.stream)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
