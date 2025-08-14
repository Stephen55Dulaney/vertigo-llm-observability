#!/bin/bash
# Thomas Debug Agent - Automated Test Suite
# Comprehensive testing framework for Vertigo Debug Toolkit

set -e  # Exit on any error

# Configuration
BASE_URL="${BASE_URL:-http://localhost:5000}"
THOMAS_SESSION_ID=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="./thomas_reports"
COOKIES_FILE="./thomas_cookies_$THOMAS_SESSION_ID.txt"
TEST_RESULTS_FILE="$REPORT_DIR/test_results_$THOMAS_SESSION_ID.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize testing environment
initialize_thomas() {
    echo -e "${BLUE}=== Thomas Debug Agent Starting ===${NC}"
    echo "Session ID: $THOMAS_SESSION_ID"
    echo "Base URL: $BASE_URL"
    echo "Report Directory: $REPORT_DIR"
    
    # Create directories
    mkdir -p $REPORT_DIR
    
    # Initialize results file
    cat > $TEST_RESULTS_FILE << EOF
{
  "session_id": "$THOMAS_SESSION_ID",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "base_url": "$BASE_URL",
  "phases": {},
  "bugs_found": [],
  "summary": {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "critical_issues": 0,
    "high_issues": 0,
    "medium_issues": 0,
    "low_issues": 0
  }
}
EOF
    
    echo "Thomas initialized successfully"
}

# Logging function
log_test() {
    local phase=$1
    local test_name=$2
    local status=$3
    local details=$4
    local http_code=$5
    local response_time=$6
    
    local color=$GREEN
    if [ "$status" = "FAIL" ]; then
        color=$RED
    elif [ "$status" = "WARN" ]; then
        color=$YELLOW
    fi
    
    echo -e "${color}[$phase] $test_name: $status${NC}"
    if [ ! -z "$details" ]; then
        echo "  Details: $details"
    fi
    if [ ! -z "$http_code" ]; then
        echo "  HTTP Code: $http_code"
    fi
    if [ ! -z "$response_time" ]; then
        echo "  Response Time: ${response_time}s"
    fi
    echo
}

# Bug reporting function
report_bug() {
    local severity=$1
    local category=$2
    local title=$3
    local description=$4
    local endpoint=$5
    local suggested_agent=$6
    
    local bug_id="BUG-$(date +%Y%m%d%H%M%S)-$(printf '%04d' $RANDOM)"
    
    echo -e "${RED}🐛 BUG FOUND: $bug_id${NC}"
    echo "  Severity: $severity"
    echo "  Category: $category"
    echo "  Title: $title"
    echo "  Endpoint: $endpoint"
    echo "  Suggested Agent: $suggested_agent"
    echo "  Description: $description"
    echo
    
    # Add to results file (simplified - would normally use jq)
    echo "Bug $bug_id reported: $title" >> $REPORT_DIR/bugs_$THOMAS_SESSION_ID.log
}

