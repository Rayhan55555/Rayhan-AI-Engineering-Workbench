# API Reference — Rayhan AI Engineering Workbench (v1.0.0)

> Complete HTTP REST & WebSocket API specification matching the live FastAPI OpenAPI schema (`88` HTTP endpoints + `1` WebSocket endpoint).

- **Base URL**: `/api/v1` (except `GET /`)
- **Authentication**: Bearer JWT access token (`Authorization: Bearer <access_token>`) obtained via `/api/v1/auth/login`.
- **Standard Error Schema**:
  - `401 Unauthorized` / `403 Forbidden`: `{"error": "http_error", "message": "...", "status_code": 401|403}`
  - `422 Unprocessable Entity`: `{"error": "validation_error", "message": "...", "status_code": 422}`
  - `429 Too Many Requests`: Sliding-window rate limit exceeded (includes `Retry-After` header)
  - `500 Internal Server Error`: `{"error": "internal_server_error", "message": "An unexpected error occurred. Please contact the administrator.", "status_code": 500}`
- **Default Global Rate Limit**: `60 req/min` per client IP unless stricter per-route limit applies.

---

## 1. Root & Health

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `GET` | `/` | Public | 60/min | API root metadata & version info (`200`) |
| `GET` | `/api/v1/health` | Public | 60/min | Service liveness & database connectivity probe (`200`) |

---

## 2. Authentication (`/api/v1/auth`)

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Public | 5/min | Register user (`email`, `username`, `password`) -> `201 Created` |
| `POST` | `/api/v1/auth/login` | Public | 5/min | Exchange credentials (`username`, `password`) for `access_token` + `refresh_token` -> `200` |
| `POST` | `/api/v1/auth/refresh` | Public | 5/min | Rotate refresh token and issue new token pair (`refresh_token`) -> `200` |
| `POST` | `/api/v1/auth/logout` | Bearer | 5/min | Revoke all active refresh tokens for user -> `204 No Content` |
| `GET` | `/api/v1/auth/me` | Bearer | 60/min | Return current authenticated user profile -> `200` |

---

## 3. Projects (`/api/v1/projects`)

All endpoints enforce user ownership (`owner_id == current_user.id` or superuser).

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/projects` | Bearer | 60/min | List current user's projects (`limit`, `offset`, `status`) -> `200` |
| `POST` | `/api/v1/projects` | Bearer | 60/min | Create project (`name`, `description`, `tech_stack`, `repo_url`) -> `201` |
| `GET` | `/api/v1/projects/{id}` | Bearer (Owner) | 60/min | Get project detail (`403` on cross-user access) -> `200` |
| `PATCH` | `/api/v1/projects/{id}` | Bearer (Owner) | 60/min | Update project fields -> `200` |
| `DELETE` | `/api/v1/projects/{id}` | Bearer (Owner) | 60/min | Soft delete project (`status = Archived`) -> `204` |

---

## 4. Agent Registry (`/api/v1/agents`)

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/agents` | Public | 30/min | List registered agents (`status`, `phase`, `search`) -> `200` |
| `GET` | `/api/v1/agents/{slug}` | Public | 30/min | Get single agent metadata & capabilities -> `200` |
| `POST` | `/api/v1/agents/seed` | Superuser | 60/min | Seed core Phase 01 agent catalog -> `200` |
| `PATCH` | `/api/v1/agents/{slug}` | Superuser | 60/min | Update agent specification -> `200` |
| `POST` | `/api/v1/agents/{slug}/configure` | Superuser | 60/min | Configure agent (`Planned` -> `Configured`) -> `200` |
| `PATCH` | `/api/v1/agents/{slug}/status` | Superuser | 60/min | Transition agent lifecycle state -> `200` |

---

## 5. Agent Executions (`/api/v1/executions`)

All execution reads/cancellations verify `execution.user_id == current_user.id` or superuser. `IMPLEMENT` / `DEPLOY` scopes pause at `Pending` until explicitly approved.

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/executions` | Bearer | 60/min | Queue background execution (`agent_slug`, `instruction`, `scope`, `project_id`) -> `202` |
| `GET` | `/api/v1/executions` | Bearer | 60/min | Paginated list of user's executions -> `200` |
| `GET` | `/api/v1/executions/{execution_id}` | Bearer (Owner) | 60/min | Get execution status, `output`, and `simulated` metadata -> `200` |
| `DELETE` | `/api/v1/executions/{execution_id}` | Bearer (Owner) | 60/min | Cancel pending or running execution -> `200` |
| `POST` | `/api/v1/executions/{execution_id}/approve` | Bearer (Owner) | 60/min | Approve `Pending` execution (`IMPLEMENT` scope) -> `200` |
| `POST` | `/api/v1/executions/{execution_id}/reject` | Bearer (Owner) | 60/min | Reject `Pending` execution (`Cancelled`) -> `200` |

---

## 6. Coding / Security Agent (`/api/v1/security`)

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/security/rules` | Bearer | 60/min | List static security rules & CWE remediation catalog -> `200` |
| `POST` | `/api/v1/security/scan` | Bearer | 60/min | Trigger security scan (`target`, `path`, `scan_types`) -> `202` |
| `GET` | `/api/v1/security/scans` | Bearer (Owner) | 60/min | List user's past security scans & severity summaries -> `200` |
| `GET` | `/api/v1/security/scans/{execution_id}` | Bearer (Owner) | 60/min | Get detailed scan findings, evidence, and artifacts -> `200` |

