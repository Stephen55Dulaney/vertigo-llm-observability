# Vertigo Issue Management System

## 🎯 **System Overview**

The Vertigo Issue Management System provides comprehensive tracking, assignment, and resolution of bugs, features, and research tasks across the Vertigo ecosystem. It integrates with both the Debug Toolkit dashboard and Google Cloud Firestore for persistent, scalable issue management.

---

## 📊 **Issue Classification System**

### **Issue Types**
```python
ISSUE_TYPES = {
    "bug": {
        "description": "Defects, errors, or unexpected behavior",
        "priority_default": "high",
        "template": "bug_report_template",
        "sla_hours": {"critical": 4, "high": 24, "medium": 72, "low": 168}
    },
    "feature": {
        "description": "New functionality or enhancement requests", 
        "priority_default": "medium",
        "template": "feature_request_template",
        "sla_hours": {"critical": 24, "high": 72, "medium": 168, "low": 336}
    },
    "research": {
        "description": "Investigation, analysis, or exploration tasks",
        "priority_default": "low", 
        "template": "research_task_template",
        "sla_hours": {"high": 48, "medium": 120, "low": 240}
    },
    "enhancement": {
        "description": "Improvements to existing functionality",
        "priority_default": "medium",
        "template": "enhancement_template", 
        "sla_hours": {"high": 48, "medium": 96, "low": 240}
    },
    "maintenance": {
        "description": "Code cleanup, refactoring, technical debt",
        "priority_default": "low",
        "template": "maintenance_template",
        "sla_hours": {"medium": 120, "low": 240}
    }
}
```

### **Priority Matrix**
```
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│   IMPACT    │  CRITICAL   │    HIGH     │   MEDIUM    │     LOW     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ System Down │ CRITICAL    │ CRITICAL    │    HIGH     │   MEDIUM    │
│ Major Bug   │ CRITICAL    │    HIGH     │   MEDIUM    │     LOW     │
│ Minor Bug   │    HIGH     │   MEDIUM    │     LOW     │     LOW     │
│ Enhancement │   MEDIUM    │   MEDIUM    │     LOW     │     LOW     │
│ Nice to Have│     LOW     │     LOW     │     LOW     │     LOW     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

---

## 🗄️ **Data Storage Architecture**

### **Firestore Collections Structure**
```javascript
// Primary Issues Collection
issues/{issueId} = {
  // Identity & Classification
  id: "ISS-2025-08-001",
  title: "Advanced evaluation report generation error",
  description: "Error: '>' not supported between instances of 'st' and 'int'",
  type: "bug",
  priority: "critical",
  severity: "high",
  
  // Status & Lifecycle
  status: "open", // open, assigned, in_progress, testing, closed, reopened
  created_at: "2025-08-02T10:00:00Z",
  updated_at: "2025-08-02T14:30:00Z",
  resolved_at: null,
  closed_at: null,
  
  // Assignment & Ownership
  assigned_to: "database-agent",
  assigned_at: "2025-08-02T10:15:00Z", 
  created_by: "orchestrator",
  
  // Context & Details
  component: "debug-toolkit", // debug-toolkit, core-services, evaluation, ui
  affected_files: [
    "app/services/prompt_evaluator.py",
    "app/models.py"
  ],
  
  // User Story Format
  user_story: {
    as_a: "product manager",
    i_want: "to generate evaluation reports successfully", 
    so_that: "I can analyze prompt performance and make data-driven decisions"
  },
  
  // Technical Details
  technical_details: {
    error_message: "Error: '>' not supported between instances of 'st' and 'int'",
    stack_trace: "...",
    file_path: "app/services/prompt_evaluator.py",
    line_number: 311,
    function_name: "generate_evaluation_report",
    environment: "localhost:8080",
    browser: "Chrome 118.0.0.0"
  },
  
  // Reproduction Information
  reproduction: {
    steps: [
      "Navigate to http://localhost:8080/dashboard/advanced-evaluation",
      "Select any prompt from dropdown", 
      "Click 'Generate Report' button",
      "Observe error in console/UI"
    ],
    expected_behavior: "Report generates successfully with all metrics",
    actual_behavior: "Error thrown, report generation fails",
    frequency: "always",
    first_occurrence: "2025-08-02T09:00:00Z"
  },
  
  // Requirements & Acceptance
  acceptance_criteria: [
    "Report generation completes without errors",
    "All performance metrics display correctly", 
    "View Report button functions properly",
    "No console errors during operation"
  ],
  
  // Estimation & Planning
  estimated_hours: 4,
  actual_hours: null,
  story_points: 5,
  sprint: "2025-08-Sprint-1",
  epic: "evaluation-system-improvements",
  
  // Dependencies & Relationships
  depends_on: [],
  blocks: ["ISS-2025-08-002"],
  related_issues: ["ISS-2025-07-045"],
  duplicate_of: null,
  
  // Labels & Categorization
  labels: ["evaluation", "database", "urgent", "schema-fix"],
  tags: ["backend", "firestore", "langfuse"],
  
  // Progress Tracking
  progress_percentage: 25,
  progress_notes: [
    {
      timestamp: "2025-08-02T11:00:00Z",
      author: "database-agent",
      note: "Identified root cause: Trace model schema mismatch",
      type: "analysis"
    },
    {
      timestamp: "2025-08-02T14:00:00Z", 
      author: "database-agent",
      note: "Working on schema alignment - updating PromptEvaluator to use correct fields",
      type: "progress"
    }
  ],
  
  // Quality & Testing
  test_cases: [
    {
      name: "Report generation with valid data",
      steps: ["Select prompt", "Click generate", "Verify report appears"],
      expected: "Report displays successfully"
    }
  ],
  
  // Documentation & Communication
  documentation_updates: [],
  communication_log: [],
  
  // Metrics & Analytics
  metrics: {
    time_to_assignment: 15, // minutes
    time_to_first_response: 45, // minutes  
    resolution_time: null,
    reopened_count: 0,
    comment_count: 3
  }
}

