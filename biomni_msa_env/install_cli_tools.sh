#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
GEN_DIR="$REPO_ROOT/generated"
REQ_FILE="$GEN_DIR/requirements.cli.txt"
FAIL_FILE="$GEN_DIR/failed.cli.txt"
MGR="${MSA_ENV_MGR:-conda}"

if [[ ! -f "$REQ_FILE" ]]; then
  echo "[cli] requirements.cli.txt not found"
  exit 0
fi

if ! command -v brew >/dev/null 2>&1; then
  HAS_BREW=0
else
  HAS_BREW=1
fi

to_conda_name() {
  case "$1" in
    FastTree) echo "fasttree" ;;
    gcta64) echo "gcta" ;;
    Homer) echo "homer" ;;
    iqtree2) echo "iqtree" ;;
    plink2) echo "plink2" ;;
    plink) echo "plink" ;;
    vina) echo "vina" ;;
    macs2) echo "macs2" ;;
    autosite) echo "" ;;
    plannotate) echo "" ;;
    fcsparser) echo "" ;;
    *) echo "$1" ;;
  esac
}

to_brew_name() {
  case "$1" in
    FastTree) echo "veryfasttree" ;;
    gcta64) echo "gcta" ;;
    iqtree2) echo "iqtree" ;;
    Homer) echo "homer" ;;
    plink2) echo "plink2" ;;
    plink) echo "plink" ;;
    macs2) echo "macs2" ;;
    trimmomatic) echo "trimmomatic" ;;
    muscle) echo "muscle" ;;
    vina) echo "vina" ;;
    autosite) echo "" ;;
    plannotate) echo "" ;;
    fcsparser) echo "" ;;
    *) echo "$1" ;;
  esac
}

ok=0
fail=0
tmp_fail="$FAIL_FILE.tmp"
rm -f "$tmp_fail"

while IFS= read -r raw || [[ -n "$raw" ]]; do
  tool="$(echo "$raw" | xargs)"
  [[ -z "$tool" ]] && continue

  if command -v "$tool" >/dev/null 2>&1; then
    ok=$((ok+1))
    continue
  fi

  installed=0

  conda_name="$(to_conda_name "$tool")"
  if [[ -n "$conda_name" ]]; then
    if "$MGR" install -y -c bioconda -c conda-forge "$conda_name" >/dev/null 2>&1; then
      installed=1
    fi
  fi

  if [[ "$installed" -eq 0 && "$HAS_BREW" -eq 1 ]]; then
    brew_name="$(to_brew_name "$tool")"
    if [[ -n "$brew_name" ]]; then
      if brew install "$brew_name" >/dev/null 2>&1; then
        installed=1
      fi
    fi
  fi

  if [[ "$installed" -eq 0 && "$tool" == "fcsparser" ]]; then
    if python -m pip install fcsparser >/dev/null 2>&1; then
      installed=1
    fi
  fi

  if [[ "$installed" -eq 0 && "$tool" == "plannotate" ]]; then
    if python -m pip install plannotate >/dev/null 2>&1; then
      installed=1
    fi
  fi

  if [[ "$installed" -eq 1 ]]; then
    ok=$((ok+1))
  else
    echo "$tool" >> "$tmp_fail"
    fail=$((fail+1))
  fi
done < "$REQ_FILE"

if [[ -f "$tmp_fail" ]]; then
  mv "$tmp_fail" "$FAIL_FILE"
else
  rm -f "$FAIL_FILE"
fi

echo "[cli/brew] ok=$ok fail=$fail"
