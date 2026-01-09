"""
Authentication router for user signup, login, logout, and password reset.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from src.api.schemas import (
    SignupRequest, LoginRequest, PasswordResetRequest, 
    AuthResponse, MessageResponse
)
from src.api.config import supabase, SITE_URL
from src.api.middleware import security, get_current_user
import jwt
from datetime import datetime, timedelta
from src.api.config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentication"])


# PUBLIC_INTERFACE
def create_access_token(data: dict) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Dictionary containing token payload data
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Signup",
    description="Register a new user with email and password. Creates user profile in Supabase Auth.",
    responses={
        201: {"description": "User successfully created"},
        400: {"description": "Invalid request data or user already exists"}
    }
)
async def signup(user_data: SignupRequest):
    """
    Register a new user.
    
    Creates a new user account in Supabase Auth with email and password.
    Also creates a user profile record with the provided full name.
    
    Args:
        user_data: SignupRequest containing email, password, and full name
        
    Returns:
        AuthResponse: Access token and user information
        
    Raises:
        HTTPException: If signup fails or user already exists
    """
    try:
        # Sign up user with Supabase Auth
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name
                },
                "email_redirect_to": SITE_URL
            }
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        
        # Create user profile in database
        profile_data = {
            "id": response.user.id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("user_profiles").insert(profile_data).execute()
        
        # Create access token
        access_token = response.session.access_token if response.session else create_access_token(
            data={"sub": response.user.id, "email": response.user.email}
        )
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": response.user.id,
                "email": response.user.email,
                "full_name": user_data.full_name
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {str(e)}"
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="User Login",
    description="Authenticate user with email and password. Returns JWT access token.",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"}
    }
)
async def login(credentials: LoginRequest):
    """
    Authenticate user and return access token.
    
    Validates user credentials against Supabase Auth and returns
    a JWT access token for subsequent authenticated requests.
    
    Args:
        credentials: LoginRequest containing email and password
        
    Returns:
        AuthResponse: Access token and user information
        
    Raises:
        HTTPException: If login fails or credentials are invalid
    """
    try:
        # Sign in with Supabase Auth
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Get user profile
        profile_response = supabase.table("user_profiles").select("*").eq("id", response.user.id).execute()
        profile = profile_response.data[0] if profile_response.data else {}
        
        return AuthResponse(
            access_token=response.session.access_token,
            token_type="bearer",
            user={
                "id": response.user.id,
                "email": response.user.email,
                "full_name": profile.get("full_name", "")
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User Logout",
    description="Log out the current user and invalidate their session.",
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Not authenticated"}
    }
)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Log out the current user.
    
    Invalidates the user's session in Supabase Auth.
    
    Args:
        credentials: HTTP authorization credentials from the request
        
    Returns:
        MessageResponse: Confirmation message
        
    Raises:
        HTTPException: If logout fails
    """
    try:
        # Verify user is authenticated
        await get_current_user(credentials)
        
        # Sign out from Supabase
        supabase.auth.sign_out()
        
        return MessageResponse(message="Logged out successfully")
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}"
        )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Request Password Reset",
    description="Send password reset email to user. User will receive an email with reset instructions.",
    responses={
        200: {"description": "Password reset email sent"},
        400: {"description": "Failed to send reset email"}
    }
)
async def reset_password(reset_data: PasswordResetRequest):
    """
    Send password reset email to user.
    
    Triggers Supabase Auth password reset flow. User will receive
    an email with a link to reset their password.
    
    Args:
        reset_data: PasswordResetRequest containing user email
        
    Returns:
        MessageResponse: Confirmation message
        
    Raises:
        HTTPException: If password reset request fails
    """
    try:
        # Request password reset from Supabase
        supabase.auth.reset_password_email(
            reset_data.email,
            options={"redirect_to": f"{SITE_URL}/reset-password"}
        )
        
        return MessageResponse(
            message="If the email exists, a password reset link has been sent"
        )
    
    except Exception:
        # Don't reveal if email exists or not for security
        return MessageResponse(
            message="If the email exists, a password reset link has been sent"
        )


@router.get(
    "/me",
    response_model=dict,
    summary="Get Current User",
    description="Get information about the currently authenticated user.",
    responses={
        200: {"description": "User information retrieved"},
        401: {"description": "Not authenticated"}
    }
)
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current authenticated user information.
    
    Returns information about the user associated with the provided
    JWT access token.
    
    Args:
        credentials: HTTP authorization credentials from the request
        
    Returns:
        dict: Current user information
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user = await get_current_user(credentials)
    return user
