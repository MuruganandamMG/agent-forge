"""Tests for the request enricher module."""

from unittest.mock import patch

from runtime.enricher import enrich_request


class TestEnrichRequest:
    @patch("runtime.enricher.chat")
    def test_enrich_request_returns_enriched_string(self, mock_chat) -> None:
        mock_chat.return_value = (
            "Files: main.py\n"
            "Related: utils.py\n"
            "Context: Main application entry point."
        )
        raw_query = "Fix bug in main"
        project_ctx = "main.py\nutils.py"

        result = enrich_request(raw_query, project_ctx)

        assert raw_query in result
        assert "--- Enrichment ---" in result
        assert "Files: main.py" in result
        mock_chat.assert_called_once()
        _, kwargs = mock_chat.call_args
        assert kwargs.get("temperature") == 0.1
        assert kwargs.get("max_tokens") == 2000
        assert kwargs.get("stop") == ["<|im_end|>"]

    @patch("runtime.enricher.chat")
    def test_enrich_request_handles_exception_gracefully(self, mock_chat) -> None:
        mock_chat.side_effect = Exception("Connection refused")
        raw_query = "Add feature X"
        project_ctx = "app.py"

        result = enrich_request(raw_query, project_ctx)

        assert result == raw_query

    @patch("runtime.enricher.chat")
    def test_enrich_request_empty_project_context(self, mock_chat) -> None:
        mock_chat.return_value = (
            "Files: none\n"
            "Related: none\n"
            "Context: Empty project context."
        )
        raw_query = "Create new module"
        project_ctx = ""

        result = enrich_request(raw_query, project_ctx)

        assert raw_query in result
        assert "--- Enrichment ---" in result
        assert "Files: none" in result
        mock_chat.assert_called_once()

    @patch("runtime.enricher.chat")
    def test_enrich_request_with_memory_context(self, mock_chat) -> None:
        mock_chat.return_value = "Files: helper.py"
        raw_query = "Do something"
        project_ctx = "helper.py"
        memory_ctx = "Previous session built helper.py"

        result = enrich_request(raw_query, project_ctx, memory_context=memory_ctx)

        assert raw_query in result
        assert "--- Enrichment ---" in result
        _, kwargs = mock_chat.call_args
        messages = kwargs["messages"]
        user_msg = messages[1]["content"]
        assert "Recent session context: Previous session built helper.py" in user_msg
