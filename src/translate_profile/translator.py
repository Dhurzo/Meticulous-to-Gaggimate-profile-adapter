import re
import warnings
from typing import Any

# Typical brewing pressure range (bar)
MIN_PRESSURE = 1.0
MAX_PRESSURE = 10.0

# Bloom phase pressure (for pressure-hold behavior during bloom)
MIN_BLOOM_PRESSURE = 2.0

# Transition mode constants
TRANSITION_MODE_SMART = "smart"
TRANSITION_MODE_PRESERVE = "preserve"
TRANSITION_MODE_LINEAR = "linear"
TRANSITION_MODE_INSTANT = "instant"

# Interpolation to transition type mapping for smart mode
SMART_INTERPOLATION_MAP = {
    "linear": "linear",
    "step": "linear",
    "instant": "instant",
    "bezier": "ease-in-out",
    "spline": "ease-in-out",
}

# Preserve mode mapping (1:1 mapping)
PRESERVE_INTERPOLATION_MAP = {
    "linear": "linear",
    "step": "linear",
    "instant": "linear",
    "bezier": "bezier",
    "spline": "spline",
}


def calculate_transition_duration(
    pressure_delta: float,
    transition_type: str,
    mode: str = TRANSITION_MODE_SMART
) -> float:
    """
    Calculate transition duration based on pressure delta and mode.

    Args:
        pressure_delta: Absolute pressure difference between phases (bar)
        transition_type: The target transition type (ease-out, linear, etc.)
        mode: Transition mode (smart, preserve, linear, instant)

    Returns:
        Duration in seconds for the transition
    """
    # Instant transitions always have 0 duration
    if transition_type == "instant":
        return 0.0

    # For non-instant transitions, calculate duration based on pressure delta
    # and mode
    if mode == TRANSITION_MODE_PRESERVE:
        # Preserve mode uses phase duration (simplified)
        return 5.0  # Default fallback

    # Smart mode: pressure-aware duration
    if pressure_delta > 3.0:
        # Large pressure jump: short duration (1-2 seconds)
        return 1.5
    elif pressure_delta < 1.0:
        # Small pressure change: longer duration (5-10 seconds)
        return 7.0
    else:
        # Normal pressure change: medium duration (3-5 seconds)
        return 4.0


def validate_pressure_range(pressure: float, stage_name: str) -> None:
    """Warn if pressure is outside typical brewing range."""
    if pressure < MIN_PRESSURE or pressure > MAX_PRESSURE:
        warnings.warn(
            f"Stage '{stage_name}': pressure {pressure:.1f} bar is outside "
            f"typical range ({MIN_PRESSURE}-{MAX_PRESSURE} bar). "
            f"Check if this is intentional."
        )


from .models.gaggimate import (
    ExitTarget,
    GaggimatePhase,
    GaggimateProfile,
    PumpSettings,
    TransitionSettings,
)
from .models.meticulous import ExitTrigger, MeticulousProfile
from .exit_mode import convert_exit_triggers

VAR_PATTERN = re.compile(r"\$(\w+)\b")


