#!/usr/bin/env python3
"""
Test correct LangFuse API usage for version 3.2.1
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Add the vertigo-debug-toolkit to the path
sys.path.append('/Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit')

# Load environment variables
load_dotenv()

def test_correct_api_usage():
    """Test with correct LangFuse 3.2.1 API usage"""
    print("🔍 TESTING CORRECT LANGFUSE 3.2.1 API USAGE")
    print("=" * 60)
    
    try:
        from langfuse import Langfuse
        
        # Initialize client
        client = Langfuse(
            public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
            secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
            host=os.getenv('LANGFUSE_HOST', 'https://us.cloud.langfuse.com')
        )
        print("✅ Client initialized")
        
        # Check available methods
        print("\n📋 Available methods:")
        methods = [method for method in dir(client) if not method.startswith('_')]
        for method in sorted(methods):
            print(f"  - {method}")
        
        # Test Method 1: Create trace using correct API
        print("\n🔄 Method 1: Using langfuse.create_trace()")
        try:
            if hasattr(client, 'create_trace'):
                trace_response = client.create_trace(
                    name="test_trace_method1",
                    metadata={
                        "test_type": "api_debug",
                        "timestamp": datetime.now().isoformat(),
                        "method": "create_trace"
                    }
                )
                print(f"✅ create_trace: SUCCESS - {trace_response}")
            else:
                print("❌ create_trace method not available")
        except Exception as e:
            print(f"❌ create_trace failed: {e}")
        
        # Test Method 2: Create generation directly
        print("\n🔄 Method 2: Using langfuse.create_generation()")
        try:
            if hasattr(client, 'create_generation'):
                generation_response = client.create_generation(
                    name="test_generation_method2",
                    model="gpt-3.5-turbo",
                    input="Test input",
                    output="Test output",
                    metadata={
                        "test_type": "api_debug",
                        "method": "create_generation"
                    }
                )
                print(f"✅ create_generation: SUCCESS - {generation_response}")
            else:
                print("❌ create_generation method not available")
        except Exception as e:
            print(f"❌ create_generation failed: {e}")
        
        # Test Method 3: Using client methods from your existing code
        print("\n🔄 Method 3: Using existing LangfuseClient wrapper")
        try:
            from app.services.langfuse_client import LangfuseClient
            wrapper_client = LangfuseClient()
            
            trace_id = wrapper_client.create_trace(
                name="test_trace_wrapper",
                metadata={
                    "test_type": "wrapper_debug", 
                    "method": "wrapper_client"
                }
            )
            print(f"✅ LangfuseClient wrapper: SUCCESS - {trace_id}")
            
        except Exception as e:
            print(f"❌ LangfuseClient wrapper failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test Method 4: Direct API calls
        print("\n🔄 Method 4: Testing direct API methods")
        try:
            # Try different approaches based on SDK docs
            if hasattr(client, 'log'):
                log_response = client.log(
                    event_name="test_log_event",
                    properties={
                        "test_type": "direct_log",
                        "timestamp": datetime.now().isoformat()
                    }
                )
                print(f"✅ log method: SUCCESS - {log_response}")
            else:
                print("❌ log method not available")
                
        except Exception as e:
            print(f"❌ Direct API calls failed: {e}")
        
        # Flush and wait
        print("\n🔄 Flushing data...")
        if hasattr(client, 'flush'):
            client.flush()
            print("✅ Flush called successfully")
        
        print("⏰ Waiting 10 seconds for data to appear in dashboard...")
        time.sleep(10)
        
        # Test getting traces back
        print("\n🔄 Testing trace retrieval...")
        try:
            if hasattr(client, 'get_traces'):
                traces = client.get_traces(limit=5)
                print(f"✅ Retrieved traces: {traces}")
            else:
                print("❌ get_traces method not available")
        except Exception as e:
            print(f"❌ Trace retrieval failed: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 SUMMARY")
        print("=" * 60)
        print("✅ Client initialization works")
        print("❌ Modern .trace() method not available in this version")
        print("🔍 Need to use correct API methods for LangFuse 3.2.1")
        print("📊 Check dashboard in a few minutes for any traces that were created")
        print(f"🔗 Dashboard: https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7/traces")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_correct_api_usage()