// Agent Assignments Collection
agent_assignments/{agentId} = {
  agent_id: "database-agent",
  current_assignments: [
    {
      issue_id: "ISS-2025-08-001",
      assigned_at: "2025-08-02T10:15:00Z",
      priority: "critical",
      estimated_hours: 4
    }
  ],
  completed_assignments: [],
  workload_metrics: {
    total_active_hours: 12,
    capacity_hours: 40,
    utilization_percentage: 30
  },
  performance_metrics: {
    average_resolution_time: 18.5, // hours
    quality_score: 8.7,
    on_time_completion_rate: 0.85
  }
}

// Issue Analytics Collection
issue_analytics/summary = {
  total_issues: 156,
  open_issues: 23,
  in_progress_issues: 8,
  closed_issues: 125,
  
  by_priority: {
    critical: 2,
    high: 6, 
    medium: 12,
    low: 3
  },
  
  by_component: {
    "debug-toolkit": 8,
    "core-services": 6,
    "evaluation": 5,
    "ui": 4
  },
  
  by_agent: {
    "ux-agent": 5,
    "database-agent": 7,
    "evaluation-agent": 6,
    "devops-agent": 3,
    "integration-agent": 2
  },
  
  performance_metrics: {
    average_resolution_time: 2.3, // days
    sla_compliance_rate: 0.92,
    reopened_rate: 0.05
  }
}
```

---

## 📝 **Issue Templates**

### **Bug Report Template**
```markdown
# Bug Report: [Brief Description]

## 🐛 Issue Classification
- **Type**: Bug
- **Priority**: [Critical/High/Medium/Low]
- **Component**: [debug-toolkit/core-services/evaluation/ui]
- **Affected Version**: [Version/Branch]

## 👤 User Story
**As a** [role]  
**I want** [functionality]  
**So that** [benefit/outcome]

## 🔍 Current Behavior
[Describe what currently happens - be specific]

## ✅ Expected Behavior  
[Describe what should happen instead]

## 🔄 Steps to Reproduce
1. [First step]
2. [Second step]
3. [Third step]
4. [Observe the error]

## 💻 Technical Details
- **Error Message**: `[Exact error message]`
- **File/Location**: `[file_path:line_number]`
- **Browser**: [Chrome/Firefox/Safari version]
- **Environment**: [localhost/staging/production]
- **Stack Trace**: 
  ```
  [Paste stack trace if available]
  ```

