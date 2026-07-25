import sys
from pathlib import Path

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add the agent directory to the Python path
root_dir = Path(__file__).parent.resolve()
agent_dir = root_dir / "agent"
sys.path.insert(0, str(agent_dir))

from runtime.main import main

if __name__ == "__main__":
    # Call the CLI click entry point/
    main()
