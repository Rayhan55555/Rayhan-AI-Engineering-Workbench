import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_seed_and_list_agents(client: AsyncClient, super_auth_headers: dict, auth_headers: dict):
    # 1. Non-superuser cannot seed
    unauth_seed = await client.post("/api/v1/agents/seed", headers=auth_headers)
    assert unauth_seed.status_code == 403

    # 2. Superuser seeds 8 agents
    seed_res = await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    assert seed_res.status_code == 200
    agents = seed_res.json()
    assert len(agents) == 8
    assert any(a["slug"] == "curizx-core" for a in agents)

    # 3. Public list agents without auth
    list_res = await client.get("/api/v1/agents")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 8

    # 4. Search filter
    search_res = await client.get("/api/v1/agents?search=rag")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data) >= 1
    assert any(a["slug"] == "rag-engine-v1" for a in search_data)


@pytest.mark.asyncio
async def test_get_agent_by_slug(client: AsyncClient, super_auth_headers: dict):
    # Seed first
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)

    # Existing agent
    res = await client.get("/api/v1/agents/curizx-core")
    assert res.status_code == 200
    assert res.json()["slug"] == "curizx-core"
    assert res.json()["name"] == "Curizx AI Employee"

    # Non-existent agent
    not_found = await client.get("/api/v1/agents/non-existent-agent-slug")
    assert not_found.status_code == 404
    assert not_found.json()["error"] == "not_found"


@pytest.mark.asyncio
async def test_update_agent_permissions(
    client: AsyncClient, super_auth_headers: dict, auth_headers: dict
):
    # Seed
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)

    # Regular user cannot update -> 403
    reg_update = await client.patch(
        "/api/v1/agents/curizx-core",
        json={"name": "Tampered Name"},
        headers=auth_headers,
    )
    assert reg_update.status_code == 403

    # Superuser can update -> 200
    su_update = await client.patch(
        "/api/v1/agents/curizx-core",
        json={"name": "Curizx Autonomous AI Employee (v1)"},
        headers=super_auth_headers,
    )
    assert su_update.status_code == 200
    assert su_update.json()["name"] == "Curizx Autonomous AI Employee (v1)"
