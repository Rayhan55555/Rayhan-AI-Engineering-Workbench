import pytest
import json
from backend.app.streaming.sse import format_sse, mock_or_live_execution_stream
from backend.app.streaming.ws_manager import ConnectionManager


def test_sse_format_structure():
    """Verify SSE formatter outputs standard event: <name> \n data: <json> \n\n"""
    formatted = format_sse("thinking", {"step": "Evaluating AST", "progress": 50})
    assert formatted.startswith("event: thinking\n")
    assert "data: " in formatted
    assert formatted.endswith("\n\n")

    # Parse JSON from data line
    data_line = [line for line in formatted.splitlines() if line.startswith("data: ")][0]
    payload = json.loads(data_line.replace("data: ", ""))
    assert payload["step"] == "Evaluating AST"
    assert payload["progress"] == 50


@pytest.mark.asyncio
async def test_sse_stream_sequence():
    """Verify stream generator yields thinking, tool_call, tool_result, llm_start, complete."""
    events = []
    async for item in mock_or_live_execution_stream(
        execution_id="test-exec-1",
        agent_slug="arch-sentinel",
        task_description="Analyze code",
    ):
        event_name = item.splitlines()[0].replace("event: ", "")
        events.append(event_name)

    assert "thinking" in events
    assert "tool_call" in events
    assert "tool_result" in events
    assert "llm_start" in events
    assert "complete" in events


def test_ws_connection_manager_initial_state():
    """Verify connection manager initializes with 0 active users."""
    mgr = ConnectionManager()
    assert mgr.count_active_users() == 0
