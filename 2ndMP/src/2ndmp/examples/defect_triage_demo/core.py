"""
core.py -- three ways to triage the SAME defect report with the SAME tools.

  run_agent     one model, all tools; THE MODEL decides what to do and in what order
  run_workflow  fixed steps in code; the model only reads the report and writes the summary
  run_multi     an orchestrator (code) hands work between role-limited agents:
                Intake -> Analyst -> Triage Lead -> Reviewer

Every run records an event trace (what the UI shows) and an audit of the result.
Two "brains" can sit behind every model call: OllamaBrain (real LLM) and RuleBrain
(a deterministic stand-in with NO LLM, for demos without a model and for tests).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from tools import DEFECT_CODES

HERE = Path(__file__).parent
SEVERITIES = ["P1", "P2", "P3", "NEEDS_INFO"]

# ------------------------------------------------------------------ prompts & schemas
CODE_HELP = ("SOLDER_BRIDGE (solder joins two pads), TOMBSTONE (part stands up on one end), "
             "MISSING_COMP (part not placed), COLD_JOINT (dull or weak joint), "
             "WRONG_POLARITY (part installed backwards), COSMETIC_SCRATCH (surface scratch)")
EXTRACT_SYS = ("You read a factory defect report and extract fields. Reply with JSON only. "
               "line: the production line number (0 if not stated). lot: the lot id such as L-2231 ('UNKNOWN' if not stated). "
               "part: the reference designator such as U7 ('UNKNOWN' if not stated). "
               f"defect_code: one of {CODE_HELP}; 'UNKNOWN' if the report does not say. "
               "count: number of boards or units affected (0 if not stated). Never guess.")
EXTRACT_SCHEMA = {"type": "object", "required": ["line", "lot", "part", "defect_code", "count"], "properties": {
    "line": {"type": "integer"}, "lot": {"type": "string"}, "part": {"type": "string"},
    "defect_code": {"type": "string", "enum": DEFECT_CODES + ["UNKNOWN"]}, "count": {"type": "integer"}}}
FINAL_SCHEMA = {"type": "object", "required": ["severity", "team", "recommended_action", "summary"], "properties": {
    "severity": {"type": "string", "enum": SEVERITIES}, "team": {"type": "string"},
    "recommended_action": {"type": "string"}, "summary": {"type": "string"}}}
SUMMARY_SCHEMA = {"type": "object", "required": ["summary"], "properties": {"summary": {"type": "string"}}}
REVIEW_SCHEMA = {"type": "object", "required": ["verdict", "reason"], "properties": {
    "verdict": {"type": "string", "enum": ["APPROVE", "REVISE"]}, "reason": {"type": "string"}}}
FINAL_ASK = ("Now give the triage result as JSON. severity: the severity_policy result, or NEEDS_INFO if the report "
             "lacks a lot or defect. team: the part's owner_team, or 'Triage Desk' if the part is unknown. "
             "recommended_action: from the policy. summary: two sentences with the key numbers.")

AGENT_SYS = ("You are a defect-triage agent at an electronics factory. Read the report, then use the tools to gather "
             "evidence: lookup_part (part facts), defect_stats (lot defect rate; pass defect_code), find_similar "
             "(earlier lots on the same line; pass exclude_lot). Then call severity_policy with the numbers you found. "
             "Typical order: lookup_part, defect_stats, find_similar, severity_policy. Each tool takes DIFFERENT arguments: "
             "read each tool's argument names carefully. Never choose severity yourself and never invent numbers. If the report does not say which lot or which "
             "defect, do not guess: do not call tools. If a part is not in the database, treat it as safety critical. "
             "When you are done gathering and applying the policy, say 'ready'.")
INTAKE_SYS = "You are the INTAKE agent. " + EXTRACT_SYS
ANALYST_SYS = ("You are the ANALYST agent. Collect evidence for a defect report with the tools: lookup_part, "
               "defect_stats (pass lot_id and defect_code), find_similar (pass defect_code, line and exclude_lot). "
               "Call each once, then reply with a three-line evidence summary quoting the numbers. "
               "Do not assign severity.")
LEAD_SYS = ("You are the TRIAGE LEAD agent. You are given the extracted fields and the evidence. Call severity_policy "
            "with defect_code, defect_rate_pct, safety_critical and recurring from the evidence (use the lines given). Never choose severity yourself. "
            "If the part is unknown, treat it as safety critical.")
REVIEWER_SYS = ("You are the REVIEWER agent. You do not use tools. Check the proposed triage against the evidence: "
                "does the severity equal the policy result, is the team the part's owner (or 'Triage Desk' if the part "
                "is unknown), and does the summary match the numbers? Reply APPROVE or REVISE with a short reason.")
SUMMARY_SYS = ("Write a two-sentence summary of this defect triage for the engineer on duty. "
               "Use only the facts given. Reply as JSON.")

# ------------------------------------------------------------------ helpers
def strip_thinking(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    if "</think>" in text:
        text = text.split("</think>")[-1]
    return text.replace("<think>", "").strip()


def parse_json(text: str):
    text = strip_thinking(text)
    try:
        return json.loads(text)
    except ValueError:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except ValueError:
                pass
    return None


def result_text(result) -> str:
    return "\n".join(getattr(c, "text", str(c)) for c in result.content)


def mcp_tool_to_ollama(tool) -> dict:
    return {"type": "function", "function": {"name": tool.name, "description": tool.description or "",
            "parameters": getattr(tool, "input_schema", None) or tool.inputSchema}}


def kv_block(d: dict) -> str:
    return "\n".join(f"{k}: {str(v).lower() if isinstance(v, bool) else v}" for k, v in d.items())


@asynccontextmanager
async def connect():
    """Start server.py as a subprocess and open an MCP session (same Python env)."""
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


# ------------------------------------------------------------------ brains
class OllamaBrain:
    name = "ollama"

    def __init__(self, model: str):
        import ollama
        self.ollama, self.model, self.client = ollama, model, ollama.AsyncClient()

    async def chat(self, messages, tools=None, schema=None) -> dict:
        kw = dict(model=self.model, messages=messages, options={"temperature": 0, "num_ctx": 8192})
        if tools:
            kw["tools"] = tools
        if schema:
            kw["format"] = schema
        try:
            resp = await self.client.chat(**kw, think=False)
        except (TypeError, self.ollama.ResponseError) as e:
            if isinstance(e, self.ollama.ResponseError) and "think" not in str(e).lower():
                raise
            resp = await self.client.chat(**kw)
        m = resp.message
        return {"content": strip_thinking(m.content or ""),
                "tool_calls": [(tc.function.name, dict(tc.function.arguments)) for tc in (m.tool_calls or [])]}


_CODE_WORDS = [("bridge", "SOLDER_BRIDGE"), ("tombston", "TOMBSTONE"), ("cold", "COLD_JOINT"), ("skipped", "MISSING_COMP"),
               ("missing", "MISSING_COMP"), ("bare", "MISSING_COMP"), ("backward", "WRONG_POLARITY"),
               ("polarity", "WRONG_POLARITY"), ("scratch", "COSMETIC_SCRATCH")]


def regex_extract(text: str) -> dict:
    line = re.search(r"[Ll]ine\s+(\d+)", text)
    lot = re.search(r"\bL-\d{4}\b", text)
    part = re.search(r"\b[UQHCDJ]\d{1,2}\b", text)
    cnt = re.search(r"\b(\d+)\s+(?:boards|enclosures|units)\b", text)
    low = text.lower()
    code = next((c for w, c in _CODE_WORDS if w in low), "UNKNOWN")
    return {"line": int(line.group(1)) if line else 0, "lot": lot.group(0) if lot else "UNKNOWN",
            "part": part.group(0) if part else "UNKNOWN", "defect_code": code, "count": int(cnt.group(1)) if cnt else 0}


def parse_kv(text: str) -> dict:
    out = {}
    for k, v in re.findall(r"^(\w+):\s*(.+)$", text, flags=re.M):
        v = v.strip()
        out[k] = {"true": True, "false": False}.get(v.lower(), v)
    return out


class RuleBrain:
    """Deterministic stand-in for a model: NO LLM. It follows the obvious steps with regexes and the
    tool results it sees, so the UI and the tests work without Ollama. It shows the plumbing, not intelligence."""
    name = "rules"
    ORDER = ["lookup_part", "defect_stats", "find_similar", "severity_policy"]

    async def chat(self, messages, tools=None, schema=None) -> dict:
        first = next((m["content"] for m in messages if m["role"] == "user"), "")
        facts = parse_kv(first)
        if "lot" not in facts:
            facts = {**regex_extract(first), **facts}
        results = {m["tool_name"]: json.loads(m["content"]) for m in messages if m["role"] == "tool"
                   if not str(json.loads(m["content"]).get("error", "")).startswith("Wrong arguments")}
        props = (schema or {}).get("properties", {})
        known = facts.get("lot", "UNKNOWN") != "UNKNOWN" and facts.get("defect_code", "UNKNOWN") != "UNKNOWN"

        if "defect_code" in props:
            return {"content": json.dumps(regex_extract(first)), "tool_calls": []}
        if "verdict" in props:
            return {"content": json.dumps({"verdict": "APPROVE", "reason": "Severity follows the policy result and the team is the part owner."}), "tool_calls": []}
        if "recommended_action" in props:
            return {"content": json.dumps(self._final(facts, results, known)), "tool_calls": []}
        if "summary" in props:
            return {"content": json.dumps({"summary": self._summary(facts)}), "tool_calls": []}
        if tools:
            if not known:
                return {"content": "The report does not say which lot or defect; I need more information.", "tool_calls": []}
            names = [t["function"]["name"] for t in tools]
            for n in self.ORDER:
                if n in names and n not in results:
                    return {"content": "", "tool_calls": [(n, self._args(n, facts, results))]}
            return {"content": "ready", "tool_calls": []}
        return {"content": "ok", "tool_calls": []}

    @staticmethod
    def _part_ok(results):
        p = results.get("lookup_part")
        return p if p and "error" not in p else None

    def _args(self, name, facts, results):
        if name == "lookup_part":
            return {"part_id": facts["part"]}
        if name == "defect_stats":
            return {"lot_id": facts["lot"], "defect_code": facts["defect_code"]}
        if name == "find_similar":
            return {"defect_code": facts["defect_code"], "line": int(facts["line"]), "exclude_lot": facts["lot"]}
        st, sim, part = results.get("defect_stats"), results.get("find_similar"), results.get("lookup_part")
        rate = st["defect_rate_pct"] if st and "error" not in st else float(facts.get("defect_rate_pct", 0))
        crit = part["safety_critical"] if part and "error" not in part else (True if part else bool(facts.get("safety_critical", True)))
        rec = sim["recurring"] if sim else bool(facts.get("recurring", False))
        return {"defect_code": facts["defect_code"], "defect_rate_pct": rate, "safety_critical": crit, "recurring": rec}

    def _final(self, facts, results, known):
        if not known:
            return {"severity": "NEEDS_INFO", "team": "Triage Desk", "recommended_action": "Ask the reporter for the lot, part and defect type",
                    "summary": "The report does not identify the lot or the defect, so it cannot be triaged yet."}
        pol = results.get("severity_policy") or {}
        part = self._part_ok(results)
        team = part["owner_team"] if part else facts.get("owner_team", "Triage Desk")
        st = results.get("defect_stats") or {}
        return {"severity": pol.get("severity", "NEEDS_INFO"), "team": team,
                "recommended_action": pol.get("recommended_action", "n/a"),
                "summary": f"{facts.get('defect_code')} on {facts.get('part')} in lot {facts.get('lot')}: "
                           f"{st.get('defect_rate_pct', facts.get('defect_rate_pct', '?'))}% defect rate. Policy rule: {pol.get('rule', 'n/a')}."}

    def _summary(self, f):
        return (f"{f.get('defect_code')} on {f.get('part')} in lot {f.get('lot')} at {f.get('defect_rate_pct')}% defect rate, "
                f"{f.get('previous_lots')} similar earlier lot(s). Severity {f.get('severity')} because {f.get('rule')}.")


# ------------------------------------------------------------------ run + trace
@dataclass
class Event:
    kind: str      # step | handoff | llm | tool_call | tool_result | gate | error
    actor: str
    text: str
    data: object = None
    t: float = 0.0


class Run:
    def __init__(self, session, brain, on_event=None):
        self.session, self.brain, self.on_event = session, brain, on_event
        self.events, self.tool_log, self.model_calls, self.t0 = [], [], 0, time.time()
        self._specs = None

    def emit(self, kind, actor, text, data=None):
        ev = Event(kind, actor, text, data, round(time.time() - self.t0, 1))
        self.events.append(ev)
        if self.on_event:
            self.on_event(ev)

    async def specs(self, names):
        if self._specs is None:
            self._specs = [mcp_tool_to_ollama(t) for t in (await self.session.list_tools()).tools]
        return [s for s in self._specs if s["function"]["name"] in names]

    async def call_tool(self, actor, name, args):
        self.emit("tool_call", actor, f"{name}({', '.join(f'{k}={v!r}' for k, v in args.items())})", args)
        data = await self._validate(name, args)
        if data is None:
            try:
                res = await self.session.call_tool(name, args)
                text = result_text(res)
                data = parse_json(text) or {"raw": text}
                if getattr(res, "is_error", False) or getattr(res, "isError", False):
                    data = {"error": f"The tool failed: {text[:300]}"}
            except Exception as e:                  # bad name / bad arguments: tell the model, do not crash
                data = {"error": f"The tool failed: {e}"}
        self.tool_log.append({"actor": actor, "name": name, "args": args, "result": data})
        self.emit("tool_result", actor, json.dumps(data), data)
        return data

    async def _validate(self, name, args):
        """Check the model's arguments against the tool's own schema. A small model often mixes up
        argument names; a short, specific error lets it fix the call instead of a pydantic dump."""
        await self.specs(())
        spec = next((s for s in self._specs if s["function"]["name"] == name), None)
        if spec is None:
            return {"error": f"There is no tool called '{name}'."}
        sch = spec["function"]["parameters"] or {}
        props, req = set(sch.get("properties", {})), sch.get("required", [])
        missing, extra = [k for k in req if k not in args], [k for k in args if k not in props]
        if missing or extra:
            return {"error": f"Wrong arguments for {name}. Missing: {missing or 'none'}. Not accepted: {extra or 'none'}. "
                             f"{name} takes: {sorted(props)} (required: {req})."}
        return None

    async def _chat(self, actor, msgs, specs=None, schema=None):
        self.model_calls += 1
        m = await self.brain.chat(msgs, tools=specs, schema=schema)
        if m["tool_calls"]:
            self.emit("llm", actor, "decides to call: " + ", ".join(n for n, _ in m["tool_calls"]))
        else:
            self.emit("llm", actor, (m["content"] or "(empty)")[:300])
        return m

    async def ask(self, actor, system, user, *, tool_names=None, schema=None, final_ask="Reply with the JSON only.", max_steps=8):
        """One agent turn: optional tool loop, then optional structured (JSON) answer. Returns (text, parsed_json)."""
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        text = ""
        if tool_names:
            specs = await self.specs(tool_names)
            for _ in range(max_steps):
                m = await self._chat(actor, msgs, specs=specs)
                if not m["tool_calls"]:
                    text = m["content"]
                    break
                msgs.append({"role": "assistant", "content": m["content"],
                             "tool_calls": [{"function": {"name": n, "arguments": a}} for n, a in m["tool_calls"]]})
                for n, a in m["tool_calls"]:
                    msgs.append({"role": "tool", "tool_name": n, "content": json.dumps(await self.call_tool(actor, n, a))})
            else:
                text = "(stopped: too many tool steps)"
                self.emit("error", actor, text)
        if not schema:
            if not tool_names:
                text = (await self._chat(actor, msgs))["content"]
            return text, None
        if tool_names:
            msgs += [{"role": "assistant", "content": text or "ready"}, {"role": "user", "content": final_ask}]
        m = await self._chat(actor, msgs, schema=schema)
        parsed = parse_json(m["content"])
        if parsed is None:
            self.emit("error", actor, "the model did not return valid JSON")
        return text, parsed

    def metrics(self):
        return {"model_calls": self.model_calls, "tool_calls": len(self.tool_log), "seconds": round(time.time() - self.t0, 1)}


# ------------------------------------------------------------------ result + audit
def needs_info(f) -> bool:
    return not f or f.get("lot", "UNKNOWN") == "UNKNOWN" or f.get("defect_code", "UNKNOWN") == "UNKNOWN"


def make_result(mode, fields, prop, note=""):
    prop = prop or {}
    sev = prop.get("severity", "FAILED")
    r = {"mode": mode, "fields": fields, "severity": sev, "team": prop.get("team", "?"),
         "action": prop.get("recommended_action", "?"), "summary": prop.get("summary", ""), "note": note}
    r["ticket"] = {"team": r["team"], "severity": sev, "summary": f"{r['action']}. {r['summary']}"} if sev in ("P1", "P2", "P3") else None
    return r


def needs_info_result(mode, fields):
    return make_result(mode, fields, {"severity": "NEEDS_INFO", "team": "Triage Desk",
                                      "recommended_action": "Ask the reporter for the lot, part and defect type",
                                      "summary": "The report does not identify the lot or the defect, so it cannot be triaged yet."})


def audit(result, tool_log, key=None):
    """Checks computed from the trace. (label, True | False | None)."""
    names = [c["name"] for c in tool_log]
    pol = next((c["result"] for c in reversed(tool_log) if c["name"] == "severity_policy" and "error" not in c["result"]), None)
    checks = []
    if result["severity"] == "NEEDS_INFO":
        checks.append(("Asked for more information instead of guessing", True))
    else:
        checks.append(("Gathered evidence: part, lot stats, history", all(n in names for n in ("lookup_part", "defect_stats", "find_similar"))))
        checks.append(("Used the severity policy tool", pol is not None))
        checks.append(("Severity equals the policy result", None if pol is None else pol.get("severity") == result["severity"]))
    if key:
        checks.append(("Severity matches the answer key", result["severity"] == key["severity"]))
        checks.append(("Team matches the answer key", result["team"].strip().lower() == key["team"].strip().lower()))
    return checks


# ------------------------------------------------------------------ the three modes
async def run_agent(run: Run, report: str) -> dict:
    run.emit("step", "Agent", "One model gets the report and ALL read-only tools. It decides what to do next.")
    _, prop = await run.ask("Agent", AGENT_SYS, report, tool_names={"lookup_part", "defect_stats", "find_similar", "severity_policy"},
                            schema=FINAL_SCHEMA, final_ask=FINAL_ASK)
    return make_result("agent", None, prop)


async def run_workflow(run: Run, report: str) -> dict:
    run.emit("step", "Step 1 · Extract", "LLM reads the report into fields (JSON schema).")
    _, f = await run.ask("Step 1 · Extract (LLM)", EXTRACT_SYS, report, schema=EXTRACT_SCHEMA)
    if f is None or needs_info(f):
        run.emit("gate", "Code", "Lot or defect missing → stop here and ask the reporter. No guessing.")
        return needs_info_result("workflow", f)
    run.emit("step", "Step 2 · Evidence", "CODE calls the three evidence tools. The model is not involved.")
    part = await run.call_tool("Step 2 · Evidence (code)", "lookup_part", {"part_id": f["part"]})
    stats = await run.call_tool("Step 2 · Evidence (code)", "defect_stats", {"lot_id": f["lot"], "defect_code": f["defect_code"]})
    sim = await run.call_tool("Step 2 · Evidence (code)", "find_similar", {"defect_code": f["defect_code"], "line": f["line"], "exclude_lot": f["lot"]})
    unknown_part = "error" in part
    if unknown_part:
        run.emit("gate", "Code", "Part not in the database → rule: treat as safety critical and send to the Triage Desk.")
    if "error" in stats:
        run.emit("gate", "Code", "Lot not in the inspection log → stop and ask the reporter.")
        return needs_info_result("workflow", f)
    run.emit("step", "Step 3 · Policy", "CODE applies the severity policy tool.")
    pol = await run.call_tool("Step 3 · Policy (code)", "severity_policy", {
        "defect_code": f["defect_code"], "defect_rate_pct": stats["defect_rate_pct"],
        "safety_critical": True if unknown_part else part["safety_critical"], "recurring": sim["recurring"]})
    team = "Triage Desk" if unknown_part else part["owner_team"]
    run.emit("step", "Step 4 · Write-up", "LLM writes the summary from the facts. Severity and team are already fixed by code.")
    facts = {**f, "severity": pol["severity"], "rule": pol["rule"], "team": team,
             "defect_rate_pct": stats["defect_rate_pct"], "previous_lots": sim["previous_lots"]}
    _, s = await run.ask("Step 4 · Write-up (LLM)", SUMMARY_SYS, kv_block(facts), schema=SUMMARY_SCHEMA)
    res = make_result("workflow", f, {"severity": pol["severity"], "team": team, "recommended_action": pol["recommended_action"],
                                      "summary": (s or {}).get("summary", "(no summary)")})
    run.emit("gate", "Gate", f"Ticket proposed for {team} ({pol['severity']}). A human must approve before anything is written.")
    return res


def collect_facts(tool_log, actor) -> dict:
    out = {}
    for c in tool_log:
        if c["actor"] == actor and "error" not in c["result"]:
            out[c["name"]] = c["result"]
    return out


async def run_multi(run: Run, report: str) -> dict:
    run.emit("step", "Orchestrator", "Code hands the report to the Intake agent.")
    _, f = await run.ask("Intake agent", INTAKE_SYS, report, schema=EXTRACT_SCHEMA)
    if f is None or needs_info(f):
        run.emit("gate", "Orchestrator", "Intake found no lot or defect → stop and ask the reporter.")
        return needs_info_result("multi", f)
    run.emit("handoff", "Orchestrator", "Intake → Analyst: the extracted fields, as plain text.")
    await run.ask("Analyst agent", ANALYST_SYS, kv_block(f), tool_names={"lookup_part", "defect_stats", "find_similar"})
    ev = collect_facts(run.tool_log, "Analyst agent")
    part, stats, sim = ev.get("lookup_part"), ev.get("defect_stats"), ev.get("find_similar")
    unknown_part = part is None
    handoff = {**f, "part_description": part["description"] if part else "NOT IN DATABASE",
               "owner_team": part["owner_team"] if part else "Triage Desk",
               "safety_critical": True if unknown_part else part["safety_critical"],
               "defect_rate_pct": stats["defect_rate_pct"] if stats else "MISSING",
               "recurring": sim["recurring"] if sim else False}
    run.emit("handoff", "Orchestrator", "Analyst → Lead: the TOOL OUTPUTS as key: value lines, not the Analyst's prose.", handoff)
    feedback, prop = "", None
    for attempt in (1, 2):
        _, prop = await run.ask("Triage Lead agent", LEAD_SYS, kv_block(handoff) + feedback, tool_names={"severity_policy"},
                                schema=FINAL_SCHEMA, final_ask=FINAL_ASK)
        run.emit("handoff", "Orchestrator", "Lead → Reviewer: the proposal and the evidence.")
        review_in = kv_block(handoff) + "\nproposal: " + json.dumps(prop)
        _, rv = await run.ask("Reviewer agent", REVIEWER_SYS, review_in, schema=REVIEW_SCHEMA)
        if (rv or {}).get("verdict", "APPROVE") == "APPROVE" or attempt == 2:
            if rv and rv.get("verdict") == "REVISE":
                run.emit("gate", "Orchestrator", "Reviewer still unhappy after one revision → continue and flag it.")
            break
        feedback = f"\nThe reviewer asked for a revision: {rv.get('reason', '')}"
        run.emit("gate", "Orchestrator", "Reviewer says REVISE → the Lead tries once more.")
    res = make_result("multi", f, prop)
    run.emit("gate", "Gate", f"Ticket proposed for {res['team']} ({res['severity']}). A human must approve before anything is written.")
    return res


RUNNERS = {"agent": run_agent, "workflow": run_workflow, "multi": run_multi}


async def execute(mode: str, report: str, brain, on_event=None, key=None) -> dict:
    """Run one mode on one report. Returns result, trace, tool log, metrics and the audit."""
    async with connect() as session:
        run = Run(session, brain, on_event)
        try:
            result = await RUNNERS[mode](run, report)
        except Exception as e:                    # keep the UI alive: show the failure as part of the trace
            run.emit("error", mode, f"{type(e).__name__}: {e}")
            result = make_result(mode, None, None, note=str(e))
    return {"mode": mode, "result": result, "events": run.events, "tool_log": run.tool_log,
            "metrics": run.metrics(), "audit": audit(result, run.tool_log, key)}


async def file_ticket(ticket: dict, report_id: str = "") -> dict:
    """The human-approved write: the ONLY place create_ticket is called."""
    async with connect() as session:
        res = await session.call_tool("create_ticket", {**ticket, "report_id": report_id})
        return parse_json(result_text(res)) or {"error": "no result"}
