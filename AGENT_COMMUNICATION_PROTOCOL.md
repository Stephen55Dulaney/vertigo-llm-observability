# Agent Communication Protocol & Directory Structure

## 🧠 **Agent Communication Architecture**

### **Communication Layers:**
```
┌─ ORCHESTRATOR LAYER ─────────────────────────────────────────────┐
│ Vertigo Prime (Claude Code)                                     │
│ ├── Task assignment and coordination                             │
│ ├── Quality assurance and validation                            │
│ ├── Inter-agent conflict resolution                             │
│ └── Strategic planning and architecture decisions               │
└──────────────────────────────────────────────────────────────────┘
                                ↕
┌─ COMMUNICATION BUS ──────────────────────────────────────────────┐
│ Firestore Agent Context Collection                              │
│ ├── agent_tasks/{taskId} - Task assignments and status          │
│ ├── agent_context/{sessionId} - Shared context and state        │
│ ├── agent_logs/{logId} - Activity logs and handoffs            │
│ └── agent_coordination/{messageId} - Inter-agent messages       │
└──────────────────────────────────────────────────────────────────┘
                                ↕
┌─ SPECIALIZED AGENTS ─────────────────────────────────────────────┐
│ Integration Agent │ UX Agent │ Database Agent │ Evaluation Agent │
│ DevOps Agent     │ [Future Agents]                              │
└──────────────────────────────────────────────────────────────────┘
```

### **Agent State Management**
```javascript
// Firestore agent_context collection structure
agent_context/{sessionId} = {
  session_id: "session-2025-08-002",
  orchestrator: "claude-code",
  active_agents: ["integration-agent", "ux-agent"],
  
  shared_context: {
    current_project: "semantic-prompt-search",
    current_phase: "sprint-execution",
    active_issues: ["ISS-2025-08-004"],
    quality_standards: "VISUAL_DESIGN_GUIDE.md",
    success_criteria: {...}
  },
  
  agent_status: {
    "integration-agent": {
      status: "active",
      current_task: "ISS-2025-08-004-backend",
      progress: 25,
      last_update: "2025-08-02T14:30:00Z",
      next_checkpoint: "2025-08-02T18:00:00Z"
    },
    "ux-agent": {
      status: "active", 
      current_task: "ISS-2025-08-004-frontend",
      progress: 15,
      last_update: "2025-08-02T14:15:00Z",
      next_checkpoint: "2025-08-02T17:00:00Z"
    }
  },
  
  coordination_queue: [
    {
      from: "integration-agent",
      to: "ux-agent", 
      message: "API response format ready for frontend integration",
      priority: "high",
      requires_response: true
    }
  ]
}
```

### **Agent Handoff Protocol**
```python
class AgentHandoffProtocol:
    """Standardized handoff between agents"""
    
    def initiate_handoff(self, from_agent: str, to_agent: str, 
                        context: dict, task_data: dict):
        """
        Standard handoff procedure:
        1. Validate current agent completion status
        2. Package context and deliverables
        3. Create handoff record in agent_logs
        4. Notify receiving agent with full context
        5. Update agent_context with new assignments
        """
        
    def emergency_handoff(self, current_agent: str, reason: str, 
                         incomplete_work: dict):
        """
        Emergency handoff for token limits or blockers:
        1. Immediately document current state
        2. Create emergency handoff record
        3. Escalate to Orchestrator for reassignment
        4. Preserve all work context and progress
        """
```

## 📁 **Directory Structure for Cursor Agent**

