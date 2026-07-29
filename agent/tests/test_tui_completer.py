from cli.tui import get_slash_completer

def test_get_slash_completer():
    completer = get_slash_completer()
    words = completer.words
    assert "/plan" in words
    assert "/status" in words
    assert "/help" in words
