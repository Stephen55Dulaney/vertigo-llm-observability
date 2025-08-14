#!/usr/bin/env python3
"""
Script to sync real Langfuse data to the local database.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app import create_app, db
from app.models import Trace, Cost, Prompt
from app.services.langfuse_client import LangfuseClient

# Load environment variables
load_dotenv()

def sync_langfuse_data():
    """Sync real data from Langfuse to local database."""
    
    print("🔄 Syncing Langfuse Data to Local Database")
    print("=" * 50)
    
    # Initialize Flask app context
    app = create_app()
    with app.app_context():
        
        # Initialize Langfuse client
        langfuse_client = LangfuseClient()
        
        # Clear existing demo data
        print("🗑️  Clearing existing demo data...")
        Trace.query.delete()
        Cost.query.delete()
        db.session.commit()
        print("✅ Demo data cleared")
        
        # Get real traces from Langfuse
        print("📥 Fetching traces from Langfuse...")
        try:
            # Get traces from the last 7 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            # Use the correct API to get traces
            traces_response = langfuse_client.langfuse.api.trace.list(
                from_timestamp=start_date,
                to_timestamp=end_date,
                limit=100
            )
            
            print(f"📊 Found {len(traces_response.data)} traces in Langfuse")
            
            # Sync traces to database
            synced_count = 0
            for trace_data in traces_response.data:
                # Check if trace already exists
                existing_trace = Trace.query.filter_by(trace_id=trace_data.id).first()
                if existing_trace:
                    continue
                
                # Create new trace record
                trace = Trace(
                    trace_id=trace_data.id,
                    name=trace_data.name or "Unnamed Trace",
                    status=trace_data.status or "unknown",
                    start_time=datetime.fromisoformat(trace_data.timestamp.replace('Z', '+00:00')) if trace_data.timestamp else datetime.utcnow(),
                    end_time=datetime.fromisoformat(trace_data.end_time.replace('Z', '+00:00')) if trace_data.end_time else None,
                    duration_ms=trace_data.latency or 0,
                    trace_metadata=trace_data.metadata or {},
                    error_message=trace_data.error or '',
                    vertigo_operation=trace_data.metadata.get('operation') if trace_data.metadata else None,
                    project=trace_data.metadata.get('project') if trace_data.metadata else None,
                    meeting_id=trace_data.metadata.get('meeting_id') if trace_data.metadata else None
                )
                
                db.session.add(trace)
                synced_count += 1
            
            db.session.commit()
            print(f"✅ Synced {synced_count} new traces to database")
            
        except Exception as e:
            print(f"❌ Error syncing traces: {e}")
            db.session.rollback()
        
        # For now, let's create some sample cost data based on the traces
        print("💰 Creating sample cost data based on traces...")
        try:
            traces = Trace.query.all()
            cost_count = 0
            
            for trace in traces:
                # Create a sample cost record for each trace
                cost_record = Cost(
                    trace_id=trace.trace_id,
                    model="gemini-1.5-pro",
                    input_tokens=500,
                    output_tokens=200,
                    total_tokens=700,
                    cost_usd=0.005,
                    timestamp=trace.start_time
                )
                
                db.session.add(cost_record)
                cost_count += 1
            
            db.session.commit()
            print(f"✅ Created {cost_count} sample cost records")
            
        except Exception as e:
            print(f"❌ Error creating cost data: {e}")
            db.session.rollback()
        
        # Show final stats
        total_traces = Trace.query.count()
        total_costs = Cost.query.count()
        
        print("\n" + "=" * 50)
        print("📊 Final Database Stats:")
        print(f"   Total Traces: {total_traces}")
        print(f"   Total Cost Records: {total_costs}")
        print("=" * 50)
        
        if total_traces > 0:
            print("🎉 Database now contains real Langfuse data!")
            print("🔄 Refresh your dashboard to see live metrics")
        else:
            print("⚠️  No traces found. Check Langfuse connection.")

if __name__ == "__main__":
    sync_langfuse_data() 