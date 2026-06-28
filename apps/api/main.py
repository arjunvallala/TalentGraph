"""
TalentGraph AI — FastAPI Application Entry Point

Configures the FastAPI application with:
- Lifespan management (startup/shutdown)
- CORS middleware
- Request logging middleware
- Error handling middleware
- API versioning (/api/v1/)
- Health checks
- OpenAPI documentation

Usage:
    uvicorn apps.api.main:app --reload --port 8000
"""
from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from apps.api.middleware.error_handler import register_error_handlers
from apps.api.routers import (
    analytics,
    candidates,
    health,
    jobs,
    submission,
    system,
)
from shared.config import settings
from shared.constants import API_PREFIX, APP_NAME, APP_VERSION
from shared.logging_setup import configure_logging, get_logger

logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Runs startup tasks before the app begins serving requests,
    and cleanup tasks after the app stops.
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    configure_logging()
    logger.info(
        f"🚀 Starting {APP_NAME} v{APP_VERSION}",
        environment=settings.app_env,
        demo_mode=settings.demo_mode,
    )
    settings.ensure_directories()
    logger.info("✅ Directories initialised")

    if settings.demo_mode:
        logger.info("🎭 Demo mode is ENABLED — using pre-generated fixture data")

    logger.info(f"✅ {APP_NAME} is ready to serve requests")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info(f"🛑 Shutting down {APP_NAME}")


# ── Application Factory ───────────────────────────────────────────────────────

def create_application() -> FastAPI:
    """
    Application factory that creates and configures the FastAPI instance.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title=f"{APP_NAME} API",
        description=(
            "The AI Hiring Intelligence Platform that thinks like a hiring "
            "committee, not a search engine.\n\n"
            "**Offline | Explainable | Recruiter-Grade | Production-Ready**"
        ),
        version=APP_VERSION,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # ── Middleware ─────────────────────────────────────────────────────────────
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request Logging Middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:
        """Log every request with timing information."""
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"{request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        response.headers["X-TalentGraph-Version"] = APP_VERSION
        return response

    # ── Error Handlers ─────────────────────────────────────────────────────────
    register_error_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    prefix = API_PREFIX
    app.include_router(health.router, prefix=prefix, tags=["Health"])
    app.include_router(jobs.router, prefix=prefix, tags=["Jobs"])
    app.include_router(candidates.router, prefix=prefix, tags=["Candidates"])
    app.include_router(analytics.router, prefix=prefix, tags=["Analytics"])
    app.include_router(submission.router, prefix=prefix, tags=["Submission"])
    app.include_router(system.router, prefix=prefix, tags=["System"])

    @app.get("/", include_in_schema=False)
    async def root_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/docs")

    return app


# ── Application Instance ──────────────────────────────────────────────────────
app = create_application()
