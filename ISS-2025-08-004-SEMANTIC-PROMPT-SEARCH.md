# Feature Request: Transform Prompt Manager into Semantic Prompt Search Hub

## 🎯 Issue Classification
- **Issue ID**: ISS-2025-08-004
- **Type**: Feature Enhancement  
- **Priority**: High
- **Component**: debug-toolkit/evaluation
- **Epic**: Prompt Evaluation Hub
- **Estimated Hours**: 16-20 hours
- **Story Points**: 13

## 👤 User Story
**As a** AI/UX team member working with prompt evaluation  
**I want** intelligent semantic search that understands my intent beyond exact keywords  
**So that** I can quickly discover, test, and optimize prompts efficiently for specific evaluation scenarios

## 💡 Feature Description

Transform the current `/prompts/manager` page from a basic prompt management interface into a comprehensive "Semantic Prompt Search" hub that serves as the core evaluation workflow tool. This addresses the current pain point where users must manually scan prompt cards to find relevant ones for testing.

### Current Issues Identified:
1. **Page shows "0 prompts found"** - Data loading/connection issue
2. **Basic keyword-only search** - Limited discovery capabilities  
3. **Generic "Prompt Manager" naming** - Doesn't reflect evaluation focus
4. **Underutilized right column** - Could enhance evaluation workflow

## 🎨 Proposed Solution

### 1. Page Transformation
- **Rename**: "Prompt Manager" → "🔍 Semantic Prompt Search"
- **Navigation Update**: Update all navigation references
- **URL Structure**: Keep `/prompts/manager` for consistency, update page title and breadcrumbs
- **Design Enhancement**: Maintain existing layout while adding semantic search capabilities

### 2. Intelligent Semantic Search Engine
```typescript
// Core search functionality
GET /api/prompts/search
Query params:
- q: string (natural language query)
- context?: string (project context for relevance)
- tags?: string[] (filter by semantic tags)  
- limit?: number (default 10)
- performance_threshold?: number (min success rate)
- sort_by?: 'relevance' | 'performance' | 'recent' | 'usage'

Response:
{
  results: Array<{
    id: string,
    name: string,
    type: string,
    tags: string[],
    relevance_score: number,
    match_reasons: string[], // AI-generated explanations
    performance_metrics: {
      success_rate: number,
      avg_response_time: number,
      usage_count: number,
      last_used: string
    },
    preview_content: string // First 150 chars
  }>,
  total: number,
  semantic_suggestions: string[], // "Also try: email summarization, meeting analysis"
  query_interpretation: string // "Searching for: email-related prompts with good performance"
}
```

### 3. Enhanced User Interface

#### Search Experience:
- **Natural Language Input**: "find prompts for email summarization" 
- **Smart Suggestions**: Auto-complete with semantic suggestions
- **Query Interpretation**: Show how the system understood the search
- **Match Explanations**: Display why each prompt matched

#### Results Display:
- **Relevance Scoring**: Visual indicators of match quality
- **Performance Badges**: Quick visual performance indicators
- **Usage Patterns**: Show when/how often prompts are used
- **Quick Actions**: Test, Compare, Optimize directly from results

#### Right Column Enhancement:
```
🔍 Semantic Prompt Search

┌─ SEARCH RESULTS ────────────┐  ┌─ EVALUATION WORKSPACE ──────┐
│ Natural language search     │  │ 🎯 Quick Actions             │
│ [find email summary prompts]│  │ ✅ Add to Test Queue         │
│                            │  │ ⚖️ Compare Selected          │
│ 📊 Found 8 relevant prompts│  │ 🚀 Batch Test Runner         │
│                            │  │                              │
│ 🎯 Meeting Analysis v2      │  │ 📝 Test Workspace            │
│ Tags: meeting, executive    │  │ Sample Content:              │
│ Match: 95% relevance       │  │ [Email content here]         │
│ Performance: 8.7/10        │  │                              │
│ Last used: 2 days ago      │  │ Context: [Project Alpha ▼]   │
│ [Test] [Compare] [View]    │  │                              │
│                            │  │ [🧪 Test Selected Prompts]   │
│ 📧 Email Summary v1        │  │                              │
│ Tags: email, summary       │  │ 📊 Evaluation Queue          │
│ Match: 87% relevance       │  │ • Meeting Analysis v2        │
│ Performance: 9.1/10        │  │ • Email Summary v1           │
│ Last used: 1 hour ago      │  │ • Daily Standup              │
│ [Test] [Compare] [View]    │  │                              │
└────────────────────────────┘  │ [📈 Run Batch Evaluation]    │
                                │                              │
                                │ 💡 AI Recommendations        │
                                │ Based on your search:        │
                                │ • Try "action item extract"  │
                                │ • Consider A/B testing v1/v2 │
                                │ • Check recent performance   │
                                └──────────────────────────────┘
```

