"""Security blueprint for security management endpoints."""

from flask import Blueprint

security_bp = Blueprint('security', __name__, url_prefix='/security')