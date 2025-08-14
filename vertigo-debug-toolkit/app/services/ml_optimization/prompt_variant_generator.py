"""
Prompt Variant Generator - ML-Driven Prompt Optimization
Generates intelligent prompt variations based on ML performance analysis, quality assessments,
and proven optimization patterns.
"""

import os
import logging
import re
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import hashlib

from app.models import Prompt, PromptPerformanceAnalysis, PromptQualityAssessment
from .ml_service import ml_optimization_service
from .quality_scorer import PromptQualityScorer

logger = logging.getLogger(__name__)


@dataclass
class PromptVariant:
    """Generated prompt variant."""
    variant_id: str
    name: str
    content: str
    generation_method: str
    generation_context: Dict[str, Any]
    expected_improvements: List[str]
    confidence_score: float
    is_control: bool = False


@dataclass
class VariantGenerationConfig:
    """Configuration for variant generation."""
    base_prompt: str
    optimization_targets: List[str]  # ['latency', 'cost', 'accuracy', 'clarity']
    variation_types: List[str]  # ['structure', 'length', 'tone', 'examples']
    num_variants: int = 3
    include_control: bool = True
    creativity_level: float = 0.7  # 0-1, higher = more creative variations
    preserve_intent: bool = True


@dataclass
class OptimizationPattern:
    """Optimization pattern for prompt generation."""
    pattern_type: str
    pattern_name: str
    description: str
    transformation_rules: List[Dict[str, Any]]
    expected_impact: Dict[str, float]
    confidence: float
    applicability_criteria: List[str]