---

## 7. Testing Agent (`/api/v1/testing`)

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/testing/analyze` | Bearer | 60/min | Trigger coverage/gap/quality/failure analysis -> `202` |
| `POST` | `/api/v1/testing/generate` | Bearer | 60/min | Generate deterministic test templates (`SUGGEST` only) -> `200` |
| `POST` | `/api/v1/testing/run` | Bearer | 60/min | Queue test execution (`IMPLEMENT` approval required) -> `202` |
| `GET` | `/api/v1/testing/reports` | Bearer (Owner) | 60/min | List user's testing reports -> `200` |
| `GET` | `/api/v1/testing/reports/{execution_id}` | Bearer (Owner) | 60/min | Get detailed test execution output & evidence -> `200` |

---

## 8. AI Gateway (`/api/v1/gateway`)

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/gateway/complete` | Bearer | 60/min | Guarded Gemini + Claude fallback completion with token accounting -> `200` |
| `GET` | `/api/v1/gateway/models` | Bearer | 60/min | Supported model catalog, pricing, and context limits -> `200` |
| `GET` | `/api/v1/gateway/providers` | Bearer | 60/min | Provider configuration status & rate-limit headroom -> `200` |
| `GET` | `/api/v1/gateway/usage` | Bearer | 60/min | Aggregated token & USD spend breakdown (`llm_usage`) -> `200` |
| `GET` | `/api/v1/gateway/usage/daily` | Bearer | 60/min | Daily token/cost rollup for last `N` days -> `200` |

---

## 9. MCP & Tool Integrations (`/api/v1/mcp`) + WebSocket

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/mcp/tools` | Bearer | 60/min | List 18 MCP tools (`category`, `scope`) -> `200` |
| `GET` | `/api/v1/mcp/tools/{name}` | Bearer | 60/min | Inspect tool JSON schema, scope, and approval flags -> `200` |
| `POST` | `/api/v1/mcp/tools/{name}/execute` | Bearer | 60/min | Execute read-only tool or queue approval for write/deploy tools -> `200` |
| `GET` | `/api/v1/mcp/approvals` | Bearer | 60/min | List pending MCP tool approval requests -> `200` |
| `POST` | `/api/v1/mcp/approvals/{approval_id}/approve` | Bearer | 60/min | Approve queued write/deploy tool request -> `200` |
| `POST` | `/api/v1/mcp/approvals/{approval_id}/reject` | Bearer | 60/min | Reject queued request with optional reason -> `200` |
| `GET` | `/api/v1/mcp/audit` | Bearer | 60/min | Paginated immutable tool audit logs (secrets redacted) -> `200` |
| `GET` | `/api/v1/mcp/stream/demo` | Public | 60/min | SSE synthetic demo event stream for frontend `EventSource` UI preview -> `200` |
| `WS` | `/api/v1/ws/{user_id}` | JWT (`?token=` or `Bearer`) | — | Authenticated execution status stream bound strictly to JWT `sub == user_id` (`1008` on mismatch) |

---

## 10. Architecture Agent (`/api/v1/architecture`)

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/architecture/analyze` | Bearer | 60/min | Structural coupling, module boundary, and scalability analysis -> `200` |
| `POST` | `/api/v1/architecture/diagram` | Bearer | 60/min | Generate validated Mermaid diagram (`flowchart`, `sequence`, `er`) -> `200` |
| `POST` | `/api/v1/architecture/adr` | Bearer | 60/min | Draft structured Architecture Decision Record (ADR) -> `200` |
| `GET` | `/api/v1/architecture/adrs` | Bearer | 60/min | List saved/generated ADR artifacts -> `200` |

---

## 11. Documentation Agent (`/api/v1/docs`)

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/docs/generate` | Bearer | 60/min | Generate technical documentation draft (`readme`, `runbook`, `guide`) -> `200` |
| `POST` | `/api/v1/docs/audit` | Bearer | 60/min | Audit repository documentation freshness & broken links -> `200` |
| `GET` | `/api/v1/docs/coverage` | Bearer | 60/min | Docstring & module documentation coverage metrics -> `200` |

---

## 12. Knowledge & RAG (`/api/v1/knowledge`)

Document mutations/reads enforce `owner_id == current_user.id` or `access_level == public`.

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/knowledge/ingest` | Bearer | 60/min | Upload file (max 10MB, blocks `.env`/binaries) or URL into chunked vector store -> `202` |
| `GET` | `/api/v1/knowledge/documents` | Bearer | 60/min | List accessible non-deleted documents -> `200` |
| `DELETE` | `/api/v1/knowledge/documents/{doc_id}` | Bearer (Owner) | 60/min | Soft delete document (`is_deleted = True`) -> `204` |
| `POST` | `/api/v1/knowledge/search` | Bearer | 60/min | Cosine similarity search + 4-factor reranking + grounded citations -> `200` |
| `GET` | `/api/v1/knowledge/stats` | Bearer | 60/min | Document, chunk, and token footprint statistics -> `200` |
| `POST` | `/api/v1/knowledge/evaluate` | Superuser | 60/min | Run RAG precision/recall evaluation benchmark -> `200` |

