# Production Deployment Checklist — Rayhan AI Engineering Workbench (v1.0.0)

> Pre-deployment, deployment, rollback, and post-deployment operational checklist grounded in Phase 14 security, migration, and reliability verification.

---

## 1. Pre-Deployment Verification

### Code Quality & Automated Tests
- [x] Full backend test suite passing (196 pre-existing Phase 01–13 tests + Phase 14 E2E, performance, and final audit integration tests)
- [x] Frontend TypeScript build clean (`npm run build` — gzipped initial entry chunk ~158.5 KB, under 500 KB budget)
- [x] Frontend lint check clean (`npm run lint` / `tsc --noEmit`)
- [x] Security Audit (`backend/app/security/final_audit.py`) has **0 FAIL** findings across all 7 categories
- [x] Zero real secrets hardcoded in `backend/app` or `src` (`.env` excluded via `.gitignore`)
- [ ] **Host Requirement**: Generate exact pinned dependency lockfile (`pip freeze > backend/requirements.lock`) prior to immutable container release (`DEP-02` non-critical warning)

### Database & Alembic Migrations
- [x] All 16 SQLAlchemy tables covered by Alembic migrations (`001_initial_schema` through `004_phase_12_13_content_portfolio`)
- [x] `alembic upgrade head` and `alembic downgrade base` -> `upgrade head` cycle tested
- [x] PostgreSQL offline DDL (`alembic upgrade head --sql`) verified cleanly including `CREATE EXTENSION IF NOT EXISTS vector`
- [ ] **Host Requirement**: Run `alembic upgrade head` against target live PostgreSQL (`pgvector/pgvector:pg15`) instance and verify `alembic current` prints `004_phase_12_13_content_portfolio (head)`
- [ ] **Host Requirement**: Document and verify encrypted automated PostgreSQL backup schedule (`pg_dump` / snapshot retention)
- [x] SQLAlchemy async connection pool configured (`pool_pre_ping=True`, `pool_size`, `max_overflow`) in `backend/app/database.py`

### Infrastructure & Containers
- [x] `backend/Dockerfile` aligned with repository root build context (`COPY backend/requirements.txt`, non-root `USER appuser`)
- [x] `docker-compose.yml` updated to `pgvector/pgvector:pg15`, backend healthcheck, and memory resource limits
- [ ] **Host Requirement**: Execute `docker compose build` and `docker compose config --quiet` on Docker-enabled CI/target host (blocked inside sandbox lacking Docker daemon)
- [ ] **Host Requirement**: Configure TLS termination (HTTPS via Nginx / Caddy / Cloud Load Balancer) and bind public domain
- [ ] **Host Requirement**: Set strict `CORS_ORIGINS` env var matching production origin(s)

### Security Configuration (Mandatory Overrides)
- [ ] **Mandatory**: Override `SECRET_KEY` with a freshly generated 64-char hex secret (`openssl rand -hex 32`) (`SEC-04` check)
- [x] Debug mode disabled (`DEBUG=false` by default in `backend/app/config.py`)
- [x] Authentication enforcement verified across all non-public HTTP routes and `/api/v1/ws/{user_id}` WebSocket endpoint
- [x] Sliding-window rate limiting enabled on global (`60/min`), auth (`5/min`), portfolio reads (`30/min`), demos (`10/min`), and contact inquiries (`3/hr`)
- [x] MCP tool audit scrubbing and AI Gateway error key redaction verified
- [x] Frontend Mermaid diagram XSS hardening (`securityLevel: 'strict'` + `DOMParser` SVG sanitization)

### Monitoring & Observability
- [x] `/api/v1/health` and `/api/v1/devops/health` endpoints returning structured liveness/readiness JSON
- [x] Structured JSON access logging middleware (`StructuredLoggingMiddleware`) recording request ID, method, path, status, and duration
- [ ] **Host Requirement**: Attach log aggregation, uptime alerting, and multi-worker Redis/Nginx rate limiter store if scaling horizontally beyond 1 worker

---

## 2. Deployment Procedure

1. **Pull & Verify Environment**
   - Ensure `.env` exists on host (never committed to git) with strong `SECRET_KEY`, `POSTGRES_*`, `DATABASE_URL`, `CORS_ORIGINS`, and optional `GEMINI_API_KEY` / `ANTHROPIC_API_KEY`.
2. **Run Final Verification Gate**
   - `npm run build`
   - `PYTHONPATH=. pytest backend/tests -v`
3. **Build & Validate Containers**
   - `docker compose config --quiet`
   - `docker compose build`
4. **Apply Database Migrations**
   - Start database service first: `docker compose up -d db`
   - Apply migrations: `docker compose run --rm backend alembic -c backend/alembic.ini upgrade head`
   - Verify head: `docker compose run --rm backend alembic -c backend/alembic.ini current`
5. **Start Backend & Frontend Services**
   - `docker compose up -d`
   - Seed initial 8–9 agents (superuser token) via `POST /api/v1/agents/seed`
6. **Health & Smoke Verification**
   - Check `GET /api/v1/health` and `GET /api/v1/devops/health` return HTTP `200`.
   - Confirm `/api/v1/portfolio/profile` returns HTTP `200` and `/api/v1/projects` unauthenticated returns HTTP `401`.
7. **Superuser Deployment Gate**
   - Inside Workbench UI/API, verify `/api/v1/devops/readiness` reports zero `BLOCKED` checks before marking staging/production release live.
8. **Post-Release Observation (30 Minutes)**
   - Watch structured request logs for `5xx` responses, rate-limit `429` spikes, database pool saturation, or auth errors.

---

## 3. Rollback Plan

1. **Application Rollback**:
   - Re-deploy previous known-good container tag or invoke `POST /api/v1/devops/rollback/{deployment_id}` (superuser required) for Workbench release tracking.
2. **Database Schema Rollback (if schema migration caused issue)**:
   - Restore latest pre-migration `pg_dump` snapshot or run bounded downgrade:
     `alembic -c backend/alembic.ini downgrade -1`
3. **Token Invalidation (if credential compromise suspected)**:
   - Rotate `SECRET_KEY`, restart backend workers, and instruct active users to re-authenticate.

---

## 4. Post-Deployment Sign-Off

- [ ] `GET /api/v1/health` -> `200 OK`
- [ ] `POST /api/v1/auth/login` + `GET /api/v1/auth/me` -> `200 OK`
- [ ] Public portfolio (`/#portfolio`) returns public-only records (no drafts or private projects)
- [ ] Internal workbench (`/#workbench`) enforces authentication & ownership isolation
- [ ] Error rate steady (`< 0.1%` 5xx over 30-minute observation window)
