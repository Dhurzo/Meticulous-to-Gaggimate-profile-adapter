import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from translate_profile.models.gaggimate import GaggimatePhase
from pydantic import ValidationError


def test_range_validation():
    print("Testing range validation...")

    # Invalid temp
    try:
        GaggimatePhase(
            name="Test",
            phase="preinfusion",
            valve=1,
            duration=10,
            temperature=200,
            transition={"type": "instant", "duration": 0, "adaptive": True},
            pump=0,
            targets=[],
        )
        print("FAILED: Accepted temperature=200")
        sys.exit(1)
    except ValidationError:
        print("SUCCESS: Rejected temperature=200")

    # Invalid pressure
    try:
        GaggimatePhase(
            name="Test",
            phase="preinfusion",
            valve=1,
            duration=10,
            temperature=90,
            transition={"type": "instant", "duration": 0, "adaptive": True},
            pump={"target": "flow", "pressure": 20, "flow": 2},
            targets=[],
        )
        print("FAILED: Accepted pressure=20")
        sys.exit(1)
    except ValidationError:
        print("SUCCESS: Rejected pressure=20")

    # Invalid duration (gt 0)
    try:
        GaggimatePhase(
            name="Test",
            phase="preinfusion",
            valve=1,
            duration=0,
            temperature=90,
            transition={"type": "instant", "duration": 0, "adaptive": True},
            pump=0,
            targets=[],
        )
        print("FAILED: Accepted duration=0")
        sys.exit(1)
    except ValidationError:
        print("SUCCESS: Rejected duration=0")


def test_valid_instantiation():
    print("Testing valid instantiation...")
    try:
        GaggimatePhase(
            name="Test",
            phase="preinfusion",
            valve=1,
            duration=1.5,
            temperature=90,
            transition={"type": "instant", "duration": 0, "adaptive": True},
            pump={"target": "flow", "pressure": 9, "flow": 2.4},
            targets=[{"type": "pressure", "operator": "gte", "value": 0.7}],
        )
        print("SUCCESS: Accepted valid GaggimatePhase")
    except ValidationError as e:
        print(f"FAILED: Rejected valid data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_range_validation()
    test_valid_instantiation()
    print("All tests passed!")
