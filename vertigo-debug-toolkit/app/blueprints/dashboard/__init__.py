"""
Dashboard blueprint for the Vertigo Debug Toolkit.
"""

from flask import Blueprint

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

from . import routes 