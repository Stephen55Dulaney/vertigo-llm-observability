# Token Management & Emergency Handoff Procedures

## 🎯 **Token Management Overview**

The Token Management System ensures seamless continuation of work when conversation limits are approached, maintaining quality and context through sophisticated handoff protocols between Claude Code and Cursor Agent.

---

## 📊 **Token Monitoring System**

### **Token Thresholds & Actions**
```python
class TokenMonitor:
    """Advanced token usage monitoring and management"""
    
    def __init__(self):
        self.token_limits = {
            "max_context": 225000,      # Absolute maximum
            "emergency": 220000,        # 98% - Emergency handoff required
            "critical": 200000,         # 89% - Prepare handoff immediately  
            "warning": 180000,          # 80% - Plan handoff strategy
            "optimal": 160000,          # 71% - Begin handoff preparation
            "safe": 140000             # 62% - Normal operation
        }
        
        self.handoff_strategies = {
            "emergency": "immediate_emergency_handoff",
            "critical": "structured_critical_handoff", 
            "warning": "planned_handoff_preparation",
            "optimal": "handoff_context_preparation",
            "safe": "continue_normal_operation"
        }
        
    def get_token_status(self, current_tokens: int):
        """Determine current token status and required action"""
        for status, threshold in reversed(self.token_limits.items()):
            if current_tokens >= threshold:
                return {
                    "status": status,
                    "threshold": threshold,
                    "remaining": self.token_limits["max_context"] - current_tokens,
                    "action": self.handoff_strategies[status],
                    "urgency": self.calculate_urgency(status),
                    "estimated_exchanges": self.estimate_remaining_exchanges(current_tokens)
                }
        return {
            "status": "safe",
            "action": "continue_normal_operation",
            "urgency": "none"
        }
        
    def estimate_remaining_exchanges(self, current_tokens: int):
        """Estimate remaining conversation exchanges"""
        remaining_tokens = self.token_limits["max_context"] - current_tokens
        
        # Conservative estimates for different types of exchanges
        exchange_estimates = {
            "simple_response": 1500,
            "code_generation": 3000, 
            "complex_analysis": 4500,
            "handoff_preparation": 8000
        }
        
        return {
            "simple": remaining_tokens // exchange_estimates["simple_response"],
            "code": remaining_tokens // exchange_estimates["code_generation"],
            "complex": remaining_tokens // exchange_estimates["complex_analysis"],
            "handoff": remaining_tokens // exchange_estimates["handoff_preparation"]
        }
```

### **Proactive Token Management**
```python
class ProactiveTokenManager:
    """Proactively manage token usage to optimize handoffs"""
    
    def __init__(self):
        self.context_optimization = {
            "summarize_old_context": True,
            "compress_redundant_info": True,
            "extract_key_decisions": True,
            "maintain_critical_context": True
        }
        
    def optimize_context_for_handoff(self, conversation_history: list):
        """Optimize conversation context for clean handoff"""
        optimization_result = {
            "summarized_context": self.summarize_early_context(conversation_history),
            "key_decisions": self.extract_key_decisions(conversation_history),
            "active_work": self.identify_active_work(conversation_history),
            "critical_context": self.preserve_critical_context(conversation_history),
            "handoff_instructions": self.generate_handoff_instructions(conversation_history)
        }
        
        return optimization_result
        
    def prepare_handoff_documentation(self, current_status: dict):
        """Prepare comprehensive handoff documentation"""
        handoff_doc = {
            "executive_summary": self.create_executive_summary(current_status),
            "technical_context": self.extract_technical_context(current_status),
            "immediate_actions": self.identify_immediate_actions(current_status),
            "quality_requirements": self.define_quality_requirements(current_status),
            "success_criteria": self.establish_success_criteria(current_status),
            "reference_materials": self.gather_reference_materials(current_status)
        }
        
        return handoff_doc
```

---

## 🚨 **Emergency Handoff Protocols**

