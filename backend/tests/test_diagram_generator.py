import pytest
from backend.app.tools.diagram_generator import DiagramGenerator, DiagramResult


def test_system_architecture_diagram_valid_mermaid():
    """Verify system architecture generates valid Mermaid graph TD."""
    result = DiagramGenerator.system_architecture()
    assert isinstance(result, DiagramResult)
    assert result.diagram_type == "system_architecture"
    assert DiagramGenerator.validate_mermaid_syntax(result.mermaid_code) is True
    assert "graph TD" in result.mermaid_code
    assert "React" in result.mermaid_code
    assert "FastAPI" in result.mermaid_code
    assert "PostgreSQL" in result.mermaid_code
    assert len(result.components_found) >= 5


def test_database_er_diagram_valid_mermaid():
    """Verify database ER diagram generates valid Mermaid erDiagram with real tables."""
    result = DiagramGenerator.database_er()
    assert isinstance(result, DiagramResult)
    assert result.diagram_type == "database_er"
    assert DiagramGenerator.validate_mermaid_syntax(result.mermaid_code) is True
    assert "erDiagram" in result.mermaid_code
    assert "users" in result.mermaid_code
    assert "projects" in result.mermaid_code
    assert "agent_executions" in result.mermaid_code
    assert "tool_audits" in result.mermaid_code
    assert len(result.components_found) >= 4


def test_api_flow_sequence_diagram_valid_mermaid():
    """Verify API flow diagram generates valid Mermaid sequenceDiagram."""
    result = DiagramGenerator.api_flow()
    assert isinstance(result, DiagramResult)
    assert result.diagram_type == "api_flow"
    assert DiagramGenerator.validate_mermaid_syntax(result.mermaid_code) is True
    assert "sequenceDiagram" in result.mermaid_code
    assert "Client" in result.mermaid_code
    assert "Middleware" in result.mermaid_code or "Auth" in result.mermaid_code
    assert "Router" in result.mermaid_code


def test_agent_workflow_state_diagram_valid_mermaid():
    """Verify agent workflow generates valid Mermaid stateDiagram."""
    result = DiagramGenerator.agent_workflow("architecture-agent")
    assert isinstance(result, DiagramResult)
    assert result.diagram_type == "agent_workflow"
    assert DiagramGenerator.validate_mermaid_syntax(result.mermaid_code) is True
    assert "stateDiagram" in result.mermaid_code
    assert "PLANNED" in result.mermaid_code
    assert "RUNNING" in result.mermaid_code
    assert "COMPLETED" in result.mermaid_code


def test_component_hierarchy_diagram_valid_mermaid():
    """Verify component hierarchy generates valid Mermaid graph LR."""
    result = DiagramGenerator.component_hierarchy()
    assert isinstance(result, DiagramResult)
    assert result.diagram_type == "component_hierarchy"
    assert DiagramGenerator.validate_mermaid_syntax(result.mermaid_code) is True
    assert "graph LR" in result.mermaid_code
    assert "App" in result.mermaid_code
    assert "Sidebar" in result.mermaid_code


def test_invalid_diagram_type_raises_value_error():
    """Verify invalid diagram type raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        DiagramGenerator.generate("non_existent_type")
    assert "Unknown diagram_type" in str(excinfo.value)
