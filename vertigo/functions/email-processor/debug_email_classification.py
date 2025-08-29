#!/usr/bin/env python3
"""
DEBUG SCRIPT 5: Test Email Classification Logic
Tests the email classification logic to ensure meeting emails trigger the correct handler.

This script tests:
1. is_vertigo_command() function with various subjects
2. is_status_request() function with various subjects/bodies
3. is_daily_summary_request() function with various subjects/bodies  
4. Default routing to process_meeting_transcript()
5. Edge cases that might cause misclassification
"""

import logging
import sys
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path to import from main.py
sys.path.append('.')

def test_vertigo_commands():
    """Test is_vertigo_command() function with various inputs."""
    logger.info("=" * 60)
    logger.info("TESTING is_vertigo_command() FUNCTION")
    logger.info("=" * 60)
    
    try:
        from main import is_vertigo_command
        
        test_cases = [
            # Should be TRUE (Vertigo commands)
            ("Vertigo: help", True),
            ("vertigo: help", True),
            ("Re: Vertigo: list this week", True),
            ("Fwd: Vertigo: total stats", True),
            ("VERTIGO: LIST PROJECTS", True),
            ("Vertigo: prompt report", True),
            
            # Should be FALSE (not Vertigo commands)
            ("Meeting about Vertigo project", False),
            ("Vertigo project discussion", False),
            ("Status update for Vertigo", False),
            ("Daily summary - Vertigo work", False),
            ("Random email subject", False),
            ("", False),
        ]
        
        logger.info("📋 Testing is_vertigo_command():")
        
        all_correct = True
        for subject, expected in test_cases:
            result = is_vertigo_command(subject)
            status = "✅" if result == expected else "❌"
            
            logger.info(f"   {status} '{subject}' → {result} (expected {expected})")
            
            if result != expected:
                all_correct = False
                logger.error(f"      MISCLASSIFICATION DETECTED!")
        
        if all_correct:
            logger.info(f"\n✅ is_vertigo_command() working correctly")
        else:
            logger.error(f"\n❌ is_vertigo_command() has classification issues")
        
        return all_correct
        
    except ImportError as e:
        logger.error(f"❌ Cannot import is_vertigo_command: {e}")
        return False

def test_status_requests():
    """Test is_status_request() function with various inputs."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING is_status_request() FUNCTION")
    logger.info("=" * 60)
    
    try:
        from main import is_status_request
        
        test_cases = [
            # Should be TRUE (status requests)
            ("Status Request", "Please generate a status report", True),
            ("Generate Status", "I need a project status", True),
            ("Weekly Status", "What's our status?", True),
            ("Project Update", "Give me a status summary", True),
            ("Random Subject", "Please generate status for the project", True),
            
            # Should be FALSE (not status requests)
            ("Meeting Notes", "Here is the meeting transcript", False),
            ("Daily Summary", "3:00 PM update content", False),
            ("Vertigo: help", "Need command help", False),
            ("Project Discussion", "Let's discuss the project", False),
            ("", "", False),
        ]
        
        logger.info("📋 Testing is_status_request():")
        
        all_correct = True
        for subject, body, expected in test_cases:
            result = is_status_request(subject, body)
            status = "✅" if result == expected else "❌"
            
            logger.info(f"   {status} '{subject}' / '{body[:30]}...' → {result} (expected {expected})")
            
            if result != expected:
                all_correct = False
                logger.error(f"      MISCLASSIFICATION DETECTED!")
        
        if all_correct:
            logger.info(f"\n✅ is_status_request() working correctly")
        else:
            logger.error(f"\n❌ is_status_request() has classification issues")
        
        return all_correct
        
    except ImportError as e:
        logger.error(f"❌ Cannot import is_status_request: {e}")
        return False

def test_daily_summary_requests():
    """Test is_daily_summary_request() function with various inputs."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING is_daily_summary_request() FUNCTION")
    logger.info("=" * 60)
    
    try:
        from main import is_daily_summary_request
        
        test_cases = [
            # Should be TRUE (daily summary requests)
            ("3:00 PM Update", "Daily summary content", True),
            ("Daily Summary", "Boss update for today", True),
            ("3pm Update", "End of day summary", True),
            ("Boss Update", "Daily update content", True),
            ("Random Subject", "This is a 3:00 pm daily summary", True),
            
            # Should be FALSE (not daily summary requests)
            ("Meeting Notes", "Here is the meeting transcript", False),
            ("Status Request", "Generate status report", False),
            ("Project Discussion", "Let's discuss the project", False),
            ("Vertigo: help", "Need command help", False),
            ("", "", False),
        ]
        
        logger.info("📋 Testing is_daily_summary_request():")
        
        all_correct = True
        for subject, body, expected in test_cases:
            result = is_daily_summary_request(subject, body)
            status = "✅" if result == expected else "❌"
            
            logger.info(f"   {status} '{subject}' / '{body[:30]}...' → {result} (expected {expected})")
            
            if result != expected:
                all_correct = False
                logger.error(f"      MISCLASSIFICATION DETECTED!")
        
        if all_correct:
            logger.info(f"\n✅ is_daily_summary_request() working correctly")
        else:
            logger.error(f"\n❌ is_daily_summary_request() has classification issues")
        
        return all_correct
        
    except ImportError as e:
        logger.error(f"❌ Cannot import is_daily_summary_request: {e}")
        return False

