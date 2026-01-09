"""
Users router for user profile CRUD operations.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from src.api.schemas import UserProfile, UserProfileUpdate
from src.api.config import supabase
from src.api.middleware import security, get_current_user
from datetime import datetime

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/profile",
    response_model=UserProfile,
    summary="Get User Profile",
    description="Get the profile of the currently authenticated user.",
    responses={
        200: {"description": "User profile retrieved"},
        401: {"description": "Not authenticated"},
        404: {"description": "Profile not found"}
    }
)
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user's profile.
    
    Retrieves the profile information for the authenticated user.
    
    Args:
        credentials: HTTP authorization credentials from the request
        
    Returns:
        UserProfile: User profile information
        
    Raises:
        HTTPException: If profile not found or user not authenticated
    """
    user = await get_current_user(credentials)
    
    try:
        response = supabase.table("user_profiles").select("*").eq("id", user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        profile = response.data[0]
        return UserProfile(**profile)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@router.put(
    "/profile",
    response_model=UserProfile,
    summary="Update User Profile",
    description="Update the profile of the currently authenticated user.",
    responses={
        200: {"description": "User profile updated"},
        401: {"description": "Not authenticated"},
        404: {"description": "Profile not found"}
    }
)
async def update_profile(
    profile_update: UserProfileUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update current user's profile.
    
    Updates profile information for the authenticated user.
    Only provided fields will be updated.
    
    Args:
        profile_update: UserProfileUpdate containing fields to update
        credentials: HTTP authorization credentials from the request
        
    Returns:
        UserProfile: Updated user profile
        
    Raises:
        HTTPException: If update fails or user not authenticated
    """
    user = await get_current_user(credentials)
    
    try:
        # Prepare update data
        update_data = profile_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update profile
        response = supabase.table("user_profiles").update(update_data).eq("id", user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        updated_profile = response.data[0]
        return UserProfile(**updated_profile)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.delete(
    "/profile",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User Profile",
    description="Delete the profile and account of the currently authenticated user.",
    responses={
        204: {"description": "User profile deleted"},
        401: {"description": "Not authenticated"}
    }
)
async def delete_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Delete current user's profile and account.
    
    Permanently deletes the user's profile and all associated data.
    This action cannot be undone.
    
    Args:
        credentials: HTTP authorization credentials from the request
        
    Raises:
        HTTPException: If deletion fails or user not authenticated
    """
    user = await get_current_user(credentials)
    
    try:
        # Delete user profile
        supabase.table("user_profiles").delete().eq("id", user["id"]).execute()
        
        # Note: Supabase Auth user deletion requires admin privileges
        # In production, this should be handled by an admin endpoint or background job
        
        return None
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )
