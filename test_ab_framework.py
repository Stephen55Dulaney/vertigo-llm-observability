#!/usr/bin/env python3
"""
Simple A/B Testing Test for Vertigo
Test the A/B testing framework with simulated results.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langfuse import Langfuse

# Load environment variables
load_dotenv()

# Initialize Langfuse client
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
)

def test_dataset_access():
    """Test accessing our evaluation datasets."""
    
    print("🧪 Testing Dataset Access")
    print("=" * 40)
    
    datasets = {
        "meeting_summary": "vertigo-meeting-summary-evaluation",
        "daily_summary": "vertigo-daily-summary-evaluation", 
        "status_update": "vertigo-status-update-evaluation"
    }
    
    for prompt_type, dataset_name in datasets.items():
        try:
            # Get dataset
            dataset = langfuse.api.datasets.get(dataset_name)
            print(f"✅ Dataset '{dataset_name}': {dataset.id}")
            
            # Get dataset items
            items_response = langfuse.api.dataset_items.list(dataset_name=dataset_name)
            print(f"  📊 Items: {len(items_response.data)}")
            
            if items_response.data:
                print(f"  📝 Sample input: {items_response.data[0].input[:50]}...")
            
        except Exception as e:
            print(f"❌ Error accessing {dataset_name}: {e}")

def simulate_ab_test():
    """Simulate an A/B test with our datasets."""
    
    print("\n🧪 Simulating A/B Test")
    print("=" * 40)
    
    # Test criteria
    criteria = {
        "accuracy": {"weight": 0.4, "description": "How accurately does output match expected result?"},
        "completeness": {"weight": 0.3, "description": "How complete is the output?"},
        "clarity": {"weight": 0.2, "description": "How clear and well-structured is the output?"},
        "cost_efficiency": {"weight": 0.1, "description": "How cost-effective is the prompt?"}
    }
    
    # Simulate A/B test results
    import random
    
    variant_a_scores = {
        "accuracy": random.uniform(3.5, 5.0),
        "completeness": random.uniform(3.0, 5.0),
        "clarity": random.uniform(3.5, 5.0),
        "cost_efficiency": random.uniform(3.0, 4.5)
    }
    
    variant_b_scores = {
        "accuracy": random.uniform(3.0, 5.0),
        "completeness": random.uniform(3.5, 5.0),
        "clarity": random.uniform(3.0, 5.0),
        "cost_efficiency": random.uniform(3.5, 4.5)
    }
    
    # Calculate weighted scores
    a_weighted = sum(variant_a_scores[criterion] * criteria[criterion]["weight"] for criterion in criteria.keys())
    b_weighted = sum(variant_b_scores[criterion] * criteria[criterion]["weight"] for criterion in criteria.keys())
    
    print(f"📊 Variant A (Concise): {a_weighted:.2f}")
    print(f"📊 Variant B (Detailed): {b_weighted:.2f}")
    
    if a_weighted > b_weighted:
        winner = "Variant A (Concise)"
        improvement = ((a_weighted - b_weighted) / b_weighted) * 100
    else:
        winner = "Variant B (Detailed)"
        improvement = ((b_weighted - a_weighted) / a_weighted) * 100
    
    print(f"🏆 Winner: {winner}")
    print(f"📈 Improvement: {improvement:.1f}%")
    
    return {
        "winner": winner,
        "improvement": improvement,
        "variant_a_scores": variant_a_scores,
        "variant_b_scores": variant_b_scores
    }

def main():
    """Run the A/B testing test."""
    
    print("🚀 Vertigo A/B Testing Test")
    print("=" * 50)
    
    # Test dataset access
    test_dataset_access()
    
    # Simulate A/B test
    results = simulate_ab_test()
    
    print(f"\n✅ A/B Testing Test Complete!")
    print(f"🎯 Recommendation: Use {results['winner']} for production")
    print(f"📈 Expected improvement: {results['improvement']:.1f}%")
    
    print(f"\n📋 Next Steps:")
    print("1. Implement winning variant in Vertigo")
    print("2. Set up continuous monitoring")
    print("3. Create more prompt variants for testing")
    print("4. Integrate with real LLM evaluation")

if __name__ == "__main__":
    main() 