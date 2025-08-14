# Vertigo Sub-Agent Framework Architecture

## 🏗️ **Framework Overview**

The Vertigo Sub-Agent Framework is a sophisticated orchestration system that coordinates specialized AI agents to manage complex software development tasks. Each agent operates with defined responsibilities while maintaining seamless communication through the Orchestrator Agent.

---

## 🎯 **Core Architecture Principles**

### **1. Separation of Concerns**
- Each agent has a clearly defined specialty and scope
- No overlap in primary responsibilities
- Cross-functional collaboration through defined protocols

### **2. Scalable Communication**
- All inter-agent communication flows through the Orchestrator
- Standardized message formats and protocols
- Asynchronous task processing with status tracking

### **3. Quality Assurance**
- Built-in review processes for all deliverables
- Automated quality checks and validation
- Continuous improvement through performance metrics

### **4. Fault Tolerance**
- Graceful degradation when agents are unavailable
- Automatic task redistribution mechanisms
- Emergency escalation procedures

---

## 🔧 **Technical Implementation**

### **Agent State Management**
```python
class AgentState:
    """Track agent status and workload"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.status = "available"  # available, busy, offline
        self.current_tasks = []
        self.completed_tasks = []
        self.performance_metrics = {}
        self.last_activity = None
        
    def assign_task(self, task: Task):
        """Assign new task to agent"""
        if len(self.current_tasks) >= 3:
            raise WorkloadExceeded("Agent at maximum capacity")
        
        self.current_tasks.append(task)
        self.status = "busy"
        self.last_activity = datetime.now()
        
    def complete_task(self, task_id: str, deliverables: dict):
        """Mark task as completed with deliverables"""
        task = self.find_task(task_id)
        task.status = "completed"
        task.deliverables = deliverables
        
        self.current_tasks.remove(task)
        self.completed_tasks.append(task)
        
        if not self.current_tasks:
            self.status = "available"
```

### **Communication Protocol**
```python
class AgentMessage:
    """Standardized message format between agents"""
    
    def __init__(self):
        self.message_id = uuid.uuid4()
        self.timestamp = datetime.now()
        self.sender = None
        self.recipient = None
        self.message_type = None  # task_assignment, status_update, request_help
        self.priority = "medium"  # low, medium, high, critical
        self.content = {}
        self.requires_response = False
        self.correlation_id = None  # Link related messages
        
class CommunicationProtocol:
    """Manage message routing and delivery"""
    
    def __init__(self):
        self.message_queue = []
        self.agent_registry = {}
        self.orchestrator = None
        
    def route_message(self, message: AgentMessage):
        """Route message to appropriate recipient"""
        if message.recipient == "orchestrator":
            self.orchestrator.receive_message(message)
        else:
            agent = self.agent_registry.get(message.recipient)
            if agent and agent.is_available():
                agent.receive_message(message)
            else:
                self.escalate_to_orchestrator(message)
```

### **Task Definition Structure**
```python
class Task:
    """Comprehensive task definition"""
    
    def __init__(self):
        self.task_id = None
        self.title = None
        self.description = None
        self.type = None  # bug_fix, feature, research, optimization
        self.priority = None
        self.estimated_hours = None
        
        # Assignment Details
        self.assigned_agent = None
        self.assigned_at = None
        self.due_date = None
        
        # Technical Context
        self.affected_components = []
        self.required_skills = []
        self.dependencies = []
        self.blocking_issues = []
        
        # User Story Format
        self.user_story = {
            "as_a": "",
            "i_want": "",
            "so_that": ""
        }
        
        # Acceptance Criteria
        self.acceptance_criteria = []
        
        # Progress Tracking
        self.status = "pending"
        self.progress_updates = []
        self.deliverables = {}
        
        # Quality Metrics
        self.complexity_score = None
        self.quality_requirements = []
        self.testing_requirements = []
```

---

## 📊 **Agent Orchestration Dashboard**

