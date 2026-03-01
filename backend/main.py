"""
main.py
───────
MoodLens FastAPI application entry point.

Startup sequence
────────────────
1. Create SQLite tables (idempotent)
2. Register all routers
3. Mount /static for the React SPA
4. Serve index.html on the root path (SPA catch-all)

Run locally
───────────
  uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import create_tables
from backend.routes.analytics import router as analytics_router
from backend.routes.auth import router as auth_router
from backend.routes.journal import router as journal_router

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Lifespan ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: runs startup logic before yield, teardown after."""
    logger.info("🚀  Starting %s v%s", settings.app_name, settings.app_version)
    await create_tables()
    logger.info("✅  Database tables ready")
    yield
    logger.info("👋  Shutting down %s", settings.app_name)


# ── App ────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered mental health journal. "
        "Track your mood, receive personalised insights, and build healthy habits."
    ),
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ────────────────────────────────────────────────────────────
app.include_router(auth_router,      prefix="/api")
app.include_router(journal_router,   prefix="/api")
app.include_router(analytics_router, prefix="/api")


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
async def health() -> dict:
    """Lightweight health check for load balancers / uptime monitors."""
    return {"status": "ok", "version": settings.app_version}


# ── Global error handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all so unhandled exceptions don't leak stack traces to clients."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."},
    )


# ── Static / SPA ───────────────────────────────────────────────────────────
_FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

if _FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        """Serve the React SPA for all non-API routes."""
        index = _FRONTEND_DIR / "index.html"
        return FileResponse(str(index))
