#!/usr/bin/env python3
"""
Get Langwatch project information for the new Vertigo LLM Observability project.
"""

import os
import sys
import requests
from datetime import datetime

# Add path and load environment
sys.path.append('vertigo-debug-toolkit')
from dotenv import load_dotenv
load_dotenv('vertigo-debug-toolkit/.env')

def get_project_info():
    """Get project information from Langwatch API."""
    api_key = os.getenv('LANGWATCH_API_KEY')
    if not api_key:
        print("❌ LANGWATCH_API_KEY not found in environment")
        return None
    
    print(f"🔑 Using API key: {api_key[:20]}...")
    
    # Try to get project info
    try:
        # Common Langwatch API endpoints to try
        endpoints = [
            "https://app.langwatch.ai/api/projects",
            "https://app.langwatch.ai/api/v1/projects",
            "https://app.langwatch.ai/api/project/info"
        ]
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        for endpoint in endpoints:
            print(f"\n🌐 Trying endpoint: {endpoint}")
            
            try:
                response = requests.get(endpoint, headers=headers, timeout=10)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Success! Project data:")
                    print(f"   Response: {data}")
                    return data
                else:
                    print(f"   Response: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"   Error: {e}")
        
        # If API calls don't work, provide manual instructions
        print("\n📋 **Manual Project Setup Instructions:**")
        print(f"   1. Your new API key: {api_key}")
        print(f"   2. Project name: Vertigo LLM Observability")
        print(f"   3. Team: Eunoia")
        print(f"   4. Language: Python")
        print(f"   5. Framework: Other")
        print(f"\n🎯 After project creation, your dashboard will be at:")
        print(f"   https://app.langwatch.ai/[your-project-id]/analytics/users")
        
        return None
        
    except Exception as e:
        print(f"❌ Error getting project info: {e}")
        return None

def main():
    """Main function."""
    print("📊 Langwatch Project Information")
    print("=" * 40)
    
    project_info = get_project_info()
    
    if project_info:
        print(f"\n✅ Successfully retrieved project information!")
    else:
        print(f"\n⚠️  Using manual configuration for now")
        print(f"💡 Your traces should appear in the new Vertigo project dashboard")

if __name__ == "__main__":
    main()