### **Enhanced Vertigo Architecture:**
```
vertigo-debug-toolkit/
├── agents/                          # 🤖 Agent Implementation
│   ├── base/
│   │   ├── __init__.py
│   │   ├── agent_base.py           # Base Agent class
│   │   ├── communication.py        # Inter-agent messaging
│   │   └── context_manager.py      # Shared context handling
│   ├── specialized/
│   │   ├── __init__.py
│   │   ├── integration_agent.py    # API & backend development
│   │   ├── ux_agent.py            # UI/UX design and implementation
│   │   ├── database_agent.py      # Firestore & data operations
│   │   ├── evaluation_agent.py    # LLM performance & testing
│   │   └── devops_agent.py        # Cloud deployment & monitoring
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── vertigo_prime.py       # Main orchestrator logic
│   │   ├── task_assignment.py     # Intelligent task routing
│   │   └── quality_assurance.py   # QA and validation
│   └── tests/
│       ├── test_agent_base.py
│       ├── test_communication.py
│       └── test_specialized_agents.py
│
├── app/                            # 🌐 Flask Application
│   ├── blueprints/
│   │   ├── dashboard/
│   │   │   ├── routes.py          # Enhanced with agent endpoints
│   │   │   └── agent_api.py       # Agent coordination API
│   │   └── agents/                # New agent management interface
│   │       ├── __init__.py
│   │       ├── routes.py          # Agent status and control
│   │       └── monitoring.py      # Agent performance tracking
│   ├── services/
│   │   ├── semantic_search.py     # 🔍 Semantic search engine
│   │   ├── agent_coordinator.py   # Agent orchestration service
│   │   └── performance_analytics.py # Enhanced analytics
│   └── models/
│       ├── agent_models.py        # Agent state and task models
│       └── enhanced_models.py     # Extended prompt/trace models
│
├── firestore_models/               # 🗄️ Database Schema
│   ├── __init__.py
│   ├── agent_context.py           # Agent coordination data
│   ├── agent_tasks.py             # Task assignment and tracking
│   ├── agent_logs.py              # Activity and handoff logs
│   ├── enhanced_prompts.py        # Prompts with embeddings
│   └── performance_metrics.py     # Evaluation and analytics
│
├── cloud_functions/                # ☁️ Google Cloud Functions
│   ├── agent_trigger/             # Agent coordination triggers
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── agent_dispatcher.py
│   └── enhanced_processors/        # Enhanced email/meeting processing
│       ├── email_processor_v2/
│       └── meeting_processor_v2/
│
├── templates/                      # 🎨 Enhanced UI Templates
│   ├── agents/
│   │   ├── dashboard.html         # Agent monitoring dashboard
│   │   ├── task_board.html        # Kanban-style task management
│   │   └── performance.html       # Agent performance metrics
│   └── prompts/
│       └── semantic_search.html   # Enhanced semantic search page
│
├── static/                         # 📱 Frontend Assets
│   ├── js/
│   │   ├── semantic_search.js     # Semantic search functionality
│   │   ├── agent_monitoring.js    # Real-time agent status
│   │   └── batch_evaluation.js    # Batch testing interface
│   └── css/
│       ├── semantic_search.css    # Search interface styling
│       └── agent_dashboard.css    # Agent monitoring styles
│
├── docs/                          # 📚 Documentation
│   ├── AGENT_HIERARCHY.md         # ✅ Already created
│   ├── SUB_AGENT_FRAMEWORK.md     # ✅ Already created
│   ├── COMMUNICATION_PROTOCOLS.md # ✅ Already created
│   ├── ISSUE_MANAGEMENT.md        # ✅ Already created
│   ├── DEVELOPMENT_ROADMAP.md     # ✅ Already created
│   ├── TOKEN_MANAGEMENT.md        # ✅ Already created
│   └── VERTIGO_MASTER_INDEX.md    # ✅ Already created
│
└── tests/                         # 🧪 Testing Suite
    ├── unit/
    │   ├── test_semantic_search.py
    │   ├── test_agent_coordination.py
    │   └── test_performance_analytics.py
    ├── integration/
    │   ├── test_agent_workflows.py
    │   ├── test_api_endpoints.py
    │   └── test_firestore_integration.py
    └── e2e/
        ├── test_semantic_search_workflow.py
        └── test_agent_handoff_scenarios.py
```

## 🔄 **Agent Interaction Patterns**

