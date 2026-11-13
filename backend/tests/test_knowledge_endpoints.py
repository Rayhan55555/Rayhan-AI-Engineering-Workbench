import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User


@pytest.mark.asyncio
async def test_knowledge_stats_endpoint(client: AsyncClient, auth_headers: dict, test_user: User):
    res = await client.get("/api/v1/knowledge/stats", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_documents" in data
    assert "total_chunks" in data
    assert "total_tokens" in data
    assert "coverage_topics" in data


@pytest.mark.asyncio
async def test_knowledge_ingest_and_documents_endpoint(client: AsyncClient, auth_headers: dict, test_user: User):
    # Upload markdown file
    file_content = b"# API Guide\n\nFastAPI handles asynchronous request routing and Swagger UI generation.\n"
    files = {"file": ("guide.md", io.BytesIO(file_content), "text/markdown")}
    data = {"title": "API Guide", "access_level": "private"}

    res = await client.post("/api/v1/knowledge/ingest", headers=auth_headers, files=files, data=data)
    assert res.status_code == 202
    result = res.json()
    assert result["title"] == "API Guide"
    assert result["chunks_created"] >= 1
    assert result["skipped"] is False

    # List documents
    res_list = await client.get("/api/v1/knowledge/documents", headers=auth_headers)
    assert res_list.status_code == 200
    doc_data = res_list.json()
    assert doc_data["total"] >= 1
    assert any(d["title"] == "API Guide" for d in doc_data["items"])


@pytest.mark.asyncio
async def test_knowledge_search_endpoint(client: AsyncClient, auth_headers: dict, test_user: User):
    # Perform search
    search_payload = {
        "query": "FastAPI request routing",
        "top_k": 5,
        "threshold": 0.5,
    }
    res = await client.post("/api/v1/knowledge/search", headers=auth_headers, json=search_payload)
    assert res.status_code == 200
    search_data = res.json()
    assert search_data["query"] == "FastAPI request routing"
    assert "results" in search_data
    assert "citations" in search_data


@pytest.mark.asyncio
async def test_knowledge_delete_endpoint(client: AsyncClient, auth_headers: dict, test_user: User):
    # Ingest document
    file_content = b"Content to be deleted via soft delete."
    files = {"file": ("temp.txt", io.BytesIO(file_content), "text/plain")}
    data = {"title": "Temp Doc", "access_level": "private"}

    ingest_res = await client.post("/api/v1/knowledge/ingest", headers=auth_headers, files=files, data=data)
    assert ingest_res.status_code == 202
    doc_id = ingest_res.json()["document_id"]

    # Delete document
    del_res = await client.delete(f"/api/v1/knowledge/documents/{doc_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Verify not in list
    res_list = await client.get("/api/v1/knowledge/documents", headers=auth_headers)
    items = res_list.json()["items"]
    assert not any(d["id"] == doc_id for d in items)
