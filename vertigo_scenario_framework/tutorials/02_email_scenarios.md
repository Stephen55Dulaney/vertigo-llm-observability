# Tutorial 02: Email Command Testing - Deep Dive

**Master Professional Email Agent Testing**

Now that you understand the basics, let's dive deep into comprehensive email command testing. This tutorial will show you how to create robust test suites for your Vertigo email processing system.

## What You'll Learn

- **Advanced email testing scenarios** including edge cases
- **Performance testing** under realistic conditions  
- **Error handling evaluation** for production readiness
- **Business impact measurement** for email automation
- **Integration testing** with Firestore and external services

## Prerequisites

- Completed Tutorial 01 successfully
- Hello World scenario running without errors
- Understanding of your email command parser functionality
- Access to Firestore (for full integration tests)

## Part 1: Understanding Your Email System

### Your Current Email Commands

Let's start by documenting what your system currently supports:

```bash
# Test each command individually to understand current behavior
cd /Users/stephendulaney/Documents/Vertigo
python -c "
from email_command_parser import EmailCommandParser
parser = EmailCommandParser()

commands = [
    'Vertigo: Help',
    'Vertigo: Total stats',
    'Vertigo: List this week', 
    'Vertigo: List projects',
    'Vertigo: Prompt report'
]

print('=== CURRENT COMMAND ANALYSIS ===')
for cmd in commands:
    result = parser.parse_command(cmd)
    print(f'\\nCommand: {cmd}')
    print(f'Detected: {result.get(\"command\") if result else \"None\"}')
    print(f'Has Response: {bool(result)}')
    if result and 'body' in result:
        print(f'Response Length: {len(result[\"body\"])} chars')
"
```

**Document your results:**
- Which commands work consistently?
- Which commands access Firestore?
- What are the typical response times?
- Any commands that fail or behave unexpectedly?

### Understanding Email Processing Flow

Your email system follows this flow:

1. **Subject Parsing**: Extracts command from email subject
2. **Command Detection**: Identifies the specific command type
3. **Data Retrieval**: Fetches relevant data from Firestore (if needed)
4. **Response Generation**: Creates formatted response
5. **Error Handling**: Manages failures gracefully

## Part 2: Comprehensive Email Testing

### Test Scenario Categories

We'll test five key categories:

1. **Basic Functionality**: Core commands work correctly
2. **Email Format Handling**: Replies, forwards, case variations
3. **Error Scenarios**: Invalid commands, edge cases
4. **Performance Testing**: Speed and reliability under load
5. **Business Context**: Real-world usage patterns

### Hands-On Exercise 1: Running the Email Test Suite

Let's run a comprehensive test suite:

```bash
cd vertigo_scenario_framework
python -c "
import asyncio
from adapters.email_processor_adapter import EmailProcessorAdapter

async def run_comprehensive_test():
    print('🚀 Starting Comprehensive Email Test Suite...')
    adapter = EmailProcessorAdapter()
    
    # Run the full test suite
    results = await adapter.run_comprehensive_test()
    
    print(f'\\n📊 OVERALL RESULTS:')
    print(f'Total Scenarios: {results[\"total_scenarios\"]}')
    print(f'Successful: {results[\"successful_scenarios\"]}')
    print(f'Success Rate: {results[\"success_rate\"]:.1%}')
    print(f'Avg Response Time: {results[\"average_response_time\"]:.3f}s')
    print(f'System Health: {results[\"summary\"][\"overall_health\"]}')
    
    # Show failed tests
    failed_tests = [r for r in results[\"results\"] if not r.get(\"success\", False)]
    if failed_tests:
        print(f'\\n❌ FAILED TESTS ({len(failed_tests)}):')
        for test in failed_tests:
            print(f'  • {test.get(\"scenario_name\", \"Unknown\")}')
    
    return results

# Run the test
results = asyncio.run(run_comprehensive_test())
"
```

**What to look for:**
- **Success rate above 90%**: Good system health
- **Response times under 1 second**: Acceptable performance
- **Failed test patterns**: Common failure modes to address

### Interpreting Results

**Example Output Analysis:**

