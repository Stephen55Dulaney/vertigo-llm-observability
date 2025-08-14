#!/usr/bin/env python3
"""
Thomas Bug Manager - Intelligent Bug Assignment and Escalation System
Part of the Vertigo Debug Toolkit

This module handles:
1. Bug classification and severity assessment
2. Intelligent agent assignment based on bug characteristics
3. Escalation protocols for critical issues
4. Automated reporting and notifications
"""

import json
import logging
import requests
import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Union
from enum import Enum
import sqlite3
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class BugCategory(Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    UI_UX = "ui_ux"
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    AUTHENTICATION = "authentication"
    API_FORMAT = "api_format"
    ERROR_HANDLING = "error_handling"
    CONNECTIVITY = "connectivity"

class Agent(Enum):
    SPEC = "spec"           # Security/Code Auditor
    HUE = "hue"             # Visual Design Reviewer
    PROBE = "probe"         # System Tester (Performance)
    CUSTODIA = "custodia"   # Cleanup Agent
    FORGE = "forge"         # Critical Thinking Analyzer
    HUMAN = "human"         # Human escalation

class BugStatus(Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

@dataclass
class Bug:
    """Represents a bug found by Thomas"""
    id: str
    title: str
    description: str
    severity: Severity
    category: BugCategory
    endpoint: str
    status: BugStatus
    assigned_agent: Optional[Agent] = None
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None
    reproduction_steps: List[str] = None
    evidence: Dict = None
    estimated_effort_hours: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.reproduction_steps is None:
            self.reproduction_steps = []
        if self.evidence is None:
            self.evidence = {}

class ThomasBugManager:
    """Main bug management system for Thomas"""
    
    def __init__(self, db_path: str = "./thomas_bugs.db", base_url: str = "http://localhost:5000"):
        self.db_path = db_path
        self.base_url = base_url
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._init_database()
        
        # Agent assignment rules based on bug characteristics
        self.assignment_rules = {
            BugCategory.SECURITY: Agent.SPEC,
            BugCategory.AUTHENTICATION: Agent.SPEC,
            BugCategory.PERFORMANCE: Agent.PROBE,
            BugCategory.UI_UX: Agent.HUE,
            BugCategory.CODE_QUALITY: Agent.CUSTODIA,
            BugCategory.ERROR_HANDLING: Agent.CUSTODIA,
            BugCategory.ARCHITECTURE: Agent.FORGE,
            BugCategory.CONNECTIVITY: Agent.FORGE,
            BugCategory.API_FORMAT: Agent.CUSTODIA,
        }
        
        # Escalation thresholds
        self.escalation_rules = {
            "critical_threshold": 1,  # Any critical bug escalates immediately
            "high_cluster_threshold": 3,  # 3+ high severity bugs in same category
            "security_immediate": True,  # All critical security bugs escalate immediately
            "performance_degradation_threshold": 5.0,  # 5+ second response times
        }
    
    def _init_database(self):
        """Initialize SQLite database for bug tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bugs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_agent TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                reproduction_steps TEXT,
                evidence TEXT,
                estimated_effort_hours INTEGER DEFAULT 0,
                session_id TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bug_ids TEXT NOT NULL,
                reason TEXT NOT NULL,
                escalated_at TEXT NOT NULL,
                resolved_at TEXT,
                session_id TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def create_bug(self, 
                   title: str,
                   description: str,
                   severity: Union[Severity, str],
                   category: Union[BugCategory, str],
                   endpoint: str,
                   reproduction_steps: List[str] = None,
                   evidence: Dict = None) -> Bug:
        """Create a new bug with automatic ID generation and assignment"""
        
        # Convert string inputs to enums if needed
        if isinstance(severity, str):
            severity = Severity(severity.lower())
        if isinstance(category, str):
            category = BugCategory(category.lower())
        
        # Generate unique bug ID
        bug_id = f"BUG-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(title) % 10000:04d}"
        
        # Create bug object
        bug = Bug(
            id=bug_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            endpoint=endpoint,
            status=BugStatus.NEW,
            reproduction_steps=reproduction_steps or [],
            evidence=evidence or {}
        )
        
        # Auto-assign based on category
        bug.assigned_agent = self._assign_agent(bug)
        bug.status = BugStatus.ASSIGNED
        
        # Estimate effort
        bug.estimated_effort_hours = self._estimate_effort(bug)
        
        # Save to database
        self._save_bug(bug)
        
        # Check for escalation
        self._check_escalation(bug)
        
        logger.info(f"Bug created: {bug.id} - {bug.title} (assigned to {bug.assigned_agent.value})")
        return bug
    
    def _assign_agent(self, bug: Bug) -> Agent:
        """Assign bug to appropriate agent based on category and severity"""
        
        # Critical security issues always go to human first
        if bug.severity == Severity.CRITICAL and bug.category == BugCategory.SECURITY:
            return Agent.HUMAN
        
        # Use standard assignment rules
        agent = self.assignment_rules.get(bug.category, Agent.CUSTODIA)
        
        # Override for critical issues
        if bug.severity == Severity.CRITICAL:
            if bug.category in [BugCategory.AUTHENTICATION, BugCategory.CONNECTIVITY]:
                return Agent.HUMAN
        
        return agent
    
    def _estimate_effort(self, bug: Bug) -> int:
        """Estimate effort in hours based on severity and category"""
        base_effort = {
            Severity.CRITICAL: 8,
            Severity.HIGH: 4, 
            Severity.MEDIUM: 2,
            Severity.LOW: 1
        }
        
        category_multiplier = {
            BugCategory.SECURITY: 1.5,
            BugCategory.ARCHITECTURE: 2.0,
            BugCategory.PERFORMANCE: 1.2,
            BugCategory.UI_UX: 0.8,
            BugCategory.CODE_QUALITY: 0.6,
        }
        
        effort = base_effort.get(bug.severity, 2)
        multiplier = category_multiplier.get(bug.category, 1.0)
        
        return int(effort * multiplier)
    
    def _save_bug(self, bug: Bug):
        """Save bug to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO bugs 
            (id, title, description, severity, category, endpoint, status, 
             assigned_agent, created_at, updated_at, reproduction_steps, 
             evidence, estimated_effort_hours, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bug.id,
            bug.title,
            bug.description,
            bug.severity.value,
            bug.category.value,
            bug.endpoint,
            bug.status.value,
            bug.assigned_agent.value if bug.assigned_agent else None,
            bug.created_at.isoformat(),
            bug.updated_at.isoformat(),
            json.dumps(bug.reproduction_steps),
            json.dumps(bug.evidence),
            bug.estimated_effort_hours,
            self.session_id
        ))
        
        conn.commit()
        conn.close()
    
    def _check_escalation(self, bug: Bug):
        """Check if bug should be escalated based on rules"""
        escalation_reasons = []
        
        # Critical bug escalation
        if bug.severity == Severity.CRITICAL:
            escalation_reasons.append(f"Critical severity bug: {bug.title}")
        
        # Security escalation
        if (bug.category == BugCategory.SECURITY and 
            bug.severity in [Severity.CRITICAL, Severity.HIGH]):
            escalation_reasons.append(f"High/Critical security issue: {bug.title}")
        
        # Check for bug clusters
        similar_bugs = self.get_bugs_by_category(bug.category, [BugStatus.NEW, BugStatus.ASSIGNED, BugStatus.IN_PROGRESS])
        high_severity_count = len([b for b in similar_bugs if b.severity == Severity.HIGH])
        
        if high_severity_count >= self.escalation_rules["high_cluster_threshold"]:
            escalation_reasons.append(f"High severity bug cluster in {bug.category.value}: {high_severity_count} bugs")
        
        # Escalate if needed
        if escalation_reasons:
            self._escalate_bug(bug, escalation_reasons)
    
    def _escalate_bug(self, bug: Bug, reasons: List[str]):
        """Escalate bug to human attention"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO escalations (bug_ids, reason, escalated_at, session_id)
            VALUES (?, ?, ?, ?)
        ''', (
            bug.id,
            "; ".join(reasons),
            datetime.datetime.utcnow().isoformat(),
            self.session_id
        ))
        
        conn.commit()
        conn.close()
        
        # Update bug status
        bug.status = BugStatus.ESCALATED
        bug.assigned_agent = Agent.HUMAN
        bug.updated_at = datetime.datetime.utcnow()
        self._save_bug(bug)
        
        # Send notification
        self._send_escalation_notification(bug, reasons)
        
        logger.warning(f"Bug escalated: {bug.id} - Reasons: {'; '.join(reasons)}")
    
    def _send_escalation_notification(self, bug: Bug, reasons: List[str]):
        """Send escalation notification (placeholder for real implementation)"""
        notification = {
            "type": "bug_escalation",
            "bug_id": bug.id,
            "title": bug.title,
            "severity": bug.severity.value,
            "category": bug.category.value,
            "endpoint": bug.endpoint,
            "reasons": reasons,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "session_id": self.session_id
        }
        
        logger.critical(f"ESCALATION NOTIFICATION: {json.dumps(notification, indent=2)}")
        
        # In real implementation, this would send to Slack, email, etc.
        try:
            # Placeholder for notification system
            print(f"\n🚨 ESCALATION ALERT 🚨")
            print(f"Bug ID: {bug.id}")
            print(f"Title: {bug.title}")
            print(f"Severity: {bug.severity.value.upper()}")
            print(f"Category: {bug.category.value}")
            print(f"Reasons: {'; '.join(reasons)}")
            print(f"Endpoint: {bug.endpoint}")
            print(f"Description: {bug.description}")
            print("=" * 50)
        except Exception as e:
            logger.error(f"Failed to send escalation notification: {e}")
    
    def get_bugs_by_category(self, category: BugCategory, statuses: List[BugStatus] = None) -> List[Bug]:
        """Get bugs by category and optional status filter"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if statuses:
            status_placeholders = ','.join(['?' for _ in statuses])
            cursor.execute(f'''
                SELECT * FROM bugs 
                WHERE category = ? AND status IN ({status_placeholders})
            ''', [category.value] + [s.value for s in statuses])
        else:
            cursor.execute('SELECT * FROM bugs WHERE category = ?', (category.value,))
        
        rows = cursor.fetchall()
        conn.close()
        
        bugs = []
        for row in rows:
            bug = Bug(
                id=row[0],
                title=row[1],
                description=row[2],
                severity=Severity(row[3]),
                category=BugCategory(row[4]),
                endpoint=row[5],
                status=BugStatus(row[6]),
                assigned_agent=Agent(row[7]) if row[7] else None,
                created_at=datetime.datetime.fromisoformat(row[8]),
                updated_at=datetime.datetime.fromisoformat(row[9]),
                reproduction_steps=json.loads(row[10]) if row[10] else [],
                evidence=json.loads(row[11]) if row[11] else {},
                estimated_effort_hours=row[12]
            )
            bugs.append(bug)
        
        return bugs
    
    def generate_report(self) -> Dict:
        """Generate comprehensive bug report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all bugs for current session
        cursor.execute('SELECT * FROM bugs WHERE session_id = ?', (self.session_id,))
        all_bugs = cursor.fetchall()
        
        # Get escalations
        cursor.execute('SELECT * FROM escalations WHERE session_id = ?', (self.session_id,))
        escalations = cursor.fetchall()
        
        conn.close()
        
        # Process statistics
        stats = {
            "total_bugs": len(all_bugs),
            "by_severity": {},
            "by_category": {},
            "by_agent": {},
            "by_status": {},
            "escalations": len(escalations),
            "estimated_total_effort": 0
        }
        
        for bug_row in all_bugs:
            severity = bug_row[3]
            category = bug_row[4]
            agent = bug_row[7]
            status = bug_row[6]
            effort = bug_row[12]
            
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            if agent:
                stats["by_agent"][agent] = stats["by_agent"].get(agent, 0) + 1
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["estimated_total_effort"] += effort
        
        # Generate recommendations
        recommendations = []
        
        if stats["by_severity"].get("critical", 0) > 0:
            recommendations.append({
                "priority": "immediate",
                "action": f"Address {stats['by_severity']['critical']} critical security issues",
                "urgency": "critical"
            })
        
        if stats["by_severity"].get("high", 0) > 2:
            recommendations.append({
                "priority": "high",
                "action": f"Review {stats['by_severity']['high']} high priority issues for clustering",
                "urgency": "high"
            })
        
        if stats["by_category"].get("security", 0) > 0:
            recommendations.append({
                "priority": "high",
                "action": "Conduct security audit of authentication and input validation",
                "urgency": "high"
            })
        
        report = {
            "session_id": self.session_id,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "statistics": stats,
            "recommendations": recommendations,
            "escalations": [
                {
                    "bug_ids": esc[1],
                    "reason": esc[2],
                    "escalated_at": esc[3]
                } for esc in escalations
            ]
        }
        
        return report
    
    def save_report(self, report: Dict, filename: str = None):
        """Save report to file"""
        if filename is None:
            filename = f"thomas_report_{self.session_id}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {filename}")
        return filename

# CLI Interface
def main():
    """Command line interface for Thomas Bug Manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Thomas Bug Manager")
    parser.add_argument("--create-bug", action="store_true", help="Create a new bug interactively")
    parser.add_argument("--generate-report", action="store_true", help="Generate bug report")
    parser.add_argument("--list-bugs", action="store_true", help="List all bugs")
    parser.add_argument("--db-path", default="./thomas_bugs.db", help="Database path")
    
    args = parser.parse_args()
    
    manager = ThomasBugManager(db_path=args.db_path)
    
    if args.create_bug:
        # Interactive bug creation
        print("=== Thomas Bug Manager - Create Bug ===")
        title = input("Bug Title: ")
        description = input("Description: ")
        severity = input("Severity (critical/high/medium/low): ").lower()
        category = input("Category (security/performance/ui_ux/code_quality/architecture): ").lower()
        endpoint = input("Endpoint: ")
        
        bug = manager.create_bug(title, description, severity, category, endpoint)
        print(f"Bug created: {bug.id}")
    
    elif args.generate_report:
        report = manager.generate_report()
        filename = manager.save_report(report)
        print(f"Report generated: {filename}")
        
        # Print summary
        print("\n=== Bug Summary ===")
        print(f"Total Bugs: {report['statistics']['total_bugs']}")
        print(f"Critical: {report['statistics']['by_severity'].get('critical', 0)}")
        print(f"High: {report['statistics']['by_severity'].get('high', 0)}")
        print(f"Medium: {report['statistics']['by_severity'].get('medium', 0)}")
        print(f"Low: {report['statistics']['by_severity'].get('low', 0)}")
        print(f"Escalations: {report['statistics']['escalations']}")
        print(f"Estimated Effort: {report['statistics']['estimated_total_effort']} hours")
    
    elif args.list_bugs:
        # This would list all bugs - simplified for demo
        print("Bug listing not implemented in demo")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()