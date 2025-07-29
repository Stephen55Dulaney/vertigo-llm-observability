# Status Generator Function

This Cloud Function is triggered by emails with subjects like "generate status". It queries Firestore for recent meeting data, uses Gemini Pro to synthesize an executive summary, and drafts a status update email for review and sending.
