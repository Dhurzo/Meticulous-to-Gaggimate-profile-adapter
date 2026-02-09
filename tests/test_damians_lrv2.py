"""Test Damians LRv2.json profile translation."""

import json
import pytest
from translate_profile.translator import translate_profile


def test_damians_lrv2_translation():
    """Test that Damians LRv2.json translates correctly."""
    # Load Damians LRv2.json
    with open("Damians LRv2.json") as f:
        data = json.load(f)

    # Translate
    result = translate_profile(data)

    # Verify we have 7 phases
    assert len(result["phases"]) == 7
    print(f"✓ Profile has {len(result['phases'])} phases")

    # Verify specific pressure values for first 4 pressure-type stages
    phase_pressures = {
        "Fill start": 2.0,
        "Fill": 2.0,
        "Infuse": 3.0,
        "Pressure Up": 9.0,
    }

    for phase in result["phases"]:
        name = phase["name"]
        if name in phase_pressures:
            expected = phase_pressures[name]
            assert phase["pump"]["target"] == "pressure"
            assert abs(phase["pump"]["pressure"] - expected) < 0.1
            print(f"  {name}: {phase['pump']['pressure']} bar ✓")

    print("✓ Damians LRv2.json translation verified")


def test_damians_lrv2_flow_limit_phase():
    """Test Flow Limit phase uses flow target."""
    with open("Damians LRv2.json") as f:
        data = json.load(f)

    result = translate_profile(data)
    flow_phase = result["phases"][-1]

    assert flow_phase["pump"]["target"] == "flow"
    assert abs(flow_phase["pump"]["flow"] - 2.5) < 0.1
    print(f"  Flow Limit: flow={flow_phase['pump']['flow']} ✓")


def test_damians_lrv2_all_pressures_in_range():
    """Test all pressure values are in valid range (1-10 bar typical)."""
    import warnings

    with open("Damians LRv2.json") as f:
        data = json.load(f)

    # Should not trigger any warnings (all pressures in range)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = translate_profile(data)

        # Filter for pressure-related warnings
        pressure_warnings = [warning for warning in w if "pressure" in str(warning.message)]
        assert len(pressure_warnings) == 0, f"Unexpected pressure warnings: {pressure_warnings}"

    # Verify all pressure values
    pressures = [
        phase["pump"]["pressure"]
        for phase in result["phases"]
        if phase["pump"]["target"] == "pressure"
    ]

    print(f"  Pressure range: {min(pressures):.1f} - {max(pressures):.1f} bar ✓")
    assert all(1.0 <= p <= 10.0 for p in pressures), "All pressures should be in 1-10 bar range"
    print("✓ All pressures in valid range (1-10 bar)")
