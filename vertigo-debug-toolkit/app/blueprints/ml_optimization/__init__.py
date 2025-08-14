"""ML Optimization Blueprint for Vertigo Debug Toolkit."""

from flask import Blueprint

# Create blueprint
ml_optimization = Blueprint('ml_optimization', __name__, url_prefix='/ml')

# Import routes to register them
from . import routes