#!/usr/bin/env python3
"""
Test EOD Prompt A/B Testing with Firestore Data
Uses the test_eod_firestore_data.json file to test different EOD prompt variants.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the parent directory to the path to import the A/B testing framework
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ab_testing_framework import ABTestingFramework

# Load environment variables
load_dotenv()

def load_test_data():
    """Load the test Firestore data."""
    try:
        with open('test_eod_firestore_data.json', 'r') as f:
            data = json.load(f)
        print(f"✅ Loaded test data with {len(data['meetings'])} meetings")
        return data
    except FileNotFoundError:
        print("❌ test_eod_firestore_data.json not found")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return None

def create_eod_prompt_variants():
    """Create different EOD prompt variants for testing."""
    
    return {
        "variant_a": {
            "name": "EOD Summary - Executive Focus",
            "prompt": """Create an executive-level end-of-day summary from the provided meeting data.

Structure as:
**Key Accomplishments:**
- [High-impact items completed today]

**Critical Decisions:**
- [Decisions that affect timeline/scope/resources]

**Blockers & Risks:**
- [Items needing executive attention]
- [Proposed solutions or escalation needs]

**Next Week Focus:**
- [3-4 priority items for upcoming week]

**Metrics & Progress:**
- [Quantifiable progress indicators]

Tone: Professional but conversational. Highlight what executives need to know and where they can help remove blockers.

Meeting Data:
{meeting_data}""",
            "description": "Executive-focused, structured approach"
        },
        
        "variant_b": {
            "name": "EOD Summary - Technical Deep Dive",
            "prompt": """Generate a comprehensive technical end-of-day summary from the meeting data.

Include:
**Technical Progress:**
- [Specific technical achievements and implementations]
- [Architecture decisions and rationale]
- [Performance metrics and optimizations]

**Development Status:**
- [Current sprint progress and milestones]
- [Code quality and testing status]
- [Integration points and dependencies]

**Technical Challenges:**
- [Technical blockers and their impact]
- [Performance issues and solutions]
- [Scalability considerations]

**Next Technical Priorities:**
- [Immediate technical tasks]
- [Architecture improvements needed]
- [Technical debt to address]

**Team Technical Capacity:**
- [Individual technical contributions]
- [Skill development needs]
- [Technical coordination requirements]

Format as a detailed technical report with clear sections and technical specifics.

Meeting Data:
{meeting_data}""",
            "description": "Technical-focused, comprehensive approach"
        },
        
        "variant_c": {
            "name": "EOD Summary - Action-Oriented",
            "prompt": """Create an action-oriented end-of-day summary focused on next steps and deliverables.

Structure as:
**What We Accomplished Today:**
- [Specific deliverables completed]
- [Milestones reached]
- [Key achievements]

**Immediate Action Items:**
- [Tasks for tomorrow with owners]
- [Deadlines and priorities]
- [Required resources or support]

**Blockers to Resolve:**
- [Issues preventing progress]
- [Escalation needs]
- [Alternative approaches]

**Success Metrics:**
- [How we measure progress]
- [Current status vs targets]
- [Trends and patterns]

**Team Coordination:**
- [Who needs what from whom]
- [Communication requirements]
- [Meeting schedules]

Focus on actionable insights and clear next steps. Be specific about who does what by when.

Meeting Data:
{meeting_data}""",
            "description": "Action-focused, task-oriented approach"
        }
    }

def prepare_meeting_data_for_prompt(meetings):
    """Prepare meeting data in a format suitable for prompt input.
    
    This simulates the data that the EOD prompt would receive from Firestore
    for the last 24 hours of meetings.
    """
    
    meeting_summaries = []
    for meeting in meetings:
        # Extract key information
        summary = f"""
Meeting: {meeting['metadata']['meeting_title']}
Date: {meeting['timestamp']}
Duration: {meeting['metadata']['duration_minutes']} minutes
Participants: {', '.join(meeting['metadata']['participants'])}

