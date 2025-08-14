# Thomas Debug Assistant - Comprehensive Testing Framework

## Overview
Thomas is a specialized debugging agent designed to systematically test the Vertigo Debug Toolkit, identify bugs, and intelligently triage them to appropriate specialist agents or escalate to humans when necessary.

## Core Architecture Analysis
Based on the codebase analysis, the Vertigo Debug Toolkit has the following structure:

### Main Application Routes
- **Root**: `/` (redirects to dashboard if authenticated)
- **Health Check**: `/health`
- **API Status**: `/api/vertigo/status`
- **Workflow Simulation**: `/api/simulate/workflow`

### Authentication Routes (`/auth/`)
- `/login` (GET/POST)
- `/logout`
- `/profile`
- `/profile/edit` (GET/POST)
- `/change-password` (GET/POST)
- `/admin/users` (admin only)
- `/admin/users/<id>/toggle` (admin only)

### Dashboard Routes (`/dashboard/`)
- `/` (main dashboard)
- `/api/metrics`
- `/api/cloud-status`
- `/api/prompts/performance/<id>`
- `/api/prompts/compare` (POST)
- `/api/prompts/<id>/recommendations`
- `/api/sessions/<session_id>`
- `/api/evaluation/report` (POST)
- `/api/prompts/<name>/history`
- `/advanced-evaluation`
- `/api/prompts/list`
- `/api/recent-activity`
- `/api/vertigo-status`
- `/api/langfuse-status`

### Prompts Routes (`/prompts/`)
- `/` (index)
- `/api/prompts` (GET)
- `/load-existing` (POST)
- `/add` (GET/POST)
- `/<id>/edit` (GET/POST)
- `/<id>/view`
- `/<id>/test` (GET/POST)
- `/manager`
- `/debug`
- `/test-selection`
- `/api/prompts/list`
- `/api/prompts` (POST)
- `/api/prompts/<id>` (GET/PUT)
- `/api/prompts/<id>/version` (POST)
- `/api/prompts/search` (GET)

### Performance Routes (`/performance/`)
### Costs Routes (`/costs/`)

## Phase 1: Basic Connectivity Testing

### Thomas Testing Protocol

#### 1.1 Health Check Tests
```bash
# Basic health check
curl -X GET "http://localhost:5000/health" \
  -H "Accept: application/json" \
  -w "\nHTTP Status: %{http_code}\nResponse Time: %{time_total}s\n"

# Expected Response:
# {"status": "healthy", "timestamp": "2025-08-03T...", "version": "1.0.0"}
# HTTP Status: 200
```

#### 1.2 Public Route Tests
```bash
# Test root route (should redirect or show login)
curl -X GET "http://localhost:5000/" \
  -w "\nHTTP Status: %{http_code}\nRedirect: %{redirect_url}\n"

# Test login page
curl -X GET "http://localhost:5000/login" \
  -w "\nHTTP Status: %{http_code}\n"
```

#### 1.3 Error Page Tests
```bash
# Test 404 handling
curl -X GET "http://localhost:5000/nonexistent" \
  -w "\nHTTP Status: %{http_code}\n"

# Should return 404 with custom error page
```

### Bug Identification Criteria for Phase 1
- **CRITICAL**: 500 errors on health check or basic routes
- **HIGH**: Missing error pages (raw Flask errors instead of custom templates)
- **MEDIUM**: Slow response times (>2 seconds for basic routes)
- **LOW**: Missing security headers

## Phase 2: Authentication Flow Testing

### 2.1 Login Flow Tests
```bash
# Test login page load
curl -X GET "http://localhost:5000/login" \
  -c cookies.txt \
  -w "\nHTTP Status: %{http_code}\n"

# Test login with invalid credentials
curl -X POST "http://localhost:5000/login" \
  -b cookies.txt -c cookies.txt \
  -d "email=invalid@test.com&password=wrongpassword" \
  -w "\nHTTP Status: %{http_code}\n"

# Test login with valid credentials (requires setup)
curl -X POST "http://localhost:5000/login" \
  -b cookies.txt -c cookies.txt \
  -d "email=admin@vertigo.com&password=ValidPassword123!" \
  -w "\nHTTP Status: %{http_code}\n"
```

