#!/bin/bash
# Deploy Cloud Function with optimized settings

gcloud functions deploy email-processor-v2 \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --timeout=540s \
  --memory=512MB \
  --max-instances=10 \
  --entry-point email_processor_v2 \
  --source ../vertigo/functions/email-processor \
  --set-env-vars GOOGLE_CLOUD_PROJECT_ID=vertigo-466116 \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \
  --set-env-vars LANGWATCH_API_KEY=$LANGWATCH_API_KEY \
  --set-env-vars LANGWATCH_PROJECT_ID=$LANGWATCH_PROJECT_ID \
  --set-env-vars LANGWATCH_HOST=$LANGWATCH_HOST
