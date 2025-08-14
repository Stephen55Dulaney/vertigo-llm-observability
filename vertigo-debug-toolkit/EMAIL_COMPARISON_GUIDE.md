# Email Format Comparison Tool

A comprehensive tool for comparing LLM evaluation results in human-readable email format, making it easy to understand the differences between actual emails and AI-generated content.

## 🎯 Overview

This tool transforms JSON-based LLM evaluation results into professional, Gmail-like visual comparisons that stakeholders can easily understand. Instead of reading through complex JSON data, users can see side-by-side email comparisons with clear visual indicators for:

- Content accuracy scores
- Structural differences
- Missing or added information
- Performance metrics
- Optimization recommendations

## 🚀 Features

### Visual Email Comparison
- **Gmail-like Interface**: Familiar email styling with sender avatars, timestamps, and professional formatting
- **Side-by-Side Layout**: Compare actual emails and LLM results simultaneously
- **Difference Highlighting**: Visual indicators for added, missing, or modified content
- **Responsive Design**: Works on desktop and mobile devices

### Advanced Metrics
- **Content Accuracy**: Measures how well the LLM matches the original content
- **Structure Match**: Evaluates organizational similarity
- **Tone Consistency**: Assesses writing style alignment
- **Completeness**: Checks if all information is included
- **Format Compliance**: Verifies proper email structure
- **Factual Precision**: Validates specific details and participants

### Multiple Access Methods
1. **Web Interface**: Integrated into the Vertigo Debug Toolkit
2. **Command Line Tool**: Standalone script for automation
3. **API Endpoints**: Programmatic access for integration

## 📁 File Structure

```
vertigo-debug-toolkit/
├── templates/dashboard/
│   └── email_comparison.html          # Web interface template
├── app/services/
│   └── email_formatter.py             # Core comparison logic  
├── email_comparison_tool.py           # Standalone CLI tool
├── test_email_comparison.py           # Test suite
└── EMAIL_COMPARISON_GUIDE.md          # This guide
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- Flask application running
- Bootstrap 5 and Bootstrap Icons (loaded via CDN)

### Setup
1. Ensure you're in the vertigo-debug-toolkit directory
2. The service is automatically available when the Flask app runs
3. No additional dependencies needed (uses existing Vertigo toolkit libraries)

## 💻 Usage

### 1. Web Interface

Access the email comparison tool through the Vertigo Debug Toolkit:

```
http://localhost:8080/email-comparison
```

**Features:**
- Click "Refresh Comparison" to load sample data
- Export comparisons as standalone HTML files
- Interactive metrics with color-coded scoring
- Real-time difference highlighting

### 2. Command Line Tool

Use the standalone script for automation and batch processing:

```bash
# Compare two text files
python email_comparison_tool.py --actual-file actual_email.txt --llm-file llm_result.txt --output comparison.html

# Compare from JSON evaluation data
python email_comparison_tool.py --json-file evaluation_results.json --output comparison.html

# Interactive mode
python email_comparison_tool.py --interactive
```

**Interactive Mode Options:**
1. Compare two text files
2. Compare from JSON evaluation data  
3. Enter content manually

### 3. API Integration

Use the REST API endpoints for programmatic access:

```python
import requests

# Compare actual content with LLM result
response = requests.post('http://localhost:8080/api/email-comparison/compare', json={
    'actual_content': 'Meeting summary...',
    'llm_content': 'Generated summary...',
    'evaluation_data': {'response_time': 1.2, 'total_cost': 0.045}
})

# Generate comparison from JSON data
response = requests.post('http://localhost:8080/api/email-comparison/from-json', json={
    'json_data': {
        'actual_output': 'Original email...',
        'llm_output': 'Generated email...',
        'metrics': {'response_time': 1.5}
    }
})

# Get sample comparison for testing
response = requests.get('http://localhost:8080/api/email-comparison/sample')
```

## 📊 Understanding the Results

### Score Interpretation
- **90-100%**: Excellent (Green) - Meets or exceeds expectations
- **75-89%**: Good (Blue) - Acceptable performance with minor issues
- **60-74%**: Fair (Orange) - Needs improvement but functional
- **Below 60%**: Poor (Red) - Significant issues requiring attention

### Visual Indicators
- **Blue Highlight**: Added content not in original
- **Yellow Highlight**: Modified content with differences
- **Red Highlight**: Missing content from original
- **No Highlight**: Perfect match

### Key Metrics Explained

1. **Content Accuracy**: How well key points and action items match
2. **Structure Match**: Similarity in section organization 
3. **Tone Consistency**: Writing style and formality alignment
4. **Completeness**: Percentage of original information included
5. **Format Compliance**: Adherence to email structure standards
6. **Factual Precision**: Accuracy of specific details and names

## 🧪 Testing

Run the test suite to verify functionality:

```bash
python test_email_comparison.py
```

**Test Coverage:**
- Basic email parsing and comparison
- JSON data processing
- HTML output generation
- Error handling and edge cases

## 🔄 Integration Workflow

### Typical Usage Pattern:
1. **Run LLM Evaluation**: Generate JSON results from your LLM testing
2. **Load into Comparison Tool**: Use web interface or CLI to process results
3. **Review Visual Comparison**: Analyze differences and metrics
4. **Export Report**: Generate HTML for stakeholder review
5. **Implement Improvements**: Use recommendations to optimize prompts

### Integration with Existing Systems:
- Works with Langfuse evaluation data
- Compatible with Vertigo prompt testing framework
- Exports to standard HTML for sharing
- API endpoints for custom integrations

## 🛠️ Customization

### Modifying Email Templates
Edit `templates/dashboard/email_comparison.html` to customize:
- Visual styling and colors
- Layout and spacing
- Additional metrics display
- Export functionality

### Extending Comparison Logic
Modify `app/services/email_formatter.py` to add:
- Custom parsing rules
- New evaluation metrics
- Different similarity algorithms
- Industry-specific formatting

### Adding New Data Sources
The system can be extended to support:
- Different email formats
- Custom JSON schemas
- External evaluation services
- Real-time comparison feeds

## 📈 Performance Considerations

- **Memory Usage**: Lightweight processing, suitable for batch operations
- **Response Time**: Typical comparisons complete in under 1 second
- **Scalability**: Can handle hundreds of comparisons per minute
- **Storage**: Generated HTML reports are typically 50-200KB

## 🔍 Troubleshooting

### Common Issues:

**Error: "Could not import EmailFormatter"**
- Ensure you're running from the vertigo-debug-toolkit directory
- Check that all dependencies are installed

**Low Accuracy Scores**
- Verify input content is properly formatted
- Check for encoding issues in text files
- Ensure content sections are clearly marked

**HTML Export Not Working**
- Check file permissions in output directory
- Verify web browser supports the generated HTML
- Try a different output location

**API Endpoints Not Responding**
- Confirm Flask application is running on correct port
- Check that email_formatter service is properly imported
- Verify authentication if required

## 🤝 Support

For issues and questions:
1. Check the test suite for working examples
2. Review the source code comments for implementation details
3. Examine sample data in the web interface
4. Reference the Vertigo Debug Toolkit documentation

## 🔮 Future Enhancements

Planned improvements:
- Multi-language support for email content
- Advanced diff algorithms with semantic understanding
- Integration with more LLM evaluation frameworks
- Real-time collaboration features
- Automated report scheduling and distribution