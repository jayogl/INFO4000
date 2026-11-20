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
    # Hand calculate first (see EXERCISE.md): a tension of 5905 N, safety
    # factor 5. What is the design load? Which cable in cables.csv is the
    # smallest that holds it? What is its margin_pct?
    # Then a second case: 2162 N, safety factor 5.
    pytest.fail("TODO: write this test")


def test_catalog_is_not_sorted_so_pick_the_lightest_strong_one():
    # cables.csv lists Rope-12 first. A tension of 8000 N with safety factor 5
    # needs 40 kN. Which cable should come back?
    pytest.fail("TODO: write this test")


def test_select_cable_rejects_bad_input():
    # Which inputs make no sense? Also try a load no cable can carry, and a
    # catalog file that does not exist. Check that "error" is in the result.
    pytest.fail("TODO: write this test")
