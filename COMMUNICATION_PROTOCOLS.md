# Communication Protocols & Handoff Templates

## 📡 **Inter-Agent Communication Standards**

### **Message Types & Formats**

#### **1. Task Assignment Message**
```json
{
  "message_type": "task_assignment",
  "message_id": "MSG-2025-001",
  "timestamp": "2025-08-02T10:30:00Z",
  "sender": "orchestrator",
  "recipient": "ux-agent",
  "priority": "high",
  "correlation_id": "TASK-ISS-2025-001",
  
  "task_details": {
    "task_id": "ISS-2025-001",
    "title": "Fix Edit Prompt Page Design Consistency",
    "description": "Update edit prompt page to match add prompt page design standards",
    "type": "ui_enhancement",
    "priority": "high",
    "estimated_hours": 4,
    
    "user_story": {
      "as_a": "prompt manager",
      "i_want": "consistent design across all prompt pages",
      "so_that": "the interface feels professional and cohesive"
    },
    
    "acceptance_criteria": [
      "Two-column layout matching add prompt page",
      "Guidance panel with placeholders and examples",
      "Consistent card styling and shadows",
      "Proper form hierarchy and button styling"
    ],
    
    "technical_context": {
      "affected_files": [
        "templates/prompts/edit.html",
        "static/css/prompts.css"
      ],
      "reference_design": "templates/prompts/add.html",
      "design_guide": "VISUAL_DESIGN_GUIDE.md"
    },
    
    "dependencies": [],
    "blocking_issues": [],
    "due_date": "2025-08-03T17:00:00Z"
  },
  
  "instructions": {
    "approach": "Follow existing design patterns from add prompt page exactly",
    "quality_requirements": [
      "Must pass visual consistency audit",
      "Must maintain responsive design",
      "Must follow accessibility guidelines"
    ],
    "testing_requirements": [
      "Test on multiple screen sizes",
      "Verify form functionality",
      "Check browser compatibility"
    ]
  },
  
  "orchestrator_notes": "This is part of broader UI consistency initiative. Coordinate with database agent if schema questions arise.",
  
  "requires_response": true,
  "response_deadline": "2025-08-02T11:00:00Z"
}
```

#### **2. Status Update Message**
```json
{
  "message_type": "status_update",
  "message_id": "MSG-2025-002",
  "timestamp": "2025-08-02T11:15:00Z",
  "sender": "ux-agent",
  "recipient": "orchestrator",
  "correlation_id": "TASK-ISS-2025-001",
  
  "task_id": "ISS-2025-001",
  "status": "in_progress",
  "progress_percentage": 25,
  
  "progress_details": {
    "completed_items": [
      "Analyzed current edit prompt page structure",
      "Compared with add prompt page design",
      "Identified 6 specific inconsistencies"
    ],
    "current_work": "Implementing two-column layout structure",
    "next_items": [
      "Add guidance panel with placeholders",
      "Update CSS for consistent styling",
      "Test responsive behavior"
    ]
  },
  
  "findings": {
    "issues_discovered": [
      "Form uses basic Bootstrap classes instead of custom styling",
      "Missing guidance panel entirely",
      "Button hierarchy doesn't match design standards"
    ],
    "technical_notes": "Will need to create new CSS classes for consistency",
    "estimated_completion": "2025-08-02T15:30:00Z"
  },
  
  "requests": [],
  "blockers": [],
  "quality_checks": {
    "design_review": "pending",
    "responsive_test": "pending",
    "accessibility_check": "pending"
  }
}
```

#### **3. Help Request Message**
```json
{
  "message_type": "help_request",
  "message_id": "MSG-2025-003",
  "timestamp": "2025-08-02T14:20:00Z",
  "sender": "evaluation-agent",
  "recipient": "database-agent",
  "priority": "high",
  "correlation_id": "TASK-ISS-2025-003",
  
  "issue_summary": "Need clarification on Trace model schema for evaluation report fix",
  "task_context": {
    "task_id": "ISS-2025-003",
    "title": "Fix evaluation report generation error",
    "current_blocker": "Schema mismatch between PromptEvaluator and Trace model"
  },
  
  "specific_request": {
    "type": "schema_clarification",
    "questions": [
      "What is the correct field name for response time in Trace model?",
      "Should token count come from Cost model relationship?",
      "Is created_at field actually start_time?"
    ],
    "urgency": "blocking_implementation",
    "context_files": [
      "app/models.py (Trace model)",
      "app/services/prompt_evaluator.py (lines 84, 213, 311)"
    ]
  },
  
  "attempted_solutions": [
    "Reviewed Trace model definition - fields don't match evaluator expectations",
    "Checked Cost model for token information - found total_tokens field",
    "Tried using duration_ms instead of response_time - still type mismatch"
  ],
  
  "requires_response": true,
  "response_deadline": "2025-08-02T16:00:00Z",
  "cc": ["orchestrator"]
}
```

