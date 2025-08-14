#!/usr/bin/env python3
"""
Quick fix script for Vertigo Scenario testing issues.
"""

import os
import sys
from pathlib import Path

def setup_google_cloud_auth():
    """Set up Google Cloud authentication for Firestore access."""
    print("🔐 Setting up Google Cloud Authentication...")
    
    # Check if service account key exists
    service_account_files = [
        "client_secret_579831320777-f2c5rmtki7h17phu8kjb1aoh7mnucrtp.apps.googleusercontent.com.json",
        "vertigo-service-account.json",
        "google-cloud-key.json"
    ]
    
    found_key = None
    for key_file in service_account_files:
        if Path(key_file).exists():
            found_key = key_file
            break
    
    if found_key:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = found_key
        print(f"✅ Found service account key: {found_key}")
        return True
    else:
        print("⚠️  No service account key found. Options:")
        print("1. Add service account JSON file to project root")
        print("2. Use 'gcloud auth application-default login'")
        print("3. Use mock data for testing (recommended for learning)")
        return False

def enable_mock_mode():
    """Enable mock mode for testing without external dependencies."""
    print("🎭 Enabling Mock Mode for Testing...")
    
    # Set environment variable for mock mode
    os.environ['MOCK_EXTERNAL_SERVICES'] = 'true'
    os.environ['VERTIGO_TESTING_MODE'] = 'mock'
    
    print("✅ Mock mode enabled - tests will use sample data")
    return True

def run_diagnostic():
    """Run diagnostic to see what's working."""
    print("🔍 Running Diagnostic Check...")
    
    try:
        # Check email parser
        sys.path.append(str(Path.cwd()))
        from email_command_parser import EmailCommandParser
        
        parser = EmailCommandParser()
        
        # Test basic command detection
        test_commands = [
            "Vertigo: Help",
            "Re: Vertigo: Help", 
            "Vertigo: Unknown command"
        ]
        
        print("\n📧 Testing Command Detection:")
        for command in test_commands:
            try:
                result = parser.parse_command(command, "")
                print(f"  ✅ '{command}' → {result.get('command', 'no command')}")
            except Exception as e:
                print(f"  ❌ '{command}' → Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        return False

def main():
    """Main fix function."""
    print("🛠️  Vertigo Scenario Testing Fix Script")
    print("=" * 45)
    
    print("\n🎯 Choose your approach:")
    print("1. Set up Google Cloud authentication (production testing)")
    print("2. Enable mock mode (faster learning)")
    print("3. Run diagnostic only")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        setup_google_cloud_auth()
    elif choice == "2":
        enable_mock_mode()
    elif choice == "3":
        run_diagnostic()
    else:
        print("Invalid choice. Running diagnostic...")
        run_diagnostic()
    
    print(f"\n🚀 Now run your scenario tests:")
    print(f"cd vertigo_scenario_framework")
    print(f"python examples/hello_world_scenario.py")

if __name__ == "__main__":
    main()