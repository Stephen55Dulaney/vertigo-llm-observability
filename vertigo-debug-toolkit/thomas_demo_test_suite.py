#!/usr/bin/env python3
"""
Thomas Demo Test Suite for Vertigo Debug Toolkit
Comprehensive testing for 9 AM presentation demo flow

Tests the complete demo flow to ensure professional presentation quality:
1. Landing Page → Professional first impression
2. Login Flow → Smooth authentication
3. Dashboard → Key metrics and overview display
4. Prompts Management → Show prompt library and testing
5. Performance Monitoring → Demonstrate observability
6. User Experience → Navigation, forms, and interactions

Focus on demo-critical issues that would disrupt presentation.
"""

import requests
import time
import json
from datetime import datetime
from bs4 import BeautifulSoup
import sys
import os

class DemoTestResults:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        
    def add_result(self, step, status, load_time, notes, issues=None):
        self.results.append({
            'step': step,
            'status': status,
            'load_time': load_time,
            'notes': notes,
            'issues': issues or [],
            'timestamp': datetime.now()
        })
        
    def print_summary(self):
        print("\n" + "="*80)
        print("🎯 VERTIGO DEBUG TOOLKIT - DEMO READINESS REPORT")
        print("="*80)
        print(f"📅 Test Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎬 Demo Target: 9 AM Business Presentation")
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == '✅'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed")
        
        if failed_tests == 0:
            print("🎉 DEMO READY! All tests passed - system looks professional and polished.")
        else:
            print(f"⚠️  DEMO CONCERNS: {failed_tests} issues found that could disrupt presentation")
            
        print("\n" + "="*80)
        print("📋 DETAILED TEST RESULTS")
        print("="*80)
        
        demo_critical_issues = []
        
        for result in self.results:
            print(f"\n{result['status']} {result['step']}")
            print(f"   ⏱️  Load Time: {result['load_time']:.2f}s")
            print(f"   📝 Notes: {result['notes']}")
            
            if result['load_time'] > 2.0:
                demo_critical_issues.append(f"SLOW LOAD: {result['step']} took {result['load_time']:.2f}s (>2s)")
                
            if result['issues']:
                for issue in result['issues']:
                    print(f"   🚨 ISSUE: {issue}")
                    demo_critical_issues.append(f"{result['step']}: {issue}")
                    
        # Professional appearance assessment
        print("\n" + "="*80)
        print("🎨 PROFESSIONAL APPEARANCE ASSESSMENT")
        print("="*80)
        
        appearance_score = self._calculate_appearance_score()
        
        if appearance_score >= 90:
            print("🌟 EXCELLENT: System looks very professional and demo-ready")
        elif appearance_score >= 75:
            print("✅ GOOD: System looks professional with minor polish needed")
        elif appearance_score >= 60:
            print("⚠️  OK: System functional but needs improvement for professional demo")
        else:
            print("❌ POOR: System has significant issues that would embarrass in demo")
            
        print(f"Professional Appearance Score: {appearance_score}/100")
        
        # Demo-critical issues summary
        if demo_critical_issues:
            print("\n" + "="*80)
            print("🚨 DEMO-CRITICAL ISSUES (Fix before presentation!)")
            print("="*80)
            
            for i, issue in enumerate(demo_critical_issues, 1):
                print(f"{i}. {issue}")
                
        # Final recommendation
        print("\n" + "="*80)
        print("🎯 FINAL DEMO RECOMMENDATION")
        print("="*80)
        
        if failed_tests == 0 and len(demo_critical_issues) == 0:
            print("🎉 GO FOR DEMO! System is ready for professional presentation.")
            print("✅ All critical functionality works smoothly")
            print("✅ Load times are acceptable")
            print("✅ No embarrassing bugs detected")
            print("✅ Professional appearance maintained throughout")
        elif len(demo_critical_issues) <= 2:
            print("⚠️  PROCEED WITH CAUTION - Minor issues to address:")
            print("   • Test the specific demo path one more time")
            print("   • Have backup plan for any slow-loading sections")
            print("   • Practice transitions between sections")
        else:
            print("❌ DELAY DEMO - Too many critical issues:")
            print("   • Fix critical functionality issues first")
            print("   • Optimize slow-loading pages")
            print("   • Test again after fixes")
            
    def _calculate_appearance_score(self):
        """Calculate professional appearance score based on test results"""
        base_score = 100
        
        # Deduct points for failures
        failed_tests = len([r for r in self.results if r['status'] == '❌'])
        base_score -= (failed_tests * 15)
        
        # Deduct points for slow load times
        slow_tests = len([r for r in self.results if r['load_time'] > 2.0])
        base_score -= (slow_tests * 10)
        
        # Deduct points for issues
        total_issues = sum(len(r['issues']) for r in self.results)
        base_score -= (total_issues * 5)
        
        return max(0, base_score)

