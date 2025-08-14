"""
Costs blueprint for the Vertigo Debug Toolkit.
"""

from flask import Blueprint

costs_bp = Blueprint('costs', __name__)

from . import routes 