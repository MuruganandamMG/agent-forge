from unittest.mock import patch

import pytest

from runtime.validate import ValidationResult, validate


class TestValidationResult:
    def test_passed_result(self) -> None:
        r = ValidationResult(
            passed=True,
            stage="all",
            errors="",
            details={"black": True, "ruff": True, "pytest": True},
        )
        assert r.passed is True
        assert r.stage == "all"

    def test_failed_result_shows_stage(self) -> None:
        r = ValidationResult(
            passed=False,
            stage="ruff",
            errors="E501 line too long",
            details={"black": True, "ruff": False},
        )
        assert r.passed is False
        assert r.stage == "ruff"
        assert "E501" in r.errors


class TestValidate:
    @patch("runtime.validate._run_tool")
    def test_all_pass(self, mock_run) -> None:
        mock_run.return_value = {"returncode": 0, "stdout": "", "stderr": ""}
        result = validate("/fake/project")
        assert result.passed is True
        assert result.details["black"] is True
        assert result.details["ruff"] is True
        assert result.details["pytest"] is True

    @patch("runtime.validate._run_tool")
    def test_black_fails_stops_pipeline(self, mock_run) -> None:
        mock_run.return_value = {
            "returncode": 1,
            "stdout": "would reformat file.py",
            "stderr": "",
        }
        result = validate("/fake/project")
        assert result.passed is False
        assert result.stage == "black"
        assert "would reformat" in result.errors

    @patch("runtime.validate._run_tool")
    def test_ruff_fails_after_black_passes(self, mock_run) -> None:
        def side_effect(cmd, cwd):
            if "black" in cmd:
                return {"returncode": 0, "stdout": "", "stderr": ""}
            return {"returncode": 1, "stdout": "E501 line too long", "stderr": ""}

        mock_run.side_effect = side_effect
        result = validate("/fake/project")
        assert result.passed is False
        assert result.stage == "ruff"
        assert result.details["black"] is True
        assert result.details["ruff"] is False

    @patch("runtime.validate._run_tool")
    def test_skip_pytest(self, mock_run) -> None:
        mock_run.return_value = {"returncode": 0, "stdout": "", "stderr": ""}
        result = validate("/fake/project", run_pytest=False)
        assert result.passed is True
        assert "pytest" not in result.details
        assert result.details["black"] is True
        assert result.details["ruff"] is True

    @patch("runtime.validate._run_tool")
    def test_pytest_fails(self, mock_run) -> None:
        def side_effect(cmd, cwd):
            if "pytest" in cmd:
                return {"returncode": 1, "stdout": "1 failed", "stderr": ""}
            return {"returncode": 0, "stdout": "", "stderr": ""}

        mock_run.side_effect = side_effect
        result = validate("/fake/project")
        assert result.passed is False
        assert result.stage == "pytest"
        assert "1 failed" in result.errors
