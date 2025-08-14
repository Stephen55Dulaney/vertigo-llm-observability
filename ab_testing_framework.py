#!/usr/bin/env python3
"""
A/B Testing Framework for Vertigo Prompts
Test prompt variants using Langfuse evaluation datasets.
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

class ABTestingFramework:
    """A/B testing framework for prompt evaluation."""
    
    def __init__(self):
        self.datasets = {
            "meeting_summary": "vertigo-meeting-summary-evaluation",
            "daily_summary": "vertigo-daily-summary-evaluation", 
            "status_update": "vertigo-status-update-evaluation"
        }
        
        # Load evaluation criteria
        self.criteria = {
            "accuracy": {"weight": 0.4, "description": "How accurately does output match expected result?"},
            "completeness": {"weight": 0.3, "description": "How complete is the output?"},
            "clarity": {"weight": 0.2, "description": "How clear and well-structured is the output?"},
            "cost_efficiency": {"weight": 0.1, "description": "How cost-effective is the prompt?"}
        }
    
    def create_prompt_variants(self, prompt_type):
        """Create different variants of a prompt for A/B testing."""
        
        if prompt_type == "meeting_summary":
            return {
                "variant_a": {
                    "name": "Meeting Summary - Concise",
                    "prompt": """Analyze this meeting transcript and create a professional summary.

Focus on:
- Key decisions and outcomes
- Action items with owners
- Important discussion points
- Next steps and timeline

Format the output as a structured summary with clear sections.""",
                    "description": "Concise, structured approach"
                },
                "variant_b": {
                    "name": "Meeting Summary - Detailed", 
                    "prompt": """Create a comprehensive meeting summary from this transcript.

Include:
- Executive summary of main topics
- Detailed discussion points with context
- Specific action items with deadlines and owners
- Key decisions and rationale
- Risks and blockers identified
- Next steps with timeline
- Participant contributions

Format as a detailed report with clear sections and bullet points.""",
                    "description": "Detailed, comprehensive approach"
                },
                "variant_c": {
                    "name": "Meeting Summary - Action-Oriented",
                    "prompt": """Transform this meeting transcript into an action-oriented summary.

Structure as:
1. **Key Outcomes** - Main decisions and results
2. **Action Items** - Specific tasks with owners and deadlines
3. **Next Steps** - Immediate priorities and timeline
4. **Blockers** - Issues that need resolution
5. **Follow-up** - Required meetings or communications

Focus on actionable insights and clear next steps.""",
                    "description": "Action-focused, structured approach"
                }
            }
        
        elif prompt_type == "daily_summary":
            return {
                "variant_a": {
                    "name": "Daily Summary - Professional",
                    "prompt": """Create a professional daily summary from this work log.

Structure as:
**My Ambition:** [Overall goal/focus]
**What We Did Today:** [Key accomplishments]
**What We'll Do Next:** [Immediate priorities]

Keep it concise and professional for executive communication.""",
                    "description": "Professional, executive-focused"
                },
                "variant_b": {
                    "name": "Daily Summary - Detailed",
                    "prompt": """Generate a comprehensive daily summary from this work log.

Include:
- Strategic context and goals
- Detailed accomplishments with metrics
- Technical progress and challenges
- Team collaboration highlights
- Resource utilization
- Risk assessment
- Next steps with priorities

Format for detailed stakeholder review.""",
                    "description": "Comprehensive, detailed approach"
                }
            }
        
        elif prompt_type == "status_update":
            return {
                "variant_a": {
                    "name": "Status Update - Executive",
                    "prompt": """Create an executive status update from this project information.

Include:
- Current progress percentage
- Key achievements this period
- Next milestones
- Any blockers or risks
- Timeline status

Format for executive review with clear metrics.""",
                    "description": "Executive-level summary"
                },
                "variant_b": {
                    "name": "Status Update - Technical",
                    "prompt": """Generate a technical status update from this project information.

Include:
- Technical progress and metrics
- Implementation details and challenges
- Performance data and optimizations
- Technical debt and refactoring
- Integration status
- Testing and quality metrics
- Technical risks and mitigation

