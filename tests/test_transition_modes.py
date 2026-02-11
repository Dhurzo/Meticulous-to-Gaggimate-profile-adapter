"""Tests for transition mode functionality."""
import pytest
from src.translate_profile.translator import (
    translate_profile,
    SMART_INTERPOLATION_MAP,
    PRESERVE_INTERPOLATION_MAP,
    TRANSITION_MODE_SMART,
    TRANSITION_MODE_PRESERVE,
    TRANSITION_MODE_LINEAR,
    TRANSITION_MODE_INSTANT,
)


def create_test_profile(interpolation_type: str) -> dict:
    """Create a minimal Meticulous profile with specified interpolation type."""
    return {
        "name": f"Test {interpolation_type}",
        "id": f"test-{interpolation_type}",
        "author": "test",
        "author_id": "test",
        "temperature": 93.0,
        "final_weight": 30.0,
        "stages": [
            {
                "name": "Test Stage",
                "key": "Fill",
                "type": "power",
                "dynamics": {
                    "points": [[0, 50], [10, 50]],
                    "over": "time",
                    "interpolation": interpolation_type,
                },
                "exit_triggers": [],
            }
        ],
    }


class TestSmartMode:
    """Tests for smart transition mode - intelligent mapping."""

    def test_smart_mode_linear_interpolation(self):
        """Verify linear interpolation maps to linear transition."""
        profile = create_test_profile("linear")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        assert result["phases"][0]["transition"]["type"] == "linear"

    def test_smart_mode_step_interpolation(self):
        """Verify step interpolation maps to linear transition."""
        profile = create_test_profile("step")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        assert result["phases"][0]["transition"]["type"] == "linear"

    def test_smart_mode_instant_interpolation(self):
        """Verify instant interpolation maps to instant transition."""
        profile = create_test_profile("instant")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        assert result["phases"][0]["transition"]["type"] == "instant"

    def test_smart_mode_bezier_interpolation(self):
        """Verify bezier interpolation maps to ease-in-out transition."""
        profile = create_test_profile("bezier")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        assert result["phases"][0]["transition"]["type"] == "ease-in-out"

    def test_smart_mode_spline_interpolation(self):
        """Verify spline interpolation maps to ease-in-out transition."""
        profile = create_test_profile("spline")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        assert result["phases"][0]["transition"]["type"] == "ease-in-out"


class TestPreserveMode:
    """Tests for preserve transition mode - 1:1 mapping."""

    def test_preserve_mode_linear_interpolation(self):
        """Verify linear interpolation maps to linear transition."""
        profile = create_test_profile("linear")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_PRESERVE)
        assert result["phases"][0]["transition"]["type"] == "linear"

    def test_preserve_mode_step_interpolation(self):
        """Verify step interpolation maps to linear transition."""
        profile = create_test_profile("step")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_PRESERVE)
        assert result["phases"][0]["transition"]["type"] == "linear"

    def test_preserve_mode_instant_interpolation(self):
        """Verify instant interpolation maps to linear transition (not instant)."""
        profile = create_test_profile("instant")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_PRESERVE)
        assert result["phases"][0]["transition"]["type"] == "linear"

    def test_preserve_mode_bezier_interpolation(self):
        """Verify bezier interpolation is preserved as bezier."""
        profile = create_test_profile("bezier")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_PRESERVE)
        assert result["phases"][0]["transition"]["type"] == "bezier"

    def test_preserve_mode_spline_interpolation(self):
        """Verify spline interpolation is preserved as spline."""
        profile = create_test_profile("spline")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_PRESERVE)
        assert result["phases"][0]["transition"]["type"] == "spline"


