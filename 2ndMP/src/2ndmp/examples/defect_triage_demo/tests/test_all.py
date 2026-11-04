import asyncio, json, os, sys, tempfile
from pathlib import Path

os.environ["TRIAGE_TICKETS"] = str(Path(tempfile.mkdtemp()) / "tickets.jsonl")   # never touch real data
sys.path.insert(0, str(Path(__file__).parent.parent))
import pytest
import tools
from core import RuleBrain, execute, file_ticket, audit, connect

REPORTS = {r["id"]: r for r in json.loads((Path(__file__).parent.parent / "data" / "reports.json").read_text(encoding="utf-8"))}


def test_data_storylines():
    s = tools.defect_stats("L-2231", "SOLDER_BRIDGE")
    assert s["units_inspected"] == 1200 and s["defect_rate_pct"] == 2.58
    assert tools.find_similar("SOLDER_BRIDGE", 2, "L-2231")["previous_lots"] == 3
    assert tools.find_similar("COLD_JOINT", 1, "L-2240")["previous_lots"] == 0       # noise never touches story pairs
    assert tools.find_similar("TOMBSTONE", 1, "L-2238")["recurring"] is True
    assert "error" in tools.lookup_part("D9") and "error" in tools.defect_stats("L-0000")


@pytest.mark.parametrize("rate,crit,rec,sev", [(5.3, False, False, "P1"), (0.6, True, False, "P1"), (2.58, False, True, "P2"),
                                               (0.5, False, True, "P2"), (0.22, True, False, "P2"), (0.2, False, False, "P3")])
def test_policy(rate, crit, rec, sev):
    assert tools.severity_policy("X", rate, crit, rec)["severity"] == sev


def test_ticket_is_written():
    t = tools.create_ticket("SMT Process", "P2", "x", "R-001")
    assert t["ticket_id"].startswith("DEF-") and tools.TICKETS.exists()


@pytest.mark.parametrize("mode", ["agent", "workflow", "multi"])
@pytest.mark.parametrize("rid", sorted(REPORTS))
def test_all_modes_all_reports_with_stand_in(mode, rid):
    r = REPORTS[rid]
    out = asyncio.run(execute(mode, r["text"], RuleBrain(), None, r["expected"]))
    assert out["result"]["severity"] == r["expected"]["severity"], out["result"]
    assert out["result"]["team"] == r["expected"]["team"]
    assert all(ok for _, ok in out["audit"] if ok is not None), out["audit"]


def test_workflow_calls_tools_in_code_order_and_agent_calls_are_model_chosen():
    out = asyncio.run(execute("workflow", REPORTS["R-001"]["text"], RuleBrain()))
    assert [c["name"] for c in out["tool_log"]] == ["lookup_part", "defect_stats", "find_similar", "severity_policy"]
    assert out["metrics"]["model_calls"] == 2            # extract + write-up only


def test_vague_report_does_not_call_tools():
    for mode in ("agent", "workflow", "multi"):
        out = asyncio.run(execute(mode, REPORTS["R-006"]["text"], RuleBrain()))
        assert out["tool_log"] == [] and out["result"]["severity"] == "NEEDS_INFO" and out["result"]["ticket"] is None


class LazyAgent(RuleBrain):
    """An agent that skips the policy tool and guesses P3 -- what a weak model can do."""
    async def chat(self, messages, tools=None, schema=None):
        if tools and any(t["function"]["name"] == "severity_policy" for t in tools):
            names = [t["function"]["name"] for t in tools if t["function"]["name"] != "severity_policy"]
            done = {m["tool_name"] for m in messages if m["role"] == "tool"}
            first = next(m["content"] for m in messages if m["role"] == "user")
            from core import regex_extract
            f = regex_extract(first)
            if "defect_stats" not in done:
                return {"content": "", "tool_calls": [("defect_stats", {"lot_id": f["lot"], "defect_code": f["defect_code"]})]}
            return {"content": "ready", "tool_calls": []}
        if schema and "recommended_action" in schema.get("properties", {}):
            return {"content": json.dumps({"severity": "P3", "team": "SMT Process", "recommended_action": "Log it", "summary": "Looks fine."}), "tool_calls": []}
        return await super().chat(messages, tools, schema)


def test_audit_catches_a_lazy_agent():
    r = REPORTS["R-001"]
    out = asyncio.run(execute("agent", r["text"], LazyAgent(), None, r["expected"]))
    failed = [label for label, ok in out["audit"] if ok is False]
    assert "Used the severity policy tool" in failed and "Severity matches the answer key" in failed


class Skeptic(RuleBrain):
    """Reviewer says REVISE the first time."""
    n = 0
    async def chat(self, messages, tools=None, schema=None):
        if schema and "verdict" in schema.get("properties", {}):
            Skeptic.n += 1
            if Skeptic.n == 1:
                return {"content": json.dumps({"verdict": "REVISE", "reason": "check the team"}), "tool_calls": []}
        return await super().chat(messages, tools, schema)


def test_reviewer_revise_triggers_one_retry():
    Skeptic.n = 0
    out = asyncio.run(execute("multi", REPORTS["R-002"]["text"], Skeptic()))
    leads = [e for e in out["events"] if e.actor == "Triage Lead agent" and e.kind == "tool_call"]
    assert len(leads) == 2 and out["result"]["severity"] == "P1"


def test_server_lists_five_tools_and_ticket_roundtrip():
    async def go():
        async with connect() as s:
            return {t.name for t in (await s.list_tools()).tools}
    assert asyncio.run(go()) == {"lookup_part", "defect_stats", "find_similar", "severity_policy", "create_ticket"}
    assert asyncio.run(file_ticket({"team": "A", "severity": "P2", "summary": "s"}, "R-1"))["ticket_id"].startswith("DEF-")


def test_no_model_ever_sees_create_ticket():
    out = asyncio.run(execute("agent", REPORTS["R-001"]["text"], RuleBrain()))
    assert "create_ticket" not in [c["name"] for c in out["tool_log"]]


class WrongArgsFirst(RuleBrain):
    """Calls severity_policy with lookup_part's argument first (the real-model mistake), then behaves."""
    done = False
    async def chat(self, messages, tools=None, schema=None):
        if tools and not WrongArgsFirst.done:
            WrongArgsFirst.done = True
            return {"content": "", "tool_calls": [("severity_policy", {"part_id": "U7"})]}
        return await super().chat(messages, tools, schema)


def test_wrong_arguments_get_a_clear_error_and_the_agent_recovers():
    WrongArgsFirst.done = False
    r = REPORTS["R-001"]
    out = asyncio.run(execute("agent", r["text"], WrongArgsFirst(), None, r["expected"]))
    first = out["tool_log"][0]["result"]
    assert "Missing" in first["error"] and "defect_rate_pct" in first["error"]      # short, names the fix
    assert out["result"]["severity"] == "P2"                                          # recovered
    assert all(ok for _, ok in out["audit"] if ok is not None)
