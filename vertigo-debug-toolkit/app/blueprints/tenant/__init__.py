"""
Tenant management blueprint for multi-tenant isolation and administration.
"""

from flask import Blueprint

tenant_bp = Blueprint('tenant', __name__, url_prefix='/tenant')