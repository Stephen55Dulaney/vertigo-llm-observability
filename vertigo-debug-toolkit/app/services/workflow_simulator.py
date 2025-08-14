"""
Workflow simulator for testing Vertigo email processing workflows.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
# from langfuse.decorators import observe
import google.generativeai as genai
from app import db
from app.models import Trace, Cost, SampleData
from app.services.langwatch_client import LangWatchClient

logger = logging.getLogger(__name__)

class WorkflowSimulator:
    """Simulates Vertigo email processing workflows for testing."""
    
    def __init__(self):
        """Initialize the workflow simulator."""
        self.langwatch_client = LangWatchClient()
        
        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-pro")
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY not set, LLM calls will be simulated")
    
    # @observe()
    def run_sample_workflow(self) -> Dict[str, Any]:
        """Run a complete sample workflow simulation."""
        
        # Create trace (LangWatch integration can be added here)
        trace_id = "sample-workflow-trace"
        
        try:
            # Step 1: Process incoming email
            email_result = self._simulate_email_processing(trace_id)
            
            # Step 2: Extract meeting transcript
            transcript_result = self._simulate_transcript_extraction(trace_id, email_result)
            
            # Step 3: Generate meeting summary
            summary_result = self._simulate_summary_generation(trace_id, transcript_result)
            
            # Step 4: Store in database
            storage_result = self._simulate_database_storage(trace_id, summary_result)
            
            # Step 5: Generate status report
            status_result = self._simulate_status_generation(trace_id)
            
            return {
                "status": "success",
                "trace_id": trace_id,
                "steps": {
                    "email_processing": email_result,
                    "transcript_extraction": transcript_result,
                    "summary_generation": summary_result,
                    "database_storage": storage_result,
                    "status_generation": status_result
                },
                "total_duration_ms": sum([
                    email_result.get("duration_ms", 0),
                    transcript_result.get("duration_ms", 0),
                    summary_result.get("duration_ms", 0),
                    storage_result.get("duration_ms", 0),
                    status_result.get("duration_ms", 0)
                ])
            }
            
        except Exception as e:
            logger.error(f"Workflow simulation failed: {e}")
            return {
                "status": "error",
                "trace_id": trace_id,
                "error": str(e)
            }
    
    def _simulate_email_processing(self, trace_id: str) -> Dict[str, Any]:
        """Simulate email processing step."""
        start_time = datetime.utcnow()
        
        # Simulate email content
        email_content = {
            "from": "user@company.com",
            "subject": "Meeting Transcript - Q4 Planning",
            "body": "Please process the attached meeting transcript for our Q4 planning session.",
            "attachments": ["meeting_transcript_2024_q4.pdf"]
        }
        
        # Simulate processing time
        import time
        time.sleep(0.5)
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return {
            "status": "success",
            "email_content": email_content,
            "duration_ms": duration_ms
        }
    
    def _simulate_transcript_extraction(self, trace_id: str, email_result: Dict) -> Dict[str, Any]:
        """Simulate transcript extraction step."""
        start_time = datetime.utcnow()
        
        # Sample meeting transcript
        transcript = """
        Q4 Planning Meeting - October 15, 2024
        
        Participants: John Smith (CEO), Sarah Johnson (CTO), Mike Davis (CFO)
        
        John: Welcome everyone to our Q4 planning session. Let's start with a review of our Q3 performance.
        
        Sarah: Q3 was strong for our engineering team. We shipped 15 new features and improved our system reliability by 25%. However, we're behind on the mobile app redesign.
        
        Mike: Financially, we're 5% ahead of projections. Revenue grew 12% quarter-over-quarter, but our customer acquisition costs increased by 8%.
        
        John: What are our key priorities for Q4?
        
        Sarah: We need to complete the mobile app redesign by December 1st. Also, we should prioritize the AI integration features that customers have been requesting.
        
        Mike: From a financial perspective, we should focus on reducing customer churn and improving our enterprise sales pipeline.
        
        John: Agreed. Let's set these as our top three Q4 priorities:
        1. Complete mobile app redesign
        2. Launch AI integration features
        3. Reduce customer churn by 15%
        
        Next meeting: November 1st for progress review.
        """
        
        # Simulate processing time
        import time
        time.sleep(1.0)
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return {
            "status": "success",
            "transcript": transcript,
            "duration_ms": duration_ms
        }
    
    def _simulate_summary_generation(self, trace_id: str, transcript_result: Dict) -> Dict[str, Any]:
        """Simulate meeting summary generation using LLM."""
        start_time = datetime.utcnow()
        
        transcript = transcript_result["transcript"]
        
        if self.model:
            # Use real LLM
            prompt = f"""
            Analyze this meeting transcript and create a structured summary with the following format:
            
            **Key Decisions:**
            - [List key decisions made]
            
            **Action Items:**
            - [List action items with owners and deadlines]
            
            **Key Metrics:**
            - [List important metrics mentioned]
            
            **Next Steps:**
            - [List next steps and follow-ups]
            
            Transcript:
            {transcript}
            """
            
            try:
                response = self.model.generate_content(prompt)
                summary = response.text
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                summary = self._generate_fallback_summary(transcript)
        else:
            # Generate fallback summary
            summary = self._generate_fallback_summary(transcript)
        
        # Simulate processing time
        import time
        time.sleep(2.0)
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Calculate estimated cost
        estimated_cost = self._calculate_estimated_cost(duration_ms, len(transcript), len(summary))
        
        return {
            "status": "success",
            "summary": summary,
            "duration_ms": duration_ms,
            "estimated_cost_usd": estimated_cost
        }
    
    def _generate_fallback_summary(self, transcript: str) -> str:
        """Generate a fallback summary when LLM is not available."""
        return """
        **Key Decisions:**
        - Set Q4 priorities: mobile app redesign, AI integration features, and customer churn reduction
        - Mobile app redesign deadline: December 1st
        - Target customer churn reduction: 15%
        
        **Action Items:**
        - Engineering team to complete mobile app redesign by December 1st
        - Launch AI integration features in Q4
        - Sales team to focus on enterprise pipeline and churn reduction
        
        **Key Metrics:**
        - Q3 revenue growth: 12% quarter-over-quarter
        - Q3 feature delivery: 15 new features
        - System reliability improvement: 25%
        - Customer acquisition cost increase: 8%
        
        **Next Steps:**
        - Progress review meeting scheduled for November 1st
        - Engineering to provide detailed timeline for mobile app redesign
        - Sales to develop churn reduction strategy
        """
    
    def _simulate_database_storage(self, trace_id: str, summary_result: Dict) -> Dict[str, Any]:
        """Simulate database storage step."""
        start_time = datetime.utcnow()
        
        # Store sample data
        sample_data = SampleData(
            name="Q4 Planning Meeting Summary",
            data_type="meeting_summary",
            content=summary_result["summary"],
            metadata={
                "project": "sample-project",
                "meeting_date": "2024-10-15",
                "participants": ["John Smith", "Sarah Johnson", "Mike Davis"],
                "duration_minutes": 60
            }
        )
        
        db.session.add(sample_data)
        db.session.commit()
        
        # Simulate processing time
        import time
        time.sleep(0.3)
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return {
            "status": "success",
            "stored_id": sample_data.id,
            "duration_ms": duration_ms
        }
    
    def _simulate_status_generation(self, trace_id: str) -> Dict[str, Any]:
        """Simulate status report generation."""
        start_time = datetime.utcnow()
        
        if self.model:
            # Use real LLM
            prompt = """
            Create an executive status update based on the following meeting summary:
            
            **Key Decisions:**
            - Set Q4 priorities: mobile app redesign, AI integration features, and customer churn reduction
            - Mobile app redesign deadline: December 1st
            - Target customer churn reduction: 15%
            
            **Action Items:**
            - Engineering team to complete mobile app redesign by December 1st
            - Launch AI integration features in Q4
            - Sales team to focus on enterprise pipeline and churn reduction
            
            **Key Metrics:**
            - Q3 revenue growth: 12% quarter-over-quarter
            - Q3 feature delivery: 15 new features
            - System reliability improvement: 25%
            - Customer acquisition cost increase: 8%
            
            Format as an executive summary with:
            - Key accomplishments
            - Critical decisions
            - Blockers & risks
            - Next week focus
            """
            
            try:
                response = self.model.generate_content(prompt)
                status_report = response.text
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                status_report = self._generate_fallback_status()
        else:
            # Generate fallback status
            status_report = self._generate_fallback_status()
        
        # Simulate processing time
        import time
        time.sleep(1.5)
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return {
            "status": "success",
            "status_report": status_report,
            "duration_ms": duration_ms
        }
    
    def _generate_fallback_status(self) -> str:
        """Generate a fallback status report when LLM is not available."""
        return """
        **Executive Status Update - Q4 Planning**
        
        **Key Accomplishments:**
        - Successfully completed Q3 with 12% revenue growth
        - Delivered 15 new features and improved system reliability by 25%
        - Established clear Q4 priorities and timelines
        
        **Critical Decisions:**
        - Prioritized mobile app redesign with December 1st deadline
        - Committed to AI integration features launch in Q4
        - Set aggressive 15% customer churn reduction target
        
        **Blockers & Risks:**
        - Mobile app redesign timeline is tight and may require additional resources
        - Customer acquisition costs increased 8% in Q3, need to address
        - AI integration features require significant engineering effort
        
        **Next Week Focus:**
        - Engineering team to provide detailed mobile app redesign timeline
        - Sales team to develop customer churn reduction strategy
        - Schedule follow-up meetings for progress tracking
        """
    
    def _calculate_estimated_cost(self, duration_ms: int, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost for LLM usage."""
        # Rough estimation based on Gemini pricing
        input_cost_per_1k = 0.0035
        output_cost_per_1k = 0.0105
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return round(input_cost + output_cost, 6)
    
    def load_sample_data(self) -> Dict[str, Any]:
        """Load sample data for testing."""
        sample_transcripts = [
            {
                "name": "Q4 Planning Meeting",
                "data_type": "meeting_transcript",
                "content": "Q4 Planning Meeting - October 15, 2024...",
                "metadata": {"project": "planning", "date": "2024-10-15"}
            },
            {
                "name": "Product Review Session",
                "data_type": "meeting_transcript", 
                "content": "Product Review Session - October 20, 2024...",
                "metadata": {"project": "product", "date": "2024-10-20"}
            }
        ]
        
        loaded_count = 0
        for sample in sample_transcripts:
            existing = SampleData.query.filter_by(name=sample["name"]).first()
            if not existing:
                data = SampleData(**sample)
                db.session.add(data)
                loaded_count += 1
        
        db.session.commit()
        
        return {
            "status": "success",
            "loaded_count": loaded_count,
            "total_samples": len(sample_transcripts)
        } 