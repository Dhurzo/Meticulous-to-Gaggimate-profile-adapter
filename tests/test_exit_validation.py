"""
Test suite for exit trigger validation features (VAL-01, VAL-02, VAL-03).

Tests conflicting trigger detection, enhanced duplicate reporting,
and warning categorization.
"""

import pytest

from translate_profile.exit_mode import (
    convert_exit_triggers,
    detect_conflicting_triggers,
)
from translate_profile.models.meticulous import ExitTrigger


# Helper function to create ExitTrigger with default relative=False
def trigger(type: str, comparison: str, value: float, relative: bool = False) -> ExitTrigger:
    """Factory function for creating ExitTrigger objects."""
    return ExitTrigger(type=type, comparison=comparison, value=value, relative=relative)


class TestConflictingTriggerDetection:
    """VAL-01: Conflicting exit triggers generate warnings without breaking translation."""

    def test_conflicting_pressure_triggers_ge_le(self):
        """Test >= X AND <= Y where X <= Y (conditions can never both be true)."""
        triggers = [
            trigger("pressure", ">=", 4.0),
            trigger("pressure", "<=", 2.0),
        ]

        conflicts = detect_conflicting_triggers(triggers)

        assert len(conflicts) == 1
        assert "Conflicting pressure triggers" in conflicts[0]
        assert "pressure >= 4.0" in conflicts[0]
        assert "pressure <= 2.0" in conflicts[0]

    def test_conflicting_pressure_triggers_le_ge(self):
        """Test <= X AND >= Y where X >= Y."""
        triggers = [
            trigger("pressure", "<=", 6.0),
            trigger("pressure", ">=", 8.0),
        ]

        conflicts = detect_conflicting_triggers(triggers)

        assert len(conflicts) == 1
        assert "Conflicting pressure triggers" in conflicts[0]

    def test_conflicting_weight_triggers(self):
        """Test conflicting weight triggers."""
        triggers = [
            trigger("weight", ">=", 36.0),
            trigger("weight", "<=", 30.0),
        ]

        conflicts = detect_conflicting_triggers(triggers)

        assert len(conflicts) == 1
        assert "Conflicting weight triggers" in conflicts[0]

    def test_conflicting_time_triggers(self):
        """Test conflicting time triggers."""
        triggers = [
            trigger("time", ">=", 20.0),
            trigger("time", "<=", 15.0),
        ]

        conflicts = detect_conflicting_triggers(triggers)

        assert len(conflicts) == 1
        assert "Conflicting time triggers" in conflicts[0]

    def test_conflicting_flow_triggers(self):
        """Test conflicting flow triggers."""
        triggers = [
            trigger("flow", ">", 5.0),
            trigger("flow", "<", 3.0),
        ]

        conflicts = detect_conflicting_triggers(triggers)

        assert len(conflicts) == 1
        assert "Conflicting flow triggers" in conflicts[0]

    def test_no_conflict_with_overlapping_ranges(self):
        """Test that overlapping ranges don't trigger conflicts."""
        triggers = [
            trigger("pressure", ">=", 4.0),
            trigger("pressure", "<=", 6.0),
        ]

        conflicts = detect_conflicting_triggers(triggers)

        assert len(conflicts) == 0  # No conflict - ranges overlap

    def test_no_conflict_with_same_direction(self):
        """Test that same-direction triggers don't trigger conflicts."""
        triggers = [
            trigger("pressure", ">=", 4.0),
            trigger("pressure", ">=", 6.0),
        ]

        conflicts = detect_conflicting_triggers(triggers)

        assert len(conflicts) == 0  # No conflict - both >=

    def test_multiple_conflicts_across_types(self):
        """Test detecting conflicts across different trigger types."""
        triggers = [
            trigger("pressure", ">=", 4.0),
            trigger("pressure", "<=", 2.0),
            trigger("weight", ">=", 36.0),
            trigger("weight", "<=", 30.0),
        ]

        conflicts = detect_conflicting_triggers(triggers)

        assert len(conflicts) == 2  # One for pressure, one for weight

    def test_no_conflicts_single_trigger(self):
        """Test that single triggers don't have conflicts."""
        triggers = [
            trigger("pressure", ">=", 4.0),
        ]

        conflicts = detect_conflicting_triggers(triggers)

        assert len(conflicts) == 0


