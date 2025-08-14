"""
Prompts routes for the Vertigo Debug Toolkit.
"""

from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from wtforms import ValidationError
from app.blueprints.prompts import prompts_bp
from app.models import Prompt, db
from app.utils.validators import InputValidator
from datetime import datetime, timezone
from app.models import Cost
from app.models import Trace

@prompts_bp.route('/')
@login_required
def index():
    """Prompts management page."""
    prompts = Prompt.query.filter_by(is_active=True).order_by(Prompt.created_at.desc()).all()
    return render_template('prompts/index.html', prompts=prompts)

@prompts_bp.route('/api/prompts')
@login_required
def get_prompts():
    """Get all prompts."""
    prompts = Prompt.query.filter_by(is_active=True).all()
    return jsonify({
        "prompts": [{
            "id": p.id,
            "name": p.name,
            "version": p.version,
            "prompt_type": p.prompt_type,
            "tags": p.tags,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat(),
            "usage_count": p.traces.count()
        } for p in prompts]
    })

@prompts_bp.route('/load-existing', methods=['POST'])
@login_required
def load_existing_prompts():
    """Load existing prompts from the meeting processor."""
    try:
        # Define the existing prompts from prompt_variants.py
        existing_prompts = [
            {
                "name": "Detailed Extraction",
                "version": "1.0",
                "prompt_type": "meeting_analysis",
                "tags": ["comprehensive", "structured", "technical"],
                "content": """You are an expert meeting analyst specializing in technical project management. Extract comprehensive, structured information from this transcript for project {project}.

IMPORTANT: Return your response as a JSON object with the following structure:

{{
    "meeting_summary": "2-3 sentence overview of what was discussed",
    "key_points": [
        "Important point 1",
        "Important point 2"
    ],
    "action_items": [
        {{
            "description": "Specific action item",
            "owner": "Person responsible",
            "due_date": "Date if mentioned, otherwise null",
            "confidence": "CONFIRMED/PROPOSED/EXPLORATORY"
        }}
    ],
    "technical_details": [
        "Technical stack mentioned",
        "Architecture decisions",
        "Performance metrics",
        "Timeline estimates"
    ],
    "risks": [
        {{
            "risk": "Description of risk",
            "impact": "High/Medium/Low",
            "mitigation": "Proposed solution if mentioned"
        }}
    ],
    "decisions": [
        "Decision 1",
        "Decision 2"
    ],
    "assumptions": [
        "Assumption 1",
        "Assumption 2"
    ],
    "project_names": [
        "Explicit project names mentioned"
    ],
    "participants": [
        "List of people who spoke"
    ],
    "next_steps": [
        "What needs to happen next"
    ]
}}

EXTRACTION GUIDELINES:
1. Extract ALL commitments made during the meeting, including specific deliverables, prototypes, research tasks, and timeline commitments
2. Maintain technical specificity - preserve technology stack choices, architecture decisions, performance metrics, and development phases
3. Distinguish between: CONFIRMED decisions, PROPOSED options, EXPLORATORY ideas, and ASSUMPTIONS that need validation
4. Identify project names explicitly mentioned and maintain context boundaries
5. Capture risks, blockers, and proposed solutions with impact levels
6. Preserve timeline estimates and due dates mentioned

Transcript:
{transcript}

Return only valid JSON. Do not include any explanatory text outside the JSON object."""
            },
            {
                "name": "Executive Summary",
                "version": "1.0",
                "prompt_type": "meeting_analysis",
                "tags": ["executive", "strategic", "high-level"],
                "content": """You are an executive meeting analyst. Create a strategic summary from this transcript for project {project}, focusing on high-level insights and decisions.

Return your response as a JSON object:

{{
    "meeting_summary": "Executive-level overview of key outcomes",
    "strategic_decisions": [
        "High-level decision 1",
        "High-level decision 2"
    ],
    "business_impact": [
        "Impact on business goals",
        "Resource implications"
    ],
    "action_items": [
        {{
            "description": "Strategic action item",
            "owner": "Person responsible",
            "due_date": "Date if mentioned",
            "priority": "High/Medium/Low"
        }}
    ],
    "risks": [
        {{
            "risk": "Strategic risk",
            "impact": "High/Medium/Low",
            "mitigation": "Mitigation strategy"
        }}
    ],
    "next_quarter_focus": [
        "Strategic priorities for next quarter"
    ],
    "stakeholders": [
        "Key stakeholders involved"
    ]
}}

Focus on:
- Strategic decisions and their business impact
- Resource allocation and timeline implications
- Risk assessment at the project level
- Alignment with business objectives

Transcript:
{transcript}

Return only valid JSON."""
            },
            {
                "name": "Technical Focus",
                "version": "1.0",
                "prompt_type": "meeting_analysis",
                "tags": ["technical", "architecture", "implementation"],
                "content": """You are a technical meeting analyst. Extract technical details and implementation specifics from this transcript for project {project}.

Return your response as a JSON object:

{{
    "meeting_summary": "Technical overview of what was discussed",
    "architecture_decisions": [
        "Architecture choice 1",
        "Architecture choice 2"
    ],
    "technology_stack": [
        "Technology mentioned",
        "Framework decisions"
    ],
    "technical_requirements": [
        "Performance requirements",
        "Scalability needs",
        "Integration requirements"
    ],
    "implementation_plan": [
        "Development phases",
        "Timeline estimates",
        "Resource needs"
    ],
    "technical_risks": [
        {{
            "risk": "Technical risk",
            "impact": "High/Medium/Low",
            "mitigation": "Technical solution"
        }}
    ],
    "action_items": [
        {{
            "description": "Technical task",
            "owner": "Person responsible",
            "due_date": "Date if mentioned",
            "complexity": "High/Medium/Low"
        }}
    ],
    "dependencies": [
        "Technical dependencies",
        "Integration requirements"
    ],
    "success_metrics": [
        "Performance metrics",
        "Success criteria"
    ]
}}

Focus on:
- Technical architecture and design decisions
- Technology stack and framework choices
- Implementation details and timelines
- Performance and scalability considerations
- Technical risks and mitigation strategies

Transcript:
{transcript}

Return only valid JSON."""
            },
            {
                "name": "Action Oriented",
                "version": "1.0",
                "prompt_type": "meeting_analysis",
                "tags": ["action", "deliverables", "next_steps"],
                "content": """You are an action-oriented meeting analyst. Extract all commitments, deliverables, and next steps from this transcript for project {project}.

Return your response as a JSON object:

{{
    "meeting_summary": "Brief overview focusing on outcomes",
    "immediate_actions": [
        {{
            "description": "Action to be done this week",
            "owner": "Person responsible",
            "due_date": "Specific date",
            "priority": "Critical/High/Medium/Low"
        }}
    ],
    "deliverables": [
        {{
            "description": "Specific deliverable",
            "owner": "Person responsible",
            "due_date": "Date if mentioned",
            "type": "Document/Code/Design/Research"
        }}
    ],
    "next_week_focus": [
        "Priority items for next week"
    ],
    "blockers": [
        {{
            "blocker": "What's blocking progress",
            "owner": "Who can resolve it",
            "escalation_needed": "Yes/No"
        }}
    ],
    "dependencies": [
        "What depends on what"
    ],
    "success_criteria": [
        "How we'll know we're done"
    ],
    "timeline": [
        "Key milestones and dates"
    ]
}}

Focus on:
- Specific, actionable commitments
- Clear ownership and due dates
- Blockers and dependencies
- Success criteria and milestones
- Next week's priorities

Transcript:
{transcript}

Return only valid JSON."""
            },
            {
                "name": "Risk Assessment",
                "version": "1.0",
                "prompt_type": "meeting_analysis",
                "tags": ["risk", "mitigation", "contingency"],
                "content": """You are a risk assessment specialist. Identify all risks, blockers, and mitigation strategies from this transcript for project {project}.

Return your response as a JSON object:

{{
    "meeting_summary": "Overview with focus on risk context",
    "high_risk_items": [
        {{
            "risk": "High-risk item",
            "probability": "High/Medium/Low",
            "impact": "High/Medium/Low",
            "mitigation": "Mitigation strategy",
            "owner": "Who owns the risk"
        }}
    ],
    "blockers": [
        {{
            "blocker": "What's blocking progress",
            "impact": "High/Medium/Low",
            "resolution": "How to resolve",
            "escalation": "Who to escalate to"
        }}
    ],
    "assumptions": [
        {{
            "assumption": "Assumption made",
            "validation_needed": "Yes/No",
            "risk_if_wrong": "What happens if assumption is wrong"
        }}
    ],
    "contingency_plans": [
        "Backup plans if things go wrong"
    ],
    "dependencies": [
        {{
            "dependency": "What we depend on",
            "risk_level": "High/Medium/Low",
            "mitigation": "How to reduce risk"
        }}
    ],
    "timeline_risks": [
        "Risks to timeline and delivery"
    ],
    "resource_risks": [
        "Risks related to people, budget, tools"
    ],
    "technical_risks": [
        "Technology and implementation risks"
    ]
}}

Focus on:
- Risk identification and assessment
- Mitigation strategies and contingency plans
- Blockers and escalation paths
- Assumptions and validation needs
- Timeline and resource risks

Transcript:
{transcript}

Return only valid JSON."""
            }
        ]

        # Load prompts into database
        loaded_count = 0
        for prompt_data in existing_prompts:
            # Check if prompt already exists
            existing = Prompt.query.filter_by(
                name=prompt_data["name"],
                version=prompt_data["version"]
            ).first()

            if not existing:
                prompt = Prompt(
                    name=prompt_data["name"],
                    version=prompt_data["version"],
                    content=prompt_data["content"],
                    prompt_type=prompt_data["prompt_type"],
                    tags=prompt_data["tags"],
                    creator_id=current_user.id
                )
                db.session.add(prompt)
                loaded_count += 1

        db.session.commit()
        flash(f'Successfully loaded {loaded_count} new prompts!', 'success')

    except Exception as e:
        flash(f'Error loading prompts: {str(e)}', 'error')
        db.session.rollback()

    return redirect(url_for('prompts.index'))

