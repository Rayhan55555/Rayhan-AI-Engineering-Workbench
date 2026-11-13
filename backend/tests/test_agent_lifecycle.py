import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_valid_lifecycle_transitions(client: AsyncClient, super_auth_headers: dict):
    # 1. Seed agents (all Planned)
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)

    # 2. Planned -> Configured (via configure endpoint)
    conf_res = await client.post(
        "/api/v1/agents/arch-sentinel/configure",
        json={"purpose": "Configured code auditing agent"},
        headers=super_auth_headers,
    )
    assert conf_res.status_code == 200
    assert conf_res.json()["status"] == "Configured"

    # 3. Configured -> Available
    avail_res = await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Available", "reason": "Passed pre-flight check"},
        headers=super_auth_headers,
    )
    assert avail_res.status_code == 200
    assert avail_res.json()["status"] == "Available"

    # 4. Available -> Maintenance
    maint_res = await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Maintenance", "reason": "Updating tools"},
        headers=super_auth_headers,
    )
    assert maint_res.status_code == 200
    assert maint_res.json()["status"] == "Maintenance"

    # 5. Maintenance -> Available
    back_res = await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Available", "reason": "Maintenance complete"},
        headers=super_auth_headers,
    )
    assert back_res.status_code == 200
    assert back_res.json()["status"] == "Available"


@pytest.mark.asyncio
async def test_invalid_lifecycle_transition_raises_422(
    client: AsyncClient, super_auth_headers: dict
):
    # Seed agents (all Planned)
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)

    # Attempt illegal transition: Planned -> Running directly (must be 422)
    invalid_res = await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Running", "reason": "Attempting illegal jump"},
        headers=super_auth_headers,
    )
    assert invalid_res.status_code == 422
    data = invalid_res.json()
    assert data["error"] == "invalid_transition"
    assert "Planned" in data["message"]
    assert "Running" in data["message"]


@pytest.mark.asyncio
async def test_permission_denied_regular_user_change_status(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)

    # Regular user attempts status change -> 403 Forbidden
    res = await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Configured"},
        headers=auth_headers,
    )
    assert res.status_code == 403
    assert res.json()["error"] == "forbidden"


@pytest.mark.asyncio
async def test_agent_configure_endpoint_as_regular_user_denied(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)

    # Regular user attempts to configure -> 403
    res = await client.post(
        "/api/v1/agents/arch-sentinel/configure",
        json={},
        headers=auth_headers,
    )
    assert res.status_code == 403
    assert res.json()["error"] == "forbidden"
