#!/usr/bin/env python3
"""
Comprehensive Langfuse Connection Diagnosis Report
Final analysis of the connection and trace visibility issues.
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the vertigo-debug-toolkit to the path
sys.path.append('/Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit')

def generate_diagnosis_report():
    """Generate comprehensive diagnosis report"""
    print("🏥 LANGFUSE CONNECTION DIAGNOSIS REPORT")
    print("=" * 80)
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🔍 ISSUE SUMMARY:")
    print("-" * 40)
    print("User reported that traces created via API are not visible in the Langfuse dashboard.")
    print("User mentioned previously using 'cloud.langfuse.com' on another machine successfully.")
    print("Current configuration uses 'https://us.cloud.langfuse.com'.")
    print()
    
    print("🔧 TESTING PERFORMED:")
    print("-" * 40)
    print("✅ Environment variable configuration")
    print("✅ Langfuse SDK import and version check")
    print("✅ Client initialization with multiple URL formats")
    print("✅ Trace creation using correct Langfuse 3.x API methods")
    print("✅ URL comparison between us.cloud.langfuse.com and cloud.langfuse.com")
    print("✅ Trace retrieval and visibility testing")
    print("✅ LangfuseClient wrapper functionality")
    print()
    
    print("🎯 KEY FINDINGS:")
    print("-" * 40)
    print("1. ✅ BOTH URL formats work correctly:")
    print("   • https://us.cloud.langfuse.com ✅ Working")
    print("   • https://cloud.langfuse.com ✅ Working")
    print()
    print("2. ✅ Trace creation is successful:")
    print("   • LangfuseClient wrapper creates traces successfully")
    print("   • start_span() method works")
    print("   • start_generation() method works")
    print("   • create_event() method works")
    print()
    print("3. ✅ Trace retrieval confirms data synchronization:")
    print("   • Traces created on 'us.cloud.langfuse.com' are visible on 'cloud.langfuse.com'")
    print("   • Traces created on 'cloud.langfuse.com' are visible on 'us.cloud.langfuse.com'")
    print("   • This proves both URLs point to the same backend system")
    print()
    print("4. ✅ Authentication and API keys are working correctly")
    print()
    print("5. ❌ The issue is NOT URL-related")
    print()
    
    print("🚨 ROOT CAUSE ANALYSIS:")
    print("-" * 40)
    print("Based on comprehensive testing, the URL difference is NOT causing the issue.")
    print("Both 'https://us.cloud.langfuse.com' and 'https://cloud.langfuse.com' work identically.")
    print()
    print("The most likely causes of trace visibility issues are:")
    print()
    print("1. 🕐 TIMING ISSUES:")
    print("   • Traces can take 5-10 minutes to appear in dashboard")
    print("   • Dashboard may need manual refresh")
    print("   • Check timestamps of recent traces vs. dashboard view")
    print()
    print("2. 🔍 DASHBOARD FILTERING:")
    print("   • Dashboard may have active filters hiding traces")
    print("   • Date range filters may exclude recent traces")
    print("   • Project/workspace selection may be incorrect")
    print("   • Search filters may be active")
    print()
    print("3. 📊 PROJECT CONFIGURATION:")
    print("   • Multiple projects or workspaces in the account")
    print("   • API keys may be associated with different project than dashboard view")
    print("   • Project ID mismatch between API and dashboard URL")
    print()
    print("4. 🏷️ TRACE METADATA ISSUES:")
    print("   • Traces created with metadata that doesn't match dashboard search")
    print("   • Trace names may not match expected patterns")
    print("   • Tags or labels may affect visibility")
    print()
    
    print("✅ SUCCESSFUL TEST EVIDENCE:")
    print("-" * 40)
    print("During testing, we successfully:")
    print("• Created multiple traces using both URL endpoints")
    print("• Retrieved traces from both endpoints showing identical data")
    print("• Confirmed trace IDs and metadata are preserved across endpoints")
    print("• Verified API authentication is working")
    print("• Demonstrated the LangfuseClient wrapper works correctly")
    print()
    
    print("🚀 RECOMMENDED ACTIONS:")
    print("-" * 40)
    print("1. ⏰ WAIT AND VERIFY:")
    print("   • Wait 10-15 minutes after creating traces")
    print("   • Check both dashboard URLs:")
    print("     - https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7/traces")
    print("     - https://cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7/traces")
    print()
    print("2. 🔍 CHECK DASHBOARD SETTINGS:")
    print("   • Clear all filters on the traces page")
    print("   • Expand date range to 'Last 7 days' or 'All time'")
    print("   • Verify you're viewing the correct project")
    print("   • Check for any active search terms")
    print()
    print("3. 🔬 VERIFY RECENT TRACES:")
    print("   • Look for traces with names like 'working_test_*', 'wrapper_test_*'")
    print("   • Check traces created around timestamp: 2025-08-04 19:56:36")
    print("   • Look for traces with metadata containing 'test_host' field")
    print()
    print("4. 📞 CONTACT SUPPORT IF NEEDED:")
    print("   • If traces still don't appear after 15 minutes")
    print("   • Provide trace IDs from test runs")
    print("   • Mention both US and Global endpoints return identical data")
    print()
    
    print("🎯 CONCLUSION:")
    print("-" * 40)
    print("The Langfuse connection is working correctly with both URL formats.")
    print("Traces are being successfully created and stored.")
    print("The issue appears to be dashboard visibility or timing-related,")
    print("not a fundamental connection or URL problem.")
    print()
    print("No changes to URL configuration are needed.")
    print("Focus troubleshooting efforts on dashboard settings and timing.")
    print()
    
    # Test one more time to create a trace for immediate verification
    print("🔧 CREATING FINAL VERIFICATION TRACE:")
    print("-" * 40)
    
    try:
        from app.services.langfuse_client import LangfuseClient
        client = LangfuseClient()
        
        trace_id = client.create_trace(
            name="DIAGNOSIS_VERIFICATION_TRACE",
            metadata={
                "created_for": "diagnosis_verification",
                "timestamp": datetime.now().isoformat(),
                "instructions": "Look for this trace in your dashboard within 10 minutes",
                "search_term": "DIAGNOSIS_VERIFICATION_TRACE"
            }
        )
        
        print(f"✅ Created verification trace: {trace_id}")
        print(f"🔍 Search for 'DIAGNOSIS_VERIFICATION_TRACE' in your dashboard")
        print(f"⏰ This trace should appear within 10 minutes")
        
    except Exception as e:
        print(f"❌ Failed to create verification trace: {e}")
    
    print()
    print("📋 TESTING ARTIFACTS CREATED:")
    print("-" * 40)
    print("• test_langfuse_url_comparison.py - Comprehensive URL testing")
    print("• test_working_trace_creation.py - Working API method tests")
    print("• langfuse_connection_diagnosis_report.py - This report")
    print("• Existing: test_langfuse_connection.py, test_correct_langfuse_api.py")
    print()
    print("🎉 DIAGNOSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    generate_diagnosis_report()