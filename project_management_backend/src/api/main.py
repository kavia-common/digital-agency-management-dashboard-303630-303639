"""
Main FastAPI application with comprehensive API documentation and error handling.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

# Import routers
from src.api.routers import auth, users, projects, clients, dashboard, settings
from src.api.config import ALLOWED_ORIGINS

# API metadata for OpenAPI documentation
tags_metadata = [
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    print(f"Unexpected error: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"}
    )


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(clients.router)
app.include_router(dashboard.router)
app.include_router(settings.router)


# Health check endpoint
@app.get(
    "/",
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is running and healthy.",
    response_description="API health status"
)
def health_check():
    """
    Health check endpoint.
    
    Returns a simple message indicating that the API is running and healthy.
    Useful for monitoring and load balancer health checks.
    
    Returns:
        dict: Health status message
    """
    return {
        "message": "Healthy",
        "status": "ok",
        "version": "1.0.0"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    Performs initialization tasks when the application starts.
    """
    print("Starting Digital Agency Project Management API...")
    print(f"Environment: {os.getenv('NODE_ENV', 'development')}")
    print(f"CORS Origins: {ALLOWED_ORIGINS}")
