import functions_framework
from google.cloud import firestore
import logging
import re
from datetime import datetime, timedelta
import json
import os
from googleapiclient.discovery import build
from google.auth import default
import google.generativeai as genai
from langfuse_client import langfuse_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("status-generator")

def parse_natural_language_request(request_text: str):
    """
    Parse natural language requests for status updates.
    Examples:
    - "generate status" -> {days_back: 7, project: None}
    - "generate vertigo status since Monday" -> {start_date: "2025-07-14", end_date: "now", project: "vertigo"}
    - "generate memento status this week" -> {start_date: "2025-07-14", end_date: "2025-07-20", project: "memento"}
    """
    request_text = request_text.lower().strip()
    
    # Default values
    result = {
        "days_back": 7,
        "project": None,
        "start_date": None,
        "end_date": None
    }
    
    # Extract project name
    project_patterns = [
        r"generate\s+(\w+)\s+status",
        r"(\w+)\s+status",
        r"status\s+for\s+(\w+)"
    ]
    
    for pattern in project_patterns:
        match = re.search(pattern, request_text)
        if match:
            result["project"] = match.group(1)
            break
    
    # Parse date ranges
    now = datetime.now()
    
    if "this week" in request_text:
        # Monday to Sunday of current week
        monday = now - timedelta(days=now.weekday())
        sunday = monday + timedelta(days=6)
        result["start_date"] = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        result["end_date"] = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
        result["days_back"] = None
    
    elif "last week" in request_text:
        # Previous Monday to Sunday
        monday = now - timedelta(days=now.weekday() + 7)
        sunday = monday + timedelta(days=6)
        result["start_date"] = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        result["end_date"] = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
        result["days_back"] = None
    
    elif "since monday" in request_text:
        # Monday to now
        monday = now - timedelta(days=now.weekday())
        result["start_date"] = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        result["end_date"] = now
        result["days_back"] = None
    
    elif "since" in request_text:
        # Try to parse "since [day]"
        day_patterns = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        for day_name, day_num in day_patterns.items():
            if day_name in request_text:
                target_day = now - timedelta(days=now.weekday() - day_num)
                if target_day > now:  # If target day is in the future, go back a week
                    target_day -= timedelta(days=7)
                result["start_date"] = target_day.replace(hour=0, minute=0, second=0, microsecond=0)
                result["end_date"] = now
                result["days_back"] = None
                break
    
    # Parse specific day ranges
    elif "last" in request_text and "days" in request_text:
        match = re.search(r"last\s+(\d+)\s+days?", request_text)
        if match:
            days = int(match.group(1))
            result["days_back"] = days
    
    return result

