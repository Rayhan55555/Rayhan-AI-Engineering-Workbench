import pytest
from httpx import AsyncClient
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_create_project_authenticated(client: AsyncClient, auth_headers: dict, test_user: User):
    payload = {
        "name": "Curizx Autonomous Pipeline",
        "description": "Enterprise lead generation agent backend",
        "status": "Active",
    }
    response = await client.post("/api/v1/projects", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["status"] == "Active"
    assert data["owner_id"] == str(test_user.id)
    assert "id" in data


@pytest.mark.asyncio
async def test_list_projects_authenticated(client: AsyncClient, auth_headers: dict):
    # Create 3 projects
    for i in range(3):
        await client.post(
            "/api/v1/projects",
            json={"name": f"Project {i}", "description": f"Desc {i}"},
            headers=auth_headers,
        )

    response = await client.get("/api/v1/projects?page=1&limit=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total_pages"] == 2


@pytest.mark.asyncio
async def test_get_own_project(client: AsyncClient, auth_headers: dict):
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "Knowledge RAG Pipeline", "description": "Vector indexing"},
        headers=auth_headers,
    )
    project_id = create_res.json()["id"]

    response = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == project_id


@pytest.mark.asyncio
async def test_get_other_user_project_forbidden(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict
):
    # User 1 creates project
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "Confidential Architecture", "description": "Classified"},
        headers=auth_headers,
    )
    project_id = create_res.json()["id"]

    # User 2 tries to get User 1's project -> 403 Forbidden
    response = await client.get(f"/api/v1/projects/{project_id}", headers=other_auth_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error"] == "forbidden"


@pytest.mark.asyncio
async def test_update_own_project(client: AsyncClient, auth_headers: dict):
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "Draft Project", "description": "Initial draft"},
        headers=auth_headers,
    )
    project_id = create_res.json()["id"]

    # Partial update
    update_res = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Refined Production Project", "status": "Paused"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["name"] == "Refined Production Project"
    assert data["status"] == "Paused"
    assert data["description"] == "Initial draft"


@pytest.mark.asyncio
async def test_delete_other_user_project_forbidden(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict
):
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "User 1 Project", "description": "Do not touch"},
        headers=auth_headers,
    )
    project_id = create_res.json()["id"]

    # User 2 tries to delete -> 403
    del_res = await client.delete(f"/api/v1/projects/{project_id}", headers=other_auth_headers)
    assert del_res.status_code == 403
    assert del_res.json()["error"] == "forbidden"

    # User 1 deletes own project -> 204
    own_del = await client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert own_del.status_code == 204

    # Verify soft delete: project exists but has status 'Archived'
    get_res = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "Archived"
