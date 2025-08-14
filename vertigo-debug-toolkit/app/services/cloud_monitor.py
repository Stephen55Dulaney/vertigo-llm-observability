"""
Cloud Service Monitor for Vertigo Debug Toolkit.

Monitors the health and status of all Vertigo cloud services deployed on Google Cloud Functions.
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class CloudServiceMonitor:
    """Monitor for Vertigo cloud services."""
    
    def __init__(self):
        self.project_id = "vertigo-466116"
        self.region = "us-central1"
        self.services = {
            "email_processor": {
                "name": "Email Processor",
                "url": f"https://{self.region}-{self.project_id}.cloudfunctions.net/email_processor",
                "description": "Processes incoming emails from vertigo.agent.2025@gmail.com",
                "critical": True,
                "expected_response_time": 30.0  # seconds
            },
            "meeting_processor_v2": {
                "name": "Meeting Processor v2",
                "url": f"https://{self.region}-{self.project_id}.cloudfunctions.net/meeting-processor-v2",
                "description": "Processes meeting transcripts and generates structured notes",
                "critical": True,
                "expected_response_time": 60.0  # seconds
            },
            "status_generator": {
                "name": "Status Generator",
                "url": f"https://{self.region}-{self.project_id}.cloudfunctions.net/status-generator",
                "description": "Generates status reports and creates Gmail drafts",
                "critical": True,
                "expected_response_time": 45.0  # seconds
            }
        }
    
    def check_service_health(self, service_key: str) -> Dict:
        """Check health of a specific service."""
        service = self.services.get(service_key)
        if not service:
            return {
                "service": service_key,
                "status": "unknown",
                "error": "Service not found in configuration"
            }
        
        try:
            start_time = datetime.now()
            
            # Send a health check request
            response = requests.get(
                service["url"],
                timeout=service["expected_response_time"],
                headers={"User-Agent": "Vertigo-Debug-Toolkit/1.0"}
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            if response.status_code == 200:
                return {
                    "service": service_key,
                    "name": service["name"],
                    "status": "healthy",
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "url": service["url"],
                    "description": service["description"],
                    "critical": service["critical"],
                    "last_check": datetime.now().isoformat()
                }
            else:
                return {
                    "service": service_key,
                    "name": service["name"],
                    "status": "unhealthy",
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "url": service["url"],
                    "description": service["description"],
                    "critical": service["critical"],
                    "error": f"HTTP {response.status_code}",
                    "last_check": datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            return {
                "service": service_key,
                "name": service["name"],
                "status": "timeout",
                "response_time": service["expected_response_time"],
                "url": service["url"],
                "description": service["description"],
                "critical": service["critical"],
                "error": f"Request timed out after {service['expected_response_time']}s",
                "last_check": datetime.now().isoformat()
            }
        except requests.exceptions.ConnectionError:
            return {
                "service": service_key,
                "name": service["name"],
                "status": "connection_error",
                "url": service["url"],
                "description": service["description"],
                "critical": service["critical"],
                "error": "Connection failed - service may be down",
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "service": service_key,
                "name": service["name"],
                "status": "error",
                "url": service["url"],
                "description": service["description"],
                "critical": service["critical"],
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def check_all_services(self) -> Dict:
        """Check health of all services."""
        results = {}
        overall_status = "healthy"
        critical_services_down = 0
        
        for service_key in self.services.keys():
            result = self.check_service_health(service_key)
            results[service_key] = result
            
            if result["status"] != "healthy" and result.get("critical", False):
                critical_services_down += 1
                overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "critical_services_down": critical_services_down,
            "total_services": len(self.services),
            "services": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def test_email_processor(self) -> Dict:
        """Test the email processor with a sample request."""
        service = self.services["email_processor"]
        
        # Create a test email processing request
        test_data = {
            "message": {
                "data": "test_message_data",
                "messageId": "test_message_id",
                "publishTime": datetime.now().isoformat()
            },
            "subscription": "projects/vertigo-466116/subscriptions/gmail-notifications"
        }
        
        try:
            response = requests.post(
                service["url"],
                json=test_data,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            return {
                "service": "email_processor",
                "test_status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code,
                "response": response.text[:500] if response.text else "No response body",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "service": "email_processor",
                "test_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def test_meeting_processor(self) -> Dict:
        """Test the meeting processor with a sample transcript."""
        service = self.services["meeting_processor_v2"]
        
        test_data = {
            "transcript": "Meeting started at 2:00 PM. John: 'We need to test the meeting processor.' Sarah: 'I agree, let's make sure it's working properly.' Meeting ended at 3:00 PM.",
            "transcript_type": "dictation",
            "project": "vertigo",
            "participants": ["John", "Sarah"],
            "duration_minutes": 60,
            "meeting_title": "Test Meeting"
        }
        
        try:
            response = requests.post(
                service["url"],
                json=test_data,
                timeout=60,
                headers={"Content-Type": "application/json"}
            )
            
            return {
                "service": "meeting_processor_v2",
                "test_status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code,
                "response": response.text[:500] if response.text else "No response body",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "service": "meeting_processor_v2",
                "test_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_gmail_status(self) -> Dict:
        """Check Gmail integration status."""
        try:
            # This would check if Gmail push notifications are working
            # For now, we'll return a basic status
            return {
                "gmail_integration": "configured",
                "push_notifications": "unknown",  # Would need to check Gmail API
                "last_email_check": "unknown",
                "unprocessed_emails": "unknown",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "gmail_integration": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_deployment_info(self) -> Dict:
        """Get deployment information for all services."""
        return {
            "project_id": self.project_id,
            "region": self.region,
            "services": {
                key: {
                    "name": service["name"],
                    "url": service["url"],
                    "description": service["description"],
                    "critical": service["critical"]
                }
                for key, service in self.services.items()
            },
            "deployment_info": {
                "runtime": "python310",
                "memory": "512MB",
                "timeout": "540s",
                "max_instances": "10"
            }
        } 