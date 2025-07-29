import functions_framework
from google.cloud import firestore
import logging
import google.generativeai as genai
import os
from datetime import datetime
import json
import re
from prompt_variants import get_prompt_variant
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meeting-processor")

@functions_framework.http
def process_meeting(request):
    """
    Process meeting transcripts from various sources and store in Firestore.
    Supports: dictation, Google Meet, Zoom, meeting notes, agent summaries
    """
    logger.info("Received meeting processing request.")
    
    try:
        # Parse request
        request_data = request.get_json(silent=True) or {}
        
        # Extract meeting data
        transcript = request_data.get("transcript", "")
        transcript_type = request_data.get("transcript_type", "dictation")
        project = request_data.get("project", "unknown")
        participants = request_data.get("participants", [])
        duration_minutes = request_data.get("duration_minutes")
        meeting_title = request_data.get("meeting_title", "")
        
        # Validate required fields
        if not transcript:
            return ("Transcript is required", 400)
        
        if not project:
            return ("Project is required", 400)
        
        # Process transcript based on type
        processed_data = process_transcript_by_type(transcript, transcript_type)
        
        # Generate meeting notes if it's a raw transcript or daily summary
        if transcript_type in ["dictation", "google_meet", "zoom", "daily_summary"]:
            # Get prompt variant from request or use default
            prompt_variant = request_data.get("prompt_variant", "detailed_extraction")
            meeting_notes_result = generate_meeting_notes(transcript, project, prompt_variant)
            processed_data["processed_notes"] = meeting_notes_result["narrative_summary"]
            processed_data["structured_data"] = meeting_notes_result["structured_data"]
            processed_data["gemini_result"] = meeting_notes_result["full_response"]
        
        # Store in Firestore
        meeting_id = store_meeting_in_firestore(
            transcript=transcript,
            processed_data=processed_data,
            project=project,
            participants=participants,
            duration_minutes=duration_minutes,
            meeting_title=meeting_title,
            transcript_type=transcript_type
        )
        
        logger.info(f"Successfully processed meeting {meeting_id}")
        
        return ({
            "meeting_id": meeting_id,
            "transcript_type": transcript_type,
            "project": project,
            "processed_notes": processed_data.get("processed_notes", ""),
            "structured_data": processed_data.get("structured_data", {}),
            "prompt_variant": prompt_variant if transcript_type in ["dictation", "google_meet", "zoom"] else None,
            "stored_at": datetime.now().isoformat()
        }, 200, {"Content-Type": "application/json"})
        
    except Exception as e:
        logger.exception("Error processing meeting")
        return ("Internal Server Error", 500)

def process_transcript_by_type(transcript: str, transcript_type: str):
    """Process transcript based on its type and extract metadata."""
    processed_data = {
        "transcript": transcript,
        "metadata": {
            "transcript_type": transcript_type,
            "quality": "low",
            "speakers": [],
            "timestamps": False
        }
    }
    
    if transcript_type == "dictation":
        # Simple dictation - no speakers, no timestamps
        processed_data["metadata"]["quality"] = "low"
        processed_data["metadata"]["speakers"] = []
        processed_data["metadata"]["timestamps"] = False
        
    elif transcript_type == "google_meet":
        # Google Meet format: "Speaker Name: text"
        speakers = extract_speakers_from_google_meet(transcript)
        processed_data["metadata"]["speakers"] = speakers
        processed_data["metadata"]["quality"] = "high"
        processed_data["metadata"]["timestamps"] = True
        
    elif transcript_type == "zoom":
        # Zoom format: "[timestamp] Speaker Name: text"
        speakers = extract_speakers_from_zoom(transcript)
        processed_data["metadata"]["speakers"] = speakers
        processed_data["metadata"]["quality"] = "high"
        processed_data["metadata"]["timestamps"] = True
        
    elif transcript_type == "meeting_notes":
        # Already processed meeting notes
        processed_data["metadata"]["quality"] = "high"
        processed_data["metadata"]["speakers"] = []
        processed_data["metadata"]["timestamps"] = False
        
    elif transcript_type == "agent_summary":
        # Agent-generated summary
        processed_data["metadata"]["quality"] = "high"
        processed_data["metadata"]["speakers"] = []
        processed_data["metadata"]["timestamps"] = False
        
    elif transcript_type == "daily_summary":
        # Daily summary content (3:00 PM updates)
        processed_data["metadata"]["quality"] = "high"
        processed_data["metadata"]["speakers"] = []
        processed_data["metadata"]["timestamps"] = False
        processed_data["metadata"]["summary_type"] = "daily_boss_update"
    
    return processed_data

