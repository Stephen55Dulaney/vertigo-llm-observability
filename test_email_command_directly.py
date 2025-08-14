#!/usr/bin/env python3
"""
Test email command processing directly without Firestore dependency.
This demonstrates the core evaluation concepts while we wait for permissions.
"""

import sys
import time
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

def test_email_command_parser():
    """Test the email command parser directly."""
    print("🧪 Testing Email Command Parser Directly")
    print("=" * 45)
    
    try:
        from email_command_parser import EmailCommandParser
        
        parser = EmailCommandParser()
        
        # Test scenarios that don't require Firestore
        test_cases = [
            {
                "name": "Help Command",
                "subject": "Vertigo: Help",
                "body": "",
                "expected_command": "help",
                "description": "Basic help request should be detected"
            },
            {
                "name": "Reply Help Command", 
                "subject": "Re: Vertigo: Help",
                "body": "",
                "expected_command": "help",
                "description": "Reply to help should still work"
            },
            {
                "name": "Unknown Command",
                "subject": "Vertigo: Do something random",
                "body": "",
                "expected_command": None,
                "description": "Unknown commands should be ignored"
            },
            {
                "name": "Non-Vertigo Email",
                "subject": "Regular meeting invitation",
                "body": "Let's meet tomorrow",
                "expected_command": None,
                "description": "Regular emails should not trigger commands"
            }
        ]
        
        results = []
        print(f"\n📧 Running {len(test_cases)} test scenarios...")
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n  Test {i}: {test['name']}")
            print(f"  📝 {test['description']}")
            print(f"  📨 Input: '{test['subject']}'")
            
            start_time = time.time()
            
            try:
                result = parser.parse_command(test['subject'], test['body'])
                response_time = time.time() - start_time
                
                detected_command = result.get('command')
                passed = detected_command == test['expected_command']
                
                if passed:
                    print(f"  ✅ PASSED - Detected: '{detected_command}'")
                else:
                    print(f"  ❌ FAILED - Expected: '{test['expected_command']}', Got: '{detected_command}'")
                
                print(f"  ⏱️  Response time: {response_time:.3f}s")
                
                results.append({
                    'test_name': test['name'],
                    'passed': passed,
                    'response_time': response_time,
                    'expected': test['expected_command'],
                    'actual': detected_command,
                    'result': result
                })
                
            except Exception as e:
                print(f"  ❌ ERROR - {e}")
                results.append({
                    'test_name': test['name'],
                    'passed': False,
                    'response_time': time.time() - start_time,
                    'error': str(e)
                })
        
        # Analyze results
        print(f"\n📊 Results Analysis")
        print("=" * 20)
        
        passed_tests = sum(1 for r in results if r['passed'])
        total_tests = len(results)
        success_rate = (passed_tests / total_tests) * 100
        avg_response_time = sum(r['response_time'] for r in results) / total_tests
        
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"⚡ Avg Response Time: {avg_response_time:.3f}s")
        
        # Grade the performance
        if success_rate >= 90:
            grade = "A+"
            status = "Excellent"
        elif success_rate >= 80:
            grade = "A"
            status = "Very Good"
        elif success_rate >= 70:
            grade = "B"
            status = "Good"
        elif success_rate >= 60:
            grade = "C"
            status = "Needs Improvement"
        else:
            grade = "F"
            status = "Requires Attention"
        
        print(f"\n🎯 Overall Grade: {grade} ({status})")
        
        # Professional insights
        print(f"\n💼 Professional Analysis:")
        print(f"=" * 25)
        
        if success_rate == 100:
            print("✅ Command detection is working perfectly!")
            print("✅ Ready for production use")
            print("✅ No critical issues found")
        else:
            print("⚠️  Some command detection issues found")
            failed_tests = [r for r in results if not r['passed']]
            for test in failed_tests:
                print(f"   • {test['test_name']}: Expected '{test.get('expected')}', got '{test.get('actual')}'")
        
        if avg_response_time < 0.1:
            print("⚡ Excellent response time performance")
        elif avg_response_time < 0.5:
            print("✅ Good response time performance") 
        else:
            print("⚠️  Response time could be improved")
        
        print(f"\n🚀 Next Steps:")
        print("• Once Firestore permissions are ready, test database-dependent commands")
        print("• Run full scenario testing with business contexts")
        print("• Set up production monitoring and alerting")
        
        return results
        
    except ImportError as e:
        print(f"❌ Could not import email_command_parser: {e}")
        print("💡 Make sure you're running from the Vertigo project root")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main testing function."""
    print("🎯 Vertigo Email Command Direct Testing")
    print("Professional LLM Agent Evaluation - Core Functions")
    print("=" * 55)
    
    results = test_email_command_parser()
    
    if results:
        print(f"\n✅ Core evaluation completed successfully!")
        print(f"📊 Results show your command detection system quality")
        print(f"🎓 This demonstrates professional agent testing methodology")
        
        # Save results for analysis
        import json
        results_file = f"direct_test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📋 Results saved to: {results_file}")
    else:
        print(f"\n⚠️  Testing encountered issues, but this is part of learning!")
        print(f"💡 Professional evaluation includes debugging and problem-solving")

if __name__ == "__main__":
    main()