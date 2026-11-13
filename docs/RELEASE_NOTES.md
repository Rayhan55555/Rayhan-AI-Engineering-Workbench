# Rayhan AI Engineering Workbench
## v1.0.0 — Initial Release

---

## Overview

Personal AI engineering workspace uniting **9 specialized AI engineering agents**, **18 sandboxed MCP tools**, a **pgvector hybrid RAG knowledge system**, an **AI Gateway (Gemini + Claude fallback)**, **DevOps CI/CD workflows**, **Content Studio**, and an **isolated Public Portfolio** behind strict JWT authentication and ownership controls.

---

## What's Included

### Specialized Agents (9 Production Agents + 1 Workflow Stub)
1. **Coding Agent** (`arch-sentinel`) — AST structure analysis, refactoring guidance, and syntax inspection
2. **Security Agent** (`security-agent`) — Secret exposure detection, CWE rule catalog scanning, and auth auditing
3. **Testing Agent** (`testing-agent`) — Coverage calculation, test gap analysis, failure triage, and deterministic test synthesis
4. **Architecture Agent** (`architecture-agent`) — System coupling evaluation, Mermaid diagram generation, and ADR authoring
5. **Documentation Agent** (`documentation-agent`) — Docstring coverage audit, broken-link inspection, and runbook generation
6. **RAG / Knowledge Agent** (`rag-engine-v1`) — Multi-tenant document ingestion, hybrid vector search, 4-factor reranking, and grounded citations
7. **DevOps Agent** (`devops-agent`) — GitHub Actions CI/CD generation, Dockerfile/Compose validation, readiness gating, and rollback orchestration
8. **Content Agent** (`masterclass-synth`) — Technical articles, architecture case studies, YouTube scripts, LinkedIn posts, and Twitter threads (`[REVIEW REQUIRED]` enforced)
9. **Eval Matrix Agent** (`eval-matrix`) — Regression benchmarking for faithfulness, prompt injection resistance, and schema accuracy
*(Plus `flow-executor` maintained strictly as an execution-stub test harness agent.)*

### Key Capabilities
- **AI Gateway**: Complexity-aware routing across Gemini (`2.0-flash`, `1.5-pro`) and Claude (`claude-3-5-sonnet`) with fallback, USD/token accounting (`llm_usage`), and API key redaction in error outputs
- **MCP Tool Protocol (18 Tools)**: Read-only (`READ_ONLY`) tools execute immediately; state-mutating (`IMPLEMENT` / `DEPLOY`) tools enforce explicit human approval queues and scrubbed `tool_audits` logs
- **Hybrid Vector RAG (`pgvector`)**: Semantic + size-bounded ingestion (10MB limit, `.env`/binary blocking), duplicate SHA-256 detection, cosine retrieval, reranking, and inline citation tracking
- **DevOps Automation & Safety Gates**: Superuser-gated deploy & rollback, `BLOCKED` checklist enforcement, and Dockerfile/Compose static analyzer (`pgvector/pgvector:pg15`)
- **Content Studio & Pipeline**: Enforces `Idea -> Outline -> Draft -> Approved -> Published` with `[REVIEW REQUIRED]` watermark on drafts and superuser gate on publishing
- **Public Portfolio & Safe Demos**: Cohesive dark-obsidian React SPA showcase strictly isolated to `is_public == True` projects and `Published` content, featuring read-only Code AST, Security Scanner, and Mermaid Architecture Diagram demos plus 3/hr rate-limited contact form
- **Database Schema & Alembic**: Complete 16-table schema tracked across revisions `001` through `004`
- **Security Hardening (Phase 14)**: Cross-user ownership checks enforced across all user-scoped routers, JWT validation on WebSocket connections, strict Mermaid SVG sanitization (`securityLevel: 'strict'` + `DOMParser`), and a 29-check automated security auditor

### Tech Stack
- **Frontend**: React 19 + TypeScript + Vite 8 + Tailwind CSS v4 SPA (hash-based portfolio & workbench views; zero-reload transitions; gzipped entry bundle ~158.5 KB)
- **Backend**: FastAPI (Python 3.10+) + SQLAlchemy Async ORM + Alembic
- **AI Providers**: Google Gemini (`gemini-2.0-flash` / `1.5-pro` / `text-embedding-004`) + Anthropic Claude fallback
- **Vector & Relational Store**: PostgreSQL 15+ with `pgvector` extension (local SQLite async fallback supported for unit/integration tests)
- **Security & Auth**: JWT (`HS256`, short-lived access tokens + SHA-256 rotated refresh tokens) + `bcrypt` (cost factor 12) + sliding-window rate limiter
- **Deployment**: Docker + `docker-compose.yml` (`pgvector/pgvector:pg15`, non-root backend user, healthcheck)

---

## Known Limitations (Honest Disclosure)

1. **Docker & Live PostgreSQL Execution Blocked in Sandbox**: The CI/build sandbox lacks a running Docker daemon and live PostgreSQL server. Alembic Postgres DDL was verified via `--sql` offline mode and full live schema/CRUD checks were executed against SQLite (`aiosqlite`); target host must run `docker compose build` and `alembic upgrade head` against live `pgvector/pgvector:pg15`.
2. **Offline / Unkeyed External Provider Fallbacks**: When `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` are unset, `Embedder` honestly returns `None` (no fabricated vectors) and `AgentExecution` records mark `simulated: true` where deterministic local execution applies.
3. **Production `SECRET_KEY` Override Required**: `backend/app/config.py` ships with a documented development fallback key (`SEC-04` warning); production deployments **must** supply a freshly generated `SECRET_KEY` via environment variables.
4. **Dependency Lockfile**: `backend/requirements.txt` uses upper-bounded version ranges (`DEP-02` warning) rather than exact `==` hashes; run `pip freeze > backend/requirements.lock` on the release build host for deterministic image builds.
5. **Single-Process In-Memory Rate Limiter**: `RateLimitMiddleware` stores sliding-window counters in process memory. Multi-worker production scaling should back rate limiting with Redis or an ingress API gateway.
6. **Frontend Dev Standalone vs Coupled API Origin**: Running `vite dev` alone without FastAPI running on `/api/v1` causes live portfolio fetches to fall back gracefully after `404` API calls unless served behind a shared reverse proxy or coupled deployment.

---

## Next Steps (Post-v1.0.0 Roadmap)

- Wire Redis-backed distributed rate limiting and multi-worker pub/sub for WebSocket execution updates
- Generate hashed `requirements.lock` + automated Trivy/pip-audit CI security gate on PRs
- Add automated Postgres + `pgvector` service container job inside `.github/workflows/` CI
- Introduce end-to-end authenticated user onboarding and superuser role management UI inside the Workbench Settings view
