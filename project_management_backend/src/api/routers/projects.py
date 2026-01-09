"""
Projects router for project CRUD operations.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import List
from src.api.schemas import Project, ProjectCreate, ProjectUpdate
from src.api.config import supabase
from src.api.middleware import security, get_current_user
from datetime import datetime

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
    summary="Create Project",
    description="Create a new project for the authenticated user.",
    responses={
        201: {"description": "Project created successfully"},
        401: {"description": "Not authenticated"},
        400: {"description": "Invalid request data"}
    }
)
async def create_project(
    project_data: ProjectCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new project.
    
    Creates a new project associated with the authenticated user.
    
    Args:
        project_data: ProjectCreate containing project details
        credentials: HTTP authorization credentials from the request
        
    Returns:
        Project: Created project information
        
    Raises:
        HTTPException: If creation fails or user not authenticated
    """
    user = await get_current_user(credentials)
    
    try:
        # Prepare project data
        new_project = project_data.model_dump()
        new_project["user_id"] = user["id"]
        new_project["created_at"] = datetime.utcnow().isoformat()
        new_project["updated_at"] = datetime.utcnow().isoformat()
        
        # Insert project
        response = supabase.table("projects").insert(new_project).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create project"
            )
        
        created_project = response.data[0]
        return Project(**created_project)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get(
    "",
    response_model=List[Project],
    summary="List Projects",
    description="Get all projects for the authenticated user.",
    responses={
        200: {"description": "Projects retrieved successfully"},
        401: {"description": "Not authenticated"}
    }
)
async def list_projects(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get all projects for the current user.
    
    Retrieves a list of all projects owned by the authenticated user.
    
    Args:
        credentials: HTTP authorization credentials from the request
        
    Returns:
        List[Project]: List of projects
        
    Raises:
        HTTPException: If retrieval fails or user not authenticated
    """
    user = await get_current_user(credentials)
    
    try:
        response = supabase.table("projects").select("*").eq("user_id", user["id"]).execute()
        
        projects = [Project(**project) for project in response.data]
        return projects
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}"
        )


@router.get(
    "/{project_id}",
    response_model=Project,
    summary="Get Project",
    description="Get a specific project by ID.",
    responses={
        200: {"description": "Project retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Project not found"}
    }
)
async def get_project(
    project_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get a specific project by ID.
    
    Retrieves detailed information about a project. User must be
    the owner of the project.
    
    Args:
        project_id: Project unique identifier
        credentials: HTTP authorization credentials from the request
        
    Returns:
        Project: Project information
        
    Raises:
        HTTPException: If project not found or user not authorized
    """
    user = await get_current_user(credentials)
    
    try:
        response = supabase.table("projects").select("*").eq("id", project_id).eq("user_id", user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        return Project(**project)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project: {str(e)}"
        )


@router.put(
    "/{project_id}",
    response_model=Project,
    summary="Update Project",
    description="Update a specific project by ID.",
    responses={
        200: {"description": "Project updated successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Project not found"}
    }
)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a specific project.
    
    Updates project information. User must be the owner of the project.
    Only provided fields will be updated.
    
    Args:
        project_id: Project unique identifier
        project_update: ProjectUpdate containing fields to update
        credentials: HTTP authorization credentials from the request
        
    Returns:
        Project: Updated project information
        
    Raises:
        HTTPException: If update fails or user not authorized
    """
    user = await get_current_user(credentials)
    
    try:
        # Prepare update data
        update_data = project_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update project
        response = supabase.table("projects").update(update_data).eq("id", project_id).eq("user_id", user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        updated_project = response.data[0]
        return Project(**updated_project)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Project",
    description="Delete a specific project by ID.",
    responses={
        204: {"description": "Project deleted successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Project not found"}
    }
)
async def delete_project(
    project_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a specific project.
    
    Permanently deletes a project. User must be the owner of the project.
    This action cannot be undone.
    
    Args:
        project_id: Project unique identifier
        credentials: HTTP authorization credentials from the request
        
    Raises:
        HTTPException: If deletion fails or user not authorized
    """
    user = await get_current_user(credentials)
    
    try:
        response = supabase.table("projects").delete().eq("id", project_id).eq("user_id", user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )
