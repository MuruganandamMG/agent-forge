"""Input gate classifier for fast rejection of non-actionable CLI inputs."""

import re
from pathlib import Path

from runtime.models import chat

TRIVIAL_PATTERNS = [
    r"^(hi|hello|hey|hola|sup|yo|nahh?|hmm+)\b",
    r"^[a-z]{1,6}$",
    r"^\s*$",
]

CODE_SIGNALS = [
    "def ",
    "class ",
    "import ",
    "fix ",
    "add ",
    "implement ",
    "refactor ",
    "create ",
    "write ",
    "bug",
    "error",
    "test",
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".json",
    ".toml",
    ".md",
    "git",
    "pip",
    "pytest",
    "function",
    "module",
]


def quick_classify(text: str) -> str:
    """Classify user input into 'trivial', 'vague', 'task', or 'unknown'.

    Returns:
        'trivial': Greetings, gibberish (e.g. 'hhmm', 'HELLO NAHH'), empty strings
        'task': Actionable coding request containing clear code signals
        'unknown': Needs LLM classification
    """
    if not text:
        return "trivial"

    t = text.strip().lower()
    if not t:
        return "trivial"

    words = t.split()

    # Check for trivial patterns (short gibberish or simple greetings)
    if len(words) <= 3 and any(re.search(p, t) for p in TRIVIAL_PATTERNS):
        return "trivial"

    # Specific vague phrases check
    if t in ("fix it", "check this", "do something", "help me"):
        return "unknown"

    # Check for strong code signals
    if any(sig in t for sig in CODE_SIGNALS) or t.startswith("/plan"):
        return "task"

    # For everything else (including questions > 3 words), ask the LLM
    return "unknown"


def _load_classifier_prompt() -> str:
    """Load classifier system prompt from prompts/classifier_system.txt."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "classifier_system.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return (
        "You are a task classifier for a coding assistant.\n"
        "Classify the following user input as exactly one of:\n"
        "- TASK: a clear, actionable coding request (create, fix, refactor, test, debug, etc.)\n"
        "- VAGUE: needs more detail before the assistant can act\n"
        "- CHAT: conversation, greeting, or non-coding discussion\n\n"
        "Reply with exactly one word: TASK, VAGUE, or CHAT."
    )


def llm_classify(text: str, project_context: str = "") -> str:
    """Stage 2 LLM-assisted input classifier for ambiguous user inputs.

    Calls chat() from runtime.models with prompts/classifier_system.txt.
    Returns normalized label: 'task', 'vague', or 'chat' (fallback to 'task' on error).
    """
    try:
        system_prompt = _load_classifier_prompt()
        if project_context:
            user_content = f"Project Context:\n{project_context}\n\nUser Input: {text}"
        else:
            user_content = f"User Input: {text}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        response = chat(messages, temperature=0.0, max_tokens=1000, stop=["\n"])
        res = response.strip().lower()
        first_word = res.split()[0] if res else ""
        if first_word in ("task", "vague", "chat"):
            return first_word
        return "task"
    except Exception:
        return "task"


def classify_input(text: str, project_context: str = "") -> str:
    """Two-stage input gate classifier.

    Stage 1: Quick regex/keyword heuristic (quick_classify).
    Stage 2: Fast LLM classifier (llm_classify) if Stage 1 returned 'unknown'.
    """
    stage1 = quick_classify(text)
    if stage1 == "trivial":
        return "trivial"
    if stage1 == "task":
        return "task"
    
    return llm_classify(text, project_context)
