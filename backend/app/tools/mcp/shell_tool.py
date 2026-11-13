import asyncio
import re
from typing import Dict, Any
from pathlib import Path


class ShellTool:
    """
    MCP Shell execution tool.
    Strictly forbids arbitrary shell injection.
    - shell_run_linter (READ_ONLY): Runs python compile check or linter
    - shell_run_tests (IMPLEMENT): Runs scoped pytest on authorized file
    """

    ALLOWED_TEST_PREFIXES = ("backend/tests/", "tests/")

    @classmethod
    async def run_linter(cls, target_path: str = "backend/app") -> Dict[str, Any]:
        clean_path = target_path.strip().lstrip("/")
        if ".." in clean_path or ";" in clean_path or "|" in clean_path or "&" in clean_path:
            return {"success": False, "error": "Invalid target path rejected."}

        # Run python3 -m py_compile verification on target
        cmd = ["python3", "-m", "compileall", "-q", clean_path]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)

            errors = stderr.decode("utf-8").strip()
            success = proc.returncode == 0 and not errors

            return {
                "success": success,
                "tool": "shell_run_linter",
                "target_path": clean_path,
                "exit_code": proc.returncode,
                "output": "Lint syntax verification passed: 0 compile errors." if success else errors,
            }
        except Exception as e:
            return {"success": False, "error": f"Linter run failed: {str(e)}"}

    @classmethod
    async def run_tests(cls, test_path: str) -> Dict[str, Any]:
        clean_path = test_path.strip().lstrip("/")

        if not any(clean_path.startswith(prefix) for prefix in cls.ALLOWED_TEST_PREFIXES):
            return {
                "success": False,
                "error": f"Test runner only allows tests under: {cls.ALLOWED_TEST_PREFIXES}",
            }

        if re.search(r"[;&|`$><]", clean_path) or ".." in clean_path:
            return {"success": False, "error": "Shell metacharacters or path traversal rejected."}

        cmd = ["python3", "-m", "pytest", clean_path, "-v"]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)

            out_text = stdout.decode("utf-8", errors="replace")
            err_text = stderr.decode("utf-8", errors="replace")

            return {
                "success": proc.returncode == 0,
                "tool": "shell_run_tests",
                "test_path": clean_path,
                "exit_code": proc.returncode,
                "output": out_text[-2000:] if len(out_text) > 2000 else out_text,
                "errors": err_text[-500:] if err_text else None,
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Test run timed out after 30 seconds."}
        except Exception as e:
            return {"success": False, "error": f"Test run failed: {str(e)}"}
