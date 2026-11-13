"""E2E Test 5: Portfolio Public Isolation, Cross-User Ownership & Contact Rate Limit."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_e2e_portfolio_isolation_and_rate_limits(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict, super_auth_headers: dict
):
    # 1. Public profile never reveals credentials or private IDs
    profile = await client.get("/api/v1/portfolio/profile")
    assert profile.status_code == 200
    assert profile.json()["name"] == "Rayhan"

    # 2. Private portfolio project hidden publicly (404) & protected against cross-user mutation (403)
    proj = await client.post(
        "/api/v1/portfolio/projects",
        json={
            "title": "E2E Secret Agent Architecture",
            "tagline": "Private draft case architecture",
            "description": "## Internal Architecture\nZero public leakage.",
            "tech_stack": ["FastAPI", "React"],
            "category": "ai_agent",
        },
        headers=auth_headers,
    )
    assert proj.status_code == 201
    proj_id = proj.json()["id"]
    slug = proj.json()["slug"]

    assert (await client.get(f"/api/v1/portfolio/projects/{slug}")).status_code == 404

    cross_patch = await client.patch(
        f"/api/v1/portfolio/projects/{proj_id}",
        json={"title": "Cross-user Tamper"},
        headers=other_auth_headers,
    )
    assert cross_patch.status_code == 403

    # 3. Superuser publish exposes project publicly (200)
    pub = await client.patch(
        f"/api/v1/portfolio/projects/{proj_id}/publish",
        headers=super_auth_headers,
    )
    assert pub.status_code == 200
    assert (await client.get(f"/api/v1/portfolio/projects/{slug}")).status_code == 200

    # 4. Safe demo executes sample-only workflow
    demo = await client.post(
        "/api/v1/portfolio/demos/code-analyzer/run",
        json={"code": "def add(a: int, b: int) -> int:\n    return a + b\n", "language": "python"},
    )
    assert demo.status_code == 200
    assert demo.json()["sample_data_only"] is True
    assert demo.json()["persisted"] is False

    # 5. Contact rate limit (3/hr per IP)
    for i in range(3):
        res = await client.post(
            "/api/v1/portfolio/contact",
            json={
                "name": "Hiring Lead",
                "email": "lead@example.org",
                "subject": f"Role inquiry {i}",
                "message": "Architecture discussion request.",
            },
            headers={"X-Forwarded-For": "198.51.100.88"},
        )
        assert res.status_code == 200

    blocked = await client.post(
        "/api/v1/portfolio/contact",
        json={
            "name": "Hiring Lead",
            "email": "lead@example.org",
            "subject": "Role inquiry 4",
            "message": "Exceeding 3/hr quota.",
        },
        headers={"X-Forwarded-For": "198.51.100.88"},
    )
    assert blocked.status_code == 429
