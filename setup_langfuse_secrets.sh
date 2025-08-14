#!/bin/bash

# Setup Langfuse credentials in Google Cloud Secret Manager
# Run this script to configure Langfuse observability for your cloud functions

PROJECT_ID="vertigo-466116"

echo "Setting up Langfuse credentials in Google Cloud Secret Manager..."
echo "Project: $PROJECT_ID"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ Please authenticate with gcloud first:"
    echo "gcloud auth login"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

echo "📋 Please provide your Langfuse credentials:"
echo "(You can find these at: https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7)"

# Get Langfuse public key
read -p "Enter your Langfuse Public Key: " LANGFUSE_PUBLIC_KEY
if [ -z "$LANGFUSE_PUBLIC_KEY" ]; then
    echo "❌ Public key is required"
    exit 1
fi

# Get Langfuse secret key
read -s -p "Enter your Langfuse Secret Key: " LANGFUSE_SECRET_KEY
echo  # New line after secret input
if [ -z "$LANGFUSE_SECRET_KEY" ]; then
    echo "❌ Secret key is required"
    exit 1
fi

echo "🔐 Creating secrets in Google Cloud Secret Manager..."

# Create the public key secret
echo -n "$LANGFUSE_PUBLIC_KEY" | gcloud secrets create langfuse-public-key --data-file=-
if [ $? -eq 0 ]; then
    echo "✅ Created langfuse-public-key secret"
else
    echo "⚠️  Secret langfuse-public-key might already exist, updating..."
    echo -n "$LANGFUSE_PUBLIC_KEY" | gcloud secrets versions add langfuse-public-key --data-file=-
fi

# Create the secret key secret
echo -n "$LANGFUSE_SECRET_KEY" | gcloud secrets create langfuse-secret-key --data-file=-
if [ $? -eq 0 ]; then
    echo "✅ Created langfuse-secret-key secret"
else
    echo "⚠️  Secret langfuse-secret-key might already exist, updating..."
    echo -n "$LANGFUSE_SECRET_KEY" | gcloud secrets versions add langfuse-secret-key --data-file=-
fi

echo "🚀 Langfuse secrets are now configured!"
echo ""
echo "📝 Next steps:"
echo "1. Deploy your updated cloud functions"
echo "2. Test email processing to verify traces appear in Langfuse"
echo "3. Check your Langfuse dashboard at: https://us.cloud.langfuse.com/project/cmdly8e8a069pad07wqtif0e7"
echo ""
echo "🔧 To deploy functions, run:"
echo "cd vertigo-debug-toolkit"
echo "./deploy_function.sh meeting-processor"
echo "./deploy_function.sh email-processor"