import os
import json
from main import process_incoming_email

class DummyRequest:
    def __init__(self, data):
        self._data = data
    def get_json(self, silent=False):
        return self._data

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        exit(1)
    sample_email = {
        "transcript": "Yesterday we decided to move the launch to next week. John will handle the client update. Blocker: API integration is delayed. Participants: John, Sarah, Priya.",
        "metadata": {"message_id": "test123", "subject": "Meeting Notes"},
        "attachments": []
    }
    req = DummyRequest(sample_email)
    resp = process_incoming_email(req)
    print("Response:", resp) 