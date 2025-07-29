# Vertigo: AI Status Generator

Vertigo is an intelligent email processing system that automatically generates executive status updates from meeting transcripts and project communications. Built on Google Vertex AI stack with Gemini LLM integration.

## Project Structure

```
vertigo/
├── functions/
│   ├── email-processor/
│   ├── status-generator/
│   └── shared/
├── firestore/
│   ├── security-rules.js
│   └── indexes.json
├── config/
│   ├── env.yaml
│   └── vertex-ai-config.json
└── tests/
```

## Core Features
- Cloud Functions for email processing and status generation
- Firestore for semantic data storage
- Vertex AI (Gemini) for content analysis
- Gmail API integration

## Setup Instructions
1. **Clone the repository**
2. **Set up Google Cloud Project**
   - Enable Vertex AI, Firestore, and Gmail APIs
   - Create service accounts and download credentials
3. **Configure environment variables**
   - See `config/env.yaml` for required variables
4. **Install dependencies**
   - Each Cloud Function has its own `requirements.txt`
5. **Deploy Cloud Functions**
   - Use `gcloud functions deploy ...` for each function
6. **Set up Gmail webhook and Firestore indexes**

See individual directories for more details and usage examples. 