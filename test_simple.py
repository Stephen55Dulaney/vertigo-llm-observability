#!/usr/bin/env python3
import sys
import os

print("Testing EmailCommandParser...")

try:
    from email_command_parser import EmailCommandParser
    print("✅ Successfully imported EmailCommandParser")
    
    # Test instantiation
    try:
        parser = EmailCommandParser()
        print("✅ Successfully created EmailCommandParser instance")
        
        # Test help command
        result = parser.parse_command("Vertigo: Help")
        if result:
            print("✅ Help command works!")
            print(f"Subject: {result['subject']}")
            print(f"Command: {result['command']}")
        else:
            print("❌ Help command returned None")
            
    except Exception as e:
        print(f"❌ Error creating parser: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Error importing EmailCommandParser: {e}")
    import traceback
    traceback.print_exc() 