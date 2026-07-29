import os
from unittest.mock import patch, MagicMock
from runtime.providers.gemini_provider import GeminiProvider

@patch("runtime.providers.gemini_provider.genai.Client")
def test_gemini_provider_loads_env_key(mock_client_cls, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=test_api_key_from_env", encoding="utf-8")

    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key_from_env"}):
        provider = GeminiProvider()
        mock_client_cls.assert_called_with(api_key="test_api_key_from_env")
