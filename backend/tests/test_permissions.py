import pytest
from httpx import AsyncClient
from backend.app.agents.base_agent import TaskScope
from backend.app.agents.permissions import check_permission


def test_permission_checker_reasons():
    # READ_ONLY is granted
    ok, msg = check_permission("arch-sentinel", TaskScope.read_only)
    assert ok is True
    assert "verified" in msg.lower()

    # SUGGEST is granted
    ok, msg = check_permission("arch-sentinel", TaskScope.suggest)
    assert ok is True

    # IMPLEMENT is blocked with clear reason
    ok, msg = check_permission("arch-sentinel", TaskScope.implement)
    assert ok is False
    assert "Phase 04+" in msg

    # DEPLOY is blocked with clear reason
    ok, msg = check_permission("arch-sentinel", TaskScope.deploy)
    assert ok is False
    assert "Phase 11" in msg

    # Prohibited tool requires implement
    ok, msg = check_permission("arch-sentinel", TaskScope.read_only, requested_tools=["file_write"])
    assert ok is False
    assert "restricted in Phase 03" in msg


@pytest.mark.asyncio
async def test_permission_endpoints_enforcement(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    # Setup agent as Available
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    await client.post("/api/v1/agents/arch-sentinel/configure", json={}, headers=super_auth_headers)
    await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Available"},
        headers=super_auth_headers,
    )

    # 1. READ_ONLY scope allowed -> 202
    ro_res = await client.post(
        "/api/v1/executions",
        json={"agent_slug": "arch-sentinel", "instruction": "Read AST", "scope": "read_only"},
        headers=auth_headers,
    )
    assert ro_res.status_code == 202

    # 2. SUGGEST scope allowed -> 202
    sug_res = await client.post(
        "/api/v1/executions",
        json={"agent_slug": "arch-sentinel", "instruction": "Suggest refactoring", "scope": "suggest"},
        headers=auth_headers,
    )
    assert sug_res.status_code == 202

    # 3. IMPLEMENT scope blocked for agents without implement capabilities -> 403
    impl_res = await client.post(
        "/api/v1/executions",
        json={"agent_slug": "curizx-core", "instruction": "Write refactoring", "scope": "implement"},
        headers=auth_headers,
    )
    assert impl_res.status_code == 403
    assert impl_res.json()["error"] == "scope_restricted"

    # 4. DEPLOY scope blocked -> 403
    deploy_res = await client.post(
        "/api/v1/executions",
        json={"agent_slug": "arch-sentinel", "instruction": "Deploy to prod", "scope": "deploy"},
        headers=auth_headers,
    )
    assert deploy_res.status_code == 403
    assert deploy_res.json()["error"] == "scope_restricted"
