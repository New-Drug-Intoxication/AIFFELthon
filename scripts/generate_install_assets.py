from __future__ import annotations

import argparse
import json
from pathlib import Path


def detect_kind(short_desc: str) -> str:
    s = (short_desc or "").lower()
    if "[python package]" in s:
        return "python"
    if "[r package]" in s:
        return "r"
    if "[cli tool]" in s:
        return "cli"
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    index_file = repo_root / "resources" / "index" / "master_index.json"
    out_dir = repo_root / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(index_file.read_text(encoding="utf-8"))
    libs = data.get("resources", {}).get("libraries", [])

    py_pkgs: set[str] = set()
    r_pkgs: set[str] = set()
    cli_tools: set[str] = set()
    unknown: set[str] = set()

    for row in libs:
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        kind = detect_kind(str(row.get("short_description", "")))
        if kind == "python":
            py_pkgs.add(name)
        elif kind == "r":
            r_pkgs.add(name)
        elif kind == "cli":
            cli_tools.add(name)
        else:
            unknown.add(name)

    py_list = sorted(py_pkgs, key=lambda x: x.lower())
    r_list = sorted(r_pkgs, key=lambda x: x.lower())
    cli_list = sorted(cli_tools, key=lambda x: x.lower())
    unknown_list = sorted(unknown, key=lambda x: x.lower())

    (out_dir / "requirements.python.txt").write_text(
        "\n".join(py_list) + "\n", encoding="utf-8"
    )
    (out_dir / "requirements.r.txt").write_text(
        "\n".join(r_list) + "\n", encoding="utf-8"
    )
    (out_dir / "requirements.cli.txt").write_text(
        "\n".join(cli_list) + "\n", encoding="utf-8"
    )
    (out_dir / "requirements.unknown.txt").write_text(
        "\n".join(unknown_list) + "\n", encoding="utf-8"
    )

    report = [
        "# Auto-generated install assets",
        "",
        f"- Python packages: {len(py_list)}",
        f"- R packages: {len(r_list)}",
        f"- CLI tools: {len(cli_list)}",
        f"- Unknown-tag items: {len(unknown_list)}",
        "",
        "Generated files:",
        "- generated/requirements.python.txt",
        "- generated/requirements.r.txt",
        "- generated/requirements.cli.txt",
        "- generated/requirements.unknown.txt",
    ]
    (out_dir / "install_plan.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print("Generated install assets under generated/")


if __name__ == "__main__":
    main()
