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
    # Hand calculate first: 450 km at 90 km/h with 30 min break -> drive 5.0h, total 5.5h
    assert trip_time(450, 90, 30) == {"drive_h": 5.0, "total_h": 5.5}
    # Second case: 200 km at 80 km/h with 15 min break -> drive 2.5h, total 2.75h
    assert trip_time(200, 80, 15) == {"drive_h": 2.5, "total_h": 2.75}


def test_no_break_by_default():
    # 450 km at 90 km/h with no break given -> drive 5.0h, total 5.0h
    assert trip_time(450, 90) == {"drive_h": 5.0, "total_h": 5.0}


def test_trip_time_rejects_bad_input():
    assert "error" in trip_time(450, 0, 30)  # speed_kmh of 0
    assert "error" in trip_time(-100, 90, 30)  # negative distance
    assert "error" in trip_time(450, 90, -15)  # negative break