"""E2E Test 6: Full Multi-Agent Pipeline (Coding, Security, RAG, Content)."""

import asyncio
import pytest
from httpx import AsyncClient

from backend.app.content.pipeline import REVIEW_MARKER
from backend.app.rag.embedder import Embedder, EmbeddedChunk


@pytest.mark.asyncio
async def test_e2e_full_multi_agent_pipeline(
    client: AsyncClient,
    auth_headers: dict,
    other_auth_headers: dict,
    super_auth_headers: dict,
    monkeypatch,
):
    def fake_embed_chunks(chunks, task_type="retrieval_document"):
        return [
            EmbeddedChunk(
                chunk_id=getattr(c, "chunk_id", str(i)),
                content=getattr(c, "content", str(c)),
                embedding=[0.1] * 768,
                token_count=getattr(c, "token_count", 10),
                metadata=getattr(c, "metadata", {}),
            )
            for i, c in enumerate(chunks)
        ]

    monkeypatch.setattr(Embedder, "embed_chunks", classmethod(lambda cls, chunks, task_type="retrieval_document": fake_embed_chunks(chunks, task_type)))
    monkeypatch.setattr(Embedder, "embed_query", classmethod(lambda cls, query: [0.1] * 768))

    await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    for slug in ("arch-sentinel",):
        await client.post(f"/api/v1/agents/{slug}/configure", json={}, headers=super_auth_headers)
        await client.patch(
            f"/api/v1/agents/{slug}/status",
            json={"status": "Available"},
            headers=super_auth_headers,
        )

    # 1. Coding Agent execution
    coding = await client.post(
        "/api/v1/executions",
        json={
            "agent_slug": "arch-sentinel",
            "instruction": "analyze codebase",
            "scope": "read_only",
        },
        headers=auth_headers,
    )
    assert coding.status_code == 202
    c_id = coding.json()["execution_id"]
    for _ in range(30):
        r = await client.get(f"/api/v1/executions/{c_id}", headers=auth_headers)
        if r.json()["status"] in ("Completed", "Failed"):
            assert r.json()["status"] == "Completed"
            break
        await asyncio.sleep(0.1)

    # 2. Security Agent scan
    scan = await client.post(
        "/api/v1/security/scan",
        json={"target": "file", "path": "backend/app/config.py", "scan_types": ["secrets"]},
        headers=auth_headers,
    )
    assert scan.status_code == 202
    s_id = scan.json()["execution_id"]
    for _ in range(30):
        sr = await client.get(f"/api/v1/security/scans/{s_id}", headers=auth_headers)
        if sr.json()["status"] in ("Completed", "Failed"):
            assert sr.json()["status"] == "Completed"
            break
        await asyncio.sleep(0.1)

    # 3. RAG Knowledge ingest + search -> citations
    ingest = await client.post(
        "/api/v1/knowledge/ingest",
        files={"file": ("arch_notes.md", b"# Vector RAG\npgvector hybrid reranking improves citation precision.", "text/markdown")},
        data={"title": "RAG Pipeline Notes", "access_level": "private"},
        headers=auth_headers,
    )
    assert ingest.status_code == 202
    search = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "hybrid reranking precision", "top_k": 3, "threshold": 0.5},
        headers=auth_headers,
    )
    assert search.status_code == 200
    assert len(search.json()["citations"]) >= 1

    # 4. Content Studio generate -> [REVIEW REQUIRED] + cross-user isolation
    content = await client.post(
        "/api/v1/content/generate",
        json={"topic": "Hybrid Vector RAG", "content_type": "article", "save_to_pipeline": True},
        headers=auth_headers,
    )
    assert content.status_code == 200
    cdata = content.json()
    assert REVIEW_MARKER in cdata["body_markdown"]
    item_id = cdata["saved_item"]["id"]

    # Another regular user cannot access or delete owner's draft content
    cross_get = await client.get(f"/api/v1/content/items/{item_id}", headers=other_auth_headers)
    assert cross_get.status_code == 403
    cross_del = await client.delete(f"/api/v1/content/items/{item_id}", headers=other_auth_headers)
    assert cross_del.status_code == 403
