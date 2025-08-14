# Vertigo Scenario Framework - Complete Deployment Guide

## 🎯 Professional LLM Agent Evaluation Framework

This comprehensive framework provides professional-grade testing and evaluation capabilities for Vertigo's LLM agents, designed for Stephen to master LLM evaluation methodologies through hands-on practice.

## 📋 Framework Overview

### Components Built

1. **Setup & Configuration System** (`vertigo_scenario_framework/setup/`)
   - Environment configuration management
   - Dependency validation
   - Framework diagnostics

2. **Agent Adapters** (`vertigo_scenario_framework/adapters/`)
   - `EmailProcessorAdapter`: Tests email command detection and processing
   - `MeetingAnalyzerAdapter`: Evaluates meeting transcript analysis with prompt variants
   - `StatusGeneratorAdapter`: Tests executive status generation capabilities

3. **Comprehensive Evaluation Framework** (`vertigo_scenario_framework/evaluators/`)
   - `AccuracyEvaluator`: Command detection, response correctness, technical precision
   - `RelevanceEvaluator`: User intent matching, contextual appropriateness, information quality
   - `BusinessImpactEvaluator`: Executive utility, decision support, strategic value
   - `ComprehensiveEvaluator`: Multi-dimensional scoring with weighted composite results

4. **Scenario Management** (`vertigo_scenario_framework/scenarios/`)
   - `EmailScenarioBuilder`: Comprehensive email testing scenarios
   - Basic functionality, edge cases, business contexts, stress tests
   - Realistic user personas and business impact levels

5. **Production Monitoring** (`vertigo_scenario_framework/monitoring/`)
   - `LangfuseMonitor`: Production trace collection and analytics
   - Performance monitoring and trend analysis
   - Integration with existing Vertigo observability stack

6. **Educational Tutorial Series** (`vertigo_scenario_framework/tutorials/`)
   - Step-by-step learning materials
   - Hands-on exercises and practical examples
   - Best practices for professional evaluation

## 🚀 Quick Start Installation

### 1. Install Dependencies

```bash
# From Vertigo root directory
pip install -r scenario_requirements.txt
```

### 2. Configure Environment

```bash
# Copy and customize configuration
cp vertigo_scenario_framework/setup/.env.example .env.scenario

# Edit .env.scenario with your settings
# Key configurations:
# - VERTIGO_ROOT_PATH=/Users/stephendulaney/Documents/Vertigo  
# - LANGFUSE_PUBLIC_KEY=your_key (optional)
# - GEMINI_API_KEY=your_key (for production)
```

### 3. Validate Setup

```bash
cd vertigo_scenario_framework
python setup/config.py
```

### 4. Run Hello World Test

```bash
python examples/hello_world_scenario.py
```

## 📚 Learning Path for Stephen

### Phase 1: Foundation (1-2 hours)
1. **Introduction Tutorial**: `tutorials/01_introduction.md`
   - Core concepts of agent evaluation
   - Understanding multi-dimensional scoring
   - Framework architecture overview

2. **Hello World Exercise**: `examples/hello_world_scenario.py`
   - Basic evaluation workflow
   - Interpreting results
   - Understanding scoring methodology

### Phase 2: Email Evaluation Mastery (2-3 hours)
1. **Email Scenarios Tutorial**: `tutorials/02_email_scenarios.md`
   - Comprehensive scenario design
   - Business context integration
   - Edge case handling

2. **Email Scenario Demo**: `examples/email_scenario_demo.py`
   - Running full email test suites
   - Performance analysis by category
   - Improvement identification

### Phase 3: Advanced Evaluation (2-3 hours)
1. **Meeting Analysis Evaluation**: `tutorials/03_meeting_evaluation.md`
   - Prompt variant testing
   - Content quality assessment
   - Multi-turn conversation analysis

2. **Production Deployment**: `examples/production_evaluation_demo.py`
   - Complete evaluation pipeline
   - Production monitoring integration
   - Continuous improvement workflows

## 🛠️ Component Integration Guide

### Email Processing Integration