# Phase 1: Basic Connectivity Testing
phase1_basic_connectivity() {
    echo -e "${BLUE}=== PHASE 1: Basic Connectivity Testing ===${NC}"
    local phase_start=$(date +%s)
    local tests_passed=0
    local tests_failed=0
    
    # Test 1: Health Check
    echo "Testing health check endpoint..."
    local response=$(curl -s -w "HTTPSTATUS:%{http_code};TIME:%{time_total}" -X GET "$BASE_URL/health")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local response_time=$(echo $response | grep -o "TIME:[0-9.]*" | cut -d: -f2)
    local body=$(echo $response | sed -E 's/HTTPSTATUS:[0-9]*;TIME:[0-9.]*$//')
    
    if [ "$http_code" = "200" ]; then
        log_test "PHASE1" "Health Check" "PASS" "Health endpoint responding correctly" "$http_code" "$response_time"
        tests_passed=$((tests_passed + 1))
        
        # Check if response contains expected fields
        if echo "$body" | grep -q "status.*healthy"; then
            log_test "PHASE1" "Health Response Format" "PASS" "Response contains expected 'status: healthy'"
        else
            log_test "PHASE1" "Health Response Format" "WARN" "Response format may be incorrect"
            report_bug "low" "api_format" "Health endpoint response format issue" "Health endpoint doesn't return expected JSON format" "/health" "custodia"
        fi
    else
        log_test "PHASE1" "Health Check" "FAIL" "Health endpoint not responding correctly" "$http_code" "$response_time"
        tests_failed=$((tests_failed + 1))
        report_bug "critical" "connectivity" "Health endpoint failure" "Health check endpoint returning $http_code instead of 200" "/health" "forge"
    fi
    
    # Test 2: Root Route
    echo "Testing root route..."
    local response=$(curl -s -w "HTTPSTATUS:%{http_code};TIME:%{time_total}" -X GET "$BASE_URL/")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local response_time=$(echo $response | grep -o "TIME:[0-9.]*" | cut -d: -f2)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "302" ]; then
        log_test "PHASE1" "Root Route" "PASS" "Root route accessible" "$http_code" "$response_time"
        tests_passed=$((tests_passed + 1))
    else
        log_test "PHASE1" "Root Route" "FAIL" "Root route not accessible" "$http_code" "$response_time"
        tests_failed=$((tests_failed + 1))
        report_bug "high" "connectivity" "Root route failure" "Root route returning $http_code" "/" "forge"
    fi
    
    # Test 3: 404 Error Handling
    echo "Testing 404 error handling..."
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$BASE_URL/nonexistent-route-12345")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local body=$(echo $response | sed -E 's/HTTPSTATUS:[0-9]*$//')
    
    if [ "$http_code" = "404" ]; then
        log_test "PHASE1" "404 Error Handling" "PASS" "404 errors handled correctly" "$http_code"
        tests_passed=$((tests_passed + 1))
        
        # Check if custom 404 page is returned
        if echo "$body" | grep -q "<!DOCTYPE html>" && ! echo "$body" | grep -q "Werkzeug"; then
            log_test "PHASE1" "Custom 404 Page" "PASS" "Custom 404 page served"
        else
            log_test "PHASE1" "Custom 404 Page" "WARN" "Default error page served instead of custom"
            report_bug "medium" "ui_ux" "Missing custom 404 page" "Application serves default error page instead of custom 404 template" "/nonexistent" "hue"
        fi
    else
        log_test "PHASE1" "404 Error Handling" "FAIL" "404 errors not handled correctly" "$http_code"
        tests_failed=$((tests_failed + 1))
        report_bug "medium" "error_handling" "404 handling issue" "Non-existent routes return $http_code instead of 404" "/nonexistent" "custodia"
    fi
    
    # Test 4: Security Headers
    echo "Testing security headers..."
    local headers=$(curl -s -I "$BASE_URL/")
    local security_score=0
    local total_headers=4
    
    if echo "$headers" | grep -qi "X-Frame-Options"; then
        security_score=$((security_score + 1))
    fi
    if echo "$headers" | grep -qi "X-XSS-Protection"; then
        security_score=$((security_score + 1))
    fi
    if echo "$headers" | grep -qi "X-Content-Type-Options"; then
        security_score=$((security_score + 1))
    fi
    if echo "$headers" | grep -qi "Strict-Transport-Security"; then
        security_score=$((security_score + 1))
    fi
    
    if [ $security_score -ge 3 ]; then
        log_test "PHASE1" "Security Headers" "PASS" "$security_score/$total_headers security headers present"
        tests_passed=$((tests_passed + 1))
    elif [ $security_score -ge 2 ]; then
        log_test "PHASE1" "Security Headers" "WARN" "Only $security_score/$total_headers security headers present"
        report_bug "medium" "security" "Missing security headers" "Some security headers missing" "/" "spec"
    else
        log_test "PHASE1" "Security Headers" "FAIL" "Only $security_score/$total_headers security headers present"
        tests_failed=$((tests_failed + 1))
        report_bug "high" "security" "Critical security headers missing" "Most security headers missing" "/" "spec"
    fi
    
    local phase_end=$(date +%s)
    local phase_duration=$((phase_end - phase_start))
    
    echo -e "${BLUE}Phase 1 Complete: $tests_passed passed, $tests_failed failed (${phase_duration}s)${NC}"
    echo
}

