import pytest
from translate_profile.translator import translate_profile


def test_metadata_preservation():
    meticulous_data = {
        "name": "Test Profile",
        "id": "met-123",
        "author": "John Doe",
        "author_id": "auth-456",
        "temperature": 93.0,
        "final_weight": 36.0,
        "stages": [
            {
                "name": "Preinfusion",
                "key": "pre",
                "type": "power",
                "dynamics": {"points": [[0, 20]], "over": "time", "interpolation": "linear"},
                "exit_triggers": [
                    {"type": "time", "value": 10.0, "relative": True, "comparison": ">="}
                ],
            }
        ],
    }

    result = translate_profile(meticulous_data)

    assert result["label"] == "Test Profile"
    assert "John Doe" in result["description"]
    assert "met-123" in result["description"]
    assert result["temperature"] == 93.0
    assert result["type"] == "pro"
    assert result["utility"] is False


def test_power_to_pressure_scaling():
    meticulous_data = {
        "name": "Scaling Test",
        "id": "1",
        "author": "test",
        "author_id": "test",
        "temperature": 90.0,
        "final_weight": 40.0,
        "stages": [
            {
                "name": "High Power",
                "key": "high",
                "type": "power",
                "dynamics": {"points": [[0, 100]], "over": "time", "interpolation": "linear"},
                "exit_triggers": [],
            }
        ],
    }

    result = translate_profile(meticulous_data)
    pump = result["phases"][0]["pump"]
    assert pump["target"] == "pressure"
    assert pump["pressure"] == 10.0


def test_flow_to_flow_mapping():
    meticulous_data = {
        "name": "Flow Test",
        "id": "2",
        "author": "test",
        "author_id": "test",
        "temperature": 90.0,
        "final_weight": 40.0,
        "stages": [
            {
                "name": "Fixed Flow",
                "key": "flow",
                "type": "flow",
                "dynamics": {"points": [[0, 2.5]], "over": "time", "interpolation": "linear"},
                "exit_triggers": [],
            }
        ],
    }

    result = translate_profile(meticulous_data)
    pump = result["phases"][0]["pump"]
    assert pump["target"] == "flow"
    assert pump["flow"] == 2.5


def test_exit_triggers_and_operators():
    meticulous_data = {
        "name": "Trigger Test",
        "id": "3",
        "author": "test",
        "author_id": "test",
        "temperature": 90.0,
        "final_weight": 40.0,
        "stages": [
            {
                "name": "Exit",
                "key": "exit",
                "type": "power",
                "dynamics": {"points": [[0, 0]], "over": "time", "interpolation": "linear"},
                "exit_triggers": [
                    {"type": "weight", "value": 36.0, "relative": True, "comparison": ">="},
                    {"type": "time", "value": 45.0, "relative": True, "comparison": "<="},
                    {"type": "pressure", "value": 9.0, "relative": False, "comparison": ">"},
                ],
            }
        ],
    }

    result = translate_profile(meticulous_data)
    targets = result["phases"][0]["targets"]

    assert len(targets) == 3

    assert targets[0]["type"] == "volumetric"
    assert targets[0]["operator"] == "gte"
    assert targets[0]["value"] == 36.0

    assert targets[1]["type"] == "time"
    assert targets[1]["operator"] == "lte"
    assert targets[1]["value"] == 45.0

    assert targets[2]["type"] == "pressure"
    assert targets[2]["operator"] == "gt"
    assert targets[2]["value"] == 9.0


def test_duration_from_trigger():
    meticulous_data = {
        "name": "Duration Test",
        "id": "4",
        "author": "test",
        "author_id": "test",
        "temperature": 90.0,
        "final_weight": 40.0,
        "stages": [
            {
                "name": "Timed",
                "key": "timed",
                "type": "power",
                "dynamics": {"points": [[0, 0]], "over": "time", "interpolation": "linear"},
                "exit_triggers": [
                    {"type": "time", "value": 15.5, "relative": True, "comparison": ">="}
                ],
            }
        ],
    }

    result = translate_profile(meticulous_data)
    assert result["phases"][0]["duration"] == 15.5
