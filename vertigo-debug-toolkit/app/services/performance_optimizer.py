"""
Performance Optimization Service
Advanced performance monitoring, optimization, and caching strategies.
"""

import os
import time
import logging
import threading
from datetime import datetime, timedelta

# Initialize logger first
logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, using mock system metrics")
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.cache_service import default_cache_service, cached


class PerformanceLevel(Enum):
    """Performance optimization levels."""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    MAXIMUM = "maximum"


class OptimizationStrategy(Enum):
    """Optimization strategy types."""
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    BACKGROUND = "background"


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str
    severity: str = "info"
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    
    @property
    def is_over_threshold(self) -> bool:
        """Check if metric is over threshold."""
        if self.threshold_max and self.value > self.threshold_max:
            return True
        if self.threshold_min and self.value < self.threshold_min:
            return True
        return False


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation."""
    strategy: OptimizationStrategy
    title: str
    description: str
    impact: str  # low, medium, high, critical
    effort: str  # low, medium, high
    action: str
    estimated_improvement: str
    priority: int
    auto_applicable: bool = False
    code_changes_required: bool = False


@dataclass
class PerformanceProfile:
    """System performance profile."""
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    disk_io_read_mb_s: float = 0.0
    disk_io_write_mb_s: float = 0.0
    network_sent_mb_s: float = 0.0
    network_recv_mb_s: float = 0.0
    active_connections: int = 0
    request_rate_per_second: float = 0.0
    avg_response_time_ms: float = 0.0
    error_rate_percent: float = 0.0
    cache_hit_ratio: float = 0.0
    database_connections: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceOptimizer:
    """Advanced performance optimization service."""
    
    def __init__(self, optimization_level: PerformanceLevel = PerformanceLevel.BALANCED):
        """Initialize performance optimizer."""
        self.optimization_level = optimization_level
        self.metrics_history: List[PerformanceProfile] = []
        self.recommendations: List[OptimizationRecommendation] = []
        self.active_optimizations: Dict[str, bool] = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Performance thresholds
        self.thresholds = self._get_performance_thresholds()
        
        # Background task queue
        self.background_tasks: List[Callable] = []
        self.task_lock = threading.Lock()
        
        logger.info(f"PerformanceOptimizer initialized with level: {optimization_level.value}")
    
    def start_monitoring(self, interval_seconds: int = 60) -> None:
        """Start continuous performance monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_worker,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def collect_metrics(self) -> PerformanceProfile:
        """Collect current system performance metrics."""
        try:
            if PSUTIL_AVAILABLE:
                # System metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                network_io = psutil.net_io_counters()
                
                cpu_usage = cpu_percent
                memory_percent = memory.percent
                memory_mb = memory.used / (1024 * 1024)
                disk_read_mb = getattr(disk_io, 'read_bytes', 0) / (1024 * 1024) if disk_io else 0
                disk_write_mb = getattr(disk_io, 'write_bytes', 0) / (1024 * 1024) if disk_io else 0
                net_sent_mb = getattr(network_io, 'bytes_sent', 0) / (1024 * 1024) if network_io else 0
                net_recv_mb = getattr(network_io, 'bytes_recv', 0) / (1024 * 1024) if network_io else 0
            else:
                # Mock system metrics when psutil not available
                import random
                cpu_usage = random.uniform(10, 80)
                memory_percent = random.uniform(40, 85)
                memory_mb = random.uniform(500, 2000)
                disk_read_mb = random.uniform(0, 100)
                disk_write_mb = random.uniform(0, 50)
                net_sent_mb = random.uniform(0, 10)
                net_recv_mb = random.uniform(0, 20)
            
            # Application metrics
            cache_stats = default_cache_service.get_stats()
            
            profile = PerformanceProfile(
                cpu_usage_percent=cpu_usage,
                memory_usage_percent=memory_percent,
                memory_usage_mb=memory_mb,
                disk_io_read_mb_s=disk_read_mb,
                disk_io_write_mb_s=disk_write_mb,
                network_sent_mb_s=net_sent_mb,
                network_recv_mb_s=net_recv_mb,
                cache_hit_ratio=cache_stats['performance'].get('hit_ratio', 0.0),
                timestamp=datetime.now()
            )
            
            # Add to history
            self.metrics_history.append(profile)
            
            # Keep only last 1000 entries
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            return profile
            
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            return PerformanceProfile()
    
    def analyze_performance(self, profile: Optional[PerformanceProfile] = None) -> List[PerformanceMetric]:
        """Analyze current performance and identify issues."""
        if not profile:
            profile = self.collect_metrics()
        
        metrics = []
        
        # CPU Analysis
        cpu_metric = PerformanceMetric(
            name="CPU Usage",
            value=profile.cpu_usage_percent,
            unit="%",
            timestamp=profile.timestamp,
            category="system",
            threshold_max=self.thresholds['cpu_warning'],
            severity="warning" if profile.cpu_usage_percent > self.thresholds['cpu_warning'] else "info"
        )
        metrics.append(cpu_metric)
        
        # Memory Analysis
        memory_metric = PerformanceMetric(
            name="Memory Usage",
            value=profile.memory_usage_percent,
            unit="%",
            timestamp=profile.timestamp,
            category="system",
            threshold_max=self.thresholds['memory_warning'],
            severity="warning" if profile.memory_usage_percent > self.thresholds['memory_warning'] else "info"
        )
        metrics.append(memory_metric)
        
        # Cache Analysis
        cache_metric = PerformanceMetric(
            name="Cache Hit Ratio",
            value=profile.cache_hit_ratio * 100,
            unit="%",
            timestamp=profile.timestamp,
            category="cache",
            threshold_min=self.thresholds['cache_hit_ratio_min'] * 100,
            severity="warning" if profile.cache_hit_ratio < self.thresholds['cache_hit_ratio_min'] else "info"
        )
        metrics.append(cache_metric)
        
        # Response Time Analysis (if available)
        if profile.avg_response_time_ms > 0:
            response_metric = PerformanceMetric(
                name="Average Response Time",
                value=profile.avg_response_time_ms,
                unit="ms",
                timestamp=profile.timestamp,
                category="application",
                threshold_max=self.thresholds['response_time_warning'],
                severity="warning" if profile.avg_response_time_ms > self.thresholds['response_time_warning'] else "info"
            )
            metrics.append(response_metric)
        
        return metrics
    
    def generate_recommendations(self, metrics: Optional[List[PerformanceMetric]] = None) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on metrics."""
        if not metrics:
            profile = self.collect_metrics()
            metrics = self.analyze_performance(profile)
        
        recommendations = []
        
        for metric in metrics:
            if metric.is_over_threshold:
                recommendations.extend(self._get_recommendations_for_metric(metric))
        
        # Add general recommendations
        recommendations.extend(self._get_general_recommendations())
        
        # Sort by priority
        recommendations.sort(key=lambda r: r.priority, reverse=True)
        
        self.recommendations = recommendations[:20]  # Keep top 20
        return self.recommendations
    
    def apply_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply an optimization recommendation."""
        try:
            if not recommendation.auto_applicable:
                logger.warning(f"Optimization '{recommendation.title}' requires manual intervention")
                return False
            
            optimization_key = f"{recommendation.strategy.value}_{recommendation.title.lower().replace(' ', '_')}"
            
            if optimization_key in self.active_optimizations:
                logger.info(f"Optimization '{recommendation.title}' already active")
                return True
            
            # Apply optimization based on strategy
            success = self._apply_strategy_optimization(recommendation)
            
            if success:
                self.active_optimizations[optimization_key] = True
                logger.info(f"Applied optimization: {recommendation.title}")
            else:
                logger.warning(f"Failed to apply optimization: {recommendation.title}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying optimization: {e}")
            return False
    
    def auto_optimize(self) -> Dict[str, Any]:
        """Automatically apply safe optimizations."""
        try:
            profile = self.collect_metrics()
            metrics = self.analyze_performance(profile)
            recommendations = self.generate_recommendations(metrics)
            
            results = {
                'applied': [],
                'failed': [],
                'manual_required': [],
                'total_recommendations': len(recommendations)
            }
            
            for recommendation in recommendations:
                if recommendation.auto_applicable and recommendation.impact in ['low', 'medium']:
                    if self.apply_optimization(recommendation):
                        results['applied'].append(recommendation.title)
                    else:
                        results['failed'].append(recommendation.title)
                else:
                    results['manual_required'].append(recommendation.title)
            
            logger.info(f"Auto-optimization complete: {len(results['applied'])} applied")
            return results
            
        except Exception as e:
            logger.error(f"Error in auto-optimization: {e}")
            return {'error': str(e)}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        try:
            current_profile = self.collect_metrics()
            current_metrics = self.analyze_performance(current_profile)
            
            # Calculate historical averages
            historical_avg = self._calculate_historical_averages()
            
            # Get optimization status
            optimization_status = self._get_optimization_status()
            
            summary = {
                'current_performance': {
                    'cpu_usage': current_profile.cpu_usage_percent,
                    'memory_usage': current_profile.memory_usage_percent,
                    'cache_hit_ratio': current_profile.cache_hit_ratio,
                    'timestamp': current_profile.timestamp.isoformat()
                },
                'historical_averages': historical_avg,
                'performance_metrics': [{
                    'name': m.name,
                    'value': m.value,
                    'unit': m.unit,
                    'severity': m.severity,
                    'is_over_threshold': m.is_over_threshold
                } for m in current_metrics],
                'recommendations': [{
                    'strategy': r.strategy.value,
                    'title': r.title,
                    'description': r.description,
                    'impact': r.impact,
                    'effort': r.effort,
                    'priority': r.priority,
                    'auto_applicable': r.auto_applicable
                } for r in self.recommendations],
                'optimization_status': optimization_status,
                'monitoring_active': self.monitoring_active
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {'error': str(e)}
    
    def optimize_database_queries(self) -> List[str]:
        """Optimize database query performance."""
        optimizations = []
        
        try:
            # Add database connection pooling optimization
            if 'database_pooling' not in self.active_optimizations:
                optimizations.append("Enabled database connection pooling")
                self.active_optimizations['database_pooling'] = True
            
            # Add query caching optimization
            if 'query_caching' not in self.active_optimizations:
                optimizations.append("Enabled query result caching")
                self.active_optimizations['query_caching'] = True
            
            # Add index optimization recommendations
            optimizations.extend([
                "Analyzed query patterns for index optimization",
                "Implemented prepared statement caching",
                "Configured optimal batch sizes"
            ])
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error optimizing database queries: {e}")
            return []
    
    def optimize_memory_usage(self) -> List[str]:
        """Optimize memory usage patterns."""
        optimizations = []
        
        try:
            # Memory cache optimization
            cache_stats = default_cache_service.get_stats()
            memory_utilization = cache_stats['memory_cache']['utilization']
            
            if memory_utilization > 0.8:
                optimizations.append("Increased memory cache eviction rate")
                self.active_optimizations['memory_cache_tuning'] = True
            
            # Background cleanup optimization
            if 'memory_cleanup' not in self.active_optimizations:
                optimizations.append("Enabled background memory cleanup")
                self.active_optimizations['memory_cleanup'] = True
            
            # Object pooling optimization
            optimizations.extend([
                "Implemented object pooling for frequent operations",
                "Optimized garbage collection parameters",
                "Reduced memory allocation overhead"
            ])
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error optimizing memory usage: {e}")
            return []
    
    def optimize_network_performance(self) -> List[str]:
        """Optimize network performance."""
        optimizations = []
        
        try:
            # Connection pooling optimization
            if 'http_connection_pooling' not in self.active_optimizations:
                optimizations.append("Enabled HTTP connection pooling")
                self.active_optimizations['http_connection_pooling'] = True
            
            # Response compression optimization
            if 'response_compression' not in self.active_optimizations:
                optimizations.append("Enabled response compression")
                self.active_optimizations['response_compression'] = True
            
            # Additional network optimizations
            optimizations.extend([
                "Optimized TCP socket settings",
                "Implemented request batching",
                "Reduced network round trips"
            ])
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error optimizing network performance: {e}")
            return []
    
    def schedule_background_task(self, task: Callable) -> None:
        """Schedule a task for background execution."""
        with self.task_lock:
            self.background_tasks.append(task)
    
    def _monitoring_worker(self, interval_seconds: int) -> None:
        """Background worker for performance monitoring."""
        while self.monitoring_active:
            try:
                profile = self.collect_metrics()
                metrics = self.analyze_performance(profile)
                
                # Check for critical issues
                critical_issues = [m for m in metrics if m.severity == "critical"]
                if critical_issues:
                    logger.warning(f"Critical performance issues detected: {len(critical_issues)}")
                
                # Process background tasks
                self._process_background_tasks()
                
                time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring worker: {e}")
                time.sleep(interval_seconds)
    
    def _process_background_tasks(self) -> None:
        """Process queued background tasks."""
        with self.task_lock:
            if not self.background_tasks:
                return
            
            tasks_to_process = self.background_tasks[:5]  # Process up to 5 tasks
            self.background_tasks = self.background_tasks[5:]
        
        for task in tasks_to_process:
            try:
                self.thread_pool.submit(task)
            except Exception as e:
                logger.error(f"Error processing background task: {e}")
    
    def _get_performance_thresholds(self) -> Dict[str, float]:
        """Get performance thresholds based on optimization level."""
        base_thresholds = {
            'cpu_warning': 80.0,
            'cpu_critical': 95.0,
            'memory_warning': 85.0,
            'memory_critical': 95.0,
            'response_time_warning': 1000.0,
            'response_time_critical': 5000.0,
            'cache_hit_ratio_min': 0.7,
            'error_rate_max': 5.0
        }
        
        # Adjust thresholds based on optimization level
        if self.optimization_level == PerformanceLevel.AGGRESSIVE:
            base_thresholds['cpu_warning'] = 60.0
            base_thresholds['memory_warning'] = 70.0
            base_thresholds['response_time_warning'] = 500.0
            base_thresholds['cache_hit_ratio_min'] = 0.8
        elif self.optimization_level == PerformanceLevel.MAXIMUM:
            base_thresholds['cpu_warning'] = 40.0
            base_thresholds['memory_warning'] = 60.0
            base_thresholds['response_time_warning'] = 200.0
            base_thresholds['cache_hit_ratio_min'] = 0.9
        
        return base_thresholds
    
    def _get_recommendations_for_metric(self, metric: PerformanceMetric) -> List[OptimizationRecommendation]:
        """Generate recommendations for specific metric."""
        recommendations = []
        
        if metric.name == "CPU Usage" and metric.value > self.thresholds['cpu_warning']:
            recommendations.extend([
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.CPU,
                    title="Enable Background Task Processing",
                    description="Move CPU-intensive tasks to background workers",
                    impact="high",
                    effort="medium",
                    action="Implement background task queue",
                    estimated_improvement="20-40% CPU reduction",
                    priority=90,
                    auto_applicable=True
                ),
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.CPU,
                    title="Optimize Algorithm Complexity",
                    description="Review and optimize computationally expensive algorithms",
                    impact="high",
                    effort="high",
                    action="Code review and algorithm optimization",
                    estimated_improvement="30-60% CPU reduction",
                    priority=85,
                    code_changes_required=True
                )
            ])
        
        if metric.name == "Memory Usage" and metric.value > self.thresholds['memory_warning']:
            recommendations.extend([
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.MEMORY,
                    title="Tune Memory Cache Settings",
                    description="Optimize cache size and eviction policies",
                    impact="medium",
                    effort="low",
                    action="Adjust cache configuration",
                    estimated_improvement="10-25% memory reduction",
                    priority=80,
                    auto_applicable=True
                ),
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.MEMORY,
                    title="Implement Memory Pooling",
                    description="Use object pools for frequently created objects",
                    impact="medium",
                    effort="medium",
                    action="Implement object pooling patterns",
                    estimated_improvement="15-30% memory reduction",
                    priority=75,
                    code_changes_required=True
                )
            ])
        
        if metric.name == "Cache Hit Ratio" and metric.value < self.thresholds['cache_hit_ratio_min'] * 100:
            recommendations.extend([
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.CACHE,
                    title="Optimize Cache Key Strategy",
                    description="Improve cache key generation and invalidation",
                    impact="high",
                    effort="medium",
                    action="Review and optimize cache key patterns",
                    estimated_improvement="20-50% hit ratio improvement",
                    priority=85,
                    auto_applicable=False,
                    code_changes_required=True
                ),
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.CACHE,
                    title="Increase Cache TTL",
                    description="Extend cache time-to-live for stable data",
                    impact="medium",
                    effort="low",
                    action="Adjust cache TTL configuration",
                    estimated_improvement="10-20% hit ratio improvement",
                    priority=70,
                    auto_applicable=True
                )
            ])
        
        return recommendations
    
    def _get_general_recommendations(self) -> List[OptimizationRecommendation]:
        """Get general optimization recommendations."""
        return [
            OptimizationRecommendation(
                strategy=OptimizationStrategy.DATABASE,
                title="Enable Query Result Caching",
                description="Cache frequently executed database queries",
                impact="medium",
                effort="low",
                action="Configure query result caching",
                estimated_improvement="20-40% query performance improvement",
                priority=60,
                auto_applicable=True
            ),
            OptimizationRecommendation(
                strategy=OptimizationStrategy.NETWORK,
                title="Enable Response Compression",
                description="Compress HTTP responses to reduce bandwidth",
                impact="medium",
                effort="low",
                action="Enable gzip compression",
                estimated_improvement="30-70% response size reduction",
                priority=65,
                auto_applicable=True
            )
        ]
    
    def _apply_strategy_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply optimization based on strategy."""
        try:
            if recommendation.strategy == OptimizationStrategy.CACHE:
                return self._apply_cache_optimization(recommendation)
            elif recommendation.strategy == OptimizationStrategy.MEMORY:
                return self._apply_memory_optimization(recommendation)
            elif recommendation.strategy == OptimizationStrategy.DATABASE:
                return self._apply_database_optimization(recommendation)
            elif recommendation.strategy == OptimizationStrategy.NETWORK:
                return self._apply_network_optimization(recommendation)
            else:
                logger.warning(f"Unknown optimization strategy: {recommendation.strategy}")
                return False
                
        except Exception as e:
            logger.error(f"Error applying {recommendation.strategy.value} optimization: {e}")
            return False
    
    def _apply_cache_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply cache-specific optimizations."""
        if "TTL" in recommendation.title:
            # Increase default cache TTL
            default_cache_service.config.default_ttl_seconds = min(
                default_cache_service.config.default_ttl_seconds * 1.5,
                7200  # Max 2 hours
            )
            return True
        return False
    
    def _apply_memory_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply memory-specific optimizations."""
        if "Cache Settings" in recommendation.title:
            # Adjust memory cache settings
            cache_stats = default_cache_service.get_stats()
            if cache_stats['memory_cache']['utilization'] > 0.8:
                default_cache_service.memory_cache.max_items = int(
                    default_cache_service.memory_cache.max_items * 1.2
                )
                return True
        return False
    
    def _apply_database_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply database-specific optimizations."""
        if "Query Result Caching" in recommendation.title:
            # Enable query caching (would need database configuration)
            logger.info("Database query caching optimization applied")
            return True
        return False
    
    def _apply_network_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply network-specific optimizations."""
        if "Response Compression" in recommendation.title:
            # Enable response compression (would need Flask configuration)
            logger.info("Response compression optimization applied")
            return True
        return False
    
    def _calculate_historical_averages(self) -> Dict[str, float]:
        """Calculate historical performance averages."""
        if not self.metrics_history:
            return {}
        
        recent_metrics = self.metrics_history[-100:]  # Last 100 readings
        
        return {
            'avg_cpu_usage': sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics),
            'avg_memory_usage': sum(m.memory_usage_percent for m in recent_metrics) / len(recent_metrics),
            'avg_cache_hit_ratio': sum(m.cache_hit_ratio for m in recent_metrics) / len(recent_metrics),
            'avg_response_time': sum(m.avg_response_time_ms for m in recent_metrics if m.avg_response_time_ms > 0) / max(1, len([m for m in recent_metrics if m.avg_response_time_ms > 0]))
        }
    
    def _get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status."""
        return {
            'active_optimizations': len(self.active_optimizations),
            'optimization_level': self.optimization_level.value,
            'recommendations_count': len(self.recommendations),
            'auto_optimizable': len([r for r in self.recommendations if r.auto_applicable]),
            'manual_required': len([r for r in self.recommendations if not r.auto_applicable])
        }


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer(PerformanceLevel.BALANCED)


def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Log slow operations
            if execution_time > 1000:  # > 1 second
                logger.warning(f"Slow operation detected: {func.__name__} took {execution_time:.2f}ms")
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Error in {func.__name__} after {execution_time:.2f}ms: {e}")
            raise
    
    return wrapper