```
📊 OVERALL RESULTS:
Total Scenarios: 11
Successful: 10
Success Rate: 90.9%
Avg Response Time: 0.234s
System Health: good

❌ FAILED TESTS (1):
  • Full Weekly Report Processing
```

**This tells us:**
- Overall system is healthy (90%+ success rate)
- Performance is good (< 1 second average)
- One integration test failed (likely Firestore connectivity)

## Part 3: Custom Business Scenarios

### Creating Your Own Test Scenarios

Let's create tests that match your actual business needs:

```python
# Save this as: custom_email_scenarios.py
import asyncio
from vertigo_scenario_framework.adapters.email_processor_adapter import EmailProcessorAdapter

class CustomEmailScenarios:
    """Custom business scenarios for Stephen's Vertigo system."""
    
    def __init__(self):
        self.adapter = EmailProcessorAdapter()
    
    def get_business_scenarios(self):
        """Define realistic business scenarios."""
        return [
            {
                "name": "CEO Weekly Request",
                "description": "CEO requests weekly summary for board meeting",
                "subject": "Vertigo: List this week",
                "body": "Stephen, need the weekly transcript summary for today's board meeting. Thanks!",
                "test_type": "full_processing",
                "business_impact": "high",
                "user_persona": "Executive",
                "expected_elements": ["transcripts", "meetings", "success rate"]
            },
            {
                "name": "Team Lead Stats Request", 
                "description": "Team lead needs project statistics",
                "subject": "Re: Vertigo: Total stats",
                "body": "Following up on the project stats request from yesterday.",
                "test_type": "full_processing",
                "business_impact": "medium",
                "user_persona": "Manager",
                "expected_elements": ["all-time", "projects", "total"]
            },
            {
                "name": "New User Help Request",
                "description": "New team member needs help with commands",
                "subject": "Vertigo: Help",
                "body": "I'm new to the team. Can you show me what commands are available?",
                "test_type": "command_detection",
                "business_impact": "medium", 
                "user_persona": "New User",
                "expected_elements": ["available commands", "usage", "examples"]
            },
            {
                "name": "Project Manager Dashboard",
                "description": "PM wants project breakdown for planning",
                "subject": "Vertigo: List projects",
                "body": "Need project breakdown for resource planning next week.",
                "test_type": "full_processing",
                "business_impact": "high",
                "user_persona": "Project Manager",
                "expected_elements": ["projects", "transcripts", "meetings"]
            }
        ]
    
    async def run_business_scenario_test(self):
        """Run all business scenarios and provide analysis."""
        scenarios = self.get_business_scenarios()
        results = []
        
        print("🏢 Running Business Scenario Tests...")
        print("=" * 50)
        
        for scenario in scenarios:
            print(f"\\n📧 Testing: {scenario['name']}")
            print(f"👤 User: {scenario['user_persona']}")
            print(f"📈 Impact: {scenario['business_impact']}")
            
            # Run the test
            test_data = {
                'subject': scenario['subject'],
                'body': scenario['body'],
                'test_type': scenario['test_type']
            }
            
            result = await self.adapter.execute_with_metrics(test_data)
            result['scenario_info'] = scenario
            results.append(result)
            
            # Quick analysis
            if result.get('success'):
                print(f"✅ PASSED ({result['performance']['processing_time']:.3f}s)")
                
                # Check for expected elements
                if result.get('result', {}).get('body'):
                    response_body = result['result']['body'].lower()
                    found_elements = [elem for elem in scenario['expected_elements'] 
                                    if elem in response_body]
                    print(f"📝 Found elements: {found_elements}")
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
        
        # Business analysis
        self._analyze_business_results(results)
        return results
    
    def _analyze_business_results(self, results):
        """Analyze results from a business perspective."""
        print("\\n" + "=" * 50)
        print("📊 BUSINESS IMPACT ANALYSIS")
        print("=" * 50)
        
        # Group by business impact
        by_impact = {}
        for result in results:
            impact = result['scenario_info']['business_impact']
            if impact not in by_impact:
                by_impact[impact] = []
            by_impact[impact].append(result)
        
        # Analyze each impact level
        for impact_level in ['high', 'medium', 'low']:
            if impact_level not in by_impact:
                continue
                
            scenarios = by_impact[impact_level]
            successful = sum(1 for s in scenarios if s.get('success'))
            total = len(scenarios)
            success_rate = successful / total if total > 0 else 0
            
            avg_time = sum(s['performance']['processing_time'] for s in scenarios) / total
            
            print(f"\\n{impact_level.upper()} IMPACT SCENARIOS:")
            print(f"  Success Rate: {success_rate:.1%} ({successful}/{total})")
            print(f"  Avg Response Time: {avg_time:.3f}s")
            
            if success_rate < 0.95:
                print(f"  ⚠️  CONCERN: {impact_level} impact scenarios below 95% success rate")
        
        # Overall business readiness
        total_success = sum(1 for r in results if r.get('success'))
        total_tests = len(results)
        overall_rate = total_success / total_tests if total_tests > 0 else 0
        
        print(f"\\n🎯 BUSINESS READINESS ASSESSMENT:")
        if overall_rate >= 0.95:
            print("✅ READY FOR PRODUCTION - High reliability demonstrated")
        elif overall_rate >= 0.85:
            print("⚠️  NEEDS IMPROVEMENT - Some reliability concerns")
        else:
            print("❌ NOT READY - Significant reliability issues")

# Usage
async def main():
    scenarios = CustomEmailScenarios()
    await scenarios.run_business_scenario_test()

if __name__ == "__main__":
    asyncio.run(main())
```

