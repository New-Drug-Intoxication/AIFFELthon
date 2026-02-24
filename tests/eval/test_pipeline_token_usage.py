from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage

from biomni.eval.pipeline import _compute_step_token_usage


def test_compute_step_token_usage_no_explicit_usage_uses_estimate():
    conversation = {
        "messages": [
            HumanMessage(content="Task prompt"),
            AIMessage(content="<observation>first</observation>"),
            HumanMessage(content="Next prompt"),
            AIMessage(content="Final <solution>A</solution>"),
        ]
    }

    agent = SimpleNamespace(_conversation_state=conversation)
    token_usage = _compute_step_token_usage(agent, "Task prompt")

    assert token_usage["step_count"] == 2
    assert token_usage["total_tokens"] > 0
    assert token_usage["steps"][0]["step"] == 1
    assert token_usage["steps"][1]["step"] == 2


def test_compute_step_token_usage_with_explicit_usage_metadata():
    conversation = {
        "messages": [
            HumanMessage(content="Task prompt"),
            AIMessage(
                content="answer",
                usage_metadata={"input_tokens": 12, "output_tokens": 5, "total_tokens": 17},
            ),
        ]
    }
    agent = SimpleNamespace(_conversation_state=conversation)

    token_usage = _compute_step_token_usage(agent, "Task prompt")

    assert token_usage["step_count"] == 1
    assert token_usage["total_prompt_tokens"] == 12
    assert token_usage["total_completion_tokens"] == 5
    assert token_usage["total_tokens"] == 17
