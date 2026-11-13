import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional


def format_sse(event: str, data: Any) -> str:
    """Formats a message according to the Server-Sent Events (SSE) standard."""
    json_data = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {json_data}\n\n"


async def mock_or_live_execution_stream(
    execution_id: str,
    agent_slug: str,
    task_description: str,
    tool_calls: Optional[list] = None,
) -> AsyncGenerator[str, None]:
    """
    Yields realistic, real-time SSE execution steps for frontend display:
    1. thinking
    2. tool_call
    3. tool_result
    4. llm_start
    5. llm_chunk
    6. complete
    """
    # 1. Thinking
    yield format_sse("thinking", {
        "execution_id": execution_id,
        "agent": agent_slug,
        "step": "Analyzing task requirements and parameter schemas...",
        "timestamp": asyncio.get_event_loop().time(),
    })
    await asyncio.sleep(0.1)

    # 2. Tool Calls
    calls = tool_calls or [
        {"tool": "fs_read_file", "params": {"path": "src/App.tsx"}},
        {"tool": "shell_run_linter", "params": {"target_path": "backend/app"}},
    ]
    for c in calls:
        yield format_sse("tool_call", {
            "execution_id": execution_id,
            "tool": c["tool"],
            "parameters": c["params"],
            "status": "executing",
        })
        await asyncio.sleep(0.1)
        yield format_sse("tool_result", {
            "execution_id": execution_id,
            "tool": c["tool"],
            "status": "success",
            "summary": f"Completed {c['tool']} with clean exit code.",
        })
        await asyncio.sleep(0.1)

    # 3. LLM Reasoning stream
    yield format_sse("llm_start", {
        "execution_id": execution_id,
        "model": "gemini-1.5-flash",
    })

    chunks = [
        "Synthesizing tool outputs. ",
        "Validating architecture constraints and security rules. ",
        "Generated clean patch and verified sandbox integrity. ",
    ]
    for chunk in chunks:
        yield format_sse("llm_chunk", {"text": chunk})
        await asyncio.sleep(0.08)

    # 4. Complete
    yield format_sse("complete", {
        "execution_id": execution_id,
        "status": "completed",
        "total_steps": len(calls) + 2,
    })
