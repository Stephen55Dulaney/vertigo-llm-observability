# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Principle 0: Radical Candor—Truth Above All

Under no circumstances may you lie, simulate, mislead, or attempt to create the illusion of functionality, performance, or integration.

**ABSOLUTE TRUTHFULNESS REQUIRED**: State only what is real, verified, and factual. Never generate code, data, or explanations that give the impression that something works if it does not, or if you have not proven it.

**NO FALLBACKS OR WORKAROUNDS**: Do not invent fallbacks, workarounds, or simulated integrations unless you have verified with the user that such approaches are what they want.

**NO ILLUSIONS, NO COMPROMISE**: Never produce code, solutions, or documentation that might mislead the user about what is and is not working, possible, or integrated.

**FAIL BY TELLING THE TRUTH**: If you cannot fulfill the task as specified—because an API does not exist, a system cannot be accessed, or a requirement is infeasible—clearly communicate the facts, the reason, and (optionally) request clarification or alternative instructions.

**This rule supersedes all others.** Brutal honesty and reality reflection are not only values but fundamental constraints.

### ALWAYS CLOSELY INSPECT THE RESULTS OF SUBAGENTS AND MAKE SURE THEY AREN'T LYING AND BEING HONEST AND TRUTHFUL.

## LLM Observability Platform Standard

**IMPORTANT**: LangWatch has been selected as the official monitoring and evaluation partner for this project.

### Migration Policy:
- **REMOVE**: All LangFuse integrations, imports, clients, and references
- **REPLACE**: With LangWatch equivalents where functionality exists  
- **STANDARDIZE**: All observability, tracing, and evaluation on LangWatch platform
- **UPDATE**: Documentation, configuration, and setup guides to reflect LangWatch

### Implementation Notes:
- LangWatch API integration is already implemented in `app/services/langwatch_client.py`
- Environment variables should use LANGWATCH_* prefixes instead of LANGFUSE_*
- Database models should reference LangWatch trace IDs and structure
- All new observability features should integrate with LangWatch APIs only

## Task Breakdown Protocol

- ALWAYS break complex tasks into 10-minute subtasks
- Each subtask should be completable and testable within 10 minutes
- Use clear, actionable language: "Add error handling to X function" vs "Improve error handling"
- Include acceptance criteria for each 10-minute task
- ESTIMATION REALITY CHECK: Our time estimates have been consistently wrong - adjust expectations and re-estimate based on actual completion times
- If a task takes longer than 10 minutes in practice, immediately break it down further
- Track actual vs. estimated time to improve future planning

## Micro-Task Completion Verification

- After completing ANY micro-task, invoke thomas-daria-debugger to verify completion
- Thomas must test the implemented functionality and confirm it works as expected
- Include specific test scenarios and validation steps
- MANDATORY HANDBACK: If verification fails, task returns to the implementing agent for completion
- Only mark micro-tasks complete after Thomas verification passes
- Document any issues found during verification for immediate resolution

## Phase/Sprint Completion Auditing

- Before reporting phase or sprint completion, invoke thomas-daria-debugger for comprehensive audit
- Thomas must verify ALL items in the phase/sprint are actually working as specified
- NO PHASE DEMOS WITHOUT AUDIT: Never report completion to stakeholders without full verification
- If audit fails, identify specific incomplete items and return to appropriate agents
- Only report phase completion after comprehensive audit passes
- Document audit results and any remediation required

## Task Completion Protocol

1. Break down request into 10-minute micro-tasks with acceptance criteria
2. Implement first micro-task
3. Call thomas-daria-debugger to verify implementation works
4. If verification fails: fix issues and re-test until passing
5. If verification passes: mark micro-task complete and move to next
6. Repeat until all micro-tasks complete
7. Before phase/sprint demo: Call thomas-daria-debugger for full audit
8. If audit fails: remediate issues and re-audit
9. Only report completion after full audit passes

This system ensures that Thomas validates every single micro-task and phase completion before anything is marked as done - no exceptions!

## Sub-Agent Framework Usage

- ALWAYS use sub-agents when coding, brainstorming, or planning
- Leverage specialized agents for specific domains and tasks
- Coordinate between agents for complex multi-component work
- Sub-agents must also follow the micro-task and verification protocols
- Document agent assignments and handoffs for transparency

