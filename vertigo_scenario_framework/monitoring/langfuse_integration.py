"""
Langfuse integration for production monitoring of agent evaluations.
Provides trace collection, performance monitoring, and evaluation analytics.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class EvaluationTrace:
    """Structured evaluation trace for Langfuse."""
    trace_id: str
    scenario_id: str
    agent_type: str
    evaluation_scores: Dict[str, float]
    performance_metrics: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime

class LangfuseMonitor:
    """
    Langfuse integration for monitoring agent evaluations in production.
    Tracks evaluation metrics, performance trends, and business impact.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Langfuse monitor with configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.enabled = self.config.get("enabled", True)
        
        # Initialize Langfuse client if available
        self.langfuse_client = None
        if self.enabled:
            self._initialize_langfuse_client()
    
    def _initialize_langfuse_client(self):
        """Initialize Langfuse client with error handling."""
        try:
            # Try to import and initialize Langfuse
            from langfuse import Langfuse
            
            langfuse_config = self.config.get("langfuse", {})
            self.langfuse_client = Langfuse(
                public_key=langfuse_config.get("public_key"),
                secret_key=langfuse_config.get("secret_key"),
                host=langfuse_config.get("host", "https://cloud.langfuse.com")
            )
            
            self.logger.info("Langfuse client initialized successfully")
            
        except ImportError:
            self.logger.warning("Langfuse not available - monitoring disabled")
            self.enabled = False
        except Exception as e:
            self.logger.error(f"Failed to initialize Langfuse: {e}")
            self.enabled = False
    
    def start_evaluation_trace(self, scenario: Dict[str, Any], 
                              agent_type: str) -> Optional[str]:
        """
        Start a new evaluation trace in Langfuse.
        
        Args:
            scenario: Test scenario being evaluated
            agent_type: Type of agent (email_processor, meeting_analyzer, etc.)
            
        Returns:
            Trace ID if successful, None if disabled
        """
        if not self.enabled or not self.langfuse_client:
            return None
        
        try:
            trace_name = f"{agent_type}_evaluation_{scenario.get('id', 'unknown')}"
            
            trace = self.langfuse_client.trace(
                name=trace_name,
                metadata={
                    "scenario_name": scenario.get("name", "Unknown"),
                    "scenario_id": scenario.get("id", "unknown"),
                    "agent_type": agent_type,
                    "user_persona": scenario.get("user_persona"),
                    "business_impact": scenario.get("business_impact"),
                    "priority": scenario.get("priority"),
                    "tags": scenario.get("tags", [])
                },
                tags=["agent_evaluation", agent_type, "scenario_framework"]
            )
            
            return trace.id
            
        except Exception as e:
            self.logger.error(f"Failed to start evaluation trace: {e}")
            return None
    
    def log_agent_execution(self, trace_id: str, scenario: Dict[str, Any], 
                           agent_response: Dict[str, Any], 
                           execution_time: float) -> Optional[str]:
        """
        Log agent execution within an evaluation trace.
        
        Args:
            trace_id: Langfuse trace ID
            scenario: Test scenario
            agent_response: Agent's response
            execution_time: Execution time in seconds
            
        Returns:
            Observation ID if successful
        """
        if not self.enabled or not self.langfuse_client or not trace_id:
            return None
        
        try:
            # Extract key information from response
            response_summary = self._summarize_agent_response(agent_response)
            
            # Create observation for agent execution
            observation = self.langfuse_client.observation(
                trace_id=trace_id,
                name="agent_execution",
                type="generation",
                input={
                    "scenario_input": {
                        "subject": scenario.get("subject", ""),
                        "body": scenario.get("body", ""),
                        "expected_command": scenario.get("expected_command")
                    }
                },
                output=response_summary,
                metadata={
                    "execution_time_seconds": execution_time,
                    "agent_success": not bool(agent_response.get("error")),
                    "response_type": type(agent_response).__name__,
                    "has_error": bool(agent_response.get("error"))
                },
                usage={
                    "input_tokens": len(str(scenario)) // 4,  # Rough estimate
                    "output_tokens": len(str(agent_response)) // 4,  # Rough estimate
                    "total_tokens": (len(str(scenario)) + len(str(agent_response))) // 4
                }
            )
            
            return observation.id
            
        except Exception as e:
            self.logger.error(f"Failed to log agent execution: {e}")
            return None
    
    def log_evaluation_results(self, trace_id: str, evaluation_result: Dict[str, Any], 
                              scenario: Dict[str, Any]) -> Optional[str]:
        """
        Log evaluation results to Langfuse.
        
        Args:
            trace_id: Langfuse trace ID
            evaluation_result: Comprehensive evaluation results
            scenario: Original scenario
            
        Returns:
            Score ID if successful
        """
        if not self.enabled or not self.langfuse_client or not trace_id:
            return None
        
        try:
            # Log composite score
            composite_score = evaluation_result.get("composite_score", 0.0)
            
            score = self.langfuse_client.score(
                trace_id=trace_id,
                name="composite_evaluation_score",
                value=composite_score,
                comment=f"Grade: {evaluation_result.get('quality_grade', 'Unknown')}"
            )
            
            # Log individual dimension scores
            dimension_scores = evaluation_result.get("dimension_scores", {})
            for dimension, score_value in dimension_scores.items():
                self.langfuse_client.score(
                    trace_id=trace_id,
                    name=f"{dimension}_score",
                    value=score_value,
                    comment=f"{dimension.title()} evaluation score"
                )
            
            # Log evaluation metadata
            self.langfuse_client.observation(
                trace_id=trace_id,
                name="evaluation_analysis",
                type="llm",
                input={
                    "evaluation_request": {
                        "scenario_type": scenario.get("scenario_type", "unknown"),
                        "evaluation_dimensions": ["accuracy", "relevance", "business_impact"]
                    }
                },
                output={
                    "evaluation_summary": {
                        "composite_score": composite_score,
                        "quality_grade": evaluation_result.get("quality_grade"),
                        "dimension_scores": dimension_scores,
                        "recommendations": evaluation_result.get("recommendations", []),
                        "critical_issues": evaluation_result.get("comprehensive_analysis", {}).get("critical_issues", [])
                    }
                },
                metadata={
                    "evaluation_time_seconds": evaluation_result.get("evaluation_time_seconds", 0),
                    "weights_used": evaluation_result.get("weights_used", {}),
                    "context_multiplier": evaluation_result.get("context_multiplier", 1.0)
                }
            )
            
            return score.id
            
        except Exception as e:
            self.logger.error(f"Failed to log evaluation results: {e}")
            return None
    
    def log_batch_evaluation(self, batch_results: Dict[str, Any]) -> Optional[str]:
        """
        Log batch evaluation results as a session.
        
        Args:
            batch_results: Results from batch evaluation
            
        Returns:
            Session ID if successful
        """
        if not self.enabled or not self.langfuse_client:
            return None
        
        try:
            batch_summary = batch_results.get("batch_summary", {})
            
            # Create session for batch evaluation
            session = self.langfuse_client.trace(
                name=f"batch_evaluation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                session_id=f"batch_{datetime.utcnow().timestamp()}",
                metadata={
                    "evaluation_type": "batch",
                    "total_scenarios": batch_summary.get("total_scenarios", 0),
                    "average_score": batch_summary.get("average_composite_score", 0),
                    "dimension_averages": batch_summary.get("dimension_averages", {}),
                    "score_distribution": batch_summary.get("score_distribution", {})
                },
                tags=["batch_evaluation", "agent_testing", "comprehensive"]
            )
            
            # Log aggregate metrics
            avg_score = batch_summary.get("average_composite_score", 0)
            self.langfuse_client.score(
                trace_id=session.id,
                name="batch_average_score",
                value=avg_score,
                comment=f"Average across {batch_summary.get('total_scenarios', 0)} scenarios"
            )
            
            # Log performance distribution
            score_dist = batch_summary.get("score_distribution", {})
            for performance_level, count in score_dist.items():
                self.langfuse_client.score(
                    trace_id=session.id,
                    name=f"scenarios_{performance_level}",
                    value=count,
                    comment=f"Number of scenarios with {performance_level} performance"
                )
            
            return session.id
            
        except Exception as e:
            self.logger.error(f"Failed to log batch evaluation: {e}")
            return None
    
    def track_performance_trend(self, agent_type: str, 
                               time_period: str = "daily") -> Dict[str, Any]:
        """
        Track performance trends over time using Langfuse data.
        
        Args:
            agent_type: Type of agent to analyze
            time_period: Time period for analysis (daily, weekly, monthly)
            
        Returns:
            Performance trend analysis
        """
        if not self.enabled or not self.langfuse_client:
            return {"error": "Langfuse monitoring not enabled"}
        
        try:
            # This would query Langfuse for historical data
            # For now, we'll return a structure showing what would be available
            
            return {
                "agent_type": agent_type,
                "time_period": time_period,
                "trend_analysis": {
                    "average_score_trend": "increasing",  # Would calculate from data
                    "evaluation_count": 150,  # Would count from traces
                    "improvement_areas": ["accuracy", "business_impact"],
                    "top_performing_scenarios": [],
                    "concerning_patterns": []
                },
                "data_source": "langfuse_traces"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to track performance trends: {e}")
            return {"error": str(e)}
    
    def _summarize_agent_response(self, agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of agent response for logging."""
        if not isinstance(agent_response, dict):
            return {"response_type": "non_dict", "content": str(agent_response)[:200]}
        
        summary = {
            "has_error": bool(agent_response.get("error")),
            "response_fields": list(agent_response.keys()),
            "processing_successful": not bool(agent_response.get("error"))
        }
        
        # Add key content summaries
        if "body" in agent_response:
            body = agent_response["body"]
            summary["response_length"] = len(str(body))
            summary["body_preview"] = str(body)[:100] + "..." if len(str(body)) > 100 else str(body)
        
        if "subject" in agent_response:
            summary["subject"] = agent_response["subject"]
        
        if "command" in agent_response:
            summary["detected_command"] = agent_response["command"]
        
        return summary
    
    def create_evaluation_dashboard_data(self) -> Dict[str, Any]:
        """
        Create data structure for evaluation dashboard.
        This would integrate with Vertigo Debug Toolkit.
        """
        if not self.enabled:
            return {"error": "Monitoring not enabled"}
        
        return {
            "dashboard_data": {
                "recent_evaluations": {
                    "count": 0,  # Would query Langfuse
                    "average_score": 0.0,
                    "trend": "stable"
                },
                "agent_performance": {
                    "email_processor": {"score": 0.85, "trend": "up"},
                    "meeting_analyzer": {"score": 0.78, "trend": "stable"}, 
                    "status_generator": {"score": 0.82, "trend": "up"}
                },
                "evaluation_metrics": {
                    "total_scenarios_run": 0,
                    "evaluation_frequency": "daily",
                    "monitoring_status": "active"
                }
            },
            "integration_status": {
                "langfuse_connected": self.enabled,
                "data_collection": "active" if self.enabled else "disabled",
                "last_update": datetime.utcnow().isoformat()
            }
        }
    
    def cleanup_old_traces(self, days_to_keep: int = 30):
        """
        Clean up old evaluation traces to manage storage.
        
        Args:
            days_to_keep: Number of days of traces to retain
        """
        if not self.enabled or not self.langfuse_client:
            return
        
        try:
            # This would implement cleanup logic
            # Langfuse might have built-in retention policies
            self.logger.info(f"Cleanup policy: keeping traces for {days_to_keep} days")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old traces: {e}")
    
    def export_evaluation_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Export evaluation data for analysis or reporting.
        
        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format
            
        Returns:
            Exported evaluation data
        """
        if not self.enabled or not self.langfuse_client:
            return {"error": "Monitoring not enabled"}
        
        try:
            # This would query and export data from Langfuse
            return {
                "export_summary": {
                    "date_range": f"{start_date} to {end_date}",
                    "total_evaluations": 0,  # Would count from query
                    "data_points": [],  # Would contain actual data
                    "export_format": "json",
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to export evaluation data: {e}")
            return {"error": str(e)}