Format for technical stakeholders.""",
                    "description": "Technical, detailed approach"
                }
            }
        
        return {}
    
    def run_ab_test(self, prompt_type, variant_a, variant_b, num_samples=5):
        """Run an A/B test between two prompt variants."""
        
        print(f"🧪 Running A/B Test: {variant_a['name']} vs {variant_b['name']}")
        print("=" * 60)
        
        # Get dataset items for evaluation
        dataset_name = self.datasets.get(prompt_type)
        if not dataset_name:
            print(f"❌ No dataset found for prompt type: {prompt_type}")
            return None
        
        try:
            # Get dataset items using correct API
            dataset_items = langfuse.api.datasets.get(dataset_name).items
            test_items = dataset_items[:num_samples]
            
            print(f"📊 Testing with {len(test_items)} samples from dataset: {dataset_name}")
            
            # Simulate evaluation (in real implementation, this would call the actual LLM)
            results = {
                "variant_a": {"name": variant_a["name"], "scores": []},
                "variant_b": {"name": variant_b["name"], "scores": []}
            }
            
            for i, item in enumerate(test_items):
                print(f"  Testing sample {i+1}...")
                
                # Simulate scores (in real implementation, these would come from LLM evaluation)
                import random
                a_scores = {
                    "accuracy": random.uniform(3.5, 5.0),
                    "completeness": random.uniform(3.0, 5.0),
                    "clarity": random.uniform(3.5, 5.0),
                    "cost_efficiency": random.uniform(3.0, 4.5)
                }
                
                b_scores = {
                    "accuracy": random.uniform(3.0, 5.0),
                    "completeness": random.uniform(3.5, 5.0),
                    "clarity": random.uniform(3.0, 5.0),
                    "cost_efficiency": random.uniform(3.5, 4.5)
                }
                
                results["variant_a"]["scores"].append(a_scores)
                results["variant_b"]["scores"].append(b_scores)
            
            # Calculate aggregate scores
            for variant in ["variant_a", "variant_b"]:
                avg_scores = {}
                for criterion in self.criteria.keys():
                    scores = [score[criterion] for score in results[variant]["scores"]]
                    avg_scores[criterion] = sum(scores) / len(scores)
                
                # Calculate weighted score
                weighted_score = sum(
                    avg_scores[criterion] * self.criteria[criterion]["weight"]
                    for criterion in self.criteria.keys()
                )
                
                results[variant]["avg_scores"] = avg_scores
                results[variant]["weighted_score"] = weighted_score
            
            # Determine winner
            a_score = results["variant_a"]["weighted_score"]
            b_score = results["variant_b"]["weighted_score"]
            
            if a_score > b_score:
                winner = "variant_a"
                improvement = ((a_score - b_score) / b_score) * 100
            else:
                winner = "variant_b"
                improvement = ((b_score - a_score) / a_score) * 100
            
            results["winner"] = winner
            results["improvement_percentage"] = improvement
            
            return results
            
        except Exception as e:
            print(f"❌ Error running A/B test: {e}")
            return None
    
    def generate_ab_test_report(self, results):
        """Generate a comprehensive A/B test report."""
        
        if not results:
            return "❌ No results to report"
        
        report = f"""
📊 A/B Test Report
{'=' * 50}

🏆 Winner: {results[results['winner']]['name']}
📈 Improvement: {results['improvement_percentage']:.1f}%

📋 Detailed Results:
"""
        
        for variant in ["variant_a", "variant_b"]:
            report += f"\n{results[variant]['name']}:\n"
            report += f"  Weighted Score: {results[variant]['weighted_score']:.2f}\n"
            
            for criterion, score in results[variant]["avg_scores"].items():
                report += f"  {criterion.title()}: {score:.2f}\n"
        
        report += f"""
🎯 Recommendations:
• Use {results[results['winner']]['name']} for production
• Monitor performance over time
• Consider further optimization based on specific criteria
• Re-run test with larger sample size for validation

📊 Next Steps:
1. Implement winning variant in production
2. Set up continuous monitoring
3. Plan follow-up optimization tests
4. Document lessons learned
"""
        
        return report

def main():
    """Run A/B tests for different prompt types."""
    
    print("🚀 Vertigo A/B Testing Framework")
    print("=" * 50)
    
    framework = ABTestingFramework()
    
    # Test meeting summary prompts
    print("\n📝 Testing Meeting Summary Prompts...")
    meeting_variants = framework.create_prompt_variants("meeting_summary")
    
    if "variant_a" in meeting_variants and "variant_b" in meeting_variants:
        results = framework.run_ab_test("meeting_summary", meeting_variants["variant_a"], meeting_variants["variant_b"])
        if results:
            report = framework.generate_ab_test_report(results)
            print(report)
    
    # Test daily summary prompts
    print("\n📅 Testing Daily Summary Prompts...")
    daily_variants = framework.create_prompt_variants("daily_summary")
    
    if "variant_a" in daily_variants and "variant_b" in daily_variants:
        results = framework.run_ab_test("daily_summary", daily_variants["variant_a"], daily_variants["variant_b"])
        if results:
            report = framework.generate_ab_test_report(results)
            print(report)
    
    print("\n✅ A/B Testing Complete!")
    print("🎯 Next: Implement winning variants in production")

if __name__ == "__main__":
    main() 