import json
import re
from typing import Any, Dict, List
from backend.app.agents.base_agent import (
    AgentResult,
    AgentTask,
    Artifact,
    BaseAgent,
    CapabilityDescription,
    Evidence,
    ExecutionContext,
    TaskScope,
    ValidationResult,
)
from backend.app.tools.code_analyzer import CodeAnalyzerTool
from backend.app.tools.dependency_checker import DependencyCheckerTool
from backend.app.tools.diff_generator import DiffGeneratorTool
from backend.app.tools.file_reader import FileReaderTool
from backend.app.tools.test_runner import TestRunnerTool


class CodingAgent(BaseAgent):
    """
    Phase 04 Full Implementation of the Coding & Architecture Auditor Agent.
    Executes real tools (FileReader, CodeAnalyzer, DiffGenerator, TestRunner)
    without fabricated outputs.
    """
    slug = "arch-sentinel"
    name = "Coding & Architecture Auditor Agent"
    purpose = (
        "Real codebase inspection, AST parsing, unified diff generation, "
        "and sandboxed test execution with approval gating."
    )
    phase = 4
    version = "1.0.0"
    allowed_tools = [
        "file_reader",
        "code_analyzer",
        "diff_generator",
        "test_runner",
        "dependency_checker",
    ]
    required_permissions = ["READ_ONLY", "SUGGEST", "IMPLEMENT"]
    limitations = [
        "Cannot access sensitive files (.env, .git, /etc, /proc)",
        "Direct disk write is locked (diff generation only for SUGGEST)",
        "Test execution (IMPLEMENT scope) requires explicit user approval",
        "Test execution command is restricted to pytest and scoped paths",
    ]

    def __init__(self):
        self.file_reader = FileReaderTool()
        self.code_analyzer = CodeAnalyzerTool()
        self.diff_generator = DiffGeneratorTool()
        self.test_runner = TestRunnerTool()
        self.dependency_checker = DependencyCheckerTool()

    async def validate_input(self, task: AgentTask) -> ValidationResult:
        instruction = task.instruction.strip()
        if len(instruction) < 3:
            return ValidationResult(
                valid=False,
                error="Instruction is too short (minimum 3 characters required).",
            )
        if len(instruction) > 2000:
            return ValidationResult(
                valid=False,
                error="Instruction exceeds maximum length of 2,000 characters.",
            )

        # Scoped validation
        if task.scope == TaskScope.deploy:
            return ValidationResult(
                valid=False,
                error="Scope 'deploy' is locked until Phase 11.",
            )

        return ValidationResult(valid=True)

    async def execute(self, task: AgentTask, context: ExecutionContext) -> AgentResult:
        instruction = task.instruction.strip()
        scope = task.scope

        # Target file extraction from instruction or context
        target_path = task.context.get("path") or task.context.get("file_path")
        if not target_path:
            # Try to extract path from instruction (e.g. 'inspect backend/app/main.py')
            path_matches = re.findall(r"[\w\./\-]+\.(?:py|ts|tsx|js|json|md|txt|sql)", instruction)
            if path_matches:
                target_path = path_matches[0]

        evidence: List[str] = []
        artifacts: List[Dict[str, Any]] = []

        # ---------------------------------------------------------
        # 1. READ_ONLY Scope: File reading, AST analysis, dependencies
        # ---------------------------------------------------------
        if scope == TaskScope.read_only:
            # Check if user wants dependency listing
            if "dependenc" in instruction.lower() or "packages" in instruction.lower():
                res = await self.dependency_checker.execute({}, context)
                evidence.extend(res.evidence)
                structured_evidence = [
                    Evidence(source="dependencies", snippet=e, confidence=1.0)
                    for e in evidence
                ]
                return AgentResult(
                    success=res.success,
                    output=json.dumps(res.output, indent=2) if isinstance(res.output, dict) else str(res.output),
                    artifacts=[],
                    evidence=structured_evidence,
                    limitations=self.limitations,
                    simulated=False,
                )

            if not target_path:
                target_path = "backend/app/main.py"  # Default inspection target if unspecified

            # 1. Read file
            read_res = await self.file_reader.execute({"path": target_path}, context)
            evidence.extend(read_res.evidence)
            if not read_res.success:
                return AgentResult(
                    success=False,
                    output=f"Failed to inspect '{target_path}': {read_res.error}",
                    artifacts=artifacts,
                    evidence=evidence,
                    limitations=self.limitations,
                    simulated=False,
                )

            # 2. Analyze code AST
            analyze_res = await self.code_analyzer.execute({"path": target_path}, context)
            evidence.extend(analyze_res.evidence)

            analysis = analyze_res.output if isinstance(analyze_res.output, dict) else {}
            metrics = analysis.get("metrics", {})
            issues = analysis.get("issues", [])

            summary_output = {
                "file": target_path,
                "lines": read_res.metadata.get("line_count", 0),
                "size_bytes": read_res.metadata.get("size_bytes", 0),
                "language": analysis.get("language", "python"),
                "functions": analysis.get("functions", []),
                "classes": analysis.get("classes", []),
                "imports_count": len(analysis.get("imports", [])),
                "issues": issues,
                "metrics": metrics,
            }

            # Convert string evidence to Evidence objects
            structured_evidence = [
                Evidence(source=target_path, snippet=e, confidence=1.0)
                for e in evidence
            ]

            return AgentResult(
                success=True,
                output=json.dumps(summary_output, indent=2),
                artifacts=[],
                evidence=structured_evidence,
                limitations=self.limitations,
                simulated=False,
            )

        # ---------------------------------------------------------
        # 2. SUGGEST Scope: Diff generation and proposed improvements
        # ---------------------------------------------------------
        elif scope == TaskScope.suggest:
            if not target_path:
                target_path = "backend/app/main.py"

            # Read target file to suggest improvement on
            read_res = await self.file_reader.execute({"path": target_path}, context)
            evidence.extend(read_res.evidence)
            if not read_res.success:
                return AgentResult(
                    success=False,
                    output=f"Cannot generate suggestion: {read_res.error}",
                    artifacts=[],
                    evidence=[Evidence(source=target_path, snippet=read_res.error or "Error", confidence=1.0)],
                    limitations=self.limitations,
                    simulated=False,
                )

            original_code = str(read_res.output)
            # Perform AST analysis to find real improvements
            analyze_res = await self.code_analyzer.execute({"path": target_path}, context)
            evidence.extend(analyze_res.evidence)
            analysis = analyze_res.output if isinstance(analyze_res.output, dict) else {}
            issues = analysis.get("issues", [])

            # Generate improved code version
            # E.g. Add module header or docstring if missing
            modified_lines = original_code.splitlines()
            if not original_code.startswith('"""') and not original_code.startswith("#"):
                header = [
                    '"""',
                    f"Architecture Sentinel Audited Module: {target_path}",
                    f"Identified issues: {len(issues)} code quality / type suggestions.",
                    '"""',
                ]
                modified_lines = header + modified_lines

            # If unused imports were found, generate diff with comment
            for issue in issues:
                if issue.get("type") == "missing_type_hint":
                    line_idx = issue.get("line", 1) - 1
                    if 0 <= line_idx < len(modified_lines):
                        if not modified_lines[line_idx].endswith("  # Type hint suggested"):
                            modified_lines[line_idx] = modified_lines[line_idx] + "  # Type hint suggested"

            modified_code = "\n".join(modified_lines) + "\n"

            # Generate unified diff
            diff_res = await self.diff_generator.execute({
                "path": target_path,
                "original": original_code,
                "modified": modified_code,
            }, context)
            evidence.extend(diff_res.evidence)

            # Optional AI Gateway Enhancement Layer (Runs after deterministic tools)
            llm_explanation = None
            try:
                from backend.app.config import settings
                if settings.GEMINI_API_KEY:
                    from backend.app.gateway.router import GatewayTask, ModelRouter
                    from backend.app.gateway.base_provider import Message, MessageRole
                    from backend.app.prompts.renderer import PromptRenderer

                    renderer = PromptRenderer()
                    rendered_prompt = renderer.render(
                        "coding_agent.j2",
                        {
                            "agent_name": self.name,
                            "agent_purpose": self.purpose,
                            "instruction": instruction,
                            "target_file": target_path,
                            "ast_analysis": analysis,
                        },
                    )
                    router = ModelRouter()
                    gw_task = GatewayTask(complexity="simple", requires_reasoning=True)
                    llm_res = await router.execute_with_fallback(
                        messages=[Message(role=MessageRole.USER, content=rendered_prompt)],
                        task=gw_task,
                        max_tokens=1000,
                    )
                    llm_explanation = llm_res.content
            except Exception:
                # Deterministic tool output is primary; LLM failure never blocks
                pass

            output_summary = {
                "target_file": target_path,
                "suggestions_count": len(issues),
                "diff": diff_res.output,
                "summary": f"Generated unified diff patch for {target_path} addressing {len(issues)} detected issues.",
                "llm_insights": llm_explanation,
                "note": "Diff generation only. Disk write requires explicit approval under IMPLEMENT scope.",
            }

            diff_artifact = Artifact(
                name=f"{target_path}.patch",
                artifact_type="unified_diff",
                content=str(diff_res.output),
                metadata={"file": target_path},
            )

            structured_evidence = [
                Evidence(source=target_path, snippet=e, confidence=1.0)
                for e in evidence
            ]

            return AgentResult(
                success=True,
                output=json.dumps(output_summary, indent=2),
                artifacts=[diff_artifact],
                evidence=structured_evidence,
                limitations=self.limitations,
                simulated=False,
            )

        # ---------------------------------------------------------
        # 3. IMPLEMENT Scope: Sandboxed Test Execution
        # ---------------------------------------------------------
        elif scope == TaskScope.implement:
            test_command = "pytest"
            if "backend/tests" in instruction or "test_" in instruction:
                # Scoped pytest execution
                matched_test = re.findall(r"backend/tests/[\w\./\-]+\.py", instruction)
                if matched_test:
                    test_command = f"pytest {matched_test[0]}"

            run_res = await self.test_runner.execute({
                "command": test_command,
                "path": target_path if (target_path and "test" in target_path) else None,
            }, context)
            evidence.extend(run_res.evidence)

            output_payload = {
                "command": test_command,
                "result": run_res.output,
                "status": "PASSED" if run_res.success else "FAILED",
                "simulated": False,
            }

            structured_evidence = [
                Evidence(source="test_runner", snippet=e, confidence=1.0)
                for e in evidence
            ]

            return AgentResult(
                success=run_res.success,
                output=json.dumps(output_payload, indent=2) if isinstance(run_res.output, dict) else str(run_res.output),
                artifacts=[],
                evidence=structured_evidence,
                limitations=self.limitations,
                simulated=False,
            )

        return AgentResult(
            success=False,
            output=f"Unsupported task scope: '{scope}'",
            artifacts=[],
            evidence=["Scope error"],
            limitations=self.limitations,
            simulated=False,
        )

    async def describe_capabilities(self) -> CapabilityDescription:
        return CapabilityDescription(
            slug=self.slug,
            name=self.name,
            purpose=self.purpose,
            phase=self.phase,
            version=self.version,
            allowed_tools=self.allowed_tools,
            required_permissions=self.required_permissions,
            limitations=self.limitations,
        )