# Phase 2: Authentication Flow Testing
phase2_authentication() {
    echo -e "${BLUE}=== PHASE 2: Authentication Flow Testing ===${NC}"
    local phase_start=$(date +%s)
    local tests_passed=0
    local tests_failed=0
    
    # Test 1: Login Page Accessibility
    echo "Testing login page accessibility..."
    local response=$(curl -s -w "HTTPSTATUS:%{http_code};TIME:%{time_total}" -c "$COOKIES_FILE" -X GET "$BASE_URL/login")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local response_time=$(echo $response | grep -o "TIME:[0-9.]*" | cut -d: -f2)
    local body=$(echo $response | sed -E 's/HTTPSTATUS:[0-9]*;TIME:[0-9.]*$//')
    
    if [ "$http_code" = "200" ]; then
        log_test "PHASE2" "Login Page Access" "PASS" "Login page accessible" "$http_code" "$response_time"
        tests_passed=$((tests_passed + 1))
        
        # Check for CSRF token
        if echo "$body" | grep -q "csrf_token\|_token"; then
            log_test "PHASE2" "CSRF Protection" "PASS" "CSRF token found in login form"
        else
            log_test "PHASE2" "CSRF Protection" "WARN" "CSRF token not detected"
            report_bug "high" "security" "Missing CSRF protection" "Login form may not have CSRF protection" "/login" "spec"
        fi
    else
        log_test "PHASE2" "Login Page Access" "FAIL" "Login page not accessible" "$http_code" "$response_time"
        tests_failed=$((tests_failed + 1))
        report_bug "critical" "authentication" "Login page inaccessible" "Login page returns $http_code" "/login" "forge"
    fi
    
    # Test 2: Invalid Login Attempt
    echo "Testing invalid login protection..."
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -b "$COOKIES_FILE" -c "$COOKIES_FILE" \
        -X POST "$BASE_URL/login" \
        -d "email=invalid@test.com&password=wrongpassword")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local body=$(echo $response | sed -E 's/HTTPSTATUS:[0-9]*$//')
    
    if [ "$http_code" = "302" ] || [ "$http_code" = "200" ]; then
        # Check if we were NOT authenticated (good)
        if echo "$body" | grep -qi "invalid\|incorrect\|error"; then
            log_test "PHASE2" "Invalid Login Protection" "PASS" "Invalid credentials rejected correctly"
            tests_passed=$((tests_passed + 1))
        else
            # Test if we can access protected content
            local dashboard_response=$(curl -s -w "HTTPSTATUS:%{http_code}" -b "$COOKIES_FILE" -X GET "$BASE_URL/dashboard/")
            local dashboard_code=$(echo $dashboard_response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
            
            if [ "$dashboard_code" = "302" ] || [ "$dashboard_code" = "401" ] || [ "$dashboard_code" = "403" ]; then
                log_test "PHASE2" "Invalid Login Protection" "PASS" "Invalid credentials properly rejected"
                tests_passed=$((tests_passed + 1))
            else
                log_test "PHASE2" "Invalid Login Protection" "FAIL" "Invalid credentials may have been accepted"
                tests_failed=$((tests_failed + 1))
                report_bug "critical" "security" "Authentication bypass possible" "Invalid credentials may provide access to protected resources" "/login" "spec"
            fi
        fi
    else
        log_test "PHASE2" "Invalid Login Protection" "FAIL" "Login endpoint error" "$http_code"
        tests_failed=$((tests_failed + 1))
        report_bug "high" "authentication" "Login endpoint error" "Login POST returns unexpected status $http_code" "/login" "custodia"
    fi
    
    # Test 3: Protected Route Access Without Auth
    echo "Testing protected route protection..."
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$BASE_URL/dashboard/")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    
    if [ "$http_code" = "302" ] || [ "$http_code" = "401" ] || [ "$http_code" = "403" ]; then
        log_test "PHASE2" "Protected Route Protection" "PASS" "Protected routes properly secured" "$http_code"
        tests_passed=$((tests_passed + 1))
    elif [ "$http_code" = "200" ]; then
        log_test "PHASE2" "Protected Route Protection" "FAIL" "Protected route accessible without authentication" "$http_code"
        tests_failed=$((tests_failed + 1))
        report_bug "critical" "security" "Authentication bypass" "Dashboard accessible without authentication" "/dashboard/" "spec"
    else
        log_test "PHASE2" "Protected Route Protection" "WARN" "Unexpected response from protected route" "$http_code"
        report_bug "medium" "authentication" "Unexpected protected route response" "Dashboard returns unexpected status $http_code" "/dashboard/" "custodia"
    fi
    
    # Test 4: Admin Route Protection
    echo "Testing admin route protection..."
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$BASE_URL/admin/users")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    
    if [ "$http_code" = "302" ] || [ "$http_code" = "401" ] || [ "$http_code" = "403" ] || [ "$http_code" = "404" ]; then
        log_test "PHASE2" "Admin Route Protection" "PASS" "Admin routes properly secured" "$http_code"
        tests_passed=$((tests_passed + 1))
    elif [ "$http_code" = "200" ]; then
        log_test "PHASE2" "Admin Route Protection" "FAIL" "Admin route accessible without authentication" "$http_code"
        tests_failed=$((tests_failed + 1))
        report_bug "critical" "security" "Admin authentication bypass" "Admin users page accessible without authentication" "/admin/users" "spec"
    else
        log_test "PHASE2" "Admin Route Protection" "WARN" "Unexpected response from admin route" "$http_code"
    fi
    
    local phase_end=$(date +%s)
    local phase_duration=$((phase_end - phase_start))
    
    echo -e "${BLUE}Phase 2 Complete: $tests_passed passed, $tests_failed failed (${phase_duration}s)${NC}"
    echo
}

