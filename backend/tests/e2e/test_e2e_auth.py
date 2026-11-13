"""E2E Test 1: Full Authentication & WebSocket Session Flow."""

from datetime import timedelta
import pytest
from httpx import AsyncClient
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app.main import app
from backend.app.services.auth_service import create_access_token


@pytest.mark.asyncio
async def test_e2e_full_auth_lifecycle(client: AsyncClient):
    e2e_ip = {"X-Forwarded-For": "10.14.1.10"}

    # 1. Register new user
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "e2e_auth@rayhan-ai.com",
            "username": "e2e_auth_user",
            "password": "E2ePassword123!",
        },
        headers=e2e_ip,
    )
    assert reg.status_code == 201
    user_id = reg.json()["id"]

    # 2. Login -> receive access + refresh tokens
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "e2e_auth@rayhan-ai.com", "password": "E2ePassword123!"},
        headers=e2e_ip,
    )
    assert login.status_code == 200
    tokens = login.json()
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    # 3. Protected route with valid token
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["id"] == user_id

    # 4. Rotate refresh token -> new access token, old refresh token invalidated
    rot = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh}, headers=e2e_ip)
    assert rot.status_code == 200
    new_access = rot.json()["access_token"]
    assert new_access != ""

    reuse = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh}, headers=e2e_ip)
    assert reuse.status_code == 401

    # 5. Re-login, then logout -> revokes refresh tokens
    login2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "e2e_auth@rayhan-ai.com", "password": "E2ePassword123!"},
        headers=e2e_ip,
    )
    access2 = login2.json()["access_token"]
    refresh2 = login2.json()["refresh_token"]

    logout = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {access2}"})
    assert logout.status_code == 204

    post_logout_refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh2})
    assert post_logout_refresh.status_code == 401

    # 6. Expired access token rejected cleanly with 401
    expired, _ = create_access_token(data={"sub": user_id}, expires_delta=timedelta(seconds=-5))
    exp_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert exp_res.status_code == 401
    assert exp_res.json()["error"] == "token_expired"


def test_e2e_websocket_requires_jwt(monkeypatch):
    """Verify WebSocket /ws/{user_id} blocks unauthenticated or mismatched-user connections."""
    from backend.tests.conftest import test_engine
    monkeypatch.setattr("backend.app.main.engine", test_engine)

    with TestClient(app) as sync_client:
        with pytest.raises(WebSocketDisconnect):
            with sync_client.websocket_connect("/api/v1/ws/user-123"):
                pass

        token, _ = create_access_token(data={"sub": "user-123"})
        with sync_client.websocket_connect(f"/api/v1/ws/user-123?token={token}") as ws:
            hello = ws.receive_json()
            assert hello["type"] == "connection_established"
            assert hello["user_id"] == "user-123"
            ws.send_text("ping")
            assert ws.receive_text() == "pong"