class TestEnhancedDuplicateReporting:
    """VAL-02: Duplicate trigger types are reported with specific details."""

    def test_duplicate_pressure_trigger_specific_warning(self):
        """Test duplicate pressure trigger includes specific trigger details."""
        triggers = [
            trigger("pressure", ">=", 6.0),
            trigger("pressure", ">=", 4.0),
        ]

        targets, warnings = convert_exit_triggers(triggers)

        duplicate_warnings = [w for w in warnings if "duplicate" in w.lower() and "pressure" in w.lower()]
        assert len(duplicate_warnings) == 1
        assert "pressure >= 6.0" in duplicate_warnings[0]
        assert "pressure >= 4.0" in duplicate_warnings[0]

    def test_duplicate_weight_trigger_specific_warning(self):
        """Test duplicate weight trigger includes specific trigger details."""
        triggers = [
            trigger("weight", "<=", 30.0),
            trigger("weight", "<=", 25.0),
        ]

        targets, warnings = convert_exit_triggers(triggers)

        duplicate_warnings = [w for w in warnings if "duplicate" in w.lower() and "weight" in w.lower()]
        assert len(duplicate_warnings) == 1
        assert "weight <= 30.0" in duplicate_warnings[0]
        assert "weight <= 25.0" in duplicate_warnings[0]

    def test_multiple_duplicates_same_type(self):
        """Test multiple duplicates of same type are all reported."""
        triggers = [
            trigger("pressure", ">=", 8.0),
            trigger("pressure", ">=", 6.0),
            trigger("pressure", ">=", 4.0),
        ]

        targets, warnings = convert_exit_triggers(triggers)

        duplicate_warnings = [w for w in warnings if "duplicate" in w.lower()]
        assert len(duplicate_warnings) == 2  # Two duplicates

    def test_no_duplicate_warning_when_unique(self):
        """Test no duplicate warning when all triggers are unique."""
        triggers = [
            trigger("pressure", ">=", 6.0),
            trigger("weight", ">=", 30.0),
            trigger("time", ">=", 20.0),
        ]

        targets, warnings = convert_exit_triggers(triggers)

        duplicate_warnings = [w for w in warnings if "duplicate" in w.lower()]
        assert len(duplicate_warnings) == 0


class TestWarningCategorization:
    """VAL-03: All validation warnings are categorized and surfaced to users."""

    def test_conflict_warnings_categorized(self):
        """Test conflict warnings are categorized as [Validation]."""
        triggers = [
            trigger("pressure", ">=", 4.0),
            trigger("pressure", "<=", 2.0),
        ]

        targets, warnings = convert_exit_triggers(triggers)

        validation_warnings = [w for w in warnings if "[Validation]" in w]
        assert len(validation_warnings) >= 1

    def test_duplicate_warnings_categorized(self):
        """Test duplicate warnings are categorized as [Validation]."""
        triggers = [
            trigger("pressure", ">=", 6.0),
            trigger("pressure", ">=", 4.0),
        ]

        targets, warnings = convert_exit_triggers(triggers)

        validation_warnings = [w for w in warnings if "[Validation]" in w]
        duplicate_warnings = [w for w in validation_warnings if "duplicate" in w.lower()]
        assert len(duplicate_warnings) >= 1

    def test_unsupported_warnings_categorized(self):
        """Test unsupported type warnings are categorized as [Unsupported]."""
        triggers = [
            trigger("piston_position", ">=", 50.0),
        ]

        targets, warnings = convert_exit_triggers(triggers)

        unsupported_warnings = [w for w in warnings if "[Unsupported]" in w]
        assert len(unsupported_warnings) == 1
        assert "piston_position" in unsupported_warnings[0]

    def test_warning_includes_actionable_guidance(self):
        """Test warnings include actionable guidance for users."""
        triggers = [
            trigger("pressure", ">=", 4.0),
            trigger("pressure", "<=", 2.0),
        ]

        targets, warnings = convert_exit_triggers(triggers)

        # Check for actionable guidance in warnings
        assert any("Only the first trigger will be used" in w for w in warnings)

    def test_multiple_warnings_all_categorized(self):
        """Test that multiple warnings of different types are all categorized."""
        triggers = [
            trigger("pressure", ">=", 4.0),
            trigger("pressure", "<=", 2.0),
            trigger("weight", ">=", 36.0),
            trigger("weight", ">=", 30.0),
            trigger("piston_position", ">=", 50.0),
        ]

        targets, warnings = convert_exit_triggers(triggers)

        validation_warnings = [w for w in warnings if "[Validation]" in w]
        unsupported_warnings = [w for w in warnings if "[Unsupported]" in w]

        assert len(validation_warnings) >= 2  # At least 2 conflicts/duplicates
        assert len(unsupported_warnings) == 1

    def test_translation_continues_despite_warnings(self):
        """Test that translation continues and produces valid targets despite warnings."""
        triggers = [
            trigger("pressure", ">=", 4.0),
            trigger("pressure", "<=", 2.0),
            trigger("pressure", ">=", 6.0),
        ]

        targets, warnings = convert_exit_triggers(triggers)

        # Should still produce one target (first valid trigger)
        assert len(targets) == 1
        assert targets[0].type == "pressure"
        assert targets[0].operator == "gte"
        assert targets[0].value == 4.0


class TestIntegrationWithTranslator:
    """Integration tests verifying warnings reach users during translation."""

    def test_convert_exit_triggers_returns_both_targets_and_warnings(self):
        """Test function returns proper tuple structure."""
        triggers = [
            trigger("pressure", ">=", 6.0),
        ]

        result = convert_exit_triggers(triggers)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)  # targets
        assert isinstance(result[1], list)  # warnings

    def test_empty_triggers_returns_empty_results(self):
        """Test empty trigger list returns empty targets and no warnings."""
        targets, warnings = convert_exit_triggers([])

        assert len(targets) == 0
        assert len(warnings) == 0