def test_meeting_transcript_routing():
    """Test emails that should route to process_meeting_transcript()."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING MEETING TRANSCRIPT ROUTING")
    logger.info("=" * 60)
    
    try:
        from main import is_vertigo_command, is_status_request, is_daily_summary_request
        
        # These should all route to process_meeting_transcript (default case)
        test_cases = [
            ("Meeting Notes - Vertigo Debug", "Here is the transcript from our debugging session..."),
            ("Project Discussion", "We discussed the email delivery issue..."),
            ("Team Standup", "Today we worked on fixing the summary emails..."),
            ("Debug Session Notes", "Meeting transcript about why summaries aren't being sent..."),
            ("Weekly Review", "Here are the notes from our weekly review meeting..."),
            ("Architecture Discussion", "We talked about the system architecture..."),
            ("Random Meeting Subject", "Some meeting content here..."),
        ]
        
        logger.info("📋 Testing meeting transcript routing:")
        
        all_correct = True
        for subject, body in test_cases:
            is_command = is_vertigo_command(subject)
            is_status = is_status_request(subject, body)
            is_daily = is_daily_summary_request(subject, body)
            
            # Should route to meeting transcript if all others are false
            routes_to_meeting = not (is_command or is_status or is_daily)
            
            if routes_to_meeting:
                logger.info(f"   ✅ '{subject}' → process_meeting_transcript()")
            else:
                logger.error(f"   ❌ '{subject}' → NOT process_meeting_transcript()")
                logger.error(f"      Routes to: {'command' if is_command else 'status' if is_status else 'daily'}")
                all_correct = False
        
        if all_correct:
            logger.info(f"\n✅ Meeting transcript routing working correctly")
        else:
            logger.error(f"\n❌ Meeting transcript routing has issues")
            logger.error(f"   Some meeting emails are being misclassified!")
        
        return all_correct
        
    except ImportError as e:
        logger.error(f"❌ Cannot import classification functions: {e}")
        return False

def test_edge_cases():
    """Test edge cases that might cause classification problems."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING EDGE CASES")
    logger.info("=" * 60)
    
    try:
        from main import is_vertigo_command, is_status_request, is_daily_summary_request
        
        edge_cases = [
            # Empty or minimal content
            ("", ""),
            ("Subject only", ""),
            ("", "Body only content"),
            
            # Mixed signals
            ("Vertigo Meeting Status", "This meeting is about status but not a command"),
            ("Status of Vertigo: help request", "Mixed command and status keywords"),
            ("3:00 PM Vertigo Status", "Mixed daily and status and command keywords"),
            
            # Case sensitivity
            ("VERTIGO: HELP", "uppercase command"),
            ("status request", "lowercase status"),
            ("3:00 pm daily", "lowercase daily"),
            
            # Special characters
            ("Re: Fwd: Meeting Notes", "Multiple reply prefixes"),
            ("Subject with: colons", "Colons that aren't commands"),
            ("Meeting (Urgent)", "Parentheses in subject"),
        ]
        
        logger.info("📋 Testing edge cases:")
        
        for subject, body in edge_cases:
            is_command = is_vertigo_command(subject)
            is_status = is_status_request(subject, body) 
            is_daily = is_daily_summary_request(subject, body)
            
            routes_to_meeting = not (is_command or is_status or is_daily)
            
            if routes_to_meeting:
                handler = "process_meeting_transcript()"
            elif is_command:
                handler = "process_vertigo_command()"
            elif is_status:
                handler = "process_status_request()"  
            elif is_daily:
                handler = "process_daily_summary()"
            
            logger.info(f"   📧 '{subject}' / '{body[:20]}...' → {handler}")
        
        logger.info(f"\n✅ Edge cases tested - review routing above")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Cannot import classification functions: {e}")
        return False

