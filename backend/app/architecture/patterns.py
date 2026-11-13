from typing import Dict, List, Any
from pydantic import BaseModel, Field


class ArchitecturePattern(BaseModel):
    name: str
    category: str
    description: str
    benefits: List[str]
    tradeoffs: List[str]
    applied_in: List[str]


KNOWN_PATTERNS: Dict[str, ArchitecturePattern] = {
    "layered_architecture": ArchitecturePattern(
        name="Layered Clean Architecture",
        category="Structural",
        description="Strict separation of presentation (FastAPI routers), domain (agent contracts & lifecycle), data access (SQLAlchemy models), and infrastructure (AI Gateway, MCP tools).",
        benefits=[
            "Isolated testability without database or network",
            "Clear boundaries between business logic and transport protocols",
            "Independent evolution of client and storage mechanisms",
        ],
        tradeoffs=[
            "Indirection between HTTP requests and low-level data models",
            "Boilerplate mapping between Pydantic schemas and ORM entities",
        ],
        applied_in=["backend/app/routers", "backend/app/models", "backend/app/agents", "backend/app/gateway"],
    ),
    "gateway_routing": ArchitecturePattern(
        name="AI Gateway & Provider Abstraction",
        category="Integration",
        description="Unified model provider interface (Gemini primary, Claude fallback) with sliding window rate limiting and cost accounting.",
        benefits=[
            "High availability against external LLM outages",
            "Deterministic fallback without client-side error propagation",
            "Fine-grained token and USD cost tracking down to 6 decimals",
        ],
        tradeoffs=[
            "Provider-specific feature differences must be unified",
            "Slight routing latency overhead (typically <5ms)",
        ],
        applied_in=["backend/app/gateway"],
    ),
    "mcp_protocol": ArchitecturePattern(
        name="Model Context Protocol (MCP 1.0)",
        category="Tooling & Integration",
        description="JSON-RPC standardized tool catalog with 4-tier permission enforcement and human-in-the-loop approval gating.",
        benefits=[
            "Sandboxed file system and restricted execution boundaries",
            "Mandatory approval flow for destructive or write operations",
            "Immutable audit logs with automatic credential redaction",
        ],
        tradeoffs=[
            "Approval pauses asynchronous agent workflows for up to 10 minutes",
            "Schema enforcement requires explicit parameter validation",
        ],
        applied_in=["backend/app/mcp", "backend/app/tools/mcp"],
    ),
    "immutable_audit": ArchitecturePattern(
        name="Append-Only Immutable Audit Trail",
        category="Security & Compliance",
        description="All tool calls, agent executions, and user authorizations are stored in append-only tables with no deletion or mutation permitted.",
        benefits=[
            "Tamper-proof compliance history for AI agent behaviors",
            "Traceability for security forensics and debugging",
        ],
        tradeoffs=[
            "Continuous storage growth requiring archiving strategies in later phases",
        ],
        applied_in=["backend/app/models/tool_audit.py", "backend/app/mcp/audit_logger.py"],
    ),
}
