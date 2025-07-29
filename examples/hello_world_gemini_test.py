import google.generativeai as genai
import os

api_key = os.environ["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-pro")
response = model.generate_content("Say hello to the world as Gemini!")
print("Gemini says:", response.text) 