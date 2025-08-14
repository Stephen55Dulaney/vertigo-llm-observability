"""
AgentAdapter classes for Vertigo components.
These adapters connect Vertigo's email processing, meeting analysis, 
and status generation systems to the Scenario testing framework.
"""

from .email_processor_adapter import EmailProcessorAdapter
from .meeting_analyzer_adapter import MeetingAnalyzerAdapter  
from .status_generator_adapter import StatusGeneratorAdapter

__all__ = [
    "EmailProcessorAdapter",
    "MeetingAnalyzerAdapter", 
    "StatusGeneratorAdapter"
]