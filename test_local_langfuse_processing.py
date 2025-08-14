#!/usr/bin/env python3
"""
Test local email processing with Langfuse tracing to verify integration before cloud deployment.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the email processor directory to path to import langfuse_client
sys.path.append('vertigo/functions/email-processor')

try:
    from langfuse_client import langfuse_client
    print("✅ Successfully imported langfuse_client")
except ImportError as e:
    print(f"❌ Failed to import langfuse_client: {e}")
    sys.exit(1)

def test_langfuse_connection():
    """Test basic Langfuse connection and trace creation."""
    print("🔍 Testing Langfuse connection...")
    
    if not langfuse_client.is_enabled():
        print("❌ Langfuse client is not enabled. Check credentials.")
        return False
    
    print("✅ Langfuse client is enabled")
    
    # Test creating a trace
    trace_id = langfuse_client.create_trace(
        name="test_local_trace",
        metadata={
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "source": "local_test"
        }
    )
    
    if trace_id:
        print(f"✅ Created test trace: {trace_id}")
        
        # Test updating the trace
        success = langfuse_client.update_trace(
            trace_id=trace_id,
            metadata={
                "completed": True,
                "status": "success"
            },
            output={"result": "Test trace completed successfully"},
            level="DEFAULT"
        )
        
        if success:
            print("✅ Successfully updated trace")
        else:
            print("❌ Failed to update trace")
        
        # Flush the trace
        langfuse_client.flush()
        print("✅ Flushed trace to Langfuse")
        
        return True
    else:
        print("❌ Failed to create trace")
        return False

def simulate_email_processing():
    """Simulate email processing with Langfuse tracing."""
    print("\n📧 Simulating email processing with Langfuse tracing...")
    
    # Create main trace for email processing
    trace_id = langfuse_client.create_trace(
        name="local_email_processing_simulation",
        metadata={
            "operation": "simulate_email_processing",
            "service": "local_test",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    if not trace_id:
        print("❌ Failed to create main trace")
        return False
    
    print(f"✅ Created main trace: {trace_id}")
    
    # Simulate processing different types of emails
    test_emails = [
        {
            "subject": "Vertigo: Help",
            "body": "Please send me help information",
            "type": "help_command"
        },
        {
            "subject": "Meeting Notes - Sprint Planning",
            "body": "We discussed the implementation plan for Q4...",
            "type": "meeting_transcript"
        },
        {
            "subject": "3:00 PM Daily Summary",
            "body": "Today's progress on the Vertigo project...",
            "type": "daily_summary"
        }
    ]
    
    for i, email_data in enumerate(test_emails, 1):
        print(f"\n📧 Processing simulated email {i}: {email_data['subject']}")
        
        # Create span for individual email processing
        email_span_id = langfuse_client.create_span(
            trace_id=trace_id,
            name="process_simulated_email",
            metadata={
                "email_number": i,
                "subject": email_data["subject"],
                "type": email_data["type"],
                "simulated": True
            }
        )
        
        print(f"✅ Created email processing span")
        
        # Simulate some processing based on email type
        if email_data["type"] == "help_command":
            print("   🤖 Processing help command...")
        elif email_data["type"] == "meeting_transcript":
            print("   📝 Processing meeting transcript...")
        elif email_data["type"] == "daily_summary":
            print("   📊 Processing daily summary...")
    
    # Update main trace with results
    success = langfuse_client.update_trace(
        trace_id=trace_id,
        metadata={
            "processed_count": len(test_emails),
            "total_emails": len(test_emails),
            "success": True,
            "simulation": True
        },
        output={
            "processed_count": len(test_emails),
            "total_emails": len(test_emails),
            "email_types": [email["type"] for email in test_emails]
        },
        level="DEFAULT"
    )
    
    if success:
        print("✅ Updated main trace with results")
    else:
        print("❌ Failed to update main trace")
    
    # Flush all traces
    langfuse_client.flush()
    print("✅ Flushed all traces to Langfuse")
    
    return True

if __name__ == "__main__":
    print("🚀 Testing Local Langfuse Integration")
    print("=" * 50)
    
    # Test basic connection
    if test_langfuse_connection():
        print("\n" + "=" * 50)
        
        # Test email processing simulation
        if simulate_email_processing():
            print("\n" + "=" * 50)
            print("✅ All tests completed successfully!")
            print("\n📈 Check your Langfuse dashboard for new traces:")
            print("   https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7/traces")
            print("\nExpected traces:")
            print("   1. 'test_local_trace' - Basic connection test")
            print("   2. 'local_email_processing_simulation' - Email processing simulation")
            print("   3. Multiple 'process_simulated_email' spans within the main trace")
        else:
            print("\n❌ Email processing simulation failed")
    else:
        print("\n❌ Langfuse connection test failed")
        print("\nTroubleshooting:")
        print("1. Check LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env file")
        print("2. Verify LANGFUSE_HOST is set to https://us.cloud.langfuse.com")
        print("3. Ensure Langfuse credentials are valid and active")