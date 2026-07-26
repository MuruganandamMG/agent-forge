import sys
import traceback
from pathlib import Path
agent_dir = Path(__file__).parent / "agent"
sys.path.insert(0, str(agent_dir))

from runtime.chat_responder import generate_chat_response
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are the Forge Coding Agent, a capable CLI-based AI assistant.
The user just sent a conversational or vague message (not an explicit coding task).
Respond politely, conversationally, and concisely.
If they ask what you can do, explain you can build, refactor, and fix code in their project.
Keep responses under 3 sentences unless explaining a complex topic.

Project Context Summary:
{project_context}
"""
truncated_ctx = "Context"

messages = [
    {"role": "system", "content": SYSTEM_PROMPT.format(project_context=truncated_ctx)},
    {"role": "user", "content": "Yooo"}
]

from runtime.models import chat
try:
    res = chat(messages, temperature=0.7, max_tokens=500).strip()
    print("Direct chat call result:", repr(res))
except Exception as e:
    traceback.print_exc()

res2 = generate_chat_response("Yooo", [], "Context")
print(f"generate_chat_response result: {repr(res2)}")