class ThomasDemoTester:
    def __init__(self, base_url='http://127.0.0.1:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = DemoTestResults()
        
    def test_landing_page(self):
        """Test 1: Landing Page - Professional first impression"""
        print("\n🏠 Testing Landing Page...")
        
        start_time = time.time()
        try:
            response = self.session.get(f'{self.base_url}/', timeout=10)
            load_time = time.time() - start_time
            
            issues = []
            
            # Check response
            if response.status_code != 200:
                issues.append(f"HTTP {response.status_code} instead of 200")
            
            # Check load time
            if load_time > 2.0:
                issues.append(f"Slow load time: {load_time:.2f}s (target: <2s)")
                
            # Check content quality
            if 'Vertigo' not in response.text:
                issues.append("Missing Vertigo branding")
                
            if 'Debug Toolkit' not in response.text:
                issues.append("Missing main product name")
                
            # Check for professional styling
            soup = BeautifulSoup(response.text, 'html.parser')
            if not soup.find('link', {'rel': 'stylesheet'}):
                issues.append("No CSS stylesheets detected")
                
            status = '✅' if not issues else '❌'
            notes = "Professional landing page loads cleanly" if not issues else "Landing page has styling/content issues"
            
        except Exception as e:
            load_time = time.time() - start_time
            status = '❌'
            notes = f"Failed to load: {str(e)}"
            issues = [f"Connection error: {str(e)}"]
            
        self.results.add_result("Landing Page", status, load_time, notes, issues)
        
    def test_login_flow(self):
        """Test 2: Login Flow - Smooth authentication"""
        print("\n🔐 Testing Login Flow...")
        
        # Test login page load
        start_time = time.time()
        try:
            response = self.session.get(f'{self.base_url}/login', timeout=10)
            load_time = time.time() - start_time
            
            issues = []
            
            if response.status_code != 200:
                issues.append(f"Login page HTTP {response.status_code}")
                
            if load_time > 2.0:
                issues.append(f"Login page slow: {load_time:.2f}s")
                
            # Extract CSRF token
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = soup.find('input', {'name': 'csrf_token'})
            
            if not csrf_token:
                issues.append("No CSRF token found in login form")
                
            # Test actual login
            if csrf_token:
                login_start = time.time()
                login_data = {
                    'csrf_token': csrf_token['value'],
                    'email': 'admin@vertigo.com',
                    'password': 'SecureTest123!',
                    'remember': 'on'
                }
                
                login_response = self.session.post(f'{self.base_url}/login', 
                                                 data=login_data, 
                                                 allow_redirects=False,
                                                 timeout=10)
                login_time = time.time() - login_start
                
                if login_response.status_code != 302:
                    issues.append(f"Login failed: HTTP {login_response.status_code}")
                    
                if login_time > 3.0:
                    issues.append(f"Login process slow: {login_time:.2f}s")
                    
                # Check redirect location
                if login_response.status_code == 302:
                    redirect_location = login_response.headers.get('Location', '')
                    if 'dashboard' not in redirect_location.lower():
                        issues.append("Login doesn't redirect to dashboard")
                        
            total_time = time.time() - start_time
            status = '✅' if not issues else '❌'
            notes = "Authentication flows smoothly" if not issues else "Login has UX or performance issues"
            
        except Exception as e:
            total_time = time.time() - start_time
            status = '❌'
            notes = f"Login flow failed: {str(e)}"
            issues = [f"Login error: {str(e)}"]
            
        self.results.add_result("Login Flow", status, total_time, notes, issues)
        
    def test_dashboard(self):
        """Test 3: Dashboard - Key metrics and overview display"""
        print("\n📊 Testing Dashboard...")
        
        start_time = time.time()
        try:
            response = self.session.get(f'{self.base_url}/dashboard/', timeout=15)
            load_time = time.time() - start_time
            
            issues = []
            
            if response.status_code != 200:
                issues.append(f"Dashboard HTTP {response.status_code}")
                
            if load_time > 3.0:  # Dashboard can be slower due to data
                issues.append(f"Dashboard very slow: {load_time:.2f}s")
                
            # Check for key dashboard elements
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for dashboard indicators
            if 'dashboard' not in response.text.lower():
                issues.append("Missing dashboard indicators")
                
            # Check for charts/metrics
            if not (soup.find('script') and ('chart' in response.text.lower() or 'metric' in response.text.lower())):
                issues.append("No charts or metrics detected")
                
            # Check for professional layout
            if not soup.find('div', class_=lambda x: x and any(word in x.lower() for word in ['card', 'panel', 'widget', 'metric'])):
                issues.append("No professional dashboard widgets found")
                
            status = '✅' if not issues else '❌'
            notes = "Dashboard displays metrics professionally" if not issues else "Dashboard missing key elements or slow"
            
        except Exception as e:
            load_time = time.time() - start_time
            status = '❌'
            notes = f"Dashboard failed to load: {str(e)}"
            issues = [f"Dashboard error: {str(e)}"]
            
        self.results.add_result("Dashboard", status, load_time, notes, issues)
        
    def test_prompts_management(self):
        """Test 4: Prompts Management - Show prompt library"""
        print("\n📝 Testing Prompts Management...")
        
        start_time = time.time()
        try:
            response = self.session.get(f'{self.base_url}/prompts/', timeout=10)
            load_time = time.time() - start_time
            
            issues = []
            
            if response.status_code != 200:
                issues.append(f"Prompts page HTTP {response.status_code}")
                
            if load_time > 2.0:
                issues.append(f"Prompts page slow: {load_time:.2f}s")
                
            # Check for prompt management features
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if 'prompt' not in response.text.lower():
                issues.append("No prompt-related content detected")
                
            # Look for management actions
            has_add_button = soup.find('a', string=lambda x: x and 'add' in x.lower()) or \
                           soup.find('button', string=lambda x: x and 'add' in x.lower())
            
            if not has_add_button:
                issues.append("No 'Add Prompt' functionality visible")
                
            # Test prompt testing interface (if prompts exist)
            try:
                test_response = self.session.get(f'{self.base_url}/prompts/1/test', timeout=5)
                if test_response.status_code == 200:
                    if 'test' not in test_response.text.lower():
                        issues.append("Prompt testing interface missing test elements")
                        
            except:
                # It's okay if specific prompt doesn't exist
                pass
                
            status = '✅' if not issues else '❌'
            notes = "Prompt library displays and functions well" if not issues else "Prompt management has usability issues"
            
        except Exception as e:
            load_time = time.time() - start_time
            status = '❌'
            notes = f"Prompts management failed: {str(e)}"
            issues = [f"Prompts error: {str(e)}"]
            
        self.results.add_result("Prompts Management", status, load_time, notes, issues)
        
    def test_performance_monitoring(self):
        """Test 5: Performance Monitoring - Demonstrate observability"""
        print("\n⚡ Testing Performance Monitoring...")
        
        start_time = time.time()
        try:
            response = self.session.get(f'{self.base_url}/performance/', timeout=10)
            load_time = time.time() - start_time
            
            issues = []
            
            if response.status_code != 200:
                issues.append(f"Performance page HTTP {response.status_code}")
                
            if load_time > 2.5:
                issues.append(f"Performance page slow: {load_time:.2f}s")
                
            # Check for monitoring elements
            soup = BeautifulSoup(response.text, 'html.parser')
            
            performance_keywords = ['performance', 'monitoring', 'metrics', 'trace', 'latency']
            if not any(keyword in response.text.lower() for keyword in performance_keywords):
                issues.append("No performance monitoring indicators found")
                
            # Look for charts or metrics
            if not (soup.find('canvas') or soup.find('script') and 'chart' in response.text.lower()):
                issues.append("No performance charts or visualizations detected")
                
            status = '✅' if not issues else '❌'
            notes = "Performance monitoring shows observability features" if not issues else "Performance monitoring lacks key features"
            
        except Exception as e:
            load_time = time.time() - start_time
            status = '❌'
            notes = f"Performance monitoring failed: {str(e)}"
            issues = [f"Performance error: {str(e)}"]
            
        self.results.add_result("Performance Monitoring", status, load_time, notes, issues)
        
    def test_navigation_ux(self):
        """Test 6: User Experience - Navigation and interactions"""
        print("\n🧭 Testing Navigation & UX...")
        
        start_time = time.time()
        issues = []
        
        # Test key navigation paths
        nav_tests = [
            ('/dashboard/', 'Dashboard navigation'),
            ('/prompts/', 'Prompts navigation'),
            ('/performance/', 'Performance navigation'),
            ('/costs/', 'Costs navigation')
        ]
        
        for path, description in nav_tests:
            try:
                nav_start = time.time()
                response = self.session.get(f'{self.base_url}{path}', timeout=5)
                nav_time = time.time() - nav_start
                
                if response.status_code != 200:
                    issues.append(f"{description} returns HTTP {response.status_code}")
                    
                if nav_time > 2.0:
                    issues.append(f"{description} slow: {nav_time:.2f}s")
                    
            except Exception as e:
                issues.append(f"{description} failed: {str(e)}")
                
        # Test error handling
        try:
            error_response = self.session.get(f'{self.base_url}/nonexistent-page', timeout=5)
            if error_response.status_code == 404:
                # Check if custom 404 page exists
                soup = BeautifulSoup(error_response.text, 'html.parser')
                if 'werkzeug' in error_response.text.lower():
                    issues.append("Shows default Flask error page instead of custom 404")
            else:
                issues.append(f"404 test returned unexpected status: {error_response.status_code}")
                
        except Exception as e:
            issues.append(f"Error page test failed: {str(e)}")
            
        # Test API endpoints
        api_tests = [
            ('/health', 'Health check API'),
            ('/api/vertigo/status', 'Vertigo status API')
        ]
        
        for path, description in api_tests:
            try:
                api_response = self.session.get(f'{self.base_url}{path}', timeout=5)
                if api_response.status_code != 200:
                    issues.append(f"{description} returns HTTP {api_response.status_code}")
                    
            except Exception as e:
                issues.append(f"{description} failed: {str(e)}")
                
        total_time = time.time() - start_time
        status = '✅' if not issues else '❌'
        notes = "Navigation flows smoothly between sections" if not issues else "Navigation has usability or performance issues"
        
        self.results.add_result("Navigation & UX", status, total_time, notes, issues)
        
    def test_server_availability(self):
        """Pre-test: Check if server is running"""
        print("🔍 Checking server availability...")
        
        try:
            response = self.session.get(f'{self.base_url}/health', timeout=5)
            if response.status_code == 200:
                print(f"✅ Server is running at {self.base_url}")
                return True
            else:
                print(f"❌ Server responded with HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Server not accessible: {str(e)}")
            print("\n💡 To start the server:")
            print(f"   cd {os.path.dirname(os.path.abspath(__file__))}")
            print("   python app.py --port 5000")
            print("\nThen run this test again.")
            return False
            
    def run_complete_demo_test(self):
        """Run the complete demo test suite"""
        print("🎬 VERTIGO DEBUG TOOLKIT - DEMO READINESS TEST")
        print("="*60)
        print("Testing system for 9 AM business presentation...")
        
        # Check server availability first
        if not self.test_server_availability():
            return False
            
        # Run all demo tests
        self.test_landing_page()
        self.test_login_flow()
        self.test_dashboard()
        self.test_prompts_management()
        self.test_performance_monitoring()
        self.test_navigation_ux()
        
        # Print comprehensive results
        self.results.print_summary()
        
        return True

def main():
    """Main execution function"""
    
    # Default to port 5000, but allow override
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Usage: python thomas_demo_test_suite.py [port]")
            sys.exit(1)
            
    base_url = f'http://127.0.0.1:{port}'
    
    tester = ThomasDemoTester(base_url)
    success = tester.run_complete_demo_test()
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()