"""
Performance blueprint for the Vertigo Debug Toolkit.
"""

from flask import Blueprint

performance_bp = Blueprint('performance', __name__)

from . import routes 