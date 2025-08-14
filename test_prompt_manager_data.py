#!/usr/bin/env python3
"""
Test script to check prompt data for the Prompt Manager
"""

import os
import sys
import json
from datetime import datetime

# Add the vertigo-debug-toolkit to the path
sys.path.append('/Users/stephendulaney/Documents/Vertigo/vertigo-debug-toolkit')

def test_prompt_data():
    """Test what data the Prompt Manager should be receiving"""
    print("🔍 TESTING PROMPT MANAGER DATA")
    print("=" * 60)
    
    try:
        from app import create_app
        from app.models import Prompt
        
        # Create app context
        app = create_app()
        
        with app.app_context():
            # Get all prompts like the API does
            prompts = Prompt.query.all()
            print(f"✅ Found {len(prompts)} prompts in database")
            
            if len(prompts) == 0:
                print("❌ No prompts found! Need to run reload_prompts.py first")
                return
            
            prompts_data = []
            for prompt in prompts:
                # Calculate basic metrics like the API does
                total_uses = prompt.traces.count()
                success_count = prompt.traces.filter_by(status='success').count()
                success_rate = (success_count / total_uses * 100) if total_uses > 0 else 0
                
                prompt_data = {
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
                        'success_rate': success_rate
                    }
                }
                prompts_data.append(prompt_data)
                
                print(f"\n📋 Prompt {prompt.id}: {prompt.name}")
                print(f"   Type: {prompt.prompt_type}")
                print(f"   Version: {prompt.version}")
                print(f"   Active: {prompt.is_active}")
                print(f"   Tags: {prompt.tags}")
                print(f"   Uses: {total_uses}")
            
            # Test what the API would return
            api_response = {
                'status': 'success',
                'data': prompts_data
            }
            
            print(f"\n" + "=" * 60)
            print("📤 API RESPONSE PREVIEW:")
            print("=" * 60)
            print(json.dumps(api_response, indent=2)[:500] + "...")
            
            print(f"\n" + "=" * 60)
            print("🎯 SEARCH TEST:")
            print("=" * 60)
            
            # Test search functionality
            search_terms = ["risk", "action", "executive", "technical", "detailed"]
            
            for term in search_terms:
                matches = [p for p in prompts_data if term.lower() in p['name'].lower()]
                print(f"Search '{term}': {len(matches)} matches")
                for match in matches:
                    print(f"  - {match['name']}")
            
            print(f"\n" + "=" * 60)
            print("🔧 RECOMMENDATIONS:")
            print("=" * 60)
            
            if len(prompts_data) > 0:
                print("✅ Prompts are in database - API should work")
                print("❌ Issue is likely authentication in Prompt Manager")
                print("🔧 Solutions:")
                print("   1. Make sure you're logged in to the web app")
                print("   2. Or temporarily remove @login_required from API")
                print("   3. Check browser console for JavaScript errors")
            else:
                print("❌ No prompts found - need to reload prompts first")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_prompt_data()