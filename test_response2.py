import sys
from pathlib import Path
agent_dir = Path(__file__).parent / "agent"
sys.path.insert(0, str(agent_dir))

from runtime.models import chat
from dotenv import load_dotenv

load_dotenv()

try:
    messages = [
        {"role": "system", "content": "You are a bot."},
        {"role": "user", "content": "Yooo"}
    ]
    res = chat(messages)
    print(f"RAW CHAT RESPONSE: {res}")
except Exception as e:
    print(f"API ERROR: {e}")
