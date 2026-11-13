<div align="center">

# Rayhan AI Engineering Workbench

### *"Architecting Intelligence. Engineering the Future."*

**Built by [Rayhan](https://github.com/Rayhan55555) · [Curizx AI](https://rayhan-ai-engineering-workbench-production.up.railway.app)**

[![Tests](https://img.shields.io/badge/Tests-196%20passed-22c55e?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/Rayhan55555/Rayhan-AI-Engineering-Workbench)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](#-license)
[![Deploy](https://img.shields.io/badge/Deploy-Railway-8B5CF6?style=for-the-badge&logo=railway&logoColor=white)](https://rayhan-ai-engineering-workbench-production.up.railway.app)
[![Status](https://img.shields.io/badge/Status-Production-10B981?style=for-the-badge)](https://rayhan-ai-engineering-workbench-production.up.railway.app)

---

🚀 **[Live Production Deployment](https://rayhan-ai-engineering-workbench-production.up.railway.app)** · 📂 **[GitHub Repository](https://github.com/Rayhan55555/Rayhan-AI-Engineering-Workbench)** · 📖 **[API Reference](docs/API_REFERENCE.md)** · ✅ **[Production Checklist](docs/PRODUCTION_CHECKLIST.md)** · 🏷️ **[Release Notes v1.0.0](docs/RELEASE_NOTES.md)**

</div>

---

## 🧠 What It Does

**Rayhan AI Engineering Workbench** is an end-to-end Applied AI Systems Engineering workspace built under **Curizx AI**. It orchestrates **9 specialized AI engineering agents**, **18 sandboxed Model Context Protocol (MCP) tools**, a **hybrid `pgvector` RAG knowledge engine**, a **Content Studio**, and an **isolated Public Portfolio** inside a single, production-hardened platform. Every workflow enforces strict JWT/RBAC isolation, explicit human-in-the-loop approval checkpoints for mutating operations, and deterministic audit logging.

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    Client["🌐 React + TypeScript + Tailwind SPA<br/>Public Portfolio (#portfolio) & Workbench (#workbench)"]
    API["⚡ FastAPI API Gateway & Auth Layer<br/>JWT HS256 • Sliding-Window Rate Limiter • WebSocket /ws/{user_id}"]

    subgraph Agents["🤖 9 Specialized AI Agents"]
        A1["arch-sentinel<br/>Coding"]
        A2["security-agent<br/>Security"]
        A3["testing-agent<br/>QA & Coverage"]
        A4["architecture-agent<br/>Diagrams & ADRs"]
        A5["documentation-agent<br/>Docs & Audits"]
        A6["rag-engine-v1<br/>RAG Search"]
        A7["devops-agent<br/>CI/CD & Deploy"]
        A8["masterclass-synth<br/>Content Studio"]
        A9["eval-matrix<br/>Benchmarks"]
    end

    Gateway["🔀 Multi-Model AI Gateway<br/>Gemini 1.5 Primary → Claude Fallback • USD Telemetry"]
    MCP["🛠️ 18 Sandboxed MCP Tools<br/>READ_ONLY Immediate · IMPLEMENT/DEPLOY Approval Queue"]
    DB[("🗄️ PostgreSQL 15 + pgvector<br/>16 Tables • Alembic 004 Head • 768-dim Embeddings")]

    Client -->|"REST / SSE / WSS"| API
    API --> Agents
    Agents --> Gateway
    Agents --> MCP
    API --> DB
    Agents --> DB
    MCP -->|"Scrubbed Tool Audits"| DB
```

---

## 🤖 The 9 Specialized AI Agents

| # | Agent Name | Registry Slug | Core Responsibility & Safety Guardrails |
|---|---|---|---|
| 1 | **Coding Agent** | `arch-sentinel` | AST code structure inspection, multi-language diagnostics, and diff synthesis (`READ_ONLY` / `SUGGEST`) |
| 2 | **Security Agent** | `security-agent` | Secret scanning, CWE rule matching, auth & ownership auditing, dependency checks |
| 3 | **Testing Agent** | `testing-agent` | Coverage calculation, gap detection, failure root-cause analysis, test scaffolding |
| 4 | **Architecture Agent** | `architecture-agent` | System coupling evaluation, Mermaid.js topology synthesis, Architecture Decision Records (ADRs) |
| 5 | **Documentation Agent** | `documentation-agent` | Docstring coverage metrics, broken-link audits, technical runbook & guide generation |
| 6 | **RAG / Knowledge Agent** | `rag-engine-v1` | Hybrid `pgvector` semantic retrieval, 4-factor cross-scoring reranker, verified inline citations |
| 7 | **DevOps Agent** | `devops-agent` | GitHub Actions YAML synthesis, Dockerfile/Compose validation, readiness gating, superuser rollback |
| 8 | **Content Agent** | `masterclass-synth` | Technical articles, YouTube scripts, LinkedIn/Twitter threads, case studies (`[REVIEW REQUIRED]`) |
| 9 | **Eval Matrix Agent** | `eval-matrix` | Systematic regression harness measuring faithfulness, schema accuracy, and prompt resistance |

---

## 🧰 Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | FastAPI, Python 3.11, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2 |
| **Database & Vector** | PostgreSQL 15 + `pgvector` (768-dimensional vector cosine search), `aiosqlite` test parity |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Mermaid.js (`strict` SVG sanitization) |
| **AI Gateway** | Google Gemini 1.5 (`gemini-2.0-flash` / `1.5-pro` / `text-embedding-004`) + Anthropic Claude fallback |
| **Protocol & Auth** | Model Context Protocol (18 MCP tools), JWT (`HS256`), rotated SHA-256 refresh tokens, `bcrypt` |
| **Deployment** | Docker, `docker-compose`, GitHub Actions CI/CD, Railway Cloud |

---

## ⚡ Quick Start

```bash
# 1. Clone the repository & configure environment
git clone https://github.com/Rayhan55555/Rayhan-AI-Engineering-Workbench.git && cd Rayhan-AI-Engineering-Workbench
cp .env.example .env

# 2. Boot PostgreSQL (pgvector) + FastAPI backend via Docker Compose
docker compose up -d --build

# 3. Apply database migrations & seed initial agent catalog
docker compose exec backend alembic -c backend/alembic.ini upgrade head

# 4. Run the frontend development server (http://localhost:3000)
npm install && npm run dev
```

---

## 🔐 Environment Variables

Configure these variables in `.env` (see `.env.example` for safe placeholder defaults — **never commit `.env`**):

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | **Yes (Prod)** | Cryptographic JWT signing key (minimum 32+ chars; generate with `openssl rand -hex 32`) |
| `DATABASE_URL` | **Yes** | Async PostgreSQL connection string (`postgresql+asyncpg://user:pass@host:5432/rayhan_workbench`) |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | **Yes (Docker)** | Containerized PostgreSQL credentials (`pgvector/pgvector:pg15`) |
| `CORS_ORIGINS` | **Yes** | Allowed frontend origins JSON list (e.g. `["http://localhost:3000"]`) |
| `GEMINI_API_KEY` | Optional | Google Gemini API key for AI Gateway & `text-embedding-004` RAG embeddings |
| `ANTHROPIC_API_KEY` | Optional | Anthropic Claude API key for automatic AI Gateway fallback routing |
| `ENVIRONMENT` / `DEBUG` | Optional | Runtime environment (`production` / `development`) and debug toggle (`False` in prod) |
| `RATE_LIMIT_PER_MINUTE` | Optional | Sliding-window API throttling thresholds (`60/min` global, `5/min` auth, `30/min` public) |

---

## ✨ Key Features

- 🤖 **9 Specialized AI Agents**: End-to-end lifecycle states (`Planned` → `Configured` → `Available`) with explicit scope gating (`READ_ONLY`, `SUGGEST`, `IMPLEMENT`, `DEPLOY`)
- 🛠️ **18 Sandboxed MCP Tools**: GitHub, Filesystem, Web, Database, and Shell tools enforcing path-traversal guards, approval queues for writes, and credential-scrubbed `tool_audits` logs
- 📚 **RAG Knowledge System (`pgvector`)**: SHA-256 deduplication, 10MB / `.env`-blocked ingestion, semantic vector retrieval, 4-factor reranking, and strict multi-tenant access filtering
- 🔀 **AI Gateway (Gemini + Claude)**: Complexity-based model routing, automatic provider fallback, real-time USD cost ledger (`llm_usage`), and API-key redaction in errors
- ✍️ **Content Studio**: Editorial pipeline (`Idea` → `Outline` → `Draft` → `Approved` → `Published`) with RAG topic research, `[REVIEW REQUIRED]` draft watermarks, and superuser publish controls
- 🌐 **Public Portfolio & Safe Demos**: Cohesive obsidian/cyan showcase (`#portfolio`) strictly isolated to `is_public = True` records, interactive read-only sandboxes, and a 3/hr rate-limited contact endpoint
- 🚀 **DevOps CI/CD Workflows**: GitHub Actions YAML generator, Dockerfile & Compose static analyzer, deployment readiness checklists, and superuser rollback tracking
- ✅ **Automated Quality & Security**: Core 196+ automated test suite (211 total including Phase 14 E2E, latency benchmarks, and 29-check security auditor)

---

## 📄 License

Distributed under the **MIT License**. Copyright © 2026 Rayhan (**Curizx AI**).

---

<div align="center">

**Rayhan · Curizx AI** — *Architecting Intelligence. Engineering the Future.*

</div>
