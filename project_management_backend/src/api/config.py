"""
Configuration module for loading environment variables and initializing services.
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BACKEND_URL = os.getenv("BACKEND_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")
SITE_URL = os.getenv("SITE_URL")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Validate required environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

# PUBLIC_INTERFACE
def get_supabase_client() -> Client:
    """
    Get Supabase client instance.
    
    Returns:
        Client: Supabase client for database and auth operations
    """
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Supabase client
supabase: Client = get_supabase_client()
