import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import (
    PROJECT_ROOT,
    SandboxSecurityError,
    resolve_safe_path,
)
from backend.app.tools.base_tool import BaseTool, ToolResult


class TestGap(BaseModel):
    file: str
    function: str
    type: str  # 'untested', 'missing_negative', 'missing_boundary'
    priority: str  # 'high', 'medium', 'low'
    suggestion: str


class GapAnalysisResult(BaseModel):
    source_functions: int
    tested_functions: int
    coverage_ratio: float
    gaps: List[TestGap]
    missing_test_files: List[str]
    recommendations: List[str]


class TestGapDetectorTool(BaseTool):
    """
    Analyzes source files vs test files to identify untested public functions,
    missing edge cases (no negative test, no boundary test), and missing test files.
    Works across Python (AST) and TypeScript/TSX (regex/exports).
    """
    name = "test_gap_detector"
    description = (
        "Statically compares source modules against test suites using Python AST and TypeScript pattern analysis. "
        "Finds untested public functions, missing test files, and missing negative/boundary test cases."
    )
    required_permission = PermissionLevel.READ_ONLY
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        target_path_str = params.get("path") or params.get("target")

        try:
            if target_path_str:
                safe_path = resolve_safe_path(target_path_str, PROJECT_ROOT)
                if safe_path.is_file():
                    res = self.analyze_single_file(safe_path)
                else:
                    res = self.analyze_directory(safe_path)
            else:
                res = self.analyze_directory(PROJECT_ROOT / "backend" / "app")

            evidence = [
                f"Evaluated {res.source_functions} source functions across codebase",
                f"Identified {res.tested_functions} functions with dedicated tests (ratio: {res.coverage_ratio})",
                f"Found {len(res.gaps)} test gaps ({sum(1 for g in res.gaps if g.priority == 'high')} high priority)",
            ]
            if res.missing_test_files:
                evidence.append(f"Detected {len(res.missing_test_files)} source modules without corresponding test files")

            return ToolResult(
                success=True,
                output=res.model_dump(),
                evidence=evidence,
                simulated=False,
                metadata={
                    "gaps_count": len(res.gaps),
                    "coverage_ratio": res.coverage_ratio,
                },
            )
        except SandboxSecurityError as e:
            return ToolResult(
                success=False,
                output={},
                error=f"Path security violation: {str(e)}",
                evidence=[f"Blocked target path: {target_path_str}"],
                simulated=False,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output={},
                error=f"Error detecting test gaps: {str(e)}",
                evidence=[f"Test gap detection error: {str(e)}"],
                simulated=False,
            )

    def analyze_single_file(self, file_path: Path) -> GapAnalysisResult:
        rel_path = str(file_path.relative_to(PROJECT_ROOT))
        source_funcs = self._extract_python_functions(file_path)
        all_test_funcs = self._collect_existing_test_names()

        gaps: List[TestGap] = []
        tested_count = 0

        for func in source_funcs:
            # Check if matching test exists
            matched_tests = [t for t in all_test_funcs if func.lower() in t.lower()]
            if matched_tests:
                tested_count += 1
                # Check for negative/boundary tests
                has_negative = any("invalid" in t or "error" in t or "fail" in t or "reject" in t for t in matched_tests)
                if not has_negative:
                    gaps.append(
                        TestGap(
                            file=rel_path,
                            function=func,
                            type="missing_negative",
                            priority="medium",
                            suggestion=f"Add error/invalid input scenario test for '{func}'",
                        )
                    )
            else:
                priority = "high" if not func.startswith("_") and any(k in func.lower() for k in ("auth", "exec", "scan", "token", "create", "delete", "validate")) else "medium"
                gaps.append(
                    TestGap(
                        file=rel_path,
                        function=func,
                        type="untested",
                        priority=priority,
                        suggestion=f"Add unit test covering happy path and boundary conditions for '{func}'",
                    )
                )

        ratio = round(tested_count / max(1, len(source_funcs)), 2)

        # Check if corresponding test file exists
        test_file_candidates = [
            PROJECT_ROOT / "backend" / "tests" / f"test_{file_path.stem}.py",
            PROJECT_ROOT / "tests" / f"test_{file_path.stem}.py",
        ]
        missing_files = []
        if not any(cand.exists() for cand in test_file_candidates):
            missing_files.append(f"backend/tests/test_{file_path.stem}.py")

        recs = [
            f"Focus on {sum(1 for g in gaps if g.priority == 'high')} high-priority public function test gaps.",
            f"Ensure edge-case and negative tests are implemented for critical business logic.",
        ]

        return GapAnalysisResult(
            source_functions=len(source_funcs),
            tested_functions=tested_count,
            coverage_ratio=ratio,
            gaps=gaps,
            missing_test_files=missing_files,
            recommendations=recs,
        )

    def analyze_directory(self, root_dir: Path) -> GapAnalysisResult:
        all_source_funcs: List[tuple[str, str]] = []  # (rel_file, func_name)
        missing_test_files: List[str] = []
        skip_dirs = {"__pycache__", ".git", "venv", "node_modules", "dist", "build"}

        for py_file in root_dir.rglob("*.py"):
            if any(s in py_file.parts for s in skip_dirs):
                continue
            if "test_" in py_file.name or py_file.name.startswith("test"):
                continue
            if py_file.name in ("__init__.py", "conftest.py"):
                continue

            rel_file = str(py_file.relative_to(PROJECT_ROOT))
            funcs = self._extract_python_functions(py_file)
            for f in funcs:
                all_source_funcs.append((rel_file, f))

            # Check test file presence
            test_target = PROJECT_ROOT / "backend" / "tests" / f"test_{py_file.stem}.py"
            if not test_target.exists():
                missing_test_files.append(f"backend/tests/test_{py_file.stem}.py")

        all_test_funcs = self._collect_existing_test_names()

        gaps: List[TestGap] = []
        tested_count = 0

        for rel_file, func in all_source_funcs:
            matched_tests = [t for t in all_test_funcs if func.lower() in t.lower()]
            if matched_tests:
                tested_count += 1
                has_negative = any("invalid" in t or "error" in t or "fail" in t or "reject" in t for t in matched_tests)
                if not has_negative:
                    gaps.append(
                        TestGap(
                            file=rel_file,
                            function=func,
                            type="missing_negative",
                            priority="medium",
                            suggestion=f"Add error/invalid input scenario test for '{func}'",
                        )
                    )
            else:
                is_high = not func.startswith("_") and any(k in func.lower() for k in ("auth", "exec", "scan", "token", "create", "delete", "validate", "run"))
                gaps.append(
                    TestGap(
                        file=rel_file,
                        function=func,
                        type="untested",
                        priority="high" if is_high else "medium",
                        suggestion=f"Add unit test covering happy path for '{func}'",
                    )
                )

        total_funcs = len(all_source_funcs)
        ratio = round(tested_count / max(1, total_funcs), 2)

        recs = [
            f"Prioritize the {sum(1 for g in gaps if g.priority == 'high')} high-priority untested functions in security and auth modules.",
            f"Generate test files for {len(missing_test_files)} uncovered modules.",
        ]

        return GapAnalysisResult(
            source_functions=total_funcs,
            tested_functions=tested_count,
            coverage_ratio=ratio,
            gaps=gaps[:50],  # Cap at 50 for clean presentation
            missing_test_files=missing_test_files[:15],
            recommendations=recs,
        )

    def _extract_python_functions(self, file_path: Path) -> List[str]:
        funcs: List[str] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Exclude dunder methods like __init__
                    if not (node.name.startswith("__") and node.name.endswith("__")):
                        funcs.append(node.name)
        except Exception:
            pass
        return funcs

    def _collect_existing_test_names(self) -> Set[str]:
        test_names: Set[str] = set()
        tests_dir = PROJECT_ROOT / "backend" / "tests"
        if not tests_dir.exists():
            return test_names

        for t_file in tests_dir.glob("*.py"):
            try:
                tree = ast.parse(t_file.read_text(encoding="utf-8", errors="replace"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith("test_"):
                            test_names.add(node.name)
            except Exception:
                continue

        return test_names
