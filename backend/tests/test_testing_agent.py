import json
import uuid
import pytest
from backend.app.agents.base_agent import AgentTask, ExecutionContext, TaskScope
from backend.app.agents.implementations.testing_agent import TestingAgent

DUMMY_USER_ID = uuid.uuid4()


@pytest.mark.asyncio
async def test_testing_agent_coverage_analysis_read_only():
    agent = TestingAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="analyze coverage in backend/tests/test_security_rules.py",
        scope=TaskScope.read_only,
        context={"path": "backend/tests/test_security_rules.py"},
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, context)

    assert result.success
    assert not result.simulated
    assert len(result.evidence) > 0
    data = json.loads(result.output)
    assert data["task_type"] == "coverage_analysis"
    assert "overall_coverage" in data["summary"]


@pytest.mark.asyncio
async def test_testing_agent_gap_detection_task():
    agent = TestingAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="find test gaps in backend/app/routers/auth.py",
        scope=TaskScope.read_only,
        context={"path": "backend/app/routers/auth.py"},
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, context)

    assert result.success
    assert not result.simulated
    data = json.loads(result.output)
    assert data["task_type"] == "gap_analysis"
    assert len(data["gaps"]) >= 0


@pytest.mark.asyncio
async def test_testing_agent_test_generation_suggest_only():
    agent = TestingAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="generate tests for backend/app/routers/auth.py",
        scope=TaskScope.suggest,
        context={"path": "backend/app/routers/auth.py"},
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, context)

    assert result.success
    assert not result.simulated
    data = json.loads(result.output)
    assert data["task_type"] == "test_generation"
    assert len(data["templates"]) > 0

    # Ensure generated code has review required badge and is an in-memory artifact
    assert len(result.artifacts) == 1
    assert "REVIEW_REQUIRED" in data["templates"][0]["review_status"]
    assert "[GENERATED - REVIEW REQUIRED]" in data["templates"][0]["code"]


@pytest.mark.asyncio
async def test_testing_agent_failure_analysis():
    agent = TestingAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="analyze failures",
        scope=TaskScope.read_only,
        context={"failure_output": "FAILED test_auth.py::test_login - AssertionError: 401 != 200"},
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, context)

    assert result.success
    assert not result.simulated
    data = json.loads(result.output)
    assert data["task_type"] == "failure_analysis"
    assert data["analysis"]["total_failures"] >= 1


@pytest.mark.asyncio
async def test_testing_agent_run_tests_implement_scope():
    agent = TestingAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="run test in backend/tests/test_security_rules.py",
        scope=TaskScope.implement,
        context={"path": "backend/tests/test_security_rules.py"},
        requested_by=DUMMY_USER_ID,
    )
    context = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, context)

    assert result.success
    assert not result.simulated
    data = json.loads(result.output)
    assert data["task_type"] == "test_run"
    assert data["status"] == "PASSED"
