#!/usr/bin/env python3

# Test the parse_command method directly
subject = 'Re: Vertigo: Help'
subject_lower = subject.lower().strip()

print(f"Original: {subject}")
print(f"After lower: {subject_lower}")

# Remove common reply/forward prefixes
if subject_lower.startswith('re:'):
    subject_lower = subject_lower[3:].strip()
elif subject_lower.startswith('fwd:'):
    subject_lower = subject_lower[4:].strip()
print(f"After re: removal: {subject_lower}")

# Check for Vertigo prefix
if subject_lower.startswith('vertigo:'):
    subject_lower = subject_lower[8:].strip()
print(f"After vertigo: removal: {subject_lower}")

print(f"Final subject: '{subject_lower}'")

# Test the commands
commands = ['list this week', 'total stats', 'list projects', 'help', 'prompt report']
for command in commands:
    match = subject_lower.startswith(command)
    print(f"'{subject_lower}'.startswith('{command}'): {match}")
    if match:
        print(f"MATCH FOUND: {command}")
        break 