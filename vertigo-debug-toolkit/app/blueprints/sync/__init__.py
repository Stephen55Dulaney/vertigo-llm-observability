"""
Sync Management Blueprint

API endpoints for managing Firestore sync operations, monitoring sync health,
and controlling sync scheduler.
"""

from flask import Blueprint

sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')

from . import routes