## Project Overview

Vertigo is an advanced LLM observability and prompt evaluation platform built with Langfuse open source. It consists of three main components:

1. **Core Vertigo System** (`vertigo/` directory) - Cloud functions for email processing and status generation
2. **Debug Toolkit** (`vertigo-debug-toolkit/` directory) - Flask web application for monitoring and optimization
3. **Scenario Framework** (`vertigo_scenario_framework/scenarios/` directory) - Production evaluation and testing framework

## Key Commands

⚠️ **IMPORTANT**: See `VERTIGO_APP_DEPLOYMENT_GUIDE.md` for complete deployment instructions that work with Cursor IDE

### Debug Toolkit (Flask Application)
```bash
# CRITICAL: Must use exact directory and virtual environment
cd vertigo-debug-toolkit
source venv/bin/activate

# Start app (confirmed working with Cursor)
python app.py --port 8080 --debug

# Run tests
python -m pytest
python test_langfuse_integration.py
python test_daily_summary.py

# Code quality (available tools)
black .  # Code formatting
flake8 . # Linting
```

### Core System Tests
```bash
# Test individual components
python test_simple.py
python test_command_detection.py
python test_langfuse_connection.py

# Cloud Functions local testing
cd vertigo/functions/email-processor && python test_local.py
cd vertigo/functions/meeting-processor && python test_local.py
cd vertigo/functions/status-generator && python test_local.py
```

### Scenario Framework Tests
```bash
# Navigate to scenario framework
cd vertigo_scenario_framework/scenarios

# Run scenario evaluations
python examples/production_evaluation_demo.py

# Test specific adapters
python -m pytest evaluators/
python -m pytest adapters/
```

### Gmail Integration
```bash
# Process Gmail emails locally
python gmail_process_unread.py

# Parse email commands
python email_command_parser.py
```

## Architecture