### Running Your Custom Scenarios

```bash
cd vertigo_scenario_framework
python custom_email_scenarios.py
```

**Expected Output:**
```
🏢 Running Business Scenario Tests...
==================================================

📧 Testing: CEO Weekly Request
👤 User: Executive
📈 Impact: high
✅ PASSED (0.156s)
📝 Found elements: ['transcripts', 'meetings']

📧 Testing: Team Lead Stats Request
👤 User: Manager
📈 Impact: medium
✅ PASSED (0.203s)
📝 Found elements: ['all-time', 'total']

...

📊 BUSINESS IMPACT ANALYSIS
==================================================

HIGH IMPACT SCENARIOS:
  Success Rate: 100.0% (2/2)
  Avg Response Time: 0.179s

🎯 BUSINESS READINESS ASSESSMENT:
✅ READY FOR PRODUCTION - High reliability demonstrated
```

## Part 4: Performance and Load Testing

### Testing Under Realistic Load

Let's test how your email system performs under load:

```bash
cd vertigo_scenario_framework
python -c "
import asyncio
import time
from adapters.email_processor_adapter import EmailProcessorAdapter

async def load_test():
    print('⚡ Starting Email System Load Test...')
    adapter = EmailProcessorAdapter()
    
    # Test concurrent processing
    test_scenarios = [
        {'subject': 'Vertigo: Help', 'test_type': 'command_detection'},
        {'subject': 'Vertigo: Total stats', 'test_type': 'command_detection'}, 
        {'subject': 'Vertigo: List this week', 'test_type': 'command_detection'},
        {'subject': 'Re: Vertigo: Help', 'test_type': 'command_detection'},
    ]
    
    # Run performance test
    performance_test = {
        'subject': 'Vertigo: Help',
        'test_type': 'performance',
        'iterations': 20
    }
    
    start_time = time.time()
    result = await adapter.execute_with_metrics(performance_test)
    total_time = time.time() - start_time
    
    print(f'\\n📈 PERFORMANCE RESULTS:')
    perf = result['performance']
    print(f'Total Iterations: {perf[\"total_iterations\"]}')
    print(f'Success Rate: {perf[\"success_rate\"]:.1%}')
    print(f'Avg Response Time: {perf[\"avg_response_time\"]:.3f}s')
    print(f'Min Response Time: {perf[\"min_response_time\"]:.3f}s')
    print(f'Max Response Time: {perf[\"max_response_time\"]:.3f}s')
    print(f'Total Test Time: {total_time:.2f}s')
    
    # Analysis
    analysis = result['analysis']
    print(f'\\n🔍 ANALYSIS:')
    print(f'Performance Acceptable: {analysis[\"performance_acceptable\"]}')
    print(f'Consistent Performance: {analysis[\"consistency\"]}')
    print(f'High Reliability: {analysis[\"reliability\"]}')

asyncio.run(load_test())
"
```