### **Dashboard Components**
```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT ORCHESTRATION HUB                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─ AGENT STATUS ──────┐  ┌─ TASK QUEUE ──────┐  ┌─ METRICS ───┐ │
│ │ UX Agent     ●●○    │  │ High Priority: 3  │  │ Avg Velocity │ │
│ │ DB Agent     ●○○    │  │ Medium Priority:7 │  │ 2.3 tasks/day│ │
│ │ Eval Agent   ●●●    │  │ Low Priority: 12  │  │              │ │
│ │ DevOps Agent ○○○    │  │ Overdue: 1       │  │ Quality: 8.7 │ │
│ │ Integ Agent  ●○○    │  │ Blocked: 2       │  │ /10 average  │ │
│ └─────────────────────┘  └───────────────────┘  └──────────────┘ │
│                                                                 │
│ ┌─ ACTIVE TASKS ─────────────────────────────────────────────────┐ │
│ │ ISS-001 | DB Agent    | Schema Fix        | ●●○ | Due: Today │ │
│ │ ISS-002 | UX Agent    | Button Styling    | ●○○ | Due: Mon   │ │
│ │ ISS-003 | Eval Agent  | Report Generator  | ●●● | Due: Tue   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─ RECENT COMPLETIONS ───────────────────────────────────────────┐ │
│ │ ✅ ISS-045 | UX Agent   | Login Form Fix    | Quality: 9/10  │ │
│ │ ✅ ISS-044 | DB Agent   | Index Optimization| Quality: 8/10  │ │
│ │ ✅ ISS-043 | DevOps     | Function Deploy   | Quality: 10/10 │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Real-time Monitoring**
```python
class OrchestratorDashboard:
    """Real-time agent monitoring and management"""
    
    def __init__(self):
        self.agents = {}
        self.task_queue = PriorityQueue()
        self.active_tasks = {}
        self.completed_tasks = []
        self.performance_metrics = {}
        
    def get_system_status(self):
        """Get comprehensive system status"""
        return {
            "agents": {
                name: {
                    "status": agent.status,
                    "workload": len(agent.current_tasks),
                    "last_activity": agent.last_activity
                }
                for name, agent in self.agents.items()
            },
            "queue_stats": {
                "high_priority": len([t for t in self.task_queue if t.priority == "high"]),
                "total_pending": len(self.task_queue),
                "overdue": len([t for t in self.active_tasks.values() if t.is_overdue()])
            },
            "performance": {
                "avg_completion_time": self.calculate_avg_completion_time(),
                "quality_score": self.calculate_avg_quality_score(),
                "velocity": self.calculate_team_velocity()
            }
        }
        
    def auto_assign_tasks(self):
        """Automatically assign tasks based on agent capabilities and workload"""
        while not self.task_queue.empty():
            task = self.task_queue.get()
            
            # Find best agent for task
            best_agent = self.find_optimal_agent(task)
            
            if best_agent and best_agent.can_accept_task():
                self.assign_task_to_agent(task, best_agent)
            else:
                # Put task back in queue and wait
                self.task_queue.put(task)
                break
```

---

## 🔄 **Workflow Automation**

### **Automated Task Routing**
```python
class TaskRouter:
    """Intelligent task routing based on content analysis"""
    
    def __init__(self):
        self.routing_rules = {
            "ui_keywords": ["button", "form", "styling", "css", "html", "frontend"],
            "db_keywords": ["firestore", "schema", "query", "database", "collection"],
            "eval_keywords": ["prompt", "evaluation", "langfuse", "a/b test", "performance"],
            "devops_keywords": ["deploy", "cloud", "function", "monitoring", "performance"],
            "integration_keywords": ["api", "webhook", "sync", "endpoint", "service"]
        }
        
    def analyze_task_content(self, task: Task):
        """Analyze task content to determine appropriate agent"""
        content = f"{task.title} {task.description}".lower()
        
        scores = {}
        for agent_type, keywords in self.routing_rules.items():
            score = sum(1 for keyword in keywords if keyword in content)
            scores[agent_type] = score
            
        # Return highest scoring agent type
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "general"
        
    def route_task(self, task: Task):
        """Route task to appropriate agent"""
        agent_type = self.analyze_task_content(task)
        
        agent_mapping = {
            "ui_keywords": "ux-agent",
            "db_keywords": "database-agent",
            "eval_keywords": "evaluation-agent",
            "devops_keywords": "devops-agent",
            "integration_keywords": "integration-agent"
        }
        
        return agent_mapping.get(agent_type, "orchestrator")
```

### **Progress Tracking & Notifications**
```python
class ProgressTracker:
    """Track task progress and send notifications"""
    
    def __init__(self):
        self.notifications = []
        self.progress_thresholds = [25, 50, 75, 100]
        
    def update_progress(self, task_id: str, progress: int, notes: str):
        """Update task progress with automatic notifications"""
        task = self.get_task(task_id)
        old_progress = task.progress
        task.progress = progress
        
        # Check for threshold notifications
        for threshold in self.progress_thresholds:
            if old_progress < threshold <= progress:
                self.send_progress_notification(task, threshold)
                
        # Add progress note
        task.progress_updates.append({
            "timestamp": datetime.now(),
            "progress": progress,
            "notes": notes,
            "updated_by": task.assigned_agent
        })
        
    def send_progress_notification(self, task: Task, milestone: int):
        """Send notification for progress milestones"""
        notification = {
            "type": "progress_milestone",
            "task_id": task.task_id,
            "milestone": milestone,
            "agent": task.assigned_agent,
            "timestamp": datetime.now()
        }
        
        self.notifications.append(notification)
        
        # Send to orchestrator dashboard
        self.orchestrator.receive_notification(notification)
