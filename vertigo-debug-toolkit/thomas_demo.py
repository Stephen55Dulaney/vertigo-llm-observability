#!/usr/bin/env python3
"""
Thomas Debug Agent Demo
Demonstrates the complete Thomas debugging workflow
"""

import sys
import os
import time
import subprocess
from thomas_bug_manager import ThomasBugManager, Severity, BugCategory

def print_header(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

def print_step(step, description):
    print(f"\n🔍 Step {step}: {description}")
    print("-" * 40)

def simulate_thomas_testing():
    """Simulate Thomas running his test suite and finding bugs"""
    
    print_header("THOMAS DEBUG AGENT DEMONSTRATION")
    print("Simulating a complete Thomas debugging session...")
    
    # Initialize Thomas
    manager = ThomasBugManager()
    
    print_step(1, "Initialize Thomas Bug Manager")
    print(f"✅ Session ID: {manager.session_id}")
    print(f"✅ Database: {manager.db_path}")
    print(f"✅ Base URL: {manager.base_url}")
    
    # Simulate finding various bugs during testing
    print_step(2, "Simulating Bug Discovery During Testing")
    
    bugs_found = [
        {
            "title": "SQL Injection in Search Endpoint",
            "description": "Search parameter allows SQL injection via malformed query: ' OR 1=1 --",
            "severity": "critical",
            "category": "security",
            "endpoint": "/prompts/api/prompts/search",
            "reproduction_steps": [
                "curl -X GET 'http://localhost:5000/prompts/api/prompts/search?q=\\' OR 1=1 --'",
                "Observe database error messages in response",
                "Payload: ' OR 1=1 -- returns all prompts without authentication"
            ],
            "evidence": {
                "http_code": 200,
                "response_contains": "mysql error",
                "vulnerability_type": "SQL Injection"
            }
        },
        {
            "title": "XSS Vulnerability in Error Pages",
            "description": "Error pages reflect user input without proper encoding",
            "severity": "high",
            "category": "security",
            "endpoint": "/dashboard/?error=<script>alert('xss')</script>",
            "reproduction_steps": [
                "Navigate to /dashboard/?error=<script>alert('xss')</script>",
                "Observe that script tag is not encoded in error message"
            ],
            "evidence": {
                "http_code": 200,
                "response_contains": "<script>alert('xss')</script>",
                "vulnerability_type": "Reflected XSS"
            }
        },
        {
            "title": "Dashboard API Response Time Degradation",
            "description": "Dashboard metrics API consistently taking 8+ seconds to respond",
            "severity": "high", 
            "category": "performance",
            "endpoint": "/dashboard/api/metrics",
            "reproduction_steps": [
                "curl -X GET 'http://localhost:5000/dashboard/api/metrics' -w 'Time: %{time_total}'",
                "Repeat test 10 times",
                "Average response time: 8.3 seconds"
            ],
            "evidence": {
                "avg_response_time": 8.3,
                "baseline_response_time": 0.5,
                "degradation_percentage": 1560
            }
        },
        {
            "title": "Missing CSRF Protection on Admin Forms",
            "description": "Admin user management forms lack CSRF token validation",
            "severity": "medium",
            "category": "security",
            "endpoint": "/admin/users/<id>/toggle",
            "reproduction_steps": [
                "Login as admin",
                "Inspect /admin/users page form",
                "No CSRF token found in form"
            ],
            "evidence": {
                "form_analysis": "no_csrf_token",
                "vulnerability_type": "CSRF"
            }
        },
        {
            "title": "Custom 404 Page Not Rendering",
            "description": "Application serves default Flask error page instead of custom 404 template",
            "severity": "medium",
            "category": "ui_ux",
            "endpoint": "/nonexistent-page",
            "reproduction_steps": [
                "curl -X GET 'http://localhost:5000/nonexistent-page'",
                "Response contains 'Werkzeug' instead of custom template"
            ],
            "evidence": {
                "http_code": 404,
                "response_contains": "Werkzeug",
                "expected": "custom 404 template"
            }
        },
        {
            "title": "Inconsistent Error Handling in Prompts Module",
            "description": "Some routes return JSON errors while others return HTML, breaking API consistency",
            "severity": "low",
            "category": "code_quality",
            "endpoint": "/prompts/api/prompts/<invalid-id>",
            "reproduction_steps": [
                "Test various invalid inputs on prompts API",
                "Some return JSON errors, others HTML"
            ],
            "evidence": {
                "inconsistency_type": "mixed_response_formats",
                "affected_endpoints": ["/prompts/api/prompts/999", "/prompts/999/view"]
            }
        }
    ]
    
    created_bugs = []
    for i, bug_data in enumerate(bugs_found, 1):
        print(f"\n  🐛 Finding Bug {i}: {bug_data['title']}")
        print(f"     Severity: {bug_data['severity'].upper()}")
        print(f"     Category: {bug_data['category']}")
        print(f"     Endpoint: {bug_data['endpoint']}")
        
        # Create bug in system
        bug = manager.create_bug(
            title=bug_data['title'],
            description=bug_data['description'],
            severity=bug_data['severity'],
            category=bug_data['category'],
            endpoint=bug_data['endpoint'],
            reproduction_steps=bug_data.get('reproduction_steps', []),
            evidence=bug_data.get('evidence', {})
        )
        created_bugs.append(bug)
        
        print(f"     ✅ Bug ID: {bug.id}")
        print(f"     📋 Assigned to: {bug.assigned_agent.value}")
        print(f"     ⏱️  Estimated effort: {bug.estimated_effort_hours} hours")
        
        if bug.status.value == "escalated":
            print(f"     🚨 ESCALATED to human attention!")
        
        time.sleep(0.5)  # Simulate time between discoveries
    
    print_step(3, "Agent Assignment Summary")
    
    # Show agent assignments
    agent_assignments = {}
    for bug in created_bugs:
        agent = bug.assigned_agent.value
        if agent not in agent_assignments:
            agent_assignments[agent] = []
        agent_assignments[agent].append(bug)
    
    for agent, bugs in agent_assignments.items():
        print(f"\n📋 {agent.upper()} ({len(bugs)} bugs):")
        for bug in bugs:
            print(f"   • {bug.id}: {bug.title} ({bug.severity.value})")
    
    print_step(4, "Escalation Analysis")
    
    escalated_bugs = [bug for bug in created_bugs if bug.status.value == "escalated"]
    if escalated_bugs:
        print(f"🚨 {len(escalated_bugs)} bugs escalated to human attention:")
        for bug in escalated_bugs:
            print(f"   • {bug.id}: {bug.title}")
            print(f"     Reason: {bug.severity.value} {bug.category.value} issue")
    else:
        print("✅ No bugs required immediate escalation")
    
    print_step(5, "Generate Comprehensive Report")
    
    report = manager.generate_report()
    report_file = manager.save_report(report)
    
    print(f"📊 Report saved to: {report_file}")
    print(f"\n📈 Session Statistics:")
    print(f"   Total Bugs Found: {report['statistics']['total_bugs']}")
    print(f"   Critical: {report['statistics']['by_severity'].get('critical', 0)}")
    print(f"   High: {report['statistics']['by_severity'].get('high', 0)}")
    print(f"   Medium: {report['statistics']['by_severity'].get('medium', 0)}")
    print(f"   Low: {report['statistics']['by_severity'].get('low', 0)}")
    print(f"   Escalations: {report['statistics']['escalations']}")
    print(f"   Total Estimated Effort: {report['statistics']['estimated_total_effort']} hours")
    
    print_step(6, "Recommendations")
    
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. [{rec['urgency'].upper()}] {rec['action']}")
    
    print_header("THOMAS DEBUG SESSION COMPLETE")
    print("✅ All bugs discovered, classified, and assigned")
    print("✅ Critical issues escalated appropriately") 
    print("✅ Comprehensive report generated")
    print("✅ Next actions identified for each specialist agent")
    
    print(f"\n📁 Files created:")
    print(f"   • Bug database: {manager.db_path}")
    print(f"   • Report: {report_file}")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Review escalated critical security issues immediately")
    print(f"   2. Spec should investigate SQL injection and XSS vulnerabilities")
    print(f"   3. Probe should optimize dashboard API performance")
    print(f"   4. Hue should implement custom 404 error pages")
    print(f"   5. Custodia should standardize error response formats")
    print(f"   6. Schedule follow-up Thomas testing session after fixes")

if __name__ == "__main__":
    simulate_thomas_testing()