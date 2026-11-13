import pytest
from httpx import AsyncClient
from jose import jwt


@pytest.mark.asyncio
async def test_sql_injection_attempt(client: AsyncClient, auth_headers: dict):
    # Attempt SQL injection inside structured fields
    malicious_payload = {
        "name": "'; DROP TABLE users; --",
        "description": "' OR '1'='1",
        "status": "Active",
    }
    # It should either be safely stored as a string literal (ORM parameterization) or validated
    response = await client.post("/api/v1/projects", json=malicious_payload, headers=auth_headers)
    assert response.status_code == 201
    created_id = response.json()["id"]

    # Verify table 'users' was NOT dropped
    me_res = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_res.status_code == 200

    # Test invalid enum injection (e.g. status injection) -> 422
    invalid_enum = {
        "name": "Test Project",
        "status": "Active'; DROP TABLE projects; --",
    }
    inv_res = await client.post("/api/v1/projects", json=invalid_enum, headers=auth_headers)
    assert inv_res.status_code == 422
    assert inv_res.json()["error"] == "validation_error"


@pytest.mark.asyncio
async def test_oversized_input_validation(client: AsyncClient, auth_headers: dict):
    # Name has max_length=255
    oversized_payload = {
        "name": "A" * 300,
        "description": "Standard description",
    }
    response = await client.post("/api/v1/projects", json=oversized_payload, headers=auth_headers)
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "validation_error"


@pytest.mark.asyncio
async def test_rate_limit_exceeded(client: AsyncClient):
    # Auth endpoints have limit of 5 req/min per IP
    # Fire 6 rapid login requests from same client
    payload = {"email": "nonexistent@rayhan-ai.com", "password": "WrongPassword123!"}
    
    last_status = None
    for i in range(8):
        res = await client.post("/api/v1/auth/login", json=payload)
        last_status = res.status_code
        if last_status == 429:
            break

    assert last_status == 429
    assert res.json()["error"] == "rate_limit_exceeded"
    assert "Retry-After" in res.headers


@pytest.mark.asyncio
async def test_invalid_jwt_signature(client: AsyncClient):
    # Forge token with arbitrary key
    forged_token = jwt.encode({"sub": "random-id"}, "wrong-secret-key-12345678901234567890", algorithm="HS256")
    headers = {"Authorization": f"Bearer {forged_token}"}
    
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "invalid_token"


@pytest.mark.asyncio
async def test_superuser_only_endpoint_forbidden_for_regular_user(
    client: AsyncClient, auth_headers: dict
):
    response = await client.post("/api/v1/agents/seed", headers=auth_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error"] == "forbidden"
