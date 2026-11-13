from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
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
from backend.app.tools.coverage_analyzer import CoverageAnalyzerTool
from backend.app.tools.failure_analyzer import FailureAnalyzerTool
from backend.app.tools.test_gap_detector import TestGapDetectorTool
from backend.app.tools.test_generator import TestGeneratorTool
from backend.app.tools.test_runner import TestRunnerTool


class TestingAgent(BaseAgent):
    """
    Phase 06 Full Implementation of the Testing & QA Automation Agent.
    Executes real coverage.py subprocess, AST-based test gap detection,
    deterministic test case synthesis (SUGGEST only), failure root-cause analysis,
    and approval-gated test suite execution.
    """
    __test__ = False  # Tells pytest not to collect TestingAgent class as a test suite
    slug = "testing-agent"
    name = "Test Automation & QA Agent"
    purpose = (
        "Real test coverage analysis, missing test gap detection, deterministic test generation, "
        "failure root-cause classification, and approval-gated test suite execution."
    )
    phase = 6
    version = "1.0.0"
    allowed_tools = [
        "coverage_analyzer",
        "test_gap_detector",
        "test_generator",
        "failure_analyzer",
        "test_runner",
    ]
    required_permissions = ["READ_ONLY", "SUGGEST", "IMPLEMENT"]
    limitations = [
        "Template-based test generation — no LLM inference until Phase 07",
        "Generated test templates require human review before use",
        "Test execution (IMPLEMENT scope) requires explicit user approval",
        "No mutation or property-based testing in Phase 06",
        "Coverage analysis scoped to backend/app modules",
    ]

    def __init__(self):
        self.coverage_analyzer = CoverageAnalyzerTool()
        self.test_gap_detector = TestGapDetectorTool()
        self.test_generator = TestGeneratorTool()
        self.failure_analyzer = FailureAnalyzerTool()
        self.test_runner = TestRunnerTool()

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

        if task.scope == TaskScope.deploy:
            return ValidationResult(
                valid=False,
                error="Scope 'deploy' is locked until Phase 11.",
            )

        return ValidationResult(valid=True)

    async def execute(self, task: AgentTask, context: ExecutionContext) -> AgentResult:
        instruction = task.instruction.strip().lower()
        scope = task.scope

        # Extract target path if specified
        target_path: Optional[str] = task.context.get("path") or task.context.get("file_path") or task.context.get("target_file")
        if not target_path:
            path_matches = re.findall(r"[\w\./\-]+\.(?:py|ts|tsx|json|md)", task.instruction)
            if path_matches:
                target_path = path_matches[0]

        evidence_items: List[Evidence] = []
        artifacts: List[Artifact] = []

        # -------------------------------------------------------------
        # 1. IMPLEMENT Scope: Run Full or Scoped Test Suite (Gated by Approval)
        # -------------------------------------------------------------
        if scope == TaskScope.implement or "run full test suite" in instruction or "run test" in instruction:
            test_path = target_path if (target_path and "test" in target_path) else "backend/tests"
            runner_res = await self.test_runner.execute({
                "command": f"pytest {test_path}",
                "path": test_path,
            }, context)

            for ev in runner_res.evidence:
                evidence_items.append(Evidence(source="test_runner", snippet=ev, confidence=1.0))

            failure_analysis = None
            if not runner_res.success:
                raw_out = runner_res.output if isinstance(runner_res.output, str) else json.dumps(runner_res.output)
                fail_res = await self.failure_analyzer.execute({"output": raw_out}, context)
                failure_analysis = fail_res.output
                for ev in fail_res.evidence:
                    evidence_items.append(Evidence(source="failure_analyzer", snippet=ev, confidence=1.0))

            report = {
                "task_type": "test_run",
                "target": test_path,
                "status": "PASSED" if runner_res.success else "FAILED",
                "runner_output": runner_res.output,
                "failure_analysis": failure_analysis,
                "executed_at": datetime.now(timezone.utc).isoformat(),
            }

            return AgentResult(
                success=runner_res.success,
                output=json.dumps(report, indent=2),
                artifacts=artifacts,
                evidence=evidence_items,
                limitations=self.limitations,
                simulated=False,
            )

        # -------------------------------------------------------------
        # 2. SUGGEST Scope: Generate Test Templates or Test Plan
        # -------------------------------------------------------------
        if scope == TaskScope.suggest or "generate test" in instruction:
            target_file = target_path or "backend/app/routers/auth.py"
            gen_res = await self.test_generator.execute({
                "target_file": target_file,
            }, context)

            for ev in gen_res.evidence:
                evidence_items.append(Evidence(source="test_generator", snippet=ev, confidence=1.0))

            templates_output = gen_res.output.get("templates", []) if isinstance(gen_res.output, dict) else []

            # Create in-memory artifact (never written to disk automatically)
            if templates_output:
                combined_code = "\n\n".join([t.get("code", "") for t in templates_output])
                artifacts.append(
                    Artifact(
                        name=f"suggested_tests_{Path(target_file).stem}.py",
                        artifact_type="test_template",
                        content=combined_code,
                        metadata={"target": target_file, "review_required": True},
                    )
                )

            # Optional AI Gateway Test Improvement Layer
            llm_test_advice = None
            try:
                from backend.app.config import settings
                if settings.GEMINI_API_KEY:
                    from backend.app.gateway.router import GatewayTask, ModelRouter
                    from backend.app.gateway.base_provider import Message, MessageRole
                    from backend.app.prompts.renderer import PromptRenderer

                    renderer = PromptRenderer()
                    rendered_prompt = renderer.render(
                        "testing_agent.j2",
                        {
                            "agent_name": self.name,
                            "agent_purpose": self.purpose,
                            "instruction": task.instruction,
                            "target": target_file,
                        },
                    )
                    router = ModelRouter()
                    gw_task = GatewayTask(complexity="simple", requires_reasoning=True)
                    llm_res = await router.execute_with_fallback(
                        messages=[Message(role=MessageRole.USER, content=rendered_prompt)],
                        task=gw_task,
                        max_tokens=1000,
                    )
                    llm_test_advice = llm_res.content
            except Exception:
                pass

            report = {
                "task_type": "test_generation",
                "target_file": target_file,
                "total_generated": len(templates_output),
                "templates": templates_output,
                "llm_test_strategy": llm_test_advice,
                "note": "Suggested test templates only. Marked [GENERATED - REVIEW REQUIRED]. Human review mandatory before committing.",
            }

            return AgentResult(
                success=gen_res.success,
                output=json.dumps(report, indent=2),
                artifacts=artifacts,
                evidence=evidence_items,
                limitations=self.limitations,
                simulated=False,
            )

        # -------------------------------------------------------------
        # 3. READ_ONLY Scope: Specific Tasks
        # -------------------------------------------------------------
        # A. Coverage Analysis
        if "coverage" in instruction or "analyze coverage" in instruction:
            cov_res = await self.coverage_analyzer.execute({
                "test_path": target_path or "backend/tests",
            }, context)

            for ev in cov_res.evidence:
                evidence_items.append(Evidence(source="coverage_analyzer", snippet=ev, confidence=1.0))

            cov_data = cov_res.output if isinstance(cov_res.output, dict) else {}
            summary_data = cov_data.get("summary", {})

            full_report = {
                "task_type": "coverage_analysis",
                "summary": {
                    "overall_coverage": cov_data.get("overall_coverage", 0.0),
                    "total_files": summary_data.get("total_files", 0),
                    "files_above_80": summary_data.get("files_above_80", 0),
                    "files_below_50": summary_data.get("files_below_50", 0),
                    "critical_gaps": summary_data.get("critical_gaps", []),
                },
                "coverage": cov_data,
                "scanned_at": datetime.now(timezone.utc).isoformat(),
            }

            artifacts.append(
                Artifact(
                    name="coverage_report.json",
                    artifact_type="coverage_report",
                    content=json.dumps(full_report, indent=2),
                    metadata={"overall_coverage": cov_data.get("overall_coverage", 0.0)},
                )
            )

            return AgentResult(
                success=cov_res.success,
                output=json.dumps(full_report, indent=2),
                artifacts=artifacts,
                evidence=evidence_items,
                limitations=self.limitations,
                simulated=False,
            )

        # B. Test Gap Detection
        if "gap" in instruction or "missing test" in instruction:
            gap_res = await self.test_gap_detector.execute({
                "path": target_path or "backend/app",
            }, context)

            for ev in gap_res.evidence:
                evidence_items.append(Evidence(source="test_gap_detector", snippet=ev, confidence=1.0))

            gap_data = gap_res.output if isinstance(gap_res.output, dict) else {}
            report = {
                "task_type": "gap_analysis",
                "summary": {
                    "source_functions": gap_data.get("source_functions", 0),
                    "tested_functions": gap_data.get("tested_functions", 0),
                    "coverage_ratio": gap_data.get("coverage_ratio", 0.0),
                    "gaps_count": len(gap_data.get("gaps", [])),
                },
                "gaps": gap_data.get("gaps", []),
                "missing_test_files": gap_data.get("missing_test_files", []),
                "recommendations": gap_data.get("recommendations", []),
                "scanned_at": datetime.now(timezone.utc).isoformat(),
            }

            return AgentResult(
                success=gap_res.success,
                output=json.dumps(report, indent=2),
                artifacts=artifacts,
                evidence=evidence_items,
                limitations=self.limitations,
                simulated=False,
            )

        # C. Failure Analysis on Provided Output
        if "failure" in instruction or task.context.get("failure_output"):
            raw_failure = task.context.get("failure_output") or task.instruction
            fail_res = await self.failure_analyzer.execute({"output": raw_failure}, context)

            for ev in fail_res.evidence:
                evidence_items.append(Evidence(source="failure_analyzer", snippet=ev, confidence=1.0))

            report = {
                "task_type": "failure_analysis",
                "analysis": fail_res.output,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }

            return AgentResult(
                success=fail_res.success,
                output=json.dumps(report, indent=2),
                artifacts=artifacts,
                evidence=evidence_items,
                limitations=self.limitations,
                simulated=False,
            )

        # Default READ_ONLY: Aggregated Test Quality & Gap Inspection
        gap_res = await self.test_gap_detector.execute({"path": target_path or "backend/app"}, context)
        for ev in gap_res.evidence:
            evidence_items.append(Evidence(source="test_gap_detector", snippet=ev, confidence=1.0))

        gap_data = gap_res.output if isinstance(gap_res.output, dict) else {}
        default_report = {
            "task_type": "test_quality_inspection",
            "summary": {
                "source_functions": gap_data.get("source_functions", 0),
                "tested_functions": gap_data.get("tested_functions", 0),
                "coverage_ratio": gap_data.get("coverage_ratio", 0.0),
                "total_gaps": len(gap_data.get("gaps", [])),
            },
            "gaps": gap_data.get("gaps", []),
            "missing_test_files": gap_data.get("missing_test_files", []),
            "recommendations": gap_data.get("recommendations", []),
        }

        return AgentResult(
            success=True,
            output=json.dumps(default_report, indent=2),
            artifacts=artifacts,
            evidence=evidence_items,
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
