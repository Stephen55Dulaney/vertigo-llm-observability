# Vertigo Master Index & Quick Reference Guide

## 📚 **Complete Documentation Structure**

### **Core Project Documentation**
```
📁 Vertigo Project Documentation
├── 📋 README.md - Project overview and quick start
├── 🎯 AGENT_HIERARCHY.md - Agent roles and responsibilities  
├── 🏗️ SUB_AGENT_FRAMEWORK.md - Technical architecture
├── 📡 COMMUNICATION_PROTOCOLS.md - Inter-agent communication
├── 🗂️ ISSUE_MANAGEMENT.md - Issue tracking and resolution
├── 🛣️ DEVELOPMENT_ROADMAP.md - Implementation timeline
├── 🔄 TOKEN_MANAGEMENT.md - Handoff procedures
├── 🎨 VISUAL_DESIGN_GUIDE.md - UI/UX standards
├── 📅 Daily Ambition Files - Planning and progress tracking
└── 📖 VERTIGO_MASTER_INDEX.md - This comprehensive guide
```

---

## 🚀 **Quick Start Guide**

### **For New Team Members**
1. **Start Here**: Read `README.md` for project overview
2. **Understand Roles**: Review `AGENT_HIERARCHY.md` 
3. **Learn Standards**: Study `VISUAL_DESIGN_GUIDE.md`
4. **See Progress**: Check latest daily ambition file
5. **Get Context**: Review `ISSUE_MANAGEMENT.md` for current priorities

### **For Cursor Agent Handoffs**
1. **Read Handoff Document**: Provided in handoff message
2. **Check Token Status**: Review `TOKEN_MANAGEMENT.md` if needed
3. **Validate Context**: Confirm understanding per onboarding checklist
4. **Begin Work**: Follow immediate next steps from handoff
5. **Maintain Quality**: Adhere to standards in `VISUAL_DESIGN_GUIDE.md`

---

## 🎯 **Agent Quick Reference**

### **Orchestrator Agent (Claude Code)**
```
PRIMARY RESPONSIBILITIES:
├── Strategic planning and roadmap management
├── Agent task assignment and workload balancing
├── Quality assurance and standard enforcement  
├── Conflict resolution and priority decisions
├── Token management and handoff coordination
└── Documentation maintenance and updates

AUTHORITY LEVEL: Full authority over all agents and decisions
SELF-ASSIGNMENT: Framework implementation, critical fixes, planning
```

### **Specialized Sub-Agents**
```
🎨 UX AGENT
├── UI consistency audits and design enforcement
├── Component styling and user experience optimization
├── Design system compliance and accessibility
└── Frontend bug fixes and visual improvements

💾 DATABASE AGENT  
├── Firestore schema design and optimization
├── Data integrity validation and migrations
├── Performance optimization and query tuning
└── Database-related bug fixes and maintenance

📊 EVALUATION AGENT
├── Langfuse integration and trace analysis
├── Prompt performance evaluation and A/B testing
├── Cost optimization and LLM performance analysis
└── Evaluation system bug fixes and improvements

☁️ DEVOPS AGENT
├── Google Cloud Function deployments
├── Infrastructure monitoring and optimization
├── Security and permissions management
└── Production environment maintenance

🔗 INTEGRATION AGENT
├── API endpoint development and management
├── Inter-service communication and data sync
├── Third-party integrations and webhooks
└── Integration testing and validation
```

---

## 📋 **Issue Management Quick Reference**

### **Issue Types & Priorities**
```
🐛 BUG REPORTS
├── Critical: System down, data loss, security vulnerability
├── High: Major functionality broken, poor user experience  
├── Medium: Minor functionality issues, edge cases
└── Low: Cosmetic issues, nice-to-have improvements

🚀 FEATURE REQUESTS
├── High: Core functionality, user-critical features
├── Medium: Enhancement to existing features
└── Low: Nice-to-have additions

🔬 RESEARCH TASKS
├── High: Blocking technical decisions
├── Medium: Architecture improvements
└── Low: Exploration and innovation

🔧 MAINTENANCE
├── Medium: Technical debt, refactoring
└── Low: Code cleanup, documentation
```

