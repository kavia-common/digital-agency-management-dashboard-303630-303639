"""
Main FastAPI application with comprehensive API documentation and error handling.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration with error handling
try:
    from src.api.config import ALLOWED_ORIGINS, SUPABASE_URL, SUPABASE_KEY
    config_loaded = True
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    # Set fallback values
    ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:4000"]
    SUPABASE_URL = None
    SUPABASE_KEY = None
    config_loaded = False

# Import routers with error handling
routers_loaded = {}
try:
    from src.api.routers import auth
    routers_loaded['auth'] = True
except Exception as e:
    logger.warning(f"Failed to load auth router: {e}")
    routers_loaded['auth'] = False

try:
    from src.api.routers import users
    routers_loaded['users'] = True
except Exception as e:
    logger.warning(f"Failed to load users router: {e}")
    routers_loaded['users'] = False

try:
    from src.api.routers import projects
    routers_loaded['projects'] = True
except Exception as e:
    logger.warning(f"Failed to load projects router: {e}")
    routers_loaded['projects'] = False

try:
    from src.api.routers import clients
    routers_loaded['clients'] = True
except Exception as e:
    logger.warning(f"Failed to load clients router: {e}")
    routers_loaded['clients'] = False

try:
    from src.api.routers import dashboard
    routers_loaded['dashboard'] = True
except Exception as e:
    logger.warning(f"Failed to load dashboard router: {e}")
    routers_loaded['dashboard'] = False

try:
    from src.api.routers import settings
    routers_loaded['settings'] = True
except Exception as e:
    logger.warning(f"Failed to load settings router: {e}")
    routers_loaded['settings'] = False

# API metadata for OpenAPI documentation
tags_metadata = [
    {
        "name": "Health",
        "description": "Health check and readiness endpoints for monitoring and load balancers.",
    },
    {
        "name": "Authentication",
        "description": "Operations for user authentication including signup, login, logout, and password reset. All endpoints use Supabase Auth for secure user management.",
    },
    {
        "name": "Users",
        "description": "Operations for managing user profiles. Authenticated users can view, update, and delete their own profile information.",
    },
    {
        "name": "Projects",
        "description": "CRUD operations for projects. Users can create, read, update, and delete projects. Projects include details like name, description, budget, client association, and status tracking.",
    },
    {
        "name": "Clients",
        "description": "CRUD operations for clients. Users can manage their client database including contact information, company details, and notes.",
    },
    {
        "name": "Dashboard",
        "description": "Analytics and aggregated data endpoints for dashboard displays. Provides statistics on projects, clients, revenue, and recent activity.",
    },
    {
        "name": "Settings",
        "description": "User settings management including theme preferences and data export functionality. Users can customize their experience and export all their data.",
    },
]

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Digital Agency Project Management API",
    description="""
    A comprehensive backend API for managing a digital agency's projects, clients, and operations.
    
    ## Features
    
    * **Authentication**: Secure user signup, login, and password reset using Supabase Auth
    * **User Management**: Profile management with CRUD operations
    * **Projects**: Full CRUD operations for project tracking including budget, timeline, and status
    * **Clients**: Client database management with contact information and notes
    * **Dashboard Analytics**: Aggregated statistics and recent activity tracking
    * **Settings**: User preferences including theme selection and data export
    
    ## Authentication
    
    Most endpoints require authentication. After logging in or signing up, you'll receive a JWT access token.
    Include this token in the Authorization header for protected endpoints:
    
    ```
    Authorization: Bearer <your_access_token>
    ```
    
    ## Integration
    
    This API is designed to work seamlessly with:
    - **Supabase**: For authentication and database operations
    - **React Frontend**: Provides data for a modern web interface
    
    ## Real-time Updates
    
    For real-time project and client updates, consider subscribing to Supabase real-time channels
    in your client application.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS with proper fallback
cors_origins = ALLOWED_ORIGINS if ALLOWED_ORIGINS and ALLOWED_ORIGINS != [''] else [
    "http://localhost:3000",
    "http://localhost:4000",
    "https://vscode-internal-42152-beta.beta01.cloud.kavia.ai:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["*"],
)


