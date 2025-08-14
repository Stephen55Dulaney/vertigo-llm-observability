#!/usr/bin/env python3

def is_vertigo_command(subject):
    """Check if email subject contains a Vertigo command."""
    subject_lower = subject.lower().strip()
    
    # Remove common reply/forward prefixes
    if subject_lower.startswith('re:'):
        subject_lower = subject_lower[3:].strip()
    elif subject_lower.startswith('fwd:'):
        subject_lower = subject_lower[4:].strip()
    
    # Check for Vertigo prefix
    if subject_lower.startswith('vertigo:'):
        subject_lower = subject_lower[8:].strip()
    
    commands = [
        'list this week',
        'total stats', 
        'list projects',
        'help',
        'prompt report'
    ]
    
    return any(subject_lower.startswith(cmd) for cmd in commands)

# Test cases
test_subjects = [
    "Vertigo: Help",
    "Re: Vertigo: Help", 
    "Fwd: Vertigo: Help",
    "Vertigo: Total stats",
    "Total stats",
    "List this week",
    "Vertigo: List this week",
    "Some random subject",
    "Meeting summary",
    "Re: Vertigo: List projects"
]

print("Testing command detection:")
print("=" * 50)

for subject in test_subjects:
    is_command = is_vertigo_command(subject)
    print(f"'{subject}' -> {'✅ COMMAND' if is_command else '❌ NOT COMMAND'}") 