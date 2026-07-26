import sys
from pathlib import Path
agent_dir = Path(__file__).parent
sys.path.insert(0, str(agent_dir))

from runtime.gate import quick_classify

test_queries = [
    "what is ur name!",
    "nothong"
]

for q in test_queries:
    intent = quick_classify(q)
    print(f"QUICK CLASSIFY FOR '{q}': {intent}")
