import asyncio, sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).parent.parent))
import tools
from agent import run_question, strip_thinking
from multi_agent import design_divider
from client import connect


def test_pid_integrator_reaches_setpoint():
    r = tools.simulate_pid(2, 8, 2)            # hand check: zeta=0.375 plus a PI zero -> ~32 % overshoot
    assert r["stable"] and abs(r["steady_state_value"] - 1) < 1e-3 and 30 < r["overshoot_pct"] < 35
    assert tools.simulate_pid(2, 0.5, 1)["overshoot_pct"] == 0   # overdamped: no overshoot


def test_pid_p_only_has_offset():
    r = tools.simulate_pid(1, 0, 1)            # T = 1/(tau s + 2) -> final value 0.5
    assert abs(r["steady_state_value"] - 0.5) < 1e-3 and r["overshoot_pct"] == 0


def test_pid_unstable_flagged():
    assert tools.simulate_pid(-5, 1, 1)["stable"] is False      # negative gain -> unstable
    assert tools.simulate_pid(0, 0, 1).get("error")


def test_rc():
    r = tools.design_rc_lowpass(1000, 10)
    assert abs(r["ideal_r_ohms"] - 15915.5) < 1 and r["nearest_e24_ohms"] == 16000.0


def test_log_spike():
    r = tools.read_log_stats("temp_c", 220)
    assert r["max"] > 220 and 1200 <= r["first_above_s"] <= 1260
    assert "available_columns" in tools.read_log_stats("nope")


def test_server_roundtrip():
    async def go():
        async with connect() as s:
            names = {t.name for t in (await s.list_tools()).tools}
            res = await s.call_tool("design_rc_lowpass", {"cutoff_hz": 1000, "capacitance_nf": 10})
            return names, res.content[0].text
    names, text = asyncio.run(go())
    assert names == {"simulate_pid", "design_rc_lowpass", "read_log_stats", "divider_design", "divider_check"} and "16000" in text


def test_agent_loop_with_fake_model():
    calls = iter([
        NS(message=NS(role="assistant", content="", tool_calls=[NS(function=NS(name="design_rc_lowpass",
                      arguments={"cutoff_hz": 1000, "capacitance_nf": 10}))])),
        NS(message=NS(role="assistant", content="Use about 16 kOhm.", tool_calls=None)),
    ])
    class Fake:
        async def chat(self, **kw): return next(calls)
    async def go():
        async with connect() as s:
            return await run_question(s, "fake", "RC filter?", client=Fake(), verbose=False)
    out = asyncio.run(go())
    assert out["answer"] == "Use about 16 kOhm." and out["calls"][0]["name"] == "design_rc_lowpass"


def test_strip_thinking():
    assert strip_thinking("Okay, let me see...\nWait.\n</think>\n\nThe overshoot is 32.37%.") == "The overshoot is 32.37%."
    assert strip_thinking("<think>hmm</think>Answer.") == "Answer."
    assert strip_thinking("Plain answer.") == "Plain answer."


def test_divider_tools_match_hand_calc():
    d = tools.divider_design(12, 3.3, 10000)
    assert d["r1_e24_ohms"] == 27000 and abs(d["vout_unloaded_v"] - 3.243) < 1e-3
    bad = tools.divider_check(12, 27000, 10000, 3.3, 100000)          # 12*9090.9/(27000+9090.9) = 3.023
    assert abs(bad["vout_v"] - 3.023) < 1e-3 and bad["passes"] is False and "hint" in bad
    ok = tools.divider_check(12, 2700, 1000, 3.3, 100000)             # 12*990.1/(2700+990.1) = 3.220
    assert abs(ok["vout_v"] - 3.22) < 1e-3 and ok["passes"] is True
    worst = tools.divider_check(12, 2700, 1000, 3.3, 100000, 3.0, 1.0)
    assert worst["passes"] is False and worst["worst_case_error_pct"] < -3     # +/-1 % parts break the margin
    assert tools.divider_design(12, 15, 1000).get("error")


def _call(name, args):
    return NS(message=NS(role="assistant", content="", tool_calls=[NS(function=NS(name=name, arguments=args))]))


def _say(text):
    return NS(message=NS(role="assistant", content=text, tool_calls=None))


def test_multi_agent_two_rounds_with_fake_model():
    # Scripted model, consumed in order: Designer, Checker, Designer, Checker.
    script = iter([
        _call("divider_design", {"vin": 12, "vout": 3.3, "r2_ohms": 10000}), _say("R1 = 27000, R2 = 10000"),
        _call("divider_check", {"vin": 12, "r1_ohms": 27000, "r2_ohms": 10000, "target_vout": 3.3,
                                "load_ohms": 100000, "tolerance_pct": 3.0, "resistor_tol_pct": 0.0}), _say("FAIL: 3.02 V."),
        _call("divider_design", {"vin": 12, "vout": 3.3, "r2_ohms": 1000}), _say("R1 = 2700, R2 = 1000"),
        _call("divider_check", {"vin": 12, "r1_ohms": 2700, "r2_ohms": 1000, "target_vout": 3.3,
                                "load_ohms": 100000, "tolerance_pct": 3.0, "resistor_tol_pct": 0.0}), _say("PASS: 3.22 V."),
    ])
    class Fake:
        async def chat(self, **kw): return next(script)
    async def go():
        async with connect() as s:
            return await design_divider(s, "fake", vin=12, vout=3.3, load_ohms=100000, client=Fake(), verbose=False)
    r = asyncio.run(go())
    assert r["ok"] and r["rounds"] == 2 and (r["r1_ohms"], r["r2_ohms"]) == (2700, 1000)
    assert r["history"][0]["check"]["passes"] is False and r["history"][1]["check"]["passes"] is True


def test_agents_see_only_their_own_tools():
    seen = []
    class Spy:
        async def chat(self, **kw):
            seen.append({t["function"]["name"] for t in kw["tools"]}); return _say("ok")
    async def go():
        async with connect() as s:
            await run_question(s, "fake", "x", client=Spy(), verbose=False, tool_names={"divider_design"})
    asyncio.run(go())
    assert seen == [{"divider_design"}]
