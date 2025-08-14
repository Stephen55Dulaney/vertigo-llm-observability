"""
Centralized error handling and message management for consistent UX.
"""

from flask import flash
from typing import Dict, List, Optional
from enum import Enum

class MessageType(Enum):
    """Standard message types for consistent UI."""
    SUCCESS = "success"
    ERROR = "error" 
    WARNING = "warning"
    INFO = "info"

class ErrorManager:
    """Centralized error handling to prevent duplicate messages and ensure consistent UX."""
    
    def __init__(self):
        self._active_messages = set()
    
    def add_message(self, message: str, message_type: MessageType, unique_key: Optional[str] = None) -> bool:
        """
        Add a message with duplication prevention.
        
        Args:
            message: The message text
            message_type: Type of message (success, error, warning, info)
            unique_key: Optional key to prevent duplicate messages
            
        Returns:
            bool: True if message was added, False if duplicate was prevented
        """
        # Use message itself as key if no unique key provided
        key = unique_key or f"{message_type.value}:{message}"
        
        if key in self._active_messages:
            return False
            
        self._active_messages.add(key)
        flash(message, message_type.value)
        return True
    
    def clear_messages(self):
        """Clear the tracking of active messages."""
        self._active_messages.clear()
    
    def format_prompt_variable_error(self, missing_var: str, context: str = "prompt template") -> str:
        """Generate consistent error message for missing prompt variables."""
        return f"Missing required variable '{missing_var}' in {context}. Please update the template or provide the required data."
    
    def format_api_error(self, service: str, error_details: str) -> str:
        """Generate consistent error message for API failures."""
        return f"{service} API error: {error_details}"
    
    def format_validation_error(self, field: str, issue: str) -> str:
        """Generate consistent validation error messages."""
        return f"Validation failed for {field}: {issue}"

# Global instance for use across the application
error_manager = ErrorManager()

class PromptTestingErrors:
    """Specific error messages for prompt testing workflow."""
    
    @staticmethod
    def missing_variable(var_name: str) -> str:
        return f"Prompt template requires variable '{var_name}' which is not available. Please update the prompt template to remove this variable or ensure it's provided in the test data."
    
    @staticmethod
    def llm_api_failure(error_details: str) -> str:
        return f"Failed to generate response from AI model: {error_details}"
    
    @staticmethod
    def template_format_error(details: str) -> str:
        return f"Prompt template formatting error: {details}"
    
    @staticmethod
    def placeholder_info(variables: List[str]) -> str:
        var_list = ', '.join(variables)
        return f"Prompt template uses variables ({var_list}) that will be replaced with actual values during testing."