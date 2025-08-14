"""
Dashboard routes for the Vertigo Debug Toolkit.
"""

import json
import logging
from datetime import datetime, timedelta
from flask import render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from app.utils.auth_decorators import api_login_required
from app import csrf
from app.blueprints.dashboard import dashboard_bp
from app.models import db, Trace, Cost, Prompt, User
from app.services.langwatch_client import LangWatchClient
from app.services.prompt_evaluator import PromptEvaluator
from app.services.cloud_monitor import CloudServiceMonitor
from app.services.semantic_search import SemanticPromptSearch
from app.services.email_formatter import EmailFormatter
from app.services.live_data_service import live_data_service
from sqlalchemy import func, case, and_

logger = logging.getLogger(__name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard main page with live data integration."""
    # Get live performance metrics from unified data service
    try:
        # Get unified metrics from live_data_service (Sprint 1/2 implementation)
        live_metrics = live_data_service.get_unified_performance_metrics(hours=24)
        
        # Get prompt count from database 
        total_prompts = Prompt.query.count()
        
        # Extract metrics from live data service
        metrics = {
            'total_traces': live_metrics.get('total_traces', 0),
            'success_rate': round(live_metrics.get('success_rate', 0), 2),
            'avg_latency': round(live_metrics.get('avg_latency_ms', 0), 2),
            'total_cost': float(live_metrics.get('total_cost', 0)),
            'error_count': live_metrics.get('error_count', 0),
            'recent_traces': live_metrics.get('active_traces_24h', 0),
            'data_sources': live_metrics.get('data_sources', {}),
            'last_updated': live_metrics.get('last_updated'),
            'total_prompts': total_prompts
        }
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        # Fallback metrics matching live data structure
        metrics = {
            'total_traces': 0,
            'success_rate': 0,
            'avg_latency': 0,
            'total_cost': 0,
            'error_count': 0,
            'recent_traces': 0,
            'data_sources': {},
            'last_updated': None,
            'total_prompts': 0
        }
    
    return render_template('dashboard/index.html', metrics=metrics)

@dashboard_bp.route('/api/metrics')
@api_login_required
def get_metrics():
    """Get dashboard metrics using live data service."""
    try:
        # Get time range from request parameters
        hours = request.args.get('hours', 24, type=int)
        hours = max(1, min(hours, 168))  # Limit between 1 hour and 1 week
        
        # Get unified metrics from live_data_service
        live_metrics = live_data_service.get_unified_performance_metrics(hours=hours)
        
        # Get prompt count
        total_prompts = Prompt.query.count()
        
        # Get time series data from live data service
        latency_series = live_data_service.get_latency_time_series(hours=hours)
        
        # Format as performance data for charts (maintaining backwards compatibility)
        performance_data = []
        for point in latency_series:
            performance_data.append({
                'timestamp': point.get('timestamp'),
                'latency_ms': point.get('latency_ms', 0),
                'trace_count': point.get('trace_count', 0)
            })
        
        return jsonify({
            'total_traces': live_metrics.get('total_traces', 0),
            'total_costs': float(live_metrics.get('total_cost', 0)),
            'total_prompts': total_prompts,
            'recent_traces': live_metrics.get('active_traces_24h', 0),
            'success_rate': round(live_metrics.get('success_rate', 0), 2),
            'error_count': live_metrics.get('error_count', 0),
            'performance_data': performance_data,
            'data_sources': live_metrics.get('data_sources', {}),
            'last_updated': live_metrics.get('last_updated')
        })
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/cloud-status')
@login_required
def get_cloud_status():
    """Get cloud service status."""
    try:
        monitor = CloudServiceMonitor()
        status = monitor.check_all_services()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting cloud status: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/prompts/performance/<int:prompt_id>')
@login_required
def get_prompt_performance(prompt_id):
    """Get performance metrics for a specific prompt."""
    try:
        evaluator = PromptEvaluator()
        days = request.args.get('days', 30, type=int)
        metrics = evaluator.get_prompt_performance(prompt_id, days)
        
        return jsonify({
            'prompt_id': metrics.prompt_id,
            'prompt_name': metrics.prompt_name,
            'total_calls': metrics.total_calls,
            'success_rate': metrics.success_rate,
            'avg_response_time': metrics.avg_response_time,
            'total_cost': metrics.total_cost,
            'avg_tokens_used': metrics.avg_tokens_used,
            'error_count': metrics.error_count,
            'last_used': metrics.last_used.isoformat() if metrics.last_used else None
        })
    except Exception as e:
        logger.error(f"Error getting prompt performance: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/prompts/compare', methods=['POST'])
@csrf.exempt
@login_required
def compare_prompts():
    """Compare two prompts using A/B testing."""
    try:
        data = request.get_json()
        prompt_a_id = data.get('prompt_a_id')
        prompt_b_id = data.get('prompt_b_id')
        
        # Convert days to integer with error handling
        try:
            days = int(data.get('days', 30))
        except (ValueError, TypeError):
            days = 30  # Default fallback
        
        if not prompt_a_id or not prompt_b_id:
            return jsonify({'error': 'Both prompt_a_id and prompt_b_id are required'}), 400
        
        evaluator = PromptEvaluator()
        result = evaluator.compare_prompts(prompt_a_id, prompt_b_id, days)
        
        return jsonify({
            'prompt_a': result.prompt_a,
            'prompt_b': result.prompt_b,
            'winner': result.winner,
            'confidence_level': result.confidence_level,
            'improvement_percentage': result.improvement_percentage,
            'prompt_a_metrics': {
                'total_calls': result.prompt_a_metrics.total_calls,
                'success_rate': result.prompt_a_metrics.success_rate,
                'avg_response_time': result.prompt_a_metrics.avg_response_time,
                'total_cost': result.prompt_a_metrics.total_cost,
                'avg_tokens_used': result.prompt_a_metrics.avg_tokens_used
            },
            'prompt_b_metrics': {
                'total_calls': result.prompt_b_metrics.total_calls,
                'success_rate': result.prompt_b_metrics.success_rate,
                'avg_response_time': result.prompt_b_metrics.avg_response_time,
                'total_cost': result.prompt_b_metrics.total_cost,
                'avg_tokens_used': result.prompt_b_metrics.avg_tokens_used
            }
        })
    except Exception as e:
        logger.error(f"Error comparing prompts: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/prompts/<int:prompt_id>/recommendations')
@login_required
def get_prompt_recommendations(prompt_id):
    """Get cost optimization recommendations for a prompt."""
    try:
        evaluator = PromptEvaluator()
        recommendations = evaluator.get_cost_optimization_recommendations(prompt_id)
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/sessions/<session_id>')
@login_required
def get_session_analysis(session_id):
    """Get session analysis for a specific session."""
    try:
        evaluator = PromptEvaluator()
        analysis = evaluator.get_session_analysis(session_id)
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error analyzing session: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/evaluation/report', methods=['POST'])
@csrf.exempt
@login_required
def generate_evaluation_report():
    """Generate a comprehensive evaluation report for multiple prompts."""
    try:
        data = request.get_json()
        prompt_ids = data.get('prompt_ids', [])
        
        # Convert days to integer with error handling
        try:
            days = int(data.get('days', 30))
        except (ValueError, TypeError):
            days = 30  # Default fallback
        
        if not prompt_ids:
            return jsonify({'error': 'prompt_ids array is required'}), 400
        
        evaluator = PromptEvaluator()
        report = evaluator.generate_evaluation_report(prompt_ids, days)
        return jsonify(report)
    except Exception as e:
        logger.error(f"Error generating evaluation report: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/prompts/<prompt_name>/history')
@login_required
def get_prompt_history(prompt_name):
    """Get version history for a specific prompt."""
    try:
        evaluator = PromptEvaluator()
        history = evaluator.get_prompt_version_history(prompt_name)
        return jsonify({'history': history})
    except Exception as e:
        logger.error(f"Error getting prompt history: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/advanced-evaluation')
@login_required
def advanced_evaluation():
    """Advanced prompt evaluation page."""
    return render_template('dashboard/advanced_evaluation.html')

@dashboard_bp.route('/api/prompts/list')
@login_required
def get_prompts_list():
    """Get list of all prompts with basic metrics."""
    try:
        prompts = Prompt.query.all()
        prompt_list = []
        
        evaluator = PromptEvaluator()
        
        for prompt in prompts:
            # Get basic metrics for the last 7 days
            metrics = evaluator.get_prompt_performance(prompt.id, days=7)
            
            prompt_list.append({
                'id': prompt.id,
                'name': prompt.name,
                'version': prompt.version,
                'prompt_type': prompt.prompt_type,
                'created_at': prompt.created_at.isoformat(),
                'metrics': {
                    'total_calls': metrics.total_calls,
                    'success_rate': metrics.success_rate,
                    'total_cost': metrics.total_cost,
                    'avg_response_time': metrics.avg_response_time
                }
            })
        
        return jsonify({'prompts': prompt_list})
    except Exception as e:
        logger.error(f"Error getting prompts list: {e}")
        return jsonify({'error': str(e)}), 500 

@dashboard_bp.route('/api/recent-activity')
@api_login_required
def get_recent_activity():
    """Get recent activity data."""
    try:
        # Get recent traces
        recent_traces = Trace.query.order_by(Trace.start_time.desc()).limit(10).all()
        
        activity_data = []
        for trace in recent_traces:
            activity_data.append({
                'id': trace.id,
                'name': trace.name,
                'status': trace.status,
                'timestamp': trace.start_time.isoformat() if trace.start_time else None,
                'prompt_name': trace.prompt.name if trace.prompt else 'Unknown',
                'duration': trace.duration_ms if trace.duration_ms else None
            })
        
        return jsonify({
            'status': 'success',
            'data': activity_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@dashboard_bp.route('/api/vertigo-status')
@api_login_required
def get_vertigo_status():
    """Get Vertigo agent status."""
    try:
        # For now, return a basic status
        # In the future, this could check actual Vertigo services
        status = {
            'agent_status': 'operational',
            'last_check': datetime.utcnow().isoformat(),
            'services': {
                'email_processor': 'operational',
                'meeting_processor': 'operational',
                'daily_summary': 'operational'
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': status
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@dashboard_bp.route('/api/langwatch-status')
@login_required
def get_langwatch_status():
    """Get LangWatch connection status and recent traces."""
    try:
        langwatch_client = current_app.langwatch
        
        # Test connection by getting recent traces
        traces = langwatch_client.get_recent_traces_for_display(limit=5)
        
        # Count total traces in database
        total_traces = Trace.query.count()
        recent_traces = Trace.query.order_by(Trace.start_time.desc()).limit(10).all()
        
        # Get connection status
        status = {
            'connection_status': 'connected' if langwatch_client.is_enabled() else 'disconnected',
            'total_traces_in_db': total_traces,
            'langwatch_traces_available': len(traces) if traces else 0,
            'last_sync': datetime.utcnow().isoformat(),
            'recent_traces': [
                {
                    'id': trace.id,
                    'name': trace.name,
                    'status': trace.status,
                    'timestamp': trace.start_time.isoformat() if trace.start_time else None
                } for trace in recent_traces[:5]
            ]
        }
        
        return jsonify({
            'status': 'success',
            'data': status
        })
    except Exception as e:
        logger.error(f"Error checking LangWatch status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'data': {
                'connection_status': 'error',
                'total_traces_in_db': 0,
                'langfuse_traces_available': 0
            }
        }), 500

@dashboard_bp.route('/email-comparison')
@login_required
def email_comparison():
    """Email format comparison page."""
    return render_template('dashboard/email_comparison.html')

@dashboard_bp.route('/api/email-comparison/compare', methods=['POST'])
@csrf.exempt
@login_required
def compare_email_formats():
    """Compare actual email with LLM evaluation results."""
    try:
        data = request.get_json()
        actual_content = data.get('actual_content', '')
        llm_content = data.get('llm_content', '')
        evaluation_data = data.get('evaluation_data', {})
        
        if not actual_content or not llm_content:
            return jsonify({'error': 'Both actual_content and llm_content are required'}), 400
        
        formatter = EmailFormatter()
        comparison = formatter.compare_emails(actual_content, llm_content, evaluation_data)
        result = formatter.format_for_html(comparison)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error comparing email formats: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/email-comparison/from-json', methods=['POST'])
@csrf.exempt
@login_required
def compare_from_json():
    """Generate email comparison from JSON evaluation data."""
    try:
        data = request.get_json()
        json_data = data.get('json_data', {})
        
        if not json_data:
            return jsonify({'error': 'json_data is required'}), 400
        
        formatter = EmailFormatter()
        comparison = formatter.generate_comparison_from_json(json_data)
        result = formatter.format_for_html(comparison)
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error generating comparison from JSON: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/email-comparison/sample')
@login_required
def get_sample_comparison():
    """Get a sample email comparison for demonstration."""
    try:
        # Return a simplified mock response that matches the expected format
        mock_result = {
            'metrics': {
                'overall_score': 85,
                'response_time': 1.2,
                'total_cost': 0.045,
                'content_accuracy': 92,
                'structure_match': 78,
                'tone_consistency': 65,
                'completeness': 84,
                'format_compliance': 96,
                'factual_precision': 45
            },
            'actual_email': {
                'key_points': [
                    'Daily planning and goal setting discussion',
                    'Google Agent Space exploration and setup',
                    'AI enablement strategy for workflow optimization'
                ],
                'action_items': [
                    '<strong>Max:</strong> Complete migration of legacy systems by Friday',
                    '<strong>Sarah:</strong> Research AI tools for customer service automation',
                    '<strong>Team:</strong> Review and approve new workflow documentation'
                ],
                'next_steps': [
                    'Schedule follow-up meeting for next week',
                    'Implement priority AI tools identified in research',
                    'Begin pilot testing of new workflow processes'
                ],
                'participants': ['Max Thompson', 'Sarah Chen', 'Alex Rodriguez', 'Jordan Kim']
            },
            'llm_email': {
                'key_points': [
                    'Daily planning and goal setting discussion',
                    'Google Agent workspace configuration and implementation',
                    'AI enablement strategy for workflow optimization'
                ],
                'action_items': [
                    '<strong>Max:</strong> Complete migration of legacy systems by Friday',
                    '<strong>Sarah:</strong> Research AI tools for customer service automation',
                    '<strong>Jordan:</strong> Update team documentation with new processes',
                    '<strong>Team:</strong> Review and approve new workflow documentation'
                ],
                'next_steps': [
                    'Schedule follow-up meeting for next week',
                    'Implement priority AI tools identified in research',
                    'Begin pilot testing of new workflow processes',
                    'Conduct training session on new AI tools'
                ],
                'participants': ['Max Thompson', 'Sarah Chen', 'Alex Rodriguez', 'Jordan Kim']
            },
            'differences': [
                {
                    'section': 'key_points',
                    'type': 'modified',
                    'content': 'Google Agent workspace configuration and implementation'
                },
                {
                    'section': 'action_items',
                    'type': 'added',
                    'content': '<strong>Jordan:</strong> Update team documentation with new processes'
                },
                {
                    'section': 'next_steps',
                    'type': 'added',
                    'content': 'Conduct training session on new AI tools'
                }
            ],
            'recommendations': [
                'Improve factual precision (currently 45%)',
                'Enhance tone consistency matching',
                'Consider prompt refinement for better structure'
            ],
            'strengths': [
                'Content accuracy is very high (92%)',
                'Format compliance nearly perfect (96%)',
                'Response time within acceptable range'
            ]
        }
        
        return jsonify({
            'status': 'success',
            'data': mock_result
        })
        
    except Exception as e:
        logger.error(f"Error generating sample comparison: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/vertigo/test-email-processor')
@login_required
def test_email_processor():
    """Test the email processor Cloud Function."""
    try:
        monitor = CloudServiceMonitor()
        result = monitor.test_email_processor()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error testing email processor: {e}")
        return jsonify({'test_status': 'error', 'error': str(e)}), 500

@dashboard_bp.route('/api/vertigo/test-meeting-processor')
@login_required
def test_meeting_processor():
    """Test the meeting processor Cloud Function."""
    try:
        monitor = CloudServiceMonitor()
        result = monitor.test_meeting_processor()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error testing meeting processor: {e}")
        return jsonify({'test_status': 'error', 'error': str(e)}), 500 