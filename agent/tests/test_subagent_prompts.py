import pytest
from runtime.subagents.prompts import PLANNER_PROMPT, IMPLEMENTER_PROMPT, REVIEWER_PROMPT

def test_prompts_exist_and_are_strings():
    assert isinstance(PLANNER_PROMPT, str)
    assert isinstance(IMPLEMENTER_PROMPT, str)
    assert isinstance(REVIEWER_PROMPT, str)
    assert "plan" in PLANNER_PROMPT.lower()
    assert "diff" in IMPLEMENTER_PROMPT.lower()
    assert "review" in REVIEWER_PROMPT.lower()
