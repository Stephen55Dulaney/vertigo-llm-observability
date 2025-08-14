"""
Business Impact evaluator for measuring the business value of agent responses.
Focuses on executive utility, decision support, and strategic value.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re

class BusinessImpactEvaluator:
    """
    Evaluates the business impact and value of agent responses.
    Measures executive utility, decision support capability, and strategic value.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize business impact evaluator with configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Define business value indicators by category
        self.business_indicators = {
            "executive_value": [
                "summary", "overview", "strategic", "key", "critical", "important",
                "decision", "recommendation", "impact", "value", "roi", "results"
            ],
            "actionability": [
                "action", "next steps", "should", "recommend", "suggest", "plan",
                "implement", "execute", "follow up", "schedule", "deadline"
            ],
            "data_driven": [
                "data", "metrics", "numbers", "statistics", "performance", 
                "measurement", "kpi", "trend", "analysis", "insights"
            ],
            "risk_awareness": [
                "risk", "concern", "issue", "problem", "challenge", "blocker",
                "mitigation", "contingency", "backup", "alternative"
            ],
            "time_sensitivity": [
                "urgent", "immediate", "asap", "deadline", "timeline", "schedule",
                "date", "today", "tomorrow", "this week", "priority"
            ]
        }
        
        # Define user persona business impact weights
        self.persona_weights = {
            "CEO": {"strategic": 0.4, "executive": 0.3, "operational": 0.3},
            "Executive": {"strategic": 0.35, "executive": 0.35, "operational": 0.3},
            "Project Manager": {"operational": 0.4, "strategic": 0.3, "executive": 0.3},
            "Technical": {"operational": 0.5, "technical": 0.3, "strategic": 0.2}
        }
    
    async def evaluate(self, scenario: Dict[str, Any], 
                      agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate business impact of agent response for given scenario.
        
        Args:
            scenario: Test scenario with business context
            agent_response: Agent's response to evaluate
            
        Returns:
            Business impact evaluation results
        """
        evaluation_results = {
            "score": 0.0,
            "details": {},
            "breakdown": {},
            "evaluation_timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Executive Utility
            executive_utility = self._evaluate_executive_utility(scenario, agent_response)
            
            # Decision Support
            decision_support = self._evaluate_decision_support(scenario, agent_response)
            
            # Strategic Value
            strategic_value = self._evaluate_strategic_value(scenario, agent_response)
            
            # Time to Value
            time_to_value = self._evaluate_time_to_value(scenario, agent_response)
            
            # Calculate weighted score based on business context
            business_components = {
                "executive_utility": executive_utility,
                "decision_support": decision_support,
                "strategic_value": strategic_value,
                "time_to_value": time_to_value
            }
            
            # Adjust weights based on user persona and business context
            weights = self._get_business_weights(scenario)
            
            overall_score = sum(
                business_components[component] * weights[component]
                for component in business_components.keys()
            )
            
            # Apply business context multiplier
            context_multiplier = self._get_business_context_multiplier(scenario)
            final_score = overall_score * context_multiplier
            
            evaluation_results.update({
                "score": round(min(1.0, final_score), 3),
                "breakdown": business_components,
                "weights": weights,
                "context_multiplier": context_multiplier,
                "details": {
                    "executive_analysis": self._get_executive_analysis(scenario, agent_response),
                    "decision_analysis": self._get_decision_analysis(scenario, agent_response),
                    "strategic_analysis": self._get_strategic_analysis(scenario, agent_response),
                    "value_analysis": self._get_value_analysis(scenario, agent_response)
                }
            })
            
        except Exception as e:
            self.logger.error(f"Error in business impact evaluation: {e}")
            evaluation_results.update({
                "error": str(e),
                "score": 0.0
            })
        
        return evaluation_results
    
    def _evaluate_executive_utility(self, scenario: Dict[str, Any], 
                                   agent_response: Dict[str, Any]) -> float:
        """Evaluate utility for executive-level users."""
        response_text = self._extract_response_text(agent_response)
        
        if not response_text:
            return 0.0
        
        utility_score = 0.0
        
        # Check for executive-level language
        executive_indicators = self.business_indicators["executive_value"]
        response_lower = response_text.lower()
        found_indicators = sum(1 for indicator in executive_indicators 
                              if indicator in response_lower)
        executive_language_score = min(1.0, found_indicators / 6.0)
        utility_score += executive_language_score * 0.3
        
        # Check for high-level summaries
        summary_score = self._check_summary_quality(response_text)
        utility_score += summary_score * 0.3
        
        # Check for strategic insights
        strategic_score = self._check_strategic_insights(response_text)
        utility_score += strategic_score * 0.25
        
        # Check for brevity and conciseness (executives prefer concise info)
        conciseness_score = self._check_conciseness(response_text)
        utility_score += conciseness_score * 0.15
        
        return utility_score
    
    def _evaluate_decision_support(self, scenario: Dict[str, Any], 
                                  agent_response: Dict[str, Any]) -> float:
        """Evaluate how well response supports business decisions."""
        response_text = self._extract_response_text(agent_response)
        
        if not response_text:
            return 0.0
        
        decision_score = 0.0
        
        # Check for actionable recommendations
        actionability_indicators = self.business_indicators["actionability"]
        response_lower = response_text.lower()
        found_actions = sum(1 for indicator in actionability_indicators 
                           if indicator in response_lower)
        actionability_score = min(1.0, found_actions / 4.0)
        decision_score += actionability_score * 0.4
        
        # Check for data-driven insights
        data_indicators = self.business_indicators["data_driven"]
        found_data = sum(1 for indicator in data_indicators 
                        if indicator in response_lower)
        data_score = min(1.0, found_data / 4.0)
        decision_score += data_score * 0.3
        
        # Check for risk awareness
        risk_indicators = self.business_indicators["risk_awareness"]
        found_risks = sum(1 for indicator in risk_indicators 
                         if indicator in response_lower)
        risk_score = min(1.0, found_risks / 3.0)
        decision_score += risk_score * 0.3
        
        return decision_score
    
    def _evaluate_strategic_value(self, scenario: Dict[str, Any], 
                                 agent_response: Dict[str, Any]) -> float:
        """Evaluate strategic business value of response."""
        response_text = self._extract_response_text(agent_response)
        business_impact = scenario.get("business_impact", "medium")
        
        if not response_text:
            return 0.0
        
        strategic_score = 0.0
        
        # Check for strategic thinking indicators
        strategic_indicators = [
            "strategy", "strategic", "long-term", "vision", "goal", "objective",
            "competitive", "market", "opportunity", "growth", "expansion"
        ]
        response_lower = response_text.lower()
        found_strategic = sum(1 for indicator in strategic_indicators 
                             if indicator in response_lower)
        strategic_thinking_score = min(1.0, found_strategic / 5.0)
        strategic_score += strategic_thinking_score * 0.4
        
        # Check for business outcome focus
        outcome_indicators = [
            "outcome", "result", "impact", "benefit", "value", "roi",
            "revenue", "cost", "efficiency", "productivity", "performance"
        ]
        found_outcomes = sum(1 for indicator in outcome_indicators 
                            if indicator in response_lower)
        outcome_score = min(1.0, found_outcomes / 4.0)
        strategic_score += outcome_score * 0.35
        
        # Check alignment with business context
        context_alignment = self._check_business_context_alignment(
            business_impact, response_text
        )
        strategic_score += context_alignment * 0.25
        
        return strategic_score
    
    def _evaluate_time_to_value(self, scenario: Dict[str, Any], 
                               agent_response: Dict[str, Any]) -> float:
        """Evaluate how quickly response provides business value."""
        response_text = self._extract_response_text(agent_response)
        
        if not response_text:
            return 0.0
        
        time_value_score = 0.0
        
        # Check for immediate actionability
        immediate_indicators = ["now", "today", "immediately", "right away", "urgent"]
        response_lower = response_text.lower()
        found_immediate = sum(1 for indicator in immediate_indicators 
                             if indicator in response_lower)
        immediacy_score = min(1.0, found_immediate / 2.0)
        time_value_score += immediacy_score * 0.3
        
        # Check for clear next steps
        next_step_indicators = ["next", "step", "action", "follow", "do"]
        found_steps = sum(1 for indicator in next_step_indicators 
                         if indicator in response_lower)
        steps_score = min(1.0, found_steps / 3.0)
        time_value_score += steps_score * 0.3
        
        # Check for time-sensitive information
        time_indicators = self.business_indicators["time_sensitivity"]
        found_time = sum(1 for indicator in time_indicators 
                        if indicator in response_lower)
        time_sensitivity_score = min(1.0, found_time / 3.0)
        time_value_score += time_sensitivity_score * 0.2
        
        # Bonus for providing specific timelines or deadlines
        timeline_bonus = self._check_timeline_specificity(response_text)
        time_value_score += timeline_bonus * 0.2
        
        return time_value_score
    
    def _get_business_weights(self, scenario: Dict[str, Any]) -> Dict[str, float]:
        """Get weights adjusted for business context."""
        user_persona = scenario.get("user_persona", "")
        business_impact = scenario.get("business_impact", "medium")
        
        # Default weights
        weights = {
            "executive_utility": 0.25,
            "decision_support": 0.3,
            "strategic_value": 0.25,
            "time_to_value": 0.2
        }
        
        # Adjust based on user persona
        if user_persona in ["CEO", "Executive"]:
            weights["executive_utility"] = 0.35
            weights["strategic_value"] = 0.3
            weights["decision_support"] = 0.25
            weights["time_to_value"] = 0.1
        elif user_persona == "Project Manager":
            weights["decision_support"] = 0.4
            weights["time_to_value"] = 0.3
            weights["executive_utility"] = 0.2
            weights["strategic_value"] = 0.1
        
        # Adjust based on business impact level
        if business_impact == "high":
            weights["strategic_value"] *= 1.2
            weights["executive_utility"] *= 1.1
        elif business_impact == "low":
            weights["time_to_value"] *= 1.3
        
        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        for key in weights:
            weights[key] /= total_weight
        
        return weights
    
    def _get_business_context_multiplier(self, scenario: Dict[str, Any]) -> float:
        """Get multiplier based on business context importance."""
        business_impact = scenario.get("business_impact", "medium")
        priority = scenario.get("priority", "medium")
        
        multiplier = 1.0
        
        # Business impact multiplier
        if business_impact == "high":
            multiplier *= 1.1
        elif business_impact == "critical":
            multiplier *= 1.2
        elif business_impact == "low":
            multiplier *= 0.9
        
        # Priority multiplier
        if priority == "high":
            multiplier *= 1.05
        elif priority == "critical":
            multiplier *= 1.1
        
        return multiplier
    
    def _check_summary_quality(self, response_text: str) -> float:
        """Check quality of high-level summaries."""
        if not response_text:
            return 0.0
        
        summary_indicators = {
            "has_summary_section": any(word in response_text.lower() 
                                     for word in ["summary", "overview", "key points"]),
            "concise_format": 200 <= len(response_text) <= 800,
            "structured_content": any(char in response_text 
                                    for char in ["•", "-", "1.", "2."]),
            "executive_language": any(word in response_text.lower() 
                                    for word in ["key", "critical", "important", "strategic"])
        }
        
        return sum(summary_indicators.values()) / len(summary_indicators)
    
    def _check_strategic_insights(self, response_text: str) -> float:
        """Check for strategic business insights."""
        strategic_patterns = [
            r"impact.*business", r"strategic.*decision", r"long[- ]term.*goal",
            r"competitive.*advantage", r"market.*opportunity", r"growth.*potential"
        ]
        
        response_lower = response_text.lower()
        found_patterns = sum(1 for pattern in strategic_patterns 
                            if re.search(pattern, response_lower))
        
        return min(1.0, found_patterns / 3.0)
    
    def _check_conciseness(self, response_text: str) -> float:
        """Check if response is appropriately concise for executives."""
        if not response_text:
            return 0.0
        
        word_count = len(response_text.split())
        
        # Optimal range for executive communication: 50-300 words
        if 50 <= word_count <= 150:
            return 1.0
        elif 150 < word_count <= 300:
            return 0.8
        elif 25 <= word_count < 50 or 300 < word_count <= 500:
            return 0.6
        elif word_count < 25 or word_count > 500:
            return 0.3
        else:
            return 0.1
    
    def _check_business_context_alignment(self, business_impact: str, 
                                        response_text: str) -> float:
        """Check alignment with business context."""
        response_lower = response_text.lower()
        
        if business_impact == "high":
            # Should include strategic language
            strategic_terms = ["strategic", "critical", "important", "key", "priority"]
            found_terms = sum(1 for term in strategic_terms if term in response_lower)
            return min(1.0, found_terms / 3.0)
        elif business_impact == "medium":
            # Should be balanced
            return 0.7
        else:  # low impact
            # Should be efficient and practical
            practical_terms = ["simple", "quick", "easy", "straightforward"]
            found_terms = sum(1 for term in practical_terms if term in response_lower)
            return min(1.0, 0.5 + found_terms / 4.0)
    
    def _check_timeline_specificity(self, response_text: str) -> float:
        """Check for specific timelines and deadlines."""
        # Look for specific dates, times, or deadlines
        timeline_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # ISO dates
            r'\d{1,2}/\d{1,2}/\d{4}',  # US dates
            r'by \w+day',  # by Monday, by Friday, etc.
            r'within \d+ \w+',  # within 3 days, within 2 weeks
            r'deadline.*\d+',  # deadline mentions with numbers
        ]
        
        found_patterns = sum(1 for pattern in timeline_patterns 
                            if re.search(pattern, response_text))
        
        return min(1.0, found_patterns / 2.0)
    
    def _extract_response_text(self, agent_response: Dict[str, Any]) -> str:
        """Extract text content from agent response."""
        if not isinstance(agent_response, dict):
            return str(agent_response)
        
        text_parts = []
        
        # Extract from common text fields
        for field in ["body", "subject", "output"]:
            if field in agent_response and agent_response[field]:
                text_parts.append(str(agent_response[field]))
        
        return " ".join(text_parts)
    
    def _get_executive_analysis(self, scenario: Dict[str, Any], 
                              agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed executive utility analysis."""
        response_text = self._extract_response_text(agent_response)
        
        return {
            "executive_language_score": self._count_executive_indicators(response_text),
            "summary_quality": self._check_summary_quality(response_text),
            "conciseness_rating": self._rate_conciseness(response_text),
            "strategic_depth": self._check_strategic_insights(response_text)
        }
    
    def _get_decision_analysis(self, scenario: Dict[str, Any], 
                             agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed decision support analysis."""
        response_text = self._extract_response_text(agent_response)
        
        return {
            "actionable_items": self._count_actionable_items(response_text),
            "data_driven_insights": self._count_data_insights(response_text),
            "risk_considerations": self._count_risk_mentions(response_text),
            "decision_clarity": self._assess_decision_clarity(response_text)
        }
    
    def _get_strategic_analysis(self, scenario: Dict[str, Any], 
                              agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed strategic value analysis."""
        response_text = self._extract_response_text(agent_response)
        business_impact = scenario.get("business_impact", "medium")
        
        return {
            "strategic_thinking_score": self._assess_strategic_thinking(response_text),
            "business_outcome_focus": self._assess_outcome_focus(response_text),
            "context_alignment": self._check_business_context_alignment(business_impact, response_text),
            "long_term_perspective": self._check_long_term_perspective(response_text)
        }
    
    def _get_value_analysis(self, scenario: Dict[str, Any], 
                          agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed time-to-value analysis."""
        response_text = self._extract_response_text(agent_response)
        
        return {
            "immediate_value": self._assess_immediate_value(response_text),
            "clear_next_steps": self._count_next_steps(response_text),
            "timeline_specificity": self._check_timeline_specificity(response_text),
            "urgency_indicators": self._count_urgency_indicators(response_text)
        }
    
    # Helper methods for detailed analysis
    def _count_executive_indicators(self, response_text: str) -> int:
        """Count executive-level language indicators."""
        indicators = self.business_indicators["executive_value"]
        response_lower = response_text.lower()
        return sum(1 for indicator in indicators if indicator in response_lower)
    
    def _rate_conciseness(self, response_text: str) -> str:
        """Rate conciseness level."""
        word_count = len(response_text.split())
        if word_count <= 100:
            return "Very Concise"
        elif word_count <= 200:
            return "Concise"
        elif word_count <= 400:
            return "Moderate"
        else:
            return "Verbose"
    
    def _count_actionable_items(self, response_text: str) -> int:
        """Count actionable items in response."""
        action_patterns = [
            r"action.*item", r"next.*step", r"should.*do", r"recommend.*that",
            r"suggest.*to", r"need.*to", r"must.*do"
        ]
        
        response_lower = response_text.lower()
        return sum(1 for pattern in action_patterns 
                  if re.search(pattern, response_lower))
    
    def _count_data_insights(self, response_text: str) -> int:
        """Count data-driven insights."""
        data_indicators = self.business_indicators["data_driven"]
        response_lower = response_text.lower()
        return sum(1 for indicator in data_indicators if indicator in response_lower)
    
    def _count_risk_mentions(self, response_text: str) -> int:
        """Count risk-related mentions."""
        risk_indicators = self.business_indicators["risk_awareness"]
        response_lower = response_text.lower()
        return sum(1 for indicator in risk_indicators if indicator in response_lower)
    
    def _assess_decision_clarity(self, response_text: str) -> str:
        """Assess clarity of decision support."""
        clarity_indicators = ["clear", "obvious", "evident", "recommend", "suggest"]
        response_lower = response_text.lower()
        found_indicators = sum(1 for indicator in clarity_indicators 
                              if indicator in response_lower)
        
        if found_indicators >= 3:
            return "High"
        elif found_indicators >= 1:
            return "Medium"
        else:
            return "Low"
    
    def _assess_strategic_thinking(self, response_text: str) -> float:
        """Assess level of strategic thinking."""
        strategic_indicators = [
            "strategic", "long-term", "vision", "goal", "objective",
            "competitive", "market", "opportunity", "growth"
        ]
        response_lower = response_text.lower()
        found_indicators = sum(1 for indicator in strategic_indicators 
                              if indicator in response_lower)
        
        return min(1.0, found_indicators / 5.0)
    
    def _assess_outcome_focus(self, response_text: str) -> float:
        """Assess focus on business outcomes."""
        outcome_indicators = [
            "outcome", "result", "impact", "benefit", "value", "roi",
            "revenue", "cost", "efficiency", "productivity"
        ]
        response_lower = response_text.lower()
        found_indicators = sum(1 for indicator in outcome_indicators 
                              if indicator in response_lower)
        
        return min(1.0, found_indicators / 4.0)
    
    def _check_long_term_perspective(self, response_text: str) -> bool:
        """Check for long-term perspective."""
        long_term_indicators = [
            "long-term", "future", "years", "strategic", "vision", "roadmap"
        ]
        response_lower = response_text.lower()
        return any(indicator in response_lower for indicator in long_term_indicators)
    
    def _assess_immediate_value(self, response_text: str) -> float:
        """Assess immediate business value."""
        immediate_indicators = ["now", "today", "immediate", "right away", "urgent"]
        response_lower = response_text.lower()
        found_indicators = sum(1 for indicator in immediate_indicators 
                              if indicator in response_lower)
        
        return min(1.0, found_indicators / 2.0)
    
    def _count_next_steps(self, response_text: str) -> int:
        """Count clear next steps."""
        step_patterns = [
            r"next.*step", r"step \d+", r"first.*do", r"then.*do",
            r"action.*item", r"follow.*up"
        ]
        
        response_lower = response_text.lower()
        return sum(1 for pattern in step_patterns 
                  if re.search(pattern, response_lower))
    
    def _count_urgency_indicators(self, response_text: str) -> int:
        """Count urgency indicators."""
        urgency_indicators = self.business_indicators["time_sensitivity"]
        response_lower = response_text.lower()
        return sum(1 for indicator in urgency_indicators if indicator in response_lower)