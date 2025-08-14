"""
Comprehensive multi-dimensional evaluator for Vertigo agents.
Combines accuracy, relevance, and business impact metrics for complete evaluation.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .accuracy_evaluator import AccuracyEvaluator
from .relevance_evaluator import RelevanceEvaluator
from .business_impact_evaluator import BusinessImpactEvaluator

class ComprehensiveEvaluator:
    """
    Multi-dimensional evaluator that combines accuracy, relevance, and business impact.
    Provides weighted scoring and detailed analysis across all evaluation dimensions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the comprehensive evaluator.
        
        Args:
            config: Configuration dictionary with weights and settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize individual evaluators
        self.accuracy_evaluator = AccuracyEvaluator(config)
        self.relevance_evaluator = RelevanceEvaluator(config)
        self.business_impact_evaluator = BusinessImpactEvaluator(config)
        
        # Default weights for different dimensions
        self.weights = {
            "accuracy": config.get("accuracy_weight", 0.4),
            "relevance": config.get("relevance_weight", 0.3),
            "business_impact": config.get("business_impact_weight", 0.3)
        }
        
        # Validate weights sum to 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.001:
            self.logger.warning(f"Weights sum to {total_weight}, normalizing to 1.0")
            for key in self.weights:
                self.weights[key] /= total_weight
        
        self.logger.info(f"Initialized comprehensive evaluator with weights: {self.weights}")
    
    async def evaluate_single(self, scenario: Dict[str, Any], 
                            agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single agent response across all dimensions.
        
        Args:
            scenario: Test scenario data
            agent_response: Agent's response to evaluate
            
        Returns:
            Comprehensive evaluation results
        """
        evaluation_start = datetime.utcnow()
        
        # Run all evaluations in parallel
        accuracy_task = self.accuracy_evaluator.evaluate(scenario, agent_response)
        relevance_task = self.relevance_evaluator.evaluate(scenario, agent_response)
        business_impact_task = self.business_impact_evaluator.evaluate(scenario, agent_response)
        
        # Wait for all evaluations to complete
        accuracy_result, relevance_result, business_impact_result = await asyncio.gather(
            accuracy_task, relevance_task, business_impact_task,
            return_exceptions=True
        )
        
        # Handle any evaluation errors
        evaluation_errors = []
        if isinstance(accuracy_result, Exception):
            evaluation_errors.append(f"Accuracy evaluation error: {accuracy_result}")
            accuracy_result = {"score": 0.0, "error": str(accuracy_result)}
        
        if isinstance(relevance_result, Exception):
            evaluation_errors.append(f"Relevance evaluation error: {relevance_result}")
            relevance_result = {"score": 0.0, "error": str(relevance_result)}
        
        if isinstance(business_impact_result, Exception):
            evaluation_errors.append(f"Business impact evaluation error: {business_impact_result}")
            business_impact_result = {"score": 0.0, "error": str(business_impact_result)}
        
        # Calculate weighted composite score
        composite_score = self._calculate_composite_score(
            accuracy_result, relevance_result, business_impact_result
        )
        
        # Generate comprehensive analysis
        comprehensive_analysis = self._generate_comprehensive_analysis(
            scenario, agent_response, accuracy_result, relevance_result, business_impact_result
        )
        
        evaluation_end = datetime.utcnow()
        evaluation_time = (evaluation_end - evaluation_start).total_seconds()
        
        return {
            "scenario_id": scenario.get("id", "unknown"),
            "scenario_name": scenario.get("name", "Unknown Scenario"),
            "evaluation_timestamp": evaluation_start.isoformat(),
            "evaluation_time_seconds": evaluation_time,
            "composite_score": composite_score,
            "dimension_scores": {
                "accuracy": accuracy_result.get("score", 0.0),
                "relevance": relevance_result.get("score", 0.0),
                "business_impact": business_impact_result.get("score", 0.0)
            },
            "weights_used": self.weights.copy(),
            "detailed_results": {
                "accuracy": accuracy_result,
                "relevance": relevance_result,
                "business_impact": business_impact_result
            },
            "comprehensive_analysis": comprehensive_analysis,
            "evaluation_errors": evaluation_errors,
            "quality_grade": self._assign_quality_grade(composite_score),
            "recommendations": self._generate_recommendations(
                accuracy_result, relevance_result, business_impact_result
            )
        }
    
    def _calculate_composite_score(self, accuracy_result: Dict[str, Any],
                                  relevance_result: Dict[str, Any],
                                  business_impact_result: Dict[str, Any]) -> float:
        """Calculate weighted composite score across all dimensions."""
        accuracy_score = accuracy_result.get("score", 0.0)
        relevance_score = relevance_result.get("score", 0.0)
        business_impact_score = business_impact_result.get("score", 0.0)
        
        composite_score = (
            accuracy_score * self.weights["accuracy"] +
            relevance_score * self.weights["relevance"] + 
            business_impact_score * self.weights["business_impact"]
        )
        
        return round(composite_score, 3)
    
    def _generate_comprehensive_analysis(self, scenario: Dict[str, Any],
                                       agent_response: Dict[str, Any],
                                       accuracy_result: Dict[str, Any],
                                       relevance_result: Dict[str, Any],
                                       business_impact_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis combining all evaluation dimensions."""
        
        # Identify strengths and weaknesses
        scores = {
            "accuracy": accuracy_result.get("score", 0.0),
            "relevance": relevance_result.get("score", 0.0), 
            "business_impact": business_impact_result.get("score", 0.0)
        }
        
        strongest_dimension = max(scores.keys(), key=lambda k: scores[k])
        weakest_dimension = min(scores.keys(), key=lambda k: scores[k])
        
        # Analyze response characteristics
        response_characteristics = {
            "has_structured_output": self._check_structured_output(agent_response),
            "response_length": self._get_response_length(agent_response),
            "includes_quantitative_data": self._check_quantitative_data(agent_response),
            "error_present": bool(agent_response.get("error")),
            "processing_successful": not bool(agent_response.get("error"))
        }
        
        # Business context analysis
        business_context = {
            "scenario_priority": scenario.get("priority", "medium"),
            "business_impact_level": scenario.get("business_impact", "medium"),
            "user_persona": scenario.get("user_persona", "unknown"),
            "tags": scenario.get("tags", [])
        }
        
        return {
            "overall_performance": self._categorize_performance(
                sum(scores.values()) / len(scores)
            ),
            "strongest_dimension": strongest_dimension,
            "weakest_dimension": weakest_dimension,
            "dimension_balance": self._calculate_dimension_balance(scores),
            "response_characteristics": response_characteristics,
            "business_context": business_context,
            "critical_issues": self._identify_critical_issues(
                accuracy_result, relevance_result, business_impact_result
            ),
            "success_factors": self._identify_success_factors(
                accuracy_result, relevance_result, business_impact_result
            )
        }
    
    def _assign_quality_grade(self, composite_score: float) -> str:
        """Assign letter grade based on composite score."""
        if composite_score >= 0.9:
            return "A+"
        elif composite_score >= 0.85:
            return "A"
        elif composite_score >= 0.8:
            return "A-"
        elif composite_score >= 0.75:
            return "B+"
        elif composite_score >= 0.7:
            return "B"
        elif composite_score >= 0.65:
            return "B-"
        elif composite_score >= 0.6:
            return "C+"
        elif composite_score >= 0.55:
            return "C"
        elif composite_score >= 0.5:
            return "C-"
        elif composite_score >= 0.4:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(self, accuracy_result: Dict[str, Any],
                                relevance_result: Dict[str, Any],
                                business_impact_result: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on evaluation results."""
        recommendations = []
        
        # Accuracy-based recommendations
        if accuracy_result.get("score", 0) < 0.7:
            recommendations.append("Improve command recognition accuracy through better prompt engineering")
            if accuracy_result.get("details", {}).get("command_detection_failed"):
                recommendations.append("Review and expand command matching patterns")
        
        # Relevance-based recommendations
        if relevance_result.get("score", 0) < 0.7:
            recommendations.append("Enhance response relevance by including more contextual information")
            if relevance_result.get("details", {}).get("missing_key_elements"):
                recommendations.append("Ensure all expected response elements are included")
        
        # Business impact recommendations
        if business_impact_result.get("score", 0) < 0.7:
            recommendations.append("Increase business value by providing more actionable insights")
            if business_impact_result.get("details", {}).get("low_executive_value"):
                recommendations.append("Include executive-level summaries and strategic implications")
        
        # Cross-dimensional recommendations
        scores = [
            accuracy_result.get("score", 0),
            relevance_result.get("score", 0),
            business_impact_result.get("score", 0)
        ]
        
        if max(scores) - min(scores) > 0.3:
            recommendations.append("Work on balancing performance across all evaluation dimensions")
        
        if all(score < 0.6 for score in scores):
            recommendations.append("Consider fundamental prompt redesign or additional training data")
        
        return recommendations
    
    def _check_structured_output(self, response: Dict[str, Any]) -> bool:
        """Check if response has structured output."""
        if not isinstance(response, dict):
            return False
        
        # Look for structured elements
        structured_indicators = ["subject", "body", "analysis", "output"]
        return any(key in response for key in structured_indicators)
    
    def _get_response_length(self, response: Dict[str, Any]) -> int:
        """Get total length of response content."""
        if isinstance(response, dict):
            response_str = str(response.get("body", "")) + str(response.get("output", ""))
            return len(response_str)
        return len(str(response))
    
    def _check_quantitative_data(self, response: Dict[str, Any]) -> bool:
        """Check if response includes quantitative data."""
        response_str = str(response).lower()
        quantitative_indicators = ["%", "$", "total:", "count:", "average:", "rate:"]
        return any(indicator in response_str for indicator in quantitative_indicators)
    
    def _categorize_performance(self, average_score: float) -> str:
        """Categorize overall performance level."""
        if average_score >= 0.85:
            return "Excellent"
        elif average_score >= 0.75:
            return "Good"
        elif average_score >= 0.65:
            return "Satisfactory"
        elif average_score >= 0.5:
            return "Needs Improvement"
        else:
            return "Poor"
    
    def _calculate_dimension_balance(self, scores: Dict[str, float]) -> float:
        """Calculate how balanced the scores are across dimensions."""
        if not scores:
            return 0.0
        
        score_values = list(scores.values())
        mean_score = sum(score_values) / len(score_values)
        variance = sum((score - mean_score) ** 2 for score in score_values) / len(score_values)
        
        # Return balance score (higher = more balanced)
        return max(0.0, 1.0 - variance)
    
    def _identify_critical_issues(self, accuracy_result: Dict[str, Any],
                                relevance_result: Dict[str, Any],
                                business_impact_result: Dict[str, Any]) -> List[str]:
        """Identify critical issues that need immediate attention."""
        issues = []
        
        if accuracy_result.get("score", 0) < 0.5:
            issues.append("Critical accuracy failure - agent not performing basic functions correctly")
        
        if relevance_result.get("score", 0) < 0.5:
            issues.append("Severe relevance issues - responses not meeting user expectations")
        
        if business_impact_result.get("score", 0) < 0.3:
            issues.append("Extremely low business value - agent responses lack actionable insights")
        
        # Check for errors in individual evaluations
        for result, name in [(accuracy_result, "accuracy"), (relevance_result, "relevance"), 
                            (business_impact_result, "business_impact")]:
            if result.get("error"):
                issues.append(f"Evaluation system error in {name} dimension")
        
        return issues
    
    def _identify_success_factors(self, accuracy_result: Dict[str, Any],
                                relevance_result: Dict[str, Any],
                                business_impact_result: Dict[str, Any]) -> List[str]:
        """Identify factors contributing to success."""
        success_factors = []
        
        if accuracy_result.get("score", 0) >= 0.8:
            success_factors.append("High accuracy in command recognition and processing")
        
        if relevance_result.get("score", 0) >= 0.8:
            success_factors.append("Strong relevance and contextual appropriateness")
        
        if business_impact_result.get("score", 0) >= 0.8:
            success_factors.append("High business value and actionable insights")
        
        # Look for specific strengths in detailed results
        if accuracy_result.get("details", {}).get("perfect_command_match"):
            success_factors.append("Perfect command recognition accuracy")
        
        if relevance_result.get("details", {}).get("all_elements_present"):
            success_factors.append("Complete coverage of expected response elements")
        
        return success_factors
    
    async def evaluate_batch(self, scenarios: List[Dict[str, Any]], 
                           agent_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate a batch of scenarios and responses.
        
        Args:
            scenarios: List of test scenarios
            agent_responses: List of corresponding agent responses
            
        Returns:
            Batch evaluation results with aggregate analysis
        """
        if len(scenarios) != len(agent_responses):
            raise ValueError("Number of scenarios must match number of responses")
        
        # Evaluate all scenario-response pairs
        evaluation_tasks = [
            self.evaluate_single(scenario, response)
            for scenario, response in zip(scenarios, agent_responses)
        ]
        
        individual_results = await asyncio.gather(*evaluation_tasks)
        
        # Generate aggregate analysis
        aggregate_analysis = self._generate_aggregate_analysis(individual_results)
        
        return {
            "batch_summary": {
                "total_scenarios": len(scenarios),
                "evaluation_timestamp": datetime.utcnow().isoformat(),
                "average_composite_score": aggregate_analysis["average_composite_score"],
                "score_distribution": aggregate_analysis["score_distribution"],
                "dimension_averages": aggregate_analysis["dimension_averages"]
            },
            "individual_results": individual_results,
            "aggregate_analysis": aggregate_analysis,
            "recommendations": aggregate_analysis["batch_recommendations"]
        }
    
    def _generate_aggregate_analysis(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate aggregate analysis across all evaluation results."""
        if not results:
            return {}
        
        # Calculate averages
        composite_scores = [r["composite_score"] for r in results]
        average_composite = sum(composite_scores) / len(composite_scores)
        
        dimension_scores = {
            "accuracy": [r["dimension_scores"]["accuracy"] for r in results],
            "relevance": [r["dimension_scores"]["relevance"] for r in results],
            "business_impact": [r["dimension_scores"]["business_impact"] for r in results]
        }
        
        dimension_averages = {
            dim: sum(scores) / len(scores)
            for dim, scores in dimension_scores.items()
        }
        
        # Score distribution
        score_distribution = {
            "excellent": sum(1 for s in composite_scores if s >= 0.85),
            "good": sum(1 for s in composite_scores if 0.75 <= s < 0.85),
            "satisfactory": sum(1 for s in composite_scores if 0.65 <= s < 0.75),
            "needs_improvement": sum(1 for s in composite_scores if 0.5 <= s < 0.65),
            "poor": sum(1 for s in composite_scores if s < 0.5)
        }
        
        # Quality grades distribution
        quality_grades = [r["quality_grade"] for r in results]
        grade_distribution = {}
        for grade in quality_grades:
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        # Batch recommendations
        batch_recommendations = self._generate_batch_recommendations(results)
        
        return {
            "average_composite_score": round(average_composite, 3),
            "dimension_averages": {k: round(v, 3) for k, v in dimension_averages.items()},
            "score_distribution": score_distribution,
            "grade_distribution": grade_distribution,
            "performance_trends": self._analyze_performance_trends(results),
            "critical_issues_count": sum(len(r.get("comprehensive_analysis", {}).get("critical_issues", [])) 
                                       for r in results),
            "batch_recommendations": batch_recommendations
        }
    
    def _generate_batch_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on batch evaluation results."""
        recommendations = []
        
        # Analyze common issues
        dimension_averages = {
            "accuracy": sum(r["dimension_scores"]["accuracy"] for r in results) / len(results),
            "relevance": sum(r["dimension_scores"]["relevance"] for r in results) / len(results),
            "business_impact": sum(r["dimension_scores"]["business_impact"] for r in results) / len(results)
        }
        
        # Identify weakest dimension
        weakest_dimension = min(dimension_averages.keys(), key=lambda k: dimension_averages[k])
        
        if dimension_averages[weakest_dimension] < 0.7:
            recommendations.append(f"Focus improvement efforts on {weakest_dimension} - consistently lowest performing dimension")
        
        # Check for systemic issues
        error_count = sum(1 for r in results if r.get("evaluation_errors"))
        if error_count > len(results) * 0.1:  # More than 10% error rate
            recommendations.append("Address evaluation system errors - high failure rate detected")
        
        # Performance distribution analysis
        poor_performance_count = sum(1 for r in results if r["composite_score"] < 0.5)
        if poor_performance_count > len(results) * 0.2:  # More than 20% poor performance
            recommendations.append("Consider fundamental system redesign - high failure rate across scenarios")
        
        return recommendations
    
    def _analyze_performance_trends(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends across the batch."""
        # This could be expanded to analyze trends over time, by scenario type, etc.
        scenario_types = {}
        for result in results:
            scenario_name = result.get("scenario_name", "unknown")
            if scenario_name not in scenario_types:
                scenario_types[scenario_name] = []
            scenario_types[scenario_name].append(result["composite_score"])
        
        type_averages = {
            scenario_type: sum(scores) / len(scores)
            for scenario_type, scores in scenario_types.items()
        }
        
        return {
            "by_scenario_type": type_averages,
            "best_performing_scenario": max(type_averages.keys(), key=lambda k: type_averages[k]) if type_averages else None,
            "worst_performing_scenario": min(type_averages.keys(), key=lambda k: type_averages[k]) if type_averages else None
        }