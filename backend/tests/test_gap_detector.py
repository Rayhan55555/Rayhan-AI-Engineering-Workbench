import pytest
from backend.app.agents.base_agent import ExecutionContext
from backend.app.tools.test_gap_detector import TestGapDetectorTool


@pytest.mark.asyncio
async def test_gap_detector_extracts_ast_functions():
    tool = TestGapDetectorTool()
    context = ExecutionContext(allowed_tools=["test_gap_detector"], dry_run=False)

    res = await tool.execute({"path": "backend/app/routers/auth.py"}, context)
    assert res.success
    assert not res.simulated
    assert res.output["source_functions"] > 0
    assert "coverage_ratio" in res.output


@pytest.mark.asyncio
async def test_gap_detector_flags_untested_functions():
    tool = TestGapDetectorTool()
    context = ExecutionContext(allowed_tools=["test_gap_detector"], dry_run=False)

    res = await tool.execute({"path": "backend/app/tools/failure_analyzer.py"}, context)
    assert res.success
    gaps = res.output["gaps"]
    assert isinstance(gaps, list)
    for g in gaps:
        assert "function" in g
        assert "type" in g
        assert g["priority"] in ("high", "medium", "low")
        assert len(g["suggestion"]) > 5


@pytest.mark.asyncio
async def test_gap_detector_missing_test_files():
    tool = TestGapDetectorTool()
    context = ExecutionContext(allowed_tools=["test_gap_detector"], dry_run=False)

    res = await tool.execute({"path": "backend/app/tools"}, context)
    assert res.success
    assert "missing_test_files" in res.output
    assert isinstance(res.output["missing_test_files"], list)
