"""Test coverage for variable resolution edge cases."""

import pytest
import warnings
from translate_profile.translator import translate_profile, resolve_variables
from translate_profile.exceptions import UndefinedVariableError


def test_empty_variables_array():
    """Profile with empty variables array should pass through unchanged."""
    profile = {
        "name": "Test",
        "id": "test-1",
        "author": "test",
        "author_id": "test",
        "temperature": 93.0,
        "final_weight": 36.0,
        "variables": [],
        "stages": [
            {
                "name": "Test Stage",
                "key": "test",
                "type": "power",
                "dynamics": {
                    "points": [[0, 50], [10, 80]],
                    "over": "time",
                    "interpolation": "linear",
                },
                "exit_triggers": [],
            }
        ],
    }
    result = resolve_variables(profile)
    assert result["stages"][0]["dynamics"]["points"][0][1] == 50
    assert result["stages"][0]["dynamics"]["points"][1][1] == 80


def test_variables_array_missing():
    """Profile without variables key should pass through unchanged."""
    profile = {
        "name": "Test",
        "id": "test-2",
        "author": "test",
        "author_id": "test",
        "temperature": 93.0,
        "final_weight": 36.0,
        "stages": [
            {
                "name": "Test Stage",
                "key": "test",
                "type": "power",
                "dynamics": {"points": [[0, 50]], "over": "time", "interpolation": "linear"},
                "exit_triggers": [],
            }
        ],
    }
    result = resolve_variables(profile)
    assert result["stages"][0]["dynamics"]["points"][0][1] == 50


def test_word_boundary_matching():
    """$fill should match 'fill' but NOT 'fill_power' or 'fill_extra'."""
    profile = {
        "name": "Word Boundary Test",
        "id": "test-3",
        "author": "test",
        "author_id": "test",
        "temperature": 93.0,
        "final_weight": 36.0,
        "variables": [{"key": "fill", "value": 5.0}, {"key": "fill_power", "value": 9.0}],
        "stages": [
            {
                "name": "Test Stage",
                "key": "test",
                "type": "power",
                "dynamics": {
                    "points": [[0, "$fill"], [5, "$fill_extra"]],
                    "over": "time",
                    "interpolation": "linear",
                },
                "exit_triggers": [],
            }
        ],
    }
    result = resolve_variables(profile)
    assert result["stages"][0]["dynamics"]["points"][0][1] == 5.0
    assert result["stages"][0]["dynamics"]["points"][1][1] == "$fill_extra"


def test_type_coercion_int():
    """Integer variable values should remain int type after resolution."""
    profile = {
        "name": "Int Type Test",
        "id": "test-4",
        "author": "test",
        "author_id": "test",
        "temperature": 93.0,
        "final_weight": 36.0,
        "variables": [{"key": "time", "value": 15}],
        "stages": [
            {
                "name": "Test Stage",
                "key": "test",
                "type": "power",
                "dynamics": {"points": [[0, "$time"]], "over": "time", "interpolation": "linear"},
                "exit_triggers": [],
            }
        ],
    }
    result = resolve_variables(profile)
    resolved_value = result["stages"][0]["dynamics"]["points"][0][1]
    assert isinstance(resolved_value, int), f"Expected int, got {type(resolved_value)}"
    assert resolved_value == 15


def test_type_coercion_float():
    """Float variable values should remain float type after resolution."""
    profile = {
        "name": "Float Type Test",
        "id": "test-5",
        "author": "test",
        "author_id": "test",
        "temperature": 93.0,
        "final_weight": 36.0,
        "variables": [{"key": "pressure", "value": 9.5}],
        "stages": [
            {
                "name": "Test Stage",
                "key": "test",
                "type": "power",
                "dynamics": {
                    "points": [[0, "$pressure"]],
                    "over": "time",
                    "interpolation": "linear",
                },
                "exit_triggers": [],
            }
        ],
    }
    result = resolve_variables(profile)
    resolved_value = result["stages"][0]["dynamics"]["points"][0][1]
    assert isinstance(resolved_value, float), f"Expected float, got {type(resolved_value)}"
    assert resolved_value == 9.5


def test_undefined_variable_error():
    """Undefined variable references should raise UndefinedVariableError."""
    profile = {
        "name": "Undefined Var Test",
        "id": "test-6",
        "author": "test",
        "author_id": "test",
        "temperature": 93.0,
        "final_weight": 36.0,
        "variables": [{"key": "fill", "value": 5.0}],
        "stages": [
            {
                "name": "Test Stage",
                "key": "test",
                "type": "power",
                "dynamics": {
                    "points": [[0, "$undefined_var"]],
                    "over": "time",
                    "interpolation": "linear",
                },
                "exit_triggers": [],
            }
        ],
    }
    with pytest.raises(UndefinedVariableError) as exc_info:
        translate_profile(profile)
    assert "undefined_var" in str(exc_info.value)


def test_cycle_detection_max_depth():
    """Self-referencing variables should raise ValueError when max_depth exceeded."""
    profile = {
        "name": "Cycle Detection Test",
        "id": "test-7",
        "author": "test",
        "author_id": "test",
        "temperature": 93.0,
        "final_weight": 36.0,
        "variables": [{"key": "x", "value": "$x"}],
        "stages": [
            {
                "name": "Test Stage",
                "key": "test",
                "type": "power",
                "dynamics": {"points": [[0, "$x"]], "over": "time", "interpolation": "linear"},
                "exit_triggers": [],
            }
        ],
    }
    with pytest.raises(ValueError) as exc_info:
        resolve_variables(profile, max_depth=2)
    assert "depth" in str(exc_info.value).lower()


def test_unused_variable_warning():
    """Unused defined variables should emit warning without blocking translation."""
    profile = {
        "name": "Unused Var Warning Test",
        "id": "test-8",
        "author": "test",
        "author_id": "test",
        "temperature": 93.0,
        "final_weight": 36.0,
        "variables": [{"key": "used_var", "value": 5.0}, {"key": "unused_var", "value": 10.0}],
        "stages": [
            {
                "name": "Test Stage",
                "key": "test",
                "type": "power",
                "dynamics": {
                    "points": [[0, "$used_var"]],
                    "over": "time",
                    "interpolation": "linear",
                },
                "exit_triggers": [],
            }
        ],
    }
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = resolve_variables(profile)
        assert len(w) >= 1
        warning_messages = [str(warning.message) for warning in w]
        assert any("unused_var" in msg for msg in warning_messages)


def test_ultra_low_contact_translation():
    """Ultra_Low_Contact.json profile should translate successfully."""
    import json
    from pathlib import Path

    profile_path = Path(__file__).parent.parent / "Ultra_Low_Contact.json"
    assert profile_path.exists(), f"Profile not found: {profile_path}"

    with open(profile_path) as f:
        profile = json.load(f)

    result, _ = translate_profile(profile)
    assert result is not None
    assert "label" in result
    assert "phases" in result
    assert len(result["phases"]) > 0
