from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class MASCompatConfig:
    path: str = "./data"
    timeout_seconds: int = 600
    llm: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    use_tool_retriever: bool = True
    commercial_mode: bool = False
    base_url: str | None = None
    api_key: str | None = None
    source: str | None = None
    protocols_io_access_token: str | None = None

    def __post_init__(self) -> None:
        if os.getenv("MAS_PATH"):
            self.path = str(os.getenv("MAS_PATH"))
        if os.getenv("MAS_TIMEOUT_SECONDS"):
            self.timeout_seconds = int(str(os.getenv("MAS_TIMEOUT_SECONDS")))
        if os.getenv("MAS_LLM"):
            self.llm = str(os.getenv("MAS_LLM"))
        if os.getenv("MAS_TEMPERATURE"):
            self.temperature = float(str(os.getenv("MAS_TEMPERATURE")))
        if os.getenv("MAS_USE_TOOL_RETRIEVER"):
            self.use_tool_retriever = (
                str(os.getenv("MAS_USE_TOOL_RETRIEVER")).lower() == "true"
            )
        if os.getenv("MAS_COMMERCIAL_MODE"):
            self.commercial_mode = (
                str(os.getenv("MAS_COMMERCIAL_MODE")).lower() == "true"
            )
        if os.getenv("MAS_CUSTOM_BASE_URL"):
            self.base_url = str(os.getenv("MAS_CUSTOM_BASE_URL"))
        if os.getenv("MAS_CUSTOM_API_KEY"):
            self.api_key = str(os.getenv("MAS_CUSTOM_API_KEY"))
        if os.getenv("MAS_SOURCE"):
            self.source = str(os.getenv("MAS_SOURCE"))

        env_token = os.getenv("PROTOCOLS_IO_ACCESS_TOKEN") or os.getenv(
            "MAS_PROTOCOLS_IO_ACCESS_TOKEN"
        )
        if env_token:
            self.protocols_io_access_token = env_token


default_config = MASCompatConfig()
