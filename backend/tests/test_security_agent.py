import json
import uuid
import pytest
from backend.app.agents.base_agent import AgentTask, ExecutionContext, TaskScope
from backend.app.agents.implementations.security_agent import SecurityAgent

DUMMY_USER_ID = uuid.uuid4()


@pytest.mark.asyncio
async def test_security_agent_rejects_implement_scope():
    """Security Agent must strictly reject IMPLEMENT scope with clear guidance."""
    agent = SecurityAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="apply automated security patch to fix SQL injection",
        scope=TaskScope.implement,
        requested_by=DUMMY_USER_ID,
    )
    validation = await agent.validate_input(task)
    assert not validation.valid
    assert "Security fixes must be reviewed and applied manually" in validation.error
    assert "Use SUGGEST scope" in validation.error


@pytest.mark.asyncio
async def test_security_agent_allows_read_only_and_suggest_scopes():
    agent = SecurityAgent()
    task_read = AgentTask(
        agent_slug=agent.slug,
        instruction="scan backend/app/main.py for vulnerabilities",
        scope=TaskScope.read_only,
        requested_by=DUMMY_USER_ID,
    )
    valid_read = await agent.validate_input(task_read)
    assert valid_read.valid

    task_suggest = AgentTask(
        agent_slug=agent.slug,
        instruction="suggest fixes for INJ-001",
        scope=TaskScope.suggest,
        requested_by=DUMMY_USER_ID,
    )
    valid_suggest = await agent.validate_input(task_suggest)
    assert valid_suggest.valid


@pytest.mark.asyncio
async def test_security_agent_scan_file_real_analysis():
    agent = SecurityAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="scan file backend/app/main.py for vulnerabilities",
        scope=TaskScope.read_only,
        context={"path": "backend/app/main.py"},
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, context)

    assert result.success
    assert not result.simulated
    assert len(result.evidence) > 0
    data = json.loads(result.output)
    assert data["scan_type"] == "file_security_scan"
    assert "results" in data


@pytest.mark.asyncio
async def test_security_agent_secret_detection_flow():
    agent = SecurityAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="audit secrets and credentials in backend/app/config.py",
        scope=TaskScope.read_only,
        context={"path": "backend/app/config.py"},
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, context)

    assert result.success
    assert not result.simulated
    data = json.loads(result.output)
    assert data["scan_type"] == "secret_audit"
    # Ensure no raw secret is leaked in output string
    assert "AKIA" not in result.output or "AKIA****" in result.output


@pytest.mark.asyncio
async def test_security_agent_auth_audit_flow():
    agent = SecurityAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="audit auth and permission boundaries",
        scope=TaskScope.read_only,
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, context)

    assert result.success
    assert not result.simulated
    data = json.loads(result.output)
    assert data["scan_type"] == "auth_audit"
    summary = data["summary"]
    assert "total_checks" in summary
    assert summary["total_checks"] > 0


@pytest.mark.asyncio
async def test_security_agent_dependency_audit_flow():
    agent = SecurityAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="check dependencies and cve patterns",
        scope=TaskScope.read_only,
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, context)

    assert result.success
    assert not result.simulated
    data = json.loads(result.output)
    assert data["scan_type"] == "dependency_audit"
    assert "total_dependency_findings" in data["summary"]


@pytest.mark.asyncio
async def test_security_agent_suggest_remediation():
    agent = SecurityAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="suggest fixes for INJ-001",
        scope=TaskScope.suggest,
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, context)

    assert result.success
    assert not result.simulated
    data = json.loads(result.output)
    assert data["scan_type"] == "remediation_guidance"
    recs = data["recommendations"]
    assert len(recs) >= 1
    assert recs[0]["finding_id"] == "INJ-001"
    assert "parameterized" in recs[0]["remediation"].lower() or "prepare" in recs[0]["remediation"].lower()


@pytest.mark.asyncio
async def test_security_agent_full_review():
    agent = SecurityAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="full security review",
        scope=TaskScope.read_only,
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, context)

    assert result.success
    assert not result.simulated
    assert len(result.artifacts) == 1
    assert result.artifacts[0].name == "security_audit_report.json"
    data = json.loads(result.output)
    assert data["scan_type"] == "full_security_review"
    assert "summary" in data
    assert "findings" in data
    assert "auth_audit" in data
    assert "dependency_audit" in data
