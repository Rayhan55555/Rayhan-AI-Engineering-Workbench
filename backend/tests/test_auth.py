from datetime import timedelta
import pytest
from httpx import AsyncClient
from backend.app.models.user import User
from backend.app.services.auth_service import create_access_token


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    payload = {
        "email": "newuser@rayhan-ai.com",
        "username": "new_user_1",
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["username"] == payload["username"]
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    payload = {
        "email": test_user.email,
        "username": "unique_username",
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["error"] == "conflict"


@pytest.mark.asyncio
async def test_login_valid_credentials(client: AsyncClient, test_user: User):
    payload = {
        "email": test_user.email,
        "password": "SecurePass123!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_user: User):
    payload = {
        "email": test_user.email,
        "password": "WrongPassword999!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_access_protected_route_with_token(client: AsyncClient, auth_headers: dict, test_user: User):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_access_protected_route_without_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "unauthorized"


@pytest.mark.asyncio
async def test_access_protected_route_with_expired_token(client: AsyncClient, test_user: User):
    # Create expired token (negative delta)
    expired_token, _ = create_access_token(
        data={"sub": str(test_user.id)}, expires_delta=timedelta(seconds=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "token_expired"


@pytest.mark.asyncio
async def test_refresh_token_lifecycle(client: AsyncClient, test_user: User):
    # 1. Login to get tokens
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "SecurePass123!"},
    )
    assert login_res.status_code == 200
    refresh_token = login_res.json()["refresh_token"]

    # 2. Use refresh token to get new access token
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # 3. Old refresh token should now be consumed/revoked
    second_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert second_refresh.status_code == 401