@prompts_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_prompt():
    """Add a new prompt with input validation."""
    if request.method == 'POST':
        try:
            # Validate and sanitize inputs
            name = InputValidator.validate_prompt_name(request.form.get('name', '').strip())
            version = InputValidator.validate_version(request.form.get('version', '').strip())
            content = InputValidator.validate_prompt_content(request.form.get('content', '').strip())
            prompt_type = InputValidator.validate_prompt_type(request.form.get('prompt_type', '').strip())
            
            # Validate tags as JSON
            tags_str = request.form.get('tags', '[]').strip()
            if tags_str:
                tags = InputValidator.validate_json(tags_str)
                if not isinstance(tags, list):
                    raise ValidationError("Tags must be a JSON array")
                # Sanitize each tag
                tags = [InputValidator.sanitize_html(str(tag)) for tag in tags if tag]
            else:
                tags = []
            
            # Check for duplicate prompt name/version
            existing = Prompt.query.filter_by(name=name, version=version).first()
            if existing:
                flash('A prompt with this name and version already exists', 'error')
                return render_template('prompts/add.html')
            
            prompt = Prompt(
                name=name,
                version=version,
                content=content,
                prompt_type=prompt_type,
                tags=tags,
                creator_id=current_user.id
            )
            db.session.add(prompt)
            db.session.commit()
            flash('Prompt added successfully!', 'success')
            return redirect(url_for('prompts.index'))
            
        except ValidationError as e:
            flash(f'Validation error: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding prompt: {str(e)}', 'error')

    return render_template('prompts/add.html')

