#!/usr/bin/env python3
"""
Setup script for Vertex AI Learning Project.
Installs dependencies and helps with initial configuration.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def install_dependencies() -> bool:
    """Install project dependencies."""
    print("\n📦 Installing dependencies...")
    
    # Upgrade pip
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    return True


def setup_google_cloud() -> bool:
    """Help set up Google Cloud configuration."""
    print("\n☁️  Google Cloud Setup")
    print("To use Vertex AI, you need to:")
    print("1. Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install")
    print("2. Authenticate: gcloud auth login")
    print("3. Create a project: gcloud projects create your-project-id")
    print("4. Enable APIs: gcloud services enable aiplatform.googleapis.com")
    print("5. Set up credentials: gcloud auth application-default login")
    
    # Check if gcloud is installed
    if shutil.which("gcloud"):
        print("✅ Google Cloud CLI is installed")
        
        # Check if authenticated
        try:
            result = subprocess.run(["gcloud", "auth", "list"], capture_output=True, text=True)
            if "ACTIVE" in result.stdout:
                print("✅ Google Cloud authentication found")
                return True
            else:
                print("⚠️  Please run: gcloud auth login")
        except:
            pass
    else:
        print("⚠️  Google Cloud CLI not found. Please install it first.")
    
    return False


def create_env_file() -> bool:
    """Create .env file from template."""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please update .env with your Google Cloud project details")
        return True
    else:
        print("❌ env.example not found")
        return False


def run_tests() -> bool:
    """Run basic tests to verify setup."""
    print("\n🧪 Running basic tests...")
    
    # Test imports
    test_imports = [
        "google.cloud.aiplatform",
        "google.auth",
        "pydantic",
        "asyncio"
    ]
    
    for module in test_imports:
        try:
            __import__(module)
            print(f"✅ {module} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {module}: {e}")
            return False
    
    return True


def main():
    """Main setup function."""
    print("🚀 Vertex AI Learning Project Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        print("❌ Failed to create environment file")
        sys.exit(1)
    
    # Setup Google Cloud
    setup_google_cloud()
    
    # Run tests
    if not run_tests():
        print("❌ Basic tests failed")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update .env with your Google Cloud project details")
    print("2. Set up Google Cloud authentication")
    print("3. Run examples: python examples/gmail_workflow_example.py")
    print("4. Explore the codebase in the agents/, search/, and workspace/ directories")


if __name__ == "__main__":
    main() 