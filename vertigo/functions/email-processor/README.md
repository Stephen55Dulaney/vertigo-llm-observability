# Email Processor Function

This Cloud Function is triggered by incoming emails to vertigo@[domain].com. It extracts meeting transcripts, attachments, and metadata, then uses Gemini Pro for content analysis and semantic tagging. Results are stored in Firestore for downstream processing.
