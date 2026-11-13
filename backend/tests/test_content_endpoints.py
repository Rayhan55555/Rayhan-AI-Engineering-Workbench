"""Integration tests for Phase 12 Content Studio REST API endpoints."""

import pytest
from httpx import AsyncClient

from backend.app.content.pipeline import REVIEW_MARKER


@pytest.mark.asyncio
async def test_api_content_generate_and_pipeline_lifecycle(
    client: AsyncClient, auth_headers: dict
):
    """Verify generation stamps [REVIEW REQUIRED] and enforces Idea -> Draft -> Approved -> Published."""
    # Unauthenticated rejected
    unauth = await client.post(
        "/api/v1/content/generate",
        json={"topic": "FastAPI Rate Limiting", "content_type": "article"},
    )
    assert unauth.status_code == 401

    # 1. Generate case study saved into pipeline as draft
    gen_res = await client.post(
        "/api/v1/content/generate",
        json={
            "topic": "Phase 11 Deployment Guardrails",
            "content_type": "case_study",
            "save_to_pipeline": True,
        },
        headers=auth_headers,
    )
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["review_required"] is True
    assert gen_data["stage"] == "draft"
    assert REVIEW_MARKER in gen_data["body_markdown"]
    assert "[BENCHMARK NEEDED]" in gen_data["body_markdown"]
    item_id = gen_data["saved_item"]["id"]

    # 2. Attempt direct draft -> published (auto-publish bypass) -> 400
    bypass_res = await client.post(
        f"/api/v1/content/items/{item_id}/transition",
        json={"target_stage": "published", "approved": True},
        headers=auth_headers,
    )
    assert bypass_res.status_code == 400

    # 3. Attempt draft -> approved without approved=True -> 400
    unapproved_res = await client.post(
        f"/api/v1/content/items/{item_id}/transition",
        json={"target_stage": "approved", "approved": False},
        headers=auth_headers,
    )
    assert unapproved_res.status_code == 400

    # 4. Approve with explicit approval=True -> 200
    approve_res = await client.post(
        f"/api/v1/content/items/{item_id}/transition",
        json={"target_stage": "approved", "approved": True},
        headers=auth_headers,
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["stage"] == "approved"
    assert approve_res.json()["approved_at"] is not None

    # 5. Publish with explicit approval=True -> 200
    pub_res = await client.post(
        f"/api/v1/content/items/{item_id}/transition",
        json={"target_stage": "published", "approved": True},
        headers=auth_headers,
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["stage"] == "published"
    assert pub_res.json()["published_at"] is not None


@pytest.mark.asyncio
async def test_api_content_social_and_youtube_generation(
    client: AsyncClient, auth_headers: dict
):
    """Verify /generate returns social thread <= 280 chars and YouTube script segments."""
    social_res = await client.post(
        "/api/v1/content/generate",
        json={
            "topic": "Vector Search Reranking",
            "content_type": "social_pack",
            "save_to_pipeline": False,
        },
        headers=auth_headers,
    )
    assert social_res.status_code == 200
    sdata = social_res.json()
    assert sdata["channel"] == "cross_platform"
    assert len(sdata["twitter_thread"]) >= 4
    assert all(len(t) <= 280 for t in sdata["twitter_thread"])
    assert len(sdata["linkedin_post"]) > 50

    yt_res = await client.post(
        "/api/v1/content/generate",
        json={
            "topic": "MCP Tool Registry",
            "content_type": "youtube_script",
            "target_minutes": 10,
            "save_to_pipeline": False,
        },
        headers=auth_headers,
    )
    assert yt_res.status_code == 200
    assert yt_res.json()["channel"] == "youtube"
    assert REVIEW_MARKER in yt_res.json()["body_markdown"]


@pytest.mark.asyncio
async def test_api_content_calendar_and_crud(client: AsyncClient, auth_headers: dict):
    """Verify creating ideas, scheduling dates, listing calendar, and deleting items."""
    create_res = await client.post(
        "/api/v1/content/items",
        json={
            "title": "Zero Downtime Alembic Migrations",
            "content_type": "tutorial",
            "stage": "idea",
            "channel": "blog",
            "scheduled_at": "2026-11-25T10:00:00Z",
        },
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    created_id = create_res.json()["id"]

    cal_res = await client.get("/api/v1/content/calendar", headers=auth_headers)
    assert cal_res.status_code == 200
    cal_data = cal_res.json()
    assert cal_data["total_items"] >= 1
    assert cal_data["stage_counts"]["idea"] >= 1
    assert any(it["id"] == created_id for it in cal_data["scheduled_items"])

    # Clean delete
    del_res = await client.delete(f"/api/v1/content/items/{created_id}", headers=auth_headers)
    assert del_res.status_code == 204
