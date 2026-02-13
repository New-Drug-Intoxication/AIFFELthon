from types import SimpleNamespace

from langchain_core.messages import AIMessage

from biomni.eval.pipeline import _count_tool_calls_from_agent_state, _count_tool_calls_from_trajectory


def test_count_tool_calls_from_trajectory_uses_execute_tags():
    trajectory = [
        "step 1 <execute>print('a')</execute>",
        "step 2 <execute>print('b')</execute>",
        "final <solution>A</solution>",
    ]
    assert _count_tool_calls_from_trajectory(trajectory) == 2


def test_count_tool_calls_from_agent_state_uses_observation_messages():
    agent = SimpleNamespace(
        _conversation_state={
            "messages": [
                AIMessage(content="<observation>ok1</observation>"),
                AIMessage(content="<observation>ok2</observation>"),
            ]
        }
    )
    assert _count_tool_calls_from_agent_state(agent) == 2
