"""
Pydantic schemas for request and response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Auth schemas
class SignupRequest(BaseModel):
    """Schema for user signup request."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    full_name: str = Field(..., min_length=1, description="User full name")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "user@example.com",
            "password": "securepassword123",
            "full_name": "John Doe"
        }
    })


class LoginRequest(BaseModel):
    """Schema for user login request."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "user@example.com",
            "password": "securepassword123"
        }
    })


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr = Field(..., description="User email address for password reset")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "user@example.com"
        }
    })


class AuthResponse(BaseModel):
    """Schema for authentication response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: dict = Field(..., description="User information")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "user": {"id": "123", "email": "user@example.com", "full_name": "John Doe"}
        }
    })


# User schemas
class UserProfile(BaseModel):
    """Schema for user profile."""
    id: str = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "123",
            "email": "user@example.com",
            "full_name": "John Doe",
            "avatar_url": "https://example.com/avatar.jpg",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


class UserProfileUpdate(BaseModel):
    """Schema for user profile update."""
    full_name: Optional[str] = Field(None, description="User full name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "full_name": "John Doe Updated",
            "avatar_url": "https://example.com/new-avatar.jpg"
        }
    })


# Project schemas
class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    name: str = Field(..., min_length=1, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    client_id: Optional[str] = Field(None, description="Associated client ID")
    status: str = Field(default="active", description="Project status")
    budget: Optional[float] = Field(None, ge=0, description="Project budget")
    start_date: Optional[datetime] = Field(None, description="Project start date")
    end_date: Optional[datetime] = Field(None, description="Project end date")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Website Redesign",
            "description": "Complete redesign of company website",
            "client_id": "client-123",
            "status": "active",
            "budget": 50000.00,
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-06-30T00:00:00Z"
        }
    })


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    client_id: Optional[str] = Field(None, description="Associated client ID")
    status: Optional[str] = Field(None, description="Project status")
    budget: Optional[float] = Field(None, ge=0, description="Project budget")
    start_date: Optional[datetime] = Field(None, description="Project start date")
    end_date: Optional[datetime] = Field(None, description="Project end date")


class Project(BaseModel):
    """Schema for project response."""
    id: str = Field(..., description="Project unique identifier")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    client_id: Optional[str] = Field(None, description="Associated client ID")
    user_id: str = Field(..., description="Owner user ID")
    status: str = Field(..., description="Project status")
    budget: Optional[float] = Field(None, description="Project budget")
    start_date: Optional[datetime] = Field(None, description="Project start date")
    end_date: Optional[datetime] = Field(None, description="Project end date")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "proj-123",
            "name": "Website Redesign",
            "description": "Complete redesign of company website",
            "client_id": "client-123",
            "user_id": "user-123",
            "status": "active",
            "budget": 50000.00,
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-06-30T00:00:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


# Client schemas
class ClientCreate(BaseModel):
    """Schema for creating a client."""
    name: str = Field(..., min_length=1, description="Client name")
    email: Optional[EmailStr] = Field(None, description="Client email address")
    phone: Optional[str] = Field(None, description="Client phone number")
    company: Optional[str] = Field(None, description="Client company name")
    address: Optional[str] = Field(None, description="Client address")
    notes: Optional[str] = Field(None, description="Additional notes")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Acme Corporation",
            "email": "contact@acme.com",
            "phone": "+1-555-0100",
            "company": "Acme Corp",
            "address": "123 Main St, City, State 12345",
            "notes": "Preferred client, priority support"
        }
    })


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    name: Optional[str] = Field(None, min_length=1, description="Client name")
    email: Optional[EmailStr] = Field(None, description="Client email address")
    phone: Optional[str] = Field(None, description="Client phone number")
    company: Optional[str] = Field(None, description="Client company name")
    address: Optional[str] = Field(None, description="Client address")
    notes: Optional[str] = Field(None, description="Additional notes")


class Client(BaseModel):
    """Schema for client response."""
    id: str = Field(..., description="Client unique identifier")
    name: str = Field(..., description="Client name")
    email: Optional[str] = Field(None, description="Client email address")
    phone: Optional[str] = Field(None, description="Client phone number")
    company: Optional[str] = Field(None, description="Client company name")
    address: Optional[str] = Field(None, description="Client address")
    notes: Optional[str] = Field(None, description="Additional notes")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "client-123",
            "name": "Acme Corporation",
            "email": "contact@acme.com",
            "phone": "+1-555-0100",
            "company": "Acme Corp",
            "address": "123 Main St, City, State 12345",
            "notes": "Preferred client",
            "user_id": "user-123",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


# Dashboard schemas
class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total_projects: int = Field(..., description="Total number of projects")
    active_projects: int = Field(..., description="Number of active projects")
    completed_projects: int = Field(..., description="Number of completed projects")
    total_clients: int = Field(..., description="Total number of clients")
    total_revenue: float = Field(..., description="Total revenue from all projects")
    recent_projects: List[Project] = Field(default=[], description="List of recent projects")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_projects": 25,
            "active_projects": 10,
            "completed_projects": 15,
            "total_clients": 18,
            "total_revenue": 500000.00,
            "recent_projects": []
        }
    })


# Settings schemas
class ThemePreference(BaseModel):
    """Schema for theme preference."""
    theme: str = Field(..., description="Theme preference (light or dark)")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "theme": "light"
        }
    })


class UserSettings(BaseModel):
    """Schema for user settings."""
    id: str = Field(..., description="Settings unique identifier")
    user_id: str = Field(..., description="Owner user ID")
    theme: str = Field(default="light", description="Theme preference")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "settings-123",
            "user_id": "user-123",
            "theme": "light",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    })


class DataExportResponse(BaseModel):
    """Schema for data export response."""
    message: str = Field(..., description="Export status message")
    data: dict = Field(..., description="Exported data")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message": "Data exported successfully",
            "data": {
                "projects": [],
                "clients": []
            }
        }
    })


# Generic response schemas
class MessageResponse(BaseModel):
    """Schema for generic message response."""
    message: str = Field(..., description="Response message")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message": "Operation completed successfully"
        }
    })


class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str = Field(..., description="Error detail message")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "detail": "An error occurred"
        }
    })
