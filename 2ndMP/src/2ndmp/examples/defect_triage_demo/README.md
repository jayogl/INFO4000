# Defect report triage: single agent vs workflow vs multi-agent

One factory defect report. Same MCP tools, same model. Three ways to triage it, shown side by side in a Streamlit UI.

| | Who decides the steps? | What the model does |
|---|---|---|
| **Single agent** | the model | picks tools, order, and when to stop |
| **Workflow** | the code | reads the report into fields, writes the summary |
| **Multi-agent** | orchestrator code + each agent inside its step | Intake, Analyst, Triage Lead, Reviewer, each with its own prompt and tools |

## Setup (macOS and Windows)

1. Install [uv](https://docs.astral.sh/uv/) and [Ollama](https://ollama.com), then `ollama pull qwen3:4b`.
2. In this folder: `uv sync`
3. Start the UI: `uv run streamlit run app.py`

No Ollama? Pick **Rule-based stand-in (no LLM)** in the sidebar. It has no model: it follows the obvious steps with regexes so you can show the UI and the plumbing offline. It is not a demonstration of what a model does.

In the UI: every result carries a **RUN #n** banner (mode, report, backend, start time). If you change the sidebar after a run, a warning says the screen still shows the earlier run. **Clear screen** wipes all results and traces.

Terminal version: `uv run python cli.py --mode agent --report R-001 --backend ollama`
(`--mode agent|workflow|multi`, `--backend ollama|rules`, `--create` to approve and file the ticket)

Tests: `uv sync --group dev && uv run pytest`

## The tools (tools.py, plain Python, served by server.py over MCP)

| Tool | Purpose | Side effect |
|---|---|---|
| `lookup_part` | what the part is, safety critical?, owning team | none |
| `defect_stats` | defect rate for a lot | none |
| `find_similar` | same defect on the same line in the last 30 days (recurring?) | none |
| `severity_policy` | P1/P2/P3 and recommended action from fixed rules | none |
| `create_ticket` | files a ticket | **writes** |

No model is ever given `create_ticket`. Every mode ends with a **proposed** ticket; a person clicks **Approve** and the app calls it. The model proposes, a human approves, the write happens outside the model.

"Today" in the data is fixed at 2026-10-14, so results never change.

## Sample reports (each has an answer key)

| Id | What it teaches | Answer |
|---|---|---|
| R-001 | normal case, recurring defect | P2, SMT Process |
| R-002 | safety-critical part, small rate | P1, Power Electronics |
| R-003 | cosmetic, low rate | P3, Assembly |
| R-004 | high rate (5.3%) | P1, SMT Process |
| R-005 | rate under 1% but recurring | P2, SMT Process |
| R-006 | vague: no lot, no part | NEEDS_INFO (do not guess) |
| R-007 | part **not in the database** | P2, Triage Desk (unknown part is treated as safety critical) |

## What the audit panel checks

Computed from the trace, not from what the model says: evidence gathered, severity policy tool used, severity equals the policy result, and (for sample reports) severity and team match the answer key. A model that skips the policy tool or guesses a severity shows red crosses. The workflow and the multi-agent flow are built to avoid those failures, and that contrast is the lesson.

## Suggested class script

1. **R-001, Compare all three.** All reach P2. Count model calls: workflow uses 2, the others more. Open each trace and ask: who chose the next step?
2. **R-007 (unknown part).** The workflow has a coded rule for it. The agent has to remember the rule from its prompt. Watch the audit.
3. **R-006 (vague report).** Does each mode stop, or does it guess?
4. **Ablation.** Change one thing: the `severity_policy` docstring in tools.py, or `AGENT_SYS` in core.py, and rerun the agent only.
5. **Discuss.** More agents is not automatically better: the multi-agent run costs more model calls, and the Lead only sees what the orchestrator hands it (tool outputs, not the Analyst's prose, on purpose).

## Notes

* Structured outputs use Ollama's `format` JSON schema, so extraction and the final answers are valid JSON.
* The server also exposes `create_ticket` to any MCP client you connect (for example LM Studio, which asks for confirmation on each call).
* On Windows, if the UI says the model failed to start the server, run `uv run python server.py` once in a terminal to see the error.
* Tested with the stand-in on mcp 1.30 and 2.3 (37 tests, including the Streamlit app). **Not yet run against a real qwen3:4b**: expect the single agent to be the least reliable of the three, which is part of the lesson.