#### **4. Completion Message**
```json
{
  "message_type": "task_completion",
  "message_id": "MSG-2025-004", 
  "timestamp": "2025-08-02T15:45:00Z",
  "sender": "ux-agent",
  "recipient": "orchestrator",
  "correlation_id": "TASK-ISS-2025-001",
  
  "task_id": "ISS-2025-001",
  "status": "completed",
  "completion_time": "2025-08-02T15:45:00Z",
  "actual_hours": 3.5,
  
  "deliverables": {
    "files_modified": [
      "templates/prompts/edit.html",
      "static/css/prompts.css"
    ],
    "changes_summary": "Updated edit prompt page to match add prompt page design exactly",
    "implementation_details": [
      "Added two-column responsive layout",
      "Created guidance panel with placeholders and examples",
      "Updated CSS for consistent card styling and shadows",
      "Implemented proper form hierarchy with visual indicators"
    ]
  },
  
  "quality_validation": {
    "design_review": "passed",
    "responsive_test": "passed - tested on mobile, tablet, desktop",
    "accessibility_check": "passed - proper ARIA labels and contrast",
    "cross_browser_test": "passed - Chrome, Firefox, Safari",
    "functionality_test": "passed - form submission and validation working"
  },
  
  "acceptance_criteria_status": [
    {
      "criteria": "Two-column layout matching add prompt page",
      "status": "completed",
      "notes": "Exact match achieved with responsive breakpoints"
    },
    {
      "criteria": "Guidance panel with placeholders and examples", 
      "status": "completed",
      "notes": "Added comprehensive placeholder documentation"
    },
    {
      "criteria": "Consistent card styling and shadows",
      "status": "completed", 
      "notes": "Matches design system exactly"
    },
    {
      "criteria": "Proper form hierarchy and button styling",
      "status": "completed",
      "notes": "Primary/secondary button hierarchy implemented"
    }
  ],
  
  "additional_improvements": [
    "Added form validation enhancements",
    "Improved error message styling",
    "Added keyboard navigation improvements"
  ],
  
  "documentation_updates": [
    "Updated VISUAL_DESIGN_GUIDE.md to mark edit page as compliant",
    "Added implementation notes for future reference"
  ],
  
  "next_recommendations": [
    "Apply same patterns to view prompt page",
    "Consider adding similar guidance panels to other forms"
  ]
}
```

---

## 🔄 **Handoff Protocols**

### **Token Limit Management**

#### **Token Monitoring System**
```python
class TokenMonitor:
    """Monitor conversation token usage and trigger handoffs"""
    
    def __init__(self):
        self.token_limits = {
            "warning_threshold": 180000,  # 80% of limit
            "critical_threshold": 200000,  # 90% of limit  
            "emergency_threshold": 220000  # 98% of limit
        }
        self.current_tokens = 0
        self.conversation_history = []
        
    def check_token_status(self):
        """Check current token usage and return status"""
        if self.current_tokens >= self.token_limits["emergency_threshold"]:
            return "emergency_handoff_required"
        elif self.current_tokens >= self.token_limits["critical_threshold"]:
            return "critical_prepare_handoff"
        elif self.current_tokens >= self.token_limits["warning_threshold"]:
            return "warning_plan_handoff"
        else:
            return "normal"
    
    def estimate_remaining_capacity(self):
        """Estimate how many more exchanges are possible"""
        remaining_tokens = 225000 - self.current_tokens  # Conservative limit
        avg_exchange_tokens = 3000  # Estimated average
        return remaining_tokens // avg_exchange_tokens
```

### **Emergency Handoff Template**

