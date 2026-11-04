"""STEP 5 -- The loop. THIS is the agent.

Same four moves as step 4, but repeated until the model stops asking for tools.
A model + a tool + a loop.
"""
from llm import chat, question, strip_thinking
from s1_tool import cantilever_beam
from s2_describe import TOOLS

messages = [{"role": "user", "content": question()}]
while True:
    reply = chat(messages, tools=TOOLS)
    messages.append(reply.message)
    if not reply.message.tool_calls:                                  # no more tool calls: it is done
        print("\nanswer:", strip_thinking(reply.message.content))
        break
    for call in reply.message.tool_calls:                             # it can ask more than once
        result = cantilever_beam(**call.function.arguments)
        print("tool:", call.function.name, dict(call.function.arguments), "->", result)
        messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})
