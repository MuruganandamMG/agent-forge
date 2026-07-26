import sys
import traceback
from pathlib import Path
agent_dir = Path(__file__).parent / "agent"
sys.path.insert(0, str(agent_dir))

from runtime.chat_responder import generate_chat_response
from dotenv import load_dotenv

load_dotenv()

res2 = generate_chat_response("Yooo", [], "Context")
print(f"generate_chat_response result: {repr(res2)}")
