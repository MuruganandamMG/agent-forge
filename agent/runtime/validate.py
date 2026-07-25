"""Validation pipeline: black -> ruff -> pytest."""

import subprocess
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Result of running the validation pipeline."""

    passed: bool
    stage: str  # "all" if passed, or the name of the failing stage
    errors: str  # error output from the failing stage
    details: dict[str, bool] = field(default_factory=dict)


def _run_tool(cmd: str, cwd: str) -> dict:
    """Run a validation tool and return {returncode, stdout, stderr}."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=120,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timed out: {cmd}",
        }


# Ordered pipeline: each stage must pass before the next runs
PIPELINE = [
    ("black", "black --check ."),
    ("ruff", "ruff check ."),
    # ("pyright", "pyright ."),  # Uncomment when pyright is installed
]

PYTEST_STAGE = ("pytest", "pytest --tb=short -q")


def validate(project_dir: str, run_pytest: bool = True) -> ValidationResult:
    """Run the validation pipeline. Returns structured pass/fail."""
    details: dict[str, bool] = {}
    stages = list(PIPELINE)
    if run_pytest:
        stages.append(PYTEST_STAGE)

    for stage_name, cmd in stages:
        result = _run_tool(cmd, project_dir)
        passed = result["returncode"] == 0
        details[stage_name] = passed

        if not passed:
            error_text = result["stdout"] + "\n" + result["stderr"]
            return ValidationResult(
                passed=False,
                stage=stage_name,
                errors=error_text.strip(),
                details=details,
            )

    return ValidationResult(
        passed=True,
        stage="all",
        errors="",
        details=details,
    )
