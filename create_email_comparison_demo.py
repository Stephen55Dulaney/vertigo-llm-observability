#!/usr/bin/env python3
"""
Create a beautiful email-format comparison demo using your actual email data.
"""

import json
from datetime import datetime

def create_email_comparison_html():
    """Create a beautiful email comparison display."""
    
    # Your actual email content (from screenshot)
    actual_email = {
        "from": "vertigo.agent.2025@gmail.com",
        "to": "sdulaney",
        "subject": "Meeting Summary",
        "timestamp": "9:50 AM (5 hours ago)",
        "content": {
            "summary": "The team discussed daily planning using \"Ambition MD\" and its sub-agents, explored Google Agent Space integration, reviewed AI enablement strategy and tools, addressed speed issues, and confirmed access to AI Studio. They also discussed knowledge sharing and platform migration.",
            "key_points": [
                "Introduction of \"Ambition MD\" for daily planning",
                "Exploration of Google Agent Space",
                "AI enablement strategy and tool evaluation", 
                "Speed issue investigation",
                "Access confirmation for AI Studio and other tools",
                "Knowledge sharing and platform migration"
            ],
            "action_items": [
                "Work on Max migration - Kurt Miller",
                "Send strategy and format for tools being investigated - Kurt Miller",
                "Track down issue of not getting more traces after successfully getting langu traces - Stephen Dulaney",
                "Share learnings about Google Agent Space platform and write up for the team - Kurt Miller",
                "Continue going through base off tool set and share with Bob Schneider and Jay Ma - Kurt Miller",
                "Work with Stephen Dulaney on interview style for meeting platform owners, documenting personas, rockstars, and best use cases - Kurt Miller"
            ],
            "next_steps": [
                "Complete Max migration by end of weekend",
                "Investigate and share information on various AI tools",
                "Troubleshoot 'langu traces' issue",
                "Explore and report on Google Agent Space",
                "Address speed problem",
                "Share knowledge on Cursor",
                "Add Jay Ma to relevant communication channels",
                "Create technology tips channel"
            ],
            "participants": ["Stephen Dulaney", "Kurt Miller"]
        }
    }
    
    # LLM Test Results (simulated based on your evaluation)
    llm_result = {
        "from": "LLM Test Engine",
        "to": "Evaluation System", 
        "subject": "Meeting Analysis Test Results",
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "content": {
            "summary": "Executive-level overview of key outcomes from team meeting covering project management tools, AI platform integration, technical issues resolution, and strategic planning initiatives.",
            "key_points": [
                "Implementation of \"Ambition MD\" project management system",
                "Google Agent Space platform evaluation and integration",
                "AI tools strategy development and assessment",
                "Technical debugging and performance optimization",
                "AI Studio access and tool confirmation",
                "Cross-platform migration and knowledge transfer"
            ],
            "action_items": [
                "Complete Max platform migration - Kurt Miller (Weekend deadline)",
                "Document tool evaluation strategy and format - Kurt Miller", 
                "Debug and resolve trace generation issues - Stephen Dulaney",
                "Create Google Agent Space documentation - Kurt Miller",
                "Review and optimize tool performance baseline - Kurt Miller",
                "Develop interview framework for platform assessment - Kurt Miller & Stephen Dulaney"
            ],
            "next_steps": [
                "Finalize Max migration timeline and deliverables",
                "Conduct comprehensive AI tools research and reporting",
                "Resolve technical tracing and monitoring issues",
                "Document and share Google Agent Space findings",
                "Address system performance bottlenecks", 
                "Establish Cursor knowledge sharing protocols",
                "Expand team communication channels and collaboration",
                "Create dedicated technology tips and best practices channel"
            ],
            "participants": ["Stephen Dulaney", "Kurt Miller"]
        },
        "evaluation_scores": {
            "accuracy": 0.87,
            "relevance": 0.92,
            "completeness": 0.85,
            "structure": 0.90,
            "tone": 0.88,
            "factual_precision": 0.86
        }
    }
    
    # Create beautiful HTML comparison
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vertigo Email vs LLM Test Results Comparison</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
                line-height: 1.5;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .comparison-container {{
                display: flex;
                min-height: 600px;
            }}
            .email-column {{
                flex: 1;
                padding: 0;
                border-right: 2px solid #e9ecef;
            }}
            .email-column:last-child {{
                border-right: none;
            }}
            .email-header {{
                background: #f8f9fa;
                padding: 20px 25px;
                border-bottom: 1px solid #dee2e6;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            .email-title {{
                font-size: 18px;
                font-weight: 600;
                color: #343a40;
                margin: 0 0 8px 0;
                display: flex;
                align-items: center;
            }}
            .email-meta {{
                font-size: 14px;
                color: #6c757d;
                margin: 4px 0;
            }}
            .email-content {{
                padding: 25px;
            }}
            .section {{
                margin-bottom: 25px;
            }}
            .section-title {{
                font-size: 16px;
                font-weight: 600;
                color: #495057;
                margin-bottom: 12px;
                padding-bottom: 6px;
                border-bottom: 2px solid #e9ecef;
            }}
            .summary {{
                background: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #2196f3;
                font-size: 15px;
                line-height: 1.6;
            }}
            .list-item {{
                display: flex;
                align-items: flex-start;
                margin-bottom: 8px;
                padding: 8px 12px;
                background: #f8f9fa;
                border-radius: 6px;
                font-size: 14px;
            }}
            .list-item:nth-child(even) {{
                background: #ffffff;
            }}
            .bullet {{
                color: #007bff;
                font-weight: bold;
                margin-right: 8px;
                flex-shrink: 0;
            }}
            .participants {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .participant {{
                background: #007bff;
                color: white;
                padding: 4px 12px;
                border-radius: 15px;
                font-size: 13px;
                font-weight: 500;
            }}
            .scores {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-top: 20px;
            }}
            .score-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 12px;
                margin-top: 15px;
            }}
            .score-item {{
                text-align: center;
                padding: 12px;
                border-radius: 6px;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .score-value {{
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 4px;
            }}
            .score-label {{
                font-size: 12px;
                color: #6c757d;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .score-excellent {{ color: #28a745; }}
            .score-good {{ color: #17a2b8; }}
            .score-fair {{ color: #ffc107; }}
            .score-poor {{ color: #dc3545; }}
            .icon {{
                width: 20px;
                height: 20px;
                margin-right: 8px;
            }}
            @media (max-width: 768px) {{
                .comparison-container {{
                    flex-direction: column;
                }}
                .email-column {{
                    border-right: none;
                    border-bottom: 2px solid #e9ecef;
                }}
                .email-column:last-child {{
                    border-bottom: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📧 Vertigo Email vs LLM Test Results</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Human-Readable Comparison for Stakeholder Review</p>
            </div>
            
            <div class="comparison-container">
                <!-- Actual Email Column -->
                <div class="email-column">
                    <div class="email-header">
                        <div class="email-title">
                            📨 Actual Gmail Email
                        </div>
                        <div class="email-meta">From: {actual_email['from']}</div>
                        <div class="email-meta">To: {actual_email['to']}</div>
                        <div class="email-meta">Subject: {actual_email['subject']}</div>
                        <div class="email-meta">Time: {actual_email['timestamp']}</div>
                    </div>
                    
                    <div class="email-content">
                        <div class="section">
                            <div class="section-title">📝 Meeting Summary</div>
                            <div class="summary">{actual_email['content']['summary']}</div>
                        </div>
                        
                        <div class="section">
                            <div class="section-title">🎯 Key Points</div>
                            {''.join([f'<div class="list-item"><span class="bullet">•</span>{point}</div>' for point in actual_email['content']['key_points']])}
                        </div>
                        
                        <div class="section">
                            <div class="section-title">✅ Action Items</div>
                            {''.join([f'<div class="list-item"><span class="bullet">→</span>{item}</div>' for item in actual_email['content']['action_items']])}
                        </div>
                        
                        <div class="section">
                            <div class="section-title">🚀 Next Steps</div>
                            {''.join([f'<div class="list-item"><span class="bullet">▶</span>{step}</div>' for step in actual_email['content']['next_steps']])}
                        </div>
                        
                        <div class="section">
                            <div class="section-title">👥 Participants</div>
                            <div class="participants">
                                {''.join([f'<span class="participant">{p}</span>' for p in actual_email['content']['participants']])}
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- LLM Test Results Column -->
                <div class="email-column">
                    <div class="email-header">
                        <div class="email-title">
                            🤖 LLM Test Results
                        </div>
                        <div class="email-meta">From: {llm_result['from']}</div>
                        <div class="email-meta">To: {llm_result['to']}</div>
                        <div class="email-meta">Subject: {llm_result['subject']}</div>
                        <div class="email-meta">Time: {llm_result['timestamp']}</div>
                    </div>
                    
                    <div class="email-content">
                        <div class="section">
                            <div class="section-title">📝 Generated Summary</div>
                            <div class="summary">{llm_result['content']['summary']}</div>
                        </div>
                        
                        <div class="section">
                            <div class="section-title">🎯 Identified Points</div>
                            {''.join([f'<div class="list-item"><span class="bullet">•</span>{point}</div>' for point in llm_result['content']['key_points']])}
                        </div>
                        
                        <div class="section">
                            <div class="section-title">✅ Extracted Actions</div>
                            {''.join([f'<div class="list-item"><span class="bullet">→</span>{item}</div>' for item in llm_result['content']['action_items']])}
                        </div>
                        
                        <div class="section">
                            <div class="section-title">🚀 Planned Steps</div>
                            {''.join([f'<div class="list-item"><span class="bullet">▶</span>{step}</div>' for step in llm_result['content']['next_steps']])}
                        </div>
                        
                        <div class="section">
                            <div class="section-title">👥 Detected Participants</div>
                            <div class="participants">
                                {''.join([f'<span class="participant">{p}</span>' for p in llm_result['content']['participants']])}
                            </div>
                        </div>
                        
                        <div class="scores">
                            <div class="section-title">📊 Evaluation Scores</div>
                            <div class="score-grid">
    """
    
    # Add evaluation scores
    for metric, score in llm_result['evaluation_scores'].items():
        score_class = "score-excellent" if score >= 0.9 else "score-good" if score >= 0.8 else "score-fair" if score >= 0.7 else "score-poor"
        html_content += f'''
                                <div class="score-item">
                                    <div class="score-value {score_class}">{score:.0%}</div>
                                    <div class="score-label">{metric.replace('_', ' ').title()}</div>
                                </div>
        '''
    
    html_content += """
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def main():
    """Create and save the email comparison."""
    print("📧 Creating Email vs LLM Test Results Comparison...")
    
    html_content = create_email_comparison_html()
    
    filename = f"email_vs_llm_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Comparison created: {filename}")
    print(f"📊 Opening in browser...")
    
    # Open in browser
    import webbrowser
    webbrowser.open(f'file://{os.path.abspath(filename)}')
    
    return filename

if __name__ == "__main__":
    import os
    main()