"""
Google Cloud authentication module.
Handles credential management and client initialization.
"""

import os
from typing import Optional
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import aiplatform
# from google.cloud import search  # REMOVED: No such package
from google.oauth2 import service_account
from .settings import settings


class GoogleCloudAuth:
    """Handles Google Cloud authentication and client initialization."""
    
    def __init__(self):
        self.credentials = None
        self.project_id = settings.google_cloud_project_id
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        """Initialize Google Cloud credentials."""
        try:
            # Try service account credentials first
            if settings.google_application_credentials:
                if os.path.exists(settings.google_application_credentials):
                    self.credentials = service_account.Credentials.from_service_account_file(
                        settings.google_application_credentials
                    )
                    print(f"✅ Using service account credentials from: {settings.google_application_credentials}")
                else:
                    print(f"⚠️  Service account file not found: {settings.google_application_credentials}")
            
            # Fall back to default credentials
            if not self.credentials:
                self.credentials, _ = default()
                print("✅ Using default Google Cloud credentials")
                
        except DefaultCredentialsError as e:
            print(f"❌ Failed to initialize credentials: {e}")
            print("Please run: gcloud auth application-default login")
            raise
    
    def get_vertex_ai_client(self):
        """Initialize Vertex AI client."""
        try:
            aiplatform.init(
                project=self.project_id,
                location=settings.vertex_ai_location,
                credentials=self.credentials
            )
            print(f"✅ Vertex AI client initialized for project: {self.project_id}")
            return aiplatform
        except Exception as e:
            print(f"❌ Failed to initialize Vertex AI client: {e}")
            raise
    
    # def get_search_client(self):
    #     """Initialize Search client."""
    #     try:
    #         client = search.SearchServiceClient(credentials=self.credentials)
    #         print("✅ Search client initialized")
    #         return client
    #     except Exception as e:
    #         print(f"❌ Failed to initialize Search client: {e}")
    #         raise
    
    def verify_credentials(self) -> bool:
        """Verify that credentials are valid."""
        try:
            # Test with a simple API call
            aiplatform.init(
                project=self.project_id,
                location=settings.vertex_ai_location,
                credentials=self.credentials
            )
            print("✅ Google Cloud credentials verified successfully")
            return True
        except Exception as e:
            print(f"❌ Credential verification failed: {e}")
            return False


# Global auth instance
auth = GoogleCloudAuth() 