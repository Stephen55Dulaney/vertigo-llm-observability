"""
Alert Blueprint Routes

Routes for managing alert rules, viewing alert events, and configuring notifications.
Provides comprehensive CRUD operations and real-time alert management.
"""

import json
import logging
from datetime import datetime, timedelta
from flask import (
    render_template, request, jsonify, redirect, url_for, flash, 
    current_app, abort
)
from flask_login import login_required, current_user
from sqlalchemy import desc, and_, or_
from werkzeug.exceptions import BadRequest

from app.models import db, AlertRule, AlertEvent, DataSource, User
from app.services.alert_service import alert_service
from app.services.live_data_service import live_data_service
from . import alerts_bp

logger = logging.getLogger(__name__)

@alerts_bp.route('/')
@login_required
def index():
    """Alert management dashboard."""
    try:
        # Get alert rules with pagination
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Base query
        rules_query = AlertRule.query
        
        # Apply filters
        filter_type = request.args.get('type')
        filter_status = request.args.get('status')
        filter_severity = request.args.get('severity')
        search = request.args.get('search')
        
        if filter_type:
            rules_query = rules_query.filter(AlertRule.alert_type == filter_type)
        
        if filter_status == 'active':
            rules_query = rules_query.filter(AlertRule.is_active == True)
        elif filter_status == 'inactive':
            rules_query = rules_query.filter(AlertRule.is_active == False)
        
        if filter_severity:
            rules_query = rules_query.filter(AlertRule.severity == filter_severity)
        
        if search:
            rules_query = rules_query.filter(
                or_(
                    AlertRule.name.ilike(f'%{search}%'),
                    AlertRule.alert_type.ilike(f'%{search}%')
                )
            )
        
        # Order by last triggered (most recent first), then by created date
        rules_query = rules_query.order_by(
            AlertRule.last_triggered.desc().nullslast(),
            AlertRule.created_at.desc()
        )
        
        rules_pagination = rules_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get recent alert events
        recent_events = AlertEvent.query.join(AlertRule).filter(
            AlertEvent.triggered_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(AlertEvent.triggered_at.desc()).limit(10).all()
        
        # Get alert statistics
        stats = {
            'total_rules': AlertRule.query.count(),
            'active_rules': AlertRule.query.filter(AlertRule.is_active == True).count(),
            'triggered_today': AlertEvent.query.filter(
                AlertEvent.triggered_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count(),
            'active_alerts': AlertEvent.query.filter(AlertEvent.status == 'active').count()
        }
        
        # Get available data sources
        data_sources = DataSource.query.filter(DataSource.is_active == True).all()
        
        return render_template('alerts/index.html',
                             rules=rules_pagination.items,
                             pagination=rules_pagination,
                             recent_events=recent_events,
                             stats=stats,
                             data_sources=data_sources,
                             current_filters={
                                 'type': filter_type,
                                 'status': filter_status,
                                 'severity': filter_severity,
                                 'search': search
                             })
        
    except Exception as e:
        logger.error(f"Error in alerts index: {e}")
        flash(f"Error loading alerts: {str(e)}", 'error')
        return render_template('alerts/index.html', 
                             rules=[], 
                             recent_events=[], 
                             stats={},
                             data_sources=[],
                             current_filters={})

@alerts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_rule():
    """Create new alert rule."""
    if not current_user.is_admin:
        flash('Administrator privileges required to create alert rules.', 'error')
        return redirect(url_for('alerts.index'))
    
    if request.method == 'GET':
        # Get available data sources for the form
        data_sources = DataSource.query.filter(DataSource.is_active == True).all()
        
        return render_template('alerts/create.html', 
                             data_sources=data_sources,
                             alert_types=alert_service.get_available_alert_types(),
                             comparison_operators=alert_service.get_comparison_operators(),
                             notification_channels=alert_service.get_available_channels(),
                             severities=['low', 'medium', 'high', 'critical'])
    
    try:
        # Validate required fields
        required_fields = ['name', 'alert_type', 'threshold_value', 'comparison_operator']
        for field in required_fields:
            if not request.form.get(field):
                raise BadRequest(f"Missing required field: {field}")
        
        # Create new alert rule
        rule = AlertRule()
        rule.name = request.form['name'].strip()
        rule.alert_type = request.form['alert_type']
        rule.threshold_value = float(request.form['threshold_value'])
        rule.comparison_operator = request.form['comparison_operator']
        rule.time_window_minutes = int(request.form.get('time_window_minutes', 5))
        rule.severity = request.form.get('severity', 'medium')
        rule.cooldown_minutes = int(request.form.get('cooldown_minutes', 60))
        rule.is_active = request.form.get('is_active') == 'on'
        
        # Set data source if specified
        data_source_id = request.form.get('data_source_id')
        if data_source_id:
            rule.data_source_id = int(data_source_id)
        
        # Process notification channels
        selected_channels = request.form.getlist('notification_channels')
        if selected_channels:
            rule.notification_channels = json.dumps(selected_channels)
        else:
            rule.notification_channels = json.dumps(['email'])  # Default to email
        
        # Optional fields
        if request.form.get('condition_query'):
            rule.condition_query = request.form['condition_query'].strip()
        
        # Validate the rule before saving
        validation_result = alert_service.validate_alert_rule(rule)
        if not validation_result['valid']:
            raise BadRequest(validation_result['error'])
        
        # Save to database
        db.session.add(rule)
        db.session.commit()
        
        logger.info(f"Alert rule created: {rule.name} by user {current_user.username}")
        flash(f"Alert rule '{rule.name}' created successfully.", 'success')
        return redirect(url_for('alerts.view_rule', rule_id=rule.id))
        
    except ValueError as e:
        logger.error(f"Validation error creating alert rule: {e}")
        flash(f"Invalid input: {str(e)}", 'error')
        return redirect(url_for('alerts.create_rule'))
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}")
        db.session.rollback()
        flash(f"Error creating alert rule: {str(e)}", 'error')
        return redirect(url_for('alerts.create_rule'))

@alerts_bp.route('/rule/<int:rule_id>')
@login_required
def view_rule(rule_id):
    """View alert rule details."""
    try:
        rule = AlertRule.query.get_or_404(rule_id)
        
        # Get recent events for this rule
        events = AlertEvent.query.filter(
            AlertEvent.rule_id == rule_id
        ).order_by(AlertEvent.triggered_at.desc()).limit(50).all()
        
        # Get rule evaluation history (last 24 hours)
        evaluation_history = alert_service.get_rule_evaluation_history(rule_id, hours=24)
        
        # Get current metric value
        current_value = alert_service.get_current_metric_value(rule)
        
        return render_template('alerts/view_rule.html',
                             rule=rule,
                             events=events,
                             evaluation_history=evaluation_history,
                             current_value=current_value)
        
    except Exception as e:
        logger.error(f"Error viewing alert rule {rule_id}: {e}")
        flash(f"Error loading alert rule: {str(e)}", 'error')
        return redirect(url_for('alerts.index'))

@alerts_bp.route('/rule/<int:rule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rule(rule_id):
    """Edit alert rule."""
    if not current_user.is_admin:
        flash('Administrator privileges required to edit alert rules.', 'error')
        return redirect(url_for('alerts.view_rule', rule_id=rule_id))
    
    rule = AlertRule.query.get_or_404(rule_id)
    
    if request.method == 'GET':
        data_sources = DataSource.query.filter(DataSource.is_active == True).all()
        
        return render_template('alerts/edit_rule.html',
                             rule=rule,
                             data_sources=data_sources,
                             alert_types=alert_service.get_available_alert_types(),
                             comparison_operators=alert_service.get_comparison_operators(),
                             notification_channels=alert_service.get_available_channels(),
                             severities=['low', 'medium', 'high', 'critical'])
    
    try:
        # Update rule fields
        rule.name = request.form['name'].strip()
        rule.alert_type = request.form['alert_type']
        rule.threshold_value = float(request.form['threshold_value'])
        rule.comparison_operator = request.form['comparison_operator']
        rule.time_window_minutes = int(request.form.get('time_window_minutes', 5))
        rule.severity = request.form.get('severity', 'medium')
        rule.cooldown_minutes = int(request.form.get('cooldown_minutes', 60))
        rule.is_active = request.form.get('is_active') == 'on'
        
        # Update data source
        data_source_id = request.form.get('data_source_id')
        rule.data_source_id = int(data_source_id) if data_source_id else None
        
        # Update notification channels
        selected_channels = request.form.getlist('notification_channels')
        rule.notification_channels = json.dumps(selected_channels if selected_channels else ['email'])
        
        # Update condition query
        rule.condition_query = request.form.get('condition_query', '').strip() or None
        
        # Validate the updated rule
        validation_result = alert_service.validate_alert_rule(rule)
        if not validation_result['valid']:
            raise BadRequest(validation_result['error'])
        
        db.session.commit()
        
        logger.info(f"Alert rule updated: {rule.name} by user {current_user.username}")
        flash(f"Alert rule '{rule.name}' updated successfully.", 'success')
        return redirect(url_for('alerts.view_rule', rule_id=rule.id))
        
    except Exception as e:
        logger.error(f"Error updating alert rule {rule_id}: {e}")
        db.session.rollback()
        flash(f"Error updating alert rule: {str(e)}", 'error')
        return redirect(url_for('alerts.edit_rule', rule_id=rule_id))

@alerts_bp.route('/rule/<int:rule_id>/delete', methods=['POST'])
@login_required
def delete_rule(rule_id):
    """Delete alert rule."""
    if not current_user.is_admin:
        return jsonify({'error': 'Administrator privileges required'}), 403
    
    try:
        rule = AlertRule.query.get_or_404(rule_id)
        rule_name = rule.name
        
        # Delete associated alert events first
        AlertEvent.query.filter(AlertEvent.rule_id == rule_id).delete()
        
        # Delete the rule
        db.session.delete(rule)
        db.session.commit()
        
        logger.info(f"Alert rule deleted: {rule_name} by user {current_user.username}")
        flash(f"Alert rule '{rule_name}' deleted successfully.", 'success')
        return redirect(url_for('alerts.index'))
        
    except Exception as e:
        logger.error(f"Error deleting alert rule {rule_id}: {e}")
        db.session.rollback()
        flash(f"Error deleting alert rule: {str(e)}", 'error')
        return redirect(url_for('alerts.index'))

@alerts_bp.route('/rule/<int:rule_id>/toggle', methods=['POST'])
@login_required
def toggle_rule(rule_id):
    """Toggle alert rule active status."""
    if not current_user.is_admin:
        return jsonify({'error': 'Administrator privileges required'}), 403
    
    try:
        rule = AlertRule.query.get_or_404(rule_id)
        rule.is_active = not rule.is_active
        db.session.commit()
        
        status = "activated" if rule.is_active else "deactivated"
        logger.info(f"Alert rule {status}: {rule.name} by user {current_user.username}")
        
        return jsonify({
            'success': True,
            'is_active': rule.is_active,
            'message': f"Alert rule {status}"
        })
        
    except Exception as e:
        logger.error(f"Error toggling alert rule {rule_id}: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/events')
@login_required
def events():
    """View alert events."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 25
        
        # Base query
        events_query = AlertEvent.query.join(AlertRule)
        
        # Apply filters
        filter_status = request.args.get('status')
        filter_severity = request.args.get('severity')
        filter_rule = request.args.get('rule_id', type=int)
        days = request.args.get('days', 7, type=int)
        
        if filter_status:
            events_query = events_query.filter(AlertEvent.status == filter_status)
        
        if filter_severity:
            events_query = events_query.filter(AlertEvent.severity == filter_severity)
        
        if filter_rule:
            events_query = events_query.filter(AlertEvent.rule_id == filter_rule)
        
        # Time filter
        if days > 0:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            events_query = events_query.filter(AlertEvent.triggered_at >= cutoff_date)
        
        # Order by triggered time (most recent first)
        events_query = events_query.order_by(AlertEvent.triggered_at.desc())
        
        events_pagination = events_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get available rules for filtering
        rules = AlertRule.query.order_by(AlertRule.name).all()
        
        # Get event statistics
        event_stats = {
            'active': AlertEvent.query.filter(AlertEvent.status == 'active').count(),
            'resolved': AlertEvent.query.filter(AlertEvent.status == 'resolved').count(),
            'acknowledged': AlertEvent.query.filter(AlertEvent.status == 'acknowledged').count(),
            'today': AlertEvent.query.filter(
                AlertEvent.triggered_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
        }
        
        return render_template('alerts/events.html',
                             events=events_pagination.items,
                             pagination=events_pagination,
                             rules=rules,
                             stats=event_stats,
                             current_filters={
                                 'status': filter_status,
                                 'severity': filter_severity,
                                 'rule_id': filter_rule,
                                 'days': days
                             })
        
    except Exception as e:
        logger.error(f"Error loading alert events: {e}")
        flash(f"Error loading alert events: {str(e)}", 'error')
        return render_template('alerts/events.html', 
                             events=[], 
                             rules=[], 
                             stats={},
                             current_filters={})

@alerts_bp.route('/event/<int:event_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_event(event_id):
    """Acknowledge an alert event."""
    try:
        event = AlertEvent.query.get_or_404(event_id)
        
        if event.status != 'active':
            return jsonify({'error': 'Only active alerts can be acknowledged'}), 400
        
        event.status = 'acknowledged'
        event.acknowledgment_user_id = current_user.id
        event.acknowledgment_note = request.json.get('note', '') if request.is_json else request.form.get('note', '')
        
        db.session.commit()
        
        logger.info(f"Alert acknowledged: Event {event_id} by user {current_user.username}")
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Alert acknowledged'})
        else:
            flash('Alert acknowledged successfully.', 'success')
            return redirect(url_for('alerts.events'))
        
    except Exception as e:
        logger.error(f"Error acknowledging alert event {event_id}: {e}")
        db.session.rollback()
        
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f"Error acknowledging alert: {str(e)}", 'error')
            return redirect(url_for('alerts.events'))

@alerts_bp.route('/event/<int:event_id>/resolve', methods=['POST'])
@login_required
def resolve_event(event_id):
    """Manually resolve an alert event."""
    try:
        event = AlertEvent.query.get_or_404(event_id)
        
        if event.status not in ['active', 'acknowledged']:
            return jsonify({'error': 'Only active or acknowledged alerts can be resolved'}), 400
        
        event.status = 'resolved'
        event.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Alert resolved: Event {event_id} by user {current_user.username}")
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Alert resolved'})
        else:
            flash('Alert resolved successfully.', 'success')
            return redirect(url_for('alerts.events'))
        
    except Exception as e:
        logger.error(f"Error resolving alert event {event_id}: {e}")
        db.session.rollback()
        
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f"Error resolving alert: {str(e)}", 'error')
            return redirect(url_for('alerts.events'))

@alerts_bp.route('/api/test/<int:rule_id>')
@login_required
def test_rule(rule_id):
    """Test alert rule evaluation."""
    if not current_user.is_admin:
        return jsonify({'error': 'Administrator privileges required'}), 403
    
    try:
        rule = AlertRule.query.get_or_404(rule_id)
        
        # Test rule evaluation
        result = alert_service.evaluate_single_rule(rule, test_mode=True)
        
        return jsonify({
            'success': True,
            'rule_name': rule.name,
            'evaluation_result': result,
            'message': 'Rule test completed'
        })
        
    except Exception as e:
        logger.error(f"Error testing alert rule {rule_id}: {e}")
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/api/metrics/current')
@login_required
def current_metrics():
    """Get current metrics for alert rule creation/editing."""
    try:
        # Get live performance metrics
        metrics = live_data_service.get_unified_performance_metrics(hours=1)
        
        # Add additional computed metrics
        current_metrics = {
            'error_rate': metrics.get('error_rate', 0),
            'success_rate': metrics.get('success_rate', 100),
            'avg_latency_ms': metrics.get('avg_latency_ms', 0),
            'total_cost': metrics.get('total_cost', 0),
            'total_traces': metrics.get('total_traces', 0),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'metrics': current_metrics,
            'data_sources': len(metrics.get('data_sources', []))
        })
        
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/api/notifications/test', methods=['POST'])
@login_required
def test_notification():
    """Test notification channel."""
    if not current_user.is_admin:
        return jsonify({'error': 'Administrator privileges required'}), 403
    
    try:
        data = request.get_json()
        channel_type = data.get('channel_type')
        config = data.get('config', {})
        
        if not channel_type:
            return jsonify({'error': 'Missing channel_type'}), 400
        
        # Test the notification channel
        result = alert_service.test_notification_channel(
            channel_type, 
            config, 
            current_user
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error testing notification channel: {e}")
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/settings')
@login_required
def settings():
    """Alert system settings and configuration."""
    if not current_user.is_admin:
        flash('Administrator privileges required to access alert settings.', 'error')
        return redirect(url_for('alerts.index'))
    
    try:
        # Get notification channel settings
        notification_settings = alert_service.get_notification_settings()
        
        # Get system metrics for configuration hints
        system_metrics = alert_service.get_system_metrics_summary()
        
        return render_template('alerts/settings.html',
                             notification_settings=notification_settings,
                             system_metrics=system_metrics,
                             available_channels=alert_service.get_available_channels())
        
    except Exception as e:
        logger.error(f"Error loading alert settings: {e}")
        flash(f"Error loading alert settings: {str(e)}", 'error')
        return redirect(url_for('alerts.index'))

@alerts_bp.route('/api/status')
@login_required
def api_status():
    """Get alert system status."""
    try:
        status = alert_service.get_system_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting alert system status: {e}")
        return jsonify({'error': str(e)}), 500