## 📋 Acceptance Criteria

### Core Functionality:
- [ ] **Data Loading Fixed**: Page loads existing prompts (no more "0 prompts found")
- [ ] **Semantic Search Active**: Natural language queries return relevant results
- [ ] **Navigation Updated**: All references changed to "Semantic Prompt Search"
- [ ] **Performance Integration**: Results include Langfuse performance metrics
- [ ] **Match Explanations**: AI-generated reasons for each result

### Search Quality:
- [ ] **Intent Understanding**: Queries like "email summarization" find relevant prompts
- [ ] **Context Awareness**: Project context influences result relevance
- [ ] **Performance Filtering**: Can filter by success rate, response time
- [ ] **Smart Suggestions**: System suggests related search terms
- [ ] **Result Ranking**: Most relevant prompts appear first

### User Experience:
- [ ] **Responsive Design**: Works on all screen sizes per design standards
- [ ] **Fast Response**: Search results appear in <500ms
- [ ] **Clear Feedback**: Users understand why results were returned
- [ ] **Easy Actions**: One-click testing, comparison, optimization
- [ ] **Batch Operations**: Select multiple prompts for bulk actions

### Evaluation Workflow:
- [ ] **Test Queue**: Add prompts to evaluation queue
- [ ] **Batch Testing**: Run multiple prompts against same content
- [ ] **Performance Comparison**: Side-by-side prompt performance
- [ ] **AI Recommendations**: System suggests optimization opportunities

## 🔧 Technical Requirements

### Backend Implementation:
```python
# New search service
class SemanticPromptSearch:
    def __init__(self):
        self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.prompt_index = None
        
    def search(self, query: str, context: str = None, filters: dict = None):
        # 1. Generate query embedding
        query_embedding = self.embeddings_model.encode([query])
        
        # 2. Semantic similarity search
        prompt_embeddings = self.get_prompt_embeddings()
        similarities = cosine_similarity(query_embedding, prompt_embeddings)
        
        # 3. Apply performance filters
        filtered_results = self.apply_filters(similarities, filters)
        
        # 4. Generate match explanations
        explanations = self.generate_match_reasons(query, filtered_results)
        
        return {
            'results': filtered_results,
            'explanations': explanations,
            'suggestions': self.generate_suggestions(query)
        }
```

### Frontend Enhancement:
```typescript
// Enhanced search component
interface SearchState {
  query: string;
  results: SearchResult[];
  loading: boolean;
  suggestions: string[];
  selectedPrompts: string[];
  testQueue: PromptTest[];
}

// Real-time search with debouncing
const useSemanticSearch = () => {
  const [searchState, setSearchState] = useState<SearchState>({...});
  
  const search = useDebouncedCallback(async (query: string) => {
    setSearchState(prev => ({ ...prev, loading: true }));
    
    const results = await api.searchPrompts({
      q: query,
      context: selectedProject,
      performance_threshold: 0.7
    });
    
    setSearchState(prev => ({
      ...prev,
      results: results.results,
      suggestions: results.semantic_suggestions,
      loading: false
    }));
  }, 300);
  
  return { searchState, search, addToTestQueue, runBatchTest };
};
```

