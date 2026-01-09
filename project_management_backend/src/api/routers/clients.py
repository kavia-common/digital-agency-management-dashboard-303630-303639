"""
Clients router for client CRUD operations.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import List
from src.api.schemas import Client, ClientCreate, ClientUpdate
from src.api.config import supabase
from src.api.middleware import security, get_current_user
from datetime import datetime

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post(
    "",
    response_model=Client,
    status_code=status.HTTP_201_CREATED,
    summary="Create Client",
    description="Create a new client for the authenticated user.",
    responses={
        201: {"description": "Client created successfully"},
        401: {"description": "Not authenticated"},
        400: {"description": "Invalid request data"}
    }
)
async def create_client(
    client_data: ClientCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new client.
    
    Creates a new client associated with the authenticated user.
    
    Args:
        client_data: ClientCreate containing client details
        credentials: HTTP authorization credentials from the request
        
    Returns:
        Client: Created client information
        
    Raises:
        HTTPException: If creation fails or user not authenticated
    """
    user = await get_current_user(credentials)
    
    try:
        # Prepare client data
        new_client = client_data.model_dump()
        new_client["user_id"] = user["id"]
        new_client["created_at"] = datetime.utcnow().isoformat()
        new_client["updated_at"] = datetime.utcnow().isoformat()
        
        # Insert client
        response = supabase.table("clients").insert(new_client).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create client"
            )
        
        created_client = response.data[0]
        return Client(**created_client)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client: {str(e)}"
        )


@router.get(
    "",
    response_model=List[Client],
    summary="List Clients",
    description="Get all clients for the authenticated user.",
    responses={
        200: {"description": "Clients retrieved successfully"},
        401: {"description": "Not authenticated"}
    }
)
async def list_clients(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get all clients for the current user.
    
    Retrieves a list of all clients owned by the authenticated user.
    
    Args:
        credentials: HTTP authorization credentials from the request
        
    Returns:
        List[Client]: List of clients
        
    Raises:
        HTTPException: If retrieval fails or user not authenticated
    """
    user = await get_current_user(credentials)
    
    try:
        response = supabase.table("clients").select("*").eq("user_id", user["id"]).execute()
        
        clients = [Client(**client) for client in response.data]
        return clients
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve clients: {str(e)}"
        )


@router.get(
    "/{client_id}",
    response_model=Client,
    summary="Get Client",
    description="Get a specific client by ID.",
    responses={
        200: {"description": "Client retrieved successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Client not found"}
    }
)
async def get_client(
    client_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get a specific client by ID.
    
    Retrieves detailed information about a client. User must be
    the owner of the client.
    
    Args:
        client_id: Client unique identifier
        credentials: HTTP authorization credentials from the request
        
    Returns:
        Client: Client information
        
    Raises:
        HTTPException: If client not found or user not authorized
    """
    user = await get_current_user(credentials)
    
    try:
        response = supabase.table("clients").select("*").eq("id", client_id).eq("user_id", user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        client = response.data[0]
        return Client(**client)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve client: {str(e)}"
        )


@router.put(
    "/{client_id}",
    response_model=Client,
    summary="Update Client",
    description="Update a specific client by ID.",
    responses={
        200: {"description": "Client updated successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Client not found"}
    }
)
async def update_client(
    client_id: str,
    client_update: ClientUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update a specific client.
    
    Updates client information. User must be the owner of the client.
    Only provided fields will be updated.
    
    Args:
        client_id: Client unique identifier
        client_update: ClientUpdate containing fields to update
        credentials: HTTP authorization credentials from the request
        
    Returns:
        Client: Updated client information
        
    Raises:
        HTTPException: If update fails or user not authorized
    """
    user = await get_current_user(credentials)
    
    try:
        # Prepare update data
        update_data = client_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update client
        response = supabase.table("clients").update(update_data).eq("id", client_id).eq("user_id", user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        updated_client = response.data[0]
        return Client(**updated_client)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client: {str(e)}"
        )


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Client",
    description="Delete a specific client by ID.",
    responses={
        204: {"description": "Client deleted successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Client not found"}
    }
)
async def delete_client(
    client_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Delete a specific client.
    
    Permanently deletes a client. User must be the owner of the client.
    This action cannot be undone.
    
    Args:
        client_id: Client unique identifier
        credentials: HTTP authorization credentials from the request
        
    Raises:
        HTTPException: If deletion fails or user not authorized
    """
    user = await get_current_user(credentials)
    
    try:
        response = supabase.table("clients").delete().eq("id", client_id).eq("user_id", user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete client: {str(e)}"
        )
