#!/usr/bin/env python3
"""
Langfuse Evaluation Dataset Setup for Vertigo
Create evaluation datasets for different prompt types and establish testing framework.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langfuse import Langfuse

# Initialize Langfuse client with proper credentials
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
)

def create_meeting_summary_dataset():
    """Create evaluation dataset for meeting summary prompts."""
    
    # Sample meeting transcripts for evaluation
    meeting_samples = [
        {
            "input": "Meeting: Project Vertigo Development Discussion\n\nStephen: We need to focus on the Langfuse integration today. The evaluation framework is critical.\n\nJeff: Absolutely. Eval, eval, eval is our priority. We need measurable improvements.\n\nStephen: I'll set up the A/B testing framework and create evaluation datasets.\n\nJeff: Perfect. Let's track success rates and cost optimization.",
            "expected_output": {
                "meeting_summary": "Project Vertigo Development Discussion focused on Langfuse integration and evaluation framework.",
                "key_points": [
                    "Langfuse integration is critical for project success",
                    "Evaluation framework needs to be prioritized",
                    "A/B testing framework needs to be set up",
                    "Success rates and cost optimization need tracking"
                ],
                "action_items": [
                    "Set up A/B testing framework - Stephen",
                    "Create evaluation datasets - Stephen",
                    "Track success rates and costs - Team"
                ],
                "participants": ["Stephen", "Jeff"],
                "project": "vertigo"
            }
        },
        {
            "input": "Meeting: AI System Optimization\n\nTeam: We're seeing 85% success rate with current prompts.\n\nManager: We need to get to 95%. What's our evaluation strategy?\n\nTeam: We'll implement systematic A/B testing and track metrics.\n\nManager: Good. Focus on cost efficiency too.",
            "expected_output": {
                "meeting_summary": "AI System Optimization discussion focused on improving success rates from 85% to 95%.",
                "key_points": [
                    "Current success rate is 85%",
                    "Target success rate is 95%",
                    "Systematic A/B testing needed",
                    "Cost efficiency is important"
                ],
                "action_items": [
                    "Implement systematic A/B testing - Team",
                    "Track performance metrics - Team",
                    "Focus on cost efficiency - Team"
                ],
                "participants": ["Team", "Manager"],
                "project": "ai-optimization"
            }
        }
    ]
    
    # Create dataset using correct API syntax
    dataset = langfuse.create_dataset(
        name="vertigo-meeting-summary-evaluation",
        description="Evaluation dataset for meeting summary prompts in Vertigo system"
    )
    
    print(f"✅ Created meeting summary dataset: {dataset.id}")
    
    # Add evaluation items
    for i, sample in enumerate(meeting_samples):
        item = langfuse.create_dataset_item(
            dataset_name="vertigo-meeting-summary-evaluation",
            input=sample["input"],
            expected_output=json.dumps(sample["expected_output"]),
            id=f"meeting-summary-sample-{i+1}"
        )
        print(f"  ✅ Added sample {i+1}")
    
    return dataset.id

def create_daily_summary_dataset():
    """Create evaluation dataset for daily summary prompts."""
    
    daily_samples = [
        {
            "input": "Daily Work Log:\n- Fixed email command parser issues\n- Deployed updated Cloud Function\n- Set up Langfuse evaluation framework\n- Created daily ambition document\n- Tested prompt evaluation tools",
            "expected_output": {
                "my_ambition": "Complete Langfuse evaluation tool integration and establish robust prompt testing framework",
                "what_we_did_today": [
                    "Fixed email command parser to handle reply subjects",
                    "Deployed updated Cloud Function with improved error handling",
                    "Set up Langfuse evaluation framework for systematic testing",
                    "Created comprehensive daily ambition document",
                    "Tested advanced prompt evaluation tools"
                ],
                "what_well_do_next": [
                    "Configure Langfuse evaluation datasets for different prompt types",
                    "Implement A/B testing framework for systematic comparison",
                    "Establish automated evaluation workflows and reporting",
                    "Create prompt variants for optimization testing",
                    "Build continuous improvement loops based on evaluation results"
                ]
            }
        },
        {
            "input": "Daily Work Log:\n- Implemented A/B testing framework\n- Created evaluation datasets\n- Optimized prompt performance\n- Reduced costs by 15%\n- Improved success rate to 92%",
            "expected_output": {
                "my_ambition": "Achieve 95% success rate through systematic evaluation and optimization",
                "what_we_did_today": [
                    "Implemented comprehensive A/B testing framework",
                    "Created evaluation datasets for all prompt types",
                    "Optimized prompt performance through systematic testing",
                    "Reduced operational costs by 15% through optimization",
                    "Improved overall success rate to 92%"
                ],
                "what_well_do_next": [
                    "Scale successful optimization patterns to all prompts",
                    "Implement automated evaluation triggers",
                    "Create predictive models for prompt performance",
                    "Integrate user feedback into evaluation framework",
                    "Achieve target 95% success rate"
                ]
            }
        }
    ]
    
    # Create dataset
    dataset = langfuse.create_dataset(
        name="vertigo-daily-summary-evaluation",
        description="Evaluation dataset for daily summary prompts in Vertigo system"
    )
    
    print(f"✅ Created daily summary dataset: {dataset.id}")
    
    # Add evaluation items
    for i, sample in enumerate(daily_samples):
        item = langfuse.create_dataset_item(
            dataset_name="vertigo-meeting-summary-evaluation",
            input=sample["input"],
            expected_output=json.dumps(sample["expected_output"]),
            id=f"daily-summary-sample-{i+1}"
        )
        print(f"  ✅ Added sample {i+1}")
    
    return dataset.id

def create_status_update_dataset():
    """Create evaluation dataset for status update prompts."""
    
    status_samples = [
        {
            "input": "Generate status update for Project Vertigo. Current progress: 75% complete. Recent achievements: Fixed email parser, deployed Cloud Function, set up evaluation framework. Next steps: Implement A/B testing, optimize prompts.",
            "expected_output": {
                "status_summary": "Project Vertigo is 75% complete with significant progress on core functionality.",
                "recent_achievements": [
                    "Fixed email command parser issues",
                    "Successfully deployed updated Cloud Function",
                    "Established Langfuse evaluation framework"
                ],
                "current_progress": "75% complete",
                "next_steps": [
                    "Implement comprehensive A/B testing framework",
                    "Optimize prompts based on evaluation results",
                    "Scale successful patterns across all components"
                ],
                "risks_blockers": "No major blockers identified",
                "timeline": "On track for completion"
            }
        },
        {
            "input": "Generate status update for AI Evaluation System. Current progress: 90% complete. Recent achievements: Achieved 92% success rate, reduced costs by 15%, implemented automated testing. Next steps: Reach 95% target, deploy to production.",
            "expected_output": {
                "status_summary": "AI Evaluation System is 90% complete with excellent performance metrics.",
                "recent_achievements": [
                    "Achieved 92% success rate through optimization",
                    "Reduced operational costs by 15%",
                    "Implemented comprehensive automated testing"
                ],
                "current_progress": "90% complete",
                "next_steps": [
                    "Reach target 95% success rate",
                    "Deploy optimized system to production",
                    "Monitor performance and iterate"
                ],
                "risks_blockers": "No blockers - on track for target",
                "timeline": "Ready for production deployment"
            }
        }
    ]
    
    # Create dataset
    dataset = langfuse.create_dataset(
        name="vertigo-status-update-evaluation",
        description="Evaluation dataset for status update prompts in Vertigo system"
    )
    
    print(f"✅ Created status update dataset: {dataset.id}")
    
    # Add evaluation items
    for i, sample in enumerate(status_samples):
        item = langfuse.create_dataset_item(
            dataset_name="vertigo-meeting-summary-evaluation",
            input=sample["input"],
            expected_output=json.dumps(sample["expected_output"]),
            id=f"status-update-sample-{i+1}"
        )
        print(f"  ✅ Added sample {i+1}")
    
    return dataset.id

def create_evaluation_criteria():
    """Define evaluation criteria for different aspects of prompt performance."""
    
    criteria = {
        "accuracy": {
            "description": "How accurately does the output match the expected result?",
            "scale": "1-5",
            "1": "Completely inaccurate or irrelevant",
            "2": "Partially accurate but missing key elements",
            "3": "Generally accurate with some minor issues",
            "4": "Very accurate with minimal issues",
            "5": "Perfect accuracy and relevance"
        },
        "completeness": {
            "description": "How complete is the output compared to expectations?",
            "scale": "1-5",
            "1": "Missing most required elements",
            "2": "Missing several important elements",
            "3": "Contains most elements with some gaps",
            "4": "Contains all elements with minor omissions",
            "5": "Complete and comprehensive"
        },
        "clarity": {
            "description": "How clear and well-structured is the output?",
            "scale": "1-5",
            "1": "Unclear and poorly structured",
            "2": "Somewhat unclear or disorganized",
            "3": "Generally clear with some issues",
            "4": "Clear and well-structured",
            "5": "Exceptionally clear and professional"
        },
        "cost_efficiency": {
            "description": "How cost-effective is the prompt in terms of tokens used?",
            "scale": "1-5",
            "1": "Very expensive for the output quality",
            "2": "Somewhat expensive",
            "3": "Moderate cost for quality",
            "4": "Good cost-to-quality ratio",
            "5": "Excellent cost efficiency"
        }
    }
    
    return criteria

def test_langfuse_connection():
    """Test Langfuse connection and credentials."""
    try:
        print("🔍 Testing Langfuse connection...")
        print(f"Public Key: {os.getenv('LANGFUSE_PUBLIC_KEY', 'Not set')[:10]}...")
        print(f"Secret Key: {os.getenv('LANGFUSE_SECRET_KEY', 'Not set')[:10]}...")
        print(f"Host: {os.getenv('LANGFUSE_HOST', 'Not set')}")
        
        # Test basic connection
        traces = langfuse.api.trace.list(limit=1)
        print("✅ Langfuse connection successful!")
        return True
    except Exception as e:
        print(f"❌ Langfuse connection failed: {e}")
        return False

def main():
    """Set up all evaluation datasets for Vertigo."""
    
    print("🚀 Setting up Langfuse Evaluation Datasets for Vertigo")
    print("=" * 60)
    
    # Test connection first
    if not test_langfuse_connection():
        print("❌ Cannot proceed without Langfuse connection")
        return
    
    try:
        # Create datasets
        meeting_dataset_id = create_meeting_summary_dataset()
        daily_dataset_id = create_daily_summary_dataset()
        status_dataset_id = create_status_update_dataset()
        
        # Create evaluation criteria
        criteria = create_evaluation_criteria()
        
        # Save dataset IDs and criteria
        config = {
            "datasets": {
                "meeting_summary": meeting_dataset_id,
                "daily_summary": daily_dataset_id,
                "status_update": status_dataset_id
            },
            "evaluation_criteria": criteria,
            "created_at": datetime.utcnow().isoformat()
        }
        
        with open("langfuse_evaluation_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("\n✅ Evaluation Setup Complete!")
        print("=" * 60)
        print(f"📊 Meeting Summary Dataset: {meeting_dataset_id}")
        print(f"📊 Daily Summary Dataset: {daily_dataset_id}")
        print(f"📊 Status Update Dataset: {status_dataset_id}")
        print(f"📋 Evaluation Criteria: {len(criteria)} criteria defined")
        print(f"💾 Config saved to: langfuse_evaluation_config.json")
        
        print("\n🎯 Next Steps:")
        print("1. Run A/B tests using these datasets")
        print("2. Implement automated evaluation triggers")
        print("3. Create prompt variants for testing")
        print("4. Set up continuous improvement workflows")
        
    except Exception as e:
        print(f"❌ Error setting up evaluation datasets: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 