# Error handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions with consistent JSON responses.
    
    Args:
        request: The incoming request
        exc: The HTTP exception
        
    Returns:
        JSONResponse: Formatted error response
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors with detailed information.
    
    Args:
        request: The incoming request
        exc: The validation error
        
    Returns:
        JSONResponse: Formatted validation error response
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions with safe error responses.
    
    Args:
        request: The incoming request
        exc: The exception
        
    Returns:
        JSONResponse: Generic error response
    """
    # Log the error in production
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"}
    )


# Include routers with error handling
if routers_loaded.get('auth'):
    app.include_router(auth.router)
else:
    logger.warning("Auth router not loaded - authentication endpoints unavailable")

if routers_loaded.get('users'):
    app.include_router(users.router)
else:
    logger.warning("Users router not loaded - user endpoints unavailable")

if routers_loaded.get('projects'):
    app.include_router(projects.router)
else:
    logger.warning("Projects router not loaded - project endpoints unavailable")

if routers_loaded.get('clients'):
    app.include_router(clients.router)
else:
    logger.warning("Clients router not loaded - client endpoints unavailable")

if routers_loaded.get('dashboard'):
    app.include_router(dashboard.router)
else:
    logger.warning("Dashboard router not loaded - dashboard endpoints unavailable")

if routers_loaded.get('settings'):
    app.include_router(settings.router)
else:
    logger.warning("Settings router not loaded - settings endpoints unavailable")


# Health check endpoints
@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is running. Always returns 200 OK.",
    response_description="API health status"
)
def health_check():
    """
    Basic health check endpoint.
    
    Returns a simple message indicating that the API is running.
    This endpoint always returns 200 OK, even if external services are down.
    
    Returns:
        dict: Health status message
    """
    return {
        "status": "healthy",
        "service": "Digital Agency Project Management API",
        "version": "1.0.0"
    }


@app.get(
    "/ready",
    tags=["Health"],
    summary="Readiness Check",
    description="Check if the API is ready to serve requests. Verifies configuration.",
    response_description="API readiness status"
)
def readiness_check():
    """
    Readiness check endpoint.
    
    Checks if the API is properly configured and ready to serve requests.
    Returns 200 OK even if external services (like Supabase) are temporarily unavailable,
    but logs warnings about configuration issues.
    
    Returns:
        dict: Readiness status with configuration details
    """
    ready = True
    issues = []
    
    # Check configuration
    if not config_loaded:
        issues.append("Configuration not fully loaded")
        logger.warning("Configuration not fully loaded")
    
    if not SUPABASE_URL:
        issues.append("SUPABASE_URL not configured")
        logger.warning("SUPABASE_URL environment variable not set")
    
    if not SUPABASE_KEY:
        issues.append("SUPABASE_KEY not configured")
        logger.warning("SUPABASE_KEY environment variable not set")
    
    # Check routers
    failed_routers = [name for name, loaded in routers_loaded.items() if not loaded]
    if failed_routers:
        issues.append(f"Some routers failed to load: {', '.join(failed_routers)}")
    
    return {
        "status": "ready" if ready and not issues else "ready with warnings",
        "service": "Digital Agency Project Management API",
        "version": "1.0.0",
        "config_loaded": config_loaded,
        "routers_loaded": routers_loaded,
        "issues": issues if issues else None
    }


# Root endpoint
@app.get(
    "/",
    tags=["Health"],
    summary="Root Endpoint",
    description="API root endpoint with basic information.",
    response_description="API information"
)
def root():
    """
    Root endpoint.
    
    Returns basic information about the API.
    
    Returns:
        dict: API information
    """
    return {
        "message": "Digital Agency Project Management API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    Performs initialization tasks and logs configuration when the application starts.
    """
    logger.info("=" * 60)
    logger.info("Starting Digital Agency Project Management API")
    logger.info("=" * 60)
    
    # Log environment
    env_mode = os.getenv('NODE_ENV', 'development')
    logger.info(f"Environment: {env_mode}")
    
    # Log configuration (masked)
    logger.info("Configuration Summary:")
    logger.info(f"  - SUPABASE_URL: {'✓ Configured' if SUPABASE_URL else '✗ Missing'}")
    logger.info(f"  - SUPABASE_KEY: {'✓ Configured (masked)' if SUPABASE_KEY else '✗ Missing'}")
    logger.info(f"  - JWT_SECRET: {'✓ Configured (masked)' if os.getenv('JWT_SECRET') else '✗ Missing (using default)'}")
    logger.info(f"  - ALLOWED_ORIGINS: {cors_origins}")
    
    # Log router status
    logger.info("Router Status:")
    for router_name, loaded in routers_loaded.items():
        status_icon = "✓" if loaded else "✗"
        logger.info(f"  {status_icon} {router_name}")
    
    # Warn about missing configuration
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("CRITICAL: Supabase configuration is missing!")
        logger.error("Please ensure SUPABASE_URL and SUPABASE_KEY are set in .env file")
        logger.error("The API will start but authentication and database operations will fail")
    
    # Log server configuration
    host = os.getenv('UVICORN_HOST', os.getenv('HOST', '0.0.0.0'))
    port = os.getenv('PORT', '3001')
    logger.info(f"Server listening on {host}:{port}")
    logger.info("=" * 60)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    
    Performs cleanup tasks when the application shuts down.
    """
    logger.info("Shutting down Digital Agency Project Management API")


# Ensure this is not run when imported
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3001"))
    host = os.getenv("UVICORN_HOST", "0.0.0.0")
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=True
    )
