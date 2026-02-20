from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()
    ]


def run(cmd: list[str]) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return p.returncode == 0, (p.stdout + "\n" + p.stderr).strip()
    except Exception as e:
        return False, str(e)


def install_python(packages: list[str]) -> tuple[list[str], list[str]]:
    ok, fail = [], []
    for pkg in packages:
        success, _ = run([sys.executable, "-m", "pip", "install", pkg])
        (ok if success else fail).append(pkg)
    return ok, fail


def install_cli_brew(tools: list[str]) -> tuple[list[str], list[str]]:
    ok, fail = [], []
    mapping = {
        "Model-based Analysis of ChIP-Seq data.": "macs2",
        "Model-based Analysis of ChIP-Seq data": "macs2",
        "Genome-wide Complex Trait Analysis (GCTA) tool.": "gcta",
    }
    for tool in tools:
        formula = mapping.get(tool, tool)
        success, _ = run(["brew", "install", formula])
        (ok if success else fail).append(tool)
    return ok, fail


def install_r(packages: list[str]) -> tuple[list[str], list[str]]:
    if not packages:
        return [], []
    expr = (
        "install.packages(c("
        + ",".join(repr(x) for x in packages)
        + "), repos='https://cloud.r-project.org')"
    )
    success, _ = run(["Rscript", "-e", expr])
    return (packages, []) if success else ([], packages)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--python", action="store_true")
    parser.add_argument("--r", action="store_true")
    parser.add_argument("--cli", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root)
    gen = root / "generated"
    py = read_lines(gen / "requirements.python.txt")
    rpkgs = read_lines(gen / "requirements.r.txt")
    cli = read_lines(gen / "requirements.cli.txt")

    do_python = args.all or args.python
    do_r = args.all or args.r
    do_cli = args.all or args.cli

    if args.dry_run:
        print(f"python packages: {len(py)}")
        print(f"r packages: {len(rpkgs)}")
        print(f"cli tools: {len(cli)}")
        return

    if do_python:
        ok, fail = install_python(py)
        print(f"[python] ok={len(ok)} fail={len(fail)}")
        if fail:
            (gen / "failed.python.txt").write_text(
                "\n".join(fail) + "\n", encoding="utf-8"
            )

    if do_r:
        ok, fail = install_r(rpkgs)
        print(f"[r] ok={len(ok)} fail={len(fail)}")
        if fail:
            (gen / "failed.r.txt").write_text("\n".join(fail) + "\n", encoding="utf-8")

    if do_cli:
        ok, fail = install_cli_brew(cli)
        print(f"[cli/brew] ok={len(ok)} fail={len(fail)}")
        if fail:
            (gen / "failed.cli.txt").write_text(
                "\n".join(fail) + "\n", encoding="utf-8"
            )


if __name__ == "__main__":
    main()
