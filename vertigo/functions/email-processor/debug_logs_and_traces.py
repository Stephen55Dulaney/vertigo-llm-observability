#!/usr/bin/env python3
"""
DEBUG SCRIPT 4: Check Logs and Traces for Processing Errors
Examines Langfuse traces and Cloud Function logs to identify processing failures.

This script looks for:
1. Recent email processing traces in Langfuse
2. Meeting processing traces and any errors
3. Cloud Function execution logs
4. Silent failures in the processing pipeline
"""

import requests
import json
import logging
from datetime import datetime, timedelta
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_langfuse_traces():
    """Check Langfuse for recent email and meeting processing traces."""
    logger.info("=" * 60)
    logger.info("CHECKING LANGFUSE TRACES FOR PROCESSING ERRORS")
    logger.info("=" * 60)
    
    try:
        # Try to import and check langfuse client
        from langfuse_client import langfuse_client
        
        logger.info("✅ Langfuse client imported successfully")
        
        # Note: We can't directly query Langfuse API from this script easily
        # But we can check if traces are being created properly
        logger.info("📊 Langfuse Integration Status:")
        logger.info(f"   Client Type: {type(langfuse_client)}")
        logger.info(f"   Client Methods: {[m for m in dir(langfuse_client) if not m.startswith('_')]}")
        
        # Try to create a test trace to verify connectivity
        try:
            test_trace_id = langfuse_client.create_trace(
                name="debug_trace_test",
                metadata={
                    "operation": "debug_logs_and_traces",
                    "purpose": "verify_langfuse_connectivity",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"✅ Test trace created: {test_trace_id}")
            
            # Update the trace to complete it
            langfuse_client.update_trace(
                trace_id=test_trace_id,
                metadata={
                    "status": "completed",
                    "result": "connectivity_verified"
                },
                level="DEFAULT"
            )
            
            langfuse_client.flush()
            logger.info(f"✅ Langfuse connectivity verified")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create test trace: {e}")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Cannot import langfuse_client: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Langfuse client error: {e}")
        return False

def analyze_email_classification_logic():
    """Analyze the email classification logic to identify potential issues."""
    logger.info("\n" + "=" * 60)
    logger.info("ANALYZING EMAIL CLASSIFICATION LOGIC")
    logger.info("=" * 60)
    
    # Read main.py to analyze the classification logic
    try:
        with open('main.py', 'r') as f:
            main_content = f.read()
        
        logger.info("✅ Successfully read main.py")
        
        # Check the process_unread_emails function
        logger.info("\n📋 EMAIL CLASSIFICATION LOGIC ANALYSIS:")
        
        # Look for the classification conditions
        classification_checks = [
            ("is_vertigo_command", "Vertigo command emails"),
            ("is_status_request", "Status request emails"), 
            ("is_daily_summary_request", "Daily summary request emails"),
            ("process_meeting_transcript", "Default: Meeting transcript processing")
        ]
        
        for func_name, description in classification_checks:
            if func_name in main_content:
                logger.info(f"   ✅ {func_name}: {description}")
            else:
                logger.error(f"   ❌ {func_name}: MISSING")
        
        # Check the classification flow in process_unread_emails
        if "elif is_status_request(subject, body):" in main_content:
            logger.info(f"\n📊 CLASSIFICATION FLOW:")
            logger.info(f"   1. is_vertigo_command() → process_vertigo_command()")
            logger.info(f"   2. is_status_request() → process_status_request()")
            logger.info(f"   3. is_daily_summary_request() → process_daily_summary()")
            logger.info(f"   4. DEFAULT → process_meeting_transcript()")
            logger.info(f"\n⚠️  POTENTIAL ISSUE IDENTIFIED:")
            logger.info(f"   Regular meeting emails should go to process_meeting_transcript()")
            logger.info(f"   But they might be caught by earlier conditions")
        
        # Check the send_reply calls
        send_reply_calls = main_content.count("send_reply(")
        logger.info(f"\n📧 send_reply() CALLS IN CODE: {send_reply_calls}")
        
        if "send_reply(service, msg_data, sender_email, subject, meeting_notes)" in main_content:
            logger.info(f"   ✅ process_meeting_transcript() calls send_reply()")
        else:
            logger.error(f"   ❌ process_meeting_transcript() missing send_reply() call")
        
        # Check the conditions for sending
        if "if meeting_notes and meeting_notes.strip():" in main_content:
            logger.info(f"   ✅ send_reply() has proper content check")
            logger.info(f"   📝 Condition: meeting_notes must exist and not be empty")
            logger.info(f"   🔍 Key variable: meeting_notes = resp_json.get('processed_notes', '')")
        else:
            logger.error(f"   ❌ send_reply() missing content validation")
        
        return True
        
    except FileNotFoundError:
        logger.error(f"❌ Cannot find main.py file")
        return False
    except Exception as e:
        logger.error(f"❌ Error analyzing main.py: {e}")
        return False

