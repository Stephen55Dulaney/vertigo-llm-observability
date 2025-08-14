#!/usr/bin/env python3
"""
Test script to verify Langfuse integration in cloud functions.
This script can be run locally to test the langfuse_client before deployment.
"""

import os
import sys
import json
import time
from datetime import datetime

# Add the shared directory to path
sys.path.append('vertigo/functions/shared')

def test_langfuse_connection():
    """Test basic Langfuse connection and trace creation."""
    print("🔍 Testing Langfuse integration for cloud functions...")
    
    try:
        from langfuse_client import langfuse_client
        
        if not langfuse_client.is_enabled():
            print("❌ Langfuse client is not enabled.")
            print("📋 Please check:")
            print("   1. LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables")
            print("   2. Or Google Cloud Secret Manager secrets: langfuse-public-key, langfuse-secret-key")
            return False
        
        print("✅ Langfuse client initialized successfully")
        
        # Test trace creation
        trace_id = langfuse_client.create_trace(
            name="test_cloud_function_trace",
            metadata={
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "source": "local_test"
            }
        )
        
        if trace_id:
            print(f"✅ Created test trace: {trace_id}")
            
            # Test generation creation
            generation_id = langfuse_client.create_generation(
                trace_id=trace_id,
                name="test_llm_call",
                model="gemini-1.5-pro",
                input_data={"prompt": "Test prompt for tracing"},
                output_data={"response": "Test response from LLM"},
                metadata={"test": True}
            )
            
            if generation_id:
                print(f"✅ Created test generation: {generation_id}")
            else:
                print("⚠️  Generation creation returned empty ID")
            
            # Update trace with success
            langfuse_client.update_trace(
                trace_id=trace_id,
                metadata={"test_completed": True, "success": True},
                output={"test_result": "All tests passed"},
                level="DEFAULT"
            )
            
            # Flush to ensure data is sent
            langfuse_client.flush()
            print("✅ Flushed trace data to Langfuse")
            
            print("🎉 Langfuse integration test completed successfully!")
            print(f"🔗 Check your Langfuse dashboard for trace: {trace_id}")
            return True
            
        else:
            print("❌ Failed to create trace")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📋 Make sure you're in the correct directory and langfuse is installed")
        return False
    except Exception as e:
        print(f"❌ Error testing Langfuse: {e}")
        return False

def test_with_environment_variables():
    """Test with environment variables (for local development)."""
    print("\n🔧 Testing with environment variables...")
    
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    
    if not public_key or not secret_key:
        print("⚠️  LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not found in environment")
        print("📋 Set them with:")
        print("   export LANGFUSE_PUBLIC_KEY='your_public_key'")
        print("   export LANGFUSE_SECRET_KEY='your_secret_key'")
        return False
    
    print(f"✅ Found environment variables")
    print(f"   Public Key: {public_key[:8]}...")
    print(f"   Secret Key: {secret_key[:8]}...")
    
    return test_langfuse_connection()

def main():
    """Main test function."""
    print("🚀 Cloud Function Langfuse Integration Test")
    print("=" * 50)
    
    # Test with environment variables first
    env_success = test_with_environment_variables()
    
    if not env_success:
        print("\n🔐 Testing with Google Cloud Secret Manager...")
        print("   (This requires gcloud auth and project setup)")
        connection_success = test_langfuse_connection()
        
        if not connection_success:
            print("\n❌ Both environment variables and Secret Manager tests failed")
            print("📋 Setup checklist:")
            print("   1. Run ./setup_langfuse_secrets.sh to configure Secret Manager")
            print("   2. Or set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables")
            print("   3. Ensure you have the correct Langfuse credentials from:")
            print("      https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7")
            sys.exit(1)
    
    print("\n✅ All tests passed! Your cloud functions should now create traces in Langfuse.")
    print("🚀 Deploy your functions and test email processing to see traces in action.")

if __name__ == "__main__":
    main()