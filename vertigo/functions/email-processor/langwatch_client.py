"""
Langwatch client for observability demo.
"""

import os
import logging
import requests
import json
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class LangwatchClient:
    """Langwatch client for LLM observability."""
    
    def __init__(self):
        """Initialize Langwatch client."""
        self.api_key = os.getenv('LANGWATCH_API_KEY', '')
        self.base_url = 'https://app.langwatch.ai/api'
        self.project_id = 'vertigo-llm-observability-3Jujjc'
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            logger.info("Langwatch client initialized successfully")
        else:
            logger.warning("Langwatch API key not found - tracing disabled")
    
    def is_enabled(self) -> bool:
        """Check if Langwatch client is enabled."""
        return self.enabled
    
    def create_trace(self, name: str, input_data: Any = None, metadata: Optional[Dict] = None) -> str:
        """Create a new trace in Langwatch."""
        if not self.is_enabled():
            return ""
        
        try:
            trace_data = {
                "project_id": self.project_id,
                "trace_id": f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name}",
                "name": name,
                "input": input_data if input_data else f"Processing {name}",
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
                "type": "trace"
            }
            
            response = requests.post(
                f"{self.base_url}/traces",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=trace_data
            )
            
            if response.status_code == 200:
                logger.info(f"Created Langwatch trace: {name}")
                return trace_data["trace_id"]
            else:
                logger.error(f"Failed to create trace: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"Error creating Langwatch trace {name}: {e}")
            return ""
    
    def log_llm_call(self, trace_id: str, model: str, input_data: Any, output_data: Any, 
                     metadata: Optional[Dict] = None) -> bool:
        """Log an LLM call to Langwatch."""
        if not self.is_enabled():
            return False
        
        try:
            llm_data = {
                "trace_id": trace_id,
                "model": model,
                "input": str(input_data)[:2000],  # Truncate long inputs
                "output": str(output_data)[:2000] if output_data else "",
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
                "type": "llm_call"
            }
            
            response = requests.post(
                f"{self.base_url}/llm_calls",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=llm_data
            )
            
            if response.status_code == 200:
                logger.info(f"Logged LLM call for trace {trace_id}")
                return True
            else:
                logger.error(f"Failed to log LLM call: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging LLM call for trace {trace_id}: {e}")
            return False
    
    def finish_trace(self, trace_id: str, output_data: Any = None, success: bool = True) -> bool:
        """Finish a trace in Langwatch."""
        if not self.is_enabled():
            return False
        
        try:
            finish_data = {
                "trace_id": trace_id,
                "output": str(output_data) if output_data else "Completed successfully",
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.patch(
                f"{self.base_url}/traces/{trace_id}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=finish_data
            )
            
            if response.status_code == 200:
                logger.info(f"Finished Langwatch trace: {trace_id}")
                return True
            else:
                logger.error(f"Failed to finish trace: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error finishing trace {trace_id}: {e}")
            return False

# Global instance
langwatch_client = LangwatchClient()