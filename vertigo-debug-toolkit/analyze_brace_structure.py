#!/usr/bin/env python3
"""
Analyze the brace structure in prompts to identify malformed templates.
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from app.models import Prompt
from app import create_app

def analyze_braces():
    app = create_app()
    with app.app_context():
        prompt = Prompt.query.first()  # Get first prompt
        content = prompt.content
        
        print(f"=== Analyzing Prompt: {prompt.name} ===")
        print(f"Total length: {len(content)}")
        print()
        
        # Show the actual content with line numbers
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            print(f"{i:3d}: {line}")
        
        print("\n=== Brace Analysis ===")
        single_open = content.count('{')
        single_close = content.count('}')
        double_open = content.count('{{')
        double_close = content.count('}}')
        
        print(f"Single braces: {single_open} open, {single_close} close")
        print(f"Double braces: {double_open} open, {double_close} close")
        print(f"Net single braces: {single_open - double_open*2} open, {single_close - double_close*2} close")
        
        # Find all single brace positions
        print("\n=== Single Brace Positions ===")
        for i, char in enumerate(content):
            if char == '{':
                # Check if it's part of a double brace
                if i > 0 and content[i-1] == '{':
                    continue  # Part of {{
                if i < len(content) - 1 and content[i+1] == '{':
                    continue  # Part of {{
                
                # Find the end of this variable
                end_pos = content.find('}', i)
                if end_pos != -1:
                    # Check if it's part of a double brace
                    if end_pos < len(content) - 1 and content[end_pos+1] == '}':
                        continue
                    if end_pos > 0 and content[end_pos-1] == '}':
                        continue
                    
                    var_content = content[i:end_pos+1]
                    context_start = max(0, i-20)
                    context_end = min(len(content), end_pos+21)
                    context = content[context_start:context_end]
                    print(f"Variable at {i}-{end_pos}: {var_content}")
                    print(f"Context: ...{context}...")
                    print()

if __name__ == "__main__":
    analyze_braces()