### 2.2 Protected Route Tests
```bash
# Test accessing protected route without authentication
curl -X GET "http://localhost:5000/dashboard/" \
  -w "\nHTTP Status: %{http_code}\nRedirect: %{redirect_url}\n"

# Test accessing protected route with authentication
curl -X GET "http://localhost:5000/dashboard/" \
  -b cookies.txt \
  -w "\nHTTP Status: %{http_code}\n"
```

### 2.3 Session Management Tests
```bash
# Test logout
curl -X GET "http://localhost:5000/logout" \
  -b cookies.txt -c cookies.txt \
  -w "\nHTTP Status: %{http_code}\n"

# Test accessing protected route after logout
curl -X GET "http://localhost:5000/dashboard/" \
  -b cookies.txt \
  -w "\nHTTP Status: %{http_code}\n"
```

### Bug Identification Criteria for Phase 2
- **CRITICAL**: Authentication bypass vulnerabilities
- **HIGH**: Session fixation or CSRF vulnerabilities
- **HIGH**: Unprotected admin routes
- **MEDIUM**: Poor error messages revealing system information
- **LOW**: Missing password strength validation

## Phase 3: Core Functionality Testing

### 3.1 Dashboard API Tests
```bash
# Test metrics API (authenticated)
curl -X GET "http://localhost:5000/dashboard/api/metrics" \
  -b cookies.txt \
  -H "Accept: application/json" \
  -w "\nHTTP Status: %{http_code}\n"

# Test cloud status API
curl -X GET "http://localhost:5000/dashboard/api/cloud-status" \
  -b cookies.txt \
  -H "Accept: application/json" \
  -w "\nHTTP Status: %{http_code}\n"

# Test recent activity API
curl -X GET "http://localhost:5000/dashboard/api/recent-activity" \
  -b cookies.txt \
  -H "Accept: application/json" \
  -w "\nHTTP Status: %{http_code}\n"
```

### 3.2 Prompts API Tests
```bash
# Test prompts list API
curl -X GET "http://localhost:5000/prompts/api/prompts/list" \
  -b cookies.txt \
  -H "Accept: application/json" \
  -w "\nHTTP Status: %{http_code}\n"

# Test semantic search API
curl -X GET "http://localhost:5000/prompts/api/prompts/search?q=meeting%20analysis" \
  -b cookies.txt \
  -H "Accept: application/json" \
  -w "\nHTTP Status: %{http_code}\n"

# Test creating a prompt
curl -X POST "http://localhost:5000/prompts/api/prompts" \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Prompt","content":"Test content","prompt_type":"test"}' \
  -w "\nHTTP Status: %{http_code}\n"
```

### 3.3 Database Integrity Tests
```bash
# Test database operations don't cause 500 errors
curl -X POST "http://localhost:5000/prompts/load-existing" \
  -b cookies.txt \
  -d "" \
  -w "\nHTTP Status: %{http_code}\n"
```

### Bug Identification Criteria for Phase 3
- **CRITICAL**: Database connection failures
- **CRITICAL**: Data corruption or loss during operations
- **HIGH**: API endpoints returning 500 errors
- **HIGH**: Missing input validation leading to injection attacks
- **MEDIUM**: Slow database queries (>5 seconds)
- **LOW**: Inconsistent API response formats

## Phase 4: Edge Case and Error Handling

### 4.1 Input Validation Tests
```bash
# Test XSS attempts
curl -X POST "http://localhost:5000/prompts/add" \
  -b cookies.txt \
  -d "name=<script>alert('xss')</script>&content=test&prompt_type=test" \
  -w "\nHTTP Status: %{http_code}\n"

# Test SQL injection attempts
curl -X GET "http://localhost:5000/prompts/api/prompts/search?q=' OR 1=1 --" \
  -b cookies.txt \
  -w "\nHTTP Status: %{http_code}\n"

# Test oversized payloads
curl -X POST "http://localhost:5000/prompts/api/prompts" \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "print('{\"name\":\"' + 'A'*10000 + '\",\"content\":\"test\",\"prompt_type\":\"test\"}')")" \
  -w "\nHTTP Status: %{http_code}\n"
```

