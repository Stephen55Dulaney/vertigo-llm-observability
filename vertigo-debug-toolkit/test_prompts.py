#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json

# Create session and login
session = requests.Session()

# Login first
login_page = session.get('http://127.0.0.1:8080/login')
soup = BeautifulSoup(login_page.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

login_data = {
    'csrf_token': csrf_token,
    'email': 'admin@vertigo.com',
    'password': 'SecureTest123!',
    'remember': 'on'
}

login_response = session.post('http://127.0.0.1:8080/login', data=login_data)

if login_response.status_code == 200:
    print("✓ Logged in successfully")
    
    # Test prompts page
    prompts_response = session.get('http://127.0.0.1:8080/prompts/')
    print(f"Prompts page: {prompts_response.status_code}")
    
    # Check if prompts list loads
    if "Prompts Management" in prompts_response.text:
        print("✓ Prompts page loads correctly")
    else:
        print("✗ Prompts page content issue")
    
    # Test add prompt page
    add_response = session.get('http://127.0.0.1:8080/prompts/add')
    print(f"Add prompt page: {add_response.status_code}")
    
    if add_response.status_code == 200:
        print("✓ Add prompt page accessible")
        
        # Extract CSRF for form submission
        soup = BeautifulSoup(add_response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        
        if csrf_token:
            print("✓ CSRF token found in add form")
        else:
            print("✗ CSRF token missing in add form")
    
    # Test performance monitoring
    perf_response = session.get('http://127.0.0.1:8080/performance/')
    print(f"Performance page: {perf_response.status_code}")
    
    # Test costs page
    costs_response = session.get('http://127.0.0.1:8080/costs/')
    print(f"Costs page: {costs_response.status_code}")
    
    # Test API endpoints
    try:
        vertigo_status = session.get('http://127.0.0.1:8080/api/vertigo/status')
        print(f"Vertigo status API: {vertigo_status.status_code}")
        if vertigo_status.status_code == 200:
            try:
                data = vertigo_status.json()
                print(f"✓ API response: {data['status']}")
            except:
                print("✗ API response not valid JSON")
        elif vertigo_status.status_code == 500:
            print("⚠ Vertigo service unavailable (expected)")
    except Exception as e:
        print(f"✗ API error: {e}")
        
    # Test workflow simulation
    try:
        workflow = session.get('http://127.0.0.1:8080/api/simulate/workflow')
        print(f"Workflow simulation API: {workflow.status_code}")
        if workflow.status_code == 200:
            try:
                data = workflow.json()
                print(f"✓ Workflow API response: {data['status']}")
            except:
                print("✗ Workflow API response not valid JSON")
        elif workflow.status_code == 500:
            print("⚠ Workflow simulation error (expected)")
    except Exception as e:
        print(f"✗ Workflow API error: {e}")
        
else:
    print("✗ Login failed")