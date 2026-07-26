import traceback
from runtime.chat_responder import generate_chat_response

try:
    res = generate_chat_response("hello", [], "Context")
    print(f"RAW RESULT: '{res}'")
except Exception as e:
    print("EXCEPTION BUBBLED OUT:")
    traceback.print_exc()
