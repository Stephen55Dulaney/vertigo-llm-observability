#!/usr/bin/env python3
"""
Email Format Comparison Service for Vertigo LLM Observability.
Converts JSON evaluation results into human-readable email format for easy comparison.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

@dataclass
class EmailContent:
    """Structured email content."""
    sender_name: str
    sender_email: str
    subject: str
    timestamp: str
    key_points: List[str]
    action_items: List[str]
    next_steps: List[str]
    participants: List[str]
    raw_content: str

@dataclass
class ComparisonMetrics:
    """Metrics for email comparison."""
    content_accuracy: float
    structure_match: float
    tone_consistency: float
    completeness: float
    format_compliance: float
    factual_precision: float
    overall_score: float
    response_time: float
    total_cost: float

@dataclass
class ComparisonResult:
    """Result of email comparison."""
    actual_email: EmailContent
    llm_email: EmailContent
    metrics: ComparisonMetrics
    differences: List[Dict[str, Any]]
    recommendations: List[str]
    strengths: List[str]

class EmailFormatter:
    """Service for formatting LLM evaluation results as email comparisons."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_email_content(self, content: str, sender_info: Dict[str, str] = None) -> EmailContent:
        """Parse email content into structured format."""
        try:
            # Default sender info
            if not sender_info:
                sender_info = {
                    "name": "Vertigo Agent",
                    "email": "vertigo.agent.2025@gmail.com"
                }
            
            # Extract subject (look for common patterns)
            subject_patterns = [
                r"Subject:\s*(.+?)(?:\n|$)",
                r"^(.+?)\n",  # First line as subject
                r"# (.+?)(?:\n|$)",  # Markdown header
            ]
            
            subject = "Meeting Summary"  # Default
            for pattern in subject_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    subject = match.group(1).strip()
                    break
            
            # Extract structured sections
            key_points = self._extract_section(content, ["key points", "main points", "summary"])
            action_items = self._extract_section(content, ["action items", "actions", "tasks", "to do"])
            next_steps = self._extract_section(content, ["next steps", "follow up", "next actions"])
            participants = self._extract_participants(content)
            
            return EmailContent(
                sender_name=sender_info["name"],
                sender_email=sender_info["email"],
                subject=subject,
                timestamp=datetime.now().strftime("%b %d, %Y, %I:%M %p"),
                key_points=key_points,
                action_items=action_items,
                next_steps=next_steps,
                participants=participants,
                raw_content=content
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing email content: {e}")
            # Return minimal structure on error
            return EmailContent(
                sender_name="Unknown",
                sender_email="unknown@vertigo.com",
                subject="Content Parse Error",
                timestamp=datetime.now().strftime("%b %d, %Y, %I:%M %p"),
                key_points=["Failed to parse content"],
                action_items=[],
                next_steps=[],
                participants=[],
                raw_content=content
            )
    
    def _extract_section(self, content: str, section_names: List[str]) -> List[str]:
        """Extract items from a specific section."""
        items = []
        
        for section_name in section_names:
            # Look for section headers
            patterns = [
                rf"#{1,4}\s*{section_name}[\s:]*\n(.*?)(?=\n#{1,4}|\n\n|\Z)",
                rf"\*\*{section_name}\*\*[\s:]*\n(.*?)(?=\n\*\*|\n\n|\Z)",
                rf"{section_name}[\s:]*\n(.*?)(?=\n[A-Z]|\n\n|\Z)",
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    section_content = match.group(1).strip()
                    
                    # Extract list items
                    list_patterns = [
                        r"[-*+]\s*(.+?)(?=\n[-*+]|\n\n|\Z)",  # Markdown lists
                        r"\d+\.\s*(.+?)(?=\n\d+\.|\n\n|\Z)",  # Numbered lists
                        r"•\s*(.+?)(?=\n•|\n\n|\Z)",  # Bullet points
                    ]
                    
                    for list_pattern in list_patterns:
                        items.extend([
                            item.strip() 
                            for item in re.findall(list_pattern, section_content, re.MULTILINE)
                            if item.strip()
                        ])
                    
                    # If no list patterns found, split by lines
                    if not items:
                        items = [
                            line.strip() 
                            for line in section_content.split('\n') 
                            if line.strip() and not line.strip().startswith('#')
                        ]
                    
                    break
        
        return items[:10]  # Limit to reasonable number
    
    def _extract_participants(self, content: str) -> List[str]:
        """Extract participant names from content."""
        participants = []
        
        # Look for participant sections
        participant_patterns = [
            r"participants?[\s:]*(.+?)(?=\n\n|\Z)",
            r"attendees?[\s:]*(.+?)(?=\n\n|\Z)",
            r"present[\s:]*(.+?)(?=\n\n|\Z)",
        ]
        
        for pattern in participant_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                participant_text = match.group(1).strip()
                
                # Extract names (look for common name patterns)
                name_patterns = [
                    r"([A-Z][a-z]+\s+[A-Z][a-z]+)",  # First Last
                    r"([A-Z][a-z]+)",  # Single names
                ]
                
                for name_pattern in name_patterns:
                    found_names = re.findall(name_pattern, participant_text)
                    participants.extend(found_names)
                
                # If no names found, split by common separators
                if not participants:
                    separators = [',', ';', '&', ' and ', '\n']
                    for sep in separators:
                        if sep in participant_text:
                            participants = [
                                name.strip() 
                                for name in participant_text.split(sep) 
                                if name.strip()
                            ]
                            break
                
                break
        
        return list(set(participants))[:8]  # Remove duplicates, limit count
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        try:
            return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100
        except Exception:
            return 0.0
    
    def compare_emails(self, actual_content: str, llm_content: str, 
                      evaluation_data: Dict[str, Any] = None) -> ComparisonResult:
        """Compare actual email with LLM generated content."""
        try:
            # Parse both emails
            actual_email = self.parse_email_content(
                actual_content, 
                {"name": "Vertigo Agent", "email": "vertigo.agent.2025@gmail.com"}
            )
            llm_email = self.parse_email_content(
                llm_content,
                {"name": "LLM Test Result", "email": "evaluation@vertigo.com"}
            )
            
            # Calculate metrics
            metrics = self._calculate_metrics(actual_email, llm_email, evaluation_data)
            
            # Find differences
            differences = self._find_differences(actual_email, llm_email)
            
            # Generate recommendations
            recommendations, strengths = self._generate_recommendations(metrics, differences)
            
            return ComparisonResult(
                actual_email=actual_email,
                llm_email=llm_email,
                metrics=metrics,
                differences=differences,
                recommendations=recommendations,
                strengths=strengths
            )
            
        except Exception as e:
            self.logger.error(f"Error comparing emails: {e}")
            raise
    
    def _calculate_metrics(self, actual: EmailContent, llm: EmailContent, 
                          eval_data: Dict[str, Any] = None) -> ComparisonMetrics:
        """Calculate comparison metrics."""
        try:
            # Content accuracy - compare key points and action items
            key_points_similarity = self.calculate_similarity(
                ' '.join(actual.key_points), 
                ' '.join(llm.key_points)
            )
            action_items_similarity = self.calculate_similarity(
                ' '.join(actual.action_items), 
                ' '.join(llm.action_items)
            )
            content_accuracy = (key_points_similarity + action_items_similarity) / 2
            
            # Structure match - compare section presence and organization
            actual_sections = len([s for s in [actual.key_points, actual.action_items, actual.next_steps] if s])
            llm_sections = len([s for s in [llm.key_points, llm.action_items, llm.next_steps] if s])
            structure_match = min(actual_sections, llm_sections) / max(actual_sections, llm_sections, 1) * 100
            
            # Tone consistency - based on content similarity
            tone_consistency = self.calculate_similarity(actual.raw_content, llm.raw_content)
            
            # Completeness - compare total content length and sections
            actual_total = len(actual.key_points) + len(actual.action_items) + len(actual.next_steps)
            llm_total = len(llm.key_points) + len(llm.action_items) + len(llm.next_steps)
            completeness = min(llm_total, actual_total) / max(actual_total, 1) * 100
            
            # Format compliance - check if structured sections exist
            format_compliance = 90.0  # Base score
            if not llm.key_points: format_compliance -= 15
            if not llm.action_items: format_compliance -= 15
            if not llm.subject: format_compliance -= 10
            
            # Factual precision - participants and specific details
            participant_match = len(set(actual.participants) & set(llm.participants)) / max(len(actual.participants), 1) * 100
            factual_precision = participant_match * 0.6 + content_accuracy * 0.4
            
            # Overall score
            overall_score = (
                content_accuracy * 0.25 +
                structure_match * 0.20 +
                tone_consistency * 0.15 +
                completeness * 0.15 +
                format_compliance * 0.15 +
                factual_precision * 0.10
            )
            
            # Use evaluation data if provided
            response_time = eval_data.get('response_time', 1.2) if eval_data else 1.2
            total_cost = eval_data.get('total_cost', 0.045) if eval_data else 0.045
            
            return ComparisonMetrics(
                content_accuracy=round(content_accuracy, 1),
                structure_match=round(structure_match, 1),
                tone_consistency=round(tone_consistency, 1),
                completeness=round(completeness, 1),
                format_compliance=round(format_compliance, 1),
                factual_precision=round(factual_precision, 1),
                overall_score=round(overall_score, 1),
                response_time=response_time,
                total_cost=total_cost
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")
            # Return default metrics on error
            return ComparisonMetrics(
                content_accuracy=50.0,
                structure_match=50.0,
                tone_consistency=50.0,
                completeness=50.0,
                format_compliance=50.0,
                factual_precision=50.0,
                overall_score=50.0,
                response_time=2.0,
                total_cost=0.1
            )
    
    def _find_differences(self, actual: EmailContent, llm: EmailContent) -> List[Dict[str, Any]]:
        """Find specific differences between emails."""
        differences = []
        
        try:
            # Compare sections
            sections = [
                ("key_points", actual.key_points, llm.key_points),
                ("action_items", actual.action_items, llm.action_items),
                ("next_steps", actual.next_steps, llm.next_steps),
            ]
            
            for section_name, actual_items, llm_items in sections:
                # Find added items
                for item in llm_items:
                    if not any(self.calculate_similarity(item, actual_item) > 70 for actual_item in actual_items):
                        differences.append({
                            "type": "added",
                            "section": section_name,
                            "content": item,
                            "description": f"Added item in {section_name.replace('_', ' ')}"
                        })
                
                # Find missing items
                for item in actual_items:
                    if not any(self.calculate_similarity(item, llm_item) > 70 for llm_item in llm_items):
                        differences.append({
                            "type": "missing",
                            "section": section_name,
                            "content": item,
                            "description": f"Missing item from {section_name.replace('_', ' ')}"
                        })
                
                # Find modified items
                for actual_item in actual_items:
                    best_match = None
                    best_similarity = 0
                    for llm_item in llm_items:
                        similarity = self.calculate_similarity(actual_item, llm_item)
                        if 30 < similarity < 70 and similarity > best_similarity:
                            best_similarity = similarity
                            best_match = llm_item
                    
                    if best_match:
                        differences.append({
                            "type": "modified",
                            "section": section_name,
                            "original": actual_item,
                            "modified": best_match,
                            "similarity": best_similarity,
                            "description": f"Modified item in {section_name.replace('_', ' ')}"
                        })
            
            return differences[:10]  # Limit to most significant differences
            
        except Exception as e:
            self.logger.error(f"Error finding differences: {e}")
            return []
    
    def _generate_recommendations(self, metrics: ComparisonMetrics, 
                                differences: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """Generate improvement recommendations and strengths."""
        recommendations = []
        strengths = []
        
        try:
            # Identify strengths
            if metrics.content_accuracy >= 90:
                strengths.append("Content accuracy is very high (>90%)")
            if metrics.format_compliance >= 95:
                strengths.append("Format compliance nearly perfect (>95%)")
            if metrics.response_time < 2.0:
                strengths.append("Response time within acceptable range")
            if metrics.overall_score >= 80:
                strengths.append("Overall performance meets quality standards")
            
            # Generate recommendations based on weak areas
            if metrics.factual_precision < 60:
                recommendations.append("Improve factual precision - enhance training data accuracy")
            if metrics.tone_consistency < 70:
                recommendations.append("Enhance tone consistency matching - review prompt instructions")
            if metrics.structure_match < 75:
                recommendations.append("Consider prompt refinement for better structure matching")
            if metrics.completeness < 80:
                recommendations.append("Increase content completeness - ensure all sections are covered")
            if metrics.response_time > 3.0:
                recommendations.append("Optimize response time - consider model selection or prompt length")
            if metrics.total_cost > 0.1:
                recommendations.append("Review cost efficiency - evaluate model choice and token usage")
            
            # Specific recommendations based on differences
            added_count = len([d for d in differences if d["type"] == "added"])
            missing_count = len([d for d in differences if d["type"] == "missing"])
            
            if added_count > missing_count:
                recommendations.append("Reduce hallucination - model is adding non-existent content")
            elif missing_count > added_count:
                recommendations.append("Improve content recall - model is missing important information")
            
            return recommendations[:6], strengths[:4]  # Limit counts
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"], ["Unable to assess strengths"]
    
    def format_for_html(self, comparison: ComparisonResult) -> Dict[str, Any]:
        """Format comparison result for HTML template."""
        try:
            return {
                "actual_email": {
                    "sender_name": comparison.actual_email.sender_name,
                    "sender_email": comparison.actual_email.sender_email,
                    "subject": comparison.actual_email.subject,
                    "timestamp": comparison.actual_email.timestamp,
                    "key_points": comparison.actual_email.key_points,
                    "action_items": comparison.actual_email.action_items,
                    "next_steps": comparison.actual_email.next_steps,
                    "participants": comparison.actual_email.participants,
                },
                "llm_email": {
                    "sender_name": comparison.llm_email.sender_name,
                    "sender_email": comparison.llm_email.sender_email,
                    "subject": comparison.llm_email.subject,
                    "timestamp": comparison.llm_email.timestamp,
                    "key_points": comparison.llm_email.key_points,
                    "action_items": comparison.llm_email.action_items,
                    "next_steps": comparison.llm_email.next_steps,
                    "participants": comparison.llm_email.participants,
                },
                "metrics": {
                    "content_accuracy": comparison.metrics.content_accuracy,
                    "structure_match": comparison.metrics.structure_match,
                    "tone_consistency": comparison.metrics.tone_consistency,
                    "completeness": comparison.metrics.completeness,
                    "format_compliance": comparison.metrics.format_compliance,
                    "factual_precision": comparison.metrics.factual_precision,
                    "overall_score": comparison.metrics.overall_score,
                    "response_time": comparison.metrics.response_time,
                    "total_cost": comparison.metrics.total_cost,
                },
                "differences": comparison.differences,
                "recommendations": comparison.recommendations,
                "strengths": comparison.strengths,
            }
            
        except Exception as e:
            self.logger.error(f"Error formatting for HTML: {e}")
            return {"error": "Failed to format comparison data"}
    
    def generate_comparison_from_json(self, json_data: str) -> ComparisonResult:
        """Generate comparison from JSON evaluation data."""
        try:
            data = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            # Extract actual and expected content from JSON
            actual_content = data.get('actual_output', data.get('expected', ''))
            llm_content = data.get('llm_output', data.get('actual', ''))
            
            # Extract evaluation metrics if available
            eval_metrics = data.get('metrics', {})
            
            return self.compare_emails(actual_content, llm_content, eval_metrics)
            
        except Exception as e:
            self.logger.error(f"Error generating comparison from JSON: {e}")
            raise