```

---

## 🔐 **Security & Access Control**

### **Agent Permissions Matrix**
```python
class AgentPermissions:
    """Define what each agent can access and modify"""
    
    PERMISSIONS = {
        "ux-agent": {
            "read": ["templates/*", "static/*", "app/blueprints/*/templates/*"],
            "write": ["templates/*", "static/*"],
            "execute": ["ui_tests", "style_validation"],
            "forbidden": ["database_schema", "cloud_deployment", "api_keys"]
        },
        "database-agent": {
            "read": ["app/models/*", "app/services/*", "database/*"],
            "write": ["app/models/*", "database/migrations/*"],
            "execute": ["schema_migration", "data_validation"],
            "forbidden": ["templates/*", "static/*", "cloud_functions/*"]
        },
        "evaluation-agent": {
            "read": ["app/services/prompt_*", "app/services/evaluation_*"],
            "write": ["app/services/prompt_*", "app/services/evaluation_*"],
            "execute": ["evaluation_tests", "prompt_optimization"],
            "forbidden": ["database_schema", "ui_components"]
        },
        "devops-agent": {
            "read": ["*"],
            "write": ["deploy/*", "config/*", "requirements.txt"],
            "execute": ["deployment", "monitoring_setup", "performance_tests"],
            "forbidden": ["app/models/*", "templates/*"]
        },
        "integration-agent": {
            "read": ["app/api/*", "app/services/*", "app/blueprints/*"],
            "write": ["app/api/*", "app/webhooks/*"],
            "execute": ["api_tests", "integration_tests"],
            "forbidden": ["database_migrations", "cloud_deployment"]
        }
    }
    
    def check_permission(self, agent: str, action: str, resource: str):
        """Check if agent has permission for specific action on resource"""
        if agent not in self.PERMISSIONS:
            return False
            
        permissions = self.PERMISSIONS[agent]
        
        # Check forbidden first
        if self.matches_pattern(resource, permissions.get("forbidden", [])):
            return False
            
        # Check specific permission
        allowed_resources = permissions.get(action, [])
        return self.matches_pattern(resource, allowed_resources)
        
    def matches_pattern(self, resource: str, patterns: list):
        """Check if resource matches any pattern"""
        import fnmatch
        return any(fnmatch.fnmatch(resource, pattern) for pattern in patterns)
```

---

## 📈 **Performance Optimization**

### **Load Balancing**
```python
class LoadBalancer:
    """Balance workload across agents"""
    
    def __init__(self):
        self.agent_capacities = {
            "ux-agent": 3,
            "database-agent": 3,
            "evaluation-agent": 3,
            "devops-agent": 2,  # More intensive tasks
            "integration-agent": 4  # Lighter tasks
        }
        
    def get_optimal_agent(self, task: Task, agent_type: str):
        """Find optimal agent considering workload and capabilities"""
        available_agents = [
            agent for agent in self.agents.values()
            if agent.agent_type == agent_type and agent.can_accept_task()
        ]
        
        if not available_agents:
            return None
            
        # Sort by current workload (ascending)
        available_agents.sort(key=lambda a: len(a.current_tasks))
        
        # Consider agent performance history
        best_agent = min(available_agents, key=lambda a: (
            len(a.current_tasks),
            -a.performance_metrics.get("quality_score", 0)
        ))
        
        return best_agent
```

### **Quality Metrics & Optimization**
```python
class QualityAssurance:
    """Monitor and improve agent output quality"""
    
    def __init__(self):
        self.quality_thresholds = {
            "minimum_acceptable": 6.0,
            "good_performance": 8.0,
            "excellent_performance": 9.0
        }
        
    def evaluate_deliverable(self, task: Task, deliverable: dict):
        """Evaluate quality of agent deliverable"""
        criteria = {
            "completeness": self.check_completeness(task, deliverable),
            "correctness": self.check_correctness(task, deliverable),
            "code_quality": self.check_code_quality(deliverable),
            "documentation": self.check_documentation(deliverable),
            "testing": self.check_testing_coverage(deliverable)
        }
        
        # Calculate weighted score
        weights = {
            "completeness": 0.3,
            "correctness": 0.3,
            "code_quality": 0.2,
            "documentation": 0.1,
            "testing": 0.1
        }
        
        quality_score = sum(
            criteria[criterion] * weights[criterion]
            for criterion in criteria
        )
        
        return {
            "overall_score": quality_score,
            "criteria_scores": criteria,
            "improvement_suggestions": self.generate_improvement_suggestions(criteria)
        }
```

---

**Next Document**: [Communication Protocols & Handoff Templates](COMMUNICATION_PROTOCOLS.md)