def extract_speakers_from_google_meet(transcript: str):
    """Extract speaker names from Google Meet transcript format."""
    # Pattern: "Speaker Name: text"
    speaker_pattern = r'^([^:]+):\s*(.+)$'
    speakers = set()
    
    for line in transcript.split('\n'):
        match = re.match(speaker_pattern, line.strip())
        if match:
            speaker_name = match.group(1).strip()
            speakers.add(speaker_name)
    
    return list(speakers)

def extract_speakers_from_zoom(transcript: str):
    """Extract speaker names from Zoom transcript format."""
    # Pattern: "[timestamp] Speaker Name: text"
    speaker_pattern = r'\[\d{2}:\d{2}:\d{2}\]\s*([^:]+):\s*(.+)$'
    speakers = set()
    
    for line in transcript.split('\n'):
        match = re.match(speaker_pattern, line.strip())
        if match:
            speaker_name = match.group(1).strip()
            speakers.add(speaker_name)
    
    return list(speakers)

def generate_meeting_notes(transcript: str, project: str, prompt_variant: str = "detailed_extraction"):
    """Use Gemini to generate structured meeting notes from transcript."""
    try:
        api_key = os.environ["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        
                # Get the appropriate prompt variant
        prompt = get_prompt_variant(prompt_variant, transcript, project)
        
        response = model.generate_content(prompt)
        
        # Try to parse the response as JSON
        try:
            # Clean up the response - remove markdown code blocks if present
            cleaned_response = response.text.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]  # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            
            # Remove JSON comments and other invalid elements
            cleaned_response = re.sub(r'//.*$', '', cleaned_response, flags=re.MULTILINE)  # Remove single-line comments
            cleaned_response = re.sub(r'/\*.*?\*/', '', cleaned_response, flags=re.DOTALL)  # Remove multi-line comments
            cleaned_response = re.sub(r',\s*}', '}', cleaned_response)  # Remove trailing commas
            cleaned_response = re.sub(r',\s*]', ']', cleaned_response)  # Remove trailing commas in arrays
            
            structured_data = json.loads(cleaned_response.strip())
            
            # Create a narrative summary from the structured data
            narrative_summary = create_narrative_summary(structured_data, project)
            
            # Store both structured and narrative data
            return {
                "structured_data": structured_data,
                "narrative_summary": narrative_summary,
                "full_response": response.text
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response text: {response.text}")
            # Fallback to the original text if JSON parsing fails
            return {
                "structured_data": {},
                "narrative_summary": response.text,
                "full_response": response.text
            }
        
    except Exception as e:
        logger.error(f"Error generating meeting notes: {e}")
        return {
            "structured_data": {},
            "narrative_summary": "Error generating meeting notes",
            "full_response": f"Error: {str(e)}"
        }

def create_narrative_summary(structured_data: dict, project: str) -> str:
    """Create a narrative summary from structured data."""
    try:
        # Check if this is a daily summary format
        if "my_ambition" in structured_data:
            # Format as daily summary
            summary = f"**My Ambition:**\n{structured_data.get('my_ambition', 'Drive clarity and momentum on key projects.')}\n\n"
            
            # What We Did Today
            what_we_did = structured_data.get('what_we_did_today', [])
            if what_we_did:
                summary += "**What We Did Today:**\n"
                for item in what_we_did:
                    summary += f"• {item}\n"
                summary += "\n"
            
            # What We'll Do Next
            what_well_do = structured_data.get('what_well_do_next', [])
            if what_well_do:
                summary += "**What We'll Do Next:**\n"
                for item in what_well_do:
                    summary += f"• {item}\n"
                summary += "\n"
            
            # Add any blockers if present
            blockers = structured_data.get('blockers_risks', [])
            if blockers:
                summary += "**Blockers & Risks:**\n"
                for blocker in blockers:
                    if isinstance(blocker, dict):
                        issue = blocker.get('issue', '')
                        impact = blocker.get('impact', '')
                        action = blocker.get('action_needed', '')
                        summary += f"• {issue} (Impact: {impact})"
                        if action:
                            summary += f" - {action}"
                        summary += "\n"
                    else:
                        summary += f"• {blocker}\n"
                summary += "\n"
            
            # Add team coordination if present
            team_coord = structured_data.get('team_coordination', [])
            if team_coord:
                summary += "**Team Coordination:**\n"
                for item in team_coord:
                    summary += f"• {item}\n"
                summary += "\n"
            
            return summary.strip()
        
        else:
            # Original meeting summary format
            summary = f"**Meeting Summary:**\n{structured_data.get('meeting_summary', 'Meeting discussion and outcomes.')}\n\n"
            
            # Key Points
            key_points = structured_data.get('key_points', [])
            if key_points:
                summary += "**Key Points:**\n"
                for point in key_points:
                    summary += f"• {point}\n"
                summary += "\n"
            
            # Action Items
            action_items = structured_data.get('action_items', [])
            if action_items:
                summary += "**Action Items:**\n"
                for item in action_items:
                    if isinstance(item, dict):
                        desc = item.get('description', '')
                        owner = item.get('owner', '')
                        due_date = item.get('due_date', '')
                        summary += f"• {desc}"
                        if owner:
                            summary += f" - {owner}"
                        if due_date:
                            summary += f" (Due: {due_date})"
                        summary += "\n"
                    else:
                        summary += f"• {item}\n"
                summary += "\n"
            
            # Next Steps
            next_steps = structured_data.get('next_steps', [])
            if next_steps:
                summary += "**Next Steps:**\n"
                for step in next_steps:
                    summary += f"• {step}\n"
                summary += "\n"
            
            # Participants
            participants = structured_data.get('participants', [])
            if participants:
                summary += "**Participants:**\n"
                for participant in participants:
                    summary += f"• {participant}\n"
                summary += "\n"
            
            # Project Context
            summary += f"**Project Context:**\nThis meeting relates to the {project} project goals and objectives."
            
            return summary.strip()
            
    except Exception as e:
        logger.error(f"Error creating narrative summary: {e}")
        return f"Error generating summary for {project} project."

def store_meeting_in_firestore(transcript: str, processed_data: dict, project: str, 
                              participants: list, duration_minutes: int, 
                              meeting_title: str, transcript_type: str):
    """Store meeting data in Firestore."""
    db = firestore.Client()
    
    meeting_data = {
        "transcript": transcript,
        "processed_notes": processed_data.get("processed_notes", ""),
        "structured_data": processed_data.get("structured_data", {}),
        "gemini_result": processed_data.get("gemini_result", ""),
        "transcript_type": transcript_type,
        "project": project.lower(),
        "timestamp": datetime.now(),
        "participants": participants,
        "duration_minutes": duration_minutes or 0,
        "meeting_title": meeting_title,
        "metadata": processed_data.get("metadata", {}),
        "created_at": datetime.now()
    }
    
    # Add to meetings collection
    doc_ref = db.collection("meetings").add(meeting_data)
    meeting_id = doc_ref[1].id
    
    logger.info(f"Stored meeting {meeting_id} in Firestore")
    return meeting_id 

def extract_gdoc_link(email_body):
    match = re.search(r'https://docs\.google\.com/document/d/[\w-]+', email_body)
    return match.group(0) if match else None

def fetch_gdoc_content(doc_url, credentials):
    doc_id = doc_url.split('/d/')[1].split('/')[0]
    service = build('docs', 'v1', credentials=credentials)
    doc = service.documents().get(documentId=doc_id).execute()
    text = ''
    for element in doc.get('body', {}).get('content', []):
        if 'paragraph' in element:
            for run in element['paragraph'].get('elements', []):
                text += run.get('textRun', {}).get('content', '')
    return text 