### **CRITICAL: Emergency Handoff Template**
```markdown
# 🚨 EMERGENCY TOKEN LIMIT HANDOFF

## IMMEDIATE STATUS REPORT
- **Token Count**: ~{current_tokens} / 225,000 (CRITICAL)
- **Remaining Capacity**: <{remaining_exchanges} exchanges
- **Handoff Reason**: Emergency token limit approaching
- **Timestamp**: {current_timestamp}

## 🎯 ACTIVE WORK CONTEXT

### Primary Task in Progress:
**Task ID**: {task_id}
**Title**: {task_title}
**Agent Assignment**: {assigned_agent}
**Completion Status**: {completion_percentage}%

### Current State:
- **Files Being Modified**: 
  - `{file_path_1}` - {modification_description}
  - `{file_path_2}` - {modification_description}
  
- **Incomplete Code**: 
  ```{language}
  {incomplete_code_snippet}
  ```

- **Last Successful Action**: {last_action_description}

## 🚀 IMMEDIATE NEXT STEPS FOR CURSOR AGENT

### Step 1: {immediate_step_1}
- **Action**: {specific_action}
- **Files**: {file_paths}
- **Expected Outcome**: {expected_result}

### Step 2: {immediate_step_2}  
- **Action**: {specific_action}
- **Files**: {file_paths}
- **Expected Outcome**: {expected_result}

### Step 3: {immediate_step_3}
- **Action**: {specific_action}
- **Files**: {file_paths}
- **Expected Outcome**: {expected_result}

## ✅ COMPLETION CRITERIA
- [ ] {specific_requirement_1}
- [ ] {specific_requirement_2}
- [ ] {specific_requirement_3}
- [ ] {specific_requirement_4}

## 📋 CONTEXT FILES TO READ
- `{context_file_1}` - {why_important}
- `{context_file_2}` - {why_important}
- `{context_file_3}` - {why_important}

## 🔧 TECHNICAL REQUIREMENTS
- **Code Style**: Follow existing patterns in modified files
- **Testing**: {specific_testing_requirements}
- **Documentation**: Update {specific_docs} after changes
- **Quality**: Maintain {quality_standards}

## ⚠️ CRITICAL WARNINGS
- **Avoid**: {things_to_avoid}
- **Must Include**: {required_elements}
- **Dependencies**: {blocking_dependencies}

## 🎨 DESIGN REQUIREMENTS
- Follow `VISUAL_DESIGN_GUIDE.md` standards
- Maintain consistency with existing UI patterns
- Test responsive behavior on multiple screen sizes

## 🤖 AGENT COORDINATION NOTES
- **Other Active Agents**: {other_agents_status}
- **Pending Reviews**: {pending_review_items}
- **Blocked Issues**: {blocking_issues}

---

## 📞 HANDOFF VALIDATION CHECKLIST
**Cursor Agent MUST confirm:**
- [ ] ✅ Understood the incomplete task and next steps
- [ ] ✅ Located and reviewed all mentioned files  
- [ ] ✅ Ready to continue from specified step
- [ ] ✅ Committed to quality requirements and testing
- [ ] ✅ Aware of design standards and dependencies

---

**EMERGENCY HANDOFF COMPLETED**: {timestamp}
**CURSOR AGENT**: Please acknowledge understanding and begin with Step 1
```

