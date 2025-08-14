# Agent Assignment: ISS-2025-08-004 - Semantic Prompt Search

## 📞 **Message Type**: Task Assignment
**FROM**: Orchestrator Agent  
**TO**: Integration Agent  
**Priority**: High  
**Estimated Hours**: 16-20 hours  
**Deadline**: 2025-08-09 (1 week)

---

## 🎯 **Mission Overview**
Transform the current `/prompts/manager` page (now working with prompts loaded) into an intelligent "Semantic Prompt Search" hub that uses natural language processing and AI to help users discover, test, and optimize prompts efficiently.

## ✅ **Current Status**
- **FIXED**: "0 prompts found" issue resolved (template block mismatch)
- **VERIFIED**: Page now loads 7 prompts successfully
- **READY**: Foundation is solid for enhancement

## 🔧 **Technical Implementation Plan**

### **Phase 1: Backend API Development (6-8 hours)**

#### **1.1 Semantic Search Engine**
```python
# New file: app/services/semantic_search.py
class SemanticPromptSearch:
    def __init__(self):
        # Use lightweight model for fast inference
        self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def search(self, query: str, context: str = None, filters: dict = None):
        # Implementation steps:
        # 1. Generate query embedding
        # 2. Load/generate prompt embeddings  
        # 3. Calculate cosine similarity
        # 4. Apply performance filters
        # 5. Generate match explanations
        # 6. Return ranked results with metadata
        pass
```

#### **1.2 New API Endpoints**
Add to `/app/blueprints/dashboard/routes.py`:

```python
@dashboard_bp.route('/prompts/api/search', methods=['GET'])
def semantic_search_prompts():
    """
    Semantic search endpoint for natural language queries
    Query params: q, context, tags, limit, performance_threshold
    """
    pass

@dashboard_bp.route('/prompts/api/batch-test', methods=['POST']) 
def batch_test_prompts():
    """
    Batch testing endpoint for multiple prompts
    Body: {prompt_ids: [], test_content: str, context: str}
    """
    pass

@dashboard_bp.route('/prompts/api/suggestions', methods=['GET'])
def get_search_suggestions():
    """
    Get semantic suggestions for query expansion
    Query params: q (partial query)
    """
    pass
```

### **Phase 2: Data Enhancement (4-5 hours)**

#### **2.1 Prompt Embedding Generation**
```python
# Add to existing models or create new service
def generate_prompt_embeddings():
    """
    Generate and store embeddings for all existing prompts
    Store in Firestore for fast retrieval
    """
    pass

def update_prompt_metadata():
    """
    Add semantic tags and performance data to existing prompts
    """
    pass
```

#### **2.2 Performance Metrics Integration**
```python
# Integrate with existing Langfuse data
def enrich_with_performance_data(prompts):
    """
    Add performance metrics from traces/costs tables
    Calculate success rates, response times, usage patterns
    """
    pass
```

### **Phase 3: Frontend Enhancement (4-5 hours)**

#### **3.1 Enhanced Search Interface**
Update `/templates/prompts/manager.html`:

```javascript
// Add to existing PromptManager class
class SemanticSearch {
    constructor() {
        this.searchInput = document.getElementById('search-input');
        this.resultsContainer = document.getElementById('results-container');
        this.selectedPrompts = new Set();
        this.setupEventListeners();
    }
    
    async performSearch(query) {
        // Real-time semantic search with debouncing
        // Display match explanations and relevance scores
        // Update suggestions and query interpretation
    }
    
    addToTestQueue(promptId) {
        // Add selected prompts to evaluation queue
    }
    
    runBatchTest() {
        // Execute batch testing workflow
    }
}
```

#### **3.2 Right Column Enhancement**
Transform the existing right column into an evaluation workspace:
- Test queue management
- Batch testing controls  
- AI recommendations
- Performance insights

## 📊 **Success Criteria**

### **Technical Requirements:**
- [ ] API returns results in <500ms for typical queries
- [ ] Search relevance >85% for common use cases
- [ ] All existing functionality preserved
- [ ] No performance degradation on page load

### **User Experience:**
- [ ] Natural language queries work ("find email summarization prompts")
- [ ] Match explanations are clear and helpful
- [ ] Batch testing workflow is intuitive
- [ ] Page maintains existing design standards

### **Integration:**
- [ ] Langfuse performance data properly integrated
- [ ] Firestore queries optimized for search workload
- [ ] Error handling for edge cases and failures

## 🔧 **Implementation Guidelines**

### **Code Quality:**
- Follow existing patterns in the codebase
- Maintain consistency with current Flask structure
- Add comprehensive error handling
- Include logging for debugging and monitoring

### **Testing Strategy:**
- Unit tests for search algorithm accuracy
- Integration tests for API endpoints
- Frontend tests for user interactions
- Performance tests for search response time

### **Documentation:**
- Update API documentation
- Add code comments for search logic
- Document new endpoints and parameters

## 📁 **Key Files to Work With**

### **Backend Files:**
- `/app/blueprints/dashboard/routes.py` - Add new endpoints
- `/app/services/` - Create semantic_search.py
- `/app/models.py` - Enhance if needed for search data

### **Frontend Files:**
- `/templates/prompts/manager.html` - Main page template
- `/static/js/` - Add semantic search JavaScript
- Navigation templates - Update page title references

### **Reference Files:**
- `/templates/prompts/add.html` - Gold standard design
- `VISUAL_DESIGN_GUIDE.md` - Maintain design consistency
- Existing Langfuse integration patterns

## 🤝 **Coordination Needs**

### **UX Agent Collaboration:**
- Interface design review after Phase 1 backend completion
- User experience testing and feedback
- Design standard compliance validation

### **Evaluation Agent Input:**
- Langfuse integration best practices
- Performance metrics interpretation
- Testing workflow optimization

### **Orchestrator Checkpoints:**
- Progress review after each phase
- Quality validation before user-facing changes
- Integration testing coordination

## ⚡ **Getting Started**

### **Immediate Next Steps:**
1. **Set up development environment** for semantic search
2. **Install required dependencies** (sentence-transformers, sklearn)
3. **Create basic search service structure** 
4. **Test with existing 7 prompts** to validate approach

### **First Milestone (24-48 hours):**
- Basic semantic search API endpoint working
- Simple similarity search returning results
- Initial integration with existing prompt data

## 📞 **Communication Protocol**

### **Status Updates Required:**
- **Daily progress updates** with current phase and blockers
- **Immediate escalation** for architectural decisions
- **Collaboration requests** when UX Agent input needed

### **Quality Checkpoints:**
- **Phase 1 Complete**: Backend API demo with search results
- **Phase 2 Complete**: Enhanced data with performance metrics
- **Phase 3 Complete**: Full frontend integration and testing

---

## 🚀 **Ready to Begin**

**Integration Agent**: Please confirm understanding of this assignment and provide estimated start time. The foundation is solid and ready for enhancement.

**Expected Deliverable**: Transform the current working Prompt Manager into an intelligent Semantic Prompt Search hub that revolutionizes how users discover and evaluate prompts.

**Success Impact**: 50% faster prompt discovery, 90% search relevance, and streamlined evaluation workflows.

---

**Assignment Created**: 2025-08-02T11:15:00Z  
**Orchestrator**: Claude Code  
**Status**: Awaiting Agent Acknowledgment