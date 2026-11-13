"""E2E Test 4: MCP Tool Read vs Write Approval Flow & Audit Logging."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_e2e_mcp_read_write_approval_and_audit(client: AsyncClient, auth_headers: dict):
    # 1. Read-only MCP tool executes directly
    read_res = await client.post(
        "/api/v1/mcp/tools/fs_read_file/execute",
        json={"parameters": {"path": "backend/app/config.py"}},
        headers=auth_headers,
    )
    assert read_res.status_code == 200
    read_data = read_res.json()
    assert read_data["success"] is True
    assert read_data["requires_approval"] is False

    # 2. Write MCP tool pauses and issues pending approval request
    tmp_rel = f"backend/tests/e2e/.tmp_mcp_e2e_{uuid.uuid4().hex[:6]}.txt"
    write_res = await client.post(
        "/api/v1/mcp/tools/fs_write_file/execute",
        json={"parameters": {"path": tmp_rel, "content": "e2e verified"}},
        headers=auth_headers,
    )
    assert write_res.status_code == 200
    write_data = write_res.json()
    assert write_data["requires_approval"] is True
    approval_id = write_data["approval_id"]
    assert approval_id

    # 3. Approve pending request & verify approval state
    appr_res = await client.post(
        f"/api/v1/mcp/approvals/{approval_id}/approve",
        headers=auth_headers,
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "approved"

    # 4. Reject flow on a second write request verifies audit trail cleanly without disk clutter
    rej_req = await client.post(
        "/api/v1/mcp/tools/fs_write_file/execute",
        json={"parameters": {"path": tmp_rel, "content": "rejected payload", "api_key": "sk-secret-123456"}},
        headers=auth_headers,
    )
    rej_id = rej_req.json()["approval_id"]
    rej_res = await client.post(
        f"/api/v1/mcp/approvals/{rej_id}/reject",
        json={"reason": "E2E test clean rejection"},
        headers=auth_headers,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"

    # 5. Audit log contains entries with scrubbed secrets
    audit_res = await client.get("/api/v1/mcp/audit", headers=auth_headers)
    assert audit_res.status_code == 200
    audits = audit_res.json()
    assert len(audits) >= 1
    assert "sk-secret-123456" not in audit_res.text