def analyze_real_world_scenarios():
    """Analyze real-world scenarios based on the user's description."""
    logger.info("\n" + "=" * 60)
    logger.info("ANALYZING REAL-WORLD SCENARIOS")
    logger.info("=" * 60)
    
    logger.info("🔍 Based on the issue description, analyzing likely email patterns:")
    
    # These are the types of emails the user is likely sending
    real_scenarios = [
        ("Meeting transcript from debugging session", 
         "Here is the transcript from our debugging session about why meeting summaries aren't being emailed..."),
        
        ("Project meeting notes",
         "Meeting notes from our Vertigo project discussion today..."),
        
        ("Debug session notes",
         "We investigated the email delivery pipeline and found several potential issues..."),
        
        ("Team meeting transcript", 
         "Today's team meeting covered the following topics..."),
    ]
    
    try:
        from main import is_vertigo_command, is_status_request, is_daily_summary_request
        
        logger.info("📋 Real-world scenario analysis:")
        
        for subject, body in real_scenarios:
            is_command = is_vertigo_command(subject)
            is_status = is_status_request(subject, body)
            is_daily = is_daily_summary_request(subject, body)
            
            routes_to_meeting = not (is_command or is_status or is_daily)
            
            if routes_to_meeting:
                logger.info(f"   ✅ '{subject}' → process_meeting_transcript()")
                logger.info(f"      This SHOULD generate and email a summary")
            else:
                logger.error(f"   ❌ '{subject}' → NOT process_meeting_transcript()")
                logger.error(f"      This explains why no summary emails are sent!")
                
                if is_command:
                    logger.error(f"      Incorrectly routed to: process_vertigo_command()")
                elif is_status:
                    logger.error(f"      Incorrectly routed to: process_status_request()")
                elif is_daily:
                    logger.error(f"      Incorrectly routed to: process_daily_summary()")
        
        logger.info(f"\n🎯 ROOT CAUSE ANALYSIS:")
        logger.info(f"   If real meeting emails are being misrouted, this explains")
        logger.info(f"   why no summary emails are being sent to sdulaney@mergeworld.com")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Cannot import classification functions: {e}")
        return False

def main():
    """Run the complete email classification debug test."""
    logger.info("Starting Email Classification Logic Debug Test")
    
    # Test all classification functions
    vertigo_success = test_vertigo_commands()
    status_success = test_status_requests() 
    daily_success = test_daily_summary_requests()
    meeting_success = test_meeting_transcript_routing()
    edge_success = test_edge_cases()
    real_success = analyze_real_world_scenarios()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("EMAIL CLASSIFICATION DEBUG SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Vertigo Commands: {'✅ PASS' if vertigo_success else '❌ FAIL'}")
    logger.info(f"Status Requests: {'✅ PASS' if status_success else '❌ FAIL'}")
    logger.info(f"Daily Summaries: {'✅ PASS' if daily_success else '❌ FAIL'}")
    logger.info(f"Meeting Routing: {'✅ PASS' if meeting_success else '❌ FAIL'}")
    logger.info(f"Edge Cases: {'✅ PASS' if edge_success else '❌ FAIL'}")
    logger.info(f"Real Scenarios: {'✅ PASS' if real_success else '❌ FAIL'}")
    
    all_success = all([vertigo_success, status_success, daily_success, meeting_success, edge_success, real_success])
    
    if all_success:
        logger.info(f"\n✅ CLASSIFICATION LOGIC WORKING CORRECTLY")
        logger.info(f"   Meeting emails should properly route to process_meeting_transcript()")
        logger.info(f"   Issue is likely in a different part of the pipeline")
    else:
        logger.error(f"\n❌ CLASSIFICATION ISSUES DETECTED")
        logger.error(f"   Some meeting emails may be misrouted")
        logger.error(f"   This could explain why summaries aren't being sent")
    
    logger.info(f"\n🔍 NEXT DEBUGGING STEPS:")
    logger.info(f"   1. Run debug_meeting_processor_response.py")
    logger.info(f"   2. Run debug_gmail_send_permissions.py") 
    logger.info(f"   3. Run debug_full_pipeline.py")
    logger.info(f"   4. Check Cloud Function logs for actual processing")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()