### **Structured Critical Handoff Template**
```markdown
# 📋 CRITICAL HANDOFF - Structured Transition

## HANDOFF OVERVIEW
- **Handoff Type**: Structured Critical (Token optimization)
- **Current Token Usage**: ~{current_tokens} / 225,000
- **Handoff Urgency**: High (Limited remaining capacity)
- **Estimated Remaining Work**: {estimated_hours} hours

## 📊 PROJECT STATUS SUMMARY

### Completed This Session:
1. ✅ **{completed_task_1}** - {brief_outcome}
2. ✅ **{completed_task_2}** - {brief_outcome}
3. ✅ **{completed_task_3}** - {brief_outcome}

### In Progress:
1. 🔄 **{in_progress_task_1}** - {current_status} ({percentage}% complete)
2. 🔄 **{in_progress_task_2}** - {current_status} ({percentage}% complete)

### Pending (Next Priority):
1. 📋 **{pending_task_1}** - {brief_description}
2. 📋 **{pending_task_2}** - {brief_description}

## 🎯 IMMEDIATE FOCUS AREA

### Primary Objective:
**Complete {primary_objective}** to unblock {dependent_work}

### Approach Strategy:
1. {strategic_step_1}
2. {strategic_step_2}
3. {strategic_step_3}

### Files Requiring Attention:
- **Primary**: `{primary_file}` - {what_needs_to_be_done}
- **Secondary**: `{secondary_file}` - {what_needs_to_be_done}
- **Reference**: `{reference_file}` - {why_this_is_relevant}

## 🔧 TECHNICAL CONTEXT

### Current System State:
- **Database**: {database_status_and_changes}
- **UI Components**: {ui_status_and_changes}  
- **API Endpoints**: {api_status_and_changes}
- **Testing Coverage**: {testing_status}

### Recent Changes Made:
```{language}
// Key changes implemented this session
{recent_code_changes}
```

### Configuration Updates:
- {config_change_1}
- {config_change_2}

## 📋 QUALITY STANDARDS CHECKLIST

### Code Quality:
- [ ] Follow existing code patterns and conventions
- [ ] Maintain consistent naming and structure
- [ ] Add appropriate error handling
- [ ] Include relevant comments for complex logic

### Testing Requirements:
- [ ] Write/update unit tests for new functionality
- [ ] Verify integration points work correctly
- [ ] Test error scenarios and edge cases
- [ ] Validate UI components across screen sizes

### Documentation:
- [ ] Update relevant README files
- [ ] Add/update code comments
- [ ] Update API documentation if applicable
- [ ] Maintain design documentation consistency

## 🚀 SUCCESS METRICS

### Immediate Success (Next 2-3 hours):
- [ ] {immediate_success_metric_1}
- [ ] {immediate_success_metric_2}
- [ ] {immediate_success_metric_3}

### Session Success (End of work session):
- [ ] {session_success_metric_1}
- [ ] {session_success_metric_2}
- [ ] {session_success_metric_3}

## 📚 REFERENCE MATERIALS

### Essential Reading:
- `AGENT_HIERARCHY.md` - Understanding agent roles and responsibilities
- `SUB_AGENT_FRAMEWORK.md` - Technical framework implementation
- `VISUAL_DESIGN_GUIDE.md` - UI/UX standards and patterns
- `{project_specific_doc}` - {why_this_is_important}

### Code References:
- Look at `{example_file_1}` for implementation patterns
- Reference `{example_file_2}` for similar functionality
- Check `{example_file_3}` for error handling approaches

## 🤖 AGENT COORDINATION

### Current Agent Status:
- **UX Agent**: {status_and_current_work}
- **Database Agent**: {status_and_current_work}
- **Evaluation Agent**: {status_and_current_work}

### Coordination Notes:
- {coordination_note_1}
- {coordination_note_2}

## 🔄 NEXT HANDOFF PLANNING

### Optimal Handoff Point:
After completing {specific_milestone}, handoff should occur at a natural break point

### Context to Preserve:
- {context_item_1}
- {context_item_2}
- {context_item_3}

---

**HANDOFF TIMESTAMP**: {current_timestamp}
**CURSOR AGENT ONBOARDING**: Please review reference materials and confirm understanding of immediate objectives before proceeding.
```

---

## 🔄 **Planned Handoff Procedures**

### **Optimal Handoff Strategy**
```python
class PlannedHandoffManager:
    """Manage planned handoffs at optimal break points"""
    
    def __init__(self):
        self.optimal_handoff_points = [
            "task_completion",
            "major_milestone_reached", 
            "natural_break_in_work",
            "before_complex_implementation",
            "after_successful_testing"
        ]
        
    def identify_handoff_opportunity(self, current_context: dict):
        """Identify optimal handoff opportunities"""
        opportunities = []
        
        # Check for completed tasks
        if current_context.get("completed_tasks"):
            opportunities.append({
                "type": "task_completion",
                "score": 10,
                "reason": "Clean completion of assigned tasks"
            })
            
        # Check for natural break points
        if current_context.get("current_phase") in ["planning", "documentation"]:
            opportunities.append({
                "type": "natural_break",
                "score": 8,
                "reason": "End of planning/documentation phase"
            })
            
        # Check for milestone completion
        if current_context.get("milestone_progress", 0) >= 100:
            opportunities.append({
                "type": "milestone_completion", 
                "score": 9,
                "reason": "Major milestone achieved"
            })
            
        return sorted(opportunities, key=lambda x: x["score"], reverse=True)
        
    def prepare_context_transfer(self, handoff_point: dict):
        """Prepare context for smooth transfer"""
        context_package = {
            "executive_summary": self.create_executive_summary(),
            "completed_work": self.document_completed_work(),
            "current_status": self.capture_current_status(),
            "next_priorities": self.define_next_priorities(),
            "reference_materials": self.compile_reference_materials(),
            "quality_standards": self.document_quality_standards(),
            "handoff_validation": self.create_validation_checklist()
        }
        
        return context_package
```

