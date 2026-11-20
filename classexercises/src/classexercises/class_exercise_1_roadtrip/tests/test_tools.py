"""test_tools.py -- test the tools with NO AI and NO MCP."""
import pytest

from tools import fuel_cost, trip_time


# ---- fuel_cost: written together in class
def test_fuel_cost_by_hand():
    assert fuel_cost(450, 15, 1.60) == {"litres": 30.0, "cost": 48.0}
    assert fuel_cost(200, 10, 1.50) == {"litres": 20.0, "cost": 30.0}


def test_zero_distance_costs_nothing():
    assert fuel_cost(0, 15, 1.60) == {"litres": 0.0, "cost": 0.0}


def test_fuel_cost_rejects_bad_input():
    assert "error" in fuel_cost(450, 0, 1.60)        # km_per_litre of 0
    assert "error" in fuel_cost(-5, 15, 1.60)        # negative distance


# ---- trip_time: YOUR turn. Replace each pytest.fail with real asserts.
def test_trip_time_by_hand():
    # Hand calculate first. 450 km at 90 km/h with a 30 minute break.
    # Then a second case: 200 km at 80 km/h with a 15 minute break.
    pytest.fail("TODO: write this test")


def test_no_break_by_default():
    # What should total_h be for 450 km at 90 km/h with no break given?
    pytest.fail("TODO: write this test")


def test_trip_time_rejects_bad_input():
    # Which inputs make no sense? Check that "error" is in the result.
    pytest.fail("TODO: write this test")
