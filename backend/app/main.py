from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from backend.app.config import settings
from backend.app.database import Base, engine
from backend.app.agents.lifecycle import TransitionError
from backend.app.middleware.logging import StructuredLoggingMiddleware
from backend.app.middleware.rate_limit import RateLimitMiddleware
from backend.app.routers.agents import router as agents_router
from backend.app.routers.auth import router as auth_router
from backend.app.routers.executions import router as executions_router
from backend.app.routers.health import router as health_router
from backend.app.routers.projects import router as projects_router
from backend.app.routers.security import router as security_router
from backend.app.routers.testing import router as testing_router
from backend.app.routers.gateway import router as gateway_router
from backend.app.routers.mcp import router as mcp_router
from backend.app.routers.ws import router as ws_router
from backend.app.routers.architecture import router as architecture_router
from backend.app.routers.documentation import router as documentation_router
from backend.app.routers.knowledge import router as knowledge_router
from backend.app.routers.devops import router as devops_router
from backend.app.routers.content import router as content_router
from backend.app.routers.portfolio import router as portfolio_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist for sqlite / local runtime
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: dispose of database engine pools
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-ready REST API for Rayhan AI Engineering Workbench.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 1. Custom Exception Handlers (Never expose internal stack traces)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Build clean human-readable summary
    msg = "; ".join([f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors])
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": msg,
            "status_code": 422,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # If detail is already a structured dict, use it
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=exc.headers,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": str(exc.detail),
            "status_code": exc.status_code,
        },
        headers=exc.headers,
    )


@app.exception_handler(TransitionError)
async def transition_error_handler(request: Request, exc: TransitionError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "invalid_transition",
            "message": str(exc),
            "status_code": 422,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please contact the administrator.",
            "status_code": 500,
        },
    )


# 2. Register Middlewares (Order: Logging -> Rate Limit -> CORS)
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Register Routers with /api/v1 Prefix
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(agents_router, prefix=settings.API_V1_PREFIX)
app.include_router(executions_router, prefix=settings.API_V1_PREFIX)
app.include_router(security_router, prefix=settings.API_V1_PREFIX)
app.include_router(testing_router, prefix=settings.API_V1_PREFIX)
app.include_router(gateway_router, prefix=settings.API_V1_PREFIX)
app.include_router(mcp_router, prefix=settings.API_V1_PREFIX)
app.include_router(ws_router, prefix=settings.API_V1_PREFIX)
app.include_router(architecture_router, prefix=settings.API_V1_PREFIX)
app.include_router(documentation_router, prefix=settings.API_V1_PREFIX)
app.include_router(knowledge_router, prefix=settings.API_V1_PREFIX)
app.include_router(devops_router, prefix=settings.API_V1_PREFIX)
app.include_router(content_router, prefix=settings.API_V1_PREFIX)
app.include_router(portfolio_router, prefix=settings.API_V1_PREFIX)




@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }
