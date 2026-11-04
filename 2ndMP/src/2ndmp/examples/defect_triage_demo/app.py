"""
app.py -- Streamlit UI: one defect report, three ways to triage it.

  uv run streamlit run app.py
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from core import OllamaBrain, RuleBrain, execute, file_ticket

st.set_page_config(page_title="Defect triage: agent vs workflow vs multi-agent", page_icon="🛠️", layout="wide")

REPORTS = json.loads((Path(__file__).parent / "data" / "reports.json").read_text(encoding="utf-8"))
BY_ID = {r["id"]: r for r in REPORTS}
MODES = {
    "agent": ("🤖 Single agent", "One model gets ALL the tools and decides what to look up, in what order, and when it is done.", "The model"),
    "workflow": ("🧭 Workflow", "Fixed steps in code. The model only reads the report and writes the summary.", "The code"),
    "multi": ("👥 Multi-agent", "An orchestrator hands work between role-limited agents: Intake, Analyst, Triage Lead, Reviewer.", "Code + each agent for its own step"),
}
CHOICES = {"Compare all three": ["agent", "workflow", "multi"], "Single agent": ["agent"], "Workflow": ["workflow"], "Multi-agent": ["multi"]}
SEV_COLOR = {"P1": "#D64545", "P2": "#E08A1E", "P3": "#5E9C3A", "NEEDS_INFO": "#7A7A7A", "FAILED": "#7A7A7A"}
ICON = {"step": "▶️", "handoff": "➡️", "llm": "🧠", "tool_call": "🔧", "tool_result": "📦", "gate": "🚦", "error": "⚠️"}

st.markdown("""<style>
.block-container{padding-top:2.2rem;max-width:1500px}
.sev{display:inline-block;padding:.15rem .8rem;border-radius:999px;color:white;font-weight:700;font-size:1.1rem}
.card{border:1px solid #e3e3e3;border-radius:12px;padding:.8rem 1rem;background:#fafafa;margin-bottom:.6rem}
.small{color:#6b6b6b;font-size:.85rem}
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=15)
def ollama_models():
    try:
        import ollama
        return sorted(m.model for m in ollama.Client(timeout=2).list().models)
    except Exception:
        return None


# ------------------------------------------------------------------ sidebar
models = ollama_models()
with st.sidebar:
    st.header("Setup")
    backend = st.radio("Model backend", ["Ollama (real LLM)", "Rule-based stand-in (no LLM)"], index=0 if models else 1, key="backend")
    if backend.startswith("Ollama"):
        if models:
            model = st.selectbox("Model", models, index=models.index("qwen3:4b") if "qwen3:4b" in models else 0, key="model")
        else:
            model = st.text_input("Model", "qwen3:4b", key="model")
            st.warning("Ollama is not reachable. Start it, or switch to the stand-in.")
    else:
        model = None
        st.info("The stand-in has no LLM. It follows the obvious steps with regexes so you can show the UI and the plumbing offline.")
    st.divider()
    choice = st.radio("What to run", list(CHOICES), key="mode")
    rid = st.selectbox("Sample report", [r["id"] for r in REPORTS], format_func=lambda i: f"{i} · {BY_ID[i]['title']}", key="report_id")
    st.caption("Edit the text below to try your own report.")
    text = st.text_area("Report", BY_ID[rid]["text"], height=170, key=f"text_{rid}")
    run_clicked = st.button("▶ Run", type="primary", use_container_width=True, key="run")
    reset_clicked = st.button("🧹 Clear screen", use_container_width=True, key="reset",
                              help="Remove all results and traces so the next run starts on a clean page")

# ------------------------------------------------------------------ header
st.title("🛠️ Defect report triage: three ways")
st.caption("Same report, same MCP tools, same model. What changes is **who decides the steps**.")
cols = st.columns(3)
for c, (k, (name, desc, who)) in zip(cols, MODES.items()):
    c.markdown(f"<div class='card'><b>{name}</b><br><span class='small'>{desc}</span><br><br>"
               f"<span class='small'>Who decides the flow:</span> <b>{who}</b></div>", unsafe_allow_html=True)
st.markdown(f"<div class='card'><span class='small'>SELECTED IN THE SIDEBAR: {rid if text == BY_ID[rid]['text'] else rid + ' (edited)'}</span><br>{text}</div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ rendering
def render_event(container, ev):
    with container:
        with st.container(border=True):
            st.markdown(f"{ICON.get(ev.kind, '·')} **{ev.actor}** <span class='small'>· {ev.t}s</span>", unsafe_allow_html=True)
            if ev.kind == "tool_result" and isinstance(ev.data, dict) and "error" in ev.data:
                st.warning(ev.data["error"], icon="⚠️")
            elif ev.kind == "tool_result":
                st.code(json.dumps(ev.data, indent=1), language="json", wrap_lines=True)
            elif ev.kind == "tool_call":
                st.code(ev.text, language="python", wrap_lines=True)
            else:
                st.markdown(ev.text if ev.kind != "llm" else f"<span class='small'>{ev.text}</span>", unsafe_allow_html=True)


def show_run(key, out, expand_trace=True):
    name = MODES[key][0]
    r, m = out["result"], out["metrics"]
    st.subheader(name)
    st.markdown(f"<span class='sev' style='background:{SEV_COLOR.get(r['severity'], '#7A7A7A')}'>{r['severity']}</span> &nbsp; "
                f"<b>{r['team']}</b>", unsafe_allow_html=True)
    st.markdown(f"**Action:** {r['action']}")
    st.markdown(f"<span class='small'>{r['summary']}</span>", unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.metric("Model calls", m["model_calls"]); b.metric("Tool calls", m["tool_calls"]); c.metric("Seconds", m["seconds"])
    st.markdown("**Audit** <span class='small'>(checked from the trace, not from what the model said)</span>", unsafe_allow_html=True)
    for label, ok in out["audit"]:
        st.markdown({True: "✅", False: "❌", None: "➖"}[ok] + f" {label}")
    # human-in-the-loop: the model proposes, a person approves, and only then is anything written
    tickets = st.session_state.setdefault("tickets", {})
    if r["ticket"]:
        if key in tickets:
            t = tickets[key]
            st.success(f"Ticket **{t.get('ticket_id', '?')}** created for {t.get('team')} ({t.get('severity')})")
        elif st.button("✅ Approve and create ticket", key=f"approve_{key}"):
            try:
                tickets[key] = asyncio.run(file_ticket(r["ticket"], st.session_state.get("report_id_run", "")))
                st.success(f"Ticket **{tickets[key].get('ticket_id', '?')}** created for {tickets[key].get('team')} ({tickets[key].get('severity')})")
            except Exception as e:
                st.error(f"Could not create the ticket: {e}")
        else:
            st.caption("🚦 Proposed ticket. Nothing is written until a person approves.")
    else:
        st.caption("🚦 No ticket: more information is needed first." if r["severity"] == "NEEDS_INFO" else "⚠️ No usable result.")
    with st.expander("Step-by-step trace", expanded=expand_trace):
        box = st.container()
        for ev in out["events"]:
            render_event(box, ev)


def compare_table(runs):
    rows = {}
    for k, out in runs.items():
        r, m = out["result"], out["metrics"]
        ok = [x for _, x in out["audit"] if x is not None]
        rows[MODES[k][0]] = {"Severity": r["severity"], "Team": r["team"], "Model calls": m["model_calls"],
                             "Tool calls": m["tool_calls"], "Seconds": m["seconds"],
                             "Audit passed": f"{sum(ok)}/{len(ok)}", "Who decided the flow": MODES[k][2]}
    st.subheader("Side by side")
    st.dataframe(pd.DataFrame(rows).T, use_container_width=True)


# ------------------------------------------------------------------ run / clear / show
def settings_now():
    return {"report": rid, "text": text, "choice": choice, "backend": backend, "model": model}


def banner(meta):
    where = f"{meta['backend'].split(' (')[0]}" + (f" · {meta['model']}" if meta["model"] else "")
    st.markdown(f"<div class='card' style='border-left:6px solid #2E8FC0'><b>RUN #{meta['n']}</b> &nbsp;·&nbsp; {meta['choice']} "
                f"&nbsp;·&nbsp; {meta['report']}{' (edited)' if meta['edited'] else ''} &nbsp;·&nbsp; {where} "
                f"&nbsp;·&nbsp; <span class='small'>started {meta['time']}</span></div>", unsafe_allow_html=True)


area = st.empty()          # everything below lives here, so it can be wiped in one go
if reset_clicked:
    st.session_state.runs, st.session_state.tickets, st.session_state.run_meta = {}, {}, None
    area.empty()

if run_clicked:
    area.empty()           # remove the previous run before drawing anything new
    n = st.session_state.get("run_count", 0) + 1
    st.session_state.run_count = n
    edited = text != BY_ID[rid]["text"]
    st.session_state.runs, st.session_state.tickets = {}, {}
    st.session_state.report_id_run = "custom" if edited else rid
    st.session_state.run_meta = {"n": n, "choice": choice, "report": rid, "edited": edited, "backend": backend, "model": model,
                                 "time": datetime.now().strftime("%H:%M:%S"), "settings": settings_now()}
    key_ans = None if edited else BY_ID[rid]["expected"]
    keys = CHOICES[choice]
    brain = OllamaBrain(model) if model else RuleBrain()
    failed = False
    with area.container():
        banner(st.session_state.run_meta)
        columns = st.columns(len(keys)) if len(keys) > 1 else [st.container()]
        for k, col in zip(keys, columns):
            with col:
                st.subheader(MODES[k][0])
                status = st.status("Running…", expanded=True)
            holder = status.container()
            try:
                st.session_state.runs[k] = asyncio.run(execute(k, text, brain, lambda ev, h=holder: render_event(h, ev), key_ans))
                status.update(label="Done", state="complete", expanded=False)
            except Exception as e:
                status.update(label="Failed", state="error")
                col.error(f"{type(e).__name__}: {e}. Is Ollama running and the model pulled?" if model else f"{type(e).__name__}: {e}")
                failed = True
    if not failed:
        st.rerun()
elif st.session_state.get("runs"):
    runs, meta = st.session_state.runs, st.session_state.run_meta
    with area.container():
        banner(meta)
        if meta["settings"] != settings_now():
            st.warning(f"The sidebar has changed since run #{meta['n']}. What is shown below is still run #{meta['n']}. "
                       "Press **Run** to update it, or **Clear screen** to start clean.", icon="⚠️")
        columns = st.columns(len(runs)) if len(runs) > 1 else [st.container()]
        for (k, out), col in zip(runs.items(), columns):
            with col:
                show_run(k, out, expand_trace=len(runs) == 1)
        if len(runs) > 1:
            compare_table(runs)
else:
    with area.container():
        st.info("Pick a report and a mode in the sidebar, then press **Run**. Try *Compare all three* on R-007 (a part that is not in the "
                "database) and R-006 (a vague report). Use **Clear screen** between runs.")
