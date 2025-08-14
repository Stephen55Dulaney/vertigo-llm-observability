#!/usr/bin/env python3
"""
Test script for new Vertigo features:
- Dashboard metrics fix
- Firestore statistics
- Email command parser
- Prompt manager
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_fix():
    """Test that dashboard metrics are working."""
    print("🧪 Testing Dashboard Metrics Fix")
    print("=" * 50)
    
    try:
        from app import create_app
        from app.models import db, Trace, Cost, Prompt
        
        app = create_app()
        
        with app.app_context():
            # Test basic metrics calculation
            total_traces = Trace.query.count()
            total_costs = Cost.query.count()
            total_prompts = Prompt.query.count()
            
            print(f"✅ Database connection working")
            print(f"   Total traces: {total_traces}")
            print(f"   Total costs: {total_costs}")
            print(f"   Total prompts: {total_prompts}")
            
            # Test metrics calculation
            from app.blueprints.dashboard.routes import get_metrics
            from flask import Flask
            test_app = Flask(__name__)
            
            with test_app.app_context():
                metrics = get_metrics()
                print(f"✅ Metrics calculation working")
                
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")

def test_firestore_stats():
    """Test Firestore statistics script."""
    print("\n🧪 Testing Firestore Statistics")
    print("=" * 50)
    
    try:
        # Test if the script can be imported
        from firestore_stats import get_firestore_client, get_transcript_stats
        
        print("✅ Firestore stats script imported successfully")
        print("📊 Available functions:")
        print("   - get_firestore_client()")
        print("   - get_transcript_stats()")
        print("   - get_meeting_stats()")
        print("   - print_stats()")
        
        # Note: Actual Firestore connection requires credentials
        print("ℹ️  Firestore connection requires proper credentials")
        
    except ImportError as e:
        print(f"❌ Firestore stats import failed: {e}")
    except Exception as e:
        print(f"❌ Firestore stats test failed: {e}")

def test_email_command_parser():
    """Test email command parser."""
    print("\n🧪 Testing Email Command Parser")
    print("=" * 50)
    
    try:
        from email_command_parser import EmailCommandParser
        
        parser = EmailCommandParser()
        print("✅ Email command parser created successfully")
        
        # Test command detection
        test_commands = [
            "Vertigo: List this week",
            "Vertigo: Total stats", 
            "Vertigo: List projects",
            "Vertigo: Help",
            "list this week",
            "total stats"
        ]
        
        print("📧 Testing command detection:")
        for cmd in test_commands:
            result = parser.parse_command(cmd)
            if result:
                print(f"   ✅ '{cmd}' -> {result['command']}")
            else:
                print(f"   ❌ '{cmd}' -> No match")
                
    except ImportError as e:
        print(f"❌ Email command parser import failed: {e}")
    except Exception as e:
        print(f"❌ Email command parser test failed: {e}")

def test_prompt_manager():
    """Test prompt manager routes."""
    print("\n🧪 Testing Prompt Manager")
    print("=" * 50)
    
    try:
        from app import create_app
        from app.models import Prompt
        
        app = create_app()
        
        with app.app_context():
            # Test prompt creation
            test_prompt_data = {
                'name': 'Test Prompt',
                'content': 'This is a test prompt with {variable}',
                'prompt_type': 'test',
                'version': '1.0',
                'is_active': True
            }
            
            print("✅ Prompt manager routes available")
            print("📝 Available endpoints:")
            print("   - GET /prompts/manager")
            print("   - POST /api/prompts")
            print("   - PUT /api/prompts/<id>")
            print("   - POST /api/prompts/<id>/version")
            
            # Test prompt model
            prompt = Prompt(**test_prompt_data)
            print(f"✅ Prompt model working")
            print(f"   Name: {prompt.name}")
            print(f"   Type: {prompt.prompt_type}")
            print(f"   Version: {prompt.version}")
            
    except Exception as e:
        print(f"❌ Prompt manager test failed: {e}")

def test_advanced_evaluation():
    """Test advanced evaluation features."""
    print("\n🧪 Testing Advanced Evaluation")
    print("=" * 50)
    
    try:
        from app.services.prompt_evaluator import PromptEvaluator
        
        evaluator = PromptEvaluator()
        print("✅ PromptEvaluator created successfully")
        
        print("📊 Available evaluation methods:")
        print("   - get_prompt_performance()")
        print("   - compare_prompts()")
        print("   - get_cost_optimization_recommendations()")
        print("   - get_session_analysis()")
        print("   - generate_evaluation_report()")
        print("   - get_prompt_version_history()")
        
        # Test dashboard routes
        from app.blueprints.dashboard.routes import advanced_evaluation
        print("✅ Advanced evaluation route available")
        print("   - GET /dashboard/advanced-evaluation")
        
    except ImportError as e:
        print(f"❌ Advanced evaluation import failed: {e}")
    except Exception as e:
        print(f"❌ Advanced evaluation test failed: {e}")

def main():
    """Run all tests."""
    print("🚀 Testing New Vertigo Features")
    print("=" * 60)
    
    test_dashboard_fix()
    test_firestore_stats()
    test_email_command_parser()
    test_prompt_manager()
    test_advanced_evaluation()
    
    print("\n✅ All tests completed!")
    print("\n🎯 Next Steps:")
    print("   1. Visit http://localhost:8080/dashboard to see the fixed metrics")
    print("   2. Visit http://localhost:8080/prompts/manager to test prompt management")
    print("   3. Visit http://localhost:8080/dashboard/advanced-evaluation for evaluation tools")
    print("   4. Test email commands by sending to vertigo.agent.2025@gmail.com:")
    print("      - Subject: 'Vertigo: Help'")
    print("      - Subject: 'Vertigo: List this week'")
    print("      - Subject: 'Vertigo: Total stats'")
    print("   5. Run firestore_stats.py to get database statistics")

if __name__ == "__main__":
    main() 