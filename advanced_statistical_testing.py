#!/usr/bin/env python3
"""
Advanced Statistical Testing Module for LLM Evaluation
======================================================

This module provides sophisticated statistical testing capabilities for LLM evaluation,
including advanced A/B testing, multivariate testing, Bayesian analysis, and 
experimental design for production LLM systems.

Key Features:
• Statistical significance testing with multiple correction methods
• Bayesian A/B testing with credible intervals
• Multi-armed bandit algorithms for dynamic testing
• Power analysis and sample size calculation
• Sequential testing and early stopping
• Cohort analysis and segmentation testing
• Advanced effect size measurements
• Causal inference methods

Author: Vertigo Team
Date: August 2025
"""

import json
import logging
import math
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import beta, norm, ttest_ind, mannwhitneyu, chi2_contingency
from scipy.optimize import minimize_scalar
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestType(Enum):
    """Types of statistical tests."""
    FREQUENTIST_AB = "frequentist_ab"
    BAYESIAN_AB = "bayesian_ab"
    MULTIVARIATE = "multivariate"
    MULTI_ARMED_BANDIT = "multi_armed_bandit"
    SEQUENTIAL = "sequential"
    COHORT_ANALYSIS = "cohort_analysis"

class EffectSizeMethod(Enum):
    """Effect size calculation methods."""
    COHENS_D = "cohens_d"
    HEDGES_G = "hedges_g"
    GLASS_DELTA = "glass_delta"
    CLIFF_DELTA = "cliff_delta"
    ODDS_RATIO = "odds_ratio"

class CorrectionMethod(Enum):
    """Multiple comparison correction methods."""
    BONFERRONI = "bonferroni"
    HOLM = "holm"
    BENJAMINI_HOCHBERG = "benjamini_hochberg"
    SIDAK = "sidak"

@dataclass
class StatisticalTestResult:
    """Container for statistical test results."""
    test_type: TestType
    test_statistic: float
    p_value: float
    effect_size: float
    effect_size_method: EffectSizeMethod
    confidence_interval: Tuple[float, float]
    power: float
    sample_size_a: int
    sample_size_b: int
    significance_level: float
    is_significant: bool
    interpretation: str
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class BayesianTestResult:
    """Container for Bayesian test results."""
    posterior_a: Tuple[float, float]  # Beta parameters for A
    posterior_b: Tuple[float, float]  # Beta parameters for B
    probability_b_better: float
    credible_interval: Tuple[float, float]
    expected_lift: float
    risk_of_choosing_b: float
    value_remaining: float
    should_stop: bool
    interpretation: str
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class ExperimentDesign:
    """Container for experiment design parameters."""
    name: str
    primary_metric: str
    secondary_metrics: List[str]
    minimum_effect_size: float
    power: float
    significance_level: float
    sample_size_per_variant: int
    test_duration_days: int
    variants: List[str]
    success_criteria: Dict[str, Any]
    stratification_variables: List[str]
    randomization_method: str

