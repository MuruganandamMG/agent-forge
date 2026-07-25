from unittest.mock import MagicMock, patch

from runtime.gate import classify_input, llm_classify, quick_classify


class TestQuickClassify:
    def test_trivial_inputs(self) -> None:
        assert quick_classify("") == "trivial"
        assert quick_classify("   ") == "trivial"
        assert quick_classify("hello") == "trivial"
        assert quick_classify("hi") == "trivial"
        assert quick_classify("hhmm") == "trivial"
        assert quick_classify("HELLO NAHH") == "trivial"
        assert quick_classify("yo") == "trivial"
        assert quick_classify("sup") == "trivial"

    def test_vague_inputs(self) -> None:
        assert quick_classify("fix it") == "unknown"
        assert quick_classify("do something") == "unknown"
        assert quick_classify("check this") == "unknown"

    def test_task_inputs(self) -> None:
        assert quick_classify("create fibonacci function in fib.py") == "task"
        assert quick_classify("fix error in models.py") == "task"
        assert quick_classify("add unit tests for scheduler") == "task"
        assert quick_classify("def main(): pass") == "task"
        assert quick_classify("/plan build a full web app") == "unknown"
        assert quick_classify("refactor validation pipeline") == "task"


class TestStage2ClassifyInput:
    @patch("runtime.gate.llm_classify")
    def test_trivial_bypasses_llm(self, mock_llm_classify: MagicMock) -> None:
        """Trivial input must immediately return 'trivial' without calling Stage 2 LLM."""
        res = classify_input("hello", project_context="some context")
        assert res == "trivial"
        mock_llm_classify.assert_not_called()

    @patch("runtime.gate.llm_classify")
    def test_task_bypasses_llm(self, mock_llm_classify: MagicMock) -> None:
        """Explicit task input must immediately return 'task' without calling Stage 2 LLM."""
        res = classify_input("create fibonacci function in fib.py")
        assert res == "task"
        mock_llm_classify.assert_not_called()

    @patch("runtime.gate.llm_classify", return_value="task")
    def test_vague_triggers_llm(self, mock_llm_classify: MagicMock) -> None:
        """Ambiguous vague input must trigger llm_classify with query and project_context."""
        res = classify_input("fix it", project_context="fib.py with bug in main")
        assert res == "task"
        mock_llm_classify.assert_called_once_with("fix it", "fib.py with bug in main")


class TestLLMClassify:
    @patch("runtime.gate.chat", return_value="TASK")
    def test_llm_classify_returns_task(self, mock_chat: MagicMock) -> None:
        res = llm_classify("fix it", project_context="ctx")
        assert res == "task"
        mock_chat.assert_called_once()
        args, kwargs = mock_chat.call_args
        assert kwargs.get("temperature") == 0.0
        assert kwargs.get("max_tokens") == 1000
        assert kwargs.get("stop") == ["\n"]
        assert "ctx" in args[0][1]["content"]

    @patch("runtime.gate.chat", return_value="CHAT")
    def test_llm_classify_returns_chat(self, mock_chat: MagicMock) -> None:
        res = llm_classify("how are you doing today?", project_context="")
        assert res == "chat"

    @patch("runtime.gate.chat", return_value="VAGUE")
    def test_llm_classify_returns_vague(self, mock_chat: MagicMock) -> None:
        res = llm_classify("do something", project_context="")
        assert res == "vague"

    @patch("runtime.gate.chat", side_effect=RuntimeError("llama-server unavailable"))
    def test_llm_classify_fallback_on_error(self, mock_chat: MagicMock) -> None:
        """Exceptions in LLM call should gracefully fall back to 'task'."""
        res = llm_classify("fix it", project_context="")
        assert res == "task"

    @patch("runtime.gate.chat", return_value="UNEXPECTED_LABEL")
    def test_llm_classify_fallback_on_unexpected_output(self, mock_chat: MagicMock) -> None:
        """Unexpected LLM outputs should fall back to 'task'."""
        res = llm_classify("fix it", project_context="")
        assert res == "task"
