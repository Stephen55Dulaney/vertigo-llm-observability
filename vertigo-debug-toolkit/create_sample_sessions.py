#!/usr/bin/env python3
"""
Create sample session data for testing Session Analysis
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from app import create_app
from app.models import db, Trace
from datetime import datetime, timedelta
import random

def create_sample_sessions():
    """Create sample session data for testing."""
    app = create_app()
    
    with app.app_context():
        # Sample session data
        sessions = [
            # Session 1: Email Processing Session
            {
                'session_id': 'email_session_001',
                'traces': [
                    {'name': 'Email Classification', 'status': 'success', 'duration_ms': 1200},
                    {'name': 'Content Extraction', 'status': 'success', 'duration_ms': 800},
                    {'name': 'Response Generation', 'status': 'success', 'duration_ms': 2500}
                ]
            },
            # Session 2: Meeting Analysis Session
            {
                'session_id': 'meeting_session_002', 
                'traces': [
                    {'name': 'Transcript Processing', 'status': 'success', 'duration_ms': 5000},
                    {'name': 'Summary Generation', 'status': 'success', 'duration_ms': 3200},
                    {'name': 'Action Items Extraction', 'status': 'success', 'duration_ms': 1800}
                ]
            },
            # Session 3: Status Report Session
            {
                'session_id': 'status_session_003',
                'traces': [
                    {'name': 'Data Collection', 'status': 'success', 'duration_ms': 2100},
                    {'name': 'Report Generation', 'status': 'error', 'duration_ms': 1500},
                    {'name': 'Retry Report Generation', 'status': 'success', 'duration_ms': 2000}
                ]
            }
        ]
        
        print("Creating sample session data...")
        
        for session in sessions:
            session_id = session['session_id']
            base_time = datetime.utcnow() - timedelta(hours=random.randint(1, 24))
            
            for i, trace_data in enumerate(session['traces']):
                trace_time = base_time + timedelta(minutes=i * 2)
                
                trace = Trace(
                    trace_id=f"{session_id}_trace_{i+1}",
                    name=trace_data['name'],
                    status=trace_data['status'],
                    start_time=trace_time,
                    end_time=trace_time + timedelta(milliseconds=trace_data['duration_ms']),
                    duration_ms=trace_data['duration_ms'],
                    vertigo_operation='session_analysis',
                    project='vertigo-debug',
                    trace_metadata={
                        'session_id': session_id,
                        'session_type': session_id.split('_')[0],
                        'trace_sequence': i + 1
                    }
                )
                
                db.session.add(trace)
            
            print(f"✓ Created session: {session_id}")
        
        db.session.commit()
        print(f"\n🎉 Successfully created sample sessions!")
        print(f"📝 You can now use these Session IDs in the Session Analysis tool:")
        for session in sessions:
            print(f"   • {session['session_id']}")
        
        print(f"\n💡 Or leave the Session ID field empty to analyze all recent sessions")

if __name__ == '__main__':
    create_sample_sessions()