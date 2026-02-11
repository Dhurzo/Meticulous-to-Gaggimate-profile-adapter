"""Core validation logic for comparing Meticulous and Gaggimate profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import orjson

from .exceptions import (
    PhaseMismatchError,
    ProfileLoadError,
    ToleranceExceededError,
)
from .models import (
    BatchValidationResult,
    GaggimatePhaseData,
    MeticulousStageData,
    PhaseDeviation,
    PhaseMatch,
    PhaseType,
    PhaseTypeResult,
    PhaseTypeValidationReport,
    ProfileValidationResult,
    StagePoint,
    ValidationResult,
)

# Tolerance constants
PRESSURE_ABSOLUTE_TOLERANCE = 0.1  # bar
PRESSURE_PERCENTAGE_TOLERANCE = 0.02  # 2%
FLOW_ABSOLUTE_TOLERANCE = 0.2  # ml/s
FLOW_PERCENTAGE_TOLERANCE = 0.05  # 5%
DURATION_ABSOLUTE_TOLERANCE = 0.5  # seconds
DURATION_PERCENTAGE_TOLERANCE = 0.02  # 2%

# Tolerance configuration
TOLERANCES = {
    "pressure": {
        "absolute": PRESSURE_ABSOLUTE_TOLERANCE,
        "percentage": PRESSURE_PERCENTAGE_TOLERANCE,
    },
    "flow": {
        "absolute": FLOW_ABSOLUTE_TOLERANCE,
        "percentage": FLOW_PERCENTAGE_TOLERANCE,
    },
    "duration": {
        "absolute": DURATION_ABSOLUTE_TOLERANCE,
        "percentage": DURATION_PERCENTAGE_TOLERANCE,
    },
}


def read_meticulous_json(file_path: Path) -> dict[str, Any]:
    """Read and parse a Meticulous profile JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ProfileLoadError(f"Meticulous profile not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ProfileLoadError(f"Invalid JSON in Meticulous profile: {e}")


def read_gaggimate_json(file_path: Path) -> dict[str, Any]:
    """Read and parse a Gaggimate profile JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return orjson.loads(f.read())
    except FileNotFoundError:
        raise ProfileLoadError(f"Gaggimate profile not found: {file_path}")
    except orjson.JSONDecodeError as e:
        raise ProfileLoadError(f"Invalid JSON in Gaggimate profile: {e}")


def extract_meticulous_stage_data(stage: dict[str, Any]) -> MeticulousStageData:
    """Extract validation-relevant data from a Meticulous stage."""
    stage_type = stage.get("type", "unknown")

    # Determine controlled variable based on stage type
    if stage_type == "flow":
        controlled_variable: str = "flow"
    elif stage_type == "pressure":
        controlled_variable = "pressure"
    else:
        controlled_variable = "flow"  # Default

    # Extract points from dynamics
    dynamics = stage.get("dynamics", {})
    points_raw = dynamics.get("points", [])
    points = [StagePoint(time=p[0], value=p[1]) for p in points_raw]

    # Calculate duration from points (last point time)
    # Use exit triggers to determine duration if points only show start time
    duration = 0.0
    if points:
        duration = max(p.time for p in points)

    # If duration is 0 but we have exit triggers, estimate from triggers
    if duration == 0:
        exit_triggers = stage.get("exit_triggers", [])
        for trigger in exit_triggers:
            if trigger.get("type") == "time" and trigger.get("relative"):
                # Relative time trigger from stage start
                duration = max(duration, trigger.get("value", 0))
            elif trigger.get("type") == "weight":
                # Weight-based exit - use a reasonable estimate
                duration = max(duration, 60.0)  # Default max for weight-based

    return MeticulousStageData(
        name=stage.get("name", "Unknown"),
        key=stage.get("key", ""),
        stage_type=stage_type,
        points=points,
        duration=duration,
        controlled_variable=controlled_variable,
    )


def extract_gaggimate_phase_data(phase: dict[str, Any]) -> GaggimatePhaseData:
    """Extract validation-relevant data from a Gaggimate phase."""
    pump = phase.get("pump", {})
    phase_type = pump.get("target", "unknown")

    return GaggimatePhaseData(
        name=phase.get("name", "Unknown"),
        phase_type=phase_type,
        duration=phase.get("duration", 0.0),
        pressure=pump.get("pressure"),
        flow=pump.get("flow"),
    )


def parse_split_suffix(name: str) -> tuple[str, int, int] | None:
    """Parse a phase name with (X/Y) suffix for split phases.

    Returns (base_name, index, total) or None if no suffix.
    """
    import re

    match = re.search(r"\((\d+)/(\d+)\)\s*$", name)
    if match:
        index = int(match.group(1))
        total = int(match.group(2))
        base_name = name[: match.start()].strip()
        return (base_name, index, total)
    return None


def match_phases(
    meticulous_stages: list[MeticulousStageData],
    gaggimate_phases: list[GaggimatePhaseData],
) -> list[PhaseMatch]:
    """Match Meticulous stages to Gaggimate phases, handling split phases.

    Split phases have names like "Extraction (1/2)" and "Extraction (2/2)".
    These should be matched to a single Meticulous stage that was split
    during translation.
    """
    matches: list[PhaseMatch] = []
    stage_index = 0

    for gaggimate_phase in gaggimate_phases:
        if stage_index >= len(meticulous_stages):
            break

        # Check if this is a split phase
        split_info = parse_split_suffix(gaggimate_phase.name)

        if split_info:
            base_name, index, total = split_info

            # Find the corresponding Meticulous stage
            # (use the first stage that matches base name or current stage)
            while stage_index < len(meticulous_stages):
                stage = meticulous_stages[stage_index]
                stage_base = stage.name.split(" (")[0]  # Handle existing suffixes

                if stage_base == base_name or stage.name == base_name:
                    matches.append(
                        PhaseMatch(
                            meticulous_stage=stage,
                            gaggimate_phase=gaggimate_phase,
                            split_index=index,
                            total_splits=total,
                        )
                    )
                    stage_index += 1
                    break
                elif index == 1:
                    # First split, must match
                    matches.append(
                        PhaseMatch(
                            meticulous_stage=stage,
                            gaggimate_phase=gaggimate_phase,
                            split_index=index,
                            total_splits=total,
                        )
                    )
                    stage_index += 1
                    break
                else:
                    # Skip to next stage
                    stage_index += 1
        else:
            # Regular phase match
            if stage_index < len(meticulous_stages):
                matches.append(
                    PhaseMatch(
                        meticulous_stage=meticulous_stages[stage_index],
                        gaggimate_phase=gaggimate_phase,
                    )
                )
                stage_index += 1

    return matches


def calculate_tolerance(
    meticulous_value: float, tolerance: dict[str, float]
) -> float:
    """Calculate the absolute tolerance for a given value.

    Uses the larger of the absolute tolerance or the percentage tolerance.
    """
    abs_tol = tolerance["absolute"]
    pct_tol = abs(meticulous_value) * tolerance["percentage"]

    # Use the larger tolerance
    return max(abs_tol, pct_tol)


def compare_with_tolerance(
    meticulous_value: float,
    gaggimate_value: float,
    tolerance: dict[str, float],
    variable: str = "value",
) -> tuple[bool, float, float]:
    """Compare two values and return whether they're within tolerance.

    Returns (within_tolerance, actual_difference, percentage_difference).
    """
    if meticulous_value == 0:
        # Handle division by zero for percentage calculation
        pct_diff = 100.0 if gaggimate_value != 0 else 0.0
        abs_diff = abs(gaggimate_value - meticulous_value)
        return abs_diff <= tolerance["absolute"], abs_diff, pct_diff

    abs_diff = abs(gaggimate_value - meticulous_value)
    pct_diff = (abs_diff / abs(meticulous_value)) * 100.0

    # Use the larger tolerance
    max_tolerance = calculate_tolerance(meticulous_value, tolerance)

    return abs_diff <= max_tolerance, abs_diff, pct_diff


def extract_controlled_value(
    stage: MeticulousStageData,
) -> float | None:
    """Extract the controlled variable value from a Meticulous stage."""
    if not stage.points:
        return None

    # Use the first point value (start of stage)
    first_value = stage.points[0].value

    # Handle variable references (e.g., '$flow_1')
    if isinstance(first_value, str):
        return None  # Can't compare unresolved variables

    return first_value


def validate_phase_match(
    phase_match: PhaseMatch,
) -> ValidationResult:
    """Validate a single phase match and return deviations."""
    stage = phase_match.meticulous_stage
    phase = phase_match.gaggimate_phase
    deviations: list[PhaseDeviation] = []

    # Determine which variable to compare based on stage type
    if stage.stage_type == "flow":
        meticulous_value = extract_controlled_value(stage)
        gaggimate_value = phase.flow
        tolerance_config = TOLERANCES["flow"]
        variable = "flow"
    elif stage.stage_type == "pressure":
        meticulous_value = extract_controlled_value(stage)
        gaggimate_value = phase.pressure
        tolerance_config = TOLERANCES["pressure"]
        variable = "pressure"
    else:
        # For other types, compare flow
        meticulous_value = extract_controlled_value(stage)
        gaggimate_value = phase.flow
        tolerance_config = TOLERANCES["flow"]
        variable = "flow"

    # Compare controlled variable if both values exist
    if meticulous_value is not None and gaggimate_value is not None:
        within_tol, abs_diff, pct_diff = compare_with_tolerance(
            meticulous_value, gaggimate_value, tolerance_config, variable
        )

        # Determine which tolerance was used
        abs_tol = tolerance_config["absolute"]
        pct_tol = abs(meticulous_value) * tolerance_config["percentage"]
        tolerance_used = "absolute" if abs_tol >= pct_tol else "percentage"
        tolerance_value = max(abs_tol, pct_tol)

        deviation = PhaseDeviation(
            phase_name=phase.name,
            variable=variable,
            meticulous_value=meticulous_value,
            gaggimate_value=gaggimate_value,
            deviation_absolute=abs_diff,
            deviation_percentage=pct_diff,
            within_tolerance=within_tol,
            tolerance_used=tolerance_used,
            tolerance_value=tolerance_value,
        )
        deviations.append(deviation)

    # Compare duration only if Meticulous stage has an explicit duration
    # (derived from points time or exit triggers)
    if phase.duration > 0 and stage.duration > 0:
        within_tol, abs_diff, pct_diff = compare_with_tolerance(
            stage.duration, phase.duration, TOLERANCES["duration"], "duration"
        )

        # Determine which tolerance was used
        abs_tol = TOLERANCES["duration"]["absolute"]
        pct_tol = abs(stage.duration) * TOLERANCES["duration"]["percentage"]
        tolerance_used = "absolute" if abs_tol >= pct_tol else "percentage"
        tolerance_value = max(abs_tol, pct_tol)

        duration_deviation = PhaseDeviation(
            phase_name=phase.name,
            variable="duration",
            meticulous_value=stage.duration,
            gaggimate_value=phase.duration,
            deviation_absolute=abs_diff,
            deviation_percentage=pct_diff,
            within_tolerance=within_tol,
            tolerance_used=tolerance_used,
            tolerance_value=tolerance_value,
        )
        deviations.append(duration_deviation)

    # Check if validation passed (all deviations within tolerance)
    passed = all(d.within_tolerance for d in deviations)
    error_message = None if passed else f"{len([d for d in deviations if not d.within_tolerance])} deviation(s) exceeded tolerance"

    return ValidationResult(
        phase_match=phase_match,
        deviations=deviations,
        passed=passed,
        error_message=error_message,
    )


def validate_profile_pair(
    meticulous_path: Path,
    gaggimate_path: Path,
) -> ProfileValidationResult:
    """Validate a pair of Meticulous and Gaggimate profiles.

    Returns a detailed validation result with all deviations.
    """
    # Load profiles
    try:
        meticulous_data = read_meticulous_json(meticulous_path)
        gaggimate_data = read_gaggimate_json(gaggimate_path)
    except ProfileLoadError as e:
        return ProfileValidationResult(
            profile_name=meticulous_path.stem,
            meticulous_file=meticulous_path,
            gaggimate_file=gaggimate_path,
            error_message=str(e),
            passed=False,
        )

    # Extract data from profiles
    meticulous_stages = [
        extract_meticulous_stage_data(s) for s in meticulous_data.get("stages", [])
    ]
    gaggimate_phases = [
        extract_gaggimate_phase_data(p) for p in gaggimate_data.get("phases", [])
    ]

    # Match phases
    matches = match_phases(meticulous_stages, gaggimate_phases)

    # Validate each match
    phase_results = [validate_phase_match(m) for m in matches]

    # Count results
    total_phases = len(phase_results)
    passed_phases = sum(1 for r in phase_results if r.passed)
    failed_phases = total_phases - passed_phases
    total_deviations = sum(len(r.deviations) for r in phase_results)

    passed = failed_phases == 0

    return ProfileValidationResult(
        profile_name=meticulous_data.get("name", meticulous_path.stem),
        meticulous_file=meticulous_path,
        gaggimate_file=gaggimate_path,
        phase_results=phase_results,
        total_phases=total_phases,
        passed_phases=passed_phases,
        failed_phases=failed_phases,
        total_deviations=total_deviations,
        passed=passed,
    )


def detect_meticulous_phase_type(stage_key: str, stage_name: str | None = None) -> PhaseType:
    from typing import Optional
    phase_type_map = {
        "Fill": PhaseType.PREINFUSION,
        "Bloom": PhaseType.PREINFUSION,
        "blooming": PhaseType.PREINFUSION,
        "Extraction": PhaseType.BREW,
    }
    if stage_key in phase_type_map:
        return phase_type_map[stage_key]
    if stage_name:
        name_lower = stage_name.lower()
        if "prebrew" in name_lower or "preinfus" in name_lower or "fill" in name_lower or "bloom" in name_lower:
            return PhaseType.PREINFUSION
        elif "extraction" in name_lower or "brew" in name_lower:
            return PhaseType.BREW
    return PhaseType.UNKNOWN


def detect_gaggimate_phase_type(phase_name: str) -> PhaseType:
    name_lower = phase_name.lower()
    if "preinfus" in name_lower or "prebrew" in name_lower or "fill" in name_lower or "bloom" in name_lower:
        return PhaseType.PREINFUSION
    elif "brew" in name_lower or "extraction" in name_lower:
        return PhaseType.BREW
    elif "flush" in name_lower:
        return PhaseType.UNKNOWN
    return PhaseType.UNKNOWN


def verify_phase_ordering(types: list[PhaseType]) -> bool:
    if not types:
        return True
    preinfusion_indices = [i for i, t in enumerate(types) if t == PhaseType.PREINFUSION]
    brew_indices = [i for i, t in enumerate(types) if t == PhaseType.BREW]

    if not preinfusion_indices or not brew_indices:
        return True

    return max(preinfusion_indices) < min(brew_indices)


def validate_phase_types(
    original_path: Path, translated_path: Path
) -> PhaseTypeValidationReport:
    from translate_profile.translator import resolve_variables

    original = resolve_variables(read_meticulous_json(original_path))
    translated = read_gaggimate_json(translated_path)

    meticulous_stages = [
        extract_meticulous_stage_data(s) for s in original.get("stages", [])
    ]
    gaggimate_phases = [
        extract_gaggimate_phase_data(p) for p in translated.get("phases", [])
    ]

    matched_pairs = match_phases(meticulous_stages, gaggimate_phases)

    type_results = []
    for match in matched_pairs:
        stage = match.meticulous_stage
        phase = match.gaggimate_phase
        original_type = detect_meticulous_phase_type(stage.key, stage.name)
        translated_type = detect_gaggimate_phase_type(phase.name)
        matched = original_type == translated_type

        result = PhaseTypeResult(
            stage_key=stage.key,
            original_type=original_type,
            translated_type=translated_type,
            matched=matched,
        )
        type_results.append(result)

    stage_types = [detect_meticulous_phase_type(m.meticulous_stage.key) for m in matched_pairs]
    ordering_correct = verify_phase_ordering(stage_types)

    all_matched = all(r.matched for r in type_results)
    overall_passed = all_matched and ordering_correct

    summary = f"{sum(1 for r in type_results if r.matched)}/{len(type_results)} phases passed type check"
    if not ordering_correct:
        summary += ", ordering issues found"

    return PhaseTypeValidationReport(
        profile_name=original_path.stem,
        original_path=original_path,
        translated_path=translated_path,
        phases_checked=len(type_results),
        type_mismatches=[r for r in type_results if not r.matched],
        ordering_correct=ordering_correct,
        overall_passed=overall_passed,
        summary=summary,
    )


def validate_batch(
    profiles_dir: Path,
    gaggimate_dir: Path,
) -> BatchValidationResult:
    """Validate all matching profile pairs in directories.

    Matches profiles by filename between the two directories.
    """
    result = BatchValidationResult()

    # Find all JSON files in profiles directory
    meticulous_files = list(profiles_dir.glob("*.json"))
    gaggimate_files = set(f.stem for f in gaggimate_dir.glob("*.json"))

    for meticulous_file in meticulous_files:
        stem = meticulous_file.stem

        # Find corresponding Gaggimate file
        gaggimate_file = gaggimate_dir / f"{stem}.json"

        if gaggimate_file.exists():
            profile_result = validate_profile_pair(meticulous_file, gaggimate_file)
            result.profile_results.append(profile_result)

    # Calculate totals
    result.total_profiles = len(result.profile_results)
    result.passed_profiles = sum(1 for r in result.profile_results if r.passed)
    result.failed_profiles = result.total_profiles - result.passed_profiles

    return result
