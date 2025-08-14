#!/usr/bin/env python3
"""
Create test data for A/B testing demonstration
"""

import random
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Trace, Cost

def create_test_traces():
    """Create sample traces for A/B testing"""
    app = create_app()
    
    with app.app_context():
        # Clear existing test data
        Trace.query.filter(Trace.trace_id.like('test_%')).delete()
        Cost.query.filter(Cost.trace_id.like('test_%')).delete()
        
        # Create traces for Prompt A (ID: 1) - Detailed Extraction
        for i in range(50):
            duration = random.randint(1200, 3500)  # 1.2-3.5 seconds in ms
            trace = Trace(
                trace_id=f"test_prompt_a_{i}",
                name=f"Email Processing Test {i}",
                prompt_id=1,
                status=random.choice(['success'] * 8 + ['error'] * 2),  # 80% success
                duration_ms=duration,
                start_time=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                end_time=datetime.utcnow() - timedelta(days=random.randint(0, 30)) + timedelta(milliseconds=duration),
                user_id=1
            )
            db.session.add(trace)
            db.session.flush()  # Get the ID
            
            # Add cost data
            input_tokens = random.randint(200, 500)
            output_tokens = random.randint(100, 300)
            cost = Cost(
                trace_id=trace.id,
                model='gemini-1.5-pro',
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=round((input_tokens * 0.0015 + output_tokens * 0.002) / 1000, 6),
                timestamp=trace.start_time
            )
            db.session.add(cost)
        
        # Create traces for Prompt B (ID: 2) - Executive Summary  
        for i in range(45):
            duration = random.randint(800, 2100)  # Faster: 0.8-2.1 seconds in ms
            trace = Trace(
                trace_id=f"test_prompt_b_{i}",
                name=f"Executive Summary Test {i}",
                prompt_id=2,
                status=random.choice(['success'] * 9 + ['error'] * 1),  # 90% success (better!)
                duration_ms=duration,
                start_time=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                end_time=datetime.utcnow() - timedelta(days=random.randint(0, 30)) + timedelta(milliseconds=duration),
                user_id=1
            )
            db.session.add(trace)
            db.session.flush()  # Get the ID
            
            # Add cost data (lower cost due to fewer tokens)
            input_tokens = random.randint(150, 350)  # More efficient
            output_tokens = random.randint(80, 200)   # Shorter responses
            cost = Cost(
                trace_id=trace.id,
                model='gemini-1.5-pro',
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=round((input_tokens * 0.0015 + output_tokens * 0.002) / 1000, 6),
                timestamp=trace.start_time
            )
            db.session.add(cost)
        
        db.session.commit()
        print("✅ Created 95 test traces for A/B testing")
        print("📊 Prompt A (Detailed): 50 traces, ~80% success rate, slower/expensive")
        print("📊 Prompt B (Executive): 45 traces, ~90% success rate, faster/cheaper")
        print("🎯 Expected winner: Prompt B (Executive Summary)")

if __name__ == '__main__':
    create_test_traces()