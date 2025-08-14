import json
from main import process_meeting

class DummyRequest:
    def __init__(self, data):
        self._data = data
    def get_json(self, silent=False):
        return self._data

if __name__ == "__main__":
    # Test with a simple dictation transcript
    test_transcript = """
    We discussed the API integration for the Vertigo project. John mentioned that the Gmail API integration is working well but we need to fix the authentication issues. Sarah suggested we look at the OAuth flow more carefully. We decided to prioritize the status generator feature and push the Gmail draft creation to next week. The team agreed that we should focus on getting the core functionality working first.
    """
    
    test_request = {
        "transcript": test_transcript,
        "transcript_type": "dictation",
        "project": "vertigo",
        "participants": ["John", "Sarah", "Steve"],
        "duration_minutes": 45,
        "meeting_title": "Vertigo API Integration Review"
    }
    
    req = DummyRequest(test_request)
    
    print("Testing meeting processor...")
    print("=" * 60)
    
    resp = process_meeting(req)
    print(f"Response: {resp}")
    
    if len(resp) >= 2 and resp[1] == 200:
        print("\n" + "=" * 60)
        print("MEETING PROCESSED SUCCESSFULLY:")
        print("=" * 60)
        print(f"Meeting ID: {resp[0]['meeting_id']}")
        print(f"Project: {resp[0]['project']}")
        print(f"Transcript Type: {resp[0]['transcript_type']}")
        print(f"Stored At: {resp[0]['stored_at']}")
        print("\n" + "=" * 60)
        print("GENERATED MEETING NOTES:")
        print("=" * 60)
        print(resp[0]['processed_notes'])
    else:
        print(f"Error: {resp}") 