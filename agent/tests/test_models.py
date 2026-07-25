from unittest.mock import MagicMock, patch

import httpx
import pytest
from respx import MockRouter

from runtime.models import chat, count_tokens, ensure_server, health_check


class TestChat:
    def test_chat_returns_assistant_content(self, respx_mock: MockRouter) -> None:
        respx_mock.post("http://localhost:8081/v1/chat/completions").respond(
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Hello! How can I help you?",
                        }
                    }
                ]
            }
        )
        messages = [{"role": "user", "content": "Hi"}]
        result = chat(messages)
        assert result == "Hello! How can I help you?"

    def test_chat_sends_correct_temperature(self, respx_mock: MockRouter) -> None:
        route = respx_mock.post("http://localhost:8081/v1/chat/completions").respond(
            json={"choices": [{"message": {"content": "Response"}}]}
        )
        messages = [{"role": "user", "content": "Test"}]
        chat(messages, temperature=0.7, max_tokens=1024)

        assert route.called
        last_request = route.calls.last.request
        import json

        data = json.loads(last_request.content)
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 1024
        assert data["messages"] == messages

    def test_chat_raises_http_status_error_on_500(self, respx_mock: MockRouter) -> None:
        respx_mock.post("http://localhost:8081/v1/chat/completions").respond(status_code=500)
        messages = [{"role": "user", "content": "Hi"}]
        with pytest.raises(httpx.HTTPStatusError):
            chat(messages)


class TestCountTokens:
    def test_count_tokens_empty_string(self) -> None:
        assert count_tokens("") == 0

    def test_count_tokens_400_chars(self) -> None:
        text = "a" * 400
        assert count_tokens(text) == 100


class TestHealthCheck:
    def test_health_check_returns_true_on_200(self, respx_mock: MockRouter) -> None:
        respx_mock.get("http://localhost:8081/health").respond(status_code=200)
        assert health_check() is True

    def test_health_check_returns_false_on_503(self, respx_mock: MockRouter) -> None:
        respx_mock.get("http://localhost:8081/health").respond(status_code=503)
        assert health_check() is False

    def test_health_check_returns_false_on_connect_error(self, respx_mock: MockRouter) -> None:
        respx_mock.get("http://localhost:8081/health").side_effect = httpx.ConnectError(
            "Connection refused"
        )
        assert health_check() is False


class TestEnsureServer:
    @patch("runtime.models.health_check")
    def test_ensure_server_already_running(self, mock_health: MagicMock) -> None:
        mock_health.return_value = True
        proc = ensure_server("dummy_path.gguf")
        assert proc is None

    @patch("runtime.models.subprocess.Popen")
    @patch("runtime.models.health_check")
    def test_ensure_server_launches_if_down(
        self, mock_health: MagicMock, mock_popen: MagicMock
    ) -> None:
        # First check returns False, second check returns True
        mock_health.side_effect = [False, True]
        dummy_proc = MagicMock()
        mock_popen.return_value = dummy_proc

        proc = ensure_server("dummy_path.gguf", port=8081, ctx_size=4096)

        assert proc == dummy_proc
        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]
        assert "llama-server" in cmd[0] or "llama-server.exe" in cmd[0]
        assert "-m" in cmd
        assert "dummy_path.gguf" in cmd
        assert "--port" in cmd
        assert "8081" in cmd
