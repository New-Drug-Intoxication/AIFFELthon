from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class MSAPaths:
    repo_root: Path
    prompt_root: Path
    resource_source_root: Path
    resource_index_root: Path
    resource_index_file: Path
    data_lake_root: Path

    @classmethod
    def default(cls) -> "MSAPaths":
        repo_root = Path(__file__).resolve().parents[1]
        resource_index_root = repo_root / "resources"
        resource_index_file = resource_index_root / "index" / "master_index.json"
        return cls(
            repo_root=repo_root,
            prompt_root=repo_root / "prompts",
            resource_source_root=repo_root / "resources" / "source",
            resource_index_root=resource_index_root,
            resource_index_file=resource_index_file,
            data_lake_root=Path(
                os.getenv("MSA_DATA_LAKE_ROOT", str(repo_root / "data_lake"))
            ),
        )


@dataclass
class AgentRuntimeConfig:
    timeout_seconds: int = 600
    observation_max_chars: int = 10000
    verbose_default: bool = True
    json_retries: int = int(os.getenv("MSA_JSON_RETRIES", "0"))
    step_retry_limit: int = 2
    plan_revision_limit: int = 2
    s3_bucket_url: str = os.getenv("MSA_S3_BUCKET_URL", "")