## 📋 Acceptance Criteria
- [ ] [Specific outcome 1]
- [ ] [Specific outcome 2] 
- [ ] [Specific outcome 3]

## 🔧 Additional Context
[Any other relevant information, screenshots, logs]

## 🏷️ Labels
[Add relevant labels: urgent, database, ui, evaluation, etc.]
```

### **Feature Request Template**
```markdown
# Feature Request: [Feature Name]

## 🎯 Feature Classification
- **Type**: Feature
- **Priority**: [High/Medium/Low]
- **Component**: [debug-toolkit/core-services/evaluation/ui]
- **Epic**: [Related epic/theme]

## 👤 User Story
**As a** [role]  
**I want** [functionality]  
**So that** [benefit/outcome]

## 💡 Feature Description
[Detailed description of the requested feature]

## 🎨 Proposed Solution
[How you envision this feature working]

## 📋 Acceptance Criteria
- [ ] [Specific requirement 1]
- [ ] [Specific requirement 2]
- [ ] [Specific requirement 3]

## 🔧 Technical Requirements
- [Technical constraint 1]
- [Technical constraint 2]
- [Performance requirement]

## 📈 Success Metrics
- [How will we measure success]
- [Key performance indicators]

## 🔗 Dependencies
- [List any dependencies on other features/fixes]

## 🎯 Out of Scope
- [What this feature will NOT include]

## 🏷️ Labels
[Add relevant labels: enhancement, ui, evaluation, etc.]
```

### **Research Task Template**
```markdown
# Research Task: [Research Topic]

## 🔬 Research Classification
- **Type**: Research
- **Priority**: [High/Medium/Low]
- **Category**: [technical/user/market/competitive]
- **Timeline**: [Expected completion timeframe]

## 🎯 Research Objective
[What question are we trying to answer?]

## 📋 Research Questions
1. [Specific question 1]
2. [Specific question 2]
3. [Specific question 3]

## 🔍 Research Approach
[How will this research be conducted?]

## 📊 Expected Deliverables
- [ ] [Research report]
- [ ] [Recommendations document]
- [ ] [Technical specification]
- [ ] [Prototype/proof of concept]

## 📈 Success Criteria
- [How will we know this research is complete and successful?]

## 🔗 Related Issues
- [Link to related bugs, features, or other research]

