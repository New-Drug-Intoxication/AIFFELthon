import re
import os
import time
import traceback
import json
import pandas as pd
from collections import defaultdict
from typing import Any, Dict, List, Optional

from tqdm import tqdm

from biomni.eval.benchmark import Benchmark
from biomni.eval.logger import BaseLogger
from biomni.utils import run_with_timeout
from biomni.tool.support_tools import reset_python_repl_namespace
from biomni.config import default_config


try:
    import tiktoken
except Exception:  # pragma: no cover - optional dependency fallback
    tiktoken = None


def _coerce_env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _coerce_env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _coerce_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _normalize_gene_token(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _relation_score(relation_text: str) -> int:
    text = str(relation_text or "").lower()
    if "causal" in text or "causative" in text or "causes" in text or "caused" in text:
        return 3
    if "involved" in text or "modulates" in text or "regulates" in text:
        return 2
    if "associated" in text or "association" in text or "correlate" in text:
        return 1
    return 0


def _flatten_content_blocks(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                    continue
                content = item.get("content")
                if isinstance(content, str):
                    parts.append(content)
                    continue
            parts.append(str(item))
        return "\n".join(parts)

    return str(value)


def _extract_solution_text(text: str) -> str:
    match = re.search(r"<solution>(.*?)</solution>", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return text
    return match.group(1).strip()


def _extract_answer_tags(text: str) -> list[str]:
    return [match.group(1).upper() for match in re.finditer(r"\[ANSWER\]\s*([A-Za-z])\s*\[/ANSWER\]", text, re.IGNORECASE)]


def _extract_answer_tag(text: str) -> str | None:
    tags = _extract_answer_tags(text)
    if tags:
        return tags[-1]
    return None


def _extract_lab_bench_option_letters(prompt: str) -> list[str]:
    letters: list[str] = []
    for value in re.findall(r"(?im)^\s*([A-Za-z])\s*[\)\.]\s+", prompt):
        letter = value.upper()
        if letter not in letters:
            letters.append(letter)

    # Patterns like: "1) Option A" / "1. A"
    for value in re.findall(r"(?im)^\s*\d+\)\s*(?:[Oo]ption\s+)?([A-Za-z])\s*(?:[\)\.]?\s*$|\s+)", prompt):
        letter = value.upper()
        if letter not in letters:
            letters.append(letter)

    # Patterns like: "1) Answer A" with trailing text
    for value in re.findall(r"(?im)^\s*\d+\)\s*[^A-Za-z]*([A-Za-z])\s*[,\)]?\s*$", prompt):
        letter = value.upper()
        if letter not in letters:
            letters.append(letter)

    if not letters:
        return []

    max_letter = max(letters)
    return [chr(v) for v in range(ord("A"), ord(max_letter) + 1)]


def _coerce_structured_text_value(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    if not ((stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]"))):
        return text.strip()

    parsed = None
    try:
        parsed = json.loads(stripped)
    except Exception:
        return text.strip()

    if isinstance(parsed, list):
        if not parsed:
            return ""
        first = parsed[0]
        if isinstance(first, str):
            return first.strip()
        return str(first).strip()

    if isinstance(parsed, dict):
        for key in ("causal_gene", "answer", "result", "value"):
            value = parsed.get(key)
            if value:
                if isinstance(value, str):
                    return value.strip()
                if isinstance(value, list) and value:
                    list_value = value[0]
                    return str(list_value).strip()
                return str(value).strip()
        first_value = next(iter(parsed.values()), None)
        if first_value is not None:
            if isinstance(first_value, str):
                return first_value.strip()
            if isinstance(first_value, list) and first_value:
                first_item = first_value[0]
                return str(first_item).strip()
            return str(first_value).strip()

    return text.strip()


def _extract_candidate_variants(prompt: str) -> list[str]:
    found = re.findall(r"\brs\d+\b", prompt, flags=re.IGNORECASE)
    dedup: list[str] = []
    seen: set[str] = set()
    for item in found:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)
    return dedup


def _extract_candidate_genes(prompt: str) -> list[str]:
    candidates: list[str] = []

    for value in re.findall(r"\{([^{}]+)\}", prompt):
        token = value.strip().strip("'\"")
        if token:
            candidates.append(token)

    line_matches = re.findall(r"(?im)^(?:Candidate genes|Genes in locus):\s*(.+)$", prompt)
    for line in line_matches:
        for raw in line.split(","):
            token = raw.strip().strip("'\"").strip("{}")
            if token:
                candidates.append(token)

    dedup: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        key = item.upper()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)
    return dedup


def _extract_patient_task_tokens(prompt: str) -> tuple[list[str], list[str]]:
    candidates = _extract_candidate_genes(prompt)

    phenotypes: list[str] = []
    phenotype_lines = []
    phenotype_patterns = [
        r"(?im)^\s*(?:clinical features|clinical feature|phenotypes?|phenotype|disease|clinical findings|hpo ids?)\s*[:：]\s*(.+)$",
        r"(?im)^\s*(?:patient presents with|has phenotype\s*[:：])\s*(.+)$",
    ]

    for pattern in phenotype_patterns:
        phenotype_lines.extend(re.findall(pattern, prompt))

    for line in phenotype_lines:
        parts = re.split(r"[,;\n]", line)
        for part in parts:
            token = part.strip().strip("{}[]()")
            if not token:
                continue
            # Keep HPO style tokens (HP:123456) as-is and strip trailing punctuation.
            token = re.sub(r"[\.\;\)\]]+$", "", token).strip()
            if token:
                phenotypes.append(token)

    hpo_ids = re.findall(r"\bHP:?[:]?\d{7}\b", prompt, flags=re.IGNORECASE)
    for hpo in hpo_ids:
        if hpo not in phenotypes:
            phenotypes.append(hpo)

    dedup_candidates: list[str] = []
    seen_candidates: set[str] = set()
    for value in candidates:
        key = value.upper()
        if key in seen_candidates:
            continue
        seen_candidates.add(key)
        dedup_candidates.append(value)

    dedup_phenotypes: list[str] = []
    seen_phenotypes: set[str] = set()
    for value in phenotypes:
        key = _normalize_gene_token(value)
        if not key or key in seen_phenotypes:
            continue
        seen_phenotypes.add(key)
        dedup_phenotypes.append(value.strip())

    return dedup_candidates[:200], dedup_phenotypes[:200]


def _contains_token(text: str, token: str) -> bool:
    pattern = rf"(?<![A-Za-z0-9_.-]){re.escape(token)}(?![A-Za-z0-9_.-])"
    if re.search(pattern, text, flags=re.IGNORECASE):
        return True
    return token.lower() in text.lower()


def _to_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _estimate_tokens(text: str, model_name: str | None = None) -> int:
    """
    Estimate token count for a text segment.

    Uses tiktoken when available (best effort), otherwise word-count fallback.
    """
    if not text:
        return 0

    if tiktoken is not None:
        encoding_name = "cl100k_base"
        model = (model_name or "").lower()
        if "gpt-4" in model or "gpt-3.5" in model:
            encoding_name = "cl100k_base"
        elif "gpt-4o" in model:
            encoding_name = "o200k_base"
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except Exception:
            # Fallback to a conservative approximation
            return max(1, len(re.findall(r"\S+", text)))

    # Fallback: rough approximation when tokenizer is unavailable.
    return max(1, len(re.findall(r"\S+", text)))


def _extract_message_token_usage(message: Any) -> dict[str, int]:
    """Try to extract token usage fields from one LLM message object."""
    usage = getattr(message, "usage_metadata", None)
    if isinstance(usage, dict):
        prompt_tokens = _to_int(usage.get("input_tokens"))
        completion_tokens = _to_int(usage.get("output_tokens"))
        total_tokens = _to_int(usage.get("total_tokens"))
        if prompt_tokens is not None or completion_tokens is not None or total_tokens is not None:
            return {
                "prompt_tokens": prompt_tokens or 0,
                "completion_tokens": completion_tokens or 0,
                "total_tokens": total_tokens or 0,
            }

    metadata = getattr(message, "response_metadata", None)
    if isinstance(metadata, dict):
        token_usage = metadata.get("token_usage")
        if isinstance(token_usage, dict):
            prompt_tokens = _to_int(token_usage.get("prompt_tokens"))
            completion_tokens = _to_int(token_usage.get("completion_tokens"))
            total_tokens = _to_int(token_usage.get("total_tokens"))
            if prompt_tokens is not None or completion_tokens is not None or total_tokens is not None:
                return {
                    "prompt_tokens": prompt_tokens or 0,
                    "completion_tokens": completion_tokens or 0,
                    "total_tokens": total_tokens or 0,
                }

        prompt_tokens = _to_int(metadata.get("prompt_tokens"))
        completion_tokens = _to_int(metadata.get("completion_tokens"))
        total_tokens = _to_int(metadata.get("total_tokens"))
        if prompt_tokens is not None or completion_tokens is not None or total_tokens is not None:
            return {
                "prompt_tokens": prompt_tokens or 0,
                "completion_tokens": completion_tokens or 0,
                "total_tokens": total_tokens or 0,
            }

    return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def _compute_step_token_usage(agent: Any, prompt: str, model_name: str | None = None) -> dict[str, Any]:
    """Compute approximate token usage per agent step and aggregate totals."""
    state = getattr(agent, "_conversation_state", None)
    if not isinstance(state, dict):
        state = {}
    messages = state.get("messages", [])
    if not isinstance(messages, list):
        messages = []

    steps: list[dict[str, Any]] = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    previous_human = prompt
    step_no = 0

    for message in messages:
        # Human turns are treated as prompt contexts for following AI turns.
        if hasattr(message, "content") and message.__class__.__name__ == "HumanMessage":
            previous_human = "" if message.content is None else str(message.content)
            continue

        if not hasattr(message, "content"):
            continue

        # Count only AI outputs as LLM steps.
        from langchain_core.messages import AIMessage, HumanMessage

        if not isinstance(message, AIMessage):
            continue

        message_content = str(message.content or "")
        step_no += 1
        usage = _extract_message_token_usage(message)
        has_explicit_usage = usage["total_tokens"] > 0 or usage["prompt_tokens"] > 0 or usage["completion_tokens"] > 0

        if has_explicit_usage:
            prompt_tokens = usage["prompt_tokens"]
            completion_tokens = usage["completion_tokens"]
            total_step_tokens = usage["total_tokens"] or (prompt_tokens + completion_tokens)
        else:
            # Fallback: best-effort token estimate
            prompt_tokens = _estimate_tokens(previous_human, model_name=model_name)
            completion_tokens = _estimate_tokens(message_content, model_name=model_name)
            total_step_tokens = prompt_tokens + completion_tokens

        steps.append(
            {
                "step": step_no,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_step_tokens,
            }
        )
        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens
        total_tokens += total_step_tokens

        previous_human = ""

    return {
        "steps": steps,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "step_count": len(steps),
    }


def _canonicalize_letter_answer(task_name: str, text: str, valid_options: list[str] | None = None) -> str:
    answer_tags = _extract_answer_tags(text)
    if answer_tags:
        last_answer_tag = answer_tags[-1]
        if not valid_options or last_answer_tag in valid_options:
            return last_answer_tag
        if valid_options:
            print(
                f"Invalid option '{last_answer_tag}' extracted, valid range: "
                f"{valid_options[0]}-{valid_options[-1]}"
            )

    stripped = text.strip()
    if len(stripped) == 1 and stripped.isalpha():
        letter = stripped.upper()
        if not valid_options:
            return letter
        if letter in valid_options:
            return letter
        print(f"Invalid option '{letter}' extracted, valid range: {valid_options[0]}-{valid_options[-1]}")
        return ""

    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    for line in reversed(lines):
        if len(line) <= 6:
            match = re.fullmatch(r"[\[\(\{]?\s*([A-Za-z])\s*[\]\)\}]?", line)
            if match:
                letter = match.group(1).upper()
                if not valid_options:
                    return letter
                if letter in valid_options:
                    return letter
                print(
                    f"Invalid option '{letter}' extracted, valid range: "
                    f"{valid_options[0]}-{valid_options[-1]}"
                )
                continue

    pattern = r"\b([A-Fa-f])\b" if task_name == "crispr_delivery" else r"\b([A-Za-z])\b"
    match = re.search(pattern, stripped)
    if match:
        letter = match.group(1).upper()
        if not valid_options:
            return letter
        if letter in valid_options:
            return letter
        print(f"Invalid option '{letter}' extracted, valid range: {valid_options[0]}-{valid_options[-1]}")
        return ""

    if answer_tags:
        for tag in reversed(answer_tags):
            if not valid_options or tag in valid_options:
                return tag

    return stripped


def _canonicalize_variant_answer(text: str, prompt: str) -> str:
    prompt_candidates = _extract_candidate_variants(prompt)
    prompt_map = {item.lower(): item for item in prompt_candidates}
    structured_text = _coerce_structured_text_value(text)
    text_candidates = re.findall(r"\brs\d+\b", structured_text, flags=re.IGNORECASE)

    if text_candidates:
        return text_candidates[-1]

    if prompt_candidates:
        for candidate in prompt_candidates:
            if re.search(rf"\b{re.escape(candidate)}\b", text, flags=re.IGNORECASE):
                return candidate

    return structured_text if structured_text else text.strip()


def _canonicalize_rare_disease_answer(text: str) -> str:
    structured_text = _coerce_structured_text_value(text)
    omim_candidates = re.findall(r"\b\d{6}\b", structured_text)

    if omim_candidates:
        return json.dumps({"OMIM_ID": str(omim_candidates[-1])})

    normalized = structured_text.strip()
    if normalized:
        return json.dumps({"OMIM_ID": normalized})
    return ""


def _canonicalize_gene_answer(text: str, prompt: str) -> str:
    structured_text = _coerce_structured_text_value(text)
    check_text = structured_text or text
    ensg_candidates = re.findall(r"\bENSG\d{11}\b", check_text)
    if ensg_candidates:
        return ensg_candidates[-1]

    candidates = _extract_candidate_genes(prompt)
    if not candidates:
        return check_text.strip()

    for candidate in candidates:
        if _contains_token(check_text, candidate):
            return candidate

    return check_text.strip()


def normalize_prediction_for_scoring(task_name: str, prompt: str, prediction: Any) -> str:
    text = _flatten_content_blocks(prediction).strip()
    if not text:
        return ""

    if task_name != "gwas_variant_prioritization":
        text = _extract_solution_text(text).strip()
    answer_tag = _extract_answer_tag(text)
    if answer_tag:
        text = answer_tag

    if task_name in {"crispr_delivery", "hle"} or task_name.startswith("lab_bench"):
        valid_options = _extract_lab_bench_option_letters(prompt) if task_name.startswith("lab_bench") else None
        return _canonicalize_letter_answer(task_name, text, valid_options=valid_options)

    if task_name == "gwas_variant_prioritization":
        return _canonicalize_variant_answer(text, prompt)

    if task_name == "rare_disease_diagnosis":
        return _canonicalize_rare_disease_answer(text)

    if task_name.startswith("gwas_causal_gene") or task_name == "screen_gene_retrieval":
        return _canonicalize_gene_answer(text, prompt)
    if task_name == "patient_gene_detection":
        return _canonicalize_gene_answer(text, prompt)

    return text.strip()


def _extract_last_tool(trajectory: list[Any], agent: Any) -> str:
    known_tools = {
        "query_monarch",
        "query_gwas_catalog",
        "query_ensembl",
        "query_info",
        "query_uniprot",
        "query_pubmed",
        "query_scholar",
        "blast_sequence",
        "get_rna_seq_archs4",
        "query_hpo",
    }

    def _scan_text(value: str) -> str:
        for tool_name in known_tools:
            if re.search(rf"\b{re.escape(tool_name)}\b", value):
                return tool_name
        return ""

    for step in reversed(trajectory or []):
        step_text = str(step.get("content", step) if isinstance(step, dict) else step)
        for execute_block in re.findall(r"<execute>(.*?)</execute>", step_text, re.IGNORECASE | re.DOTALL):
            last_seen = _scan_text(execute_block)
            if last_seen:
                return last_seen
        match = _scan_text(step_text)
        if match:
            return match

    state = getattr(agent, "_conversation_state", None)
    messages = getattr(state, "get", lambda key, default=None: None)("messages", []) if isinstance(state, dict) else []
    if isinstance(messages, list):
        for message in reversed(messages):
            content = getattr(message, "content", message)
            last_seen = _scan_text(str(content))
            if last_seen:
                return last_seen

    return "unknown"


def _count_tool_calls_from_trajectory(trajectory: list[Any]) -> int:
    """Estimate tool calls from serialized trajectory entries."""
    count = 0
    for step in trajectory:
        text = ""
        if isinstance(step, dict):
            text = str(step.get("content", ""))
        else:
            text = str(step)
        if not text:
            continue

        execute_hits = len(re.findall(r"<execute>", text, flags=re.IGNORECASE))
        if execute_hits:
            count += execute_hits
            continue

        if "Tool:" in text or "Invoking:" in text or "tool call" in text.lower():
            count += 1
    return count


def _count_tool_calls_from_agent_state(agent: Any) -> int:
    """Fallback tool-call counting using the agent's final conversation state."""
    state = getattr(agent, "_conversation_state", None)
    if not isinstance(state, dict):
        return 0

    messages = state.get("messages", [])
    if not isinstance(messages, list):
        return 0

    count = 0
    for message in messages:
        content = getattr(message, "content", message)
        text = str(content)
        observation_hits = len(re.findall(r"<observation>", text, flags=re.IGNORECASE))
        if observation_hits:
            # One observation is emitted per execute call.
            count += observation_hits
            continue

        # Fallback for cases where observation messages are missing.
        count += len(re.findall(r"<execute>", text, flags=re.IGNORECASE))
    return count


class EvaluationPipeline:
    def __init__(
        self,
        benchmark: Benchmark,
        agent_factory,
        logger: BaseLogger,
        max_instances: Optional[int] = None,
        agent_config: Optional[Dict[str, Any]] = None,
        completed_instance_ids: Optional[Dict[str, set[str]]] = None,
    ):
        """
        Args:
            benchmark: The benchmark adapter to use.
            agent_factory: A function/callable that returns a fresh agent instance.
            logger: The logger to use.
            max_instances: Max instances per task to evaluate (for debugging/testing).
            agent_config: Configuration dictionary for the agent.
        """
        self.benchmark = benchmark
        self.agent_factory = agent_factory
        self.logger = logger
        self.max_instances = max_instances
        self.agent_config = agent_config or {}
        self.completed_instance_ids = completed_instance_ids or {}
        self.instance_timeout_seconds = self.agent_config.pop("agent_timeout_seconds", None)
        self.data_root = default_config.path
        self.instance_hard_timeout_seconds = _coerce_env_int(
            "BIOMNI_INSTANCE_HARD_TIMEOUT_SECONDS",
            30 * 60,
        )
        self.patient_gene_local_kg_enabled = _coerce_env_bool(
            "BIOMNI_PATIENT_GENE_LOCAL_KG_ENABLED", True
        )
        self.patient_gene_local_kg_confidence = _coerce_env_float(
            "BIOMNI_PATIENT_GENE_LOCAL_KG_CONFIDENCE", 1.5
        )
        self.patient_gene_local_kg_max_candidates = _coerce_env_int(
            "BIOMNI_PATIENT_GENE_LOCAL_KG_MAX_CANDIDATES", 100
        )
        self.gwas_variant_tool_call_limit = _coerce_env_int(
            "BIOMNI_GWAS_TASK_TOOL_CALL_MAX", 12
        )
        self.gwas_task_instance_timeout_seconds = _coerce_env_int(
            "BIOMNI_GWAS_INSTANCE_TIMEOUT_SECONDS", 180
        )
        self.gwas_task_step_timeout_seconds = _coerce_env_int(
            "BIOMNI_GWAS_STEP_TIMEOUT_SECONDS", 90
        )
        self.gwas_task_max_steps = _coerce_env_int(
            "BIOMNI_GWAS_TASK_MAX_STEPS", 24
        )
        self.gwas_task_max_recursion = _coerce_env_int(
            "BIOMNI_GWAS_TASK_RECURSION_LIMIT", 24
        )

        self._patient_gene_local_kg_resources: dict[str, Any] = {
            "loaded": False,
            "p2g_gene_hpo_map": {},
            "gene_hpo_map": {},
            "ensg_to_symbol": {},
            "symbol_to_ensg": {},
            "load_error": None,
        }

    def _configure_task_tool_budget(self, agent: Any, task_name: str) -> None:
        """Set optional per-task cumulative tool-call limits on the agent."""
        is_gwas_task = task_name == "gwas_variant_prioritization"
        task_limit = self.gwas_variant_tool_call_limit if is_gwas_task else None
        if task_limit and task_limit > 0:
            setattr(agent, "_task_tool_call_limit", int(task_limit))
        else:
            setattr(agent, "_task_tool_call_limit", None)

        setattr(agent, "_task_name", task_name)
        if is_gwas_task:
            setattr(agent, "_task_recursion_limit", max(1, self.gwas_task_max_recursion))
            setattr(agent, "_task_step_timeout_seconds", max(1, self.gwas_task_step_timeout_seconds))
            setattr(agent, "_task_max_steps", max(1, self.gwas_task_max_steps))
        else:
            setattr(agent, "_task_recursion_limit", None)
            setattr(agent, "_task_step_timeout_seconds", None)
            setattr(agent, "_task_max_steps", None)

        setattr(agent, "_task_tool_call_count", 0)


    def _load_patient_gene_local_kg_resources(self) -> None:
        """Load and cache local KG / gene_info resources for patient-gene task.

        Primary: builds ``p2g_gene_hpo_map`` (gene_symbol → set of HPO ID
        strings "HP:XXXXXXX") from the HPO ``phenotype_to_genes.txt`` file.
        Fallback: builds ``gene_hpo_map`` from the KG's gene→phenotype edges
        (1621 genes, HPO IDs as integers) for genes not in p2g.
        """
        if self._patient_gene_local_kg_resources["loaded"]:
            return

        if not self.patient_gene_local_kg_enabled:
            self._patient_gene_local_kg_resources["loaded"] = True
            self._patient_gene_local_kg_resources["load_error"] = "disabled"
            return

        data_root = self.data_root
        p2g_path = os.path.join(data_root, "data_lake", "phenotype_to_genes.txt")
        gene_info_path = os.path.join(data_root, "data_lake", "gene_info.parquet")

        try:
            # ── Load gene_info for ENSG→symbol mapping ──────────────────────
            gene_info_df = pd.read_parquet(gene_info_path, columns=["ensembl_gene_id", "gene_name"])
            gene_info_df["ensembl_gene_id"] = gene_info_df["ensembl_gene_id"].fillna("").astype(str).str.strip()
            gene_info_df["gene_name"] = gene_info_df["gene_name"].fillna("").astype(str).str.strip()

            ensg_to_symbol: dict[str, str] = {}
            symbol_to_ensg: dict[str, str] = {}
            for _, row in gene_info_df.iterrows():
                ensg = str(row.get("ensembl_gene_id", "")).strip().upper()
                symbol = str(row.get("gene_name", "")).strip()
                if not ensg or not symbol:
                    continue
                ensg_to_symbol[ensg] = symbol
                symbol_to_ensg[symbol.upper()] = ensg

            # ── Primary: HPO phenotype_to_genes.txt ─────────────────────────
            p2g_gene_hpo_map: dict[str, set[str]] = defaultdict(set)
            if os.path.exists(p2g_path):
                p2g_df = pd.read_csv(
                    p2g_path,
                    sep="\t",
                    comment="#",
                    header=0,
                    usecols=["hpo_id", "gene_symbol"],
                    dtype=str,
                )
                for _, row in p2g_df.iterrows():
                    gene = str(row["gene_symbol"]).strip()
                    hpo = str(row["hpo_id"]).strip()
                    if gene and hpo:
                        p2g_gene_hpo_map[gene].add(hpo)
                print(f"[local_patient_kg] loaded {len(p2g_gene_hpo_map)} genes from phenotype_to_genes.txt")
            else:
                print("[local_patient_kg] phenotype_to_genes.txt not found; falling back to KG-only")

            # ── Fallback: KG gene→phenotype edges ───────────────────────────
            kg_path = os.path.join(data_root, "data_lake", "kg.csv")
            gene_hpo_map: dict[str, set[int]] = {}
            if os.path.exists(kg_path):
                kg_df = pd.read_csv(
                    kg_path,
                    usecols=["x_type", "y_type", "x_name", "y_id"],
                    low_memory=False,
                )
                gp = kg_df[
                    (kg_df["x_type"] == "gene/protein")
                    & (kg_df["y_type"] == "effect/phenotype")
                ].copy()
                _kg_tmp: dict[str, set[int]] = defaultdict(set)
                for _, row in gp.iterrows():
                    gene = str(row["x_name"]).strip()
                    if not gene:
                        continue
                    try:
                        hpo_id = int(row["y_id"])
                    except (TypeError, ValueError):
                        continue
                    _kg_tmp[gene.lower()].add(hpo_id)
                gene_hpo_map = dict(_kg_tmp)
                del kg_df, gp
                print(f"[local_patient_kg] loaded {len(gene_hpo_map)} genes from kg.csv")

            self._patient_gene_local_kg_resources.update(
                {
                    "loaded": True,
                    "p2g_gene_hpo_map": dict(p2g_gene_hpo_map),
                    "gene_hpo_map": gene_hpo_map,
                    "ensg_to_symbol": ensg_to_symbol,
                    "symbol_to_ensg": symbol_to_ensg,
                    "load_error": None,
                }
            )
        except Exception as exc:
            self._patient_gene_local_kg_resources["loaded"] = True
            self._patient_gene_local_kg_resources["load_error"] = str(exc)
            self._patient_gene_local_kg_resources["p2g_gene_hpo_map"] = {}
            self._patient_gene_local_kg_resources["gene_hpo_map"] = {}
            self._patient_gene_local_kg_resources["ensg_to_symbol"] = {}
            self._patient_gene_local_kg_resources["symbol_to_ensg"] = {}

    def _solve_patient_gene_from_local_kg(self, prompt: str) -> dict[str, Any] | None:
        """Try to solve patient-gene instance via local HPO phenotype matching.

        Algorithm (primary path — phenotype_to_genes.txt):
        1. Extract candidate ENSG IDs and patient HPO IDs from the prompt.
        2. Map each ENSG → gene symbol via ensg_to_symbol.
        3. For each candidate, score = |patient_HPOs ∩ gene_HPOs| using
           the HPO phenotype_to_genes.txt mapping (gene_symbol → set["HP:XXXXXXX"]).
        4. Confidence = top1_overlap / (top2_overlap + 1).
        5. If confidence ≥ threshold → solve locally; else → fall back to agent.

        Falls back to KG-based integer HPO matching for genes not in p2g.
        """
        if not self.patient_gene_local_kg_enabled:
            return None

        candidates, _phenotypes = _extract_patient_task_tokens(prompt)
        if not candidates:
            return None

        self._load_patient_gene_local_kg_resources()
        resources = self._patient_gene_local_kg_resources

        if not resources.get("loaded"):
            return None

        if resources.get("load_error"):
            if resources.get("load_error") != "disabled":
                print(f"[local_patient_kg] resource load skipped: {resources.get('load_error')}")
            return None

        p2g_gene_hpo_map: dict[str, set[str]] = resources.get("p2g_gene_hpo_map", {})
        ensg_to_symbol: dict[str, str] = resources.get("ensg_to_symbol", {})

        # Collect patient HPO IDs in canonical "HP:XXXXXXX" form
        patient_hpos_str: set[str] = set(re.findall(r"HP:\d{7}", prompt, flags=re.IGNORECASE))
        # Normalise casing
        patient_hpos_str = {h.upper() for h in patient_hpos_str}

        if not patient_hpos_str:
            return None

        candidates = candidates[: self.patient_gene_local_kg_max_candidates]

        # Score each candidate by HPO overlap using phenotype_to_genes.txt
        candidate_scores: list[tuple[str, int, str]] = []  # (ensg, overlap, symbol)
        for raw in candidates:
            ensg = raw.strip().upper()
            if not (ensg.startswith("ENSG") and re.fullmatch(r"ENSG\d{11}", ensg)):
                continue

            symbol = ensg_to_symbol.get(ensg, "")
            if not symbol:
                continue

            gene_hpos_str = p2g_gene_hpo_map.get(symbol, set())
            overlap = len(patient_hpos_str & gene_hpos_str)
            candidate_scores.append((ensg, overlap, symbol))

        if not candidate_scores:
            return None

        # Sort by overlap descending
        candidate_scores.sort(key=lambda x: x[1], reverse=True)

        top1_ensg, top1_overlap, top1_symbol = candidate_scores[0]
        top2_overlap = candidate_scores[1][1] if len(candidate_scores) > 1 else 0

        # If top1 has no HPO matches, fall back to agent
        if top1_overlap == 0:
            return {
                "method": "local_kg_no_overlap",
                "confidence": 0.0,
                "top2_scores": [(c[0], c[1]) for c in candidate_scores[:2]],
                "solved": False,
                "prediction": None,
            }

        # Confidence: how much better is top1 vs top2
        confidence = top1_overlap / (top2_overlap + 1)

        debug_info = {
            "candidate": top1_ensg,
            "symbol": top1_symbol,
            "overlap": top1_overlap,
            "patient_hpo_count": len(patient_hpos_str),
        }
        print(
            f"[local_patient_kg] top1={top1_symbol}({top1_ensg}) overlap={top1_overlap} "
            f"top2_overlap={top2_overlap} confidence={confidence:.2f} "
            f"patient_hpos={len(patient_hpos_str)}"
        )

        if confidence < self.patient_gene_local_kg_confidence:
            return {
                "method": "local_kg_fallback",
                "confidence": confidence,
                "top2_scores": [(c[0], c[1]) for c in candidate_scores[:2]],
                "solved": False,
                "prediction": None,
                "prediction_meta": debug_info,
            }

        return {
            "method": "local_p2g",
            "confidence": confidence,
            "top2_scores": [(c[0], c[1]) for c in candidate_scores[:2]],
            "solved": True,
            "prediction": {"causal_gene": [top1_ensg]},
            "prediction_meta": debug_info,
        }

    def _get_instances_to_evaluate(self, task_name: str, split: str) -> list[Dict[str, Any]]:
        instances = self.benchmark.get_instances(task_name, split)

        completed = self.completed_instance_ids.get(task_name, set())
        if completed:
            instances = [instance for instance in instances if str(instance["instance_id"]) not in completed]

        if self.max_instances is not None:
            instances = instances[: self.max_instances]

        return instances

    def run(self, tasks: Optional[List[str]] = None, split: str = "val"):
        """
        Run the evaluation pipeline.

        Args:
            tasks: List of task names to evaluate. If None, runs all tasks.
            split: Dataset split to use (e.g., 'val', 'test').
        """
        available_tasks = self.benchmark.get_tasks()

        if tasks is None:
            tasks = available_tasks
        else:
            tasks = [t for t in tasks if t in available_tasks]
            if not tasks:
                print("No valid tasks found to evaluate.")
                return

        config = {
            "benchmark_id": self.benchmark.id,
            "tasks": tasks,
            "split": split,
            "max_instances": self.max_instances,
            "timestamp": time.time(),
        }
        self.logger.log_config(config)

        total_instances = 0
        for task_name in tasks:
            instances = self._get_instances_to_evaluate(task_name, split)
            total_instances += len(instances)

        print(f"Starting evaluation on {len(tasks)} tasks: {tasks}")
        print(f"Total instances to evaluate: {total_instances}")

        task_summaries: list[dict[str, Any]] = []

        with tqdm(total=total_instances, desc="Overall Progress", unit="inst") as pbar:
            for task_name in tasks:
                summary = self._evaluate_task(task_name, split, pbar)
                if summary is not None:
                    task_summaries.append(summary)

        self._print_summary(task_summaries)
        self.logger.finish()

    def _evaluate_task(self, task_name: str, split: str, pbar: tqdm) -> dict[str, Any] | None:
        pbar.write(f"\n=== Evaluating Task: {task_name} ===")
        instances = self._get_instances_to_evaluate(task_name, split)

        if not instances:
            pbar.write(f"Task {task_name} already completed or empty. Skipping.")
            return {
                "task_name": task_name,
                "instances": 0,
                "accuracy": 0.0,
                "avg_score": 0.0,
                "successes": 0,
            }

        success_count = 0
        total_score = 0.0

        for i, instance in enumerate(instances):
            pbar.write(f"[{task_name}] Processing instance {i + 1}/{len(instances)} (ID: {instance['instance_id']})")

            # Create a fresh agent for each instance to avoid state leakage.
            agent = self.agent_factory()

            # Reset shared Python REPL namespace so one instance does not leak to another.
            reset_python_repl_namespace(preload_defaults=True)

            if self.agent_config:
                agent.configure(**self.agent_config)

            # Enforce hard per-instance timeout and continue on timeout with 0 score.
            instance_start_time = time.time()
            hard_timeout = self.instance_hard_timeout_seconds
            if hard_timeout is not None and hard_timeout <= 0:
                hard_timeout = None

            if hard_timeout is None:
                result_data = self._process_instance(agent, task_name, instance)
            else:
                run_result = run_with_timeout(
                    self._process_instance,
                    args=[agent, task_name, instance],
                    timeout=hard_timeout,
                )
                if isinstance(run_result, dict):
                    result_data = run_result
                else:
                    timeout_seconds = hard_timeout
                    elapsed = None
                    if isinstance(run_result, str):
                        elapsed_match = re.search(r"elapsed=([0-9]+(?:\.[0-9]+)?)s", run_result)
                        if elapsed_match:
                            try:
                                elapsed = float(elapsed_match.group(1))
                            except ValueError:
                                elapsed = None
                    result_data = {
                        "task_name": task_name,
                        "instance_id": instance["instance_id"],
                        "prompt": instance["prompt"],
                        "prediction": "ERROR",
                        "ground_truth": instance["ground_truth"],
                        "score": 0.0,
                        "success": False,
                        "error": run_result if isinstance(run_result, str) else str(run_result),
                        "trajectory": [],
                        "metrics": {
                            "latency": time.time() - instance_start_time,
                            "tool_calls": 0,
                            "timeout_source": "run_with_timeout",
                            "elapsed_seconds": elapsed,
                            "tool_calls_before_timeout": 0,
                            "last_tool_used": None,
                            "patient_gene_local_kg_used": False,
                            "patient_gene_local_kg_confidence": None,
                            "patient_gene_local_kg_method": None,
                            "patient_gene_local_kg_top2_scores": None,
                            "patient_gene_local_kg_prediction_score": None,
                            "raw_response_type": type(run_result).__name__,
                            "normalized_prediction_len": 0,
                            "token_steps": None,
                            "token_prompt_total": None,
                            "token_completion_total": None,
                            "token_total": None,
                        },
                    }
                    if elapsed is None:
                        elapsed = time.time() - instance_start_time
                    print(
                        f"[timeout] task={task_name} instance={instance['instance_id']} "
                        f"source=run_with_timeout timeout={timeout_seconds} elapsed={elapsed}s reason={result_data['error']}"
                    )

            self.logger.log_result(result_data)

            if result_data["success"]:
                success_count += 1
            total_score += result_data["score"]
            pbar.update(1)

        if instances:
            task_metrics = {
                f"{task_name}/accuracy": success_count / len(instances),
                f"{task_name}/avg_score": total_score / len(instances),
                f"{task_name}/count": len(instances),
            }
            self.logger.log_metrics(task_metrics)
            pbar.write(f"Task {task_name} finished. Accuracy: {task_metrics[f'{task_name}/accuracy']:.2f}")

            return {
                "task_name": task_name,
                "instances": len(instances),
                "accuracy": task_metrics[f"{task_name}/accuracy"],
                "avg_score": task_metrics[f"{task_name}/avg_score"],
                "successes": success_count,
            }

        return {
            "task_name": task_name,
            "instances": 0,
            "accuracy": 0.0,
            "avg_score": 0.0,
            "successes": 0,
        }

    def _print_summary(self, task_summaries: list[dict[str, Any]]):
        if not task_summaries:
            print("No task results to summarize.")
            return

        print("\n=== Evaluation Summary (per task) ===")
        total_instances = sum(item["instances"] for item in task_summaries)
        total_success = sum(item["successes"] for item in task_summaries)
        for item in task_summaries:
            task_name = item["task_name"]
            print(
                f"{task_name}: accuracy={item['accuracy']:.4f} "
                f"({item['successes']}/{item['instances']}), "
                f"avg_score={item['avg_score']:.4f}"
            )

        overall_accuracy = (total_success / total_instances) if total_instances else 0.0
        print(f"Overall: accuracy={overall_accuracy:.4f} ({total_success}/{total_instances})")

    def _process_instance(self, agent: Any, task_name: str, instance: Dict[str, Any]) -> Dict[str, Any]:
        prompt = instance["prompt"]
        start_time = time.time()

        raw_response: Any = None
        prediction = ""
        trajectory: list[str] = []
        error = None
        score = 0.0
        instance_timed_out = False
        timeout_meta: dict[str, Any] | None = None
        local_kg_meta: dict[str, Any] = {}
        used_local_patient_kg = False

        def _is_execution_error_output(value: Any) -> bool:
            if not isinstance(value, str):
                return False
            prefixes = (
                "TIMEOUT:",
                "ERROR:",
                "Error in execution:",
                "GWAS_TIMEOUT:",
                "MONARCH_TIMEOUT:",
                "ENSEMBL_TIMEOUT:",
            )
            return any(value.startswith(prefix) for prefix in prefixes)

        def _extract_timeout_metadata(raw: str) -> tuple[float | None, str | None]:
            if not isinstance(raw, str):
                return None, None

            lowered = raw.lower()
            if "GWAS_TIMEOUT:" in raw:
                source = "query_gwas_catalog"
            elif "MONARCH_TIMEOUT:" in raw:
                source = "query_monarch"
            elif "ENSEMBL_TIMEOUT:" in raw:
                source = "query_ensembl"
            elif "run_with_timeout" in lowered or "timed out" in lowered:
                source = "run_with_timeout"
            else:
                source = None

            match = re.search(r"elapsed=([0-9]+(?:\.[0-9]+)?)s", raw)
            if match:
                try:
                    return float(match.group(1)), source
                except ValueError:
                    pass
            if "timed out" in lowered:
                return None, source
            return None, None

        try:
            local_patient_solution = (
                self._solve_patient_gene_from_local_kg(prompt)
                if task_name == "patient_gene_detection"
                else None
            )
            self._configure_task_tool_budget(agent, task_name)

            if local_patient_solution and local_patient_solution.get("solved"):
                used_local_patient_kg = True
                local_kg_meta = {
                    "patient_gene_local_kg_used": True,
                    "patient_gene_local_kg_confidence": local_patient_solution.get("confidence"),
                    "patient_gene_local_kg_method": local_patient_solution.get("method"),
                    "patient_gene_local_kg_top2_scores": local_patient_solution.get("top2_scores"),
                    "patient_gene_local_kg_prediction_score": (
                        local_patient_solution.get("prediction_meta", {}).get("score") if local_patient_solution else None
                    ),
                }
                prediction = local_patient_solution["prediction"]
                raw_response = prediction
                trajectory = ["<solution>local_patient_gene_kg</solution>"]
            else:
                local_kg_meta = {
                    "patient_gene_local_kg_used": False,
                    "patient_gene_local_kg_confidence": (
                        local_patient_solution.get("confidence") if local_patient_solution else None
                    ),
                    "patient_gene_local_kg_method": (
                        local_patient_solution.get("method") if local_patient_solution else None
                    ),
                    "patient_gene_local_kg_top2_scores": (
                        local_patient_solution.get("top2_scores") if local_patient_solution else None
                    ),
                    "patient_gene_local_kg_prediction_score": None,
                }
                # Prefer explicit run timeout from CLI, but keep hard timeout as a ceiling.
                task_timeout = self.instance_timeout_seconds
                if self.instance_hard_timeout_seconds is not None and self.instance_hard_timeout_seconds > 0:
                    if task_timeout is None or task_timeout > self.instance_hard_timeout_seconds:
                        task_timeout = self.instance_hard_timeout_seconds
                if task_timeout is None and task_name == "gwas_variant_prioritization":
                    task_timeout = self.gwas_task_instance_timeout_seconds
                    if (
                        self.instance_hard_timeout_seconds is not None
                        and self.instance_hard_timeout_seconds > 0
                        and task_timeout > self.instance_hard_timeout_seconds
                    ):
                        task_timeout = self.instance_hard_timeout_seconds

                if task_timeout is None:
                    log, raw_response = agent.go(prompt)
                else:
                    run_result = run_with_timeout(agent.go, args=[prompt], timeout=task_timeout)

                    if isinstance(run_result, tuple) and len(run_result) == 2:
                        log, raw_response = run_result
                    elif _is_execution_error_output(run_result):
                        instance_timed_out = True
                        prediction = "ERROR"
                        error = run_result
                        timeout_elapsed, timeout_source = _extract_timeout_metadata(error)
                        timeout_meta = {
                            "source": timeout_source,
                            "timeout_seconds": task_timeout,
                            "elapsed_seconds": timeout_elapsed,
                        }
                        raw_response = run_result
                        trajectory = []
                    else:
                        # Unexpected return value from timeout wrapper
                        instance_timed_out = True
                        prediction = "ERROR"
                        error = f"Unexpected run_with_timeout result: {run_result!r}"
                        raw_response = str(run_result)
                        trajectory = []

            if not instance_timed_out and not used_local_patient_kg:
                trajectory = log
                if _is_execution_error_output(raw_response):
                    instance_timed_out = True
                    error = raw_response
                    prediction = "ERROR"
                else:
                    prediction = normalize_prediction_for_scoring(
                        task_name=task_name, prompt=prompt, prediction=raw_response
                    )

            if instance_timed_out and error:
                if timeout_meta is None and isinstance(error, str) and "timed out" in error.lower():
                    timeout_elapsed, timeout_source = _extract_timeout_metadata(error)
                    timeout_meta = {
                        "source": timeout_source,
                        "timeout_seconds": task_timeout if task_timeout is not None else self.instance_timeout_seconds,
                        "elapsed_seconds": timeout_elapsed,
                    }

                if timeout_meta:
                    print(
                        f"[timeout] task={task_name} instance={instance['instance_id']} "
                        f"source={timeout_meta.get('source', 'run_with_timeout')} "
                        f"timeout={timeout_meta.get('timeout_seconds')} "
                        f"elapsed={timeout_meta.get('elapsed_seconds')}s reason={error}"
                    )
                else:
                    print(f"[timeout] Instance {instance['instance_id']} on task {task_name}: {error}")

            if not instance_timed_out and prediction != "ERROR":
                try:
                    score = self.benchmark.evaluate_result(task_name, instance, prediction)
                except Exception as eval_error:
                    preview = prediction[:240].replace("\n", "\\n")
                    print(f"Evaluation error for {task_name}/{instance['instance_id']}: {eval_error}")
                    print(
                        "Debug:"
                        f" raw_response_type={type(raw_response).__name__},"
                        f" normalized_prediction_len={len(prediction)},"
                        f" normalized_prediction_preview={preview}"
                    )
                    traceback.print_exc()
                    error = str(eval_error)
                    score = 0.0

        except Exception as exc:
            error = str(exc)
            traceback.print_exc()
            prediction = "ERROR"
            score = 0.0

        end_time = time.time()
        success = score == 1.0
        model_name = None
        llm_obj = getattr(agent, "llm", None)
        if llm_obj is not None:
            model_name = getattr(llm_obj, "model_name", None)

        token_usage = _compute_step_token_usage(agent, prompt, model_name=model_name)
        if token_usage.get("step_count"):
            print(
                f"[token] task={task_name} instance={instance['instance_id']} "
                f"steps={token_usage['step_count']} "
                f"prompt_tokens={token_usage['total_prompt_tokens']} "
                f"completion_tokens={token_usage['total_completion_tokens']} "
                f"total_tokens={token_usage['total_tokens']}"
            )
            for step in token_usage["steps"]:
                print(
                    f"[token-step] task={task_name} instance={instance['instance_id']} "
                    f"step={step['step']} prompt={step['prompt_tokens']} "
                    f"completion={step['completion_tokens']} total={step['total_tokens']}"
                )

        tool_calls = _count_tool_calls_from_trajectory(trajectory)
        if tool_calls == 0:
            tool_calls = _count_tool_calls_from_agent_state(agent)
        last_tool = _extract_last_tool(trajectory, agent)
        if instance_timed_out:
            timeout_meta = timeout_meta or {}
            timeout_meta = dict(timeout_meta)
            timeout_meta.setdefault("tool_calls_before_timeout", tool_calls)
            timeout_meta.setdefault("last_tool_used", last_tool)

        if timeout_meta:
            print(
                f"[timeout] task={task_name} instance={instance['instance_id']} "
                f"tool_calls_before_timeout={timeout_meta.get('tool_calls_before_timeout')} "
                f"last_tool_used={timeout_meta.get('last_tool_used')}"
            )

        return {
            "task_name": task_name,
            "instance_id": instance["instance_id"],
            "prompt": prompt,
            "prediction": prediction,
            "ground_truth": instance["ground_truth"],
            "score": score,
            "success": success,
            "error": error,
            "trajectory": trajectory,
            "metrics": {
                "latency": end_time - start_time,
                "tool_calls": tool_calls,
                "timeout_source": timeout_meta.get("source") if timeout_meta else None,
                "elapsed_seconds": timeout_meta.get("elapsed_seconds") if timeout_meta else None,
                "tool_calls_before_timeout": timeout_meta.get("tool_calls_before_timeout") if timeout_meta else None,
                "last_tool_used": timeout_meta.get("last_tool_used") if timeout_meta else None,
                "patient_gene_local_kg_used": bool(local_kg_meta.get("patient_gene_local_kg_used", False)),
                "patient_gene_local_kg_confidence": local_kg_meta.get("patient_gene_local_kg_confidence"),
                "patient_gene_local_kg_method": local_kg_meta.get("patient_gene_local_kg_method"),
                "patient_gene_local_kg_top2_scores": local_kg_meta.get("patient_gene_local_kg_top2_scores"),
                "patient_gene_local_kg_prediction_score": local_kg_meta.get("patient_gene_local_kg_prediction_score"),
                "raw_response_type": type(raw_response).__name__,
                "normalized_prediction_len": len(prediction),
                "token_steps": token_usage.get("steps"),
                "token_prompt_total": token_usage.get("total_prompt_tokens"),
                "token_completion_total": token_usage.get("total_completion_tokens"),
                "token_total": token_usage.get("total_tokens"),
            },
        }
