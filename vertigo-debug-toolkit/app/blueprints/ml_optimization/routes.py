"""
ML Optimization API Routes
Provides endpoints for ML-based prompt performance analysis and optimization.
"""

import logging
from datetime import datetime, timedelta
from flask import jsonify, request, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from . import ml_optimization
from app.services.ml_optimization.ml_service import ml_optimization_service
from app.services.ml_optimization.ab_testing_orchestrator import (
    ab_testing_orchestrator, ABTestConfiguration, TrafficSplit
)
from app.services.ml_optimization.prompt_variant_generator import (
    prompt_variant_generator, VariantGenerationConfig
)
from app.models import db, ABTest, ABTestVariant, ABTestResult, ABTestAnalysis
import json
import uuid

logger = logging.getLogger(__name__)


@ml_optimization.route('/dashboard')
@login_required
def ml_dashboard():
    """ML optimization dashboard page."""
    try:
        # Get dashboard data
        insights = ml_optimization_service.get_ml_insights_dashboard()
        
        return render_template('ml_optimization/dashboard.html', 
                             insights=insights,
                             page_title='ML Optimization Dashboard')
                             
    except Exception as e:
        logger.error(f"Error loading ML dashboard: {e}")
        flash('Error loading ML dashboard', 'error')
        return redirect(url_for('dashboard.index'))


