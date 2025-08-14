"""
Cross-Tenant Learning Dashboard Blueprint
Provides web interface for cross-tenant learning insights and recommendations.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import logging

from app.services.ml_optimization.cross_tenant_learning_engine import cross_tenant_learning_engine
from app.services.tenant_service import tenant_service, require_tenant_access

logger = logging.getLogger(__name__)

# Create Blueprint
cross_tenant_learning_blueprint = Blueprint('cross_tenant_learning', __name__, url_prefix='/cross-tenant-learning')


@cross_tenant_learning_blueprint.route('/')
@login_required
def dashboard():
    """
    Cross-tenant learning insights dashboard.
    """
    try:
        # Get current tenant
        current_tenant = tenant_service.get_current_tenant()
        if not current_tenant:
            logger.warning(f"User {current_user.id} attempted to access cross-tenant dashboard without tenant context")
            return render_template('error.html', 
                                 error_title="No Tenant Context",
                                 error_message="Please select a tenant to view cross-tenant learning insights."), 400
        
        # Check if tenant has consented to cross-tenant learning
        learning_enabled = tenant_service._tenant_consents_to_learning(current_tenant.id)
        
        return render_template('cross_tenant_insights.html',
                             tenant_id=current_tenant.id,
                             tenant_name=current_tenant.name,
                             learning_enabled=learning_enabled,
                             page_title="Cross-Tenant Learning Insights")
        
    except Exception as e:
        logger.error(f"Error rendering cross-tenant learning dashboard: {e}")
        return render_template('error.html', 
                             error_title="Dashboard Error",
                             error_message="Unable to load cross-tenant learning dashboard."), 500


@cross_tenant_learning_blueprint.route('/global-trends')
@login_required  
def global_trends():
    """
    Global optimization trends dashboard (anonymized data only).
    """
    try:
        return render_template('global_optimization_trends.html',
                             page_title="Global Optimization Trends",
                             show_privacy_notice=True)
        
    except Exception as e:
        logger.error(f"Error rendering global trends dashboard: {e}")
        return render_template('error.html',
                             error_title="Dashboard Error", 
                             error_message="Unable to load global trends dashboard."), 500


@cross_tenant_learning_blueprint.route('/patterns')
@login_required
@require_tenant_access('read', 'cross_tenant_patterns')
def patterns_explorer():
    """
    Cross-tenant patterns explorer interface.
    """
    try:
        current_tenant = tenant_service.get_current_tenant()
        if not current_tenant:
            return render_template('error.html',
                                 error_title="No Tenant Context", 
                                 error_message="Please select a tenant to explore patterns."), 400
        
        return render_template('cross_tenant_patterns.html',
                             tenant_id=current_tenant.id,
                             tenant_name=current_tenant.name,
                             page_title="Cross-Tenant Patterns Explorer")
        
    except Exception as e:
        logger.error(f"Error rendering patterns explorer: {e}")
        return render_template('error.html',
                             error_title="Dashboard Error",
                             error_message="Unable to load patterns explorer."), 500


@cross_tenant_learning_blueprint.route('/privacy-settings')
@login_required
@require_tenant_access('admin', 'privacy_settings')
def privacy_settings():
    """
    Privacy settings for cross-tenant learning.
    """
    try:
        current_tenant = tenant_service.get_current_tenant()
        if not current_tenant:
            return render_template('error.html',
                                 error_title="No Tenant Context",
                                 error_message="Please select a tenant to manage privacy settings."), 400
        
        # Get current privacy settings
        learning_enabled = tenant_service._tenant_consents_to_learning(current_tenant.id)
        
        privacy_status = {
            'cross_tenant_learning_enabled': learning_enabled,
            'anonymization_level': 'high',
            'data_isolation_maintained': True,
            'min_tenant_threshold': cross_tenant_learning_engine.MIN_TENANT_THRESHOLD,
            'audit_trail_enabled': True
        }
        
        return render_template('cross_tenant_privacy_settings.html',
                             tenant_id=current_tenant.id,
                             tenant_name=current_tenant.name,
                             privacy_status=privacy_status,
                             page_title="Cross-Tenant Learning Privacy Settings")
        
    except Exception as e:
        logger.error(f"Error rendering privacy settings: {e}")
        return render_template('error.html',
                             error_title="Settings Error",
                             error_message="Unable to load privacy settings."), 500


# AJAX endpoints for dashboard components
@cross_tenant_learning_blueprint.route('/api/tenant/current')
@login_required
def get_current_tenant_api():
    """Get current tenant context for JavaScript."""
    try:
        current_tenant = tenant_service.get_current_tenant()
        if not current_tenant:
            return jsonify({
                'success': False,
                'error': 'No tenant context available'
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'tenant_id': current_tenant.id,
                'tenant_name': current_tenant.name,
                'learning_enabled': tenant_service._tenant_consents_to_learning(current_tenant.id)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting current tenant context: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get tenant context'
        }), 500


@cross_tenant_learning_blueprint.route('/api/quick-insights/<tenant_id>')
@login_required
@require_tenant_access('read', 'cross_tenant_insights')
def get_quick_insights(tenant_id: str):
    """Get quick insights summary for dashboard widgets."""
    try:
        # Validate tenant access
        if not tenant_service.check_user_access(tenant_id, current_user.id, 'read', 'cross_tenant_insights'):
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions'
            }), 403
        
        # Get summary insights (lightweight version)
        insights = cross_tenant_learning_engine.generate_cross_tenant_insights(
            target_tenant_id=tenant_id,
            days_back=7  # Quick insights use 7 days
        )
        
        # Extract key metrics for widgets
        patterns = insights.get('cross_tenant_patterns', {})
        opportunities = insights.get('opportunity_metrics', {})
        state = insights.get('tenant_optimization_state', {})
        
        quick_insights = {
            'applicable_patterns': patterns.get('applicable_patterns', 0),
            'high_impact_opportunities': opportunities.get('high_impact_opportunities', 0),
            'avg_improvement_potential': opportunities.get('avg_improvement_potential', 0),
            'implementation_readiness_score': opportunities.get('implementation_readiness_score', 0),
            'performance_tier': state.get('performance_tier', 'unknown'),
            'optimization_maturity': state.get('optimization_maturity', 'unknown'),
            'recommendations_count': len(insights.get('cross_tenant_recommendations', []))
        }
        
        return jsonify({
            'success': True,
            'data': quick_insights,
            'meta': {
                'tenant_id': tenant_id,
                'timestamp': insights.get('analysis_metadata', {}).get('generated_at')
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting quick insights for tenant {tenant_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load quick insights'
        }), 500