#### **🚨 EMERGENCY HANDOFF PROTOCOL**
```markdown
# URGENT: Token Limit Emergency Handoff

## IMMEDIATE STATUS
- **Current Token Count**: ~[X] tokens
- **Remaining Capacity**: <5 exchanges
- **Current Task**: [Brief description]
- **Completion Status**: [X]% complete

## CRITICAL CONTEXT FOR CURSOR AGENT

### Active Work in Progress:
1. **Primary Task**: [Task ID and title]
   - Status: [In progress/blocked/testing]
   - Completion: [X]%
   - Next immediate step: [Specific action needed]

2. **Files Currently Being Modified**:
   - `[file_path]` - [What's being changed]
   - `[file_path]` - [What's being changed]

3. **Incomplete Code/Changes**:
   ```[language]
   // Code that needs to be completed
   [Paste any incomplete code]
   ```

### EXACT NEXT STEPS:
1. [Specific step 1 - be very detailed]
2. [Specific step 2 - include file paths and line numbers]
3. [Specific step 3 - mention expected outputs]

### QUALITY REQUIREMENTS:
- [ ] [Specific requirement 1]
- [ ] [Specific requirement 2]
- [ ] [Specific requirement 3]

### TESTING NEEDED:
- [ ] [Test 1 - how to run it]
- [ ] [Test 2 - expected results]

### FILES TO READ FOR CONTEXT:
- `[file_path]` - [Why this file is important]
- `[file_path]` - [Key information in this file]

## HANDOFF VALIDATION
**Cursor Agent must confirm:**
1. ✅ Understood the incomplete task
2. ✅ Located all mentioned files  
3. ✅ Ready to continue from specified step
4. ✅ Committed to quality requirements

## ORCHESTRATOR NOTES
[Any additional context about task priority, dependencies, or special considerations]

---
**HANDOFF TIMESTAMP**: [Current timestamp]
**ESTIMATED COMPLETION TIME**: [Time estimate for remaining work]
```

### **Planned Handoff Template**

#### **📋 PLANNED HANDOFF PROTOCOL**
```markdown
# Planned Handoff to Cursor Agent

## HANDOFF SUMMARY
- **Reason**: Token optimization / Natural break point
- **Current Phase**: [Planning/Implementation/Testing/Documentation]
- **Overall Progress**: [X]% of current sprint completed

## COMPLETED WORK
### ✅ Finished Tasks:
1. **[Task ID]**: [Title] - [Brief outcome]
2. **[Task ID]**: [Title] - [Brief outcome]

### 📄 Created/Updated Files:
- `[file_path]` - [What was done]
- `[file_path]` - [What was done]

## NEXT PHASE TASKS

### 🎯 Immediate Priority (Next 1-2 hours):
1. **[Task ID]**: [Title]
   - **Description**: [What needs to be done]
   - **Approach**: [Recommended approach]
   - **Files to modify**: [List of files]
   - **Acceptance criteria**: [How to know it's done]

### 📋 Medium Priority (This session):
1. **[Task ID]**: [Title] - [Brief description]
2. **[Task ID]**: [Title] - [Brief description]

### 🔄 Future Items (Next session):
1. **[Task ID]**: [Title] - [Brief description]

## PROJECT CONTEXT

### Current System State:
- **Database**: [Any recent schema changes or important data]
- **UI**: [Current state of interface work]
- **Testing**: [What's been tested, what needs testing]
- **Deployment**: [Any deployment considerations]

### Key Reference Files:
- `AGENT_HIERARCHY.md` - Agent roles and responsibilities  
- `SUB_AGENT_FRAMEWORK.md` - Technical implementation details
- `VISUAL_DESIGN_GUIDE.md` - UI standards and requirements
- `[other_relevant_files]` - [Brief description]

## QUALITY STANDARDS REMINDER
- Follow existing code patterns and conventions
- Update documentation for any changes made
- Test all modifications before marking complete
- Maintain design consistency per VISUAL_DESIGN_GUIDE.md
- Use TodoWrite tool to track progress on tasks

## AGENT COORDINATION
- **Active Agents**: [List any other agents currently working]
- **Pending Reviews**: [Any work waiting for review]
- **Blocked Items**: [Anything waiting for external input]

## SUCCESS METRICS
- [ ] All immediate priority tasks completed
- [ ] Quality standards maintained
- [ ] Documentation updated
- [ ] Tests passing
- [ ] Ready for next handoff or completion

---
**HANDOFF TIMESTAMP**: [Current timestamp]
**NEXT REVIEW POINT**: [When to check progress]
**CURSOR AGENT CHECKLIST**: Please confirm understanding of immediate priorities and reference files before beginning work.
```

