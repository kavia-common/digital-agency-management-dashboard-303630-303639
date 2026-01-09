"""
Main FastAPI application with comprehensive API documentation and error handling.

Startup hardening goals:
- App must boot even if optional dependencies/config (Supabase, JWT_SECRET) are missing.
- /health and /ready must always be available and return 200.
- Routers are imported/registered defensively; failures are logged but do not stop startup.
- CORS should allow the frontend (http://localhost:3000) and support credentials.
"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure logging early
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import configuration with error handling
try:
    from src.api.config import (
        ALLOWED_ORIGINS,
        AUTH_CONFIGURED,
        FRONTEND_URL,
        SUPABASE_KEY,
        SUPABASE_URL,
        get_env_summary,
    )

    config_loaded = True
except Exception as e:  # pragma: no cover
    logger.error(f"Failed to load configuration module: {e}", exc_info=True)
    # Fallback values (keep app alive)
    ALLOWED_ORIGINS = []
    FRONTEND_URL = "http://localhost:3000"
    SUPABASE_URL = None
    SUPABASE_KEY = None
    AUTH_CONFIGURED = False

    def get_env_summary() -> dict:
        return {"config_loaded": False}

    config_loaded = False


# API metadata for OpenAPI documentation
tags_metadata = [
    {"name": "Health", "description": "Health check and readiness endpoints for monitoring and load balancers."},
    {
        "name": "Authentication",
        "description": "Operations for user authentication including signup, login, logout, and password reset.",
    },
    {"name": "Users", "description": "Operations for managing user profiles."},
    {"name": "Projects", "description": "CRUD operations for projects."},
    {"name": "Clients", "description": "CRUD operations for clients."},
    {"name": "Dashboard", "description": "Analytics and aggregated data endpoints for dashboard displays."},
    {"name": "Settings", "description": "User settings management including theme preferences and data export functionality."},
]

app = FastAPI(
    title="Digital Agency Project Management API",
    description="Backend API for managing projects, clients, and users.",
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS configuration (must allow frontend + credentials)
default_origins = [
    "http://localhost:3000",
    "http://localhost:4000",
    "https://vscode-internal-42152-beta.beta01.cloud.kavia.ai:3000",
]
cors_origins = ALLOWED_ORIGINS if ALLOWED_ORIGINS else default_origins
if FRONTEND_URL and FRONTEND_URL not in cors_origins:
    cors_origins = [*cors_origins, FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Defensive router imports/registration
routers_loaded: dict[str, bool] = {}


def _include_router_safe(module_path: str, key: str) -> None:
    """Import and include a router without failing application startup."""
    try:
        module = __import__(module_path, fromlist=["router"])
        router = getattr(module, "router", None)
        if router is None:
            raise AttributeError(f"{module_path} has no attribute 'router'")
        app.include_router(router)
        routers_loaded[key] = True
        logger.info(f"Router registered: {key} ({module_path}) ✓")
    except Exception as e:
        routers_loaded[key] = False
        logger.warning(f"Router NOT loaded: {key} ({module_path}): {e}")


# Register routers (optional)
_include_router_safe("src.api.routers.auth", "auth")
_include_router_safe("src.api.routers.users", "users")
_include_router_safe("src.api.routers.projects", "projects")
_include_router_safe("src.api.routers.clients", "clients")
_include_router_safe("src.api.routers.dashboard", "dashboard")
_include_router_safe("src.api.routers.settings", "settings")


# Error handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions with consistent JSON responses.

    Args:
        request: The incoming request.
        exc: The HTTP exception.

    Returns:
        JSONResponse: Formatted error response.
    """
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors with detailed information.

    Args:
        request: The incoming request.
        exc: The validation error.

    Returns:
        JSONResponse: Formatted validation error response.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": "Validation error", "errors": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions with safe error responses.

    Args:
        request: The incoming request.
        exc: The exception.

    Returns:
        JSONResponse: Generic error response.
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "An unexpected error occurred"})


# Health check endpoints (must always be available)
@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is running. Always returns 200 OK.",
    response_description="API health status",
)
def health_check():
    """
    Basic health check endpoint.

    Returns:
        dict: Health status message.
    """
    return {"status": "healthy", "service": "Digital Agency Project Management API", "version": "1.0.0"}


@app.get(
    "/ready",
    tags=["Health"],
    summary="Readiness Check",
    description="Check if the API is ready to serve requests. Always returns 200; may include warnings.",
    response_description="API readiness status",
)
def readiness_check():
    """
    Readiness check endpoint.

    This endpoint ALWAYS returns HTTP 200 so orchestrators/E2E can proceed, but it will
    include warnings if optional configuration (Supabase/JWT) is missing.

    Returns:
        dict: Readiness status with configuration details.
    """
    issues: list[str] = []

    if not config_loaded:
        issues.append("Configuration not fully loaded")

    if not SUPABASE_URL:
        issues.append("SUPABASE_URL not configured")

    if not SUPABASE_KEY:
        issues.append("SUPABASE_KEY not configured")

    if not AUTH_CONFIGURED:
        issues.append("Auth not fully configured (JWT_SECRET missing and/or Supabase missing)")

    failed_routers = [name for name, loaded in routers_loaded.items() if not loaded]
    if failed_routers:
        issues.append(f"Some routers failed to load: {', '.join(failed_routers)}")

    return {
        "status": "ready" if not issues else "ready_with_warnings",
        "service": "Digital Agency Project Management API",
        "version": "1.0.0",
        "config_loaded": config_loaded,
        "routers_loaded": routers_loaded,
        "issues": issues or None,
    }


@app.get(
    "/",
    tags=["Health"],
    summary="Root Endpoint",
    description="API root endpoint with basic information.",
    response_description="API information",
)
def root():
    """
    Root endpoint.

    Returns:
        dict: API information.
    """
    return {"message": "Digital Agency Project Management API", "version": "1.0.0", "status": "running", "health": "/health", "ready": "/ready"}


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.

    Logs masked env summary and router registration status.
    """
    logger.info("=" * 60)
    logger.info("Starting Digital Agency Project Management API")
    logger.info("=" * 60)

    env_mode = os.getenv("NODE_ENV", os.getenv("REACT_APP_NODE_ENV", "development"))
    logger.info(f"Environment: {env_mode}")

    # Masked config summary
    summary = get_env_summary()
    logger.info("Configuration Summary (masked):")
    for k, v in summary.items():
        logger.info(f"  - {k}: {v}")

    # Router status
    logger.info("Router Status:")
    for router_name, loaded in routers_loaded.items():
        status_icon = "✓" if loaded else "✗"
        logger.info(f"  {status_icon} {router_name}")

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase configuration missing: app running in degraded mode (DB/auth endpoints may fail).")

    host = os.getenv("UVICORN_HOST", os.getenv("HOST", "0.0.0.0"))
    port = os.getenv("PORT", "3001")
    logger.info(f"Server configured for {host}:{port}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    """
    logger.info("Shutting down Digital Agency Project Management API")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "3001"))
    host = os.getenv("UVICORN_HOST", "0.0.0.0")
    uvicorn.run("src.api.main:app", host=host, port=port, reload=True)
