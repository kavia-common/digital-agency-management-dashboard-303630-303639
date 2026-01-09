"""
Configuration module for loading environment variables and initializing services.
"""
import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
SITE_URL = os.getenv("SITE_URL", FRONTEND_URL)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Validate required environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("CRITICAL: SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    logger.warning("The API will start but authentication and database operations will fail")
    # Set to None to allow app to start with degraded functionality
    supabase: Optional[Client] = None
else:
    # PUBLIC_INTERFACE
    def get_supabase_client() -> Client:
        """
        Get Supabase client instance.
        
        Returns:
            Client: Supabase client for database and auth operations
            
        Raises:
            ValueError: If Supabase credentials are not configured
        """
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        return create_client(SUPABASE_URL, SUPABASE_KEY)

    # Initialize Supabase client
    try:
        supabase: Client = get_supabase_client()
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        supabase = None
