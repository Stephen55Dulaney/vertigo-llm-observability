#!/usr/bin/env python3
"""
Vertigo Debug Toolkit - Main Application

A Flask-based debug toolkit for monitoring and optimizing the Vertigo email inbox agent
using Langfuse for prompt management, performance monitoring, and cost tracking.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import app components
from app import create_app, db
from app.models import User, Prompt, Trace, Cost

# Create Flask app
app = create_app()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Blueprints are now registered in the app factory

@app.route('/')
def index():
    """Main landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }

@app.route('/api/vertigo/status')
@login_required
def vertigo_status():
    """Check Vertigo agent status."""
    try:
        import requests
        from app.services.vertigo_client import VertigoClient
        
        client = VertigoClient()
        status = client.get_status()
        return {'status': 'success', 'data': status}
    except Exception as e:
        logger.error(f"Error checking Vertigo status: {e}")
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/simulate/workflow')
@login_required
def simulate_workflow():
    """Simulate a Vertigo workflow for testing."""
    try:
        from app.services.workflow_simulator import WorkflowSimulator
        
        simulator = WorkflowSimulator()
        result = simulator.run_sample_workflow()
        return {'status': 'success', 'data': result}
    except Exception as e:
        logger.error(f"Error simulating workflow: {e}")
        return {'status': 'error', 'message': str(e)}, 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    return render_template('errors/500.html'), 500

# CLI Commands
@app.cli.command('create-admin')
def create_admin():
    """Create admin user - DEPRECATED: Use setup_admin.py instead."""
    print("⚠️  This command is deprecated for security reasons.")
    print("Please use: python setup_admin.py")
    print("This ensures proper password validation and security.")
    return

@app.cli.command('load-sample-data')
def load_sample_data():
    """Load sample data for testing."""
    from app.services.sample_data import SampleDataLoader
    
    loader = SampleDataLoader()
    loader.load_all()
    print("Sample data loaded successfully")

@app.cli.command('simulate-workflow')
def simulate_workflow_cli():
    """Simulate Vertigo workflow from CLI."""
    from app.services.workflow_simulator import WorkflowSimulator
    
    simulator = WorkflowSimulator()
    result = simulator.run_sample_workflow()
    print(f"Workflow simulation completed: {result}")

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Vertigo Debug Toolkit')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Use SocketIO run method for WebSocket support
    from app.extensions import socketio
    socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug or os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        allow_unsafe_werkzeug=True
    ) 