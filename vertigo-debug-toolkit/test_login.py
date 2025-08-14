#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

# Test login with proper session handling
session = requests.Session()

# Get login page and extract CSRF token
login_page = session.get('http://127.0.0.1:8080/login')
soup = BeautifulSoup(login_page.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

print(f"CSRF Token: {csrf_token}")
print(f"Login page status: {login_page.status_code}")

# Submit login form
login_data = {
    'csrf_token': csrf_token,
    'email': 'admin@vertigo.com',
    'password': 'SecureTest123!',
    'remember': 'on'  # Note: using 'remember' not 'remember_me'
}

response = session.post('http://127.0.0.1:8080/login', data=login_data, allow_redirects=False)
print(f"Login response status: {response.status_code}")
print(f"Login response headers: {dict(response.headers)}")

if response.status_code == 302:
    print(f"Redirect location: {response.headers.get('Location')}")
    
    # Follow redirect
    redirect_url = 'http://127.0.0.1:8080' + response.headers.get('Location', '/dashboard/')
    redirect_response = session.get(redirect_url)
    print(f"After redirect status: {redirect_response.status_code}")
    if redirect_response.status_code == 200:
        print("LOGIN SUCCESS - Dashboard accessible")
    else:
        print("LOGIN FAILED - Still redirecting to login")
else:
    print("LOGIN FAILED - Bad response")
    print(response.text[:500])