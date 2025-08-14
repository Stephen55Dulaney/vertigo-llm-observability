"""
Visualizations blueprint for advanced dashboard components.
"""

from flask import Blueprint

visualizations_bp = Blueprint('visualizations', __name__, url_prefix='/viz')

# Import routes to register them with the blueprint
from . import routes