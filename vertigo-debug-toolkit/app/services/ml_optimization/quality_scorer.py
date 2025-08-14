"""
Prompt Quality Scoring Algorithms
Provides intelligent scoring and quality assessment of prompts based on multiple criteria.
"""

import os
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import Counter
import statistics
import json

logger = logging.getLogger(__name__)


@dataclass
class QualityMetric:
    """Individual quality metric assessment."""
    metric_name: str
    score: float  # 0-100
    weight: float  # Importance weight
    description: str
    recommendations: List[str]
    evidence: Dict[str, Any]


@dataclass
class PromptQualityAssessment:
    """Complete prompt quality assessment."""
    prompt_id: str
    prompt_text: str
    overall_score: float  # 0-100
    grade: str  # A+, A, B+, B, C+, C, D, F
    metrics: List[QualityMetric]
    strengths: List[str]
    weaknesses: List[str]
    optimization_priority: str  # high, medium, low
    estimated_improvement_potential: float  # 0-1


class PromptQualityScorer:
    """
    Advanced prompt quality scoring system.
    
    Evaluates prompts across multiple dimensions including:
    - Clarity and specificity
    - Structure and organization  
    - Performance characteristics
    - Token efficiency
    - Error resilience
    """
    
    def __init__(self):
        """Initialize the quality scorer."""
        
        # Quality metric weights (must sum to 1.0)
        self.metric_weights = {
            'clarity_specificity': 0.20,
            'structure_organization': 0.15,
            'performance_consistency': 0.25,
            'token_efficiency': 0.15,
            'error_resilience': 0.15,
            'context_appropriateness': 0.10
        }
        
        # Performance thresholds for scoring
        self.performance_thresholds = {
            'excellent_latency_ms': 1000,
            'good_latency_ms': 3000,
            'excellent_success_rate': 0.98,
            'good_success_rate': 0.90,
            'excellent_cost_usd': 0.05,
            'good_cost_usd': 0.20
        }
        
        # Prompt quality indicators
        self.quality_indicators = {
            'positive_patterns': [
                r'\b(specific|detailed|precise|clear|concise)\b',
                r'\b(step-by-step|systematic|structured)\b',
                r'\b(example|format|template)\b',
                r'\b(constraint|requirement|criteria)\b'
            ],
            'negative_patterns': [
                r'\b(vague|unclear|ambiguous|confusing)\b',
                r'\b(maybe|perhaps|possibly|might)\b',
                r'\bplease\s+try\b',
                r'\banything\s+you\s+want\b'
            ],
            'structure_keywords': [
                'role:', 'task:', 'context:', 'format:', 'example:',
                'instructions:', 'steps:', 'requirements:', 'constraints:'
            ]
        }
        
        logger.info("PromptQualityScorer initialized")
    
    def assess_prompt_quality(self, prompt_text: str, prompt_id: str = None,
                            performance_data: Dict[str, Any] = None) -> PromptQualityAssessment:
        """
        Assess the overall quality of a prompt.
        
        Args:
            prompt_text: The prompt text to analyze
            prompt_id: Optional prompt identifier
            performance_data: Optional performance metrics
            
        Returns:
            Complete quality assessment
        """
        try:
            if not prompt_text or not isinstance(prompt_text, str):
                return self._create_empty_assessment(prompt_id or 'unknown')
            
            # Calculate individual quality metrics
            metrics = []
            
            # 1. Clarity and Specificity
            clarity_metric = self._assess_clarity_specificity(prompt_text)
            metrics.append(clarity_metric)
            
            # 2. Structure and Organization
            structure_metric = self._assess_structure_organization(prompt_text)
            metrics.append(structure_metric)
            
            # 3. Performance Consistency (if data available)
            if performance_data:
                performance_metric = self._assess_performance_consistency(performance_data)
                metrics.append(performance_metric)
            else:
                # Use default neutral score if no performance data
                metrics.append(QualityMetric(
                    metric_name='performance_consistency',
                    score=50.0,
                    weight=self.metric_weights['performance_consistency'],
                    description='Performance data not available',
                    recommendations=['Collect performance data for better assessment'],
                    evidence={'status': 'no_data'}
                ))
            
            # 4. Token Efficiency
            token_metric = self._assess_token_efficiency(prompt_text)
            metrics.append(token_metric)
            
            # 5. Error Resilience
            resilience_metric = self._assess_error_resilience(prompt_text)
            metrics.append(resilience_metric)
            
            # 6. Context Appropriateness
            context_metric = self._assess_context_appropriateness(prompt_text)
            metrics.append(context_metric)
            
            # Calculate overall score
            overall_score = sum(m.score * m.weight for m in metrics)
            
            # Determine grade
            grade = self._calculate_grade(overall_score)
            
            # Extract strengths and weaknesses
            strengths = []
            weaknesses = []
            
            for metric in metrics:
                if metric.score >= 80:
                    strengths.append(f"Strong {metric.metric_name.replace('_', ' ')}")
                elif metric.score <= 40:
                    weaknesses.append(f"Weak {metric.metric_name.replace('_', ' ')}")
            
            # Determine optimization priority
            optimization_priority = self._determine_optimization_priority(overall_score, metrics)
            
            # Estimate improvement potential
            improvement_potential = self._estimate_improvement_potential(metrics)
            
            return PromptQualityAssessment(
                prompt_id=prompt_id or 'unknown',
                prompt_text=prompt_text[:500] + '...' if len(prompt_text) > 500 else prompt_text,
                overall_score=overall_score,
                grade=grade,
                metrics=metrics,
                strengths=strengths,
                weaknesses=weaknesses,
                optimization_priority=optimization_priority,
                estimated_improvement_potential=improvement_potential
            )
            
        except Exception as e:
            logger.error(f"Error assessing prompt quality: {e}")
            return self._create_empty_assessment(prompt_id or 'unknown')
    
    def batch_assess_prompts(self, prompts: List[Dict[str, Any]]) -> List[PromptQualityAssessment]:
        """
        Assess quality of multiple prompts.
        
        Args:
            prompts: List of prompt dictionaries with 'text', 'id', and optional 'performance_data'
            
        Returns:
            List of quality assessments
        """
        try:
            assessments = []
            
            for prompt_data in prompts:
                prompt_text = prompt_data.get('text', '')
                prompt_id = prompt_data.get('id')
                performance_data = prompt_data.get('performance_data')
                
                assessment = self.assess_prompt_quality(
                    prompt_text=prompt_text,
                    prompt_id=prompt_id,
                    performance_data=performance_data
                )
                assessments.append(assessment)
            
            # Sort by overall score (highest first)
            assessments.sort(key=lambda x: x.overall_score, reverse=True)
            
            return assessments
            
        except Exception as e:
            logger.error(f"Error in batch prompt assessment: {e}")
            return []
    
    def get_quality_insights(self, assessments: List[PromptQualityAssessment]) -> Dict[str, Any]:
        """
        Generate insights from quality assessments.
        
        Args:
            assessments: List of prompt quality assessments
            
        Returns:
            Quality insights summary
        """
        try:
            if not assessments:
                return {}
            
            # Overall statistics
            scores = [a.overall_score for a in assessments]
            avg_score = statistics.mean(scores)
            median_score = statistics.median(scores)
            
            # Grade distribution
            grade_counts = Counter(a.grade for a in assessments)
            
            # Common weaknesses
            all_weaknesses = []
            for assessment in assessments:
                all_weaknesses.extend(assessment.weaknesses)
            common_weaknesses = Counter(all_weaknesses).most_common(5)
            
            # High improvement potential prompts
            high_potential = [a for a in assessments if a.estimated_improvement_potential > 0.6]
            
            # Metric analysis
            metric_averages = {}
            for metric_name in self.metric_weights.keys():
                metric_scores = []
                for assessment in assessments:
                    for metric in assessment.metrics:
                        if metric.metric_name == metric_name:
                            metric_scores.append(metric.score)
                
                if metric_scores:
                    metric_averages[metric_name] = {
                        'average': statistics.mean(metric_scores),
                        'lowest': min(metric_scores),
                        'highest': max(metric_scores)
                    }
            
            return {
                'summary': {
                    'total_prompts_assessed': len(assessments),
                    'average_quality_score': round(avg_score, 1),
                    'median_quality_score': round(median_score, 1),
                    'score_distribution': {
                        'excellent': len([s for s in scores if s >= 90]),
                        'good': len([s for s in scores if 80 <= s < 90]),
                        'fair': len([s for s in scores if 60 <= s < 80]),
                        'poor': len([s for s in scores if s < 60])
                    }
                },
                'grade_distribution': dict(grade_counts),
                'common_weaknesses': [
                    {'weakness': weakness, 'frequency': count}
                    for weakness, count in common_weaknesses
                ],
                'improvement_opportunities': {
                    'high_potential_prompts': len(high_potential),
                    'avg_improvement_potential': round(
                        statistics.mean([a.estimated_improvement_potential for a in assessments]), 2
                    ),
                    'top_candidates': [
                        {
                            'prompt_id': a.prompt_id,
                            'current_score': round(a.overall_score, 1),
                            'improvement_potential': round(a.estimated_improvement_potential, 2),
                            'priority': a.optimization_priority
                        }
                        for a in sorted(assessments, key=lambda x: x.estimated_improvement_potential, reverse=True)[:5]
                    ]
                },
                'metric_analysis': metric_averages,
                'recommendations': self._generate_global_recommendations(assessments)
            }
            
        except Exception as e:
            logger.error(f"Error generating quality insights: {e}")
            return {}
    
    def _assess_clarity_specificity(self, prompt_text: str) -> QualityMetric:
        """Assess clarity and specificity of the prompt."""
        try:
            score = 50.0  # Base score
            recommendations = []
            evidence = {}
            
            # Check for specific instructions
            specific_patterns = 0
            for pattern in self.quality_indicators['positive_patterns']:
                matches = len(re.findall(pattern, prompt_text, re.IGNORECASE))
                specific_patterns += matches
            
            # Bonus for specificity indicators
            score += min(30, specific_patterns * 5)
            evidence['positive_indicators'] = specific_patterns
            
            # Check for vague language
            vague_patterns = 0
            for pattern in self.quality_indicators['negative_patterns']:
                matches = len(re.findall(pattern, prompt_text, re.IGNORECASE))
                vague_patterns += matches
            
            # Penalty for vague language
            score -= min(20, vague_patterns * 10)
            evidence['negative_indicators'] = vague_patterns
            
            # Check for examples or format specifications
            has_examples = bool(re.search(r'\b(example|format|template|like this)\b', prompt_text, re.IGNORECASE))
            if has_examples:
                score += 15
                evidence['has_examples'] = True
            else:
                recommendations.append("Add specific examples or format templates")
                evidence['has_examples'] = False
            
            # Check prompt length (too short might lack detail)
            word_count = len(prompt_text.split())
            if word_count < 10:
                score -= 15
                recommendations.append("Consider adding more specific details and instructions")
            elif word_count > 200:
                recommendations.append("Consider breaking down into more concise instructions")
            
            evidence['word_count'] = word_count
            
            # Add recommendations based on score
            if score < 60:
                recommendations.extend([
                    "Use more specific and concrete language",
                    "Define clear success criteria",
                    "Provide detailed context and background"
                ])
            
            return QualityMetric(
                metric_name='clarity_specificity',
                score=max(0, min(100, score)),
                weight=self.metric_weights['clarity_specificity'],
                description='Measures how clear, specific, and unambiguous the prompt is',
                recommendations=recommendations,
                evidence=evidence
            )
            
        except Exception as e:
            logger.error(f"Error assessing clarity/specificity: {e}")
            return QualityMetric(
                metric_name='clarity_specificity',
                score=50.0,
                weight=self.metric_weights['clarity_specificity'],
                description='Error in assessment',
                recommendations=['Review prompt for clarity issues'],
                evidence={'error': str(e)}
            )
    
    def _assess_structure_organization(self, prompt_text: str) -> QualityMetric:
        """Assess structure and organization of the prompt."""
        try:
            score = 50.0
            recommendations = []
            evidence = {}
            
            # Check for structural keywords
            structure_found = 0
            for keyword in self.quality_indicators['structure_keywords']:
                if keyword.lower() in prompt_text.lower():
                    structure_found += 1
            
            score += min(25, structure_found * 5)
            evidence['structure_keywords_found'] = structure_found
            
            # Check for numbered/bulleted lists
            has_lists = bool(re.search(r'(\n\s*[\d\-\*\+]|\n\s*\([a-zA-Z0-9]\))', prompt_text))
            if has_lists:
                score += 15
                evidence['has_lists'] = True
            else:
                recommendations.append("Consider using numbered or bulleted lists for complex instructions")
                evidence['has_lists'] = False
            
            # Check for paragraph breaks
            paragraph_count = len([p for p in prompt_text.split('\n\n') if p.strip()])
            if paragraph_count > 1:
                score += 10
                evidence['paragraph_count'] = paragraph_count
            else:
                recommendations.append("Break long instructions into logical paragraphs")
                evidence['paragraph_count'] = paragraph_count
            
            # Check for section headers or separators
            has_headers = bool(re.search(r'(^|\n)#{1,6}\s+\w+|^[A-Z\s]+:|\n[A-Z\s]+:', prompt_text, re.MULTILINE))
            if has_headers:
                score += 10
                evidence['has_headers'] = True
            
            # Penalty for wall of text (no structure)
            if len(prompt_text) > 200 and '\n' not in prompt_text:
                score -= 20
                recommendations.append("Break up large blocks of text with line breaks and structure")
            
            if score < 60:
                recommendations.extend([
                    "Add clear section headers (Role, Task, Context, etc.)",
                    "Use consistent formatting throughout",
                    "Organize instructions in logical sequence"
                ])
            
            return QualityMetric(
                metric_name='structure_organization',
                score=max(0, min(100, score)),
                weight=self.metric_weights['structure_organization'],
                description='Measures how well-organized and structured the prompt is',
                recommendations=recommendations,
                evidence=evidence
            )
            
        except Exception as e:
            logger.error(f"Error assessing structure/organization: {e}")
            return QualityMetric(
                metric_name='structure_organization',
                score=50.0,
                weight=self.metric_weights['structure_organization'],
                description='Error in assessment',
                recommendations=['Review prompt structure'],
                evidence={'error': str(e)}
            )
    
    def _assess_performance_consistency(self, performance_data: Dict[str, Any]) -> QualityMetric:
        """Assess performance consistency based on execution data."""
        try:
            score = 50.0
            recommendations = []
            evidence = performance_data.copy()
            
            # Success rate scoring
            success_rate = performance_data.get('success_rate', 0.5)
            if success_rate >= self.performance_thresholds['excellent_success_rate']:
                score += 30
            elif success_rate >= self.performance_thresholds['good_success_rate']:
                score += 20
            else:
                score -= 10
                recommendations.append(f"Improve success rate (currently {success_rate:.1%})")
            
            # Latency scoring
            avg_latency = performance_data.get('avg_latency_ms', 3000)
            if avg_latency <= self.performance_thresholds['excellent_latency_ms']:
                score += 20
            elif avg_latency <= self.performance_thresholds['good_latency_ms']:
                score += 10
            else:
                score -= 10
                recommendations.append(f"Optimize for faster response time (currently {avg_latency:.0f}ms)")
            
            # Cost efficiency scoring
            avg_cost = performance_data.get('avg_cost_usd', 0.1)
            if avg_cost <= self.performance_thresholds['excellent_cost_usd']:
                score += 20
            elif avg_cost <= self.performance_thresholds['good_cost_usd']:
                score += 10
            else:
                recommendations.append(f"Optimize cost efficiency (currently ${avg_cost:.3f} per request)")
            
            # Consistency scoring (low variance is good)
            p95_latency = performance_data.get('p95_latency_ms', avg_latency * 1.5)
            latency_consistency = avg_latency / max(p95_latency, 1)  # Higher is more consistent
            if latency_consistency > 0.8:
                score += 10
            elif latency_consistency < 0.5:
                score -= 10
                recommendations.append("Improve response time consistency")
            
            if score < 60:
                recommendations.extend([
                    "Test prompt variations to improve reliability",
                    "Add error handling instructions",
                    "Consider model parameter optimization"
                ])
            
            return QualityMetric(
                metric_name='performance_consistency',
                score=max(0, min(100, score)),
                weight=self.metric_weights['performance_consistency'],
                description='Measures reliability and consistency of prompt execution',
                recommendations=recommendations,
                evidence=evidence
            )
            
        except Exception as e:
            logger.error(f"Error assessing performance consistency: {e}")
            return QualityMetric(
                metric_name='performance_consistency',
                score=50.0,
                weight=self.metric_weights['performance_consistency'],
                description='Error in assessment',
                recommendations=['Review performance data'],
                evidence={'error': str(e)}
            )
    
    def _assess_token_efficiency(self, prompt_text: str) -> QualityMetric:
        """Assess token efficiency of the prompt."""
        try:
            score = 70.0  # Start with good base score
            recommendations = []
            evidence = {}
            
            # Estimate token count (rough approximation: 1 token ≈ 4 characters)
            estimated_tokens = len(prompt_text) // 4
            evidence['estimated_tokens'] = estimated_tokens
            
            # Scoring based on length efficiency
            if estimated_tokens <= 100:  # Very concise
                score += 20
            elif estimated_tokens <= 300:  # Reasonable length
                score += 10
            elif estimated_tokens > 1000:  # Very long
                score -= 20
                recommendations.append("Consider reducing prompt length for better efficiency")
            
            # Check for redundancy
            sentences = prompt_text.split('.')
            unique_sentences = set(s.strip().lower() for s in sentences if s.strip())
            redundancy_ratio = len(sentences) / max(len(unique_sentences), 1)
            
            if redundancy_ratio > 1.5:  # High redundancy
                score -= 15
                recommendations.append("Remove redundant instructions and repetitive content")
            
            evidence['redundancy_ratio'] = redundancy_ratio
            
            # Check for verbose patterns
            verbose_patterns = [
                r'\bplease\s+',
                r'\bkindly\s+',
                r'\bi\s+would\s+like\s+you\s+to\b',
                r'\bif\s+you\s+could\b',
                r'\bwould\s+you\s+be\s+able\s+to\b'
            ]
            
            verbose_count = 0
            for pattern in verbose_patterns:
                verbose_count += len(re.findall(pattern, prompt_text, re.IGNORECASE))
            
            if verbose_count > 0:
                score -= min(10, verbose_count * 2)
                recommendations.append("Use more direct and concise language")
            
            evidence['verbose_expressions'] = verbose_count
            
            # Bonus for efficient instruction patterns
            efficient_patterns = [
                r'^(create|generate|analyze|summarize|list|identify)',
                r'\bin\s+format:',
                r'\busing\s+the\s+following\s+template:'
            ]
            
            efficient_count = 0
            for pattern in efficient_patterns:
                if re.search(pattern, prompt_text, re.IGNORECASE):
                    efficient_count += 1
            
            score += efficient_count * 5
            evidence['efficient_patterns'] = efficient_count
            
            if score < 60:
                recommendations.extend([
                    "Prioritize essential instructions only",
                    "Use bullet points instead of prose",
                    "Combine related instructions"
                ])
            
            return QualityMetric(
                metric_name='token_efficiency',
                score=max(0, min(100, score)),
                weight=self.metric_weights['token_efficiency'],
                description='Measures how efficiently the prompt uses tokens',
                recommendations=recommendations,
                evidence=evidence
            )
            
        except Exception as e:
            logger.error(f"Error assessing token efficiency: {e}")
            return QualityMetric(
                metric_name='token_efficiency',
                score=70.0,
                weight=self.metric_weights['token_efficiency'],
                description='Error in assessment',
                recommendations=['Review prompt length'],
                evidence={'error': str(e)}
            )
    
    def _assess_error_resilience(self, prompt_text: str) -> QualityMetric:
        """Assess error resilience and robustness of the prompt."""
        try:
            score = 60.0  # Base score
            recommendations = []
            evidence = {}
            
            # Check for error handling instructions
            error_handling_patterns = [
                r'\bif\s+(uncertain|unsure|unclear|unable)\b',
                r'\bwhen\s+in\s+doubt\b',
                r'\bif\s+you\s+don.?t\s+know\b',
                r'\berror\s+(handling|case|condition)\b',
                r'\bfallback\b',
                r'\bdefault\s+(to|response|behavior)\b'
            ]
            
            error_handling_found = 0
            for pattern in error_handling_patterns:
                if re.search(pattern, prompt_text, re.IGNORECASE):
                    error_handling_found += 1
            
            score += min(20, error_handling_found * 7)
            evidence['error_handling_instructions'] = error_handling_found
            
            if error_handling_found == 0:
                recommendations.append("Add instructions for handling uncertain or ambiguous cases")
            
            # Check for constraint specifications
            constraint_patterns = [
                r'\bmust\s+(not\s+)?',
                r'\brequired?\b',
                r'\bmandatory\b',
                r'\bdo\s+not\b',
                r'\bavoid\b',
                r'\bexclude\b',
                r'\blimit(ed)?\s+to\b'
            ]
            
            constraints_found = 0
            for pattern in constraint_patterns:
                constraints_found += len(re.findall(pattern, prompt_text, re.IGNORECASE))
            
            score += min(15, constraints_found * 3)
            evidence['constraint_specifications'] = constraints_found
            
            # Check for output format specifications
            format_patterns = [
                r'\bformat\s*:',
                r'\bstructure\s*:',
                r'\btemplate\s*:',
                r'\bexample\s+output\s*:',
                r'\bjson\b',
                r'\bxml\b',
                r'\bmarkdown\b'
            ]
            
            format_specs = 0
            for pattern in format_patterns:
                if re.search(pattern, prompt_text, re.IGNORECASE):
                    format_specs += 1
            
            score += min(10, format_specs * 5)
            evidence['format_specifications'] = format_specs
            
            # Check for validation instructions
            validation_patterns = [
                r'\bvalidate\b',
                r'\bcheck\s+(for|that)\b',
                r'\bensure\s+that\b',
                r'\bverify\b',
                r'\bdouble[\-\s]?check\b'
            ]
            
            validation_found = 0
            for pattern in validation_patterns:
                validation_found += len(re.findall(pattern, prompt_text, re.IGNORECASE))
            
            score += min(10, validation_found * 3)
            evidence['validation_instructions'] = validation_found
            
            # Penalty for overly rigid instructions
            rigid_patterns = [
                r'\bexactly\s+as\s+shown\b',
                r'\bprecisely\b',
                r'\bword\s+for\s+word\b',
                r'\bverbatim\b'
            ]
            
            rigid_count = 0
            for pattern in rigid_patterns:
                rigid_count += len(re.findall(pattern, prompt_text, re.IGNORECASE))
            
            if rigid_count > 2:
                score -= 10
                recommendations.append("Consider allowing some flexibility in responses")
            
            evidence['rigid_instructions'] = rigid_count
            
            if score < 60:
                recommendations.extend([
                    "Add fallback instructions for edge cases",
                    "Specify clear output constraints",
                    "Include validation guidelines"
                ])
            
            return QualityMetric(
                metric_name='error_resilience',
                score=max(0, min(100, score)),
                weight=self.metric_weights['error_resilience'],
                description='Measures robustness and error-handling capability',
                recommendations=recommendations,
                evidence=evidence
            )
            
        except Exception as e:
            logger.error(f"Error assessing error resilience: {e}")
            return QualityMetric(
                metric_name='error_resilience',
                score=60.0,
                weight=self.metric_weights['error_resilience'],
                description='Error in assessment',
                recommendations=['Review error handling'],
                evidence={'error': str(e)}
            )
    
    def _assess_context_appropriateness(self, prompt_text: str) -> QualityMetric:
        """Assess context appropriateness and domain relevance."""
        try:
            score = 70.0  # Good base score
            recommendations = []
            evidence = {}
            
            # Check for context setting
            context_patterns = [
                r'\bcontext\s*:',
                r'\bbackground\s*:',
                r'\bscenario\s*:',
                r'\bsituation\s*:',
                r'\byou\s+are\s+a\b',
                r'\brole\s*:',
                r'\bacting\s+as\b'
            ]
            
            context_setting = 0
            for pattern in context_patterns:
                if re.search(pattern, prompt_text, re.IGNORECASE):
                    context_setting += 1
            
            if context_setting > 0:
                score += 15
                evidence['has_context_setting'] = True
            else:
                score -= 10
                recommendations.append("Add context or role definition to improve relevance")
                evidence['has_context_setting'] = False
            
            # Check for domain-specific language
            word_count = len(prompt_text.split())
            unique_words = len(set(prompt_text.lower().split()))
            vocabulary_diversity = unique_words / max(word_count, 1)
            
            if vocabulary_diversity > 0.7:  # High diversity suggests domain expertise
                score += 10
            elif vocabulary_diversity < 0.4:  # Low diversity might indicate generic language
                score -= 5
                recommendations.append("Use more specific domain terminology")
            
            evidence['vocabulary_diversity'] = vocabulary_diversity
            
            # Check for professional tone
            professional_indicators = [
                r'\banalyze\b',
                r'\bevaluate\b',
                r'\bassess\b',
                r'\bdetermine\b',
                r'\bimplement\b',
                r'\boptimize\b',
                r'\bconsider\b'
            ]
            
            professional_count = 0
            for pattern in professional_indicators:
                professional_count += len(re.findall(pattern, prompt_text, re.IGNORECASE))
            
            score += min(10, professional_count * 2)
            evidence['professional_language'] = professional_count
            
            # Check for inappropriate casual language
            casual_patterns = [
                r'\bhey\b',
                r'\bguys?\b',
                r'\bthanks?\b',
                r'\bawesome\b',
                r'\bcool\b',
                r'\bstuff\b'
            ]
            
            casual_count = 0
            for pattern in casual_patterns:
                casual_count += len(re.findall(pattern, prompt_text, re.IGNORECASE))
            
            if casual_count > 0:
                score -= min(15, casual_count * 5)
                recommendations.append("Use more professional and formal language")
            
            evidence['casual_language'] = casual_count
            
            if score < 60:
                recommendations.extend([
                    "Define clear role and context",
                    "Use appropriate domain terminology",
                    "Maintain consistent professional tone"
                ])
            
            return QualityMetric(
                metric_name='context_appropriateness',
                score=max(0, min(100, score)),
                weight=self.metric_weights['context_appropriateness'],
                description='Measures contextual relevance and appropriateness',
                recommendations=recommendations,
                evidence=evidence
            )
            
        except Exception as e:
            logger.error(f"Error assessing context appropriateness: {e}")
            return QualityMetric(
                metric_name='context_appropriateness',
                score=70.0,
                weight=self.metric_weights['context_appropriateness'],
                description='Error in assessment',
                recommendations=['Review context and tone'],
                evidence={'error': str(e)}
            )
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from numeric score."""
        if score >= 97:
            return 'A+'
        elif score >= 93:
            return 'A'
        elif score >= 90:
            return 'A-'
        elif score >= 87:
            return 'B+'
        elif score >= 83:
            return 'B'
        elif score >= 80:
            return 'B-'
        elif score >= 77:
            return 'C+'
        elif score >= 73:
            return 'C'
        elif score >= 70:
            return 'C-'
        elif score >= 67:
            return 'D+'
        elif score >= 65:
            return 'D'
        else:
            return 'F'
    
    def _determine_optimization_priority(self, overall_score: float, metrics: List[QualityMetric]) -> str:
        """Determine optimization priority based on score and metrics."""
        if overall_score < 60:
            return 'high'
        elif overall_score < 80:
            # Check if there are any very low individual metrics
            low_metrics = [m for m in metrics if m.score < 40]
            if low_metrics:
                return 'high'
            else:
                return 'medium'
        else:
            return 'low'
    
    def _estimate_improvement_potential(self, metrics: List[QualityMetric]) -> float:
        """Estimate improvement potential (0-1) based on current metrics."""
        try:
            # Find the largest gaps in metrics
            improvement_scores = []
            
            for metric in metrics:
                # Calculate potential improvement (how much room for growth)
                max_possible_score = 100.0
                current_weighted_contribution = metric.score * metric.weight
                max_weighted_contribution = max_possible_score * metric.weight
                
                improvement_potential = (max_weighted_contribution - current_weighted_contribution) / max_weighted_contribution
                improvement_scores.append(improvement_potential)
            
            # Average improvement potential
            avg_potential = statistics.mean(improvement_scores)
            
            # Bonus for having very low scores (easier to improve)
            low_score_bonus = len([m for m in metrics if m.score < 50]) * 0.1
            
            return min(1.0, avg_potential + low_score_bonus)
            
        except Exception as e:
            logger.error(f"Error estimating improvement potential: {e}")
            return 0.3  # Default moderate potential
    
    def _create_empty_assessment(self, prompt_id: str) -> PromptQualityAssessment:
        """Create an empty/error assessment."""
        return PromptQualityAssessment(
            prompt_id=prompt_id,
            prompt_text='Unable to assess',
            overall_score=0.0,
            grade='F',
            metrics=[],
            strengths=[],
            weaknesses=['Unable to perform assessment'],
            optimization_priority='high',
            estimated_improvement_potential=1.0
        )
    
    def _generate_global_recommendations(self, assessments: List[PromptQualityAssessment]) -> List[str]:
        """Generate global recommendations based on all assessments."""
        try:
            recommendations = []
            
            # Count common issues
            all_recommendations = []
            for assessment in assessments:
                for metric in assessment.metrics:
                    all_recommendations.extend(metric.recommendations)
            
            common_issues = Counter(all_recommendations)
            
            # Generate global recommendations based on common patterns
            if len(assessments) > 0:
                avg_score = statistics.mean([a.overall_score for a in assessments])
                
                if avg_score < 60:
                    recommendations.append("Focus on fundamental prompt quality improvements across all prompts")
                
                # Add most common specific recommendations
                top_issues = common_issues.most_common(3)
                for issue, count in top_issues:
                    if count > len(assessments) * 0.3:  # If affecting >30% of prompts
                        recommendations.append(f"Common issue: {issue} (affects {count} prompts)")
            
            return recommendations[:5]  # Top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating global recommendations: {e}")
            return ["Review prompts for common quality issues"]