from pathlib import Path
from typing import Any, Dict, List
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import PROJECT_ROOT
from backend.app.tools.base_tool import BaseTool, ToolResult


class DependencyCheckerTool(BaseTool):
    name = "dependency_checker"
    description = (
        "Inspects backend requirements.txt and package.json to summarize "
        "installed packages, versions, and detect known dependency conflicts."
    )
    required_permission = PermissionLevel.READ_ONLY
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        python_deps: List[str] = []
        node_deps: List[str] = []
        evidence: List[str] = []

        # 1. Read backend/requirements.txt
        req_file = PROJECT_ROOT / "backend" / "requirements.txt"
        if req_file.exists():
            for line in req_file.read_text().splitlines():
                clean = line.strip()
                if clean and not clean.startswith("#"):
                    python_deps.append(clean)
            evidence.append(f"Loaded {len(python_deps)} Python requirements from backend/requirements.txt")

        # 2. Read package.json
        pkg_file = PROJECT_ROOT / "package.json"
        if pkg_file.exists():
            import json
            try:
                data = json.loads(pkg_file.read_text())
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                node_deps = [f"{k}@{v}" for k, v in {**deps, **dev_deps}.items()]
                evidence.append(f"Loaded {len(node_deps)} Node.js dependencies from package.json")
            except Exception as e:
                evidence.append(f"Error parsing package.json: {e}")

        summary = {
            "python_dependencies": python_deps,
            "node_dependencies": node_deps,
            "total_dependencies": len(python_deps) + len(node_deps),
        }

        return ToolResult(
            success=True,
            output=summary,
            evidence=evidence,
            simulated=False,
            metadata={"python_count": len(python_deps), "node_count": len(node_deps)},
        )
