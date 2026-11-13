import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from backend.app.architecture.templates import ADR_TEMPLATE


class ADRSummary(BaseModel):
    number: int
    title: str
    status: str
    date: str
    filename: str
    path: str


class ADRContent(BaseModel):
    number: int
    title: str
    status: str
    content: str
    date: str
    suggest_only: bool = True
    written_to_disk: bool = False
    file_path: Optional[str] = None


PREDEFINED_DECISIONS: Dict[str, Dict[str, str]] = {
    "fastapi": {
        "title": "Adopt FastAPI as Async Web Framework",
        "status": "Accepted",
        "context": "The workbench requires a high-performance, asynchronous REST backend to handle concurrent agent task executions, real-time Server-Sent Events, and strict OpenAPI schema generation.",
        "decision": "Use FastAPI (Python 3.10+) running with Uvicorn and Starlette ASGI middleware. Pydantic v2 will be used for strict data modeling and request validation.",
        "consequences_positive": "- Native async/await support ensures non-blocking I/O during LLM and tool calls\n- Automatic OpenAPI documentation syncs directly with endpoint contracts\n- High throughput and fast development cycle",
        "consequences_negative": "- Python runtime performance for CPU-bound tasks requires subprocess isolation\n- Async SQLAlchemy requires strict context session management",
        "risks": "Third-party synchronous libraries can block the main event loop if not run via executors.",
        "alternatives_considered": "Django Ninja, Flask, Go Gin, Node.js Express. FastAPI was chosen for native Python AI tooling synergy and typed OpenAPI contracts.",
    },
    "database": {
        "title": "Use PostgreSQL with AsyncPG and SQLAlchemy 2.0",
        "status": "Accepted",
        "context": "The system requires relational persistence for users, projects, agent states, token usage, and append-only immutable audit logs.",
        "decision": "Adopt PostgreSQL 15+ with the asyncpg driver and SQLAlchemy 2.0 async ORM, enforcing foreign key cascades and UUID primary keys.",
        "consequences_positive": "- ACID guarantees for financial cost tracking and token audits\n- Native JSONB support enables dynamic parameter storage without schema thrash\n- Async session management allows high-concurrency connection pooling",
        "consequences_negative": "- Relational schema migrations require disciplined Alembic versioning\n- More operational overhead than serverless document stores",
        "risks": "Connection pool exhaustion under burst agent task dispatches.",
        "alternatives_considered": "MongoDB, SQLite, DynamoDB. PostgreSQL was chosen for relational integrity, JSONB hybrid capabilities, and strict audit compliance.",
    },
    "auth": {
        "title": "Stateless JWT Authentication with Refresh Token Rotation",
        "status": "Accepted",
        "context": "Secure authentication is required for human engineers interacting with the AI Workbench across both the public portfolio and internal agent execution environments.",
        "decision": "Implement stateless HMAC-SHA256 JWT access tokens (30-minute expiry) with cryptographically random refresh tokens stored in PostgreSQL (7-day rotation).",
        "consequences_positive": "- Stateless verification across distributed microservices\n- Fast token checks in middleware without database queries on every request\n- Revocation capabilities via refresh token blacklisting",
        "consequences_negative": "- Access tokens cannot be revoked instantly until their 30-minute window expires",
        "risks": "Leaked access tokens permit 30 minutes of unauthorized access unless blacklisted in cache.",
        "alternatives_considered": "Session cookies, OAuth2 server only. JWT was chosen for clean SPA decoupling and API-first client design.",
    },
    "gateway": {
        "title": "Multi-Provider AI Gateway with Gemini Primary and Claude Fallback",
        "status": "Accepted",
        "context": "Direct coupling to a single commercial LLM creates single-point-of-failure vulnerability during API downtime or quota depletion.",
        "decision": "Implement an AI Gateway provider abstraction layer with Gemini 1.5 as primary provider and Claude 3.5 as automatic fallback, routed based on task complexity.",
        "consequences_positive": "- Zero downtime failover during primary provider outages\n- Cost optimization by routing simple queries to Flash/Haiku and complex reasoning to Pro/Sonnet\n- Strict sliding window rate limiting prevents quota exhaustion",
        "consequences_negative": "- Prompt templates must accommodate subtle nuances between model behaviors\n- Maintenance of two provider SDK integrations",
        "risks": "Inconsistent token counting strategies between providers.",
        "alternatives_considered": "Single Gemini integration, direct LangChain router. A custom lightweight gateway was chosen for zero bloat, strict security, and 6-decimal cost auditing.",
    },
    "mcp": {
        "title": "Adopt Model Context Protocol (MCP 1.0) with Human Approval Gating",
        "status": "Accepted",
        "context": "AI agents need tool execution capabilities (file reads/writes, web search, SQL inspection, shell tests) without compromising system integrity.",
        "decision": "Standardize all tool definitions on the Model Context Protocol 1.0 specification with mandatory human-in-the-loop approval on write and destructive operations.",
        "consequences_positive": "- Uniform JSON-RPC tool schemas consumable by any compliant agent\n- Write operations require explicit approval within a 10-minute window\n- Soft-delete and automated backup preserve workspace safety",
        "consequences_negative": "- Autonomous agent workflows halt until human engineer approves actions",
        "risks": "Operator fatigue approving repetitive low-risk write operations.",
        "alternatives_considered": "Unrestricted tool execution, function calling without approval. MCP with approval gating was chosen for zero-trust security.",
    },
}