**Performance Benchmarks:**
- **Excellent**: < 0.1s average response time
- **Good**: < 0.5s average response time  
- **Acceptable**: < 1.0s average response time
- **Poor**: > 1.0s average response time

## Part 5: Error Handling and Edge Cases

### Testing Error Scenarios

It's crucial to test how your system handles errors:

```bash
cd vertigo_scenario_framework
python -c "
import asyncio
from adapters.email_processor_adapter import EmailProcessorAdapter

async def error_handling_test():
    print('🚨 Testing Error Handling and Edge Cases...')
    adapter = EmailProcessorAdapter()
    
    error_scenarios = [
        {
            'name': 'Invalid Command',
            'subject': 'Vertigo: DoSomethingRandom',
            'test_type': 'error_handling'
        },
        {
            'name': 'Empty Subject',
            'subject': '',
            'test_type': 'error_handling'
        },
        {
            'name': 'Non-Vertigo Email',
            'subject': 'Meeting tomorrow at 3pm',
            'test_type': 'error_handling'
        },
        {
            'name': 'Malformed Command',
            'subject': 'Vertigo: Help Me Please With Everything',
            'test_type': 'error_handling'
        },
        {
            'name': 'Special Characters',
            'subject': 'Vertigo: Help ñáéíóú',
            'test_type': 'error_handling'
        }
    ]
    
    print(f'Testing {len(error_scenarios)} error scenarios...')
    
    for scenario in error_scenarios:
        print(f'\\n🔧 {scenario[\"name\"]}')
        result = await adapter.execute_with_metrics(scenario)
        
        if result.get('success'):
            print('✅ Graceful handling')
            if 'analysis' in result:
                analysis = result['analysis']
                print(f'   Error Type: {analysis.get(\"error_handling_type\", \"unknown\")}')
        else:
            print('❌ Poor error handling')
            print(f'   Error: {result.get(\"error\", \"Unknown\")}')

asyncio.run(error_handling_test())
"
```

**Good Error Handling Should:**
- Not crash or throw unhandled exceptions
- Provide helpful error messages
- Suggest alternative actions
- Log errors for debugging
- Maintain consistent response format

## Part 6: Integration Testing

### Testing Firestore Integration

Test the full email processing pipeline including database operations:

```bash
cd vertigo_scenario_framework
python -c "
import asyncio
from adapters.email_processor_adapter import EmailProcessorAdapter

async def integration_test():
    print('🔗 Testing Firestore Integration...')
    adapter = EmailProcessorAdapter()
    
    # Test commands that require Firestore
    firestore_commands = [
        {
            'name': 'Weekly Stats with Firestore',
            'subject': 'Vertigo: List this week',
            'test_type': 'full_processing'
        },
        {
            'name': 'Total Stats with Firestore', 
            'subject': 'Vertigo: Total stats',
            'test_type': 'full_processing'
        },
        {
            'name': 'Projects List with Firestore',
            'subject': 'Vertigo: List projects', 
            'test_type': 'full_processing'
        }
    ]
    
    firestore_working = 0
    firestore_errors = 0
    
    for test in firestore_commands:
        print(f'\\n📊 {test[\"name\"]}')
        result = await adapter.execute_with_metrics(test)
        
        if result.get('success'):
            analysis = result.get('analysis', {})
            if analysis.get('firestore_accessed'):
                print('✅ Firestore integration working')
                firestore_working += 1
                
                quality = analysis.get('response_quality', 'unknown')
                print(f'   Data Quality: {quality}')
            else:
                print('⚠️  Command worked but no Firestore access detected')
        else:
            print('❌ Integration test failed')
            print(f'   Error: {result.get(\"error\", \"Unknown\")}')
            firestore_errors += 1
    
    print(f'\\n🔗 INTEGRATION SUMMARY:')
    print(f'Working: {firestore_working}')
    print(f'Errors: {firestore_errors}')
    
    if firestore_errors == 0:
        print('✅ All integrations working correctly')
    else:
        print('⚠️  Some integration issues detected - check Firestore connectivity')

asyncio.run(integration_test())
"
```