# Phase 3: Core Functionality Testing (without authentication)
phase3_core_functionality() {
    echo -e "${BLUE}=== PHASE 3: Core Functionality Testing ===${NC}"
    local phase_start=$(date +%s)
    local tests_passed=0
    local tests_failed=0
    
    # Test 1: Public API Endpoints
    echo "Testing public API endpoints..."
    
    # Test prompts debug endpoint (if public)
    local response=$(curl -s -w "HTTPSTATUS:%{http_code};TIME:%{time_total}" -X GET "$BASE_URL/prompts/debug")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local response_time=$(echo $response | grep -o "TIME:[0-9.]*" | cut -d: -f2)
    
    if [ "$http_code" = "200" ]; then
        log_test "PHASE3" "Prompts Debug Endpoint" "PASS" "Debug endpoint accessible" "$http_code" "$response_time"
        tests_passed=$((tests_passed + 1))
    elif [ "$http_code" = "302" ] || [ "$http_code" = "401" ]; then
        log_test "PHASE3" "Prompts Debug Endpoint" "INFO" "Debug endpoint requires authentication (expected)" "$http_code"
    else
        log_test "PHASE3" "Prompts Debug Endpoint" "WARN" "Debug endpoint returns unexpected status" "$http_code"
    fi
    
    # Test 2: Error Handling
    echo "Testing error handling..."
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$BASE_URL/prompts/999999/view")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local body=$(echo $response | sed -E 's/HTTPSTATUS:[0-9]*$//')
    
    if [ "$http_code" = "404" ]; then
        log_test "PHASE3" "Invalid Resource Handling" "PASS" "Invalid resource returns 404" "$http_code"
        tests_passed=$((tests_passed + 1))
        
        # Check for information disclosure
        if echo "$body" | grep -qi "traceback\|error.*line\|file.*line\|exception"; then
            log_test "PHASE3" "Error Information Disclosure" "FAIL" "Error page reveals system information"
            tests_failed=$((tests_failed + 1))
            report_bug "high" "security" "Information disclosure in error pages" "Error pages reveal stack traces or system paths" "/prompts/999999/view" "spec"
        else
            log_test "PHASE3" "Error Information Disclosure" "PASS" "Error pages don't reveal system information"
        fi
    elif [ "$http_code" = "302" ] || [ "$http_code" = "401" ]; then
        log_test "PHASE3" "Invalid Resource Handling" "INFO" "Route requires authentication" "$http_code"
    else
        log_test "PHASE3" "Invalid Resource Handling" "WARN" "Unexpected response for invalid resource" "$http_code"
    fi
    
    # Test 3: Content Type Handling
    echo "Testing content type handling..."
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "Accept: application/json" -X GET "$BASE_URL/health")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local body=$(echo $response | sed -E 's/HTTPSTATUS:[0-9]*$//')
    
    if [ "$http_code" = "200" ]; then
        if echo "$body" | python3 -m json.tool >/dev/null 2>&1; then
            log_test "PHASE3" "JSON Content Type" "PASS" "Valid JSON response for health endpoint"
            tests_passed=$((tests_passed + 1))
        else
            log_test "PHASE3" "JSON Content Type" "WARN" "Health endpoint may not return valid JSON"
            report_bug "low" "api_format" "Invalid JSON response" "Health endpoint doesn't return valid JSON" "/health" "custodia"
        fi
    fi
    
    local phase_end=$(date +%s)
    local phase_duration=$((phase_end - phase_start))
    
    echo -e "${BLUE}Phase 3 Complete: $tests_passed passed, $tests_failed failed (${phase_duration}s)${NC}"
    echo
}

