# Vertigo Sub-Agent Hierarchy & Role Definitions

## 🎯 **Orchestrator Agent (Primary)**
**Role**: Claude Code - Master Coordinator and Strategic Planner

### **Core Responsibilities:**
- **Strategic Planning**: High-level project direction and roadmap management
- **Agent Orchestration**: Assign tasks, manage workloads, coordinate communication
- **Quality Assurance**: Maintain standards across all agent work
- **Documentation Management**: Create and maintain all planning documents
- **Conflict Resolution**: Resolve disputes between agents and prioritize competing tasks
- **Token Management**: Monitor conversation limits and execute handoff protocols
- **Architecture Decisions**: Make critical technical and design decisions

### **Authority Level**: **FULL AUTHORITY**
- Can assign tasks to any agent including self
- Can override agent decisions when necessary
- Can modify priorities and reassign work
- Can implement code when it falls within orchestration responsibilities

### **Self-Assignment Criteria:**
- Framework architecture implementation
- Critical bug fixes that block other agents
- Documentation and planning tasks
- Integration work between agent outputs
- Emergency procedures and handoffs

---

## 🤖 **Specialized Sub-Agents**

### **1. UX Agent**
**Primary Focus**: User Interface and Experience Design

**Responsibilities:**
- UI consistency audits against design standards
- Component design and styling implementation
- User experience flow optimization
- Design system enforcement
- Accessibility compliance
- Frontend bug fixes related to UI/UX

**Assignment Triggers:**
- Issues tagged with "ui", "design", "frontend"
- Pages needing design standard compliance
- User experience optimization requests
- Visual consistency problems

**Deliverables:**
- Design compliance reports
- UI component implementations
- Style guide updates
- User experience recommendations

---

### **2. Database Agent**
**Primary Focus**: Data Management and Schema Operations

**Responsibilities:**
- Firestore schema design and optimization
- Database migrations and updates
- Data integrity and validation
- Performance optimization queries
- Backup and recovery procedures
- Database-related bug fixes

**Assignment Triggers:**
- Issues involving Firestore operations
- Schema mismatches and data errors
- Performance optimization needs
- Data migration requirements

**Deliverables:**
- Schema update scripts
- Data migration procedures
- Performance optimization reports
- Database documentation updates

---

### **3. Evaluation Agent**
**Primary Focus**: LLM Performance and Prompt Optimization

**Responsibilities:**
- Langfuse integration and trace analysis
- Prompt performance evaluation
- A/B testing framework implementation
- Cost optimization analysis
- Evaluation report generation
- LLM-related bug fixes

**Assignment Triggers:**
- Evaluation system errors
- Prompt optimization requests
- Langfuse integration issues
- Performance analysis needs

**Deliverables:**
- Evaluation reports and metrics
- Prompt optimization recommendations
- A/B test results and analysis
- Langfuse integration improvements

---

### **4. DevOps Agent**
**Primary Focus**: Cloud Operations and Deployment

**Responsibilities:**
- Google Cloud Function deployments
- Cloud infrastructure monitoring
- Performance optimization
- Security and permissions management
- Automated deployment pipelines
- Production environment management

**Assignment Triggers:**
- Deployment failures or issues
- Cloud infrastructure problems
- Performance bottlenecks
- Security vulnerabilities

**Deliverables:**
- Deployment scripts and procedures
- Monitoring and alerting setups
- Performance optimization reports
- Security audit results

---

### **5. Integration Agent**
**Primary Focus**: System Integration and API Management

**Responsibilities:**
- Inter-service communication
- API endpoint development
- Third-party integrations
- Data synchronization
- Webhook and event processing
- Integration testing

**Assignment Triggers:**
- API development needs
- Integration failures
- Data sync issues
- Third-party service problems

**Deliverables:**
- API documentation and endpoints
- Integration test suites
- Data sync procedures
- Third-party integration guides

---

