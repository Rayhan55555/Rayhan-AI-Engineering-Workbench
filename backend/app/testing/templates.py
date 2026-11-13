"""
Deterministic Pytest templates for Unit, Integration, and Boundary testing.
NO LLM - pure rule-based code synthesis.
Every generated template is strictly marked with # [GENERATED - REVIEW REQUIRED].
"""

PYTHON_UNIT_TEST_TEMPLATE = """# [GENERATED - REVIEW REQUIRED]
# Generated deterministically by Rayhan AI Engineering Workbench Testing Agent.
# Do not commit without human verification of test assertions and fixtures.

import pytest
{imports_code}

def test_{function_name}_success({fixture_params}):
    \"\"\"Verify {function_name} executes successfully on valid inputs (Happy Path).\"\"\"
    # Arrange
{arrange_code}

    # Act
    result = {act_call}

    # Assert
{assert_code}


def test_{function_name}_invalid_input({fixture_params}):
    \"\"\"Verify {function_name} raises appropriate error or handles invalid inputs safely.\"\"\"
    # Arrange
{invalid_arrange_code}

    # Act & Assert
    with pytest.raises({expected_error}):
        {invalid_act_call}


def test_{function_name}_boundary_values({fixture_params}):
    \"\"\"Verify {function_name} behavior at edge/boundary conditions.\"\"\"
    # Arrange
{boundary_arrange_code}

    # Act
    result = {boundary_act_call}

    # Assert
    assert result is not None
"""

PYTHON_ASYNC_UNIT_TEST_TEMPLATE = """# [GENERATED - REVIEW REQUIRED]
# Generated deterministically by Rayhan AI Engineering Workbench Testing Agent.
# Do not commit without human verification of test assertions and fixtures.

import pytest
{imports_code}

@pytest.mark.asyncio
async def test_{function_name}_success({fixture_params}):
    \"\"\"Verify async {function_name} executes successfully on valid inputs.\"\"\"
    # Arrange
{arrange_code}

    # Act
    result = await {act_call}

    # Assert
{assert_code}


@pytest.mark.asyncio
async def test_{function_name}_error_handling({fixture_params}):
    \"\"\"Verify async {function_name} handles errors and invalid parameters.\"\"\"
    # Arrange
{invalid_arrange_code}

    # Act & Assert
    with pytest.raises({expected_error}):
        await {invalid_act_call}
"""

PYTHON_FASTAPI_INTEGRATION_TEST_TEMPLATE = """# [GENERATED - REVIEW REQUIRED]
# Generated deterministically by Rayhan AI Engineering Workbench Testing Agent.
# Integration test for endpoint {endpoint_path}

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_{endpoint_name}_authenticated(client: AsyncClient, auth_headers: dict):
    \"\"\"Verify {endpoint_path} returns 200/202 with valid authentication.\"\"\"
    response = await client.{method_lower}(
        "{endpoint_path}",
        headers=auth_headers,
{payload_code}
    )
    assert response.status_code in (200, 201, 202)
    data = response.json()
    assert data is not None


@pytest.mark.asyncio
async def test_{endpoint_name}_unauthenticated(client: AsyncClient):
    \"\"\"Verify {endpoint_path} strictly rejects unauthenticated access with 401.\"\"\"
    response = await client.{method_lower}(
        "{endpoint_path}",
{payload_code}
    )
    assert response.status_code in (401, 403)
"""
