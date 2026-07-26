import sys
from pathlib import Path
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir))

from runtime.gate import classify_input

test_queries = [
    "what is ur name!",
    "Fix this issue. Make sure it is connected to the Gemini elements.",
    "nothong"
]

for q in test_queries:
    intent = classify_input(q)
    print(f"QUERY: '{q}'\nINTENT: {intent}\n")