@ml_optimization.route('/api/analysis/comprehensive')
@login_required
def comprehensive_analysis():
    """Generate comprehensive ML analysis."""
    try:
        # Get query parameters
        days_back = request.args.get('days', 30, type=int)
        include_quality = request.args.get('quality', 'true').lower() == 'true'
        include_recommendations = request.args.get('recommendations', 'true').lower() == 'true'
        
        # Validate parameters
        if days_back < 1 or days_back > 365:
            return jsonify({'error': 'Days parameter must be between 1 and 365'}), 400
        
        logger.info(f"Starting comprehensive ML analysis for {days_back} days")
        
        # Generate analysis
        analysis = ml_optimization_service.generate_comprehensive_analysis(
            days_back=days_back,
            include_quality=include_quality,
            include_recommendations=include_recommendations
        )
        
        if 'error' in analysis:
            return jsonify(analysis), 500
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/analysis/prompt/<prompt_id>')
@login_required
def analyze_specific_prompt(prompt_id):
    """Analyze a specific prompt in detail."""
    try:
        # Get query parameters
        days_back = request.args.get('days', 30, type=int)
        prompt_text = request.args.get('prompt_text', '')
        
        # Validate parameters
        if days_back < 1 or days_back > 365:
            return jsonify({'error': 'Days parameter must be between 1 and 365'}), 400
        
        logger.info(f"Analyzing specific prompt: {prompt_id}")
        
        # Analyze prompt
        analysis = ml_optimization_service.analyze_specific_prompt(
            prompt_id=prompt_id,
            prompt_text=prompt_text if prompt_text else None,
            days_back=days_back
        )
        
        if 'error' in analysis:
            return jsonify(analysis), 500
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing prompt {prompt_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/insights/dashboard')
@login_required
def dashboard_insights():
    """Get ML insights optimized for dashboard display."""
    try:
        insights = ml_optimization_service.get_ml_insights_dashboard()
        
        if 'error' in insights:
            return jsonify(insights), 500
        
        return jsonify(insights)
        
    except Exception as e:
        logger.error(f"Error getting dashboard insights: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/insights/model-optimization')
@login_required
def model_optimization_insights():
    """Get model-specific optimization insights."""
    try:
        insights = ml_optimization_service.get_model_optimization_insights()
        
        if 'error' in insights:
            return jsonify(insights), 500
        
        return jsonify(insights)
        
    except Exception as e:
        logger.error(f"Error getting model optimization insights: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/quality/report', methods=['POST'])
@login_required
def generate_quality_report():
    """Generate a comprehensive quality report for given prompts."""
    try:
        data = request.get_json()
        
        if not data or 'prompts' not in data:
            return jsonify({'error': 'Missing prompts data'}), 400
        
        prompts = data['prompts']
        
        # Validate prompts structure
        for prompt in prompts:
            if 'id' not in prompt or 'text' not in prompt:
                return jsonify({'error': 'Each prompt must have id and text fields'}), 400
        
        logger.info(f"Generating quality report for {len(prompts)} prompts")
        
        # Generate report
        report = ml_optimization_service.generate_quality_report(prompts)
        
        if 'error' in report:
            return jsonify(report), 500
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating quality report: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/patterns')
@login_required
def get_performance_patterns():
    """Get detected performance patterns."""
    try:
        # Get query parameters
        days_back = request.args.get('days', 30, type=int)
        pattern_type = request.args.get('type', None)
        
        # Validate parameters
        if days_back < 1 or days_back > 365:
            return jsonify({'error': 'Days parameter must be between 1 and 365'}), 400
        
        logger.info(f"Getting performance patterns for {days_back} days")
        
        # Get patterns from performance analyzer
        patterns = ml_optimization_service.performance_analyzer.detect_performance_patterns(days_back)
        
        # Filter by type if specified
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        
        # Convert to dict format
        patterns_data = [
            {
                'pattern_type': p.pattern_type,
                'description': p.pattern_description,
                'frequency': p.frequency,
                'avg_latency': float(p.avg_latency),
                'avg_cost': float(p.avg_cost),
                'success_rate': float(p.success_rate),
                'confidence_score': float(p.confidence_score),
                'prompt_id': p.prompt_id,
                'samples_count': len(p.samples)
            }
            for p in patterns
        ]
        
        return jsonify({
            'patterns': patterns_data,
            'total_patterns': len(patterns_data),
            'analysis_period_days': days_back
        })
        
    except Exception as e:
        logger.error(f"Error getting performance patterns: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/recommendations')
@login_required
def get_optimization_recommendations():
    """Get optimization recommendations."""
    try:
        # Get query parameters
        days_back = request.args.get('days', 30, type=int)
        priority = request.args.get('priority', None)  # critical, high, medium, low
        category = request.args.get('category', None)  # performance, quality, cost, reliability
        
        # Validate parameters
        if days_back < 1 or days_back > 365:
            return jsonify({'error': 'Days parameter must be between 1 and 365'}), 400
        
        logger.info(f"Getting optimization recommendations")
        
        # Generate comprehensive analysis to get recommendations
        analysis = ml_optimization_service.generate_comprehensive_analysis(
            days_back=days_back,
            include_quality=True,
            include_recommendations=True
        )
        
        if 'error' in analysis:
            return jsonify(analysis), 500
        
        recommendations = analysis.get('optimization_plan', {}).get('recommendations', [])
        
        # Filter recommendations
        if priority:
            recommendations = [r for r in recommendations if r.get('priority') == priority]
        
        if category:
            recommendations = [r for r in recommendations if r.get('category') == category]
        
        # Format for API response
        formatted_recommendations = []
        for rec in recommendations:
            formatted_recommendations.append({
                'id': rec.get('recommendation_id'),
                'title': rec.get('title'),
                'description': rec.get('description'),
                'category': rec.get('category'),
                'priority': rec.get('priority'),
                'expected_impact': rec.get('expected_impact', {}),
                'implementation_effort': rec.get('implementation_effort'),
                'timeframe': rec.get('timeframe'),
                'specific_actions': rec.get('specific_actions', []),
                'confidence_score': rec.get('confidence_score', 0),
                'applicable_prompts': rec.get('applicable_prompts', []),
                'tags': rec.get('tags', [])
            })
        
        return jsonify({
            'recommendations': formatted_recommendations,
            'total_recommendations': len(formatted_recommendations),
            'filters_applied': {
                'priority': priority,
                'category': category,
                'days_back': days_back
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/performance/analytics')
@login_required
def get_performance_analytics():
    """Get prompt performance analytics."""
    try:
        # Get query parameters
        days_back = request.args.get('days', 30, type=int)
        prompt_id = request.args.get('prompt_id', None)
        
        # Validate parameters
        if days_back < 1 or days_back > 365:
            return jsonify({'error': 'Days parameter must be between 1 and 365'}), 400
        
        logger.info(f"Getting performance analytics for {days_back} days")
        
        # Get analytics from performance analyzer
        analytics = ml_optimization_service.performance_analyzer.analyze_prompt_performance(
            prompt_id=prompt_id, days_back=days_back
        )
        
        # Convert to dict format
        analytics_data = []
        for analytic in analytics:
            analytics_data.append({
                'prompt_id': analytic.prompt_id,
                'prompt_text_preview': analytic.prompt_text[:100] + '...' if len(analytic.prompt_text) > 100 else analytic.prompt_text,
                'total_executions': analytic.total_executions,
                'avg_latency_ms': float(analytic.avg_latency_ms),
                'avg_cost_usd': float(analytic.avg_cost_usd),
                'success_rate': float(analytic.success_rate),
                'error_rate': float(analytic.error_rate),
                'p95_latency_ms': float(analytic.p95_latency_ms),
                'cost_per_success': float(analytic.cost_per_success),
                'quality_score': float(analytic.quality_score),
                'optimization_potential': float(analytic.optimization_potential),
                'performance_trends': analytic.performance_trends
            })
        
        # Calculate optimization potential summary
        optimization_summary = ml_optimization_service.performance_analyzer.calculate_optimization_potential(analytics)
        
        return jsonify({
            'analytics': analytics_data,
            'total_prompts': len(analytics_data),
            'optimization_summary': optimization_summary,
            'analysis_period_days': days_back
        })
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/quality/assessments')
@login_required  
def get_quality_assessments():
    """Get prompt quality assessments."""
    try:
        # Get query parameters
        prompt_text = request.args.get('prompt_text', '')
        prompt_id = request.args.get('prompt_id', 'test_prompt')
        
        if not prompt_text:
            return jsonify({'error': 'prompt_text parameter is required'}), 400
        
        logger.info(f"Getting quality assessment for prompt: {prompt_id}")
        
        # Get assessment from quality scorer
        assessment = ml_optimization_service.quality_scorer.assess_prompt_quality(
            prompt_text=prompt_text,
            prompt_id=prompt_id
        )
        
        # Convert to dict format
        assessment_data = {
            'prompt_id': assessment.prompt_id,
            'overall_score': float(assessment.overall_score),
            'grade': assessment.grade,
            'strengths': assessment.strengths,
            'weaknesses': assessment.weaknesses,
            'optimization_priority': assessment.optimization_priority,
            'estimated_improvement_potential': float(assessment.estimated_improvement_potential),
            'metrics': []
        }
        
        # Add individual metrics
        for metric in assessment.metrics:
            assessment_data['metrics'].append({
                'name': metric.metric_name,
                'score': float(metric.score),
                'weight': float(metric.weight),
                'description': metric.description,
                'recommendations': metric.recommendations,
                'evidence': metric.evidence
            })
        
        return jsonify(assessment_data)
        
    except Exception as e:
        logger.error(f"Error getting quality assessment: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/models/comparison')
@login_required
def get_model_comparison():
    """Get model performance comparison."""
    try:
        # Get query parameters
        days_back = request.args.get('days', 30, type=int)
        
        # Validate parameters
        if days_back < 1 or days_back > 365:
            return jsonify({'error': 'Days parameter must be between 1 and 365'}), 400
        
        logger.info(f"Getting model performance comparison for {days_back} days")
        
        # Get model comparisons
        comparisons = ml_optimization_service.performance_analyzer.compare_model_performance(days_back)
        
        # Convert to dict format
        comparisons_data = []
        for comparison in comparisons:
            comparisons_data.append({
                'model_name': comparison.model_name,
                'avg_latency': float(comparison.avg_latency),
                'avg_cost': float(comparison.avg_cost),
                'success_rate': float(comparison.success_rate),
                'cost_efficiency_score': float(comparison.cost_efficiency_score),
                'latency_efficiency_score': float(comparison.latency_efficiency_score),
                'overall_score': float(comparison.overall_score)
            })
        
        return jsonify({
            'model_comparisons': comparisons_data,
            'total_models': len(comparisons_data),
            'analysis_period_days': days_back
        })
        
    except Exception as e:
        logger.error(f"Error getting model comparison: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/health')
@login_required
def ml_service_health():
    """Get ML optimization service health status."""
    try:
        # Simple health check
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'performance_analyzer': 'available',
                'quality_scorer': 'available',
                'recommendation_engine': 'available',
                'ml_service': 'available'
            },
            'cache_status': {
                'entries': len(ml_optimization_service._cache),
                'last_cleanup': 'N/A'  # Could track this if needed
            },
            'version': '1.0.0'
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Error checking ML service health: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# Error handlers specific to ML optimization blueprint
@ml_optimization.errorhandler(400)
def bad_request(error):
    """Handle bad request errors."""
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400


@ml_optimization.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    logger.error(f"Internal error in ML optimization: {error}")
    return jsonify({'error': 'Internal server error'}), 500


@ml_optimization.errorhandler(404)
def not_found(error):
    """Handle not found errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


# ============================================================================
# A/B Testing Endpoints for Automated Prompt Optimization
# ============================================================================

@ml_optimization.route('/api/ab-tests', methods=['GET'])
@login_required
def list_ab_tests():
    """List all A/B tests with filtering options."""
    try:
        status = request.args.get('status')  # draft, running, paused, completed, cancelled
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = ABTest.query
        
        if status:
            query = query.filter(ABTest.status == status)
        
        # Order by created_at desc
        query = query.order_by(ABTest.created_at.desc())
        
        # Apply pagination
        total_count = query.count()
        tests = query.offset(offset).limit(limit).all()
        
        # Format tests for response
        tests_data = []
        for test in tests:
            test_data = {
                'id': test.id,
                'test_id': test.test_id,
                'name': test.name,
                'description': test.description,
                'status': test.status,
                'test_type': test.test_type,
                'start_time': test.start_time.isoformat() if test.start_time else None,
                'end_time': test.end_time.isoformat() if test.end_time else None,
                'creator_id': test.creator_id,
                'min_sample_size': test.min_sample_size,
                'confidence_level': float(test.confidence_level),
                'auto_conclude': test.auto_conclude,
                'auto_implement': test.auto_implement,
                'winning_variant_id': test.winning_variant_id,
                'created_at': test.created_at.isoformat(),
                'updated_at': test.updated_at.isoformat(),
                'variants_count': ABTestVariant.query.filter_by(ab_test_id=test.id).count(),
                'results_count': ABTestResult.query.filter_by(ab_test_id=test.id).count()
            }
            tests_data.append(test_data)
        
        return jsonify({
            'tests': tests_data,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing A/B tests: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests', methods=['POST'])
@login_required
def create_ab_test():
    """Create a new A/B test."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'description', 'hypothesis', 'success_metrics', 'traffic_splits']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate traffic splits
        if not data['traffic_splits'] or len(data['traffic_splits']) < 2:
            return jsonify({'error': 'Need at least 2 traffic splits'}), 400
        
        total_percentage = sum(split.get('percentage', 0) for split in data['traffic_splits'])
        if abs(total_percentage - 100.0) > 0.01:
            return jsonify({'error': f'Traffic splits must total 100%, got {total_percentage}'}), 400
        
        control_count = sum(1 for split in data['traffic_splits'] if split.get('is_control', False))
        if control_count != 1:
            return jsonify({'error': 'Exactly one variant must be marked as control'}), 400
        
        # Create traffic split objects
        traffic_splits = []
        for split_data in data['traffic_splits']:
            traffic_splits.append(TrafficSplit(
                variant_id=split_data.get('variant_id', str(uuid.uuid4())),
                percentage=split_data['percentage'],
                is_control=split_data.get('is_control', False)
            ))
        
        # Create test configuration
        config = ABTestConfiguration(
            name=data['name'],
            description=data['description'],
            hypothesis=data['hypothesis'],
            success_metrics=data['success_metrics'],
            traffic_splits=traffic_splits,
            min_sample_size=data.get('min_sample_size', 100),
            confidence_level=data.get('confidence_level', 0.95),
            statistical_power=data.get('statistical_power', 0.80),
            max_duration_hours=data.get('max_duration_hours', 168),
            auto_conclude=data.get('auto_conclude', True),
            auto_implement=data.get('auto_implement', False)
        )
        
        # Create the test
        test_id = ab_testing_orchestrator.create_ab_test(config, current_user.id)
        
        logger.info(f"Created A/B test: {test_id}")
        return jsonify({
            'test_id': test_id,
            'message': 'A/B test created successfully',
            'next_steps': ['Configure variants', 'Start test']
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests/<test_id>', methods=['GET'])
@login_required
def get_ab_test(test_id):
    """Get detailed information about an A/B test."""
    try:
        status_info = ab_testing_orchestrator.get_test_status(test_id)
        
        if 'error' in status_info:
            return jsonify(status_info), 404
        
        return jsonify(status_info)
        
    except Exception as e:
        logger.error(f"Error getting A/B test {test_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests/<test_id>/variants', methods=['POST'])
@login_required
def configure_test_variants(test_id):
    """Configure variants for an A/B test."""
    try:
        data = request.get_json()
        
        if not data or 'variants' not in data:
            return jsonify({'error': 'Missing variants configuration'}), 400
        
        # Configure variants
        success = ab_testing_orchestrator.configure_variants(test_id, data['variants'])
        
        if success:
            return jsonify({
                'message': 'Variants configured successfully',
                'configured_variants': list(data['variants'].keys())
            })
        else:
            return jsonify({'error': 'Failed to configure variants'}), 500
        
    except Exception as e:
        logger.error(f"Error configuring variants for test {test_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests/<test_id>/variants/generate', methods=['POST'])
@login_required
def generate_test_variants(test_id):
    """Generate AI-optimized variants for an A/B test."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'base_prompt' not in data:
            return jsonify({'error': 'Missing base_prompt'}), 400
        
        # Create generation configuration
        config = VariantGenerationConfig(
            base_prompt=data['base_prompt'],
            optimization_targets=data.get('optimization_targets', ['latency', 'cost', 'clarity']),
            variation_types=data.get('variation_types', ['structure', 'length', 'tone']),
            num_variants=data.get('num_variants', 3),
            include_control=data.get('include_control', True),
            creativity_level=data.get('creativity_level', 0.7),
            preserve_intent=data.get('preserve_intent', True)
        )
        
        # Generate variants
        variants = prompt_variant_generator.generate_variants(config)
        
        # Convert variants to configuration format
        variant_configs = {}
        for variant in variants:
            variant_configs[variant.variant_id] = {
                'name': variant.name,
                'description': f"Generated using {variant.generation_method}",
                'prompt_content': variant.content,
                'generation_method': variant.generation_method,
                'generation_context': variant.generation_context,
                'expected_improvements': variant.expected_improvements,
                'confidence_score': variant.confidence_score
            }
        
        # Configure the generated variants
        success = ab_testing_orchestrator.configure_variants(test_id, variant_configs)
        
        if success:
            return jsonify({
                'message': 'Variants generated and configured successfully',
                'variants_generated': len(variants),
                'variants': [
                    {
                        'variant_id': v.variant_id,
                        'name': v.name,
                        'generation_method': v.generation_method,
                        'expected_improvements': v.expected_improvements,
                        'confidence_score': v.confidence_score,
                        'is_control': v.is_control,
                        'content_preview': v.content[:100] + '...' if len(v.content) > 100 else v.content
                    }
                    for v in variants
                ]
            })
        else:
            return jsonify({'error': 'Failed to configure generated variants'}), 500
        
    except Exception as e:
        logger.error(f"Error generating variants for test {test_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests/<test_id>/start', methods=['POST'])
@login_required
def start_ab_test(test_id):
    """Start an A/B test."""
    try:
        success = ab_testing_orchestrator.start_test(test_id)
        
        if success:
            return jsonify({
                'message': 'A/B test started successfully',
                'test_id': test_id,
                'status': 'running'
            })
        else:
            return jsonify({'error': 'Failed to start test'}), 500
        
    except Exception as e:
        logger.error(f"Error starting A/B test {test_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests/<test_id>/stop', methods=['POST'])
@login_required
def stop_ab_test(test_id):
    """Stop an A/B test."""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Manual stop by user')
        
        success = ab_testing_orchestrator.stop_test(test_id, reason)
        
        if success:
            return jsonify({
                'message': 'A/B test stopped successfully',
                'test_id': test_id,
                'reason': reason
            })
        else:
            return jsonify({'error': 'Failed to stop test'}), 500
        
    except Exception as e:
        logger.error(f"Error stopping A/B test {test_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests/<test_id>/analyze', methods=['POST'])
@login_required
def analyze_ab_test(test_id):
    """Run statistical analysis on an A/B test."""
    try:
        analysis_results = ab_testing_orchestrator.analyze_test(test_id)
        
        return jsonify(analysis_results)
        
    except Exception as e:
        logger.error(f"Error analyzing A/B test {test_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests/<test_id>/select-variant', methods=['POST'])
@login_required
def select_test_variant(test_id):
    """Select a variant for a user session (for traffic splitting)."""
    try:
        data = request.get_json() or {}
        user_session = data.get('user_session', str(uuid.uuid4()))
        context = data.get('context', {})
        
        selected_variant = ab_testing_orchestrator.select_variant(
            test_id=test_id,
            user_session=user_session,
            context=context
        )
        
        if selected_variant:
            return jsonify({
                'variant_id': selected_variant,
                'user_session': user_session,
                'test_id': test_id
            })
        else:
            return jsonify({
                'error': 'No variant selected',
                'reason': 'Test not running or no variants configured'
            }), 404
        
    except Exception as e:
        logger.error(f"Error selecting variant for test {test_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests/<test_id>/record-result', methods=['POST'])
@login_required
def record_test_result(test_id):
    """Record a test result for analysis."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['variant_id', 'request_id', 'latency_ms', 'cost_usd', 'success']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        success = ab_testing_orchestrator.record_result(
            test_id=test_id,
            variant_id=data['variant_id'],
            request_id=data['request_id'],
            latency_ms=data['latency_ms'],
            cost_usd=data['cost_usd'],
            success=data['success'],
            user_session=data.get('user_session'),
            context=data.get('context', {}),
            external_trace_id=data.get('external_trace_id')
        )
        
        if success:
            return jsonify({
                'message': 'Result recorded successfully',
                'test_id': test_id,
                'variant_id': data['variant_id']
            })
        else:
            return jsonify({'error': 'Failed to record result'}), 500
        
    except Exception as e:
        logger.error(f"Error recording result for test {test_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests/<test_id>/results', methods=['GET'])
@login_required
def get_test_results(test_id):
    """Get results and analysis for an A/B test."""
    try:
        # Get test info
        test = ABTest.query.filter_by(test_id=test_id).first()
        if not test:
            return jsonify({'error': 'Test not found'}), 404
        
        # Get variants
        variants = ABTestVariant.query.filter_by(ab_test_id=test.id).all()
        
        # Get latest analysis
        latest_analysis = ABTestAnalysis.query.filter_by(
            ab_test_id=test.id
        ).order_by(ABTestAnalysis.analysis_date.desc()).first()
        
        # Get results summary
        results_data = {
            'test_id': test_id,
            'test_name': test.name,
            'status': test.status,
            'start_time': test.start_time.isoformat() if test.start_time else None,
            'end_time': test.end_time.isoformat() if test.end_time else None,
            'winning_variant_id': test.winning_variant_id,
            'variants': [],
            'analysis': None,
            'summary': test.results_summary
        }
        
        # Add variant data
        for variant in variants:
            variant_data = {
                'variant_id': variant.variant_id,
                'name': variant.name,
                'is_control': variant.is_control,
                'traffic_percentage': float(variant.traffic_percentage),
                'requests_served': variant.requests_served,
                'success_count': variant.success_count,
                'error_count': variant.error_count,
                'success_rate': float(variant.success_rate) if variant.success_rate else 0.0,
                'avg_latency_ms': float(variant.avg_latency_ms) if variant.avg_latency_ms else 0.0,
                'avg_cost_usd': float(variant.avg_cost_usd) if variant.avg_cost_usd else 0.0
            }
            results_data['variants'].append(variant_data)
        
        # Add analysis data if available
        if latest_analysis:
            results_data['analysis'] = {
                'analysis_date': latest_analysis.analysis_date.isoformat(),
                'sample_size': latest_analysis.current_sample_size,
                'sample_size_adequate': latest_analysis.sample_size_adequate,
                'statistical_significance': float(latest_analysis.statistical_significance) if latest_analysis.statistical_significance else None,
                'effect_size': float(latest_analysis.effect_size) if latest_analysis.effect_size else None,
                'confidence_level': float(latest_analysis.confidence_level),
                'recommendation': latest_analysis.recommendation,
                'recommendation_confidence': float(latest_analysis.recommendation_confidence) if latest_analysis.recommendation_confidence else None,
                'variant_comparisons': latest_analysis.variant_comparisons
            }
        
        return jsonify(results_data)
        
    except Exception as e:
        logger.error(f"Error getting results for test {test_id}: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests/active', methods=['GET'])
@login_required
def get_active_tests():
    """Get all active A/B tests."""
    try:
        active_tests = ab_testing_orchestrator.list_active_tests()
        
        return jsonify({
            'active_tests': active_tests,
            'count': len(active_tests)
        })
        
    except Exception as e:
        logger.error(f"Error getting active tests: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/variant-generation/analyze-prompt', methods=['POST'])
@login_required
def analyze_prompt_for_variants():
    """Analyze a prompt and suggest optimization opportunities."""
    try:
        data = request.get_json()
        
        if 'prompt_text' not in data:
            return jsonify({'error': 'Missing prompt_text'}), 400
        
        prompt_text = data['prompt_text']
        
        # Get quality-based variants
        quality_variants = prompt_variant_generator.generate_from_quality_insights(prompt_text)
        
        # If prompt_id provided, also get performance-based variants
        performance_variants = []
        if 'prompt_id' in data:
            performance_variants = prompt_variant_generator.generate_from_performance_insights(
                data['prompt_id'], 
                data.get('days_back', 30)
            )
        
        all_variants = quality_variants + performance_variants
        
        # Format response
        variants_data = []
        for variant in all_variants:
            variants_data.append({
                'variant_id': variant.variant_id,
                'name': variant.name,
                'content_preview': variant.content[:200] + '...' if len(variant.content) > 200 else variant.content,
                'generation_method': variant.generation_method,
                'expected_improvements': variant.expected_improvements,
                'confidence_score': variant.confidence_score,
                'is_control': variant.is_control,
                'generation_context': variant.generation_context
            })
        
        return jsonify({
            'variants': variants_data,
            'total_variants': len(variants_data),
            'quality_variants': len(quality_variants),
            'performance_variants': len(performance_variants),
            'optimization_opportunities': [
                v.expected_improvements for v in all_variants if v.expected_improvements
            ]
        })
        
    except Exception as e:
        logger.error(f"Error analyzing prompt for variants: {e}")
        return jsonify({'error': str(e)}), 500


@ml_optimization.route('/api/ab-tests/<test_id>/dashboard-data', methods=['GET'])
@login_required
def get_test_dashboard_data(test_id):
    """Get dashboard-optimized data for an A/B test."""
    try:
        # Get comprehensive test status
        status_info = ab_testing_orchestrator.get_test_status(test_id)
        
        if 'error' in status_info:
            return jsonify(status_info), 404
        
        # Enhance with dashboard-specific metrics
        dashboard_data = {
            'test_overview': {
                'test_id': test_id,
                'name': status_info['name'],
                'status': status_info['status'],
                'progress': status_info['progress'],
                'elapsed_hours': status_info['elapsed_hours'],
                'results_count': status_info['results_count']
            },
            'performance_summary': {
                'variants_count': len(status_info['variants']),
                'total_requests': sum(v['requests_served'] for v in status_info['variants']),
                'overall_success_rate': sum(v['success_rate'] * v['requests_served'] for v in status_info['variants']) / max(1, sum(v['requests_served'] for v in status_info['variants'])),
                'avg_latency': sum(v['avg_latency_ms'] * v['requests_served'] for v in status_info['variants']) / max(1, sum(v['requests_served'] for v in status_info['variants'])),
                'avg_cost': sum(v['avg_cost_usd'] * v['requests_served'] for v in status_info['variants']) / max(1, sum(v['requests_served'] for v in status_info['variants']))
            },
            'variants': status_info['variants'],
            'analysis': status_info['latest_analysis'],
            'recommendations': []
        }
        
        # Add recommendations based on current state
        if status_info['status'] == 'running':
            if status_info['progress'] < 0.5:
                dashboard_data['recommendations'].append({
                    'type': 'info',
                    'message': f"Test is {status_info['progress']:.0%} complete. Continue collecting data."
                })
            elif status_info['latest_analysis'] and status_info['latest_analysis']['recommendation']:
                dashboard_data['recommendations'].append({
                    'type': 'analysis',
                    'message': f"Analysis recommendation: {status_info['latest_analysis']['recommendation']}"
                })
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Error getting dashboard data for test {test_id}: {e}")
        return jsonify({'error': str(e)}), 500