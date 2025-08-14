#!/usr/bin/env python3
"""
Comprehensive LLM Evaluation Framework for Vertigo

Demonstrates advanced evaluation concepts including:
- Business Impact Measurement
- Multi-dimensional Quality Assessment
- Production Monitoring Integration
- Adversarial Testing
- User Experience Evaluation
- ROI Calculation
"""

import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EvaluationDimension(Enum):
    """Different dimensions for evaluating LLM performance."""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    BUSINESS_VALUE = "business_value"
    USER_SATISFACTION = "user_satisfaction"
    COST_EFFICIENCY = "cost_efficiency"
    RELIABILITY = "reliability"
    SAFETY = "safety"
    LATENCY = "latency"
    CONTEXTUAL_RELEVANCE = "contextual_relevance"

@dataclass
class EvaluationResult:
    """Comprehensive evaluation result structure."""
    dimension: EvaluationDimension
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    evidence: str
    business_impact: Optional[float] = None
    cost_impact: Optional[float] = None
    user_feedback: Optional[str] = None

@dataclass
class BusinessMetrics:
    """Business impact metrics for LLM evaluation."""
    task_completion_rate: float
    user_satisfaction_score: float
    time_saved_minutes: float
    error_resolution_rate: float
    user_retention_rate: float
    support_ticket_reduction: float

@dataclass
class ProductionMetrics:
    """Production system performance metrics."""
    throughput_requests_per_minute: float
    error_rate: float
    p95_latency_ms: float
    cost_per_request: float
    success_rate: float
    user_abandonment_rate: float

