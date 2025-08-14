#!/usr/bin/env python3
"""
Verify that test data was created and show basic metrics.
"""

from app import create_app, db
from app.models import Trace, Cost, Prompt
from datetime import datetime, timedelta

def verify_data():
    """Verify the test data and show basic metrics."""
    
    print("🔍 Verifying Test Data")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        # Check traces
        total_traces = Trace.query.count()
        success_traces = Trace.query.filter_by(status="success").count()
        error_traces = Trace.query.filter_by(status="error").count()
        
        print(f"📊 Traces:")
        print(f"   • Total: {total_traces}")
        print(f"   • Success: {success_traces}")
        print(f"   • Errors: {error_traces}")
        print(f"   • Success Rate: {(success_traces/total_traces*100):.1f}%" if total_traces > 0 else "   • Success Rate: N/A")
        
        # Check costs
        total_costs = Cost.query.count()
        total_cost_usd = sum(c.cost_usd for c in Cost.query.all())
        
        print(f"\n💰 Costs:")
        print(f"   • Total Records: {total_costs}")
        print(f"   • Total Cost: ${total_cost_usd:.4f}")
        
        # Check prompts
        total_prompts = Prompt.query.count()
        print(f"\n📝 Prompts:")
        print(f"   • Total: {total_prompts}")
        
        # Show some sample traces
        print(f"\n📋 Sample Traces:")
        sample_traces = Trace.query.limit(5).all()
        for trace in sample_traces:
            print(f"   • {trace.name} - {trace.status} - {trace.duration_ms}ms")
        
        # Show metadata structure
        if sample_traces:
            print(f"\n🔍 Metadata Structure:")
            metadata = sample_traces[0].trace_metadata
            if metadata:
                for key, value in metadata.items():
                    print(f"   • {key}: {value}")
        
        print(f"\n✅ Data verification complete!")
        print(f"📊 The advanced evaluation system is ready to use!")

if __name__ == "__main__":
    verify_data() 