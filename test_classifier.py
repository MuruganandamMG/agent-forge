import sys
from pathlib import Path
agent_dir = Path(__file__).parent / "agent"
sys.path.insert(0, str(agent_dir))

from runtime.gate import classify_input
from dotenv import load_dotenv

load_dotenv()

intent = classify_input("Yooo")
print(f"INTENT FOR 'Yooo': {intent}")
