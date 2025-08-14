#!/usr/bin/env python3
"""
Test script to demonstrate Langfuse integration with Vertigo workflow.
"""

import os
import sys
from dotenv import load_dotenv
from app.services.langfuse_client import LangfuseClient
import google.generativeai as genai

# Load environment variables
load_dotenv()

def test_langfuse_vertigo_workflow():
    """Test the complete Vertigo workflow with Langfuse integration."""
    
    print("🚀 Testing Vertigo + Langfuse Integration")
    print("=" * 50)
    
    # Initialize Langfuse client
    langfuse_client = LangfuseClient()
    
    # Initialize Gemini
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Sample meeting transcript
    transcript = """
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
    """
    
    # Create a trace for this workflow
    trace_id = langfuse_client.create_trace(
        "vertigo-email-processing",
        {
            "operation": "email_processing",
            "project": "mobile_app_launch",
            "meeting_id": "q4_planning_2024_01_15",
            "source": "email_forward"
        }
    )
    
    print(f"✅ Created Langfuse trace: {trace_id}")
    
    # Create a span for extraction
    extraction_span = langfuse_client.create_span(
        trace_id,
        "semantic_extraction",
        {"input_length": len(transcript)}
    )
    
    print(f"✅ Created extraction span: {extraction_span}")
    
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
    {transcript}
    """
    
    try:
        response = model.generate_content(extraction_prompt.format(transcript=transcript))
        
        # Create a generation span for the LLM call
        generation_id = langfuse_client.create_generation(
            trace_id,
            "gemini-1.5-pro",
            extraction_prompt.format(transcript=transcript),
            response.text,
            {
                "model": "gemini-1.5-pro",
                "operation": "semantic_extraction",
                "input_tokens": len(extraction_prompt),
                "output_tokens": len(response.text)
            }
        )
        
        print(f"✅ Created generation span: {generation_id}")
        print(f"✅ Extracted insights: {len(response.text)} characters")
        
        # Update span with results
        langfuse_client.update_span(extraction_span, {
            "extraction_success": True,
            "output_length": len(response.text)
        })
        
    except Exception as e:
        print(f"❌ Error in extraction: {e}")
        langfuse_client.update_span(extraction_span, {
            "extraction_success": False,
            "error": str(e)
        })
    
    # Create a span for status generation
    status_span = langfuse_client.create_span(
        trace_id,
        "status_generation",
        {"operation": "executive_summary"}
    )
    
    print(f"✅ Created status generation span: {status_span}")
    
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
    
    try:
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
        
        print(f"✅ Created status generation span: {status_generation_id}")
        print(f"✅ Generated status: {len(status_response.text)} characters")
        
        # Update span with results
        langfuse_client.update_span(status_span, {
            "status_success": True,
            "output_length": len(status_response.text)
        })
        
    except Exception as e:
        print(f"❌ Error in status generation: {e}")
        langfuse_client.update_span(status_span, {
            "status_success": False,
            "error": str(e)
        })
    
    print("\n" + "=" * 50)
    print("🎉 Vertigo + Langfuse Integration Test Complete!")
    print(f"📊 Trace ID: {trace_id}")
    print("🔗 Check your Langfuse dashboard for detailed traces")
    print("=" * 50)

if __name__ == "__main__":
    test_langfuse_vertigo_workflow() 