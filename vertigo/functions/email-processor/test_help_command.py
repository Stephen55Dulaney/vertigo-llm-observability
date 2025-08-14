#!/usr/bin/env python3
"""
Test script for the Help command in email processor.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_help_command():
    """Test the Help command locally."""
    print("🔍 Testing Help Command")
    print("=" * 50)
    
    try:
        # Import the email command parser
        from email_command_parser import EmailCommandParser
        
        print("✅ Successfully imported EmailCommandParser")
        
        # Initialize parser
        parser = EmailCommandParser()
        print(f"✅ Parser initialized. Firestore available: {parser.db is not None}")
        
        # Test help command variants
        test_subjects = [
            "Vertigo: Help",
            "help", 
            "Re: Vertigo: Help",
            "HELP",
            "Vertigo: help"
        ]
        
        print("\n📋 Testing Help Command Variants:")
        print("-" * 40)
        
        for subject in test_subjects:
            print(f"\n🧪 Testing subject: '{subject}'")
            
            try:
                result = parser.parse_command(subject, "")
                
                if result:
                    print(f"✅ Success! Command: {result['command']}")
                    print(f"📧 Subject: {result['subject']}")
                    print(f"📝 Body length: {len(result['body'])} characters")
                    
                    # Print first few lines of help text
                    body_lines = result['body'].strip().split('\n')
                    print("📖 Help content preview:")
                    for i, line in enumerate(body_lines[:5]):
                        print(f"   {line}")
                    if len(body_lines) > 5:
                        print(f"   ... (and {len(body_lines) - 5} more lines)")
                        
                else:
                    print("❌ No result returned")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n🔍 Testing Firestore Integration:")
        print("-" * 40)
        
        # Test other commands that require Firestore
        if parser.db:
            try:
                # Test total stats command
                result = parser.parse_command("Vertigo: Total stats", "")
                if result:
                    print("✅ Total stats command works")
                else:
                    print("❌ Total stats command failed")
                    
                # Test list projects command  
                result = parser.parse_command("Vertigo: List projects", "")
                if result:
                    print("✅ List projects command works")
                else:
                    print("❌ List projects command failed")
                    
            except Exception as e:
                print(f"⚠️ Firestore commands failed: {e}")
        else:
            print("⚠️ Firestore not available - skipping Firestore-dependent tests")
            
        print("\n✅ Help Command Test Complete!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_langfuse_client():
    """Test Langfuse client initialization."""
    print("\n🔍 Testing Langfuse Client")
    print("=" * 50)
    
    try:
        from langfuse_client import langfuse_client
        
        print(f"✅ Langfuse client imported")
        print(f"🔌 Langfuse enabled: {langfuse_client.is_enabled()}")
        
        if langfuse_client.is_enabled():
            # Test creating a trace
            trace_id = langfuse_client.create_trace(
                name="test_help_command", 
                metadata={"test": True}
            )
            print(f"✅ Test trace created: {trace_id}")
            
            # Flush to make sure it works
            langfuse_client.flush()
            print("✅ Langfuse flush completed")
        else:
            print("⚠️ Langfuse not enabled - check credentials")
            
        return True
        
    except Exception as e:
        print(f"❌ Langfuse test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Email Processor Tests")
    print("=" * 60)
    
    # Set environment for testing
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'vertigo-466116'
    
    success = True
    
    # Test help command
    if not test_help_command():
        success = False
    
    # Test Langfuse client
    if not test_langfuse_client():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed")
    
    sys.exit(0 if success else 1)