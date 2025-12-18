import os
import google.generativeai as genai

# Paste your API Key here directly to test
os.environ["GOOGLE_API_KEY"] = "AIzaSyDDIEgzGUVdQywwgg0igmW4jKc_GNUUS3Q"

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("Checking available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")