### **Cross-Agent Communication Template**

#### **📨 AGENT-TO-AGENT MESSAGE**
```markdown
# Message: [AGENT_NAME] → [RECIPIENT_AGENT]

## MESSAGE TYPE: [Task Assignment/Status Update/Help Request/Information Share]

### CONTEXT
- **Related Task**: [Task ID] - [Task Title]
- **Urgency**: [Low/Medium/High/Critical]
- **Deadline**: [If applicable]

### REQUEST/INFORMATION
[Clear, specific request or information being shared]

### BACKGROUND
[Why this communication is needed - provide context]

### EXPECTED RESPONSE
- **Type**: [Acknowledgment/Analysis/Implementation/Information]
- **Timeline**: [When response is needed]
- **Format**: [Any specific format requirements]

### DEPENDENCIES
- **Blocks**: [What this blocks if not addressed]
- **Depends on**: [What this depends on]

### TECHNICAL DETAILS
[Any code, files, or technical information relevant to the request]

---
**FROM**: [Sender Agent]
**TO**: [Recipient Agent]  
**CC**: [Orchestrator if needed]
**TIMESTAMP**: [Current timestamp]
```

---

## 🔧 **Communication Infrastructure**

### **Message Queue System**
```python
class MessageQueue:
    """Manage inter-agent message delivery"""
    
    def __init__(self):
        self.queues = {
            "orchestrator": [],
            "ux-agent": [],
            "database-agent": [],
            "evaluation-agent": [],
            "devops-agent": [],
            "integration-agent": []
        }
        self.message_history = []
        self.delivery_confirmations = {}
        
    def send_message(self, message: dict):
        """Send message to recipient's queue"""
        recipient = message["recipient"]
        
        if recipient not in self.queues:
            raise ValueError(f"Unknown recipient: {recipient}")
            
        # Add to recipient's queue
        self.queues[recipient].append(message)
        
        # Add to history
        self.message_history.append(message)
        
        # Set delivery confirmation requirement
        if message.get("requires_response"):
            self.delivery_confirmations[message["message_id"]] = {
                "sent_at": datetime.now(),
                "deadline": message.get("response_deadline"),
                "confirmed": False
            }
            
    def get_messages(self, agent: str, mark_read: bool = True):
        """Get messages for specific agent"""
        if agent not in self.queues:
            return []
            
        messages = self.queues[agent].copy()
        
        if mark_read:
            self.queues[agent].clear()
            
        return messages
        
    def confirm_delivery(self, message_id: str):
        """Confirm message was received and processed"""
        if message_id in self.delivery_confirmations:
            self.delivery_confirmations[message_id]["confirmed"] = True
            self.delivery_confirmations[message_id]["confirmed_at"] = datetime.now()
```

### **Real-time Status Broadcasting**
```python
class StatusBroadcaster:
    """Broadcast status updates to all interested agents"""
    
    def __init__(self):
        self.subscribers = {}
        self.status_updates = []
        
    def subscribe(self, agent: str, event_types: list):
        """Subscribe agent to specific event types"""
        if agent not in self.subscribers:
            self.subscribers[agent] = []
        
        self.subscribers[agent].extend(event_types)
        
    def broadcast_status(self, event_type: str, data: dict):
        """Broadcast status update to all subscribers"""
        status_update = {
            "event_type": event_type,
            "timestamp": datetime.now(),
            "data": data
        }
        
        self.status_updates.append(status_update)
        
        # Send to subscribers
        for agent, subscribed_events in self.subscribers.items():
            if event_type in subscribed_events:
                self.send_status_update(agent, status_update)
                
    def send_status_update(self, agent: str, update: dict):
        """Send status update to specific agent"""
        message = {
            "message_type": "status_broadcast",
            "message_id": str(uuid.uuid4()),
            "timestamp": update["timestamp"],
            "sender": "system",
            "recipient": agent,
            "content": update,
            "requires_response": False
        }
        
        self.message_queue.send_message(message)
```

---

**Next Document**: [Issue Management System](ISSUE_MANAGEMENT.md)