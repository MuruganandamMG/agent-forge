import traceback
from runtime.models import chat

messages = [
    {"role": "system", "content": "You are a test."},
    {"role": "user", "content": "hello"}
]

try:
    res = chat(messages)
    print(f"RAW RESULT: '{res}'")
except Exception as e:
    print("EXCEPTION CAUGHT IN SCRIPT:")
    traceback.print_exc()
