#!/usr/bin/env python3
"""
Hello World Scenario - Your First Vertigo Agent Test
====================================================

This is your first hands-on introduction to testing Vertigo agents with the Scenario framework.
Run this script to see immediate results and understand how agent testing works.

Author: Claude Code
Date: 2025-08-06

USAGE:
    cd /Users/stephendulaney/Documents/Vertigo/vertigo_scenario_framework
    python examples/hello_world_scenario.py

This will:
1. Test your email command parser
2. Show you real results
3. Explain what happened
4. Guide you to next steps
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Add the parent directories to path so we can import Vertigo components
vertigo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(vertigo_root))
sys.path.insert(0, str(Path(__file__).parent.parent))

class HelloWorldScenario:
    """Your first agent testing scenario - simple but powerful!"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        
        print("👋 Welcome to Vertigo Agent Testing!")
        print("=" * 50)
        print("This Hello World scenario will show you:")
        print("• How to test your email command parser")
        print("• What good test results look like")  
        print("• How to interpret the results")
        print("• Next steps for advanced testing")
        print()
        
    def run_scenario(self):
        """Run the complete Hello World scenario."""
        try:
            print("🚀 Starting Hello World Scenario...")
            
            self.test_email_commands()
            self.analyze_results()
            self.show_summary()
            self.suggest_next_steps()
            
        except Exception as e:
            print(f"❌ Scenario failed: {e}")
            self.show_troubleshooting()
    
    def test_email_commands(self):
        """Test basic email command parsing - your first agent test!"""
        print("\n🧪 Testing Email Command Parser...")
        print("This tests the agent that processes your Vertigo email commands.")
        
        try:
            from email_command_parser import EmailCommandParser
            parser = EmailCommandParser()
            
            # Define our test cases - these are like "scenarios" for testing
            test_cases = [
                {
                    "name": "Basic Help Command",
                    "description": "Tests if the agent understands a simple help request",
                    "input": "Vertigo: Help",
                    "expected_command": "help",
                    "should_succeed": True
                },
                {
                    "name": "Stats Request",
                    "description": "Tests if the agent can handle stats requests", 
                    "input": "Vertigo: Total stats",
                    "expected_command": "total stats",
                    "should_succeed": True
                },
                {
                    "name": "Weekly Report",
                    "description": "Tests weekly reporting functionality",
                    "input": "Vertigo: List this week", 
                    "expected_command": "list this week",
                    "should_succeed": True
                },
                {
                    "name": "Reply Handling",
                    "description": "Tests if agent handles email replies correctly",
                    "input": "Re: Vertigo: Help",
                    "expected_command": "help", 
                    "should_succeed": True
                },
                {
                    "name": "Unknown Command",
                    "description": "Tests how agent handles unknown commands",
                    "input": "Vertigo: Do something random",
                    "expected_command": None,
                    "should_succeed": False
                }
            ]
            
            # Run each test case
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n  Test {i}: {test_case['name']}")
                print(f"  📝 {test_case['description']}")
                print(f"  📨 Input: '{test_case['input']}'")
                
                start_time = time.time()
                result = parser.parse_command(test_case['input'])
                response_time = time.time() - start_time
                
                # Analyze the result
                test_result = {
                    "test_name": test_case['name'],
                    "input": test_case['input'],
                    "expected_command": test_case['expected_command'],
                    "actual_result": result,
                    "response_time": response_time,
                    "should_succeed": test_case['should_succeed']
                }
                
                # Check if test passed
                if test_case['should_succeed']:
                    if result and result.get('command') == test_case['expected_command']:
                        test_result['status'] = 'PASSED'
                        print(f"  ✅ PASSED - Agent correctly identified '{result['command']}' command")
                    else:
                        test_result['status'] = 'FAILED'
                        print(f"  ❌ FAILED - Expected '{test_case['expected_command']}', got: {result}")
                else:
                    if not result:
                        test_result['status'] = 'PASSED'
                        print(f"  ✅ PASSED - Agent correctly ignored unknown command")
                    else:
                        test_result['status'] = 'FAILED' 
                        print(f"  ❌ FAILED - Agent should have ignored this command")
                
                print(f"  ⏱️  Response time: {response_time:.3f}s")
                
                self.results.append(test_result)
                
        except ImportError as e:
            print(f"❌ Cannot import email parser: {e}")
            print("Make sure you're running this from the Vertigo directory!")
        except Exception as e:
            print(f"❌ Error testing email commands: {e}")
    
    def analyze_results(self):
        """Analyze test results - this is where you learn about your agent's performance."""
        print("\n📊 Analyzing Results...")
        print("This is where we examine how well your agent performed.")
        
        if not self.results:
            print("❌ No results to analyze")
            return
        
        # Calculate metrics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['status'] == 'PASSED')
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        avg_response_time = sum(r['response_time'] for r in self.results) / total_tests
        
        print(f"\n📈 Performance Metrics:")
        print(f"  • Total Tests: {total_tests}")
        print(f"  • Passed: {passed_tests}")
        print(f"  • Failed: {failed_tests}")
        print(f"  • Success Rate: {success_rate:.1f}%")
        print(f"  • Average Response Time: {avg_response_time:.3f}s")
        
        # Detailed analysis
        print(f"\n🔍 Detailed Analysis:")
        for result in self.results:
            status_emoji = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"  {status_emoji} {result['test_name']}: {result['status']}")
            
            if result['status'] == 'FAILED':
                print(f"    Expected: {result['expected_command']}")
                print(f"    Got: {result['actual_result']}")
    
    def show_summary(self):
        """Show a summary of what we learned."""
        print(f"\n🎯 Summary - What We Learned:")
        print("=" * 40)
        
        total_time = time.time() - self.start_time
        passed_tests = sum(1 for r in self.results if r['status'] == 'PASSED')
        total_tests = len(self.results)
        
        if passed_tests == total_tests:
            print("🌟 EXCELLENT! Your email command parser is working perfectly!")
            print("   • All commands were correctly identified")
            print("   • Response times are good")
            print("   • Error handling works properly")
        elif passed_tests >= total_tests * 0.8:
            print("👍 GOOD! Your email parser works well with some minor issues.")
            print("   • Most commands work correctly")
            print("   • A few edge cases need attention")
        else:
            print("🔧 NEEDS WORK! Your email parser has some issues to fix.")
            print("   • Several commands are not working")
            print("   • May need configuration or debugging")
        
        print(f"\n📊 Key Takeaways:")
        print(f"   • You tested {total_tests} different scenarios")
        print(f"   • {passed_tests} tests passed successfully")
        print(f"   • Total testing time: {total_time:.2f} seconds")
        print(f"   • Your agent can handle multiple command types")
        
        if self.results:
            fastest_test = min(self.results, key=lambda x: x['response_time'])
            print(f"   • Fastest response: {fastest_test['response_time']:.3f}s ({fastest_test['test_name']})")
    
    def suggest_next_steps(self):
        """Suggest what Stephen should do next."""
        print(f"\n🚀 Next Steps - Your Learning Journey:")
        print("=" * 45)
        
        print("Now that you've run your first agent test, here's what to do next:")
        print()
        print("1. 📚 LEARN MORE ABOUT TESTING:")
        print("   cd vertigo_scenario_framework/tutorials")
        print("   open 01_introduction.md")
        print()
        print("2. 🧪 TRY ADVANCED TESTING:")
        print("   python examples/production_evaluation_demo.py")
        print()
        print("3. 🏗️ BUILD CUSTOM SCENARIOS:")  
        print("   Look at scenarios/email_scenarios.py")
        print("   Create scenarios for your specific use cases")
        print()
        print("4. 📊 INTEGRATE WITH MONITORING:")
        print("   Connect your tests to Langfuse")
        print("   Set up continuous evaluation")
        print()
        print("5. 🎯 FOCUS ON BUSINESS VALUE:")
        print("   Define what 'good performance' means for your agents")
        print("   Create tests that measure business impact")
        
        # Specific recommendations based on results
        failed_tests = [r for r in self.results if r['status'] == 'FAILED']
        if failed_tests:
            print(f"\n🔧 IMMEDIATE FIXES NEEDED:")
            for test in failed_tests:
                print(f"   • Fix: {test['test_name']}")
    
    def show_troubleshooting(self):
        """Help Stephen troubleshoot common issues."""
        print(f"\n🛠️ Troubleshooting Guide:")
        print("=" * 30)
        print()
        print("If you're seeing errors, try these steps:")
        print()
        print("1. CHECK YOUR LOCATION:")
        print("   Make sure you're in: /Users/stephendulaney/Documents/Vertigo")
        print("   pwd  # Should show your current directory")
        print()
        print("2. RUN SETUP FIRST:")
        print("   python vertigo_scenario_framework/setup_scenario_framework.py")
        print()
        print("3. CHECK DEPENDENCIES:")
        print("   pip install -r scenario_requirements.txt")
        print()
        print("4. TEST BASIC COMPONENTS:")
        print("   python test_simple.py")
        print("   python test_command_detection.py")
        print()
        print("5. CHECK FIRESTORE CONNECTION:")
        print("   Your email parser needs Firestore to work fully")
        print("   Some tests may fail if Firestore isn't configured")
        print()
        print("6. GET HELP:")
        print("   Check the tutorials in vertigo_scenario_framework/tutorials/")
        print("   Look at the README files")

def main():
    """Run the Hello World scenario."""
    scenario = HelloWorldScenario()
    scenario.run_scenario()

if __name__ == "__main__":
    main()