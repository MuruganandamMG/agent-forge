import sys
from pathlib import Path
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir))

from runtime.gate import classify_input
from runtime.chat_responder import generate_chat_response
from dotenv import load_dotenv

load_dotenv()

q = "hah!1"
intent = classify_input(q)
print(f"ROUTING INTENT FOR '{q}': {intent}")

if intent == "chat":
    res = generate_chat_response(q, [], "Context")
    print(f"RESPONSE: {res}")

