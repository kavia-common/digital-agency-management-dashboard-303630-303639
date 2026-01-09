"""
Dashboard router for analytics and data aggregation.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from src.api.schemas import DashboardStats, Project
from src.api.config import get_supabase_client
from src.api.middleware import security, get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Get Dashboard Statistics",
    description="Get aggregated statistics for the dashboard including project counts, client counts, revenue, and recent projects.",
    responses={
        200: {"description": "Dashboard statistics retrieved successfully"},
        401: {"description": "Not authenticated"}
    }
)
async def get_dashboard_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get dashboard statistics and analytics.
    
    Aggregates and returns key metrics for the authenticated user including:
    - Total number of projects
    - Number of active projects
    - Number of completed projects
    - Total number of clients
    - Total revenue from all projects
    - List of recent projects
    
    Args:
        credentials: HTTP authorization credentials from the request
        
    Returns:
        DashboardStats: Aggregated dashboard statistics
        
    Raises:
        HTTPException: If retrieval fails or user not authenticated
    """
    user = await get_current_user(credentials)

    try:
        supabase = get_supabase_client()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase is not configured/available: {str(e)}",
        )
    
    try:
        # Get all projects for the user
        projects_response = supabase.table("projects").select("*").eq("user_id", user["id"]).execute()
        projects = projects_response.data
        
        # Get all clients for the user
        clients_response = supabase.table("clients").select("*").eq("user_id", user["id"]).execute()
        clients = clients_response.data
        
        # Calculate statistics
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.get("status") == "active"])
        completed_projects = len([p for p in projects if p.get("status") == "completed"])
        total_clients = len(clients)
        
        # Calculate total revenue
        total_revenue = sum(float(p.get("budget", 0) or 0) for p in projects)
        
        # Get recent projects (last 5)
        recent_projects = sorted(
            projects,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )[:5]
        
        recent_projects_list = [Project(**p) for p in recent_projects]
        
        return DashboardStats(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            total_clients=total_clients,
            total_revenue=total_revenue,
            recent_projects=recent_projects_list
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard statistics: {str(e)}"
        )
