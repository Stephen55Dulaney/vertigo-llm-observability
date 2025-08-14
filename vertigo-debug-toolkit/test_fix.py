#!/usr/bin/env python3
"""
Test the fix for variable interpolation in prompt testing.
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from app.models import Prompt
from app import create_app
import re

def test_safe_format_prompt():
    """Test the safe_format_prompt function."""
    
    def safe_format_prompt(content, variables):
        """Copy of the updated function from routes.py for testing."""
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

    # Test with sample variables
    sample_vars = {
        'project': 'test_project',
        'transcript': 'This is a test transcript'
    }
    
    print("=== Testing Safe Format Function ===")
    
    app = create_app()
    with app.app_context():
        prompts = Prompt.query.all()
        
        for prompt in prompts:
            print(f"\n--- Testing Prompt: {prompt.name} ---")
            
            try:
                formatted_content, missing_vars, has_malformed = safe_format_prompt(prompt.content, sample_vars)
                
                print(f"✅ Success!")
                print(f"  Missing variables: {missing_vars}")
                print(f"  Has malformed JSON: {has_malformed}")
                print(f"  Content length: {len(formatted_content)} chars")
                print(f"  First 200 chars: {formatted_content[:200]}...")
                
                # Verify no problematic variables in output
                remaining_vars = re.findall(r'\{([^}]*)\}', formatted_content)
                problematic_vars = [v for v in remaining_vars if '\n' in v or len(v) > 50]
                
                if problematic_vars:
                    print(f"  ⚠️  Still has problematic variables: {len(problematic_vars)}")
                    for j, pvar in enumerate(problematic_vars[:2]):  # Show first 2
                        print(f"    {j+1}. {repr(pvar[:100])}...")
                else:
                    print(f"  ✅ No problematic variables remaining")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_safe_format_prompt()