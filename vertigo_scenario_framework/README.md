# Vertigo Scenario Framework

## Professional LLM Agent Testing with Scenario

This comprehensive framework teaches LLM evaluation methodologies through hands-on practice with Vertigo's email processing and meeting analysis systems.

## 🎯 Learning Objectives

- **Master Agent Testing**: Learn professional-grade agent testing methodologies
- **Multi-step Evaluation**: Understand conversation flow evaluation
- **Scenario-Based Testing**: Build comprehensive test scenarios
- **Production Pipeline**: Create professional evaluation pipelines

## 🏗️ Architecture Overview

```
vertigo_scenario_framework/
├── README.md                    # This file
├── setup/                       # Installation and configuration
├── adapters/                    # AgentAdapter classes for Vertigo components
├── scenarios/                   # Test scenarios and use cases
├── evaluators/                  # Evaluation metrics and judges
├── tutorials/                   # Step-by-step learning materials
├── examples/                    # Working examples and demonstrations
└── reports/                     # Generated evaluation reports
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# From Vertigo root directory
pip install -r scenario_requirements.txt
```

### 2. Configure Environment
```bash
# Copy and edit configuration
cp vertigo_scenario_framework/setup/.env.example .env.scenario
# Add your API keys and configuration
```

### 3. Run First Test
```bash
cd vertigo_scenario_framework
python examples/hello_world_scenario.py
```

## 📋 Components Overview

### AgentAdapters
- **EmailProcessorAdapter**: Tests email command detection and processing
- **MeetingAnalyzerAdapter**: Evaluates meeting transcript analysis
- **StatusGeneratorAdapter**: Tests executive status generation

### Evaluation Framework
- **Multi-dimensional testing**: Accuracy, relevance, business impact
- **Real-time monitoring**: Integration with Langfuse and production systems
- **Statistical analysis**: A/B testing and confidence intervals

### Learning Materials
- **Step-by-step tutorials**: From basic concepts to advanced techniques
- **Hands-on exercises**: Practice with real Vertigo scenarios
- **Best practices**: Production-ready evaluation pipelines

## 🎓 Learning Path for Stephen

1. **Basic Concepts** → `tutorials/01_introduction.md`
2. **Email Testing** → `tutorials/02_email_scenarios.md`
3. **Meeting Analysis** → `tutorials/03_meeting_evaluation.md`
4. **Advanced Techniques** → `tutorials/04_advanced_evaluation.md`
5. **Production Deployment** → `tutorials/05_production_setup.md`

## 🔧 Key Features

- **Production-ready**: Integration with existing Vertigo infrastructure
- **Educational focus**: Comprehensive learning materials for skill development
- **Real scenarios**: Test with actual email commands and meeting transcripts
- **Comprehensive metrics**: Business impact, accuracy, and relevance scoring
- **Monitoring integration**: Langfuse traces and performance tracking

## 📊 Evaluation Metrics

### Primary Metrics
- **Command Accuracy**: Correct command detection rate
- **Response Quality**: Semantic similarity and completeness
- **Business Impact**: Relevance to business objectives
- **Error Handling**: Graceful failure and recovery

### Advanced Metrics
- **Multi-turn Consistency**: Conversation flow evaluation
- **Edge Case Handling**: Robustness testing
- **Performance**: Response time and resource usage
- **User Experience**: Simulated user satisfaction

## 🏆 Success Criteria

By completing this framework, Stephen will be able to:
- Design and implement comprehensive agent testing strategies
- Build production-ready evaluation pipelines
- Understand multi-dimensional LLM evaluation
- Create custom scenarios for specific business needs
- Monitor and optimize agent performance in production

## 🔗 Integration Points

- **Langfuse**: Trace collection and analysis
- **Vertigo Debug Toolkit**: Dashboard integration
- **Google Cloud**: Production monitoring
- **Firestore**: Test data and results storage

## 📈 Next Steps

1. Complete the tutorial series
2. Customize scenarios for your specific use cases  
3. Integrate with production monitoring
4. Expand to additional Vertigo components

---

**Ready to master LLM evaluation? Start with `tutorials/01_introduction.md`**