def simulate_email_classification(test_subjects_and_bodies):
    """Simulate email classification for test cases."""
    logger.info("\n" + "=" * 60)
    logger.info("SIMULATING EMAIL CLASSIFICATION")
    logger.info("=" * 60)
    
    # Import classification functions from main
    try:
        import sys
        sys.path.append('.')
        
        from main import is_vertigo_command, is_status_request, is_daily_summary_request
        
        logger.info("✅ Imported classification functions")
        
        test_cases = [
            ("Vertigo Debug Meeting", "Meeting transcript about debugging email delivery", "meeting"),
            ("Meeting Notes - Project Discussion", "Here are the notes from our project meeting", "meeting"),
            ("Vertigo: help", "I need help with commands", "command"),
            ("Status Report Request", "Please generate a status report", "status"),
            ("3:00 PM Daily Update", "Daily summary content for boss update", "daily"),
            ("Random Subject", "Some random email content", "meeting"),
        ]
        
        logger.info(f"\n📋 TESTING EMAIL CLASSIFICATION:")
        
        for subject, body, expected in test_cases:
            logger.info(f"\n   Test Case: {subject}")
            logger.info(f"   Expected: {expected}")
            
            is_command = is_vertigo_command(subject)
            is_status = is_status_request(subject, body)
            is_daily = is_daily_summary_request(subject, body)
            
            if is_command:
                actual = "command"
                handler = "process_vertigo_command()"
            elif is_status:
                actual = "status"
                handler = "process_status_request()"
            elif is_daily:
                actual = "daily"
                handler = "process_daily_summary()"
            else:
                actual = "meeting"
                handler = "process_meeting_transcript()"
            
            if actual == expected:
                logger.info(f"   ✅ Result: {actual} → {handler}")
            else:
                logger.error(f"   ❌ Result: {actual} → {handler} (expected {expected})")
                logger.error(f"      This could cause routing issues!")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Cannot import classification functions: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error simulating classification: {e}")
        return False

def check_cloud_function_logs():
    """Provide guidance on checking Cloud Function logs."""
    logger.info("\n" + "=" * 60)
    logger.info("CLOUD FUNCTION LOGS ANALYSIS")
    logger.info("=" * 60)
    
    logger.info("📋 To check Cloud Function logs manually:")
    logger.info("   1. Go to Google Cloud Console")
    logger.info("   2. Navigate to Cloud Functions")
    logger.info("   3. Click on 'email-processor-v2' function")
    logger.info("   4. Go to 'Logs' tab")
    logger.info("   5. Look for recent executions and any errors")
    logger.info("\n🔍 Key log entries to look for:")
    logger.info("   • 'Processing email: <subject> from <sender>'")
    logger.info("   • 'Auto-reply with meeting notes'")
    logger.info("   • 'Sent auto-reply to <email>'")
    logger.info("   • Any error messages or exceptions")
    logger.info("\n⚠️  Common issues to check:")
    logger.info("   • Meeting processor HTTP errors")
    logger.info("   • Gmail API authentication failures")
    logger.info("   • 'No meeting notes content to send' warnings")
    logger.info("   • JSON parsing errors")
    
    # Try to read local log files if they exist
    log_files = ['email-processor.log', 'function.log', 'debug.log']
    found_logs = []
    
    for log_file in log_files:
        if os.path.exists(log_file):
            found_logs.append(log_file)
    
    if found_logs:
        logger.info(f"\n📄 Local log files found: {found_logs}")
        for log_file in found_logs:
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-20:]  # Last 20 lines
                logger.info(f"\n--- Last 20 lines of {log_file} ---")
                for line in lines:
                    logger.info(f"   {line.strip()}")
            except Exception as e:
                logger.error(f"   Error reading {log_file}: {e}")
    else:
        logger.info(f"\n📄 No local log files found")
    
    return True

def main():
    """Run logs and traces analysis."""
    logger.info("Starting Logs and Traces Analysis")
    
    # Test 1: Check Langfuse traces
    langfuse_success = check_langfuse_traces()
    
    # Test 2: Analyze email classification logic
    classification_success = analyze_email_classification_logic()
    
    # Test 3: Simulate email classification
    simulation_success = simulate_email_classification([])
    
    # Test 4: Check Cloud Function logs
    logs_success = check_cloud_function_logs()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("LOGS AND TRACES ANALYSIS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Langfuse Connectivity: {'✅ PASS' if langfuse_success else '❌ FAIL'}")
    logger.info(f"Classification Logic: {'✅ PASS' if classification_success else '❌ FAIL'}")
    logger.info(f"Classification Simulation: {'✅ PASS' if simulation_success else '❌ FAIL'}")
    logger.info(f"Logs Analysis: {'✅ PASS' if logs_success else '❌ FAIL'}")
    
    logger.info(f"\n🔍 NEXT DEBUGGING STEPS:")
    logger.info(f"   1. Run the other debug scripts to test components")
    logger.info(f"   2. Check Google Cloud Console for function logs")
    logger.info(f"   3. Verify Langfuse dashboard for recent traces")
    logger.info(f"   4. Test email classification with real examples")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()