### **1. Task Assignment Flow**
```python
# Orchestrator → Specialized Agent
def assign_task(self, agent_name: str, task: dict):
    """
    1. Create task record in agent_tasks collection
    2. Update agent_context with assignment
    3. Send notification to agent via communication bus
    4. Set up monitoring and checkpoint schedule
    """
    
# Agent → Orchestrator (Status Updates)  
def update_progress(self, task_id: str, progress: int, notes: str):
    """
    1. Update task progress in agent_tasks
    2. Log activity in agent_logs
    3. Check for coordination needs with other agents
    4. Escalate blockers to Orchestrator if needed
    """
```

### **2. Inter-Agent Collaboration**
```python
# Agent A → Agent B (Coordination)
def request_collaboration(self, target_agent: str, request: dict):
    """
    1. Add coordination request to agent_context queue
    2. Log collaboration need in agent_logs
    3. Notify Orchestrator of cross-agent dependency
    4. Wait for response or escalate after timeout
    """
    
# Agent B → Agent A (Response)
def respond_to_collaboration(self, requesting_agent: str, response: dict):
    """
    1. Update coordination queue with response
    2. Log collaboration completion
    3. Update shared context with any new information
    4. Continue with coordinated work
    """
```

### **3. Quality Checkpoints**
```python
# Orchestrator Quality Validation
def validate_deliverable(self, agent: str, deliverable: dict):
    """
    1. Apply quality standards from VISUAL_DESIGN_GUIDE.md
    2. Run automated validation checks
    3. Score against acceptance criteria
    4. Provide feedback or approval
    5. Log quality assessment in agent_logs
    """
```

## 🛠️ **Base Agent Implementation**

```python
# agents/base/agent_base.py
class VertigoAgent:
    """Base class for all Vertigo specialized agents"""
    
    def __init__(self, agent_name: str, specialization: str):
        self.agent_name = agent_name
        self.specialization = specialization
        self.context_manager = ContextManager()
        self.communicator = AgentCommunicator()
        self.current_tasks = []
        self.performance_metrics = {}
        
    def receive_task(self, task: dict) -> bool:
        """Receive and validate new task assignment"""
        if self.can_accept_task(task):
            self.current_tasks.append(task)
            self.update_status("assigned", task["id"])
            return True
        return False
        
    def execute_task(self, task_id: str) -> dict:
        """Main task execution - override in specialized agents"""
        raise NotImplementedError("Specialized agents must implement execute_task")
        
    def request_help(self, issue: str, context: dict) -> dict:
        """Request help from Orchestrator or other agents"""
        return self.communicator.escalate_to_orchestrator(
            agent=self.agent_name,
            issue=issue, 
            context=context
        )
        
    def update_progress(self, task_id: str, progress: int, notes: str):
        """Update task progress and notify coordination system"""
        self.context_manager.update_task_progress(
            agent=self.agent_name,
            task_id=task_id,
            progress=progress,
            notes=notes,
            timestamp=datetime.now()
        )
```

---

## 📊 **Cursor Agent Ready Tasks**

Based on GP's feedback, here's the **Cursor-ready work breakdown**:

### **🔧 Phase 1: Agent Infrastructure (Days 1-2)**
- [ ] **Create agent directory structure** as specified above
- [ ] **Implement base Agent class** with communication protocols
- [ ] **Set up Firestore agent collections** (agent_context, agent_tasks, agent_logs)
- [ ] **Create agent coordination API endpoints** in Flask app

### **🤖 Phase 2: Specialized Agent Implementation (Days 3-4)**
- [ ] **Integration Agent implementation** for semantic search backend
- [ ] **UX Agent implementation** for interface enhancements  
- [ ] **Agent communication testing** between specialized agents
- [ ] **Orchestrator coordination logic** for task assignment and monitoring

### **🔄 Phase 3: Workflow Integration (Days 5-6)**
- [ ] **End-to-end agent workflow testing** for semantic search feature
- [ ] **Quality checkpoint implementation** with automated validation
- [ ] **Performance monitoring dashboard** for agent coordination
- [ ] **Documentation and handoff procedures** completion

This creates a **production-ready agent orchestration system** that can scale beyond the current semantic search feature to manage all future Vertigo development.

---

**Recommendation**: Proceed with enhanced sprint execution incorporating GP's refinements. This elevates our framework from good to **enterprise-grade**.