### Database Schema Enhancement:
```javascript
// Enhanced prompt document structure
prompts/{promptId} = {
  // Existing fields...
  
  // New semantic search fields
  embedding_vector: number[], // For similarity search
  semantic_tags: string[], // AI-generated semantic tags
  usage_analytics: {
    total_executions: number,
    recent_performance: number,
    avg_response_time: number,
    last_used: timestamp,
    success_contexts: string[] // Contexts where it performed well
  },
  
  // Enhanced metadata
  evaluation_metrics: {
    langfuse_trace_ids: string[],
    performance_trend: 'improving' | 'stable' | 'declining',
    optimization_suggestions: string[]
  }
}

// New search index collection
search_index/prompts = {
  prompt_id: string,
  embedding_vector: number[],
  semantic_keywords: string[],
  performance_score: number,
  last_updated: timestamp
}
```

## 🎯 Implementation Plan

### Phase 1: Foundation (5-7 hours)
- [ ] Fix "0 prompts found" data loading issue
- [ ] Update navigation and page titles
- [ ] Implement basic semantic search API endpoint
- [ ] Set up embedding model and vector similarity

### Phase 2: Search Enhancement (6-8 hours)  
- [ ] Build natural language query processing
- [ ] Implement match reason generation
- [ ] Add performance-based filtering and ranking
- [ ] Create semantic suggestion system

### Phase 3: UI/UX Polish (4-5 hours)
- [ ] Enhance search interface with real-time results
- [ ] Improve right column evaluation workspace
- [ ] Add batch testing and comparison features
- [ ] Implement AI recommendation system

## 🧪 Testing Strategy

### Unit Tests:
- [ ] Search algorithm accuracy tests
- [ ] Embedding generation and similarity scoring
- [ ] Filter and ranking logic validation
- [ ] Performance metric integration

### Integration Tests:
- [ ] End-to-end search workflow
- [ ] Langfuse integration for performance data
- [ ] Batch testing and evaluation queue
- [ ] Real-world query scenarios

### User Acceptance Tests:
- [ ] Natural language query effectiveness
- [ ] Search result relevance and ranking
- [ ] Evaluation workflow efficiency
- [ ] Performance improvement measurement

## 📊 Success Metrics

### Immediate Success (Week 1):
- [ ] Page loads prompts successfully (no more 0 results)
- [ ] Basic semantic search returns relevant results
- [ ] Navigation updated across all pages
- [ ] Users can test prompts from search results

### Long-term Success (Month 1):
- [ ] 90%+ user satisfaction with search relevance
- [ ] 50% reduction in time to find relevant prompts
- [ ] 75% of searches use natural language queries
- [ ] 40% increase in prompt testing and optimization activity

## 🔗 Dependencies & Integration

### Required Services:
- **Langfuse API**: Performance metrics integration
- **Firestore**: Enhanced prompt data storage
- **Sentence Transformers**: Semantic embedding model
- **Flask Backend**: New search API endpoints

### External Dependencies:
- [ ] Prompt data availability (fix current loading issue)
- [ ] Langfuse trace data for performance metrics
- [ ] Embedding model setup and optimization
- [ ] Search index construction and maintenance

## 🏷️ Labels & Assignment

**Labels**: `enhancement`, `search`, `evaluation`, `ui`, `backend`, `ai-ml`, `high-priority`

**Suggested Agent Assignment**:
- **Primary**: Integration Agent (API development, search logic)
- **Secondary**: UX Agent (interface enhancement, user experience)
- **Review**: Evaluation Agent (performance integration, testing workflow)

## 📚 Reference Materials

### Design Standards:
- Follow `VISUAL_DESIGN_GUIDE.md` for consistent styling
- Reference `/prompts/add` page for layout patterns
- Maintain existing Quick Actions design pattern

### Technical References:
- Current prompt data structure in Firestore
- Existing Langfuse integration patterns
- Performance metrics API endpoints

### User Research:
- Current user workflow analysis
- Pain points with manual prompt discovery
- Evaluation workflow optimization opportunities

---

**Created**: 2025-08-02T10:45:00Z  
**Status**: Ready for Assignment  
**Next Action**: Assign to Integration Agent for technical implementation planning