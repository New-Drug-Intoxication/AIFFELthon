#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
GEN_DIR="$REPO_ROOT/generated"
REQ_FILE="$GEN_DIR/requirements.python.txt"
FAIL_FILE="$GEN_DIR/failed.python.txt"
MGR="${MAS_ENV_MGR:-conda}"

if [[ ! -f "$REQ_FILE" ]]; then
  echo "[python] requirements.python.txt not found"
  exit 0
fi

to_conda_name() {
  case "$1" in
    opencv-python) echo "opencv" ;;
    PyPDF2) echo "pypdf2" ;;
    PyMassSpec) echo "pymassspec" ;;
    PyLabRobot) echo "" ;;
    python-libsbml) echo "python-libsbml" ;;
    *) echo "$1" ;;
  esac
}

ok=0
fail=0
tmp_fail="$FAIL_FILE.tmp"
rm -f "$tmp_fail"

while IFS= read -r raw || [[ -n "$raw" ]]; do
  pkg="$(echo "$raw" | xargs)"
  [[ -z "$pkg" ]] && continue

  conda_name="$(to_conda_name "$pkg")"
  installed=false

  if [[ -n "$conda_name" ]]; then
    if "$MGR" install -y -c bioconda -c conda-forge "$conda_name" >/dev/null 2>&1; then
      installed=true
    fi
  fi

  if [[ "$installed" == false ]]; then
    if python -m pip install "$pkg" >/dev/null 2>&1; then
      installed=true
    fi
  fi

  if [[ "$installed" == true ]]; then
    ok=$((ok+1))
  else
    echo "$pkg" >> "$tmp_fail"
    fail=$((fail+1))
  fi
done < "$REQ_FILE"

if [[ -f "$tmp_fail" ]]; then
  mv "$tmp_fail" "$FAIL_FILE"
else
  rm -f "$FAIL_FILE"
fi

echo "[python] ok=$ok fail=$fail"