class ComprehensiveEvaluator:
    """Advanced evaluation framework for production LLM systems."""
    
    def __init__(self):
        self.evaluation_history = []
        self.business_baselines = {
            'task_completion_rate': 0.85,
            'user_satisfaction_score': 4.2,
            'time_saved_minutes': 15.0,
            'error_resolution_rate': 0.78,
            'user_retention_rate': 0.92,
            'support_ticket_reduction': 0.25
        }
        
    def evaluate_prompt_multidimensional(self, 
                                      prompt_name: str,
                                      test_cases: List[Dict],
                                      production_data: Optional[Dict] = None) -> Dict[str, EvaluationResult]:
        """Comprehensive multi-dimensional evaluation."""
        
        logger.info(f"Starting multi-dimensional evaluation for: {prompt_name}")
        results = {}
        
        # Technical Quality Dimensions
        results[EvaluationDimension.ACCURACY.value] = self._evaluate_accuracy(test_cases)
        results[EvaluationDimension.COMPLETENESS.value] = self._evaluate_completeness(test_cases)
        results[EvaluationDimension.CLARITY.value] = self._evaluate_clarity(test_cases)
        results[EvaluationDimension.RELIABILITY.value] = self._evaluate_reliability(test_cases)
        
        # Business Impact Dimensions
        if production_data:
            results[EvaluationDimension.BUSINESS_VALUE.value] = self._evaluate_business_value(production_data)
            results[EvaluationDimension.USER_SATISFACTION.value] = self._evaluate_user_satisfaction(production_data)
            results[EvaluationDimension.COST_EFFICIENCY.value] = self._evaluate_cost_efficiency(production_data)
        
        # Contextual Dimensions
        results[EvaluationDimension.CONTEXTUAL_RELEVANCE.value] = self._evaluate_contextual_relevance(test_cases)
        results[EvaluationDimension.SAFETY.value] = self._evaluate_safety(test_cases)
        
        return results
    
    def _evaluate_accuracy(self, test_cases: List[Dict]) -> EvaluationResult:
        """Evaluate accuracy using semantic similarity and factual correctness."""
        
        scores = []
        evidence_items = []
        
        for case in test_cases:
            # Simulate semantic similarity scoring
            # In production, this would use embeddings comparison
            expected = case.get('expected_output', '')
            actual = case.get('actual_output', '')
            
            # Mock scoring based on key element matching
            key_elements_expected = self._extract_key_elements(expected)
            key_elements_actual = self._extract_key_elements(actual)
            
            overlap = len(set(key_elements_expected) & set(key_elements_actual))
            total = len(set(key_elements_expected) | set(key_elements_actual))
            
            if total > 0:
                jaccard_score = overlap / total
                scores.append(jaccard_score)
                evidence_items.append(f"Key element overlap: {overlap}/{len(key_elements_expected)}")
            else:
                scores.append(0.0)
                evidence_items.append("No key elements identified")
        
        avg_score = np.mean(scores) if scores else 0.0
        confidence = 1.0 - np.std(scores) if len(scores) > 1 else 0.5
        
        return EvaluationResult(
            dimension=EvaluationDimension.ACCURACY,
            score=avg_score,
            confidence=confidence,
            evidence=f"Average accuracy across {len(test_cases)} cases. {'; '.join(evidence_items[:3])}"
        )
    
    def _evaluate_business_value(self, production_data: Dict) -> EvaluationResult:
        """Evaluate business value impact using real production metrics."""
        
        # Calculate business value score based on multiple factors
        business_metrics = production_data.get('business_metrics', {})
        
        # Weighted scoring based on business priorities
        weights = {
            'task_completion_rate': 0.3,
            'user_satisfaction_score': 0.25,
            'time_saved_minutes': 0.2,
            'error_resolution_rate': 0.15,
            'support_ticket_reduction': 0.1
        }
        
        total_score = 0.0
        evidence_items = []
        
        for metric, weight in weights.items():
            current_value = business_metrics.get(metric, 0)
            baseline_value = self.business_baselines.get(metric, 0)
            
            if baseline_value > 0:
                improvement = (current_value - baseline_value) / baseline_value
                # Convert to 0-1 score (cap at 100% improvement = 1.0)
                metric_score = min(1.0, max(0.0, 0.5 + improvement))
                total_score += metric_score * weight
                
                evidence_items.append(f"{metric}: {improvement:.1%} vs baseline")
        
        # Calculate business impact in dollars (example)
        business_impact = self._calculate_business_impact_dollars(business_metrics)
        
        return EvaluationResult(
            dimension=EvaluationDimension.BUSINESS_VALUE,
            score=total_score,
            confidence=0.8,  # Based on data quality
            evidence=f"Business improvements: {'; '.join(evidence_items)}",
            business_impact=business_impact
        )
    
    def _calculate_business_impact_dollars(self, metrics: Dict) -> float:
        """Calculate estimated business impact in dollars."""
        
        # Example calculation - would be customized per business
        time_saved = metrics.get('time_saved_minutes', 0)
        error_reduction = metrics.get('error_resolution_rate', 0) - self.business_baselines.get('error_resolution_rate', 0)
        
        # Assume $60/hour average fully-loaded employee cost
        time_value = time_saved * (60/60) * 100  # 100 users per day estimate
        error_value = error_reduction * 50 * 30  # $50 per error * 30 errors/day estimate
        
        return time_value + error_value
    
    def create_adversarial_test_cases(self, prompt_type: str) -> List[Dict]:
        """Create adversarial test cases to stress-test prompts."""
        
        base_cases = {
            'meeting_summary': [
                {
                    'name': 'Empty meeting',
                    'input': 'Meeting transcript: [No discussion occurred]',
                    'challenge': 'Handle empty or minimal content'
                },
                {
                    'name': 'Highly technical jargon',
                    'input': 'Meeting: Discussed TCP/IP stack optimization for microservices using Kubernetes ingress controllers with ISTIO service mesh implementation',
                    'challenge': 'Technical complexity without context'
                },
                {
                    'name': 'Conflicting information',
                    'input': 'John said the project is on track for Friday. Mary said we need two more weeks. The deadline is Thursday.',
                    'challenge': 'Contradictory statements'
                },
                {
                    'name': 'Emotional content',
                    'input': 'The team is frustrated with constant changes. People are threatening to quit if this continues.',
                    'challenge': 'Sensitive emotional content'
                },
                {
                    'name': 'Extremely long content',
                    'input': 'Meeting transcript: ' + 'The discussion continued for hours covering many topics. ' * 200,
                    'challenge': 'Token limits and summarization of very long content'
                }
            ],
            'email_commands': [
                {
                    'name': 'Ambiguous command',
                    'input': 'help me with stats for the thing we discussed',
                    'challenge': 'Vague reference without context'
                },
                {
                    'name': 'Multiple commands',
                    'input': 'give me help with stats and also show status and maybe some reports?',
                    'challenge': 'Multiple overlapping commands'
                },
                {
                    'name': 'Misspelled commands',
                    'input': 'sho me teh stats pls',
                    'challenge': 'Spelling errors and informal language'
                }
            ]
        }
        
        return base_cases.get(prompt_type, [])
    
    def run_production_monitoring_evaluation(self, timeframe_hours: int = 24) -> Dict:
        """Simulate production monitoring evaluation."""
        
        logger.info(f"Running production monitoring evaluation for last {timeframe_hours} hours")
        
        # Simulate production metrics
        production_metrics = ProductionMetrics(
            throughput_requests_per_minute=15.2,
            error_rate=0.03,
            p95_latency_ms=2500,
            cost_per_request=0.0021,
            success_rate=0.97,
            user_abandonment_rate=0.08
        )
        
        business_metrics = BusinessMetrics(
            task_completion_rate=0.91,
            user_satisfaction_score=4.5,
            time_saved_minutes=18.5,
            error_resolution_rate=0.85,
            user_retention_rate=0.94,
            support_ticket_reduction=0.32
        )
        
        # Analyze trends and identify issues
        alerts = self._analyze_production_trends(production_metrics, business_metrics)
        recommendations = self._generate_optimization_recommendations(production_metrics, business_metrics)
        
        return {
            'production_metrics': production_metrics,
            'business_metrics': business_metrics,
            'alerts': alerts,
            'recommendations': recommendations,
            'evaluation_timestamp': datetime.utcnow().isoformat()
        }
    
    def _analyze_production_trends(self, prod_metrics: ProductionMetrics, biz_metrics: BusinessMetrics) -> List[Dict]:
        """Analyze trends and generate alerts."""
        
        alerts = []
        
        # Error rate alert
        if prod_metrics.error_rate > 0.05:
            alerts.append({
                'level': 'HIGH',
                'message': f'Error rate {prod_metrics.error_rate:.1%} exceeds threshold of 5%',
                'impact': 'user_experience',
                'action_required': 'Investigate error patterns and implement fixes'
            })
        
        # Latency alert
        if prod_metrics.p95_latency_ms > 3000:
            alerts.append({
                'level': 'MEDIUM',
                'message': f'P95 latency {prod_metrics.p95_latency_ms}ms above target of 3000ms',
                'impact': 'user_satisfaction',
                'action_required': 'Optimize prompt efficiency or increase resources'
            })
        
        # Business metric alerts
        if biz_metrics.user_satisfaction_score < 4.0:
            alerts.append({
                'level': 'HIGH',
                'message': f'User satisfaction {biz_metrics.user_satisfaction_score} below target of 4.0',
                'impact': 'business_value',
                'action_required': 'Review user feedback and improve prompt quality'
            })
        
        return alerts
    
    def _generate_optimization_recommendations(self, prod_metrics: ProductionMetrics, biz_metrics: BusinessMetrics) -> List[Dict]:
        """Generate specific optimization recommendations."""
        
        recommendations = []
        
        # Cost optimization
        if prod_metrics.cost_per_request > 0.002:
            potential_savings = (prod_metrics.cost_per_request - 0.002) * prod_metrics.throughput_requests_per_minute * 60 * 24 * 30
            recommendations.append({
                'category': 'cost_optimization',
                'priority': 'HIGH',
                'message': 'Optimize prompts to reduce token usage',
                'potential_savings_monthly': potential_savings,
                'implementation_effort': 'MEDIUM',
                'expected_impact': 'Reduce costs by 15-25%'
            })
        
        # Performance optimization
        if prod_metrics.p95_latency_ms > 2000:
            recommendations.append({
                'category': 'performance',
                'priority': 'MEDIUM',
                'message': 'Implement prompt caching for repeated patterns',
                'potential_savings_monthly': 0,
                'implementation_effort': 'HIGH',
                'expected_impact': 'Reduce latency by 30-40%'
            })
        
        # User experience
        if biz_metrics.user_satisfaction_score < 4.5:
            recommendations.append({
                'category': 'user_experience',
                'priority': 'HIGH',
                'message': 'A/B test prompt variants focused on clarity and completeness',
                'potential_savings_monthly': 0,
                'implementation_effort': 'LOW',
                'expected_impact': 'Increase satisfaction by 10-15%'
            })
        
        return recommendations
    
    def calculate_roi_evaluation_program(self, investment_hours: float, hourly_rate: float = 150) -> Dict:
        """Calculate ROI of the evaluation program itself."""
        
        # Investment calculation
        total_investment = investment_hours * hourly_rate
        
        # Benefits calculation (based on improvements)
        monthly_cost_savings = 2500  # From optimization
        monthly_time_savings = 15 * 60 * 100  # 15 min * 100 users/day * 30 days
        monthly_error_reduction_value = 0.1 * 50 * 30  # 10% error reduction * $50/error * 30 errors/day
        
        monthly_benefits = monthly_cost_savings + (monthly_time_savings * hourly_rate / 60) + monthly_error_reduction_value
        annual_benefits = monthly_benefits * 12
        
        payback_months = total_investment / monthly_benefits if monthly_benefits > 0 else float('inf')
        roi_percentage = ((annual_benefits - total_investment) / total_investment) * 100 if total_investment > 0 else 0
        
        return {
            'total_investment': total_investment,
            'monthly_benefits': monthly_benefits,
            'annual_benefits': annual_benefits,
            'payback_months': payback_months,
            'roi_percentage': roi_percentage,
            'break_even_point': datetime.now() + timedelta(days=payback_months * 30)
        }
    
    def _extract_key_elements(self, text: str) -> List[str]:
        """Extract key elements from text for comparison."""
        # Simplified key element extraction
        # In production, this would use NLP techniques
        import re
        
        # Extract action items, names, dates, decisions
        elements = []
        
        # Simple patterns - would be more sophisticated in production
        action_pattern = r'(?:action|todo|task|deliverable)s?:?\s*([^.\n]+)'
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'  # Simple name pattern
        date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}|\d{1,2}/\d{1,2}/\d{2,4}'
        
        elements.extend(re.findall(action_pattern, text, re.IGNORECASE))
        elements.extend(re.findall(name_pattern, text))
        elements.extend(re.findall(date_pattern, text))
        
        return [elem.strip() for elem in elements if elem.strip()]
    
    def _evaluate_completeness(self, test_cases: List[Dict]) -> EvaluationResult:
        """Evaluate completeness of outputs."""
        # Mock implementation - would analyze required elements presence
        avg_score = 0.85  # Simulated
        return EvaluationResult(
            dimension=EvaluationDimension.COMPLETENESS,
            score=avg_score,
            confidence=0.75,
            evidence="Analyzed presence of required elements across test cases"
        )
    
    def _evaluate_clarity(self, test_cases: List[Dict]) -> EvaluationResult:
        """Evaluate clarity and readability."""
        # Mock implementation - would use readability metrics
        avg_score = 0.78
        return EvaluationResult(
            dimension=EvaluationDimension.CLARITY,
            score=avg_score,
            confidence=0.80,
            evidence="Readability analysis using Flesch-Kincaid and structure scoring"
        )
    
    def _evaluate_reliability(self, test_cases: List[Dict]) -> EvaluationResult:
        """Evaluate consistency and reliability."""
        # Mock implementation - would analyze variance across similar inputs
        avg_score = 0.92
        return EvaluationResult(
            dimension=EvaluationDimension.RELIABILITY,
            score=avg_score,
            confidence=0.85,
            evidence="Consistency analysis across similar input patterns"
        )
    
    def _evaluate_user_satisfaction(self, production_data: Dict) -> EvaluationResult:
        """Evaluate user satisfaction from production feedback."""
        user_metrics = production_data.get('business_metrics', {})
        satisfaction_score = user_metrics.get('user_satisfaction_score', 0) / 5.0  # Convert to 0-1
        
        return EvaluationResult(
            dimension=EvaluationDimension.USER_SATISFACTION,
            score=satisfaction_score,
            confidence=0.90,
            evidence=f"Based on {user_metrics.get('feedback_responses', 100)} user feedback responses",
            user_feedback="Generally positive with requests for faster response times"
        )
    
    def _evaluate_cost_efficiency(self, production_data: Dict) -> EvaluationResult:
        """Evaluate cost efficiency."""
        prod_metrics = production_data.get('production_metrics', {})
        cost_per_request = prod_metrics.get('cost_per_request', 0.002)
        
        # Score based on cost target (lower is better)
        target_cost = 0.0015
        if cost_per_request <= target_cost:
            score = 1.0
        else:
            score = max(0.0, 1.0 - (cost_per_request - target_cost) / target_cost)
        
        return EvaluationResult(
            dimension=EvaluationDimension.COST_EFFICIENCY,
            score=score,
            confidence=0.95,
            evidence=f"Cost per request: ${cost_per_request:.4f} vs target ${target_cost:.4f}",
            cost_impact=cost_per_request * 10000  # Monthly impact estimate
        )
    
    def _evaluate_contextual_relevance(self, test_cases: List[Dict]) -> EvaluationResult:
        """Evaluate contextual relevance."""
        # Mock implementation - would analyze context preservation
        avg_score = 0.88
        return EvaluationResult(
            dimension=EvaluationDimension.CONTEXTUAL_RELEVANCE,
            score=avg_score,
            confidence=0.75,
            evidence="Context preservation analysis across conversation flows"
        )
    
    def _evaluate_safety(self, test_cases: List[Dict]) -> EvaluationResult:
        """Evaluate safety and appropriateness."""
        # Mock implementation - would check for harmful content
        avg_score = 0.96
        return EvaluationResult(
            dimension=EvaluationDimension.SAFETY,
            score=avg_score,
            confidence=0.90,
            evidence="Safety analysis - no harmful content detected"
        )

