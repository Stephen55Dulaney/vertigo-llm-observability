"""
Alerts Blueprint - Real-Time Alerting System

Provides comprehensive alerting capabilities for performance monitoring:
- Alert rule management (CRUD operations)
- Real-time alert evaluation
- Multi-channel notifications
- Alert history and acknowledgment
"""

from flask import Blueprint

# Create blueprint
alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')

# Import routes to register them with the blueprint
from . import routes