#!/usr/bin/env python3
"""
Check all prompts for brace structure issues.
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from app.models import Prompt
from app import create_app
import re

def check_all_prompts():
    app = create_app()
    with app.app_context():
        prompts = Prompt.query.all()
        
        for prompt in prompts:
            print(f"\n{'='*60}")
            print(f"PROMPT: {prompt.name}")
            print(f"{'='*60}")
            
            content = prompt.content
            
            # Count braces
            single_open = content.count('{')
            single_close = content.count('}')
            double_open = content.count('{{')
            double_close = content.count('}}')
            
            net_open = single_open - double_open * 2
            net_close = single_close - double_close * 2
            
            print(f"Brace counts:")
            print(f"  Single: {single_open} open, {single_close} close")
            print(f"  Double: {double_open} open, {double_close} close")
            print(f"  Net single: {net_open} open, {net_close} close")
            
            if net_open != net_close:
                print("❌ UNMATCHED BRACES DETECTED!")
                
                # Find the problematic areas
                brace_positions = []
                for i, char in enumerate(content):
                    if char == '{':
                        if i == 0 or content[i-1] != '{':
                            if i == len(content)-1 or content[i+1] != '{':
                                brace_positions.append(('open', i))
                    elif char == '}':
                        if i == 0 or content[i-1] != '}':
                            if i == len(content)-1 or content[i+1] != '}':
                                brace_positions.append(('close', i))
                
                print(f"Single brace positions: {brace_positions}")
                
                # Try to match braces and find unmatched ones
                stack = []
                unmatched = []
                for brace_type, pos in brace_positions:
                    if brace_type == 'open':
                        stack.append(pos)
                    else:  # close
                        if stack:
                            stack.pop()
                        else:
                            unmatched.append(('unmatched_close', pos))
                
                # Any remaining in stack are unmatched opens
                for pos in stack:
                    unmatched.append(('unmatched_open', pos))
                
                if unmatched:
                    print("Unmatched braces:")
                    for brace_type, pos in unmatched:
                        context_start = max(0, pos - 30)
                        context_end = min(len(content), pos + 31)
                        context = content[context_start:context_end]
                        line_num = content[:pos].count('\n') + 1
                        print(f"  {brace_type} at position {pos} (line {line_num}): ...{context}...")
            else:
                print("✅ Braces appear balanced")
                
            # Check what regex finds
            variables = re.findall(r'\{([^}]*)\}', content)
            print(f"\nRegex found {len(variables)} variables:")
            for i, var in enumerate(variables):
                if '\n' in var:
                    print(f"  {i}: PROBLEMATIC (has newlines): {repr(var[:100])}...")
                else:
                    print(f"  {i}: {var}")

if __name__ == "__main__":
    check_all_prompts()