def demonstrate_comprehensive_evaluation():
    """Demonstrate the comprehensive evaluation framework."""
    
    print("🎯 Comprehensive LLM Evaluation Framework Demonstration")
    print("=" * 80)
    
    evaluator = ComprehensiveEvaluator()
    
    # 1. Multi-dimensional Evaluation
    print("\n1️⃣ Multi-Dimensional Evaluation")
    print("-" * 50)
    
    test_cases = [
        {
            'input': 'Meeting about project status with action items',
            'expected_output': 'Summary with clear action items and next steps',
            'actual_output': 'Project status discussed. Next steps: complete testing, deploy to production.'
        }
    ]
    
    production_data = {
        'business_metrics': {
            'task_completion_rate': 0.91,
            'user_satisfaction_score': 4.5,
            'time_saved_minutes': 18.5,
            'error_resolution_rate': 0.85,
            'user_retention_rate': 0.94,
            'support_ticket_reduction': 0.32
        },
        'production_metrics': {
            'cost_per_request': 0.0018,
            'throughput_requests_per_minute': 15.2
        }
    }
    
    results = evaluator.evaluate_prompt_multidimensional(
        'Meeting Summary v2', test_cases, production_data
    )
    
    for dimension, result in results.items():
        print(f"\n📊 {dimension.replace('_', ' ').title()}:")
        print(f"   Score: {result.score:.2f} (Confidence: {result.confidence:.2f})")
        print(f"   Evidence: {result.evidence}")
        if result.business_impact:
            print(f"   Business Impact: ${result.business_impact:.2f}/month")
    
    # 2. Adversarial Testing
    print("\n\n2️⃣ Adversarial Testing")
    print("-" * 50)
    
    adversarial_cases = evaluator.create_adversarial_test_cases('meeting_summary')
    for case in adversarial_cases:
        print(f"\n🧪 {case['name']}:")
        print(f"   Challenge: {case['challenge']}")
        print(f"   Input: {case['input'][:100]}...")
    
    # 3. Production Monitoring
    print("\n\n3️⃣ Production Monitoring Evaluation")
    print("-" * 50)
    
    monitoring_results = evaluator.run_production_monitoring_evaluation()
    
    print(f"\n📈 Production Metrics:")
    prod_metrics = monitoring_results['production_metrics']
    print(f"   Throughput: {prod_metrics.throughput_requests_per_minute} req/min")
    print(f"   Error Rate: {prod_metrics.error_rate:.1%}")
    print(f"   P95 Latency: {prod_metrics.p95_latency_ms}ms")
    print(f"   Success Rate: {prod_metrics.success_rate:.1%}")
    
    print(f"\n💼 Business Metrics:")
    biz_metrics = monitoring_results['business_metrics']
    print(f"   Task Completion: {biz_metrics.task_completion_rate:.1%}")
    print(f"   User Satisfaction: {biz_metrics.user_satisfaction_score}/5.0")
    print(f"   Time Saved: {biz_metrics.time_saved_minutes} min/user")
    
    # 4. Alerts and Recommendations
    print(f"\n🚨 Alerts: {len(monitoring_results['alerts'])}")
    for alert in monitoring_results['alerts']:
        print(f"   {alert['level']}: {alert['message']}")
    
    print(f"\n💡 Recommendations: {len(monitoring_results['recommendations'])}")
    for rec in monitoring_results['recommendations']:
        print(f"   {rec['priority']}: {rec['message']}")
        if rec.get('potential_savings_monthly', 0) > 0:
            print(f"      Potential Savings: ${rec['potential_savings_monthly']:.2f}/month")
    
    # 5. ROI Calculation
    print("\n\n4️⃣ ROI Analysis")
    print("-" * 50)
    
    roi_data = evaluator.calculate_roi_evaluation_program(40, 150)  # 40 hours at $150/hour
    
    print(f"\n💰 Evaluation Program ROI:")
    print(f"   Investment: ${roi_data['total_investment']:,.2f}")
    print(f"   Monthly Benefits: ${roi_data['monthly_benefits']:,.2f}")
    print(f"   Annual Benefits: ${roi_data['annual_benefits']:,.2f}")
    print(f"   Payback Period: {roi_data['payback_months']:.1f} months")
    print(f"   ROI: {roi_data['roi_percentage']:.1f}%")
    
    print("\n✅ Comprehensive Evaluation Demonstration Complete!")
    print("=" * 80)
    
    return {
        'multidimensional_results': results,
        'adversarial_cases': adversarial_cases,
        'production_monitoring': monitoring_results,
        'roi_analysis': roi_data
    }

if __name__ == "__main__":
    demonstrate_comprehensive_evaluation()
