import uuid
import pytest
from backend.app.agents.implementations.architecture_agent import ArchitectureAgent
from backend.app.agents.base_agent import AgentTask, ExecutionContext, TaskScope
from backend.app.tools.architecture_analyzer import ArchitectureAnalyzer
from backend.app.tools.adr_generator import ADRGenerator

DUMMY_USER_ID = uuid.uuid4()


@pytest.mark.asyncio
async def test_architecture_agent_full_analysis():
    """Verify Architecture Agent runs real AST and schema analysis without simulation."""
    agent = ArchitectureAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="analyze architecture and evaluate layer boundaries",
        scope=TaskScope.read_only,
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)

    result = await agent.execute(task, context)
    assert result.success is True
    assert result.simulated is False
    assert len(result.evidence) >= 1
    assert "health_score" in result.output
    assert "grade" in result.output


@pytest.mark.asyncio
async def test_architecture_agent_generate_system_diagram():
    """Verify Architecture Agent generates authentic Mermaid system diagram."""
    agent = ArchitectureAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="generate system diagram in Mermaid format",
        scope=TaskScope.read_only,
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)

    result = await agent.execute(task, context)
    assert result.success is True
    assert result.simulated is False
    assert any(a.artifact_type == "mermaid_diagram" for a in result.artifacts)
    assert "graph TD" in result.output


@pytest.mark.asyncio
async def test_architecture_agent_generate_er_diagram():
    """Verify Architecture Agent generates valid Mermaid ER diagram."""
    agent = ArchitectureAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="generate ER diagram of database models",
        scope=TaskScope.read_only,
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)

    result = await agent.execute(task, context)
    assert result.success is True
    assert result.simulated is False
    assert "erDiagram" in result.output


@pytest.mark.asyncio
async def test_architecture_agent_adr_generation_suggest_scope():
    """Verify ADR generation in SUGGEST scope returns template without disk write."""
    agent = ArchitectureAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="create ADR for FastAPI framework choice",
        scope=TaskScope.suggest,
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)

    result = await agent.execute(task, context)
    assert result.success is True
    assert result.simulated is False
    assert "# ADR-" in result.output
    assert "## Decision" in result.output
    assert "## Consequences" in result.output


@pytest.mark.asyncio
async def test_architecture_agent_write_adr_blocks_without_implement_scope():
    """Verify attempting to write an ADR to disk without IMPLEMENT scope is rejected."""
    agent = ArchitectureAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="write ADR to docs/adr/ for database choice",
        scope=TaskScope.suggest,  # Not implement scope
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)

    result = await agent.execute(task, context)
    assert result.success is False
    assert "requires IMPLEMENT scope" in result.output


def test_circular_dependency_detection_runs():
    """Verify dependency analyzer detects import graph and checks for cycles."""
    has_cycles, cycles, metrics = ArchitectureAnalyzer.analyze_dependencies()
    assert isinstance(has_cycles, bool)
    assert isinstance(cycles, list)
    assert "total_modules_analyzed" in metrics
    assert metrics["total_modules_analyzed"] >= 10
