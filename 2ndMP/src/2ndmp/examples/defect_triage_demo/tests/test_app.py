import os, sys, tempfile
from pathlib import Path
os.environ["TRIAGE_TICKETS"] = str(Path(tempfile.mkdtemp()) / "tickets.jsonl")
sys.path.insert(0, str(Path(__file__).parent.parent))
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "app.py")


def _run(report, mode):
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception
    at.sidebar.radio(key="backend").set_value("Rule-based stand-in (no LLM)")
    at.sidebar.radio(key="mode").set_value(mode)
    at.sidebar.selectbox(key="report_id").set_value(report)
    at.run()
    at.sidebar.button(key="run").click().run()
    return at


def test_compare_all_three_renders_and_ticket_can_be_approved():
    at = _run("R-001", "Compare all three")
    assert not at.exception, at.exception
    assert len(at.session_state["runs"]) == 3
    assert {k: v["result"]["severity"] for k, v in at.session_state["runs"].items()} == {"agent": "P2", "workflow": "P2", "multi": "P2"}
    at.button(key="approve_workflow").click().run()
    assert not at.exception and "workflow" in at.session_state["tickets"]
    assert at.session_state["tickets"]["workflow"]["ticket_id"].startswith("DEF-")


def test_vague_report_has_no_approve_button():
    at = _run("R-006", "Workflow")
    assert not at.exception and at.session_state["runs"]["workflow"]["result"]["severity"] == "NEEDS_INFO"
    assert not [b for b in at.button if b.key and b.key.startswith("approve_")]


def test_clear_screen_removes_results_and_banner_shows_run_number():
    at = _run("R-001", "Workflow")
    assert at.session_state["run_meta"]["n"] == 1 and any("RUN #1" in m.value for m in at.markdown)
    at.sidebar.button(key="reset").click().run()
    assert not at.exception and not at.session_state["runs"] and at.session_state["run_meta"] is None
    assert not any("RUN #" in m.value for m in at.markdown)


def test_changed_sidebar_after_a_run_shows_a_warning_not_silent_old_results():
    at = _run("R-001", "Workflow")
    at.sidebar.radio(key="mode").set_value("Single agent").run()
    assert not at.exception and any("sidebar has changed" in w.value for w in at.warning)
    at.sidebar.button(key="run").click().run()          # running again replaces it: run #2, no warning
    assert at.session_state["run_meta"]["n"] == 2 and not any("sidebar has changed" in w.value for w in at.warning)
