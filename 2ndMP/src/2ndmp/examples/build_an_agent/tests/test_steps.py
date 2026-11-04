"""Every step runs end to end against a scripted fake of Ollama (no model needed), and the tool matches hand calculations."""
import runpy
import sys
import types
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
GOOD = {"load_n": 100, "length_mm": 300, "width_mm": 20, "height_mm": 10, "material": "steel"}


def install_fake(script):
    """script: list of replies, each ('call', name, args) or ('say', text). One reply per chat() call."""
    fake = types.ModuleType("ollama")
    fake.ResponseError = type("ResponseError", (Exception,), {})
    calls = []

    def chat(model=None, messages=None, tools=None, options=None, think=None):
        calls.append({"n_messages": len(messages), "tools": bool(tools)})
        kind, *rest = script[min(len(calls) - 1, len(script) - 1)]
        if kind == "call":
            msg = NS(content="", tool_calls=[NS(function=NS(name=rest[0], arguments=rest[1]))], role="assistant")
        else:
            msg = NS(content=rest[0], tool_calls=None, role="assistant")
        return NS(message=msg)

    fake.chat = chat
    sys.modules["ollama"] = fake
    sys.modules.pop("llm", None)
    return calls


def run_step(name, capsys, argv=("x",)):
    for m in ("s1_tool", "s2_describe", "llm"):
        sys.modules.pop(m, None)
    old = sys.argv
    sys.argv = list(argv)
    try:
        runpy.run_path(str(ROOT / name), run_name="__main__")
    finally:
        sys.argv = old
    return capsys.readouterr().out


def test_tool_matches_hand_calculation():
    sys.path.insert(0, str(ROOT))
    from s1_tool import cantilever_beam as f
    r = f(100, 300, 20, 10, "steel")
    assert (r["deflection_mm"], r["max_stress_mpa"], r["safety_factor"], r["verdict"]) == (2.7, 90.0, 2.78, "safe")
    assert f(100, 300, 20, 10, "aluminum")["deflection_mm"] == 7.826
    assert f(100, 300, 10, 20, "steel")["deflection_mm"] == 0.675           # on its side: 4 times stiffer
    assert f(500, 500, 20, 10)["verdict"] == "fails"
    assert "available" in f(1, 1, 1, 1, "wood") and "error" in f(0, 1, 1, 1)


def test_s0_model_alone(capsys):
    install_fake([("say", "About 3 mm, I think.")])
    assert "About 3 mm" in run_step("s0_model_alone.py", capsys)


def test_s2_describe_matches_the_function(capsys):
    install_fake([("say", "")])
    out = run_step("s2_describe.py", capsys)
    import inspect, json
    from s1_tool import cantilever_beam
    schema = json.loads(out)[0]["function"]
    assert schema["name"] == "cantilever_beam"
    assert set(schema["parameters"]["properties"]) == set(inspect.signature(cantilever_beam).parameters)
    assert schema["parameters"]["required"] == ["load_n", "length_mm", "width_mm", "height_mm"]


def test_s3_model_asks_but_nothing_runs(capsys):
    install_fake([("call", "cantilever_beam", GOOD)])
    out = run_step("s3_model_asks.py", capsys)
    assert "tool_calls:" in out and "cantilever_beam" in out and "deflection" not in out


def test_s4_one_round(capsys):
    calls = install_fake([("call", "cantilever_beam", GOOD), ("say", "It deflects 2.7 mm; safety factor 2.78.")])
    out = run_step("s4_run_and_answer.py", capsys)
    assert "'deflection_mm': 2.7" in out and "answer: It deflects 2.7 mm" in out and len(calls) == 2


def test_s5_loop_runs_until_the_model_stops_asking(capsys):
    calls = install_fake([("call", "cantilever_beam", GOOD), ("call", "cantilever_beam", {**GOOD, "material": "aluminum"}),
                          ("say", "Steel 2.7 mm, aluminum 7.826 mm.")])
    out = run_step("s5_agent_loop.py", capsys)
    assert len(calls) == 3 and out.count("tool: cantilever_beam") == 2 and "answer: Steel 2.7 mm" in out


def test_s6_survives_unknown_tool_and_wrong_arguments(capsys):
    calls = install_fake([("call", "calc", {"x": 1}), ("call", "cantilever_beam", {"part_id": "U7"}),
                          ("call", "cantilever_beam", GOOD), ("say", "2.7 mm, safe.")])
    out = run_step("s6_guardrails.py", capsys)
    assert "there is no tool called 'calc'" in out and "wrong arguments for cantilever_beam" in out
    assert "'deflection_mm': 2.7" in out and "answer: 2.7 mm" in out and len(calls) == 4


def test_s6_stops_after_max_steps(capsys):
    calls = install_fake([("call", "cantilever_beam", GOOD)])               # never stops asking
    out = run_step("s6_guardrails.py", capsys)
    assert "stopped: no answer after 5 steps" in out and len(calls) == 5


def test_s7_mcp_server_lists_the_tool():
    import asyncio
    sys.modules.pop("s1_tool", None)
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def go():
        params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "s7_mcp_server.py")], cwd=str(ROOT))
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                tools = (await s.list_tools()).tools
                res = await s.call_tool("cantilever_beam", GOOD)
                return [t.name for t in tools], "2.7" in "".join(getattr(c, "text", "") for c in res.content)

    names, ok = asyncio.run(go())
    assert names == ["cantilever_beam"] and ok
