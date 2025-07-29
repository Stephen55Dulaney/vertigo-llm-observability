import google.generativeai as genai
import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def analyze_transcript_with_gemini(transcript: str) -> dict:
    """
    Calls Gemini Pro to analyze a meeting transcript and extract structured insights.
    Returns a dict with keys: decisions, actions, blockers, context, sentiment.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-pro")
    prompt = (
        "Analyze this meeting transcript and extract structured data. Return JSON with:\n"
        "- decisions: [{decision, impact, stakeholders}]\n"
        "- actions: [{task, owner, deadline, priority}]\n"
        "- blockers: [{issue, impact, proposed_solution}]\n"
        "- context: {project_name, meeting_type, participants}\n"
        "- sentiment: {energy_level, confidence, concerns}\n"
        "Focus on executive-relevant insights that would matter for status reporting.\n"
        f"\nTranscript:\n{transcript}"
    )
    response = model.generate_content(prompt)
    # Try to parse the response as JSON
    try:
        import json
        return json.loads(response.text)
    except Exception:
        return {"raw_response": response.text} 