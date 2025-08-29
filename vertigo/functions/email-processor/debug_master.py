#!/usr/bin/env python3
"""
MASTER DEBUG SCRIPT: Comprehensive Email Summary Debugging
Runs all debug tests in sequence to systematically identify why meeting summaries 
aren't being emailed to sdulaney@mergeworld.com.

This script orchestrates all individual debug scripts and provides a final diagnosis.
"""

import subprocess
import logging
import sys
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_debug_script(script_name, description):
    """Run a debug script and capture its output."""
    logger.info("=" * 80)
    logger.info(f"RUNNING: {script_name}")
    logger.info(f"PURPOSE: {description}")
    logger.info("=" * 80)
    
    try:
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_name], 
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minute timeout
        )
        
        # Print stdout
        if result.stdout:
            logger.info("SCRIPT OUTPUT:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
        
        # Print stderr if there were errors
        if result.stderr:
            logger.error("SCRIPT ERRORS:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    logger.error(f"  {line}")
        
        success = result.returncode == 0
        logger.info(f"SCRIPT RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        return success, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        logger.error(f"❌ SCRIPT TIMEOUT: {script_name} took longer than 5 minutes")
        return False, "", "Timeout expired"
    except FileNotFoundError:
        logger.error(f"❌ SCRIPT NOT FOUND: {script_name}")
        return False, "", "Script file not found"
    except Exception as e:
        logger.error(f"❌ SCRIPT ERROR: {e}")
        return False, "", str(e)

def analyze_results(results):
    """Analyze all test results and provide diagnosis."""
    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE DIAGNOSIS")
    logger.info("=" * 80)
    
    # Count successes and failures
    total_tests = len(results)
    successful_tests = sum(1 for success, _, _, _ in results if success)
    failed_tests = total_tests - successful_tests
    
    logger.info(f"📊 TEST SUMMARY:")
    logger.info(f"   Total Tests Run: {total_tests}")
    logger.info(f"   Successful: {successful_tests}")
    logger.info(f"   Failed: {failed_tests}")
    logger.info(f"   Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Analyze specific components
    logger.info(f"\n🔍 COMPONENT ANALYSIS:")
    
    component_status = {}
    for script_name, success, stdout, stderr in results:
        if "meeting_processor_response" in script_name:
            component_status['meeting_processor'] = success
        elif "gmail_send_permissions" in script_name:
            component_status['gmail_sending'] = success
        elif "full_pipeline" in script_name:
            component_status['full_pipeline'] = success
        elif "email_classification" in script_name:
            component_status['email_classification'] = success
        elif "logs_and_traces" in script_name:
            component_status['logging_traces'] = success
    
    # Print component status
    for component, status in component_status.items():
        icon = "✅" if status else "❌"
        logger.info(f"   {icon} {component.replace('_', ' ').title()}: {'WORKING' if status else 'ISSUES DETECTED'}")
    
    # Provide specific diagnosis
    logger.info(f"\n🎯 ROOT CAUSE DIAGNOSIS:")
    
    if not component_status.get('meeting_processor', True):
        logger.error("❌ MEETING PROCESSOR ISSUES:")
        logger.error("   • Meeting processor not returning 'processed_notes' field")
        logger.error("   • Email processor can't send empty summaries") 
        logger.error("   • FIX: Check meeting processor cloud function")
        
    elif not component_status.get('gmail_sending', True):
        logger.error("❌ GMAIL SENDING ISSUES:")
        logger.error("   • Gmail API authentication or permissions problems")
        logger.error("   • send_reply() function not working")
        logger.error("   • FIX: Check OAuth tokens and Gmail API setup")
        
    elif not component_status.get('email_classification', True):
        logger.error("❌ EMAIL CLASSIFICATION ISSUES:")
        logger.error("   • Meeting emails being misrouted to wrong handlers")
        logger.error("   • process_meeting_transcript() not being called")
        logger.error("   • FIX: Adjust classification logic in main.py")
        
    elif component_status.get('full_pipeline', False):
        logger.error("❌ PIPELINE INTEGRATION ISSUES:")
        logger.error("   • Individual components work but pipeline fails")
        logger.error("   • Silent failures in the processing chain")
        logger.error("   • FIX: Add more logging and error handling")
        
    else:
        logger.info("✅ ALL COMPONENTS WORKING:")
        logger.info("   • Meeting processor returns valid summaries")
        logger.info("   • Gmail sending permissions work correctly")
        logger.info("   • Email classification routes properly")
        logger.info("   • Issue may be in timing or automation triggers")
    
    # Provide actionable next steps
    logger.info(f"\n🛠️  RECOMMENDED NEXT STEPS:")
    
    if failed_tests == 0:
        logger.info("   1. ✅ All tests passed - check automation triggers")
        logger.info("   2. 🔍 Verify Cloud Function is being called automatically")
        logger.info("   3. 📧 Check if new meeting emails arrive as expected")
        logger.info("   4. ⏰ Confirm processing happens within expected timeframe")
    else:
        logger.info("   1. 🔧 Fix the failed components identified above")
        logger.info("   2. 🧪 Re-run the specific debug scripts that failed")
        logger.info("   3. 📋 Check Cloud Function logs for detailed errors")
        logger.info("   4. 🔄 Test the complete pipeline after fixes")
    
    logger.info(f"\n📞 THOMAS DEBUGGING SUPPORT:")
    logger.info("   • Run individual debug scripts for detailed analysis")
    logger.info("   • Check Google Cloud Console for function logs")
    logger.info("   • Test with a real meeting email end-to-end")
    logger.info("   • Verify Langfuse traces for processing history")

def main():
    """Run the complete debugging suite."""
    logger.info("🚀 STARTING COMPREHENSIVE EMAIL SUMMARY DEBUG SUITE")
    logger.info(f"   Timestamp: {datetime.now().isoformat()}")
    logger.info(f"   Purpose: Debug why meeting summaries aren't emailed to sdulaney@mergeworld.com")
    logger.info(f"   Working Directory: {os.getcwd()}")
    
    # Define debug scripts to run in order
    debug_scripts = [
        ("debug_email_classification.py", "Test email classification logic and routing"),
        ("debug_meeting_processor_response.py", "Verify meeting processor returns 'processed_notes'"),
        ("debug_gmail_send_permissions.py", "Test Gmail API authentication and send permissions"),
        ("debug_logs_and_traces.py", "Check Langfuse traces and processing logs"),
        ("debug_full_pipeline.py", "Test complete email-to-summary pipeline end-to-end"),
    ]
    
    results = []
    
    # Run each debug script
    for script_name, description in debug_scripts:
        if os.path.exists(script_name):
            success, stdout, stderr = run_debug_script(script_name, description)
            results.append((script_name, success, stdout, stderr))
        else:
            logger.error(f"❌ SCRIPT MISSING: {script_name}")
            results.append((script_name, False, "", f"File not found: {script_name}"))
    
    # Analyze results and provide diagnosis
    analyze_results(results)
    
    logger.info("\n" + "=" * 80)
    logger.info("🏁 DEBUG SUITE COMPLETE")
    logger.info("   Review the diagnosis above for next steps")
    logger.info("   Contact Thomas for specific component debugging")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()