def resolve_variables(data: dict[str, Any], max_depth: int = 10) -> dict[str, Any]:
    """
    Resolve variable references ($var_name) in Meticulous profile data.
    Variables are defined in the 'variables' array with 'key' (without $) and 'value'.

    Args:
        data: Profile data with variables array
        max_depth: Maximum resolution depth to prevent infinite loops
    """
    import warnings

    variables = data.get("variables", [])

    # Handle empty or missing variables array
    if not variables:
        # Empty variables array - no substitutions to make
        # Just pass through stages unchanged
        return data

    var_lookup = {v.get("key", ""): v.get("value") for v in variables}

    def resolve_value(val: Any, depth: int = 0) -> Any:
        if depth > max_depth:
            raise ValueError(f"Variable resolution exceeded max depth {max_depth}")

        if isinstance(val, str) and val.startswith("$"):
            match = VAR_PATTERN.match(val)
            if match:
                var_key = match.group(1)
                if var_key in var_lookup:
                    raw_value = var_lookup[var_key]
                    resolved = resolve_value(raw_value, depth + 1)
                    # Coerce to proper numeric type after full resolution
                    if isinstance(resolved, int):
                        return int(resolved)
                    elif isinstance(resolved, float):
                        return float(resolved)
                    return resolved
            return val
        return val

    def resolve_points(points: list[list[Any]]) -> list[list[Any]]:
        return [[resolve_value(p[0]), resolve_value(p[1])] for p in points]

    def resolve_exit_triggers(triggers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{**t, "value": resolve_value(t.get("value", 0))} for t in triggers]

    def resolve_limits(limits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Resolve variable references in limits array."""
        return [{**l, "value": resolve_value(l.get("value", 0))} for l in limits]

    def resolve_stage(stage: dict[str, Any]) -> dict[str, Any]:
        return {
            **stage,
            "dynamics": {
                **stage.get("dynamics", {}),
                "points": resolve_points(stage.get("dynamics", {}).get("points", [])),
            },
            "exit_triggers": resolve_exit_triggers(stage.get("exit_triggers", [])),
            "limits": resolve_limits(stage.get("limits", [])),
        }

    # Resolve all stages
    data["stages"] = [resolve_stage(s) for s in data.get("stages", [])]

    # Find unused variables and warn
    def find_unused_variables(data: dict[str, Any]) -> list[str]:
        """Find variables that are defined but never referenced."""
        variables = data.get("variables", [])
        if not variables:
            return []

        var_keys = {v.get("key", "") for v in variables}
        used_keys = set()

        # Check all known locations for $variable usage
        def check_for_usage(val: Any) -> None:
            if isinstance(val, str) and val.startswith("$"):
                match = VAR_PATTERN.match(val)
                if match:
                    used_keys.add(match.group(1))

        for stage in data.get("stages", []):
            for point in stage.get("dynamics", {}).get("points", []):
                check_for_usage(point[0])
                check_for_usage(point[1])
            for trigger in stage.get("exit_triggers", []):
                check_for_usage(trigger.get("value"))
            for limit in stage.get("limits", []):
                check_for_usage(limit.get("value"))

        return [v.get("key") for v in variables if v.get("key") not in used_keys]

    unused = find_unused_variables(data)
    if unused:
        warnings.warn(f"Unused variables: {', '.join(unused)}")

    return data


def find_unresolved_variables(data: dict[str, Any]) -> list[dict[str, str]]:
    """
    Scan data for $variable references that don't have corresponding definitions.
    Returns list of {variable: str, location: str} for all unresolved refs.
    """
    unresolved = []
    variables = data.get("variables", [])
    var_keys = {v.get("key", "") for v in variables}

    def check_value(val: Any, path: str) -> None:
        if isinstance(val, str) and val.startswith("$"):
            var_key = val[1:]
            if var_key not in var_keys:
                unresolved.append({"variable": val, "location": path})

    # Check stages
    for i, stage in enumerate(data.get("stages", [])):
        # Check dynamics points
        for j, point in enumerate(stage.get("dynamics", {}).get("points", [])):
            check_value(point[0], f"stages[{i}].dynamics.points[{j}][0]")
            check_value(point[1], f"stages[{i}].dynamics.points[{j}][1]")

        # Check exit triggers
        for k, trigger in enumerate(stage.get("exit_triggers", [])):
            check_value(trigger.get("value"), f"stages[{i}].exit_triggers[{k}].value")

        # Check limits
        for k, limit in enumerate(stage.get("limits", [])):
            check_value(limit.get("value"), f"stages[{i}].limits[{k}].value")

    return unresolved


def translate_profile(
    meticulous_data: dict[str, Any],
    transition_mode: str = TRANSITION_MODE_SMART
) -> dict[str, Any]:
    """
    Translates a Meticulous profile to Gaggimate format.

    Args:
        meticulous_data: Meticulous profile data as dictionary
        transition_mode: Transition mode - "smart", "preserve", "linear", or "instant"
    """
    from .exceptions import UndefinedVariableError

    # Resolve variable references ($var_name) to concrete values
    meticulous_data = resolve_variables(meticulous_data)

    # Check for unresolved variables and enhance error
    unresolved = find_unresolved_variables(meticulous_data)
    if unresolved:
        var_names = ", ".join(u["variable"] for u in unresolved)
        locations = "; ".join(u["location"] for u in unresolved)
        raise UndefinedVariableError(variable_name=var_names, location=locations)

    # Load input into MeticulousProfile model
    meticulous = MeticulousProfile(**meticulous_data)

    # Preserve metadata (TRAN-10)
    # Include author and id in the description
    description = (
        f"Meticulous ID: {meticulous.id}\n"
        f"Author: {meticulous.author}\n"
        f"Original Name: {meticulous.name}"
    )

    phases: list[GaggimatePhase] = []

    # Mapping for Meticulous stage keys to Gaggimate phase types (Task 2)
    phase_type_map = {"Fill": "preinfusion", "Bloom": "preinfusion", "blooming": "preinfusion", "Extraction": "brew"}

    for stage in meticulous.stages:
        num_points = len(stage.dynamics.points)

        if num_points <= 1:
            # Single point stage logic
            target_value = stage.dynamics.points[0][1] if num_points == 1 else 0.0

            # Map stage type to pump target
            if stage.type == "power":
                pump = PumpSettings(
                    target="pressure",
                    pressure=target_value / 10.0,
                    flow=10.0,
                )
            elif stage.type == "flow":
                # Check for bloom semantics: zero/near-zero flow with bloom key
                is_bloom = (stage.key.startswith("blooming") and target_value <= 0.1)

                if is_bloom:
                    # Bloom semantics: zero-flow, pressure-hold behavior
                    pump = PumpSettings(
                        target="pressure",
                        pressure=MIN_BLOOM_PRESSURE,
                        flow=0,
                    )
                else:
                    # Standard flow stage
                    pump = PumpSettings(
                        target="flow",
                        flow=target_value,
                        pressure=12.0,
                    )
            elif stage.type == "pressure":
                pump = PumpSettings(
                    target="pressure",
                    pressure=target_value,
                    flow=10.0,
                )
                # Validate pressure range
                validate_pressure_range(target_value, stage.name)
            else:
                raise ValueError(
                    f"Unknown stage type: {stage.type}. Expected 'power', 'flow', or 'pressure'."
                )

            duration = 30.0
            for trigger in stage.exit_triggers:
                if trigger.type == "time":
                    duration = trigger.value
                    break

            if duration <= 0:
                duration = 0.1

            # Convert exit triggers for single-point stage
            targets, warnings_list = convert_exit_triggers(stage.exit_triggers, phase_start_time=0.0)
            for warning in warnings_list:
                warnings.warn(f"Stage '{stage.name}': {warning}")

            # Determine transition type based on mode
            if transition_mode == TRANSITION_MODE_SMART:
                # Flow stages use instant transitions regardless of interpolation
                if stage.type == "flow":
                    transition_type = "instant"
                else:
                    transition_type = SMART_INTERPOLATION_MAP.get(
                        stage.dynamics.interpolation, "linear"
                    )
            elif transition_mode == TRANSITION_MODE_PRESERVE:
                # Flow stages use instant transitions regardless of interpolation
                if stage.type == "flow":
                    transition_type = "instant"
                else:
                    transition_type = PRESERVE_INTERPOLATION_MAP.get(
                        stage.dynamics.interpolation, "linear"
                    )
            elif transition_mode == TRANSITION_MODE_LINEAR:
                # Force linear for everything except instant
                if stage.dynamics.interpolation == "instant":
                    transition_type = "linear"
                else:
                    transition_type = "linear"
            else:  # INSTANT mode
                transition_type = "instant"

            # Calculate duration based on pressure delta - ONLY if no time-based exit trigger
            # Time triggers define actual phase duration, pressure_delta is for transitions
            time_trigger_found = False
            for trigger in stage.exit_triggers:
                if trigger.type == "time":
                    time_trigger_found = True
                    break

            if not time_trigger_found:
                target_pressure = stage.dynamics.points[0][1] if len(stage.dynamics.points) > 0 else 0.0
                pressure_delta = abs(target_pressure - 0.0) if stage.type == "pressure" else 0.0
                calculated_duration = calculate_transition_duration(
                    pressure_delta, transition_type, transition_mode
                )
                # Minimum duration fallback: instant transitions still need minimum duration
                duration = max(calculated_duration, 1.0)  # Ensure minimum 1 second
            # else: duration already set from exit trigger at lines 314-318, keep it

            phase = GaggimatePhase(
                name=stage.name,
                phase=phase_type_map.get(stage.key, stage.key),
                valve=1,
                duration=duration,
                temperature=meticulous.temperature,
                transition=TransitionSettings(
                    type=transition_type,
                    duration=duration,
                    adaptive=False,
                ),
                pump=pump,
                targets=targets,
            )
            phases.append(phase)
        else:
            # Multi-point dynamics splitting - only process if 2+ points
            if num_points >= 2:
                for i in range(1, num_points):
                    p_prev = stage.dynamics.points[i - 1]
                    p_curr = stage.dynamics.points[i]

                    # Duration is the difference in time between points
                    phase_duration = float(p_curr[0] - p_prev[0])
                    if phase_duration <= 0:
                        phase_duration = 0.1

                    target_value = p_curr[1]

                    if stage.type == "power":
                        pump = PumpSettings(
                            target="pressure",
                            pressure=target_value / 10.0,
                            flow=10.0,
                        )
                    elif stage.type == "flow":
                        # Check for bloom semantics: zero/near-zero flow with bloom key
                        is_bloom = (stage.key.startswith("blooming") and target_value <= 0.1)

                        if is_bloom:
                            # Bloom semantics: zero-flow, pressure-hold behavior
                            pump = PumpSettings(
                                target="pressure",
                                pressure=MIN_BLOOM_PRESSURE,
                                flow=0,
                            )
                        else:
                            # Standard flow stage
                            pump = PumpSettings(
                                target="flow",
                                flow=target_value,
                                pressure=12.0,
                            )
                    elif stage.type == "pressure":
                        pump = PumpSettings(
                            target="pressure",
                            pressure=target_value,
                            flow=10.0,
                        )
                        # Validate pressure range
                        validate_pressure_range(target_value, stage.name)
                    else:
                        raise ValueError(
                            f"Unknown stage type: {stage.type}. Expected 'power', 'flow', or 'pressure'."
                        )

                    # Transition type mapping based on mode
                    if transition_mode == TRANSITION_MODE_SMART:
                        # Flow stages use instant transitions regardless of interpolation
                        if stage.type == "flow":
                            transition_type = "instant"
                        else:
                            transition_type = SMART_INTERPOLATION_MAP.get(
                                stage.dynamics.interpolation, "linear"
                            )
                    elif transition_mode == TRANSITION_MODE_PRESERVE:
                        # Flow stages use instant transitions regardless of interpolation
                        if stage.type == "flow":
                            transition_type = "instant"
                        else:
                            transition_type = PRESERVE_INTERPOLATION_MAP.get(
                                stage.dynamics.interpolation, "linear"
                            )
                    elif transition_mode == TRANSITION_MODE_LINEAR:
                        if stage.dynamics.interpolation == "instant":
                            transition_type = "linear"
                        else:
                            transition_type = "linear"
                    else:  # INSTANT mode
                        transition_type = "instant"

                    # Calculate duration based on pressure delta
                    pressure_delta = abs(target_value - p_prev[1]) if stage.type == "pressure" else 0.0
                    duration = calculate_transition_duration(
                        pressure_delta, transition_type, transition_mode
                    )

                    # Create transition with calculated duration
                    transition = TransitionSettings(
                        type=transition_type,
                        duration=duration,
                        adaptive=False,
                    )

                    # Only add exit triggers to the final phase of a split stage
                    targets = []
                    if i == num_points - 1:  # Final segment
                        # Calculate accumulated time from previous segments in this stage
                        # This is the time at the previous point
                        phase_start_time = stage.dynamics.points[i][0]
                        targets, warnings_list = convert_exit_triggers(
                            stage.exit_triggers, phase_start_time=phase_start_time
                        )
                        for warning in warnings_list:
                            warnings.warn(f"Stage '{stage.name}': {warning}")

                    phase = GaggimatePhase(
                        name=f"{stage.name} ({i}/{num_points - 1})",
                        phase=phase_type_map.get(stage.key, stage.key),
                        valve=1,
                        duration=phase_duration,
                        temperature=meticulous.temperature,
                        transition=transition,
                        pump=pump,
                        targets=targets,
                    )
                    phases.append(phase)

    gaggimate = GaggimateProfile(
        label=meticulous.name,
        type="pro",
        description=description,
        temperature=meticulous.temperature,
        utility=False,
        phases=phases,
    )

    return gaggimate.model_dump()
