#!/usr/bin/env python3
"""
Test script to verify semantic search API is working
"""

import requests
import json
from app import create_app
from app.services.semantic_search import SemanticPromptSearch

def test_direct_semantic_search():
    """Test semantic search service directly"""
    print("=== Testing Direct Semantic Search ===")
    
    app = create_app()
    with app.app_context():
        try:
            search = SemanticPromptSearch()
            results = search.search("meeting analysis", limit=5)
            
            print(f"✅ Direct search successful: {results['total']} results")
            for result in results['results'][:3]:
                print(f"  - {result['name']} (score: {result['relevance_score']:.3f})")
                print(f"    Reasons: {', '.join(result['match_reasons'])}")
            
            return True
        except Exception as e:
            print(f"❌ Direct search failed: {e}")
            return False

def test_api_endpoint():
    """Test the API endpoint"""
    print("\n=== Testing API Endpoint ===")
    
    try:
        response = requests.get("http://localhost:5001/prompts/api/prompts/search?q=meeting+analysis")
        
        if response.status_code != 200:
            print(f"❌ API failed with status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check if semantic search was used
        search_method = data.get('search_method', 'unknown')
        interpretation = data.get('query_interpretation', '')
        
        print(f"Status: {response.status_code}")
        print(f"Search method: {search_method}")
        print(f"Query interpretation: {interpretation}")
        print(f"Total results: {data.get('total', 0)}")
        
        if search_method == 'semantic':
            print("✅ Using semantic search")
            return True
        elif 'semantic' in interpretation.lower():
            print("✅ Using semantic search (detected from interpretation)")
            return True
        else:
            print("⚠️ Using fallback search")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Semantic Search Implementation")
    
    # Test direct access
    direct_success = test_direct_semantic_search()
    
    # Test API endpoint
    api_success = test_api_endpoint()
    
    print(f"\n📊 Results:")
    print(f"Direct semantic search: {'✅ Working' if direct_success else '❌ Failed'}")
    print(f"API endpoint: {'✅ Using semantic search' if api_success else '⚠️ Using fallback'}")
    
    if direct_success and not api_success:
        print("\n🔧 Recommendation: Restart Flask server to reload the route code")
    elif direct_success and api_success:
        print("\n🎉 Semantic search deployment is successful!")
    else:
        print("\n❌ Issues detected that need investigation")