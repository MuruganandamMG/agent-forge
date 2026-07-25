from unittest.mock import MagicMock, patch

from runtime.models import chat, count_tokens


class TestChat:
    @patch("runtime.models.genai.Client")
    def test_chat_returns_assistant_content(self, mock_client_class) -> None:
        mock_client_instance = mock_client_class.return_value
        mock_response = MagicMock()
        mock_response.text = "Hello! How can I help you?"
        mock_client_instance.models.generate_content.return_value = mock_response

        messages = [{"role": "user", "content": "Hi"}]
        result = chat(messages)
        
        assert result == "Hello! How can I help you?"
        mock_client_instance.models.generate_content.assert_called_once()

    @patch("runtime.models.genai.Client")
    def test_chat_sends_correct_parameters(self, mock_client_class) -> None:
        mock_client_instance = mock_client_class.return_value
        mock_response = MagicMock()
        mock_response.text = "Response"
        mock_client_instance.models.generate_content.return_value = mock_response

        messages = [{"role": "user", "content": "Test"}]
        chat(messages, temperature=0.7, max_tokens=1024, stop=["\n"])

        mock_client_instance.models.generate_content.assert_called_once()


class TestCountTokens:
    def test_count_tokens_empty_string(self) -> None:
        assert count_tokens("") == 0

    def test_count_tokens_400_chars(self) -> None:
        text = "a" * 400
        assert count_tokens(text) == 100
