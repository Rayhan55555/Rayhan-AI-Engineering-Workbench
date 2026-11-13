"""Integration tests for Phase 13 Public Portfolio & Safe Demos API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_public_profile_exposes_no_private_data(client: AsyncClient):
    """Profile endpoint is zero-auth and never exposes private emails, secrets, tokens, or DB internals."""
    res = await client.get("/api/v1/portfolio/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Rayhan"
    assert "Architecting Intelligence" in data["tagline"]
    assert len(data["expertise"]) == 6
    assert "github" in data["social_links"]
    raw = res.text.lower()
    for forbidden in ("secret_key", "password", "hashed_password", "refresh_token", "created_by"):
        assert forbidden not in raw


@pytest.mark.asyncio
async def test_project_privacy_boundary_and_superuser_publish(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    """Private projects return 404 publicly until manually published by a superuser."""
    # 1. Create project (auth user) -> defaults to is_public=False
    create_res = await client.post(
        "/api/v1/portfolio/projects",
        json={
            "title": "Curizx Hybrid RAG Pipeline",
            "tagline": "Citation-grounded multi-tenant retrieval engine",
            "description": "## Overview\nFull markdown engineering architecture.",
            "tech_stack": ["FastAPI", "pgvector", "Python"],
            "category": "rag",
            "status": "in_progress",
            "is_featured": True,
        },
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["is_public"] is False
    slug = created["slug"]
    proj_id = created["id"]

    # 2. Public projects list excludes private project
    list_res = await client.get("/api/v1/portfolio/projects")
    assert list_res.status_code == 200
    assert all(p["slug"] != slug for p in list_res.json())

    # 3. Direct slug lookup returns 404 while private
    detail_private = await client.get(f"/api/v1/portfolio/projects/{slug}")
    assert detail_private.status_code == 404

    # 4. Normal user cannot publish (403 Forbidden)
    non_super_pub = await client.patch(
        f"/api/v1/portfolio/projects/{proj_id}/publish",
        headers=auth_headers,
    )
    assert non_super_pub.status_code == 403

    # 5. Superuser manually publishes -> appears in public list & detail
    pub_res = await client.patch(
        f"/api/v1/portfolio/projects/{proj_id}/publish",
        headers=super_auth_headers,
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["is_public"] is True
    assert pub_res.json()["published_at"] is not None

    public_list = await client.get("/api/v1/portfolio/projects")
    assert any(p["slug"] == slug for p in public_list.json())

    public_detail = await client.get(f"/api/v1/portfolio/projects/{slug}")
    assert public_detail.status_code == 200
    assert public_detail.json()["title"] == "Curizx Hybrid RAG Pipeline"


@pytest.mark.asyncio
async def test_articles_and_case_studies_only_show_published(
    client: AsyncClient, auth_headers: dict
):
    """Unapproved drafts from Phase 12 never appear on public portfolio articles or case studies."""
    # Generate a draft article (remains in 'draft' stage)
    draft_res = await client.post(
        "/api/v1/content/generate",
        json={"topic": "Secret Internal Draft Protocol", "content_type": "article", "save_to_pipeline": True},
        headers=auth_headers,
    )
    assert draft_res.status_code == 200
    draft_slug = draft_res.json()["saved_item"]["slug"]
    draft_id = draft_res.json()["saved_item"]["id"]

    # Public articles endpoint must NOT contain draft
    pub_articles_before = await client.get("/api/v1/portfolio/articles")
    assert pub_articles_before.status_code == 200
    assert all(a["slug"] != draft_slug for a in pub_articles_before.json())

    single_draft_lookup = await client.get(f"/api/v1/portfolio/articles/{draft_slug}")
    assert single_draft_lookup.status_code == 404

    # Approve then publish via Phase 12 explicit approval workflow
    await client.post(
        f"/api/v1/content/items/{draft_id}/transition",
        json={"target_stage": "approved", "approved": True},
        headers=auth_headers,
    )
    await client.post(
        f"/api/v1/content/items/{draft_id}/transition",
        json={"target_stage": "published", "approved": True},
        headers=auth_headers,
    )

    pub_articles_after = await client.get("/api/v1/portfolio/articles")
    assert any(a["slug"] == draft_slug for a in pub_articles_after.json())


@pytest.mark.asyncio
async def test_safe_demos_sample_only_and_isolated(client: AsyncClient):
    """Demos run read-only in-memory checks on sample data with zero DB persistence."""
    catalog = await client.get("/api/v1/portfolio/demos")
    assert catalog.status_code == 200
    slugs = [d["slug"] for d in catalog.json()]
    assert set(slugs) == {"code-analyzer", "security-scanner", "architecture-diagram"}

    # Code analyzer demo
    code_res = await client.post(
        "/api/v1/portfolio/demos/code-analyzer/run",
        json={"code": "import os\ndef hello(x):\n    return x\n", "language": "python"},
    )
    assert code_res.status_code == 200
    cdata = code_res.json()
    assert cdata["demo_label"] == "Demo — Sample Data"
    assert cdata["sample_data_only"] is True
    assert cdata["persisted"] is False
    assert "functions" in cdata["output"]

    # Security scanner demo
    sec_res = await client.post(
        "/api/v1/portfolio/demos/security-scanner/run",
        json={"code": "cursor.execute(f'SELECT * FROM users WHERE id = {uid}')", "language": "python"},
    )
    assert sec_res.status_code == 200
    assert sec_res.json()["output"]["total_findings"] >= 1

    # Architecture diagram demo
    diag_res = await client.post(
        "/api/v1/portfolio/demos/architecture-diagram/run",
        json={"prompt": "FastAPI gateway with pgvector RAG and MCP tools"},
    )
    assert diag_res.status_code == 200
    assert diag_res.json()["output"]["syntax_valid"] is True
    assert diag_res.json()["output"]["mermaid_code"].startswith("graph TD")


@pytest.mark.asyncio
async def test_contact_honeypot_and_rate_limit(client: AsyncClient):
    """Contact form rejects honeypot spam submissions and rate-limits at 3 requests/hour per IP."""
    # 1. Honeypot triggers 400 rejection without consuming quota
    spam_res = await client.post(
        "/api/v1/portfolio/contact",
        json={
            "name": "Bot User",
            "email": "bot@spam.example",
            "subject": "SEO Spam",
            "message": "Buy backlinks now!",
            "honeypot": "http://spam.example",
        },
        headers={"X-Forwarded-For": "203.0.113.55"},
    )
    assert spam_res.status_code == 400

    # 2. First 3 valid requests succeed
    for i in range(3):
        ok_res = await client.post(
            "/api/v1/portfolio/contact",
            json={
                "name": "Alice Engineer",
                "email": "alice@example.com",
                "subject": f"Advisory inquiry {i + 1}",
                "message": "Interested in discussing RAG system architecture.",
            },
            headers={"X-Forwarded-For": "203.0.113.77"},
        )
        assert ok_res.status_code == 200
        assert ok_res.json()["received"] is True

    # 3. 4th request from same IP within the hour is rate-limited (429)
    limited_res = await client.post(
        "/api/v1/portfolio/contact",
        json={
            "name": "Alice Engineer",
            "email": "alice@example.com",
            "subject": "Advisory inquiry 4",
            "message": "Following up again immediately.",
        },
        headers={"X-Forwarded-For": "203.0.113.77"},
    )
    assert limited_res.status_code == 429
    assert limited_res.json()["error"] == "rate_limit_exceeded"
