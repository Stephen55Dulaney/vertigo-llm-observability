from google.cloud import firestore

def save_meeting_data(meeting_id: str, data: dict):
    db = firestore.Client()
    db.collection("meetings").document(meeting_id).set(data) 