"""
Test scenarios for comprehensive Vertigo agent evaluation.
Provides realistic scenarios for testing email processing, meeting analysis, 
and status generation across different use cases and edge conditions.
"""

from .email_scenarios import EmailScenarioBuilder
from .meeting_scenarios import MeetingScenarioBuilder
from .status_scenarios import StatusScenarioBuilder
from .multi_agent_scenarios import MultiAgentScenarioBuilder

__all__ = [
    "EmailScenarioBuilder",
    "MeetingScenarioBuilder", 
    "StatusScenarioBuilder",
    "MultiAgentScenarioBuilder"
]