## 🏷️ Labels
[Add relevant labels: research, investigation, analysis, etc.]
```

---

## 🤖 **Agent Assignment Logic**

### **Automatic Assignment Rules**
```python
class IssueAssignmentEngine:
    """Intelligent issue assignment based on content analysis and agent capacity"""
    
    def __init__(self):
        self.agent_specializations = {
            "ux-agent": {
                "keywords": ["ui", "button", "form", "styling", "css", "html", "frontend", "design"],
                "components": ["ui", "templates", "static"],
                "issue_types": ["bug", "enhancement", "feature"],
                "max_capacity": 3
            },
            "database-agent": {
                "keywords": ["firestore", "schema", "query", "database", "collection", "model"],
                "components": ["core-services", "database"],
                "issue_types": ["bug", "enhancement", "maintenance"],
                "max_capacity": 3
            },
            "evaluation-agent": {
                "keywords": ["prompt", "evaluation", "langfuse", "a/b test", "performance", "llm"],
                "components": ["evaluation", "debug-toolkit"],
                "issue_types": ["bug", "feature", "research"],
                "max_capacity": 3
            },
            "devops-agent": {
                "keywords": ["deploy", "cloud", "function", "monitoring", "performance", "gcp"],
                "components": ["core-services", "deployment"],
                "issue_types": ["bug", "maintenance", "enhancement"],
                "max_capacity": 2
            },
            "integration-agent": {
                "keywords": ["api", "webhook", "sync", "endpoint", "service", "integration"],
                "components": ["core-services", "debug-toolkit"],
                "issue_types": ["bug", "feature", "enhancement"],
                "max_capacity": 4
            }
        }
        
    def analyze_issue_content(self, issue: dict):
        """Analyze issue content to determine best agent match"""
        content = f"{issue['title']} {issue['description']}".lower()
        
        agent_scores = {}
        
        for agent, spec in self.agent_specializations.items():
            score = 0
            
            # Keyword matching
            keyword_matches = sum(1 for keyword in spec["keywords"] if keyword in content)
            score += keyword_matches * 2
            
            # Component matching  
            if issue.get("component") in spec["components"]:
                score += 5
                
            # Issue type matching
            if issue.get("type") in spec["issue_types"]:
                score += 3
                
            agent_scores[agent] = score
            
        return agent_scores
        
    def get_optimal_assignment(self, issue: dict):
        """Get optimal agent assignment considering content and capacity"""
        content_scores = self.analyze_issue_content(issue)
        
        # Filter by capacity
        available_agents = []
        for agent, score in content_scores.items():
            current_workload = self.get_agent_workload(agent)
            max_capacity = self.agent_specializations[agent]["max_capacity"]
            
            if current_workload < max_capacity:
                available_agents.append({
                    "agent": agent,
                    "content_score": score,
                    "workload": current_workload,
                    "capacity_remaining": max_capacity - current_workload
                })
        
        if not available_agents:
            return None  # All agents at capacity
            
        # Sort by content score, then by available capacity
        available_agents.sort(
            key=lambda x: (x["content_score"], x["capacity_remaining"]), 
            reverse=True
        )
        
        return available_agents[0]["agent"]
        
    def get_agent_workload(self, agent: str):
        """Get current workload for specific agent"""
        # Query Firestore for current assignments
        assignments = self.db.collection("agent_assignments").document(agent).get()
        if assignments.exists:
            return len(assignments.to_dict().get("current_assignments", []))
        return 0
```

---

## 📊 **Issue Dashboard Integration**

### **Dashboard Layout**
```
┌─────────────────────────────────────────────────────────────────┐
│                      ISSUE MANAGEMENT HUB                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─ ISSUE STATS ───────┐  ┌─ PRIORITY QUEUE ──┐  ┌─ AGENT STATUS ┐ │
│ │ Total: 23 Open      │  │ 🔴 Critical: 2   │  │ UX: 2/3 tasks  │ │
│ │ Bugs: 8 Features: 6 │  │ 🟠 High: 6      │  │ DB: 3/3 tasks  │ │
│ │ Research: 3 Maint: 6│  │ 🟡 Medium: 12   │  │ Eval: 1/3 tasks│ │
│ │ Avg Resolution: 2.3d│  │ 🟢 Low: 3       │  │ DevOps: 1/2     │ │
│ └─────────────────────┘  └──────────────────┘  │ Integ: 2/4 tasks│ │
│                                                 └─────────────────┘ │
│                                                                 │
│ ┌─ ACTIVE ISSUES ─────────────────────────────────────────────────┐ │
│ │ ISS-001 │🔴│ Evaluation Report Error    │ DB Agent │ 🟡 In Prog│ │
│ │ ISS-002 │🟠│ UI Consistency Audit       │ UX Agent │ 🟢 Testing│ │
│ │ ISS-003 │🟡│ Schema Migration Planning  │ DB Agent │ 🔵 Review │ │
│ │ ISS-004 │🟠│ Prompt Performance Analysis│ Eval Ag. │ 🟡 In Prog│ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ QUICK ACTIONS ─────────────────────────────────────────────────┐ │
│ │ [+ New Issue] [🔄 Refresh] [📊 Analytics] [⚙️ Settings]        │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Flask Routes for Issue Management**
```python
@dashboard_bp.route('/issues')
def issue_dashboard():
    """Main issue management dashboard"""
    issues = get_open_issues()
    agent_workloads = get_agent_workloads()
    issue_stats = calculate_issue_statistics()
    
    return render_template('dashboard/issues.html', 
                         issues=issues,
                         agent_workloads=agent_workloads,
                         stats=issue_stats)

@dashboard_bp.route('/issues/create', methods=['GET', 'POST'])
def create_issue():
    """Create new issue"""
    if request.method == 'POST':
        issue_data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'type': request.form['type'],
            'priority': request.form['priority'],
            'component': request.form['component'],
            'created_by': 'orchestrator',
            'created_at': datetime.now(),
            'status': 'open'
        }
        
        # Auto-assign if possible
        optimal_agent = assignment_engine.get_optimal_assignment(issue_data)
        if optimal_agent:
            issue_data['assigned_to'] = optimal_agent
            issue_data['status'] = 'assigned'
            issue_data['assigned_at'] = datetime.now()
        
        # Save to Firestore
        issue_id = create_issue_in_db(issue_data)
        
        flash(f'Issue {issue_id} created successfully', 'success')
        return redirect(url_for('dashboard.issue_detail', issue_id=issue_id))
    
    return render_template('dashboard/create_issue.html')

@dashboard_bp.route('/issues/<issue_id>')
def issue_detail(issue_id):
    """View issue details"""
    issue = get_issue_by_id(issue_id)
    progress_history = get_issue_progress_history(issue_id)
    
    return render_template('dashboard/issue_detail.html',
                         issue=issue,
                         progress_history=progress_history)

@dashboard_bp.route('/issues/<issue_id>/assign', methods=['POST'])
def assign_issue(issue_id):
    """Assign issue to agent"""
    agent = request.form['agent']
    
    # Update in Firestore
    update_issue_assignment(issue_id, agent)
    
    # Send assignment message to agent
    send_task_assignment_message(issue_id, agent)
    
    flash(f'Issue assigned to {agent}', 'success')
    return redirect(url_for('dashboard.issue_detail', issue_id=issue_id))
```

