import pytest
from agent.runtime.ui import format_context_gauge, UIManager, ui_manager

def test_format_context_gauge_green():
    result = format_context_gauge(used_tokens=10000, limit_tokens=100000, width=10)
    assert "10.0%" in result
    assert "10,000 / 100,000 tokens" in result

def test_format_context_gauge_yellow():
    result = format_context_gauge(used_tokens=60000, limit_tokens=100000, width=10)
    assert "60.0%" in result

def test_format_context_gauge_red():
    result = format_context_gauge(used_tokens=90000, limit_tokens=100000, width=10)
    assert "90.0%" in result

def test_ui_manager_telemetry():
    ui = UIManager()
    ui.add_tokens(5000)
    assert ui.total_tokens == 5000
    ui.add_tokens(3000)
    assert ui.total_tokens == 8000
    ui.reset_telemetry()
    assert ui.total_tokens == 0
