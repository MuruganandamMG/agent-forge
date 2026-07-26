import pytest
from runtime.ui import print_banner, print_error, print_success, print_markdown, print_diff

def test_ui_functions_exist():
    # Just checking they don't raise exceptions when called
    try:
        print_banner("Test", "path", 10)
        print_error("Error")
        print_success("Success")
        print_markdown("# Markdown")
        print_diff("--- a/file\n+++ b/file\n@@ -1 +1 @@\n-old\n+new")
    except Exception as e:
        pytest.fail(f"UI functions raised exception: {e}")
