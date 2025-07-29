"""
Settings configuration for Vertex AI project.
Uses Pydantic for environment variable validation.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google Cloud Configuration
    google_cloud_project_id: str = Field(..., env="GOOGLE_CLOUD_PROJECT_ID")
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # Vertex AI Configuration
    vertex_ai_location: str = Field(default="us-central1", env="VERTEX_AI_LOCATION")
    vertex_ai_model_name: str = Field(default="gemini-1.5-pro", env="VERTEX_AI_MODEL_NAME")
    
    # Agent Space Configuration
    agent_space_id: Optional[str] = Field(None, env="AGENT_SPACE_ID")
    agent_space_location: str = Field(default="us-central1", env="AGENT_SPACE_LOCATION")
    
    # Search Configuration
    search_engine_id: Optional[str] = Field(None, env="SEARCH_ENGINE_ID")
    
    # Workspace Configuration
    workspace_domain: Optional[str] = Field(None, env="WORKSPACE_DOMAIN")
    gmail_credentials_path: Optional[str] = Field(None, env="GMAIL_CREDENTIALS_PATH")
    
    # Development Settings
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Gemini API Key
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 