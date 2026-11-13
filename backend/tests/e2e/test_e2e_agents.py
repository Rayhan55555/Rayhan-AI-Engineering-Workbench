"""E2E Test 3: Agent Registry Provisioning, Execution & Honest Simulation Flag."""

import asyncio
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_e2e_agent_execution_and_truthful_flags(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    # 1. Seed agents & verify registry list
    seed = await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    assert seed.status_code == 200

    # 2. Configure and activate real coding agent (arch-sentinel -> simulated=False)
    await client.post("/api/v1/agents/arch-sentinel/configure", json={}, headers=super_auth_headers)
    await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Available"},
        headers=super_auth_headers,
    )

    # 3. Submit task & poll until completion
    sub = await client.post(
        "/api/v1/executions",
        json={
            "agent_slug": "arch-sentinel",
            "instruction": "analyze file backend/app/config.py",
            "scope": "read_only",
        },
        headers=auth_headers,
    )
    assert sub.status_code == 202
    sub_data = sub.json()
    assert sub_data["simulated"] is False
    exec_id = sub_data["execution_id"]

    status_payload = {}
    for _ in range(30):
        poll = await client.get(f"/api/v1/executions/{exec_id}", headers=auth_headers)
        assert poll.status_code == 200
        status_payload = poll.json()
        if status_payload["status"] in ("Completed", "Failed"):
            break
        await asyncio.sleep(0.1)

    assert status_payload["status"] == "Completed"
    assert status_payload["simulated"] is False
    assert status_payload["output"] is not None

    # 4. Activate stub agent (flow-executor -> simulated=True)
    await client.post("/api/v1/agents/flow-executor/configure", json={}, headers=super_auth_headers)
    await client.patch(
        "/api/v1/agents/flow-executor/status",
        json={"status": "Available"},
        headers=super_auth_headers,
    )
    stub_sub = await client.post(
        "/api/v1/executions",
        json={"agent_slug": "flow-executor", "instruction": "stub check", "scope": "read_only"},
        headers=auth_headers,
    )
    assert stub_sub.status_code == 202
    assert stub_sub.json()["simulated"] is True