class TestLinearMode:
    """Tests for linear transition mode - forces linear."""

    def test_linear_mode_forces_linear_for_linear(self):
        """Verify linear mode forces linear for linear interpolation."""
        profile = create_test_profile("linear")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_LINEAR)
        assert result["phases"][0]["transition"]["type"] == "linear"

    def test_linear_mode_forces_linear_for_bezier(self):
        """Verify linear mode forces linear for bezier interpolation."""
        profile = create_test_profile("bezier")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_LINEAR)
        assert result["phases"][0]["transition"]["type"] == "linear"

    def test_linear_mode_forces_linear_for_instant(self):
        """Verify linear mode forces linear for instant interpolation."""
        profile = create_test_profile("instant")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_LINEAR)
        assert result["phases"][0]["transition"]["type"] == "linear"


class TestInstantMode:
    """Tests for instant transition mode - forces instant."""

    def test_instant_mode_forces_instant_for_linear(self):
        """Verify instant mode forces instant for linear interpolation."""
        profile = create_test_profile("linear")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_INSTANT)
        assert result["phases"][0]["transition"]["type"] == "instant"

    def test_instant_mode_forces_instant_for_bezier(self):
        """Verify instant mode forces instant for bezier interpolation."""
        profile = create_test_profile("bezier")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_INSTANT)
        assert result["phases"][0]["transition"]["type"] == "instant"

    def test_instant_mode_forces_instant_for_spline(self):
        """Verify instant mode forces instant for spline interpolation."""
        profile = create_test_profile("spline")
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_INSTANT)
        assert result["phases"][0]["transition"]["type"] == "instant"


