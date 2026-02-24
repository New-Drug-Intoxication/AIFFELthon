from __future__ import annotations

from pathlib import Path


def load_env_from_repo_root() -> bool:
    repo_root = Path(__file__).resolve().parents[1]
    env_file = repo_root / ".env"
    if not env_file.exists():
        return False
    try:
        from dotenv import load_dotenv
    except Exception:
        return False
    load_dotenv(dotenv_path=env_file, override=False)
    return True
