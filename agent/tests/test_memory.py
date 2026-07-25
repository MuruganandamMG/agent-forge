import json
from unittest.mock import patch

import pytest

from runtime.memory import Memory


class TestStoreAndRetrieve:
    def test_store_session_returns_id(self, tmp_path) -> None:
        mem = Memory(str(tmp_path / "chroma_test"))
        doc_id = mem.store_session("fix the bug", "applied diff to models.py")
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0

    def test_retrieve_finds_stored_session(self, tmp_path) -> None:
        mem = Memory(str(tmp_path / "chroma_test"))
        mem.store_session("fix import cycle in auth.py", "moved types to schemas.py")
        results = mem.retrieve("import cycle", collection="sessions")
        assert len(results) >= 1
        assert "import cycle" in results[0]["document"]

    def test_retrieve_empty_collection_returns_empty(self, tmp_path) -> None:
        mem = Memory(str(tmp_path / "chroma_test"))
        results = mem.retrieve("anything", collection="sessions")
        assert results == []

    def test_store_reflection(self, tmp_path) -> None:
        mem = Memory(str(tmp_path / "chroma_test"))
        reflection = {
            "problem": "Import cycle",
            "cause": "auth.py imported models.py directly",
            "solution": "Moved shared types into schemas.py",
            "confidence": "high",
            "tags": ["python", "imports"],
        }
        doc_id = mem.store_reflection(reflection)
        assert isinstance(doc_id, str)

    def test_retrieve_reflection(self, tmp_path) -> None:
        mem = Memory(str(tmp_path / "chroma_test"))
        reflection = {
            "problem": "Import cycle",
            "cause": "auth.py imported models.py directly",
            "solution": "Moved shared types into schemas.py",
            "confidence": "high",
            "tags": ["python", "imports"],
        }
        mem.store_reflection(reflection)
        results = mem.retrieve("import cycle", collection="reflections")
        assert len(results) >= 1

    def test_unknown_collection_raises(self, tmp_path) -> None:
        mem = Memory(str(tmp_path / "chroma_test"))
        with pytest.raises(ValueError, match="Unknown collection"):
            mem.retrieve("query", collection="nonexistent")


class TestReflect:
    @patch("runtime.memory.chat")
    def test_reflect_generates_and_stores(self, mock_chat, tmp_path) -> None:
        mock_chat.return_value = json.dumps({
            "problem": "Missing return type",
            "cause": "Function had no annotation",
            "solution": "Added -> str return type",
            "confidence": "high",
            "tags": ["python", "typing"],
        })
        mem = Memory(str(tmp_path / "chroma_test"))
        result = mem.reflect("add return type to foo()", "applied diff")
        assert result["problem"] == "Missing return type"
        assert result["confidence"] == "high"

    @patch("runtime.memory.chat")
    def test_reflect_handles_invalid_json(self, mock_chat, tmp_path) -> None:
        mock_chat.return_value = "not valid json response"
        mem = Memory(str(tmp_path / "chroma_test"))
        result = mem.reflect("some task", "some result")
        # Should gracefully fall back
        assert result["confidence"] == "low"
        assert result["problem"] == "some task"
