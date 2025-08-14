# Vertigo Scenario Framework - Quick Start Guide

**Get up and running with professional agent testing in 5 minutes**

This guide gets you from zero to running your first comprehensive agent evaluation in just a few commands.

## 🚀 Quick Start (5 Minutes)

### Step 1: Run Setup
```bash
# From your Vertigo root directory
cd /Users/stephendulaney/Documents/Vertigo
python vertigo_scenario_framework/setup_scenario_framework.py
```

### Step 2: Test Your First Scenario
```bash
cd vertigo_scenario_framework
python examples/hello_world_scenario.py
```

### Step 3: Run Production Evaluation
```bash
python examples/production_evaluation_demo.py
```

**That's it!** You now have comprehensive agent testing running on your Vertigo system.

## 📊 What You Just Did

1. **Setup**: Installed dependencies and configured the testing framework
2. **Hello World**: Tested your email command parser with 5 realistic scenarios  
3. **Production Evaluation**: Ran a comprehensive multi-dimensional evaluation including:
   - Email processing functionality
   - Performance under load
   - Business impact assessment
   - Integration health checks
   - Production readiness analysis

## 🎯 Understanding Your Results

### Hello World Output
```
👋 Welcome to Vertigo Agent Testing!
🚀 Starting Hello World Scenario...
✅ PASSED - Agent correctly identified 'help' command
📊 Success Rate: 100.0%
```

### Production Evaluation Output
```
🏭 Production Evaluation Demo
📧 Evaluating Email Processing System...
   • Success Rate: 91.7%
   • Average Response Time: 0.234s
   • Overall Grade: A

🎯 FINAL EVALUATION REPORT
   • System Grade: A
   • Production Ready: ✅ YES
```

## 🏃‍♂️ Next Steps (Choose Your Path)

### For Learning (Start Here)
1. **📚 Read Tutorial 01**: `tutorials/01_introduction.md`
2. **🔬 Deep Dive Email Testing**: `tutorials/02_email_scenarios.md`
3. **🏗️ Build Custom Scenarios**: Create your own test cases

### For Production Use
1. **🔍 Analyze Your Results**: Check the generated evaluation reports
2. **📈 Set Up Monitoring**: Use the monitoring scripts for ongoing health checks
3. **🔧 Fix Issues**: Address any failing tests or recommendations

### For Advanced Users
1. **📊 Integrate with Langfuse**: Connect to your existing observability
2. **🤖 Add More Agents**: Create adapters for meeting analysis, status generation
3. **📋 Custom Evaluators**: Build domain-specific evaluation metrics

## 🛠️ Troubleshooting

### Common Issues & Solutions

**"Email parser not initialized"**
```bash
# Make sure you're in the right directory
pwd  # Should show: /Users/stephendulaney/Documents/Vertigo
cd /Users/stephendulaney/Documents/Vertigo
```

**"Import errors"**
```bash
pip install -r scenario_requirements.txt
```

**"Firestore connection errors"**
- Don't worry! Basic tests still work
- Full integration tests need Firestore configured
- Check your service account credentials

### Getting Help
- 📖 Check the tutorials in `tutorials/`
- 🔧 Review the setup script output
- 📋 Look at example code in `examples/`

## 📁 What's in the Framework

```
vertigo_scenario_framework/
├── setup_scenario_framework.py  # One-click setup
├── examples/
│   ├── hello_world_scenario.py       # Your first test
│   └── production_evaluation_demo.py # Complete evaluation
├── tutorials/
│   ├── 01_introduction.md       # Learn the concepts
│   └── 02_email_scenarios.md    # Deep dive testing
├── adapters/
│   ├── base_adapter.py          # Foundation for all adapters
│   └── email_processor_adapter.py  # Email system integration
└── evaluation_results/          # Your test results (created automatically)
```

## 🎓 Learning Path

**Beginner (30 minutes)**
1. Run Quick Start (above)
2. Read `tutorials/01_introduction.md`
3. Try the hands-on exercises

**Intermediate (2 hours)**  
1. Complete `tutorials/02_email_scenarios.md`
2. Create custom business scenarios
3. Set up performance monitoring

**Advanced (Half day)**
1. Build custom adapters for other Vertigo components
2. Integrate with your CI/CD pipeline
3. Create specialized evaluators for your use cases

## 🏆 Success Metrics

After completing the Quick Start, you should have:

✅ **Working test framework** running on your system  
✅ **Baseline performance metrics** for your email system  
✅ **Production readiness assessment** with specific recommendations  
✅ **Understanding of testing concepts** and how to apply them  

## 🚀 Ready to Go Deeper?

- **For Comprehensive Learning**: Start with `tutorials/01_introduction.md`
- **For Immediate Results**: Run the production evaluation regularly
- **For Custom Needs**: Look at the adapter code and create your own

**Remember**: The goal isn't perfect test scores - it's understanding your system's performance and continuously improving it.

---

**Questions? Issues? Feedback?**
- Check the troubleshooting section above
- Review the tutorial files for detailed explanations
- Look at the example code for implementation details