### 4.2 Rate Limiting Tests
```bash
# Test rapid requests (potential DoS)
for i in {1..100}; do
  curl -X GET "http://localhost:5000/health" \
    -w "%{http_code} " \
    --max-time 1 &
done
wait
```

### 4.3 File Upload Tests (if applicable)
```bash
# Test malicious file uploads
curl -X POST "http://localhost:5000/upload" \
  -b cookies.txt \
  -F "file=@malicious.php" \
  -w "\nHTTP Status: %{http_code}\n"
```

### Bug Identification Criteria for Phase 4
- **CRITICAL**: Successful XSS or SQL injection
- **CRITICAL**: File upload vulnerabilities
- **HIGH**: DoS vulnerabilities from rate limiting issues
- **HIGH**: Input validation bypasses
- **MEDIUM**: Error messages revealing stack traces
- **LOW**: Missing CSRF protection on non-critical forms

## Phase 5: Performance and Security Validation

### 5.1 Performance Baseline Tests
```bash
# Load testing with Apache Bench
ab -n 100 -c 10 http://localhost:5000/health

# Memory usage monitoring during load
while true; do
  ps aux | grep python3 | grep -v grep | awk '{print $6}' >> memory_usage.log
  sleep 1
done &

# Database connection pool testing
for i in {1..50}; do
  curl -X GET "http://localhost:5000/dashboard/api/metrics" \
    -b cookies.txt &
done
wait
```

### 5.2 Security Header Tests
```bash
# Test security headers
curl -I "http://localhost:5000/" | grep -E "(X-Frame-Options|X-XSS-Protection|X-Content-Type-Options|Strict-Transport-Security)"

# Test HTTPS enforcement (if configured)
curl -I "http://localhost:5000/" | grep -i "location"
```

### Bug Identification Criteria for Phase 5
- **HIGH**: Missing critical security headers in production
- **HIGH**: Memory leaks during load testing (>500MB growth)
- **MEDIUM**: Poor performance under load (>10 second response times)
- **MEDIUM**: Database connection pool exhaustion
- **LOW**: Non-optimized queries causing slowdowns

## Bug Assignment Logic

### Spec (Code Auditor) - Security Issues
**Trigger Conditions:**
- SQL injection vulnerabilities detected
- XSS vulnerabilities found
- Authentication bypasses
- Missing CSRF protection
- File upload vulnerabilities
- Missing security headers in production

**Assignment Command:**
```bash
curl -X POST "http://localhost:5000/api/bugs/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "bug_id": "BUG-001",
    "assigned_to": "spec",
    "category": "security",
    "severity": "critical",
    "description": "SQL injection found in search endpoint"
  }'
```

### Hue (Visual Design Reviewer) - UI/UX Issues
**Trigger Conditions:**
- Missing or broken error pages (404, 500)
- Inconsistent styling across pages
- Poor mobile responsiveness
- Accessibility violations
- Broken form layouts

**Assignment Command:**
```bash
curl -X POST "http://localhost:5000/api/bugs/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "bug_id": "BUG-002",
    "assigned_to": "hue",
    "category": "ui_ux",
    "severity": "medium",
    "description": "404 error page not rendering custom template"
  }'
```

### Probe (System Tester) - Performance Issues
**Trigger Conditions:**
- Response times >5 seconds under normal load
- Memory leaks detected
- Database query optimization needed
- Rate limiting issues
- Load balancing problems

**Assignment Command:**
```bash
curl -X POST "http://localhost:5000/api/bugs/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "bug_id": "BUG-003",
    "assigned_to": "probe",
    "category": "performance",
    "severity": "high",
    "description": "Dashboard API taking 8+ seconds to respond"
  }'
```

### Custodia (Cleanup Agent) - Code Quality Issues
**Trigger Conditions:**
- Inconsistent error handling
- Code duplication detected
- Poor logging practices
- Unused imports or functions
- Inconsistent coding standards

