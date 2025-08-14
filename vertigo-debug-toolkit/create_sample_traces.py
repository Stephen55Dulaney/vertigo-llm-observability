#!/usr/bin/env python3
"""
Create sample traces in Langfuse to demonstrate the integration.
"""

import os
import time
from datetime import datetime, timedelta
from app.services.langfuse_client import LangfuseClient

def create_sample_traces():
    """Create sample traces in Langfuse."""
    
    print("🚀 Creating Sample Traces in Langfuse")
    print("=" * 50)
    
    # Initialize Langfuse client
    langfuse_client = LangfuseClient()
    
    # Sample prompts for testing
    sample_prompts = [
        {
            "name": "Meeting Summary Generation",
            "prompt": "Generate a concise summary of the following meeting transcript: {transcript}",
            "completion": "The meeting focused on project planning and timeline discussions.",
            "model": "gpt-4"
        },
        {
            "name": "Action Item Extraction", 
            "prompt": "Extract action items from this meeting: {transcript}",
            "completion": "1. Schedule follow-up meeting\n2. Review budget proposal\n3. Update project timeline",
            "model": "gpt-4"
        },
        {
            "name": "Status Report Generation",
            "prompt": "Create a status report for the Vertigo project based on: {context}",
            "completion": "Project is on track with 75% completion. Key milestones achieved.",
            "model": "gpt-3.5-turbo"
        },
        {
            "name": "Email Response Generation",
            "prompt": "Generate a professional response to: {email_content}",
            "completion": "Thank you for your inquiry. I'll review and respond shortly.",
            "model": "gpt-4"
        },
        {
            "name": "Code Review Analysis",
            "prompt": "Analyze this code for potential issues: {code}",
            "completion": "Code looks good overall. Consider adding error handling.",
            "model": "gpt-4"
        }
    ]
    
    trace_count = 0
    
    # Create traces for the last 7 days
    for day in range(7):
        date = datetime.now() - timedelta(days=day)
        
        # Create 2-5 traces per day
        traces_per_day = 3 if day < 3 else 2
        
        for trace_num in range(traces_per_day):
            try:
                # Create trace
                trace_name = f"Sample Workflow - Day {day + 1} - Trace {trace_num + 1}"
                trace_id = langfuse_client.create_trace(
                    name=trace_name,
                    metadata={
                        "project": "vertigo",
                        "date": date.strftime("%Y-%m-%d"),
                        "workflow_type": "meeting_processing"
                    }
                )
                
                # Create spans for different steps
                extraction_span = langfuse_client.create_span(
                    trace_id=trace_id,
                    name="Email Processing",
                    metadata={"step": "email_extraction", "status": "success"}
                )
                
                # Simulate some processing time
                time.sleep(0.1)
                
                # Create generation span
                prompt_data = sample_prompts[trace_num % len(sample_prompts)]
                generation_id = langfuse_client.create_generation(
                    trace_id=trace_id,
                    model=prompt_data["model"],
                    prompt=prompt_data["prompt"].format(
                        transcript="Sample meeting transcript content...",
                        context="Project status and progress information...",
                        email_content="Sample email content...",
                        code="Sample code snippet..."
                    ),
                    completion=prompt_data["completion"],
                    metadata={
                        "prompt_name": prompt_data["name"],
                        "tokens_used": 150 + (trace_num * 10),
                        "cost": 0.002 + (trace_num * 0.001)
                    }
                )
                
                # Create final span
                final_span = langfuse_client.create_span(
                    trace_id=trace_id,
                    name="Response Generation",
                    metadata={"step": "response_creation", "status": "success"}
                )
                
                trace_count += 1
                print(f"✅ Created trace {trace_count}: {trace_name}")
                
            except Exception as e:
                print(f"❌ Error creating trace: {e}")
                continue
    
    print(f"\n🎉 Created {trace_count} sample traces in Langfuse!")
    print("🔗 Check your Langfuse dashboard to see the traces")
    print("📊 Run sync_langfuse_data.py to pull the data into the local dashboard")

if __name__ == "__main__":
    create_sample_traces() 