---

## 📈 **Analytics & Reporting**

### **Issue Metrics Dashboard**
```python
class IssueAnalytics:
    """Generate analytics and insights from issue data"""
    
    def __init__(self):
        self.db = firestore.Client()
        
    def generate_velocity_report(self, days: int = 30):
        """Generate team velocity report"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        completed_issues = self.db.collection('issues')\
            .where('status', '==', 'closed')\
            .where('closed_at', '>=', start_date)\
            .where('closed_at', '<=', end_date)\
            .stream()
        
        metrics = {
            'total_completed': 0,
            'story_points': 0,
            'avg_resolution_time': 0,
            'by_agent': {},
            'by_priority': {},
            'by_type': {}
        }
        
        resolution_times = []
        
        for issue in completed_issues:
            data = issue.to_dict()
            metrics['total_completed'] += 1
            
            if data.get('story_points'):
                metrics['story_points'] += data['story_points']
                
            # Calculate resolution time
            created = data['created_at']
            closed = data['closed_at']
            resolution_time = (closed - created).total_seconds() / 3600  # hours
            resolution_times.append(resolution_time)
            
            # Agent metrics
            agent = data.get('assigned_to', 'unassigned')
            if agent not in metrics['by_agent']:
                metrics['by_agent'][agent] = 0
            metrics['by_agent'][agent] += 1
            
            # Priority metrics
            priority = data.get('priority', 'unknown')
            if priority not in metrics['by_priority']:
                metrics['by_priority'][priority] = 0
            metrics['by_priority'][priority] += 1
            
        if resolution_times:
            metrics['avg_resolution_time'] = sum(resolution_times) / len(resolution_times)
            
        return metrics
        
    def generate_quality_report(self):
        """Generate quality metrics report"""
        issues = self.db.collection('issues').stream()
        
        quality_metrics = {
            'reopened_rate': 0,
            'sla_compliance': 0,
            'defect_rate': 0,
            'customer_satisfaction': 0
        }
        
        total_issues = 0
        reopened_count = 0
        sla_violations = 0
        
        for issue in issues:
            data = issue.to_dict()
            total_issues += 1
            
            if data.get('reopened_count', 0) > 0:
                reopened_count += 1
                
            # Check SLA compliance
            if self.is_sla_violation(data):
                sla_violations += 1
                
        if total_issues > 0:
            quality_metrics['reopened_rate'] = reopened_count / total_issues
            quality_metrics['sla_compliance'] = 1 - (sla_violations / total_issues)
            
        return quality_metrics
```

---

**Next Document**: [Development Roadmap](DEVELOPMENT_ROADMAP.md)