"""
Webhooks Blueprint for LangWatch Integration
"""
from flask import Blueprint

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')

from . import routes