@functions_framework.http
def email_processor(request):
    """
    Triggered by email with subject containing 'generate status' or 'status update'.
    Queries Firestore for recent meeting data and uses Gemini Pro to synthesize an executive summary.
    Creates a Gmail draft with the status update.
    """
    logger.info("=== STATUS GENERATOR FUNCTION STARTED ===")
    logger.info("Received status update generation request.")
    
    # Create Langfuse trace for the entire status generation operation
    trace_id = ""
    if langfuse_client.is_enabled():
        trace_id = langfuse_client.create_trace(
            name="status_generator_request",
            metadata={
                "function": "status-generator",
                "timestamp": datetime.now().isoformat(),
                "user_agent": request.headers.get("User-Agent", "unknown")
            }
        )
    
    # --- Simple Firestore Import Test ---
    try:
        logger.info("Testing Firestore import...")
        from google.cloud import firestore
        logger.info("Firestore import successful")
        
        logger.info("Testing Firestore client creation...")
        db = firestore.Client(project='vertigo-466116')
        logger.info(f"Firestore client created successfully for project: {db.project}")
        
        logger.info("Testing collection listing...")
        collections = list(db.collections())
        logger.info(f"Collections found: {[c.id for c in collections]}")
        
    except ImportError as e:
        logger.error(f"FIRESTORE IMPORT ERROR: {e}")
        return (f"Firestore import error: {e}", 500)
    except Exception as e:
        logger.error(f"FIRESTORE CLIENT ERROR: {e}")
        logger.exception("Full traceback:")
        return (f"Firestore client error: {e}", 500)
    # --- End Test ---
    
    try:
        # Parse request for parameters
        request_data = request.get_json(silent=True) or {}
        
        # Check if this is a natural language request
        if "request_text" in request_data:
            # Parse natural language request
            parsed_request = parse_natural_language_request(request_data["request_text"])
            days_back = parsed_request.get("days_back", 7)
            project = parsed_request.get("project")
            start_date = parsed_request.get("start_date")
            end_date = parsed_request.get("end_date")
            logger.info(f"Parsed request: project={project}, days_back={days_back}, start_date={start_date}, end_date={end_date}")
        else:
            # Legacy JSON parameters
            days_back = request_data.get("days_back", 7)
            project = request_data.get("project")
            start_date = request_data.get("start_date")
            end_date = request_data.get("end_date")
        
        recipient_email = request_data.get("recipient_email", "boss@company.com")
        
        # Query meetings from Firestore with project filtering
        recent_meetings = get_recent_meetings(days_back, project, start_date, end_date)
        
        if not recent_meetings:
            logger.warning("No recent meetings found for status update")
            return ({
                "status_update": "No recent meetings found to generate a status update from. Please ensure meeting transcripts have been processed and stored in the system.",
                "meetings_analyzed": 0,
                "gmail_draft_id": None,
                "recipient_email": recipient_email,
                "project": project,
                "date_range": {
                    "days_back": days_back,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "generated_at": datetime.now().isoformat()
            }, 200, {"Content-Type": "application/json"})
        
        # Generate status update using Gemini
        status_update = generate_executive_summary(recent_meetings, trace_id)
        
        # Create Gmail draft
        draft_id = create_gmail_draft(status_update["status_update"], recipient_email)
        
        logger.info(f"Generated status update based on {len(recent_meetings)} meetings and created Gmail draft: {draft_id}")
        
        # Update trace with final results
        if langfuse_client.is_enabled() and trace_id:
            langfuse_client.update_trace(
                trace_id=trace_id,
                output={
                    "meetings_analyzed": len(recent_meetings),
                    "gmail_draft_created": draft_id is not None,
                    "draft_id": draft_id,
                    "status_update_length": len(status_update["status_update"]) if status_update["status_update"] else 0
                },
                level="DEFAULT"
            )
            langfuse_client.flush()
        
        return ({
            "status_update": status_update["status_update"],
            "meetings_analyzed": len(recent_meetings),
            "gmail_draft_id": draft_id,
            "recipient_email": recipient_email,
            "project": project,
            "date_range": {
                "days_back": days_back,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "generated_at": datetime.now().isoformat()
        }, 200, {"Content-Type": "application/json"})
        
    except Exception as e:
        logger.exception("Error generating status update")
        return ("Internal Server Error", 500)

def get_recent_meetings(days_back: int | None = None, project: str | None = None, start_date: datetime | None = None, end_date: datetime | None = None):
    """Query Firestore for meetings with optional project filtering and date ranges."""
    try:
        logger.info(f"Starting get_recent_meetings with days_back={days_back}, project={project}")
        
        # Explicitly set the project
        db = firestore.Client(project='vertigo-466116')
        logger.info(f"Using Firestore project: {db.project}")
        
        # Build query
        meetings_ref = db.collection("meetings")
        logger.info("Got meetings collection reference")
        query = meetings_ref
        
        # Add project filter if specified
        if project:
            query = query.where("project", "==", project.lower())
            logger.info(f"Filtering for project: {project}")
        
        # Add date filtering
        if start_date and end_date:
            query = query.where("timestamp", ">=", start_date).where("timestamp", "<=", end_date)
            logger.info(f"Filtering by date range: {start_date} to {end_date}")
        elif days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            query = query.where("timestamp", ">=", cutoff_date)
            logger.info(f"Filtering by days back: {days_back} (since {cutoff_date})")
        
        # Execute query
        logger.info("Executing Firestore query...")
        docs = query.stream()
        
        meetings = []
        doc_count = 0
        for doc in docs:
            doc_count += 1
            meeting_data = doc.to_dict()
            logger.info(f"Processing document {doc_count}: {doc.id}")
            meetings.append({
                "id": doc.id,
                "transcript": meeting_data.get("transcript", ""),
                "semantic_tags": meeting_data.get("semantic_tags", {}),
                "gemini_result": meeting_data.get("gemini_result", ""),
                "metadata": meeting_data.get("metadata", {}),
                "project": meeting_data.get("project", "unknown"),
                "timestamp": meeting_data.get("timestamp")
            })
        
        logger.info(f"Found {len(meetings)} meetings matching criteria")
        return meetings
        
    except Exception as e:
        logger.error(f"Error in get_recent_meetings: {e}")
        logger.exception("Full traceback:")
        return []

def generate_executive_summary(meetings, trace_id=""):
    """Use Gemini to generate an executive summary from recent meetings."""
    api_key = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    # Prepare meeting data for Gemini
    meeting_summaries = []
    for meeting in meetings:
        summary = f"""
Meeting ID: {meeting['id']}
Transcript: {meeting['transcript'][:500]}...
Tags: {meeting['semantic_tags']}
Gemini Analysis: {meeting['gemini_result'][:300]}...
"""
        meeting_summaries.append(summary)
    
    all_meetings_text = "\n".join(meeting_summaries)
    
    prompt = f"""
Create an executive status update based on recent meeting data. Format as:

**Key Accomplishments:**
- [High-impact items completed]

**Critical Decisions:**
- [Decisions that affect timeline/scope/resources]

**Blockers & Risks:**
- [Items needing executive attention]
- [Proposed solutions or escalation needs]

**Next Week Focus:**
- [3-4 priority items]

**Metrics & Progress:**
- [Quantifiable progress indicators]

Tone: Professional but conversational. Highlight what the executive needs to know and where they can help remove blockers.

Recent Meeting Data:
{all_meetings_text}
"""
    
    # Create Langfuse generation trace for the Gemini LLM call
    generation_start_time = datetime.now()
    generation_id = ""
    if langfuse_client.is_enabled() and trace_id:
        generation_id = langfuse_client.create_generation(
            trace_id=trace_id,
            name="gemini_executive_summary",
            model="gemini-1.5-pro",
            input_data={
                "prompt": prompt,
                "meetings_count": len(meetings),
                "prompt_length": len(prompt)
            },
            output_data=None,  # Will be updated after response
            metadata={
                "function": "generate_executive_summary",
                "meetings_analyzed": len(meetings),
                "total_transcript_length": sum(len(m.get('transcript', '')) for m in meetings)
            }
        )
    
    # Make the Gemini API call
    response = model.generate_content(prompt)
    generation_end_time = datetime.now()
    
    # Update the generation with output data
    if langfuse_client.is_enabled() and generation_id:
        langfuse_client.update_trace(
            trace_id=generation_id,
            output={
                "status_update": response.text,
                "response_length": len(response.text) if response.text else 0,
                "generation_time_seconds": (generation_end_time - generation_start_time).total_seconds()
            }
        )
    
    return {
        "status_update": response.text,
        "meetings_analyzed": len(meetings),
        "generated_at": datetime.now().isoformat()
    }

def create_gmail_draft(status_update_text: str, recipient_email: str):
    """Create a Gmail draft with the status update."""
    try:
        # Get credentials for Gmail API
        credentials, project = default()
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Create email content
        subject = f"Status Update - {datetime.now().strftime('%B %d, %Y')}"
        
        email_content = f"""To: {recipient_email}
Subject: {subject}
Content-Type: text/plain; charset=utf-8

{status_update_text}

---
Generated by Vertigo AI
"""
        
        # Properly encode the email content for Gmail API
        import base64
        encoded_email = base64.urlsafe_b64encode(email_content.encode('utf-8')).decode('utf-8')
        
        # Create the draft
        draft = service.users().drafts().create(
            userId='me',
            body={
                'message': {
                    'raw': encoded_email
                }
            }
        ).execute()
        
        logger.info(f"Created Gmail draft with ID: {draft['id']}")
        return draft['id']
        
    except Exception as e:
        logger.error(f"Error creating Gmail draft: {e}")
        # Return None if Gmail draft creation fails, but don't fail the whole request
        return None 