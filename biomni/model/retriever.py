import json
import contextlib
import re
import os
import time
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI


class ToolRetriever:
    """Retrieve tools from the tool registry."""

    def __init__(self, token_tracker: Any | None = None):
        self._llm_call_log_path = os.getenv("BIOMNI_LLM_CALL_LOG_PATH", "").strip() or None
        raw_max_chars = os.getenv("BIOMNI_LLM_CALL_LOG_MAX_CHARS", "").strip()
        try:
            self._llm_call_log_max_chars = int(raw_max_chars) if raw_max_chars else 12000
        except ValueError:
            self._llm_call_log_max_chars = 12000
        self._llm_call_logging_enabled = bool(self._llm_call_log_path)
        self._token_tracker = token_tracker

    @staticmethod
    def _truncate_text(value: str, max_chars: int | None = None) -> str:
        if max_chars is None or max_chars <= 0:
            return value
        if len(value) <= max_chars:
            return value
        return value[:max_chars] + f"... [truncated {len(value) - max_chars} chars]"

    def _serialize_for_log(self, prompt: str, response: object | None) -> dict[str, object]:
        usage = {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        }
        if isinstance(response, dict):
            usage_block = response.get("usage") or response.get("response_metadata", {}).get("token_usage")
            if isinstance(usage_block, dict):
                usage["prompt_tokens"] = usage_block.get("prompt_tokens")
                usage["completion_tokens"] = usage_block.get("completion_tokens")
                usage["total_tokens"] = usage_block.get("total_tokens")
        else:
            metadata = getattr(response, "response_metadata", None)
            if isinstance(metadata, dict):
                token_usage = metadata.get("token_usage")
                if isinstance(token_usage, dict):
                    usage["prompt_tokens"] = token_usage.get("prompt_tokens")
                    usage["completion_tokens"] = token_usage.get("completion_tokens")
                    usage["total_tokens"] = token_usage.get("total_tokens")

        payload = {
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "component": "tool_retriever.prompt_based_retrieval",
            "model": str(getattr(response, "model_name", "unknown")),
            "prompt": self._truncate_text(prompt, self._llm_call_log_max_chars),
            "response": self._truncate_text(str(response), self._llm_call_log_max_chars),
            "response_type": str(type(response).__name__) if response is not None else "None",
            "token_usage": usage,
        }
        return payload

    def _log_llm_call(self, prompt: str, response: object | None, elapsed_sec: float, error: str | None = None) -> None:
        if not self._llm_call_logging_enabled or not self._llm_call_log_path:
            return
        payload = self._serialize_for_log(prompt, response)
        payload["elapsed_seconds"] = round(elapsed_sec, 3)
        payload["error"] = error
        try:
            parent = os.path.dirname(self._llm_call_log_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(self._llm_call_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass

    def _invoke_llm(self, llm, prompt: str):
        start = time.perf_counter()
        try:
            if hasattr(llm, "invoke"):
                response = llm.invoke([HumanMessage(content=prompt)])
            else:
                response = str(llm(prompt))
            elapsed = time.perf_counter() - start
            self._log_llm_call(prompt, response, elapsed, error=None)
            if self._token_tracker is not None:
                self._token_tracker.record_call(
                    "tool_retriever.prompt_based_retrieval",
                    prompt,
                    response,
                    model_name=getattr(llm, "model_name", None),
                )
            return response
        except Exception as e:
            elapsed = time.perf_counter() - start
            self._log_llm_call(prompt, None, elapsed, error=str(e))
            raise

    def prompt_based_retrieval(self, query: str, resources: dict, llm=None) -> dict:
        """Use a prompt-based approach to retrieve the most relevant resources for a query.

        Args:
            query: The user's query
            resources: A dictionary with keys 'tools', 'data_lake', 'libraries', and 'know_how',
                      each containing a list of available resources
            llm: Optional LLM instance to use for retrieval (if None, will create a new one)

        Returns:
            A dictionary with the same keys, but containing only the most relevant resources

        """
        # Build prompt sections for available resources
        prompt_sections = []
        prompt_sections.append(f"""
You are an expert biomedical research assistant. Your task is to select the relevant resources to help answer a user's query.

USER QUERY: {query}

Below are the available resources. For each category, select items that are directly or indirectly relevant to answering the query.
Be generous in your selection - include resources that might be useful for the task, even if they're not explicitly mentioned in the query.
It's better to include slightly more resources than to miss potentially useful ones.

AVAILABLE TOOLS:
{self._format_resources_for_prompt(resources.get("tools", []))}

AVAILABLE DATA LAKE ITEMS:
{self._format_resources_for_prompt(resources.get("data_lake", []))}

AVAILABLE SOFTWARE LIBRARIES:
{self._format_resources_for_prompt(resources.get("libraries", []))}""")

        # Add know-how section if available
        if "know_how" in resources and resources["know_how"]:
            prompt_sections.append(f"""
AVAILABLE KNOW-HOW DOCUMENTS (Best Practices & Protocols):
{self._format_resources_for_prompt(resources.get("know_how", []))}""")

        # Build response format based on available categories
        response_format = """
For each category, respond with ONLY the indices of the relevant items in the following format:
TOOLS: [list of indices]
DATA_LAKE: [list of indices]
LIBRARIES: [list of indices]"""

        if "know_how" in resources and resources["know_how"]:
            response_format += "\nKNOW_HOW: [list of indices]"

        response_format += """

For example:
TOOLS: [0, 3, 5, 7, 9]
DATA_LAKE: [1, 2, 4]
LIBRARIES: [0, 2, 4, 5, 8]"""

        if "know_how" in resources and resources["know_how"]:
            response_format += "\nKNOW_HOW: [0, 1]"

        response_format += """

If a category has no relevant items, use an empty list, e.g., DATA_LAKE: []

IMPORTANT GUIDELINES:
1. Be generous but not excessive - aim to include all potentially relevant resources
2. ALWAYS prioritize database tools for general queries - include as many database tools as possible
3. Include all literature search tools
4. For wet lab sequence type of queries, ALWAYS include molecular biology tools
5. For data lake items, include datasets that could provide useful information
6. For libraries, include those that provide functions needed for analysis
7. For know-how documents, include those that provide relevant protocols, best practices, or troubleshooting guidance
8. Don't exclude resources just because they're not explicitly mentioned in the query
9. When in doubt about a database tool or molecular biology tool, include it rather than exclude it
"""

        prompt = "\n".join(prompt_sections) + response_format

        # Use the provided LLM or create a new one
        if llm is None:
            llm = ChatOpenAI(model="gpt-4o")

        # Invoke the LLM
        response = self._invoke_llm(llm, prompt)
        if hasattr(response, "content"):
            response_content = response.content
        else:
            response_content = str(response)

        # Parse the response to extract the selected indices
        selected_indices = self._parse_llm_response(response_content)

        # Get the selected resources
        selected_resources = {
            "tools": [
                resources["tools"][i] for i in selected_indices.get("tools", []) if i < len(resources.get("tools", []))
            ],
            "data_lake": [
                resources["data_lake"][i]
                for i in selected_indices.get("data_lake", [])
                if i < len(resources.get("data_lake", []))
            ],
            "libraries": [
                resources["libraries"][i]
                for i in selected_indices.get("libraries", [])
                if i < len(resources.get("libraries", []))
            ],
        }

        # Add know-how if present
        if "know_how" in resources and resources["know_how"]:
            selected_resources["know_how"] = [
                resources["know_how"][i]
                for i in selected_indices.get("know_how", [])
                if i < len(resources.get("know_how", []))
            ]

        return selected_resources

    def _format_resources_for_prompt(self, resources: list) -> str:
        """Format resources for inclusion in the prompt."""
        formatted = []
        for i, resource in enumerate(resources):
            if isinstance(resource, dict):
                # Handle dictionary format (from tool registry or data lake/libraries with descriptions)
                name = resource.get("name", f"Resource {i}")
                description = resource.get("description", "")
                formatted.append(f"{i}. {name}: {description}")
            elif isinstance(resource, str):
                # Handle string format (simple strings)
                formatted.append(f"{i}. {resource}")
            else:
                # Try to extract name and description from tool objects
                name = getattr(resource, "name", str(resource))
                desc = getattr(resource, "description", "")
                formatted.append(f"{i}. {name}: {desc}")

        return "\n".join(formatted) if formatted else "None available"

    def _parse_llm_response(self, response) -> dict:
        """Parse the LLM response to extract the selected indices.

        Accepts either a plain string or a Responses API-style list of content blocks.
        """
        # Normalize response to string if it's a list of content blocks (Responses API)
        if isinstance(response, list):
            parts = []
            for item in response:
                # LangChain Responses API returns list of dicts like {"type": "text", "text": "..."}
                if isinstance(item, dict):
                    if item.get("type") == "text" and "text" in item:
                        parts.append(str(item.get("text", "")))
                    # If it's a tool_call or other block, ignore for this simple parsing
                elif isinstance(item, str):
                    parts.append(item)
            response = "\n".join([p for p in parts if p])
        elif not isinstance(response, str):
            response = str(response)
        selected_indices = {"tools": [], "data_lake": [], "libraries": [], "know_how": []}

        # Extract indices for each category
        tools_match = re.search(r"TOOLS:\s*\[(.*?)\]", response, re.IGNORECASE)
        if tools_match and tools_match.group(1).strip():
            with contextlib.suppress(ValueError):
                selected_indices["tools"] = [int(idx.strip()) for idx in tools_match.group(1).split(",") if idx.strip()]

        data_lake_match = re.search(r"DATA_LAKE:\s*\[(.*?)\]", response, re.IGNORECASE)
        if data_lake_match and data_lake_match.group(1).strip():
            with contextlib.suppress(ValueError):
                selected_indices["data_lake"] = [
                    int(idx.strip()) for idx in data_lake_match.group(1).split(",") if idx.strip()
                ]

        libraries_match = re.search(r"LIBRARIES:\s*\[(.*?)\]", response, re.IGNORECASE)
        if libraries_match and libraries_match.group(1).strip():
            with contextlib.suppress(ValueError):
                selected_indices["libraries"] = [
                    int(idx.strip()) for idx in libraries_match.group(1).split(",") if idx.strip()
                ]

        # Extract know-how indices
        know_how_match = re.search(r"KNOW[-_]HOW:\s*\[(.*?)\]", response, re.IGNORECASE)
        if know_how_match and know_how_match.group(1).strip():
            with contextlib.suppress(ValueError):
                selected_indices["know_how"] = [
                    int(idx.strip()) for idx in know_how_match.group(1).split(",") if idx.strip()
                ]

        return selected_indices
