#!/usr/bin/env python3
"""
Business Impact and ROI Evaluation System for Vertigo
=====================================================

This module provides comprehensive business impact measurement and ROI calculation
capabilities for LLM implementations. It connects technical performance metrics
to measurable business outcomes and financial returns.

Key Features:
• Financial ROI calculation with cost-benefit analysis
• Productivity impact measurement
• User satisfaction correlation with business metrics
• Time-to-value assessment
• Risk reduction quantification
• Competitive advantage analysis

Author: Vertigo Team
Date: August 2025
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BusinessMetric(Enum):
    """Business metrics for ROI calculation."""
    TIME_SAVINGS = "time_savings"
    ERROR_REDUCTION = "error_reduction"
    PRODUCTIVITY_GAIN = "productivity_gain"
    COST_REDUCTION = "cost_reduction"
    REVENUE_INCREASE = "revenue_increase"
    USER_SATISFACTION = "user_satisfaction"
    COMPETITIVE_ADVANTAGE = "competitive_advantage"
    RISK_MITIGATION = "risk_mitigation"

class ImpactCategory(Enum):
    """Categories of business impact."""
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    COST_OPTIMIZATION = "cost_optimization"
    REVENUE_GENERATION = "revenue_generation"
    RISK_MANAGEMENT = "risk_management"
    STRATEGIC_ADVANTAGE = "strategic_advantage"

@dataclass
class BusinessImpactResult:
    """Container for business impact evaluation results."""
    metric: BusinessMetric
    current_value: float
    baseline_value: float
    improvement: float
    improvement_percent: float
    financial_impact_usd: float
    confidence_level: float
    measurement_period_days: int
    data_sources: List[str]
    assumptions: List[str]
    timestamp: datetime

@dataclass
class ROICalculation:
    """Container for ROI calculation results."""
    total_investment_usd: float
    total_benefits_usd: float
    net_benefit_usd: float
    roi_percent: float
    payback_period_months: float
    npv_usd: float  # Net Present Value
    irr_percent: float  # Internal Rate of Return
    break_even_months: float
    confidence_interval: Tuple[float, float]
    risk_assessment: str

class BusinessImpactEvaluator:
    """
    Comprehensive business impact and ROI evaluator for LLM implementations.
    
    This class provides sophisticated business impact measurement capabilities
    that connect technical LLM performance to measurable business outcomes.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the business impact evaluator."""
        self.config = self._load_business_config(config_path)
        self.results_dir = Path("business_impact_results")
        self.results_dir.mkdir(exist_ok=True)
        self.db_path = self._initialize_database()
        
        logger.info("Business Impact Evaluator initialized")
    
    def _load_business_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load business evaluation configuration."""
        default_config = {
            "financial_assumptions": {
                "employee_hourly_rate_usd": 75.0,
                "contractor_hourly_rate_usd": 100.0,
                "executive_hourly_rate_usd": 150.0,
                "error_cost_per_incident_usd": 500.0,
                "downtime_cost_per_hour_usd": 2000.0,
                "training_cost_per_employee_usd": 1500.0,
                "annual_discount_rate": 0.08  # 8% discount rate for NPV
            },
            "business_metrics": {
                "target_productivity_increase": 25.0,  # %
                "target_error_reduction": 40.0,       # %
                "target_time_savings": 30.0,          # %
                "target_user_satisfaction": 4.0,      # out of 5
                "target_roi": 300.0                   # %
            },
            "measurement_periods": {
                "baseline_period_days": 90,
                "evaluation_period_days": 90,
                "projection_period_months": 12
            },
            "industry_benchmarks": {
                "typical_llm_roi": 250.0,             # %
                "industry_error_rate": 5.0,           # %
                "typical_processing_time_minutes": 15.0,
                "industry_satisfaction_score": 3.2    # out of 5
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _initialize_database(self) -> str:
        """Initialize database for business impact tracking."""
        db_path = self.results_dir / "business_impact.db"
        conn = sqlite3.connect(db_path)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS business_impact (
                id TEXT PRIMARY KEY,
                metric TEXT,
                current_value REAL,
                baseline_value REAL,
                improvement REAL,
                improvement_percent REAL,
                financial_impact_usd REAL,
                confidence_level REAL,
                measurement_period_days INTEGER,
                data_sources TEXT,
                assumptions TEXT,
                timestamp TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS roi_calculations (
                id TEXT PRIMARY KEY,
                total_investment_usd REAL,
                total_benefits_usd REAL,
                net_benefit_usd REAL,
                roi_percent REAL,
                payback_period_months REAL,
                npv_usd REAL,
                irr_percent REAL,
                break_even_months REAL,
                confidence_lower REAL,
                confidence_upper REAL,
                risk_assessment TEXT,
                calculation_date TEXT,
                projection_period_months INTEGER
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS productivity_tracking (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                task_type TEXT,
                time_before_minutes REAL,
                time_after_minutes REAL,
                quality_before REAL,
                quality_after REAL,
                error_count_before INTEGER,
                error_count_after INTEGER,
                satisfaction_score REAL,
                date_recorded TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        return str(db_path)
    
    def calculate_time_savings_impact(
        self,
        baseline_time_minutes: float,
        current_time_minutes: float,
        users_affected: int,
        usage_frequency_per_day: float,
        measurement_period_days: int = 90
    ) -> BusinessImpactResult:
        """Calculate business impact of time savings."""
        
        time_saved_per_task = baseline_time_minutes - current_time_minutes
        improvement_percent = (time_saved_per_task / baseline_time_minutes) * 100
        
        # Calculate total time savings over measurement period
        total_tasks = users_affected * usage_frequency_per_day * measurement_period_days
        total_time_saved_hours = (total_tasks * time_saved_per_task) / 60
        
        # Financial impact calculation
        hourly_rate = self.config["financial_assumptions"]["employee_hourly_rate_usd"]
        financial_impact = total_time_saved_hours * hourly_rate
        
        # Confidence calculation based on data quality
        confidence = self._calculate_confidence(
            baseline_value=baseline_time_minutes,
            current_value=current_time_minutes,
            sample_size=users_affected * measurement_period_days,
            data_quality=0.85  # Assume good data quality for time measurements
        )
        
        return BusinessImpactResult(
            metric=BusinessMetric.TIME_SAVINGS,
            current_value=current_time_minutes,
            baseline_value=baseline_time_minutes,
            improvement=time_saved_per_task,
            improvement_percent=improvement_percent,
            financial_impact_usd=financial_impact,
            confidence_level=confidence,
            measurement_period_days=measurement_period_days,
            data_sources=["task_timing_logs", "user_activity_tracking"],
            assumptions=[
                f"Employee hourly rate: ${hourly_rate}",
                f"Usage frequency: {usage_frequency_per_day} times/day",
                f"Users affected: {users_affected}"
            ],
            timestamp=datetime.now()
        )
    
    def calculate_error_reduction_impact(
        self,
        baseline_error_rate: float,
        current_error_rate: float,
        total_operations: int,
        cost_per_error: float,
        measurement_period_days: int = 90
    ) -> BusinessImpactResult:
        """Calculate business impact of error reduction."""
        
        error_reduction = baseline_error_rate - current_error_rate
        improvement_percent = (error_reduction / baseline_error_rate) * 100
        
        # Calculate errors prevented
        errors_prevented = total_operations * error_reduction
        
        # Financial impact
        financial_impact = errors_prevented * cost_per_error
        
        # Add secondary benefits (customer satisfaction, reputation)
        secondary_benefits_multiplier = 1.5  # Additional 50% for indirect benefits
        financial_impact *= secondary_benefits_multiplier
        
        confidence = self._calculate_confidence(
            baseline_value=baseline_error_rate,
            current_value=current_error_rate,
            sample_size=total_operations,
            data_quality=0.9  # Error tracking is usually reliable
        )
        
        return BusinessImpactResult(
            metric=BusinessMetric.ERROR_REDUCTION,
            current_value=current_error_rate,
            baseline_value=baseline_error_rate,
            improvement=error_reduction,
            improvement_percent=improvement_percent,
            financial_impact_usd=financial_impact,
            confidence_level=confidence,
            measurement_period_days=measurement_period_days,
            data_sources=["error_logs", "quality_metrics", "customer_complaints"],
            assumptions=[
                f"Cost per error: ${cost_per_error}",
                f"Secondary benefits multiplier: {secondary_benefits_multiplier}x",
                f"Total operations: {total_operations}"
            ],
            timestamp=datetime.now()
        )
    
    def calculate_productivity_impact(
        self,
        baseline_productivity_score: float,
        current_productivity_score: float,
        users_affected: int,
        annual_salary_per_user: float,
        measurement_period_days: int = 90
    ) -> BusinessImpactResult:
        """Calculate business impact of productivity improvements."""
        
        productivity_improvement = current_productivity_score - baseline_productivity_score
        improvement_percent = (productivity_improvement / baseline_productivity_score) * 100
        
        # Calculate annual financial impact
        # Productivity improvement translates to effective salary value increase
        annual_value_per_user = annual_salary_per_user * (improvement_percent / 100)
        total_annual_impact = annual_value_per_user * users_affected
        
        # Prorate for measurement period
        financial_impact = total_annual_impact * (measurement_period_days / 365)
        
        confidence = self._calculate_confidence(
            baseline_value=baseline_productivity_score,
            current_value=current_productivity_score,
            sample_size=users_affected * 30,  # Assume 30 measurement points per user
            data_quality=0.7  # Productivity is subjective, lower confidence
        )
        
        return BusinessImpactResult(
            metric=BusinessMetric.PRODUCTIVITY_GAIN,
            current_value=current_productivity_score,
            baseline_value=baseline_productivity_score,
            improvement=productivity_improvement,
            improvement_percent=improvement_percent,
            financial_impact_usd=financial_impact,
            confidence_level=confidence,
            measurement_period_days=measurement_period_days,
            data_sources=["productivity_surveys", "performance_reviews", "task_completion_rates"],
            assumptions=[
                f"Annual salary per user: ${annual_salary_per_user:,.0f}",
                f"Productivity improvement directly correlates to salary value",
                f"Users affected: {users_affected}"
            ],
            timestamp=datetime.now()
        )
    
    def calculate_cost_reduction_impact(
        self,
        baseline_monthly_costs: float,
        current_monthly_costs: float,
        cost_categories: Dict[str, float],
        measurement_period_days: int = 90
    ) -> BusinessImpactResult:
        """Calculate business impact of cost reductions."""
        
        monthly_savings = baseline_monthly_costs - current_monthly_costs
        improvement_percent = (monthly_savings / baseline_monthly_costs) * 100
        
        # Calculate total savings over measurement period
        total_savings = monthly_savings * (measurement_period_days / 30)
        
        confidence = self._calculate_confidence(
            baseline_value=baseline_monthly_costs,
            current_value=current_monthly_costs,
            sample_size=measurement_period_days,  # Daily cost measurements
            data_quality=0.95  # Financial data is usually very accurate
        )
        
        return BusinessImpactResult(
            metric=BusinessMetric.COST_REDUCTION,
            current_value=current_monthly_costs,
            baseline_value=baseline_monthly_costs,
            improvement=monthly_savings,
            improvement_percent=improvement_percent,
            financial_impact_usd=total_savings,
            confidence_level=confidence,
            measurement_period_days=measurement_period_days,
            data_sources=["financial_reports", "cost_accounting", "vendor_invoices"],
            assumptions=[
                f"Cost categories: {list(cost_categories.keys())}",
                f"Monthly baseline: ${baseline_monthly_costs:,.0f}",
                f"Savings sustained over measurement period"
            ],
            timestamp=datetime.now()
        )
    
    def calculate_revenue_impact(
        self,
        baseline_monthly_revenue: float,
        current_monthly_revenue: float,
        attribution_factor: float,
        measurement_period_days: int = 90
    ) -> BusinessImpactResult:
        """Calculate revenue impact attributable to LLM improvements."""
        
        monthly_revenue_increase = current_monthly_revenue - baseline_monthly_revenue
        # Apply attribution factor (what percentage is due to LLM improvements)
        attributed_increase = monthly_revenue_increase * attribution_factor
        
        improvement_percent = (attributed_increase / baseline_monthly_revenue) * 100
        
        # Calculate total revenue impact over measurement period
        total_revenue_impact = attributed_increase * (measurement_period_days / 30)
        
        confidence = self._calculate_confidence(
            baseline_value=baseline_monthly_revenue,
            current_value=current_monthly_revenue,
            sample_size=measurement_period_days / 7,  # Weekly revenue measurements
            data_quality=0.8  # Revenue attribution can be complex
        ) * attribution_factor  # Reduce confidence based on attribution uncertainty
        
        return BusinessImpactResult(
            metric=BusinessMetric.REVENUE_INCREASE,
            current_value=current_monthly_revenue,
            baseline_value=baseline_monthly_revenue,
            improvement=attributed_increase,
            improvement_percent=improvement_percent,
            financial_impact_usd=total_revenue_impact,
            confidence_level=confidence,
            measurement_period_days=measurement_period_days,
            data_sources=["revenue_reports", "sales_analytics", "customer_metrics"],
            assumptions=[
                f"Attribution factor: {attribution_factor:.1%}",
                f"Revenue increase sustained over period",
                f"No other major factors affecting revenue"
            ],
            timestamp=datetime.now()
        )
    
    def calculate_user_satisfaction_impact(
        self,
        baseline_satisfaction: float,
        current_satisfaction: float,
        users_surveyed: int,
        satisfaction_to_revenue_multiplier: float,
        measurement_period_days: int = 90
    ) -> BusinessImpactResult:
        """Calculate business impact of user satisfaction improvements."""
        
        satisfaction_improvement = current_satisfaction - baseline_satisfaction
        improvement_percent = (satisfaction_improvement / baseline_satisfaction) * 100
        
        # Convert satisfaction to financial impact
        # Higher satisfaction → retention → revenue impact
        financial_impact = (
            satisfaction_improvement * 
            satisfaction_to_revenue_multiplier * 
            users_surveyed * 
            (measurement_period_days / 365)  # Annualized impact, prorated
        )
        
        confidence = self._calculate_confidence(
            baseline_value=baseline_satisfaction,
            current_value=current_satisfaction,
            sample_size=users_surveyed,
            data_quality=0.75  # Survey data has inherent subjectivity
        )
        
        return BusinessImpactResult(
            metric=BusinessMetric.USER_SATISFACTION,
            current_value=current_satisfaction,
            baseline_value=baseline_satisfaction,
            improvement=satisfaction_improvement,
            improvement_percent=improvement_percent,
            financial_impact_usd=financial_impact,
            confidence_level=confidence,
            measurement_period_days=measurement_period_days,
            data_sources=["user_surveys", "satisfaction_scores", "feedback_systems"],
            assumptions=[
                f"Satisfaction to revenue multiplier: ${satisfaction_to_revenue_multiplier:,.0f}/point/user/year",
                f"Users surveyed: {users_surveyed}",
                f"Satisfaction improvements lead to retention and revenue"
            ],
            timestamp=datetime.now()
        )
    
    def calculate_comprehensive_roi(
        self,
        business_impacts: List[BusinessImpactResult],
        implementation_costs: Dict[str, float],
        ongoing_costs: Dict[str, float],
        projection_months: int = 12
    ) -> ROICalculation:
        """Calculate comprehensive ROI from multiple business impacts."""
        
        # Calculate total investment
        total_implementation = sum(implementation_costs.values())
        monthly_ongoing = sum(ongoing_costs.values())
        total_ongoing = monthly_ongoing * projection_months
        total_investment = total_implementation + total_ongoing
        
        # Calculate total benefits (annualized)
        total_benefits = 0
        confidence_weights = []
        
        for impact in business_impacts:
            # Annualize the benefit
            annual_benefit = (impact.financial_impact_usd * 365) / impact.measurement_period_days
            # Project over the specified period
            projected_benefit = annual_benefit * (projection_months / 12)
            
            total_benefits += projected_benefit
            confidence_weights.append(impact.confidence_level)
        
        # Calculate ROI metrics
        net_benefit = total_benefits - total_investment
        roi_percent = (net_benefit / total_investment) * 100 if total_investment > 0 else 0
        
        # Calculate payback period
        monthly_net_benefit = (total_benefits / projection_months) - monthly_ongoing
        payback_period_months = total_implementation / monthly_net_benefit if monthly_net_benefit > 0 else float('inf')
        
        # Calculate NPV
        discount_rate = self.config["financial_assumptions"]["annual_discount_rate"]
        monthly_discount_rate = discount_rate / 12
        
        npv = -total_implementation  # Initial investment
        for month in range(1, projection_months + 1):
            monthly_cash_flow = (total_benefits / projection_months) - monthly_ongoing
            discounted_cash_flow = monthly_cash_flow / ((1 + monthly_discount_rate) ** month)
            npv += discounted_cash_flow
        
        # Calculate IRR (simplified estimation)
        irr_percent = self._estimate_irr(total_investment, total_benefits, projection_months)
        
        # Calculate break-even point
        break_even_months = total_investment / monthly_net_benefit if monthly_net_benefit > 0 else float('inf')
        
        # Calculate confidence interval
        avg_confidence = sum(confidence_weights) / len(confidence_weights) if confidence_weights else 0.5
        confidence_interval = self._calculate_roi_confidence_interval(roi_percent, avg_confidence)
        
        # Risk assessment
        risk_assessment = self._assess_roi_risk(roi_percent, payback_period_months, avg_confidence)
        
        return ROICalculation(
            total_investment_usd=total_investment,
            total_benefits_usd=total_benefits,
            net_benefit_usd=net_benefit,
            roi_percent=roi_percent,
            payback_period_months=payback_period_months,
            npv_usd=npv,
            irr_percent=irr_percent,
            break_even_months=break_even_months,
            confidence_interval=confidence_interval,
            risk_assessment=risk_assessment
        )
    
    def run_comprehensive_business_analysis(
        self,
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run comprehensive business impact analysis."""
        logger.info("Running comprehensive business impact analysis")
        
        business_impacts = []
        
        # Time savings impact
        if 'time_savings' in analysis_data:
            ts_data = analysis_data['time_savings']
            time_impact = self.calculate_time_savings_impact(
                baseline_time_minutes=ts_data.get('baseline_time', 30.0),
                current_time_minutes=ts_data.get('current_time', 20.0),
                users_affected=ts_data.get('users_affected', 50),
                usage_frequency_per_day=ts_data.get('frequency', 3.0),
                measurement_period_days=ts_data.get('period_days', 90)
            )
            business_impacts.append(time_impact)
        
        # Error reduction impact
        if 'error_reduction' in analysis_data:
            er_data = analysis_data['error_reduction']
            error_impact = self.calculate_error_reduction_impact(
                baseline_error_rate=er_data.get('baseline_error_rate', 0.05),
                current_error_rate=er_data.get('current_error_rate', 0.02),
                total_operations=er_data.get('total_operations', 10000),
                cost_per_error=er_data.get('cost_per_error', 500.0),
                measurement_period_days=er_data.get('period_days', 90)
            )
            business_impacts.append(error_impact)
        
        # Productivity impact
        if 'productivity' in analysis_data:
            prod_data = analysis_data['productivity']
            productivity_impact = self.calculate_productivity_impact(
                baseline_productivity_score=prod_data.get('baseline_score', 3.0),
                current_productivity_score=prod_data.get('current_score', 4.2),
                users_affected=prod_data.get('users_affected', 50),
                annual_salary_per_user=prod_data.get('annual_salary', 100000.0),
                measurement_period_days=prod_data.get('period_days', 90)
            )
            business_impacts.append(productivity_impact)
        
        # Cost reduction impact
        if 'cost_reduction' in analysis_data:
            cr_data = analysis_data['cost_reduction']
            cost_impact = self.calculate_cost_reduction_impact(
                baseline_monthly_costs=cr_data.get('baseline_costs', 25000.0),
                current_monthly_costs=cr_data.get('current_costs', 18000.0),
                cost_categories=cr_data.get('categories', {'infrastructure': 15000, 'personnel': 10000}),
                measurement_period_days=cr_data.get('period_days', 90)
            )
            business_impacts.append(cost_impact)
        
        # User satisfaction impact
        if 'user_satisfaction' in analysis_data:
            us_data = analysis_data['user_satisfaction']
            satisfaction_impact = self.calculate_user_satisfaction_impact(
                baseline_satisfaction=us_data.get('baseline_satisfaction', 3.2),
                current_satisfaction=us_data.get('current_satisfaction', 4.1),
                users_surveyed=us_data.get('users_surveyed', 100),
                satisfaction_to_revenue_multiplier=us_data.get('revenue_multiplier', 500.0),
                measurement_period_days=us_data.get('period_days', 90)
            )
            business_impacts.append(satisfaction_impact)
        
        # Calculate comprehensive ROI
        implementation_costs = analysis_data.get('implementation_costs', {
            'development': 75000,
            'integration': 25000,
            'training': 15000,
            'infrastructure': 10000
        })
        
        ongoing_costs = analysis_data.get('ongoing_costs', {
            'api_costs': 2000,
            'maintenance': 5000,
            'monitoring': 1000
        })
        
        roi_calculation = self.calculate_comprehensive_roi(
            business_impacts=business_impacts,
            implementation_costs=implementation_costs,
            ongoing_costs=ongoing_costs,
            projection_months=analysis_data.get('projection_months', 12)
        )
        
        # Store results
        self._store_business_impacts(business_impacts)
        self._store_roi_calculation(roi_calculation)
        
        # Generate analysis summary
        analysis_summary = self._generate_business_analysis_summary(business_impacts, roi_calculation)
        
        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "business_impacts": [asdict(impact) for impact in business_impacts],
            "roi_calculation": asdict(roi_calculation),
            "analysis_summary": analysis_summary,
            "recommendations": self._generate_business_recommendations(business_impacts, roi_calculation),
            "risk_factors": self._identify_risk_factors(business_impacts, roi_calculation)
        }
    
    def generate_stakeholder_dashboard(self, analysis_results: Dict[str, Any]) -> str:
        """Generate executive dashboard for stakeholders."""
        
        roi_calc = analysis_results['roi_calculation']
        impacts = analysis_results['business_impacts']
        
        dashboard = f"""
# VERTIGO LLM BUSINESS IMPACT DASHBOARD
**Executive Summary - {datetime.now().strftime('%B %Y')}**

## 🎯 KEY PERFORMANCE INDICATORS

### Financial Performance
- **ROI**: {roi_calc['roi_percent']:.0f}%
- **Net Benefit**: ${roi_calc['net_benefit_usd']:,.0f}
- **Payback Period**: {roi_calc['payback_period_months']:.1f} months
- **NPV**: ${roi_calc['npv_usd']:,.0f}

### Business Impact Summary
- **Total Investment**: ${roi_calc['total_investment_usd']:,.0f}
- **Projected Benefits**: ${roi_calc['total_benefits_usd']:,.0f}
- **Risk Level**: {roi_calc['risk_assessment']}

## 📊 IMPACT BREAKDOWN

### Operational Improvements
"""
        
        for impact in impacts:
            metric_name = impact['metric'].replace('_', ' ').title()
            dashboard += f"""
**{metric_name}**
- Improvement: {impact['improvement_percent']:.1f}%
- Financial Impact: ${impact['financial_impact_usd']:,.0f}
- Confidence: {impact['confidence_level']:.0%}
"""
        
        dashboard += f"""
## 🎖️ SUCCESS METRICS

### Achieved vs Targets
- **ROI Target**: {self.config['business_metrics']['target_roi']:.0f}% 
- **ROI Achieved**: {roi_calc['roi_percent']:.0f}% {'✅' if roi_calc['roi_percent'] >= self.config['business_metrics']['target_roi'] else '⚠️'}

### Benchmark Comparison
- **Industry Average ROI**: {self.config['industry_benchmarks']['typical_llm_roi']:.0f}%
- **Vertigo Performance**: {roi_calc['roi_percent']:.0f}% ({'Above' if roi_calc['roi_percent'] > self.config['industry_benchmarks']['typical_llm_roi'] else 'Below'} Industry Average)

## 📈 TRENDS & PROJECTIONS

### 12-Month Outlook
- **Projected Annual Savings**: ${roi_calc['total_benefits_usd']:,.0f}
- **Break-Even Point**: {roi_calc['break_even_months']:.1f} months
- **Confidence Interval**: {roi_calc['confidence_interval'][0]:.0f}% - {roi_calc['confidence_interval'][1]:.0f}%

## ⚠️ RISK ASSESSMENT

**Risk Level**: {roi_calc['risk_assessment']}

**Key Risk Factors**:
"""
        
        risk_factors = analysis_results.get('risk_factors', [])
        for risk in risk_factors:
            dashboard += f"- {risk}\n"
        
        dashboard += """
## 🎯 STRATEGIC RECOMMENDATIONS

"""
        
        recommendations = analysis_results.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            dashboard += f"{i}. {rec}\n"
        
        dashboard += f"""
## 📋 NEXT STEPS

### Immediate Actions (This Month)
1. Continue monitoring key performance indicators
2. Validate cost savings projections with financial team
3. Collect additional user satisfaction data

### Strategic Initiatives (Next Quarter)
1. Expand LLM implementation to additional use cases
2. Optimize cost structure based on usage patterns
3. Develop advanced analytics capabilities

---

*Dashboard generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Data confidence: {sum(impact['confidence_level'] for impact in impacts) / len(impacts):.0%} average*
"""
        
        return dashboard
    
    # HELPER METHODS
    
    def _calculate_confidence(
        self,
        baseline_value: float,
        current_value: float,
        sample_size: int,
        data_quality: float
    ) -> float:
        """Calculate confidence level for impact measurements."""
        
        # Base confidence on sample size
        sample_confidence = min(1.0, sample_size / 100)  # 100+ samples = full confidence
        
        # Adjust for measurement difference magnitude
        relative_change = abs(current_value - baseline_value) / baseline_value
        change_confidence = min(1.0, relative_change * 2)  # Larger changes easier to measure
        
        # Apply data quality factor
        overall_confidence = (sample_confidence * 0.4 + change_confidence * 0.3 + data_quality * 0.3)
        
        return max(0.1, min(0.95, overall_confidence))  # Keep within reasonable bounds
    
    def _estimate_irr(self, investment: float, total_benefits: float, months: int) -> float:
        """Estimate Internal Rate of Return (simplified calculation)."""
        if investment <= 0 or months <= 0:
            return 0.0
        
        monthly_cash_flow = total_benefits / months
        
        # Simplified IRR estimation using approximation formula
        # For more accurate IRR, would use iterative methods
        estimated_annual_irr = ((monthly_cash_flow * 12) / investment) * 100
        
        return min(100.0, max(-50.0, estimated_annual_irr))  # Reasonable bounds
    
    def _calculate_roi_confidence_interval(self, roi_percent: float, confidence: float) -> Tuple[float, float]:
        """Calculate confidence interval for ROI."""
        # Confidence interval width based on confidence level
        interval_width = (1 - confidence) * roi_percent * 0.5
        
        lower_bound = max(0, roi_percent - interval_width)
        upper_bound = roi_percent + interval_width
        
        return (lower_bound, upper_bound)
    
    def _assess_roi_risk(self, roi_percent: float, payback_months: float, confidence: float) -> str:
        """Assess risk level of ROI projection."""
        risk_factors = []
        
        if roi_percent < 100:
            risk_factors.append("low_roi")
        if payback_months > 18:
            risk_factors.append("long_payback")
        if confidence < 0.7:
            risk_factors.append("low_confidence")
        
        if len(risk_factors) >= 2:
            return "HIGH"
        elif len(risk_factors) == 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _store_business_impacts(self, impacts: List[BusinessImpactResult]):
        """Store business impact results in database."""
        conn = sqlite3.connect(self.db_path)
        
        for impact in impacts:
            conn.execute("""
                INSERT INTO business_impact (
                    id, metric, current_value, baseline_value, improvement,
                    improvement_percent, financial_impact_usd, confidence_level,
                    measurement_period_days, data_sources, assumptions, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{impact.metric.value}_{int(impact.timestamp.timestamp())}",
                impact.metric.value,
                impact.current_value,
                impact.baseline_value,
                impact.improvement,
                impact.improvement_percent,
                impact.financial_impact_usd,
                impact.confidence_level,
                impact.measurement_period_days,
                json.dumps(impact.data_sources),
                json.dumps(impact.assumptions),
                impact.timestamp.isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def _store_roi_calculation(self, roi_calc: ROICalculation):
        """Store ROI calculation in database."""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute("""
            INSERT INTO roi_calculations (
                id, total_investment_usd, total_benefits_usd, net_benefit_usd,
                roi_percent, payback_period_months, npv_usd, irr_percent,
                break_even_months, confidence_lower, confidence_upper,
                risk_assessment, calculation_date, projection_period_months
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"roi_{int(datetime.now().timestamp())}",
            roi_calc.total_investment_usd,
            roi_calc.total_benefits_usd,
            roi_calc.net_benefit_usd,
            roi_calc.roi_percent,
            roi_calc.payback_period_months,
            roi_calc.npv_usd,
            roi_calc.irr_percent,
            roi_calc.break_even_months,
            roi_calc.confidence_interval[0],
            roi_calc.confidence_interval[1],
            roi_calc.risk_assessment,
            datetime.now().isoformat(),
            12  # Default projection period
        ))
        
        conn.commit()
        conn.close()
    
    def _generate_business_analysis_summary(
        self,
        impacts: List[BusinessImpactResult],
        roi_calc: ROICalculation
    ) -> Dict[str, Any]:
        """Generate summary of business analysis."""
        
        total_financial_impact = sum(impact.financial_impact_usd for impact in impacts)
        avg_confidence = sum(impact.confidence_level for impact in impacts) / len(impacts) if impacts else 0
        
        # Categorize impacts
        impact_categories = {}
        for impact in impacts:
            category = self._categorize_impact(impact.metric)
            if category not in impact_categories:
                impact_categories[category] = []
            impact_categories[category].append(impact.financial_impact_usd)
        
        return {
            "total_financial_impact": total_financial_impact,
            "average_confidence": avg_confidence,
            "roi_performance": "Excellent" if roi_calc.roi_percent > 300 else "Good" if roi_calc.roi_percent > 150 else "Acceptable" if roi_calc.roi_percent > 50 else "Poor",
            "payback_assessment": "Fast" if roi_calc.payback_period_months < 12 else "Moderate" if roi_calc.payback_period_months < 24 else "Slow",
            "impact_categories": {cat: sum(values) for cat, values in impact_categories.items()},
            "key_metrics": {
                "highest_impact_metric": max(impacts, key=lambda x: x.financial_impact_usd).metric.value if impacts else None,
                "most_confident_metric": max(impacts, key=lambda x: x.confidence_level).metric.value if impacts else None,
                "total_improvement_percent": sum(impact.improvement_percent for impact in impacts) / len(impacts) if impacts else 0
            }
        }
    
    def _categorize_impact(self, metric: BusinessMetric) -> ImpactCategory:
        """Categorize business impact by type."""
        category_mapping = {
            BusinessMetric.TIME_SAVINGS: ImpactCategory.OPERATIONAL_EFFICIENCY,
            BusinessMetric.ERROR_REDUCTION: ImpactCategory.RISK_MANAGEMENT,
            BusinessMetric.PRODUCTIVITY_GAIN: ImpactCategory.OPERATIONAL_EFFICIENCY,
            BusinessMetric.COST_REDUCTION: ImpactCategory.COST_OPTIMIZATION,
            BusinessMetric.REVENUE_INCREASE: ImpactCategory.REVENUE_GENERATION,
            BusinessMetric.USER_SATISFACTION: ImpactCategory.STRATEGIC_ADVANTAGE,
            BusinessMetric.COMPETITIVE_ADVANTAGE: ImpactCategory.STRATEGIC_ADVANTAGE,
            BusinessMetric.RISK_MITIGATION: ImpactCategory.RISK_MANAGEMENT
        }
        
        return category_mapping.get(metric, ImpactCategory.OPERATIONAL_EFFICIENCY)
    
    def _generate_business_recommendations(
        self,
        impacts: List[BusinessImpactResult],
        roi_calc: ROICalculation
    ) -> List[str]:
        """Generate business recommendations based on analysis."""
        recommendations = []
        
        # ROI-based recommendations
        if roi_calc.roi_percent > 300:
            recommendations.append("Excellent ROI achieved. Consider expanding LLM implementation to additional use cases.")
        elif roi_calc.roi_percent < 100:
            recommendations.append("ROI below target. Investigate cost optimization opportunities and usage patterns.")
        
        # Payback-based recommendations
        if roi_calc.payback_period_months > 18:
            recommendations.append("Long payback period. Focus on quick-win improvements to accelerate returns.")
        
        # Impact-specific recommendations
        high_impact_metrics = [impact for impact in impacts if impact.financial_impact_usd > 50000]
        for impact in high_impact_metrics:
            if impact.metric == BusinessMetric.TIME_SAVINGS:
                recommendations.append("Significant time savings achieved. Document best practices for broader adoption.")
            elif impact.metric == BusinessMetric.ERROR_REDUCTION:
                recommendations.append("Strong error reduction results. Consider expanding quality improvement initiatives.")
        
        # Confidence-based recommendations
        low_confidence_metrics = [impact for impact in impacts if impact.confidence_level < 0.6]
        if low_confidence_metrics:
            recommendations.append("Improve data collection for low-confidence metrics to increase measurement accuracy.")
        
        # Generic recommendations
        recommendations.extend([
            "Establish monthly business impact reviews with stakeholders",
            "Create automated monitoring for key business metrics",
            "Develop user training programs to maximize LLM adoption benefits"
        ])
        
        return recommendations[:8]  # Limit to top recommendations
    
    def _identify_risk_factors(
        self,
        impacts: List[BusinessImpactResult],
        roi_calc: ROICalculation
    ) -> List[str]:
        """Identify potential risk factors for business case."""
        risk_factors = []
        
        # ROI risks
        if roi_calc.roi_percent < 150:
            risk_factors.append("ROI below industry benchmark - dependent on sustained adoption")
        
        # Confidence risks
        avg_confidence = sum(impact.confidence_level for impact in impacts) / len(impacts) if impacts else 0
        if avg_confidence < 0.7:
            risk_factors.append("Moderate confidence in impact measurements - actual results may vary")
        
        # Dependency risks
        total_time_savings = sum(impact.financial_impact_usd for impact in impacts if impact.metric == BusinessMetric.TIME_SAVINGS)
        total_impact = sum(impact.financial_impact_usd for impact in impacts)
        
        if total_time_savings / total_impact > 0.6 if total_impact > 0 else False:
            risk_factors.append("High dependency on time savings - vulnerable to productivity measurement changes")
        
        # Market risks
        risk_factors.append("Technology evolution may require additional investments")
        risk_factors.append("User adoption rates may impact realized benefits")
        
        return risk_factors[:5]  # Limit to key risks

def run_business_impact_demo():
    """Run comprehensive business impact demonstration."""
    print("=" * 80)
    print("VERTIGO BUSINESS IMPACT & ROI EVALUATION DEMONSTRATION")
    print("=" * 80)
    
    evaluator = BusinessImpactEvaluator()
    
    # Sample analysis data representing Vertigo's business case
    analysis_data = {
        "time_savings": {
            "baseline_time": 45.0,  # minutes per meeting analysis task
            "current_time": 15.0,   # minutes with Vertigo LLM
            "users_affected": 25,   # employees using the system
            "frequency": 4.0,       # times per day
            "period_days": 90
        },
        "error_reduction": {
            "baseline_error_rate": 0.08,  # 8% error rate in manual processing
            "current_error_rate": 0.02,   # 2% with LLM assistance
            "total_operations": 5000,
            "cost_per_error": 750.0,
            "period_days": 90
        },
        "productivity": {
            "baseline_score": 3.1,      # out of 5
            "current_score": 4.3,       # improved with LLM
            "users_affected": 25,
            "annual_salary": 95000.0,
            "period_days": 90
        },
        "cost_reduction": {
            "baseline_costs": 22000.0,  # monthly operational costs
            "current_costs": 16500.0,   # reduced with automation
            "categories": {
                "manual_processing": 12000,
                "error_correction": 6000,
                "administrative_overhead": 4000
            },
            "period_days": 90
        },
        "user_satisfaction": {
            "baseline_satisfaction": 3.0,  # out of 5
            "current_satisfaction": 4.2,   # improved user experience
            "users_surveyed": 25,
            "revenue_multiplier": 2000.0,  # $2000 annual value per satisfaction point per user
            "period_days": 90
        },
        "implementation_costs": {
            "development": 85000,
            "integration": 30000,
            "training": 20000,
            "infrastructure": 15000
        },
        "ongoing_costs": {
            "api_costs": 2500,
            "maintenance": 4000,
            "monitoring": 1500
        },
        "projection_months": 12
    }
    
    print("\n1. RUNNING COMPREHENSIVE BUSINESS ANALYSIS")
    print("-" * 50)
    
    results = evaluator.run_comprehensive_business_analysis(analysis_data)
    
    roi_calc = results['roi_calculation']
    print(f"✅ Analysis Complete!")
    print(f"   ROI: {roi_calc['roi_percent']:.0f}%")
    print(f"   Payback Period: {roi_calc['payback_period_months']:.1f} months")
    print(f"   Net Benefit: ${roi_calc['net_benefit_usd']:,.0f}")
    
    print("\n2. BUSINESS IMPACT BREAKDOWN")
    print("-" * 50)
    
    for impact in results['business_impacts']:
        metric_name = impact['metric'].replace('_', ' ').title()
        print(f"{metric_name}:")
        print(f"  • Improvement: {impact['improvement_percent']:.1f}%")
        print(f"  • Financial Impact: ${impact['financial_impact_usd']:,.0f}")
        print(f"  • Confidence: {impact['confidence_level']:.0%}")
        print()
    
    print("3. GENERATING STAKEHOLDER DASHBOARD")
    print("-" * 50)
    
    dashboard = evaluator.generate_stakeholder_dashboard(results)
    
    # Save dashboard
    dashboard_path = evaluator.results_dir / f"business_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(dashboard_path, 'w') as f:
        f.write(dashboard)
    
    print(f"✅ Dashboard generated: {dashboard_path}")
    
    print("\n4. KEY FINDINGS SUMMARY")
    print("-" * 50)
    
    summary = results['analysis_summary']
    print(f"Total Financial Impact: ${summary['total_financial_impact']:,.0f}")
    print(f"Average Confidence: {summary['average_confidence']:.0%}")
    print(f"ROI Performance: {summary['roi_performance']}")
    print(f"Payback Assessment: {summary['payback_assessment']}")
    
    print(f"\nHighest Impact: {summary['key_metrics']['highest_impact_metric']}")
    print(f"Most Confident: {summary['key_metrics']['most_confident_metric']}")
    
    print("\n5. STRATEGIC RECOMMENDATIONS")
    print("-" * 50)
    
    for i, rec in enumerate(results['recommendations'][:5], 1):
        print(f"{i}. {rec}")
    
    print("\n6. RISK FACTORS")
    print("-" * 50)
    
    for risk in results['risk_factors']:
        print(f"⚠️  {risk}")
    
    # Save complete results
    results_path = evaluator.results_dir / f"business_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Complete results saved: {results_path}")
    
    print("\n" + "=" * 80)
    print("BUSINESS IMPACT DEMONSTRATION COMPLETE")
    print("=" * 80)
    print(f"\nResults directory: {evaluator.results_dir}")
    print("\nThis demonstration shows professional-grade business impact")
    print("measurement and ROI calculation for LLM implementations.")
    print("\nKey capabilities demonstrated:")
    print("• Multi-dimensional business impact measurement")
    print("• Comprehensive ROI calculation with NPV and IRR")
    print("• Confidence intervals and risk assessment")
    print("• Executive dashboard generation")
    print("• Strategic recommendations and risk identification")

if __name__ == "__main__":
    run_business_impact_demo()