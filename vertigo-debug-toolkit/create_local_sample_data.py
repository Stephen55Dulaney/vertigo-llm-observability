#!/usr/bin/env python3
"""
Create sample data directly in the local database for dashboard demonstration.
"""

import os
import sys
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Trace, Cost, Prompt

def create_sample_data():
    """Create sample data in the local database."""
    
    print("🚀 Creating Sample Data for Dashboard")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Clear existing data
        print("🗑️  Clearing existing data...")
        Trace.query.delete()
        Cost.query.delete()
        db.session.commit()
        print("✅ Existing data cleared")
        
        # Create sample traces for the last 7 days
        trace_count = 0
        cost_total = 0.0
        
        for day in range(7):
            date = datetime.now() - timedelta(days=day)
            
            # Create 3-5 traces per day
            traces_per_day = 4 if day < 4 else 3
            
            for trace_num in range(traces_per_day):
                # Create trace
                trace = Trace(
                    trace_id=f"sample-trace-{day}-{trace_num}",
                    name=f"Sample Workflow - Day {day + 1} - Trace {trace_num + 1}",
                    status="success" if trace_num % 5 != 0 else "error",  # 80% success rate
                    start_time=date.replace(hour=9 + trace_num, minute=30),
                    end_time=date.replace(hour=9 + trace_num, minute=35),
                    duration_ms=5000 + (trace_num * 1000),  # 5-9 seconds
                    trace_metadata={
                        "project": "vertigo",
                        "workflow_type": "meeting_processing",
                        "model": "gpt-4" if trace_num % 2 == 0 else "gpt-3.5-turbo"
                    },
                    error_message="" if trace_num % 5 != 0 else "Sample error message",
                    vertigo_operation="meeting_summary",
                    project="vertigo",
                    meeting_id=f"meeting-{day}-{trace_num}"
                )
                
                db.session.add(trace)
                trace_count += 1
                
                # Create cost record
                cost_amount = 0.002 + (trace_num * 0.001)
                cost = Cost(
                    trace_id=trace.trace_id,
                    model="gpt-4" if trace_num % 2 == 0 else "gpt-3.5-turbo",
                    input_tokens=150 + (trace_num * 10),
                    output_tokens=50 + (trace_num * 5),
                    cost_usd=cost_amount,
                    timestamp=date.replace(hour=9 + trace_num, minute=30)
                )
                
                db.session.add(cost)
                cost_total += cost_amount
        
        # Commit all data
        db.session.commit()
        
        print(f"✅ Created {trace_count} sample traces")
        print(f"💰 Total cost: ${cost_total:.4f}")
        print("\n📊 Dashboard should now show:")
        print(f"   • {trace_count} total traces")
        print(f"   • {cost_total:.4f} total cost")
        print(f"   • Performance charts with data")
        print(f"   • Cost breakdown by model")
        
        # Show some stats
        success_traces = Trace.query.filter_by(status="success").count()
        error_traces = Trace.query.filter_by(status="error").count()
        success_rate = (success_traces / trace_count * 100) if trace_count > 0 else 0
        
        print(f"\n📈 Sample Statistics:")
        print(f"   • Success Rate: {success_rate:.1f}%")
        print(f"   • Success Traces: {success_traces}")
        print(f"   • Error Traces: {error_traces}")
        print(f"   • Average Duration: {Trace.query.with_entities(db.func.avg(Trace.duration_ms)).scalar():.0f}ms")

if __name__ == "__main__":
    create_sample_data() 