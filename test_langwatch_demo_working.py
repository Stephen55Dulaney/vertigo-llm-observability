#!/usr/bin/env python3
"""
Working Langwatch demo for CTO meeting using correct API.
"""

import os
import sys
from datetime import datetime

# Add path and load environment
sys.path.append('vertigo-debug-toolkit')
from dotenv import load_dotenv
load_dotenv('vertigo-debug-toolkit/.env')

# Import langwatch with correct API
import langwatch

def setup_langwatch():
    """Setup Langwatch with API key."""
    api_key = os.getenv('LANGWATCH_API_KEY')
    if not api_key:
        print("❌ LANGWATCH_API_KEY not found in environment")
        return False
    
    print(f"🔑 Using Langwatch API key: {api_key[:20]}...")
    
    # Setup LangWatch with correct API
    langwatch.setup(api_key=api_key)
    print("✅ LangWatch setup complete")
    return True

def create_demo_traces():
    """Create demo traces for the CTO meeting."""
    
    demo_scenarios = [
        {
            "name": "Vertigo Email Processing Demo",
            "input": "Processing help request email via Vertigo system",
            "operation": "email_processing"
        },
        {
            "name": "Gemini LLM Analysis Demo", 
            "input": "Analyzing meeting transcript with Gemini-1.5-Pro",
            "operation": "llm_analysis"
        },
        {
            "name": "Executive Status Generation Demo",
            "input": "Generating daily executive summary from meeting data",
            "operation": "status_generation"
        }
    ]
    
    trace_count = 0
    
    for scenario in demo_scenarios:
        try:
            print(f"📊 Creating trace: {scenario['name']}")
            
            # Use the correct @langwatch.trace() decorator approach
            @langwatch.trace(
                name=scenario['name'],
                metadata={
                    "system": "vertigo",
                    "demo": "langwatch_cto_meeting",
                    "operation": scenario['operation'],
                    "timestamp": datetime.now().isoformat(),
                    "user_id": "vertigo_demo"
                }
            )
            def demo_operation():
                # Simulate processing
                print(f"   Input: {scenario['input']}")
                result = f"Successfully completed {scenario['operation']} operation"
                print(f"   Output: {result}")
                return result
            
            # Execute the traced operation
            result = demo_operation()
            trace_count += 1
            print(f"✅ Trace {trace_count} created successfully")
            
        except Exception as e:
            print(f"❌ Error creating trace: {e}")
    
    return trace_count

def main():
    """Main demo function."""
    print("🚀 LangWatch CTO Demo - Vertigo Integration")
    print("=" * 50)
    
    # Setup LangWatch
    if not setup_langwatch():
        return
    
    # Create demo traces
    print("\n📈 Creating Demo Traces...")
    trace_count = create_demo_traces()
    
    print(f"\n🎉 Demo Complete!")
    print(f"✅ Created {trace_count} traces successfully")
    print(f"🎯 View traces at: https://app.langwatch.ai/eunoia-Eyh6Gz/analytics/users")
    print(f"🎤 Ready for your CTO demo!")

if __name__ == "__main__":
    main()