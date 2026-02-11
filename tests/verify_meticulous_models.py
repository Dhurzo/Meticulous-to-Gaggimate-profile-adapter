import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from translate_profile.models.meticulous import MeticulousProfile
from pydantic import ValidationError


def test_variable_rejection():
    print("Testing variable rejection...")
    invalid_data = {
        "name": "Test",
        "id": "123",
        "author": "Me",
        "author_id": "456",
        "temperature": 90.0,
        "final_weight": 40.0,
        "stages": [
            {
                "name": "Fill",
                "key": "fill_1",
                "type": "power",
                "dynamics": {
                    "points": [[0, "$fill_power"]],
                    "over": "time",
                    "interpolation": "linear",
                },
                "exit_triggers": [],
                "limits": [],
            }
        ],
    }

    try:
        MeticulousProfile(**invalid_data)
        print("FAILED: MeticulousProfile accepted a string variable in a numeric field")
        sys.exit(1)
    except ValidationError as e:
        print(f"SUCCESS: Caught expected ValidationError: {e}")


def test_concrete_success():
    print("Testing concrete numeric success...")
    valid_data = {
        "name": "Test",
        "id": "123",
        "author": "Me",
        "author_id": "456",
        "temperature": 90.0,
        "final_weight": 40.0,
        "stages": [
            {
                "name": "Fill",
                "key": "fill_1",
                "type": "power",
                "dynamics": {"points": [[0, 100.0]], "over": "time", "interpolation": "linear"},
                "exit_triggers": [
                    {"type": "pressure", "value": 1.5, "relative": False, "comparison": ">="}
                ],
                "limits": [],
            }
        ],
    }

    try:
        MeticulousProfile(**valid_data)
        print("SUCCESS: MeticulousProfile accepted concrete numeric values")
    except ValidationError as e:
        print(f"FAILED: MeticulousProfile rejected valid data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_variable_rejection()
    test_concrete_success()
    print("All tests passed!")
