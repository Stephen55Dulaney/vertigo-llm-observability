"""
Input validation utilities for the Vertigo Debug Toolkit.
"""

import re
import json
import bleach
from markupsafe import Markup
from wtforms import ValidationError


class InputValidator:
    """Centralized input validation and sanitization."""
    
    # HTML tags and attributes allowed for rich text content
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'code', 'pre']
    ALLOWED_ATTRIBUTES = {}
    
    @staticmethod
    def sanitize_html(content):
        """Sanitize HTML content to prevent XSS."""
        if not content:
            return ""
        
        # Clean HTML with bleach
        clean_content = bleach.clean(
            content,
            tags=InputValidator.ALLOWED_TAGS,
            attributes=InputValidator.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return clean_content
    
    @staticmethod
    def validate_email(email):
        """Validate email format."""
        if not email:
            raise ValidationError("Email is required")
        
        # RFC 5322 compliant email regex (simplified)
        pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")
        
        if len(email) > 254:  # RFC 5321 limit
            raise ValidationError("Email address too long")
        
        return email.lower().strip()
    
    @staticmethod
    def validate_username(username):
        """Validate username format."""
        if not username:
            raise ValidationError("Username is required")
        
        username = username.strip()
        
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long")
        
        if len(username) > 64:
            raise ValidationError("Username must be less than 64 characters")
        
        # Allow letters, numbers, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, underscores, and hyphens")
        
        return username
    
    @staticmethod
    def validate_prompt_name(name):
        """Validate prompt name."""
        if not name:
            raise ValidationError("Prompt name is required")
        
        name = name.strip()
        
        if len(name) < 1:
            raise ValidationError("Prompt name cannot be empty")
        
        if len(name) > 100:
            raise ValidationError("Prompt name must be less than 100 characters")
        
        # Sanitize potential HTML/script content
        sanitized_name = InputValidator.sanitize_html(name)
        
        return sanitized_name
    
    @staticmethod
    def validate_prompt_content(content):
        """Validate and sanitize prompt content."""
        if not content:
            raise ValidationError("Prompt content is required")
        
        content = content.strip()
        
        if len(content) < 10:
            raise ValidationError("Prompt content must be at least 10 characters")
        
        if len(content) > 50000:  # 50KB limit
            raise ValidationError("Prompt content is too large (max 50KB)")
        
        # Don't sanitize prompt content as it may contain template variables
        # But check for potential malicious patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',  # event handlers
            r'data:text/html',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                raise ValidationError("Prompt content contains potentially dangerous patterns")
        
        return content
    
    @staticmethod
    def validate_json(json_str):
        """Validate and parse JSON content."""
        if not json_str:
            return None
        
        try:
            # Limit JSON size
            if len(json_str) > 10000:  # 10KB limit
                raise ValidationError("JSON content is too large")
            
            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {str(e)}")
    
    @staticmethod
    def validate_version(version):
        """Validate version string."""
        if not version:
            raise ValidationError("Version is required")
        
        version = version.strip()
        
        # Simple semantic version pattern
        if not re.match(r'^\d+\.\d+(\.\d+)?$', version):
            raise ValidationError("Version must be in format X.Y or X.Y.Z")
        
        return version
    
    @staticmethod
    def validate_prompt_type(prompt_type):
        """Validate prompt type."""
        if not prompt_type:
            raise ValidationError("Prompt type is required")
        
        valid_types = [
            'meeting_analysis',
            'daily_summary', 
            'technical_focus',
            'executive_summary',
            'action_oriented',
            'risk_assessment',
            'custom'
        ]
        
        if prompt_type not in valid_types:
            raise ValidationError(f"Invalid prompt type. Must be one of: {', '.join(valid_types)}")
        
        return prompt_type
    
    @staticmethod
    def sanitize_search_query(query):
        """Sanitize search query to prevent injection attacks."""
        if not query:
            return ""
        
        query = query.strip()
        
        # Limit query length
        if len(query) > 500:
            query = query[:500]
        
        # Remove potentially dangerous characters for SQL/NoSQL injection
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
        
        for char in dangerous_chars:
            query = query.replace(char, '')
        
        # Sanitize HTML
        query = InputValidator.sanitize_html(query)
        
        return query
    
    @staticmethod
    def validate_id_parameter(id_param):
        """Validate ID parameters (e.g., prompt_id, user_id)."""
        if not id_param:
            raise ValidationError("ID parameter is required")
        
        try:
            id_value = int(id_param)
            if id_value <= 0:
                raise ValidationError("ID must be a positive integer")
            return id_value
        except (ValueError, TypeError):
            raise ValidationError("ID must be a valid integer")


def length_validator(min_length=None, max_length=None):
    """Factory for length validation."""
    def validator(form, field):
        if field.data:
            length = len(field.data)
            if min_length and length < min_length:
                raise ValidationError(f"Must be at least {min_length} characters long")
            if max_length and length > max_length:
                raise ValidationError(f"Must be no more than {max_length} characters long")
    return validator


def no_html_validator(form, field):
    """Validator to prevent HTML content."""
    if field.data:
        # Check for HTML tags
        if re.search(r'<[^>]+>', field.data):
            raise ValidationError("HTML tags are not allowed")


def safe_json_validator(form, field):
    """Validator for JSON fields."""
    if field.data:
        try:
            InputValidator.validate_json(field.data)
        except ValidationError as e:
            raise ValidationError(str(e))