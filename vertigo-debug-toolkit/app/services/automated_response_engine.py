"""
Automated Response Engine for Vertigo Debug Toolkit
Provides intelligent automated response actions for anomaly resolution.
"""

import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict, deque

from app.models import db
from sqlalchemy import text, func
from app.services.live_data_service import live_data_service
from app.services.alert_service import alert_service, AlertSeverity
from app.services.anomaly_monitoring_engine import AnomalyAlert, AnomalyType

logger = logging.getLogger(__name__)

class ResponseStatus(Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    REQUIRES_APPROVAL = "requires_approval"

class ResponsePriority(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ResponseAction:
    """Represents a single automated response action."""
    id: str
    name: str
    description: str
    action_type: str
    parameters: Dict[str, Any]
    validation_checks: List[str]
    rollback_actions: List[Dict[str, Any]]
    execution_timeout_seconds: int = 300
    requires_human_approval: bool = False

@dataclass
class ResponseExecution:
    """Represents the execution of a response action."""
    id: str
    action_id: str
    anomaly_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: ResponseStatus
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    rollback_executed: bool = False
    human_approved: bool = False
    impact_assessment: Dict[str, Any] = field(default_factory=dict)

class ResponseHandler(ABC):
    """Abstract base class for response handlers."""
    
    @abstractmethod
    def can_handle(self, anomaly: AnomalyAlert) -> bool:
        """Check if this handler can handle the given anomaly."""
        pass
    
    @abstractmethod
    def get_response_actions(self, anomaly: AnomalyAlert) -> List[ResponseAction]:
        """Get list of response actions for the anomaly."""
        pass
    
    @abstractmethod
    def execute_action(self, action: ResponseAction, anomaly: AnomalyAlert) -> Dict[str, Any]:
        """Execute a response action."""
        pass
    
    @abstractmethod
    def validate_action(self, action: ResponseAction, anomaly: AnomalyAlert) -> Tuple[bool, str]:
        """Validate that an action is safe to execute."""
        pass
    
    @abstractmethod
    def rollback_action(self, execution: ResponseExecution) -> bool:
        """Rollback a previously executed action."""
        pass

class PerformanceResponseHandler(ResponseHandler):
    """Handler for performance-related anomalies (latency, throughput)."""
    
    def can_handle(self, anomaly: AnomalyAlert) -> bool:
        return anomaly.metric_name in ['avg_latency_ms', 'total_traces', 'success_rate']
    
    def get_response_actions(self, anomaly: AnomalyAlert) -> List[ResponseAction]:
        actions = []
        
        if anomaly.metric_name == 'avg_latency_ms' and anomaly.severity in [AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            actions.append(ResponseAction(
                id=f"latency_optimization_{int(time.time())}",
                name="Enable Latency Optimization",
                description="Temporarily reduce model complexity and enable caching to reduce latency",
                action_type="latency_optimization",
                parameters={
                    'enable_caching': True,
                    'reduce_model_complexity': True,
                    'timeout_reduction': 0.8,
                    'duration_minutes': 30
                },
                validation_checks=['check_system_load', 'check_cache_availability'],
                rollback_actions=[
                    {'action': 'disable_caching'},
                    {'action': 'restore_model_complexity'}
                ],
                execution_timeout_seconds=60,
                requires_human_approval=anomaly.severity == AlertSeverity.CRITICAL
            ))
        
        if anomaly.metric_name == 'total_traces' and anomaly.actual_value > anomaly.expected_value * 2:
            actions.append(ResponseAction(
                id=f"load_balancing_{int(time.time())}",
                name="Enable Load Balancing",
                description="Distribute traffic load and implement rate limiting",
                action_type="load_balancing",
                parameters={
                    'enable_rate_limiting': True,
                    'rate_limit_requests_per_minute': min(100, anomaly.expected_value * 1.5),
                    'enable_circuit_breaker': True,
                    'duration_minutes': 60
                },
                validation_checks=['check_load_balancer_health'],
                rollback_actions=[
                    {'action': 'disable_rate_limiting'},
                    {'action': 'disable_circuit_breaker'}
                ],
                execution_timeout_seconds=120,
                requires_human_approval=False
            ))
        
        if anomaly.metric_name == 'success_rate' and anomaly.actual_value < 85:
            actions.append(ResponseAction(
                id=f"failure_recovery_{int(time.time())}",
                name="Enable Failure Recovery",
                description="Implement retry logic and fallback mechanisms",
                action_type="failure_recovery",
                parameters={
                    'enable_retry_logic': True,
                    'max_retries': 3,
                    'enable_fallback': True,
                    'fallback_model': 'gemini-1.5-flash',
                    'duration_minutes': 45
                },
                validation_checks=['check_fallback_model_availability'],
                rollback_actions=[
                    {'action': 'disable_retry_logic'},
                    {'action': 'disable_fallback'}
                ],
                execution_timeout_seconds=90,
                requires_human_approval=anomaly.severity == AlertSeverity.CRITICAL
            ))
        
        return actions
    
    def execute_action(self, action: ResponseAction, anomaly: AnomalyAlert) -> Dict[str, Any]:
        """Execute performance optimization action."""
        try:
            if action.action_type == "latency_optimization":
                return self._execute_latency_optimization(action.parameters)
            elif action.action_type == "load_balancing":
                return self._execute_load_balancing(action.parameters)
            elif action.action_type == "failure_recovery":
                return self._execute_failure_recovery(action.parameters)
            else:
                return {'success': False, 'error': f'Unknown action type: {action.action_type}'}
                
        except Exception as e:
            logger.error(f"Error executing performance action {action.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_action(self, action: ResponseAction, anomaly: AnomalyAlert) -> Tuple[bool, str]:
        """Validate performance action."""
        try:
            # Check system resources
            if 'check_system_load' in action.validation_checks:
                # Simulate system load check
                system_load = self._get_system_load()
                if system_load > 0.9:
                    return False, "System load too high to perform optimization"
            
            # Check cache availability
            if 'check_cache_availability' in action.validation_checks:
                cache_available = self._check_cache_health()
                if not cache_available:
                    return False, "Cache system not available"
            
            # Check load balancer
            if 'check_load_balancer_health' in action.validation_checks:
                lb_healthy = self._check_load_balancer_health()
                if not lb_healthy:
                    return False, "Load balancer not healthy"
            
            # Check fallback model
            if 'check_fallback_model_availability' in action.validation_checks:
                fallback_available = self._check_fallback_model(action.parameters.get('fallback_model'))
                if not fallback_available:
                    return False, "Fallback model not available"
            
            return True, "Validation passed"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def rollback_action(self, execution: ResponseExecution) -> bool:
        """Rollback performance action."""
        try:
            # This would implement actual rollback logic
            logger.info(f"Rolling back performance action {execution.action_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back action {execution.action_id}: {e}")
            return False
    
    def _execute_latency_optimization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute latency optimization."""
        # Simulate latency optimization
        logger.info("Executing latency optimization")
        time.sleep(2)  # Simulate execution time
        
        return {
            'success': True,
            'caching_enabled': params.get('enable_caching', False),
            'model_complexity_reduced': params.get('reduce_model_complexity', False),
            'timeout_factor': params.get('timeout_reduction', 1.0),
            'duration_minutes': params.get('duration_minutes', 30)
        }
    
    def _execute_load_balancing(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute load balancing optimization."""
        logger.info("Executing load balancing optimization")
        time.sleep(1)
        
        return {
            'success': True,
            'rate_limiting_enabled': params.get('enable_rate_limiting', False),
            'rate_limit': params.get('rate_limit_requests_per_minute', 100),
            'circuit_breaker_enabled': params.get('enable_circuit_breaker', False),
            'duration_minutes': params.get('duration_minutes', 60)
        }
    
    def _execute_failure_recovery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute failure recovery optimization."""
        logger.info("Executing failure recovery optimization")
        time.sleep(1.5)
        
        return {
            'success': True,
            'retry_logic_enabled': params.get('enable_retry_logic', False),
            'max_retries': params.get('max_retries', 3),
            'fallback_enabled': params.get('enable_fallback', False),
            'fallback_model': params.get('fallback_model'),
            'duration_minutes': params.get('duration_minutes', 45)
        }
    
    def _get_system_load(self) -> float:
        """Get current system load (simulated)."""
        return 0.6  # Simulate 60% load
    
    def _check_cache_health(self) -> bool:
        """Check cache system health (simulated)."""
        return True
    
    def _check_load_balancer_health(self) -> bool:
        """Check load balancer health (simulated)."""
        return True
    
    def _check_fallback_model(self, model_name: Optional[str]) -> bool:
        """Check if fallback model is available (simulated)."""
        return model_name is not None

class CostResponseHandler(ResponseHandler):
    """Handler for cost-related anomalies."""
    
    def can_handle(self, anomaly: AnomalyAlert) -> bool:
        return anomaly.metric_name in ['total_cost', 'cost_per_trace']
    
    def get_response_actions(self, anomaly: AnomalyAlert) -> List[ResponseAction]:
        actions = []
        
        if anomaly.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            actions.append(ResponseAction(
                id=f"cost_optimization_{int(time.time())}",
                name="Enable Cost Optimization",
                description="Implement cost reduction measures including model downgrade and request throttling",
                action_type="cost_optimization",
                parameters={
                    'switch_to_cheaper_model': True,
                    'target_model': 'gemini-1.5-flash',
                    'reduce_context_window': True,
                    'enable_aggressive_caching': True,
                    'throttle_requests': True,
                    'duration_minutes': 60
                },
                validation_checks=['check_cheaper_model_availability'],
                rollback_actions=[
                    {'action': 'restore_original_model'},
                    {'action': 'restore_context_window'},
                    {'action': 'disable_throttling'}
                ],
                execution_timeout_seconds=180,
                requires_human_approval=anomaly.severity == AlertSeverity.CRITICAL
            ))
        
        return actions
    
    def execute_action(self, action: ResponseAction, anomaly: AnomalyAlert) -> Dict[str, Any]:
        """Execute cost optimization action."""
        try:
            if action.action_type == "cost_optimization":
                return self._execute_cost_optimization(action.parameters)
            else:
                return {'success': False, 'error': f'Unknown action type: {action.action_type}'}
                
        except Exception as e:
            logger.error(f"Error executing cost action {action.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_action(self, action: ResponseAction, anomaly: AnomalyAlert) -> Tuple[bool, str]:
        """Validate cost optimization action."""
        try:
            if 'check_cheaper_model_availability' in action.validation_checks:
                model_available = self._check_model_availability(action.parameters.get('target_model'))
                if not model_available:
                    return False, "Target cheaper model not available"
            
            return True, "Validation passed"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def rollback_action(self, execution: ResponseExecution) -> bool:
        """Rollback cost optimization action."""
        try:
            logger.info(f"Rolling back cost action {execution.action_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back cost action {execution.action_id}: {e}")
            return False
    
    def _execute_cost_optimization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cost optimization."""
        logger.info("Executing cost optimization")
        time.sleep(2.5)
        
        return {
            'success': True,
            'model_switched': params.get('switch_to_cheaper_model', False),
            'target_model': params.get('target_model'),
            'context_reduced': params.get('reduce_context_window', False),
            'aggressive_caching': params.get('enable_aggressive_caching', False),
            'throttling_enabled': params.get('throttle_requests', False),
            'duration_minutes': params.get('duration_minutes', 60)
        }
    
    def _check_model_availability(self, model_name: Optional[str]) -> bool:
        """Check if model is available (simulated)."""
        return model_name in ['gemini-1.5-flash', 'gemini-1.5-pro']

class ErrorRecoveryResponseHandler(ResponseHandler):
    """Handler for error-related anomalies."""
    
    def can_handle(self, anomaly: AnomalyAlert) -> bool:
        return anomaly.metric_name in ['error_rate', 'data_source_health_score']
    
    def get_response_actions(self, anomaly: AnomalyAlert) -> List[ResponseAction]:
        actions = []
        
        if anomaly.metric_name == 'error_rate' and anomaly.actual_value > 15:
            actions.append(ResponseAction(
                id=f"error_recovery_{int(time.time())}",
                name="Enable Error Recovery",
                description="Implement error recovery mechanisms and service restart procedures",
                action_type="error_recovery",
                parameters={
                    'restart_unhealthy_services': True,
                    'enable_circuit_breaker': True,
                    'increase_timeout_limits': True,
                    'enable_graceful_degradation': True,
                    'duration_minutes': 30
                },
                validation_checks=['check_service_restart_safety'],
                rollback_actions=[
                    {'action': 'disable_circuit_breaker'},
                    {'action': 'restore_timeout_limits'}
                ],
                execution_timeout_seconds=300,
                requires_human_approval=anomaly.severity == AlertSeverity.CRITICAL
            ))
        
        if anomaly.metric_name == 'data_source_health_score' and anomaly.actual_value < 70:
            actions.append(ResponseAction(
                id=f"data_source_recovery_{int(time.time())}",
                name="Data Source Recovery",
                description="Attempt to recover unhealthy data sources and enable fallback mechanisms",
                action_type="data_source_recovery",
                parameters={
                    'reconnect_data_sources': True,
                    'refresh_authentication': True,
                    'enable_fallback_sources': True,
                    'reduce_query_frequency': True,
                    'duration_minutes': 45
                },
                validation_checks=['check_fallback_sources'],
                rollback_actions=[
                    {'action': 'restore_query_frequency'},
                    {'action': 'disable_fallback_sources'}
                ],
                execution_timeout_seconds=240,
                requires_human_approval=False
            ))
        
        return actions
    
    def execute_action(self, action: ResponseAction, anomaly: AnomalyAlert) -> Dict[str, Any]:
        """Execute error recovery action."""
        try:
            if action.action_type == "error_recovery":
                return self._execute_error_recovery(action.parameters)
            elif action.action_type == "data_source_recovery":
                return self._execute_data_source_recovery(action.parameters)
            else:
                return {'success': False, 'error': f'Unknown action type: {action.action_type}'}
                
        except Exception as e:
            logger.error(f"Error executing recovery action {action.id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_action(self, action: ResponseAction, anomaly: AnomalyAlert) -> Tuple[bool, str]:
        """Validate error recovery action."""
        try:
            if 'check_service_restart_safety' in action.validation_checks:
                safe_to_restart = self._check_restart_safety()
                if not safe_to_restart:
                    return False, "Service restart not safe at this time"
            
            if 'check_fallback_sources' in action.validation_checks:
                fallbacks_available = self._check_fallback_sources()
                if not fallbacks_available:
                    return False, "No fallback data sources available"
            
            return True, "Validation passed"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def rollback_action(self, execution: ResponseExecution) -> bool:
        """Rollback error recovery action."""
        try:
            logger.info(f"Rolling back error recovery action {execution.action_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back recovery action {execution.action_id}: {e}")
            return False
    
    def _execute_error_recovery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute error recovery."""
        logger.info("Executing error recovery")
        time.sleep(3)
        
        return {
            'success': True,
            'services_restarted': params.get('restart_unhealthy_services', False),
            'circuit_breaker_enabled': params.get('enable_circuit_breaker', False),
            'timeout_increased': params.get('increase_timeout_limits', False),
            'graceful_degradation': params.get('enable_graceful_degradation', False),
            'duration_minutes': params.get('duration_minutes', 30)
        }
    
    def _execute_data_source_recovery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data source recovery."""
        logger.info("Executing data source recovery")
        time.sleep(2)
        
        return {
            'success': True,
            'sources_reconnected': params.get('reconnect_data_sources', False),
            'auth_refreshed': params.get('refresh_authentication', False),
            'fallback_enabled': params.get('enable_fallback_sources', False),
            'query_frequency_reduced': params.get('reduce_query_frequency', False),
            'duration_minutes': params.get('duration_minutes', 45)
        }
    
    def _check_restart_safety(self) -> bool:
        """Check if it's safe to restart services (simulated)."""
        return True
    
    def _check_fallback_sources(self) -> bool:
        """Check if fallback data sources are available (simulated)."""
        return True

class AutomatedResponseEngine:
    """
    Automated response engine for intelligent anomaly resolution.
    
    Features:
    - Multi-handler response system for different anomaly types
    - Action validation and rollback mechanisms
    - Human approval workflows for critical actions
    - Response orchestration and dependency management
    - Success validation and impact assessment
    """
    
    def __init__(self):
        """Initialize automated response engine."""
        self.response_handlers = [
            PerformanceResponseHandler(),
            CostResponseHandler(),
            ErrorRecoveryResponseHandler()
        ]
        
        self.active_executions = {}
        self.execution_history = deque(maxlen=1000)
        
        # Response statistics
        self.response_stats = {
            'total_responses': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'rollbacks_performed': 0,
            'human_approvals_required': 0,
            'avg_response_time_seconds': 0
        }
        
        # Approval queue for actions requiring human intervention
        self.approval_queue = deque()
        
        logger.info("Automated response engine initialized")
    
    def process_anomaly(self, anomaly: AnomalyAlert) -> List[ResponseExecution]:
        """Process an anomaly and execute appropriate response actions."""
        try:
            executions = []
            
            # Find suitable handlers
            suitable_handlers = [h for h in self.response_handlers if h.can_handle(anomaly)]
            
            if not suitable_handlers:
                logger.warning(f"No handlers found for anomaly: {anomaly.metric_name}")
                return executions
            
            # Get response actions from all suitable handlers
            all_actions = []
            for handler in suitable_handlers:
                actions = handler.get_response_actions(anomaly)
                all_actions.extend([(handler, action) for action in actions])
            
            # Prioritize actions by severity and type
            all_actions.sort(key=lambda x: (
                x[1].requires_human_approval,  # Human approval last
                x[1].execution_timeout_seconds  # Faster actions first
            ))
            
            # Execute actions
            for handler, action in all_actions:
                execution = self._execute_response_action(handler, action, anomaly)
                executions.append(execution)
                
                # Store active execution
                self.active_executions[execution.id] = execution
            
            return executions
            
        except Exception as e:
            logger.error(f"Error processing anomaly {anomaly.id}: {e}")
            return []
    
    def _execute_response_action(self, handler: ResponseHandler, action: ResponseAction, anomaly: AnomalyAlert) -> ResponseExecution:
        """Execute a single response action."""
        execution = ResponseExecution(
            id=f"exec_{action.id}",
            action_id=action.id,
            anomaly_id=anomaly.id,
            started_at=datetime.utcnow(),
            completed_at=None,
            status=ResponseStatus.PENDING,
            result_data={},
            error_message=None
        )
        
        try:
            # Validate action
            is_valid, validation_message = handler.validate_action(action, anomaly)
            if not is_valid:
                execution.status = ResponseStatus.FAILED
                execution.error_message = f"Validation failed: {validation_message}"
                execution.completed_at = datetime.utcnow()
                return execution
            
            # Check if human approval is required
            if action.requires_human_approval:
                execution.status = ResponseStatus.REQUIRES_APPROVAL
                self.approval_queue.append((handler, action, anomaly, execution))
                logger.info(f"Action {action.id} requires human approval")
                return execution
            
            # Execute action
            execution.status = ResponseStatus.EXECUTING
            start_time = time.time()
            
            result = handler.execute_action(action, anomaly)
            
            execution_time = time.time() - start_time
            execution.completed_at = datetime.utcnow()
            execution.result_data = result
            
            if result.get('success', False):
                execution.status = ResponseStatus.SUCCESS
                # Perform impact assessment
                execution.impact_assessment = self._assess_response_impact(execution, anomaly)
                logger.info(f"Successfully executed action {action.id} in {execution_time:.2f}s")
            else:
                execution.status = ResponseStatus.FAILED
                execution.error_message = result.get('error', 'Unknown error')
                logger.error(f"Failed to execute action {action.id}: {execution.error_message}")
            
            # Update statistics
            self._update_response_stats(execution, execution_time)
            
        except Exception as e:
            execution.status = ResponseStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            logger.error(f"Exception executing action {action.id}: {e}")
        
        finally:
            # Add to history
            self.execution_history.append(execution)
        
        return execution
    
    def approve_pending_action(self, execution_id: str, approved: bool, approver: str) -> bool:
        """Approve or reject a pending action requiring human approval."""
        try:
            # Find pending approval
            pending_item = None
            for i, (handler, action, anomaly, execution) in enumerate(self.approval_queue):
                if execution.id == execution_id:
                    pending_item = (handler, action, anomaly, execution, i)
                    break
            
            if not pending_item:
                logger.warning(f"No pending approval found for execution {execution_id}")
                return False
            
            handler, action, anomaly, execution, queue_index = pending_item
            
            if approved:
                # Remove from approval queue
                del self.approval_queue[queue_index]
                
                # Execute the approved action
                execution.human_approved = True
                execution.status = ResponseStatus.EXECUTING
                
                start_time = time.time()
                result = handler.execute_action(action, anomaly)
                execution_time = time.time() - start_time
                
                execution.completed_at = datetime.utcnow()
                execution.result_data = result
                execution.result_data['approver'] = approver
                
                if result.get('success', False):
                    execution.status = ResponseStatus.SUCCESS
                    execution.impact_assessment = self._assess_response_impact(execution, anomaly)
                    logger.info(f"Human-approved action {action.id} executed successfully")
                else:
                    execution.status = ResponseStatus.FAILED
                    execution.error_message = result.get('error', 'Unknown error')
                
                self._update_response_stats(execution, execution_time)
            else:
                # Rejected by human
                execution.status = ResponseStatus.FAILED
                execution.error_message = f"Rejected by {approver}"
                execution.completed_at = datetime.utcnow()
                execution.result_data = {'rejected_by': approver}
                
                # Remove from approval queue
                del self.approval_queue[queue_index]
                
                logger.info(f"Action {action.id} rejected by {approver}")
            
            # Add to history
            self.execution_history.append(execution)
            
            return True
            
        except Exception as e:
            logger.error(f"Error approving action {execution_id}: {e}")
            return False
    
    def rollback_execution(self, execution_id: str) -> bool:
        """Rollback a previously executed action."""
        try:
            execution = self.active_executions.get(execution_id)
            if not execution:
                # Check history
                for hist_exec in self.execution_history:
                    if hist_exec.id == execution_id:
                        execution = hist_exec
                        break
            
            if not execution:
                logger.warning(f"Execution {execution_id} not found")
                return False
            
            if execution.status != ResponseStatus.SUCCESS:
                logger.warning(f"Cannot rollback execution {execution_id} with status {execution.status}")
                return False
            
            if execution.rollback_executed:
                logger.warning(f"Execution {execution_id} already rolled back")
                return False
            
            # Find the appropriate handler
            handler = None
            for h in self.response_handlers:
                # This is a simplified approach - in practice, you'd store handler info with execution
                mock_anomaly = type('MockAnomaly', (), {
                    'metric_name': execution_id.split('_')[1] if '_' in execution_id else 'unknown'
                })()
                if h.can_handle(mock_anomaly):
                    handler = h
                    break
            
            if not handler:
                logger.error(f"No handler found for rollback of execution {execution_id}")
                return False
            
            # Perform rollback
            rollback_success = handler.rollback_action(execution)
            
            if rollback_success:
                execution.rollback_executed = True
                execution.status = ResponseStatus.ROLLED_BACK
                self.response_stats['rollbacks_performed'] += 1
                logger.info(f"Successfully rolled back execution {execution_id}")
                return True
            else:
                logger.error(f"Failed to rollback execution {execution_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error rolling back execution {execution_id}: {e}")
            return False
    
    def _assess_response_impact(self, execution: ResponseExecution, anomaly: AnomalyAlert) -> Dict[str, Any]:
        """Assess the impact of a response action."""
        try:
            # This would include real impact assessment logic
            # For now, return a simulated assessment
            return {
                'expected_improvement': 'high' if anomaly.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] else 'medium',
                'estimated_resolution_time_minutes': execution.result_data.get('duration_minutes', 30),
                'potential_side_effects': ['temporary performance impact', 'increased monitoring needed'],
                'success_probability': 0.85,
                'assessment_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error assessing response impact: {e}")
            return {'error': str(e)}
    
    def _update_response_stats(self, execution: ResponseExecution, execution_time: float):
        """Update response statistics."""
        self.response_stats['total_responses'] += 1
        
        if execution.status == ResponseStatus.SUCCESS:
            self.response_stats['successful_responses'] += 1
        elif execution.status == ResponseStatus.FAILED:
            self.response_stats['failed_responses'] += 1
        
        if hasattr(execution, 'requires_human_approval') and execution.requires_human_approval or execution.status == ResponseStatus.REQUIRES_APPROVAL:
            self.response_stats['human_approvals_required'] += 1
        
        # Update average response time
        current_avg = self.response_stats['avg_response_time_seconds']
        total_responses = self.response_stats['total_responses']
        self.response_stats['avg_response_time_seconds'] = (
            (current_avg * (total_responses - 1) + execution_time) / total_responses
        )
    
    def get_execution_status(self, execution_id: str) -> Optional[ResponseExecution]:
        """Get the status of a specific execution."""
        execution = self.active_executions.get(execution_id)
        if not execution:
            # Check history
            for hist_exec in self.execution_history:
                if hist_exec.id == execution_id:
                    return hist_exec
        return execution
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get list of actions pending human approval."""
        approvals = []
        for handler, action, anomaly, execution in self.approval_queue:
            approvals.append({
                'execution_id': execution.id,
                'action_name': action.name,
                'action_description': action.description,
                'anomaly_metric': anomaly.metric_name,
                'anomaly_severity': anomaly.severity.value,
                'anomaly_message': anomaly.message,
                'requested_at': execution.started_at.isoformat(),
                'timeout_seconds': action.execution_timeout_seconds
            })
        return approvals
    
    def get_response_statistics(self) -> Dict[str, Any]:
        """Get response engine statistics."""
        return {
            **self.response_stats.copy(),
            'active_executions': len(self.active_executions),
            'pending_approvals': len(self.approval_queue),
            'execution_history_size': len(self.execution_history),
            'success_rate': (
                self.response_stats['successful_responses'] / max(self.response_stats['total_responses'], 1)
            ) * 100
        }
    
    def cleanup_completed_executions(self, older_than_hours: int = 24):
        """Clean up old completed executions."""
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        # Remove from active executions
        to_remove = []
        for exec_id, execution in self.active_executions.items():
            if (execution.completed_at and execution.completed_at < cutoff and 
                execution.status in [ResponseStatus.SUCCESS, ResponseStatus.FAILED, ResponseStatus.ROLLED_BACK]):
                to_remove.append(exec_id)
        
        for exec_id in to_remove:
            del self.active_executions[exec_id]
        
        logger.info(f"Cleaned up {len(to_remove)} completed executions older than {older_than_hours} hours")

# Global response engine instance
automated_response_engine = AutomatedResponseEngine()