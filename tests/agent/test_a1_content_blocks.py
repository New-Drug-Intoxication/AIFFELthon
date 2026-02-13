from types import SimpleNamespace

from biomni.agent.a1 import _flatten_response_content_blocks


def test_flatten_response_content_blocks_handles_mixed_dict_shapes():
    content = [
        {"type": "output_text", "text": "Hello "},
        {"type": "text", "content": "world"},
        {"content": [{"type": "text", "text": "!"}]},
    ]
    assert _flatten_response_content_blocks(content) == "Hello world!"


def test_flatten_response_content_blocks_handles_object_blocks():
    content = [
        SimpleNamespace(text="alpha "),
        SimpleNamespace(content="beta"),
    ]
    assert _flatten_response_content_blocks(content) == "alpha beta"
