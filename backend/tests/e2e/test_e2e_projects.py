"""E2E Test 2: Full Project Lifecycle, Isolation & Soft Delete."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_e2e_project_workflow_and_isolation(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict
):
    # 1. Create project
    create = await client.post(
        "/api/v1/projects",
        json={
            "name": "Phase 14 E2E Project",
            "description": "End-to-end verified system project.",
            "status": "Active",
        },
        headers=auth_headers,
    )
    assert create.status_code == 201
    proj = create.json()
    proj_id = proj["id"]

    # 2. List & detail
    listing = await client.get("/api/v1/projects", headers=auth_headers)
    assert listing.status_code == 200
    assert any(p["id"] == proj_id for p in listing.json()["items"])

    detail = await client.get(f"/api/v1/projects/{proj_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "Phase 14 E2E Project"

    # 3. Cross-user access strictly blocked (403 Forbidden)
    other_get = await client.get(f"/api/v1/projects/{proj_id}", headers=other_auth_headers)
    assert other_get.status_code == 403

    other_patch = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"name": "Hijacked Name"},
        headers=other_auth_headers,
    )
    assert other_patch.status_code == 403

    # 4. Owner update verified
    upd = await client.patch(
        f"/api/v1/projects/{proj_id}",
        json={"description": "Updated E2E specification"},
        headers=auth_headers,
    )
    assert upd.status_code == 200
    assert upd.json()["description"] == "Updated E2E specification"

    # 5. Soft delete sets Archived
    soft_del = await client.delete(f"/api/v1/projects/{proj_id}", headers=auth_headers)
    assert soft_del.status_code == 204
    after_del = await client.get(f"/api/v1/projects/{proj_id}", headers=auth_headers)
    assert after_del.status_code == 200
    assert after_del.json()["status"] == "Archived"
