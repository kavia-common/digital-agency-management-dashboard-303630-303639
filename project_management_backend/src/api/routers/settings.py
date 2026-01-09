"""
Settings router for user preferences and data export.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from src.api.schemas import UserSettings, ThemePreference, DataExportResponse
from src.api.config import get_supabase_client
from src.api.middleware import security, get_current_user
from datetime import datetime

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get(
    "",
    response_model=UserSettings,
    summary="Get User Settings",
    description="Get settings for the authenticated user.",
    responses={
        200: {"description": "User settings retrieved successfully"},
        401: {"description": "Not authenticated"}
    }
)
async def get_settings(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get user settings.
    
    Retrieves settings for the authenticated user. If settings don't exist,
    creates default settings.
    
    Args:
        credentials: HTTP authorization credentials from the request
        
    Returns:
        UserSettings: User settings
        
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
        # Try to get existing settings
        response = supabase.table("user_settings").select("*").eq("user_id", user["id"]).execute()
        
        if response.data:
            settings = response.data[0]
            return UserSettings(**settings)
        
        # Create default settings if none exist
        default_settings = {
            "user_id": user["id"],
            "theme": "light",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        create_response = supabase.table("user_settings").insert(default_settings).execute()
        
        if not create_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create default settings"
            )
        
        created_settings = create_response.data[0]
        return UserSettings(**created_settings)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve settings: {str(e)}"
        )


@router.put(
    "/theme",
    response_model=UserSettings,
    summary="Update Theme Preference",
    description="Update theme preference for the authenticated user.",
    responses={
        200: {"description": "Theme preference updated successfully"},
        401: {"description": "Not authenticated"}
    }
)
async def update_theme(
    theme_data: ThemePreference,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update user theme preference.
    
    Updates the theme setting for the authenticated user (light or dark mode).
    
    Args:
        theme_data: ThemePreference containing theme value
        credentials: HTTP authorization credentials from the request
        
    Returns:
        UserSettings: Updated user settings
        
    Raises:
        HTTPException: If update fails or user not authenticated
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
        update_data = {
            "theme": theme_data.theme,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Update theme
        response = supabase.table("user_settings").update(update_data).eq("user_id", user["id"]).execute()
        
        if not response.data:
            # Settings don't exist, create them
            default_settings = {
                "user_id": user["id"],
                "theme": theme_data.theme,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            create_response = supabase.table("user_settings").insert(default_settings).execute()
            
            if not create_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update theme preference"
                )
            
            updated_settings = create_response.data[0]
        else:
            updated_settings = response.data[0]
        
        return UserSettings(**updated_settings)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update theme preference: {str(e)}"
        )


@router.get(
    "/export",
    response_model=DataExportResponse,
    summary="Export User Data",
    description="Export all user data including projects and clients in JSON format.",
    responses={
        200: {"description": "Data exported successfully"},
        401: {"description": "Not authenticated"}
    }
)
async def export_data(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Export all user data.
    
    Exports all data associated with the authenticated user including
    projects, clients, and profile information in JSON format.
    
    Args:
        credentials: HTTP authorization credentials from the request
        
    Returns:
        DataExportResponse: Exported data in JSON format
        
    Raises:
        HTTPException: If export fails or user not authenticated
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
        # Get user profile
        profile_response = supabase.table("user_profiles").select("*").eq("id", user["id"]).execute()
        profile = profile_response.data[0] if profile_response.data else {}
        
        # Get all projects
        projects_response = supabase.table("projects").select("*").eq("user_id", user["id"]).execute()
        projects = projects_response.data
        
        # Get all clients
        clients_response = supabase.table("clients").select("*").eq("user_id", user["id"]).execute()
        clients = clients_response.data
        
        # Get settings
        settings_response = supabase.table("user_settings").select("*").eq("user_id", user["id"]).execute()
        settings = settings_response.data[0] if settings_response.data else {}
        
        # Compile export data
        export_data = {
            "profile": profile,
            "projects": projects,
            "clients": clients,
            "settings": settings,
            "exported_at": datetime.utcnow().isoformat()
        }
        
        return DataExportResponse(
            message="Data exported successfully",
            data=export_data
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )
