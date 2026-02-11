import pytest
from translate_profile.translator import translate_profile


def test_dynamics_splitting():
    """
    1. A stage with 3 points ([0, 100], [5, 50], [10, 0]) results in 2 Gaggimate phases.
    2. Phase 1 duration is 5s, targets 5.0 pressure (scaled).
    3. Phase 2 duration is 5s, targets 0.0 pressure (scaled).
    4. Transition type is 'linear' for split segments.
    """
    meticulous_data = {
        "id": "test-dynamics",
        "name": "Test Dynamics",
        "author": "Antigravity",
        "author_id": "ag-123",
        "final_weight": 36.0,
        "temperature": 93.0,
        "stages": [
            {
                "name": "Split Stage",
                "key": "Extraction",
                "type": "power",
                "dynamics": {
                    "over": "time",
                    "points": [[0, 100], [5, 50], [10, 0]],
                    "interpolation": "linear",
                },
                "exit_triggers": [],
            }
        ],
    }

    result = translate_profile(meticulous_data)
    phases = result["phases"]

    assert len(phases) == 2

    # Phase 1
    assert phases[0]["name"] == "Split Stage (1/2)"
    assert phases[0]["duration"] == 5.0
    assert phases[0]["pump"]["pressure"] == 5.0
    assert phases[0]["transition"]["type"] == "linear"
    assert phases[0]["transition"]["duration"] == 5.0

    # Phase 2
    assert phases[1]["name"] == "Split Stage (2/2)"
    assert phases[1]["duration"] == 5.0
    assert phases[1]["pump"]["pressure"] == 0.0
    assert phases[1]["transition"]["type"] == "linear"
    assert phases[1]["transition"]["duration"] == 5.0


def test_instant_interpolation_splitting():
    """
    Verify that 'instant' interpolation in Meticulous results in 'instant' transition in Gaggimate.
    """
    meticulous_data = {
        "id": "instant-dynamics",
        "name": "Instant Dynamics",
        "author": "Antigravity",
        "author_id": "ag-123",
        "final_weight": 36.0,
        "temperature": 93.0,
        "stages": [
            {
                "name": "Instant Stage",
                "key": "Extraction",
                "type": "power",
                "dynamics": {
                    "over": "time",
                    "points": [[0, 100], [5, 50]],
                    "interpolation": "instant",
                },
                "exit_triggers": [],
            }
        ],
    }

    result = translate_profile(meticulous_data)
    phases = result["phases"]

    assert len(phases) == 1
    assert phases[0]["transition"]["type"] == "instant"
    assert phases[0]["transition"]["duration"] == 0.0


def test_single_point_stage():
    """
    Verify single-point stage results in one phase with 'instant' transition.
    """
    meticulous_data = {
        "id": "single-point",
        "name": "Single Point",
        "author": "Antigravity",
        "author_id": "ag-123",
        "final_weight": 36.0,
        "temperature": 93.0,
        "stages": [
            {
                "name": "Single",
                "key": "Fill",
                "type": "power",
                "dynamics": {"over": "time", "points": [[0, 50]], "interpolation": "linear"},
                "exit_triggers": [
                    {"type": "time", "value": 15.0, "comparison": ">=", "relative": False}
                ],
            }
        ],
    }

    result = translate_profile(meticulous_data)
    phases = result["phases"]

    assert len(phases) == 1
    assert phases[0]["name"] == "Single"
    assert phases[0]["duration"] == 15.0
    assert phases[0]["pump"]["pressure"] == 5.0
    assert phases[0]["transition"]["type"] == "instant"


def test_phase_mapping():
    """
    1. Verify Meticulous stage type 'Extraction' maps to Gaggimate 'brew' phase.
    2. Verify Meticulous stage type 'Fill' maps to Gaggimate 'preinfusion'.
    """
    meticulous_data = {
        "id": "phase-mapping",
        "name": "Phase Mapping",
        "author": "Antigravity",
        "author_id": "ag-123",
        "final_weight": 36.0,
        "temperature": 93.0,
        "stages": [
            {
                "name": "Preinfusion",
                "key": "Fill",
                "type": "power",
                "dynamics": {"over": "time", "points": [[0, 30]], "interpolation": "linear"},
                "exit_triggers": [],
            },
            {
                "name": "Brew",
                "key": "Extraction",
                "type": "power",
                "dynamics": {"over": "time", "points": [[0, 90]], "interpolation": "linear"},
                "exit_triggers": [],
            },
        ],
    }

    result = translate_profile(meticulous_data)
    phases = result["phases"]

    assert phases[0]["phase"] == "preinfusion"
    assert phases[1]["phase"] == "brew"


def test_multi_point_with_exit_triggers():
    """
    Verify that exit triggers are preserved on the final phase of multi-point stages.
    - Stage with 3 dynamics points and weight trigger
    - Results in 2 phases, only the 2nd phase has the weight target
    """
    meticulous_data = {
        "id": "multi-trigger",
        "name": "Multi Point with Trigger",
        "author": "Test",
        "author_id": "test-123",
        "final_weight": 36.0,
        "temperature": 93.0,
        "stages": [
            {
                "name": "Pressure Ramp",
                "key": "Extraction",
                "type": "power",
                "dynamics": {
                    "over": "time",
                    "points": [[0, 90], [5, 60], [10, 30]],
                    "interpolation": "linear",
                },
                "exit_triggers": [
                    {"type": "weight", "value": 36.0, "comparison": ">=", "relative": False}
                ],
            }
        ],
    }

    result = translate_profile(meticulous_data)
    phases = result["phases"]

    # Should create 2 phases from 3 points
    assert len(phases) == 2

    # First phase - no exit triggers (intermediate segment)
    assert phases[0]["name"] == "Pressure Ramp (1/2)"
    assert phases[0]["targets"] == []

    # Second phase - has the exit trigger (final segment)
    assert phases[1]["name"] == "Pressure Ramp (2/2)"
    assert len(phases[1]["targets"]) == 1
    assert phases[1]["targets"][0]["type"] == "volumetric"  # weight -> volumetric
    assert phases[1]["targets"][0]["operator"] == "gte"  # >= -> gte
    assert phases[1]["targets"][0]["value"] == 36.0
