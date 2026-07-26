import sys
import traceback
from pathlib import Path
agent_dir = Path(__file__).parent / "agent"
sys.path.insert(0, str(agent_dir))

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

contents = [
    types.Content(
        role="user", 
        parts=[types.Part.from_text(text="Yooo")]
    )
]

config = types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=500
)

response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents=contents,
    config=config
)

print("Text without system instruction:", repr(response.text))
print("Candidates without system instruction:", response.candidates)
