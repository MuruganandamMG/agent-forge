from dotenv import load_dotenv
load_dotenv()

import json
from runtime.models import chat
history = [
    {
      "role": "user",
      "content": "man"
    },
    {
      "role": "assistant",
      "content": ""
    },
    {
      "role": "user",
      "content": "what;;s up"
    },
    {
      "role": "assistant",
      "content": ""
    },
    {
        "role": "user",
        "content": "hello"
    }
  ]

res = chat(history)
print(f"Response: '{res}'")
