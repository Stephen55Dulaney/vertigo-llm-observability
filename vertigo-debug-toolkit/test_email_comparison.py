#!/usr/bin/env python3
"""
Test the email comparison functionality.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.email_formatter import EmailFormatter

def test_basic_comparison():
    """Test basic email comparison functionality."""
    print("🔧 Testing Email Comparison Tool...")
    
    # Sample actual email content
    actual_content = """
    Meeting Summary
    
    Key Points:
    - Daily planning and goal setting discussion
    - Google Agent Space exploration and setup
    - AI enablement strategy for workflow optimization
    
    Action Items:
    - Max: Complete migration of legacy systems by Friday
    - Sarah: Research AI tools for customer service automation
    - Team: Review and approve new workflow documentation
    
    Next Steps:
    - Schedule follow-up meeting for next week
    - Implement priority AI tools identified in research
    - Begin pilot testing of new workflow processes
    
    Participants: Max Thompson, Sarah Chen, Alex Rodriguez, Jordan Kim
    """
    
    # Sample LLM generated content with differences
    llm_content = """
    Meeting Summary
    
    Key Points:
    - Daily planning and goal setting discussion
    - Google Agent workspace configuration and implementation  
    - AI enablement strategy for workflow optimization
    
    Action Items:
    - Max: Complete migration of legacy systems by Friday
    - Sarah: Research AI tools for customer service automation
    - Jordan: Update team documentation with new processes
    - Team: Review and approve new workflow documentation
    
    Next Steps:
    - Schedule follow-up meeting for next week
    - Implement priority AI tools identified in research
    - Begin pilot testing of new workflow processes
    - Conduct training session on new AI tools
    
    Participants: Max Thompson, Sarah Chen, Alex Rodriguez, Jordan Kim
    """
    
    # Test the formatter
    formatter = EmailFormatter()
    
    try:
        print("📧 Parsing email content...")
        actual_email = formatter.parse_email_content(actual_content)
        llm_email = formatter.parse_email_content(llm_content)
        
        print(f"✅ Actual email parsed: {actual_email.subject}")
        print(f"   - Key points: {len(actual_email.key_points)}")
        print(f"   - Action items: {len(actual_email.action_items)}")
        print(f"   - Participants: {len(actual_email.participants)}")
        
        print(f"✅ LLM email parsed: {llm_email.subject}")
        print(f"   - Key points: {len(llm_email.key_points)}")
        print(f"   - Action items: {len(llm_email.action_items)}")
        print(f"   - Participants: {len(llm_email.participants)}")
        
        print("\n🔍 Performing comparison...")
        comparison = formatter.compare_emails(actual_content, llm_content)
        
        print(f"✅ Comparison completed!")
        print(f"   - Overall score: {comparison.metrics.overall_score}%")
        print(f"   - Content accuracy: {comparison.metrics.content_accuracy}%")
        print(f"   - Differences found: {len(comparison.differences)}")
        print(f"   - Recommendations: {len(comparison.recommendations)}")
        print(f"   - Strengths: {len(comparison.strengths)}")
        
        # Show some differences
        if comparison.differences:
            print("\n📋 Key differences found:")
            for i, diff in enumerate(comparison.differences[:3], 1):
                print(f"   {i}. {diff.get('description', 'Unknown difference')}")
        
        # Show some recommendations
        if comparison.recommendations:
            print("\n💡 Top recommendations:")
            for i, rec in enumerate(comparison.recommendations[:3], 1):
                print(f"   {i}. {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        return False

def test_json_comparison():
    """Test comparison from JSON data."""
    print("\n🔧 Testing JSON-based comparison...")
    
    sample_json = {
        "actual_output": """
        Meeting Summary
        
        Key Points:
        - Daily planning discussion
        - Agent workspace setup
        
        Action Items:
        - Max: Complete migration by Friday
        - Sarah: Research AI tools
        
        Participants: Max, Sarah
        """,
        "llm_output": """
        Meeting Summary
        
        Key Points:
        - Daily planning discussion
        - Agent workspace configuration
        
        Action Items:
        - Max: Complete migration by Friday
        - Sarah: Research AI automation tools
        - Jordan: Update documentation
        
        Participants: Max, Sarah, Jordan
        """,
        "metrics": {
            "response_time": 1.5,
            "total_cost": 0.032,
            "token_count": 180
        }
    }
    
    formatter = EmailFormatter()
    
    try:
        comparison = formatter.generate_comparison_from_json(sample_json)
        
        print(f"✅ JSON comparison completed!")
        print(f"   - Overall score: {comparison.metrics.overall_score}%")
        print(f"   - Response time: {comparison.metrics.response_time}s")
        print(f"   - Total cost: ${comparison.metrics.total_cost:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during JSON comparison: {e}")
        return False

def test_html_output():
    """Test HTML output generation."""
    print("\n🔧 Testing HTML output generation...")
    
    # Use the standalone tool
    from email_comparison_tool import EmailComparisonTool
    
    tool = EmailComparisonTool()
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as actual_file:
        actual_file.write("""
        Meeting Summary
        
        Key Points:
        - Daily planning discussion
        - Team coordination
        
        Action Items:
        - Complete project by Friday
        - Review documentation
        """)
        actual_path = actual_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as llm_file:
        llm_file.write("""
        Meeting Summary
        
        Key Points:
        - Daily planning discussion
        - Team coordination and communication
        
        Action Items:
        - Complete project by Friday
        - Review and update documentation
        - Schedule follow-up meeting
        """)
        llm_path = llm_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as output_file:
        output_path = output_file.name
    
    try:
        comparison = tool.compare_files(actual_path, llm_path, output_path)
        
        if comparison and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ HTML report generated successfully!")
            print(f"   - Output file: {output_path}")
            print(f"   - File size: {file_size} bytes")
            
            # Clean up
            os.unlink(actual_path)
            os.unlink(llm_path)
            os.unlink(output_path)
            
            return True
        else:
            print("❌ HTML generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error generating HTML: {e}")
        # Clean up on error
        try:
            os.unlink(actual_path)
            os.unlink(llm_path)
            os.unlink(output_path)
        except:
            pass
        return False

def main():
    """Run all tests."""
    print("🧪 Email Comparison Tool Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Comparison", test_basic_comparison),
        ("JSON Comparison", test_json_comparison),
        ("HTML Output", test_html_output),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        if test_func():
            print(f"✅ {test_name} PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Email comparison tool is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())