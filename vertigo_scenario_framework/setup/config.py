"""
Configuration management for Vertigo Scenario Framework
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

class VertigoScenarioConfig:
    """Central configuration for the Scenario framework."""
    
    def __init__(self):
        self.vertigo_root = Path(__file__).parent.parent.parent
        self.framework_root = self.vertigo_root / "vertigo_scenario_framework"
        
        # Langfuse configuration
        self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY") 
        self.langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        # Google Cloud configuration
        self.google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        # Vertigo paths
        self.email_parser_path = self.vertigo_root / "email_command_parser.py"
        self.debug_toolkit_path = self.vertigo_root / "vertigo-debug-toolkit"
        self.functions_path = self.vertigo_root / "vertigo" / "functions"
        
        # Test configuration
        self.run_integration_tests = os.getenv("RUN_INTEGRATION_TESTS", "true").lower() == "true"
        self.mock_external_services = os.getenv("MOCK_EXTERNAL_SERVICES", "false").lower() == "true"
    
    def validate(self) -> Dict[str, bool]:
        """Validate configuration and return status."""
        return {
            "langfuse_configured": bool(self.langfuse_public_key and self.langfuse_secret_key),
            "google_cloud_configured": bool(self.google_cloud_project),
            "vertigo_paths_exist": all([
                self.email_parser_path.exists(),
                self.debug_toolkit_path.exists(),
                self.functions_path.exists()
            ])
        }
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary for use in adapters."""
        return {
            "langfuse": {
                "public_key": self.langfuse_public_key,
                "secret_key": self.langfuse_secret_key,
                "host": self.langfuse_host
            },
            "google_cloud": {
                "project": self.google_cloud_project
            },
            "paths": {
                "vertigo_root": str(self.vertigo_root),
                "framework_root": str(self.framework_root),
                "email_parser": str(self.email_parser_path),
                "debug_toolkit": str(self.debug_toolkit_path),
                "functions": str(self.functions_path)
            },
            "testing": {
                "run_integration_tests": self.run_integration_tests,
                "mock_external_services": self.mock_external_services
            }
        }

# Global configuration instance
config = VertigoScenarioConfig()
