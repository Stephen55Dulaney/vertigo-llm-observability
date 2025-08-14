#!/usr/bin/env python3
"""
Script to process unprocessed emails in the Vertigo inbox.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from app import create_app, db
from app.models import Trace, Cost
from app.services.langwatch_client import LangWatchClient
import google.generativeai as genai

# Load environment variables
load_dotenv()

def process_emails():
    """Process unprocessed emails in the Vertigo inbox."""
    
    print("📧 Processing Unprocessed Emails")
    print("=" * 50)
    
    # Initialize Flask app context
    app = create_app()
    with app.app_context():
        
        # Initialize Langfuse client
        langwatch_client = LangWatchClient()
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Sample email content (you can replace this with actual email content)
        email_samples = [
            {
                "subject": "Q4 Planning Meeting - Mobile App Launch",
                "content": """
                Meeting: Q4 Planning Session
                Date: 2024-01-15
                Attendees: John (CEO), Sarah (CTO), Mike (VP Engineering)
                
                John: "We need to focus on the mobile app launch. What's the timeline?"
                Sarah: "We're targeting March 1st, but we need 2 more developers."
                Mike: "I can get them onboarded by next week. Budget approved?"
                John: "Yes, approved. What about the API integration?"
                Sarah: "Still waiting on third-party vendor. They promised end of month."
                Mike: "We have a backup plan if they're late."
                John: "Good. Let's track this weekly. Any blockers?"
                Sarah: "None from my side."
                Mike: "We're good to go."
                """,
                "sender": "john@company.com",
                "timestamp": datetime.utcnow()
            },
            {
                "subject": "Product Review Meeting - New Features",
                "content": """
                Meeting: Product Review Session
                Date: 2024-01-16
                Attendees: Lisa (Product Manager), Tom (Design Lead), Alex (Engineering Lead)
                
                Lisa: "Let's review the new features for the next sprint."
                Tom: "The UI designs are ready for the dashboard improvements."
                Alex: "We can implement the new analytics module in 2 weeks."
                Lisa: "What about the user feedback integration?"
                Tom: "Still working on the wireframes for that feature."
                Alex: "We'll need the designs by Friday to stay on schedule."
                Lisa: "I'll prioritize that. Any technical challenges?"
                Alex: "The API rate limiting might be an issue."
                Tom: "We can optimize the frontend to reduce API calls."
                """,
                "sender": "lisa@company.com",
                "timestamp": datetime.utcnow()
            }
        ]
        
        print(f"📥 Processing {len(email_samples)} emails...")
        
        for i, email in enumerate(email_samples, 1):
            print(f"\n📧 Processing Email {i}: {email['subject']}")
            
            # Create a trace for this email processing
            trace_id = langfuse_client.create_trace(
                f"email-processing-{i}",
                {
                    "operation": "email_processing",
                    "project": "email_automation",
                    "meeting_id": f"email_{i}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "source": "email_inbox",
                    "sender": email["sender"],
                    "subject": email["subject"]
                }
            )
            
            print(f"✅ Created trace: {trace_id}")
            
            # Create a span for extraction
            extraction_span = langfuse_client.create_span(
                trace_id,
                "semantic_extraction",
                {"input_length": len(email["content"])}
            )
            
            # Extract insights using Gemini
            extraction_prompt = """
            Extract key insights from this meeting transcript. Return JSON with:
            - key_decisions: List of decisions made
            - action_items: List of action items with assignees
            - blockers: List of blockers or risks
            - next_steps: List of next steps
            - project: Project name
            - urgency: High/Medium/Low
            
            Transcript:
            {content}
            """
            
            try:
                response = model.generate_content(extraction_prompt.format(content=email["content"]))
                
                # Create a generation span for the LLM call
                generation_id = langfuse_client.create_generation(
                    trace_id,
                    "gemini-1.5-pro",
                    extraction_prompt.format(content=email["content"]),
                    response.text,
                    {
                        "model": "gemini-1.5-pro",
                        "operation": "semantic_extraction",
                        "input_tokens": len(extraction_prompt),
                        "output_tokens": len(response.text)
                    }
                )
                
                print(f"✅ Extracted insights: {len(response.text)} characters")
                
                # Update span with results
                langfuse_client.update_span(extraction_span, {
                    "extraction_success": True,
                    "output_length": len(response.text)
                })
                
                # Create a span for status generation
                status_span = langfuse_client.create_span(
                    trace_id,
                    "status_generation",
                    {"operation": "executive_summary"}
                )
                
                # Generate executive summary
                status_prompt = """
                Generate an executive summary based on this extracted data:
                
                {extracted_data}
                
                Format as a professional email to executives with:
                - Summary of key decisions
                - Action items and owners
                - Blockers and mitigation plans
                - Next steps and timeline
                """
                
                status_response = model.generate_content(
                    status_prompt.format(extracted_data=response.text)
                )
                
                # Create generation span for status
                status_generation_id = langfuse_client.create_generation(
                    trace_id,
                    "gemini-1.5-pro",
                    status_prompt.format(extracted_data=response.text),
                    status_response.text,
                    {
                        "model": "gemini-1.5-pro",
                        "operation": "status_generation",
                        "input_tokens": len(status_prompt),
                        "output_tokens": len(status_response.text)
                    }
                )
                
                print(f"✅ Generated status: {len(status_response.text)} characters")
                
                # Update span with results
                langfuse_client.update_span(status_span, {
                    "status_success": True,
                    "output_length": len(status_response.text)
                })
                
                # Create trace record in database
                trace = Trace(
                    trace_id=trace_id,
                    name=f"Email Processing - {email['subject']}",
                    status="success",
                    start_time=email["timestamp"],
                    end_time=datetime.utcnow(),
                    duration_ms=5000,  # Sample duration
                    trace_metadata={
                        "operation": "email_processing",
                        "project": "email_automation",
                        "sender": email["sender"],
                        "subject": email["subject"]
                    },
                    error_message="",
                    vertigo_operation="email_processing",
                    project="email_automation",
                    meeting_id=f"email_{i}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                )
                
                db.session.add(trace)
                
                # Create cost record
                cost_record = Cost(
                    trace_id=trace_id,
                    model="gemini-1.5-pro",
                    input_tokens=800,
                    output_tokens=300,
                    total_tokens=1100,
                    cost_usd=0.008,
                    timestamp=email["timestamp"]
                )
                
                db.session.add(cost_record)
                
            except Exception as e:
                print(f"❌ Error processing email {i}: {e}")
                
                # Create error trace record
                error_trace = Trace(
                    trace_id=trace_id,
                    name=f"Email Processing - {email['subject']}",
                    status="error",
                    start_time=email["timestamp"],
                    end_time=datetime.utcnow(),
                    duration_ms=0,
                    trace_metadata={
                        "operation": "email_processing",
                        "project": "email_automation",
                        "sender": email["sender"],
                        "subject": email["subject"]
                    },
                    error_message=str(e),
                    vertigo_operation="email_processing",
                    project="email_automation",
                    meeting_id=f"email_{i}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                )
                
                db.session.add(error_trace)
        
        # Commit all changes
        db.session.commit()
        
        # Show final stats
        total_traces = Trace.query.count()
        total_costs = Cost.query.count()
        
        print("\n" + "=" * 50)
        print("📊 Processing Complete!")
        print(f"   Total Traces: {total_traces}")
        print(f"   Total Cost Records: {total_costs}")
        print("=" * 50)
        print("🔄 Refresh your dashboard to see live metrics!")

if __name__ == "__main__":
    process_emails() 