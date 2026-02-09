"""Test pressure-type stage conversion."""

import pytest
from translate_profile.translator import translate_profile


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


def test_pressure_type_basic():
    """Test basic pressure-type stage conversion."""
    profile_data = {
        "name": "Test Profile",
        "id": "test-id",
        "author": "Test",
        "author_id": "test-author",
        "previous_authors": [],
        "temperature": 93,
        "final_weight": 30,
        "variables": [],
        "stages": [create_pressure_stage("Test Stage", 5.0)],
    }

    result = translate_profile(profile_data)
    phase = result["phases"][0]

    assert phase["pump"]["target"] == "pressure"
    assert abs(phase["pump"]["pressure"] - 5.0) < 0.1
    print(f"  Basic pressure stage: {phase['pump']['pressure']} bar ✓")


@pytest.mark.parametrize("pressure_value", [1.0, 2.5, 5.0, 9.0, 10.0])
def test_pressure_type_parametrized(pressure_value: float):
    """Test various pressure values."""
    profile_data = {
        "name": "Test Profile",
        "id": "test-id",
        "author": "Test",
        "author_id": "test-author",
        "previous_authors": [],
        "temperature": 93,
        "final_weight": 30,
        "variables": [],
        "stages": [create_pressure_stage("Test Stage", pressure_value)],
    }

    result = translate_profile(profile_data)
    phase = result["phases"][0]

    assert phase["pump"]["target"] == "pressure"
    assert abs(phase["pump"]["pressure"] - pressure_value) < 0.1
    print(f"  Pressure {pressure_value}: {phase['pump']['pressure']} bar ✓")


def test_pressure_type_rejects_power_division():
    """Verify pressure-type stages don't divide by 10 (bug fix verification)."""
    profile_data = {
        "name": "Test Profile",
        "id": "test-id",
        "author": "Test",
        "author_id": "test-author",
        "previous_authors": [],
        "temperature": 93,
        "final_weight": 30,
        "variables": [],
        "stages": [create_pressure_stage("Test Stage", 5.0)],
    }

    result = translate_profile(profile_data)
    phase = result["phases"][0]

    # Should be 5.0, not 0.5 (which would happen if divided by 10)
    assert abs(phase["pump"]["pressure"] - 5.0) < 0.1
    assert phase["pump"]["pressure"] > 1.0  # Not divided by 10
    print("  ✓ Pressure-type stages use value directly (not divided by 10)")


def test_pressure_type_multi_point():
    """Test pressure-type stage with multiple dynamics points."""
    multi_point_stage = {
        "name": "Pressure Ramp",
        "key": "pressure_ramp",
        "type": "pressure",
        "dynamics": {"points": [[0, 2.0], [30, 9.0]], "over": "time", "interpolation": "linear"},
        "exit_triggers": [{"type": "time", "value": 30, "relative": False, "comparison": ">= "}],
        "limits": [],
    }

    profile_data = {
        "name": "Test Profile",
        "id": "test-id",
        "author": "Test",
        "author_id": "test-author",
        "previous_authors": [],
        "temperature": 93,
        "final_weight": 30,
        "variables": [],
        "stages": [multi_point_stage],
    }

    result = translate_profile(profile_data)

    # Should create 1 phase from 2 points
    assert len(result["phases"]) == 1
    phase = result["phases"][0]

    assert phase["pump"]["target"] == "pressure"
    assert abs(phase["pump"]["pressure"] - 9.0) < 0.1  # Final point value
    print(f"  Multi-point pressure: {phase['pump']['pressure']} bar ✓")
