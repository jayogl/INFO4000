"""test_tools.py -- test the tools with NO AI and NO MCP."""
import pytest

from tools import lift_force, select_cable


# ---- lift_force: written together in class
def test_lift_force_by_hand():
    assert lift_force(500, 2) == {"weight_n": 4905.0, "tension_n": 5905.0}
    assert lift_force(200, 1) == {"weight_n": 1962.0, "tension_n": 2162.0}


def test_steady_lift_tension_equals_weight():
    r = lift_force(500)
    assert r["tension_n"] == r["weight_n"] == 4905.0


def test_lift_force_rejects_bad_input():
    assert "error" in lift_force(0)                  # no mass
    assert "error" in lift_force(500, -1)            # negative acceleration


# ---- select_cable: YOUR turn. Replace each pytest.fail with real asserts.
def test_select_cable_by_hand():
    # Tension 5905 N * 5 = 29,525 N (29.525 kN) -> Rope-8 (32 kN), margin 8.38%
    r1 = select_cable(5905.0, 5.0)
    assert r1["design_load_n"] == 29525.0
    assert r1["cable"] == "Rope-8"
    assert r1["breaking_load_kn"] == 32.0
    assert r1["margin_pct"] == 8.38
    # Tension 2162 N * 5 = 10,810 N (10.81 kN) -> Rope-6 (18 kN)
    r2 = select_cable(2162.0, 5.0)
    assert r2["cable"] == "Rope-6"


def test_catalog_is_not_sorted_so_pick_the_lightest_strong_one():
    # Tension 8000 N * 5 = 40,000 N (40 kN).
    # CSV lists Rope-12 (72 kN) first, but Rope-10 (50 kN) is smaller and strong enough.
    r = select_cable(8000.0, 5.0)
    assert r["cable"] == "Rope-10"
    assert r["breaking_load_kn"] == 50.0


def test_select_cable_rejects_bad_input():
    assert "error" in select_cable(-100, 5)  # negative load
    assert "error" in select_cable(5000, 0.5)  # safety factor < 1
    assert "error" in select_cable(1000000, 5)  # load too large for catalog
    assert "error" in select_cable(5000, 5, "missing.csv")  # file missing