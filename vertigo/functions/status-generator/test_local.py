import json
from main import generate_status_update

class DummyRequest:
    def __init__(self, data):
        self._data = data
    def get_json(self, silent=False):
        return self._data

if __name__ == "__main__":
    # Test with natural language request
    test_request = {
        "request_text": "generate vertigo status since Monday",
        "recipient_email": "executive@company.com"
    }
    req = DummyRequest(test_request)
    
    print("Testing status generator with Gmail integration...")
    print("=" * 60)
    
    resp = generate_status_update(req)
    print(f"Response: {resp}")
    
    if len(resp) >= 2 and resp[1] == 200:
        print("\n" + "=" * 60)
        print("STATUS UPDATE GENERATED:")
        print("=" * 60)
        print(resp[0]["status_update"])
        print("\n" + "=" * 60)
        print("GMAIL DRAFT INFO:")
        print("=" * 60)
        print(f"Draft ID: {resp[0].get('gmail_draft_id', 'Not created')}")
        print(f"Recipient: {resp[0].get('recipient_email', 'Not specified')}")
        print(f"Meetings Analyzed: {resp[0].get('meetings_analyzed', 0)}")
    else:
        print(f"Error: {resp}") 