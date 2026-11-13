import asyncio
import pytest
from httpx import AsyncClient
from backend.app.models.agent import Agent, AgentStatus
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_submit_task_to_planned_agent_fails_with_400(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    # Seed agents (all initialized as Planned)
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)

    payload = {
        "agent_slug": "arch-sentinel",
        "instruction": "Audit codebase schemas",
        "scope": "read_only",
    }
    response = await client.post("/api/v1/executions", json=payload, headers=auth_headers)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "agent_not_available"


@pytest.mark.asyncio
async def test_submit_task_with_implement_scope_blocked_with_403(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    # Seed agents
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)

    # Agent other than arch-sentinel (e.g. curizx-core) cannot use implement scope
    payload = {
        "agent_slug": "curizx-core",
        "instruction": "Refactor codebase AST",
        "scope": "implement",
    }
    response = await client.post("/api/v1/executions", json=payload, headers=auth_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error"] == "scope_restricted"


@pytest.mark.asyncio
async def test_submit_task_to_available_agent_succeeds_with_202(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    # 1. Seed agents
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)

    # 2. Transition flow-executor (stub): Planned -> Configured -> Available
    await client.post("/api/v1/agents/flow-executor/configure", json={}, headers=super_auth_headers)
    status_res = await client.patch(
        "/api/v1/agents/flow-executor/status",
        json={"status": "Available", "reason": "Ready for execution"},
        headers=super_auth_headers,
    )
    assert status_res.status_code == 200

    # 3. Submit task with read_only scope to stub agent
    payload = {
        "agent_slug": "flow-executor",
        "instruction": "Audit document synthesis pipeline",
        "scope": "read_only",
    }
    exec_res = await client.post("/api/v1/executions", json=payload, headers=auth_headers)
    assert exec_res.status_code == 202
    data = exec_res.json()
    assert "execution_id" in data
    assert data["agent_slug"] == "flow-executor"
    assert data["simulated"] is True
    execution_id = data["execution_id"]

    # Allow asyncio background task to complete execution
    res_data = {}
    for _ in range(30):
        get_res = await client.get(f"/api/v1/executions/{execution_id}", headers=auth_headers)
        assert get_res.status_code == 200
        res_data = get_res.json()
        if res_data["status"] != "Pending":
            break
        await asyncio.sleep(0.1)

    assert res_data["id"] == execution_id
    assert res_data["simulated"] is True
    assert res_data["status"] == "Completed"
    assert "[STUB]" in res_data["output"]


@pytest.mark.asyncio
async def test_get_execution_other_user_forbidden(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict, super_auth_headers: dict
):
    # Seed and make agent available
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    await client.post("/api/v1/agents/arch-sentinel/configure", json={}, headers=super_auth_headers)
    await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Available"},
        headers=super_auth_headers,
    )

    # User 1 submits execution
    submit_res = await client.post(
        "/api/v1/executions",
        json={"agent_slug": "arch-sentinel", "instruction": "Private user 1 task", "scope": "read_only"},
        headers=auth_headers,
    )
    execution_id = submit_res.json()["execution_id"]

    # User 2 tries to access User 1's execution -> 403 Forbidden
    forbidden_res = await client.get(f"/api/v1/executions/{execution_id}", headers=other_auth_headers)
    assert forbidden_res.status_code == 403
    assert forbidden_res.json()["error"] == "forbidden"


@pytest.mark.asyncio
async def test_list_executions_with_pagination(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    # Seed & set Available for flow-executor stub
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    await client.post("/api/v1/agents/flow-executor/configure", json={}, headers=super_auth_headers)
    await client.patch(
        "/api/v1/agents/flow-executor/status",
        json={"status": "Available"},
        headers=super_auth_headers,
    )

    # Submit 3 executions
    for i in range(3):
        await client.post(
            "/api/v1/executions",
            json={"agent_slug": "flow-executor", "instruction": f"Workflow task {i}", "scope": "read_only"},
            headers=auth_headers,
        )

    # List page 1 limit 2
    res = await client.get("/api/v1/executions?page=1&limit=2", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["total_pages"] == 2
    for item in data["items"]:
        assert item["simulated"] is True


@pytest.mark.asyncio
async def test_cancel_execution(client: AsyncClient, auth_headers: dict, super_auth_headers: dict):
    # Seed & set Available
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    await client.post("/api/v1/agents/arch-sentinel/configure", json={}, headers=super_auth_headers)
    await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Available"},
        headers=super_auth_headers,
    )

    submit_res = await client.post(
        "/api/v1/executions",
        json={"agent_slug": "arch-sentinel", "instruction": "Task to cancel", "scope": "read_only"},
        headers=auth_headers,
    )
    execution_id = submit_res.json()["execution_id"]

    # Cancel execution
    cancel_res = await client.delete(f"/api/v1/executions/{execution_id}", headers=auth_headers)
    # Could be Cancelled or Completed if background task already finished
    assert cancel_res.status_code in (200, 409)
