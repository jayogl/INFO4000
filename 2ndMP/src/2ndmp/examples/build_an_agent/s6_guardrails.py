"""STEP 6 -- Guardrails. A loop with no limits is a bug waiting to happen.

Added to step 5: (1) a system prompt, (2) a maximum number of steps, (3) a registry of allowed tools,
(4) errors go BACK to the model as results, so it can fix its own mistake instead of crashing the program.
"""
from llm import chat, question, strip_thinking
from s1_tool import cantilever_beam
from s2_describe import TOOLS

SYSTEM = ("You are a mechanical-engineering assistant. Use the cantilever_beam tool for any beam calculation; "
          "never do the arithmetic yourself. Height is the section side in the direction of the load. "
          "Answer in two sentences with the numbers from the tool.")
ALLOWED = {"cantilever_beam": cantilever_beam}                        # (3) the ONLY things the model may run
MAX_STEPS = 5                                                         # (2)

messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question()}]   # (1)
for step in range(1, MAX_STEPS + 1):
    reply = chat(messages, tools=TOOLS)
    messages.append(reply.message)
    if not reply.message.tool_calls:
        print("\nanswer:", strip_thinking(reply.message.content))
        break
    for call in reply.message.tool_calls:
        name, args = call.function.name, dict(call.function.arguments)
        if name not in ALLOWED:
            result = {"error": f"there is no tool called '{name}'"}
        else:
            try:
                result = ALLOWED[name](**args)
            except TypeError as e:                                    # wrong or missing argument names
                result = {"error": f"wrong arguments for {name}: {e}"}
        print(f"step {step}:", name, args, "->", result)
        messages.append({"role": "tool", "tool_name": name, "content": str(result)})        # (4)
else:
    print(f"\nstopped: no answer after {MAX_STEPS} steps")