### **Assignment Logic**
```
AUTOMATIC ASSIGNMENT RULES:
├── UI keywords → UX Agent
├── Database keywords → Database Agent  
├── Evaluation keywords → Evaluation Agent
├── Cloud keywords → DevOps Agent
├── API keywords → Integration Agent
└── Architecture keywords → Orchestrator
```

---

## 🔄 **Communication Templates**

### **Task Assignment Message Structure**
```json
{
  "message_type": "task_assignment",
  "task_details": {
    "task_id": "ISS-YYYY-MM-XXX",
    "title": "Brief descriptive title",
    "description": "Detailed description",
    "user_story": {"as_a": "", "i_want": "", "so_that": ""},
    "acceptance_criteria": ["requirement 1", "requirement 2"]
  },
  "technical_context": {
    "affected_files": ["file1.py", "file2.html"],
    "dependencies": ["dependency 1"],
    "reference_design": "path/to/reference"
  }
}
```

### **Status Update Message Structure**
```json
{
  "message_type": "status_update", 
  "progress_percentage": 50,
  "progress_details": {
    "completed_items": ["item 1", "item 2"],
    "current_work": "What I'm working on now",
    "next_items": ["next step 1", "next step 2"]
  },
  "findings": {
    "issues_discovered": ["issue 1"],
    "technical_notes": "Important technical details"
  }
}
```

---

## ⚡ **Emergency Procedures**

### **Token Limit Emergency**
```
WHEN TOKENS EXCEED 220,000:
1. 🚨 IMMEDIATELY create emergency handoff document
2. 📋 Document current work state and next steps
3. 📞 Provide specific instructions for Cursor Agent
4. ✅ Ensure no context or work is lost
5. 🔄 Execute handoff with validation checklist
```

### **Critical Bug Response**
```
FOR CRITICAL SYSTEM ISSUES:
1. 🔴 Immediately assign to appropriate specialist agent
2. 📊 Update priority to Critical in issue management  
3. 🚀 Provide detailed reproduction steps
4. ⏰ Set aggressive timeline (4-hour SLA)
5. 📞 Notify all stakeholders of status
```

### **Agent Unavailability**
```
IF ASSIGNED AGENT UNAVAILABLE:
1. 🔄 Escalate to Orchestrator immediately
2. 📋 Reassign based on secondary capabilities
3. 📊 Adjust priorities to maintain critical path
4. 📝 Document reassignment reasoning
5. 🔍 Monitor for quality impact
```

---

## 🎨 **Design Standards Quick Reference**

### **Page Layout Standards**
```
GOLD STANDARD PAGES (Reference These):
├── /prompts/add - Perfect two-column layout with guidance
├── /prompts/ - Ideal card-based grid with consistent styling
└── /prompts/manager - Advanced filtering with test workspace

PAGES NEEDING UPDATES:
├── /prompts/X/edit - Must match add prompt design exactly
└── /prompts/X/view - Needs professional card-based layout
```

### **Component Standards**
```css
/* Primary Buttons */
.btn-primary { background: #007bff; font-weight: 600; }

/* Cards */  
.card { border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }

/* Typography */
h1 { font-size: 1.75rem; font-weight: 700; }
```

---

## 🔧 **Development Guidelines**

### **Code Quality Checklist**
```
BEFORE COMMITTING CODE:
├── ✅ All tests passing (unit, integration, e2e)
├── ✅ Code review completed and approved  
├── ✅ Follows existing code patterns and conventions
├── ✅ Documentation updated for changes
├── ✅ UI matches design standards exactly
├── ✅ Error handling implemented properly
└── ✅ Performance impact considered
```

### **Testing Requirements**
```
TESTING STANDARDS:
├── Unit Tests: 80%+ coverage for new code
├── Integration Tests: Required for API changes
├── UI Tests: Required for interface changes  
├── Performance Tests: Required for critical path
└── Manual Testing: Cross-browser compatibility
```

---

## 📊 **Success Metrics Dashboard**

### **Agent Performance Metrics**
```
KEY PERFORMANCE INDICATORS:
├── Task Completion Rate: >90%
├── Quality Score: 8.0+ average
├── Response Time: <2 hours to first update
├── SLA Compliance: >95%
└── User Satisfaction: 8.5+ rating
```

### **System Health Metrics**
```
SYSTEM PERFORMANCE TARGETS:
├── Uptime: >99.5%
├── Response Time: <500ms p95
├── Error Rate: <1%
├── User Growth: +20% month-over-month
└── Feature Adoption: >70% for new features
```

