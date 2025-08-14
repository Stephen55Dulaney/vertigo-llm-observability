#!/usr/bin/env python3
"""
Test Langfuse connection and check available traces.
"""

from app.services.langfuse_client import LangfuseClient

def test_langfuse_connection():
    """Test Langfuse connection and list traces."""
    
    print("🔗 Testing Langfuse Connection")
    print("=" * 40)
    
    try:
        # Initialize client
        client = LangfuseClient()
        print("✅ Langfuse client initialized")
        
        # Test getting traces
        print("\n📥 Fetching traces...")
        traces = client.get_traces(limit=10)
        
        if hasattr(traces, 'data'):
            print(f"✅ Found {len(traces.data)} traces")
            for i, trace in enumerate(traces.data[:5]):  # Show first 5
                print(f"  {i+1}. {trace.name} (ID: {trace.id})")
        else:
            print(f"❌ Unexpected response format: {type(traces)}")
            print(f"Response: {traces}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_langfuse_connection() 