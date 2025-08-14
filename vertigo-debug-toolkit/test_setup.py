#!/usr/bin/env python3
"""
Test script to verify the Vertigo Debug Toolkit setup.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test environment variables and dependencies."""
    print("🔍 Testing Environment Setup...")
    
    # Check required environment variables
    required_vars = [
        'FLASK_SECRET_KEY',
        'LANGFUSE_PUBLIC_KEY', 
        'LANGFUSE_SECRET_KEY',
        'LANGFUSE_HOST',
        'VERTIGO_API_URL',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return False
    else:
        print("✅ All environment variables are set")
    
    return True

def test_imports():
    """Test that all required packages can be imported."""
    print("\n📦 Testing Package Imports...")
    
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import langfuse
        print("✅ Langfuse imported successfully")
    except ImportError as e:
        print(f"❌ Langfuse import failed: {e}")
        return False
    
    try:
        import google.generativeai
        print("✅ Google Generative AI imported successfully")
    except ImportError as e:
        print(f"❌ Google Generative AI import failed: {e}")
        return False
    
    try:
        from app import create_app, db
        print("✅ App modules imported successfully")
    except ImportError as e:
        print(f"❌ App modules import failed: {e}")
        return False
    
    return True

def test_langfuse_connection():
    """Test Langfuse connection."""
    print("\n🔗 Testing Langfuse Connection...")
    
    try:
        from app.services.langfuse_client import LangfuseClient
        client = LangfuseClient()
        
        # Try to get traces (this will fail if connection is bad)
        traces = client.get_traces(limit=1)
        print("✅ Langfuse connection successful")
        return True
    except Exception as e:
        print(f"❌ Langfuse connection failed: {e}")
        print("Make sure Langfuse is running at the configured host")
        return False

def test_gemini_connection():
    """Test Gemini API connection."""
    print("\n🤖 Testing Gemini API Connection...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY not set")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        response = model.generate_content("Say hello!")
        print("✅ Gemini API connection successful")
        return True
    except Exception as e:
        print(f"❌ Gemini API connection failed: {e}")
        return False

def test_vertigo_connection():
    """Test Vertigo API connection."""
    print("\n📧 Testing Vertigo API Connection...")
    
    try:
        import requests
        
        vertigo_url = os.getenv('VERTIGO_API_URL')
        if not vertigo_url:
            print("❌ VERTIGO_API_URL not set")
            return False
        
        response = requests.get(vertigo_url, timeout=10)
        print(f"✅ Vertigo API connection successful (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Vertigo API connection failed: {e}")
        return False

def test_database():
    """Test database connection."""
    print("\n🗄️ Testing Database Connection...")
    
    try:
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            # Try to create tables
            db.create_all()
            print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Vertigo Debug Toolkit - Setup Test")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_imports,
        test_langfuse_connection,
        test_gemini_connection,
        test_vertigo_connection,
        test_database
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Start Langfuse: docker-compose up -d langfuse")
        print("2. Run the app: flask run")
        print("3. Access the toolkit at: http://localhost:5000")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 