---

## 13. DevOps Workflows (`/api/v1/devops`)

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/devops/health` | Public | 60/min | Infrastructure & dependency readiness summary -> `200` |
| `GET` | `/api/v1/devops/docker/analyze` | Bearer | 60/min | Static Dockerfile & Compose security/best-practice analyzer -> `200` |
| `POST` | `/api/v1/devops/cicd/generate` | Bearer | 60/min | Generate GitHub Actions CI/CD workflow YAML -> `200` |
| `GET` | `/api/v1/devops/readiness` | Bearer | 60/min | Evaluate deployment readiness gates (`READY` / `WARNING` / `BLOCKED`) -> `200` |
| `GET` | `/api/v1/devops/deployments` | Bearer | 60/min | Paginated deployment audit history -> `200` |
| `POST` | `/api/v1/devops/deploy` | Superuser | 60/min | Trigger gated deployment (`BLOCKED` checklist blocks deploy -> `409`/`422`) -> `202` |
| `POST` | `/api/v1/devops/rollback/{deployment_id}` | Superuser | 60/min | Record and execute guarded rollback for prior deployment -> `200` |

---

## 14. Content Studio (`/api/v1/content`)

All item access/mutations enforce `item.created_by == current_user.id` or superuser; `Published` stage requires superuser transition.

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/content/generate` | Bearer | 60/min | Generate technical draft (`article`, `youtube`, `linkedin`, `twitter`, `case_study`; always marked `[REVIEW REQUIRED]`) -> `200` |
| `POST` | `/api/v1/content/research` | Bearer | 60/min | RAG-grounded topic research synthesis -> `200` |
| `GET` | `/api/v1/content/items` | Bearer | 60/min | List user's content items across pipeline stages -> `200` |
| `POST` | `/api/v1/content/items` | Bearer | 60/min | Create content item (`Idea` / `Outline` / `Draft`) -> `201` |
| `GET` | `/api/v1/content/items/{item_id}` | Bearer (Owner) | 60/min | Get content item detail (`403` on cross-user access) -> `200` |
| `PATCH` | `/api/v1/content/items/{item_id}` | Bearer (Owner) | 60/min | Edit content item (`403` on cross-user access) -> `200` |
| `POST` | `/api/v1/content/items/{item_id}/transition` | Bearer (Owner/Superuser) | 60/min | Advance stage (`Idea -> Outline -> Draft -> Approved -> Published`) -> `200` |
| `DELETE` | `/api/v1/content/items/{item_id}` | Bearer (Owner) | 60/min | Delete content item -> `204` |
| `GET` | `/api/v1/content/calendar` | Bearer | 60/min | View user-scoped editorial calendar schedule -> `200` |

---

## 15. Public Portfolio & Admin Curation (`/api/v1/portfolio`)

Public routes return `is_public == True` projects and `Published` content items only — zero drafts, credentials, user emails, or inquiries are exposed.

| Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/portfolio/profile` | Public | 30/min | Public architect profile, engineering stack, and capabilities -> `200` |
| `GET` | `/api/v1/portfolio/projects` | Public | 30/min | List public showcase projects (`is_public == True`) -> `200` |
| `GET` | `/api/v1/portfolio/projects/{slug}` | Public | 30/min | Get public project detail (`404` for private/missing slugs) -> `200` |
| `GET` | `/api/v1/portfolio/case-studies` | Public | 30/min | List published architecture case studies -> `200` |
| `GET` | `/api/v1/portfolio/case-studies/{slug}` | Public | 30/min | Get single published case study -> `200` |
| `GET` | `/api/v1/portfolio/articles` | Public | 30/min | List published technical articles -> `200` |
| `GET` | `/api/v1/portfolio/articles/{slug}` | Public | 30/min | Get single published article -> `200` |
| `GET` | `/api/v1/portfolio/demos` | Public | 30/min | List safe isolated portfolio sandboxes -> `200` |
| `POST` | `/api/v1/portfolio/demos/{slug}/run` | Public | 10/min | Execute read-only isolated sample demo (`code-analyzer`, `security-scanner`, `architecture-diagram`) -> `200` |
| `POST` | `/api/v1/portfolio/contact` | Public | **3/hr** | Submit public engineering inquiry (`contact_inquiries` persistence) -> `200` |
| `POST` | `/api/v1/portfolio/projects` | Bearer | 60/min | Create portfolio project record (private by default) -> `201` |
| `PATCH` | `/api/v1/portfolio/projects/{project_id}` | Bearer (Owner) | 60/min | Update portfolio project (`403` on cross-user access) -> `200` |
| `PATCH` | `/api/v1/portfolio/projects/{project_id}/publish` | Superuser | 60/min | Toggle `is_public` showcase visibility -> `200` |
