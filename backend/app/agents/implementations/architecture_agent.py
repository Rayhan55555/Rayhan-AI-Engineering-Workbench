import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import (
    BaseAgent,
    AgentTask,
    AgentResult,
    ExecutionContext,
    ValidationResult,
    CapabilityDescription,
    Artifact,
    Evidence,
    TaskScope,
)
from backend.app.tools.diagram_generator import DiagramGenerator
from backend.app.tools.adr_generator import ADRGenerator
from backend.app.tools.architecture_analyzer import ArchitectureAnalyzer
from backend.app.gateway import ModelRouter, Message
from backend.app.config import settings


class ArchitectureAgent(BaseAgent):
    """
    Architecture Sentinel — Phase 09 full functional implementation.
    Conducts static AST layer analysis, circular dependency mapping, authentic Mermaid.js
    diagram synthesis, and standardized Architecture Decision Record generation.
    """
    slug = "architecture-agent"
    name = "Architecture Sentinel"
    purpose = "Microservices topology design, layer boundary verification, dependency cycle detection, Mermaid diagram generation, and ADR stewardship."
    phase = 9
    version = "1.0.0"
    allowed_tools = [
        "architecture_analyzer",
        "diagram_generator",
        "adr_generator",
        "file_reader",
    ]
    required_permissions = ["READ_ONLY", "SUGGEST", "IMPLEMENT"]
    limitations = [
        "Mermaid diagrams strictly reflect actual parsed entities (zero fabricated modules)",
        "Writing ADR files to /docs/adr/ (IMPLEMENT scope) requires explicit human authorization",
        "Production cloud deployment topologies locked until Phase 11",
        "Distributed tracing and latency profiling scheduled for Phase 10",
    ]

    async def validate_input(self, task: AgentTask) -> ValidationResult:
        if not task.instruction or len(task.instruction.strip()) < 3:
            return ValidationResult(valid=False, error="Instruction is too short (min 3 characters).")
        if len(task.instruction) > 2000:
            return ValidationResult(valid=False, error="Instruction exceeds maximum length of 2000 characters.")
        return ValidationResult(valid=True)

    async def execute(self, task: AgentTask, context: ExecutionContext) -> AgentResult:
        val = await self.validate_input(task)
        if not val.valid:
            return AgentResult(
                success=False,
                output=f"Input validation rejected: {val.error}",
                limitations=self.limitations,
                simulated=False,
            )

        instruction_lower = task.instruction.lower()
        artifacts: List[Artifact] = []
        evidence: List[Evidence] = []

        # 1. DIAGRAM GENERATION (READ_ONLY / SUGGEST)
        if any(w in instruction_lower for w in ("diagram", "mermaid", "topology", "sequence")):
            diag_type = "system"
            if "system" in instruction_lower or "architecture" in instruction_lower:
                diag_type = "system"
            elif any(w in instruction_lower for w in ("er diagram", "database", "schema", "entity")):
                diag_type = "er"
            elif any(w in instruction_lower for w in ("api", "flow", "sequence")):
                diag_type = "api"
            elif any(w in instruction_lower for w in ("agent", "state", "lifecycle")):
                diag_type = "agent"
            elif any(w in instruction_lower for w in ("component", "frontend", "ui")):
                diag_type = "component"

            diag_res = DiagramGenerator.generate(diag_type)
            evidence.append(Evidence(
                source="diagram_generator",
                snippet=f"Generated {diag_res.title} ({len(diag_res.components_found)} entities parsed)",
                confidence=1.0,
            ))

            artifacts.append(Artifact(
                name=f"{diag_res.diagram_type}.mmd",
                artifact_type="mermaid_diagram",
                content=diag_res.mermaid_code,
                metadata={"title": diag_res.title, "components": diag_res.components_found},
            ))

            output_dict = {
                "task": "generate_diagram",
                "diagram_type": diag_res.diagram_type,
                "title": diag_res.title,
                "mermaid_code": diag_res.mermaid_code,
                "components": diag_res.components_found,
            }

            return AgentResult(
                success=True,
                output=json.dumps(output_dict, indent=2),
                artifacts=artifacts,
                evidence=evidence,
                limitations=self.limitations,
                simulated=False,
            )

        # 2. ADR GENERATION & PERSISTENCE
        if any(w in instruction_lower for w in ("adr", "decision record", "architecture decision")):
            # Check if write requested (IMPLEMENT scope)
            is_write_task = any(w in instruction_lower for w in ("write", "save", "persist", "commit"))
            if is_write_task:
                if task.scope != TaskScope.implement:
                    return AgentResult(
                        success=False,
                        output="Writing ADR files to disk requires IMPLEMENT scope and explicit human approval.",
                        limitations=self.limitations,
                        simulated=False,
                    )

            title = "Architectural Decision"
            context_text = "Standardizing workbench technical choices."
            decision_text = task.instruction

            if "fastapi" in instruction_lower:
                title = "FastAPI Web Framework Choice"
            elif "database" in instruction_lower or "postgres" in instruction_lower:
                title = "PostgreSQL Relational Storage Choice"
            elif "jwt" in instruction_lower or "auth" in instruction_lower:
                title = "Stateless JWT Authentication Approach"
            elif "mcp" in instruction_lower or "tool" in instruction_lower:
                title = "Model Context Protocol Tool Standardization"

            adr = ADRGenerator.generate(
                title=title,
                decision=decision_text,
                context=context_text,
            )

            # Optionally enhance with AI Gateway if configured
            if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your-gemini-api-key-here":
                try:
                    router = ModelRouter()
                    gw_res = await router.route_and_execute(
                        messages=[
                            Message(role="system", content="You are a Principal Software Architect. Enhance this ADR with sharp consequences and risks. Output clean markdown."),
                            Message(role="user", content=adr.content),
                        ],
                        task_type="complex",
                    )
                    if gw_res and gw_res.content:
                        adr.content = gw_res.content
                except Exception:
                    pass

            file_saved_path = None
            if is_write_task and not context.dry_run:
                file_saved_path = ADRGenerator.write_to_disk(adr)
                adr.written_to_disk = True
                adr.file_path = file_saved_path

            evidence.append(Evidence(
                source="adr_generator",
                snippet=f"Generated ADR-{adr.number:03d}: '{adr.title}' (Status: {adr.status})",
                confidence=1.0,
            ))

            artifacts.append(Artifact(
                name=f"ADR-{adr.number:03d}.md",
                artifact_type="markdown_document",
                content=adr.content,
                metadata={"number": adr.number, "title": adr.title, "written": adr.written_to_disk},
            ))

            return AgentResult(
                success=True,
                output=adr.content,
                artifacts=artifacts,
                evidence=evidence,
                limitations=self.limitations,
                simulated=False,
            )

        # 3. FULL ARCHITECTURAL ANALYSIS & AUDIT (Default)
        report = ArchitectureAnalyzer.full_audit()

        evidence.append(Evidence(
            source="architecture_analyzer",
            snippet=f"Evaluated {report.metrics.get('total_routes', 0)} API endpoints, {report.metrics.get('modules_count', 0)} modules across 4 layers.",
            confidence=1.0,
        ))

        # Add system diagram artifact
        if "system_architecture" in report.diagrams:
            artifacts.append(Artifact(
                name="system_architecture.mmd",
                artifact_type="mermaid_diagram",
                content=report.diagrams["system_architecture"],
                metadata={"health_score": report.health_score},
            ))

        return AgentResult(
            success=True,
            output=report.model_dump_json(indent=2),
            artifacts=artifacts,
            evidence=evidence,
            limitations=self.limitations,
            simulated=False,
        )

    async def describe_capabilities(self) -> CapabilityDescription:
        return CapabilityDescription(
            slug=self.slug,
            name=self.name,
            purpose=self.purpose,
            phase=self.phase,
            version=self.version,
            allowed_tools=self.allowed_tools,
            required_permissions=self.required_permissions,
            limitations=self.limitations,
        )
