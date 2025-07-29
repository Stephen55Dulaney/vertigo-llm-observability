#!/bin/bash
# Test script for cursor meeting summarizer

echo "🧪 Testing Cursor Meeting Summarizer..."
cd "$(dirname "$0")"

# Source environment
source ./setup_env.sh

# Run the summarizer
python3 cursor_meeting_summarizer.py

echo "✅ Test completed. Check the output above and any generated files."
