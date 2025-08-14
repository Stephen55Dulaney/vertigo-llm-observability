"""
Vertigo client service for the Vertigo Debug Toolkit.
"""

import os
import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class VertigoClient:
    """Client for interacting with Vertigo API."""
    
    def __init__(self):
        """Initialize Vertigo client."""
        self.api_url = os.getenv('VERTIGO_API_URL')
    
    def get_status(self) -> Dict[str, Any]:
        """Get Vertigo agent status."""
        try:
            response = requests.get(self.api_url, timeout=10)
            return {
                "status": "success",
                "response_code": response.status_code,
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            logger.error(f"Error getting Vertigo status: {e}")
            return {
                "status": "error",
                "error": str(e)
            } 