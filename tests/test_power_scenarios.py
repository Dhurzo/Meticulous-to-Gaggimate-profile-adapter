"""Test power-to-pressure conversion scenarios."""

import pytest
from translate_profile.translator import translate_profile


def create_power_stage(name: str, power_value: float) -> dict:
    """Helper to create a power-type stage."""
    return {
        "name": name,
        "key": name.lower().replace(" ", "_"),
        "type": "power",
        "dynamics": {"points": [[0, power_value]], "over": "time", "interpolation": "linear"},
        "exit_triggers": [{"type": "time", "value": 10, "relative": False, "comparison": ">= "}],
        "limits": [],
    }


def test_power_0_percent():
    """Test 0% power (edge case - no pressure)."""
    profile_data = {
        "name": "Test Profile",
        "id": "test-id",
        "author": "Test",
        "author_id": "test-author",
        "previous_authors": [],
        "temperature": 93,
        "final_weight": 30,
        "variables": [],
        "stages": [create_power_stage("0% Power", 0.0)],
    }

    result, _ = translate_profile(profile_data)
    phase = result["phases"][0]

    assert phase["pump"]["target"] == "pressure"
    assert abs(phase["pump"]["pressure"] - 0.0) < 0.1  # 0% = 0.0 bar
    print(f"  0% power: {phase['pump']['pressure']} bar ✓")


def test_power_10_percent():
    """Test 10% power (low extraction)."""
    profile_data = {
        "name": "Test Profile",
        "id": "test-id",
        "author": "Test",
        "author_id": "test-author",
        "previous_authors": [],
        "temperature": 93,
        "final_weight": 30,
        "variables": [],
        "stages": [create_power_stage("10% Power", 10.0)],
    }

    result, _ = translate_profile(profile_data)
    phase = result["phases"][0]

    assert phase["pump"]["target"] == "pressure"
    assert abs(phase["pump"]["pressure"] - 1.0) < 0.1  # 10% = 1.0 bar
    print(f"  10% power: {phase['pump']['pressure']} bar ✓")


def test_power_50_percent():
    """Test 50% power (medium extraction)."""
    profile_data = {
        "name": "Test Profile",
        "id": "test-id",
        "author": "Test",
        "author_id": "test-author",
        "previous_authors": [],
        "temperature": 93,
        "final_weight": 30,
        "variables": [],
        "stages": [create_power_stage("50% Power", 50.0)],
    }

    result, _ = translate_profile(profile_data)
    phase = result["phases"][0]

    assert phase["pump"]["target"] == "pressure"
    assert abs(phase["pump"]["pressure"] - 5.0) < 0.1  # 50% = 5.0 bar
    print(f"  50% power: {phase['pump']['pressure']} bar ✓")


def test_power_100_percent():
    """Test 100% power (full extraction)."""
    profile_data = {
        "name": "Test Profile",
        "id": "test-id",
        "author": "Test",
        "author_id": "test-author",
        "previous_authors": [],
        "temperature": 93,
        "final_weight": 30,
        "variables": [],
        "stages": [create_power_stage("100% Power", 100.0)],
    }

    result, _ = translate_profile(profile_data)
    phase = result["phases"][0]

    assert phase["pump"]["target"] == "pressure"
    assert abs(phase["pump"]["pressure"] - 10.0) < 0.1  # 100% = 10.0 bar
    print(f"  100% power: {phase['pump']['pressure']} bar ✓")


@pytest.mark.parametrize(
    "power_value,expected_pressure",
    [
        (0.0, 0.0),
        (10.0, 1.0),
        (50.0, 5.0),
        (100.0, 10.0),
    ],
)
def test_power_to_pressure_conversion(power_value: float, expected_pressure: float):
    """Parametrized test for power-to-pressure conversion formula."""
    profile_data = {
        "name": "Test Profile",
        "id": "test-id",
        "author": "Test",
        "author_id": "test-author",
        "previous_authors": [],
        "temperature": 93,
        "final_weight": 30,
        "variables": [],
        "stages": [create_power_stage("Test", power_value)],
    }

    result, _ = translate_profile(profile_data)
    phase = result["phases"][0]

    assert phase["pump"]["target"] == "pressure"
    assert abs(phase["pump"]["pressure"] - expected_pressure) < 0.1
    print(f"  {power_value}% → {expected_pressure} bar ✓")


def test_power_vs_pressure_distinction():
    """Verify power-type and pressure-type stages are handled differently."""
    # Power-type stage
    power_profile = {
        "name": "Power Profile",
        "id": "test-id",
        "author": "Test",
        "author_id": "test-author",
        "previous_authors": [],
        "temperature": 93,
        "final_weight": 30,
        "variables": [],
        "stages": [create_power_stage("Power Stage", 50.0)],
    }

    # Pressure-type stage
    pressure_profile = {
        "name": "Pressure Profile",
        "id": "test-id",
        "author": "Test",
        "author_id": "test-author",
        "previous_authors": [],
        "temperature": 93,
        "final_weight": 30,
        "variables": [],
        "stages": [create_pressure_stage("Pressure Stage", 5.0)],
    }

    # Helper import
    from translate_profile.translator import translate_profile

    power_result, _ = translate_profile(power_profile)
    pressure_result, _ = translate_profile(pressure_profile)

    # Both should have same numerical pressure (5.0 bar)
    power_phase = power_result["phases"][0]
    pressure_phase = pressure_result["phases"][0]

    assert abs(power_phase["pump"]["pressure"] - 5.0) < 0.1  # 50% / 10 = 5.0
    assert abs(pressure_phase["pump"]["pressure"] - 5.0) < 0.1  # 5.0 directly

    print(f"  Power 50% → 5.0 bar, Pressure 5.0 → 5.0 bar ✓")


# Import helper from this file's scope for the distinction test
def create_pressure_stage(name: str, pressure_value: float) -> dict:
    """Helper to create a pressure-type stage."""
    return {
        "name": name,
        "key": name.lower().replace(" ", "_"),
        "type": "pressure",
        "dynamics": {"points": [[0, pressure_value]], "over": "time", "interpolation": "linear"},
        "exit_triggers": [{"type": "time", "value": 10, "relative": False, "comparison": ">= "}],
        "limits": [],
    }