```python
from vertigo_scenario_framework.adapters import EmailProcessorAdapter
from vertigo_scenario_framework.evaluators import ComprehensiveEvaluator

async def evaluate_email_agent():
    # Initialize components
    adapter = EmailProcessorAdapter()
    evaluator = ComprehensiveEvaluator()
    
    # Define test scenario
    scenario = {
        "name": "CEO Help Request",
        "subject": "Vertigo: Help",
        "user_persona": "CEO",
        "business_impact": "high"
    }
    
    # Execute and evaluate
    response = await adapter.execute_with_metrics(scenario)
    evaluation = await evaluator.evaluate_single(scenario, response)
    
    print(f"Score: {evaluation['composite_score']:.3f}")
    print(f"Grade: {evaluation['quality_grade']}")
```

### Langfuse Production Monitoring

```python
from vertigo_scenario_framework.monitoring import LangfuseMonitor

# Initialize monitoring
monitor = LangfuseMonitor({
    "enabled": True,
    "langfuse": {
        "public_key": "your_langfuse_public_key",
        "secret_key": "your_langfuse_secret_key"
    }
})

# Start evaluation trace
trace_id = monitor.start_evaluation_trace(scenario, "email_processor")

# Log results
monitor.log_evaluation_results(trace_id, evaluation_result, scenario)
```

### Custom Scenario Creation

```python
from vertigo_scenario_framework.scenarios import EmailScenarioBuilder

# Build comprehensive scenario suite
builder = EmailScenarioBuilder()

# Get scenarios by category
help_scenarios = builder.get_scenarios_by_tag("help_command")
business_critical = builder.get_business_critical_scenarios()
high_priority = builder.get_scenarios_by_priority("high")

# Create custom scenarios
custom_scenario = {
    "name": "Custom Business Scenario",
    "subject": "Your custom email subject",
    "user_persona": "Project Manager",
    "business_impact": "medium",
    "expected_elements": ["Expected", "Response", "Elements"]
}
```

## 📊 Evaluation Methodology

### Three-Pillar Scoring System

1. **Accuracy (40% default weight)**
   - Command detection correctness
   - Response structural integrity  
   - Technical precision
   - Error handling capability

2. **Relevance (30% default weight)**
   - User intent matching
   - Contextual appropriateness
   - Response completeness
   - Information quality

3. **Business Impact (30% default weight)**
   - Executive utility
   - Decision support capability
   - Strategic value
   - Time to business value

### Scoring Scale
- **0.9-1.0**: Excellent (A+ to A)
- **0.8-0.9**: Good (A- to B+)  
- **0.7-0.8**: Satisfactory (B to B-)
- **0.6-0.7**: Needs Improvement (C+ to C-)
- **0.0-0.6**: Poor (D to F)

## 🏗️ Production Deployment

### CI/CD Integration

```yaml
# .github/workflows/agent-evaluation.yml
name: Agent Evaluation
on: [push, pull_request]

jobs:
  evaluate-agents:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r scenario_requirements.txt
          
      - name: Run evaluation suite
        run: |
          cd vertigo_scenario_framework
          python examples/production_evaluation_demo.py
        env:
          LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
          LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
          
      - name: Upload evaluation report
        uses: actions/upload-artifact@v2
        with:
          name: evaluation-report
          path: vertigo_scenario_framework/examples/production_report_*.json
```

### Monitoring Dashboard Integration

The framework integrates with Vertigo Debug Toolkit for dashboard visualization:

```python
# In vertigo-debug-toolkit/app/services/
from vertigo_scenario_framework.monitoring import LangfuseMonitor

def get_evaluation_metrics():
    """Get evaluation metrics for dashboard."""
    monitor = LangfuseMonitor()
    return monitor.create_evaluation_dashboard_data()
```

### Alert Configuration

```python
# Set up alerts for performance degradation
def check_performance_thresholds(evaluation_results):
    """Alert on performance degradation."""
    avg_score = sum(r["composite_score"] for r in evaluation_results) / len(evaluation_results)
    
    if avg_score < 0.7:
        send_alert(f"Agent performance degraded to {avg_score:.3f}")
    
    # Dimension-specific alerts
    for dimension in ["accuracy", "relevance", "business_impact"]:
        dim_avg = sum(r["dimension_scores"][dimension] for r in evaluation_results) / len(evaluation_results)
        if dim_avg < 0.6:
            send_alert(f"{dimension} performance critically low: {dim_avg:.3f}")
```

## 🎓 Educational Value

### Skills Stephen Will Master

