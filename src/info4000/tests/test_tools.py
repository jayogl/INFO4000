"""test_tools.py -- test the tools with NO AI and NO MCP."""
from tools import motor_health_check, motor_life_estimate


def test_life_halves_every_10_degrees():
    assert motor_life_estimate(130, 130)["life_h"] == 20000
    assert motor_life_estimate(130, 140)["life_h"] == 10000
    assert motor_life_estimate(130, 150) == {
        "life_h": 5000, "life_years": 0.6, "life_ratio": 0.25}


def test_cooler_motor_lives_longer():
    r = motor_life_estimate(130, 110)
    assert r["life_h"] == 80000 and r["life_years"] == 9.1


def test_life_rejects_bad_input():
    assert "error" in motor_life_estimate(130, 300)
    assert "error" in motor_life_estimate(130, 100, rated_life_h=0)


def test_healthy_motor_is_ok():
    assert motor_health_check(0.5, 90, 20, 25) == {
        "status": "OK", "reasons": [], "vib_zone": "A",
        "load_pct": 80.0, "temp_margin_c": 40.0}


def test_motor_near_its_limit_is_watch():
    r = motor_health_check(1.0, 125, 24, 25)
    assert r["status"] == "WATCH" and r["reasons"] == ["hot"]
    assert r["vib_zone"] == "B" and r["temp_margin_c"] == 5.0


def test_hot_overloaded_vibrating_motor_is_act():
    r = motor_health_check(3.1, 150, 28, 25)
    assert r["status"] == "ACT"
    assert r["reasons"] == ["vibration", "hot", "overload"]
    assert r["vib_zone"] == "C" and r["load_pct"] == 112.0
    assert r["temp_margin_c"] == -20.0


def test_vibration_zone_d_alone_is_act():
    r = motor_health_check(5.0, 90, 20, 25)
    assert r["status"] == "ACT" and r["reasons"] == ["vibration"]


def test_health_rejects_bad_input():
    assert "error" in motor_health_check(1, 90, 20, 0)
