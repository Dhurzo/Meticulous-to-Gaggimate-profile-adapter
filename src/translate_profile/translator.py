import re
import warnings
from typing import Any

# Typical brewing pressure range (bar)
MIN_PRESSURE = 1.0
MAX_PRESSURE = 10.0
MIN_BLOOM_PRESSURE = 2.0  # Minimum pressure for bloom stages


def validate_pressure_range(pressure: float, stage_name: str) -> None:
    """Warn if pressure is outside typical brewing range."""
    if pressure < MIN_PRESSURE or pressure > MAX_PRESSURE:
        warnings.warn(
            f"Stage '{stage_name}': pressure {pressure:.1f} bar is outside "
            f"typical range ({MIN_PRESSURE}-{MAX_PRESSURE} bar). "
            f"Check if this is intentional."
        )


from .exit_mode import convert_exit_triggers as exit_mode_convert
from .models.gaggimate import (
    ExitTarget,
    GaggimatePhase,
    GaggimateProfile,
    PumpSettings,
    TransitionSettings,
)
from .models.meticulous import ExitTrigger, MeticulousProfile

# Transition mode constants for smart interpolation mapping
TRANSITION_MODE_SMART = "smart"
TRANSITION_MODE_PRESERVE = "preserve"
TRANSITION_MODE_LINEAR = "linear"
TRANSITION_MODE_INSTANT = "instant"

# Interpolation mapping for smart mode
SMART_INTERPOLATION_MAP = {
    "linear": "linear",
    "step": "linear",
    "instant": "instant",
    "bezier": "ease-in-out",
    "spline": "ease-in-out",
}

# Interpolation mapping for preserve mode (1:1 mapping)
PRESERVE_INTERPOLATION_MAP = {
    "linear": "linear",
    "step": "linear",
    "instant": "linear",
    "bezier": "bezier",
    "spline": "spline",
}

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


