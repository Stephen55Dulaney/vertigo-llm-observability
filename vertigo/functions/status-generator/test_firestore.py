import functions_framework
from google.cloud import firestore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-firestore")

@functions_framework.http
def test_firestore(request):
    """Test Firestore access in Cloud Function environment."""
    logger.info("Starting Firestore test...")
    
    try:
        # Try to create Firestore client
        logger.info("Creating Firestore client...")
        db = firestore.Client(project='vertigo-466116')
        logger.info(f"Firestore client created for project: {db.project}")
        
        # Try to list collections
        logger.info("Listing collections...")
        collections = list(db.collections())
        logger.info(f"Collections found: {[c.id for c in collections]}")
        
        # Try to query meetings collection
        if 'meetings' in [c.id for c in collections]:
            logger.info("Querying meetings collection...")
            meetings_ref = db.collection("meetings")
            docs = list(meetings_ref.limit(5).stream())
            logger.info(f"Found {len(docs)} meeting documents")
            
            for doc in docs:
                data = doc.to_dict()
                logger.info(f"Meeting: {data.get('meeting_title', 'No title')} - {data.get('timestamp', 'No timestamp')}")
        else:
            logger.warning("Meetings collection not found!")
        
        return {
            "status": "success",
            "collections": [c.id for c in collections],
            "meetings_count": len(docs) if 'docs' in locals() else 0
        }
        
    except Exception as e:
        logger.error(f"Firestore test failed: {e}")
        logger.exception("Full traceback:")
        return {
            "status": "error",
            "error": str(e)
        } 