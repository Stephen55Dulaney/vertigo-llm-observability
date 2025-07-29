import google.generativeai as genai
import os

def get_gemini_model(model_name="gemini-1.5-pro"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name) 