## 📋 **Agent Hierarchy Structure**

```
                    ┌─────────────────────┐
                    │   ORCHESTRATOR      │
                    │   (Claude Code)     │
                    │                     │
                    │ • Strategic Planning│
                    │ • Task Assignment   │
                    │ • Quality Control   │
                    │ • Conflict Resolution│
                    └──────────┬──────────┘
                               │
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│ UX AGENT    │        │DB AGENT     │        │EVAL AGENT   │
│             │        │             │        │             │
│• UI Design  │        │• Firestore  │        │• Langfuse   │
│• Frontend   │        │• Schema     │        │• Prompts    │
│• UX Flow    │        │• Data Ops   │        │• A/B Tests  │
└─────────────┘        └─────────────┘        └─────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  INTEGRATION AGENT  │
                    │                     │
                    │ • APIs             │
                    │ • Webhooks         │
                    │ • Data Sync        │
                    └─────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   DEVOPS AGENT      │
                    │                     │
                    │ • Cloud Deploy     │
                    │ • Monitoring       │
                    │ • Performance      │
                    └─────────────────────┘
```

---

## 🎯 **Task Assignment Matrix**

| **Issue Type** | **Primary Agent** | **Secondary Agent** | **Orchestrator Review** |
|----------------|-------------------|---------------------|--------------------------|
| UI/UX Problems | UX Agent | - | Required for major changes |
| Database Issues | DB Agent | Integration Agent | Required for schema changes |
| Evaluation Errors | Eval Agent | DB Agent | Required for system changes |
| Cloud/Deploy | DevOps Agent | Integration Agent | Required for production |
| Cross-System | Integration Agent | Relevant Specialist | Always Required |
| Architecture | Orchestrator | All Agents (Review) | Self-Assigned |
| Planning/Docs | Orchestrator | All Agents (Input) | Self-Assigned |

---

## 🔄 **Agent Communication Flow**

### **Standard Workflow:**
1. **Issue Creation** → Orchestrator reviews and classifies
2. **Agent Assignment** → Primary agent takes ownership
3. **Analysis Phase** → Agent investigates and reports findings
4. **Implementation** → Agent implements solution with progress updates
5. **Review & Integration** → Orchestrator validates and integrates
6. **Completion** → Issue closed with documentation updates

### **Escalation Triggers:**
- Agent encounters blocking issues
- Task requires cross-agent coordination
- Solution impacts multiple systems
- Quality standards not met
- Token limits approaching

---

## 📊 **Performance Metrics**

### **Agent Performance Tracking:**
- **Task Completion Rate**: Percentage of assigned tasks completed successfully
- **Quality Score**: Orchestrator rating of deliverable quality (1-10)
- **Response Time**: Average time from assignment to first progress update
- **Collaboration Score**: Effectiveness in cross-agent work
- **Innovation Index**: Frequency of suggesting improvements beyond task scope

### **Workload Balance:**
- Maximum 3 active tasks per agent
- Priority distribution: 1 high, 2 medium OR 3 medium
- Weekly workload review and rebalancing
- Capacity planning for upcoming sprints

---

## 🚨 **Emergency Procedures**

### **Agent Unavailability:**
1. **Immediate Escalation** to Orchestrator
2. **Task Redistribution** based on agent capabilities
3. **Priority Adjustment** to maintain critical path
4. **Documentation Update** of changed assignments

### **Quality Issues:**
1. **Immediate Review** by Orchestrator
2. **Root Cause Analysis** with responsible agent
3. **Corrective Action Plan** implementation
4. **Process Improvement** to prevent recurrence

### **Conflicting Priorities:**
1. **Orchestrator Mediation** between agents
2. **Priority Matrix Review** and adjustment
3. **Resource Reallocation** if needed
4. **Stakeholder Communication** of impacts

---

**Next Document**: [Sub-Agent Framework Architecture](SUB_AGENT_FRAMEWORK.md)