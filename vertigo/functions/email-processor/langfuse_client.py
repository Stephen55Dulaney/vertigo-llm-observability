"""
Fixed Langfuse client for Cloud Functions observability.
"""

import os
import logging
from typing import Dict, Optional, Any
from langfuse import Langfuse
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

class CloudFunctionLangfuseClient:
    """Langfuse client optimized for Google Cloud Functions."""
    
    def __init__(self):
        """Initialize Langfuse client with credentials from Secret Manager."""
        self._langfuse = None
        self._initialize_client()
    
    def _get_secret(self, secret_name: str) -> str:
        """Retrieve a secret from Google Cloud Secret Manager."""
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/579831320777/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name}: {e}")
            return ""
    
    def _initialize_client(self):
        """Initialize the Langfuse client."""
        try:
            # Try to get credentials from Secret Manager first
            public_key = self._get_secret("langfuse-public-key")
            secret_key = self._get_secret("langfuse-secret-key")
            
            # Fallback to environment variables
            if not public_key:
                public_key = os.getenv('LANGFUSE_PUBLIC_KEY', '')
            if not secret_key:
                secret_key = os.getenv('LANGFUSE_SECRET_KEY', '')
            
            if public_key and secret_key:
                host = os.getenv('LANGFUSE_HOST', 'https://us.cloud.langfuse.com')
                self._langfuse = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host
                )
                logger.info(f"Langfuse client initialized with host: {host}")
            else:
                logger.warning("Langfuse credentials not found - tracing disabled")
                self._langfuse = None
                
        except Exception as e:
            logger.error(f"Error initializing Langfuse client: {e}")
            self._langfuse = None
    
    def is_enabled(self) -> bool:
        """Check if Langfuse client is properly initialized."""
        return self._langfuse is not None
    
    def create_trace(self, name: str, metadata: Optional[Dict] = None, 
                    user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """Create a new trace using the simple API."""
        if not self.is_enabled():
            logger.debug("Langfuse not enabled, skipping trace creation")
            return ""
        
        try:
            # Use simple event creation instead of complex trace management
            event = self._langfuse.create_event(
                name=name,
                metadata=metadata or {},
                user_id=user_id,
                session_id=session_id
            )
            logger.info(f"Created Langfuse event: {name}")
            return event
        except Exception as e:
            logger.error(f"Error creating trace {name}: {e}")
            return ""
    
    def log_generation(self, name: str, model: str, input_data: Any, output_data: Any, 
                      metadata: Optional[Dict] = None) -> str:
        """Log an LLM generation using the simple API."""
        if not self.is_enabled():
            return ""
        
        try:
            # Use simple event logging for LLM calls
            event = self._langfuse.create_event(
                name=f"generation_{name}",
                metadata={
                    "model": model,
                    "input": str(input_data)[:1000],  # Truncate long inputs
                    "output": str(output_data)[:1000] if output_data else "",
                    **(metadata or {})
                }
            )
            logger.info(f"Logged generation: {name} with model {model}")
            return event
        except Exception as e:
            logger.error(f"Error logging generation {name}: {e}")
            return ""
    
    def flush(self):
        """Flush pending traces to Langfuse."""
        if self.is_enabled():
            try:
                self._langfuse.flush()
                logger.debug("Flushed traces to Langfuse")
            except Exception as e:
                logger.error(f"Error flushing traces: {e}")

# Global instance for cloud functions
langfuse_client = CloudFunctionLangfuseClient()