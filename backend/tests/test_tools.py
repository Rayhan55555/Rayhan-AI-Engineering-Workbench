import asyncio
import pytest
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import (
    MAX_FILE_SIZE_BYTES,
    PROJECT_ROOT,
    SandboxSecurityError,
    resolve_safe_path,
    validate_file_extension,
)
from backend.app.tools.code_analyzer import CodeAnalyzerTool
from backend.app.tools.dependency_checker import DependencyCheckerTool
from backend.app.tools.diff_generator import DiffGeneratorTool
from backend.app.tools.file_reader import FileReaderTool
from backend.app.tools.test_runner import TestRunnerTool


@pytest.fixture
def execution_context():
    return ExecutionContext(allowed_tools=["*"], dry_run=False)


# -------------------------------------------------------------
# 1. Sandbox Restrictions Tests
# -------------------------------------------------------------
def test_sandbox_path_traversal_blocked():
    with pytest.raises(SandboxSecurityError, match="Path traversal detected"):
        resolve_safe_path("../../etc/passwd", PROJECT_ROOT)

    with pytest.raises(SandboxSecurityError, match="Path traversal detected"):
        resolve_safe_path("../../../../../bin/sh", PROJECT_ROOT)


def test_sandbox_sensitive_files_blocked():
    with pytest.raises(SandboxSecurityError, match="sensitive file"):
        resolve_safe_path(".env", PROJECT_ROOT)

    with pytest.raises(SandboxSecurityError, match="sensitive file"):
        resolve_safe_path(".env.local", PROJECT_ROOT)


def test_sandbox_allows_env_example():
    path = resolve_safe_path(".env.example", PROJECT_ROOT)
    assert path.name == ".env.example"
    validate_file_extension(path)


def test_sandbox_validates_extensions():
    valid = PROJECT_ROOT / "main.py"
    validate_file_extension(valid)

    invalid = PROJECT_ROOT / "exploit.exe"
    with pytest.raises(SandboxSecurityError, match="not in the allowed inspection list"):
        validate_file_extension(invalid)


# -------------------------------------------------------------
# 2. FileReaderTool Tests
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_file_reader_reads_valid_file(execution_context):
    tool = FileReaderTool()
    res = await tool.execute({"path": "backend/app/main.py"}, execution_context)
    assert res.success is True
    assert "FastAPI" in res.output
    assert res.metadata["line_count"] > 10
    assert res.simulated is False


@pytest.mark.asyncio
async def test_file_reader_blocks_path_traversal(execution_context):
    tool = FileReaderTool()
    res = await tool.execute({"path": "../../etc/shadow"}, execution_context)
    assert res.success is False
    assert "traversal" in res.error.lower()


@pytest.mark.asyncio
async def test_file_reader_blocks_env_file(execution_context):
    tool = FileReaderTool()
    res = await tool.execute({"path": ".env"}, execution_context)
    assert res.success is False
    assert "strictly blocked" in res.error.lower()


# -------------------------------------------------------------
# 3. CodeAnalyzerTool Tests
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_code_analyzer_python_ast(execution_context):
    tool = CodeAnalyzerTool()
    code = (
        "import os\n"
        "import sys\n\n"
        "def compute_total(price: float, tax: float) -> float:\n"
        "    '''Compute total price with tax.'''\n"
        "    if price < 0:\n"
        "        return 0.0\n"
        "    return price + tax\n"
    )
    res = await tool.execute({"content": code, "language": "python"}, execution_context)
    assert res.success is True
    data = res.output
    assert data["language"] == "python"
    assert len(data["functions"]) == 1
    assert data["functions"][0]["name"] == "compute_total"
    assert data["functions"][0]["has_docstring"] is True
    assert data["functions"][0]["has_return_annotation"] is True
    assert data["metrics"]["complexity"] >= 2
    # Unused import detection
    issues = [i["type"] for i in data["issues"]]
    assert "unused_import" in issues


@pytest.mark.asyncio
async def test_code_analyzer_typescript_patterns(execution_context):
    tool = CodeAnalyzerTool()
    code = (
        "import React from 'react';\n"
        "export const MyButton = (props: any) => {\n"
        "  return <button>{props.label}</button>;\n"
        "};\n"
    )
    res = await tool.execute({"content": code, "language": "typescript"}, execution_context)
    assert res.success is True
    data = res.output
    assert data["language"] == "typescript"
    # Should detect ': any' usage
    issue_types = [i["type"] for i in data["issues"]]
    assert "explicit_any" in issue_types


# -------------------------------------------------------------
# 4. DiffGeneratorTool Tests
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_diff_generator_creates_unified_diff(execution_context):
    tool = DiffGeneratorTool()
    original = "line 1\nline 2\nline 3\n"
    modified = "line 1\nline 2 modified\nline 3\nline 4 added\n"
    res = await tool.execute({"original": original, "modified": modified}, execution_context)
    assert res.success is True
    diff_text = res.output
    assert "--- a/target_file" in diff_text
    assert "+++ b/target_file" in diff_text
    assert "-line 2" in diff_text
    assert "+line 2 modified" in diff_text
    assert "+line 4 added" in diff_text
    assert res.metadata["lines_added"] >= 2
    assert res.metadata["lines_removed"] >= 1


# -------------------------------------------------------------
# 5. TestRunnerTool Tests
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_test_runner_blocks_shell_characters(execution_context):
    tool = TestRunnerTool()
    res = await tool.execute({"command": "pytest; rm -rf /"}, execution_context)
    assert res.success is False
    assert "injection prevention" in res.error.lower()


@pytest.mark.asyncio
async def test_test_runner_blocks_unauthorized_commands(execution_context):
    tool = TestRunnerTool()
    res = await tool.execute({"command": "curl http://malicious.com"}, execution_context)
    assert res.success is False
    assert "forbidden" in res.error.lower() or "unauthorized" in res.error.lower()


@pytest.mark.asyncio
async def test_test_runner_runs_pytest_on_scoped_test(execution_context):
    tool = TestRunnerTool()
    # Run a quick isolated test
    res = await tool.execute({
        "command": "pytest backend/tests/test_auth.py -k test_login_invalid_password",
    }, execution_context)
    assert res.success is True
    data = res.output
    assert data["passed"] >= 1
    assert data["exit_code"] == 0
    assert res.simulated is False
