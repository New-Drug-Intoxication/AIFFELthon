from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _resolve_root_path(env_name: str, default_path: Path, repo_root: Path) -> Path:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default_path
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


@dataclass
class MASPaths:
    repo_root: Path
    prompt_root: Path
    resource_source_root: Path
    resource_index_root: Path
    resource_index_file: Path
    data_lake_root: Path
    schema_db_root: Path
    workspace_root: Path

    @classmethod
    def default(cls) -> "MASPaths":
        repo_root = Path(__file__).resolve().parents[1]
        resource_index_root = repo_root / "resources"
        resource_index_file = resource_index_root / "index" / "master_index.json"
        return cls(
            repo_root=repo_root,
            prompt_root=repo_root / "prompts",
            resource_source_root=repo_root / "resources" / "source",
            resource_index_root=resource_index_root,
            resource_index_file=resource_index_file,
            data_lake_root=_resolve_root_path(
                "MAS_DATA_LAKE_ROOT", repo_root / "data_lake", repo_root
            ),
            schema_db_root=_resolve_root_path(
                "MAS_SCHEMA_DB_ROOT", repo_root / "schema_db", repo_root
            ),
            workspace_root=_resolve_root_path(
                "MAS_WORKSPACE_ROOT", repo_root / "workspace", repo_root
            ),
        )


@dataclass
class AgentRuntimeConfig:
    timeout_seconds: int = 600
    observation_max_chars: int = 10000
    verbose_default: bool = True
    json_retries: int = int(os.getenv("MAS_JSON_RETRIES", "0"))
    step_retry_limit: int = 2
    plan_revision_limit: int = 2
    orchestrator_instruction_max_chars: int = int(
        os.getenv("MAS_ORCH_INSTRUCTION_MAX_CHARS", "480")
    )
    orchestrator_instruction_postprocess: bool = (
        str(os.getenv("MAS_ORCH_INSTRUCTION_POSTPROCESS", "false")).lower() == "true"
    )
    s3_bucket_url: str = os.getenv("MAS_S3_BUCKET_URL", "")
    graph_recursion_limit: int = int(os.getenv("MAS_GRAPH_RECURSION_LIMIT", "80"))