### **Handoff Quality Assurance**
```python
class HandoffQualityAssurance:
    """Ensure handoff quality and completeness"""
    
    def __init__(self):
        self.quality_checklist = {
            "context_completeness": [
                "Current work status documented",
                "Next steps clearly defined", 
                "Quality requirements specified",
                "Reference materials provided",
                "Success criteria established"
            ],
            "technical_accuracy": [
                "File paths are correct and accessible",
                "Code snippets are valid and complete",
                "Dependencies are clearly identified",
                "Environment setup is documented"
            ],
            "actionability": [
                "Next steps are specific and actionable",
                "Expected outcomes are clearly defined",
                "Success criteria are measurable",
                "Potential blockers are identified"
            ]
        }
        
    def validate_handoff_quality(self, handoff_document: dict):
        """Validate handoff document meets quality standards"""
        validation_results = {}
        
        for category, checks in self.quality_checklist.items():
            category_score = 0
            category_results = []
            
            for check in checks:
                passed = self.evaluate_check(handoff_document, check)
                category_results.append({
                    "check": check,
                    "passed": passed,
                    "score": 1 if passed else 0
                })
                category_score += 1 if passed else 0
                
            validation_results[category] = {
                "score": category_score / len(checks),
                "results": category_results
            }
            
        overall_score = sum(cat["score"] for cat in validation_results.values()) / len(validation_results)
        
        return {
            "overall_score": overall_score,
            "category_scores": validation_results,
            "quality_level": self.determine_quality_level(overall_score),
            "recommendations": self.generate_improvement_recommendations(validation_results)
        }
```

---

## 📞 **Cursor Agent Onboarding Protocol**

### **Onboarding Checklist Template**
```markdown
# 🚀 CURSOR AGENT ONBOARDING CHECKLIST

## INITIAL CONTEXT REVIEW
- [ ] **Read Handoff Document**: Understand current status and immediate priorities
- [ ] **Review Project Structure**: Familiarize with Vertigo architecture
- [ ] **Check File Access**: Verify ability to access all mentioned files
- [ ] **Understand Quality Standards**: Review VISUAL_DESIGN_GUIDE.md and standards

## TECHNICAL SETUP VALIDATION
- [ ] **Development Environment**: Confirm proper setup for local development
- [ ] **Database Access**: Verify Firestore connection and permissions
- [ ] **Testing Framework**: Ensure ability to run tests and validations
- [ ] **Dependencies**: Check all required packages and tools are available

## WORK CONTEXT UNDERSTANDING
- [ ] **Active Tasks**: Understand current in-progress work
- [ ] **Next Priorities**: Clear on immediate next steps
- [ ] **Success Criteria**: Know how to measure completion
- [ ] **Quality Requirements**: Understand quality standards and testing needs

## AGENT COORDINATION AWARENESS
- [ ] **Other Agents**: Understand status of other agent work
- [ ] **Communication Protocol**: Know how to coordinate with other agents
- [ ] **Escalation Process**: Understand when to seek help or clarification
- [ ] **Progress Reporting**: Know how to update status and document progress

## FINAL VALIDATION
- [ ] **Handoff Acknowledgment**: Confirm understanding of handoff context
- [ ] **Ready to Proceed**: Confirm readiness to begin immediate next steps
- [ ] **Questions Resolved**: All unclear points have been addressed
- [ ] **Quality Commitment**: Committed to maintaining established standards

---

**ONBOARDING COMPLETED**: {timestamp}
**STATUS**: Ready to begin work with full context understanding
```

