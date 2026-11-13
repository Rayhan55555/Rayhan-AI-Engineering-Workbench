import pytest
from backend.app.agents.base_agent import ExecutionContext
from backend.app.tools.coverage_analyzer import CoverageAnalyzerTool


@pytest.mark.asyncio
async def test_coverage_analyzer_runs_and_parses_json():
    """Verify coverage analyzer runs pytest under coverage and parses real stats."""
    tool = CoverageAnalyzerTool()
    context = ExecutionContext(allowed_tools=["coverage_analyzer"], dry_run=False)

    # Scoped run on quick security rules test to avoid lengthy run
    res = await tool.execute({"test_path": "backend/tests/test_security_rules.py"}, context)

    assert res.success
    assert not res.simulated
    assert "overall_coverage" in res.output
    assert isinstance(res.output["overall_coverage"], float)
    assert len(res.output["files"]) > 0
    assert "summary" in res.output
    assert res.output["summary"]["total_files"] > 0


@pytest.mark.asyncio
async def test_coverage_analyzer_identifies_uncovered_lines():
    tool = CoverageAnalyzerTool()
    context = ExecutionContext(allowed_tools=["coverage_analyzer"], dry_run=False)

    res = await tool.execute({"test_path": "backend/tests/test_secret_detector.py"}, context)
    assert res.success

    files = res.output["files"]
    for f in files:
        assert "file" in f
        assert "coverage" in f
        assert "uncovered_lines" in f
        assert isinstance(f["uncovered_lines"], list)


@pytest.mark.asyncio
async def test_coverage_analyzer_blocks_path_traversal():
    tool = CoverageAnalyzerTool()
    context = ExecutionContext(allowed_tools=["coverage_analyzer"], dry_run=False)

    res = await tool.execute({"test_path": "../../etc/passwd"}, context)
    assert not res.success
    assert "Unsafe test path" in res.error
