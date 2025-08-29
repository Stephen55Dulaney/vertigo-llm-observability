#!/usr/bin/env python3
"""
DEBUG SCRIPT 1: Test Meeting Processor Response Format
Tests if meeting processor returns 'processed_notes' field correctly.

This script directly calls the meeting processor cloud function to verify:
1. The endpoint is accessible
2. Response contains 'processed_notes' field
3. Response format matches what email processor expects
"""

import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Meeting processor endpoint
MEETING_PROCESSOR_URL = "https://us-central1-vertigo-466116.cloudfunctions.net/meeting-processor-v2"

def test_meeting_processor_response():
    """Test meeting processor with sample transcript and check response format."""
    
    # Sample meeting transcript (similar to what would come from email)
    sample_payload = {
        "transcript": """
Meeting about Vertigo project progress:

We discussed the current status of the email processing system. The meeting processor is working correctly and storing summaries in Firestore. However, we discovered that the email replies containing meeting summaries are not being sent to users.

Key issues identified:
- Email processor should call send_reply() after getting meeting notes
- Need to verify Gmail API permissions for sending emails
- Check if 'processed_notes' field exists in meeting processor response

Action items:
- Debug the email sending pipeline
- Test send_reply() function independently
- Verify all components are working end-to-end
        """.strip(),
        "transcript_type": "dictation",
        "project": "vertigo",
        "participants": [],
        "duration_minutes": 15,
        "meeting_title": "Debug Meeting Summary Email Issue"
    }
    
    logger.info("=" * 60)
    logger.info("TESTING MEETING PROCESSOR RESPONSE FORMAT")
    logger.info("=" * 60)
    
    try:
        logger.info(f"Calling meeting processor: {MEETING_PROCESSOR_URL}")
        logger.info(f"Payload: {json.dumps(sample_payload, indent=2)}")
        
        response = requests.post(MEETING_PROCESSOR_URL, json=sample_payload, timeout=60)
        
        logger.info(f"\nHTTP Status Code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            logger.error(f"❌ MEETING PROCESSOR FAILED")
            logger.error(f"Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
        
        # Parse JSON response
        try:
            resp_json = response.json()
            logger.info(f"\n✅ MEETING PROCESSOR SUCCESS")
            logger.info(f"Response JSON Keys: {list(resp_json.keys())}")
            
            # Check for required fields
            required_fields = ['meeting_id', 'processed_notes', 'project', 'stored_at']
            missing_fields = []
            
            for field in required_fields:
                if field in resp_json:
                    logger.info(f"✅ Field '{field}' EXISTS")
                    if field == 'processed_notes':
                        notes = resp_json[field]
                        logger.info(f"   processed_notes length: {len(notes) if notes else 0}")
                        logger.info(f"   processed_notes preview: {notes[:200] if notes else 'EMPTY'}...")
                else:
                    logger.error(f"❌ Field '{field}' MISSING")
                    missing_fields.append(field)
            
            # Critical test: Does processed_notes have content?
            processed_notes = resp_json.get('processed_notes', '')
            if processed_notes and processed_notes.strip():
                logger.info(f"\n✅ PROCESSED_NOTES HAS CONTENT")
                logger.info(f"   Length: {len(processed_notes)}")
                logger.info(f"   Preview: {processed_notes[:300]}...")
                
                # This is what email processor would get
                logger.info(f"\n📧 EMAIL PROCESSOR WOULD RECEIVE:")
                logger.info(f"   meeting_notes = resp_json.get('processed_notes', '') = '{processed_notes[:100]}...'")
                logger.info(f"   len(meeting_notes) = {len(processed_notes)}")
                logger.info(f"   bool(meeting_notes.strip()) = {bool(processed_notes.strip())}")
                
                return True
            else:
                logger.error(f"\n❌ PROCESSED_NOTES IS EMPTY OR MISSING")
                logger.error(f"   Value: {repr(processed_notes)}")
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ FAILED TO PARSE JSON RESPONSE")
            logger.error(f"Error: {e}")
            logger.error(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"❌ REQUEST TIMEOUT after 60 seconds")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ REQUEST FAILED: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    """Run the meeting processor response test."""
    logger.info("Starting Meeting Processor Response Format Debug Test")
    
    success = test_meeting_processor_response()
    
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✅ CONCLUSION: Meeting processor returns proper 'processed_notes' field")
        logger.info("   The issue is likely in email processor or Gmail sending")
    else:
        logger.error("❌ CONCLUSION: Meeting processor NOT returning 'processed_notes' properly")
        logger.error("   This is the root cause - email processor has no content to send")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()