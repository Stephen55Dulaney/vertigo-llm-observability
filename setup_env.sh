#!/bin/bash
# Environment setup for cursor meeting summarizer

# Set up Python path
export PYTHONPATH="$PYTHONPATH:/workspace"

# Gmail credentials (you'll need to set these)
export GMAIL_CREDENTIALS_PATH="/workspace/credentials.json"

# Gemini API key (optional, for AI-generated summaries)
# export GEMINI_API_KEY="your-gemini-api-key-here"

# Google Cloud credentials (if using)
# export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

echo "Environment variables set for cursor meeting summarizer"
