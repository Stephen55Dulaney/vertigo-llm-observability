#!/bin/bash

# Deploy email-processor-v2 Cloud Function with Help command fixes
# Usage: ./deploy.sh

set -e

echo "🚀 Deploying email-processor-v2 Cloud Function..."
echo "=" * 60

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the email-processor function directory"
    echo "Expected files: main.py, requirements.txt"
    exit 1
fi

# Check if email_command_parser.py exists
if [ ! -f "email_command_parser.py" ]; then
    echo "❌ Error: email_command_parser.py not found"
    echo "This file is required for the Help command to work"
    exit 1
fi

# Check if all required files exist
required_files=("main.py" "requirements.txt" "email_command_parser.py" "firestore_stats.py" "langfuse_client.py")

echo "🔍 Checking required files..."
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ Missing: $file"
        exit 1
    fi
done

echo ""
echo "📋 Files to be deployed:"
ls -la *.py requirements.txt

echo ""
echo "🏗️  Deploying to Google Cloud Functions..."

# Deploy the function
gcloud functions deploy email-processor-v2 \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --memory 512MB \
    --timeout 540s \
    --region us-central1 \
    --project vertigo-466116 \
    --entry-point email_processor_v2 \
    --env-vars-file .env.yaml 2>/dev/null || \
    gcloud functions deploy email-processor-v2 \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --memory 512MB \
    --timeout 540s \
    --region us-central1 \
    --project vertigo-466116 \
    --entry-point email_processor_v2

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Function URL:"
echo "https://us-central1-vertigo-466116.cloudfunctions.net/email-processor-v2"
echo ""
echo "🧪 Test the Help command by sending an email with subject:"
echo "\"Vertigo: Help\" to vertigo.agent.2025@gmail.com"
echo ""
echo "📊 Available Commands:"
echo "• Vertigo: Help"
echo "• Vertigo: List this week"
echo "• Vertigo: Total stats"
echo "• Vertigo: List projects"
echo ""
echo "🎉 Deployment successful!"