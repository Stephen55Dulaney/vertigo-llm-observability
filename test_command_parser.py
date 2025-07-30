#!/usr/bin/env python3
from email_command_parser import EmailCommandParser

def test_parser():
    parser = EmailCommandParser()
    subject = 'Re: Vertigo: Help'
    
    print(f"Testing subject: {subject}")
    
    subject_lower = subject.lower().strip()
    print(f"After lower: {subject_lower}")
    
    if subject_lower.startswith('re:'):
        subject_lower = subject_lower[3:].strip()
    elif subject_lower.startswith('fwd:'):
        subject_lower = subject_lower[4:].strip()
    print(f"After re: removal: {subject_lower}")
    
    if subject_lower.startswith('vertigo:'):
        subject_lower = subject_lower[8:].strip()
    print(f"After vertigo: removal: {subject_lower}")
    
    print(f"Final subject: '{subject_lower}'")
    print(f"Commands: {list(parser.commands.keys())}")
    
    for command in parser.commands.keys():
        match = subject_lower.startswith(command)
        print(f"Checking '{subject_lower}'.startswith('{command}'): {match}")
        if match:
            print(f"MATCH FOUND: {command}")
            break
    
    result = parser.parse_command(subject)
    print(f"Final result: {result}")

if __name__ == "__main__":
    test_parser() 