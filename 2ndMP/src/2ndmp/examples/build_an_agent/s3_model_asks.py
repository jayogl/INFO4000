"""STEP 3 -- The model ASKS for the tool. Nothing runs yet.

Send the question and the tool description. If the model decides it needs the tool, the reply has
tool_calls instead of an answer: a name and arguments, as data. That is all "tool use" is.
"""
from llm import chat, question
from s2_describe import TOOLS

reply = chat([{"role": "user", "content": question()}], tools=TOOLS)
print("tool_calls:", reply.message.tool_calls)
print("content   :", reply.message.content)