### **Context Validation Protocol**
```python
class CursorAgentOnboarding:
    """Manage Cursor Agent onboarding and context validation"""
    
    def __init__(self):
        self.validation_steps = [
            "verify_file_access",
            "confirm_task_understanding", 
            "validate_technical_setup",
            "check_quality_requirements",
            "ensure_coordination_awareness"
        ]
        
    def validate_context_transfer(self, handoff_context: dict):
        """Validate Cursor Agent understands handoff context"""
        validation_questions = {
            "immediate_next_steps": "What are the first 3 actions you will take?",
            "success_criteria": "How will you know when the current task is complete?",
            "quality_requirements": "What quality standards must be maintained?",
            "file_modifications": "Which files need to be modified and why?",
            "testing_approach": "What testing will be performed to validate changes?",
            "coordination_needs": "Are there any dependencies on other agents?"
        }
        
        return validation_questions
        
    def generate_onboarding_summary(self, handoff_context: dict):
        """Generate concise onboarding summary for quick reference"""
        summary = {
            "primary_objective": handoff_context.get("primary_objective"),
            "immediate_actions": handoff_context.get("immediate_actions", [])[:3],
            "key_files": handoff_context.get("key_files", [])[:5],
            "success_metrics": handoff_context.get("success_criteria", [])[:3],
            "quality_requirements": handoff_context.get("quality_requirements", [])[:3],
            "reference_docs": handoff_context.get("reference_materials", [])[:3]
        }
        
        return summary
```

---

## 🔧 **Token Optimization Strategies**

### **Context Compression Techniques**
```python
class ContextOptimization:
    """Optimize conversation context to extend token capacity"""
    
    def __init__(self):
        self.compression_strategies = {
            "summarize_repetitive_content": True,
            "extract_key_decisions": True,
            "compress_large_code_blocks": True,
            "maintain_critical_context": True,
            "archive_completed_work": True
        }
        
    def compress_conversation_history(self, conversation: list):
        """Compress conversation while preserving critical information"""
        compressed_context = {
            "key_decisions": self.extract_key_decisions(conversation),
            "active_work_context": self.preserve_active_work(conversation),
            "technical_context": self.maintain_technical_context(conversation),
            "quality_requirements": self.preserve_quality_requirements(conversation),
            "recent_exchanges": self.keep_recent_exchanges(conversation, count=10)
        }
        
        return compressed_context
        
    def optimize_for_handoff(self, context: dict):
        """Optimize context specifically for handoff scenarios"""
        handoff_optimized = {
            "executive_summary": self.create_executive_summary(context),
            "critical_context": self.extract_critical_context(context),
            "actionable_items": self.identify_actionable_items(context),
            "reference_materials": self.compile_essential_references(context),
            "validation_criteria": self.establish_validation_criteria(context)
        }
        
        return handoff_optimized
```

---

## 📊 **Handoff Performance Metrics**

### **Success Tracking**
```python
class HandoffMetrics:
    """Track handoff performance and quality"""
    
    def __init__(self):
        self.metrics = {
            "handoff_success_rate": 0.0,
            "context_preservation_score": 0.0,
            "continuation_quality": 0.0,
            "time_to_productivity": 0.0
        }
        
    def measure_handoff_success(self, handoff_event: dict):
        """Measure success metrics for handoff event"""
        success_metrics = {
            "context_transfer_completeness": self.measure_context_completeness(handoff_event),
            "continuation_seamlessness": self.measure_continuation_quality(handoff_event), 
            "quality_maintenance": self.measure_quality_consistency(handoff_event),
            "productivity_restoration": self.measure_productivity_recovery(handoff_event)
        }
        
        overall_success = sum(success_metrics.values()) / len(success_metrics)
        
        return {
            "overall_success": overall_success,
            "detailed_metrics": success_metrics,
            "improvement_areas": self.identify_improvement_areas(success_metrics)
        }
```

---

**Next Document**: [Master Index and Quick Reference](VERTIGO_MASTER_INDEX.md)