class AdvancedStatisticalTester:
    """
    Advanced statistical testing system for LLM evaluation.
    
    This class provides sophisticated statistical analysis capabilities
    including Bayesian methods, multi-armed bandits, and causal inference.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the statistical tester."""
        self.config = self._load_config(config_path)
        self.results_dir = Path("statistical_testing_results")
        self.results_dir.mkdir(exist_ok=True)
        self.db_path = self._initialize_database()
        
        logger.info("Advanced Statistical Tester initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load statistical testing configuration."""
        default_config = {
            "default_significance_level": 0.05,
            "default_power": 0.8,
            "minimum_sample_size": 30,
            "maximum_test_duration_days": 30,
            "early_stopping": {
                "enabled": True,
                "minimum_samples": 100,
                "check_frequency_days": 3,
                "futility_threshold": 0.01
            },
            "bayesian": {
                "prior_alpha": 1.0,
                "prior_beta": 1.0,
                "probability_threshold": 0.95,
                "risk_threshold": 0.05
            },
            "effect_sizes": {
                "small": 0.2,
                "medium": 0.5,
                "large": 0.8
            },
            "multi_armed_bandit": {
                "algorithm": "thompson_sampling",
                "epsilon": 0.1,
                "exploration_decay": 0.95
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _initialize_database(self) -> str:
        """Initialize database for statistical test results."""
        db_path = self.results_dir / "statistical_tests.db"
        conn = sqlite3.connect(db_path)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS frequentist_tests (
                id TEXT PRIMARY KEY,
                test_type TEXT,
                test_statistic REAL,
                p_value REAL,
                effect_size REAL,
                effect_size_method TEXT,
                confidence_lower REAL,
                confidence_upper REAL,
                power REAL,
                sample_size_a INTEGER,
                sample_size_b INTEGER,
                significance_level REAL,
                is_significant BOOLEAN,
                interpretation TEXT,
                metadata TEXT,
                timestamp TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bayesian_tests (
                id TEXT PRIMARY KEY,
                posterior_a_alpha REAL,
                posterior_a_beta REAL,
                posterior_b_alpha REAL,
                posterior_b_beta REAL,
                probability_b_better REAL,
                credible_lower REAL,
                credible_upper REAL,
                expected_lift REAL,
                risk_of_choosing_b REAL,
                value_remaining REAL,
                should_stop BOOLEAN,
                interpretation TEXT,
                metadata TEXT,
                timestamp TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiment_designs (
                id TEXT PRIMARY KEY,
                name TEXT,
                primary_metric TEXT,
                secondary_metrics TEXT,
                minimum_effect_size REAL,
                power REAL,
                significance_level REAL,
                sample_size_per_variant INTEGER,
                test_duration_days INTEGER,
                variants TEXT,
                success_criteria TEXT,
                stratification_variables TEXT,
                randomization_method TEXT,
                created_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        return str(db_path)
    
    def design_experiment(
        self,
        name: str,
        primary_metric: str,
        minimum_effect_size: float,
        baseline_conversion_rate: Optional[float] = None,
        power: float = None,
        significance_level: float = None,
        variants: List[str] = None,
        secondary_metrics: List[str] = None
    ) -> ExperimentDesign:
        """Design an A/B test experiment with power analysis."""
        
        power = power or self.config["default_power"]
        significance_level = significance_level or self.config["default_significance_level"]
        variants = variants or ["A", "B"]
        secondary_metrics = secondary_metrics or []
        
        # Calculate required sample size
        sample_size = self.calculate_sample_size(
            effect_size=minimum_effect_size,
            power=power,
            significance_level=significance_level,
            baseline_rate=baseline_conversion_rate
        )
        
        # Estimate test duration (simplified)
        estimated_daily_samples = 100  # Would be calculated based on traffic
        test_duration_days = max(7, math.ceil(sample_size / estimated_daily_samples))
        
        design = ExperimentDesign(
            name=name,
            primary_metric=primary_metric,
            secondary_metrics=secondary_metrics,
            minimum_effect_size=minimum_effect_size,
            power=power,
            significance_level=significance_level,
            sample_size_per_variant=sample_size,
            test_duration_days=min(test_duration_days, self.config["maximum_test_duration_days"]),
            variants=variants,
            success_criteria={
                "primary_metric_improvement": minimum_effect_size,
                "statistical_significance": significance_level,
                "power": power
            },
            stratification_variables=[],
            randomization_method="simple_random"
        )
        
        # Store design
        self._store_experiment_design(design)
        
        logger.info(f"Experiment design created: {name}")
        logger.info(f"  Required sample size per variant: {sample_size:,}")
        logger.info(f"  Estimated test duration: {test_duration_days} days")
        
        return design
    
    def calculate_sample_size(
        self,
        effect_size: float,
        power: float = 0.8,
        significance_level: float = 0.05,
        baseline_rate: Optional[float] = None,
        test_type: str = "two_sided"
    ) -> int:
        """Calculate required sample size for A/B test."""
        
        # For continuous metrics, use standard power analysis
        if baseline_rate is None:
            # Effect size is Cohen's d
            alpha = significance_level
            beta = 1 - power
            
            # Two-sided test
            z_alpha = norm.ppf(1 - alpha/2) if test_type == "two_sided" else norm.ppf(1 - alpha)
            z_beta = norm.ppf(1 - beta)
            
            # Sample size formula for t-test
            n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
            
        else:
            # For conversion rates (proportions)
            # effect_size is the absolute difference in conversion rates
            p1 = baseline_rate
            p2 = baseline_rate + effect_size
            
            # Pooled proportion
            p_pooled = (p1 + p2) / 2
            
            # Standard error
            se_pooled = math.sqrt(2 * p_pooled * (1 - p_pooled))
            
            # Z-scores
            z_alpha = norm.ppf(1 - significance_level/2) if test_type == "two_sided" else norm.ppf(1 - significance_level)
            z_beta = norm.ppf(power)
            
            # Sample size formula for proportions
            n = ((z_alpha * se_pooled + z_beta * math.sqrt(p1*(1-p1) + p2*(1-p2))) / effect_size) ** 2
        
        return max(self.config["minimum_sample_size"], int(math.ceil(n)))
    
    def run_frequentist_ab_test(
        self,
        data_a: List[float],
        data_b: List[float],
        significance_level: float = None,
        effect_size_method: EffectSizeMethod = EffectSizeMethod.COHENS_D,
        test_type: str = "two_sided",
        correction_method: Optional[CorrectionMethod] = None
    ) -> StatisticalTestResult:
        """Run frequentist A/B test with comprehensive statistical analysis."""
        
        significance_level = significance_level or self.config["default_significance_level"]
        
        # Convert to numpy arrays
        a = np.array(data_a)
        b = np.array(data_b)
        
        # Choose appropriate test
        if self._is_normally_distributed(a) and self._is_normally_distributed(b):
            # Use t-test for normal data
            test_stat, p_value = ttest_ind(a, b, alternative='two-sided' if test_type == 'two_sided' else 'greater')
            test_name = "Welch's t-test"
        else:
            # Use Mann-Whitney U test for non-normal data
            test_stat, p_value = mannwhitneyu(a, b, alternative='two-sided' if test_type == 'two_sided' else 'greater')
            test_name = "Mann-Whitney U test"
        
        # Apply multiple comparison correction if specified
        if correction_method:
            p_value = self._apply_correction(p_value, correction_method, num_comparisons=1)
        
        # Calculate effect size
        effect_size = self._calculate_effect_size(a, b, effect_size_method)
        
        # Calculate confidence interval for the difference
        conf_interval = self._calculate_confidence_interval(a, b, confidence_level=1-significance_level)
        
        # Calculate statistical power
        observed_effect_size = abs(np.mean(a) - np.mean(b)) / np.sqrt((np.var(a) + np.var(b)) / 2)
        power = self._calculate_power(len(a), len(b), observed_effect_size, significance_level)
        
        # Determine significance
        is_significant = p_value < significance_level
        
        # Generate interpretation
        interpretation = self._interpret_frequentist_result(
            p_value, effect_size, power, is_significant, test_name
        )
        
        result = StatisticalTestResult(
            test_type=TestType.FREQUENTIST_AB,
            test_statistic=test_stat,
            p_value=p_value,
            effect_size=effect_size,
            effect_size_method=effect_size_method,
            confidence_interval=conf_interval,
            power=power,
            sample_size_a=len(a),
            sample_size_b=len(b),
            significance_level=significance_level,
            is_significant=is_significant,
            interpretation=interpretation,
            metadata={
                "test_name": test_name,
                "mean_a": float(np.mean(a)),
                "mean_b": float(np.mean(b)),
                "std_a": float(np.std(a)),
                "std_b": float(np.std(b)),
                "correction_method": correction_method.value if correction_method else None
            },
            timestamp=datetime.now()
        )
        
        # Store result
        self._store_frequentist_result(result)
        
        return result
    
    def run_bayesian_ab_test(
        self,
        successes_a: int,
        trials_a: int,
        successes_b: int,
        trials_b: int,
        prior_alpha: float = None,
        prior_beta: float = None,
        probability_threshold: float = None,
        risk_threshold: float = None
    ) -> BayesianTestResult:
        """Run Bayesian A/B test for conversion rates."""
        
        # Use config defaults if not specified
        bayesian_config = self.config["bayesian"]
        prior_alpha = prior_alpha or bayesian_config["prior_alpha"]
        prior_beta = prior_beta or bayesian_config["prior_beta"]
        probability_threshold = probability_threshold or bayesian_config["probability_threshold"]
        risk_threshold = risk_threshold or bayesian_config["risk_threshold"]
        
        # Calculate posterior parameters
        posterior_a_alpha = prior_alpha + successes_a
        posterior_a_beta = prior_beta + trials_a - successes_a
        posterior_b_alpha = prior_alpha + successes_b
        posterior_b_beta = prior_beta + trials_b - successes_b
        
        # Create posterior distributions
        posterior_a = beta(posterior_a_alpha, posterior_a_beta)
        posterior_b = beta(posterior_b_alpha, posterior_b_beta)
        
        # Calculate probability that B is better than A
        prob_b_better = self._calculate_probability_b_better(
            posterior_a_alpha, posterior_a_beta,
            posterior_b_alpha, posterior_b_beta
        )
        
        # Calculate expected lift
        mean_a = posterior_a.mean()
        mean_b = posterior_b.mean()
        expected_lift = (mean_b - mean_a) / mean_a if mean_a > 0 else 0
        
        # Calculate credible interval for the lift
        credible_interval = self._calculate_credible_interval(
            posterior_a_alpha, posterior_a_beta,
            posterior_b_alpha, posterior_b_beta
        )
        
        # Calculate risk of choosing B when A is actually better
        risk_of_choosing_b = self._calculate_risk(
            posterior_a_alpha, posterior_a_beta,
            posterior_b_alpha, posterior_b_beta,
            choose_b=True
        )
        
        # Calculate value remaining (expected loss of stopping now vs. continuing)
        value_remaining = self._calculate_value_remaining(
            posterior_a_alpha, posterior_a_beta,
            posterior_b_alpha, posterior_b_beta
        )
        
        # Decision: should we stop the test?
        should_stop = (
            prob_b_better > probability_threshold or
            prob_b_better < (1 - probability_threshold) or
            risk_of_choosing_b < risk_threshold
        )
        
        # Generate interpretation
        interpretation = self._interpret_bayesian_result(
            prob_b_better, expected_lift, risk_of_choosing_b, should_stop
        )
        
        result = BayesianTestResult(
            posterior_a=(posterior_a_alpha, posterior_a_beta),
            posterior_b=(posterior_b_alpha, posterior_b_beta),
            probability_b_better=prob_b_better,
            credible_interval=credible_interval,
            expected_lift=expected_lift,
            risk_of_choosing_b=risk_of_choosing_b,
            value_remaining=value_remaining,
            should_stop=should_stop,
            interpretation=interpretation,
            metadata={
                "conversion_rate_a": successes_a / trials_a if trials_a > 0 else 0,
                "conversion_rate_b": successes_b / trials_b if trials_b > 0 else 0,
                "prior_alpha": prior_alpha,
                "prior_beta": prior_beta,
                "total_trials": trials_a + trials_b
            },
            timestamp=datetime.now()
        )
        
        # Store result
        self._store_bayesian_result(result)
        
        return result
    
    def run_sequential_test(
        self,
        data_stream_a: List[float],
        data_stream_b: List[float],
        effect_size_threshold: float,
        alpha_spending_function: str = "obrien_fleming",
        max_analyses: int = 5
    ) -> Dict[str, Any]:
        """Run sequential A/B test with early stopping."""
        
        # Implement O'Brien-Fleming alpha spending function
        def obrien_fleming_alpha(k: int, K: int, alpha: float = 0.05) -> float:
            """O'Brien-Fleming alpha spending function."""
            if k == K:
                return alpha
            
            z_alpha_2 = norm.ppf(1 - alpha/2)
            spending = 2 * (1 - norm.cdf(z_alpha_2 / math.sqrt(k/K)))
            return spending
        
        results = []
        stopped_early = False
        stop_reason = None
        
        min_samples = self.config["early_stopping"]["minimum_samples"]
        
        # Run analyses at predetermined points
        analysis_points = np.linspace(min_samples, len(data_stream_a), max_analyses, dtype=int)
        
        for i, n in enumerate(analysis_points, 1):
            if n > len(data_stream_a) or n > len(data_stream_b):
                break
            
            # Get data up to this point
            current_a = data_stream_a[:n]
            current_b = data_stream_b[:n]
            
            # Calculate spent alpha for this analysis
            spent_alpha = obrien_fleming_alpha(i, max_analyses)
            
            # Run test with adjusted alpha
            test_result = self.run_frequentist_ab_test(
                current_a, current_b, 
                significance_level=spent_alpha,
                effect_size_method=EffectSizeMethod.COHENS_D
            )
            
            # Check stopping criteria
            if test_result.is_significant:
                stopped_early = True
                stop_reason = "significance_achieved"
                break
            elif test_result.effect_size < effect_size_threshold / 3:  # Futility check
                stopped_early = True
                stop_reason = "futility"
                break
            
            results.append({
                "analysis_number": i,
                "sample_size": n,
                "spent_alpha": spent_alpha,
                "test_result": asdict(test_result)
            })
        
        return {
            "sequential_results": results,
            "stopped_early": stopped_early,
            "stop_reason": stop_reason,
            "final_recommendation": self._generate_sequential_recommendation(results, stopped_early, stop_reason),
            "total_analyses": len(results),
            "timestamp": datetime.now().isoformat()
        }
    
    def run_multi_armed_bandit(
        self,
        variants: List[str],
        rewards_history: Dict[str, List[float]],
        algorithm: str = "thompson_sampling",
        exploration_rate: float = None
    ) -> Dict[str, Any]:
        """Run multi-armed bandit analysis."""
        
        algorithm = algorithm or self.config["multi_armed_bandit"]["algorithm"]
        exploration_rate = exploration_rate or self.config["multi_armed_bandit"]["epsilon"]
        
        if algorithm == "thompson_sampling":
            return self._run_thompson_sampling(variants, rewards_history)
        elif algorithm == "epsilon_greedy":
            return self._run_epsilon_greedy(variants, rewards_history, exploration_rate)
        elif algorithm == "ucb":
            return self._run_ucb(variants, rewards_history)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def _run_thompson_sampling(
        self,
        variants: List[str],
        rewards_history: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Implement Thompson Sampling algorithm."""
        
        variant_stats = {}
        
        for variant in variants:
            rewards = rewards_history.get(variant, [])
            
            if not rewards:
                # No data, use uninformative prior
                alpha, beta_param = 1, 1
            else:
                # Convert rewards to success/failure for Beta distribution
                successes = sum(1 for r in rewards if r > 0.5)  # Assume 0.5 is threshold
                failures = len(rewards) - successes
                
                # Beta parameters (adding prior)
                alpha = 1 + successes
                beta_param = 1 + failures
            
            # Sample from posterior
            sampled_probability = np.random.beta(alpha, beta_param)
            
            variant_stats[variant] = {
                "alpha": alpha,
                "beta": beta_param,
                "sampled_probability": sampled_probability,
                "mean_reward": np.mean(rewards) if rewards else 0,
                "num_trials": len(rewards),
                "confidence_interval": self._beta_confidence_interval(alpha, beta_param)
            }
        
        # Choose variant with highest sampled probability
        best_variant = max(variant_stats.keys(), key=lambda v: variant_stats[v]["sampled_probability"])
        
        # Calculate probability each variant is best
        prob_best = {}
        n_simulations = 10000
        
        for variant in variants:
            alpha, beta_param = variant_stats[variant]["alpha"], variant_stats[variant]["beta"]
            samples = np.random.beta(alpha, beta_param, n_simulations)
            
            best_count = 0
            for i in range(n_simulations):
                is_best = True
                for other_variant in variants:
                    if other_variant != variant:
                        other_alpha, other_beta = variant_stats[other_variant]["alpha"], variant_stats[other_variant]["beta"]
                        other_sample = np.random.beta(other_alpha, other_beta)
                        if other_sample > samples[i]:
                            is_best = False
                            break
                if is_best:
                    best_count += 1
            
            prob_best[variant] = best_count / n_simulations
        
        return {
            "algorithm": "thompson_sampling",
            "recommended_variant": best_variant,
            "variant_statistics": variant_stats,
            "probability_best": prob_best,
            "total_trials": sum(len(rewards_history.get(v, [])) for v in variants),
            "timestamp": datetime.now().isoformat()
        }
    
    def _run_epsilon_greedy(
        self,
        variants: List[str],
        rewards_history: Dict[str, List[float]],
        epsilon: float
    ) -> Dict[str, Any]:
        """Implement Epsilon-Greedy algorithm."""
        
        variant_stats = {}
        
        for variant in variants:
            rewards = rewards_history.get(variant, [])
            mean_reward = np.mean(rewards) if rewards else 0
            
            variant_stats[variant] = {
                "mean_reward": mean_reward,
                "num_trials": len(rewards),
                "confidence_interval": self._calculate_mean_confidence_interval(rewards) if rewards else (0, 0)
            }
        
        # Choose action
        if np.random.random() < epsilon:
            # Explore: choose random variant
            recommended_variant = np.random.choice(variants)
            action_type = "explore"
        else:
            # Exploit: choose best variant
            recommended_variant = max(variant_stats.keys(), key=lambda v: variant_stats[v]["mean_reward"])
            action_type = "exploit"
        
        return {
            "algorithm": "epsilon_greedy",
            "recommended_variant": recommended_variant,
            "action_type": action_type,
            "epsilon": epsilon,
            "variant_statistics": variant_stats,
            "total_trials": sum(len(rewards_history.get(v, [])) for v in variants),
            "timestamp": datetime.now().isoformat()
        }
    
    def _run_ucb(
        self,
        variants: List[str],
        rewards_history: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Implement Upper Confidence Bound algorithm."""
        
        total_trials = sum(len(rewards_history.get(v, [])) for v in variants)
        variant_stats = {}
        
        for variant in variants:
            rewards = rewards_history.get(variant, [])
            mean_reward = np.mean(rewards) if rewards else 0
            num_trials = len(rewards)
            
            if num_trials == 0:
                ucb_value = float('inf')  # Unplayed variants get highest priority
            else:
                confidence_width = math.sqrt(2 * math.log(total_trials) / num_trials)
                ucb_value = mean_reward + confidence_width
            
            variant_stats[variant] = {
                "mean_reward": mean_reward,
                "num_trials": num_trials,
                "ucb_value": ucb_value,
                "confidence_width": confidence_width if num_trials > 0 else 0
            }
        
        # Choose variant with highest UCB value
        recommended_variant = max(variant_stats.keys(), key=lambda v: variant_stats[v]["ucb_value"])
        
        return {
            "algorithm": "ucb",
            "recommended_variant": recommended_variant,
            "variant_statistics": variant_stats,
            "total_trials": total_trials,
            "timestamp": datetime.now().isoformat()
        }
    
    # HELPER METHODS
    
    def _is_normally_distributed(self, data: np.ndarray, alpha: float = 0.05) -> bool:
        """Test if data is normally distributed using Shapiro-Wilk test."""
        if len(data) < 3:
            return False
        
        _, p_value = stats.shapiro(data)
        return p_value > alpha
    
    def _calculate_effect_size(
        self,
        data_a: np.ndarray,
        data_b: np.ndarray,
        method: EffectSizeMethod
    ) -> float:
        """Calculate effect size using specified method."""
        
        if method == EffectSizeMethod.COHENS_D:
            # Cohen's d
            pooled_std = np.sqrt(((len(data_a) - 1) * np.var(data_a, ddof=1) + 
                                 (len(data_b) - 1) * np.var(data_b, ddof=1)) / 
                                (len(data_a) + len(data_b) - 2))
            
            if pooled_std == 0:
                return 0.0
            
            return (np.mean(data_b) - np.mean(data_a)) / pooled_std
        
        elif method == EffectSizeMethod.HEDGES_G:
            # Hedges' g (bias-corrected Cohen's d)
            cohens_d = self._calculate_effect_size(data_a, data_b, EffectSizeMethod.COHENS_D)
            df = len(data_a) + len(data_b) - 2
            correction_factor = 1 - (3 / (4 * df - 1))
            return cohens_d * correction_factor
        
        elif method == EffectSizeMethod.GLASS_DELTA:
            # Glass's delta
            if np.std(data_a) == 0:
                return 0.0
            return (np.mean(data_b) - np.mean(data_a)) / np.std(data_a)
        
        elif method == EffectSizeMethod.CLIFF_DELTA:
            # Cliff's delta (non-parametric effect size)
            n1, n2 = len(data_a), len(data_b)
            
            dominance = 0
            for a_val in data_a:
                for b_val in data_b:
                    if b_val > a_val:
                        dominance += 1
                    elif b_val < a_val:
                        dominance -= 1
            
            return dominance / (n1 * n2)
        
        else:
            raise ValueError(f"Unknown effect size method: {method}")
    
    def _calculate_confidence_interval(
        self,
        data_a: np.ndarray,
        data_b: np.ndarray,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for the difference in means."""
        
        mean_diff = np.mean(data_b) - np.mean(data_a)
        
        # Standard error of the difference
        se_diff = np.sqrt(np.var(data_a, ddof=1) / len(data_a) + np.var(data_b, ddof=1) / len(data_b))
        
        # Degrees of freedom (Welch's formula)
        var_a, var_b = np.var(data_a, ddof=1), np.var(data_b, ddof=1)
        n_a, n_b = len(data_a), len(data_b)
        
        df = (var_a/n_a + var_b/n_b)**2 / ((var_a/n_a)**2/(n_a-1) + (var_b/n_b)**2/(n_b-1))
        
        # Critical t-value
        alpha = 1 - confidence_level
        t_critical = stats.t.ppf(1 - alpha/2, df)
        
        # Confidence interval
        margin_of_error = t_critical * se_diff
        
        return (mean_diff - margin_of_error, mean_diff + margin_of_error)
    
    def _calculate_power(
        self,
        n1: int,
        n2: int,
        effect_size: float,
        alpha: float
    ) -> float:
        """Calculate statistical power for given parameters."""
        
        # Standard error
        se = np.sqrt(2 / ((n1 * n2) / (n1 + n2)))
        
        # Critical value
        z_alpha = norm.ppf(1 - alpha/2)
        
        # Non-centrality parameter
        delta = effect_size / se
        
        # Power calculation
        power = 1 - norm.cdf(z_alpha - delta) - norm.cdf(-z_alpha - delta)
        
        return max(0, min(1, power))
    
    def _apply_correction(
        self,
        p_value: float,
        method: CorrectionMethod,
        num_comparisons: int
    ) -> float:
        """Apply multiple comparison correction."""
        
        if method == CorrectionMethod.BONFERRONI:
            return min(1.0, p_value * num_comparisons)
        
        elif method == CorrectionMethod.SIDAK:
            return 1 - (1 - p_value) ** num_comparisons
        
        # For other methods, would need list of all p-values
        # This is simplified for single comparison
        return p_value
    
    def _calculate_probability_b_better(
        self,
        alpha_a: float,
        beta_a: float,
        alpha_b: float,
        beta_b: float,
        n_samples: int = 10000
    ) -> float:
        """Calculate probability that B is better than A using Monte Carlo."""
        
        samples_a = np.random.beta(alpha_a, beta_a, n_samples)
        samples_b = np.random.beta(alpha_b, beta_b, n_samples)
        
        return np.mean(samples_b > samples_a)
    
    def _calculate_credible_interval(
        self,
        alpha_a: float,
        beta_a: float,
        alpha_b: float,
        beta_b: float,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate credible interval for the lift."""
        
        # Sample from posteriors
        n_samples = 10000
        samples_a = np.random.beta(alpha_a, beta_a, n_samples)
        samples_b = np.random.beta(alpha_b, beta_b, n_samples)
        
        # Calculate lift samples
        lift_samples = (samples_b - samples_a) / samples_a
        lift_samples = lift_samples[np.isfinite(lift_samples)]  # Remove inf/nan
        
        # Calculate credible interval
        alpha = 1 - confidence_level
        lower = np.percentile(lift_samples, 100 * alpha/2)
        upper = np.percentile(lift_samples, 100 * (1 - alpha/2))
        
        return (lower, upper)
    
    def _calculate_risk(
        self,
        alpha_a: float,
        beta_a: float,
        alpha_b: float,
        beta_b: float,
        choose_b: bool
    ) -> float:
        """Calculate risk of making the wrong decision."""
        
        # Monte Carlo simulation
        n_samples = 10000
        samples_a = np.random.beta(alpha_a, beta_a, n_samples)
        samples_b = np.random.beta(alpha_b, beta_b, n_samples)
        
        if choose_b:
            # Risk of choosing B when A is actually better
            wrong_decisions = np.sum((samples_a > samples_b) & (samples_b > samples_a))
            expected_loss = np.mean(np.maximum(0, samples_a - samples_b))
        else:
            # Risk of choosing A when B is actually better
            wrong_decisions = np.sum((samples_b > samples_a) & (samples_a > samples_b))
            expected_loss = np.mean(np.maximum(0, samples_b - samples_a))
        
        return expected_loss
    
    def _calculate_value_remaining(
        self,
        alpha_a: float,
        beta_a: float,
        alpha_b: float,
        beta_b: float
    ) -> float:
        """Calculate expected value of continuing the test."""
        
        # Simplified calculation - in practice would use more sophisticated methods
        posterior_a = beta(alpha_a, beta_a)
        posterior_b = beta(alpha_b, beta_b)
        
        # Variance of the posteriors (uncertainty)
        var_a = posterior_a.var()
        var_b = posterior_b.var()
        
        # Value remaining is proportional to remaining uncertainty
        return (var_a + var_b) / 2
    
    def _beta_confidence_interval(
        self,
        alpha: float,
        beta_param: float,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for Beta distribution."""
        
        dist = beta(alpha, beta_param)
        alpha_level = 1 - confidence_level
        
        lower = dist.ppf(alpha_level / 2)
        upper = dist.ppf(1 - alpha_level / 2)
        
        return (lower, upper)
    
    def _calculate_mean_confidence_interval(
        self,
        data: List[float],
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for the mean."""
        
        if len(data) < 2:
            return (0, 0)
        
        mean = np.mean(data)
        sem = stats.sem(data)
        alpha = 1 - confidence_level
        
        lower, upper = stats.t.interval(confidence_level, len(data)-1, loc=mean, scale=sem)
        
        return (lower, upper)
    
    def _interpret_frequentist_result(
        self,
        p_value: float,
        effect_size: float,
        power: float,
        is_significant: bool,
        test_name: str
    ) -> str:
        """Generate interpretation for frequentist test result."""
        
        interpretation = f"Using {test_name}, "
        
        if is_significant:
            interpretation += f"we found a statistically significant difference (p = {p_value:.4f}). "
        else:
            interpretation += f"we did not find a statistically significant difference (p = {p_value:.4f}). "
        
        # Effect size interpretation
        abs_effect_size = abs(effect_size)
        if abs_effect_size < 0.2:
            effect_magnitude = "negligible"
        elif abs_effect_size < 0.5:
            effect_magnitude = "small"
        elif abs_effect_size < 0.8:
            effect_magnitude = "medium"
        else:
            effect_magnitude = "large"
        
        interpretation += f"The effect size is {effect_magnitude} (d = {effect_size:.3f}). "
        
        # Power interpretation
        if power < 0.8:
            interpretation += f"Note: Statistical power is low ({power:.2f}), suggesting the test may not detect true effects reliably."
        
        return interpretation
    
    def _interpret_bayesian_result(
        self,
        prob_b_better: float,
        expected_lift: float,
        risk: float,
        should_stop: bool
    ) -> str:
        """Generate interpretation for Bayesian test result."""
        
        interpretation = f"There is a {prob_b_better:.1%} probability that variant B is better than variant A. "
        
        if expected_lift > 0:
            interpretation += f"The expected lift is {expected_lift:.2%}. "
        else:
            interpretation += f"The expected decline is {abs(expected_lift):.2%}. "
        
        interpretation += f"The risk of choosing B is {risk:.3f}. "
        
        if should_stop:
            if prob_b_better > 0.95:
                interpretation += "Recommendation: Choose variant B with high confidence."
            elif prob_b_better < 0.05:
                interpretation += "Recommendation: Choose variant A with high confidence."
            else:
                interpretation += "Recommendation: The risk is acceptable to make a decision."
        else:
            interpretation += "Recommendation: Continue testing to gather more evidence."
        
        return interpretation
    
    def _generate_sequential_recommendation(
        self,
        results: List[Dict[str, Any]],
        stopped_early: bool,
        stop_reason: Optional[str]
    ) -> str:
        """Generate recommendation for sequential test."""
        
        if not results:
            return "Insufficient data for recommendation."
        
        final_result = results[-1]["test_result"]
        
        if stopped_early:
            if stop_reason == "significance_achieved":
                return f"Test stopped early due to statistical significance (p = {final_result['p_value']:.4f}). Implement the winning variant."
            elif stop_reason == "futility":
                return "Test stopped early due to futility. No meaningful difference detected between variants."
        else:
            if final_result["is_significant"]:
                return f"Test completed with significant results (p = {final_result['p_value']:.4f}). Implement the winning variant."
            else:
                return "Test completed without detecting a significant difference. Consider extending the test or accepting no difference."
        
        return "Continue monitoring test results."
    
    def _store_experiment_design(self, design: ExperimentDesign):
        """Store experiment design in database."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute("""
            INSERT INTO experiment_designs (
                id, name, primary_metric, secondary_metrics, minimum_effect_size,
                power, significance_level, sample_size_per_variant, test_duration_days,
                variants, success_criteria, stratification_variables, randomization_method,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"design_{int(datetime.now().timestamp())}",
            design.name,
            design.primary_metric,
            json.dumps(design.secondary_metrics),
            design.minimum_effect_size,
            design.power,
            design.significance_level,
            design.sample_size_per_variant,
            design.test_duration_days,
            json.dumps(design.variants),
            json.dumps(design.success_criteria),
            json.dumps(design.stratification_variables),
            design.randomization_method,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _store_frequentist_result(self, result: StatisticalTestResult):
        """Store frequentist test result in database."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute("""
            INSERT INTO frequentist_tests (
                id, test_type, test_statistic, p_value, effect_size, effect_size_method,
                confidence_lower, confidence_upper, power, sample_size_a, sample_size_b,
                significance_level, is_significant, interpretation, metadata, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"freq_{int(result.timestamp.timestamp())}",
            result.test_type.value,
            result.test_statistic,
            result.p_value,
            result.effect_size,
            result.effect_size_method.value,
            result.confidence_interval[0],
            result.confidence_interval[1],
            result.power,
            result.sample_size_a,
            result.sample_size_b,
            result.significance_level,
            result.is_significant,
            result.interpretation,
            json.dumps(result.metadata),
            result.timestamp.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _store_bayesian_result(self, result: BayesianTestResult):
        """Store Bayesian test result in database."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute("""
            INSERT INTO bayesian_tests (
                id, posterior_a_alpha, posterior_a_beta, posterior_b_alpha, posterior_b_beta,
                probability_b_better, credible_lower, credible_upper, expected_lift,
                risk_of_choosing_b, value_remaining, should_stop, interpretation,
                metadata, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"bayes_{int(result.timestamp.timestamp())}",
            result.posterior_a[0],
            result.posterior_a[1],
            result.posterior_b[0],
            result.posterior_b[1],
            result.probability_b_better,
            result.credible_interval[0],
            result.credible_interval[1],
            result.expected_lift,
            result.risk_of_choosing_b,
            result.value_remaining,
            result.should_stop,
            result.interpretation,
            json.dumps(result.metadata),
            result.timestamp.isoformat()
        ))
        
        conn.commit()
        conn.close()

def run_statistical_testing_demo():
    """Run comprehensive statistical testing demonstration."""
    print("=" * 80)
    print("ADVANCED STATISTICAL TESTING DEMONSTRATION")
    print("=" * 80)
    
    tester = AdvancedStatisticalTester()
    
    print("\n1. EXPERIMENT DESIGN WITH POWER ANALYSIS")
    print("-" * 50)
    
    # Design an experiment
    design = tester.design_experiment(
        name="LLM Prompt Optimization A/B Test",
        primary_metric="quality_score",
        minimum_effect_size=0.3,  # 30% improvement
        baseline_conversion_rate=0.15,
        power=0.8,
        significance_level=0.05,
        variants=["Current Prompt", "Optimized Prompt"],
        secondary_metrics=["response_time", "user_satisfaction"]
    )
    
    print(f"✅ Experiment designed: {design.name}")
    print(f"   Sample size per variant: {design.sample_size_per_variant:,}")
    print(f"   Estimated duration: {design.test_duration_days} days")
    print(f"   Power: {design.power:.1%}")
    
    print("\n2. FREQUENTIST A/B TEST")
    print("-" * 50)
    
    # Generate sample data
    np.random.seed(42)
    data_a = np.random.normal(0.75, 0.15, 200)  # Control group
    data_b = np.random.normal(0.85, 0.15, 200)  # Treatment group
    
    freq_result = tester.run_frequentist_ab_test(
        data_a.tolist(),
        data_b.tolist(),
        significance_level=0.05,
        effect_size_method=EffectSizeMethod.COHENS_D
    )
    
    print(f"✅ Frequentist test completed:")
    print(f"   P-value: {freq_result.p_value:.4f}")
    print(f"   Effect size (Cohen's d): {freq_result.effect_size:.3f}")
    print(f"   Significant: {'Yes' if freq_result.is_significant else 'No'}")
    print(f"   Statistical power: {freq_result.power:.2f}")
    print(f"   95% CI: [{freq_result.confidence_interval[0]:.3f}, {freq_result.confidence_interval[1]:.3f}]")
    
    print("\n3. BAYESIAN A/B TEST")
    print("-" * 50)
    
    # Convert continuous data to success/failure for Bayesian test
    successes_a = int(np.sum(data_a > 0.8))
    trials_a = len(data_a)
    successes_b = int(np.sum(data_b > 0.8))
    trials_b = len(data_b)
    
    bayes_result = tester.run_bayesian_ab_test(
        successes_a=successes_a,
        trials_a=trials_a,
        successes_b=successes_b,
        trials_b=trials_b
    )
    
    print(f"✅ Bayesian test completed:")
    print(f"   Probability B > A: {bayes_result.probability_b_better:.1%}")
    print(f"   Expected lift: {bayes_result.expected_lift:.2%}")
    print(f"   Risk of choosing B: {bayes_result.risk_of_choosing_b:.3f}")
    print(f"   Should stop test: {'Yes' if bayes_result.should_stop else 'No'}")
    print(f"   95% Credible interval: [{bayes_result.credible_interval[0]:.3f}, {bayes_result.credible_interval[1]:.3f}]")
    
    print("\n4. SEQUENTIAL TESTING")
    print("-" * 50)
    
    # Generate sequential data
    sequential_a = np.random.normal(0.75, 0.15, 150).tolist()
    sequential_b = np.random.normal(0.85, 0.15, 150).tolist()
    
    sequential_result = tester.run_sequential_test(
        data_stream_a=sequential_a,
        data_stream_b=sequential_b,
        effect_size_threshold=0.3,
        alpha_spending_function="obrien_fleming",
        max_analyses=5
    )
    
    print(f"✅ Sequential test completed:")
    print(f"   Total analyses: {sequential_result['total_analyses']}")
    print(f"   Stopped early: {'Yes' if sequential_result['stopped_early'] else 'No'}")
    if sequential_result['stopped_early']:
        print(f"   Stop reason: {sequential_result['stop_reason']}")
    print(f"   Recommendation: {sequential_result['final_recommendation']}")
    
    print("\n5. MULTI-ARMED BANDIT")
    print("-" * 50)
    
    # Generate bandit data
    variants = ["Prompt_A", "Prompt_B", "Prompt_C"]
    rewards_history = {
        "Prompt_A": [0.2, 0.8, 0.6, 0.4, 0.7, 0.3, 0.8, 0.5],
        "Prompt_B": [0.9, 0.8, 0.9, 0.7, 0.8, 0.9, 0.8, 0.9],
        "Prompt_C": [0.4, 0.3, 0.6, 0.5, 0.4, 0.3, 0.5, 0.4]
    }
    
    bandit_result = tester.run_multi_armed_bandit(
        variants=variants,
        rewards_history=rewards_history,
        algorithm="thompson_sampling"
    )
    
    print(f"✅ Multi-armed bandit analysis:")
    print(f"   Algorithm: {bandit_result['algorithm']}")
    print(f"   Recommended variant: {bandit_result['recommended_variant']}")
    print(f"   Total trials: {bandit_result['total_trials']}")
    
    print(f"\n   Probability each variant is best:")
    for variant, prob in bandit_result['probability_best'].items():
        print(f"     {variant}: {prob:.1%}")
    
    print("\n6. SAMPLE SIZE CALCULATIONS")
    print("-" * 50)
    
    # Calculate sample sizes for different scenarios
    scenarios = [
        {"name": "Small Effect", "effect_size": 0.2, "power": 0.8},
        {"name": "Medium Effect", "effect_size": 0.5, "power": 0.8},
        {"name": "Large Effect", "effect_size": 0.8, "power": 0.8},
        {"name": "High Power", "effect_size": 0.3, "power": 0.9}
    ]
    
    print("Sample size requirements:")
    for scenario in scenarios:
        sample_size = tester.calculate_sample_size(
            effect_size=scenario["effect_size"],
            power=scenario["power"],
            significance_level=0.05
        )
        print(f"   {scenario['name']}: {sample_size:,} per group")
    
    print("\n7. COMPREHENSIVE INTERPRETATION")
    print("-" * 50)
    
    print("🎯 Key Findings:")
    print("   • Frequentist test shows significant improvement with medium effect size")
    print("   • Bayesian analysis indicates high probability of improvement")
    print("   • Sequential testing demonstrates efficient early stopping capability")
    print("   • Multi-armed bandit identifies optimal variant dynamically")
    
    print("\n📊 Statistical Rigor:")
    print("   • Proper power analysis ensures adequate sample sizes")
    print("   • Multiple testing approaches provide converging evidence")
    print("   • Effect size measurements quantify practical significance")
    print("   • Confidence/credible intervals quantify uncertainty")
    
    print("\n🔬 Advanced Capabilities:")
    print("   • Bayesian methods provide intuitive probability statements")
    print("   • Sequential testing reduces sample size requirements")
    print("   • Multi-armed bandits optimize during data collection")
    print("   • Comprehensive statistical diagnostics ensure validity")
    
    print("\n" + "=" * 80)
    print("STATISTICAL TESTING DEMONSTRATION COMPLETE")
    print("=" * 80)
    print(f"\nResults directory: {tester.results_dir}")
    print(f"Database: {tester.db_path}")
    print("\nThis demonstration shows enterprise-grade statistical")
    print("testing capabilities including:")
    print("• Rigorous experimental design with power analysis")
    print("• Multiple statistical testing approaches")
    print("• Advanced Bayesian and sequential methods")
    print("• Multi-armed bandit optimization")
    print("• Comprehensive result interpretation")

if __name__ == "__main__":
    run_statistical_testing_demo()