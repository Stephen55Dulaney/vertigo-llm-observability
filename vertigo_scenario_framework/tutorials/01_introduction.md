# Tutorial 01: Introduction to Scenario-Based Agent Testing

**Welcome to Professional Agent Testing with Vertigo!**

This tutorial introduces you to testing your LLM agents using the Scenario framework. By the end, you'll understand the fundamentals of agent testing and be ready to create your own comprehensive test suites.

## What You'll Learn

- **Why agent testing matters** for production systems
- **How to think about agent reliability** and quality
- **Practical testing strategies** you can use immediately
- **How to measure and improve** agent performance
- **Integration with Langfuse** for observability

## Prerequisites

- Vertigo system already set up and running
- Basic understanding of your email command parser
- Python environment with required packages

## Getting Started

### Step 1: Verify Your Setup

First, make sure everything is properly configured:

```bash
# From your Vertigo root directory
cd vertigo_scenario_framework
python setup_scenario_framework.py
```

If you see any errors, follow the troubleshooting guide in the setup script.

### Step 2: Run Your First Test

Let's start with the Hello World scenario to verify everything works:

```bash
python examples/hello_world_scenario.py
```

**What should happen:**
- The script tests your email command parser
- You'll see real-time results for 5 different test cases
- Each test shows pass/fail status and response times
- You get a detailed analysis of your agent's performance

**Sample Output:**
```
👋 Welcome to Vertigo Agent Testing!
==================================================
🚀 Starting Hello World Scenario...

🧪 Testing Email Command Parser...
  Test 1: Basic Help Command
  📝 Tests if the agent understands a simple help request
  📨 Input: 'Vertigo: Help'
  ✅ PASSED - Agent correctly identified 'help' command
  ⏱️  Response time: 0.002s

...

📊 Analyzing Results...
📈 Performance Metrics:
  • Total Tests: 5
  • Passed: 5
  • Failed: 0
  • Success Rate: 100.0%
  • Average Response Time: 0.003s
```

## Understanding Agent Testing Concepts

### What Are We Testing?

When we test an AI agent, we're evaluating several dimensions:

1. **Functional Correctness**: Does it do what it's supposed to do?
2. **Reliability**: Does it work consistently across different inputs?
3. **Performance**: How fast does it respond?
4. **Error Handling**: How does it handle invalid or edge-case inputs?
5. **Business Value**: Does it solve real problems effectively?

### Why Traditional Testing Isn't Enough

LLM agents are different from traditional software:

- **Non-deterministic**: Same input might produce different outputs
- **Context-sensitive**: Previous conversations affect responses
- **Quality subjective**: "Good" responses are often subjective
- **Complex failure modes**: Agents can fail in subtle, hard-to-detect ways

### The Scenario Approach

**Scenarios** are comprehensive test cases that simulate real-world usage:

```python
{
    "name": "Help Command Test",
    "description": "User requests help information",
    "input": "Vertigo: Help", 
    "expected_behavior": "Provide comprehensive help information",
    "success_criteria": ["Contains available commands", "Includes usage examples"],
    "failure_modes": ["Empty response", "Generic error", "Missing commands"]
}
```

## Hands-On Exercise 1: Understanding Your Email Agent

Let's examine what your email command parser actually does:

### Step 1: Manual Testing

Try these commands manually to understand the baseline:

```bash
cd /Users/stephendulaney/Documents/Vertigo
python -c "
from email_command_parser import EmailCommandParser
parser = EmailCommandParser()

test_commands = [
    'Vertigo: Help',
    'Vertigo: Total stats', 
    'Re: Vertigo: Help',
    'Random email subject'
]

for cmd in test_commands:
    result = parser.parse_command(cmd)
    print(f'Input: {cmd}')
    print(f'Result: {result}')
    print('---')
"
```

### Step 2: Analyze the Results

For each test, ask yourself:

1. **Did it work as expected?** 
2. **How long did it take?**
3. **What would happen if this was a real user?**
4. **Are there edge cases I should worry about?**

### Step 3: Document Your Observations

Create a simple assessment:

```
✅ Help command works correctly
✅ Stats command detected properly  
✅ Reply prefixes handled correctly
✅ Unknown commands ignored gracefully
⚠️  Response time varies based on Firestore connection
```

## Hands-On Exercise 2: Your First Custom Scenario

Let's create a test scenario for a specific business need:

### Step 1: Define the Scenario

Think about a real situation where someone would email your Vertigo system:

```python
# Example: Executive wants weekly status
scenario = {
    "name": "Executive Weekly Status Request",
    "business_context": "CEO sends weekly email asking for project status",
    "input": "Vertigo: List this week",
    "expected_outcome": "Comprehensive weekly report with key metrics",
    "success_criteria": [
        "Contains transcript count",
        "Shows meeting summaries", 
        "Includes project breakdown",
        "Response time < 2 seconds"
    ]
}
```

### Step 2: Test Your Scenario

```bash
cd vertigo_scenario_framework
python -c "
import asyncio
from adapters.email_processor_adapter import EmailProcessorAdapter

async def test_scenario():
    adapter = EmailProcessorAdapter()
    
    test_data = {
        'subject': 'Vertigo: List this week',
        'body': '',
        'test_type': 'full_processing'
    }
    
    result = await adapter.execute_with_metrics(test_data)
    print('Test Result:', result)

asyncio.run(test_scenario())
"
```

