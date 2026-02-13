from pathlib import Path


def test_code_fence_auto_conversion_logic_removed():
    content = Path("biomni/agent/a1.py").read_text(encoding="utf-8")
    assert "code_block_match = re.search" not in content
    assert "treat it as execute" not in content


def test_retry_message_is_explicit_about_xml_tags():
    content = Path("biomni/agent/a1.py").read_text(encoding="utf-8")
    assert "Regenerate now with EXACTLY one of these formats" in content
    assert "<execute>...code...</execute>" in content
    assert "<solution>...final answer only...</solution>" in content
