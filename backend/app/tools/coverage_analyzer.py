import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import (
    PROJECT_ROOT,
    SandboxSecurityError,
    resolve_safe_path,
)
from backend.app.tools.base_tool import BaseTool, ToolResult


class FileCoverage(BaseModel):
    file: str
    coverage: float
    uncovered_lines: List[int]
    total_lines: int
    covered_lines: int


class CoverageSummary(BaseModel):
    total_files: int
    files_above_80: int
    files_below_50: int
    critical_gaps: List[str]


class CoverageResult(BaseModel):
    overall_coverage: float
    files: List[FileCoverage]
    summary: CoverageSummary


class CoverageAnalyzerTool(BaseTool):
    """
    Subprocess-based coverage analysis tool executing real coverage.py.
    Runs:
      coverage run -m pytest {test_path}
      coverage json -o {output_path}
    Parses real results without fabrication, enforces 120s timeout, and cleans up artifacts.
    """
    name = "coverage_analyzer"
    description = (
        "Runs real coverage.py via subprocess to measure code execution coverage. "
        "Extracts overall percentage, per-file metrics, and uncovered lines without fabrication."
    )
    required_permission = PermissionLevel.READ_ONLY
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        test_path = params.get("test_path") or params.get("path") or "backend/tests"
        timeout_seconds = min(int(params.get("timeout", 120)), 120)

        # Validate test_path within project bounds
        try:
            safe_target = resolve_safe_path(test_path, PROJECT_ROOT)
        except SandboxSecurityError as e:
            return ToolResult(
                success=False,
                output={},
                error=f"Unsafe test path: {str(e)}",
                evidence=[f"Blocked target path: {test_path}"],
                simulated=False,
            )

        start_time = time.perf_counter()
        cov_output_file = PROJECT_ROOT / f".coverage_run_{int(time.time())}.json"
        cov_data_file = PROJECT_ROOT / ".coverage"

        cmd_run = ["python3", "-m", "coverage", "run", "--source=backend/app", "-m", "pytest", str(safe_target.relative_to(PROJECT_ROOT))]
        cmd_json = ["python3", "-m", "coverage", "json", "-o", str(cov_output_file)]

        try:
            # 1. Run coverage run
            proc_run = await asyncio.create_subprocess_exec(
                *cmd_run,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                stdout_run, stderr_run = await asyncio.wait_for(
                    proc_run.communicate(),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                proc_run.kill()
                return ToolResult(
                    success=False,
                    output={},
                    error=f"Coverage analysis timed out after {timeout_seconds} seconds.",
                    evidence=[f"Timeout exceeded during 'coverage run' on {test_path}"],
                    simulated=False,
                )

            # 2. Run coverage json
            proc_json = await asyncio.create_subprocess_exec(
                *cmd_json,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout_json, stderr_json = await proc_json.communicate()

            if not cov_output_file.exists():
                return ToolResult(
                    success=False,
                    output={},
                    error=f"Coverage JSON generation failed: {stderr_json.decode('utf-8', errors='replace')}",
                    evidence=[f"Coverage run stderr: {stderr_run.decode('utf-8', errors='replace')[:200]}"],
                    simulated=False,
                )

            # 3. Parse JSON output
            json_text = cov_output_file.read_text(encoding="utf-8")
            raw_data = json.loads(json_text)
            parsed_result = self._parse_coverage_json(raw_data)
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            return ToolResult(
                success=True,
                output=parsed_result.model_dump(),
                evidence=[
                    f"Executed real coverage.py over {parsed_result.summary.total_files} files",
                    f"Overall project coverage: {parsed_result.overall_coverage}%",
                    f"Files with >80% coverage: {parsed_result.summary.files_above_80}",
                    f"Files with <50% coverage: {parsed_result.summary.files_below_50}",
                ],
                simulated=False,
                metadata={
                    "duration_ms": duration_ms,
                    "target": test_path,
                    "overall_coverage": parsed_result.overall_coverage,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output={},
                error=f"Coverage analysis error: {str(e)}",
                evidence=[f"Error during coverage execution: {str(e)}"],
                simulated=False,
            )
        finally:
            # 4. Clean up temporary coverage files
            if cov_output_file.exists():
                try:
                    cov_output_file.unlink()
                except Exception:
                    pass
            if cov_data_file.exists():
                try:
                    cov_data_file.unlink()
                except Exception:
                    pass

    def _parse_coverage_json(self, raw: Dict[str, Any]) -> CoverageResult:
        totals = raw.get("totals", {})
        overall_pct = round(float(totals.get("percent_covered", 0.0)), 1)

        raw_files = raw.get("files", {})
        file_list: List[FileCoverage] = []

        files_above_80 = 0
        files_below_50 = 0
        critical_gaps: List[str] = []

        for f_path, f_meta in raw_files.items():
            # Make path relative to project root
            try:
                rel_path = str(Path(f_path).relative_to(PROJECT_ROOT))
            except ValueError:
                rel_path = f_path

            # Skip test files themselves from source coverage
            if "backend/tests" in rel_path or "tests/" in rel_path:
                continue

            summary = f_meta.get("summary", {})
            pct = round(float(summary.get("percent_covered", 0.0)), 1)
            num_statements = summary.get("num_statements", 0)
            covered_lines = summary.get("covered_lines", 0)
            missing_lines = f_meta.get("missing_lines", [])

            if pct >= 80.0:
                files_above_80 += 1
            elif pct < 50.0:
                files_below_50 += 1
                if num_statements > 15:
                    critical_gaps.append(rel_path)

            file_list.append(
                FileCoverage(
                    file=rel_path,
                    coverage=pct,
                    uncovered_lines=missing_lines,
                    total_lines=num_statements,
                    covered_lines=covered_lines,
                )
            )

        # Sort files by coverage ascending (lowest coverage first for clear visibility)
        file_list.sort(key=lambda x: x.coverage)

        return CoverageResult(
            overall_coverage=overall_pct,
            files=file_list,
            summary=CoverageSummary(
                total_files=len(file_list),
                files_above_80=files_above_80,
                files_below_50=files_below_50,
                critical_gaps=critical_gaps,
            ),
        )