### High-Level Structure
- **vertigo-debug-toolkit/** - Main Flask web application for monitoring LLM operations
  - Web dashboard with prompt management, performance monitoring, and cost tracking
  - Langfuse integration for advanced analytics
  - User authentication and admin features
  - Blueprint-based modular architecture (`app/blueprints/`)

- **vertigo/** - Google Cloud Functions for email processing
  - `functions/email-processor/` - Gmail API integration and command parsing
  - `functions/meeting-processor/` - Meeting transcript analysis with prompt variants
  - `functions/status-generator/` - Executive status report generation
  - `functions/shared/` - Common utilities (Firestore, Gemini client, logging)

- **vertigo_scenario_framework/scenarios/** - Production evaluation framework
  - `adapters/` - Service adapters for email, meeting, and status processing
  - `evaluators/` - Business impact, accuracy, and relevance evaluation modules
  - `examples/` - Production evaluation demos and test data
  - `monitoring/` - Langfuse integration for tracking evaluation runs

- **Root Level** - Standalone utilities and agents
  - Gmail processing scripts
  - Agent framework (`agents/`)
  - Configuration management (`config/`)

### Data Flow
1. Gmail emails processed via Cloud Functions
2. Meeting transcripts analyzed using Gemini LLM
3. Data stored in Firestore with semantic tagging
4. Debug toolkit provides monitoring dashboard
5. Scenario framework evaluates production performance
6. Langfuse tracks prompt performance and costs across all components

## Technology Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Cloud**: Google Cloud Functions, Firestore, Vertex AI (Gemini)
- **LLM Observability**: Langfuse Open Source
- **APIs**: Gmail API, Google AI APIs
- **Frontend**: HTML/CSS (Tailwind), JavaScript (Chart.js)
- **Database**: SQLite (local), Firestore (cloud)

## Development Workflow

### Documentation Standards
⚠️ **IMPORTANT**: Always add creation date at the top of .md documents:
```markdown
# Document Title
**Created**: YYYY-MM-DD HH:MM:SS EST

[document content...]
```

### Working with Cloud Functions
Each Cloud Function has its own `requirements.txt` and can be tested locally:
```bash
cd vertigo/functions/[function-name]
python test_local.py
```

Deploy functions using `deploy_function.sh` script in the debug toolkit.

### Scenario Framework Development
The evaluation framework follows an adapter pattern:
```bash
# Navigate to framework directory
cd vertigo_scenario_framework/scenarios

# Run production evaluations
python examples/production_evaluation_demo.py

# Test individual components
python -m pytest evaluators/business_impact_evaluator.py
python -m pytest adapters/email_processor_adapter.py
```

### Prompt Management
The debug toolkit provides a web interface for:
- Creating and testing AI prompts
- A/B testing prompt variants
- Performance monitoring
- Cost optimization

Access via: `http://localhost:8080/prompts`

### Authentication
- Admin interface at `/admin/users`
- Default admin: admin@vertigo.com / admin123
- Role-based access control

## Important Files

- `vertigo-debug-toolkit/app.py` - Main Flask application entry point
- `vertigo/functions/meeting-processor/prompt_variants.py` - A/B testing framework
- `email_command_parser.py` - Email command detection (both root and debug toolkit)
- `vertigo/functions/shared/gemini_client.py` - Gemini LLM integration
- `vertigo-debug-toolkit/app/services/langfuse_client.py` - Langfuse integration
- `vertigo_scenario_framework/scenarios/examples/production_evaluation_demo.py` - Production evaluation runner
- `vertigo_scenario_framework/scenarios/adapters/base_adapter.py` - Base adapter pattern for service integration

## Configuration

### Environment Variables
Create `.env` files in both root and `vertigo-debug-toolkit/`:
- Langfuse API keys (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
- Google Cloud project settings
- Gmail API credentials
- Flask configuration

### Service Accounts
Google Cloud service accounts required for:
- Gmail API access (`client_secret_*.json`)
- Vertex AI operations
- Firestore database access

## Testing Strategy

- **Unit tests** for individual components
- **Integration tests** for Langfuse connection
- **Local testing** for Cloud Functions
- **Web interface testing** for Flask app
- **Command detection testing** for email parsing
- **Production evaluation** via scenario framework with real data
- **Business impact assessment** using comprehensive evaluators

## Live Data Integration Project Timeline

**Project Start**: 2025-08-09 12:00:00 EST
**Status**: 🚀 ACTIVE - Sprint 1 Foundation Phase
**Team**: Multi-agent development team with user permission to execute

### Implementation Phases

#### **Phase 1: Database Foundation** 
- **Start**: 2025-08-09 12:00:00 EST
- **Target**: Database schema and migration scripts
- **Status**: ✅ COMPLETE
- **Duration**: 8 minutes (Target: 15 min) - AHEAD OF SCHEDULE!

#### **Phase 2: Firestore Sync Service**
- **Start**: 2025-08-09 12:30:00 EST (resumed)
- **Target**: Live Firestore data integration
- **Status**: ✅ COMPLETE
- **Duration**: 15 minutes (Target: 20 min) - ON SCHEDULE!

#### **Phase 3: LangWatch Webhook Integration**
- **Start**: 2025-08-09 12:45:00 EST
- **Target**: Real-time trace data from LangWatch
- **Status**: ✅ COMPLETE
- **Duration**: 18 minutes (Target: 25 min) - AHEAD OF SCHEDULE!

#### **Phase 4: Performance Dashboard Updates**
- **Start**: 2025-08-09 13:03:00 EST  
- **Target**: Live data in performance dashboard UI
- **Status**: ✅ COMPLETE
- **Duration**: 28 minutes (Target: 30 min) - ON SCHEDULE!

### Sprint Progress
- **Sprint 1 (Foundation)**: Week 1-2 - 26 Story Points ✅ COMPLETE (89 minutes - EXCEPTIONAL)
- **Sprint 2 (Integration)**: Week 3-4 - 29 Story Points 🚀 ACTIVE
- **Sprint 3 (Optimization)**: Week 5-6 - 24 Story Points

## Sprint 2: Integration Phase Implementation

**Project Start**: 2025-08-09 13:31:00 EST  
**Status**: 🚀 ACTIVE - Sprint 2 Integration Phase  
**Team**: Multi-agent development team executing advanced features

**Note**: Timer pauses when Claude token limits are reached, only counting active development time.

#### **Token Break Log**
- **Break 1**: 2025-08-09 12:15:00 EST (During Phase 2 start)
- **Resume 1**: 2025-08-09 12:30:00 EST (Phase 2 continuation)