def translate_profile(meticulous_data: dict[str, Any], transition_mode: str = TRANSITION_MODE_SMART) -> tuple[dict[str, Any], list[str]]:
    """
    Translates a Meticulous profile to Gaggimate format.

    Args:
        meticulous_data: The Meticulous profile data to translate
        transition_mode: Interpolation mapping mode - smart, preserve, linear, or instant

    Returns:
        Tuple of (gaggimate_data dict, warnings list)
    """
    from .exceptions import UndefinedVariableError

    # Select interpolation map based on transition mode
    if transition_mode == TRANSITION_MODE_PRESERVE:
        interpolation_map = PRESERVE_INTERPOLATION_MAP
    elif transition_mode == TRANSITION_MODE_LINEAR:
        interpolation_map = {k: "linear" for k in ["linear", "step", "instant", "bezier", "spline"]}
    elif transition_mode == TRANSITION_MODE_INSTANT:
        interpolation_map = {k: "instant" for k in ["linear", "step", "instant", "bezier", "spline"]}
    else:  # Default to smart mode
        interpolation_map = SMART_INTERPOLATION_MAP

    # Collect all translation warnings
    translation_warnings: list[str] = []

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
    cumulative_time: float = 0.0  # Track cumulative time for relative trigger conversion

    # Mapping for Meticulous stage keys to Gaggimate phase types (Task 2)
    # Case-insensitive matching for real-world Meticulous profiles
    phase_type_map = {
        "fill": "preinfusion",
        "bloom": "preinfusion",
        "blooming": "preinfusion",
        "extraction": "brew",
    }

    for stage in meticulous.stages:
        num_points = len(stage.dynamics.points)
        stage_start_time = cumulative_time  # Capture start time for this stage's triggers

        if num_points <= 1:
            # Single point stage logic
            target_value = stage.dynamics.points[0][1] if num_points == 1 else 0.0

            # Map stage type to pump target
            # Special case: Bloom stages use pressure with zero flow (bloom hold behavior)
            if stage.key.lower() in ("bloom", "blooming"):
                pump = PumpSettings(
                    target="pressure",
                    pressure=max(target_value, MIN_BLOOM_PRESSURE),
                    flow=0.0,
                )
            elif stage.type == "power":
                pump = PumpSettings(
                    target="pressure",
                    pressure=target_value / 10.0,
                    flow=10.0,
                )
            elif stage.type == "flow":
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

            # Duration calculation logic:
            # Use exit trigger if present, else:
            # For pressure or flow, use difference from dynamics (pressure delta => fast, flow delta => standard); fallback 30.0
            duration = None
            for trigger in stage.exit_triggers:
                if trigger.type == "time":
                    duration = trigger.value
                    break

            if duration is None:
                if stage.type == "pressure":
                    if num_points == 1 and len(stage.dynamics.points[0]) >= 2:
                        # Use fast shot algorithm: delta > 3.0 => 1.5s, else 4.0s
                        p1 = stage.dynamics.points[0][1]
                        p0 = 0.0
                        delta = abs(p1 - p0)
                        duration = 1.5 if delta > 3.0 else 4.0
                    else:
                        duration = 4.0
                elif stage.type == "flow":
                    # Default flow stage, fallback 4.0s
                    duration = 4.0
                else:
                    duration = 30.0

            if duration <= 0:
                duration = 0.1

            targets, exit_warnings = exit_mode_convert(stage.exit_triggers, phase_start_time=stage_start_time)
            translation_warnings.extend(exit_warnings)
            # Emit warnings for test compatibility
            import warnings as py_warnings
            for warning in exit_warnings:
                py_warnings.warn(warning)

            cumulative_time += duration  # Update cumulative time for next stage

            # Transition assignment: always force instant for flow, otherwise use mapping
            # For single-point: force 'instant' for all types except 'pressure'; else use mapping
            if stage.type != "pressure":
                transition_type = "instant"
                transition_duration = 0.0
            else:
                transition_type = interpolation_map.get(stage.dynamics.interpolation, "linear")
                transition_duration = duration if transition_type == "linear" else 0.0

            phase = GaggimatePhase(
                name=stage.name,
                phase=phase_type_map.get(stage.key.lower(), stage.key),
                valve=1,
                duration=duration,
                temperature=meticulous.temperature,
                transition=TransitionSettings(
                    type=transition_type,
                    duration=transition_duration,
                    adaptive=False,
                ),
                pump=pump,
                targets=targets,
            )
            phases.append(phase)
        else:
            # Multi-point dynamics splitting (Task 1)
            for i in range(1, num_points):
                p_prev = stage.dynamics.points[i - 1]
                p_curr = stage.dynamics.points[i]

                # Duration is the difference in time between points
                phase_duration = float(p_curr[0] - p_prev[0])
                if phase_duration <= 0:
                    phase_duration = 0.1

                target_value = p_curr[1]

                # Special case: Bloom stages use pressure with zero flow
                if stage.key.lower() in ("bloom", "blooming"):
                    pump = PumpSettings(
                        target="pressure",
                        pressure=max(target_value, MIN_BLOOM_PRESSURE),
                        flow=0.0,
                    )
                elif stage.type == "power":
                    pump = PumpSettings(
                        target="pressure",
                        pressure=target_value / 10.0,
                        flow=10.0,
                    )
                elif stage.type == "flow":
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

                # Transition type mapping based on selected mode
                # Always force instant for flow, else use mapping
                if stage.type == "flow":
                    transition_type = "instant"
                else:
                    transition_type = interpolation_map.get(stage.dynamics.interpolation, "linear")

                # Linear transition for split segments (Task 2)
                transition = TransitionSettings(
                    type=transition_type,
                    duration=phase_duration if transition_type == "linear" else 0.0,
                    adaptive=False,
                )

                # Only add exit triggers to the final phase of a split stage
                targets = []
                if i == num_points - 1:  # Final segment
                    targets, exit_warnings = exit_mode_convert(stage.exit_triggers, phase_start_time=stage_start_time)
                    translation_warnings.extend(exit_warnings)
                    # Emit warnings for test compatibility
                    import warnings as py_warnings
                    for warning in exit_warnings:
                        py_warnings.warn(warning)

                cumulative_time += phase_duration  # Update cumulative time for next segment

                phase = GaggimatePhase(
                    name=f"{stage.name} ({i}/{num_points - 1})",
                phase=phase_type_map.get(stage.key.lower(), stage.key),
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

    return gaggimate.model_dump(), translation_warnings
