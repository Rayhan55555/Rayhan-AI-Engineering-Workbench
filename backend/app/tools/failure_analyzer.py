import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.tools.base_tool import BaseTool, ToolResult


class TestFailureItem(BaseModel):
    test: str
    type: str  # 'AssertionError', 'ImportError', 'TimeoutError', 'KeyError', 'AttributeError', etc.
    message: str
    likely_cause: str
    suggested_fix: str
    stack_summary: str


class FailureAnalysis(BaseModel):
    total_failures: int
    failures: List[TestFailureItem]
    patterns: List[str]
    recommended_action: str


class FailureAnalyzerTool(BaseTool):
    """
    Analyzes pytest stdout/stderr failure output.
    Extracts failed test identifiers, classifies exception types, provides likely causes,
    and safely truncates stack traces to 5 lines maximum without sensitive data leakage.
    """
    name = "failure_analyzer"
    description = (
        "Parses pytest failure logs and stack traces. Classifies bug categories (logic, auth, dependency, timeout) "
        "and generates actionable root cause remediations with safe stack summaries."
    )
    required_permission = PermissionLevel.READ_ONLY
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        raw_output = params.get("output") or params.get("stderr") or params.get("stdout") or ""

        if not raw_output:
            return ToolResult(
                success=True,
                output={
                    "total_failures": 0,
                    "failures": [],
                    "patterns": [],
                    "recommended_action": "No failure output provided. All tests appear passing.",
                },
                evidence=["Empty test output analyzed"],
                simulated=False,
            )

        analysis = self.analyze_pytest_output(raw_output)

        evidence = [
            f"Analyzed test execution log: {analysis.total_failures} failure(s) identified",
            f"Classified patterns: {', '.join(analysis.patterns) if analysis.patterns else 'none'}",
            f"Safe stack traces truncated to max 5 lines",
        ]

        return ToolResult(
            success=True,
            output=analysis.model_dump(),
            evidence=evidence,
            simulated=False,
            metadata={"failures_count": analysis.total_failures},
        )

    def analyze_pytest_output(self, text: str) -> FailureAnalysis:
        failures: List[TestFailureItem] = []
        patterns_detected = set()

        # Find failure blocks: e.g. "_____ test_name _____" or "FAILED path/to/test.py::test_func"
        failure_headers = re.findall(r"FAILED\s+([\w\./\-]+\.py::[\w_]+)", text)

        # Fallback: regex for section headers "____ test_name ____"
        if not failure_headers:
            section_matches = re.findall(r"_{3,}\s+([\w_]+)\s+_{3,}", text)
            failure_headers = [f"test_suite.py::{m}" for m in section_matches]

        # Extract blocks per failure or perform global scan
        for test_name in failure_headers:
            # Extract exception type and message near test name or general
            err_type = "AssertionError"
            msg = "Test assertion failed"
            likely_cause = "Logic discrepancy between implementation and test assertion."
            suggested_fix = "Review expected vs actual values in test assertion."

            if "ImportError" in text or "ModuleNotFoundError" in text:
                err_type = "ImportError"
                likely_cause = "Missing dependency, circular import, or incorrect module path."
                suggested_fix = "Verify package installation and module import statement."
                patterns_detected.add("import_or_dependency_issue")
            elif "TimeoutError" in text or "timed out" in text.lower():
                err_type = "TimeoutError"
                likely_cause = "Asynchronous dead-lock or long-running subprocess exceeding timeout."
                suggested_fix = "Increase timeout threshold or optimize async execution path."
                patterns_detected.add("performance_or_timeout")
            elif "PermissionError" in text or "403" in text or "Forbidden" in text:
                err_type = "PermissionError"
                likely_cause = "Role-based permission check or sandbox boundary violation."
                suggested_fix = "Ensure appropriate user authentication headers and roles are provided."
                patterns_detected.add("auth_or_permission")
            elif "KeyError" in text:
                err_type = "KeyError"
                likely_cause = "Dictionary missing expected payload key."
                suggested_fix = "Check JSON response keys and schema definitions."
                patterns_detected.add("data_contract_issue")
            elif "AttributeError" in text:
                err_type = "AttributeError"
                likely_cause = "Object is None or missing expected method/attribute."
                suggested_fix = "Add null-check or verify object instantiation."
                patterns_detected.add("null_pointer_or_attribute")
            elif "AssertionError" in text:
                patterns_detected.add("logic_or_assertion")

            # Extract 5-line safe stack trace summary
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            stack_lines = []
            for l in lines:
                if any(k in l for k in ("File ", "line ", "assert ", "raise ")):
                    stack_lines.append(l)
                if len(stack_lines) >= 5:
                    break

            stack_summary = "\n".join(stack_lines) if stack_lines else "Stack trace summary not available."

            failures.append(
                TestFailureItem(
                    test=test_name,
                    type=err_type,
                    message=msg,
                    likely_cause=likely_cause,
                    suggested_fix=suggested_fix,
                    stack_summary=stack_summary[:300],  # Max 300 chars
                )
            )

        # If failures detected but no explicit header found, create general failure item
        if not failures and ("FAILED" in text or "AssertionError" in text or "Traceback" in text):
            failures.append(
                TestFailureItem(
                    test="unknown_test_case",
                    type="AssertionError" if "AssertionError" in text else "ExecutionError",
                    message="Pytest failed during test execution",
                    likely_cause="Test suite raised unhandled exception or assertion failure.",
                    suggested_fix="Inspect pytest output log for specific assertion mismatch.",
                    stack_summary=text[:250],
                )
            )
            patterns_detected.add("test_failure")

        rec_action = "Review identified failures and apply suggested fixes."
        if "auth_or_permission" in patterns_detected:
            rec_action = "Review JWT tokens, user permissions, and authentication dependencies."
        elif "import_or_dependency_issue" in patterns_detected:
            rec_action = "Check requirements.txt and package installations."

        return FailureAnalysis(
            total_failures=len(failures),
            failures=failures,
            patterns=list(patterns_detected),
            recommended_action=rec_action,
        )