# Phase 4: Edge Case and Security Testing
phase4_edge_cases() {
    echo -e "${BLUE}=== PHASE 4: Edge Case and Security Testing ===${NC}"
    local phase_start=$(date +%s)
    local tests_passed=0
    local tests_failed=0
    
    # Test 1: XSS Prevention
    echo "Testing XSS prevention..."
    local xss_payload="<script>alert('xss')</script>"
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$BASE_URL/?test=$xss_payload")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local body=$(echo $response | sed -E 's/HTTPSTATUS:[0-9]*$//')
    
    if echo "$body" | grep -q "<script>alert('xss')</script>"; then
        log_test "PHASE4" "XSS Prevention" "FAIL" "XSS payload reflected without encoding" "$http_code"
        tests_failed=$((tests_failed + 1))
        report_bug "critical" "security" "XSS vulnerability" "XSS payload reflected in response" "/?test=<script>" "spec"
    else
        log_test "PHASE4" "XSS Prevention" "PASS" "XSS payload properly handled" "$http_code"
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 2: SQL Injection Prevention (if search endpoint accessible)
    echo "Testing SQL injection prevention..."
    local sql_payload="' OR '1'='1"
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$BASE_URL/prompts/api/prompts/search?q=$sql_payload")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local body=$(echo $response | sed -E 's/HTTPSTATUS:[0-9]*$//')
    
    if [ "$http_code" = "200" ]; then
        # Check for SQL error messages
        if echo "$body" | grep -qi "mysql\|postgresql\|sqlite\|syntax error\|sql"; then
            log_test "PHASE4" "SQL Injection Prevention" "FAIL" "SQL error messages detected" "$http_code"
            tests_failed=$((tests_failed + 1))
            report_bug "critical" "security" "SQL injection vulnerability" "SQL error messages indicate potential injection vulnerability" "/prompts/api/prompts/search" "spec"
        else
            log_test "PHASE4" "SQL Injection Prevention" "PASS" "No SQL error messages detected" "$http_code"
            tests_passed=$((tests_passed + 1))
        fi
    elif [ "$http_code" = "302" ] || [ "$http_code" = "401" ]; then
        log_test "PHASE4" "SQL Injection Prevention" "INFO" "Search endpoint requires authentication" "$http_code"
    else
        log_test "PHASE4" "SQL Injection Prevention" "WARN" "Search endpoint returned $http_code" "$http_code"
    fi
    
    # Test 3: Large Payload Handling
    echo "Testing large payload handling..."
    local large_payload=$(python3 -c "print('A' * 10000)")
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" --max-time 10 -X POST "$BASE_URL/" -d "data=$large_payload")
    local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    
    if [ "$http_code" = "413" ]; then
        log_test "PHASE4" "Large Payload Handling" "PASS" "Large payloads properly rejected" "$http_code"
        tests_passed=$((tests_passed + 1))
    elif [ "$http_code" = "400" ] || [ "$http_code" = "422" ]; then
        log_test "PHASE4" "Large Payload Handling" "PASS" "Large payloads handled appropriately" "$http_code"
        tests_passed=$((tests_passed + 1))
    elif [ "$http_code" = "200" ]; then
        log_test "PHASE4" "Large Payload Handling" "WARN" "Large payload accepted - check if this is intended" "$http_code"
        report_bug "medium" "performance" "Large payload acceptance" "Application accepts very large payloads without limit" "/" "probe"
    else
        log_test "PHASE4" "Large Payload Handling" "INFO" "Unexpected response to large payload" "$http_code"
    fi
    
    # Test 4: Rate Limiting
    echo "Testing rate limiting..."
    local rapid_requests=0
    local successful_requests=0
    
    for i in {1..20}; do
        local response=$(curl -s -w "HTTPSTATUS:%{http_code}" --max-time 1 -X GET "$BASE_URL/health" 2>/dev/null)
        local http_code=$(echo $response | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
        rapid_requests=$((rapid_requests + 1))
        
        if [ "$http_code" = "200" ]; then
            successful_requests=$((successful_requests + 1))
        elif [ "$http_code" = "429" ]; then
            log_test "PHASE4" "Rate Limiting" "PASS" "Rate limiting active" "$http_code"
            tests_passed=$((tests_passed + 1))
            break
        fi
    done
    
    if [ $successful_requests -eq $rapid_requests ]; then
        log_test "PHASE4" "Rate Limiting" "WARN" "No rate limiting detected - may be vulnerable to DoS"
        report_bug "medium" "performance" "No rate limiting" "Application accepts unlimited rapid requests" "/health" "probe"
    elif [ $successful_requests -lt $rapid_requests ]; then
        log_test "PHASE4" "Rate Limiting" "INFO" "Some requests failed during rapid testing - may indicate rate limiting"
    fi
    
    local phase_end=$(date +%s)
    local phase_duration=$((phase_end - phase_start))
    
    echo -e "${BLUE}Phase 4 Complete: $tests_passed passed, $tests_failed failed (${phase_duration}s)${NC}"
    echo
}

# Generate final report
generate_report() {
    echo -e "${BLUE}=== Generating Thomas Debug Report ===${NC}"
    
    local total_bugs=$(grep -c "BUG-" $REPORT_DIR/bugs_$THOMAS_SESSION_ID.log 2>/dev/null || echo "0")
    local critical_bugs=$(grep -c "Severity: critical" $REPORT_DIR/bugs_$THOMAS_SESSION_ID.log 2>/dev/null || echo "0")
    local high_bugs=$(grep -c "Severity: high" $REPORT_DIR/bugs_$THOMAS_SESSION_ID.log 2>/dev/null || echo "0")
    local medium_bugs=$(grep -c "Severity: medium" $REPORT_DIR/bugs_$THOMAS_SESSION_ID.log 2>/dev/null || echo "0")
    local low_bugs=$(grep -c "Severity: low" $REPORT_DIR/bugs_$THOMAS_SESSION_ID.log 2>/dev/null || echo "0")
    
    local report_file="$REPORT_DIR/thomas_report_$THOMAS_SESSION_ID.md"
    
    cat > $report_file << EOF
# Thomas Debug Agent Report
**Session ID:** $THOMAS_SESSION_ID  
**Timestamp:** $(date -u +%Y-%m-%dT%H:%M:%SZ)  
**Base URL:** $BASE_URL  

## Executive Summary
- **Total Bugs Found:** $total_bugs
- **Critical Issues:** $critical_bugs
- **High Priority Issues:** $high_bugs
- **Medium Priority Issues:** $medium_bugs
- **Low Priority Issues:** $low_bugs

## Test Results by Phase
### Phase 1: Basic Connectivity
✅ Health endpoint functionality  
✅ Root route accessibility  
✅ Error handling (404s)  
✅ Security headers validation  

### Phase 2: Authentication Security
✅ Login page accessibility  
✅ Invalid credential rejection  
✅ Protected route security  
✅ Admin route protection  

### Phase 3: Core Functionality
✅ API endpoint responses  
✅ Error information disclosure  
✅ Content type handling  

### Phase 4: Security & Edge Cases
✅ XSS prevention testing  
✅ SQL injection prevention  
✅ Large payload handling  
✅ Rate limiting validation  

## Bug Details
EOF
    
    if [ -f "$REPORT_DIR/bugs_$THOMAS_SESSION_ID.log" ]; then
        echo "" >> $report_file
        cat $REPORT_DIR/bugs_$THOMAS_SESSION_ID.log >> $report_file
    else
        echo "No bugs found during testing." >> $report_file
    fi
    
    cat >> $report_file << EOF

## Recommendations
$(if [ $critical_bugs -gt 0 ]; then echo "🚨 **IMMEDIATE ACTION REQUIRED:** $critical_bugs critical security issues found"; fi)
$(if [ $high_bugs -gt 0 ]; then echo "⚠️ **HIGH PRIORITY:** $high_bugs high-priority issues need attention"; fi)
$(if [ $medium_bugs -gt 0 ]; then echo "📋 **MEDIUM PRIORITY:** $medium_bugs medium-priority issues for next sprint"; fi)
$(if [ $low_bugs -gt 0 ]; then echo "📝 **LOW PRIORITY:** $low_bugs low-priority improvements identified"; fi)

## Next Actions
1. Review and assign critical/high priority bugs to appropriate agents
2. Schedule follow-up testing after fixes are implemented
3. Consider implementing automated monitoring for detected issues
4. Update security controls based on findings

---
*Report generated by Thomas Debug Agent*
EOF
    
    echo "Report generated: $report_file"
    echo -e "${GREEN}Thomas testing session complete!${NC}"
    
    # Clean up
    rm -f "$COOKIES_FILE"
}

# Main execution
main() {
    initialize_thomas
    phase1_basic_connectivity
    phase2_authentication
    phase3_core_functionality
    phase4_edge_cases
    generate_report
}

# Check if script is run directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi