#!/usr/bin/env python3
"""
Test script to demonstrate different prompt variants for meeting analysis.
This helps you choose the best prompt for different types of meetings.
"""

import json
import os
import sys
from prompt_variants import get_prompt_variant
import google.generativeai as genai

# Sample meeting transcript for testing
SAMPLE_TRANSCRIPT = """
Stephen: Alright, let's dive into the Merge project. I've been thinking about the architecture - we need to decide between a microservices approach or a monolithic design.

Claude: I think microservices would be better for scalability, but it adds complexity. What's your take on the trade-offs?

Stephen: Good point. I'm leaning toward microservices because we'll need to handle multiple data sources. But we need to be careful about the API design.

Claude: Agreed. I suggest we start with a proof of concept using Node.js and Express for the API layer. We can use MongoDB for the database.

Stephen: That sounds good. Let's set up the development environment by Friday. John, can you handle the initial setup?

John: Sure, I'll get the basic project structure ready by Friday. I'll also look into Docker for containerization.

Sarah: I can help with the database schema design. Should we use Mongoose for the ODM?

Stephen: Yes, Mongoose would be perfect. Sarah, can you have a draft schema ready by next Tuesday?

Sarah: Absolutely. I'll also research authentication options - I'm thinking JWT tokens.

Claude: Good choice. We should also plan for testing. I recommend Jest for unit tests and Postman for API testing.

Stephen: Excellent. Let's also set up CI/CD with GitHub Actions. John, can you handle that?

John: Yes, I'll set up the GitHub Actions workflow. Should we deploy to AWS or Google Cloud?

Stephen: Let's go with AWS for now. We can always migrate later if needed.

Claude: One concern - we need to make sure our API is secure. We should implement rate limiting and input validation.

Stephen: Absolutely. That's a critical requirement. Let's add security testing to our checklist.

Sarah: I'm also thinking about performance. We should plan for caching with Redis.

Stephen: Good thinking. Let's add Redis to our tech stack. John, can you research Redis setup?

John: Will do. I'll also look into monitoring tools like New Relic or DataDog.

Stephen: Perfect. So our action items are: John handles dev environment and CI/CD, Sarah works on database schema, and we all need to think about security and performance.

Claude: And we should have our first API endpoint ready for testing by next Friday.

Stephen: Agreed. Let's meet again next Monday to review progress.
"""

def test_prompt_variant(variant_name: str, transcript: str, project: str):
    """Test a specific prompt variant and return the results."""
    try:
        # Configure Gemini
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY environment variable not set")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        # Get the prompt
        prompt = get_prompt_variant(variant_name, transcript, project)
        
        print(f"\n{'='*60}")
        print(f"Testing Prompt Variant: {variant_name.upper()}")
        print(f"{'='*60}")
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Try to parse as JSON
        try:
            # Clean up the response - remove markdown code blocks if present
            cleaned_response = response.text.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]  # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            
            structured_data = json.loads(cleaned_response.strip())
            print("✅ Successfully parsed as JSON")
            print(f"📊 Structured Data Keys: {list(structured_data.keys())}")
            
            # Show key metrics
            if "action_items" in structured_data:
                print(f"📋 Action Items: {len(structured_data['action_items'])}")
            if "risks" in structured_data:
                print(f"⚠️  Risks: {len(structured_data['risks'])}")
            if "technical_details" in structured_data:
                print(f"🔧 Technical Details: {len(structured_data['technical_details'])}")
            
            return {
                "variant": variant_name,
                "success": True,
                "structured_data": structured_data,
                "raw_response": response.text
            }
            
        except json.JSONDecodeError as e:
            print("❌ Failed to parse as JSON")
            print(f"Error: {e}")
            print(f"Raw response: {response.text[:500]}...")
            return {
                "variant": variant_name,
                "success": False,
                "error": str(e),
                "raw_response": response.text
            }
            
    except Exception as e:
        print(f"❌ Error testing {variant_name}: {e}")
        return {
            "variant": variant_name,
            "success": False,
            "error": str(e)
        }

def compare_variants(transcript: str, project: str):
    """Compare all prompt variants and show results."""
    variants = [
        "detailed_extraction",
        "executive_summary", 
        "technical_focus",
        "action_oriented",
        "risk_assessment"
    ]
    
    results = {}
    
    print("🧪 Testing All Prompt Variants")
    print("="*60)
    
    for variant in variants:
        result = test_prompt_variant(variant, transcript, project)
        results[variant] = result
        
        if result and result["success"]:
            print(f"✅ {variant}: SUCCESS")
        else:
            print(f"❌ {variant}: FAILED")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    successful_variants = [v for v, r in results.items() if r and r["success"]]
    failed_variants = [v for v, r in results.items() if not r or not r["success"]]
    
    print(f"✅ Successful: {len(successful_variants)}")
    print(f"❌ Failed: {len(failed_variants)}")
    
    if successful_variants:
        print(f"\n🎯 Best Variants: {', '.join(successful_variants)}")
    
    return results

def show_detailed_comparison(results: dict):
    """Show detailed comparison of successful variants."""
    successful_results = {k: v for k, v in results.items() if v and v["success"]}
    
    if not successful_results:
        print("No successful variants to compare")
        return
    
    print(f"\n{'='*60}")
    print("📈 DETAILED COMPARISON")
    print(f"{'='*60}")
    
    for variant, result in successful_results.items():
        data = result["structured_data"]
        print(f"\n🔍 {variant.upper()}:")
        
        # Count different types of extracted information
        metrics = {}
        for key, value in data.items():
            if isinstance(value, list):
                metrics[key] = len(value)
            elif isinstance(value, str):
                metrics[key] = len(value.split())
        
        # Show top metrics
        for metric, count in sorted(metrics.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {metric}: {count}")
        
        # Show sample action items if available
        if "action_items" in data and data["action_items"]:
            print(f"  Sample Action Item: {data['action_items'][0].get('description', 'N/A')[:50]}...")

if __name__ == "__main__":
    print("🚀 Meeting Processor Prompt Variant Tester")
    print("="*60)
    
    # Test with sample transcript
    project = "merge"
    
    # Run comparison
    results = compare_variants(SAMPLE_TRANSCRIPT, project)
    
    # Show detailed comparison
    show_detailed_comparison(results)
    
    print(f"\n{'='*60}")
    print("💡 RECOMMENDATIONS")
    print(f"{'='*60}")
    print("1. Use 'detailed_extraction' for comprehensive meeting analysis")
    print("2. Use 'action_oriented' for meetings focused on deliverables")
    print("3. Use 'technical_focus' for engineering/architecture meetings")
    print("4. Use 'executive_summary' for high-level strategic meetings")
    print("5. Use 'risk_assessment' for meetings with significant risks/blockers")
    
    print(f"\n🎯 For your Merge meeting tomorrow, I recommend:")
    print("   - 'detailed_extraction' for comprehensive coverage")
    print("   - 'action_oriented' if you want to focus on deliverables")
    print("   - 'technical_focus' if it's primarily a technical discussion") 