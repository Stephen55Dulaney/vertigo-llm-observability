"""
Semantic search service for intelligent prompt discovery.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import re

from app.models import Prompt, Trace, Cost, db
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

class SemanticPromptSearch:
    """
    Semantic search service for finding relevant prompts based on query similarity.
    Uses sentence-transformers for embedding generation and cosine similarity for matching.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the semantic search service.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.prompt_embeddings = {}
        self.prompt_cache = {}
        self.last_cache_update = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the sentence transformer model."""
        try:
            logger.info(f"Loading semantic search model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Semantic search model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load semantic search model: {e}")
            raise
    
    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed (every 5 minutes)."""
        if not self.last_cache_update:
            return True
        return (datetime.utcnow() - self.last_cache_update).total_seconds() > 300
    
    def _build_searchable_text(self, prompt: Prompt) -> str:
        """
        Build searchable text from prompt data.
        
        Args:
            prompt: Prompt object from database
            
        Returns:
            Combined text for semantic search
        """
        searchable_parts = []
        
        # Add prompt name and type
        searchable_parts.append(prompt.name)
        searchable_parts.append(prompt.prompt_type.replace('_', ' '))
        
        # Add tags
        if prompt.tags:
            searchable_parts.extend(prompt.tags)
        
        # Extract key phrases from content (first 500 chars)
        content_preview = prompt.content[:500]
        # Remove JSON formatting and placeholder syntax
        cleaned_content = re.sub(r'[{}]', '', content_preview)
        cleaned_content = re.sub(r'\n+', ' ', cleaned_content)
        searchable_parts.append(cleaned_content)
        
        return ' '.join(searchable_parts)
    
    def _get_prompt_performance_metrics(self, prompt_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get performance metrics for a prompt.
        
        Args:
            prompt_id: ID of the prompt
            days: Number of days to look back
            
        Returns:
            Dictionary of performance metrics
        """
        try:
            # Get time range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get traces for this prompt in the time range
            traces = Trace.query.filter(
                and_(
                    Trace.prompt_id == prompt_id,
                    Trace.start_time >= start_date,
                    Trace.start_time <= end_date
                )
            ).all()
            
            if not traces:
                return {
                    'success_rate': 0.0,
                    'avg_response_time': 0.0,
                    'usage_count': 0,
                    'last_used': None,
                    'total_cost': 0.0
                }
            
            # Calculate metrics
            total_traces = len(traces)
            success_traces = len([t for t in traces if t.status == 'success'])
            success_rate = (success_traces / total_traces) * 100 if total_traces > 0 else 0
            
            # Average response time
            response_times = [t.duration_ms for t in traces if t.duration_ms is not None]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            avg_response_time = avg_response_time / 1000  # Convert to seconds
            
            # Last used
            last_used = max(t.start_time for t in traces) if traces else None
            
            # Total cost
            trace_ids = [t.id for t in traces]
            total_cost = db.session.query(func.sum(Cost.cost_usd)).filter(
                Cost.trace_id.in_(trace_ids)
            ).scalar() or 0
            
            return {
                'success_rate': round(success_rate, 1),
                'avg_response_time': round(avg_response_time, 2),
                'usage_count': total_traces,
                'last_used': self._format_last_used(last_used),
                'total_cost': float(total_cost)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics for prompt {prompt_id}: {e}")
            return {
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'usage_count': 0,
                'last_used': None,
                'total_cost': 0.0
            }
    
    def _format_last_used(self, last_used: Optional[datetime]) -> Optional[str]:
        """Format last used timestamp for display."""
        if not last_used:
            return None
            
        now = datetime.utcnow()
        diff = now - last_used
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    
    def _generate_match_reasons(self, query: str, prompt: Prompt, similarity_score: float) -> List[str]:
        """
        Generate human-readable reasons why a prompt matched the query.
        
        Args:
            query: Search query
            prompt: Matched prompt
            similarity_score: Similarity score
            
        Returns:
            List of match reasons
        """
        reasons = []
        
        # Check for direct name matches
        query_words = query.lower().split()
        prompt_name_words = prompt.name.lower().split()
        
        if any(word in prompt_name_words for word in query_words):
            reasons.append("Matches prompt name")
        
        # Check for type matches
        if prompt.prompt_type.replace('_', ' ').lower() in query.lower():
            reasons.append("Matches prompt type")
        
        # Check for tag matches
        if prompt.tags:
            for tag in prompt.tags:
                if tag.lower() in query.lower():
                    reasons.append(f"Tagged as '{tag}'")
        
        # Check content keywords
        content_lower = prompt.content.lower()
        for word in query_words:
            if len(word) > 3 and word in content_lower:
                reasons.append(f"Contains '{word}' in content")
        
        # Add similarity-based reason
        if similarity_score > 0.8:
            reasons.append("High semantic similarity")
        elif similarity_score > 0.6:
            reasons.append("Good semantic match")
        
        return reasons[:3]  # Limit to top 3 reasons
    
    def _get_semantic_suggestions(self, query: str, all_prompts: List[Prompt]) -> List[str]:
        """
        Generate semantic suggestions based on the query and available prompts.
        
        Args:
            query: Search query
            all_prompts: All available prompts
            
        Returns:
            List of suggested search terms
        """
        suggestions = set()
        
        # Extract common terms from prompt names and tags
        for prompt in all_prompts:
            # Add prompt type variations
            prompt_type = prompt.prompt_type.replace('_', ' ')
            suggestions.add(prompt_type)
            
            # Add tags
            if prompt.tags:
                suggestions.update(prompt.tags)
        
        # Add common semantic search terms
        common_terms = [
            "meeting analysis", "executive summary", "technical details",
            "action items", "risk assessment", "strategic planning",
            "implementation", "architecture", "performance"
        ]
        suggestions.update(common_terms)
        
        # Filter suggestions that are somewhat related to the query
        query_words = set(query.lower().split())
        relevant_suggestions = []
        
        for suggestion in suggestions:
            suggestion_words = set(suggestion.lower().split())
            if query_words.intersection(suggestion_words) or len(query) < 3:
                relevant_suggestions.append(suggestion)
        
        return sorted(list(set(relevant_suggestions)))[:5]
    
    def search(self, query: str, context: str = '', limit: int = 10, 
               performance_threshold: float = 0.0) -> Dict[str, Any]:
        """
        Perform semantic search on prompts.
        
        Args:
            query: Search query string
            context: Additional context for search
            limit: Maximum number of results to return
            performance_threshold: Minimum performance threshold (0-10)
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            logger.info(f"Performing semantic search for query: '{query}'")
            
            # Refresh cache if needed
            if self._should_refresh_cache():
                self._refresh_prompt_cache()
            
            if not query.strip():
                return self._get_empty_results()
            
            # Build full search query with context
            full_query = f"{query} {context}".strip()
            
            # Generate embedding for the query
            query_embedding = self.model.encode([full_query])
            
            # Get all active prompts
            prompts = Prompt.query.filter_by(is_active=True).all()
            
            if not prompts:
                return self._get_empty_results()
            
            # Calculate similarities
            results = []
            prompt_embeddings = []
            
            for prompt in prompts:
                # Get or generate embedding for this prompt
                if prompt.id in self.prompt_embeddings:
                    embedding = self.prompt_embeddings[prompt.id]
                else:
                    searchable_text = self._build_searchable_text(prompt)
                    embedding = self.model.encode([searchable_text])[0]
                    self.prompt_embeddings[prompt.id] = embedding
                
                prompt_embeddings.append(embedding)
            
            # Calculate cosine similarities
            similarities = cosine_similarity(query_embedding, prompt_embeddings)[0]
            
            # Create results with similarity scores
            for i, prompt in enumerate(prompts):
                similarity_score = similarities[i]
                
                # Skip if similarity is too low
                if similarity_score < 0.3:
                    continue
                
                # Get performance metrics
                performance_metrics = self._get_prompt_performance_metrics(prompt.id)
                
                # Apply performance threshold filter
                if performance_metrics['success_rate'] < performance_threshold:
                    continue
                
                # Generate match reasons
                match_reasons = self._generate_match_reasons(query, prompt, similarity_score)
                
                # Create result entry
                result = {
                    'id': prompt.id,
                    'name': prompt.name,
                    'type': prompt.prompt_type,
                    'tags': prompt.tags or [],
                    'relevance_score': round(similarity_score, 3),
                    'match_reasons': match_reasons,
                    'performance_metrics': performance_metrics,
                    'preview_content': prompt.content[:200] + "..." if len(prompt.content) > 200 else prompt.content
                }
                
                results.append(result)
            
            # Sort by relevance score
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Limit results
            results = results[:limit]
            
            # Generate semantic suggestions
            suggestions = self._get_semantic_suggestions(query, prompts)
            
            # Generate query interpretation
            interpretation = self._generate_query_interpretation(query, context, len(results))
            
            return {
                'results': results,
                'total': len(results),
                'semantic_suggestions': suggestions,
                'query_interpretation': interpretation
            }
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return {
                'results': [],
                'total': 0,
                'semantic_suggestions': [],
                'query_interpretation': f"Error performing search: {str(e)}",
                'error': str(e)
            }
    
    def _refresh_prompt_cache(self):
        """Refresh the prompt cache and embeddings."""
        try:
            logger.info("Refreshing prompt cache")
            prompts = Prompt.query.filter_by(is_active=True).all()
            
            for prompt in prompts:
                if prompt.id not in self.prompt_embeddings:
                    searchable_text = self._build_searchable_text(prompt)
                    embedding = self.model.encode([searchable_text])[0]
                    self.prompt_embeddings[prompt.id] = embedding
            
            self.last_cache_update = datetime.utcnow()
            logger.info(f"Cache refreshed with {len(prompts)} prompts")
            
        except Exception as e:
            logger.error(f"Error refreshing prompt cache: {e}")
    
    def _get_empty_results(self) -> Dict[str, Any]:
        """Return empty results structure."""
        return {
            'results': [],
            'total': 0,
            'semantic_suggestions': ['meeting analysis', 'executive summary', 'technical details'],
            'query_interpretation': 'No search query provided'
        }
    
    def _generate_query_interpretation(self, query: str, context: str, result_count: int) -> str:
        """Generate a human-readable interpretation of the search query."""
        if not query.strip():
            return "No search query provided"
        
        base_interpretation = f"Searching for prompts related to '{query}'"
        
        if context:
            base_interpretation += f" in the context of '{context}'"
        
        if result_count == 0:
            return base_interpretation + " - no matching prompts found"
        elif result_count == 1:
            return base_interpretation + " - found 1 matching prompt"
        else:
            return base_interpretation + f" - found {result_count} matching prompts"