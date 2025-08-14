#!/usr/bin/env python3
"""
Examine the remaining problematic variables after our fix.
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from app.models import Prompt
from app import create_app
import re

def examine_remaining_issues():
    app = create_app()
    with app.app_context():
        prompt = Prompt.query.first()  # Get first prompt to examine
        content = prompt.content
        
        print(f"=== Examining: {prompt.name} ===")
        
        # Apply our escaping logic step by step
        print("\n1. Find valid variables:")
        valid_var_pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        valid_matches = list(re.finditer(valid_var_pattern, content))
        for match in valid_matches:
            print(f"   Valid: {match.group(0)} at {match.start()}-{match.end()}")
        
        print("\n2. Replace with placeholders:")
        temp_content = content
        placeholder_map = {}
        
        for i, match in enumerate(reversed(valid_matches)):
            placeholder = f"__TEMP_VAR_{i}__"
            placeholder_map[placeholder] = match.group(0)
            temp_content = temp_content[:match.start()] + placeholder + temp_content[match.end():]
            print(f"   Replaced {match.group(0)} with {placeholder}")
        
        print(f"\n3. Content after placeholder replacement (first 300 chars):")
        print(temp_content[:300])
        
        print(f"\n4. Escape remaining braces:")
        escaped_content = temp_content.replace('{', '{{').replace('}', '}}')
        print(f"Content after escaping (first 300 chars):")
        print(escaped_content[:300])
        
        print(f"\n5. Restore placeholders:")
        final_content = escaped_content
        for placeholder, original in placeholder_map.items():
            final_content = final_content.replace(placeholder, original)
        
        print(f"Final content (first 500 chars):")
        print(final_content[:500])
        
        print(f"\n6. Check for remaining problematic patterns:")
        remaining_vars = re.findall(r'\{([^}]*)\}', final_content)
        problematic_vars = [v for v in remaining_vars if '\n' in v or len(v) > 50]
        
        print(f"Found {len(problematic_vars)} problematic patterns:")
        for i, pvar in enumerate(problematic_vars[:3]):
            print(f"  {i+1}. {repr(pvar[:150])}...")
            
        # Let's also check for unmatched braces
        print(f"\n7. Brace analysis:")
        single_open = final_content.count('{')
        single_close = final_content.count('}')
        double_open = final_content.count('{{')
        double_close = final_content.count('}}')
        
        net_open = single_open - double_open * 2
        net_close = single_close - double_close * 2
        
        print(f"  Single braces: {single_open} open, {single_close} close")
        print(f"  Double braces: {double_open} open, {double_close} close") 
        print(f"  Net single: {net_open} open, {net_close} close")
        
        if net_open != net_close:
            print(f"  ❌ STILL UNMATCHED!")
        else:
            print(f"  ✅ Balanced braces")

if __name__ == "__main__":
    examine_remaining_issues()