"""
EmailProcessorAdapter - Real Integration with Vertigo Email Processing
====================================================================

This adapter connects the Scenario framework with Stephen's actual Vertigo email
command processing system. It provides comprehensive testing capabilities for
email command detection, parsing, and response generation.

Author: Claude Code
Date: 2025-08-06
"""

import asyncio
import logging
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import the base adapter
from .base_adapter import BaseVertigoAdapter

class EmailProcessorAdapter(BaseVertigoAdapter):
    """
    Adapter for testing Vertigo's email command processing system.
    
    This adapter can test:
    - Command detection and parsing
    - Response generation 
    - Error handling
    - Performance metrics
    - Integration with Firestore
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the email processor adapter."""
        super().__init__("EmailProcessor", config)
        
        # Add Vertigo root to path for imports
        vertigo_root = Path(__file__).parent.parent.parent
        if str(vertigo_root) not in sys.path:
            sys.path.insert(0, str(vertigo_root))
        
        self.email_parser = None
        self.setup_parser()
    
    def setup_parser(self):
        """Initialize the email command parser."""
        try:
            from email_command_parser import EmailCommandParser
            self.email_parser = EmailCommandParser()
            self.logger.info("Email command parser initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize email parser: {e}")
            self.email_parser = None
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for email processing tests.
        
        Expected input format:
        {
            "subject": "Email subject line",
            "body": "Email body content (optional)",
            "test_type": "command_detection|full_processing|error_handling",
            "expected_result": {...} (optional, for validation)
        }
        """
        if not isinstance(input_data, dict):
            self.logger.error("Input data must be a dictionary")
            return False
        
        if "subject" not in input_data:
            self.logger.error("Missing required field: subject")
            return False
        
        if not isinstance(input_data["subject"], str):
            self.logger.error("Subject must be a string")
            return False
        
        valid_test_types = ["command_detection", "full_processing", "error_handling", "performance"]
        test_type = input_data.get("test_type", "command_detection")
        if test_type not in valid_test_types:
            self.logger.error(f"Invalid test_type: {test_type}. Must be one of: {valid_test_types}")
            return False
        
        return True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an email testing scenario.
        
        Args:
            input_data: Test scenario data including subject, body, test_type
            
        Returns:
            Dict containing test results, metrics, and analysis
        """
        if not self.email_parser:
            return {
                "error": "Email parser not initialized",
                "success": False,
                "test_type": input_data.get("test_type", "unknown")
            }
        
        test_type = input_data.get("test_type", "command_detection")
        subject = input_data["subject"]
        body = input_data.get("body", "")
        
        self.logger.info(f"Processing {test_type} test for subject: {subject}")
        
        # Execute the appropriate test type
        if test_type == "command_detection":
            return await self._test_command_detection(subject, body, input_data)
        elif test_type == "full_processing":
            return await self._test_full_processing(subject, body, input_data)
        elif test_type == "error_handling":
            return await self._test_error_handling(subject, body, input_data)
        elif test_type == "performance":
            return await self._test_performance(subject, body, input_data)
        else:
            return {
                "error": f"Unknown test type: {test_type}",
                "success": False,
                "test_type": test_type
            }
    
    async def _test_command_detection(self, subject: str, body: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test basic command detection functionality."""
        start_time = time.time()
        
        try:
            # Parse the command
            result = self.email_parser.parse_command(subject, body)
            processing_time = time.time() - start_time
            
            # Analyze the result
            detected_command = result.get('command') if result else None
            expected_command = input_data.get('expected_result', {}).get('command')
            
            # Determine success
            success = True
            analysis = {}
            
            if expected_command is not None:
                command_match = detected_command == expected_command
                success = command_match
                analysis['command_match'] = command_match
                analysis['expected_command'] = expected_command
                analysis['detected_command'] = detected_command
            else:
                # If no expected result, just check if we got a reasonable response
                success = result is not None
                analysis['has_response'] = success
                analysis['detected_command'] = detected_command
            
            # Check response structure
            if result:
                analysis['has_subject'] = 'subject' in result
                analysis['has_body'] = 'body' in result
                analysis['has_command'] = 'command' in result
                analysis['response_length'] = len(result.get('body', ''))
            
            return {
                "success": success,
                "test_type": "command_detection",
                "input": {"subject": subject, "body": body},
                "result": result,
                "analysis": analysis,
                "performance": {
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error in command detection test: {e}")
            
            return {
                "success": False,
                "test_type": "command_detection",
                "error": str(e),
                "error_type": type(e).__name__,
                "input": {"subject": subject, "body": body},
                "performance": {
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    async def _test_full_processing(self, subject: str, body: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test full email processing including Firestore integration."""
        start_time = time.time()
        
        try:
            # Parse the command
            result = self.email_parser.parse_command(subject, body)
            processing_time = time.time() - start_time
            
            # Additional analysis for full processing
            analysis = {
                "command_detected": result is not None,
                "firestore_accessed": False,  # We'll try to detect this
                "response_quality": "unknown"
            }
            
            if result:
                # Check if the command likely accessed Firestore
                command_type = result.get('command', '')
                firestore_commands = ['list this week', 'total stats', 'list projects']
                if command_type in firestore_commands:
                    analysis['firestore_accessed'] = True
                    
                    # Check for data in response
                    response_body = result.get('body', '')
                    if 'transcripts' in response_body.lower() or 'meetings' in response_body.lower():
                        analysis['response_quality'] = "data_present"
                    elif 'error' in response_body.lower():
                        analysis['response_quality'] = "error_response"
                    else:
                        analysis['response_quality'] = "generic_response"
                
                # Analyze response structure
                analysis['response_structure'] = {
                    'has_subject': 'subject' in result,
                    'has_body': 'body' in result,
                    'has_command': 'command' in result,
                    'subject_length': len(result.get('subject', '')),
                    'body_length': len(result.get('body', ''))
                }
            
            return {
                "success": result is not None,
                "test_type": "full_processing",
                "input": {"subject": subject, "body": body},
                "result": result,
                "analysis": analysis,
                "performance": {
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error in full processing test: {e}")
            
            return {
                "success": False,
                "test_type": "full_processing",
                "error": str(e),
                "error_type": type(e).__name__,
                "input": {"subject": subject, "body": body},
                "performance": {
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    async def _test_error_handling(self, subject: str, body: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test error handling capabilities."""
        start_time = time.time()
        
        try:
            result = self.email_parser.parse_command(subject, body)
            processing_time = time.time() - start_time
            
            # Analyze error handling
            analysis = {
                "graceful_failure": False,
                "error_message_present": False,
                "error_message_helpful": False
            }
            
            if result is None:
                # No result - this is expected for unknown commands
                analysis['graceful_failure'] = True
                analysis['error_handling_type'] = 'silent_ignore'
            elif result.get('command') == 'error':
                # Explicit error response
                analysis['graceful_failure'] = True
                analysis['error_message_present'] = True
                analysis['error_handling_type'] = 'explicit_error'
                
                # Check if error message is helpful
                error_body = result.get('body', '').lower()
                if 'help' in error_body or 'command' in error_body:
                    analysis['error_message_helpful'] = True
            
            return {
                "success": analysis['graceful_failure'],
                "test_type": "error_handling",
                "input": {"subject": subject, "body": body},
                "result": result,
                "analysis": analysis,
                "performance": {
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # For error handling tests, exceptions are actually valuable data
            return {
                "success": False,  # Exception occurred
                "test_type": "error_handling",
                "input": {"subject": subject, "body": body},
                "exception_occurred": True,
                "error": str(e),
                "error_type": type(e).__name__,
                "analysis": {
                    "graceful_failure": False,
                    "exception_type": type(e).__name__,
                    "error_handling_type": "exception"
                },
                "performance": {
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    async def _test_performance(self, subject: str, body: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test performance characteristics."""
        num_iterations = input_data.get('iterations', 10)
        response_times = []
        results = []
        
        for i in range(num_iterations):
            start_time = time.time()
            try:
                result = self.email_parser.parse_command(subject, body)
                response_time = time.time() - start_time
                response_times.append(response_time)
                results.append({"success": True, "result": result})
            except Exception as e:
                response_time = time.time() - start_time
                response_times.append(response_time)
                results.append({"success": False, "error": str(e)})
        
        # Calculate performance metrics
        successful_runs = sum(1 for r in results if r["success"])
        success_rate = successful_runs / num_iterations if num_iterations > 0 else 0
        
        performance_metrics = {
            "total_iterations": num_iterations,
            "successful_runs": successful_runs,
            "success_rate": success_rate,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "total_time": sum(response_times)
        }
        
        return {
            "success": success_rate >= 0.8,  # 80% success rate threshold
            "test_type": "performance",
            "input": {"subject": subject, "body": body},
            "performance": performance_metrics,
            "analysis": {
                "performance_acceptable": performance_metrics["avg_response_time"] < 1.0,
                "consistency": performance_metrics["max_response_time"] - performance_metrics["min_response_time"] < 0.5,
                "reliability": success_rate >= 0.95
            }
        }
    
    def create_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create a comprehensive set of test scenarios for email processing."""
        return [
            # Basic command detection scenarios
            {
                "name": "Basic Help Command",
                "test_type": "command_detection",
                "subject": "Vertigo: Help",
                "body": "",
                "expected_result": {"command": "help"}
            },
            {
                "name": "Stats Command",
                "test_type": "command_detection", 
                "subject": "Vertigo: Total stats",
                "body": "",
                "expected_result": {"command": "total stats"}
            },
            {
                "name": "Weekly Report Command",
                "test_type": "command_detection",
                "subject": "Vertigo: List this week", 
                "body": "",
                "expected_result": {"command": "list this week"}
            },
            
            # Reply handling scenarios
            {
                "name": "Reply to Help Command",
                "test_type": "command_detection",
                "subject": "Re: Vertigo: Help",
                "body": "",
                "expected_result": {"command": "help"}
            },
            {
                "name": "Forward of Stats Command",
                "test_type": "command_detection",
                "subject": "Fwd: Vertigo: Total stats",
                "body": "",
                "expected_result": {"command": "total stats"}
            },
            
            # Case sensitivity scenarios
            {
                "name": "Uppercase Command",
                "test_type": "command_detection",
                "subject": "VERTIGO: HELP",
                "body": "",
                "expected_result": {"command": "help"}
            },
            
            # Error handling scenarios
            {
                "name": "Unknown Command",
                "test_type": "error_handling",
                "subject": "Vertigo: Unknown command",
                "body": "",
                "expected_result": {"command": None}
            },
            {
                "name": "Malformed Subject",
                "test_type": "error_handling",
                "subject": "Not a vertigo command",
                "body": "",
                "expected_result": {"command": None}
            },
            
            # Full processing scenarios
            {
                "name": "Full Stats Processing",
                "test_type": "full_processing",
                "subject": "Vertigo: Total stats",
                "body": ""
            },
            {
                "name": "Full Weekly Report Processing", 
                "test_type": "full_processing",
                "subject": "Vertigo: List this week",
                "body": ""
            },
            
            # Performance scenarios
            {
                "name": "Help Command Performance",
                "test_type": "performance",
                "subject": "Vertigo: Help",
                "body": "",
                "iterations": 10
            }
        ]
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run a comprehensive test suite covering all scenarios."""
        scenarios = self.create_test_scenarios()
        results = []
        
        self.logger.info(f"Running comprehensive test with {len(scenarios)} scenarios")
        
        for scenario in scenarios:
            self.logger.info(f"Running scenario: {scenario['name']}")
            result = await self.execute_with_metrics(scenario)
            result['scenario_name'] = scenario['name']
            results.append(result)
        
        # Aggregate results
        total_scenarios = len(results)
        successful_scenarios = sum(1 for r in results if r.get('success', False))
        success_rate = successful_scenarios / total_scenarios if total_scenarios > 0 else 0
        
        avg_response_time = sum(
            r.get('performance', {}).get('processing_time', 0) 
            for r in results
        ) / total_scenarios if total_scenarios > 0 else 0
        
        return {
            "test_suite": "comprehensive_email_processing",
            "total_scenarios": total_scenarios,
            "successful_scenarios": successful_scenarios,
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "overall_health": "good" if success_rate >= 0.8 else "poor",
                "performance": "good" if avg_response_time < 0.5 else "slow",
                "reliability": "high" if success_rate >= 0.95 else "medium" if success_rate >= 0.8 else "low"
            }
        }