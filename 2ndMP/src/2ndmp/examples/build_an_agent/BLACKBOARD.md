# Blackboard script (about 60 minutes)

**Set up before class:** `uv sync`, the model pulled, a terminal and an editor side by side.
**The one rule to repeat:** *the model never runs anything. It asks. Our code runs.*

Hand calculation first, on the board, so students own the right answer:

```
I     = b h^3 / 12 = 20 * 10^3 / 12 = 1667 mm^4
delta = P L^3 / (3 E I) = 100 * 300^3 / (3 * 200 000 * 1667) = 2.7 mm      (E = 200 GPa = 200 000 N/mm^2)
sigma = 6 P L / (b h^2) = 6 * 100 * 300 / (20 * 100) = 90 MPa
SF    = 250 / 90 = 2.78
```

---

## Step 0 · The model alone · `s0_model_alone.py` · 5 min
**Draw:** a box "MODEL" with an arrow in (question) and an arrow out (text).
**Run:** the file. **Say:** "It sounds sure. Is it right? Compare with the board." The number will usually be wrong or unexplained.
**Ask:** change one word in the question (say 12 mm instead of 10 mm) and run again. Does the answer change sensibly? (A model estimates; it does not calculate. We set temperature 0, so the same question gives the same answer, but that does not make it right.)
**Takeaway:** fluent is not correct.

## Step 1 · The tool · `s1_tool.py` · 10 min
**Draw:** a box "TOOL = Python function" below the model. Write the three formulas next to it.
**Type:** the function, one formula at a time. **Say:** "No AI in this file." **Run:** `python s1_tool.py` and match 2.7 / 90 / 2.78.
**Ask:** what happens if h and b are swapped? (Run it: 0.675 mm. The beam on its side is 4x stiffer: h is cubed.) That is why the docstring says what height means.
**Takeaway:** a tool is a function you can test without a model. Return numbers, not sentences.

## Step 2 · Describe it · `s2_describe.py` · 8 min
**Draw:** a restaurant menu: *name · what it does · what to give it*.
**Say:** "The model has never seen your code. This is all it knows." Run it and read the JSON out loud.
**Ask:** which line would you change if the model keeps passing millimetres as metres? (The argument descriptions.)
**Takeaway:** the description is the interface. Most tool problems are description problems.

## Step 3 · The model asks · `s3_model_asks.py` · 7 min
**Draw:** an arrow from MODEL to the board labelled `tool_calls: cantilever_beam(...)`. Put a big **no** where the tool would run.
**Run:** show `tool_calls` and the empty `content`. **Ask:** did anything calculate yet? (No. A request only.)
**Takeaway:** "tool use" is the model returning structured data.

## Step 4 · Run it and answer · `s4_run_and_answer.py` · 10 min
**Draw:** the four moves in a circle: ask → run → hand back → answer.
**Type:** the four moves. **Run:** compare the tool result with the board, then read the final answer.
**Ask:** where did the number in the answer come from? (From the tool result we handed back.)
**Takeaway:** the result goes back into the conversation as a `tool` message.

## Step 5 · The loop · `s5_agent_loop.py` · 10 min
**Draw:** put an arrow from "answer" back to "ask" and write **while**.
**Type:** the loop (about 10 lines). **Run** the default question, then:
`uv run python s5_agent_loop.py "Compare steel and aluminum for this beam."`: two tool calls in one run.
**Say:** "This is an agent: a model, a tool and a loop."
**Takeaway:** the loop is what lets it try, look, and try again.

## Step 6 · Guardrails · `s6_guardrails.py` · 8 min
**Draw:** a fence around the loop with four labels: *system prompt · max steps · allowed tools · errors go back*.
**Type:** the four additions. **Try to break it:**
- `"What is the capital of France?"`: no tool, and it should just answer.
- `"Use the beam tool for a wooden beam."`: the tool returns an error and the model has to explain.
- Set `MAX_STEPS = 1` and ask the compare question: watch it stop.
**Ask:** why do we send errors back as tool results instead of crashing? (It lets the model correct itself.)
**Takeaway:** the model proposes, our code decides what is allowed.

## Step 7 · Share it (bonus) · `s7_mcp_server.py` · 5 min
**Draw:** the TOOL box with a plug on its side and three apps (our script, LM Studio, Claude Desktop) plugging into it.
**Run:** `uv run mcp dev s7_mcp_server.py` and call the tool from the inspector, with no model at all.
**Takeaway:** the function did not change. MCP only changes who can use it.

---

### If it goes wrong in front of the class
- **The model answers without calling the tool:** run `ollama show <model>` and check for `tools`. Or try `MODEL=qwen3:8b`. Then say: "this is exactly why Step 6 exists."
- **Wrong argument names:** Step 6 shows the error going back. Let the model fix it, and point it out.
- **Slow:** the first call loads the model into memory. The second is fast.
- **Numbers differ from the board:** that is the tool's number, not the model's. The tool is the source of truth.

### Extensions
Add a second tool (a material lookup); add a deflection limit and ask for the lightest beam that passes (now the loop has to search); build the same thing as a workflow where code fixes the order.
