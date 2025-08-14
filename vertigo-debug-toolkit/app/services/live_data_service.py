"""
Live Data Service for Performance Dashboard
Aggregates data from multiple sources for real-time dashboard updates.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict
from dataclasses import dataclass
from dateutil import parser as date_parser

from app.models import db
from sqlalchemy import text, func
from app.services.langwatch_client import langwatch_client
from app.services.firestore_sync import firestore_sync_service

logger = logging.getLogger(__name__)

@dataclass
class DataSourceMetrics:
    """Metrics from a specific data source."""
    source_name: str
    total_traces: int
    success_count: int
    error_count: int
    success_rate: float
    error_rate: float
    avg_latency_ms: float
    total_cost: float
    latest_trace_time: Optional[datetime]
    is_live: bool
    
class LiveDataService:
    """
    Service for aggregating performance data from multiple sources.
    
    Data Sources:
    1. Local live_traces table (from Firestore sync + webhooks)
    2. LangWatch API (direct integration)
    3. Demo data (fallback for development)
    """
    
    def __init__(self):
        """Initialize live data service."""
        self.available_sources = self._detect_available_sources()
        logger.info(f"Live data service initialized with sources: {list(self.available_sources.keys())}")
    
    def _detect_available_sources(self) -> Dict[str, bool]:
        """Detect which data sources are available."""
        sources = {}
        
        # Check database connection
        try:
            db.session.execute(text("SELECT 1")).fetchone()
            sources['database'] = True
        except Exception as e:
            logger.warning(f"Database not available: {e}")
            sources['database'] = False
        
        # Check Firestore sync
        sources['firestore'] = firestore_sync_service.is_available()
        
        # Check LangWatch client
        sources['langwatch'] = langwatch_client.is_enabled()
        
        return sources
    
    def get_unified_performance_metrics(self, hours: int = 24, data_source: str = 'all') -> Dict[str, Any]:
        """
        Get unified performance metrics from all available sources.
        
        Args:
            hours: Time window in hours
            data_source: 'all', 'database', 'langwatch', 'firestore', or specific source
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            if data_source == 'all':
                return self._aggregate_all_sources(start_time, end_time, hours)
            elif data_source == 'database':
                return self._get_database_metrics(start_time, end_time, hours)
            elif data_source == 'langwatch':
                return self._get_langwatch_metrics(hours)
            elif data_source == 'firestore':
                return self._get_firestore_metrics(start_time, end_time, hours)
            else:
                logger.warning(f"Unknown data source: {data_source}")
                return self._get_fallback_metrics(hours)
                
        except Exception as e:
            logger.error(f"Error getting unified performance metrics: {e}")
            return self._get_fallback_metrics(hours)
    
    def _aggregate_all_sources(self, start_time: datetime, end_time: datetime, hours: int) -> Dict[str, Any]:
        """Aggregate metrics from all available sources."""
        aggregated_metrics = {
            'total_traces': 0,
            'success_count': 0,
            'error_count': 0,
            'success_rate': 0.0,
            'error_rate': 0.0,
            'avg_latency_ms': 0.0,
            'total_cost': 0.0,
            'period_hours': hours,
            'timestamp': datetime.utcnow().isoformat(),
            'data_sources': [],
            'source_breakdown': {}
        }
        
        source_metrics = []
        total_traces_across_sources = 0
        total_latency_weighted = 0
        total_cost_across_sources = 0
        
        # Get metrics from each available source
        if self.available_sources.get('database', False):
            db_metrics = self._get_database_metrics(start_time, end_time, hours)
            if db_metrics['total_traces'] > 0:
                source_metrics.append(('database', db_metrics))
        
        if self.available_sources.get('langwatch', False):
            lw_metrics = self._get_langwatch_metrics(hours)
            if lw_metrics['total_traces'] > 0:
                source_metrics.append(('langwatch', lw_metrics))
        
        # Aggregate the metrics
        for source_name, metrics in source_metrics:
            traces = metrics['total_traces']
            total_traces_across_sources += traces
            
            aggregated_metrics['success_count'] += metrics.get('success_count', 0)
            aggregated_metrics['error_count'] += metrics.get('error_count', 0)
            
            # Weight latency by number of traces
            avg_latency = metrics.get('avg_latency_ms', 0)
            if traces > 0 and avg_latency > 0:
                total_latency_weighted += avg_latency * traces
            
            total_cost_across_sources += metrics.get('total_cost', 0)
            
            # Store individual source data
            aggregated_metrics['source_breakdown'][source_name] = {
                'traces': traces,
                'success_rate': metrics['success_rate'],
                'avg_latency': metrics.get('avg_latency_ms', 0),
                'cost': metrics['total_cost'],
                'is_live': metrics.get('is_live', False)
            }
            
            aggregated_metrics['data_sources'].append({
                'name': source_name,
                'traces': traces,
                'is_live': metrics.get('is_live', False)
            })
        
        # Calculate aggregated values
        aggregated_metrics['total_traces'] = total_traces_across_sources
        aggregated_metrics['total_cost'] = total_cost_across_sources
        
        if total_traces_across_sources > 0:
            aggregated_metrics['success_rate'] = round(
                (aggregated_metrics['success_count'] / total_traces_across_sources) * 100, 2
            )
            aggregated_metrics['error_rate'] = round(
                (aggregated_metrics['error_count'] / total_traces_across_sources) * 100, 2
            )
            
            if total_latency_weighted > 0:
                aggregated_metrics['avg_latency_ms'] = round(
                    total_latency_weighted / total_traces_across_sources, 2
                )
        
        # If no real data, use fallback
        if total_traces_across_sources == 0:
            return self._get_fallback_metrics(hours)
        
        return aggregated_metrics
    
    def _get_database_metrics(self, start_time: datetime, end_time: datetime, hours: int) -> Dict[str, Any]:
        """Get metrics from local live_traces database."""
        try:
            # Query live traces within time window
            result = db.session.execute(
                text("""
                SELECT 
                    COUNT(*) as total_traces,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status IN ('error', 'failed') THEN 1 ELSE 0 END) as error_count,
                    AVG(duration_ms) as avg_latency,
                    SUM(cost_usd) as total_cost,
                    MAX(start_time) as latest_trace_time
                FROM live_traces 
                WHERE start_time >= :start_time 
                AND start_time <= :end_time
                """),
                {"start_time": start_time, "end_time": end_time}
            ).fetchone()
            
            if result and result[0] > 0:
                total_traces = result[0] or 0
                success_count = result[1] or 0
                error_count = result[2] or 0
                avg_latency = result[3] or 0.0
                total_cost = result[4] or 0.0
                latest_trace_time = result[5]
                
                return {
                    'total_traces': total_traces,
                    'success_count': success_count,
                    'error_count': error_count,
                    'success_rate': round((success_count / total_traces) * 100, 2) if total_traces > 0 else 0,
                    'error_rate': round((error_count / total_traces) * 100, 2) if total_traces > 0 else 0,
                    'avg_latency_ms': round(avg_latency, 2),
                    'total_cost': round(total_cost, 4),
                    'period_hours': hours,
                    'latest_trace_time': self._parse_datetime(latest_trace_time).isoformat() if latest_trace_time else None,
                    'is_live': True,
                    'source': 'database'
                }
            
            # No data in database
            return {
                'total_traces': 0,
                'success_count': 0,
                'error_count': 0,
                'success_rate': 0,
                'error_rate': 0,
                'avg_latency_ms': 0,
                'total_cost': 0,
                'period_hours': hours,
                'is_live': False,
                'source': 'database'
            }
            
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {
                'total_traces': 0,
                'success_count': 0,
                'error_count': 0,
                'success_rate': 0,
                'error_rate': 0,
                'avg_latency_ms': 0,
                'total_cost': 0,
                'period_hours': hours,
                'is_live': False,
                'source': 'database',
                'error': str(e)
            }
    
    def _get_langwatch_metrics(self, hours: int) -> Dict[str, Any]:
        """Get metrics from LangWatch API."""
        try:
            if not langwatch_client.is_enabled():
                return {
                    'total_traces': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'success_rate': 0,
                    'error_rate': 0,
                    'avg_latency_ms': 0,
                    'total_cost': 0,
                    'period_hours': hours,
                    'is_live': False,
                    'source': 'langwatch'
                }
            
            metrics = langwatch_client.get_performance_metrics(hours)
            metrics['is_live'] = True
            metrics['source'] = 'langwatch'
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting LangWatch metrics: {e}")
            return {
                'total_traces': 0,
                'success_count': 0,
                'error_count': 0,
                'success_rate': 0,
                'error_rate': 0,
                'avg_latency_ms': 0,
                'total_cost': 0,
                'period_hours': hours,
                'is_live': False,
                'source': 'langwatch',
                'error': str(e)
            }
    
    def _get_firestore_metrics(self, start_time: datetime, end_time: datetime, hours: int) -> Dict[str, Any]:
        """Get metrics specifically from Firestore synced data."""
        try:
            # Query only Firestore-sourced data
            result = db.session.execute(
                text("""
                SELECT 
                    COUNT(*) as total_traces,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status IN ('error', 'failed') THEN 1 ELSE 0 END) as error_count,
                    AVG(duration_ms) as avg_latency,
                    SUM(cost_usd) as total_cost
                FROM live_traces lt
                JOIN data_sources ds ON lt.data_source_id = ds.id
                WHERE ds.name = 'firestore'
                AND lt.start_time >= :start_time 
                AND lt.start_time <= :end_time
                """),
                {"start_time": start_time, "end_time": end_time}
            ).fetchone()
            
            if result and result[0] > 0:
                total_traces = result[0] or 0
                success_count = result[1] or 0
                error_count = result[2] or 0
                avg_latency = result[3] or 0.0
                total_cost = result[4] or 0.0
                
                return {
                    'total_traces': total_traces,
                    'success_count': success_count,
                    'error_count': error_count,
                    'success_rate': round((success_count / total_traces) * 100, 2) if total_traces > 0 else 0,
                    'error_rate': round((error_count / total_traces) * 100, 2) if total_traces > 0 else 0,
                    'avg_latency_ms': round(avg_latency, 2),
                    'total_cost': round(total_cost, 4),
                    'period_hours': hours,
                    'is_live': firestore_sync_service.is_available(),
                    'source': 'firestore'
                }
            
            return {
                'total_traces': 0,
                'success_count': 0,
                'error_count': 0,
                'success_rate': 0,
                'error_rate': 0,
                'avg_latency_ms': 0,
                'total_cost': 0,
                'period_hours': hours,
                'is_live': False,
                'source': 'firestore'
            }
            
        except Exception as e:
            logger.error(f"Error getting Firestore metrics: {e}")
            return {
                'total_traces': 0,
                'success_count': 0,
                'error_count': 0,
                'success_rate': 0,
                'error_rate': 0,
                'avg_latency_ms': 0,
                'total_cost': 0,
                'period_hours': hours,
                'is_live': False,
                'source': 'firestore',
                'error': str(e)
            }
    
    def _get_fallback_metrics(self, hours: int) -> Dict[str, Any]:
        """Get fallback demo metrics when no live data is available."""
        logger.info("Using fallback demo metrics - no live data sources available")
        
        # Use LangWatch client's demo data generation
        demo_metrics = langwatch_client._generate_demo_performance_data(hours)
        demo_metrics.update({
            'data_sources': [{'name': 'demo', 'traces': demo_metrics['total_traces'], 'is_live': False}],
            'source_breakdown': {
                'demo': {
                    'traces': demo_metrics['total_traces'],
                    'success_rate': demo_metrics['success_rate'],
                    'avg_latency': demo_metrics['average_latency_ms'],
                    'cost': demo_metrics['total_cost'],
                    'is_live': False
                }
            },
            'is_fallback': True
        })
        
        return demo_metrics
    
    def get_latency_time_series(self, hours: int = 24, data_source: str = 'all') -> List[Dict]:
        """Get latency time series data."""
        try:
            if data_source == 'database' or data_source == 'all':
                return self._get_database_latency_series(hours)
            elif data_source == 'langwatch':
                return langwatch_client.get_latency_time_series(hours)
            else:
                return langwatch_client._generate_demo_latency_series(hours)
                
        except Exception as e:
            logger.error(f"Error getting latency time series: {e}")
            return langwatch_client._generate_demo_latency_series(hours)
    
    def _get_database_latency_series(self, hours: int) -> List[Dict]:
        """Get latency time series from database."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Group by hour and calculate metrics
            result = db.session.execute(
                text("""
                SELECT 
                    strftime('%Y-%m-%dT%H:00:00Z', start_time) as hour_bucket,
                    AVG(duration_ms) as avg_latency,
                    MAX(duration_ms) as max_latency,
                    COUNT(*) as trace_count
                FROM live_traces 
                WHERE start_time >= :start_time 
                AND start_time <= :end_time
                AND duration_ms IS NOT NULL
                GROUP BY strftime('%Y-%m-%dT%H:00:00Z', start_time)
                ORDER BY hour_bucket
                """),
                {"start_time": start_time, "end_time": end_time}
            ).fetchall()
            
            time_series = []
            for row in result:
                time_series.append({
                    'time': row[0],
                    'latency_avg': round(row[1] or 0, 2),
                    'latency_p95': round((row[2] or 0) * 0.95, 2),  # Approximation
                    'trace_count': row[3] or 0
                })
            
            # Fill in missing hours with zero values if needed
            if len(time_series) < hours:
                filled_series = []
                current_time = start_time
                existing_data = {item['time']: item for item in time_series}
                
                for i in range(hours):
                    hour_key = current_time.strftime('%Y-%m-%dT%H:00:00Z')
                    if hour_key in existing_data:
                        filled_series.append(existing_data[hour_key])
                    else:
                        filled_series.append({
                            'time': hour_key,
                            'latency_avg': 0,
                            'latency_p95': 0,
                            'trace_count': 0
                        })
                    current_time += timedelta(hours=1)
                
                return filled_series
            
            return time_series
            
        except Exception as e:
            logger.error(f"Error getting database latency series: {e}")
            return langwatch_client._generate_demo_latency_series(hours)
    
    def get_recent_traces(self, limit: int = 20, data_source: str = 'all') -> List[Dict]:
        """Get recent traces from available sources."""
        try:
            if data_source == 'database' or data_source == 'all':
                return self._get_recent_traces_from_db(limit)
            elif data_source == 'langwatch':
                return langwatch_client.get_recent_traces_for_display(limit)
            else:
                return langwatch_client._generate_demo_traces(limit)
                
        except Exception as e:
            logger.error(f"Error getting recent traces: {e}")
            return langwatch_client._generate_demo_traces(limit)
    
    def _get_recent_traces_from_db(self, limit: int) -> List[Dict]:
        """Get recent traces from local database."""
        try:
            result = db.session.execute(
                text("""
                SELECT 
                    external_trace_id,
                    name,
                    status,
                    duration_ms,
                    start_time,
                    cost_usd,
                    user_id,
                    model
                FROM live_traces 
                ORDER BY start_time DESC 
                LIMIT :limit
                """),
                {"limit": limit}
            ).fetchall()
            
            traces = []
            for row in result:
                traces.append({
                    'id': row[0] or 'unknown',
                    'name': row[1] or 'Unnamed Operation',
                    'status': row[2] or 'unknown',
                    'latency': row[3] or 0,
                    'timestamp': self._parse_datetime(row[4]).isoformat() + 'Z' if row[4] else datetime.utcnow().isoformat() + 'Z',
                    'cost': row[5] or 0,
                    'user_id': row[6],
                    'model': row[7] or 'Unknown'
                })
            
            return traces
            
        except Exception as e:
            logger.error(f"Error getting traces from database: {e}")
            return langwatch_client._generate_demo_traces(limit)
    
    def _parse_datetime(self, date_value: Any) -> datetime:
        """Parse datetime from various formats (string, datetime object)."""
        if isinstance(date_value, datetime):
            return date_value
        elif isinstance(date_value, str):
            try:
                return date_parser.parse(date_value)
            except Exception:
                # Fallback to current time if parsing fails
                return datetime.utcnow()
        else:
            return datetime.utcnow()
    
    def get_data_source_status(self) -> Dict[str, Any]:
        """Get status of all data sources."""
        try:
            # Refresh availability
            self.available_sources = self._detect_available_sources()
            
            source_statuses = {}
            
            # Database status
            if self.available_sources.get('database', False):
                try:
                    count = db.session.execute(text("SELECT COUNT(*) FROM live_traces")).fetchone()[0]
                    source_statuses['database'] = {
                        'available': True,
                        'total_traces': count,
                        'description': 'Local SQLite database with live traces',
                        'health': 'healthy'
                    }
                except Exception as e:
                    source_statuses['database'] = {
                        'available': False,
                        'error': str(e),
                        'description': 'Local SQLite database',
                        'health': 'unhealthy'
                    }
            else:
                source_statuses['database'] = {
                    'available': False,
                    'description': 'Local SQLite database not accessible',
                    'health': 'unhealthy'
                }
            
            # Firestore status
            source_statuses['firestore'] = {
                'available': self.available_sources.get('firestore', False),
                'description': 'Google Firestore sync service',
                'health': 'healthy' if firestore_sync_service.is_available() else 'unhealthy'
            }
            
            # LangWatch status
            source_statuses['langwatch'] = {
                'available': self.available_sources.get('langwatch', False),
                'description': 'LangWatch API integration',
                'health': 'healthy' if langwatch_client.is_enabled() else 'degraded'
            }
            
            return {
                'sources': source_statuses,
                'total_available': sum(1 for s in source_statuses.values() if s['available']),
                'all_healthy': all(s.get('health') == 'healthy' for s in source_statuses.values()),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting data source status: {e}")
            return {
                'sources': {},
                'total_available': 0,
                'all_healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Global service instance
live_data_service = LiveDataService()