# Vertigo - Advanced LLM Observability & Prompt Evaluation System

A comprehensive LLM observability and prompt evaluation platform built with Langfuse open source, featuring advanced analytics, A/B testing, cost optimization, and session analysis.

## 🚀 Features

### Advanced Prompt Evaluation
- **Performance Analytics** - Success rates, latency, cost tracking
- **A/B Testing Framework** - Statistical comparison of prompt versions
- **Cost Optimization** - Token usage analysis and savings recommendations
- **Session Analysis** - Multi-turn conversation quality tracking
- **Comprehensive Grading** - A-F performance scores with actionable insights

### LLM Observability
- **Complete Tracing** - Every API call, prompt, completion, and token usage
- **Session-Level Data** - Track entire conversation flows
- **Real-time Monitoring** - Live performance and cost metrics
- **Error Detection** - Automatic error pattern identification

### Vertigo Debug Toolkit
- **Web Dashboard** - Real-time monitoring and analytics
- **Prompt Management** - Version control and testing interface
- **Cloud Service Monitoring** - Health checks for deployed services
- **Cost Tracking** - Detailed cost breakdown by model and prompt

## 📁 Project Structure

```
Vertigo/
├── vertigo-debug-toolkit/     # Main Flask application
│   ├── app/                   # Flask app structure
│   │   ├── blueprints/        # Route modules
│   │   ├── models/           # Database models
│   │   ├── services/         # Business logic
│   │   └── templates/        # HTML templates
│   ├── static/               # CSS, JS, images
│   ├── tests/                # Test scripts
│   └── requirements.txt      # Python dependencies
├── vertigo/                  # Cloud functions
│   └── functions/           # Google Cloud Functions
├── agents/                   # AI agent implementations
├── config/                   # Configuration files
└── docs/                     # Documentation
```

## 🛠️ Technology Stack

- **Backend**: Python, Flask, SQLAlchemy
- **LLM Observability**: Langfuse Open Source
- **Cloud**: Google Cloud Functions, Cloud Scheduler
- **Database**: SQLite (local), Firestore (cloud)
- **Frontend**: HTML, CSS (Tailwind), JavaScript (Chart.js)
- **AI Models**: GPT-4, GPT-3.5-turbo, Gemini

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Cloud SDK
- Langfuse account (free tier available)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Vertigo
   ```

2. **Set up virtual environment**
   ```bash
   cd vertigo-debug-toolkit
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Initialize the database**
   ```bash
   python setup_admin.py
   ```

5. **Start the application**
   ```bash
   python app.py
   ```

6. **Access the dashboard**
   - Open http://localhost:8080
   - Login with admin credentials

## 📊 Advanced Features

### Prompt Evaluation System
```python
from app.services.prompt_evaluator import PromptEvaluator

# Get comprehensive performance metrics
evaluator = PromptEvaluator()
metrics = evaluator.get_prompt_performance("Meeting Summary v2", days=30)

# A/B test two prompt versions
result = evaluator.compare_prompts("Meeting Summary v1", "Meeting Summary v2")

# Get cost optimization recommendations
recommendations = evaluator.get_cost_optimization_recommendations("Meeting Summary v1")
```

### Langfuse Integration
```python
from app.services.langfuse_client import LangfuseClient

# Create traces for LLM calls
client = LangfuseClient()
trace_id = client.create_trace("meeting_summary", metadata={"project": "vertigo"})

# Track generations
generation_id = client.create_generation(
    trace_id=trace_id,
    model="gpt-4",
    prompt="Generate meeting summary...",
    completion="Meeting focused on..."
)
```

## 🔧 Configuration

### Environment Variables
```bash
# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_HOST=https://us.cloud.langfuse.com

# Google Cloud
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GEMINI_API_KEY=your-gemini-key

# Flask
FLASK_SECRET_KEY=your-secret-key
FLASK_DEBUG=True
```

### Cloud Functions Deployment
```bash
# Deploy email processor
cd vertigo/functions/email-processor
bash ../../vertigo-debug-toolkit/deploy_function.sh

# Deploy meeting processor
cd ../meeting-processor
bash ../../vertigo-debug-toolkit/deploy_function.sh
```

## 📈 Usage Examples

### 1. Monitor Prompt Performance
- Track success rates, latency, and costs
- Identify underperforming prompts
- Optimize based on real data

### 2. A/B Test Prompt Versions
- Compare different prompt formulations
- Measure statistical significance
- Make data-driven improvements

### 3. Cost Optimization
- Analyze token usage patterns
- Identify expensive prompts
- Get specific savings recommendations

### 4. Session Analysis
- Track multi-turn conversations
- Analyze context retention
- Optimize user experience

## 🧪 Testing

### Run Test Suite
```bash
# Test Langfuse integration
python test_langfuse_integration.py

# Test advanced evaluation
python test_advanced_evaluation.py

# Verify data
python verify_data.py
```

### Create Sample Data
```bash
# Generate test traces and costs
python create_sample_traces.py

# Sync from Langfuse
python sync_langfuse_data.py
```

## 📊 Dashboard Features

- **Real-time Metrics** - Live performance data
- **Interactive Charts** - Performance trends and cost breakdowns
- **Prompt Management** - Create, edit, and test prompts
- **Cloud Monitoring** - Health checks for deployed services
- **Cost Analytics** - Detailed cost tracking and optimization

## 🔒 Security

- Environment variable protection
- Google Cloud IAM integration
- Secure API key management
- Database access controls

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation in `/docs`
- Review the test scripts for examples
- Open an issue on GitHub

## 🎯 Roadmap

- [ ] Real-time alerting system
- [ ] Advanced statistical analysis
- [ ] Multi-model comparison
- [ ] Automated prompt optimization
- [ ] Integration with more LLM providers
- [ ] Mobile dashboard
- [ ] API for external integrations

---

**Built with ❤️ using Langfuse Open Source for advanced LLM observability** 