"""Workflow Automation Worker stub agent for planned async pipeline execution."""

from backend.app.agents.base_agent import (
    AgentResult,
    AgentTask,
    BaseAgent,
    CapabilityDescription,
    ExecutionContext,
    ValidationResult,
)


class FlowExecutorStubAgent(BaseAgent):
    slug = "flow-executor"
    name = "Workflow Automation Worker"
    purpose = "Durable event-driven asynchronous background processing daemon for webhook validation and downstream enrichment."
    phase = 1
    version = "0.1.0"
    allowed_tools = ["Webhook Ingestion", "Payload Transformer", "Slack/Email Notifier", "State Store"]
    required_permissions = ["READ_ONLY", "SUGGEST"]
    limitations = ["Stub runtime active until durable webhook worker activation"]

    async def validate_input(self, task: AgentTask) -> ValidationResult:
        if len(task.instruction.strip()) < 3:
            return ValidationResult(valid=False, error="Instruction is too short.")
        return ValidationResult(valid=True)

    async def execute(self, task: AgentTask, context: ExecutionContext) -> AgentResult:
        output = (
            f"[STUB] FlowExecutorStubAgent processed request: '{task.instruction}'. "
            "Durable workflow execution runtime not yet enabled."
        )
        return AgentResult(
            success=True,
            output=output,
            artifacts=[],
            evidence=[],
            limitations=self.limitations,
            simulated=True,
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
