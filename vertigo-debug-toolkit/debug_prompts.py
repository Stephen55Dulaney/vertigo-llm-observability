#\!/usr/bin/env python3
"""
Debug script to test JavaScript rendering for prompts.
"""

from app import create_app, db
from app.models import Prompt
from flask import render_template_string

app = create_app()

test_template = """
{% for prompt in prompts %}
<button onclick="createABTestForPrompt({{ prompt.id }}, {{ prompt.name|tojson }})" 
        class="btn btn-outline-success btn-sm">
    {{ prompt.name }}
</button>
{% endfor %}
"""

with app.app_context():
    prompts = Prompt.query.all()
    
    print("=== Testing JavaScript Rendering ===")
    for prompt in prompts:
        try:
            # Test individual prompt rendering
            rendered = render_template_string(
                '<button onclick="createABTestForPrompt({{ prompt.id }}, {{ prompt.name|tojson }})">Test</button>',
                prompt=prompt
            )
            print(f"✅ Prompt {prompt.id} '{prompt.name}': {rendered}")
        except Exception as e:
            print(f"❌ Prompt {prompt.id} '{prompt.name}': ERROR - {e}")
    
    print("\n=== Full Template Test ===")
    try:
        full_rendered = render_template_string(test_template, prompts=prompts)
        print("✅ Full template rendered successfully")
        print(full_rendered)
    except Exception as e:
        print(f"❌ Full template error: {e}")
EOF < /dev/null