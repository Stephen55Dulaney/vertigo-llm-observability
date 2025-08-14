"""
Accuracy evaluator for measuring correctness of agent responses.
Focuses on command detection accuracy, response correctness, and technical precision.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

class AccuracyEvaluator:
    """
    Evaluates the accuracy of agent responses across multiple dimensions.
    Measures command detection, response correctness, and technical precision.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize accuracy evaluator with configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    async def evaluate(self, scenario: Dict[str, Any], 
                      agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate accuracy of agent response for given scenario.
        
        Args:
            scenario: Test scenario with expected outcomes
            agent_response: Agent's response to evaluate
            
        Returns:
            Accuracy evaluation results
        """
        evaluation_results = {
            "score": 0.0,
            "details": {},
            "breakdown": {},
            "evaluation_timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Command Detection Accuracy
            command_accuracy = self._evaluate_command_detection(scenario, agent_response)
            
            # Response Structure Accuracy  
            structure_accuracy = self._evaluate_response_structure(scenario, agent_response)
            
            # Content Accuracy
            content_accuracy = self._evaluate_content_accuracy(scenario, agent_response)
            
            # Error Handling Accuracy
            error_handling_accuracy = self._evaluate_error_handling(scenario, agent_response)
            
            # Calculate weighted score
            accuracy_components = {
                "command_detection": command_accuracy,
                "response_structure": structure_accuracy,
                "content_accuracy": content_accuracy,
                "error_handling": error_handling_accuracy
            }
            
            # Default weights (can be configured)
            weights = {
                "command_detection": self.config.get("command_weight", 0.4),
                "response_structure": self.config.get("structure_weight", 0.2),
                "content_accuracy": self.config.get("content_weight", 0.3),
                "error_handling": self.config.get("error_weight", 0.1)
            }
            
            overall_score = sum(
                accuracy_components[component] * weights[component]
                for component in accuracy_components.keys()
            )
            
            evaluation_results.update({
                "score": round(overall_score, 3),
                "breakdown": accuracy_components,
                "weights": weights,
                "details": {
                    "command_detection_details": self._get_command_detection_details(scenario, agent_response),
                    "structure_analysis": self._get_structure_analysis(agent_response),
                    "content_analysis": self._get_content_analysis(scenario, agent_response),
                    "error_analysis": self._get_error_analysis(scenario, agent_response)
                }
            })
            
        except Exception as e:
            self.logger.error(f"Error in accuracy evaluation: {e}")
            evaluation_results.update({
                "error": str(e),
                "score": 0.0
            })
        
        return evaluation_results
    
    def _evaluate_command_detection(self, scenario: Dict[str, Any], 
                                   agent_response: Dict[str, Any]) -> float:
        """Evaluate accuracy of command detection."""
        expected_command = scenario.get("expected_command")
        
        # Extract detected command from response
        detected_command = None
        if isinstance(agent_response, dict):
            detected_command = agent_response.get("command")
            if not detected_command and "analysis" in agent_response:
                analysis = agent_response["analysis"]
                if isinstance(analysis, dict):
                    detected_command = analysis.get("input", {}).get("expected_command")
        
        # Handle cases where no command is expected
        if expected_command is None:
            return 1.0 if detected_command is None else 0.0
        
        # Handle cases where command should be detected but wasn't
        if detected_command is None:
            return 0.0
        
        # Exact match
        if expected_command == detected_command:
            return 1.0
        
        # Partial match (for similar commands)
        if self._commands_are_similar(expected_command, detected_command):
            return 0.7
        
        return 0.0
    
    def _evaluate_response_structure(self, scenario: Dict[str, Any], 
                                   agent_response: Dict[str, Any]) -> float:
        """Evaluate the structural correctness of the response."""
        if not isinstance(agent_response, dict):
            return 0.1  # Very low score for non-dict responses
        
        structure_score = 0.0
        max_score = 4.0
        
        # Check for required fields
        if "subject" in agent_response:
            structure_score += 1.0
        if "body" in agent_response:
            structure_score += 1.0
        if "command" in agent_response:
            structure_score += 1.0
        
        # Check for analysis/metadata
        if "analysis" in agent_response or "test_metadata" in agent_response:
            structure_score += 1.0
        
        return structure_score / max_score
    
    def _evaluate_content_accuracy(self, scenario: Dict[str, Any], 
                                 agent_response: Dict[str, Any]) -> float:
        """Evaluate the accuracy of response content."""
        expected_elements = scenario.get("expected_response_elements", [])
        
        if not expected_elements:
            return 0.8  # Neutral score when no specific elements expected
        
        response_text = self._extract_response_text(agent_response)
        if not response_text:
            return 0.0
        
        response_text_lower = response_text.lower()
        found_elements = []
        
        for element in expected_elements:
            element_lower = element.lower()
            # Check for exact match or partial match
            if element_lower in response_text_lower:
                found_elements.append(element)
            # Check for semantic similarity (simple keyword matching)
            elif self._semantic_match(element_lower, response_text_lower):
                found_elements.append(element)
        
        accuracy_ratio = len(found_elements) / len(expected_elements)
        return accuracy_ratio
    
    def _evaluate_error_handling(self, scenario: Dict[str, Any], 
                               agent_response: Dict[str, Any]) -> float:
        """Evaluate how well errors are handled."""
        expected_command = scenario.get("expected_command")
        has_error = bool(agent_response.get("error"))
        
        # If no command expected (invalid input scenario)
        if expected_command is None:
            # Good error handling: either no response or graceful error
            if has_error or not agent_response.get("body"):
                return 1.0
            else:
                return 0.5  # Agent responded when it shouldn't have
        
        # If command expected (valid input scenario)
        else:
            # Good handling: no error and response provided
            if not has_error and agent_response.get("body"):
                return 1.0
            # Acceptable: error but with helpful message
            elif has_error and self._is_helpful_error(agent_response):
                return 0.6
            # Poor handling: error without helpful message
            else:
                return 0.2
    
    def _get_command_detection_details(self, scenario: Dict[str, Any], 
                                     agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed analysis of command detection."""
        expected_command = scenario.get("expected_command")
        detected_command = agent_response.get("command")
        
        return {
            "expected_command": expected_command,
            "detected_command": detected_command,
            "exact_match": expected_command == detected_command,
            "detection_successful": detected_command is not None,
            "false_positive": expected_command is None and detected_command is not None,
            "false_negative": expected_command is not None and detected_command is None
        }
    
    def _get_structure_analysis(self, agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response structure."""
        if not isinstance(agent_response, dict):
            return {"is_dict": False, "field_count": 0}
        
        required_fields = ["subject", "body", "command"]
        optional_fields = ["analysis", "test_metadata", "adapter_metadata"]
        
        return {
            "is_dict": True,
            "field_count": len(agent_response.keys()),
            "has_required_fields": sum(1 for field in required_fields if field in agent_response),
            "has_optional_fields": sum(1 for field in optional_fields if field in agent_response),
            "all_fields": list(agent_response.keys())
        }
    
    def _get_content_analysis(self, scenario: Dict[str, Any], 
                            agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response content quality."""
        response_text = self._extract_response_text(agent_response)
        expected_elements = scenario.get("expected_response_elements", [])
        
        analysis = {
            "response_length": len(response_text) if response_text else 0,
            "has_content": bool(response_text and response_text.strip()),
            "expected_elements_count": len(expected_elements),
            "found_elements": []
        }
        
        if response_text and expected_elements:
            response_lower = response_text.lower()
            for element in expected_elements:
                if element.lower() in response_lower:
                    analysis["found_elements"].append(element)
            
            analysis["elements_found_count"] = len(analysis["found_elements"])
            analysis["elements_coverage_ratio"] = len(analysis["found_elements"]) / len(expected_elements)
        
        return analysis
    
    def _get_error_analysis(self, scenario: Dict[str, Any], 
                          agent_response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error handling."""
        return {
            "has_error": bool(agent_response.get("error")),
            "error_message": agent_response.get("error", ""),
            "expected_error": scenario.get("expected_command") is None,
            "error_is_helpful": self._is_helpful_error(agent_response),
            "graceful_failure": self._check_graceful_failure(agent_response)
        }
    
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
    
    def _commands_are_similar(self, expected: str, detected: str) -> bool:
        """Check if two commands are semantically similar."""
        if not expected or not detected:
            return False
        
        expected_words = set(expected.lower().split())
        detected_words = set(detected.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(expected_words.intersection(detected_words))
        union = len(expected_words.union(detected_words))
        
        return (intersection / union) > 0.6 if union > 0 else False
    
    def _semantic_match(self, element: str, response_text: str) -> bool:
        """Check for semantic match between expected element and response."""
        # Simple keyword-based semantic matching
        element_keywords = element.split()
        
        # Check if most keywords from element appear in response
        matches = sum(1 for keyword in element_keywords if keyword in response_text)
        return (matches / len(element_keywords)) > 0.5 if element_keywords else False
    
    def _is_helpful_error(self, agent_response: Dict[str, Any]) -> bool:
        """Check if error message is helpful to the user."""
        error_msg = agent_response.get("error", "")
        if not error_msg:
            return False
        
        helpful_indicators = [
            "try again", "please", "available commands", "help", "usage", 
            "example", "format", "contact", "support"
        ]
        
        error_lower = error_msg.lower()
        return any(indicator in error_lower for indicator in helpful_indicators)
    
    def _check_graceful_failure(self, agent_response: Dict[str, Any]) -> bool:
        """Check if the system failed gracefully."""
        # No error is good
        if not agent_response.get("error"):
            return True
        
        # Error with helpful message is graceful
        if self._is_helpful_error(agent_response):
            return True
        
        # System still provided some structure even with error
        if isinstance(agent_response, dict) and len(agent_response) > 1:
            return True
        
        return False