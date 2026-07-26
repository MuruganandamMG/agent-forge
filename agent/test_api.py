from runtime.chat_responder import generate_chat_response
from dotenv import load_dotenv

load_dotenv()

res = generate_chat_response("hello", [], "Context")
print(f"Response: '{res}'")
