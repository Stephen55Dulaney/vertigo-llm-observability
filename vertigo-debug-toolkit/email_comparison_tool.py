#!/usr/bin/env python3
"""
Standalone Email Comparison Tool for Vertigo LLM Evaluation.

Usage:
    python email_comparison_tool.py --actual-file actual_email.txt --llm-file llm_result.txt --output comparison.html
    python email_comparison_tool.py --json-file evaluation_results.json --output comparison.html
    python email_comparison_tool.py --interactive
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the app directory to the path so we can import our services
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from services.email_formatter import EmailFormatter
except ImportError:
    print("Error: Could not import EmailFormatter. Make sure you're running from the vertigo-debug-toolkit directory.")
    sys.exit(1)

class EmailComparisonTool:
    """Standalone tool for email format comparison."""
    
    def __init__(self):
        self.formatter = EmailFormatter()
    
    def compare_files(self, actual_file: str, llm_file: str, output_file: str = None):
        """Compare two email files and generate HTML output."""
        try:
            # Read actual email content
            with open(actual_file, 'r', encoding='utf-8') as f:
                actual_content = f.read()
            
            # Read LLM result content
            with open(llm_file, 'r', encoding='utf-8') as f:
                llm_content = f.read()
            
            # Perform comparison
            comparison = self.formatter.compare_emails(actual_content, llm_content)
            
            # Generate HTML output
            html_output = self.generate_html_report(comparison)
            
            # Save or display output
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_output)
                print(f"Comparison report saved to: {output_file}")
            else:
                print(html_output)
            
            return comparison
            
        except FileNotFoundError as e:
            print(f"Error: File not found - {e}")
            return None
        except Exception as e:
            print(f"Error comparing files: {e}")
            return None
    
    def compare_from_json(self, json_file: str, output_file: str = None):
        """Compare emails from JSON evaluation data."""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            comparison = self.formatter.generate_comparison_from_json(json_data)
            
            # Generate HTML output
            html_output = self.generate_html_report(comparison)
            
            # Save or display output
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_output)
                print(f"Comparison report saved to: {output_file}")
            else:
                print(html_output)
            
            return comparison
            
        except FileNotFoundError:
            print(f"Error: JSON file not found - {json_file}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in file {json_file} - {e}")
            return None
        except Exception as e:
            print(f"Error processing JSON file: {e}")
            return None
    
    def interactive_mode(self):
        """Interactive mode for comparing emails."""
        print("🔧 Vertigo Email Comparison Tool - Interactive Mode")
        print("=" * 60)
        
        # Get comparison type
        print("\nComparison Options:")
        print("1. Compare two text files")
        print("2. Compare from JSON evaluation data")
        print("3. Enter content manually")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == "1":
            actual_file = input("Enter path to actual email file: ").strip()
            llm_file = input("Enter path to LLM result file: ").strip()
            output_file = input("Enter output HTML file path (optional): ").strip() or None
            
            return self.compare_files(actual_file, llm_file, output_file)
        
        elif choice == "2":
            json_file = input("Enter path to JSON evaluation file: ").strip()
            output_file = input("Enter output HTML file path (optional): ").strip() or None
            
            return self.compare_from_json(json_file, output_file)
        
        elif choice == "3":
            print("\nEnter actual email content (press Ctrl+D when done):")
            actual_content = sys.stdin.read()
            
            print("\nEnter LLM result content (press Ctrl+D when done):")
            llm_content = sys.stdin.read()
            
            output_file = input("Enter output HTML file path (optional): ").strip() or None
            
            comparison = self.formatter.compare_emails(actual_content, llm_content)
            html_output = self.generate_html_report(comparison)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_output)
                print(f"Comparison report saved to: {output_file}")
            else:
                print(html_output)
            
            return comparison
        
        else:
            print("Invalid option selected.")
            return None
    
    def generate_html_report(self, comparison):
        """Generate a complete HTML report from comparison results."""
        
        # Generate email content HTML
        actual_email_html = self.generate_email_html(comparison.actual_email, "actual")
        llm_email_html = self.generate_email_html_with_diffs(comparison.llm_email, comparison.differences, "llm")
        
        # Generate metrics HTML
        metrics_html = self.generate_metrics_html(comparison.metrics)
        
        # Generate recommendations HTML
        recommendations_html = self.generate_recommendations_html(comparison.recommendations, comparison.strengths)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Comparison Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        /* Gmail-like styling */
        .email-container {{
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            overflow: hidden;
        }}

        .email-header {{
            background-color: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .sender-avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 16px;
            margin-right: 12px;
        }}

        .email-body {{
            padding: 24px;
            line-height: 1.6;
            color: #202124;
            font-size: 14px;
        }}

        .email-body h4 {{
            color: #1a73e8;
            font-size: 16px;
            font-weight: 600;
            margin: 20px 0 12px 0;
            border-bottom: 2px solid #e8f0fe;
            padding-bottom: 8px;
        }}

        .comparison-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 20px 0;
        }}

        .metric-card {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 16px;
            text-align: center;
            margin: 8px;
        }}

        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 4px;
        }}

        .metric-label {{
            font-size: 12px;
            color: #5f6368;
            text-transform: uppercase;
        }}

        .score-excellent {{ color: #137333; }}
        .score-good {{ color: #1a73e8; }}
        .score-fair {{ color: #f57c00; }}
        .score-poor {{ color: #d93025; }}

        .diff-highlight {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 8px 12px;
            margin: 8px 0;
            border-radius: 4px;
        }}

        .diff-added {{
            background-color: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 8px 12px;
            margin: 8px 0;
            border-radius: 4px;
        }}

        .diff-removed {{
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 8px 12px;
            margin: 8px 0;
            border-radius: 4px;
        }}

        .evaluation-summary {{
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            border-radius: 12px;
            padding: 24px;
            margin: 30px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .participants-list {{
            background: #f5f5f5;
            border-radius: 6px;
            padding: 12px;
            margin: 12px 0;
        }}

        @media (max-width: 768px) {{
            .comparison-container {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container-fluid p-4">
        <div class="row mb-4">
            <div class="col-12">
                <h1 class="h3 mb-1">
                    <i class="bi bi-envelope-check me-2"></i>
                    Email Comparison Report
                </h1>
                <p class="text-muted">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
        </div>

        <!-- Evaluation Summary -->
        <div class="evaluation-summary">
            <div class="text-center">
                <h4>Overall Evaluation Results</h4>
                <div class="row mt-3">
                    <div class="col-md-4">
                        <div class="metric-value score-{self.get_score_class(comparison.metrics.overall_score)}">{comparison.metrics.overall_score}%</div>
                        <div class="metric-label">Overall Score</div>
                    </div>
                    <div class="col-md-4">
                        <div class="metric-value score-good">{comparison.metrics.response_time}s</div>
                        <div class="metric-label">Response Time</div>
                    </div>
                    <div class="col-md-4">
                        <div class="metric-value score-fair">${comparison.metrics.total_cost:.3f}</div>
                        <div class="metric-label">Total Cost</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Comparison Headers -->
        <div class="comparison-container">
            <div class="text-center">
                <h5>Actual Email</h5>
                <p class="text-muted">From Gmail inbox</p>
            </div>
            <div class="text-center">
                <h5>LLM Generated Result</h5>
                <p class="text-muted">From evaluation test</p>
            </div>
        </div>

        <!-- Email Comparison -->
        <div class="comparison-container">
            {actual_email_html}
            {llm_email_html}
        </div>

        <!-- Detailed Metrics -->
        {metrics_html}

        <!-- Recommendations -->
        {recommendations_html}
    </div>
</body>
</html>
        """
        
        return html_template
    
    def generate_email_html(self, email_data, email_type):
        """Generate HTML for an email."""
        avatar_text = email_data.sender_name[:2].upper() if email_data.sender_name else "VA"
        
        html = f"""
        <div class="email-container">
            <div class="email-header">
                <div class="d-flex align-items-center">
                    <div class="sender-avatar">{avatar_text}</div>
                    <div>
                        <div class="fw-bold">{email_data.sender_name}</div>
                        <div class="text-muted small">{email_data.sender_email}</div>
                    </div>
                </div>
                <div class="text-muted small">{email_data.timestamp}</div>
            </div>
            
            <div class="email-body">
                <h3 class="mb-3">{email_data.subject}</h3>
        """
        
        if email_data.key_points:
            html += "<h4>Key Points</h4><ul>"
            for point in email_data.key_points:
                html += f"<li>{point}</li>"
            html += "</ul>"
        
        if email_data.action_items:
            html += "<h4>Action Items</h4><ul>"
            for item in email_data.action_items:
                html += f"<li>{item}</li>"
            html += "</ul>"
        
        if email_data.next_steps:
            html += "<h4>Next Steps</h4><ul>"
            for step in email_data.next_steps:
                html += f"<li>{step}</li>"
            html += "</ul>"
        
        if email_data.participants:
            html += f'<div class="participants-list"><strong>Participants:</strong> {", ".join(email_data.participants)}</div>'
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def generate_email_html_with_diffs(self, email_data, differences, email_type):
        """Generate HTML for an email with difference highlighting."""
        avatar_text = email_data.sender_name[:2].upper() if email_data.sender_name else "LLM"
        
        html = f"""
        <div class="email-container">
            <div class="email-header">
                <div class="d-flex align-items-center">
                    <div class="sender-avatar">{avatar_text}</div>
                    <div>
                        <div class="fw-bold">{email_data.sender_name}</div>
                        <div class="text-muted small">{email_data.sender_email}</div>
                    </div>
                </div>
                <div class="text-muted small">{email_data.timestamp}</div>
            </div>
            
            <div class="email-body">
                <h3 class="mb-3">{email_data.subject}</h3>
        """
        
        # Helper function to get diff class
        def get_diff_class(content, section):
            for diff in differences:
                if (diff.get('section') == section and 
                    (diff.get('content') == content or diff.get('modified') == content)):
                    return {
                        'added': 'diff-added',
                        'missing': 'diff-removed', 
                        'modified': 'diff-highlight'
                    }.get(diff.get('type'), '')
            return ''
        
        if email_data.key_points:
            html += "<h4>Key Points</h4><ul>"
            for point in email_data.key_points:
                css_class = get_diff_class(point, 'key_points')
                html += f'<li class="{css_class}">{point}</li>'
            html += "</ul>"
        
        if email_data.action_items:
            html += "<h4>Action Items</h4><ul>"
            for item in email_data.action_items:
                css_class = get_diff_class(item, 'action_items')
                html += f'<li class="{css_class}">{item}</li>'
            html += "</ul>"
        
        if email_data.next_steps:
            html += "<h4>Next Steps</h4><ul>"
            for step in email_data.next_steps:
                css_class = get_diff_class(step, 'next_steps')
                html += f'<li class="{css_class}">{step}</li>'
            html += "</ul>"
        
        if email_data.participants:
            html += f'<div class="participants-list"><strong>Participants:</strong> {", ".join(email_data.participants)}</div>'
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def generate_metrics_html(self, metrics):
        """Generate HTML for detailed metrics."""
        metric_items = [
            ("Content Accuracy", metrics.content_accuracy),
            ("Structure Match", metrics.structure_match),
            ("Tone Consistency", metrics.tone_consistency),
            ("Completeness", metrics.completeness),
            ("Format Compliance", metrics.format_compliance),
            ("Factual Precision", metrics.factual_precision)
        ]
        
        html = """
        <div class="card mt-4">
            <div class="card-header">
                <h5><i class="bi bi-graph-up me-2"></i>Detailed Evaluation Metrics</h5>
            </div>
            <div class="card-body">
                <div class="row">
        """
        
        for label, value in metric_items:
            score_class = self.get_score_class(value)
            html += f"""
                <div class="col-md-4 col-sm-6">
                    <div class="metric-card">
                        <div class="metric-value score-{score_class}">{value}%</div>
                        <div class="metric-label">{label}</div>
                    </div>
                </div>
            """
        
        html += """
                </div>
            </div>
        </div>
        """
        
        return html
    
    def generate_recommendations_html(self, recommendations, strengths):
        """Generate HTML for recommendations and strengths."""
        html = """
        <div class="card mt-4">
            <div class="card-header">
                <h5><i class="bi bi-lightbulb me-2"></i>Analysis & Recommendations</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6>Areas of Excellence</h6>
                        <ul class="list-group list-group-flush">
        """
        
        for strength in strengths:
            html += f"""
            <li class="list-group-item border-0 px-0">
                <i class="bi bi-check-circle text-success me-2"></i>
                {strength}
            </li>
            """
        
        html += """
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>Improvement Opportunities</h6>
                        <ul class="list-group list-group-flush">
        """
        
        for recommendation in recommendations:
            html += f"""
            <li class="list-group-item border-0 px-0">
                <i class="bi bi-exclamation-triangle text-warning me-2"></i>
                {recommendation}
            </li>
            """
        
        html += """
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        """
        
        return html
    
    def get_score_class(self, score):
        """Get CSS class for score color."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        else:
            return "poor"

def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(
        description="Compare LLM evaluation results in human-readable email format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --actual-file actual.txt --llm-file result.txt --output report.html
  %(prog)s --json-file evaluation.json --output report.html
  %(prog)s --interactive
        """
    )
    
    parser.add_argument('--actual-file', help='Path to actual email content file')
    parser.add_argument('--llm-file', help='Path to LLM result file')
    parser.add_argument('--json-file', help='Path to JSON evaluation results file')
    parser.add_argument('--output', help='Output HTML file path')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    args = parser.parse_args()
    
    tool = EmailComparisonTool()
    
    if args.interactive:
        tool.interactive_mode()
    elif args.json_file:
        tool.compare_from_json(args.json_file, args.output)
    elif args.actual_file and args.llm_file:
        tool.compare_files(args.actual_file, args.llm_file, args.output)
    else:
        parser.print_help()
        print("\nError: You must specify either --interactive, --json-file, or both --actual-file and --llm-file")
        sys.exit(1)

if __name__ == "__main__":
    main()