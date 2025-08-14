"""
Live Data Blueprint for real-time data integration.
"""

from flask import Blueprint

live_data_bp = Blueprint('live_data', __name__, url_prefix='/live-data')