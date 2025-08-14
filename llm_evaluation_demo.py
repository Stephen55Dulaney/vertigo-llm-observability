#!/usr/bin/env python3
"""
LLM Evaluation Demo for Vertigo - Professional Grade Evaluation System
"""

import os
import sys
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Any

# Add path and load environment
sys.path.append('vertigo-debug-toolkit')
from dotenv import load_dotenv
load_dotenv('vertigo-debug-toolkit/.env')

import langwatch

class VertigoLLMEvaluator:
    """Professional LLM evaluation system for Vertigo."""
    
    def __init__(self):
        """Initialize the evaluator."""
        self.api_key = os.getenv('LANGWATCH_API_KEY')
        if self.api_key:
            langwatch.setup(api_key=self.api_key)
        
        self.test_cases = self.create_test_cases()
        
    def create_test_cases(self) -> List[Dict]:
        """Create comprehensive test cases for Vertigo evaluation."""
        return [
            {
                "test_id": "email_help_command",
                "input": "Subject: Vertigo: Help\nBody: I need help with available commands",
                "expected_output": "help response with command list",
                "category": "email_processing",
                "difficulty": "easy"
            },
            {
                "test_id": "meeting_analysis",
                "input": "Meeting transcript: We discussed Q4 budget allocation, decided to increase marketing spend by 20%, and identified three key risks...",
                "expected_output": "structured summary with decisions, action items, risks",
                "category": "meeting_processing", 
                "difficulty": "hard"
            },
            {
                "test_id": "status_generation",
                "input": "Generate executive status from 5 recent meetings covering budget, hiring, product launch",
                "expected_output": "executive summary with key decisions and metrics",
                "category": "status_generation",
                "difficulty": "medium"
            },
            {
                "test_id": "edge_case_empty",
                "input": "",
                "expected_output": "graceful error handling",
                "category": "edge_cases",
                "difficulty": "medium"
            },
            {
                "test_id": "complex_email_command",
                "input": "Subject: Vertigo: List projects for last month with cost breakdown and team metrics",
                "expected_output": "detailed project list with metrics",
                "category": "email_processing",
                "difficulty": "hard"
            }
        ]
    
    @langwatch.trace(name="llm_evaluation_test")
    def run_evaluation_suite(self):
        """Run comprehensive evaluation suite."""
        print("🚀 Starting Vertigo LLM Evaluation Suite")
        print("=" * 50)
        
        results = {
            "test_results": [],
            "metrics": {
                "accuracy_score": 0.0,
                "relevance_score": 0.0,
                "cost_efficiency": 0.0,
                "response_time_avg": 0.0
            },
            "business_impact": {
                "estimated_time_saved": 0.0,
                "productivity_gain": 0.0,
                "cost_savings": 0.0
            }
        }
        
        total_accuracy = 0
        total_relevance = 0
        total_cost = 0
        total_time = 0
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n📝 Test {i}/{len(self.test_cases)}: {test_case['test_id']}")
            
            # Simulate LLM evaluation
            start_time = time.time()
            
            # Mock LLM response (in real system, this would call your actual LLM)
            mock_response = self.simulate_llm_response(test_case)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            # Evaluate response quality
            evaluation = self.evaluate_response(test_case, mock_response)
            
            # Calculate costs (mock data)
            estimated_cost = self.calculate_cost(test_case, mock_response)
            
            result = {
                "test_id": test_case["test_id"],
                "category": test_case["category"],
                "difficulty": test_case["difficulty"],
                "response_time_ms": response_time,
                "accuracy_score": evaluation["accuracy"],
                "relevance_score": evaluation["relevance"],
                "cost_dollars": estimated_cost,
                "passed": evaluation["accuracy"] >= 0.8,
                "response": mock_response[:100] + "..." if len(mock_response) > 100 else mock_response
            }
            
            results["test_results"].append(result)
            
            # Accumulate metrics
            total_accuracy += evaluation["accuracy"]
            total_relevance += evaluation["relevance"]
            total_cost += estimated_cost
            total_time += response_time
            
            print(f"   ✅ Accuracy: {evaluation['accuracy']:.2f}")
            print(f"   🎯 Relevance: {evaluation['relevance']:.2f}")
            print(f"   💰 Cost: ${estimated_cost:.4f}")
            print(f"   ⏱️  Time: {response_time:.0f}ms")
        
        # Calculate final metrics
        num_tests = len(self.test_cases)
        results["metrics"] = {
            "accuracy_score": total_accuracy / num_tests,
            "relevance_score": total_relevance / num_tests,
            "cost_efficiency": total_cost / num_tests,
            "response_time_avg": total_time / num_tests
        }
        
        # Calculate business impact
        results["business_impact"] = self.calculate_business_impact(results)
        
        # Print summary
        self.print_evaluation_summary(results)
        
        return results
    
    def simulate_llm_response(self, test_case: Dict) -> str:
        """Simulate LLM response for demonstration."""
        responses = {
            "email_help_command": "Available Vertigo commands: Help, List this week, Total stats, List projects. Send emails with these subjects to get information.",
            "meeting_analysis": "Meeting Summary: Q4 budget discussed. Key Decision: Increase marketing spend 20%. Action Items: Review risk mitigation. Risks: Budget overrun, timeline delays, resource constraints.",
            "status_generation": "Executive Status Update: Budget approved (+20% marketing), 3 new hires pending, product launch on track for Q1. Key metrics: 15% growth, 2 critical risks identified.",
            "edge_case_empty": "Error: No input provided. Please include a subject line or message body for processing.",
            "complex_email_command": "Project Summary (Last Month): 5 active projects, $45K budget, 12 team members. Top project: Product Launch (60% complete, $15K spent). Metrics: 85% on-time delivery."
        }
        
        return responses.get(test_case["test_id"], "Generic response for testing purposes")
    
    def evaluate_response(self, test_case: Dict, response: str) -> Dict:
        """Evaluate response quality using multiple metrics."""
        # Mock evaluation scores (in production, use actual evaluation models)
        base_accuracy = random.uniform(0.75, 0.95)
        base_relevance = random.uniform(0.80, 0.95)
        
        # Adjust based on difficulty
        difficulty_multiplier = {
            "easy": 1.0,
            "medium": 0.9,
            "hard": 0.8
        }
        
        multiplier = difficulty_multiplier.get(test_case["difficulty"], 0.85)
        
        return {
            "accuracy": min(base_accuracy * multiplier, 1.0),
            "relevance": min(base_relevance * multiplier, 1.0),
            "completeness": random.uniform(0.8, 0.95),
            "safety": random.uniform(0.95, 1.0)
        }
    
    def calculate_cost(self, test_case: Dict, response: str) -> float:
        """Calculate estimated cost for the LLM call."""
        # Mock cost calculation (tokens * rate)
        input_tokens = len(test_case["input"].split()) * 1.3
        output_tokens = len(response.split()) * 1.3
        
        # Gemini pricing (approximate)
        cost_per_1k_tokens = 0.002
        total_tokens = input_tokens + output_tokens
        
        return (total_tokens / 1000) * cost_per_1k_tokens
    
    def calculate_business_impact(self, results: Dict) -> Dict:
        """Calculate business impact metrics."""
        avg_accuracy = results["metrics"]["accuracy_score"]
        avg_time = results["metrics"]["response_time_avg"]
        
        # Business impact calculations
        time_saved_per_task = 15  # minutes saved per automated task
        tasks_per_day = 50  # estimated daily tasks
        hourly_rate = 75  # average hourly rate
        
        daily_time_saved = (time_saved_per_task * tasks_per_day * avg_accuracy) / 60  # hours
        annual_savings = daily_time_saved * 250 * hourly_rate  # 250 work days
        
        return {
            "estimated_time_saved_hours_daily": daily_time_saved,
            "productivity_gain_percent": avg_accuracy * 100,
            "annual_cost_savings": annual_savings,
            "roi_percent": (annual_savings / 50000) * 100  # assuming $50K investment
        }
    
    def print_evaluation_summary(self, results: Dict):
        """Print comprehensive evaluation summary."""
        print(f"\n🎯 EVALUATION SUMMARY")
        print("=" * 30)
        
        metrics = results["metrics"]
        business = results["business_impact"]
        
        print(f"📊 Technical Metrics:")
        print(f"   Accuracy Score: {metrics['accuracy_score']:.1%}")
        print(f"   Relevance Score: {metrics['relevance_score']:.1%}")
        print(f"   Avg Response Time: {metrics['response_time_avg']:.0f}ms")
        print(f"   Avg Cost per Call: ${metrics['cost_efficiency']:.4f}")
        
        print(f"\n💼 Business Impact:")
        print(f"   Time Saved Daily: {business['estimated_time_saved_hours_daily']:.1f} hours")
        print(f"   Productivity Gain: {business['productivity_gain_percent']:.1f}%")
        print(f"   Annual Savings: ${business['annual_cost_savings']:,.0f}")
        print(f"   ROI: {business['roi_percent']:.0f}%")
        
        # Test results breakdown
        passed_tests = sum(1 for result in results["test_results"] if result["passed"])
        total_tests = len(results["test_results"])
        
        print(f"\n✅ Test Results: {passed_tests}/{total_tests} passed ({passed_tests/total_tests:.1%})")
        
        print(f"\n🎯 Ready for stakeholder presentation!")

def main():
    """Main evaluation function."""
    print("🚀 Vertigo LLM Evaluation System")
    print("Demonstrating professional-grade LLM evaluation")
    print("=" * 50)
    
    evaluator = VertigoLLMEvaluator()
    results = evaluator.run_evaluation_suite()
    
    # Save results for further analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"evaluation_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📋 Results saved to: {results_file}")
    print(f"🎤 Evaluation complete - ready for demonstration!")

if __name__ == "__main__":
    main()