#!/usr/bin/env python3
"""
Comprehensive LangFuse connection and trace creation test.
This script will help us identify exactly what's working and what's failing.
"""

import os
import sys
import time
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the vertigo-debug-toolkit to the path
sys.path.append('/Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit')

def test_environment_setup():
    """Test 1: Environment Variables"""
    print("=" * 60)
    print("TEST 1: Environment Variables")
    print("=" * 60)
    
    required_vars = ['LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY', 'LANGFUSE_HOST']
    results = {}
    
    for var in required_vars:
        value = os.getenv(var)
        results[var] = value is not None and len(value) > 0
        status = "✅ FOUND" if results[var] else "❌ MISSING"
        masked_value = value[:8] + "..." + value[-4:] if value and len(value) > 12 else value
        print(f"{var}: {status} ({masked_value})")
    
    all_present = all(results.values())
    print(f"\nEnvironment Setup: {'✅ PASS' if all_present else '❌ FAIL'}")
    return all_present

def test_langfuse_import():
    """Test 2: LangFuse Import"""
    print("\n" + "=" * 60)
    print("TEST 2: LangFuse Import")
    print("=" * 60)
    
    try:
        from langfuse import Langfuse
        print("✅ LangFuse import: SUCCESS")
        print(f"✅ LangFuse version: {Langfuse.__version__ if hasattr(Langfuse, '__version__') else 'Unknown'}")
        return True, Langfuse
    except ImportError as e:
        print(f"❌ LangFuse import: FAILED - {e}")
        return False, None

def test_client_initialization(Langfuse):
    """Test 3: Client Initialization"""
    print("\n" + "=" * 60)
    print("TEST 3: Client Initialization")
    print("=" * 60)
    
    try:
        client = Langfuse(
            public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
            secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
            host=os.getenv('LANGFUSE_HOST', 'https://us.cloud.langfuse.com')
        )
        print("✅ Client initialization: SUCCESS")
        return True, client
    except Exception as e:
        print(f"❌ Client initialization: FAILED - {e}")
        traceback.print_exc()
        return False, None

def test_basic_trace_creation(client):
    """Test 4: Basic Trace Creation"""
    print("\n" + "=" * 60)
    print("TEST 4: Basic Trace Creation")
    print("=" * 60)
    
    try:
        # Method 1: Direct trace creation (modern approach)
        print("Trying Method 1: Direct trace creation")
        trace = client.trace(
            name="debug_test_trace",
            metadata={
                "test_type": "connection_debug",
                "timestamp": datetime.now().isoformat(),
                "source": "debug_script"
            }
        )
        print(f"✅ Method 1: SUCCESS - Trace ID: {trace.id}")
        
        # Method 2: Generation within trace
        print("\nTrying Method 2: Generation within trace")
        generation = trace.generation(
            name="test_generation",
            model="gpt-3.5-turbo",
            input="Hello, this is a test",
            output="This is a test response",
            metadata={"test": True}
        )
        print(f"✅ Method 2: SUCCESS - Generation ID: {generation.id}")
        
        return True, trace.id
    except Exception as e:
        print(f"❌ Trace creation: FAILED - {e}")
        traceback.print_exc()
        return False, None

def test_alternative_trace_methods(client):
    """Test 5: Alternative Trace Methods"""
    print("\n" + "=" * 60)
    print("TEST 5: Alternative Trace Methods")
    print("=" * 60)
    
    methods_tested = {}
    
    # Method A: create_trace (if it exists)
    try:
        if hasattr(client, 'create_trace'):
            trace_id = client.create_trace(
                name="alt_test_trace_A",
                metadata={"method": "create_trace"}
            )
            methods_tested['create_trace'] = f"✅ SUCCESS - {trace_id}"
        else:
            methods_tested['create_trace'] = "❌ Method not available"
    except Exception as e:
        methods_tested['create_trace'] = f"❌ FAILED - {e}"
    
    # Method B: Manual trace creation
    try:
        import uuid
        trace_id = str(uuid.uuid4())
        
        # Try to send trace data manually
        trace_data = {
            "id": trace_id,
            "name": "alt_test_trace_B", 
            "metadata": {"method": "manual_creation"},
            "timestamp": datetime.now().isoformat()
        }
        
        # This might not work, but let's try
        if hasattr(client, 'create_trace_id'):
            trace_id_result = client.create_trace_id()
            methods_tested['create_trace_id'] = f"✅ SUCCESS - {trace_id_result}"
        else:
            methods_tested['create_trace_id'] = "❌ Method not available"
            
    except Exception as e:
        methods_tested['create_trace_id'] = f"❌ FAILED - {e}"
    
    # Print results
    for method, result in methods_tested.items():
        print(f"{method}: {result}")
    
    return any("SUCCESS" in result for result in methods_tested.values())

