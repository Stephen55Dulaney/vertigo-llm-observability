"""
Base adapter class for integrating Vertigo components with Scenario framework.
Provides common functionality for logging, error handling, and metrics collection.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

class BaseVertigoAdapter(ABC):
    """
    Base class for all Vertigo agent adapters.
    Provides common functionality and interface for Scenario integration.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base adapter.
        
        Args:
            name: Human-readable name for this adapter
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"vertigo.scenario.{name}")
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0
        }
        
        self.logger.info(f"Initialized {self.name} adapter")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data through the Vertigo component.
        
        Args:
            input_data: Input data specific to the component
            
        Returns:
            Dict containing response data and metadata
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate that input data is properly formatted for this adapter.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    async def execute_with_metrics(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the adapter with automatic metrics collection.
        
        Args:
            input_data: Input data for processing
            
        Returns:
            Dict containing response data, metadata, and metrics
        """
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        try:
            # Validate input
            if not self.validate_input(input_data):
                raise ValueError(f"Invalid input data for {self.name}")
            
            # Log the request
            self.logger.info(f"Processing request with {self.name}")
            self.logger.debug(f"Input data: {input_data}")
            
            # Process the request
            result = await self.process(input_data)
            
            # Record success
            self.metrics["successful_requests"] += 1
            
            # Add metadata to result
            result["adapter_metadata"] = {
                "adapter_name": self.name,
                "processing_time": time.time() - start_time,
                "timestamp": datetime.utcnow().isoformat(),
                "success": True
            }
            
            self.logger.info(f"Successfully processed request with {self.name}")
            return result
            
        except Exception as e:
            # Record failure
            self.metrics["failed_requests"] += 1
            
            error_result = {
                "error": str(e),
                "error_type": type(e).__name__,
                "adapter_metadata": {
                    "adapter_name": self.name,
                    "processing_time": time.time() - start_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": False
                }
            }
            
            self.logger.error(f"Error in {self.name}: {e}")
            return error_result
            
        finally:
            # Update timing metrics
            response_time = time.time() - start_time
            self.metrics["total_response_time"] += response_time
            self.metrics["average_response_time"] = (
                self.metrics["total_response_time"] / self.metrics["total_requests"]
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics for this adapter.
        
        Returns:
            Dict containing performance metrics
        """
        success_rate = 0.0
        if self.metrics["total_requests"] > 0:
            success_rate = self.metrics["successful_requests"] / self.metrics["total_requests"]
        
        return {
            "adapter_name": self.name,
            "total_requests": self.metrics["total_requests"],
            "successful_requests": self.metrics["successful_requests"],
            "failed_requests": self.metrics["failed_requests"],
            "success_rate": success_rate,
            "average_response_time": self.metrics["average_response_time"]
        }
    
    def reset_metrics(self):
        """Reset all metrics to zero."""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0
        }
        self.logger.info(f"Reset metrics for {self.name}")
    
    def configure(self, config: Dict[str, Any]):
        """
        Update adapter configuration.
        
        Args:
            config: New configuration dictionary
        """
        self.config.update(config)
        self.logger.info(f"Updated configuration for {self.name}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check for this adapter.
        
        Returns:
            Dict containing health status information
        """
        return {
            "adapter_name": self.name,
            "status": "healthy",
            "config_loaded": bool(self.config),
            "metrics": self.get_metrics()
        }