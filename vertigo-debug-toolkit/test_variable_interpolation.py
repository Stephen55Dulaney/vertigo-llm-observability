#!/usr/bin/env python3
"""
Test script to reproduce the variable interpolation bug in prompt testing.
This will help us understand exactly what's happening with the escape characters.
"""

def test_variable_interpolation_bug():
    """Reproduce the variable interpolation bug."""
    
    # Simulate a prompt with problematic variable formatting
    test_prompt = """You are analyzing meeting transcript for project {project}.

IMPORTANT: Return your response as JSON:

{{
    "meeting_summary": "Summary of the meeting",
    "key_points": [
        "Point 1"
    ]
}}

Transcript:
{transcript}"""

    # Sample variables that might cause issues
    sample_vars = {
        'project': 'test_project',
        'transcript': 'This is a test transcript'
    }
    
    print("=== Testing Normal Case ===")
    try:
        formatted = test_prompt.format(**sample_vars)
        print("✅ Normal formatting works")
        print("First 200 chars:", formatted[:200])
    except KeyError as e:
        print(f"❌ KeyError: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error str: '{str(e)}'")
        print(f"Error repr: {repr(str(e))}")
    
    print("\n=== Testing with Missing Variable ===")
    # Remove a variable to trigger the error
    incomplete_vars = {'project': 'test_project'}  # Missing 'transcript'
    
    try:
        formatted = test_prompt.format(**incomplete_vars)
        print("✅ Should not reach here")
    except KeyError as e:
        print(f"❌ KeyError: {e}")
        print(f"Error str: '{str(e)}'")
        print(f"Error repr: {repr(str(e))}")
        
        # Test the problematic logic from the original code
        error_var = str(e).strip("'")
        print(f"After strip('): '{error_var}'")
        newline_char = '\\n'
        print(f"Starts with \\n: {error_var.startswith(newline_char)}")
        print(f"Contains \\n: {newline_char in error_var}")
        
        # Show what the original code would do
        if error_var.startswith(newline_char):
            error_var_cleaned = error_var.replace(newline_char, '').strip()
            print(f"After cleaning: '{error_var_cleaned}'")

    print("\n=== Testing with Actual Newline in Variable Name ===")
    # Test with a variable that actually has a newline in the name
    problematic_prompt = "Hello {normal_var} and {var_with\nnewline}"
    vars_with_newline = {'normal_var': 'test'}
    
    try:
        formatted = problematic_prompt.format(**vars_with_newline)
        print("✅ Should not reach here")
    except KeyError as e:
        print(f"❌ KeyError with actual newline: {e}")
        print(f"Error str: '{str(e)}'")
        print(f"Error repr: {repr(str(e))}")

if __name__ == "__main__":
    test_variable_interpolation_bug()