import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
print("API Key loaded from env:", bool(os.environ.get("GEMINI_API_KEY")))

try:
    client = genai.Client()
    print("Client initialized successfully.")
    
    # Let's do a tiny test call
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents="Say exactly the word 'SUCCESS'"
    )
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
