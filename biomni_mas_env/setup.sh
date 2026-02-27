#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_NAME="biomni_mas_e1"
ENV_DIR="$REPO_ROOT/biomni_mas_env"
export MAS_ENV_MGR=""

if ! command -v conda >/dev/null 2>&1 && ! command -v micromamba >/dev/null 2>&1; then
  echo "[setup] conda or micromamba is required"
  exit 1
fi

if command -v conda >/dev/null 2>&1; then
  MGR="conda"
else
  MGR="micromamba"
fi
export MAS_ENV_MGR="$MGR"

ACTIVE_ENV="${CONDA_DEFAULT_ENV:-${MAMBA_DEFAULT_ENV:-}}"
if [[ "$ACTIVE_ENV" != "$ENV_NAME" ]]; then
  echo "[setup] activate environment first: conda activate $ENV_NAME"
  exit 1
fi

echo "[setup] step1 bio env update"
"$MGR" env update -n "$ENV_NAME" -f "$ENV_DIR/bio_env.yml" || true

echo "[setup] step2 r base update"
"$MGR" env update -n "$ENV_NAME" -f "$ENV_DIR/r_packages.yml" || true

echo "[setup] step3 install generated requirements"

python "$REPO_ROOT/scripts/generate_install_assets.py"
bash "$ENV_DIR/install_python_packages.sh" "$REPO_ROOT" || true
Rscript "$ENV_DIR/install_r_packages.R" "$REPO_ROOT" || true
bash "$ENV_DIR/install_cli_tools.sh" "$REPO_ROOT" || true

echo "[setup] done"
