from google.cloud import firestore

db = firestore.Client(project='vertigo-466116')
meetings = list(db.collection('meetings').stream())

print(f"Found {len(meetings)} meetings in Firestore")

for i, meeting in enumerate(meetings[-5:], 1):  # Show last 5 meetings
    data = meeting.to_dict()
    print(f"\n{i}. Meeting ID: {meeting.id}")
    print(f"   Timestamp: {data.get('timestamp')}")
    print(f"   Subject: {data.get('subject', 'No subject')}")
    print(f"   Project: {data.get('project', 'No project')}")
    print(f"   Participants: {len(data.get('participants', []))}")
    print(f"   Key decisions: {len(data.get('key_decisions', []))}")
    print(f"   Action items: {len(data.get('action_items', []))}")
    print(f"   Blockers: {len(data.get('blockers', []))}")

# Check for meetings with extracted data
print(f"\n{'='*50}")
print("Meetings with extracted data:")
for meeting in meetings:
    data = meeting.to_dict()
    if data.get('key_decisions') or data.get('action_items') or data.get('blockers'):
        print(f"Meeting {meeting.id}: {len(data.get('key_decisions', []))} decisions, {len(data.get('action_items', []))} actions, {len(data.get('blockers', []))} blockers") 