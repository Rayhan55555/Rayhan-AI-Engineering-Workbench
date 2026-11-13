"""Unit and integration tests for Health Monitor Tool (Phase 11.4)."""

import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.tools.health_monitor import HealthMonitor, HealthReport, ServiceHealth


@pytest.mark.asyncio
async def test_health_monitor_database_healthy(db_session: AsyncSession):
    """Verify database health check reports healthy when session is connected."""
    status = await HealthMonitor.check_database()
    assert isinstance(status, ServiceHealth)
    assert status.status == "healthy"
    assert status.ms >= 0


@pytest.mark.asyncio
async def test_health_monitor_database_down():
    """Verify database health check gracefully reports down when query fails."""
    with patch("backend.app.tools.health_monitor.db_module.AsyncSessionLocal") as mock_session_local:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.side_effect = ConnectionRefusedError("Database offline")
        mock_session_local.return_value = mock_ctx

        status = await HealthMonitor.check_database()
        assert status.status == "down"
        assert "Database offline" in (status.details or "")


@pytest.mark.asyncio
async def test_health_monitor_api_healthy():
    """Verify internal API check returns healthy."""
    status = await HealthMonitor.check_api()
    assert status.status == "healthy"
    assert status.ms >= 0


@pytest.mark.asyncio
async def test_health_monitor_check_all():
    """Verify consolidated system report contains all services and timestamp."""
    report = await HealthMonitor.check_all()
    assert isinstance(report, HealthReport)
    assert report.overall in ["healthy", "degraded", "down"]
    assert "api" in report.services
    assert "database" in report.services
    assert "github" in report.services
    assert "gemini" in report.services
    assert report.timestamp is not None


@pytest.mark.asyncio
async def test_health_monitor_degraded_creates_alert():
    """Verify degraded service triggers an alert entry in HealthReport."""
    with patch.object(
        HealthMonitor,
        "check_database",
        return_value=ServiceHealth(status="down", ms=500, details="Failed pool"),
    ):
        report = await HealthMonitor.check_all()
        assert report.overall in ["degraded", "down"]
        assert any("CRITICAL: Database connection is DOWN" in a for a in report.alerts)