class PromptVariantGenerator:
    """
    ML-driven prompt variant generator for A/B testing.
    
    Creates intelligent prompt variations based on:
    - Historical performance data
    - Quality assessment insights
    - Proven optimization patterns
    - ML-generated recommendations
    """
    
    def __init__(self):
        """Initialize the prompt variant generator."""
        self.logger = logging.getLogger(__name__)
        self.ml_service = ml_optimization_service
        self.quality_scorer = PromptQualityScorer()
        
        # Load optimization patterns
        self.optimization_patterns = self._load_optimization_patterns()
        
        # Template variations
        self.structure_templates = self._load_structure_templates()
        self.tone_variations = self._load_tone_variations()
        
        self.logger.info("PromptVariantGenerator initialized with optimization patterns")
    
    def generate_variants(self, config: VariantGenerationConfig) -> List[PromptVariant]:
        """
        Generate prompt variants based on configuration.
        
        Args:
            config: Variant generation configuration
            
        Returns:
            List of generated variants
        """
        try:
            variants = []
            
            # Add control variant if requested
            if config.include_control:
                control_variant = PromptVariant(
                    variant_id="control",
                    name="Control (Original)",
                    content=config.base_prompt,
                    generation_method="control",
                    generation_context={'base_prompt': config.base_prompt},
                    expected_improvements=[],
                    confidence_score=1.0,
                    is_control=True
                )
                variants.append(control_variant)
            
            # Analyze base prompt for optimization opportunities
            analysis = self._analyze_prompt_for_optimization(config.base_prompt, config.optimization_targets)
            
            # Generate variants based on different strategies
            generation_strategies = []
            
            if 'structure' in config.variation_types:
                generation_strategies.append(self._generate_structure_variants)
            if 'length' in config.variation_types:
                generation_strategies.append(self._generate_length_variants)
            if 'tone' in config.variation_types:
                generation_strategies.append(self._generate_tone_variants)
            if 'examples' in config.variation_types:
                generation_strategies.append(self._generate_example_variants)
            
            # Generate variants using each strategy
            variant_count = 1 if config.include_control else 0
            variants_per_strategy = max(1, (config.num_variants - variant_count) // len(generation_strategies))
            
            for strategy in generation_strategies:
                strategy_variants = strategy(
                    base_prompt=config.base_prompt,
                    analysis=analysis,
                    optimization_targets=config.optimization_targets,
                    creativity_level=config.creativity_level,
                    count=variants_per_strategy
                )
                variants.extend(strategy_variants)
                
                if len(variants) >= config.num_variants:
                    break
            
            # ML-enhanced variants if we need more
            if len(variants) < config.num_variants:
                ml_variants = self._generate_ml_enhanced_variants(
                    base_prompt=config.base_prompt,
                    analysis=analysis,
                    optimization_targets=config.optimization_targets,
                    count=config.num_variants - len(variants)
                )
                variants.extend(ml_variants)
            
            # Limit to requested number of variants
            variants = variants[:config.num_variants]
            
            # Score and rank variants
            variants = self._score_and_rank_variants(variants, config.optimization_targets)
            
            self.logger.info(f"Generated {len(variants)} prompt variants")
            return variants
            
        except Exception as e:
            self.logger.error(f"Error generating variants: {e}")
            return []
    
    def generate_from_performance_insights(self, prompt_id: str, days_back: int = 30) -> List[PromptVariant]:
        """
        Generate variants based on ML performance insights.
        
        Args:
            prompt_id: Prompt to optimize
            days_back: Days of performance data to analyze
            
        Returns:
            Performance-optimized variants
        """
        try:
            # Get prompt content
            prompt = Prompt.query.filter_by(id=prompt_id).first()
            if not prompt:
                raise ValueError(f"Prompt {prompt_id} not found")
            
            # Get ML analysis
            analysis = self.ml_service.analyze_specific_prompt(prompt_id, prompt.content, days_back)
            
            performance_data = analysis.get('performance_analysis')
            quality_assessment = analysis.get('quality_assessment')
            recommendations = analysis.get('recommendations', [])
            
            if not performance_data:
                return []
            
            # Identify optimization opportunities
            optimization_targets = []
            if performance_data['avg_latency_ms'] > 3000:
                optimization_targets.append('latency')
            if performance_data['avg_cost_usd'] > 0.20:
                optimization_targets.append('cost')
            if performance_data['success_rate'] < 0.90:
                optimization_targets.append('reliability')
            
            if quality_assessment and quality_assessment['overall_score'] < 70:
                optimization_targets.append('clarity')
            
            # Generate configuration
            config = VariantGenerationConfig(
                base_prompt=prompt.content,
                optimization_targets=optimization_targets,
                variation_types=['structure', 'length', 'tone'],
                num_variants=4,
                creativity_level=0.6
            )
            
            # Generate variants with performance context
            variants = self.generate_variants(config)
            
            # Enhance with performance-specific improvements
            for variant in variants:
                variant.generation_context['performance_data'] = performance_data
                variant.generation_context['optimization_targets'] = optimization_targets
                variant.generation_context['recommendations'] = [r['title'] for r in recommendations]
            
            return variants
            
        except Exception as e:
            self.logger.error(f"Error generating performance-based variants: {e}")
            return []
    
    def generate_from_quality_insights(self, prompt_text: str, quality_assessment: Optional[Dict] = None) -> List[PromptVariant]:
        """
        Generate variants based on quality assessment insights.
        
        Args:
            prompt_text: Prompt to optimize
            quality_assessment: Optional existing quality assessment
            
        Returns:
            Quality-optimized variants
        """
        try:
            # Get quality assessment if not provided
            if not quality_assessment:
                assessment = self.quality_scorer.assess_prompt_quality(prompt_text)
                quality_assessment = asdict(assessment) if assessment else {}
            
            # Identify quality improvement opportunities
            optimization_targets = ['clarity']
            
            if quality_assessment.get('structure_organization_score', 0) < 70:
                optimization_targets.append('structure')
            if quality_assessment.get('token_efficiency_score', 0) < 70:
                optimization_targets.append('length')
            if quality_assessment.get('clarity_specificity_score', 0) < 70:
                optimization_targets.append('specificity')
            
            config = VariantGenerationConfig(
                base_prompt=prompt_text,
                optimization_targets=optimization_targets,
                variation_types=['structure', 'tone', 'examples'],
                num_variants=3,
                creativity_level=0.5
            )
            
            variants = self.generate_variants(config)
            
            # Enhance with quality context
            for variant in variants:
                variant.generation_context['quality_assessment'] = quality_assessment
                variant.generation_context['quality_targets'] = optimization_targets
            
            return variants
            
        except Exception as e:
            self.logger.error(f"Error generating quality-based variants: {e}")
            return []
    
    def _analyze_prompt_for_optimization(self, prompt: str, targets: List[str]) -> Dict[str, Any]:
        """Analyze prompt to identify optimization opportunities."""
        try:
            analysis = {
                'word_count': len(prompt.split()),
                'char_count': len(prompt),
                'sentence_count': len(re.split(r'[.!?]+', prompt)),
                'structure_type': self._identify_structure_type(prompt),
                'tone': self._identify_tone(prompt),
                'complexity': self._calculate_complexity(prompt),
                'optimization_opportunities': []
            }
            
            # Identify specific optimization opportunities
            if 'latency' in targets and analysis['word_count'] > 300:
                analysis['optimization_opportunities'].append('reduce_length')
            
            if 'clarity' in targets and analysis['complexity'] > 0.7:
                analysis['optimization_opportunities'].append('simplify_language')
            
            if 'cost' in targets and analysis['word_count'] > 200:
                analysis['optimization_opportunities'].append('optimize_token_usage')
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing prompt: {e}")
            return {}
    
    def _generate_structure_variants(self, base_prompt: str, analysis: Dict, 
                                   optimization_targets: List[str], creativity_level: float, 
                                   count: int) -> List[PromptVariant]:
        """Generate structure-based variants."""
        try:
            variants = []
            current_structure = analysis.get('structure_type', 'unstructured')
            
            # Select different structure templates
            available_templates = [t for t in self.structure_templates if t['name'] != current_structure]
            
            for i, template in enumerate(available_templates[:count]):
                transformed_prompt = self._apply_structure_template(base_prompt, template)
                
                variant = PromptVariant(
                    variant_id=f"structure_{template['name']}",
                    name=f"Structure: {template['display_name']}",
                    content=transformed_prompt,
                    generation_method="structure_transformation",
                    generation_context={
                        'template': template['name'],
                        'original_structure': current_structure,
                        'transformation_rules': template.get('rules', [])
                    },
                    expected_improvements=template.get('benefits', []),
                    confidence_score=min(0.9, creativity_level + 0.2)
                )
                variants.append(variant)
            
            return variants
            
        except Exception as e:
            self.logger.error(f"Error generating structure variants: {e}")
            return []
    
    def _generate_length_variants(self, base_prompt: str, analysis: Dict,
                                optimization_targets: List[str], creativity_level: float,
                                count: int) -> List[PromptVariant]:
        """Generate length-optimized variants."""
        try:
            variants = []
            current_length = analysis.get('word_count', 0)
            
            # Generate shorter and longer versions
            if 'latency' in optimization_targets or 'cost' in optimization_targets:
                # Shorter version
                short_prompt = self._shorten_prompt(base_prompt, target_reduction=0.3)
                variants.append(PromptVariant(
                    variant_id="length_short",
                    name="Concise Version",
                    content=short_prompt,
                    generation_method="length_optimization",
                    generation_context={
                        'optimization': 'shorten',
                        'original_length': current_length,
                        'target_reduction': 0.3
                    },
                    expected_improvements=['reduced_latency', 'reduced_cost'],
                    confidence_score=0.8
                ))
            
            # Ultra-concise version if needed
            if len(variants) < count and current_length > 150:
                ultra_short = self._shorten_prompt(base_prompt, target_reduction=0.5)
                variants.append(PromptVariant(
                    variant_id="length_ultra_short",
                    name="Ultra-Concise Version",
                    content=ultra_short,
                    generation_method="length_optimization",
                    generation_context={
                        'optimization': 'ultra_shorten',
                        'original_length': current_length,
                        'target_reduction': 0.5
                    },
                    expected_improvements=['minimal_latency', 'minimal_cost'],
                    confidence_score=0.7
                ))
            
            return variants[:count]
            
        except Exception as e:
            self.logger.error(f"Error generating length variants: {e}")
            return []
    
    def _generate_tone_variants(self, base_prompt: str, analysis: Dict,
                              optimization_targets: List[str], creativity_level: float,
                              count: int) -> List[PromptVariant]:
        """Generate tone-adjusted variants."""
        try:
            variants = []
            current_tone = analysis.get('tone', 'neutral')
            
            # Select different tones
            available_tones = [t for t in self.tone_variations if t['name'] != current_tone]
            
            for i, tone_config in enumerate(available_tones[:count]):
                adjusted_prompt = self._apply_tone_adjustment(base_prompt, tone_config)
                
                variant = PromptVariant(
                    variant_id=f"tone_{tone_config['name']}",
                    name=f"Tone: {tone_config['display_name']}",
                    content=adjusted_prompt,
                    generation_method="tone_adjustment",
                    generation_context={
                        'tone': tone_config['name'],
                        'original_tone': current_tone,
                        'adjustments': tone_config.get('adjustments', [])
                    },
                    expected_improvements=tone_config.get('benefits', []),
                    confidence_score=0.7 + creativity_level * 0.2
                )
                variants.append(variant)
            
            return variants
            
        except Exception as e:
            self.logger.error(f"Error generating tone variants: {e}")
            return []
    
    def _generate_example_variants(self, base_prompt: str, analysis: Dict,
                                 optimization_targets: List[str], creativity_level: float,
                                 count: int) -> List[PromptVariant]:
        """Generate variants with different example strategies."""
        try:
            variants = []
            
            # Add examples variant
            if not self._has_examples(base_prompt):
                with_examples = self._add_examples_to_prompt(base_prompt)
                variants.append(PromptVariant(
                    variant_id="examples_added",
                    name="With Examples",
                    content=with_examples,
                    generation_method="example_enhancement",
                    generation_context={
                        'modification': 'add_examples',
                        'example_count': 2
                    },
                    expected_improvements=['improved_clarity', 'better_understanding'],
                    confidence_score=0.8
                ))
            
            # Remove examples variant if they exist
            if self._has_examples(base_prompt) and len(variants) < count:
                without_examples = self._remove_examples_from_prompt(base_prompt)
                variants.append(PromptVariant(
                    variant_id="examples_removed",
                    name="Without Examples",
                    content=without_examples,
                    generation_method="example_simplification",
                    generation_context={
                        'modification': 'remove_examples'
                    },
                    expected_improvements=['reduced_length', 'faster_processing'],
                    confidence_score=0.6
                ))
            
            return variants[:count]
            
        except Exception as e:
            self.logger.error(f"Error generating example variants: {e}")
            return []
    
    def _generate_ml_enhanced_variants(self, base_prompt: str, analysis: Dict,
                                     optimization_targets: List[str], count: int) -> List[PromptVariant]:
        """Generate ML-enhanced variants using advanced patterns."""
        try:
            variants = []
            
            # Apply optimization patterns based on targets
            applicable_patterns = []
            for pattern in self.optimization_patterns:
                if any(criteria in optimization_targets for criteria in pattern.applicability_criteria):
                    applicable_patterns.append(pattern)
            
            # Sort by confidence and expected impact
            applicable_patterns.sort(key=lambda p: p.confidence, reverse=True)
            
            for i, pattern in enumerate(applicable_patterns[:count]):
                enhanced_prompt = self._apply_optimization_pattern(base_prompt, pattern)
                
                variant = PromptVariant(
                    variant_id=f"ml_enhanced_{pattern.pattern_type}",
                    name=f"ML Enhanced: {pattern.pattern_name}",
                    content=enhanced_prompt,
                    generation_method="ml_pattern_optimization",
                    generation_context={
                        'pattern': pattern.pattern_name,
                        'pattern_type': pattern.pattern_type,
                        'rules_applied': len(pattern.transformation_rules)
                    },
                    expected_improvements=[f"{k}_{v:.0%}" for k, v in pattern.expected_impact.items()],
                    confidence_score=pattern.confidence
                )
                variants.append(variant)
            
            return variants
            
        except Exception as e:
            self.logger.error(f"Error generating ML-enhanced variants: {e}")
            return []
    
    def _score_and_rank_variants(self, variants: List[PromptVariant], 
                               optimization_targets: List[str]) -> List[PromptVariant]:
        """Score and rank variants based on optimization targets."""
        try:
            for variant in variants:
                if variant.is_control:
                    continue
                
                # Calculate composite score based on expected improvements
                target_score = 0.0
                improvement_count = 0
                
                for improvement in variant.expected_improvements:
                    if any(target in improvement.lower() for target in optimization_targets):
                        target_score += 1.0
                        improvement_count += 1
                
                # Normalize score
                if improvement_count > 0:
                    target_score = target_score / improvement_count
                
                # Combine with confidence
                variant.confidence_score = (variant.confidence_score + target_score) / 2
            
            # Sort by confidence score (keeping control first if present)
            control_variants = [v for v in variants if v.is_control]
            other_variants = [v for v in variants if not v.is_control]
            other_variants.sort(key=lambda v: v.confidence_score, reverse=True)
            
            return control_variants + other_variants
            
        except Exception as e:
            self.logger.error(f"Error scoring variants: {e}")
            return variants
    
    def _load_optimization_patterns(self) -> List[OptimizationPattern]:
        """Load ML optimization patterns."""
        return [
            OptimizationPattern(
                pattern_type="conciseness",
                pattern_name="Remove Redundancy",
                description="Remove redundant phrases and unnecessary words",
                transformation_rules=[
                    {"type": "remove_redundant_phrases", "patterns": ["in order to", "please note that", "it should be noted"]},
                    {"type": "simplify_complex_sentences", "max_clause_count": 2},
                    {"type": "remove_filler_words", "words": ["very", "quite", "rather", "fairly"]}
                ],
                expected_impact={"latency": 0.15, "cost": 0.20},
                confidence=0.8,
                applicability_criteria=["latency", "cost"]
            ),
            OptimizationPattern(
                pattern_type="clarity",
                pattern_name="Improve Structure",
                description="Add clear structure and numbered steps",
                transformation_rules=[
                    {"type": "add_numbered_steps", "when": "contains_process"},
                    {"type": "add_section_headers", "when": "long_prompt"},
                    {"type": "group_related_instructions", "similarity_threshold": 0.7}
                ],
                expected_impact={"clarity": 0.25, "reliability": 0.10},
                confidence=0.85,
                applicability_criteria=["clarity", "reliability"]
            ),
            OptimizationPattern(
                pattern_type="specificity",
                pattern_name="Add Constraints",
                description="Add specific constraints and output format requirements",
                transformation_rules=[
                    {"type": "add_output_format", "when": "missing_format"},
                    {"type": "add_length_constraints", "when": "unbounded_output"},
                    {"type": "specify_edge_cases", "when": "ambiguous_requirements"}
                ],
                expected_impact={"reliability": 0.30, "clarity": 0.15},
                confidence=0.75,
                applicability_criteria=["reliability", "clarity"]
            )
        ]
    
    def _load_structure_templates(self) -> List[Dict[str, Any]]:
        """Load structure templates."""
        return [
            {
                "name": "step_by_step",
                "display_name": "Step-by-Step",
                "pattern": "1. {step1}\n2. {step2}\n3. {step3}",
                "benefits": ["improved_clarity", "better_reliability"],
                "rules": ["break_into_steps", "number_steps", "one_action_per_step"]
            },
            {
                "name": "context_instruction_example",
                "display_name": "Context-Instruction-Example",
                "pattern": "Context: {context}\n\nInstructions: {instructions}\n\nExample: {example}",
                "benefits": ["improved_understanding", "better_consistency"],
                "rules": ["separate_context", "clear_instructions", "provide_example"]
            },
            {
                "name": "constraint_based",
                "display_name": "Constraint-Based",
                "pattern": "Task: {task}\n\nConstraints:\n- {constraint1}\n- {constraint2}\n\nOutput format: {format}",
                "benefits": ["improved_reliability", "consistent_output"],
                "rules": ["define_task", "list_constraints", "specify_format"]
            }
        ]
    
    def _load_tone_variations(self) -> List[Dict[str, Any]]:
        """Load tone variation configurations."""
        return [
            {
                "name": "formal",
                "display_name": "Formal",
                "adjustments": ["remove_contractions", "use_passive_voice", "technical_language"],
                "benefits": ["professional_tone", "precise_language"]
            },
            {
                "name": "conversational",
                "display_name": "Conversational",
                "adjustments": ["add_contractions", "use_active_voice", "friendly_language"],
                "benefits": ["approachable_tone", "engaging_style"]
            },
            {
                "name": "direct",
                "display_name": "Direct",
                "adjustments": ["remove_qualifiers", "imperative_mood", "concise_language"],
                "benefits": ["clear_instructions", "reduced_ambiguity"]
            }
        ]
    
    # Implementation methods for transformations
    def _identify_structure_type(self, prompt: str) -> str:
        """Identify the current structure type of the prompt."""
        if re.search(r'\d+\.\s', prompt):
            return "numbered_list"
        elif re.search(r'[-*]\s', prompt):
            return "bullet_list"
        elif "Context:" in prompt and "Instructions:" in prompt:
            return "context_instruction_example"
        else:
            return "unstructured"
    
    def _identify_tone(self, prompt: str) -> str:
        """Identify the tone of the prompt."""
        formal_indicators = len(re.findall(r'\b(shall|ought|must|please)\b', prompt, re.IGNORECASE))
        casual_indicators = len(re.findall(r'\b(you\'re|don\'t|can\'t|let\'s)\b', prompt, re.IGNORECASE))
        
        if formal_indicators > casual_indicators:
            return "formal"
        elif casual_indicators > formal_indicators:
            return "conversational"
        else:
            return "neutral"
    
    def _calculate_complexity(self, prompt: str) -> float:
        """Calculate prompt complexity score (0-1)."""
        words = prompt.split()
        if not words:
            return 0.0
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Sentence length
        sentences = re.split(r'[.!?]+', prompt)
        avg_sentence_length = len(words) / max(1, len(sentences))
        
        # Complex word ratio (words > 6 characters)
        complex_words = sum(1 for word in words if len(word) > 6)
        complex_ratio = complex_words / len(words)
        
        # Normalize and combine scores
        complexity = min(1.0, (avg_word_length / 8 + avg_sentence_length / 20 + complex_ratio) / 3)
        return complexity
    
    def _apply_structure_template(self, prompt: str, template: Dict[str, Any]) -> str:
        """Apply a structure template to transform the prompt."""
        # Simplified implementation - in practice this would be more sophisticated
        if template['name'] == 'step_by_step':
            return self._convert_to_steps(prompt)
        elif template['name'] == 'context_instruction_example':
            return self._convert_to_cie_format(prompt)
        elif template['name'] == 'constraint_based':
            return self._convert_to_constraint_format(prompt)
        else:
            return prompt
    
    def _convert_to_steps(self, prompt: str) -> str:
        """Convert prompt to step-by-step format."""
        # Simple heuristic: split on periods and create steps
        sentences = [s.strip() for s in prompt.split('.') if s.strip()]
        if len(sentences) > 1:
            return '\n'.join([f"{i+1}. {s}." for i, s in enumerate(sentences[:5])])
        else:
            return f"1. {prompt}"
    
    def _convert_to_cie_format(self, prompt: str) -> str:
        """Convert to Context-Instruction-Example format."""
        # Simplified conversion
        return f"Instructions: {prompt}\n\nPlease follow the above instructions carefully."
    
    def _convert_to_constraint_format(self, prompt: str) -> str:
        """Convert to constraint-based format."""
        return f"Task: {prompt}\n\nConstraints:\n- Provide accurate information\n- Keep response concise\n\nOutput format: Clear, structured response"
    
    def _apply_tone_adjustment(self, prompt: str, tone_config: Dict[str, Any]) -> str:
        """Apply tone adjustments to the prompt."""
        adjusted = prompt
        
        for adjustment in tone_config.get('adjustments', []):
            if adjustment == 'remove_contractions':
                adjusted = re.sub(r"can't", "cannot", adjusted)
                adjusted = re.sub(r"don't", "do not", adjusted)
                adjusted = re.sub(r"won't", "will not", adjusted)
            elif adjustment == 'add_contractions':
                adjusted = re.sub(r"cannot", "can't", adjusted)
                adjusted = re.sub(r"do not", "don't", adjusted)
                adjusted = re.sub(r"will not", "won't", adjusted)
            elif adjustment == 'remove_qualifiers':
                adjusted = re.sub(r'\b(perhaps|maybe|possibly|might)\s+', '', adjusted, flags=re.IGNORECASE)
        
        return adjusted
    
    def _shorten_prompt(self, prompt: str, target_reduction: float = 0.3) -> str:
        """Shorten prompt by target reduction percentage."""
        words = prompt.split()
        target_length = int(len(words) * (1 - target_reduction))
        
        if target_length >= len(words):
            return prompt
        
        # Remove filler words first
        filler_words = {'very', 'quite', 'rather', 'fairly', 'pretty', 'really', 'actually', 'basically'}
        filtered_words = [w for w in words if w.lower() not in filler_words]
        
        if len(filtered_words) <= target_length:
            return ' '.join(filtered_words)
        
        # Keep most important words (simple heuristic: longer words and early position)
        word_scores = []
        for i, word in enumerate(filtered_words):
            position_score = 1.0 / (i + 1)  # Earlier words more important
            length_score = len(word) / 10  # Longer words more important
            word_scores.append((position_score + length_score, word))
        
        # Sort by score and take top words
        word_scores.sort(reverse=True)
        shortened_words = [word for _, word in word_scores[:target_length]]
        
        # Try to maintain sentence structure
        result = ' '.join(shortened_words)
        return result
    
    def _has_examples(self, prompt: str) -> bool:
        """Check if prompt contains examples."""
        example_patterns = [
            r'example:', r'for example', r'such as', r'like this:',
            r'input:', r'output:', r'sample:'
        ]
        return any(re.search(pattern, prompt, re.IGNORECASE) for pattern in example_patterns)
    
    def _add_examples_to_prompt(self, prompt: str) -> str:
        """Add examples to the prompt."""
        return f"{prompt}\n\nExample:\nInput: [sample input]\nOutput: [expected output format]"
    
    def _remove_examples_from_prompt(self, prompt: str) -> str:
        """Remove examples from the prompt."""
        # Remove common example patterns
        cleaned = re.sub(r'\n\s*Example:.*?(?=\n\s*[A-Z]|\Z)', '', prompt, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r'\n\s*Input:.*?Output:.*?(?=\n|\Z)', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        return cleaned.strip()
    
    def _apply_optimization_pattern(self, prompt: str, pattern: OptimizationPattern) -> str:
        """Apply an optimization pattern to the prompt."""
        optimized = prompt
        
        for rule in pattern.transformation_rules:
            if rule['type'] == 'remove_redundant_phrases':
                for phrase in rule.get('patterns', []):
                    optimized = re.sub(rf'\b{re.escape(phrase)}\b', '', optimized, flags=re.IGNORECASE)
            elif rule['type'] == 'remove_filler_words':
                for word in rule.get('words', []):
                    optimized = re.sub(rf'\b{re.escape(word)}\b\s*', '', optimized, flags=re.IGNORECASE)
            elif rule['type'] == 'add_output_format':
                if 'format' not in optimized.lower():
                    optimized += '\n\nOutput format: [Specify desired format]'
        
        return optimized.strip()


# Global service instance
prompt_variant_generator = PromptVariantGenerator()