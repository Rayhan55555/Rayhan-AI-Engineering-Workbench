from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.gateway.base_provider import LLMResponse
from backend.app.models.llm_usage import LLMUsage


class CostTracker:
    """
    Manages recording LLM token usage and USD costs into PostgreSQL.
    Provides daily and aggregate analytics across users, agents, and models.
    """
    @staticmethod
    async def record_usage(
        db: AsyncSession,
        user_id: uuid.UUID,
        agent_slug: str,
        response: LLMResponse,
        task_type: str = "completion",
    ) -> LLMUsage:
        usage = LLMUsage(
            user_id=user_id,
            agent_slug=agent_slug,
            provider=response.provider,
            model=response.model_used,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            total_tokens=response.total_tokens,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
            task_type=task_type,
        )
        db.add(usage)
        await db.commit()
        await db.refresh(usage)
        return usage

    @staticmethod
    async def get_usage_summary(
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        agent_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = select(
            func.count(LLMUsage.id).label("total_requests"),
            func.coalesce(func.sum(LLMUsage.input_tokens), 0).label("total_input_tokens"),
            func.coalesce(func.sum(LLMUsage.output_tokens), 0).label("total_output_tokens"),
            func.coalesce(func.sum(LLMUsage.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(LLMUsage.cost_usd), 0.0).label("total_cost_usd"),
            func.coalesce(func.avg(LLMUsage.latency_ms), 0.0).label("avg_latency_ms"),
        )
        if user_id:
            query = query.where(LLMUsage.user_id == user_id)
        if agent_slug:
            query = query.where(LLMUsage.agent_slug == agent_slug)

        row = (await db.execute(query)).first()

        # Cost breakdown by agent
        agent_query = select(
            LLMUsage.agent_slug,
            func.coalesce(func.sum(LLMUsage.cost_usd), 0.0).label("cost"),
            func.count(LLMUsage.id).label("requests"),
            func.coalesce(func.sum(LLMUsage.total_tokens), 0).label("tokens"),
        ).group_by(LLMUsage.agent_slug)
        if user_id:
            agent_query = agent_query.where(LLMUsage.user_id == user_id)
        agent_rows = (await db.execute(agent_query)).all()

        by_agent = [
            {"agent_slug": r.agent_slug, "cost_usd": round(float(r.cost), 6), "requests": r.requests, "tokens": r.tokens}
            for r in agent_rows
        ]

        # Breakdown by model
        model_query = select(
            LLMUsage.model,
            func.count(LLMUsage.id).label("requests"),
            func.coalesce(func.sum(LLMUsage.cost_usd), 0.0).label("cost"),
        ).group_by(LLMUsage.model)
        if user_id:
            model_query = model_query.where(LLMUsage.user_id == user_id)
        model_rows = (await db.execute(model_query)).all()

        by_model = [
            {"model": r.model, "requests": r.requests, "cost_usd": round(float(r.cost), 6)}
            for r in model_rows
        ]

        return {
            "total_requests": row.total_requests if row else 0,
            "total_input_tokens": row.total_input_tokens if row else 0,
            "total_output_tokens": row.total_output_tokens if row else 0,
            "total_tokens": row.total_tokens if row else 0,
            "total_cost_usd": round(float(row.total_cost_usd if row else 0.0), 6),
            "avg_latency_ms": round(float(row.avg_latency_ms if row else 0.0), 1),
            "by_agent": by_agent,
            "by_model": by_model,
        }

    @staticmethod
    async def get_daily_usage(
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        days: int = 14,
    ) -> List[Dict[str, Any]]:
        # Cast created_at to date
        query = select(
            func.date(LLMUsage.created_at).label("day"),
            func.count(LLMUsage.id).label("requests"),
            func.coalesce(func.sum(LLMUsage.total_tokens), 0).label("tokens"),
            func.coalesce(func.sum(LLMUsage.cost_usd), 0.0).label("cost"),
        ).group_by(func.date(LLMUsage.created_at)).order_by(func.date(LLMUsage.created_at).desc()).limit(days)

        if user_id:
            query = query.where(LLMUsage.user_id == user_id)

        rows = (await db.execute(query)).all()
        return [
            {
                "date": str(r.day),
                "requests": r.requests,
                "tokens": r.tokens,
                "cost_usd": round(float(r.cost), 6),
            }
            for r in reversed(rows)
        ]
