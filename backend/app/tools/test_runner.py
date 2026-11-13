import asyncio
import re
import shlex
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import (
    PROJECT_ROOT,
    SandboxSecurityError,
    resolve_safe_path,
)
from backend.app.tools.base_tool import BaseTool, ToolResult

# Allowed command binaries / base command strings
ALLOWED_COMMANDS = {
    "pytest",
    "python3 -m pytest",
    "python -m pytest",
}

# Forbidden command tokens or operators
FORBIDDEN_SHELL_CHARS = {";", "&&", "||", "|", "`", "$", ">", "<", "\n", "&"}
FORBIDDEN_COMMANDS = {
    "rm",
    "mv",
    "cp",
    "curl",
    "wget",
    "git",
    "sudo",
    "chmod",
    "chown",
    "bash",
    "sh",
    "kill",
    "pkill",
    "node",
    "npm",
    "pnpm",
}


class TestRunnerTool(BaseTool):
    name = "test_runner"
    description = (
        "Executes automated pytest suites in a sandboxed subprocess without shell=True. "
        "Enforces command restrictions, timeouts (default 30s, max 120s), and captures exit codes."
    )
    required_permission = PermissionLevel.IMPLEMENT
    safe_by_default = False

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        command_str = params.get("command", "pytest").strip()
        target_path_str = params.get("path")
        timeout_seconds = min(int(params.get("timeout", 30)), 120)

        # 1. Check for forbidden shell metacharacters
        for char in FORBIDDEN_SHELL_CHARS:
            if char in command_str:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Command injection prevention: Metacharacter '{char}' is forbidden.",
                    evidence=["Command blocked due to illegal shell characters"],
                    simulated=False,
                )

        # Parse command into tokens
        tokens = shlex.split(command_str)
        if not tokens:
            return ToolResult(
                success=False,
                output="",
                error="Empty command provided.",
                evidence=[],
                simulated=False,
            )

        # 2. Block forbidden commands
        binary = tokens[0].lower()
        if binary in FORBIDDEN_COMMANDS:
            return ToolResult(
                success=False,
                output="",
                error=f"Command '{binary}' is forbidden in test execution sandbox.",
                evidence=[f"Blocked unauthorized command: {binary}"],
                simulated=False,
            )

        # Normalize and construct safe command args
        # Standardize to `python3 -m pytest`
        cmd_args: List[str]
        if binary in ("pytest", "py.test"):
            cmd_args = ["python3", "-m", "pytest"] + tokens[1:]
        elif binary == "python3" and len(tokens) >= 3 and tokens[1] == "-m" and tokens[2] == "pytest":
            cmd_args = tokens
        elif binary == "python" and len(tokens) >= 3 and tokens[1] == "-m" and tokens[2] == "pytest":
            cmd_args = ["python3"] + tokens[1:]
        else:
            return ToolResult(
                success=False,
                output="",
                error=f"Unauthorized test command: '{command_str}'. Allowed commands: pytest, python -m pytest.",
                evidence=["Command whitelist check failed"],
                simulated=False,
            )

        # If scoped to a specific file or folder
        if target_path_str:
            try:
                safe_target = resolve_safe_path(target_path_str, PROJECT_ROOT)
                cmd_args.append(str(safe_target.relative_to(PROJECT_ROOT)))
            except SandboxSecurityError as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=str(e),
                    evidence=[f"Blocked test path: {target_path_str}"],
                    simulated=False,
                )

        # 3. Execute safely with subprocess (no shell=True)
        start_time = time.time()
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
            )

            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(),
                    timeout=float(timeout_seconds),
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                duration_ms = int((time.time() - start_time) * 1000)
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Test execution timed out after {timeout_seconds} seconds.",
                    evidence=[f"Process killed after {timeout_seconds}s timeout"],
                    simulated=False,
                    metadata={"duration_ms": duration_ms, "exit_code": -1, "timeout": True},
                )

            duration_ms = int((time.time() - start_time) * 1000)
            stdout_text = stdout_data.decode("utf-8", errors="replace")
            stderr_text = stderr_data.decode("utf-8", errors="replace")
            exit_code = process.returncode or 0

            # Parse passed / failed / errors from pytest output
            passed_match = re.search(r"(\d+)\s+passed", stdout_text)
            failed_match = re.search(r"(\d+)\s+failed", stdout_text)
            errors_match = re.search(r"(\d+)\s+error", stdout_text)

            passed_count = int(passed_match.group(1)) if passed_match else 0
            failed_count = int(failed_match.group(1)) if failed_match else 0
            errors_count = int(errors_match.group(1)) if errors_match else 0

            output_summary = {
                "passed": passed_count,
                "failed": failed_count,
                "errors": errors_count,
                "duration_ms": duration_ms,
                "exit_code": exit_code,
                "stdout": stdout_text[-10000:],  # limit output size
                "stderr": stderr_text[-5000:],
            }

            is_success = (exit_code == 0) and (failed_count == 0) and (errors_count == 0)

            return ToolResult(
                success=is_success,
                output=output_summary,
                error=None if is_success else f"Tests finished with exit code {exit_code}",
                evidence=[
                    f"Executed: {' '.join(cmd_args)} in {duration_ms}ms",
                    f"Results: {passed_count} passed, {failed_count} failed, {errors_count} errors (exit code: {exit_code})",
                ],
                simulated=False,
                metadata={
                    "duration_ms": duration_ms,
                    "exit_code": exit_code,
                    "passed": passed_count,
                    "failed": failed_count,
                    "errors": errors_count,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Subprocess execution error: {str(e)}",
                evidence=[f"Failed to spawn test runner: {str(e)}"],
                simulated=False,
            )
