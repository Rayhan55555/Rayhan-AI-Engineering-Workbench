"""Phase 14 Performance & Latency Verification Suite.

Measures real wall-clock response times against Phase 14 SLO targets:
- GET  /api/v1/health             < 50ms (warm)
- POST /api/v1/auth/login         < 500ms
- GET  /api/v1/projects           < 200ms
- GET  /api/v1/agents             < 100ms
- GET  /api/v1/mcp/tools          < 100ms
- GET  /api/v1/portfolio/profile  < 100ms
- POST /api/v1/knowledge/search   < 2000ms
- POST /api/v1/content/generate   < 5000ms
- DB simple SELECT / paginated list / aggregation queries
- Frontend entry gzipped bundle < 500KB (when dist/ built)
"""

import gzip
import time
from pathlib import Path
import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.project import Project
from backend.app.models.user import User


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


@pytest.mark.asyncio
async def test_api_endpoint_latency_targets(
    client: AsyncClient, test_user: User, auth_headers: dict
):
    # Warm health route once for SQLite connection & route dispatch warmup
    warm = await client.get("/api/v1/health")
    assert warm.status_code == 200

    # 1. Health < 50ms
    t0 = time.perf_counter()
    h = await client.get("/api/v1/health")
    health_ms = _elapsed_ms(t0)
    assert h.status_code == 200
    assert health_ms < 50.0, f"Health latency {health_ms:.2f}ms exceeded 50ms"

    # 2. Auth login < 500ms
    t0 = time.perf_counter()
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "SecurePass123!"},
        headers={"X-Forwarded-For": "10.14.2.20"},
    )
    login_ms = _elapsed_ms(t0)
    assert login.status_code == 200
    assert login_ms < 500.0, f"Auth login latency {login_ms:.2f}ms exceeded 500ms"

    # 3. Project list < 200ms
    t0 = time.perf_counter()
    proj = await client.get("/api/v1/projects", headers=auth_headers)
    proj_ms = _elapsed_ms(t0)
    assert proj.status_code == 200
    assert proj_ms < 200.0, f"Project list latency {proj_ms:.2f}ms exceeded 200ms"

    # 4. Agent list < 100ms
    t0 = time.perf_counter()
    agents = await client.get("/api/v1/agents")
    agent_ms = _elapsed_ms(t0)
    assert agents.status_code == 200
    assert agent_ms < 100.0, f"Agent list latency {agent_ms:.2f}ms exceeded 100ms"

    # 5. MCP tool list < 100ms
    t0 = time.perf_counter()
    tools = await client.get("/api/v1/mcp/tools", headers=auth_headers)
    mcp_ms = _elapsed_ms(t0)
    assert tools.status_code == 200
    assert mcp_ms < 100.0, f"MCP tool list latency {mcp_ms:.2f}ms exceeded 100ms"

    # 6. Portfolio profile < 100ms
    t0 = time.perf_counter()
    prof = await client.get("/api/v1/portfolio/profile")
    prof_ms = _elapsed_ms(t0)
    assert prof.status_code == 200
    assert prof_ms < 100.0, f"Portfolio profile latency {prof_ms:.2f}ms exceeded 100ms"

    # 7. RAG Search < 2000ms
    t0 = time.perf_counter()
    rag = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "architecture patterns", "top_k": 5, "threshold": 0.0},
        headers=auth_headers,
    )
    rag_ms = _elapsed_ms(t0)
    assert rag.status_code == 200
    assert rag_ms < 2000.0, f"RAG search latency {rag_ms:.2f}ms exceeded 2000ms"

    # 8. Content Generate < 5000ms
    t0 = time.perf_counter()
    gen = await client.post(
        "/api/v1/content/generate",
        json={"topic": "FastAPI Security Hardening", "content_type": "article", "save_to_pipeline": False},
        headers=auth_headers,
    )
    gen_ms = _elapsed_ms(t0)
    assert gen.status_code == 200
    assert gen_ms < 5000.0, f"Content generate latency {gen_ms:.2f}ms exceeded 5000ms"


@pytest.mark.asyncio
async def test_database_query_performance(db_session: AsyncSession, test_user: User):
    for i in range(15):
        db_session.add(
            Project(name=f"Perf Project {i}", description="Benchmark", status="Active", owner_id=test_user.id)
        )
    await db_session.commit()

    # Simple SELECT < 50ms
    t0 = time.perf_counter()
    await db_session.execute(text("SELECT 1"))
    simple_ms = _elapsed_ms(t0)
    assert simple_ms < 50.0, f"Simple SELECT took {simple_ms:.2f}ms"

    # Paginated list < 100ms
    t0 = time.perf_counter()
    rows = (
        await db_session.execute(
            select(Project).where(Project.owner_id == test_user.id).order_by(Project.created_at.desc()).limit(10)
        )
    ).scalars().all()
    list_ms = _elapsed_ms(t0)
    assert len(rows) == 10
    assert list_ms < 100.0, f"Paginated query took {list_ms:.2f}ms"

    # Aggregation < 200ms
    t0 = time.perf_counter()
    total = (await db_session.execute(select(func.count(Project.id)))).scalar_one()
    agg_ms = _elapsed_ms(t0)
    assert total >= 15
    assert agg_ms < 200.0, f"Aggregation took {agg_ms:.2f}ms"


def test_frontend_entry_bundle_under_500kb_gzipped():
    """Verify initial Vite entry bundle stays under 500KB gzipped when built."""
    assets_dir = Path("dist/assets")
    if not assets_dir.exists():
        pytest.skip("dist/assets not present — run npm run build before bundle size check.")

    entry_bundles = sorted(assets_dir.glob("index-*.js"))
    assert entry_bundles, "No Vite entry bundle (index-*.js) found in dist/assets."
    for bundle in entry_bundles:
        gz_bytes = len(gzip.compress(bundle.read_bytes()))
        gz_kb = gz_bytes / 1024.0
        assert gz_kb < 500.0, f"Frontend entry bundle {bundle.name} is {gz_kb:.1f}KB gzipped (>500KB)"
