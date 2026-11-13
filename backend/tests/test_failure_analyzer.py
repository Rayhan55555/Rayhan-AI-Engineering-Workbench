import pytest
from backend.app.agents.base_agent import ExecutionContext
from backend.app.tools.failure_analyzer import FailureAnalyzerTool


@pytest.mark.asyncio
async def test_failure_analyzer_assertion_error():
    tool = FailureAnalyzerTool()
    context = ExecutionContext(allowed_tools=["failure_analyzer"], dry_run=False)

    sample_output = """
FAILED backend/tests/test_auth.py::test_login_valid - AssertionError: Expected 200, got 401
    assert 401 == 200
    +  where 401 = response.status_code
"""
    res = await tool.execute({"output": sample_output}, context)
    assert res.success
    analysis = res.output
    assert analysis["total_failures"] >= 1
    assert analysis["failures"][0]["type"] == "AssertionError"
    assert "Discrepancy" in analysis["failures"][0]["likely_cause"] or "assertion" in analysis["failures"][0]["likely_cause"].lower()


@pytest.mark.asyncio
async def test_failure_analyzer_import_error():
    tool = FailureAnalyzerTool()
    context = ExecutionContext(allowed_tools=["failure_analyzer"], dry_run=False)

    sample_output = """
FAILED backend/tests/test_demo.py::test_missing - ModuleNotFoundError: No module named 'non_existent_pkg'
"""
    res = await tool.execute({"output": sample_output}, context)
    assert res.success
    analysis = res.output
    assert analysis["total_failures"] >= 1
    assert analysis["failures"][0]["type"] == "ImportError"


@pytest.mark.asyncio
async def test_failure_analyzer_truncates_stack_trace_safely():
    tool = FailureAnalyzerTool()
    context = ExecutionContext(allowed_tools=["failure_analyzer"], dry_run=False)

    long_output = "FAILED test_x.py::test_x\n" + "\n".join([f"    File 'test.py', line {i}, in test_fn" for i in range(50)])
    res = await tool.execute({"output": long_output}, context)
    assert res.success
    stack_summary = res.output["failures"][0]["stack_summary"]
    # Truncated safely
    assert len(stack_summary) <= 300
    assert len(stack_summary.splitlines()) <= 6
