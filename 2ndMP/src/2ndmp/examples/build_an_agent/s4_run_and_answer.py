"""STEP 4 -- WE run the tool, then give the result back so the model can answer.

Four moves: ask -> run -> send the result back -> final answer. One round only (no loop yet).
"""
from llm import chat, question, strip_thinking
from s1_tool import cantilever_beam
from s2_describe import TOOLS

messages = [{"role": "user", "content": question()}]
reply = chat(messages, tools=TOOLS)                                   # 1. the model asks
call = reply.message.tool_calls[0]
print("model asks :", call.function.name, dict(call.function.arguments))

result = cantilever_beam(**call.function.arguments)                   # 2. WE run it
print("tool result:", result)

messages.append(reply.message)                                        # 3. hand the result back
messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})
final = chat(messages, tools=TOOLS)                                   # 4. the model answers
print("\nanswer:", strip_thinking(final.message.content))