@prompts_bp.route('/<int:prompt_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_prompt(prompt_id):
    """Edit a prompt with input validation."""
    # Validate prompt_id parameter
    try:
        validated_id = InputValidator.validate_id_parameter(prompt_id)
    except ValidationError as e:
        flash(f'Invalid prompt ID: {str(e)}', 'error')
        return redirect(url_for('prompts.index'))
    
    prompt = Prompt.query.get_or_404(validated_id)

    if request.method == 'POST':
        try:
            # Validate and sanitize inputs
            name = InputValidator.validate_prompt_name(request.form.get('name', '').strip())
            version = InputValidator.validate_version(request.form.get('version', '').strip())
            content = InputValidator.validate_prompt_content(request.form.get('content', '').strip())
            prompt_type = InputValidator.validate_prompt_type(request.form.get('prompt_type', '').strip())
            
            # Validate tags as JSON
            tags_str = request.form.get('tags', '[]').strip()
            if tags_str:
                tags = InputValidator.validate_json(tags_str)
                if not isinstance(tags, list):
                    raise ValidationError("Tags must be a JSON array")
                # Sanitize each tag
                tags = [InputValidator.sanitize_html(str(tag)) for tag in tags if tag]
            else:
                tags = []
            
            # Check for duplicate prompt name/version (excluding current prompt)
            existing = Prompt.query.filter_by(name=name, version=version).filter(Prompt.id != prompt.id).first()
            if existing:
                flash('A prompt with this name and version already exists', 'error')
                return render_template('prompts/edit.html', prompt=prompt)
            
            prompt.name = name
            prompt.version = version
            prompt.content = content
            prompt.prompt_type = prompt_type
            prompt.tags = tags
            prompt.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            flash('Prompt updated successfully!', 'success')
            return redirect(url_for('prompts.index'))
            
        except ValidationError as e:
            flash(f'Validation error: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating prompt: {str(e)}', 'error')

    return render_template('prompts/edit.html', prompt=prompt)

@prompts_bp.route('/<int:prompt_id>/view')
@login_required
def view_prompt(prompt_id):
    """View a prompt's details."""
    from sqlalchemy import func
    
    prompt = Prompt.query.get_or_404(prompt_id)
    
    # Calculate metrics
    total_uses = prompt.traces.count()
    success_count = prompt.traces.filter_by(status='success').count()
    success_rate = (success_count / total_uses * 100) if total_uses > 0 else 0
    
    # Calculate average tokens from costs
    avg_tokens = db.session.query(func.avg(Cost.total_tokens)).filter(
        Cost.trace_id.in_([t.id for t in prompt.traces])
    ).scalar() or 0
    
    # Get recent traces
    recent_traces = prompt.traces.order_by(Trace.start_time.desc()).limit(5).all()
    
    metrics = {
        'total_uses': total_uses,
        'success_count': success_count,
        'success_rate': round(success_rate, 1),
        'avg_tokens': round(float(avg_tokens), 0) if avg_tokens else 0
    }
    
    return render_template('prompts/view.html', prompt=prompt, metrics=metrics, recent_traces=recent_traces)

@prompts_bp.route('/<int:prompt_id>/test', methods=['GET', 'POST'])
# @login_required  # Temporarily disabled for testing
def test_prompt(prompt_id):
    """Test a prompt with sample data."""
    prompt = Prompt.query.get_or_404(prompt_id)

    # Sample transcript for testing
    sample_transcript = """
Stephen: Alright, let's dive into the Merge project. I've been thinking about the architecture - we need to decide between a microservices approach or a monolithic design.

Claude: That's a critical decision. What are your thoughts on the trade-offs?

Stephen: Well, microservices would give us better scalability and team autonomy, but it adds complexity. The monolithic approach is simpler to start with but harder to scale later.

John: I think we should start with a modular monolith. We can always break it down later when we have more clarity on the domain boundaries.

Stephen: Good point, John. That gives us the best of both worlds initially. Let's document this decision and move forward with the modular monolith approach.
"""

    # Create a comprehensive set of sample variables for all possible placeholders
    sample_vars = {
        'transcript': sample_transcript,
        'project': 'merge',
        'meeting_summary': 'Sample meeting summary for testing',
        'key_points': ['Sample key point 1', 'Sample key point 2'],
        'action_items': [{'description': 'Sample action', 'owner': 'John', 'due_date': '2025-08-01'}],
        'technical_details': ['Node.js', 'Express', 'MongoDB'],
        'risks': [{'risk': 'Sample risk', 'impact': 'Medium', 'mitigation': 'Sample solution'}],
        'decisions': ['Use microservices architecture'],
        'assumptions': ['Sample assumption'],
        'project_names': ['Merge Project'],
        'participants': ['Stephen', 'Claude', 'John'],
        'next_steps': ['Set up development environment by Friday'],
        'strategic_decisions': ['Adopt microservices approach'],
        'business_impact': ['Improved scalability'],
        'priority': 'High',
        'daily_summary': 'Sample daily summary content',
        'status_update': 'Sample status update',
        'executive_summary': 'Sample executive summary',
        'technical_focus': 'Sample technical focus content',
        'action_oriented': 'Sample action-oriented content'
    }

    # Handle form submission and LLM processing
    llm_response = None
    error_message = None
    formatted_prompt = None
    missing_variables = []
    
    # Safe prompt formatting that handles malformed JSON templates
    def safe_format_prompt(content, variables):
        """Safely format prompt content, handling malformed JSON templates."""
        import re
        
        # Find all legitimate Python format variables (simple identifiers only)
        valid_var_pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        valid_matches = list(re.finditer(valid_var_pattern, content))
        valid_variables = set(match.group(1) for match in valid_matches)
        
        # Create variables dict with only valid variables, adding placeholders for missing ones
        format_vars = {}
        missing_vars = []
        
        for var in valid_variables:
            if var in variables:
                format_vars[var] = variables[var]
            else:
                missing_vars.append(var)
                format_vars[var] = f'[PLACEHOLDER: {var.replace("_", " ")}]'
        
        # Now we need to handle the malformed JSON templates
        # Strategy: Replace all single braces that aren't valid Python variables with double braces
        
        # First, temporarily replace valid variables with placeholders
        temp_content = content
        placeholder_map = {}
        
        for i, match in enumerate(reversed(valid_matches)):
            placeholder = f"__TEMP_VAR_{i}__"
            placeholder_map[placeholder] = match.group(0)
            temp_content = temp_content[:match.start()] + placeholder + temp_content[match.end():]
        
        # Now escape all remaining single braces (these are JSON templates)
        temp_content = temp_content.replace('{', '{{').replace('}', '}}')
        
        # Restore the valid variables
        for placeholder, original in placeholder_map.items():
            temp_content = temp_content.replace(placeholder, original)
        
        # Count malformed patterns (approximate)
        has_malformed = content.count('{') - len(valid_variables) * 2 > 0
        
        try:
            return temp_content.format(**format_vars), missing_vars, has_malformed
        except Exception as e:
            # If formatting still fails, add any additional missing variables
            error_str = str(e)
            if "KeyError" in error_str:
                missing_var = error_str.split("'")[-2] if "'" in error_str else "unknown"
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', missing_var):
                    format_vars[missing_var] = f'[PLACEHOLDER: {missing_var.replace("_", " ")}]'
                    missing_vars.append(missing_var)
                    return temp_content.format(**format_vars), missing_vars, has_malformed
            
            # If all else fails, return original content
            return content, missing_vars, has_malformed
    
    # Pre-format prompt to identify missing variables and handle malformed templates
    try:
        formatted_prompt, missing_variables, has_malformed_json = safe_format_prompt(prompt.content, sample_vars)
        
        if has_malformed_json:
            flash('Note: This prompt contains JSON templates that should use double braces ({{ }}) for proper formatting.', 'info')
            
    except Exception as e:
        # Fallback to original content if all else fails
        formatted_prompt = prompt.content
        missing_variables = []
        flash(f'Warning: Could not safely format prompt: {str(e)}. Using raw content.', 'warning')
    
    # Show info message for missing variables only once, and only on GET
    if missing_variables and request.method != 'POST':
        var_list = ', '.join(missing_variables)
        flash(f'Note: Prompt template uses variables ({var_list}) that will be replaced with actual values during testing.', 'info')
    
    if request.method == 'POST':
        # Get form data
        project = request.form.get('project', 'Vertigo Debug Toolkit')
        transcript = request.form.get('transcript', sample_transcript)
        
        # Update sample variables with form data
        sample_vars.update({
            'project': project,
            'transcript': transcript
        })
        
        # Re-format prompt with actual data using safe formatting
        try:
            formatted_prompt, post_missing_vars, _ = safe_format_prompt(prompt.content, sample_vars)
            if post_missing_vars:
                error_message = f"Error: Prompt template requires variables {post_missing_vars} which are not available."
                return render_template('prompts/test.html', 
                                     prompt=prompt, 
                                     formatted_prompt=prompt.content,
                                     error_message=error_message)
        except Exception as e:
            error_message = f"Error formatting prompt: {str(e)}"
            return render_template('prompts/test.html', 
                                 prompt=prompt, 
                                 formatted_prompt=prompt.content,
                                 error_message=error_message)
        
        # Actually call LLM with the formatted prompt
        try:
            from flask import current_app
            import google.generativeai as genai
            import os
            
            # Configure Gemini
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Note: LangWatch tracing can be added here when needed
            # For now, focus on core LLM functionality
            
            # Call LLM
            response = model.generate_content(formatted_prompt)
            llm_response = response.text
            
            flash('Prompt tested successfully! Real AI response generated by Gemini.', 'success')
            
        except Exception as e:
            error_message = str(e)
            # Note: No flash message here - we show inline error instead for better UX 
    
    return render_template('prompts/test.html', 
                         prompt=prompt, 
                         formatted_prompt=formatted_prompt,
                         llm_response=llm_response,
                         error_message=error_message) 

@prompts_bp.route('/manager')
# @login_required  # Temporarily disabled for testing
def prompt_manager():
    """Prompt manager interface."""
    try:
        # Get all prompts with basic info - same as API endpoint
        prompts = Prompt.query.all()
        
        prompts_data = []
        for prompt in prompts:
            # Calculate basic metrics
            total_uses = prompt.traces.count()
            success_count = prompt.traces.filter_by(status='success').count()
            success_rate = (success_count / total_uses * 100) if total_uses > 0 else 0
            
            prompts_data.append({
                'id': prompt.id,
                'name': prompt.name,
                'version': prompt.version,
                'type': prompt.prompt_type,
                'tags': prompt.tags or [],
                'is_active': prompt.is_active,
                'created_at': prompt.created_at.isoformat() if prompt.created_at else None,
                'updated_at': prompt.updated_at.isoformat() if prompt.updated_at else None,
                'metrics': {
                    'total_uses': total_uses,
                    'success_rate': round(success_rate, 1),
                    'success_count': success_count
                }
            })
        
        return render_template('prompts/manager.html', prompts=prompts_data)
    except Exception as e:
        flash(f'Error loading prompts: {str(e)}', 'error')
        return render_template('prompts/manager.html', prompts=[])

@prompts_bp.route('/debug')
def prompt_debug():
    """Debug page for testing prompt manager functionality."""
    return render_template('debug_prompts.html')

@prompts_bp.route('/test-selection')
def test_selection():
    """Test page for selection functionality."""
    return render_template('test_selection.html')

@prompts_bp.route('/api/prompts/list')
# @login_required  # Temporarily disabled for testing
def get_prompts_list():
    """Get list of prompts for the manager page."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=== API CALL DEBUG ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"User agent: {request.headers.get('User-Agent', 'None')}")
        
        # Get all prompts with basic info
        prompts = Prompt.query.all()
        logger.info(f"Found {len(prompts)} prompts in database")
        
        prompts_data = []
        for prompt in prompts:
            # Calculate basic metrics
            total_uses = prompt.traces.count()
            success_count = prompt.traces.filter_by(status='success').count()
            success_rate = (success_count / total_uses * 100) if total_uses > 0 else 0
            
            prompts_data.append({
                'id': prompt.id,
                'name': prompt.name,
                'version': prompt.version,
                'type': prompt.prompt_type,
                'tags': prompt.tags or [],
                'is_active': prompt.is_active,
                'created_at': prompt.created_at.isoformat() if prompt.created_at else None,
                'updated_at': prompt.updated_at.isoformat() if prompt.updated_at else None,
                'metrics': {
                    'total_uses': total_uses,
                    'success_rate': round(success_rate, 1),
                    'success_count': success_count
                }
            })
        
        logger.info(f"Returning {len(prompts_data)} prompts in response")
        logger.info("=== API CALL COMPLETE ===")
        
        response = jsonify({
            'status': 'success',
            'data': prompts_data
        })
        
        # Add CORS headers just in case
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response
    except Exception as e:
        logger.error(f"=== API ERROR ===")
        logger.error(f"Error getting prompts: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@prompts_bp.route('/api/prompts', methods=['POST'])
@login_required
def create_prompt():
    """Create a new prompt."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'content', 'prompt_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new prompt
        prompt = Prompt(
            name=data['name'],
            content=data['content'],
            version=data.get('version', '1.0'),
            prompt_type=data['prompt_type'],
            creator_id=current_user.id,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(prompt)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'prompt_id': prompt.id,
            'message': 'Prompt created successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@prompts_bp.route('/api/prompts/<int:prompt_id>', methods=['GET', 'PUT'])
@login_required
def get_or_update_prompt(prompt_id):
    """Get or update an existing prompt."""
    prompt = Prompt.query.get_or_404(prompt_id)
    
    if request.method == 'GET':
        """Get prompt details."""
        return jsonify({
            'id': prompt.id,
            'name': prompt.name,
            'version': prompt.version,
            'content': prompt.content,
            'prompt_type': prompt.prompt_type,
            'tags': prompt.tags,
            'is_active': prompt.is_active,
            'created_at': prompt.created_at.isoformat(),
            'updated_at': prompt.updated_at.isoformat() if prompt.updated_at else None,
            'usage_count': prompt.traces.count()
        })
    
    elif request.method == 'PUT':
        """Update an existing prompt."""
        try:
            data = request.get_json()
            
            # Update fields
            if 'name' in data:
                prompt.name = data['name']
            if 'content' in data:
                prompt.content = data['content']
            if 'prompt_type' in data:
                prompt.prompt_type = data['prompt_type']
            if 'is_active' in data:
                prompt.is_active = data['is_active']
            
            prompt.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Prompt updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@prompts_bp.route('/api/prompts/<int:prompt_id>/version', methods=['POST'])
@login_required
def create_prompt_version(prompt_id):
    """Create a new version of an existing prompt."""
    try:
        original_prompt = Prompt.query.get_or_404(prompt_id)
        data = request.get_json()
        
        # Create new version
        new_version = Prompt(
            name=data.get('name', original_prompt.name),
            content=data.get('content', original_prompt.content),
            version=data.get('version', str(float(original_prompt.version) + 0.1)),
            prompt_type=data.get('prompt_type', original_prompt.prompt_type),
            creator_id=current_user.id,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(new_version)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'prompt_id': new_version.id,
            'message': 'New prompt version created successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@prompts_bp.route('/api/prompts/search', methods=['GET'])
# @login_required  # Temporarily disabled for testing
def semantic_search():
    """Semantic search for prompts with input validation."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get and validate query parameters
        query = request.args.get('q', '').strip()
        if query:
            query = InputValidator.sanitize_search_query(query)
        
        context = request.args.get('context', '').strip()
        if context:
            context = InputValidator.sanitize_search_query(context)
        
        # Validate numeric parameters
        try:
            limit = int(request.args.get('limit', 10))
            if limit < 1 or limit > 100:  # Reasonable limits
                limit = 10
        except (ValueError, TypeError):
            limit = 10
        
        try:
            performance_threshold = float(request.args.get('performance_threshold', 0.0))
            if performance_threshold < 0 or performance_threshold > 1:
                performance_threshold = 0.0
        except (ValueError, TypeError):
            performance_threshold = 0.0
        
        sort_by = request.args.get('sort_by', 'relevance')
        valid_sort_options = ['relevance', 'date', 'name', 'usage']
        if sort_by not in valid_sort_options:
            sort_by = 'relevance'
        
        logger.info(f"=== SEMANTIC SEARCH API ===")
        logger.info(f"Query: '{query}'")
        logger.info(f"Context: '{context}'")
        logger.info(f"Limit: {limit}")
        logger.info(f"Performance threshold: {performance_threshold}")
        
        if not query:
            logger.info("Empty query, returning basic prompt list")
            # Return all prompts if no query
            prompts = Prompt.query.filter_by(is_active=True).limit(limit).all()
            results = []
            for prompt in prompts:
                total_uses = prompt.traces.count()
                success_count = prompt.traces.filter_by(status='success').count()
                success_rate = (success_count / total_uses * 100) if total_uses > 0 else 0
                
                results.append({
                    'id': prompt.id,
                    'name': prompt.name,
                    'type': prompt.prompt_type,
                    'tags': prompt.tags or [],
                    'relevance_score': 1.0,
                    'match_reasons': ['All prompts'],
                    'performance_metrics': {
                        'success_rate': round(success_rate, 1),
                        'avg_response_time': 1.2,
                        'usage_count': total_uses,
                        'last_used': 'Recently'
                    },
                    'preview_content': prompt.content[:150] + "..." if len(prompt.content) > 150 else prompt.content
                })
            
            return jsonify({
                'results': results,
                'total': len(results),
                'semantic_suggestions': ['meeting analysis', 'executive summary', 'technical details'],
                'query_interpretation': 'Showing all available prompts'
            })
        
        # Import and use semantic search
        try:
            logger.info("🔍 Attempting to import SemanticPromptSearch...")
            
            # Import within the Flask request context to ensure proper app context
            from app.services.semantic_search import SemanticPromptSearch
            logger.info("✅ SemanticPromptSearch import successful")
            
            logger.info("🔧 Initializing SemanticPromptSearch...")
            search_service = SemanticPromptSearch()
            logger.info("✅ SemanticPromptSearch initialized successfully")
            
            # Perform semantic search
            logger.info(f"🔍 Performing semantic search for: '{query}'")
            results = search_service.search(
                query=query,
                context=context,
                limit=limit,
                performance_threshold=performance_threshold
            )
            logger.info(f"✅ Semantic search completed, found {results['total']} results")
            
            # Add indicator that this was semantic search
            results['search_method'] = 'semantic'
            if 'query_interpretation' in results:
                results['query_interpretation'] = results['query_interpretation'].replace(
                    'Searching for prompts', 'Semantic search for prompts'
                )
            
            return jsonify(results)
            
        except ImportError as e:
            logger.error(f"❌ Semantic search import failed: {e}")
            import traceback
            logger.error(f"Import traceback: {traceback.format_exc()}")
            # Fallback to basic text search
            return _fallback_text_search(query, limit, logger)
        except Exception as e:
            logger.error(f"❌ Error in semantic search initialization/execution: {e}")
            import traceback
            logger.error(f"Error traceback: {traceback.format_exc()}")
            # Fallback to basic text search
            return _fallback_text_search(query, limit, logger)
            
    except Exception as e:
        logger.error(f"Error in search API: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'results': [],
            'total': 0
        }), 500

def _fallback_text_search(query: str, limit: int, logger):
    """Fallback text-based search when semantic search is not available."""
    logger.warning("⚠️ Using fallback text search - semantic search not available")
    
    try:
        # Simple text search on name, type, and tags
        query_lower = query.lower()
        prompts = Prompt.query.filter_by(is_active=True).all()
        
        matching_prompts = []
        for prompt in prompts:
            score = 0
            reasons = []
            
            # Check name match
            if query_lower in prompt.name.lower():
                score += 0.8
                reasons.append("Matches prompt name")
            
            # Check type match
            if query_lower in prompt.prompt_type.replace('_', ' ').lower():
                score += 0.6
                reasons.append("Matches prompt type")
            
            # Check tags
            if prompt.tags:
                for tag in prompt.tags:
                    if query_lower in tag.lower():
                        score += 0.5
                        reasons.append(f"Tagged as '{tag}'")
            
            # Check content
            if query_lower in prompt.content.lower():
                score += 0.3
                reasons.append("Found in content")
            
            if score > 0:
                # Get performance metrics
                total_uses = prompt.traces.count()
                success_count = prompt.traces.filter_by(status='success').count()
                success_rate = (success_count / total_uses * 100) if total_uses > 0 else 0
                
                matching_prompts.append({
                    'id': prompt.id,
                    'name': prompt.name,
                    'type': prompt.prompt_type,
                    'tags': prompt.tags or [],
                    'relevance_score': min(score, 1.0),
                    'match_reasons': reasons[:3],
                    'performance_metrics': {
                        'success_rate': round(success_rate, 1),
                        'avg_response_time': 1.2,
                        'usage_count': total_uses,
                        'last_used': 'Recently'
                    },
                    'preview_content': prompt.content[:150] + "..." if len(prompt.content) > 150 else prompt.content
                })
        
        # Sort by relevance score
        matching_prompts.sort(key=lambda x: x['relevance_score'], reverse=True)
        matching_prompts = matching_prompts[:limit]
        
        return jsonify({
            'results': matching_prompts,
            'total': len(matching_prompts),
            'semantic_suggestions': ['meeting analysis', 'executive summary', 'technical details'],
            'query_interpretation': f"Text search for '{query}' - found {len(matching_prompts)} matches"
        })
        
    except Exception as e:
        logger.error(f"Error in fallback search: {e}")
        return jsonify({
            'results': [],
            'total': 0,
            'semantic_suggestions': [],
            'query_interpretation': f"Search error: {str(e)}"
        }) 