**Assignment Command:**
```bash
curl -X POST "http://localhost:5000/api/bugs/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "bug_id": "BUG-004",
    "assigned_to": "custodia",
    "category": "code_quality",
    "severity": "low",
    "description": "Inconsistent error handling in prompts module"
  }'
```

### Forge (Critical Thinking Analyzer) - Architecture Issues
**Trigger Conditions:**
- Database design flaws
- API architecture inconsistencies
- Scalability bottlenecks
- Integration problems
- Configuration management issues

**Assignment Command:**
```bash
curl -X POST "http://localhost:5000/api/bugs/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "bug_id": "BUG-005",
    "assigned_to": "forge",
    "category": "architecture",
    "severity": "medium",
    "description": "Database schema inefficiencies affecting query performance"
  }'
```

## Escalation Criteria and Protocols

### Immediate Human Escalation (CRITICAL)
**Triggers:**
- Active security exploits detected
- Database corruption or data loss
- Complete authentication system failure
- Multiple cascade failures (>3 critical systems failing)
- Production data exposure

**Escalation Protocol:**
```bash
# Immediate notification
curl -X POST "https://alerts.vertigo.com/critical" \
  -H "Authorization: Bearer $ALERT_TOKEN" \
  -d '{
    "severity": "critical",
    "system": "vertigo-debug-toolkit",
    "message": "CRITICAL: Active security exploit detected",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "requester": "thomas-debug-agent"
  }'

# Follow-up documentation
curl -X POST "http://localhost:5000/api/incidents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Critical Security Issue",
    "description": "Detailed description of the issue",
    "severity": "critical",
    "status": "escalated",
    "assigned_to": "human",
    "created_by": "thomas"
  }'
```

### Automated Escalation (HIGH)
**Triggers:**
- Multiple high-severity bugs in same category
- Performance degradation >80% from baseline
- Authentication issues affecting user access
- API endpoints completely non-functional

**Escalation Protocol:**
```bash
# Schedule escalation for next business day
curl -X POST "http://localhost:5000/api/escalations/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "bugs": ["BUG-001", "BUG-003", "BUG-007"],
    "category": "high_priority_cluster",
    "scheduled_for": "'$(date -d "+1 day" +%Y-%m-%d)'T09:00:00Z",
    "reason": "Multiple high-severity performance issues detected"
  }'
```

### Agent Collaboration Required (MEDIUM)
**Triggers:**
- Cross-functional issues requiring multiple agents
- Complex bugs requiring domain expertise
- Issues with unclear ownership

**Collaboration Protocol:**
```bash
# Multi-agent assignment
curl -X POST "http://localhost:5000/api/bugs/collaborate" \
  -H "Content-Type: application/json" \
  -d '{
    "bug_id": "BUG-008",
    "primary_agent": "spec",
    "collaborating_agents": ["hue", "forge"],
    "reason": "Security issue with UI implications and architectural impact"
  }'
```

## Structured Reporting Format

### Thomas Test Report Template
```json
{
  "report_id": "THOMAS-RPT-20250803-001",
  "timestamp": "2025-08-03T10:30:00Z",
  "test_session": {
    "duration_minutes": 45,
    "phases_completed": ["basic_connectivity", "authentication", "core_functionality"],
    "total_endpoints_tested": 23,
    "total_requests_made": 156
  },
  "summary": {
    "total_bugs_found": 8,
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 2,
    "overall_health_score": 75.5
  },
  "bugs_found": [
    {
      "bug_id": "BUG-001",
      "title": "SQL Injection in Search Endpoint",
      "severity": "critical",
      "category": "security",
      "endpoint": "/prompts/api/prompts/search",
      "description": "Search parameter allows SQL injection via malformed query",
      "reproduction_steps": [
        "curl -X GET 'http://localhost:5000/prompts/api/prompts/search?q=' OR 1=1 --'",
        "Observe database error messages in response"
      ],
      "assigned_to": "spec",
      "status": "assigned",
      "discovered_at": "2025-08-03T10:15:23Z"
    }
  ],
  "performance_metrics": {
    "average_response_time_ms": 450,
    "slowest_endpoint": "/dashboard/api/metrics",
    "slowest_response_time_ms": 2300,
    "errors_encountered": 3,
    "success_rate_percentage": 94.2
  },
  "recommendations": [
    {
      "priority": "critical",
      "action": "Immediately patch SQL injection vulnerability",
      "estimated_effort": "2 hours",
      "assigned_to": "spec"
    },
    {
      "priority": "high",
      "action": "Optimize dashboard metrics query",
      "estimated_effort": "4 hours",
      "assigned_to": "probe"
    }
  ],
  "next_actions": [
    "Schedule follow-up test in 24 hours after critical fixes",
    "Implement automated security scanning",
    "Add performance monitoring alerts"
  ]
}
```

