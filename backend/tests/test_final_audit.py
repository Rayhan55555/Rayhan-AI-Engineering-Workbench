"""Phase 14 Final Security, Migration, Documentation & Integrity Verification."""

from pathlib import Path
import pytest
from httpx import AsyncClient

from backend.app.database import Base
from backend.app.main import app as fastapi_app
from backend.app.sandbox.restrictions import PROJECT_ROOT
from backend.app.security.final_audit import FinalSecurityAuditor
from backend.app.tools.docker_validator import DockerValidator


def test_final_security_audit_has_zero_failures():
    report = FinalSecurityAuditor.run_full_audit()
    assert report.total_checks >= 25
    assert report.failed == 0, f"Critical security failures found: {[c for cat in report.categories for c in cat.checks if c.status == 'FAIL']}"
    assert report.overall_status in ("PASS", "WARNING")


def test_alembic_migrations_cover_all_sqlalchemy_models():
    versions_dir = PROJECT_ROOT / "backend" / "migrations" / "versions"
    migration_files = list(versions_dir.glob("*.py"))
    assert len(migration_files) >= 4
    combined_migrations = "\n".join(f.read_text(encoding="utf-8") for f in migration_files)

    # Ensure every SQLAlchemy model table has a corresponding create_table in migrations
    missing = [
        table_name
        for table_name in Base.metadata.tables.keys()
        if f'"{table_name}"' not in combined_migrations and f"'{table_name}'" not in combined_migrations
    ]
    assert not missing, f"Models missing from Alembic migrations: {missing}"


def test_phase14_documentation_complete_and_openapi_aligned():
    docs_dir = PROJECT_ROOT / "docs"
    checklist = docs_dir / "PRODUCTION_CHECKLIST.md"
    api_ref = docs_dir / "API_REFERENCE.md"
    release_notes = docs_dir / "RELEASE_NOTES.md"

    for doc in (checklist, api_ref, release_notes):
        assert doc.exists(), f"Missing documentation file: {doc}"
        assert len(doc.read_text(encoding="utf-8").strip()) > 400

    api_text = api_ref.read_text(encoding="utf-8")
    spec = fastapi_app.openapi()
    missing_paths = [path for path in spec["paths"].keys() if path not in api_text]
    assert not missing_paths, f"API endpoints omitted from docs/API_REFERENCE.md: {missing_paths}"


def test_docker_and_compose_validation_passes():
    result = DockerValidator.analyze_project(str(PROJECT_ROOT))
    assert result.dockerfile_score >= 85
    assert not result.security_issues
    assert result.compose_summary is not None
    assert result.compose_summary.get("valid") is True


@pytest.mark.asyncio
async def test_phase14_remediated_authorization_and_routes(
    client: AsyncClient, auth_headers: dict, other_auth_headers: dict
):
    # 1. Content item cross-user isolation
    create_item = await client.post(
        "/api/v1/content/items",
        json={
            "title": "Confidential Draft",
            "content_type": "article",
            "body_markdown": "# Confidential",
            "target_platform": "blog",
        },
        headers=auth_headers,
    )
    assert create_item.status_code == 201
    item_id = create_item.json()["id"]

    other_get = await client.get(f"/api/v1/content/items/{item_id}", headers=other_auth_headers)
    assert other_get.status_code == 403
    other_patch = await client.patch(
        f"/api/v1/content/items/{item_id}",
        json={"title": "Tampered"},
        headers=other_auth_headers,
    )
    assert other_patch.status_code == 403
    other_del = await client.delete(f"/api/v1/content/items/{item_id}", headers=other_auth_headers)
    assert other_del.status_code == 403

    # 2. Portfolio project PATCH ownership isolation
    create_proj = await client.post(
        "/api/v1/portfolio/projects",
        json={
            "slug": "isolated-showcase-item",
            "title": "Isolated Showcase Item",
            "tagline": "Scoped showcase item for RBAC verification",
            "description": "Owned portfolio project record created for Phase 14 ownership verification.",
            "tech_stack": ["FastAPI"],
            "is_featured": False,
        },
        headers=auth_headers,
    )
    assert create_proj.status_code == 201
    proj_id = create_proj.json()["id"]
    other_proj_patch = await client.patch(
        f"/api/v1/portfolio/projects/{proj_id}",
        json={"title": "Hijacked"},
        headers=other_auth_headers,
    )
    assert other_proj_patch.status_code == 403

    # 3. Security & Testing detail endpoints return 200 (AttributeError regression check)
    sec_scans = await client.get("/api/v1/security/scans", headers=auth_headers)
    assert sec_scans.status_code == 200
    test_reports = await client.get("/api/v1/testing/reports", headers=auth_headers)
    assert test_reports.status_code == 200