---

## 🔍 **Troubleshooting Guide**

### **Common Issues & Solutions**
```
EVALUATION REPORT ERROR:
├── Symptom: "'>' not supported between instances"
├── Cause: Database schema mismatch in PromptEvaluator
├── Agent: Database Agent
├── Solution: Align Trace model fields with evaluator expectations
└── Files: app/services/prompt_evaluator.py, app/models.py

UI INCONSISTENCY:
├── Symptom: Pages don't match design standards
├── Cause: Missing implementation of VISUAL_DESIGN_GUIDE
├── Agent: UX Agent  
├── Solution: Apply two-column layout and card styling
└── Reference: templates/prompts/add.html (gold standard)

EMAIL COMMANDS FAILING:
├── Symptom: vertigo-help not responding
├── Cause: Email parsing or Cloud Function issues
├── Agent: Integration Agent
├── Solution: Debug email processing pipeline
└── Files: vertigo/functions/email-processor/
```

### **Escalation Matrix**
```
ISSUE ESCALATION:
├── Agent can't resolve → Escalate to Orchestrator
├── Cross-agent dependency → Orchestrator coordinates
├── Quality standards not met → Orchestrator reviews
├── System architecture impact → Orchestrator decides
└── Resource constraints → Orchestrator reallocates
```

---

## 📞 **Contact & Coordination**

### **Agent Status Dashboard**
```
AGENT WORKLOAD MONITORING:
├── UX Agent: {current_tasks}/3 capacity
├── Database Agent: {current_tasks}/3 capacity
├── Evaluation Agent: {current_tasks}/3 capacity  
├── DevOps Agent: {current_tasks}/2 capacity
└── Integration Agent: {current_tasks}/4 capacity
```

### **Communication Channels**
```
COMMUNICATION FLOW:
├── All agent communication → Through Orchestrator
├── Status updates → Required every 4 hours
├── Blockers → Immediate escalation to Orchestrator
├── Quality issues → Orchestrator review required
└── Handoffs → Follow TOKEN_MANAGEMENT.md protocols
```

---

## 🏁 **Implementation Readiness**

### **Framework Completion Status**
```
✅ COMPLETED DOCUMENTATION:
├── Agent hierarchy and role definitions
├── Sub-agent framework architecture  
├── Communication protocols and templates
├── Issue management system design
├── Development roadmap and timeline
├── Token management and handoff procedures
└── Master index and quick reference

🚀 READY FOR IMPLEMENTATION:
├── All architectural decisions documented
├── Quality standards established
├── Communication protocols defined
├── Emergency procedures planned
├── Success metrics identified
└── Implementation roadmap complete
```

### **Next Steps for Implementation**
```
IMMEDIATE PRIORITIES:
1. 🔴 Fix critical evaluation report error (ISS-2025-08-001)
2. 🟠 Implement agent framework foundation
3. 🟡 Set up Firestore collections for issue management
4. 🟢 Deploy first specialized agents (UX, Database)
5. 🔵 Begin automated task assignment system
```

---

## 📈 **Continuous Improvement**

### **Feedback Loops**
```
IMPROVEMENT MECHANISMS:
├── Weekly agent performance reviews
├── Monthly system architecture assessments  
├── Quarterly strategic roadmap updates
├── Continuous user feedback integration
└── Real-time quality monitoring and adjustment
```

### **Innovation Opportunities**
```
FUTURE ENHANCEMENTS:
├── Machine learning for optimal task assignment
├── Predictive analytics for issue resolution
├── Advanced automation and self-healing
├── Enhanced collaboration and communication
└── Expanded agent specializations
```

---

**🎯 FRAMEWORK SUMMARY**: The Vertigo Sub-Agent Development Framework is now fully documented and ready for implementation. All architectural decisions, communication protocols, quality standards, and emergency procedures are established. The system is designed for scalability, maintainability, and continuous improvement while ensuring high-quality deliverables and seamless agent coordination.

**🚀 IMPLEMENTATION STATUS**: Ready to proceed with Phase 1 implementation focusing on critical bug fixes and framework foundation establishment.

---

*Last Updated: {current_timestamp}*  
*Framework Version: 1.0*  
*Status: Complete and Ready for Implementation*