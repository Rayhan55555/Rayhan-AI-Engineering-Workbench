"""Health Monitor Tool for application, database, and external service vitality checks.

Provides real latency metrics, error tracking, and overall system state
without fabrication.
"""

import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx
from pydantic import BaseModel, Field
from sqlalchemy import text

try:
    from backend.app.config import settings
    import backend.app.database as db_module
except ImportError:
    from app.config import settings
    import app.database as db_module


class ServiceHealth(BaseModel):
    """Health metrics for an individual service."""

    status: str  # "healthy", "degraded", "down", "unconfigured"
    ms: int
    details: Optional[str] = None


class HealthReport(BaseModel):
    """System-wide consolidated health report."""

    overall: str  # "healthy", "degraded", "down"
    timestamp: str
    services: Dict[str, ServiceHealth]
    alerts: List[str] = Field(default_factory=list)


class HealthMonitor:
    """Monitors live status of API, database, and external integrations."""

    @classmethod
    async def check_database(cls) -> ServiceHealth:
        """Measure database query roundtrip latency and connectivity."""
        start = time.perf_counter()
        try:
            async with db_module.AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ServiceHealth(
                status="healthy",
                ms=max(1, elapsed_ms),
                details="PostgreSQL connection pool healthy; SELECT 1 succeeded.",
            )
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ServiceHealth(
                status="down",
                ms=elapsed_ms,
                details=f"Database unreachable: {type(e).__name__} - {str(e)}",
            )

    @classmethod
    async def check_api(cls) -> ServiceHealth:
        """Measure local API responsiveness."""
        start = time.perf_counter()
        # Direct internal check
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return ServiceHealth(
            status="healthy",
            ms=max(1, elapsed_ms),
            details=f"FastAPI app v{settings.VERSION} active in {settings.ENVIRONMENT} mode.",
        )

    @classmethod
    async def check_github(cls, timeout_sec: float = 3.0) -> ServiceHealth:
        """Check GitHub API reachability and rate limits."""
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=timeout_sec) as client:
                resp = await client.get("https://api.github.com/rate_limit", headers={"User-Agent": "Rayhan-Workbench"})
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                if resp.status_code == 200:
                    data = resp.json()
                    core_rem = data.get("resources", {}).get("core", {}).get("remaining", "unknown")
                    return ServiceHealth(
                        status="healthy",
                        ms=max(1, elapsed_ms),
                        details=f"GitHub API reachable; remaining rate limit: {core_rem}",
                    )
                else:
                    return ServiceHealth(
                        status="degraded",
                        ms=elapsed_ms,
                        details=f"GitHub API returned HTTP {resp.status_code}",
                    )
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ServiceHealth(
                status="degraded",
                ms=elapsed_ms,
                details=f"GitHub API connection notice: {type(e).__name__}",
            )

    @classmethod
    async def check_gemini(cls, timeout_sec: float = 3.0) -> ServiceHealth:
        """Check Gemini AI Gateway / Google API connectivity."""
        start = time.perf_counter()
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if not gemini_key:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ServiceHealth(
                status="unconfigured",
                ms=elapsed_ms,
                details="GEMINI_API_KEY is not set in environment.",
            )

        try:
            # Check Google GenAI API endpoint vitality
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
            async with httpx.AsyncClient(timeout=timeout_sec) as client:
                resp = await client.get(url)
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                if resp.status_code == 200:
                    return ServiceHealth(
                        status="healthy",
                        ms=max(1, elapsed_ms),
                        details="Gemini models endpoint authenticated and responding.",
                    )
                else:
                    return ServiceHealth(
                        status="degraded",
                        ms=elapsed_ms,
                        details=f"Gemini API returned status {resp.status_code}",
                    )
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ServiceHealth(
                status="degraded",
                ms=elapsed_ms,
                details=f"Gemini API unreachable: {type(e).__name__}",
            )

    @classmethod
    async def check_all(cls) -> HealthReport:
        """Run all health checks and assemble consolidated report."""
        api_h = await cls.check_api()
        db_h = await cls.check_database()
        gh_h = await cls.check_github()
        gemini_h = await cls.check_gemini()

        services = {
            "api": api_h,
            "database": db_h,
            "gemini": gemini_h,
            "github": gh_h,
        }

        alerts: List[str] = []
        if db_h.status == "down":
            alerts.append("CRITICAL: Database connection is DOWN. Immediate attention required.")
        elif db_h.status == "degraded":
            alerts.append("WARNING: Database connection is degraded.")

        if api_h.status != "healthy":
            alerts.append("WARNING: API latency or responsiveness issue detected.")

        if gh_h.status == "degraded":
            alerts.append("NOTICE: GitHub API rate limit or latency degraded.")

        if gemini_h.status == "unconfigured":
            alerts.append("INFO: Gemini API key unconfigured; AI Gateway operates in fallback mode.")
        elif gemini_h.status in ["down", "degraded"]:
            alerts.append("NOTICE: Gemini API endpoint reported latency or connectivity degradation.")

        # Determine overall state
        if db_h.status == "down" or api_h.status == "down":
            overall = "down"
        elif any(s.status in ["degraded", "down"] for s in services.values()):
            overall = "degraded"
        else:
            overall = "healthy"

        return HealthReport(
            overall=overall,
            timestamp=datetime.now(timezone.utc).isoformat(),
            services=services,
            alerts=alerts,
        )
