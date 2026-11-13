from typing import Dict, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.agents.implementations import (
    ArchitectureAgent,
    CodingAgent,
    ContentAgent,
    DevOpsAgent,
    DocumentationAgent,
    EvalMatrixAgent,
    FlowExecutorStubAgent,
    RAGAgent,
    SecurityAgent,
    TestingAgent,
)


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        default_agents = [
            CodingAgent(),
            SecurityAgent(),
            TestingAgent(),
            ArchitectureAgent(),
            DocumentationAgent(),
            RAGAgent(),
            DevOpsAgent(),
            ContentAgent(),
            EvalMatrixAgent(),
            FlowExecutorStubAgent(),
        ]
        for agent in default_agents:
            self._agents[agent.slug] = agent

    def register(self, agent: BaseAgent):
        self._agents[agent.slug] = agent

    def get(self, slug: str) -> Optional[BaseAgent]:
        return self._agents.get(slug)

    def list_all(self) -> List[BaseAgent]:
        return list(self._agents.values())

    def exists(self, slug: str) -> bool:
        return slug in self._agents


# Global singleton instance
agent_registry = AgentRegistry()
