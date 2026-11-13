from typing import Dict, List, Set, Tuple
from backend.app.models.agent import AgentStatus


class TransitionError(Exception):
    def __init__(self, from_status: AgentStatus, to_status: AgentStatus, reason: str):
        self.from_status = from_status
        self.to_status = to_status
        self.reason = reason
        super().__init__(
            f"Invalid status transition from '{from_status.value}' to '{to_status.value}': {reason}"
        )


# Valid directed transitions map
VALID_TRANSITIONS: Dict[AgentStatus, Set[AgentStatus]] = {
    AgentStatus.Planned: {AgentStatus.Configured},
    AgentStatus.Configured: {AgentStatus.Available, AgentStatus.Maintenance, AgentStatus.Planned},
    AgentStatus.Available: {AgentStatus.Running, AgentStatus.Maintenance, AgentStatus.Configured},
    AgentStatus.Running: {AgentStatus.Completed if hasattr(AgentStatus, "Completed") else AgentStatus.Available, AgentStatus.Failed},
    AgentStatus.Failed: {AgentStatus.Available, AgentStatus.Maintenance, AgentStatus.Configured},
    AgentStatus.Maintenance: {AgentStatus.Available, AgentStatus.Configured},
}


class AgentLifecycleManager:
    @staticmethod
    def can_transition(
        current_status: AgentStatus, target_status: AgentStatus
    ) -> Tuple[bool, str]:
        if current_status == target_status:
            return True, "No status change"

        allowed_targets = VALID_TRANSITIONS.get(current_status, set())
        if target_status in allowed_targets:
            return True, "Valid transition"

        # Explicit rejection reasons
        if current_status == AgentStatus.Planned and target_status == AgentStatus.Running:
            return (
                False,
                "Agent cannot go directly from Planned to Running. It must first be Configured and Available.",
            )

        if target_status == AgentStatus.Running and current_status != AgentStatus.Available:
            return (
                False,
                f"Agent cannot run without Available status. Current status is '{current_status.value}'.",
            )

        return (
            False,
            f"Transition from '{current_status.value}' to '{target_status.value}' violates lifecycle state machine.",
        )

    @classmethod
    def validate_transition(
        cls, current_status: AgentStatus, target_status: AgentStatus, reason: str = ""
    ) -> None:
        can_move, explanation = cls.can_transition(current_status, target_status)
        if not can_move:
            raise TransitionError(current_status, target_status, explanation)
