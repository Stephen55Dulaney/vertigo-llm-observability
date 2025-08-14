"""
Meeting Analyzer Adapter for Scenario Testing.
Tests Vertigo's meeting transcript analysis and prompt variant capabilities.
"""

import sys
import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add Vertigo root to Python path
vertigo_root = Path(__file__).parents[2]
sys.path.insert(0, str(vertigo_root))

from vertigo_scenario_framework.adapters.base_adapter import BaseVertigoAdapter

class MeetingAnalyzerAdapter(BaseVertigoAdapter):
    """
    Adapter for testing Vertigo's meeting transcript analysis system.
    Tests different prompt variants and evaluation capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Meeting Analyzer Adapter."""
        super().__init__("MeetingAnalyzer", config)
        
        # Import Vertigo meeting analysis components
        try:
            # Import prompt variants
            sys.path.insert(0, str(vertigo_root / "vertigo" / "functions" / "meeting-processor"))
            from prompt_variants import (
                get_prompt_variant, detailed_extraction_prompt, 
                executive_summary_prompt, technical_focus_prompt,
                action_oriented_prompt, risk_assessment_prompt, daily_summary_prompt
            )
            self.prompt_variants = {
                "detailed_extraction": detailed_extraction_prompt,
                "executive_summary": executive_summary_prompt,
                "technical_focus": technical_focus_prompt,
                "action_oriented": action_oriented_prompt,
                "risk_assessment": risk_assessment_prompt,
                "daily_summary": daily_summary_prompt
            }
            self.get_prompt_variant = get_prompt_variant
            self.logger.info("Successfully imported meeting analysis components")
            
        except ImportError as e:
            self.logger.error(f"Failed to import meeting analysis components: {e}")
            self.prompt_variants = {}
            self.get_prompt_variant = None
        
        # Mock LLM for testing (replace with real Gemini integration if needed)
        self.use_mock_llm = config.get("use_mock_llm", True) if config else True
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate meeting analysis input data.
        
        Required fields:
        - transcript: Meeting transcript text
        - project: Project name
        - variant: Prompt variant to use (optional, defaults to detailed_extraction)
        """
        if not isinstance(input_data, dict):
            return False
        
        required_fields = ["transcript", "project"]
        for field in required_fields:
            if field not in input_data or not input_data[field]:
                self.logger.error(f"Missing or empty required field: {field}")
                return False
        
        variant = input_data.get("variant", "detailed_extraction")
        if variant not in self.prompt_variants:
            self.logger.error(f"Invalid prompt variant: {variant}")
            return False
        
        return True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process meeting transcript through selected prompt variant.
        
        Args:
            input_data: Dict with 'transcript', 'project', and optional 'variant'
            
        Returns:
            Dict with analysis results and metadata
        """
        if not self.prompt_variants:
            raise RuntimeError("Meeting analysis components not initialized")
        
        transcript = input_data["transcript"]
        project = input_data["project"]
        variant = input_data.get("variant", "detailed_extraction")
        
        # Generate the prompt
        if variant in self.prompt_variants:
            prompt_text = self.prompt_variants[variant](transcript, project)
        else:
            prompt_text = self.get_prompt_variant(variant, transcript, project)
        
        # Mock LLM response for testing
        if self.use_mock_llm:
            llm_response = self._generate_mock_response(variant, transcript, project)
        else:
            # Here you would integrate with actual Gemini LLM
            llm_response = await self._call_real_llm(prompt_text)
        
        # Analyze the result
        analysis = {
            "input": {
                "transcript": transcript[:200] + "..." if len(transcript) > 200 else transcript,
                "project": project,
                "variant": variant,
                "transcript_length": len(transcript)
            },
            "prompt_analysis": {
                "prompt_length": len(prompt_text),
                "prompt_preview": prompt_text[:300] + "..." if len(prompt_text) > 300 else prompt_text,
                "expected_json_format": "JSON" in prompt_text.upper(),
                "structured_format": self._analyze_prompt_structure(prompt_text)
            },
            "llm_response": llm_response,
            "analysis": self._analyze_meeting_result(llm_response, variant),
            "test_metadata": {
                "variant_used": variant,
                "mock_response": self.use_mock_llm,
                "processing_successful": not isinstance(llm_response, dict) or "error" not in llm_response
            }
        }
        
        return analysis
    
    def _generate_mock_response(self, variant: str, transcript: str, project: str) -> Dict[str, Any]:
        """
        Generate a realistic mock response based on the prompt variant.
        
        Args:
            variant: Prompt variant being tested
            transcript: Input transcript
            project: Project name
            
        Returns:
            Mock response dictionary
        """
        base_response = {
            "meeting_summary": f"Mock meeting summary for {project} using {variant} analysis",
        }
        
        # Variant-specific mock responses
        if variant == "detailed_extraction":
            return {
                **base_response,
                "key_points": [
                    "Discussed project architecture decisions",
                    "Reviewed current development progress"
                ],
                "action_items": [
                    {
                        "description": "Complete feature implementation",
                        "owner": "Development Team",
                        "due_date": "2024-01-15",
                        "confidence": "CONFIRMED"
                    }
                ],
                "technical_details": [
                    "Using Python Flask framework",
                    "PostgreSQL database integration"
                ],
                "risks": [
                    {
                        "risk": "Timeline may be tight",
                        "impact": "Medium",
                        "mitigation": "Add additional resources if needed"
                    }
                ],
                "decisions": ["Approved new architecture approach"],
                "assumptions": ["Team has required expertise"],
                "project_names": [project],
                "participants": ["Team Lead", "Developer", "Product Manager"],
                "next_steps": ["Begin implementation phase"]
            }
        
        elif variant == "executive_summary":
            return {
                **base_response,
                "strategic_decisions": ["Approved budget increase for Q2"],
                "business_impact": ["Expected 20% improvement in user engagement"],
                "action_items": [
                    {
                        "description": "Present to board of directors",
                        "owner": "Executive Team",
                        "due_date": "2024-01-20",
                        "priority": "High"
                    }
                ],
                "risks": [
                    {
                        "risk": "Market competition increasing",
                        "impact": "High",
                        "mitigation": "Accelerate feature development"
                    }
                ],
                "next_quarter_focus": ["User experience improvements"],
                "stakeholders": ["Product Team", "Executive Leadership"]
            }
        
        elif variant == "technical_focus":
            return {
                **base_response,
                "architecture_decisions": ["Microservices architecture adopted"],
                "technology_stack": ["Python", "Docker", "Kubernetes"],
                "technical_requirements": ["99.9% uptime requirement", "Sub-200ms response time"],
                "implementation_plan": ["Phase 1: Core services", "Phase 2: Integration"],
                "technical_risks": [
                    {
                        "risk": "Database scaling challenges",
                        "impact": "Medium",
                        "mitigation": "Implement read replicas"
                    }
                ],
                "action_items": [
                    {
                        "description": "Set up CI/CD pipeline",
                        "owner": "DevOps Team",
                        "due_date": "2024-01-18",
                        "complexity": "Medium"
                    }
                ],
                "dependencies": ["Third-party API integration"],
                "success_metrics": ["Response time < 200ms", "Zero downtime deployments"]
            }
        
        elif variant == "action_oriented":
            return {
                **base_response,
                "immediate_actions": [
                    {
                        "description": "Update project documentation",
                        "owner": "Technical Writer",
                        "due_date": "2024-01-12",
                        "priority": "High"
                    }
                ],
                "deliverables": [
                    {
                        "description": "Design mockups",
                        "owner": "Design Team",
                        "due_date": "2024-01-15",
                        "type": "Design"
                    }
                ],
                "next_week_focus": ["Complete testing phase"],
                "blockers": [
                    {
                        "blocker": "Waiting for API access",
                        "owner": "External Vendor",
                        "escalation_needed": "Yes"
                    }
                ],
                "dependencies": ["Legal approval for data processing"],
                "success_criteria": ["All tests pass", "Performance benchmarks met"],
                "timeline": ["MVP by end of January"]
            }
        
        elif variant == "daily_summary":
            return {
                "my_ambition": "Deliver a robust and scalable solution that meets user needs",
                "what_we_did_today": [
                    "Reviewed architecture proposals with the team",
                    "Finalized technical specifications",
                    "Conducted stakeholder alignment meeting"
                ],
                "what_well_do_next": [
                    "Begin implementation of core features",
                    "Set up development environment",
                    "Schedule regular check-ins"
                ],
                "key_metrics": [
                    "3 major decisions finalized",
                    "Timeline confirmed for January delivery"
                ],
                "blockers_risks": [
                    {
                        "issue": "Need approval for additional resources",
                        "impact": "Medium",
                        "action_needed": "Schedule meeting with finance team"
                    }
                ],
                "team_coordination": [
                    "Working closely with design team on mockups",
                    "Coordinating with QA for testing strategy"
                ]
            }
        
        else:  # risk_assessment
            return {
                **base_response,
                "high_risk_items": [
                    {
                        "risk": "Aggressive timeline may impact quality",
                        "probability": "High",
                        "impact": "High",
                        "mitigation": "Add quality checkpoints",
                        "owner": "Project Manager"
                    }
                ],
                "blockers": [
                    {
                        "blocker": "Waiting for security review",
                        "impact": "High",
                        "resolution": "Follow up with security team",
                        "escalation": "Security Manager"
                    }
                ],
                "assumptions": [
                    {
                        "assumption": "Current team size is sufficient",
                        "validation_needed": "Yes",
                        "risk_if_wrong": "Project delays"
                    }
                ],
                "contingency_plans": ["Have backup developer ready"],
                "dependencies": [
                    {
                        "dependency": "Third-party service integration",
                        "risk_level": "Medium",
                        "mitigation": "Prepare fallback solution"
                    }
                ],
                "timeline_risks": ["Holiday season may slow external dependencies"],
                "resource_risks": ["Key developer may be unavailable"],
                "technical_risks": ["New technology has learning curve"]
            }
    
    def _analyze_prompt_structure(self, prompt_text: str) -> Dict[str, Any]:
        """Analyze the structure and quality of the generated prompt."""
        return {
            "has_json_schema": "{" in prompt_text and "}" in prompt_text,
            "has_instructions": "return" in prompt_text.lower() or "extract" in prompt_text.lower(),
            "has_examples": "example" in prompt_text.lower(),
            "word_count": len(prompt_text.split()),
            "line_count": len(prompt_text.split('\n'))
        }
    
    def _analyze_meeting_result(self, response: Dict[str, Any], variant: str) -> Dict[str, Any]:
        """
        Analyze the quality and completeness of meeting analysis result.
        
        Args:
            response: LLM response
            variant: Prompt variant used
            
        Returns:
            Analysis of response quality and completeness
        """
        analysis = {
            "response_format": "json" if isinstance(response, dict) else "text",
            "has_error": isinstance(response, dict) and "error" in response,
            "completeness_score": 0.0,
            "structure_score": 0.0,
            "content_quality": {}
        }
        
        if analysis["has_error"]:
            return analysis
        
        # Check for expected fields based on variant
        expected_fields = self._get_expected_fields(variant)
        if expected_fields and isinstance(response, dict):
            found_fields = sum(1 for field in expected_fields if field in response)
            analysis["completeness_score"] = found_fields / len(expected_fields)
            analysis["expected_fields"] = expected_fields
            analysis["found_fields"] = [field for field in expected_fields if field in response]
            analysis["missing_fields"] = [field for field in expected_fields if field not in response]
        
        # Analyze content quality
        if isinstance(response, dict):
            analysis["content_quality"] = {
                "has_summary": bool(response.get("meeting_summary")),
                "summary_length": len(response.get("meeting_summary", "")),
                "action_items_count": len(response.get("action_items", [])),
                "structured_data": self._check_structured_data(response)
            }
        
        return analysis
    
    def _get_expected_fields(self, variant: str) -> List[str]:
        """Get expected fields for each prompt variant."""
        field_mapping = {
            "detailed_extraction": [
                "meeting_summary", "key_points", "action_items", "technical_details",
                "risks", "decisions", "assumptions", "project_names", "participants", "next_steps"
            ],
            "executive_summary": [
                "meeting_summary", "strategic_decisions", "business_impact", "action_items",
                "risks", "next_quarter_focus", "stakeholders"
            ],
            "technical_focus": [
                "meeting_summary", "architecture_decisions", "technology_stack",
                "technical_requirements", "implementation_plan", "technical_risks",
                "action_items", "dependencies", "success_metrics"
            ],
            "action_oriented": [
                "meeting_summary", "immediate_actions", "deliverables", "next_week_focus",
                "blockers", "dependencies", "success_criteria", "timeline"
            ],
            "risk_assessment": [
                "meeting_summary", "high_risk_items", "blockers", "assumptions",
                "contingency_plans", "dependencies", "timeline_risks", "resource_risks", "technical_risks"
            ],
            "daily_summary": [
                "my_ambition", "what_we_did_today", "what_well_do_next",
                "key_metrics", "blockers_risks", "team_coordination"
            ]
        }
        return field_mapping.get(variant, [])
    
    def _check_structured_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Check if response contains well-structured data."""
        structure_analysis = {
            "has_arrays": any(isinstance(v, list) for v in response.values()),
            "has_objects": any(isinstance(v, dict) for v in response.values()),
            "nested_structure": False,
            "array_item_count": 0
        }
        
        for value in response.values():
            if isinstance(value, list):
                structure_analysis["array_item_count"] += len(value)
                if value and isinstance(value[0], dict):
                    structure_analysis["nested_structure"] = True
        
        return structure_analysis
    
    async def _call_real_llm(self, prompt_text: str) -> Dict[str, Any]:
        """
        Call real LLM (Gemini) with the prompt. 
        This would be implemented for production use.
        """
        # TODO: Implement actual Gemini API call
        # This is a placeholder for real LLM integration
        return {"error": "Real LLM integration not implemented in test mode"}
    
    def create_test_scenarios(self) -> List[Dict[str, Any]]:
        """
        Create comprehensive test scenarios for meeting analysis.
        
        Returns:
            List of test scenario dictionaries
        """
        # Sample meeting transcripts
        short_transcript = """
        Team meeting - Project Alpha discussion
        - Reviewed current progress on user authentication module
        - Discussed timeline for completing the database integration
        - Action item: John to complete API documentation by Friday
        - Next meeting scheduled for next Tuesday
        """
        
        medium_transcript = """
        Product Strategy Meeting - Q1 Planning Session
        
        Participants: Sarah (Product Manager), Mike (Engineering Lead), Lisa (Design Lead), Tom (Data Analyst)
        
        Sarah: Let's review our Q1 objectives. We need to focus on improving user engagement metrics.
        
        Mike: From an engineering perspective, we can implement the new recommendation engine. 
        It should improve user retention by about 15% based on our initial analysis.
        
        Lisa: I've completed the UI mockups for the new dashboard. The design system is ready 
        and should improve usability significantly.
        
        Tom: Our current data shows that users spend an average of 3.2 minutes per session. 
        The new features should help increase this to at least 5 minutes.
        
        Action Items:
        - Mike: Complete recommendation engine implementation by January 31st
        - Lisa: Finalize design system documentation by January 25th  
        - Tom: Set up analytics tracking for new metrics by January 20th
        - Sarah: Schedule stakeholder review meeting for February 1st
        
        Risks discussed:
        - Timeline is aggressive given holiday season
        - Need to ensure data privacy compliance with new features
        - Third-party API integration may have dependencies
        """
        
        technical_transcript = """
        Architecture Review Meeting - Microservices Migration
        
        Engineering Team Discussion:
        
        Lead Architect: We need to migrate from monolith to microservices architecture. 
        Current system is hitting scalability limits at 10K concurrent users.
        
        Backend Developer: I propose using Docker containers with Kubernetes orchestration. 
        We should implement API Gateway pattern for service communication.
        
        DevOps Engineer: For the migration, we need:
        1. Set up CI/CD pipeline with Jenkins
        2. Implement monitoring with Prometheus and Grafana  
        3. Database sharding strategy for PostgreSQL
        4. Redis caching layer for session management
        
        Frontend Developer: We'll need to update API calls to work with new service endpoints. 
        Estimated 2 weeks of frontend changes.
        
        Security Engineer: Each microservice needs individual authentication. 
        JWT tokens with OAuth2 implementation recommended.
        
        Technical Decisions Made:
        - Use Docker + Kubernetes for containerization
        - Implement API Gateway with rate limiting
        - PostgreSQL with read replicas for scaling
        - JWT authentication across all services
        
        Timeline:
        - Phase 1: Core services migration (4 weeks)
        - Phase 2: Authentication service (2 weeks)  
        - Phase 3: Frontend integration (2 weeks)
        - Phase 4: Performance testing (1 week)
        
        Risks:
        - Data migration complexity
        - Potential downtime during cutover
        - Team learning curve for Kubernetes
        """
        
        scenarios = [
            # Test different prompt variants with same content
            {
                "name": "Detailed Extraction - Short Meeting",
                "transcript": short_transcript,
                "project": "Project Alpha",
                "variant": "detailed_extraction",
                "scenario_type": "prompt_variant_testing",
                "expected_elements": ["action_items", "participants", "next_steps"]
            },
            {
                "name": "Executive Summary - Product Strategy",
                "transcript": medium_transcript,
                "project": "Product Strategy",
                "variant": "executive_summary",
                "scenario_type": "prompt_variant_testing",
                "expected_elements": ["strategic_decisions", "business_impact"]
            },
            {
                "name": "Technical Focus - Architecture Review",
                "transcript": technical_transcript,
                "project": "Architecture Migration",
                "variant": "technical_focus",
                "scenario_type": "prompt_variant_testing", 
                "expected_elements": ["architecture_decisions", "technology_stack", "technical_requirements"]
            },
            {
                "name": "Action Oriented - Product Strategy",
                "transcript": medium_transcript,
                "project": "Product Strategy",
                "variant": "action_oriented",
                "scenario_type": "prompt_variant_testing",
                "expected_elements": ["immediate_actions", "deliverables", "next_week_focus"]
            },
            {
                "name": "Risk Assessment - Technical Migration",
                "transcript": technical_transcript,
                "project": "Architecture Migration", 
                "variant": "risk_assessment",
                "scenario_type": "prompt_variant_testing",
                "expected_elements": ["high_risk_items", "blockers", "contingency_plans"]
            },
            {
                "name": "Daily Summary - Product Strategy",
                "transcript": medium_transcript,
                "project": "Product Strategy",
                "variant": "daily_summary",
                "scenario_type": "prompt_variant_testing",
                "expected_elements": ["my_ambition", "what_we_did_today", "what_well_do_next"]
            },
            
            # Edge cases and stress tests
            {
                "name": "Empty Transcript",
                "transcript": "",
                "project": "Test Project",
                "variant": "detailed_extraction",
                "scenario_type": "edge_case_testing",
                "expected_elements": []
            },
            {
                "name": "Very Long Transcript",
                "transcript": technical_transcript * 10,  # Repeat to make very long
                "project": "Long Meeting Test",
                "variant": "executive_summary",
                "scenario_type": "stress_testing",
                "expected_elements": ["meeting_summary"]
            },
            {
                "name": "Special Characters in Project",
                "transcript": short_transcript,
                "project": "Project @#$% Special-Chars_123",
                "variant": "detailed_extraction",
                "scenario_type": "edge_case_testing",
                "expected_elements": ["project_names"]
            }
        ]
        
        return scenarios
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        Run comprehensive test of all meeting analysis scenarios.
        
        Returns:
            Comprehensive test results with variant comparison
        """
        scenarios = self.create_test_scenarios()
        results = []
        
        for scenario in scenarios:
            self.logger.info(f"Running scenario: {scenario['name']}")
            result = await self.execute_with_metrics(scenario)
            results.append({
                "scenario": scenario,
                "result": result
            })
        
        # Analyze results across prompt variants
        analysis = self._analyze_comprehensive_results(results)
        
        return {
            "total_scenarios": len(scenarios),
            "individual_results": results,
            "variant_comparison": analysis,
            "adapter_metrics": self.get_metrics()
        }
    
    def _analyze_comprehensive_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze results across all prompt variants and scenarios.
        
        Returns:
            Comprehensive analysis with variant performance comparison
        """
        # Group results by variant and scenario type
        by_variant = {}
        by_scenario_type = {}
        
        for result_item in results:
            scenario = result_item["scenario"]
            result = result_item["result"]
            
            variant = scenario["variant"]
            scenario_type = scenario["scenario_type"]
            
            if variant not in by_variant:
                by_variant[variant] = []
            by_variant[variant].append(result)
            
            if scenario_type not in by_scenario_type:
                by_scenario_type[scenario_type] = []
            by_scenario_type[scenario_type].append(result)
        
        # Analyze performance by variant
        variant_analysis = {}
        for variant, variant_results in by_variant.items():
            completeness_scores = []
            structure_scores = []
            successful_count = 0
            
            for result in variant_results:
                if not result.get("error") and "analysis" in result:
                    analysis = result["analysis"]
                    if "completeness_score" in analysis:
                        completeness_scores.append(analysis["completeness_score"])
                    if "structure_score" in analysis:
                        structure_scores.append(analysis["structure_score"])
                    successful_count += 1
            
            variant_analysis[variant] = {
                "total_tests": len(variant_results),
                "successful_tests": successful_count,
                "success_rate": successful_count / len(variant_results),
                "average_completeness": sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0,
                "average_structure": sum(structure_scores) / len(structure_scores) if structure_scores else 0
            }
        
        # Analyze by scenario type
        scenario_type_analysis = {}
        for scenario_type, type_results in by_scenario_type.items():
            successful = sum(1 for r in type_results if not r.get("error"))
            scenario_type_analysis[scenario_type] = {
                "total_scenarios": len(type_results),
                "successful": successful,
                "success_rate": successful / len(type_results)
            }
        
        return {
            "variant_performance": variant_analysis,
            "scenario_type_performance": scenario_type_analysis,
            "best_performing_variant": max(variant_analysis.keys(), 
                                         key=lambda v: variant_analysis[v]["success_rate"]) if variant_analysis else None,
            "total_variants_tested": len(by_variant),
            "total_scenario_types": len(by_scenario_type)
        }