class TestMultiPointDynamics:
    """Tests for transition modes with multi-point dynamics."""

    def test_smart_mode_multi_point_bezier(self):
        """Verify smart mode works correctly with multi-point dynamics."""
        profile = {
            "name": "Multi-point Test",
            "id": "test-multi",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Ramp",
                    "key": "Extraction",
                    "type": "pressure",
                    "dynamics": {
                        "points": [[0, 2], [5, 6], [10, 9]],
                        "over": "time",
                        "interpolation": "bezier",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Should have 2 phases from splitting the multi-point stage
        assert len(result["phases"]) == 2
        # Both should have ease-in-out transition
        assert result["phases"][0]["transition"]["type"] == "ease-in-out"
        assert result["phases"][1]["transition"]["type"] == "ease-in-out"

    def test_preserve_mode_multi_point_spline(self):
        """Verify preserve mode works correctly with multi-point dynamics."""
        profile = {
            "name": "Multi-point Test",
            "id": "test-multi",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Ramp",
                    "key": "Extraction",
                    "type": "pressure",
                    "dynamics": {
                        "points": [[0, 2], [5, 6], [10, 9]],
                        "over": "time",
                        "interpolation": "spline",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_PRESERVE)
        # Should have 2 phases from splitting
        assert len(result["phases"]) == 2
        # Both should preserve spline
        assert result["phases"][0]["transition"]["type"] == "spline"
        assert result["phases"][1]["transition"]["type"] == "spline"


class TestPhantomPhases:
    """Tests for phantom phase detection and prevention."""

    def test_single_point_no_phantom_phases(self):
        """Verify single-point stages produce exactly 1 phase (no phantom phases)."""
        profile = {
            "name": "Single Point Test",
            "id": "test-single",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Single Point Stage",
                    "key": "Fill",
                    "type": "power",
                    "dynamics": {
                        "points": [[0, 50]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Single-point stage should produce exactly 1 phase
        assert len(result["phases"]) == 1

    def test_multi_point_correct_phase_count(self):
        """Verify 3-point stage produces exactly 2 phases (num_points - 1)."""
        profile = {
            "name": "Multi Point Test",
            "id": "test-multi",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Multi Point Stage",
                    "key": "Extraction",
                    "type": "pressure",
                    "dynamics": {
                        "points": [[0, 2], [5, 6], [10, 9]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # 3-point stage should produce exactly 2 phases
        assert len(result["phases"]) == 2

    def test_empty_dynamics_no_phases(self):
        """Verify empty points array doesn't cause crashes and handles gracefully."""
        profile = {
            "name": "Empty Dynamics Test",
            "id": "test-empty",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Empty Stage",
                    "key": "Fill",
                    "type": "power",
                    "dynamics": {
                        "points": [],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        # Should not raise an exception
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Result should still have phases (using default behavior)
        assert "phases" in result


class TestDurationPreservation:
    """Tests for duration preservation - exit triggers define phase duration."""

    def test_time_exit_trigger_preserved(self):
        """Verify time-based exit trigger defines duration and is not overwritten."""
        profile = {
            "name": "Time Trigger Test",
            "id": "test-time-trigger",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Test Stage",
                    "key": "Fill",
                    "type": "pressure",
                    "dynamics": {
                        "points": [[0, 2]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [
                        {"type": "time", "comparison": ">=", "value": 20.0, "relative": False}
                    ],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Duration should be 20.0 from exit trigger, NOT calculated from pressure delta
        assert result["phases"][0]["duration"] == 20.0

    def test_no_exit_trigger_uses_calculation(self):
        """Verify no exit triggers uses calculated duration (not 30.0 default)."""
        profile = {
            "name": "No Trigger Test",
            "id": "test-no-trigger",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Test Stage",
                    "key": "Fill",
                    "type": "pressure",
                    "dynamics": {
                        "points": [[0, 5]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Without exit triggers, duration should be calculated from pressure delta
        # Without exit triggers, duration should be calculated from pressure delta
        # Pressure delta = |5.0 - 0.0| = 5.0, which is normal range → 4.0s duration
        duration = result["phases"][0]["duration"]
        assert duration > 0.1  # Should be calculated, not default
        assert duration != 30.0  # Should NOT be the default fallback

    def test_pressure_stage_duration_calculated(self):
        """Verify pressure stage without exit triggers uses pressure delta calculation."""
        profile = {
            "name": "Pressure Calculation Test",
            "id": "test-pressure-calc",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Pressure Stage",
                    "key": "Extraction",
                    "type": "pressure",
                    "dynamics": {
                        "points": [[0, 8]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Pressure delta = |8.0 - 0.0| = 8.0, which is large (>3.0) → 1.5s duration
        duration = result["phases"][0]["duration"]
        assert duration == 1.5  # Large pressure delta = short duration

    def test_preinfusion_20s_duration(self):
        """Verify preinfusion flow stage with 20s time trigger maintains 20s duration."""
        profile = {
            "name": "Preinfusion Test",
            "id": "test-preinfusion",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Preinfusion",
                    "key": "Fill",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 2]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [
                        {"type": "time", "comparison": ">=", "value": 20.0, "relative": False}
                    ],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Flow stage with 20s time trigger should have duration = 20.0
        # NOT overwritten by pressure delta calculation (pressure delta is 0 for flow stages)
        assert result["phases"][0]["duration"] == 20.0


class TestFlowPumpMapping:
    """Tests for flow pump target mapping."""

    def test_flow_stage_uses_flow_target(self):
        """Verify flow stage uses target='flow' for non-bloom flow."""
        profile = {
            "name": "Flow Stage Test",
            "id": "test-flow",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Fill Phase",
                    "key": "Fill",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 2]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        assert result["phases"][0]["pump"]["target"] == "flow"

    def test_pressure_stage_uses_pressure_target(self):
        """Verify pressure stage uses target='pressure'."""
        profile = {
            "name": "Pressure Stage Test",
            "id": "test-pressure",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Extraction Phase",
                    "key": "Extraction",
                    "type": "pressure",
                    "dynamics": {
                        "points": [[0, 5]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        assert result["phases"][0]["pump"]["target"] == "pressure"


class TestBloomSemantics:
    """Tests for bloom phase semantics - zero-flow pressure-hold behavior."""

    def test_bloom_stage_uses_pressure_target(self):
        """Verify bloom stage uses target='pressure' instead of flow."""
        profile = {
            "name": "Bloom Stage Test",
            "id": "test-bloom",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Bloom",
                    "key": "blooming",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 0]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        assert result["phases"][0]["pump"]["target"] == "pressure"

    def test_bloom_stage_zero_flow(self):
        """Verify bloom stage has flow=0 (no water pushing)."""
        profile = {
            "name": "Bloom Zero Flow Test",
            "id": "test-bloom-zero",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Bloom",
                    "key": "blooming",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 0.05]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        assert result["phases"][0]["pump"]["flow"] == 0

    def test_bloom_stage_uses_bloom_pressure(self):
        """Verify bloom stage uses MIN_BLOOM_PRESSURE (2.0 bar)."""
        from src.translate_profile.translator import MIN_BLOOM_PRESSURE

        profile = {
            "name": "Bloom Pressure Test",
            "id": "test-bloom-pressure",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Bloom",
                    "key": "blooming",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 0]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        assert result["phases"][0]["pump"]["pressure"] == MIN_BLOOM_PRESSURE

    def test_non_bloom_flow_stage_uses_flow_target(self):
        """Verify non-bloom flow stage (key='Fill') uses target='flow'."""
        profile = {
            "name": "Non-Bloom Flow Test",
            "id": "test-fill-flow",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Fill",
                    "key": "Fill",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 3]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Should use flow target, not pressure
        assert result["phases"][0]["pump"]["target"] == "flow"
        assert result["phases"][0]["pump"]["flow"] == 3.0

    def test_bloom_multi_point_uses_pressure(self):
        """Verify bloom stage with multiple points uses pressure target."""
        profile = {
            "name": "Bloom Multi-Point Test",
            "id": "test-bloom-multi",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Bloom",
                    "key": "blooming",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 0], [5, 0.05]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Multi-point stage should produce 1 phase (from split)
        assert len(result["phases"]) == 1
        # The phase should use pressure target for bloom
        assert result["phases"][0]["pump"]["target"] == "pressure"


class TestStageTypeTransitions:
    """Tests for stage-type-aware transition mapping - flow stages use instant transitions."""

    def test_flow_stage_uses_instant_regardless_of_interpolation(self):
        """Verify flow stage with bezier interpolation uses instant transition."""
        profile = {
            "name": "Flow Bezier Test",
            "id": "test-flow-bezier",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Flow Ramp",
                    "key": "Fill",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 2]],
                        "over": "time",
                        "interpolation": "bezier",
                    },
                    "exit_triggers": [
                        {"type": "time", "comparison": ">=", "value": 10.0, "relative": False}
                    ],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Flow stage should use instant transition, not ease-in-out from bezier
        assert result["phases"][0]["transition"]["type"] == "instant"

    def test_flow_stage_instant_with_linear_interpolation(self):
        """Verify flow stage with linear interpolation uses instant transition."""
        profile = {
            "name": "Flow Linear Test",
            "id": "test-flow-linear",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Flow Stage",
                    "key": "Fill",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 3]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [
                        {"type": "time", "comparison": ">=", "value": 15.0, "relative": False}
                    ],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Flow stage should use instant transition even with linear interpolation
        assert result["phases"][0]["transition"]["type"] == "instant"

    def test_pressure_stage_uses_interpolation_mapping(self):
        """Verify pressure stage uses interpolation mapping (bezier -> ease-in-out)."""
        profile = {
            "name": "Pressure Bezier Test",
            "id": "test-pressure-bezier",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Pressure Ramp",
                    "key": "Extraction",
                    "type": "pressure",
                    "dynamics": {
                        "points": [[0, 5]],
                        "over": "time",
                        "interpolation": "bezier",
                    },
                    "exit_triggers": [
                        {"type": "time", "comparison": ">=", "value": 20.0, "relative": False}
                    ],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Pressure stage should use ease-in-out from bezier mapping
        assert result["phases"][0]["transition"]["type"] == "ease-in-out"

    def test_multi_point_flow_stage_uses_instant(self):
        """Verify multi-point flow stage uses instant transitions for all phases."""
        profile = {
            "name": "Multi-Point Flow Test",
            "id": "test-multi-flow",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Flow Ramp",
                    "key": "Extraction",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 2], [5, 4], [10, 6]],
                        "over": "time",
                        "interpolation": "bezier",
                    },
                    "exit_triggers": [],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)
        # Multi-point stage should produce 2 phases (3 points - 1)
        assert len(result["phases"]) == 2
        # Both phases should use instant transition
        assert result["phases"][0]["transition"]["type"] == "instant"
        assert result["phases"][1]["transition"]["type"] == "instant"

    def test_preserve_mode_flow_stage_instant(self):
        """Verify flow stage uses instant in preserve mode (stage type overrides)."""
        profile = {
            "name": "Flow Preserve Test",
            "id": "test-flow-preserve",
            "author": "test",
            "author_id": "test",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Flow Stage",
                    "key": "Fill",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 2]],
                        "over": "time",
                        "interpolation": "bezier",
                    },
                    "exit_triggers": [
                        {"type": "time", "comparison": ">=", "value": 10.0, "relative": False}
                    ],
                }
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_PRESERVE)
        # Flow stage should use instant transition (stage type override)
        assert result["phases"][0]["transition"]["type"] == "instant"


class TestExDosIntegration:
    """Integration tests for ExDos profile translation."""

    def test_exdos_profile_translation(self):
        """Verify ExDos profile translates with behavioral equivalence after all fixes."""
        # Create an ExDos-like profile matching the known structure
        profile = {
            "name": "Extractamundo Dos! Gaggimate",
            "id": "exdos-test",
            "author": "Meticulous User",
            "author_id": "user123",
            "temperature": 93.0,
            "final_weight": 30.0,
            "stages": [
                {
                    "name": "Preinfusion",
                    "key": "Fill",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 2]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [
                        {"type": "time", "comparison": ">=", "value": 20.0, "relative": False}
                    ],
                },
                {
                    "name": "Bloom",
                    "key": "blooming",
                    "type": "flow",
                    "dynamics": {
                        "points": [[0, 0]],
                        "over": "time",
                        "interpolation": "linear",
                    },
                    "exit_triggers": [
                        {"type": "time", "comparison": ">=", "value": 5.0, "relative": False}
                    ],
                },
                {
                    "name": "Ramp",
                    "key": "Extraction",
                    "type": "pressure",
                    "dynamics": {
                        "points": [[0, 2], [10, 9]],
                        "over": "time",
                        "interpolation": "bezier",
                    },
                    "exit_triggers": [
                        {"type": "weight", "comparison": ">=", "value": 30.0, "relative": False}
                    ],
                },
            ],
        }
        result, _ = translate_profile(profile, transition_mode=TRANSITION_MODE_SMART)

        # Verify correct number of phases (no phantom phases)
        # Preinfusion: 1 phase, Bloom: 1 phase, Ramp: 1 phase (2 points = 1 segment)
        assert len(result["phases"]) == 3

        # Verify Preinfusion phase
        preinfusion = result["phases"][0]
        assert preinfusion["phase"] == "preinfusion"
        assert preinfusion["pump"]["target"] == "flow"
        assert preinfusion["duration"] == 20.0  # From time exit trigger
        assert preinfusion["transition"]["type"] == "instant"  # Flow stage uses instant

        # Verify Bloom phase
        bloom = result["phases"][1]
        assert bloom["phase"] == "preinfusion"
        assert bloom["pump"]["target"] == "pressure"  # Bloom uses pressure target
        assert bloom["pump"]["flow"] == 0  # Zero-flow for bloom
        assert bloom["pump"]["pressure"] == 2.0  # MIN_BLOOM_PRESSURE
        assert bloom["transition"]["type"] == "instant"  # Flow stage uses instant

        # Verify Ramp phase
        ramp = result["phases"][2]
        assert ramp["phase"] == "brew"
        assert ramp["pump"]["target"] == "pressure"
        assert ramp["transition"]["type"] == "ease-in-out"  # Pressure stage uses interpolation mapping
