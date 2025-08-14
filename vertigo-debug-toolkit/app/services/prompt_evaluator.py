#!/usr/bin/env python3
"""
Advanced Prompt Evaluation Service for Vertigo LLM Observability.
"""

import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import func, and_, desc
from app.models import db, Trace, Cost, Prompt, User
from app.services.langwatch_client import LangWatchClient

logger = logging.getLogger(__name__)

@dataclass
class PromptMetrics:
    """Metrics for a specific prompt."""
    prompt_id: int
    prompt_name: str
    total_calls: int
    success_rate: float
    avg_response_time: float
    total_cost: float
    avg_tokens_used: int
    error_count: int
    last_used: Optional[datetime]

@dataclass
class ABTestResult:
    """A/B test comparison result."""
    prompt_a: str
    prompt_b: str
    prompt_a_metrics: PromptMetrics
    prompt_b_metrics: PromptMetrics
    winner: str
    confidence_level: float
    improvement_percentage: float

class PromptEvaluator:
    """Advanced prompt evaluation and analysis service."""
    
    def __init__(self):
        self.langwatch_client = LangWatchClient()
    
    def get_prompt_performance(self, prompt_id: int, days: int = 30) -> PromptMetrics:
        """Get comprehensive performance metrics for a specific prompt."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get prompt details
            prompt = Prompt.query.get(prompt_id)
            if not prompt:
                raise ValueError(f"Prompt with ID {prompt_id} not found")
            
            # Get traces for this prompt
            traces = Trace.query.filter(
                and_(
                    Trace.prompt_id == prompt_id,
                    Trace.start_time >= start_date,
                    Trace.start_time <= end_date
                )
            ).all()
            
            if not traces:
                return PromptMetrics(
                    prompt_id=prompt_id,
                    prompt_name=prompt.name,
                    total_calls=0,
                    success_rate=0.0,
                    avg_response_time=0.0,
                    total_cost=0.0,
                    avg_tokens_used=0,
                    error_count=0,
                    last_used=None
                )
            
            # Calculate metrics
            total_calls = len(traces)
            success_count = sum(1 for t in traces if t.status == 'success')
            success_rate = (success_count / total_calls) * 100 if total_calls > 0 else 0
            
            response_times = [t.duration_ms/1000.0 for t in traces if t.duration_ms]  # Convert ms to seconds
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Get cost data
            costs = Cost.query.filter(
                and_(
                    Cost.trace_id.in_([t.id for t in traces]),
                    Cost.timestamp >= start_date,
                    Cost.timestamp <= end_date
                )
            ).all()
            
            total_cost = float(sum(c.cost_usd for c in costs))
            
            # Calculate token usage from cost data
            total_tokens = sum(c.total_tokens for c in costs if c.total_tokens)
            avg_tokens_used = total_tokens / len(costs) if costs else 0
            
            error_count = total_calls - success_count
            last_used = max(t.start_time for t in traces) if traces else None
            
            return PromptMetrics(
                prompt_id=prompt_id,
                prompt_name=prompt.name,
                total_calls=total_calls,
                success_rate=success_rate,
                avg_response_time=avg_response_time,
                total_cost=total_cost,
                avg_tokens_used=int(avg_tokens_used),
                error_count=error_count,
                last_used=last_used
            )
            
        except Exception as e:
            logger.error(f"Error getting prompt performance: {e}")
            raise
    
    def compare_prompts(self, prompt_a_id: int, prompt_b_id: int, days: int = 30) -> ABTestResult:
        """Compare two prompts using A/B testing methodology."""
        try:
            metrics_a = self.get_prompt_performance(prompt_a_id, days)
            metrics_b = self.get_prompt_performance(prompt_b_id, days)
            
            # Determine winner based on success rate and cost efficiency
            score_a = (float(metrics_a.success_rate) * 0.7) - (float(metrics_a.total_cost) * 0.3)
            score_b = (float(metrics_b.success_rate) * 0.7) - (float(metrics_b.total_cost) * 0.3)
            
            winner = "A" if score_a > score_b else "B"
            
            # Calculate improvement percentage with division by zero protection
            max_score = max(abs(score_a), abs(score_b))
            if max_score > 0:
                improvement_percentage = abs(score_a - score_b) / max_score * 100
            else:
                improvement_percentage = 0.0
            
            # Calculate confidence level (simplified)
            total_calls = metrics_a.total_calls + metrics_b.total_calls
            confidence_level = min(95.0, 50 + (total_calls * 0.5))  # Higher calls = higher confidence
            
            return ABTestResult(
                prompt_a=f"Prompt A ({metrics_a.prompt_name})",
                prompt_b=f"Prompt B ({metrics_b.prompt_name})",
                prompt_a_metrics=metrics_a,
                prompt_b_metrics=metrics_b,
                winner=winner,
                confidence_level=confidence_level,
                improvement_percentage=improvement_percentage
            )
            
        except Exception as e:
            logger.error(f"Error comparing prompts: {e}")
            raise
    
    def get_cost_optimization_recommendations(self, prompt_id: int) -> List[Dict[str, Any]]:
        """Get cost optimization recommendations for a prompt."""
        try:
            metrics = self.get_prompt_performance(prompt_id)
            recommendations = []
            
            # Check for high token usage
            if metrics.avg_tokens_used > 1000:
                recommendations.append({
                    "type": "token_optimization",
                    "priority": "high",
                    "title": "High Token Usage Detected",
                    "description": f"Average {metrics.avg_tokens_used} tokens per call. Consider shortening prompts or using more efficient models.",
                    "potential_savings": f"~{metrics.avg_tokens_used * 0.001:.2f} per call"
                })
            
            # Check for high error rates
            if metrics.success_rate < 80:
                recommendations.append({
                    "type": "reliability",
                    "priority": "high",
                    "title": "Low Success Rate",
                    "description": f"Only {metrics.success_rate:.1f}% success rate. Review prompt clarity and error handling.",
                    "potential_savings": "Reduce failed call costs"
                })
            
            # Check for expensive models
            if metrics.total_cost > 10:  # Threshold for "expensive"
                recommendations.append({
                    "type": "model_optimization",
                    "priority": "medium",
                    "title": "High Cost Usage",
                    "description": f"Total cost: ${metrics.total_cost:.2f}. Consider using cheaper models for non-critical tasks.",
                    "potential_savings": f"~{metrics.total_cost * 0.3:.2f} potential savings"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting cost recommendations: {e}")
            return []
    
    def get_session_analysis(self, session_id: str) -> Dict[str, Any]:
        """Analyze a specific session's prompt usage patterns."""
        try:
            # Get all traces for a session
            traces = Trace.query.filter(Trace.session_id == session_id).order_by(Trace.start_time).all()
            
            if not traces:
                return {"error": "Session not found"}
            
            # Analyze session flow
            session_flow = []
            total_cost = 0
            total_tokens = 0
            
            for trace in traces:
                cost = Cost.query.filter(Cost.trace_id == trace.id).first()
                if cost:
                    total_cost += cost.cost_usd
                
                if trace.token_count:
                    total_tokens += trace.token_count
                
                session_flow.append({
                    "timestamp": trace.start_time.isoformat(),
                    "prompt_name": trace.prompt_name,
                    "status": trace.status,
                    "response_time": trace.response_time,
                    "token_count": trace.token_count,
                    "cost": cost.amount if cost else 0
                })
            
            # Calculate session metrics
            success_count = sum(1 for t in traces if t.status == 'success')
            success_rate = (success_count / len(traces)) * 100 if traces else 0
            
            response_times_with_data = [t.response_time for t in traces if t.response_time]
            avg_response_time = sum(response_times_with_data) / len(response_times_with_data) if response_times_with_data else 0
            
            return {
                "session_id": session_id,
                "total_interactions": len(traces),
                "success_rate": success_rate,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "avg_response_time": avg_response_time,
                "session_duration": (traces[-1].created_at - traces[0].created_at).total_seconds(),
                "flow": session_flow
            }
            
        except Exception as e:
            logger.error(f"Error analyzing session: {e}")
            return {"error": str(e)}
    
    def generate_evaluation_report(self, prompt_ids: List[int], days: int = 30) -> Dict[str, Any]:
        """Generate a comprehensive evaluation report for multiple prompts."""
        try:
            if not prompt_ids:
                return {"error": "No prompt IDs provided"}
            
            prompt_metrics = []
            total_cost = 0
            total_traces = 0
            success_rates = []
            response_times = []
            all_recommendations = []
            
            # Get metrics for each prompt
            for prompt_id in prompt_ids:
                try:
                    metrics = self.get_prompt_performance(prompt_id, days)
                    prompt = Prompt.query.get(prompt_id)
                    
                    if prompt and metrics:
                        prompt_detail = {
                            "id": prompt_id,
                            "name": metrics.prompt_name,
                            "version": prompt.version,
                            "type": prompt.prompt_type,
                            "total_calls": int(metrics.total_calls),
                            "success_rate": float(metrics.success_rate),
                            "avg_response_time": float(metrics.avg_response_time),
                            "total_cost": float(metrics.total_cost),
                            "avg_tokens_used": int(metrics.avg_tokens_used),
                            "error_count": int(metrics.error_count),
                            "last_used": metrics.last_used.isoformat() if metrics.last_used else None
                        }
                        
                        prompt_metrics.append(prompt_detail)
                        total_cost += metrics.total_cost
                        total_traces += metrics.total_calls
                        
                        if metrics.total_calls > 0:
                            success_rates.append(metrics.success_rate)
                            response_times.append(metrics.avg_response_time)
                        
                        # Get recommendations for this prompt
                        recommendations = self.get_cost_optimization_recommendations(prompt_id)
                        for rec in recommendations:
                            all_recommendations.append(f"{rec.get('title', 'Optimization')}: {rec.get('description', 'No details')}")
                        
                except Exception as e:
                    logger.warning(f"Failed to get metrics for prompt {prompt_id}: {e}")
                    continue
            
            # Calculate overall metrics
            avg_success_rate = float(sum(success_rates) / len(success_rates)) if success_rates else 0.0
            avg_response_time = float(sum(response_times) / len(response_times)) if response_times else 0.0
            
            # Find top performing prompt
            top_performing_prompt = None
            if prompt_metrics:
                # Ensure success_rate is numeric for comparison
                for metric in prompt_metrics:
                    if isinstance(metric['success_rate'], str):
                        try:
                            metric['success_rate'] = float(metric['success_rate'])
                        except (ValueError, TypeError):
                            metric['success_rate'] = 0.0
                top_performing_prompt = max(prompt_metrics, key=lambda p: float(p['success_rate']))
            
            # Build comprehensive report
            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "evaluation_period_days": int(days),
                "prompts_analyzed": len(prompt_metrics),
                "total_traces": int(total_traces),
                "total_cost": float(total_cost),
                "avg_success_rate": float(avg_success_rate),
                "avg_response_time": float(avg_response_time),
                "top_performing_prompt": top_performing_prompt,
                "prompt_details": prompt_metrics,
                "recommendations": all_recommendations[:10],  # Limit to top 10
                "cost_breakdown": {
                    "daily_average": float(total_cost / days) if days > 0 else 0.0,
                    "cost_per_trace": float(total_cost / total_traces) if total_traces > 0 else 0.0,
                    "optimization_potential": float(total_cost * 0.285),  # 28.5% estimated savings
                },
                "performance_summary": {
                    "excellent_prompts": len([p for p in prompt_metrics if float(p['success_rate']) >= 90]),
                    "good_prompts": len([p for p in prompt_metrics if 70 <= float(p['success_rate']) < 90]),
                    "needs_improvement": len([p for p in prompt_metrics if float(p['success_rate']) < 70]),
                    "high_cost_prompts": len([p for p in prompt_metrics if float(p['total_cost']) > 10]),
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating evaluation report: {e}")
            return {"error": str(e)}
    
    def get_prompt_version_history(self, prompt_name: str) -> List[Dict[str, Any]]:
        """Get version history for a specific prompt."""
        try:
            prompts = Prompt.query.filter(Prompt.name == prompt_name).order_by(desc(Prompt.created_at)).all()
            
            history = []
            for prompt in prompts:
                metrics = self.get_prompt_performance(prompt.id, days=7)  # Last 7 days
                history.append({
                    "version": prompt.version,
                    "created_at": prompt.created_at.isoformat(),
                    "content_preview": prompt.content[:100] + "..." if len(prompt.content) > 100 else prompt.content,
                    "performance": {
                        "total_calls": metrics.total_calls,
                        "success_rate": metrics.success_rate,
                        "avg_response_time": metrics.avg_response_time,
                        "total_cost": metrics.total_cost
                    }
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting prompt version history: {e}")
            return [] 