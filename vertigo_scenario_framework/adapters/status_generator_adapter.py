"""
Status Generator Adapter for Scenario Testing.
Tests Vertigo's executive status generation and reporting capabilities.
"""

import sys
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta

# Add Vertigo root to Python path
vertigo_root = Path(__file__).parents[2]
sys.path.insert(0, str(vertigo_root))

from vertigo_scenario_framework.adapters.base_adapter import BaseVertigoAdapter

class StatusGeneratorAdapter(BaseVertigoAdapter):
    """
    Adapter for testing Vertigo's executive status generation system.
    Tests status report generation from meeting data and analytics.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Status Generator Adapter."""
        super().__init__("StatusGenerator", config)
        
        # Mock status generation components (in production, this would integrate with real components)
        self.use_mock_generator = config.get("use_mock_generator", True) if config else True
        
        # Sample data for status generation
        self.sample_meeting_data = self._create_sample_meeting_data()
        
        self.logger.info("Initialized Status Generator Adapter")
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate status generation input data.
        
        Required fields:
        - time_period: Time period for the status (e.g., "daily", "weekly", "monthly")
        - projects: List of projects to include (optional)
        - status_type: Type of status report (e.g., "executive", "technical", "progress")
        """
        if not isinstance(input_data, dict):
            return False
        
        required_fields = ["time_period", "status_type"]
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        valid_periods = ["daily", "weekly", "monthly", "quarterly"]
        if input_data["time_period"] not in valid_periods:
            self.logger.error(f"Invalid time period: {input_data['time_period']}")
            return False
        
        valid_types = ["executive", "technical", "progress", "risk_summary", "team_summary"]
        if input_data["status_type"] not in valid_types:
            self.logger.error(f"Invalid status type: {input_data['status_type']}")
            return False
        
        return True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate status report based on input parameters.
        
        Args:
            input_data: Dict with status generation parameters
            
        Returns:
            Dict with generated status report and analysis
        """
        time_period = input_data["time_period"]
        status_type = input_data["status_type"]
        projects = input_data.get("projects", ["All Projects"])
        include_metrics = input_data.get("include_metrics", True)
        
        # Generate mock status report
        if self.use_mock_generator:
            status_report = self._generate_mock_status_report(
                time_period, status_type, projects, include_metrics
            )
        else:
            # In production, this would call actual status generation
            status_report = await self._call_real_status_generator(input_data)
        
        # Analyze the generated report
        analysis = {
            "input": {
                "time_period": time_period,
                "status_type": status_type,
                "projects": projects,
                "include_metrics": include_metrics
            },
            "output": status_report,
            "analysis": self._analyze_status_report(status_report, status_type),
            "test_metadata": {
                "report_generated": bool(status_report),
                "mock_response": self.use_mock_generator,
                "generation_successful": not isinstance(status_report, dict) or "error" not in status_report
            }
        }
        
        return analysis
    
    def _create_sample_meeting_data(self) -> List[Dict[str, Any]]:
        """Create sample meeting data for status generation."""
        return [
            {
                "date": "2024-01-10",
                "project": "Project Alpha",
                "meeting_type": "Sprint Planning",
                "participants": ["Product Manager", "Tech Lead", "Developers"],
                "key_outcomes": [
                    "Sprint goals defined for 2-week cycle",
                    "15 story points committed for development",
                    "Architecture review scheduled"
                ],
                "action_items": [
                    {"description": "Complete user authentication module", "owner": "John", "due": "2024-01-17"},
                    {"description": "Database schema finalization", "owner": "Sarah", "due": "2024-01-15"}
                ],
                "risks": ["Timeline may be tight with holiday schedules"],
                "decisions": ["Approved microservices architecture approach"]
            },
            {
                "date": "2024-01-12",
                "project": "Project Beta",
                "meeting_type": "Stakeholder Review",
                "participants": ["Executive Team", "Product Team"],
                "key_outcomes": [
                    "Q1 budget approved - $150K additional funding",
                    "Go-to-market strategy finalized",
                    "Launch date confirmed for March 1st"
                ],
                "action_items": [
                    {"description": "Marketing campaign development", "owner": "Marketing Team", "due": "2024-02-01"},
                    {"description": "Beta testing program setup", "owner": "QA Team", "due": "2024-01-25"}
                ],
                "risks": ["Competitive landscape changing rapidly"],
                "decisions": ["Approved accelerated launch timeline"]
            }
        ]
    
    def _generate_mock_status_report(self, time_period: str, status_type: str, 
                                   projects: List[str], include_metrics: bool) -> Dict[str, Any]:
        """
        Generate a realistic mock status report.
        
        Args:
            time_period: Time period for the report
            status_type: Type of status report
            projects: List of projects to include
            include_metrics: Whether to include metrics
            
        Returns:
            Mock status report dictionary
        """
        base_report = {
            "report_title": f"{status_type.title()} {time_period.title()} Status Report",
            "generated_date": datetime.utcnow().isoformat(),
            "time_period": time_period,
            "status_type": status_type,
            "projects_included": projects
        }
        
        # Status type specific content
        if status_type == "executive":
            return {
                **base_report,
                "executive_summary": f"Strong progress across all {len(projects)} projects this {time_period}. Key milestones achieved and on track for quarterly objectives.",
                "key_achievements": [
                    "Project Alpha: User authentication module completed ahead of schedule",
                    "Project Beta: Secured additional Q1 funding of $150K",
                    "Overall team productivity increased by 15%"
                ],
                "strategic_priorities": [
                    "Focus on Q1 product launch readiness",
                    "Scale team capabilities for upcoming projects",
                    "Strengthen competitive positioning"
                ],
                "financial_overview": {
                    "budget_status": "On track - 23% of Q1 budget utilized",
                    "cost_savings": "$25K saved through efficiency improvements",
                    "investment_requests": "Additional $50K requested for scaling infrastructure"
                } if include_metrics else None,
                "risk_summary": [
                    {"risk": "Market competition intensifying", "status": "Monitoring", "mitigation": "Accelerated feature development"},
                    {"risk": "Team capacity constraints", "status": "Active", "mitigation": "Approved hiring for 2 additional developers"}
                ],
                "next_period_priorities": [
                    "Complete Project Beta beta testing phase",
                    "Finalize Q2 strategic planning",
                    "Expand team with key technical hires"
                ]
            }
        
        elif status_type == "technical":
            return {
                **base_report,
                "technical_summary": f"Technical progress strong this {time_period} with major architecture decisions finalized and implementation proceeding on schedule.",
                "development_progress": [
                    "Microservices architecture implementation: 60% complete",
                    "Database migration: 85% complete", 
                    "API development: 40% complete",
                    "Frontend integration: 30% complete"
                ],
                "architecture_updates": [
                    "Finalized Docker containerization strategy",
                    "Kubernetes orchestration setup completed",
                    "CI/CD pipeline operational with 95% automation"
                ],
                "performance_metrics": {
                    "system_uptime": "99.8%",
                    "average_response_time": "180ms",
                    "error_rate": "0.2%",
                    "deployment_frequency": "3 deploys per week"
                } if include_metrics else None,
                "technical_debt": [
                    "Legacy authentication system: Scheduled for deprecation",
                    "Database query optimization: 15 queries identified for improvement"
                ],
                "security_updates": [
                    "Security audit completed - 2 minor vulnerabilities patched",
                    "OAuth2 implementation security review passed"
                ],
                "infrastructure_status": [
                    "Cloud costs optimized - 12% reduction achieved",
                    "Monitoring and alerting system enhanced",
                    "Backup and disaster recovery procedures updated"
                ]
            }
        
        elif status_type == "progress":
            return {
                **base_report,
                "overall_progress": f"Projects are progressing well this {time_period} with 85% of planned milestones achieved.",
                "project_status": [
                    {
                        "project": "Project Alpha",
                        "status": "On Track",
                        "completion": "65%",
                        "milestones_achieved": 4,
                        "milestones_planned": 6,
                        "next_milestone": "Beta release - Due Jan 25th"
                    },
                    {
                        "project": "Project Beta", 
                        "status": "Ahead of Schedule",
                        "completion": "75%",
                        "milestones_achieved": 6,
                        "milestones_planned": 7,
                        "next_milestone": "Stakeholder demo - Due Jan 30th"
                    }
                ],
                "timeline_analysis": {
                    "on_track_projects": 2,
                    "at_risk_projects": 0,
                    "delayed_projects": 0,
                    "average_completion": "70%"
                } if include_metrics else None,
                "resource_utilization": [
                    "Development team: 92% capacity utilization",
                    "Design team: 78% capacity utilization", 
                    "QA team: 85% capacity utilization"
                ],
                "blockers_resolved": [
                    "API access permissions - Resolved Jan 8th",
                    "Database performance issues - Resolved Jan 10th"
                ],
                "upcoming_milestones": [
                    {"milestone": "Project Alpha Beta Release", "due": "2024-01-25", "status": "On Track"},
                    {"milestone": "Project Beta Stakeholder Demo", "due": "2024-01-30", "status": "Ahead of Schedule"}
                ]
            }
        
        elif status_type == "risk_summary":
            return {
                **base_report,
                "risk_overview": f"Risk landscape manageable this {time_period} with proactive mitigation strategies in place.",
                "high_priority_risks": [
                    {
                        "risk": "Competitive market pressure increasing",
                        "probability": "High",
                        "impact": "High", 
                        "mitigation": "Accelerate feature development and marketing",
                        "owner": "Product Team",
                        "status": "Active monitoring"
                    },
                    {
                        "risk": "Key developer availability during holiday season",
                        "probability": "Medium",
                        "impact": "Medium",
                        "mitigation": "Cross-training and backup resources identified",
                        "owner": "Engineering Manager",
                        "status": "Mitigated"
                    }
                ],
                "risk_trends": {
                    "new_risks_identified": 2,
                    "risks_resolved": 3,
                    "risks_escalated": 0,
                    "overall_risk_score": "Medium"
                } if include_metrics else None,
                "mitigation_effectiveness": [
                    "Resource planning - 90% effective at preventing delays",
                    "Technical risk assessment - 85% accuracy in predictions",
                    "Market analysis - Monthly review cadence established"
                ],
                "contingency_plans": [
                    "Alternative vendor identified for third-party integrations",
                    "Backup developer pool available through consulting partners",
                    "Feature prioritization matrix ready for scope adjustments"
                ]
            }
        
        else:  # team_summary
            return {
                **base_report,
                "team_overview": f"Team performance strong this {time_period} with high collaboration and productivity metrics.",
                "team_metrics": {
                    "total_team_size": 12,
                    "active_contributors": 11,
                    "average_utilization": "88%",
                    "collaboration_score": "9.2/10"
                } if include_metrics else None,
                "achievements": [
                    "Cross-team collaboration improved with new daily standups",
                    "Knowledge sharing sessions introduced - 3 sessions this period",
                    "Team satisfaction survey: 4.6/5 average rating"
                ],
                "capacity_planning": [
                    "Current capacity adequate for Q1 objectives",
                    "2 additional developer positions approved for Q2",
                    "Design team expansion planned for March"
                ],
                "skill_development": [
                    "Kubernetes training completed by 4 team members",
                    "Security best practices workshop scheduled",
                    "Technical leadership mentoring program launched"
                ],
                "team_coordination": [
                    "Weekly all-hands meetings: 95% attendance",
                    "Project sync meetings: Streamlined to 30 minutes",
                    "Cross-project collaboration: 3 successful integrations"
                ],
                "upcoming_team_needs": [
                    "Senior frontend developer - Interviews scheduled",
                    "DevOps specialist - Job posting active",
                    "Technical writer - Proposal under review"
                ]
            }
    
    def _analyze_status_report(self, report: Dict[str, Any], status_type: str) -> Dict[str, Any]:
        """
        Analyze the quality and completeness of the generated status report.
        
        Args:
            report: Generated status report
            status_type: Type of status report
            
        Returns:
            Analysis of report quality
        """
        if isinstance(report, dict) and "error" in report:
            return {
                "has_error": True,
                "error_type": report.get("error", "Unknown error"),
                "completeness_score": 0.0
            }
        
        # Check for required sections based on status type
        expected_sections = self._get_expected_sections(status_type)
        found_sections = [section for section in expected_sections if section in report]
        missing_sections = [section for section in expected_sections if section not in report]
        
        completeness_score = len(found_sections) / len(expected_sections) if expected_sections else 1.0
        
        # Analyze content quality
        content_analysis = {
            "has_summary": any(key in report for key in ["executive_summary", "technical_summary", "overall_progress", "risk_overview", "team_overview"]),
            "has_metrics": any("metrics" in key or "status" in key for key in report.keys()),
            "has_action_items": any("action" in key.lower() or "next" in key.lower() for key in report.keys()),
            "structured_data": len([v for v in report.values() if isinstance(v, list)]) > 0,
            "quantitative_data": self._count_quantitative_data(report)
        }
        
        return {
            "has_error": False,
            "completeness_score": completeness_score,
            "expected_sections": expected_sections,
            "found_sections": found_sections,
            "missing_sections": missing_sections,
            "content_analysis": content_analysis,
            "report_length": len(str(report)),
            "section_count": len([k for k, v in report.items() if isinstance(v, (list, dict, str)) and v])
        }
    
    def _get_expected_sections(self, status_type: str) -> List[str]:
        """Get expected sections for each status report type."""
        section_mapping = {
            "executive": [
                "executive_summary", "key_achievements", "strategic_priorities", 
                "risk_summary", "next_period_priorities"
            ],
            "technical": [
                "technical_summary", "development_progress", "architecture_updates",
                "performance_metrics", "security_updates"
            ],
            "progress": [
                "overall_progress", "project_status", "resource_utilization",
                "upcoming_milestones"
            ],
            "risk_summary": [
                "risk_overview", "high_priority_risks", "mitigation_effectiveness",
                "contingency_plans"
            ],
            "team_summary": [
                "team_overview", "achievements", "capacity_planning",
                "skill_development", "team_coordination"
            ]
        }
        return section_mapping.get(status_type, [])
    
    def _count_quantitative_data(self, report: Dict[str, Any]) -> int:
        """Count quantitative data points in the report."""
        count = 0
        report_str = str(report).lower()
        
        # Look for numbers with units or percentages
        import re
        patterns = [
            r'\d+%',  # Percentages
            r'\$\d+[km]?',  # Money amounts
            r'\d+\.\d+',  # Decimals
            r'\d+ (days?|weeks?|months?|hours?|minutes?)',  # Time units
            r'\d+/\d+',  # Ratios
        ]
        
        for pattern in patterns:
            count += len(re.findall(pattern, report_str))
        
        return count
    
    async def _call_real_status_generator(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call real status generation system.
        In production, this would integrate with actual Vertigo components.
        """
        # TODO: Implement actual status generation integration
        return {"error": "Real status generation not implemented in test mode"}
    
    def create_test_scenarios(self) -> List[Dict[str, Any]]:
        """
        Create comprehensive test scenarios for status generation.
        
        Returns:
            List of test scenario dictionaries
        """
        scenarios = [
            # Different status types
            {
                "name": "Executive Daily Status",
                "time_period": "daily",
                "status_type": "executive",
                "projects": ["Project Alpha", "Project Beta"],
                "include_metrics": True,
                "scenario_type": "status_type_testing",
                "expected_sections": ["executive_summary", "key_achievements", "strategic_priorities"]
            },
            {
                "name": "Technical Weekly Status",
                "time_period": "weekly", 
                "status_type": "technical",
                "projects": ["All Projects"],
                "include_metrics": True,
                "scenario_type": "status_type_testing",
                "expected_sections": ["technical_summary", "development_progress", "architecture_updates"]
            },
            {
                "name": "Progress Monthly Status",
                "time_period": "monthly",
                "status_type": "progress",
                "projects": ["Project Alpha"],
                "include_metrics": True,
                "scenario_type": "status_type_testing",
                "expected_sections": ["overall_progress", "project_status", "upcoming_milestones"]
            },
            {
                "name": "Risk Summary Quarterly",
                "time_period": "quarterly",
                "status_type": "risk_summary",
                "projects": ["All Projects"],
                "include_metrics": False,
                "scenario_type": "status_type_testing",
                "expected_sections": ["risk_overview", "high_priority_risks", "mitigation_effectiveness"]
            },
            {
                "name": "Team Summary Weekly",
                "time_period": "weekly",
                "status_type": "team_summary",
                "projects": ["All Projects"],
                "include_metrics": True,
                "scenario_type": "status_type_testing",
                "expected_sections": ["team_overview", "achievements", "capacity_planning"]
            },
            
            # Different time periods
            {
                "name": "Daily Executive - No Metrics",
                "time_period": "daily",
                "status_type": "executive",
                "projects": ["Project Beta"],
                "include_metrics": False,
                "scenario_type": "time_period_testing",
                "expected_sections": ["executive_summary"]
            },
            {
                "name": "Monthly Technical - All Projects",
                "time_period": "monthly",
                "status_type": "technical",
                "projects": ["All Projects"],
                "include_metrics": True,
                "scenario_type": "time_period_testing",
                "expected_sections": ["technical_summary", "performance_metrics"]
            },
            
            # Edge cases
            {
                "name": "Single Project Focus",
                "time_period": "weekly",
                "status_type": "progress",
                "projects": ["Specific Single Project"],
                "include_metrics": True,
                "scenario_type": "edge_case_testing",
                "expected_sections": ["project_status"]
            },
            {
                "name": "Many Projects",
                "time_period": "monthly",
                "status_type": "executive",
                "projects": ["Project A", "Project B", "Project C", "Project D", "Project E"],
                "include_metrics": True,
                "scenario_type": "stress_testing",
                "expected_sections": ["executive_summary", "strategic_priorities"]
            }
        ]
        
        return scenarios
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        Run comprehensive test of all status generation scenarios.
        
        Returns:
            Comprehensive test results with analysis
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
        
        # Analyze results across status types and time periods
        analysis = self._analyze_comprehensive_results(results)
        
        return {
            "total_scenarios": len(scenarios),
            "individual_results": results,
            "comprehensive_analysis": analysis,
            "adapter_metrics": self.get_metrics()
        }
    
    def _analyze_comprehensive_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze results across all status generation scenarios.
        
        Returns:
            Comprehensive analysis of status generation performance
        """
        # Group by status type and time period
        by_status_type = {}
        by_time_period = {}
        by_scenario_type = {}
        
        completeness_scores = []
        
        for result_item in results:
            scenario = result_item["scenario"]
            result = result_item["result"]
            
            status_type = scenario["status_type"]
            time_period = scenario["time_period"] 
            scenario_type = scenario["scenario_type"]
            
            # Group results
            if status_type not in by_status_type:
                by_status_type[status_type] = []
            by_status_type[status_type].append(result)
            
            if time_period not in by_time_period:
                by_time_period[time_period] = []
            by_time_period[time_period].append(result)
            
            if scenario_type not in by_scenario_type:
                by_scenario_type[scenario_type] = []
            by_scenario_type[scenario_type].append(result)
            
            # Collect completeness scores
            if not result.get("error") and "analysis" in result:
                analysis = result["analysis"]
                if "completeness_score" in analysis:
                    completeness_scores.append(analysis["completeness_score"])
        
        # Analyze performance by status type
        status_type_analysis = {}
        for status_type, type_results in by_status_type.items():
            successful = sum(1 for r in type_results if not r.get("error"))
            avg_completeness = 0
            completeness_count = 0
            
            for r in type_results:
                if not r.get("error") and "analysis" in r and "completeness_score" in r["analysis"]:
                    avg_completeness += r["analysis"]["completeness_score"]
                    completeness_count += 1
            
            status_type_analysis[status_type] = {
                "total_tests": len(type_results),
                "successful_tests": successful,
                "success_rate": successful / len(type_results),
                "average_completeness": avg_completeness / completeness_count if completeness_count > 0 else 0
            }
        
        # Analyze performance by time period
        time_period_analysis = {}
        for time_period, period_results in by_time_period.items():
            successful = sum(1 for r in period_results if not r.get("error"))
            time_period_analysis[time_period] = {
                "total_tests": len(period_results),
                "successful_tests": successful,
                "success_rate": successful / len(period_results)
            }
        
        # Overall metrics
        overall_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        
        return {
            "overall_completeness_score": overall_completeness,
            "status_type_performance": status_type_analysis,
            "time_period_performance": time_period_analysis,
            "best_performing_status_type": max(status_type_analysis.keys(),
                                            key=lambda s: status_type_analysis[s]["success_rate"]) if status_type_analysis else None,
            "best_performing_time_period": max(time_period_analysis.keys(),
                                             key=lambda p: time_period_analysis[p]["success_rate"]) if time_period_analysis else None,
            "total_completeness_tests": len(completeness_scores)
        }