### Step 3: Interpret the Results

Look for:

- **Success/failure status**
- **Response time metrics**
- **Quality of the response content**
- **Whether Firestore was accessed**
- **Error handling behavior**

## Understanding Test Results

### Reading the Output

When you run a test, you get structured results:

```python
{
    "success": True,
    "test_type": "command_detection",
    "input": {"subject": "Vertigo: Help", "body": ""},
    "result": {
        "subject": "Vertigo: Help - Available Commands",
        "body": "Available Commands:\n• Help\n• Stats...",
        "command": "help"
    },
    "analysis": {
        "command_match": True,
        "expected_command": "help",
        "detected_command": "help",
        "has_subject": True,
        "has_body": True,
        "response_length": 156
    },
    "performance": {
        "processing_time": 0.002,
        "timestamp": "2025-08-06T..."
    }
}
```

### Key Metrics to Watch

1. **Success Rate**: What percentage of tests pass?
2. **Response Time**: How fast is your agent?
3. **Command Accuracy**: Are commands detected correctly?
4. **Response Quality**: Are responses complete and helpful?
5. **Error Handling**: Does it fail gracefully?

## Production Considerations

### What Makes a Good Agent?

- **Reliability**: Works consistently (95%+ success rate)
- **Speed**: Responds quickly (< 1 second for simple commands)
- **Accuracy**: Correctly interprets user intent (98%+ accuracy)
- **Robustness**: Handles edge cases gracefully
- **Observability**: Can be monitored and debugged

### Common Pitfalls

1. **Over-testing deterministic parts** (command parsing)
2. **Under-testing integration points** (Firestore, APIs)
3. **Ignoring performance under load**
4. **Not testing error conditions**
5. **Missing business context in tests**

### Best Practices

1. **Test realistic scenarios**, not just edge cases
2. **Include performance benchmarks** in your tests
3. **Monitor test results over time** for regressions
4. **Test error conditions explicitly**
5. **Validate business outcomes**, not just technical functionality

## The Three Pillars of Agent Evaluation

### 1. Accuracy (40% weight by default)
- Command detection correctness
- Response structural integrity
- Technical precision
- Error handling capability

### 2. Relevance (30% weight by default)
- User intent matching
- Contextual appropriateness
- Response completeness
- Information quality

### 3. Business Impact (30% weight by default)
- Executive utility
- Decision support capability
- Strategic value
- Time to business value

## Scenario-Based Testing Philosophy

Instead of isolated unit tests, we use **realistic scenarios**:

```python
# Traditional approach - isolated
def test_help_command():
    assert parser.parse("help") == expected_help_response

# Scenario approach - realistic
{
    "name": "CEO Weekly Request",
    "description": "Realistic CEO request for weekly summary",
    "subject": "Re: Vertigo: List this week", 
    "body": "Stephen, can you send me the weekly transcript summary? I need it for the board meeting this afternoon.",
    "user_persona": "CEO",
    "business_impact": "high",
    "expected_elements": ["Last 7 Days", "Total Transcripts", "Success Rate"]
}
```

## Next Steps

### Immediate Actions

1. **Run the Hello World scenario** to verify your setup
2. **Try the custom scenario exercise** with your own use case
3. **Document baseline performance** for your agents
4. **Identify 2-3 critical scenarios** for your business

### Continue Learning

1. **Tutorial 02**: Deep dive into email command testing
2. **Tutorial 03**: Meeting transcript analysis testing  
3. **Tutorial 04**: Advanced evaluation techniques
4. **Tutorial 05**: Production monitoring setup

### Advanced Topics to Explore

- **A/B testing for prompt optimization**
- **Continuous evaluation pipelines**
- **Business impact measurement**
- **Integration with Langfuse monitoring**

## Troubleshooting

### Common Issues

**"Email parser not initialized"**
- Check your Python path includes the Vertigo root
- Verify `email_command_parser.py` is accessible
- Try running `python test_command_detection.py` first

**"Firestore connection errors"**
- Some tests may show warnings if Firestore isn't configured
- Basic command detection should still work
- Full processing tests require Firestore connectivity

**"Import errors"**
- Run `pip install -r scenario_requirements.txt`
- Make sure you're in the correct virtual environment
- Check that all Vertigo dependencies are installed

### Getting Help

- Check the README in `vertigo_scenario_framework/`
- Review existing test files in your Vertigo directory
- Look at the adapter code for implementation details

## Summary

In this tutorial, you learned:

✅ **Why agent testing matters** for production systems  
✅ **How to run your first test scenarios** with real results  
✅ **What to look for in test results** and how to interpret them  
✅ **How to create custom scenarios** for your specific needs  
✅ **Best practices for agent testing** in production  

You're now ready to move on to more advanced testing techniques and start building comprehensive test suites for your Vertigo agents.

**Ready for the next step?** Continue with [Tutorial 02: Email Command Testing](02_email_scenarios.md) to dive deeper into testing your email processing system.