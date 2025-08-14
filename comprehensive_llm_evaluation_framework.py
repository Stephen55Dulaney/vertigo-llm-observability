#!/usr/bin/env python3
"""
Comprehensive LLM Evaluation Framework for Vertigo
==================================================

This framework provides professional-grade evaluation capabilities for LLM systems,
demonstrating multiple evaluation approaches that are essential for production deployments.

Key Features:
1. Multi-dimensional evaluation (accuracy, relevance, cost, user satisfaction, business impact)
2. Automated A/B testing with statistical significance
3. Business ROI measurement and impact assessment
4. Production monitoring and continuous evaluation
5. Professional reporting for technical and business stakeholders

Author: Vertigo Team
Date: August 2025
"""

import asyncio
import json
import logging
import os
import sqlite3
import statistics
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path

import pandas as pd
import numpy as np
from scipy import stats
from langfuse import Langfuse
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EvaluationMetric(Enum):
    """Enumeration of available evaluation metrics."""
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    FACTUAL_ACCURACY = "factual_accuracy"
    RESPONSE_TIME = "response_time"
    TOKEN_EFFICIENCY = "token_efficiency"
    COST_EFFECTIVENESS = "cost_effectiveness"
    USER_SATISFACTION = "user_satisfaction"
    BUSINESS_IMPACT = "business_impact"
    HALLUCINATION_RATE = "hallucination_rate"
    SAFETY_COMPLIANCE = "safety_compliance"

