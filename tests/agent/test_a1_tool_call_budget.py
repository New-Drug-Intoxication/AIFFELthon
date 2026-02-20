import os
from pathlib import Path

from biomni.agent.a1 import A1


def test_a1_tool_call_budget_reads_env_and_fallback(monkeypatch):
    monkeypatch.delenv("BIOMNI_TOOL_CALL_MAX_PER_STEP", raising=False)
    assert A1._get_tool_call_budget() == 20


def test_a1_tool_call_budget_parses_tool_calls_and_executable_threshold(monkeypatch):
    # Exercise parser with multiple tool calls in one execute block.
    monkeypatch.setenv("BIOMNI_TOOL_CALL_MAX_PER_STEP", "1")
    assert A1._get_tool_call_budget() == 1

    # Build minimal A1 instance for helper usage only.
    agent = A1.__new__(A1)
    agent.module2api = {
        "biomni.tool.genomics": [{"name": "query_gwas_catalog"}, {"name": "get_rna_seq_archs4"}],
        "biomni.tool.database": [{"name": "query_uniprot"}],
    }
    agent._custom_functions = {}

    code = """
from biomni.tool.genomics import query_gwas_catalog
from biomni.tool.database import query_uniprot

query_gwas_catalog('type 2 diabetes')
query_uniprot('TP53')
"""

    tools = agent._parse_tool_calls_from_code(code)
    assert len(tools) > int(os.environ["BIOMNI_TOOL_CALL_MAX_PER_STEP"])

    source = Path("biomni/agent/a1.py").read_text(encoding="utf-8")
    assert "Tool call budget exceeded for one step" in source
