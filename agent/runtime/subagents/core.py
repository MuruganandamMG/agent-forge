import json
from runtime.models import chat
from runtime.subagents.prompts import PLANNER_PROMPT, IMPLEMENTER_PROMPT, REVIEWER_PROMPT

def run_planner(query: str, project_context: str) -> str:
    messages = [
        {"role": "system", "content": PLANNER_PROMPT},
        {"role": "user", "content": f"Context:\n{project_context}\n\nQuery:\n{query}"}
    ]
    return chat(messages, temperature=0.2)

def run_implementer(task_desc: str, file_contents: str, feedback: str = "") -> str:
    user_msg = f"Task:\n{task_desc}\n\nFiles:\n{file_contents}"
    if feedback:
        user_msg += f"\n\nPrevious Reviewer Feedback:\n{feedback}\nPlease fix these issues."
        
    messages = [
        {"role": "system", "content": IMPLEMENTER_PROMPT},
        {"role": "user", "content": user_msg}
    ]
    return chat(messages, temperature=0.1, max_tokens=4000)

def run_reviewer(task_desc: str, diff: str) -> str:
    messages = [
        {"role": "system", "content": REVIEWER_PROMPT},
        {"role": "user", "content": f"Task:\n{task_desc}\n\nProposed Diff:\n{diff}"}
    ]
    return chat(messages, temperature=0.1).strip()
