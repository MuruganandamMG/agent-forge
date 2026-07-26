import sys
import traceback
from pathlib import Path
agent_dir = Path(__file__).parent / "agent"
sys.path.insert(0, str(agent_dir))

from runtime.models import chat
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an AI assistant.
Respond politely and concisely."""

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "Yooo"}
]

try:
    res = chat(messages, temperature=0.7, max_tokens=500).strip()
    print("Direct chat call result with short system prompt:", repr(res))
except Exception as e:
    traceback.print_exc()