Key Topics: {', '.join(meeting['structured_data']['key_topics'])}

Summary: {meeting['processed_notes'][:500]}...

Action Items: {len(meeting['structured_data'].get('action_items', []))} items
Blockers: {len(meeting['structured_data'].get('blockers', []))} identified
"""
        meeting_summaries.append(summary)
    
    return "\n\n".join(meeting_summaries)

def test_eod_prompt_variants():
    """Test different EOD prompt variants with the test data."""
    
    print("🚀 Testing EOD Prompt A/B Testing")
    print("=" * 60)
    
    # Load test data
    data = load_test_data()
    if not data:
        return
    
    # Create prompt variants
    variants = create_eod_prompt_variants()
    
    # Prepare meeting data
    meeting_data = prepare_meeting_data_for_prompt(data['meetings'])
    
    print(f"\n📊 Test Data Summary:")
    print(f"- Total meetings: {len(data['meetings'])}")
    print(f"- Date range: {data['summary_metadata']['date_range']}")
    print(f"- Participants: {', '.join(data['summary_metadata']['participants'])}")
    print(f"- Total duration: {data['summary_metadata']['total_duration_minutes']} minutes")
    print(f"- Key topics: {', '.join(data['summary_metadata']['key_topics'][:3])}...")
    
    print(f"\n🧪 Testing {len(variants)} EOD Prompt Variants:")
    
    # Test each variant
    results = {}
    for variant_name, variant in variants.items():
        print(f"\n--- Testing {variant['name']} ---")
        print(f"Description: {variant['description']}")
        
        # Format the prompt with actual data
        formatted_prompt = variant['prompt'].format(meeting_data=meeting_data)
        
        # Store the result
        results[variant_name] = {
            "name": variant['name'],
            "description": variant['description'],
            "prompt": formatted_prompt,
            "meeting_count": len(data['meetings']),
            "test_timestamp": datetime.now().isoformat()
        }
        
        print(f"✅ Prompt prepared with {len(data['meetings'])} meetings")
    
    # Save results for A/B testing
    output_file = f"eod_prompt_variants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "test_metadata": {
                "test_date": datetime.now().isoformat(),
                "data_source": "test_eod_firestore_data.json",
                "meeting_count": len(data['meetings']),
                "date_range": data['summary_metadata']['date_range']
            },
            "variants": results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    print(f"\n📋 Next Steps:")
    print(f"1. Use the A/B testing framework to evaluate these variants")
    print(f"2. Test with real Firestore data")
    print(f"3. Compare performance metrics")
    print(f"4. Select the best performing variant")
    
    return results

def run_ab_test():
    """Run an actual A/B test using the framework."""
    
    print("\n🔬 Running A/B Test with Framework")
    print("=" * 60)
    
    try:
        # Initialize the A/B testing framework
        ab_framework = ABTestingFramework()
        
        # Create variants for daily summary
        variants = ab_framework.create_prompt_variants("daily_summary")
        
        print(f"Created {len(variants)} variants for testing")
        
        # Run A/B test (this would normally use real data)
        print("Note: This is a demonstration. Real A/B testing would require:")
        print("- Actual Firestore data")
        print("- Langfuse integration")
        print("- Evaluation metrics")
        print("- Performance tracking")
        
        return variants
        
    except Exception as e:
        print(f"❌ Error running A/B test: {e}")
        return None

def main():
    """Main function to run the EOD prompt testing."""
    
    print("🎯 EOD Prompt A/B Testing Tool")
    print("=" * 60)
    
    # Test prompt variants
    results = test_eod_prompt_variants()
    
    if results:
        print(f"\n✅ Successfully created {len(results)} EOD prompt variants")
        print("Ready for A/B testing!")
    else:
        print("\n❌ Failed to create prompt variants")

if __name__ == "__main__":
    main() 