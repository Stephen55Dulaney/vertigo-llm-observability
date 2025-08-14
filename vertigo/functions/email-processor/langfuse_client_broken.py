"""
Langfuse client for Cloud Functions observability.
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
            # Use the correct project ID from main.py
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
        """Create a new trace."""
        if not self.is_enabled():
            logger.debug("Langfuse not enabled, skipping trace creation")
            return ""
        
        try:
            trace_id = self._langfuse.create_trace_id()
            self._langfuse.update_current_trace(
                name=name,
                metadata=metadata or {},
                user_id=user_id,
                session_id=session_id
            )
            logger.info(f"Created trace: {name} with ID: {trace_id}")
            return trace_id
        except Exception as e:
            logger.error(f"Error creating trace {name}: {e}")
            return ""
    
    def create_span(self, trace_id: str, name: str, metadata: Optional[Dict] = None) -> str:
        """Create a span within a trace."""
        if not self.is_enabled():
            return ""
        
        try:
            span = self._langfuse.start_span(
                name=name,
                metadata=metadata or {}
            )
            logger.info(f"Created span: {name} with ID: {span.id}")
            return span.id
        except Exception as e:
            logger.error(f"Error creating span {name}: {e}")
            return ""
    
    def create_generation(self, trace_id: str, name: str, model: str, 
                         input_data: Any, output_data: Any, 
                         metadata: Optional[Dict] = None,
                         usage: Optional[Dict] = None) -> str:
        """Create a generation (LLM call) within a trace."""
        if not self.is_enabled():
            return ""
        
        try:
            generation = self._langfuse.start_generation(
                name=name,
                model=model,
                input=input_data,
                metadata=metadata or {},
                usage=usage
            )
            self._langfuse.update_current_generation(
                output=output_data
            )
            logger.info(f"Created generation: {name} with model {model} (ID: {generation.id})")
            return generation.id
        except Exception as e:
            logger.error(f"Error creating generation {name}: {e}")
            return ""
    
    def update_trace(self, trace_id: str, metadata: Optional[Dict] = None, 
                    output: Optional[Any] = None, level: str = "DEFAULT") -> bool:
        """Update a trace with additional information."""
        if not self.is_enabled():
            return False
        
        try:
            # Use update_current_trace since we don't have a trace() method
            self._langfuse.update_current_trace(
                metadata=metadata or {},
                output=output,
                level=level
            )
            logger.info(f"Updated trace {trace_id} successfully")
            return True
        except Exception as e:
            logger.error(f"Error updating trace {trace_id}: {e}")
            return False
    
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