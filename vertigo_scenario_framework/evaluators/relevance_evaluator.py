"""
Relevance evaluator for measuring contextual appropriateness of agent responses.
Focuses on user intent matching, contextual awareness, and response completeness.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import re

class RelevanceEvaluator:
    """
    Evaluates the relevance and contextual appropriateness of agent responses.
    Measures how well responses match user intent and context.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize relevance evaluator with configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Define context keywords for different domains
        self.domain_keywords = {
            "email_commands": ["help", "stats", "list", "projects", "week", "total", "commands"],
            "meeting_analysis": ["meeting", "transcript", "discussion", "decisions", "action"],
            "status_reports": ["status", "progress", "summary", "report", "update"],
            "technical": ["api", "database", "code", "architecture", "deployment"],
            "business": ["revenue", "growth", "strategy", "goals", "metrics", "kpi"]
        }
    
    async def evaluate(self, scenario: Dict[str, Any], 
                      agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate relevance of agent response for given scenario.
        
        Args:
            scenario: Test scenario with context and expectations
            agent_response: Agent's response to evaluate
            
        Returns:
            Relevance evaluation results
        """
        evaluation_results = {
            "score": 0.0,
            "details": {},
            "breakdown": {},
            "evaluation_timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # User Intent Matching
            intent_relevance = self._evaluate_intent_matching(scenario, agent_response)
            
            # Contextual Appropriateness
            context_relevance = self._evaluate_contextual_appropriateness(scenario, agent_response)
            
            # Response Completeness
            completeness_relevance = self._evaluate_response_completeness(scenario, agent_response)
            
            # Information Quality
            quality_relevance = self._evaluate_information_quality(scenario, agent_response)
            
            # Calculate weighted score
            relevance_components = {
                "intent_matching": intent_relevance,
                "contextual_appropriateness": context_relevance,
                "response_completeness": completeness_relevance,
                "information_quality": quality_relevance
            }
            
            # Default weights (can be configured)
            weights = {
                "intent_matching": self.config.get("intent_weight", 0.3),
                "contextual_appropriateness": self.config.get("context_weight", 0.25),
                "response_completeness": self.config.get("completeness_weight", 0.25),
                "information_quality": self.config.get("quality_weight", 0.2)
            }
            
            overall_score = sum(
                relevance_components[component] * weights[component]
                for component in relevance_components.keys()
            )
            
            evaluation_results.update({
                "score": round(overall_score, 3),
                "breakdown": relevance_components,
                "weights": weights,
                "details": {
                    "intent_analysis": self._get_intent_analysis(scenario, agent_response),
                    "context_analysis": self._get_context_analysis(scenario, agent_response),
                    "completeness_analysis": self._get_completeness_analysis(scenario, agent_response),
                    "quality_analysis": self._get_quality_analysis(scenario, agent_response)
                }
            })
            
        except Exception as e:
            self.logger.error(f"Error in relevance evaluation: {e}")
            evaluation_results.update({
                "error": str(e),
                "score": 0.0
            })
        
        return evaluation_results
    
    def _evaluate_intent_matching(self, scenario: Dict[str, Any], 
                                 agent_response: Dict[str, Any]) -> float:
        """Evaluate how well response matches user intent."""
        expected_command = scenario.get("expected_command")
        scenario_description = scenario.get("description", "")
        
        # Extract response content
        response_text = self._extract_response_text(agent_response)
        
        if not response_text:
            return 0.0
        
        # For help commands
        if expected_command == "help":
            return self._evaluate_help_intent(response_text)
        
        # For stats commands  
        elif expected_command in ["list this week", "total stats", "list projects"]:
            return self._evaluate_stats_intent(expected_command, response_text)
        
        # For error cases (no expected command)
        elif expected_command is None:
            return self._evaluate_error_intent(response_text)
        
        # Generic intent matching based on keywords
        return self._evaluate_generic_intent(scenario_description, response_text)
    
    def _evaluate_contextual_appropriateness(self, scenario: Dict[str, Any], 
                                           agent_response: Dict[str, Any]) -> float:
        """Evaluate contextual appropriateness of response."""
        scenario_tags = scenario.get("tags", [])
        user_persona = scenario.get("user_persona", "")
        business_context = scenario.get("business_impact", "")
        
        response_text = self._extract_response_text(agent_response)
        if not response_text:
            return 0.0
        
        context_score = 0.0
        max_score = 0.0
        
        # Check domain appropriateness
        domain_score = self._check_domain_appropriateness(scenario_tags, response_text)
        context_score += domain_score * 0.4
        max_score += 0.4
        
        # Check user persona appropriateness
        if user_persona:
            persona_score = self._check_persona_appropriateness(user_persona, response_text)
            context_score += persona_score * 0.3
            max_score += 0.3
        
        # Check business context appropriateness
        if business_context:
            business_score = self._check_business_appropriateness(business_context, response_text)
            context_score += business_score * 0.3
            max_score += 0.3
        
        return context_score / max_score if max_score > 0 else 0.5
    
    def _evaluate_response_completeness(self, scenario: Dict[str, Any], 
                                      agent_response: Dict[str, Any]) -> float:
        """Evaluate completeness of response."""
        expected_elements = scenario.get("expected_response_elements", [])
        response_text = self._extract_response_text(agent_response)
        
        if not expected_elements:
            # If no specific elements expected, check for general completeness
            return self._evaluate_general_completeness(response_text)
        
        if not response_text:
            return 0.0
        
        # Check presence of expected elements
        response_lower = response_text.lower()
        found_elements = 0
        
        for element in expected_elements:
            if self._element_present(element, response_lower):
                found_elements += 1
        
        completeness_ratio = found_elements / len(expected_elements)
        
        # Bonus for additional relevant information
        additional_info_bonus = self._calculate_additional_info_bonus(response_text)
        
        return min(1.0, completeness_ratio + additional_info_bonus)
    
    def _evaluate_information_quality(self, scenario: Dict[str, Any], 
                                    agent_response: Dict[str, Any]) -> float:
        """Evaluate quality and usefulness of information provided."""
        response_text = self._extract_response_text(agent_response)
        
        if not response_text:
            return 0.0
        
        quality_score = 0.0
        
        # Check for specific/quantitative information
        specificity_score = self._check_information_specificity(response_text)
        quality_score += specificity_score * 0.3
        
        # Check for actionable information
        actionability_score = self._check_actionability(response_text)
        quality_score += actionability_score * 0.25
        
        # Check for structure and organization
        structure_score = self._check_information_structure(response_text)
        quality_score += structure_score * 0.25
        
        # Check for clarity and readability
        clarity_score = self._check_clarity(response_text)
        quality_score += clarity_score * 0.2
        
        return quality_score
    
    def _evaluate_help_intent(self, response_text: str) -> float:
        """Evaluate help command response intent matching."""
        help_indicators = [
            "commands", "help", "usage", "available", "examples", 
            "instructions", "guide", "how to"
        ]
        
        response_lower = response_text.lower()
        found_indicators = sum(1 for indicator in help_indicators 
                              if indicator in response_lower)
        
        return min(1.0, found_indicators / 4.0)  # Expect at least 4 indicators for perfect score
    
    def _evaluate_stats_intent(self, command: str, response_text: str) -> float:
        """Evaluate statistics command response intent matching."""
        stats_indicators = {
            "list this week": ["week", "days", "recent", "7", "last"],
            "total stats": ["total", "all", "overall", "statistics", "complete"],
            "list projects": ["projects", "project", "summary", "list"]
        }
        
        expected_indicators = stats_indicators.get(command, [])
        response_lower = response_text.lower()
        
        found_indicators = sum(1 for indicator in expected_indicators 
                              if indicator in response_lower)
        
        return found_indicators / len(expected_indicators) if expected_indicators else 0.5
    
    def _evaluate_error_intent(self, response_text: str) -> float:
        """Evaluate error handling intent (should not provide substantive response)."""
        # For error cases, less content is better
        if len(response_text) < 50:
            return 1.0
        elif len(response_text) < 200:
            return 0.7
        else:
            return 0.3
    
    def _evaluate_generic_intent(self, description: str, response_text: str) -> float:
        """Generic intent matching using description keywords."""
        if not description:
            return 0.5
        
        description_words = set(word.lower() for word in description.split() 
                               if len(word) > 3)
        response_words = set(word.lower() for word in response_text.split())
        
        # Calculate overlap
        overlap = len(description_words.intersection(response_words))
        return min(1.0, overlap / max(len(description_words), 1))
    
    def _check_domain_appropriateness(self, tags: List[str], response_text: str) -> float:
        """Check if response is appropriate for the domain."""
        response_lower = response_text.lower()
        domain_scores = []
        
        for tag in tags:
            if tag in self.domain_keywords:
                keywords = self.domain_keywords[tag]
                found_keywords = sum(1 for keyword in keywords 
                                   if keyword in response_lower)
                domain_scores.append(found_keywords / len(keywords))
        
        return sum(domain_scores) / len(domain_scores) if domain_scores else 0.5
    
    def _check_persona_appropriateness(self, persona: str, response_text: str) -> float:
        """Check if response tone matches user persona."""
        persona_indicators = {
            "CEO": ["strategic", "overview", "summary", "high-level", "executive"],
            "Project Manager": ["timeline", "resources", "deliverables", "milestones"],
            "Technical": ["technical", "implementation", "architecture", "system"],
            "Executive": ["business", "impact", "results", "performance"]
        }
        
        expected_indicators = persona_indicators.get(persona, [])
        if not expected_indicators:
            return 0.5
        
        response_lower = response_text.lower()
        found_indicators = sum(1 for indicator in expected_indicators 
                              if indicator in response_lower)
        
        return found_indicators / len(expected_indicators)
    
    def _check_business_appropriateness(self, business_context: str, response_text: str) -> float:
        """Check if response addresses business context appropriately."""
        if business_context == "high":
            # High business impact should have strategic language
            strategic_terms = ["strategic", "business", "impact", "value", "roi", "results"]
            response_lower = response_text.lower()
            found_terms = sum(1 for term in strategic_terms if term in response_lower)
            return min(1.0, found_terms / 3.0)
        elif business_context == "medium":
            return 0.7  # Neutral score for medium impact
        else:
            return 0.8  # Good score for low impact (less pressure)
    
    def _evaluate_general_completeness(self, response_text: str) -> float:
        """Evaluate general completeness when no specific elements expected."""
        if not response_text:
            return 0.0
        
        # Check for different types of content
        completeness_indicators = {
            "has_summary": any(word in response_text.lower() 
                              for word in ["summary", "overview", "total"]),
            "has_details": len(response_text) > 100,
            "has_structure": any(char in response_text 
                               for char in ["•", "-", ":", "\n\n"]),
            "has_numbers": bool(re.search(r'\d+', response_text))
        }
        
        return sum(completeness_indicators.values()) / len(completeness_indicators)
    
    def _element_present(self, element: str, response_lower: str) -> bool:
        """Check if expected element is present in response."""
        element_lower = element.lower()
        
        # Direct match
        if element_lower in response_lower:
            return True
        
        # Keyword-based matching
        element_words = element_lower.split()
        if len(element_words) > 1:
            # Check if most words are present
            found_words = sum(1 for word in element_words if word in response_lower)
            return found_words / len(element_words) >= 0.6
        
        return False
    
    def _calculate_additional_info_bonus(self, response_text: str) -> float:
        """Calculate bonus for providing additional useful information."""
        bonus_indicators = [
            "tips", "note", "remember", "also", "additionally", 
            "furthermore", "example", "instance"
        ]
        
        response_lower = response_text.lower()
        found_indicators = sum(1 for indicator in bonus_indicators 
                              if indicator in response_lower)
        
        return min(0.2, found_indicators * 0.05)  # Max 20% bonus
    
    def _check_information_specificity(self, response_text: str) -> float:
        """Check for specific, quantitative information."""
        specificity_indicators = {
            "has_numbers": bool(re.search(r'\d+', response_text)),
            "has_percentages": '%' in response_text,
            "has_dates": bool(re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', response_text)),
            "has_metrics": any(word in response_text.lower() 
                              for word in ["total", "count", "average", "rate"])
        }
        
        return sum(specificity_indicators.values()) / len(specificity_indicators)
    
    def _check_actionability(self, response_text: str) -> float:
        """Check for actionable information."""
        action_indicators = [
            "action", "next", "should", "can", "will", "need to", 
            "recommend", "suggest", "consider"
        ]
        
        response_lower = response_text.lower()
        found_indicators = sum(1 for indicator in action_indicators 
                              if indicator in response_lower)
        
        return min(1.0, found_indicators / 3.0)  # Expect at least 3 for perfect score
    
    def _check_information_structure(self, response_text: str) -> float:
        """Check for well-structured information presentation."""
        structure_indicators = {
            "has_sections": '=' in response_text or '---' in response_text,
            "has_bullet_points": '•' in response_text or response_text.count('\n- ') > 0,
            "has_numbering": bool(re.search(r'\d+\.', response_text)),
            "has_paragraphs": response_text.count('\n\n') > 0
        }
        
        return sum(structure_indicators.values()) / len(structure_indicators)
    
    def _check_clarity(self, response_text: str) -> float:
        """Check clarity and readability of response."""
        if not response_text:
            return 0.0
        
        # Simple clarity metrics
        sentences = response_text.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # Penalize very long or very short sentences
        if 10 <= avg_sentence_length <= 25:
            length_score = 1.0
        elif 5 <= avg_sentence_length < 10 or 25 < avg_sentence_length <= 35:
            length_score = 0.8
        else:
            length_score = 0.5
        
        # Check for clarity indicators
        clarity_indicators = {
            "has_transitions": any(word in response_text.lower() 
                                  for word in ["first", "second", "next", "finally", "also"]),
            "avoids_jargon": not any(word in response_text.lower() 
                                   for word in ["utilize", "leverage", "synergy"]),
            "uses_simple_language": True  # Placeholder for more complex analysis
        }
        
        clarity_ratio = sum(clarity_indicators.values()) / len(clarity_indicators)
        
        return (length_score + clarity_ratio) / 2
    
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
    
    def _get_intent_analysis(self, scenario: Dict[str, Any], 
                           agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed intent analysis."""
        expected_command = scenario.get("expected_command")
        response_text = self._extract_response_text(agent_response)
        
        return {
            "expected_command": expected_command,
            "response_length": len(response_text),
            "intent_keywords_found": self._count_intent_keywords(expected_command, response_text),
            "intent_match_type": self._classify_intent_match(expected_command, response_text)
        }
    
    def _get_context_analysis(self, scenario: Dict[str, Any], 
                            agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed context analysis."""
        return {
            "scenario_tags": scenario.get("tags", []),
            "user_persona": scenario.get("user_persona"),
            "business_context": scenario.get("business_impact"),
            "domain_keywords_found": self._count_domain_keywords(scenario, agent_response),
            "context_appropriateness": "high"  # Would be calculated based on analysis
        }
    
    def _get_completeness_analysis(self, scenario: Dict[str, Any], 
                                 agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed completeness analysis."""
        expected_elements = scenario.get("expected_response_elements", [])
        response_text = self._extract_response_text(agent_response)
        
        found_elements = []
        if response_text:
            response_lower = response_text.lower()
            found_elements = [elem for elem in expected_elements 
                             if self._element_present(elem, response_lower)]
        
        return {
            "expected_elements": expected_elements,
            "found_elements": found_elements,
            "missing_elements": [elem for elem in expected_elements 
                               if elem not in found_elements],
            "completeness_ratio": len(found_elements) / len(expected_elements) if expected_elements else 1.0
        }
    
    def _get_quality_analysis(self, scenario: Dict[str, Any], 
                            agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed quality analysis."""
        response_text = self._extract_response_text(agent_response)
        
        return {
            "response_length": len(response_text),
            "has_quantitative_data": bool(re.search(r'\d+', response_text)),
            "has_structure": any(char in response_text for char in ["•", "-", ":"]),
            "readability_score": self._check_clarity(response_text),
            "actionability_score": self._check_actionability(response_text)
        }
    
    def _count_intent_keywords(self, expected_command: str, response_text: str) -> int:
        """Count intent-related keywords in response."""
        if not expected_command or not response_text:
            return 0
        
        command_keywords = expected_command.lower().split()
        response_lower = response_text.lower()
        
        return sum(1 for keyword in command_keywords if keyword in response_lower)
    
    def _classify_intent_match(self, expected_command: str, response_text: str) -> str:
        """Classify the type of intent match."""
        if not expected_command:
            return "no_command_expected"
        
        if not response_text:
            return "no_response"
        
        keyword_count = self._count_intent_keywords(expected_command, response_text)
        command_word_count = len(expected_command.split())
        
        if keyword_count == command_word_count:
            return "perfect_match"
        elif keyword_count >= command_word_count * 0.7:
            return "good_match"
        elif keyword_count > 0:
            return "partial_match"
        else:
            return "poor_match"
    
    def _count_domain_keywords(self, scenario: Dict[str, Any], 
                             agent_response: Dict[str, Any]) -> int:
        """Count domain-relevant keywords in response."""
        tags = scenario.get("tags", [])
        response_text = self._extract_response_text(agent_response)
        
        if not response_text:
            return 0
        
        response_lower = response_text.lower()
        total_keywords = 0
        
        for tag in tags:
            if tag in self.domain_keywords:
                keywords = self.domain_keywords[tag]
                total_keywords += sum(1 for keyword in keywords 
                                    if keyword in response_lower)
        
        return total_keywords