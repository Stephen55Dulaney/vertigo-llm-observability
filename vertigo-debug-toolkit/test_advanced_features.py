#!/usr/bin/env python3
"""
Test script for advanced prompt evaluation features.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Trace, Cost, Prompt, User
from app.services.prompt_evaluator import PromptEvaluator
from datetime import datetime, timedelta
import random

def create_test_data():
    """Create comprehensive test data for advanced evaluation."""
    print("🔧 Creating test data for advanced evaluation...")
    
    # Clear existing test data
    Trace.query.delete()
    Cost.query.delete()
    
    # Get or create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        db.session.add(admin)
        db.session.commit()
    
    # Get prompts
    prompts = Prompt.query.all()
    if not prompts:
        print("❌ No prompts found. Please add some prompts first.")
        return False
    
    print(f"📝 Found {len(prompts)} prompts to test with")
    
    # Create traces and costs over the last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    trace_id = 1
    session_ids = [f"session_{i}" for i in range(1, 11)]
    
    for day in range(30):
        current_date = start_date + timedelta(days=day)
        
        # Create 5-15 traces per day
        daily_traces = random.randint(5, 15)
        
        for _ in range(daily_traces):
            prompt = random.choice(prompts)
            session_id = random.choice(session_ids)
            
            # Create trace
            trace = Trace(
                id=trace_id,
                name=f"Test Trace {trace_id}",
                prompt_id=prompt.id,
                prompt_name=prompt.name,
                session_id=session_id,
                status=random.choices(['success', 'error'], weights=[0.85, 0.15])[0],
                response_time=random.uniform(100, 5000),
                token_count=random.randint(50, 2000),
                created_at=current_date + timedelta(hours=random.randint(0, 23), 
                                                  minutes=random.randint(0, 59))
            )
            db.session.add(trace)
            
            # Create cost record
            cost = Cost(
                trace_id=trace_id,
                amount=random.uniform(0.001, 0.05),
                currency='USD',
                created_at=trace.created_at
            )
            db.session.add(cost)
            
            trace_id += 1
    
    db.session.commit()
    print(f"✅ Created {trace_id - 1} traces and cost records")
    return True

def test_prompt_performance():
    """Test prompt performance analysis."""
    print("\n📊 Testing Prompt Performance Analysis")
    print("=" * 50)
    
    evaluator = PromptEvaluator()
    prompts = Prompt.query.all()
    
    for prompt in prompts[:3]:  # Test first 3 prompts
        try:
            metrics = evaluator.get_prompt_performance(prompt.id, days=30)
            print(f"\n📈 {prompt.name} (v{prompt.version}):")
            print(f"   Total Calls: {metrics.total_calls}")
            print(f"   Success Rate: {metrics.success_rate:.1f}%")
            print(f"   Avg Response Time: {metrics.avg_response_time:.2f}ms")
            print(f"   Total Cost: ${metrics.total_cost:.4f}")
            print(f"   Avg Tokens: {metrics.avg_tokens_used}")
            print(f"   Error Count: {metrics.error_count}")
        except Exception as e:
            print(f"❌ Error testing {prompt.name}: {e}")

def test_ab_testing():
    """Test A/B testing functionality."""
    print("\n🔬 Testing A/B Testing")
    print("=" * 50)
    
    evaluator = PromptEvaluator()
    prompts = Prompt.query.all()
    
    if len(prompts) < 2:
        print("❌ Need at least 2 prompts for A/B testing")
        return
    
    try:
        result = evaluator.compare_prompts(prompts[0].id, prompts[1].id, days=30)
        print(f"\n📊 A/B Test Results:")
        print(f"   Prompt A: {result.prompt_a}")
        print(f"   Prompt B: {result.prompt_b}")
        print(f"   Winner: {result.winner}")
        print(f"   Confidence Level: {result.confidence_level:.1f}%")
        print(f"   Improvement: {result.improvement_percentage:.1f}%")
        
        print(f"\n📈 Detailed Metrics:")
        print(f"   A - Calls: {result.prompt_a_metrics.total_calls}, Success: {result.prompt_a_metrics.success_rate:.1f}%, Cost: ${result.prompt_a_metrics.total_cost:.4f}")
        print(f"   B - Calls: {result.prompt_b_metrics.total_calls}, Success: {result.prompt_b_metrics.success_rate:.1f}%, Cost: ${result.prompt_b_metrics.total_cost:.4f}")
        
    except Exception as e:
        print(f"❌ Error in A/B testing: {e}")

def test_cost_optimization():
    """Test cost optimization recommendations."""
    print("\n💰 Testing Cost Optimization")
    print("=" * 50)
    
    evaluator = PromptEvaluator()
    prompts = Prompt.query.all()
    
    for prompt in prompts[:2]:  # Test first 2 prompts
        try:
            recommendations = evaluator.get_cost_optimization_recommendations(prompt.id)
            print(f"\n💡 Recommendations for {prompt.name}:")
            
            if recommendations:
                for rec in recommendations:
                    print(f"   🎯 {rec['title']} ({rec['priority']})")
                    print(f"      {rec['description']}")
                    print(f"      Potential Savings: {rec['potential_savings']}")
            else:
                print("   ✅ No optimization recommendations - prompt is performing well!")
                
        except Exception as e:
            print(f"❌ Error getting recommendations for {prompt.name}: {e}")

def test_session_analysis():
    """Test session analysis."""
    print("\n🔄 Testing Session Analysis")
    print("=" * 50)
    
    evaluator = PromptEvaluator()
    
    # Get a session that has multiple traces
    session_counts = db.session.query(Trace.session_id, db.func.count(Trace.id)).group_by(Trace.session_id).all()
    
    if not session_counts:
        print("❌ No sessions found with multiple traces")
        return
    
    # Find a session with multiple traces
    multi_trace_session = None
    for session_id, count in session_counts:
        if count > 1:
            multi_trace_session = session_id
            break
    
    if not multi_trace_session:
        print("❌ No sessions with multiple traces found")
        return
    
    try:
        analysis = evaluator.get_session_analysis(multi_trace_session)
        print(f"\n📊 Session Analysis for {multi_trace_session}:")
        print(f"   Total Interactions: {analysis['total_interactions']}")
        print(f"   Success Rate: {analysis['success_rate']:.1f}%")
        print(f"   Total Cost: ${analysis['total_cost']:.4f}")
        print(f"   Total Tokens: {analysis['total_tokens']}")
        print(f"   Avg Response Time: {analysis['avg_response_time']:.2f}ms")
        print(f"   Session Duration: {analysis['session_duration']:.1f}s")
        
        print(f"\n🔄 Session Flow:")
        for i, interaction in enumerate(analysis['flow'][:5]):  # Show first 5 interactions
            print(f"   {i+1}. {interaction['prompt_name']} - {interaction['status']} - {interaction['response_time']:.2f}ms - ${interaction['cost']:.4f}")
        
    except Exception as e:
        print(f"❌ Error in session analysis: {e}")

def test_evaluation_report():
    """Test comprehensive evaluation report."""
    print("\n📋 Testing Evaluation Report")
    print("=" * 50)
    
    evaluator = PromptEvaluator()
    prompts = Prompt.query.all()
    
    if not prompts:
        print("❌ No prompts found for evaluation report")
        return
    
    try:
        prompt_ids = [p.id for p in prompts[:3]]  # Test with first 3 prompts
        report = evaluator.generate_evaluation_report(prompt_ids, days=30)
        
        print(f"\n📊 Evaluation Report Summary:")
        print(f"   Prompts Analyzed: {report['prompts_analyzed']}")
        print(f"   Total Calls: {report['summary']['total_calls']}")
        print(f"   Overall Success Rate: {report['summary']['overall_success_rate']:.1f}%")
        print(f"   Total Cost: ${report['summary']['total_cost']:.4f}")
        print(f"   Avg Cost per Call: ${report['summary']['avg_cost_per_call']:.4f}")
        
        print(f"\n📈 Cost Analysis:")
        print(f"   Daily Average: ${report['cost_analysis']['daily_average']:.4f}")
        print(f"   Cost Trend: {report['cost_analysis']['cost_trend']}")
        print(f"   Optimization Potential: {report['cost_analysis']['optimization_potential']} high-priority items")
        
        print(f"\n📝 Detailed Metrics:")
        for metric in report['detailed_metrics']:
            print(f"   {metric['prompt_name']}: {metric['total_calls']} calls, {metric['success_rate']:.1f}% success, ${metric['total_cost']:.4f} cost")
        
        print(f"\n💡 Recommendations: {len(report['recommendations'])} total")
        for rec in report['recommendations'][:3]:  # Show first 3
            print(f"   - {rec['title']} ({rec['priority']})")
        
    except Exception as e:
        print(f"❌ Error generating evaluation report: {e}")

def test_prompt_history():
    """Test prompt version history."""
    print("\n📚 Testing Prompt Version History")
    print("=" * 50)
    
    evaluator = PromptEvaluator()
    prompts = Prompt.query.all()
    
    if not prompts:
        print("❌ No prompts found for version history")
        return
    
    # Test with first prompt
    prompt = prompts[0]
    try:
        history = evaluator.get_prompt_version_history(prompt.name)
        print(f"\n📚 Version History for {prompt.name}:")
        
        if history:
            for version in history:
                print(f"   v{version['version']} ({version['created_at'][:10]}):")
                print(f"      Preview: {version['content_preview']}")
                print(f"      Performance: {version['performance']['total_calls']} calls, {version['performance']['success_rate']:.1f}% success")
        else:
            print("   No version history found")
            
    except Exception as e:
        print(f"❌ Error getting version history: {e}")

def main():
    """Run all advanced evaluation tests."""
    print("🚀 Advanced Prompt Evaluation Test Suite")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # Create test data
        if not create_test_data():
            return
        
        # Run all tests
        test_prompt_performance()
        test_ab_testing()
        test_cost_optimization()
        test_session_analysis()
        test_evaluation_report()
        test_prompt_history()
        
        print("\n✅ All advanced evaluation tests completed!")
        print("\n🎯 Next Steps:")
        print("   1. Visit http://localhost:8080/dashboard/advanced-evaluation")
        print("   2. Test the A/B testing interface")
        print("   3. Check cost optimization recommendations")
        print("   4. Analyze session patterns")
        print("   5. Generate comprehensive reports")

if __name__ == "__main__":
    main() 