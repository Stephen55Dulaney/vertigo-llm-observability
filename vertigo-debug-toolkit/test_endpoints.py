#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

def test_endpoint(session, endpoint, description):
    """Test an endpoint and return status info."""
    try:
        response = session.get(f'http://127.0.0.1:8080{endpoint}', allow_redirects=False)
        return {
            'endpoint': endpoint,
            'description': description,
            'status': response.status_code,
            'redirect': response.headers.get('Location', 'N/A'),
            'success': response.status_code == 200
        }
    except Exception as e:
        return {
            'endpoint': endpoint,
            'description': description,
            'status': 'ERROR',
            'redirect': str(e),
            'success': False
        }

# Create session and login
session = requests.Session()

# Get login page and extract CSRF token
login_page = session.get('http://127.0.0.1:8080/login')
soup = BeautifulSoup(login_page.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

# Login
login_data = {
    'csrf_token': csrf_token,
    'email': 'admin@vertigo.com',
    'password': 'SecureTest123!',
    'remember': 'on'
}

login_response = session.post('http://127.0.0.1:8080/login', data=login_data, allow_redirects=False)
print(f"Login Status: {login_response.status_code}")

if login_response.status_code == 302:
    print("✓ Authentication successful")
    
    # Test endpoints
    endpoints = [
        ('/dashboard/', 'Main Dashboard'),
        ('/prompts/', 'Prompt Management'),
        ('/performance/', 'Performance Monitoring'),
        ('/costs/', 'Cost Tracking'),
        ('/api/vertigo/status', 'Vertigo Status API'),
        ('/api/simulate/workflow', 'Workflow Simulation API'),
        ('/health', 'Health Check'),
        ('/nonexistent', '404 Test')
    ]
    
    print("\n=== ENDPOINT TESTING RESULTS ===")
    for endpoint, description in endpoints:
        result = test_endpoint(session, endpoint, description)
        status_icon = "✓" if result['success'] else "✗"
        print(f"{status_icon} {result['endpoint']} ({result['description']}): {result['status']}")
        if result['redirect'] != 'N/A':
            print(f"  → Redirect: {result['redirect']}")
            
else:
    print("✗ Authentication failed")
    print(login_response.text[:500])