### Daily Summary Report
```json
{
  "date": "2025-08-03",
  "tests_run": 4,
  "total_bugs_tracked": 23,
  "bugs_resolved_today": 5,
  "new_bugs_found": 3,
  "agent_assignments": {
    "spec": 8,
    "hue": 4,
    "probe": 6,
    "custodia": 3,
    "forge": 2
  },
  "system_health_trend": "improving",
  "critical_issues_outstanding": 0,
  "recommendations": [
    "Focus testing on new semantic search feature",
    "Increase authentication testing frequency",
    "Add monitoring for API response times"
  ]
}
```

## Thomas Implementation Commands

### Initialize Thomas Testing Session
```bash
# Set up testing environment
export THOMAS_SESSION_ID=$(date +%Y%m%d_%H%M%S)
export BASE_URL="http://localhost:5000"
export REPORT_DIR="./thomas_reports"
mkdir -p $REPORT_DIR

# Create session log
echo "Thomas Debug Session Started: $(date)" > $REPORT_DIR/session_$THOMAS_SESSION_ID.log
```

### Run Complete Test Suite
```bash
#!/bin/bash
# thomas_full_test.sh

# Phase 1: Basic Connectivity
echo "=== Phase 1: Basic Connectivity ==="
curl -X GET "$BASE_URL/health" -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" >> $REPORT_DIR/phase1_$THOMAS_SESSION_ID.log

# Phase 2: Authentication
echo "=== Phase 2: Authentication ==="
curl -X GET "$BASE_URL/login" -c cookies.txt -w "\nStatus: %{http_code}\n" >> $REPORT_DIR/phase2_$THOMAS_SESSION_ID.log

# Phase 3: Core Functionality (requires auth)
echo "=== Phase 3: Core Functionality ==="
curl -X GET "$BASE_URL/dashboard/api/metrics" -b cookies.txt -w "\nStatus: %{http_code}\n" >> $REPORT_DIR/phase3_$THOMAS_SESSION_ID.log

# Phase 4: Edge Cases
echo "=== Phase 4: Edge Cases ==="
curl -X GET "$BASE_URL/prompts/api/prompts/search?q=' OR 1=1 --" -b cookies.txt -w "\nStatus: %{http_code}\n" >> $REPORT_DIR/phase4_$THOMAS_SESSION_ID.log

# Generate report
python3 generate_thomas_report.py $THOMAS_SESSION_ID
```

### Bug Assignment Automation
```bash
# thomas_bug_processor.sh
#!/bin/bash

# Process discovered bugs and assign to appropriate agents
process_bugs() {
  local severity=$1
  local category=$2
  local agent=$3
  
  echo "Processing $severity $category bugs for assignment to $agent"
  
  # Implementation would read from bug database and make assignments
  curl -X POST "$BASE_URL/api/bugs/batch_assign" \
    -H "Content-Type: application/json" \
    -d "{
      \"filter\": {\"severity\": \"$severity\", \"category\": \"$category\"},
      \"assigned_to\": \"$agent\",
      \"processor\": \"thomas\"
    }"
}

# Run assignments
process_bugs "critical" "security" "spec"
process_bugs "high" "performance" "probe"
process_bugs "medium" "ui_ux" "hue"
```

This comprehensive framework provides Thomas with systematic testing capabilities, intelligent bug triaging, and clear escalation protocols to ensure the Vertigo Debug Toolkit remains robust and secure.