class ADRGenerator:
    """
    Manages generation, scanning, and formatting of Architecture Decision Records.
    """
    WORKSPACE_ROOT = Path("/app/applet").resolve()
    DOCS_DIR = WORKSPACE_ROOT / "docs" / "adr"

    @classmethod
    def list_existing_adrs(cls) -> List[ADRSummary]:
        """Scans docs/adr/ directory for existing ADR files."""
        if not cls.DOCS_DIR.exists():
            return []

        adrs: List[ADRSummary] = []
        for f in sorted(cls.DOCS_DIR.glob("*.md")):
            # Expected format: 001-fastapi-framework.md or ADR-001.md
            match = re.search(r"(\d+)", f.name)
            num = int(match.group(1)) if match else 1

            # Read title and status from file
            title = f.stem.replace("-", " ").capitalize()
            status = "Accepted"
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            try:
                with open(f, "r", encoding="utf-8") as handle:
                    content = handle.read()
                    title_match = re.search(r"^#\s+(?:ADR-\d+:\s*)?(.*)", content, re.MULTILINE)
                    if title_match:
                        title = title_match.group(1).strip()
                    status_match = re.search(r"##\s+Status\s*\n+([A-Za-z]+)", content)
                    if status_match:
                        status = status_match.group(1).strip()
                    date_match = re.search(r"##\s+Date\s*\n+([0-9\-]+)", content)
                    if date_match:
                        date_str = date_match.group(1).strip()
            except Exception:
                pass

            adrs.append(ADRSummary(
                number=num,
                title=title,
                status=status,
                date=date_str,
                filename=f.name,
                path=str(f.relative_to(cls.WORKSPACE_ROOT)),
            ))

        return adrs

    @classmethod
    def get_next_adr_number(cls) -> int:
        existing = cls.list_existing_adrs()
        if not existing:
            return 1
        return max(a.number for a in existing) + 1

    @classmethod
    def generate(
        cls,
        title: str,
        decision: str,
        context: str,
        status: str = "Accepted",
        consequences_positive: str = "- Improves architectural clarity and modularity",
        consequences_negative: str = "- Adds initial development overhead",
        risks: str = "Must be reviewed by engineering lead prior to production deployment.",
        alternatives_considered: str = "Evaluated current baseline and alternative open-source patterns.",
        number: Optional[int] = None,
    ) -> ADRContent:
        num = number or cls.get_next_adr_number()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Check for predefined match keywords
        lower_title = title.lower()
        for key, pre in PREDEFINED_DECISIONS.items():
            if key in lower_title:
                title = pre["title"]
                status = pre["status"]
                context = pre["context"]
                decision = pre["decision"]
                consequences_positive = pre["consequences_positive"]
                consequences_negative = pre["consequences_negative"]
                risks = pre["risks"]
                alternatives_considered = pre["alternatives_considered"]
                break

        formatted = ADR_TEMPLATE.format(
            number=num,
            title=title,
            status=status,
            context=context,
            decision=decision,
            consequences_positive=consequences_positive,
            consequences_negative=consequences_negative,
            risks=risks,
            alternatives_considered=alternatives_considered,
            date=today,
        )

        return ADRContent(
            number=num,
            title=title,
            status=status,
            content=formatted,
            date=today,
            suggest_only=True,
            written_to_disk=False,
        )

    @classmethod
    def write_to_disk(cls, adr: ADRContent) -> str:
        """
        Writes the ADR file to /docs/adr/. Requires prior human approval (IMPLEMENT scope).
        """
        cls.DOCS_DIR.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", adr.title.lower()).strip("-")
        filename = f"{adr.number:03d}-{slug}.md"
        target_path = cls.DOCS_DIR / filename

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(adr.content)

        return str(target_path.relative_to(cls.WORKSPACE_ROOT))
