import sys
from pathlib import Path
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir))

from runtime.gate import llm_classify
from dotenv import load_dotenv
load_dotenv()

test_queries = [
    "what is ur name!",
    "nothong"
]

for q in test_queries:
    intent = llm_classify(q)
    print(f"LLM CLASSIFY FOR '{q}': {intent}")
