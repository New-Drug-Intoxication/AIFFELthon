from __future__ import annotations

import os
from typing import TYPE_CHECKING, Literal

from langchain_core.language_models.chat_models import BaseChatModel

if TYPE_CHECKING:
    from biomni_msa.core.config import MSACompatConfig


SourceType = Literal[
    "OpenAI",
    "AzureOpenAI",
    "Anthropic",
    "Ollama",
    "Gemini",
    "Bedrock",
    "Groq",
    "Custom",
]
ALLOWED_SOURCES: set[str] = set(SourceType.__args__)


def get_llm(
    model: str | None = None,
    temperature: float | None = None,
    stop_sequences: list[str] | None = None,
    source: SourceType | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    config: "MSACompatConfig | None" = None,
) -> BaseChatModel:
    if config is not None:
        if model is None:
            model = getattr(config, "llm", None)
        if temperature is None:
            temperature = getattr(config, "temperature", None)
        if source is None:
            source = getattr(config, "source", None)
        if base_url is None:
            base_url = getattr(config, "base_url", None)
        if api_key is None:
            api_key = getattr(config, "api_key", None) or "EMPTY"

    if model is None:
        model = "claude-3-5-sonnet-20241022"
    if temperature is None:
        temperature = 0.7
    if api_key is None:
        api_key = "EMPTY"

    if source is None:
        env_source = os.getenv("LLM_SOURCE") or os.getenv("MSA_LLM_SOURCE")
        if env_source in ALLOWED_SOURCES:
            source = env_source  # type: ignore[assignment]
        elif model.startswith("claude-"):
            source = "Anthropic"
        elif model.startswith("gpt-oss"):
            source = "Ollama"
        elif model.startswith("gpt-"):
            source = "OpenAI"
        elif model.startswith("azure-"):
            source = "AzureOpenAI"
        elif model.startswith("gemini-"):
            source = "Gemini"
        elif "groq" in model.lower():
            source = "Groq"
        elif base_url is not None:
            source = "Custom"
        elif "/" in model or any(
            name in model.lower()
            for name in [
                "llama",
                "mistral",
                "qwen",
                "gemma",
                "phi",
                "dolphin",
                "orca",
                "vicuna",
                "deepseek",
            ]
        ):
            source = "Ollama"
        elif model.startswith(
            (
                "anthropic.claude-",
                "amazon.titan-",
                "meta.llama-",
                "mistral.",
                "cohere.",
                "ai21.",
                "us.",
            )
        ):
            source = "Bedrock"
        else:
            raise ValueError(
                "Unable to determine model source. Please specify 'source'."
            )

    if source == "OpenAI":
        from langchain_openai import ChatOpenAI

        use_responses = model.startswith("gpt-5")
        if use_responses:

            class _ChatOpenAIResponsesNoStop(ChatOpenAI):
                def _get_request_payload(self, input_, *, stop=None, **kwargs):  # type: ignore[override]
                    payload = super()._get_request_payload(input_, stop=stop, **kwargs)
                    payload.pop("stop", None)
                    payload.pop("temperature", None)
                    return payload

            return _ChatOpenAIResponsesNoStop(
                model=model,
                temperature=1,
                stop_sequences=stop_sequences,
                use_responses_api=True,
                output_version="v0",
            )
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            stop_sequences=stop_sequences,
        )

    if source == "AzureOpenAI":
        from langchain_openai import AzureChatOpenAI

        deployment = model.replace("azure-", "")
        return AzureChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
            azure_deployment=deployment,
            openai_api_version="2024-12-01-preview",
            temperature=temperature,
        )

    if source == "Anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=8192,
            stop_sequences=stop_sequences,
        )

    if source == "Gemini":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            stop_sequences=stop_sequences,
        )

    if source == "Groq":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
            stop_sequences=stop_sequences,
        )

    if source == "Ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=model, temperature=temperature)

    if source == "Bedrock":
        from langchain_aws import ChatBedrock

        return ChatBedrock(
            model=model,
            temperature=temperature,
            stop_sequences=stop_sequences,
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )

    if source == "Custom":
        from langchain_openai import ChatOpenAI

        if base_url is None:
            raise ValueError("base_url must be provided for custom LLMs")
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=8192,
            stop_sequences=stop_sequences,
            base_url=base_url,
            api_key=api_key,
        )

    raise ValueError(f"Invalid source: {source}")