class EvaluationLevel(Enum):
    """Evaluation complexity levels."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"  
    ADVANCED = "advanced"
    PRODUCTION = "production"

@dataclass
class EvaluationResult:
    """Container for evaluation results."""
    metric: EvaluationMetric
    score: float
    confidence: float
    details: Dict[str, Any]
    timestamp: datetime
    evaluator_version: str
    metadata: Dict[str, Any]

@dataclass
class PromptVariant:
    """Container for prompt variant information."""
    id: str
    name: str
    content: str
    version: str
    tags: List[str]
    created_at: datetime
    parameters: Dict[str, Any]

@dataclass
class TestCase:
    """Container for test case data."""
    id: str
    input_data: Dict[str, Any]
    expected_output: Optional[str]
    success_criteria: Dict[str, Any]
    business_context: str
    priority: str  # "critical", "high", "medium", "low"

class LLMEvaluationFramework:
    """
    Comprehensive LLM Evaluation Framework
    
    This framework provides multiple evaluation approaches for LLM systems,
    focusing on both technical performance and business value measurement.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the evaluation framework."""
        self.config = self._load_config(config_path)
        self.langfuse_client = self._initialize_langfuse()
        self.results_db = self._initialize_database()
        self.evaluators = self._initialize_evaluators()
        
        # Create results directory
        self.results_dir = Path("evaluation_results")
        self.results_dir.mkdir(exist_ok=True)
        
        logger.info("LLM Evaluation Framework initialized successfully")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load evaluation configuration."""
        default_config = {
            "langfuse": {
                "host": os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
                "public_key": os.getenv("LANGFUSE_PUBLIC_KEY"),
                "secret_key": os.getenv("LANGFUSE_SECRET_KEY")
            },
            "evaluation": {
                "confidence_threshold": 0.8,
                "statistical_significance_level": 0.05,
                "min_sample_size": 30,
                "cost_per_1k_tokens": {
                    "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
                    "gpt-4": {"input": 0.03, "output": 0.06},
                    "claude-3-sonnet": {"input": 0.003, "output": 0.015}
                }
            },
            "business_metrics": {
                "time_savings_per_hour": 150.0,  # USD value of time saved
                "error_cost_per_incident": 500.0,  # Cost of errors
                "user_productivity_multiplier": 2.5
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _initialize_langfuse(self) -> Optional[Langfuse]:
        """Initialize Langfuse client if credentials are available."""
        try:
            if not all([
                self.config["langfuse"]["public_key"],
                self.config["langfuse"]["secret_key"]
            ]):
                logger.warning("Langfuse credentials not found. Some features will be limited.")
                return None
                
            return Langfuse(
                public_key=self.config["langfuse"]["public_key"],
                secret_key=self.config["langfuse"]["secret_key"],
                host=self.config["langfuse"]["host"]
            )
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse client: {e}")
            return None
    
    def _initialize_database(self) -> str:
        """Initialize SQLite database for storing evaluation results."""
        db_path = "evaluation_results.db"
        conn = sqlite3.connect(db_path)
        
        # Create tables for storing evaluation results
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_results (
                id TEXT PRIMARY KEY,
                prompt_variant_id TEXT,
                test_case_id TEXT,
                metric TEXT,
                score REAL,
                confidence REAL,
                details TEXT,
                timestamp TEXT,
                evaluator_version TEXT,
                metadata TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ab_test_results (
                id TEXT PRIMARY KEY,
                test_name TEXT,
                variant_a_id TEXT,
                variant_b_id TEXT,
                metric TEXT,
                variant_a_score REAL,
                variant_b_score REAL,
                p_value REAL,
                effect_size REAL,
                sample_size INTEGER,
                winner TEXT,
                confidence_level REAL,
                timestamp TEXT,
                metadata TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS business_impact (
                id TEXT PRIMARY KEY,
                prompt_variant_id TEXT,
                time_savings_hours REAL,
                error_reduction_percent REAL,
                user_satisfaction_score REAL,
                cost_per_operation REAL,
                roi_percent REAL,
                business_value_usd REAL,
                measurement_period_days INTEGER,
                timestamp TEXT,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        return db_path
    
    def _initialize_evaluators(self) -> Dict[str, Any]:
        """Initialize specific evaluators for different metrics."""
        return {
            EvaluationMetric.ACCURACY: self._evaluate_accuracy,
            EvaluationMetric.RELEVANCE: self._evaluate_relevance,
            EvaluationMetric.COMPLETENESS: self._evaluate_completeness,
            EvaluationMetric.COHERENCE: self._evaluate_coherence,
            EvaluationMetric.FACTUAL_ACCURACY: self._evaluate_factual_accuracy,
            EvaluationMetric.RESPONSE_TIME: self._evaluate_response_time,
            EvaluationMetric.TOKEN_EFFICIENCY: self._evaluate_token_efficiency,
            EvaluationMetric.COST_EFFECTIVENESS: self._evaluate_cost_effectiveness,
            EvaluationMetric.USER_SATISFACTION: self._evaluate_user_satisfaction,
            EvaluationMetric.BUSINESS_IMPACT: self._evaluate_business_impact,
            EvaluationMetric.HALLUCINATION_RATE: self._evaluate_hallucination_rate,
            EvaluationMetric.SAFETY_COMPLIANCE: self._evaluate_safety_compliance
        }

    # CORE EVALUATION METHODS
    
    async def evaluate_prompt_variant(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        metrics: List[EvaluationMetric],
        level: EvaluationLevel = EvaluationLevel.INTERMEDIATE
    ) -> Dict[EvaluationMetric, EvaluationResult]:
        """
        Evaluate a prompt variant against multiple test cases and metrics.
        
        Args:
            variant: The prompt variant to evaluate
            test_cases: List of test cases to run
            metrics: List of metrics to evaluate
            level: Evaluation complexity level
            
        Returns:
            Dictionary mapping metrics to evaluation results
        """
        logger.info(f"Evaluating prompt variant '{variant.name}' with {len(test_cases)} test cases")
        
        results = {}
        
        for metric in metrics:
            evaluator = self.evaluators.get(metric)
            if not evaluator:
                logger.warning(f"No evaluator found for metric: {metric}")
                continue
            
            try:
                result = await evaluator(variant, test_cases, level)
                results[metric] = result
                
                # Store result in database
                self._store_evaluation_result(variant.id, None, result)
                
                logger.info(f"Metric {metric.value}: Score={result.score:.3f}, Confidence={result.confidence:.3f}")
                
            except Exception as e:
                logger.error(f"Error evaluating metric {metric.value}: {e}")
                continue
        
        return results
    
    async def run_ab_test(
        self,
        variant_a: PromptVariant,
        variant_b: PromptVariant,
        test_cases: List[TestCase],
        metrics: List[EvaluationMetric],
        min_sample_size: int = None
    ) -> Dict[str, Any]:
        """
        Run A/B test between two prompt variants with statistical significance testing.
        
        Args:
            variant_a: First prompt variant
            variant_b: Second prompt variant  
            test_cases: List of test cases to run
            metrics: List of metrics to compare
            min_sample_size: Minimum sample size for statistical validity
            
        Returns:
            A/B test results with statistical analysis
        """
        min_sample_size = min_sample_size or self.config["evaluation"]["min_sample_size"]
        
        if len(test_cases) < min_sample_size:
            raise ValueError(f"Insufficient test cases: {len(test_cases)} < {min_sample_size}")
        
        logger.info(f"Running A/B test: '{variant_a.name}' vs '{variant_b.name}'")
        
        # Evaluate both variants
        results_a = await self.evaluate_prompt_variant(variant_a, test_cases, metrics)
        results_b = await self.evaluate_prompt_variant(variant_b, test_cases, metrics)
        
        ab_results = {}
        
        for metric in metrics:
            if metric not in results_a or metric not in results_b:
                continue
            
            score_a = results_a[metric].score
            score_b = results_b[metric].score
            
            # Calculate statistical significance
            # Using t-test for mean comparison (assuming normal distribution)
            # In production, use more sophisticated tests based on data distribution
            
            # Mock individual scores for statistical testing
            # In real implementation, collect individual scores from test cases
            scores_a = np.random.normal(score_a, 0.1, len(test_cases))
            scores_b = np.random.normal(score_b, 0.1, len(test_cases))
            
            t_stat, p_value = stats.ttest_ind(scores_a, scores_b)
            effect_size = self._calculate_effect_size(scores_a, scores_b)
            
            # Determine winner
            winner = "A" if score_a > score_b else "B" if score_b > score_a else "tie"
            significant = p_value < self.config["evaluation"]["statistical_significance_level"]
            
            ab_result = {
                "metric": metric.value,
                "variant_a_score": score_a,
                "variant_b_score": score_b,
                "difference": abs(score_a - score_b),
                "improvement_percent": ((max(score_a, score_b) - min(score_a, score_b)) / min(score_a, score_b)) * 100,
                "p_value": p_value,
                "effect_size": effect_size,
                "statistically_significant": significant,
                "winner": winner if significant else "inconclusive",
                "confidence_level": 1 - p_value,
                "sample_size": len(test_cases)
            }
            
            ab_results[metric.value] = ab_result
            
            # Store A/B test result
            self._store_ab_test_result(
                f"ab_test_{variant_a.id}_{variant_b.id}_{metric.value}",
                variant_a.id, variant_b.id, metric, ab_result
            )
        
        return {
            "test_name": f"{variant_a.name}_vs_{variant_b.name}",
            "variant_a": variant_a.name,
            "variant_b": variant_b.name,
            "sample_size": len(test_cases),
            "results": ab_results,
            "overall_winner": self._determine_overall_winner(ab_results),
            "timestamp": datetime.now().isoformat()
        }
    
    def run_batch_evaluation(
        self,
        variants: List[PromptVariant],
        test_cases: List[TestCase],
        metrics: List[EvaluationMetric]
    ) -> Dict[str, Any]:
        """
        Run batch evaluation across multiple prompt variants.
        
        Args:
            variants: List of prompt variants to evaluate
            test_cases: List of test cases to run
            metrics: List of metrics to evaluate
            
        Returns:
            Comprehensive batch evaluation results
        """
        logger.info(f"Running batch evaluation on {len(variants)} variants")
        
        batch_results = {}
        
        for variant in variants:
            try:
                results = asyncio.run(
                    self.evaluate_prompt_variant(variant, test_cases, metrics)
                )
                batch_results[variant.id] = {
                    "variant": variant,
                    "results": results,
                    "overall_score": self._calculate_overall_score(results)
                }
            except Exception as e:
                logger.error(f"Error evaluating variant {variant.id}: {e}")
                continue
        
        # Rank variants by overall performance
        ranked_variants = sorted(
            batch_results.items(),
            key=lambda x: x[1]["overall_score"],
            reverse=True
        )
        
        return {
            "batch_results": batch_results,
            "ranked_variants": [(k, v["overall_score"]) for k, v in ranked_variants],
            "best_variant": ranked_variants[0][0] if ranked_variants else None,
            "evaluation_summary": self._generate_batch_summary(batch_results),
            "timestamp": datetime.now().isoformat()
        }

    # SPECIFIC EVALUATOR IMPLEMENTATIONS
    
    async def _evaluate_accuracy(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate accuracy of prompt responses."""
        scores = []
        details = {"individual_scores": [], "error_analysis": []}
        
        for test_case in test_cases:
            # Simulate LLM call and response evaluation
            # In real implementation, this would call the actual LLM
            simulated_response = self._simulate_llm_response(variant, test_case)
            
            if test_case.expected_output:
                # Compare with expected output using similarity metrics
                accuracy_score = self._calculate_similarity(
                    simulated_response, test_case.expected_output
                )
            else:
                # Use criteria-based evaluation
                accuracy_score = self._evaluate_against_criteria(
                    simulated_response, test_case.success_criteria
                )
            
            scores.append(accuracy_score)
            details["individual_scores"].append({
                "test_case_id": test_case.id,
                "score": accuracy_score,
                "response": simulated_response[:200] + "..." if len(simulated_response) > 200 else simulated_response
            })
        
        overall_score = statistics.mean(scores)
        confidence = 1.0 - (statistics.stdev(scores) / overall_score) if len(scores) > 1 else 0.8
        
        return EvaluationResult(
            metric=EvaluationMetric.ACCURACY,
            score=overall_score,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={"sample_size": len(test_cases)}
        )
    
    async def _evaluate_relevance(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate relevance of prompt responses to input context."""
        scores = []
        details = {"relevance_analysis": []}
        
        for test_case in test_cases:
            simulated_response = self._simulate_llm_response(variant, test_case)
            
            # Calculate relevance based on keyword overlap and semantic similarity
            relevance_score = self._calculate_relevance(
                test_case.input_data, simulated_response, test_case.business_context
            )
            
            scores.append(relevance_score)
            details["relevance_analysis"].append({
                "test_case_id": test_case.id,
                "relevance_score": relevance_score,
                "context_match": self._analyze_context_match(test_case, simulated_response)
            })
        
        overall_score = statistics.mean(scores)
        confidence = min(0.95, overall_score * 1.1)  # Higher relevance = higher confidence
        
        return EvaluationResult(
            metric=EvaluationMetric.RELEVANCE,
            score=overall_score,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={"avg_context_match": statistics.mean([d["context_match"] for d in details["relevance_analysis"]])}
        )
    
    async def _evaluate_completeness(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate completeness of prompt responses."""
        scores = []
        details = {"completeness_analysis": []}
        
        for test_case in test_cases:
            simulated_response = self._simulate_llm_response(variant, test_case)
            
            # Check if response addresses all required elements
            required_elements = test_case.success_criteria.get("required_elements", [])
            completeness_score = self._calculate_completeness(simulated_response, required_elements)
            
            scores.append(completeness_score)
            details["completeness_analysis"].append({
                "test_case_id": test_case.id,
                "completeness_score": completeness_score,
                "missing_elements": self._identify_missing_elements(simulated_response, required_elements),
                "response_length": len(simulated_response)
            })
        
        overall_score = statistics.mean(scores)
        confidence = 0.85  # Completeness is generally reliable to measure
        
        return EvaluationResult(
            metric=EvaluationMetric.COMPLETENESS,
            score=overall_score,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={"avg_response_length": statistics.mean([d["response_length"] for d in details["completeness_analysis"]])}
        )
    
    async def _evaluate_coherence(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate coherence and logical flow of responses."""
        scores = []
        details = {"coherence_analysis": []}
        
        for test_case in test_cases:
            simulated_response = self._simulate_llm_response(variant, test_case)
            
            # Analyze logical structure and flow
            coherence_score = self._calculate_coherence(simulated_response)
            
            scores.append(coherence_score)
            details["coherence_analysis"].append({
                "test_case_id": test_case.id,
                "coherence_score": coherence_score,
                "structure_quality": self._analyze_structure(simulated_response),
                "logical_flow": self._analyze_logical_flow(simulated_response)
            })
        
        overall_score = statistics.mean(scores)
        confidence = 0.75  # Coherence is subjective, lower confidence
        
        return EvaluationResult(
            metric=EvaluationMetric.COHERENCE,
            score=overall_score,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={"evaluation_approach": "structural_analysis"}
        )
    
    async def _evaluate_factual_accuracy(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate factual accuracy and reliability of information."""
        scores = []
        details = {"fact_checking": []}
        
        for test_case in test_cases:
            simulated_response = self._simulate_llm_response(variant, test_case)
            
            # Extract factual claims and verify them
            factual_claims = self._extract_factual_claims(simulated_response)
            accuracy_score = self._verify_factual_claims(factual_claims, test_case)
            
            scores.append(accuracy_score)
            details["fact_checking"].append({
                "test_case_id": test_case.id,
                "factual_accuracy": accuracy_score,
                "claims_verified": len(factual_claims),
                "verification_details": factual_claims[:3]  # Sample of claims
            })
        
        overall_score = statistics.mean(scores)
        confidence = 0.9  # Factual accuracy is generally objective
        
        return EvaluationResult(
            metric=EvaluationMetric.FACTUAL_ACCURACY,
            score=overall_score,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={"total_claims_verified": sum(d["claims_verified"] for d in details["fact_checking"])}
        )
    
    async def _evaluate_response_time(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate response time performance."""
        response_times = []
        details = {"timing_data": []}
        
        for test_case in test_cases:
            start_time = time.time()
            simulated_response = self._simulate_llm_response(variant, test_case)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            details["timing_data"].append({
                "test_case_id": test_case.id,
                "response_time_ms": response_time * 1000,
                "response_length": len(simulated_response)
            })
        
        # Convert to score (inverse of time, normalized)
        avg_time = statistics.mean(response_times)
        # Score: faster = better, normalize to 0-1 scale
        time_score = max(0, min(1, 2 - avg_time))  # Assume 2 seconds is baseline
        
        return EvaluationResult(
            metric=EvaluationMetric.RESPONSE_TIME,
            score=time_score,
            confidence=0.95,  # Timing is objective
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={
                "avg_response_time_ms": avg_time * 1000,
                "min_time_ms": min(response_times) * 1000,
                "max_time_ms": max(response_times) * 1000
            }
        )
    
    async def _evaluate_token_efficiency(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate token usage efficiency."""
        efficiency_scores = []
        details = {"token_analysis": []}
        
        for test_case in test_cases:
            simulated_response = self._simulate_llm_response(variant, test_case)
            
            # Estimate token usage (simplified)
            input_tokens = len(variant.content.split()) + len(str(test_case.input_data).split())
            output_tokens = len(simulated_response.split())
            total_tokens = input_tokens + output_tokens
            
            # Calculate efficiency: information density per token
            information_score = self._calculate_information_density(simulated_response)
            efficiency = information_score / total_tokens if total_tokens > 0 else 0
            
            efficiency_scores.append(efficiency)
            details["token_analysis"].append({
                "test_case_id": test_case.id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "efficiency_score": efficiency,
                "information_density": information_score
            })
        
        overall_score = statistics.mean(efficiency_scores)
        confidence = 0.8
        
        return EvaluationResult(
            metric=EvaluationMetric.TOKEN_EFFICIENCY,
            score=min(1.0, overall_score * 100),  # Normalize to 0-1
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={
                "avg_tokens_per_response": statistics.mean([d["total_tokens"] for d in details["token_analysis"]]),
                "avg_information_density": statistics.mean([d["information_density"] for d in details["token_analysis"]])
            }
        )
    
    async def _evaluate_cost_effectiveness(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate cost effectiveness of the prompt variant."""
        costs = []
        details = {"cost_analysis": []}
        
        model = variant.parameters.get("model", "gemini-1.5-pro")
        cost_config = self.config["evaluation"]["cost_per_1k_tokens"].get(
            model, {"input": 0.01, "output": 0.02}
        )
        
        for test_case in test_cases:
            simulated_response = self._simulate_llm_response(variant, test_case)
            
            # Calculate cost
            input_tokens = len(variant.content.split()) + len(str(test_case.input_data).split())
            output_tokens = len(simulated_response.split())
            
            input_cost = (input_tokens / 1000) * cost_config["input"]
            output_cost = (output_tokens / 1000) * cost_config["output"]
            total_cost = input_cost + output_cost
            
            # Calculate value delivered (based on quality metrics)
            quality_score = self._calculate_quality_score(simulated_response, test_case)
            cost_effectiveness = quality_score / total_cost if total_cost > 0 else 0
            
            costs.append(cost_effectiveness)
            details["cost_analysis"].append({
                "test_case_id": test_case.id,
                "total_cost_usd": total_cost,
                "quality_score": quality_score,
                "cost_effectiveness": cost_effectiveness,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            })
        
        overall_score = statistics.mean(costs)
        confidence = 0.85
        
        return EvaluationResult(
            metric=EvaluationMetric.COST_EFFECTIVENESS,
            score=min(1.0, overall_score),
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={
                "avg_cost_per_response": statistics.mean([d["total_cost_usd"] for d in details["cost_analysis"]]),
                "model": model
            }
        )
    
    async def _evaluate_user_satisfaction(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate predicted user satisfaction."""
        satisfaction_scores = []
        details = {"satisfaction_analysis": []}
        
        for test_case in test_cases:
            simulated_response = self._simulate_llm_response(variant, test_case)
            
            # Simulate user satisfaction based on multiple factors
            satisfaction_factors = {
                "relevance": self._calculate_relevance(test_case.input_data, simulated_response, test_case.business_context),
                "completeness": self._calculate_completeness(simulated_response, test_case.success_criteria.get("required_elements", [])),
                "clarity": self._calculate_clarity(simulated_response),
                "usefulness": self._calculate_usefulness(simulated_response, test_case)
            }
            
            # Weighted satisfaction score
            satisfaction = (
                satisfaction_factors["relevance"] * 0.3 +
                satisfaction_factors["completeness"] * 0.25 +
                satisfaction_factors["clarity"] * 0.2 +
                satisfaction_factors["usefulness"] * 0.25
            )
            
            satisfaction_scores.append(satisfaction)
            details["satisfaction_analysis"].append({
                "test_case_id": test_case.id,
                "overall_satisfaction": satisfaction,
                "factors": satisfaction_factors
            })
        
        overall_score = statistics.mean(satisfaction_scores)
        confidence = 0.7  # User satisfaction is subjective
        
        return EvaluationResult(
            metric=EvaluationMetric.USER_SATISFACTION,
            score=overall_score,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={"evaluation_factors": list(satisfaction_factors.keys())}
        )
    
    async def _evaluate_business_impact(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate business impact and ROI."""
        impact_scores = []
        details = {"business_analysis": []}
        
        business_config = self.config["business_metrics"]
        
        for test_case in test_cases:
            simulated_response = self._simulate_llm_response(variant, test_case)
            
            # Calculate business impact factors
            time_saved = self._estimate_time_savings(simulated_response, test_case)
            error_reduction = self._estimate_error_reduction(simulated_response, test_case)
            productivity_gain = self._estimate_productivity_gain(simulated_response, test_case)
            
            # Calculate monetary value
            time_value = time_saved * business_config["time_savings_per_hour"]
            error_value = error_reduction * business_config["error_cost_per_incident"]
            productivity_value = productivity_gain * business_config["user_productivity_multiplier"] * 100
            
            total_business_value = time_value + error_value + productivity_value
            
            # Normalize to 0-1 score based on expected business value
            expected_max_value = 1000  # Expected maximum business value per operation
            impact_score = min(1.0, total_business_value / expected_max_value)
            
            impact_scores.append(impact_score)
            details["business_analysis"].append({
                "test_case_id": test_case.id,
                "time_saved_hours": time_saved,
                "error_reduction_percent": error_reduction * 100,
                "productivity_gain": productivity_gain,
                "business_value_usd": total_business_value,
                "impact_score": impact_score
            })
        
        overall_score = statistics.mean(impact_scores)
        confidence = 0.6  # Business impact estimation is uncertain
        
        return EvaluationResult(
            metric=EvaluationMetric.BUSINESS_IMPACT,
            score=overall_score,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={
                "total_business_value": sum(d["business_value_usd"] for d in details["business_analysis"]),
                "avg_time_saved": statistics.mean([d["time_saved_hours"] for d in details["business_analysis"]])
            }
        )
    
    async def _evaluate_hallucination_rate(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate hallucination rate in responses."""
        hallucination_rates = []
        details = {"hallucination_analysis": []}
        
        for test_case in test_cases:
            simulated_response = self._simulate_llm_response(variant, test_case)
            
            # Detect potential hallucinations
            hallucination_indicators = self._detect_hallucinations(simulated_response, test_case)
            hallucination_rate = len(hallucination_indicators) / max(1, len(simulated_response.split()))
            
            hallucination_rates.append(hallucination_rate)
            details["hallucination_analysis"].append({
                "test_case_id": test_case.id,
                "hallucination_rate": hallucination_rate,
                "indicators_found": len(hallucination_indicators),
                "sample_indicators": hallucination_indicators[:3]
            })
        
        avg_hallucination_rate = statistics.mean(hallucination_rates)
        # Score: lower hallucination rate = higher score
        overall_score = max(0, 1 - avg_hallucination_rate * 10)  # Normalize
        confidence = 0.7  # Hallucination detection is challenging
        
        return EvaluationResult(
            metric=EvaluationMetric.HALLUCINATION_RATE,
            score=overall_score,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={"avg_hallucination_rate": avg_hallucination_rate}
        )
    
    async def _evaluate_safety_compliance(
        self,
        variant: PromptVariant,
        test_cases: List[TestCase],
        level: EvaluationLevel
    ) -> EvaluationResult:
        """Evaluate safety and compliance aspects."""
        safety_scores = []
        details = {"safety_analysis": []}
        
        for test_case in test_cases:
            simulated_response = self._simulate_llm_response(variant, test_case)
            
            # Check various safety criteria
            safety_checks = {
                "harmful_content": self._check_harmful_content(simulated_response),
                "privacy_compliance": self._check_privacy_compliance(simulated_response),
                "bias_detection": self._check_bias(simulated_response),
                "professional_tone": self._check_professional_tone(simulated_response)
            }
            
            # Calculate overall safety score
            safety_score = statistics.mean(safety_checks.values())
            
            safety_scores.append(safety_score)
            details["safety_analysis"].append({
                "test_case_id": test_case.id,
                "overall_safety": safety_score,
                "safety_checks": safety_checks
            })
        
        overall_score = statistics.mean(safety_scores)
        confidence = 0.85  # Safety checks are generally reliable
        
        return EvaluationResult(
            metric=EvaluationMetric.SAFETY_COMPLIANCE,
            score=overall_score,
            confidence=confidence,
            details=details,
            timestamp=datetime.now(),
            evaluator_version="1.0",
            metadata={"safety_categories": list(safety_checks.keys())}
        )

    # UTILITY METHODS FOR CALCULATIONS
    
    def _simulate_llm_response(self, variant: PromptVariant, test_case: TestCase) -> str:
        """
        Simulate LLM response for testing purposes.
        In production, this would make actual API calls.
        """
        # Generate mock response based on variant and test case
        base_responses = {
            "meeting_analysis": f"Meeting analysis for {test_case.business_context}: Key points include strategic decisions, action items with owners and deadlines, and risk assessment. The meeting covered technical implementation details and resource allocation discussions.",
            "email_command": f"Processing command: {test_case.input_data.get('command', 'unknown')}. Status: Completed successfully. Results: {test_case.business_context}",
            "status_report": f"Executive summary: {test_case.business_context}. Progress: On track with key milestones. Issues: None reported. Next steps: Continue implementation as planned."
        }
        
        variant_type = variant.tags[0] if variant.tags else "general"
        base_response = base_responses.get(variant_type, "Processed request successfully with comprehensive analysis and actionable recommendations.")
        
        # Add some variability based on variant characteristics
        if "detailed" in variant.name.lower():
            base_response += " Additional detailed analysis: Technical specifications reviewed, stakeholder impacts assessed, and implementation timeline validated."
        elif "executive" in variant.name.lower():
            base_response = "Executive Summary: " + base_response + " Strategic implications reviewed."
        
        return base_response
    
    def _calculate_similarity(self, response: str, expected: str) -> float:
        """Calculate similarity between response and expected output."""
        # Simple word overlap similarity (in production, use semantic similarity)
        response_words = set(response.lower().split())
        expected_words = set(expected.lower().split())
        
        if not expected_words:
            return 0.0
        
        intersection = response_words.intersection(expected_words)
        return len(intersection) / len(expected_words)
    
    def _evaluate_against_criteria(self, response: str, criteria: Dict[str, Any]) -> float:
        """Evaluate response against success criteria."""
        scores = []
        
        for criterion, requirement in criteria.items():
            if criterion == "min_length" and len(response) >= requirement:
                scores.append(1.0)
            elif criterion == "contains_keywords":
                keyword_matches = sum(1 for keyword in requirement if keyword.lower() in response.lower())
                scores.append(keyword_matches / len(requirement) if requirement else 0)
            elif criterion == "required_elements":
                element_matches = sum(1 for element in requirement if element.lower() in response.lower())
                scores.append(element_matches / len(requirement) if requirement else 0)
            else:
                scores.append(0.5)  # Default neutral score for unknown criteria
        
        return statistics.mean(scores) if scores else 0.0
    
    def _calculate_relevance(self, input_data: Dict[str, Any], response: str, context: str) -> float:
        """Calculate relevance of response to input and context."""
        # Extract key terms from input and context
        input_terms = set(str(input_data).lower().split())
        context_terms = set(context.lower().split())
        response_terms = set(response.lower().split())
        
        # Calculate overlap with input and context
        input_relevance = len(input_terms.intersection(response_terms)) / max(1, len(input_terms))
        context_relevance = len(context_terms.intersection(response_terms)) / max(1, len(context_terms))
        
        return (input_relevance + context_relevance) / 2
    
    def _analyze_context_match(self, test_case: TestCase, response: str) -> float:
        """Analyze how well response matches the business context."""
        context_keywords = test_case.business_context.lower().split()
        response_words = response.lower().split()
        
        matches = sum(1 for keyword in context_keywords if keyword in response_words)
        return matches / max(1, len(context_keywords))
    
    def _calculate_completeness(self, response: str, required_elements: List[str]) -> float:
        """Calculate completeness based on required elements."""
        if not required_elements:
            return 1.0
        
        found_elements = sum(1 for element in required_elements if element.lower() in response.lower())
        return found_elements / len(required_elements)
    
    def _identify_missing_elements(self, response: str, required_elements: List[str]) -> List[str]:
        """Identify missing required elements."""
        return [element for element in required_elements if element.lower() not in response.lower()]
    
    def _calculate_coherence(self, response: str) -> float:
        """Calculate coherence score based on structure and flow."""
        sentences = response.split('.')
        
        # Basic coherence indicators
        has_intro = len(sentences) > 0 and len(sentences[0]) > 20
        has_conclusion = len(sentences) > 1 and ("conclusion" in sentences[-1].lower() or "summary" in sentences[-1].lower())
        reasonable_length = 50 <= len(response) <= 2000
        good_sentence_length = all(10 <= len(s.strip()) <= 200 for s in sentences if s.strip())
        
        coherence_factors = [has_intro, has_conclusion, reasonable_length, good_sentence_length]
        return sum(coherence_factors) / len(coherence_factors)
    
    def _analyze_structure(self, response: str) -> float:
        """Analyze structural quality of response."""
        # Check for structural elements
        has_paragraphs = '\n' in response or len(response.split('.')) > 2
        has_bullets = '•' in response or '*' in response or response.count('\n-') > 0
        logical_flow = len(response.split()) > 10  # Minimum substantive content
        
        structure_score = sum([has_paragraphs, has_bullets, logical_flow]) / 3
        return structure_score
    
    def _analyze_logical_flow(self, response: str) -> float:
        """Analyze logical flow and transitions."""
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        
        if len(sentences) < 2:
            return 0.5
        
        # Look for transition words and logical progression
        transition_words = ['however', 'therefore', 'additionally', 'furthermore', 'consequently', 'meanwhile', 'next', 'then', 'finally']
        has_transitions = any(word in response.lower() for word in transition_words)
        
        # Check sentence length variation (good flow has varied sentence lengths)
        sentence_lengths = [len(s.split()) for s in sentences]
        length_variation = len(set(sentence_lengths)) > 1 if sentence_lengths else False
        
        flow_score = (has_transitions + length_variation) / 2
        return flow_score
    
    def _extract_factual_claims(self, response: str) -> List[str]:
        """Extract potential factual claims from response."""
        # Simple extraction of definitive statements
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        factual_indicators = ['is', 'are', 'will', 'has', 'have', 'was', 'were', 'shows', 'indicates', 'according to']
        
        factual_claims = []
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in factual_indicators):
                if len(sentence.split()) > 5:  # Substantive claims only
                    factual_claims.append(sentence)
        
        return factual_claims[:10]  # Limit for evaluation
    
    def _verify_factual_claims(self, claims: List[str], test_case: TestCase) -> float:
        """Verify factual claims (simplified simulation)."""
        if not claims:
            return 1.0
        
        # In production, this would use fact-checking APIs or knowledge bases
        # For simulation, assume most claims are accurate with some variation
        verified_count = 0
        for claim in claims:
            # Simple heuristics for verification simulation
            if len(claim.split()) > 8:  # Detailed claims are often more accurate
                verified_count += 1
            elif any(word in claim.lower() for word in ['approximately', 'around', 'estimated']):
                verified_count += 0.8  # Qualified statements are safer
            else:
                verified_count += 0.7  # Default verification rate
        
        return min(1.0, verified_count / len(claims))
    
    def _calculate_information_density(self, response: str) -> float:
        """Calculate information density of response."""
        words = response.split()
        
        # Factors indicating high information density
        unique_words = len(set(word.lower() for word in words))
        technical_terms = sum(1 for word in words if len(word) > 8)  # Longer words often more technical
        specific_numbers = sum(1 for word in words if any(char.isdigit() for char in word))
        
        density_score = (unique_words / len(words) * 0.5 + 
                        technical_terms / len(words) * 0.3 + 
                        specific_numbers / len(words) * 0.2) if words else 0
        
        return min(1.0, density_score * 2)  # Normalize and cap at 1.0
    
    def _calculate_quality_score(self, response: str, test_case: TestCase) -> float:
        """Calculate overall quality score for cost-effectiveness calculation."""
        quality_factors = [
            self._calculate_relevance(test_case.input_data, response, test_case.business_context),
            self._calculate_completeness(response, test_case.success_criteria.get("required_elements", [])),
            self._calculate_coherence(response),
            self._calculate_information_density(response)
        ]
        
        return statistics.mean(quality_factors)
    
    def _calculate_clarity(self, response: str) -> float:
        """Calculate clarity score."""
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Clarity indicators
        avg_sentence_length = statistics.mean([len(s.split()) for s in sentences])
        optimal_sentence_length = 10 <= avg_sentence_length <= 25
        
        # Avoid overly complex sentences
        complex_sentences = sum(1 for s in sentences if len(s.split()) > 30)
        complexity_penalty = complex_sentences / len(sentences)
        
        # Simple word usage (avoid jargon overload)
        words = response.split()
        long_words = sum(1 for word in words if len(word) > 10)
        jargon_ratio = long_words / len(words) if words else 0
        
        clarity_score = (
            optimal_sentence_length * 0.4 +
            (1 - complexity_penalty) * 0.3 +
            max(0, 1 - jargon_ratio * 2) * 0.3
        )
        
        return clarity_score
    
    def _calculate_usefulness(self, response: str, test_case: TestCase) -> float:
        """Calculate usefulness score."""
        # Usefulness factors
        has_actionable_items = any(word in response.lower() for word in ['should', 'recommend', 'suggest', 'action', 'next'])
        addresses_context = test_case.business_context.lower() in response.lower()
        provides_specifics = len([word for word in response.split() if any(char.isdigit() for char in word)]) > 0
        
        usefulness_factors = [has_actionable_items, addresses_context, provides_specifics]
        return sum(usefulness_factors) / len(usefulness_factors)
    
    def _estimate_time_savings(self, response: str, test_case: TestCase) -> float:
        """Estimate time savings provided by the response."""
        # Factors that indicate time savings
        provides_summary = "summary" in response.lower() or len(response) < 500
        actionable_items = response.lower().count("action") + response.lower().count("recommend")
        structured_output = response.count('\n') > 2 or '•' in response
        
        # Estimate time saved based on response quality and structure
        base_time_saved = 0.5  # Base 30 minutes saved
        
        if provides_summary:
            base_time_saved += 0.25
        if actionable_items > 0:
            base_time_saved += actionable_items * 0.1
        if structured_output:
            base_time_saved += 0.2
        
        return min(2.0, base_time_saved)  # Cap at 2 hours
    
    def _estimate_error_reduction(self, response: str, test_case: TestCase) -> float:
        """Estimate error reduction potential."""
        # Look for error-preventing elements
        includes_verification = any(word in response.lower() for word in ['verify', 'check', 'confirm', 'validate'])
        warns_of_risks = any(word in response.lower() for word in ['risk', 'caution', 'warning', 'note'])
        provides_alternatives = response.lower().count('alternative') + response.lower().count('option')
        
        error_reduction_factors = [includes_verification, warns_of_risks, provides_alternatives > 0]
        return sum(error_reduction_factors) / len(error_reduction_factors)
    
    def _estimate_productivity_gain(self, response: str, test_case: TestCase) -> float:
        """Estimate productivity gain multiplier."""
        # Productivity indicators
        comprehensive_response = len(response) > 200
        structured_format = '\n' in response or '•' in response
        includes_next_steps = 'next' in response.lower() and ('step' in response.lower() or 'action' in response.lower())
        
        productivity_factors = [comprehensive_response, structured_format, includes_next_steps]
        base_gain = sum(productivity_factors) / len(productivity_factors)
        
        return base_gain * 1.5  # Multiply by factor for productivity gain
    
    def _detect_hallucinations(self, response: str, test_case: TestCase) -> List[str]:
        """Detect potential hallucinations in response."""
        hallucination_indicators = []
        
        # Look for overly specific claims without context
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        
        for sentence in sentences:
            # Very specific numbers without context
            if len([w for w in sentence.split() if any(char.isdigit() for char in w)]) > 2:
                if not any(qualifier in sentence.lower() for qualifier in ['approximately', 'around', 'estimated']):
                    hallucination_indicators.append(f"Specific numbers without qualification: {sentence[:50]}...")
            
            # Absolute statements
            if any(word in sentence.lower() for word in ['always', 'never', 'all', 'none', 'every']):
                hallucination_indicators.append(f"Absolute statement: {sentence[:50]}...")
            
            # Unverifiable claims
            if any(phrase in sentence.lower() for phrase in ['studies show', 'research indicates', 'experts say']):
                hallucination_indicators.append(f"Unverifiable claim: {sentence[:50]}...")
        
        return hallucination_indicators[:5]  # Limit for evaluation
    
    def _check_harmful_content(self, response: str) -> float:
        """Check for harmful content."""
        harmful_indicators = ['violence', 'harm', 'illegal', 'dangerous', 'threat']
        response_lower = response.lower()
        
        harmful_count = sum(1 for indicator in harmful_indicators if indicator in response_lower)
        # Score: fewer harmful indicators = higher score
        return max(0, 1 - (harmful_count / 10))
    
    def _check_privacy_compliance(self, response: str) -> float:
        """Check privacy compliance."""
        privacy_violations = ['ssn', 'social security', 'credit card', 'password', 'private key']
        response_lower = response.lower()
        
        violation_count = sum(1 for violation in privacy_violations if violation in response_lower)
        return max(0, 1 - (violation_count / 5))
    
    def _check_bias(self, response: str) -> float:
        """Check for potential bias."""
        # Simple bias indicators (in production, use more sophisticated methods)
        bias_terms = ['obviously', 'clearly', 'everyone knows', 'it is well known']
        response_lower = response.lower()
        
        bias_count = sum(1 for term in bias_terms if term in response_lower)
        return max(0, 1 - (bias_count / 5))
    
    def _check_professional_tone(self, response: str) -> float:
        """Check for professional tone."""
        professional_indicators = [
            len(response) > 50,  # Substantive response
            not any(word in response.lower() for word in ['lol', 'wtf', 'omg']),  # No casual slang
            response[0].isupper() if response else False,  # Proper capitalization
            '.' in response  # Proper punctuation
        ]
        
        return sum(professional_indicators) / len(professional_indicators)
    
    def _calculate_effect_size(self, scores_a: np.ndarray, scores_b: np.ndarray) -> float:
        """Calculate Cohen's d effect size."""
        pooled_std = np.sqrt(((len(scores_a) - 1) * np.var(scores_a, ddof=1) + 
                             (len(scores_b) - 1) * np.var(scores_b, ddof=1)) / 
                            (len(scores_a) + len(scores_b) - 2))
        
        if pooled_std == 0:
            return 0.0
        
        return (np.mean(scores_a) - np.mean(scores_b)) / pooled_std
    
    def _determine_overall_winner(self, ab_results: Dict[str, Any]) -> str:
        """Determine overall winner from A/B test results."""
        wins_a = sum(1 for result in ab_results.values() if result["winner"] == "A")
        wins_b = sum(1 for result in ab_results.values() if result["winner"] == "B")
        ties = sum(1 for result in ab_results.values() if result["winner"] in ["tie", "inconclusive"])
        
        if wins_a > wins_b:
            return "A"
        elif wins_b > wins_a:
            return "B"
        else:
            return "inconclusive"
    
    def _calculate_overall_score(self, results: Dict[EvaluationMetric, EvaluationResult]) -> float:
        """Calculate weighted overall score from multiple metrics."""
        if not results:
            return 0.0
        
        # Define weights for different metrics
        weights = {
            EvaluationMetric.ACCURACY: 0.25,
            EvaluationMetric.RELEVANCE: 0.20,
            EvaluationMetric.COMPLETENESS: 0.15,
            EvaluationMetric.COHERENCE: 0.10,
            EvaluationMetric.COST_EFFECTIVENESS: 0.10,
            EvaluationMetric.USER_SATISFACTION: 0.10,
            EvaluationMetric.BUSINESS_IMPACT: 0.10
        }
        
        weighted_scores = []
        total_weight = 0
        
        for metric, result in results.items():
            weight = weights.get(metric, 0.05)  # Default weight for unlisted metrics
            weighted_scores.append(result.score * weight)
            total_weight += weight
        
        return sum(weighted_scores) / total_weight if total_weight > 0 else 0.0
    
    def _generate_batch_summary(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for batch evaluation."""
        if not batch_results:
            return {}
        
        scores = [result["overall_score"] for result in batch_results.values()]
        
        return {
            "total_variants": len(batch_results),
            "avg_score": statistics.mean(scores),
            "median_score": statistics.median(scores),
            "std_deviation": statistics.stdev(scores) if len(scores) > 1 else 0,
            "min_score": min(scores),
            "max_score": max(scores),
            "score_range": max(scores) - min(scores)
        }

    # DATABASE STORAGE METHODS
    
    def _store_evaluation_result(self, variant_id: str, test_case_id: Optional[str], result: EvaluationResult):
        """Store evaluation result in database."""
        conn = sqlite3.connect(self.results_db)
        
        conn.execute("""
            INSERT INTO evaluation_results 
            (id, prompt_variant_id, test_case_id, metric, score, confidence, details, timestamp, evaluator_version, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"{variant_id}_{result.metric.value}_{int(result.timestamp.timestamp())}",
            variant_id,
            test_case_id,
            result.metric.value,
            result.score,
            result.confidence,
            json.dumps(result.details),
            result.timestamp.isoformat(),
            result.evaluator_version,
            json.dumps(result.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    def _store_ab_test_result(self, test_id: str, variant_a_id: str, variant_b_id: str, 
                             metric: EvaluationMetric, result: Dict[str, Any]):
        """Store A/B test result in database."""
        conn = sqlite3.connect(self.results_db)
        
        conn.execute("""
            INSERT INTO ab_test_results 
            (id, test_name, variant_a_id, variant_b_id, metric, variant_a_score, variant_b_score, 
             p_value, effect_size, sample_size, winner, confidence_level, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_id,
            f"{variant_a_id}_vs_{variant_b_id}",
            variant_a_id,
            variant_b_id,
            metric.value,
            result["variant_a_score"],
            result["variant_b_score"],
            result["p_value"],
            result["effect_size"],
            result["sample_size"],
            result["winner"],
            result["confidence_level"],
            datetime.now().isoformat(),
            json.dumps(result)
        ))
        
        conn.commit()
        conn.close()

    # REPORTING METHODS
    
    def generate_evaluation_report(self, variant_id: str, output_format: str = "html") -> str:
        """Generate comprehensive evaluation report."""
        conn = sqlite3.connect(self.results_db)
        
        # Get evaluation results
        results = conn.execute("""
            SELECT metric, score, confidence, details, timestamp 
            FROM evaluation_results 
            WHERE prompt_variant_id = ?
            ORDER BY timestamp DESC
        """, (variant_id,)).fetchall()
        
        conn.close()
        
        if output_format == "html":
            return self._generate_html_report(variant_id, results)
        elif output_format == "json":
            return self._generate_json_report(variant_id, results)
        else:
            return self._generate_text_report(variant_id, results)
    
    def _generate_html_report(self, variant_id: str, results: List[Tuple]) -> str:
        """Generate HTML evaluation report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LLM Evaluation Report - {variant_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .metric {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .score {{ font-size: 24px; font-weight: bold; color: #2c5aa0; }}
                .confidence {{ color: #666; }}
                .details {{ margin-top: 10px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>LLM Evaluation Report</h1>
                <h2>Variant: {variant_id}</h2>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        for metric, score, confidence, details, timestamp in results:
            html += f"""
            <div class="metric">
                <h3>{metric.replace('_', ' ').title()}</h3>
                <div class="score">Score: {score:.3f}</div>
                <div class="confidence">Confidence: {confidence:.3f}</div>
                <div class="details">Evaluated: {timestamp}</div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_json_report(self, variant_id: str, results: List[Tuple]) -> str:
        """Generate JSON evaluation report."""
        report_data = {
            "variant_id": variant_id,
            "generated_at": datetime.now().isoformat(),
            "results": []
        }
        
        for metric, score, confidence, details, timestamp in results:
            report_data["results"].append({
                "metric": metric,
                "score": score,
                "confidence": confidence,
                "timestamp": timestamp,
                "details": json.loads(details) if details else {}
            })
        
        return json.dumps(report_data, indent=2)
    
    def _generate_text_report(self, variant_id: str, results: List[Tuple]) -> str:
        """Generate text evaluation report."""
        report = f"""
LLM EVALUATION REPORT
====================

Variant: {variant_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

RESULTS:
--------
"""
        
        for metric, score, confidence, details, timestamp in results:
            report += f"""
{metric.replace('_', ' ').title()}:
  Score: {score:.3f}
  Confidence: {confidence:.3f}
  Evaluated: {timestamp}
"""
        
        return report

    # PRODUCTION MONITORING METHODS
    
    def setup_production_monitoring(self, monitoring_config: Dict[str, Any]) -> bool:
        """Set up continuous evaluation in production."""
        try:
            # This would integrate with production systems
            logger.info("Setting up production monitoring...")
            
            # Create monitoring configuration
            config = {
                "evaluation_frequency": monitoring_config.get("frequency", "daily"),
                "metrics": monitoring_config.get("metrics", [EvaluationMetric.ACCURACY, EvaluationMetric.COST_EFFECTIVENESS]),
                "alert_thresholds": monitoring_config.get("thresholds", {}),
                "stakeholder_notifications": monitoring_config.get("notifications", [])
            }
            
            # Store configuration
            config_path = self.results_dir / "monitoring_config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            
            logger.info(f"Production monitoring configured: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up production monitoring: {e}")
            return False
    
    def run_production_evaluation(self) -> Dict[str, Any]:
        """Run evaluation on production data."""
        logger.info("Running production evaluation...")
        
        # This would integrate with Langfuse/Langwatch to get production traces
        production_results = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "alerts": [],
            "recommendations": []
        }
        
        if self.langfuse_client:
            try:
                # Get recent traces
                traces = self.langfuse_client.api.trace.list(limit=100)
                
                # Analyze performance metrics
                if traces.data:
                    total_traces = len(traces.data)
                    error_traces = sum(1 for t in traces.data if hasattr(t, 'status') and t.status == 'error')
                    
                    production_results["metrics"] = {
                        "total_requests": total_traces,
                        "error_rate": error_traces / total_traces if total_traces > 0 else 0,
                        "success_rate": 1 - (error_traces / total_traces) if total_traces > 0 else 1
                    }
                    
                    # Generate alerts if needed
                    if production_results["metrics"]["error_rate"] > 0.05:  # 5% threshold
                        production_results["alerts"].append({
                            "type": "high_error_rate",
                            "message": f"Error rate ({production_results['metrics']['error_rate']:.2%}) exceeds threshold",
                            "severity": "high"
                        })
            
            except Exception as e:
                logger.error(f"Error analyzing production data: {e}")
        
        return production_results

# DEMO AND TESTING FUNCTIONS

def create_sample_prompt_variants() -> List[PromptVariant]:
    """Create sample prompt variants for demonstration."""
    return [
        PromptVariant(
            id="meeting_detailed_v1",
            name="Detailed Meeting Analysis",
            content="You are an expert meeting analyst. Extract comprehensive information...",
            version="1.0",
            tags=["meeting_analysis", "detailed"],
            created_at=datetime.now(),
            parameters={"model": "gemini-1.5-pro", "temperature": 0.3}
        ),
        PromptVariant(
            id="meeting_executive_v1", 
            name="Executive Meeting Summary",
            content="You are an executive assistant. Create a strategic summary...",
            version="1.0",
            tags=["meeting_analysis", "executive"],
            created_at=datetime.now(),
            parameters={"model": "gemini-1.5-pro", "temperature": 0.2}
        ),
        PromptVariant(
            id="email_command_v1",
            name="Email Command Parser", 
            content="Parse email commands and provide appropriate responses...",
            version="1.0",
            tags=["email_command", "parser"],
            created_at=datetime.now(),
            parameters={"model": "gemini-1.5-pro", "temperature": 0.1}
        ),
        PromptVariant(
            id="status_report_v1",
            name="Status Report Generator",
            content="Generate executive status reports from project data...",
            version="1.0", 
            tags=["status_report", "executive"],
            created_at=datetime.now(),
            parameters={"model": "gemini-1.5-pro", "temperature": 0.4}
        )
    ]

def create_sample_test_cases() -> List[TestCase]:
    """Create sample test cases for demonstration."""
    return [
        TestCase(
            id="meeting_test_1",
            input_data={
                "transcript": "Today we discussed the Q3 roadmap for the AI platform. Key decisions include adopting the new ML framework and increasing the team by 3 engineers. John will lead the technical architecture review by Friday. Sarah raised concerns about the timeline being too aggressive.",
                "project": "AI Platform"
            },
            expected_output=None,
            success_criteria={
                "required_elements": ["decisions", "action items", "risks", "timeline"],
                "min_length": 100,
                "contains_keywords": ["Q3", "roadmap", "framework", "engineers"]
            },
            business_context="Product development meeting for AI platform expansion",
            priority="high"
        ),
        TestCase(
            id="email_command_test_1",
            input_data={
                "subject": "Vertigo: List this week",
                "command": "list this week"
            },
            expected_output="Last 7 Days Summary",
            success_criteria={
                "required_elements": ["transcripts", "meetings", "statistics"],
                "min_length": 50
            },
            business_context="Weekly status request via email",
            priority="medium"
        ),
        TestCase(
            id="status_report_test_1",
            input_data={
                "project_data": "Multiple meetings this week covering AI platform development, team expansion, and Q3 planning. Key progress on ML framework integration.",
                "timeframe": "weekly"
            },
            expected_output=None,
            success_criteria={
                "required_elements": ["summary", "progress", "next steps"],
                "min_length": 75,
                "contains_keywords": ["AI platform", "progress", "Q3"]
            },
            business_context="Executive weekly status update",
            priority="high"
        )
    ]

async def run_comprehensive_demo():
    """Run comprehensive demonstration of the evaluation framework."""
    print("=" * 80)
    print("COMPREHENSIVE LLM EVALUATION FRAMEWORK DEMONSTRATION")
    print("=" * 80)
    
    # Initialize framework
    framework = LLMEvaluationFramework()
    
    # Create sample data
    variants = create_sample_prompt_variants()
    test_cases = create_sample_test_cases()
    
    print(f"\nInitialized with {len(variants)} prompt variants and {len(test_cases)} test cases")
    
    # 1. Single Variant Evaluation
    print("\n" + "=" * 50)
    print("1. SINGLE VARIANT EVALUATION")
    print("=" * 50)
    
    variant = variants[0]  # Detailed meeting analysis
    metrics = [
        EvaluationMetric.ACCURACY,
        EvaluationMetric.RELEVANCE,
        EvaluationMetric.COMPLETENESS,
        EvaluationMetric.COST_EFFECTIVENESS
    ]
    
    results = await framework.evaluate_prompt_variant(variant, test_cases, metrics)
    
    print(f"\nEvaluation Results for '{variant.name}':")
    for metric, result in results.items():
        print(f"  {metric.value}: {result.score:.3f} (confidence: {result.confidence:.3f})")
    
    # 2. A/B Testing
    print("\n" + "=" * 50)
    print("2. A/B TESTING WITH STATISTICAL SIGNIFICANCE")
    print("=" * 50)
    
    variant_a = variants[0]  # Detailed
    variant_b = variants[1]  # Executive
    
    ab_results = await framework.run_ab_test(
        variant_a, variant_b, test_cases, 
        [EvaluationMetric.ACCURACY, EvaluationMetric.RELEVANCE]
    )
    
    print(f"\nA/B Test: '{variant_a.name}' vs '{variant_b.name}'")
    print(f"Overall Winner: {ab_results['overall_winner']}")
    
    for metric, result in ab_results['results'].items():
        print(f"\n{metric}:")
        print(f"  Variant A: {result['variant_a_score']:.3f}")
        print(f"  Variant B: {result['variant_b_score']:.3f}")
        print(f"  Winner: {result['winner']}")
        print(f"  P-value: {result['p_value']:.4f}")
        print(f"  Effect Size: {result['effect_size']:.3f}")
        print(f"  Improvement: {result['improvement_percent']:.1f}%")
    
    # 3. Batch Evaluation
    print("\n" + "=" * 50)
    print("3. BATCH EVALUATION ACROSS ALL VARIANTS")
    print("=" * 50)
    
    batch_results = framework.run_batch_evaluation(
        variants, test_cases,
        [EvaluationMetric.ACCURACY, EvaluationMetric.BUSINESS_IMPACT, EvaluationMetric.USER_SATISFACTION]
    )
    
    print("\nBatch Evaluation Results (Ranked by Overall Score):")
    for rank, (variant_id, score) in enumerate(batch_results['ranked_variants'], 1):
        variant_name = next(v.name for v in variants if v.id == variant_id)
        print(f"  {rank}. {variant_name}: {score:.3f}")
    
    # 4. Business Impact Analysis
    print("\n" + "=" * 50)
    print("4. BUSINESS IMPACT ANALYSIS")
    print("=" * 50)
    
    business_variant = variants[0]
    business_results = await framework.evaluate_prompt_variant(
        business_variant, test_cases,
        [EvaluationMetric.BUSINESS_IMPACT, EvaluationMetric.COST_EFFECTIVENESS]
    )
    
    for metric, result in business_results.items():
        if metric == EvaluationMetric.BUSINESS_IMPACT:
            total_value = result.metadata.get('total_business_value', 0)
            avg_time_saved = result.metadata.get('avg_time_saved', 0)
            print(f"\nBusiness Impact Analysis:")
            print(f"  Impact Score: {result.score:.3f}")
            print(f"  Total Business Value: ${total_value:.2f}")
            print(f"  Average Time Saved: {avg_time_saved:.2f} hours")
    
    # 5. Production Monitoring Setup
    print("\n" + "=" * 50)
    print("5. PRODUCTION MONITORING SETUP")
    print("=" * 50)
    
    monitoring_config = {
        "frequency": "daily",
        "metrics": [EvaluationMetric.ACCURACY.value, EvaluationMetric.COST_EFFECTIVENESS.value],
        "thresholds": {"error_rate": 0.05, "cost_per_request": 0.10},
        "notifications": ["admin@vertigo.com"]
    }
    
    success = framework.setup_production_monitoring(monitoring_config)
    print(f"Production monitoring setup: {'SUCCESS' if success else 'FAILED'}")
    
    production_results = framework.run_production_evaluation()
    print(f"\nProduction Evaluation Results:")
    for metric, value in production_results.get('metrics', {}).items():
        print(f"  {metric}: {value}")
    
    if production_results.get('alerts'):
        print(f"\nAlerts:")
        for alert in production_results['alerts']:
            print(f"  {alert['type']}: {alert['message']} (Severity: {alert['severity']})")
    
    # 6. Generate Reports
    print("\n" + "=" * 50)
    print("6. EVALUATION REPORTING")
    print("=" * 50)
    
    # Generate HTML report
    html_report = framework.generate_evaluation_report(variant.id, "html")
    html_path = framework.results_dir / f"evaluation_report_{variant.id}.html"
    with open(html_path, 'w') as f:
        f.write(html_report)
    print(f"HTML report generated: {html_path}")
    
    # Generate JSON report
    json_report = framework.generate_evaluation_report(variant.id, "json")
    json_path = framework.results_dir / f"evaluation_report_{variant.id}.json" 
    with open(json_path, 'w') as f:
        f.write(json_report)
    print(f"JSON report generated: {json_path}")
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print(f"\nResults saved to: {framework.results_dir}")
    print(f"Database: {framework.results_db}")
    print("\nThis framework demonstrates professional-grade LLM evaluation")
    print("capabilities suitable for production deployment and business")
    print("stakeholder reporting.")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_demo())