from backend.app.routers.auth import router as auth_router
from backend.app.routers.projects import router as projects_router
from backend.app.routers.agents import router as agents_router
from backend.app.routers.health import router as health_router
from backend.app.routers.executions import router as executions_router

__all__ = [
    "auth_router",
    "projects_router",
    "agents_router",
    "health_router",
    "executions_router",
]
