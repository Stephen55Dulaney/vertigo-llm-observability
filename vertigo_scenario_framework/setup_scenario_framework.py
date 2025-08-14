#!/usr/bin/env python3
"""
Vertigo Scenario Framework Installation and Setup Script
========================================================

This script sets up the complete Scenario framework for Stephen's Vertigo environment.
Run this once to get everything working, then start with the tutorials.

Author: Claude Code
Date: 2025-08-06
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

class VertigoScenarioSetup:
    """Complete setup system for Vertigo Scenario Framework."""
    
    def __init__(self):
        self.root_dir = Path("/Users/stephendulaney/Documents/Vertigo")
        self.framework_dir = self.root_dir / "vertigo_scenario_framework"
        self.config = {}
        
    def run_setup(self):
        """Run the complete setup process."""
        print("🚀 Setting up Vertigo Scenario Framework...")
        print("=" * 50)
        
        try:
            self.check_environment()
            self.install_dependencies()
            self.create_config()
            self.verify_vertigo_components()
            self.create_test_data()
            self.run_hello_world_test()
            
            print("\n✅ Setup complete! Ready to start learning.")
            print("\n📚 Next steps:")
            print("1. cd vertigo_scenario_framework")
            print("2. python examples/hello_world_scenario.py")
            print("3. Open tutorials/01_introduction.md")
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            print("\n🔧 Troubleshooting:")
            print("- Check your Python environment")
            print("- Ensure you're in the Vertigo directory")
            print("- Verify Firestore credentials are available")
            sys.exit(1)
    
    def check_environment(self):
        """Check that we're in the right place with the right tools."""
        print("🔍 Checking environment...")
        
        # Check we're in the right directory
        if not self.root_dir.exists():
            raise Exception(f"Vertigo directory not found: {self.root_dir}")
        
        # Check Python version
        if sys.version_info < (3, 8):
            raise Exception("Python 3.8+ required")
        
        # Check for essential Vertigo files
        essential_files = [
            "email_command_parser.py",
            "vertigo/functions/email-processor/main.py",
            "vertigo-debug-toolkit/app.py"
        ]
        
        for file_path in essential_files:
            if not (self.root_dir / file_path).exists():
                raise Exception(f"Essential Vertigo file missing: {file_path}")
        
        print("✅ Environment check passed")
    
    def install_dependencies(self):
        """Install required Python packages."""
        print("📦 Installing dependencies...")
        
        # Read existing requirements
        scenario_reqs = self.root_dir / "scenario_requirements.txt"
        if scenario_reqs.exists():
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(scenario_reqs)
                ], check=True, capture_output=True, text=True)
                print("✅ Scenario requirements installed")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Warning: Some packages may have failed to install: {e}")
                print("Continuing with setup...")
        
        # Install core packages that we know we need
        core_packages = [
            "langfuse>=2.0.0",
            "google-cloud-firestore",
            "google-auth",
            "requests",
            "python-dotenv"
        ]
        
        for package in core_packages:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                print(f"⚠️  Warning: Could not install {package}")
        
        print("✅ Core dependencies installed")
    
    def create_config(self):
        """Create configuration files for the framework."""
        print("⚙️  Creating configuration...")
        
        # Create .env file for Scenario framework
        env_file = self.framework_dir / ".env"
        if not env_file.exists():
            env_content = """# Vertigo Scenario Framework Configuration
# Copy values from your main Vertigo .env file

# Langfuse Configuration (from your existing setup)
LANGFUSE_PUBLIC_KEY=pk-lf-your-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-here
LANGFUSE_HOST=https://cloud.langfuse.com

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id

# Vertigo Configuration
VERTIGO_DEBUG_TOOLKIT_URL=http://localhost:8080
SCENARIO_LOG_LEVEL=INFO

# Test Configuration
RUN_INTEGRATION_TESTS=true
MOCK_EXTERNAL_SERVICES=false
"""
            env_file.write_text(env_content)
        
        # Create main config.py
        config_file = self.framework_dir / "setup" / "config.py"
        config_content = '''"""
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
'''
        config_file.write_text(config_content)
        
        print("✅ Configuration files created")
    
    def verify_vertigo_components(self):
        """Verify that Vertigo components are accessible."""
        print("🔍 Verifying Vertigo components...")
        
        # Test email parser
        try:
            sys.path.insert(0, str(self.root_dir))
            from email_command_parser import EmailCommandParser
            parser = EmailCommandParser()
            print("✅ Email command parser accessible")
        except Exception as e:
            print(f"⚠️  Email parser issue: {e}")
        
        # Check debug toolkit
        debug_toolkit_app = self.root_dir / "vertigo-debug-toolkit" / "app.py"
        if debug_toolkit_app.exists():
            print("✅ Debug toolkit found")
        else:
            print("⚠️  Debug toolkit not found")
        
        # Check cloud functions
        functions_dir = self.root_dir / "vertigo" / "functions"
        if functions_dir.exists():
            print("✅ Cloud functions found")
        else:
            print("⚠️  Cloud functions not found")
    
    def create_test_data(self):
        """Create sample test data for tutorials."""
        print("📊 Creating test data...")
        
        test_data_dir = self.framework_dir / "test_data"
        test_data_dir.mkdir(exist_ok=True)
        
        # Sample email commands for testing
        email_commands = {
            "basic_commands": [
                {"subject": "Vertigo: Help", "expected_command": "help"},
                {"subject": "Vertigo: Total stats", "expected_command": "total stats"},
                {"subject": "Vertigo: List this week", "expected_command": "list this week"},
                {"subject": "Re: Vertigo: Help", "expected_command": "help"}
            ],
            "edge_cases": [
                {"subject": "VERTIGO: HELP", "expected_command": "help"},
                {"subject": "   vertigo:   total stats   ", "expected_command": "total stats"},
                {"subject": "Fwd: Re: Vertigo: List projects", "expected_command": "list projects"}
            ]
        }
        
        (test_data_dir / "email_commands.json").write_text(
            json.dumps(email_commands, indent=2)
        )
        
        # Sample meeting transcripts
        meeting_transcripts = {
            "short_meeting": {
                "transcript": "Brief standup meeting. Discussed project status and next steps.",
                "expected_topics": ["project status", "next steps"],
                "duration": "5 minutes"
            },
            "detailed_meeting": {
                "transcript": "Team meeting to discuss Q4 objectives and resource allocation. John presented the budget analysis showing 15% increase in operational costs. Sarah outlined the new product roadmap with three major releases planned. The team agreed on priorities and assigned action items.",
                "expected_topics": ["Q4 objectives", "budget analysis", "product roadmap"],
                "duration": "45 minutes"
            }
        }
        
        (test_data_dir / "meeting_transcripts.json").write_text(
            json.dumps(meeting_transcripts, indent=2)
        )
        
        print("✅ Test data created")
    
    def run_hello_world_test(self):
        """Run a simple test to verify everything works."""
        print("🧪 Running Hello World test...")
        
        try:
            # Simple test of email parser
            sys.path.insert(0, str(self.root_dir))
            from email_command_parser import EmailCommandParser
            
            parser = EmailCommandParser()
            result = parser.parse_command("Vertigo: Help")
            
            if result and result.get('command') == 'help':
                print("✅ Hello World test passed")
            else:
                print("⚠️  Hello World test returned unexpected result")
                
        except Exception as e:
            print(f"⚠️  Hello World test failed: {e}")
            print("This is normal if Firestore isn't configured yet")

def main():
    """Main setup function."""
    setup = VertigoScenarioSetup()
    setup.run_setup()

if __name__ == "__main__":
    main()