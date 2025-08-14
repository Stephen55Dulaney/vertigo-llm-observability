#!/usr/bin/env python3
"""
Production Evaluation Demo - Real-World Agent Testing
====================================================

This comprehensive demo shows how to evaluate your Vertigo agents in production-like
conditions. It combines all the concepts from the tutorials into a single, powerful
evaluation system.

Author: Claude Code  
Date: 2025-08-06

USAGE:
    cd /Users/stephendulaney/Documents/Vertigo/vertigo_scenario_framework
    python examples/production_evaluation_demo.py

This demonstrates:
1. Multi-dimensional agent evaluation
2. Business impact measurement
3. Performance monitoring
4. Comprehensive reporting
5. Production readiness assessment
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the parent directories to path
vertigo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(vertigo_root))
sys.path.insert(0, str(Path(__file__).parent.parent))

class ProductionEvaluationDemo:
    """
    Comprehensive production evaluation system for Vertigo agents.
    
    This class demonstrates professional-grade agent evaluation techniques
    that can be used in production environments.
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.results = {
            'evaluation_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'timestamp': datetime.utcnow().isoformat(),
            'components_tested': [],
            'overall_metrics': {},
            'detailed_results': {},
            'business_assessment': {},
            'recommendations': []
        }
        
        print("🏭 Production Evaluation Demo")
        print("=" * 50)
        print("This demo evaluates your Vertigo agents using production-grade techniques.")
        print("We'll test multiple dimensions: functionality, performance, and business value.")
        print()
    
    async def run_full_evaluation(self):
        """Run the complete production evaluation suite."""
        try:
            print("🚀 Starting Production Evaluation...")
            
            # 1. Email Processing Evaluation
            await self._evaluate_email_processing()
            
            # 2. Performance Analysis
            await self._evaluate_system_performance()
            
            # 3. Business Impact Assessment
            await self._assess_business_impact()
            
            # 4. Integration Health Check
            await self._check_integration_health()
            
            # 5. Generate Comprehensive Report
            self._generate_final_report()
            
            # 6. Save Results
            self._save_evaluation_results()
            
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            self._show_troubleshooting()
    
    async def _evaluate_email_processing(self):
        """Comprehensive email processing evaluation."""
        print("\n📧 Evaluating Email Processing System...")
        print("-" * 40)
        
        try:
            from adapters.email_processor_adapter import EmailProcessorAdapter
            adapter = EmailProcessorAdapter()
            
            # Run comprehensive email tests
            email_results = await adapter.run_comprehensive_test()
            
            self.results['components_tested'].append('email_processing')
            self.results['detailed_results']['email_processing'] = email_results
            
            # Extract key metrics
            success_rate = email_results.get('success_rate', 0)
            avg_response_time = email_results.get('average_response_time', 0)
            total_scenarios = email_results.get('total_scenarios', 0)
            
            print(f"✅ Email Processing Evaluation Complete")
            print(f"   • Success Rate: {success_rate:.1%}")
            print(f"   • Average Response Time: {avg_response_time:.3f}s")
            print(f"   • Scenarios Tested: {total_scenarios}")
            
            # Grade the email processing system
            email_grade = self._grade_email_performance(success_rate, avg_response_time)
            self.results['detailed_results']['email_processing']['grade'] = email_grade
            print(f"   • Overall Grade: {email_grade}")
            
        except Exception as e:
            print(f"❌ Email processing evaluation failed: {e}")
            self.results['detailed_results']['email_processing'] = {
                'error': str(e),
                'status': 'failed'
            }
    
    async def _evaluate_system_performance(self):
        """Evaluate system performance under various conditions."""
        print("\n⚡ Evaluating System Performance...")
        print("-" * 40)
        
        try:
            from adapters.email_processor_adapter import EmailProcessorAdapter
            adapter = EmailProcessorAdapter()
            
            # Performance test scenarios
            performance_tests = [
                {
                    'name': 'Basic Command Performance',
                    'test_data': {
                        'subject': 'Vertigo: Help',
                        'test_type': 'performance',
                        'iterations': 15
                    }
                },
                {
                    'name': 'Data-Heavy Command Performance', 
                    'test_data': {
                        'subject': 'Vertigo: Total stats',
                        'test_type': 'performance',
                        'iterations': 10
                    }
                }
            ]
            
            performance_results = []
            
            for test in performance_tests:
                print(f"🔄 Running: {test['name']}")
                result = await adapter.execute_with_metrics(test['test_data'])
                
                if result.get('success'):
                    perf_metrics = result['performance']
                    print(f"   ✅ Avg: {perf_metrics['avg_response_time']:.3f}s")
                    print(f"   📊 Success Rate: {perf_metrics['success_rate']:.1%}")
                    
                    # Add performance grade
                    perf_grade = self._grade_performance(perf_metrics['avg_response_time'])
                    result['performance_grade'] = perf_grade
                else:
                    print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                
                performance_results.append(result)
            
            self.results['detailed_results']['performance'] = {
                'tests': performance_results,
                'overall_performance_grade': self._calculate_overall_performance_grade(performance_results)
            }
            
            print(f"✅ Performance Evaluation Complete")
            
        except Exception as e:
            print(f"❌ Performance evaluation failed: {e}")
            self.results['detailed_results']['performance'] = {
                'error': str(e),
                'status': 'failed'
            }
    
    async def _assess_business_impact(self):
        """Assess the business impact and value of the agent system."""
        print("\n📊 Assessing Business Impact...")
        print("-" * 40)
        
        try:
            # Define business scenarios with different impact levels
            business_scenarios = [
                {
                    'name': 'Executive Decision Support',
                    'description': 'CEO needs weekly metrics for board presentation',
                    'scenario': {
                        'subject': 'Vertigo: List this week',
                        'test_type': 'full_processing'
                    },
                    'business_value': 'high',
                    'user_persona': 'C-Level Executive',
                    'time_sensitivity': 'critical',
                    'business_impact_score': 9
                },
                {
                    'name': 'Team Productivity Tracking',
                    'description': 'Manager needs project statistics for team review',
                    'scenario': {
                        'subject': 'Vertigo: Total stats', 
                        'test_type': 'full_processing'
                    },
                    'business_value': 'medium',
                    'user_persona': 'Team Manager',
                    'time_sensitivity': 'normal',
                    'business_impact_score': 6
                },
                {
                    'name': 'New User Onboarding',
                    'description': 'New team member learning available commands',
                    'scenario': {
                        'subject': 'Vertigo: Help',
                        'test_type': 'command_detection'
                    },
                    'business_value': 'medium',
                    'user_persona': 'New Employee',
                    'time_sensitivity': 'low',
                    'business_impact_score': 4
                }
            ]
            
            from adapters.email_processor_adapter import EmailProcessorAdapter
            adapter = EmailProcessorAdapter()
            
            business_results = []
            total_impact_score = 0
            successful_high_impact = 0
            total_high_impact = 0
            
            for scenario in business_scenarios:
                print(f"🎯 Testing: {scenario['name']}")
                print(f"   👤 User: {scenario['user_persona']}")
                print(f"   📈 Value: {scenario['business_value']}")
                
                result = await adapter.execute_with_metrics(scenario['scenario'])
                
                # Calculate business impact
                if result.get('success'):
                    actual_impact_score = scenario['business_impact_score']
                    print(f"   ✅ PASSED (Impact Score: {actual_impact_score})")
                    
                    if scenario['business_value'] == 'high':
                        successful_high_impact += 1
                else:
                    actual_impact_score = 0
                    print(f"   ❌ FAILED (Lost Impact: {scenario['business_impact_score']})")
                
                if scenario['business_value'] == 'high':
                    total_high_impact += 1
                
                total_impact_score += actual_impact_score
                
                result['business_context'] = scenario
                result['actual_impact_score'] = actual_impact_score
                business_results.append(result)
            
            # Calculate business metrics
            max_possible_impact = sum(s['business_impact_score'] for s in business_scenarios)
            business_impact_percentage = (total_impact_score / max_possible_impact) * 100 if max_possible_impact > 0 else 0
            high_impact_success_rate = (successful_high_impact / total_high_impact) * 100 if total_high_impact > 0 else 0
            
            business_assessment = {
                'total_impact_score': total_impact_score,
                'max_possible_impact': max_possible_impact,
                'business_impact_percentage': business_impact_percentage,
                'high_impact_success_rate': high_impact_success_rate,
                'business_readiness_grade': self._grade_business_readiness(business_impact_percentage, high_impact_success_rate),
                'scenario_results': business_results
            }
            
            self.results['business_assessment'] = business_assessment
            
            print(f"\n📈 Business Impact Results:")
            print(f"   • Overall Impact Score: {business_impact_percentage:.1f}%")
            print(f"   • High-Impact Success Rate: {high_impact_success_rate:.1f}%") 
            print(f"   • Business Readiness: {business_assessment['business_readiness_grade']}")
            
        except Exception as e:
            print(f"❌ Business assessment failed: {e}")
            self.results['business_assessment'] = {
                'error': str(e),
                'status': 'failed'
            }
    
    async def _check_integration_health(self):
        """Check the health of integrations and dependencies."""
        print("\n🔗 Checking Integration Health...")
        print("-" * 40)
        
        integration_health = {
            'firestore_connectivity': 'unknown',
            'email_parser_availability': 'unknown',
            'overall_integration_health': 'unknown'
        }
        
        try:
            # Test email parser availability
            from email_command_parser import EmailCommandParser
            parser = EmailCommandParser()
            integration_health['email_parser_availability'] = 'healthy'
            print("✅ Email Parser: Available")
            
            # Test basic functionality to infer Firestore connectivity
            result = parser.parse_command("Vertigo: Total stats")
            if result and 'error' not in result.get('body', '').lower():
                integration_health['firestore_connectivity'] = 'healthy'
                print("✅ Firestore: Connected")
            else:
                integration_health['firestore_connectivity'] = 'degraded'
                print("⚠️  Firestore: Connection issues detected")
                
        except Exception as e:
            integration_health['email_parser_availability'] = 'failed'
            print(f"❌ Email Parser: {e}")
        
        # Determine overall health
        if (integration_health['firestore_connectivity'] == 'healthy' and 
            integration_health['email_parser_availability'] == 'healthy'):
            integration_health['overall_integration_health'] = 'healthy'
            print("✅ Overall Integration Health: Healthy")
        else:
            integration_health['overall_integration_health'] = 'degraded'
            print("⚠️  Overall Integration Health: Issues detected")
        
        self.results['detailed_results']['integration_health'] = integration_health
    
    def _generate_final_report(self):
        """Generate comprehensive final evaluation report."""
        print("\n📋 Generating Final Report...")
        print("=" * 50)
        
        # Calculate overall metrics
        email_results = self.results['detailed_results'].get('email_processing', {})
        performance_results = self.results['detailed_results'].get('performance', {})
        business_assessment = self.results.get('business_assessment', {})
        integration_health = self.results['detailed_results'].get('integration_health', {})
        
        # Overall system grade
        grades = []
        if 'grade' in email_results:
            grades.append(self._grade_to_numeric(email_results['grade']))
        if 'overall_performance_grade' in performance_results:
            grades.append(self._grade_to_numeric(performance_results['overall_performance_grade']))
        if 'business_readiness_grade' in business_assessment:
            grades.append(self._grade_to_numeric(business_assessment['business_readiness_grade']))
        
        overall_numeric_grade = sum(grades) / len(grades) if grades else 0
        overall_grade = self._numeric_to_grade(overall_numeric_grade)
        
        # Production readiness assessment
        production_ready = self._assess_production_readiness(
            email_results, performance_results, business_assessment, integration_health
        )
        
        self.results['overall_metrics'] = {
            'overall_grade': overall_grade,
            'overall_numeric_grade': overall_numeric_grade,
            'production_ready': production_ready,
            'evaluation_duration': time.time() - self.start_time
        }
        
        # Generate recommendations
        self.results['recommendations'] = self._generate_recommendations(
            email_results, performance_results, business_assessment, integration_health
        )
        
        # Display final report
        self._display_final_report()
    
    def _display_final_report(self):
        """Display the final evaluation report."""
        print(f"🎯 FINAL EVALUATION REPORT")
        print("=" * 50)
        
        overall_metrics = self.results['overall_metrics']
        
        # Overall Results
        print(f"📊 OVERALL RESULTS:")
        print(f"   • System Grade: {overall_metrics['overall_grade']}")
        print(f"   • Production Ready: {'✅ YES' if overall_metrics['production_ready'] else '❌ NO'}")
        print(f"   • Evaluation Duration: {overall_metrics['evaluation_duration']:.1f}s")
        
        # Component Grades
        print(f"\n🔍 COMPONENT GRADES:")
        email_grade = self.results['detailed_results'].get('email_processing', {}).get('grade', 'N/A')
        perf_grade = self.results['detailed_results'].get('performance', {}).get('overall_performance_grade', 'N/A')
        biz_grade = self.results['business_assessment'].get('business_readiness_grade', 'N/A')
        
        print(f"   • Email Processing: {email_grade}")
        print(f"   • System Performance: {perf_grade}")
        print(f"   • Business Readiness: {biz_grade}")
        
        # Key Metrics
        print(f"\n📈 KEY METRICS:")
        email_results = self.results['detailed_results'].get('email_processing', {})
        if 'success_rate' in email_results:
            print(f"   • Email Success Rate: {email_results['success_rate']:.1%}")
        if 'average_response_time' in email_results:
            print(f"   • Avg Response Time: {email_results['average_response_time']:.3f}s")
        
        business_assessment = self.results.get('business_assessment', {})
        if 'business_impact_percentage' in business_assessment:
            print(f"   • Business Impact Score: {business_assessment['business_impact_percentage']:.1f}%")
        
        # Recommendations
        recommendations = self.results.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print(f"\n🎉 Evaluation Complete!")
        if overall_metrics['production_ready']:
            print("Your Vertigo system is ready for production use! 🚀")
        else:
            print("Address the recommendations above before production deployment. 🔧")
    
    def _save_evaluation_results(self):
        """Save detailed evaluation results to file."""
        results_dir = Path("evaluation_results")
        results_dir.mkdir(exist_ok=True)
        
        filename = f"production_evaluation_{self.results['evaluation_id']}.json"
        filepath = results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filepath}")
        print(f"   Use this file for historical tracking and trend analysis.")
    
    def _grade_email_performance(self, success_rate: float, avg_response_time: float) -> str:
        """Grade email processing performance."""
        if success_rate >= 0.98 and avg_response_time <= 0.5:
            return "A+"
        elif success_rate >= 0.95 and avg_response_time <= 1.0:
            return "A"
        elif success_rate >= 0.90 and avg_response_time <= 2.0:
            return "B"
        elif success_rate >= 0.80:
            return "C"
        else:
            return "F"
    
    def _grade_performance(self, avg_response_time: float) -> str:
        """Grade system performance."""
        if avg_response_time <= 0.1:
            return "A+"
        elif avg_response_time <= 0.5:
            return "A"
        elif avg_response_time <= 1.0:
            return "B"
        elif avg_response_time <= 2.0:
            return "C"
        else:
            return "F"
    
    def _grade_business_readiness(self, impact_percentage: float, high_impact_success: float) -> str:
        """Grade business readiness."""
        if impact_percentage >= 90 and high_impact_success >= 95:
            return "A+"
        elif impact_percentage >= 80 and high_impact_success >= 90:
            return "A"
        elif impact_percentage >= 70:
            return "B"
        elif impact_percentage >= 50:
            return "C"
        else:
            return "F"
    
    def _calculate_overall_performance_grade(self, performance_results: List[Dict]) -> str:
        """Calculate overall performance grade from multiple tests."""
        if not performance_results:
            return "F"
        
        grades = []
        for result in performance_results:
            if result.get('success') and 'performance_grade' in result:
                grades.append(self._grade_to_numeric(result['performance_grade']))
        
        if not grades:
            return "F"
        
        avg_grade = sum(grades) / len(grades)
        return self._numeric_to_grade(avg_grade)
    
    def _grade_to_numeric(self, grade: str) -> float:
        """Convert letter grade to numeric score."""
        grade_map = {"A+": 4.3, "A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
        return grade_map.get(grade, 0.0)
    
    def _numeric_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 4.1:
            return "A+"
        elif score >= 3.5:
            return "A"
        elif score >= 2.5:
            return "B"
        elif score >= 1.5:
            return "C"
        elif score >= 0.5:
            return "D"
        else:
            return "F"
    
    def _assess_production_readiness(self, email_results: Dict, performance_results: Dict, 
                                   business_assessment: Dict, integration_health: Dict) -> bool:
        """Assess overall production readiness."""
        # Minimum requirements for production
        email_success_rate = email_results.get('success_rate', 0)
        business_impact = business_assessment.get('business_impact_percentage', 0)
        integration_ok = integration_health.get('overall_integration_health') == 'healthy'
        
        return (email_success_rate >= 0.90 and 
                business_impact >= 70 and 
                integration_ok)
    
    def _generate_recommendations(self, email_results: Dict, performance_results: Dict,
                                business_assessment: Dict, integration_health: Dict) -> List[str]:
        """Generate actionable recommendations based on evaluation results."""
        recommendations = []
        
        # Email processing recommendations
        email_success_rate = email_results.get('success_rate', 0)
        if email_success_rate < 0.95:
            recommendations.append(f"Improve email success rate from {email_success_rate:.1%} to 95%+ by fixing failing test scenarios")
        
        avg_response_time = email_results.get('average_response_time', 0)
        if avg_response_time > 1.0:
            recommendations.append(f"Optimize response time from {avg_response_time:.2f}s to under 1.0s for better user experience")
        
        # Business impact recommendations
        business_impact = business_assessment.get('business_impact_percentage', 0)
        if business_impact < 80:
            recommendations.append(f"Increase business impact score from {business_impact:.1f}% to 80%+ by improving high-value scenario success rates")
        
        # Integration recommendations
        if integration_health.get('firestore_connectivity') != 'healthy':
            recommendations.append("Fix Firestore connectivity issues to ensure reliable data access")
        
        if integration_health.get('overall_integration_health') != 'healthy':
            recommendations.append("Address integration health issues before production deployment")
        
        # Performance recommendations
        perf_grade = performance_results.get('overall_performance_grade')
        if perf_grade and self._grade_to_numeric(perf_grade) < 3.0:
            recommendations.append("Improve system performance through optimization or infrastructure scaling")
        
        if not recommendations:
            recommendations.append("System is performing well! Consider setting up continuous monitoring and periodic evaluations")
        
        return recommendations
    
    def _show_troubleshooting(self):
        """Show troubleshooting help."""
        print(f"\n🛠️ Troubleshooting Guide:")
        print("=" * 30)
        print("If you're seeing errors:")
        print("1. Make sure you're in the Vertigo root directory")
        print("2. Run the setup script: python vertigo_scenario_framework/setup_scenario_framework.py")
        print("3. Check dependencies: pip install -r scenario_requirements.txt")
        print("4. Verify Firestore connectivity")
        print("5. Try the Hello World example first")

async def main():
    """Run the production evaluation demo."""
    demo = ProductionEvaluationDemo()
    await demo.run_full_evaluation()

if __name__ == "__main__":
    asyncio.run(main())