#!/usr/bin/env python3
"""
Vertigo Debug Toolkit - Comprehensive Stress Testing Suite
By Probe - Merge's System Testing Expert

This script performs systematic stress testing of the Vertigo Debug Toolkit
to identify performance bottlenecks, security vulnerabilities, and edge case failures.
"""

import asyncio
import aiohttp
import requests
import time
import json
import sys
import threading
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import csv
from datetime import datetime
import os

class VertigoStressTester:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.results = []
        self.errors = []
        self.session = requests.Session()
        self.csrf_token = None
        self.authenticated = False
        
    def log_result(self, test_name, success, response_time, status_code=None, error=None):
        """Log test result with timestamp and metrics."""
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'success': success,
            'response_time_ms': round(response_time * 1000, 2),
            'status_code': status_code,
            'error': str(error) if error else None
        }
        self.results.append(result)
        
        if not success:
            self.errors.append(result)
            
        # Real-time logging
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {result['response_time_ms']}ms (HTTP {status_code})")
        if error:
            print(f"   Error: {error}")

    def get_csrf_token(self):
        """Extract CSRF token from login page."""
        try:
            response = self.session.get(urljoin(self.base_url, "/login"))
            # Look for CSRF token in the HTML
            if 'csrf_token' in response.text:
                # Simple extraction - in real scenario would use BeautifulSoup
                import re
                match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
                if match:
                    self.csrf_token = match.group(1)
                    return True
        except Exception as e:
            print(f"Failed to get CSRF token: {e}")
        return False

    def attempt_login(self, email="admin@example.com", password="admin123"):
        """Attempt to login and maintain session."""
        try:
            if not self.get_csrf_token():
                print("Warning: Could not extract CSRF token")
            
            login_data = {
                'email': email,
                'password': password,
            }
            
            if self.csrf_token:
                login_data['csrf_token'] = self.csrf_token
            
            response = self.session.post(
                urljoin(self.base_url, "/login"),
                data=login_data,
                allow_redirects=False
            )
            
            # Check for successful login (redirect or success status)
            if response.status_code in [200, 302]:
                self.authenticated = True
                print("✓ Successfully authenticated")
                return True
            else:
                print(f"✗ Login failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Login error: {e}")
            return False

    # PERFORMANCE STRESS TESTS
    
    def test_concurrent_requests(self, num_requests=20, endpoint="/health"):
        """Test system under concurrent load."""
        print(f"\n🔥 CONCURRENT LOAD TEST: {num_requests} simultaneous requests to {endpoint}")
        
        def make_request():
            start_time = time.time()
            try:
                response = requests.get(urljoin(self.base_url, endpoint), timeout=10)
                response_time = time.time() - start_time
                return {
                    'success': True,
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'error': None
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    'success': False,
                    'response_time': response_time,
                    'status_code': None,
                    'error': str(e)
                }
        
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                self.log_result(
                    f"Concurrent_{i+1}",
                    result['success'],
                    result['response_time'],
                    result['status_code'],
                    result['error']
                )

    def test_large_payload(self):
        """Test handling of large payloads."""
        print(f"\n💥 LARGE PAYLOAD TEST")
        
        # Generate large JSON payload (1MB)
        large_data = {
            'large_field': 'x' * (1024 * 1024),  # 1MB string
            'array_field': ['item'] * 10000,
            'nested': {'deep': {'very': {'nested': 'data' * 1000}}}
        }
        
        start_time = time.time()
        try:
            response = requests.post(
                urljoin(self.base_url, "/api/simulate/workflow"),
                json=large_data,
                timeout=30
            )
            response_time = time.time() - start_time
            self.log_result("Large_Payload", True, response_time, response.status_code)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("Large_Payload", False, response_time, None, e)

    def test_rapid_fire_requests(self, count=100):
        """Test rapid succession of requests."""
        print(f"\n⚡ RAPID FIRE TEST: {count} requests in quick succession")
        
        start_total = time.time()
        for i in range(count):
            start_time = time.time()
            try:
                response = requests.get(urljoin(self.base_url, "/health"), timeout=5)
                response_time = time.time() - start_time
                self.log_result(f"RapidFire_{i+1}", True, response_time, response.status_code)
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(f"RapidFire_{i+1}", False, response_time, None, e)
                
            # Minimal delay to prevent overwhelming
            time.sleep(0.01)
        
        total_time = time.time() - start_total
        print(f"Total rapid fire time: {total_time:.2f}s ({count/total_time:.1f} req/s)")

    # SECURITY EDGE CASES
    
    def test_sql_injection_attempts(self):
        """Test SQL injection vulnerabilities."""
        print(f"\n🔓 SQL INJECTION TESTS")
        
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1#",
            "1'; EXEC sp_msforeachtable 'DROP TABLE ?'; --"
        ]
        
        for i, payload in enumerate(sql_payloads):
            # Test login form
            start_time = time.time()
            try:
                response = self.session.post(
                    urljoin(self.base_url, "/login"),
                    data={'email': payload, 'password': 'test'},
                    timeout=10
                )
                response_time = time.time() - start_time
                
                # Check if we get database errors or unexpected responses
                success = response.status_code not in [500] and 'sql' not in response.text.lower()
                self.log_result(f"SQLInject_Login_{i+1}", success, response_time, response.status_code,
                              None if success else "Potential SQL injection vulnerability")
                
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(f"SQLInject_Login_{i+1}", False, response_time, None, e)

    def test_xss_attempts(self):
        """Test XSS vulnerabilities."""
        print(f"\n🔓 XSS INJECTION TESTS")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//",
            "<svg onload=alert('XSS')>",
            "<%2Fscript%3E%3Cscript%3Ealert%28%27XSS%27%29%3C%2Fscript%3E"
        ]
        
        for i, payload in enumerate(xss_payloads):
            start_time = time.time()
            try:
                # Test in login form
                response = self.session.post(
                    urljoin(self.base_url, "/login"),
                    data={'email': payload, 'password': 'test'},
                    timeout=10
                )
                response_time = time.time() - start_time
                
                # Check if payload appears unescaped in response
                success = payload not in response.text or 'alert(' not in response.text
                self.log_result(f"XSS_Test_{i+1}", success, response_time, response.status_code,
                              None if success else "Potential XSS vulnerability detected")
                
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(f"XSS_Test_{i+1}", False, response_time, None, e)

    def test_authentication_bypass(self):
        """Test authentication bypass attempts."""
        print(f"\n🔓 AUTHENTICATION BYPASS TESTS")
        
        # Test protected endpoints without authentication
        protected_endpoints = [
            "/dashboard",
            "/prompts",
            "/performance",
            "/costs",
            "/api/vertigo/status",
            "/api/simulate/workflow"
        ]
        
        # Create new session without authentication
        unauth_session = requests.Session()
        
        for endpoint in protected_endpoints:
            start_time = time.time()
            try:
                response = unauth_session.get(urljoin(self.base_url, endpoint), timeout=10)
                response_time = time.time() - start_time
                
                # Should get 401/403 or redirect to login
                success = response.status_code in [401, 403, 302] or 'login' in response.url.lower()
                self.log_result(f"AuthBypass_{endpoint.replace('/', '_')}", success, response_time, 
                              response.status_code, None if success else "Authentication bypass detected")
                
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(f"AuthBypass_{endpoint.replace('/', '_')}", False, response_time, None, e)

    def test_csrf_protection(self):
        """Test CSRF protection."""
        print(f"\n🔓 CSRF PROTECTION TESTS")
        
        if not self.authenticated:
            print("Skipping CSRF tests - not authenticated")
            return
            
        # Try to make state-changing requests without CSRF token
        start_time = time.time()
        try:
            # Create new session with cookies but no CSRF token
            csrf_session = requests.Session()
            csrf_session.cookies.update(self.session.cookies)
            
            response = csrf_session.post(
                urljoin(self.base_url, "/profile/edit"),
                data={'username': 'hacker', 'email': 'hacker@evil.com'},
                timeout=10
            )
            response_time = time.time() - start_time
            
            # Should be rejected due to missing CSRF token
            success = response.status_code in [400, 403, 422] or 'csrf' in response.text.lower()
            self.log_result("CSRF_Protection", success, response_time, response.status_code,
                          None if success else "CSRF protection may be insufficient")
            
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("CSRF_Protection", False, response_time, None, e)

    # API BOUNDARY TESTS
    
    def test_malformed_json(self):
        """Test handling of malformed JSON payloads."""
        print(f"\n🔧 MALFORMED JSON TESTS")
        
        malformed_payloads = [
            '{"incomplete": json',
            '{"numbers": 123abc}',
            '{"unicode": "\\uXXXX"}',
            '{"nested": {"unclosed": {"object": "value"}',
            '{"array": [1,2,3,}',
            '{"control_chars": "\\x00\\x01\\x02"}'
        ]
        
        for i, payload in enumerate(malformed_payloads):
            start_time = time.time()
            try:
                response = requests.post(
                    urljoin(self.base_url, "/api/simulate/workflow"),
                    data=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                response_time = time.time() - start_time
                
                # Should handle gracefully with 400 Bad Request
                success = response.status_code == 400
                self.log_result(f"MalformedJSON_{i+1}", success, response_time, response.status_code,
                              None if success else "Poor error handling for malformed JSON")
                
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(f"MalformedJSON_{i+1}", False, response_time, None, e)

    def test_unicode_edge_cases(self):
        """Test Unicode and special character handling."""
        print(f"\n🔧 UNICODE EDGE CASE TESTS")
        
        unicode_payloads = [
            {"test": "🚀💻🔥"},  # Emojis
            {"test": "测试中文"},  # Chinese characters
            {"test": "тест русский"},  # Cyrillic
            {"test": "🏴‍☠️🇺🇸🇪🇺"},  # Complex emoji sequences
            {"test": "\x00\x01\x02"},  # Control characters
            {"test": "A" * 10000},  # Very long string
            {"test": "\\n\\r\\t\\\\"},  # Escape sequences
        ]
        
        for i, payload in enumerate(unicode_payloads):
            start_time = time.time()
            try:
                response = requests.post(
                    urljoin(self.base_url, "/api/simulate/workflow"),
                    json=payload,
                    timeout=10
                )
                response_time = time.time() - start_time
                self.log_result(f"Unicode_{i+1}", True, response_time, response.status_code)
                
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(f"Unicode_{i+1}", False, response_time, None, e)

    def test_parameter_boundary_values(self):
        """Test extreme parameter values."""
        print(f"\n🔧 PARAMETER BOUNDARY TESTS")
        
        boundary_tests = [
            {"id": -1},  # Negative ID
            {"id": 0},   # Zero ID
            {"id": 999999999},  # Very large ID
            {"limit": -1},  # Negative limit
            {"limit": 999999},  # Excessive limit
            {"offset": -1},  # Negative offset
            {"page": 0},  # Zero page
            {"size": -1},  # Negative size
        ]
        
        for i, params in enumerate(boundary_tests):
            start_time = time.time()
            try:
                response = requests.get(
                    urljoin(self.base_url, "/api/vertigo/status"),
                    params=params,
                    timeout=10
                )
                response_time = time.time() - start_time
                
                # Should handle gracefully
                success = response.status_code in [200, 400, 422]
                self.log_result(f"Boundary_{i+1}", success, response_time, response.status_code,
                              None if success else "Poor boundary value handling")
                
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(f"Boundary_{i+1}", False, response_time, None, e)

    # SYSTEM RESOURCE TESTS
    
    def test_memory_exhaustion(self):
        """Test memory usage patterns."""
        print(f"\n💾 MEMORY EXHAUSTION TESTS")
        
        # Create progressively larger payloads
        sizes = [1024, 10240, 102400, 1048576]  # 1KB, 10KB, 100KB, 1MB
        
        for size in sizes:
            large_string = "x" * size
            start_time = time.time()
            try:
                response = requests.post(
                    urljoin(self.base_url, "/api/simulate/workflow"),
                    json={"large_data": large_string},
                    timeout=30
                )
                response_time = time.time() - start_time
                self.log_result(f"Memory_{size//1024}KB", True, response_time, response.status_code)
                
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(f"Memory_{size//1024}KB", False, response_time, None, e)

    def test_session_limits(self):
        """Test session handling under stress."""
        print(f"\n🔐 SESSION STRESS TESTS")
        
        # Create multiple sessions simultaneously
        sessions = []
        for i in range(10):
            session = requests.Session()
            start_time = time.time()
            try:
                response = session.get(urljoin(self.base_url, "/health"), timeout=10)
                response_time = time.time() - start_time
                self.log_result(f"Session_{i+1}", True, response_time, response.status_code)
                sessions.append(session)
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(f"Session_{i+1}", False, response_time, None, e)

    def run_all_tests(self):
        """Run the complete stress test suite."""
        print("🎯 VERTIGO DEBUG TOOLKIT - COMPREHENSIVE STRESS TEST SUITE")
        print("=" * 60)
        
        start_time = time.time()
        
        # Attempt authentication first
        print("\n🔐 AUTHENTICATION SETUP")
        self.attempt_login()
        
        # Performance Tests
        print("\n" + "="*60)
        print("PERFORMANCE STRESS TESTS")
        print("="*60)
        
        self.test_concurrent_requests(20, "/health")
        self.test_concurrent_requests(15, "/")
        self.test_rapid_fire_requests(50)
        self.test_large_payload()
        self.test_memory_exhaustion()
        
        # Security Tests
        print("\n" + "="*60)
        print("SECURITY EDGE CASE TESTS")
        print("="*60)
        
        self.test_sql_injection_attempts()
        self.test_xss_attempts()
        self.test_authentication_bypass()
        self.test_csrf_protection()
        
        # Boundary Tests  
        print("\n" + "="*60)
        print("API BOUNDARY TESTS")
        print("="*60)
        
        self.test_malformed_json()
        self.test_unicode_edge_cases()
        self.test_parameter_boundary_values()
        
        # Resource Tests
        print("\n" + "="*60)
        print("SYSTEM RESOURCE TESTS")
        print("="*60)
        
        self.test_session_limits()
        
        total_time = time.time() - start_time
        
        # Generate summary report
        self.generate_report(total_time)

    def generate_report(self, total_time):
        """Generate comprehensive test report."""
        print("\n" + "="*60)
        print("TEST EXECUTION SUMMARY")
        print("="*60)
        
        total_tests = len(self.results)
        failed_tests = len(self.errors)
        success_rate = ((total_tests - failed_tests) / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate response time statistics
        response_times = [r['response_time_ms'] for r in self.results if r['success']]
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            max_response = max(response_times)
            min_response = min(response_times)
        else:
            avg_response = max_response = min_response = 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_tests - failed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Execution Time: {total_time:.2f}s")
        print(f"Average Response Time: {avg_response:.1f}ms")
        print(f"Max Response Time: {max_response:.1f}ms")
        print(f"Min Response Time: {min_response:.1f}ms")
        
        # Highlight critical failures
        if self.errors:
            print(f"\n⚠️  CRITICAL ISSUES DETECTED:")
            for error in self.errors:
                if 'vulnerability' in str(error.get('error', '')) or 'bypass' in str(error.get('error', '')):
                    print(f"   🚨 SECURITY: {error['test_name']} - {error['error']}")
                elif error['response_time_ms'] > 5000:
                    print(f"   🐌 PERFORMANCE: {error['test_name']} - {error['response_time_ms']}ms")
                else:
                    print(f"   ❌ ERROR: {error['test_name']} - {error['error']}")
        
        # Save detailed results to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vertigo_stress_test_results_{timestamp}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'test_name', 'success', 'response_time_ms', 'status_code', 'error']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"\n📊 Detailed results saved to: {filename}")
        
        # Performance recommendations
        slow_tests = [r for r in self.results if r['response_time_ms'] > 1000]
        if slow_tests:
            print(f"\n🐌 PERFORMANCE CONCERNS ({len(slow_tests)} tests > 1000ms):")
            for test in sorted(slow_tests, key=lambda x: x['response_time_ms'], reverse=True)[:5]:
                print(f"   {test['test_name']}: {test['response_time_ms']}ms")

if __name__ == "__main__":
    tester = VertigoStressTester()
    tester.run_all_tests()