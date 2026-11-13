import asyncio
import json
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_coding_agent_read_only_inspect(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    # Seed agents and make arch-sentinel Available
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    await client.post("/api/v1/agents/arch-sentinel/configure", json={}, headers=super_auth_headers)
    await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Available"},
        headers=super_auth_headers,
    )

    # 1. Submit read_only inspect task
    payload = {
        "agent_slug": "arch-sentinel",
        "instruction": "inspect backend/app/main.py",
        "scope": "read_only",
    }
    submit_res = await client.post("/api/v1/executions", json=payload, headers=auth_headers)
    assert submit_res.status_code == 202
    data = submit_res.json()
    assert data["simulated"] is False
    execution_id = data["execution_id"]

    # Poll until Completed
    res_data = {}
    for _ in range(30):
        get_res = await client.get(f"/api/v1/executions/{execution_id}", headers=auth_headers)
        assert get_res.status_code == 200
        res_data = get_res.json()
        if res_data["status"] != "Pending":
            break
        await asyncio.sleep(0.1)

    assert res_data.get("error_message") is None, f"Execution failed with: {res_data.get('error_message')}"
    assert res_data["status"] == "Completed"
    assert res_data["simulated"] is False
    output_obj = json.loads(res_data["output"])
    assert output_obj["file"] == "backend/app/main.py"
    assert "metrics" in output_obj


@pytest.mark.asyncio
async def test_coding_agent_suggest_diff(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    # Seed and make Available
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    await client.post("/api/v1/agents/arch-sentinel/configure", json={}, headers=super_auth_headers)
    await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Available"},
        headers=super_auth_headers,
    )

    payload = {
        "agent_slug": "arch-sentinel",
        "instruction": "suggest improvements for backend/app/schemas/agent.py",
        "scope": "suggest",
    }
    submit_res = await client.post("/api/v1/executions", json=payload, headers=auth_headers)
    assert submit_res.status_code == 202
    data = submit_res.json()
    assert data["simulated"] is False
    execution_id = data["execution_id"]

    # Poll until Completed
    res_data = {}
    for _ in range(30):
        get_res = await client.get(f"/api/v1/executions/{execution_id}", headers=auth_headers)
        assert get_res.status_code == 200
        res_data = get_res.json()
        if res_data["status"] != "Pending":
            break
        await asyncio.sleep(0.1)

    assert res_data["status"] == "Completed"
    output_obj = json.loads(res_data["output"])
    assert "diff" in output_obj
    assert "diff generation only" in output_obj["note"].lower()


@pytest.mark.asyncio
async def test_coding_agent_implement_scope_approval_flow(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    # Seed and make Available
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    await client.post("/api/v1/agents/arch-sentinel/configure", json={}, headers=super_auth_headers)
    await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Available"},
        headers=super_auth_headers,
    )

    # 1. Submit implement scope task (requires approval)
    payload = {
        "agent_slug": "arch-sentinel",
        "instruction": "run tests backend/tests/test_security.py",
        "scope": "implement",
    }
    submit_res = await client.post("/api/v1/executions", json=payload, headers=auth_headers)
    assert submit_res.status_code == 202
    data = submit_res.json()
    assert data["status"] == "Pending"
    assert "awaiting user approval" in data["message"].lower()
    execution_id = data["execution_id"]

    # 2. Approve execution
    approve_res = await client.post(
        f"/api/v1/executions/{execution_id}/approve",
        json={"approved": True, "note": "Approved test run"},
        headers=auth_headers,
    )
    assert approve_res.status_code == 200

    # 3. Poll until Completed
    res_data = {}
    for _ in range(40):
        get_res = await client.get(f"/api/v1/executions/{execution_id}", headers=auth_headers)
        assert get_res.status_code == 200
        res_data = get_res.json()
        if res_data["status"] not in ("Pending", "Running"):
            break
        await asyncio.sleep(0.2)

    assert res_data.get("error_message") is None, f"IMPLEMENT execution failed: {res_data.get('error_message')}"
    assert res_data["status"] == "Completed"
    assert res_data["simulated"] is False
    output_obj = json.loads(res_data["output"])
    assert output_obj["result"]["passed"] >= 1


@pytest.mark.asyncio
async def test_coding_agent_reject_execution(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    await client.post("/api/v1/agents/arch-sentinel/configure", json={}, headers=super_auth_headers)
    await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Available"},
        headers=super_auth_headers,
    )

    submit_res = await client.post(
        "/api/v1/executions",
        json={"agent_slug": "arch-sentinel", "instruction": "run tests", "scope": "implement"},
        headers=auth_headers,
    )
    execution_id = submit_res.json()["execution_id"]

    # Reject execution
    reject_res = await client.post(
        f"/api/v1/executions/{execution_id}/reject",
        json={"reason": "Security review rejected command"},
        headers=auth_headers,
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "Cancelled"
    assert "rejected by user" in reject_res.json()["error_message"].lower()
