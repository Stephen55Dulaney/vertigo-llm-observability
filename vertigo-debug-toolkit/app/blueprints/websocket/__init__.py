"""
WebSocket blueprint for real-time communication.
"""

from flask import Blueprint

websocket_bp = Blueprint('websocket', __name__, url_prefix='/ws')