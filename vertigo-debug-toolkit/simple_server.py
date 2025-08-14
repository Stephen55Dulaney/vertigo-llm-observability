#!/usr/bin/env python3
"""
Simple server test to debug connectivity issues
"""

import os
import sys
from flask import Flask

# Simple Flask app for testing
simple_app = Flask(__name__)

@simple_app.route('/')
def home():
    return "Simple server is working!"

@simple_app.route('/health')
def health():
    return {"status": "healthy", "message": "Simple server operational"}

if __name__ == '__main__':
    print("Starting simple test server...")
    simple_app.run(host='127.0.0.1', port=8080, debug=True)