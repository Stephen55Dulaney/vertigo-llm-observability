"""
Langfuse client service for the Vertigo Debug Toolkit.
"""

import os
import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from langfuse import Langfuse
from app import db
from app.models import Trace, Cost, Prompt

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LangfuseClient:
    """Client for interacting with Langfuse API."""
    
    def __init__(self):
        """Initialize Langfuse client."""
        self.public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
        self.secret_key = os.getenv('LANGFUSE_SECRET_KEY')
        self.host = os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
        
        self.langfuse = Langfuse(
            public_key=self.public_key,
            secret_key=self.secret_key,
            host=self.host
        )
    
    def create_trace(self, name: str, metadata: Optional[Dict] = None) -> str:
        """Create a new trace in Langfuse."""
        try:
            # In Langfuse 3.x, use create_trace_id method
            trace_id = self.langfuse.create_trace_id()
            logger.info(f"Langfuse client initialized with host: {self.langfuse}")
            return trace_id
        except Exception as e:
            logger.error(f"Error creating trace {name}: {e}")
            # Fallback to generating a trace ID
            import uuid
            return str(uuid.uuid4())
    
    def create_span(self, trace_id: str, name: str, metadata: Optional[Dict] = None) -> str:
        """Create a span within a trace."""
        try:
            span = self.langfuse.start_span(
                name=name,
                metadata=metadata or {}
            )
            return span.id
        except Exception as e:
            logger.error(f"Error creating span: {e}")
            raise
    
    def update_span(self, span_id: str, metadata: Optional[Dict] = None) -> bool:
        """Update a span with additional metadata."""
        try:
            self.langfuse.update_current_span(
                metadata=metadata or {}
            )
            return True
        except Exception as e:
            logger.error(f"Error updating span: {e}")
            return False
    
    def create_generation(self, trace_id: str, model: str, prompt: str, 
                         completion: str, metadata: Optional[Dict] = None) -> str:
        """Create a generation (LLM call) within a trace."""
        try:
            generation = self.langfuse.start_generation(
                name=f"llm_call_{model}",
                model=model,
                input=prompt,
                output=completion,
                metadata=metadata or {}
            )
            # End the generation immediately since we have the output
            generation.end()
            return generation.id if hasattr(generation, 'id') else str(generation)
        except Exception as e:
            logger.error(f"Error creating generation: {e}")
            # Return a fallback ID
            import uuid
            return str(uuid.uuid4())
    
    def get_traces(self, limit=50, offset=0):
        """Get traces from Langfuse."""
        try:
            # Use the correct method for Langfuse 3.x
            traces = self.langfuse.api.trace.list(limit=limit)
            return traces
        except Exception as e:
            logger.error(f"Error getting traces: {e}")
            return []

    def get_trace(self, trace_id):
        """Get a specific trace by ID."""
        try:
            trace = self.langfuse.api.trace.get(trace_id)
            return trace
        except Exception as e:
            logger.error(f"Error getting trace {trace_id}: {e}")
            return None

    def get_prompts(self, limit=50, offset=0):
        """Get prompts from Langfuse."""
        try:
            # Use the correct method for Langfuse 3.x
            prompts = self.langfuse.prompts.list(limit=limit, offset=offset)
            return prompts
        except Exception as e:
            logger.error(f"Error getting prompts: {e}")
            return []
    
    def create_prompt(self, name: str, prompt: str, tags: Optional[List[str]] = None) -> str:
        """Create a new prompt in Langfuse."""
        try:
            prompt_obj = self.langfuse.prompts.create(
                name=name,
                prompt=prompt,
                tags=tags or []
            )
            return prompt_obj.id
        except Exception as e:
            logger.error(f"Error creating prompt: {e}")
            raise
    
    def update_prompt(self, prompt_id: str, prompt: str, tags: Optional[List[str]] = None) -> bool:
        """Update an existing prompt in Langfuse."""
        try:
            self.langfuse.prompts.update(
                id=prompt_id,
                prompt=prompt,
                tags=tags or []
            )
            return True
        except Exception as e:
            logger.error(f"Error updating prompt {prompt_id}: {e}")
            return False
    
    def get_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get metrics from Langfuse."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get traces for the period
            traces = self.langfuse.api.trace.list(
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate metrics
            total_traces = len(traces.data)
            error_traces = sum(1 for t in traces.data if t.status == 'error')
            success_rate = ((total_traces - error_traces) / total_traces * 100) if total_traces > 0 else 0
            
            # Calculate average latency
            latencies = [t.latency for t in traces.data if t.latency]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            return {
                'total_traces': total_traces,
                'error_count': error_traces,
                'success_rate': round(success_rate, 2),
                'avg_latency_ms': round(avg_latency, 2),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
    
    def sync_traces_to_db(self, limit: int = 1000) -> int:
        """Sync traces from Langfuse to local database."""
        try:
            traces = self.get_traces(limit=limit)
            synced_count = 0
            
            for trace_data in traces.data:
                # Check if trace already exists
                existing_trace = Trace.query.filter_by(trace_id=trace_data.id).first()
                if existing_trace:
                    continue
                
                # Create new trace record
                trace = Trace(
                    trace_id=trace_data.id,
                    name=trace_data.name,
                    status=trace_data.status,
                    start_time=datetime.fromisoformat(trace_data.timestamp.replace('Z', '+00:00')),
                    end_time=datetime.fromisoformat(trace_data.end_time.replace('Z', '+00:00')) if trace_data.end_time else None,
                    duration_ms=trace_data.latency or 0,
                    trace_metadata=trace_data.metadata or {},
                    error_message=trace_data.error or '',
                    vertigo_operation=trace_data.metadata.get('operation') if trace_data.metadata else None,
                    project=trace_data.metadata.get('project') if trace_data.metadata else None,
                    meeting_id=trace_data.metadata.get('meeting_id') if trace_data.metadata else None
                )
                
                db.session.add(trace)
                synced_count += 1
            
            db.session.commit()
            logger.info(f"Synced {synced_count} traces to database")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing traces: {e}")
            db.session.rollback()
            return 0
    
    def sync_prompts_to_db(self) -> int:
        """Sync prompts from Langfuse to local database."""
        try:
            prompts = self.get_prompts()
            synced_count = 0
            
            for prompt_data in prompts.data:
                # Check if prompt already exists
                existing_prompt = Prompt.query.filter_by(
                    langfuse_prompt_id=prompt_data.id
                ).first()
                
                if existing_prompt:
                    # Update existing prompt
                    existing_prompt.content = prompt_data.prompt
                    existing_prompt.tags = prompt_data.tags or []
                    existing_prompt.updated_at = datetime.utcnow()
                else:
                    # Create new prompt record
                    prompt = Prompt(
                        name=prompt_data.name,
                        version='1.0',
                        content=prompt_data.prompt,
                        prompt_type='custom',  # Default type
                        tags=prompt_data.tags or [],
                        langfuse_prompt_id=prompt_data.id,
                        creator_id=1  # Default to admin user
                    )
                    db.session.add(prompt)
                
                synced_count += 1
            
            db.session.commit()
            logger.info(f"Synced {synced_count} prompts to database")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing prompts: {e}")
            db.session.rollback()
            return 0
    
    def get_cost_data(self, days: int = 7) -> List[Dict]:
        """Get cost data from Langfuse."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get generations (LLM calls) for the period
            generations = self.langfuse.generations.list(
                start_date=start_date,
                end_date=end_date
            )
            
            cost_data = []
            for gen in generations.data:
                # Calculate cost based on model and tokens
                cost = self._calculate_cost(gen.model, gen.prompt_tokens, gen.completion_tokens)
                
                cost_data.append({
                    'id': gen.id,
                    'model': gen.model,
                    'input_tokens': gen.prompt_tokens or 0,
                    'output_tokens': gen.completion_tokens or 0,
                    'total_tokens': (gen.prompt_tokens or 0) + (gen.completion_tokens or 0),
                    'cost_usd': cost,
                    'timestamp': gen.timestamp
                })
            
            return cost_data
            
        except Exception as e:
            logger.error(f"Error getting cost data: {e}")
            return []
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model and token usage."""
        # Cost per 1K tokens (approximate)
        costs = {
            'gemini-1.5-pro': {'input': 0.0035, 'output': 0.0105},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
            'claude-3-opus': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015}
        }
        
        model_costs = costs.get(model, {'input': 0.01, 'output': 0.02})
        
        input_cost = (input_tokens / 1000) * model_costs['input']
        output_cost = (output_tokens / 1000) * model_costs['output']
        
        return round(input_cost + output_cost, 6)
    
    def _make_metrics_api_request(self, query: Dict) -> Optional[Dict]:
        """Make a request to the Langfuse Metrics API."""
        try:
            import base64
            
            # Create basic auth header
            credentials = f"{self.public_key}:{self.secret_key}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json'
            }
            
            # URL encode the JSON query
            import urllib.parse
            query_param = urllib.parse.urlencode({'query': json.dumps(query)})
            
            url = f"{self.host}/api/public/metrics?{query_param}"
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error making Metrics API request: {e}")
            return None
    
    def get_real_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get real performance metrics from Langfuse Metrics API."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            from_timestamp = start_time.isoformat() + 'Z'
            to_timestamp = end_time.isoformat() + 'Z'
            
            # Query for trace counts with time dimension
            trace_count_query = {
                "view": "traces",
                "metrics": [{"measure": "count", "aggregation": "count"}],
                "dimensions": [],
                "timeDimension": {"granularity": "hour"},
                "fromTimestamp": from_timestamp,
                "toTimestamp": to_timestamp,
                "filters": []
            }
            
            # Query for latency metrics
            latency_query = {
                "view": "traces", 
                "metrics": [
                    {"measure": "latency", "aggregation": "avg"},
                    {"measure": "latency", "aggregation": "p95"},
                    {"measure": "latency", "aggregation": "max"}
                ],
                "dimensions": [],
                "timeDimension": {"granularity": "hour"},
                "fromTimestamp": from_timestamp,
                "toTimestamp": to_timestamp,
                "filters": []
            }
            
            # Query for error rates (traces with errors)
            error_query = {
                "view": "traces",
                "metrics": [{"measure": "count", "aggregation": "count"}],
                "dimensions": [],
                "filters": [{"column": "level", "operator": "=", "value": "ERROR", "type": "string"}],
                "fromTimestamp": from_timestamp,
                "toTimestamp": to_timestamp
            }
            
            # Query for total traces
            total_query = {
                "view": "traces",
                "metrics": [{"measure": "count", "aggregation": "count"}],
                "dimensions": [],
                "filters": [],
                "fromTimestamp": from_timestamp,
                "toTimestamp": to_timestamp
            }
            
            # Query for cost data
            cost_query = {
                "view": "observations",
                "metrics": [{"measure": "totalCost", "aggregation": "sum"}],
                "dimensions": [],
                "timeDimension": {"granularity": "hour"},
                "fromTimestamp": from_timestamp,
                "toTimestamp": to_timestamp,
                "filters": []
            }
            
            # Make API calls
            trace_counts = self._make_metrics_api_request(trace_count_query)
            latency_data = self._make_metrics_api_request(latency_query)
            error_data = self._make_metrics_api_request(error_query)
            total_data = self._make_metrics_api_request(total_query)
            cost_data = self._make_metrics_api_request(cost_query)
            
            # Process results
            result = {
                'trace_counts': trace_counts.get('data', []) if trace_counts else [],
                'latency_metrics': latency_data.get('data', []) if latency_data else [],
                'error_count': error_data.get('data', [{}])[0].get('count_count', 0) if error_data and error_data.get('data') else 0,
                'total_count': total_data.get('data', [{}])[0].get('count_count', 0) if total_data and total_data.get('data') else 0,
                'cost_data': cost_data.get('data', []) if cost_data else [],
                'period_hours': hours
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting real performance metrics: {e}")
            return {}
    
    def get_latency_time_series(self, hours: int = 24) -> List[Dict]:
        """Get latency time series data for charts."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            from_timestamp = start_time.isoformat() + 'Z'
            to_timestamp = end_time.isoformat() + 'Z'
            
            query = {
                "view": "traces",
                "metrics": [
                    {"measure": "latency", "aggregation": "avg"},
                    {"measure": "latency", "aggregation": "p95"}
                ],
                "dimensions": [],
                "timeDimension": {"granularity": "hour"},
                "fromTimestamp": from_timestamp,
                "toTimestamp": to_timestamp,
                "orderBy": [{"field": "time", "direction": "asc"}]
            }
            
            response = self._make_metrics_api_request(query)
            
            if response and response.get('data'):
                return response['data']
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting latency time series: {e}")
            return []
    
    def get_error_rate_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error rate metrics."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            from_timestamp = start_time.isoformat() + 'Z'
            to_timestamp = end_time.isoformat() + 'Z'
            
            # Get total traces
            total_query = {
                "view": "traces",
                "metrics": [{"measure": "count", "aggregation": "count"}],
                "dimensions": [],
                "fromTimestamp": from_timestamp,
                "toTimestamp": to_timestamp
            }
            
            # Get error traces
            error_query = {
                "view": "traces",
                "metrics": [{"measure": "count", "aggregation": "count"}],
                "dimensions": [],
                "filters": [{"column": "level", "operator": "=", "value": "ERROR", "type": "string"}],
                "fromTimestamp": from_timestamp,
                "toTimestamp": to_timestamp
            }
            
            total_response = self._make_metrics_api_request(total_query)
            error_response = self._make_metrics_api_request(error_query)
            
            total_count = 0
            error_count = 0
            
            if total_response and total_response.get('data'):
                total_count = int(total_response['data'][0].get('count_count', 0))
            
            if error_response and error_response.get('data'):
                error_count = int(error_response['data'][0].get('count_count', 0))
            
            success_count = total_count - error_count
            error_rate = (error_count / total_count * 100) if total_count > 0 else 0
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            return {
                'total_traces': total_count,
                'error_count': error_count,
                'success_count': success_count,
                'error_rate': round(error_rate, 2),
                'success_rate': round(success_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting error rate metrics: {e}")
            return {
                'total_traces': 0,
                'error_count': 0,
                'success_count': 0,
                'error_rate': 0,
                'success_rate': 0
            }
    
    def get_recent_traces_summary(self, limit: int = 10) -> List[Dict]:
        """Get recent traces summary for the performance page."""
        try:
            traces = self.get_traces(limit=limit)
            
            if not traces or not hasattr(traces, 'data'):
                return []
            
            summary_list = []
            for trace in traces.data[:limit]:
                summary = {
                    'id': trace.id,
                    'name': trace.name or 'Unnamed',
                    'status': trace.status or 'unknown',
                    'latency': trace.latency or 0,
                    'timestamp': trace.timestamp,
                    'user_id': getattr(trace, 'userId', None),
                    'cost': getattr(trace, 'cost', 0) or 0
                }
                summary_list.append(summary)
            
            return summary_list
            
        except Exception as e:
            logger.error(f"Error getting recent traces summary: {e}")
            return []
    
    def get_cost_time_series(self, hours: int = 24) -> List[Dict]:
        """Get cost data over time for charts."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            from_timestamp = start_time.isoformat() + 'Z'
            to_timestamp = end_time.isoformat() + 'Z'
            
            query = {
                "view": "observations",
                "metrics": [{"measure": "totalCost", "aggregation": "sum"}],
                "dimensions": [],
                "timeDimension": {"granularity": "hour"},
                "fromTimestamp": from_timestamp,
                "toTimestamp": to_timestamp,
                "orderBy": [{"field": "time", "direction": "asc"}]
            }
            
            response = self._make_metrics_api_request(query)
            
            if response and response.get('data'):
                return response['data']
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting cost time series: {e}")
            return [] 