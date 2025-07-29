"""
Configuration module for Vertex AI project.
Handles Google Cloud authentication and project settings.
"""

from .settings import Settings
from .auth import GoogleCloudAuth

__all__ = ["Settings", "GoogleCloudAuth"] 