## Part 7: Continuous Monitoring Setup

### Creating a Monitoring Dashboard

Set up ongoing monitoring for your email system:

```python
# Save as: email_monitoring.py
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from adapters.email_processor_adapter import EmailProcessorAdapter

class EmailSystemMonitor:
    """Continuous monitoring for email system health."""
    
    def __init__(self):
        self.adapter = EmailProcessorAdapter()
        self.results_dir = Path("monitoring_results")
        self.results_dir.mkdir(exist_ok=True)
    
    async def run_health_check(self):
        """Run a comprehensive health check."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"🏥 Email System Health Check - {timestamp}")
        print("=" * 50)
        
        # Quick functionality test
        basic_tests = [
            {'subject': 'Vertigo: Help', 'test_type': 'command_detection'},
            {'subject': 'Vertigo: Total stats', 'test_type': 'full_processing'},
        ]
        
        results = {
            'timestamp': timestamp,
            'tests': [],
            'summary': {}
        }
        
        for test in basic_tests:
            result = await self.adapter.execute_with_metrics(test)
            results['tests'].append(result)
            
            status = "✅" if result.get('success') else "❌"
            time_ms = result['performance']['processing_time'] * 1000
            print(f"{status} {test['subject']} ({time_ms:.1f}ms)")
        
        # Calculate summary metrics
        successful = sum(1 for t in results['tests'] if t.get('success'))
        total = len(results['tests'])
        avg_time = sum(t['performance']['processing_time'] for t in results['tests']) / total
        
        results['summary'] = {
            'success_rate': successful / total,
            'avg_response_time': avg_time,
            'system_health': 'healthy' if successful == total else 'degraded'
        }
        
        print(f"\\n📊 Health Summary:")
        print(f"Success Rate: {results['summary']['success_rate']:.1%}")
        print(f"Avg Response: {results['summary']['avg_response_time']:.3f}s") 
        print(f"System Status: {results['summary']['system_health']}")
        
        # Save results
        results_file = self.results_dir / f"health_check_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results

# Usage
async def main():
    monitor = EmailSystemMonitor()
    await monitor.run_health_check()

if __name__ == "__main__":
    asyncio.run(main())
```

## Summary and Best Practices

### What You've Learned

✅ **Comprehensive email testing** across multiple dimensions  
✅ **Performance testing** under realistic conditions  
✅ **Error handling evaluation** for production readiness  
✅ **Business scenario creation** for real-world validation  
✅ **Integration testing** with external services  
✅ **Monitoring setup** for ongoing health checks  

### Email Testing Best Practices

1. **Test Realistic Scenarios**: Use actual business use cases
2. **Include Performance Metrics**: Monitor response times consistently
3. **Test Error Conditions**: Ensure graceful failure handling
4. **Monitor Integration Points**: Verify Firestore and external service connectivity
5. **Business Impact Focus**: Prioritize tests based on business value
6. **Continuous Monitoring**: Set up ongoing health checks

### Production Readiness Checklist

- [ ] **95%+ success rate** on business scenarios
- [ ] **< 1 second response time** for basic commands
- [ ] **Graceful error handling** for invalid inputs
- [ ] **Firestore integration** working reliably
- [ ] **Load testing** completed successfully
- [ ] **Monitoring system** in place

### Next Steps

1. **Fix any failing tests** identified in this tutorial
2. **Set up continuous monitoring** using the provided scripts
3. **Integrate tests into CI/CD** for automated validation
4. **Continue to Tutorial 03** for meeting transcript analysis
5. **Document your test scenarios** for team use

### Troubleshooting Common Issues

**Firestore Connection Errors:**
- Verify service account credentials are set up
- Check network connectivity to Google Cloud
- Ensure Firestore security rules allow access

**Performance Issues:**
- Check if running in debug mode (slower performance)
- Monitor system resources during tests
- Consider connection pooling for high-load scenarios

**Test Failures:**
- Review error messages carefully
- Check if recent code changes affected functionality
- Verify test expectations match current system behavior

Ready for advanced techniques? Continue with **[Tutorial 03: Meeting Analysis Testing](03_meeting_evaluation.md)** to learn about evaluating LLM-generated meeting summaries.