def test_flush_and_wait(client):
    """Test 6: Flush and Wait"""
    print("\n" + "=" * 60)
    print("TEST 6: Flush and Wait")
    print("=" * 60)
    
    try:
        print("Attempting to flush traces...")
        if hasattr(client, 'flush'):
            client.flush()
            print("✅ Flush method called successfully")
        else:
            print("❌ No flush method available")
        
        print("Waiting 5 seconds for submission...")
        time.sleep(5)
        
        return True
    except Exception as e:
        print(f"❌ Flush failed: {e}")
        return False

def test_auth_verification(client):
    """Test 7: Auth Verification"""
    print("\n" + "=" * 60)
    print("TEST 7: Authentication Verification")
    print("=" * 60)
    
    try:
        # Try to access some client properties or make a simple call
        if hasattr(client, 'auth'):
            print("✅ Client has auth property")
        
        # Check if we can access project info
        print("Testing authentication by creating a simple trace...")
        test_trace = client.trace(name="auth_test")
        print(f"✅ Authentication appears valid - created trace {test_trace.id}")
        return True
        
    except Exception as e:
        print(f"❌ Authentication verification failed: {e}")
        if "401" in str(e) or "unauthorized" in str(e).lower():
            print("❌ This looks like an authentication error - check your API keys")
        elif "403" in str(e) or "forbidden" in str(e).lower():
            print("❌ This looks like a permissions error - check project access")
        return False

def main():
    """Run comprehensive LangFuse connection tests"""
    print("🔍 COMPREHENSIVE LANGFUSE CONNECTION TEST")
    print("This will help identify exactly what's working and what's failing.")
    print()
    
    # Test 1: Environment Setup
    if not test_environment_setup():
        print("\n❌ CRITICAL: Environment variables not properly set. Stopping tests.")
        return
    
    # Test 2: Import
    import_success, Langfuse = test_langfuse_import()
    if not import_success:
        print("\n❌ CRITICAL: Cannot import LangFuse. Stopping tests.")
        return
    
    # Test 3: Client Initialization
    client_success, client = test_client_initialization(Langfuse)
    if not client_success:
        print("\n❌ CRITICAL: Cannot initialize client. Stopping tests.")
        return
    
    # Test 4: Basic Trace Creation
    trace_success, trace_id = test_basic_trace_creation(client)
    
    # Test 5: Alternative Methods
    alt_success = test_alternative_trace_methods(client)
    
    # Test 6: Flush and Wait
    flush_success = test_flush_and_wait(client)
    
    # Test 7: Auth Verification
    auth_success = test_auth_verification(client)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", True),  # We got this far
        ("LangFuse Import", import_success),
        ("Client Initialization", client_success),
        ("Basic Trace Creation", trace_success),
        ("Alternative Methods", alt_success),
        ("Flush and Wait", flush_success),
        ("Authentication", auth_success)
    ]
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<25}: {status}")
    
    overall_success = all(success for _, success in tests[:-1])  # Exclude auth as it might be redundant
    
    print(f"\nOverall Status: {'✅ MOSTLY WORKING' if overall_success else '❌ NEEDS DEBUGGING'}")
    
    if trace_success:
        print(f"\n🎉 Great! Traces appear to be created successfully.")
        print(f"🔍 Check your dashboard for trace ID: {trace_id}")
        print(f"🔗 Dashboard: https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7/traces")
    else:
        print(f"\n🚨 Trace creation is failing. This is likely the root issue.")
    
    print(f"\n⏰ Traces may take a few minutes to appear in the dashboard.")
    print(f"📧 Use this information when contacting Jannik for support.")

if __name__ == "__main__":
    main()