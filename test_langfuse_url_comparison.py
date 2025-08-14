#!/usr/bin/env python3
"""
Comprehensive Langfuse URL Comparison Test
This script tests both URL formats to identify the connection issue root cause.
"""

import os
import sys
import time
import uuid
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the vertigo-debug-toolkit to the path
sys.path.append('/Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit')

class LangfuseConnectionTester:
    """Comprehensive tester for Langfuse connections with different URL formats."""
    
    def __init__(self):
        self.public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
        self.secret_key = os.getenv('LANGFUSE_SECRET_KEY')
        self.results = {}
        
    def print_header(self, title):
        """Print a formatted header."""
        print("\n" + "=" * 80)
        print(f"🔍 {title}")
        print("=" * 80)
    
    def test_environment_setup(self):
        """Test environment variable setup."""
        self.print_header("ENVIRONMENT SETUP")
        
        print(f"Public Key: {'✅ Found' if self.public_key else '❌ Missing'}")
        print(f"Secret Key: {'✅ Found' if self.secret_key else '❌ Missing'}")
        print(f"Current HOST from .env: {os.getenv('LANGFUSE_HOST', 'Not set')}")
        
        if not self.public_key or not self.secret_key:
            print("❌ CRITICAL: API keys not found. Cannot proceed with tests.")
            return False
        
        # Mask keys for display
        masked_public = self.public_key[:8] + "..." + self.public_key[-4:] if self.public_key else "None"
        masked_secret = self.secret_key[:8] + "..." + self.secret_key[-4:] if self.secret_key else "None"
        
        print(f"Public Key (masked): {masked_public}")
        print(f"Secret Key (masked): {masked_secret}")
        
        return True
    
    def test_langfuse_import(self):
        """Test Langfuse import and version."""
        self.print_header("LANGFUSE IMPORT & VERSION")
        
        try:
            from langfuse import Langfuse
            print("✅ Langfuse import: SUCCESS")
            
            # Try to get version
            if hasattr(Langfuse, '__version__'):
                print(f"📦 Langfuse version: {Langfuse.__version__}")
            else:
                print("📦 Langfuse version: Unable to determine")
            
            return True, Langfuse
        except ImportError as e:
            print(f"❌ Langfuse import: FAILED - {e}")
            return False, None
    
    def test_single_host(self, host_url, host_label, Langfuse):
        """Test connection to a single host URL."""
        print(f"\n🌐 Testing {host_label}: {host_url}")
        print("-" * 60)
        
        test_results = {
            'host': host_url,
            'label': host_label,
            'client_init': False,
            'trace_creation': False,
            'generation_creation': False,
            'flush_success': False,
            'error': None,
            'trace_ids': []
        }
        
        try:
            # Step 1: Initialize client
            print("📡 Step 1: Initializing client...")
            client = Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=host_url
            )
            print("✅ Client initialization: SUCCESS")
            test_results['client_init'] = True
            
            # Step 2: Test trace creation using multiple methods
            print("\n📝 Step 2: Testing trace creation methods...")
            
            # Method A: Modern .trace() method (if available)
            try:
                if hasattr(client, 'trace'):
                    trace = client.trace(
                        name=f"url_test_{host_label.lower()}_{int(time.time())}",
                        metadata={
                            "test_host": host_url,
                            "test_label": host_label,
                            "test_timestamp": datetime.now().isoformat(),
                            "test_method": "modern_trace"
                        }
                    )
                    trace_id = trace.id
                    print(f"✅ Modern .trace() method: SUCCESS - ID: {trace_id}")
                    test_results['trace_creation'] = True
                    test_results['trace_ids'].append(('modern_trace', trace_id))
                    
                    # Try to add a generation to this trace
                    try:
                        generation = trace.generation(
                            name="test_generation",
                            model="gpt-3.5-turbo",
                            input="Test input for URL comparison",
                            output="Test output response",
                            metadata={"generation_test": True}
                        )
                        print(f"✅ Generation within trace: SUCCESS - ID: {generation.id}")
                        test_results['generation_creation'] = True
                    except Exception as gen_e:
                        print(f"❌ Generation within trace: FAILED - {gen_e}")
                        
                else:
                    print("❌ Modern .trace() method: Not available")
            except Exception as e:
                print(f"❌ Modern .trace() method: FAILED - {e}")
            
            # Method B: Legacy create_trace (if available)
            try:
                if hasattr(client, 'create_trace'):
                    legacy_trace_id = client.create_trace(
                        name=f"legacy_test_{host_label.lower()}_{int(time.time())}",
                        metadata={
                            "test_host": host_url,
                            "test_method": "legacy_create_trace"
                        }
                    )
                    print(f"✅ Legacy create_trace(): SUCCESS - ID: {legacy_trace_id}")
                    test_results['trace_creation'] = True
                    test_results['trace_ids'].append(('legacy_create_trace', legacy_trace_id))
                else:
                    print("❌ Legacy create_trace(): Not available")
            except Exception as e:
                print(f"❌ Legacy create_trace(): FAILED - {e}")
            
            # Method C: Direct generation (if available)
            try:
                if hasattr(client, 'create_generation'):
                    gen_id = client.create_generation(
                        name=f"direct_gen_{host_label.lower()}_{int(time.time())}",
                        model="gpt-3.5-turbo",
                        input="Direct generation test",
                        output="Direct generation response",
                        metadata={
                            "test_host": host_url,
                            "test_method": "direct_generation"
                        }
                    )
                    print(f"✅ Direct create_generation(): SUCCESS - ID: {gen_id}")
                    test_results['generation_creation'] = True
                else:
                    print("❌ Direct create_generation(): Not available")
            except Exception as e:
                print(f"❌ Direct create_generation(): FAILED - {e}")
            
            # Step 3: Test flush
            print(f"\n🔄 Step 3: Flushing data...")
            try:
                if hasattr(client, 'flush'):
                    client.flush()
                    print("✅ Flush: SUCCESS")
                    test_results['flush_success'] = True
                else:
                    print("❌ Flush: Method not available")
            except Exception as e:
                print(f"❌ Flush: FAILED - {e}")
            
            # Step 4: Wait and verify
            print("⏰ Waiting 5 seconds for data submission...")
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR for {host_label}: {e}")
            test_results['error'] = str(e)
            traceback.print_exc()
        
        return test_results
    
    def test_both_hosts(self, Langfuse):
        """Test both host URL formats."""
        self.print_header("HOST URL COMPARISON TESTS")
        
        # Test configurations
        hosts_to_test = [
            ("https://us.cloud.langfuse.com", "US Cloud (Current)"),
            ("https://cloud.langfuse.com", "Global Cloud (Alternative)"),
            ("https://api.langfuse.com", "API Endpoint (Fallback)")
        ]
        
        all_results = []
        
        for host_url, host_label in hosts_to_test:
            result = self.test_single_host(host_url, host_label, Langfuse)
            all_results.append(result)
            self.results[host_label] = result
        
        return all_results
    
    def test_trace_retrieval(self, Langfuse):
        """Test if we can retrieve traces from different endpoints."""
        self.print_header("TRACE RETRIEVAL TEST")
        
        # Test both hosts for trace retrieval
        hosts_to_test = [
            ("https://us.cloud.langfuse.com", "US Cloud"),
            ("https://cloud.langfuse.com", "Global Cloud")
        ]
        
        for host_url, host_label in hosts_to_test:
            print(f"\n🔍 Testing trace retrieval from {host_label}...")
            try:
                client = Langfuse(
                    public_key=self.public_key,
                    secret_key=self.secret_key,
                    host=host_url
                )
                
                # Try different methods to get traces
                if hasattr(client, 'get_traces'):
                    traces = client.get_traces(limit=5)
                    print(f"✅ get_traces() from {host_label}: Found {len(traces)} traces")
                elif hasattr(client, 'api') and hasattr(client.api, 'trace'):
                    traces = client.api.trace.list(limit=5)
                    print(f"✅ api.trace.list() from {host_label}: Found {len(traces.data)} traces")
                else:
                    print(f"❌ No trace retrieval method available for {host_label}")
                    
            except Exception as e:
                print(f"❌ Trace retrieval from {host_label}: FAILED - {e}")
    
    def test_wrapper_client(self):
        """Test the existing LangfuseClient wrapper."""
        self.print_header("WRAPPER CLIENT TEST")
        
        try:
            from app.services.langfuse_client import LangfuseClient
            print("✅ LangfuseClient import: SUCCESS")
            
            # Test with current configuration
            print(f"\n🔧 Testing wrapper with current config...")
            wrapper = LangfuseClient()
            
            # Try to create a trace
            trace_id = wrapper.create_trace(
                name=f"wrapper_test_{int(time.time())}",
                metadata={
                    "test_type": "wrapper_test",
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"✅ Wrapper trace creation: SUCCESS - ID: {trace_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Wrapper client test: FAILED - {e}")
            traceback.print_exc()
            return False
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        self.print_header("COMPREHENSIVE SUMMARY REPORT")
        
        print("📊 RESULTS OVERVIEW:")
        print("-" * 40)
        
        working_hosts = []
        failed_hosts = []
        
        for host_label, result in self.results.items():
            if result['client_init'] and (result['trace_creation'] or result['generation_creation']):
                working_hosts.append(host_label)
                status = "✅ WORKING"
            else:
                failed_hosts.append(host_label)
                status = "❌ FAILED"
            
            print(f"{host_label:<25}: {status}")
            
            if result['trace_ids']:
                print(f"  └── Created traces: {len(result['trace_ids'])}")
                for method, trace_id in result['trace_ids']:
                    print(f"      • {method}: {trace_id}")
        
        print(f"\n🎯 ANALYSIS:")
        print("-" * 40)
        
        if working_hosts:
            print(f"✅ Working endpoints: {', '.join(working_hosts)}")
            
            if len(working_hosts) > 1:
                print("🔍 Multiple endpoints work - no URL issue detected")
            else:
                print("🔍 Single endpoint working - may indicate regional routing")
        
        if failed_hosts:
            print(f"❌ Failed endpoints: {', '.join(failed_hosts)}")
        
        print(f"\n🚀 RECOMMENDATIONS:")
        print("-" * 40)
        
        if "US Cloud (Current)" in working_hosts:
            print("✅ Current configuration (https://us.cloud.langfuse.com) is working correctly")
            print("💡 The issue may not be URL-related. Consider:")
            print("   • Network connectivity issues")
            print("   • Trace visibility delays (can take up to 10 minutes)")
            print("   • Dashboard filtering or project settings")
        elif "Global Cloud (Alternative)" in working_hosts:
            print("🔄 Consider switching to https://cloud.langfuse.com")
            print("💡 Update both .env files with: LANGFUSE_HOST=https://cloud.langfuse.com")
        elif not working_hosts:
            print("🚨 No endpoints working - likely an API key or authentication issue")
            print("💡 Verify:")
            print("   • API keys are correct and active")
            print("   • Project permissions")
            print("   • Account status")
        else:
            print("🔄 Mixed results detected - check individual endpoint details above")
        
        # Dashboard links
        print(f"\n🔗 DASHBOARD LINKS:")
        print("-" * 40)
        project_id = "cmdly8e8a069pad07wqtif0e7"  # From your previous tests
        
        print(f"US Cloud Dashboard:")
        print(f"  https://us.cloud.langfuse.com/project/{project_id}/traces")
        print(f"Global Cloud Dashboard:")
        print(f"  https://cloud.langfuse.com/project/{project_id}/traces")
        
        print(f"\n⏰ Note: Traces may take 5-10 minutes to appear in the dashboard")
        print(f"🔍 Check both dashboard links to see which one shows your traces")

def main():
    """Run the comprehensive Langfuse connection test."""
    print("🔬 LANGFUSE URL COMPARISON & CONNECTION DIAGNOSTIC")
    print("This script will test multiple Langfuse endpoints to identify connection issues")
    print()
    
    tester = LangfuseConnectionTester()
    
    # Step 1: Environment setup
    if not tester.test_environment_setup():
        return
    
    # Step 2: Test Langfuse import
    import_success, Langfuse = tester.test_langfuse_import()
    if not import_success:
        print("❌ Cannot proceed without Langfuse import")
        return
    
    # Step 3: Test both host configurations
    tester.test_both_hosts(Langfuse)
    
    # Step 4: Test trace retrieval
    tester.test_trace_retrieval(Langfuse)
    
    # Step 5: Test existing wrapper
    tester.test_wrapper_client()
    
    # Step 6: Generate comprehensive report
    tester.generate_summary_report()
    
    print(f"\n🎉 Testing complete! Use the analysis above to determine next steps.")

if __name__ == "__main__":
    main()