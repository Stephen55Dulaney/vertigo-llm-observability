"""
Flask extensions initialization for WebSocket support.
"""

from flask_socketio import SocketIO

# Initialize SocketIO extension
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    logger=True,
    engineio_logger=True
)