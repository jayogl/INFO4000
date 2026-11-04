"""STEP 0 -- The model alone. Why do we need anything else?

Ask an engineering question with NO tools. Compare the answer with the hand calculation on the board.
"""
from llm import chat, question, strip_thinking

reply = chat([{"role": "user", "content": question()}])
print(strip_thinking(reply.message.content))
