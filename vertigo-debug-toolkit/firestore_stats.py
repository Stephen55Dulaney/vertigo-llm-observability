#!/usr/bin/env python3
"""
Firestore Statistics Script for Vertigo
Query transcript data and generate statistics.
"""

import os
import sys
from datetime import datetime, timedelta
from google.cloud import firestore
from google.cloud.firestore import FieldFilter

def get_firestore_client():
    """Initialize Firestore client."""
    try:
        # Set the project ID
        os.environ['GOOGLE_CLOUD_PROJECT'] = 'vertigo-466116'
        db = firestore.Client()
        return db
    except Exception as e:
        print(f"Error initializing Firestore client: {e}")
        return None

def get_transcript_stats(db, days=None):
    """Get transcript statistics from Firestore."""
    try:
        transcripts_ref = db.collection('transcripts')
        
        # If days specified, filter by date
        if days:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = transcripts_ref.where(filter=FieldFilter("created_at", ">=", start_date))
        else:
            query = transcripts_ref
        
        # Get all documents
        docs = query.stream()
        
        # Process results
        total_transcripts = 0
        projects = set()
        transcript_types = {}
        status_counts = {}
        
        for doc in docs:
            data = doc.to_dict()
            total_transcripts += 1
            
            # Track unique projects
            project_id = data.get('project_id') or data.get('project')
            if project_id:
                projects.add(project_id)
            
            # Track transcript types
            transcript_type = data.get('type') or data.get('transcript_type', 'unknown')
            transcript_types[transcript_type] = transcript_types.get(transcript_type, 0) + 1
            
            # Track status
            status = data.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_transcripts': total_transcripts,
            'unique_projects': len(projects),
            'projects': list(projects),
            'transcript_types': transcript_types,
            'status_counts': status_counts
        }
        
    except Exception as e:
        print(f"Error querying Firestore: {e}")
        return None

def get_meeting_stats(db, days=None):
    """Get meeting statistics from Firestore."""
    try:
        meetings_ref = db.collection('meetings')
        
        # If days specified, filter by date
        if days:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = meetings_ref.where(filter=FieldFilter("created_at", ">=", start_date))
        else:
            query = meetings_ref
        
        # Get all documents
        docs = query.stream()
        
        # Process results
        total_meetings = 0
        meeting_status = {}
        
        for doc in docs:
            data = doc.to_dict()
            total_meetings += 1
            
            # Track meeting status
            status = data.get('status', 'unknown')
            meeting_status[status] = meeting_status.get(status, 0) + 1
        
        return {
            'total_meetings': total_meetings,
            'meeting_status': meeting_status
        }
        
    except Exception as e:
        print(f"Error querying meetings: {e}")
        return None

def print_stats(stats, title):
    """Print statistics in a formatted way."""
    print(f"\n📊 {title}")
    print("=" * 50)
    
    if not stats:
        print("❌ No data available")
        return
    
    print(f"Total Items: {stats.get('total_transcripts', stats.get('total_meetings', 0))}")
    
    if 'unique_projects' in stats:
        print(f"Unique Projects: {stats['unique_projects']}")
        if stats['projects']:
            print("Projects:", ", ".join(stats['projects'][:5]))  # Show first 5
            if len(stats['projects']) > 5:
                print(f"... and {len(stats['projects']) - 5} more")
    
    if 'transcript_types' in stats:
        print("\nTranscript Types:")
        for t_type, count in stats['transcript_types'].items():
            print(f"  {t_type}: {count}")
    
    if 'status_counts' in stats:
        print("\nStatus Breakdown:")
        for status, count in stats['status_counts'].items():
            print(f"  {status}: {count}")
    
    if 'meeting_status' in stats:
        print("\nMeeting Status:")
        for status, count in stats['meeting_status'].items():
            print(f"  {status}: {count}")

def main():
    """Main function to run statistics queries."""
    print("🔍 Vertigo Firestore Statistics")
    print("=" * 50)
    
    # Initialize Firestore client
    db = get_firestore_client()
    if not db:
        print("❌ Failed to initialize Firestore client")
        return
    
    # Get all-time stats
    print("\n📈 ALL-TIME STATISTICS")
    print("=" * 50)
    
    transcript_stats = get_transcript_stats(db)
    meeting_stats = get_meeting_stats(db)
    
    print_stats(transcript_stats, "Transcript Statistics")
    print_stats(meeting_stats, "Meeting Statistics")
    
    # Get this week's stats
    print("\n📅 THIS WEEK'S STATISTICS")
    print("=" * 50)
    
    week_transcript_stats = get_transcript_stats(db, days=7)
    week_meeting_stats = get_meeting_stats(db, days=7)
    
    print_stats(week_transcript_stats, "This Week's Transcripts")
    print_stats(week_meeting_stats, "This Week's Meetings")
    
    # Summary
    print("\n📋 SUMMARY")
    print("=" * 50)
    
    if transcript_stats:
        print(f"• Total transcripts processed: {transcript_stats['total_transcripts']}")
        print(f"• Unique projects: {transcript_stats['unique_projects']}")
    
    if week_transcript_stats:
        print(f"• Transcripts this week: {week_transcript_stats['total_transcripts']}")
    
    if meeting_stats:
        print(f"• Total meetings: {meeting_stats['total_meetings']}")
    
    if week_meeting_stats:
        print(f"• Meetings this week: {week_meeting_stats['total_meetings']}")
    
    print(f"\n📅 Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 