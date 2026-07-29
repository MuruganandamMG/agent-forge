from cli.tui import handle_slash_command

def test_chat_slash_command_integration():
    handled, res = handle_slash_command("/help")
    assert handled is True
    assert "Available Slash Commands" in res