1. **Agent Testing Methodologies**
   - Scenario-based testing vs. unit testing
   - Multi-dimensional evaluation approaches
   - Business context integration

2. **Professional Evaluation Frameworks**
   - Weighted scoring systems
   - Statistical analysis and confidence intervals
   - Trend analysis and performance monitoring

3. **Production Integration**
   - Continuous evaluation pipelines
   - Monitoring and alerting systems
   - Performance optimization workflows

4. **Business Impact Assessment**
   - Executive utility measurement
   - Decision support evaluation
   - Strategic value quantification

### Practical Applications

- **Prompt Engineering**: Systematic evaluation of prompt variants
- **Model Comparison**: A/B testing different LLM approaches
- **Performance Monitoring**: Continuous quality assurance in production
- **Business Alignment**: Ensuring AI systems deliver measurable business value

## 🔧 Customization Guide

### Custom Evaluation Dimensions

```python
class CustomEvaluator(BaseEvaluator):
    """Custom evaluator for specific business needs."""
    
    async def evaluate(self, scenario, response):
        # Implement custom evaluation logic
        custom_score = self.calculate_custom_metric(response)
        
        return {
            "score": custom_score,
            "details": {"custom_analysis": "..."}
        }
```

### Custom Scenario Types

```python
class CustomScenarioBuilder:
    """Build scenarios for specific domain needs."""
    
    def build_domain_specific_scenarios(self):
        return [
            {
                "name": "Domain Specific Test",
                "custom_field": "domain_value",
                "evaluation_criteria": ["criteria1", "criteria2"]
            }
        ]
```

## 📈 Performance Optimization

### Evaluation Performance Tips

1. **Batch Processing**: Use batch evaluation for large scenario sets
2. **Parallel Execution**: Run evaluations in parallel where possible
3. **Caching**: Cache expensive evaluation computations
4. **Monitoring**: Use Langfuse for performance tracking

### Resource Management

```python
# Configure resource limits
config = {
    "max_concurrent_evaluations": 10,
    "evaluation_timeout_seconds": 300,
    "batch_size": 50
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes Vertigo root
2. **Configuration Issues**: Validate .env.scenario settings
3. **API Errors**: Check API keys and network connectivity
4. **Performance Issues**: Monitor resource usage and adjust batch sizes

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug configuration
config = {
    "debug_mode": True,
    "log_level": "DEBUG",
    "detailed_analysis": True
}
```

## 🎯 Success Metrics

### Framework Adoption Success

- [ ] Complete tutorial series (6+ hours of hands-on learning)
- [ ] Successfully evaluate all three agent types
- [ ] Implement custom scenarios for specific use cases
- [ ] Integrate with production monitoring
- [ ] Achieve consistent evaluation scores >0.8

### Business Impact Success

- [ ] Measurable improvement in agent quality
- [ ] Reduced production issues through better testing
- [ ] Faster iteration cycles with automated evaluation
- [ ] Clear ROI from evaluation framework investment

## 📞 Support & Resources

### Documentation
- **Tutorial Series**: `vertigo_scenario_framework/tutorials/`
- **API Documentation**: In-code docstrings and examples
- **Configuration Guide**: `setup/config.py`

### Example Implementations
- **Hello World**: `examples/hello_world_scenario.py`
- **Production Pipeline**: `examples/production_evaluation_demo.py`
- **Custom Scenarios**: `examples/custom_scenario_demo.py`

### Integration Points
- **Langfuse**: Production monitoring and analytics
- **Vertigo Debug Toolkit**: Dashboard integration
- **CI/CD**: Automated evaluation pipelines
- **Google Cloud**: Production deployment monitoring

---

## 🎉 Conclusion

This comprehensive Vertigo Scenario Framework provides Stephen with a professional-grade LLM agent evaluation system that demonstrates industry best practices in:

- **Systematic Agent Testing**: Moving beyond ad-hoc testing to comprehensive evaluation
- **Multi-dimensional Analysis**: Understanding quality across accuracy, relevance, and business impact
- **Production Integration**: Seamless deployment in professional environments
- **Continuous Improvement**: Data-driven optimization of agent performance

The framework is designed as both a practical tool and an educational experience, ensuring Stephen masters the methodologies and can apply them to any LLM agent evaluation challenge.

**Ready to master LLM evaluation? Start with the Hello World example and work through the tutorial series!**