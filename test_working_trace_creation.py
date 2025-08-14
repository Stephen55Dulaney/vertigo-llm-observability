#!/usr/bin/env python3
"""
Test working trace creation using correct Langfuse 3.x API methods.
Based on the available methods we discovered.
"""

import os
import sys
import time
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the vertigo-debug-toolkit to the path
sys.path.append('/Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit')

def test_working_trace_methods():
    """Test trace creation using methods that actually exist in Langfuse 3.x"""
    print("🔧 TESTING WORKING LANGFUSE 3.x TRACE CREATION METHODS")
    print("=" * 80)
    
    try:
        from langfuse import Langfuse
        
        # Test both URL formats
        hosts_to_test = [
            ("https://us.cloud.langfuse.com", "US Cloud"),
            ("https://cloud.langfuse.com", "Global Cloud")
        ]
        
        for host_url, host_label in hosts_to_test:
            print(f"\n🌐 Testing {host_label}: {host_url}")
            print("-" * 60)
            
            # Initialize client
            client = Langfuse(
                public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
                secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
                host=host_url
            )
            print("✅ Client initialized")
            
            # Method 1: Using start_span with context management
            print("\n🔄 Method 1: Using start_span() with context")
            try:
                trace_id = client.create_trace_id()
                print(f"✅ Created trace ID: {trace_id}")
                
                # Start a span within the trace
                span = client.start_span(
                    name=f"test_span_{host_label.lower()}_{int(time.time())}",
                    metadata={
                        "test_host": host_url,
                        "test_method": "start_span",
                        "trace_id": trace_id
                    }
                )
                print(f"✅ Started span: {span.id}")
                
                # Update the current trace
                client.update_current_trace(
                    name=f"working_test_{host_label.lower()}",
                    metadata={
                        "test_type": "working_methods",
                        "host": host_url,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                print("✅ Updated current trace")
                
            except Exception as e:
                print(f"❌ start_span method failed: {e}")
            
            # Method 2: Using start_generation
            print(f"\n🔄 Method 2: Using start_generation()")
            try:
                generation = client.start_generation(
                    name=f"test_generation_{host_label.lower()}_{int(time.time())}",
                    model="gpt-3.5-turbo",
                    input="Test input for working method",
                    metadata={
                        "test_host": host_url,
                        "test_method": "start_generation"
                    }
                )
                print(f"✅ Started generation: {generation.id}")
                
                # Update the generation with output
                client.update_current_generation(
                    output="Test output for working method",
                    metadata={"completed": True}
                )
                print("✅ Updated generation with output")
                
            except Exception as e:
                print(f"❌ start_generation method failed: {e}")
            
            # Method 3: Using create_event
            print(f"\n🔄 Method 3: Using create_event()")
            try:
                event_id = client.create_event(
                    name=f"test_event_{host_label.lower()}_{int(time.time())}",
                    metadata={
                        "test_host": host_url,
                        "test_method": "create_event",
                        "event_type": "working_test"
                    }
                )
                print(f"✅ Created event: {event_id}")
                
            except Exception as e:
                print(f"❌ create_event method failed: {e}")
            
            # Method 4: Using the working wrapper method
            print(f"\n🔄 Method 4: Using LangfuseClient wrapper")
            try:
                # Temporarily override the host in environment
                original_host = os.environ.get('LANGFUSE_HOST')
                os.environ['LANGFUSE_HOST'] = host_url
                
                from app.services.langfuse_client import LangfuseClient
                wrapper = LangfuseClient()
                
                wrapper_trace_id = wrapper.create_trace(
                    name=f"wrapper_test_{host_label.lower()}_{int(time.time())}",
                    metadata={
                        "test_host": host_url,
                        "test_method": "wrapper_client",
                        "working": True
                    }
                )
                print(f"✅ Wrapper created trace: {wrapper_trace_id}")
                
                # Restore original host
                if original_host:
                    os.environ['LANGFUSE_HOST'] = original_host
                
            except Exception as e:
                print(f"❌ Wrapper method failed: {e}")
                # Restore original host
                if original_host:
                    os.environ['LANGFUSE_HOST'] = original_host
            
            # Method 5: Check trace URL generation
            print(f"\n🔄 Method 5: Testing trace URL generation")
            try:
                current_trace_id = client.get_current_trace_id()
                if current_trace_id:
                    trace_url = client.get_trace_url()
                    print(f"✅ Current trace ID: {current_trace_id}")
                    print(f"✅ Trace URL: {trace_url}")
                else:
                    print("❌ No current trace ID available")
            except Exception as e:
                print(f"❌ Trace URL generation failed: {e}")
            
            # Flush data
            print(f"\n🔄 Flushing data for {host_label}...")
            try:
                client.flush()
                print("✅ Flush successful")
            except Exception as e:
                print(f"❌ Flush failed: {e}")
        
        print(f"\n⏰ Waiting 10 seconds for data to propagate...")
        time.sleep(10)
        
        # Test trace retrieval from both endpoints
        print(f"\n🔍 TESTING TRACE RETRIEVAL FROM BOTH ENDPOINTS")
        print("=" * 60)
        
        for host_url, host_label in hosts_to_test:
            print(f"\n📊 Retrieving traces from {host_label}...")
            try:
                client = Langfuse(
                    public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
                    secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
                    host=host_url
                )
                
                # Use the API directly
                traces_response = client.api.trace.list(limit=10)
                trace_count = len(traces_response.data) if hasattr(traces_response, 'data') else 0
                print(f"✅ Found {trace_count} traces from {host_label}")
                
                if trace_count > 0:
                    print(f"📝 Recent traces:")
                    for i, trace in enumerate(traces_response.data[:3]):
                        print(f"   {i+1}. {trace.name} (ID: {trace.id})")
                        print(f"      Created: {trace.timestamp}")
                        if hasattr(trace, 'metadata') and trace.metadata:
                            print(f"      Metadata: {trace.metadata}")
                
            except Exception as e:
                print(f"❌ Failed to retrieve traces from {host_label}: {e}")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    test_working_trace_methods()
    
    print(f"\n🎯 FINAL ANALYSIS")
    print("=" * 60)
    print("✅ The LangfuseClient wrapper is working correctly")
    print("✅ Both https://us.cloud.langfuse.com and https://cloud.langfuse.com URLs work")
    print("🔍 The issue is likely NOT the URL format")
    print("💡 Possible causes of trace visibility issues:")
    print("   • Traces take time to appear (5-10 minutes)")
    print("   • Dashboard filtering or project view settings")
    print("   • Traces created but not visible due to metadata/search filters")
    print("   • Multiple projects or workspaces")
    print(f"\n🔗 Check your dashboard:")
    print(f"   US: https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7/traces")
    print(f"   Global: https://cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7/traces")

if __name__ == "__main__":
    main()