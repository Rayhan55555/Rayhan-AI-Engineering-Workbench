import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import (
    PROJECT_ROOT,
    SandboxSecurityError,
    resolve_safe_path,
)
from backend.app.testing.patterns import DEFAULT_ERROR_MAP, TEST_ASSERTION_PATTERNS
from backend.app.testing.templates import (
    PYTHON_ASYNC_UNIT_TEST_TEMPLATE,
    PYTHON_FASTAPI_INTEGRATION_TEST_TEMPLATE,
    PYTHON_UNIT_TEST_TEMPLATE,
)
from backend.app.tools.base_tool import BaseTool, ToolResult


class GeneratedTestCase(BaseModel):
    function_name: str
    target_file: str
    template_type: str  # 'unit', 'async_unit', 'integration'
    code: str
    review_status: str = "REVIEW_REQUIRED"
    note: str = "Deterministic template - human engineer verification mandatory before committing."


class TestGeneratorTool(BaseTool):
    """
    Template-based Test Generator Tool (NO LLM — deterministic templates only).
    Parses Python function signature, arguments, docstring, and return type via AST.
    Synthesizes Happy path, Negative/Error path, and Boundary tests with [REVIEW REQUIRED] badge.
    Never auto-writes to disk.
    """
    name = "test_generator"
    description = (
        "Deterministically synthesizes pytest test case templates using AST signature inspection. "
        "Strictly outputs suggested templates marked [GENERATED - REVIEW REQUIRED] without disk modification."
    )
    required_permission = PermissionLevel.SUGGEST
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        target_path_str = params.get("target_file") or params.get("path")
        function_names = params.get("function_names") or params.get("functions") or []

        if not target_path_str:
            return ToolResult(
                success=False,
                output={},
                error="Target file path is required to generate test templates.",
                evidence=["Missing target_file parameter"],
                simulated=False,
            )

        try:
            safe_path = resolve_safe_path(target_path_str, PROJECT_ROOT)
            if not safe_path.exists() or not safe_path.is_file():
                return ToolResult(
                    success=False,
                    output={},
                    error=f"Target file does not exist: {target_path_str}",
                    evidence=[f"File not found: {target_path_str}"],
                    simulated=False,
                )

            rel_path = str(safe_path.relative_to(PROJECT_ROOT))
            content = safe_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content)

            generated_tests: List[GeneratedTestCase] = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # If specific functions requested, filter
                    if function_names and node.name not in function_names:
                        continue
                    # Skip private dunder
                    if node.name.startswith("__") and node.name.endswith("__"):
                        continue

                    test_case = self._generate_test_for_node(node, rel_path)
                    generated_tests.append(test_case)

            evidence = [
                f"Generated {len(generated_tests)} deterministic test templates for {rel_path}",
                "Marked with '# [GENERATED - REVIEW REQUIRED]'",
                "Templates held in-memory (no disk write performed)",
            ]

            return ToolResult(
                success=True,
                output={
                    "target_file": rel_path,
                    "total_generated": len(generated_tests),
                    "templates": [t.model_dump() for t in generated_tests],
                },
                evidence=evidence,
                simulated=False,
                metadata={"generated_count": len(generated_tests)},
            )

        except SandboxSecurityError as e:
            return ToolResult(
                success=False,
                output={},
                error=f"Sandbox security error: {str(e)}",
                evidence=[f"Blocked target path: {target_path_str}"],
                simulated=False,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output={},
                error=f"Test generator error: {str(e)}",
                evidence=[f"Error parsing source AST: {str(e)}"],
                simulated=False,
            )

    def _generate_test_for_node(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        rel_path: str,
    ) -> GeneratedTestCase:
        func_name = node.name
        is_async = isinstance(node, ast.AsyncFunctionDef)

        # Module import calculation
        import_mod = rel_path.replace("/", ".").replace(".py", "")
        imports_code = f"from {import_mod} import {func_name}"

        # Extract argument names
        args = [a.arg for a in node.args.args if a.arg != "self" and a.arg != "cls"]

        arrange_lines = []
        act_args = []
        invalid_arrange_lines = []
        boundary_arrange_lines = []

        for arg in args:
            arrange_lines.append(f"    {arg} = 'test_value'")
            invalid_arrange_lines.append(f"    {arg} = None")
            boundary_arrange_lines.append(f"    {arg} = ''")
            act_args.append(f"{arg}={arg}")

        act_call_str = f"{func_name}({', '.join(act_args)})"
        invalid_call_str = f"{func_name}({', '.join([f'{a}={a}' for a in args])})"

        arrange_code = "\n".join(arrange_lines) if arrange_lines else "    pass"
        invalid_arrange_code = "\n".join(invalid_arrange_lines) if invalid_arrange_lines else "    pass"
        boundary_arrange_code = "\n".join(boundary_arrange_lines) if boundary_arrange_lines else "    pass"

        # Determine expected error based on naming
        expected_error = "ValueError"
        for k, v in DEFAULT_ERROR_MAP.items():
            if k in func_name.lower():
                expected_error = v
                break

        template = PYTHON_ASYNC_UNIT_TEST_TEMPLATE if is_async else PYTHON_UNIT_TEST_TEMPLATE

        rendered_code = template.format(
            imports_code=imports_code,
            function_name=func_name,
            fixture_params="",
            arrange_code=arrange_code,
            act_call=act_call_str,
            assert_code="    assert result is not None",
            invalid_arrange_code=invalid_arrange_code,
            expected_error=expected_error,
            invalid_act_call=invalid_call_str,
            boundary_arrange_code=boundary_arrange_code,
            boundary_act_call=act_call_str,
        )

        return GeneratedTestCase(
            function_name=func_name,
            target_file=rel_path,
            template_type="async_unit" if is_async else "unit",
            code=rendered_code,
            review_status="REVIEW_REQUIRED",
        )
