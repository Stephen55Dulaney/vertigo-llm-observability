"""
Email processing scenarios for comprehensive testing.
Provides realistic email command scenarios for testing Vertigo's email processing capabilities.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class EmailScenarioBuilder:
    """Builder for creating comprehensive email processing test scenarios."""
    
    def __init__(self):
        self.scenarios = []
    
    def build_basic_command_scenarios(self) -> List[Dict[str, Any]]:
        """Build basic command functionality scenarios."""
        return [
            {
                "id": "email_001",
                "name": "Help Command - Standard Format",
                "description": "Test basic help command recognition and response",
                "subject": "Vertigo: Help",
                "body": "",
                "expected_command": "help",
                "expected_response_elements": [
                    "Available Commands", "Usage", "Examples"
                ],
                "priority": "high",
                "tags": ["basic_functionality", "help_command"]
            },
            {
                "id": "email_002", 
                "name": "Weekly Stats Request",
                "description": "Test weekly statistics command",
                "subject": "Vertigo: List this week",
                "body": "",
                "expected_command": "list this week",
                "expected_response_elements": [
                    "Last 7 Days", "Transcripts", "Meetings", "Total"
                ],
                "priority": "high",
                "tags": ["basic_functionality", "stats_command"]
            },
            {
                "id": "email_003",
                "name": "Total Statistics",
                "description": "Test all-time statistics command",
                "subject": "Vertigo: Total stats", 
                "body": "",
                "expected_command": "total stats",
                "expected_response_elements": [
                    "All-Time", "Statistics", "Total Transcripts", "Success Rate"
                ],
                "priority": "high",
                "tags": ["basic_functionality", "stats_command"]
            },
            {
                "id": "email_004",
                "name": "Project Listing",
                "description": "Test project list command",
                "subject": "Vertigo: List projects",
                "body": "",
                "expected_command": "list projects",
                "expected_response_elements": [
                    "Project Summary", "Transcripts by Project", "Total Projects"
                ],
                "priority": "high",
                "tags": ["basic_functionality", "project_command"]
            }
        ]
    
    def build_edge_case_scenarios(self) -> List[Dict[str, Any]]:
        """Build edge case and error handling scenarios."""
        return [
            {
                "id": "email_edge_001",
                "name": "Reply Format - Help Command",
                "description": "Test command recognition in reply format",
                "subject": "Re: Vertigo: Help",
                "body": "",
                "expected_command": "help",
                "expected_response_elements": ["Available Commands"],
                "priority": "medium",
                "tags": ["edge_case", "reply_handling"]
            },
            {
                "id": "email_edge_002",
                "name": "Forward Format - Stats Command", 
                "description": "Test command recognition in forward format",
                "subject": "Fwd: Vertigo: Total stats",
                "body": "",
                "expected_command": "total stats",
                "expected_response_elements": ["All-Time", "Statistics"],
                "priority": "medium",
                "tags": ["edge_case", "forward_handling"]
            },
            {
                "id": "email_edge_003",
                "name": "Case Insensitive - Help",
                "description": "Test case insensitive command processing",
                "subject": "VERTIGO: HELP",
                "body": "",
                "expected_command": "help",
                "expected_response_elements": ["Available Commands"],
                "priority": "medium",
                "tags": ["edge_case", "case_handling"]
            },
            {
                "id": "email_edge_004",
                "name": "Extra Whitespace",
                "description": "Test tolerance to extra whitespace",
                "subject": "   Vertigo:   Help   ",
                "body": "",
                "expected_command": "help",
                "expected_response_elements": ["Available Commands"],
                "priority": "low",
                "tags": ["edge_case", "whitespace_handling"]
            },
            {
                "id": "email_edge_005",
                "name": "No Prefix - Direct Command",
                "description": "Test command without Vertigo prefix",
                "subject": "Help",
                "body": "",
                "expected_command": "help",
                "expected_response_elements": ["Available Commands"],
                "priority": "medium",
                "tags": ["edge_case", "prefix_optional"]
            }
        ]
    
    def build_error_handling_scenarios(self) -> List[Dict[str, Any]]:
        """Build error handling and invalid input scenarios."""
        return [
            {
                "id": "email_error_001",
                "name": "Invalid Command",
                "description": "Test handling of unrecognized commands",
                "subject": "Vertigo: Invalid command request",
                "body": "",
                "expected_command": None,
                "expected_response_elements": [],
                "priority": "medium",
                "tags": ["error_handling", "invalid_command"]
            },
            {
                "id": "email_error_002",
                "name": "Empty Subject Line",
                "description": "Test handling of empty subject",
                "subject": "",
                "body": "Some body content without subject",
                "expected_command": None,
                "expected_response_elements": [],
                "priority": "medium",
                "tags": ["error_handling", "empty_input"]
            },
            {
                "id": "email_error_003",
                "name": "Unrelated Email",
                "description": "Test false positive prevention",
                "subject": "Meeting tomorrow at 3pm",
                "body": "Don't forget our scheduled meeting tomorrow.",
                "expected_command": None,
                "expected_response_elements": [],
                "priority": "high",
                "tags": ["error_handling", "false_positive"]
            },
            {
                "id": "email_error_004",
                "name": "Malformed Command",
                "description": "Test handling of malformed Vertigo commands",
                "subject": "Vertigo: Lis this wek",  # Intentional typos
                "body": "",
                "expected_command": None,
                "expected_response_elements": [],
                "priority": "medium",
                "tags": ["error_handling", "malformed_command"]
            }
        ]
    
    def build_business_context_scenarios(self) -> List[Dict[str, Any]]:
        """Build scenarios with business context and realistic usage."""
        return [
            {
                "id": "email_business_001",
                "name": "CEO Weekly Request",
                "description": "Realistic CEO request for weekly summary",
                "subject": "Re: Vertigo: List this week",
                "body": "Stephen, can you send me the weekly transcript summary? I need it for the board meeting this afternoon. Thanks!",
                "expected_command": "list this week",
                "expected_response_elements": [
                    "Last 7 Days", "Total Transcripts", "Success Rate"
                ],
                "priority": "high",
                "tags": ["business_context", "executive_request"],
                "business_impact": "high",
                "user_persona": "CEO"
            },
            {
                "id": "email_business_002", 
                "name": "Project Manager Status Check",
                "description": "PM requesting project-specific information",
                "subject": "Vertigo: List projects", 
                "body": "Hi, I need to understand which projects have been most active with meetings and transcripts. This is for resource planning.",
                "expected_command": "list projects",
                "expected_response_elements": [
                    "Project Summary", "Transcripts by Project"
                ],
                "priority": "high",
                "tags": ["business_context", "project_management"],
                "business_impact": "medium",
                "user_persona": "Project Manager"
            },
            {
                "id": "email_business_003",
                "name": "Investor Update Request",
                "description": "Request for comprehensive statistics for investor update",
                "subject": "Vertigo: Total stats",
                "body": "For the quarterly investor update, I need our complete transcript analytics. Please include all available metrics and success rates.",
                "expected_command": "total stats",
                "expected_response_elements": [
                    "All-Time Statistics", "Success Rate", "Total"
                ],
                "priority": "high",
                "tags": ["business_context", "investor_relations"],
                "business_impact": "high",
                "user_persona": "Executive"
            }
        ]
    
    def build_stress_test_scenarios(self) -> List[Dict[str, Any]]:
        """Build stress testing scenarios for system limits."""
        return [
            {
                "id": "email_stress_001",
                "name": "Very Long Subject Line",
                "description": "Test handling of extremely long subject lines",
                "subject": "Vertigo: Help " + "with additional context " * 50,
                "body": "",
                "expected_command": "help",
                "expected_response_elements": ["Available Commands"],
                "priority": "low",
                "tags": ["stress_test", "long_input"]
            },
            {
                "id": "email_stress_002",
                "name": "Large Email Body",
                "description": "Test handling of emails with large body content",
                "subject": "Vertigo: Total stats",
                "body": "Additional context information. " * 1000,
                "expected_command": "total stats", 
                "expected_response_elements": ["All-Time Statistics"],
                "priority": "low",
                "tags": ["stress_test", "large_body"]
            },
            {
                "id": "email_stress_003",
                "name": "Special Characters in Subject",
                "description": "Test handling of special characters",
                "subject": "Vertigo: Help @#$%^&*()[]{}|\\:;\"'<>,.?/~`",
                "body": "",
                "expected_command": "help",
                "expected_response_elements": ["Available Commands"],
                "priority": "medium",
                "tags": ["stress_test", "special_characters"]
            },
            {
                "id": "email_stress_004",
                "name": "Unicode and Emoji",
                "description": "Test handling of Unicode characters and emojis",
                "subject": "Vertigo: Help 🚀📊💡",
                "body": "Testing with émojis and ünïcödé characters",
                "expected_command": "help",
                "expected_response_elements": ["Available Commands"],
                "priority": "medium",
                "tags": ["stress_test", "unicode", "emoji"]
            }
        ]
    
    def build_conversation_flow_scenarios(self) -> List[Dict[str, Any]]:
        """Build multi-step conversation flow scenarios."""
        return [
            {
                "id": "email_flow_001",
                "name": "Help Then Stats Request",
                "description": "Multi-step flow: help request followed by stats",
                "conversation_flow": [
                    {
                        "step": 1,
                        "subject": "Vertigo: Help",
                        "body": "",
                        "expected_command": "help"
                    },
                    {
                        "step": 2,
                        "subject": "Re: Vertigo: Help",
                        "body": "Thanks! Now can I get Vertigo: Total stats",
                        "expected_command": "total stats"
                    }
                ],
                "priority": "medium",
                "tags": ["conversation_flow", "multi_step"]
            },
            {
                "id": "email_flow_002",
                "name": "Progressive Information Requests",
                "description": "User asking for increasingly detailed information",
                "conversation_flow": [
                    {
                        "step": 1,
                        "subject": "Vertigo: List this week",
                        "body": "",
                        "expected_command": "list this week"
                    },
                    {
                        "step": 2,
                        "subject": "Vertigo: List projects",
                        "body": "That was helpful, now I need project details",
                        "expected_command": "list projects"
                    },
                    {
                        "step": 3,
                        "subject": "Vertigo: Total stats",
                        "body": "And finally, all historical data please",
                        "expected_command": "total stats"
                    }
                ],
                "priority": "medium",
                "tags": ["conversation_flow", "information_progression"]
            }
        ]
    
    def build_all_scenarios(self) -> List[Dict[str, Any]]:
        """Build complete set of email processing scenarios."""
        all_scenarios = []
        all_scenarios.extend(self.build_basic_command_scenarios())
        all_scenarios.extend(self.build_edge_case_scenarios())
        all_scenarios.extend(self.build_error_handling_scenarios())
        all_scenarios.extend(self.build_business_context_scenarios())
        all_scenarios.extend(self.build_stress_test_scenarios())
        all_scenarios.extend(self.build_conversation_flow_scenarios())
        
        # Add metadata
        for scenario in all_scenarios:
            scenario["created_date"] = datetime.utcnow().isoformat()
            scenario["scenario_type"] = "email_processing"
            scenario["framework_version"] = "1.0.0"
        
        return all_scenarios
    
    def get_scenarios_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get scenarios filtered by tag."""
        all_scenarios = self.build_all_scenarios()
        return [s for s in all_scenarios if tag in s.get("tags", [])]
    
    def get_scenarios_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """Get scenarios filtered by priority level."""
        all_scenarios = self.build_all_scenarios()
        return [s for s in all_scenarios if s.get("priority") == priority]
    
    def get_business_critical_scenarios(self) -> List[Dict[str, Any]]:
        """Get scenarios that are business critical."""
        return [s for s in self.build_all_scenarios() 
                if s.get("business_impact") in ["high", "critical"]]