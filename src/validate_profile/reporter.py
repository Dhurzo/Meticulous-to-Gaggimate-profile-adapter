"""Reporting utilities for profile validation results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TextIO

from .models import (
    BatchValidationResult,
    PhaseDeviation,
    PhaseTypeValidationReport,
    ProfileValidationResult,
    ValidationResult,
)


@dataclass
class ProfileResult:
    """Track each profile's validation status with objective and type validation results."""
    profile_name: str
    meticulous_file: str
    gaggimate_file: str
    objective_passed: bool
    type_passed: bool
    overall_passed: bool
    objective_failures: list[str] = field(default_factory=list)
    type_failures: list[str] = field(default_factory=list)
    phase_results: list[ValidationResult] = field(default_factory=list)
    type_report: PhaseTypeValidationReport | None = None
    total_phases: int = 0
    passed_phases: int = 0
    total_deviations: int = 0


def format_deviation(deviation: PhaseDeviation, indent: int = 4) -> str:
    """Format a single deviation as a readable string."""
    status = "✓" if deviation.within_tolerance else "✗"
    tolerance_desc = (
        f"{deviation.tolerance_used} (±{deviation.tolerance_value:.3f})"
    )

    lines = [
        f"{' ' * indent}{status} {deviation.variable}:",
        f"{' ' * (indent + 2)}Meticulous: {deviation.meticulous_value:.2f}",
        f"{' ' * (indent + 2)}Gaggimate: {deviation.gaggimate_value:.2f}",
        f"{' ' * (indent + 2)}Deviation: {deviation.deviation_absolute:.3f} ({deviation.deviation_percentage:.1f}%)",
        f"{' ' * (indent + 2)}Tolerance: {tolerance_desc}",
    ]
    return "\n".join(lines)


def format_validation_result(result: ValidationResult, verbose: bool = False) -> str:
    """Format a single validation result."""
    stage = result.phase_match.meticulous_stage
    phase = result.phase_match.gaggimate_phase

    lines = []

    # Phase header
    split_info = ""
    if result.phase_match.split_index is not None:
        split_info = f" ({result.phase_match.split_index}/{result.phase_match.total_splits})"

    status = "✓ PASS" if result.passed else "✗ FAIL"
    lines.append(f"\n{'=' * 60}")
    lines.append(f"Phase: {stage.name}{split_info}")
    lines.append(f"Status: {status}")
    lines.append(f"{'=' * 60}")

    if verbose:
        lines.append(f"\nMeticulous Stage:")
        lines.append(f"  Type: {stage.stage_type}")
        lines.append(f"  Duration: {stage.duration:.2f}s")
        lines.append(f"  Controlled: {stage.controlled_variable}")

        lines.append(f"\nGaggimate Phase:")
        lines.append(f"  Name: {phase.name}")
        lines.append(f"  Duration: {phase.duration:.2f}s")
        if phase.pressure:
            lines.append(f"  Pressure: {phase.pressure:.2f} bar")
        if phase.flow:
            lines.append(f"  Flow: {phase.flow:.2f} ml/s")

    # Deviations
    if result.deviations:
        lines.append(f"\nDeviations ({len(result.deviations)}):")
        for deviation in result.deviations:
            lines.append(format_deviation(deviation))
    else:
        lines.append("\nNo deviations found.")

    if not result.passed and result.error_message:
        lines.append(f"\nError: {result.error_message}")

    return "\n".join(lines)


def format_profile_result(result: ProfileValidationResult, verbose: bool = False) -> str:
    """Format a complete profile validation result."""
    lines = []

    # Profile header
    lines.append(f"\n{'#' * 70}")
    lines.append(f" Profile: {result.profile_name}")
    lines.append(f" Meticulous: {result.meticulous_file.name}")
    lines.append(f" Gaggimate: {result.gaggimate_file.name}")
    lines.append(f"{'#' * 70}")

    # Summary
    status = "✓ PASSED" if result.passed else "✗ FAILED"
    lines.append(f"\nSummary: {status}")
    lines.append(f"  Phases: {result.passed_phases}/{result.total_phases} passed")
    lines.append(f"  Deviations: {result.total_deviations}")

    if result.failed_phases > 0:
        failed_names = [
            r.phase_match.meticulous_stage.name for r in result.phase_results if not r.passed
        ]
        lines.append(f"  Failed phases: {', '.join(failed_names)}")

    if result.error_message:
        lines.append(f"\nError: {result.error_message}")

    # Detailed phase results
    for phase_result in result.phase_results:
        lines.append(format_validation_result(phase_result, verbose))

    return "\n".join(lines)


def format_batch_result(result: BatchValidationResult, verbose: bool = False) -> str:
    """Format a complete batch validation result."""
    lines = []

    lines.append(f"\n{'=' * 70}")
    lines.append(f" BATCH VALIDATION REPORT")
    lines.append(f"{'=' * 70}")

    # Summary
    lines.append(f"\nOverall Status:")
    if result.failed_profiles == 0:
        lines.append(f"  ✓ All {result.total_profiles} profiles PASSED")
    else:
        lines.append(
            f"  {result.passed_profiles}/{result.total_profiles} profiles passed, "
            f"{result.failed_profiles} failed"
        )

    # Individual profile results
    for profile_result in result.profile_results:
        profile_status = "✓" if profile_result.passed else "✗"
        lines.append(
            f"\n{profile_status} {profile_result.profile_name}: "
            f"{profile_result.passed_phases}/{profile_result.total_phases} phases, "
            f"{profile_result.total_deviations} deviations"
        )

        # Show failed phases
        if not profile_result.passed:
            lines.append(format_profile_result(profile_result, verbose))

    return "\n".join(lines)


def print_profile_result(result: ProfileValidationResult, verbose: bool = False, stream: TextIO | None = None) -> None:
    """Print a profile validation result to stdout or a stream."""
    output = format_profile_result(result, verbose)
    print(output, file=stream or __import__("sys").stdout)


def print_batch_result(result: BatchValidationResult, verbose: bool = False, stream: TextIO | None = None) -> None:
    """Print a batch validation result to stdout or a stream."""
    output = format_batch_result(result, verbose)
    print(output, file=stream or __import__("sys").stdout)


def generate_report(
    profile_results: list[ProfileResult],
    format: str = "text",
) -> str:
    """Generate comprehensive report with summary section, failure details.

    Args:
        profile_results: List of profile validation results
        format: Output format - "text" or "json"

    Returns:
        Formatted report string
    """
    if format == "json":
        return generate_json_report(profile_results)
    else:
        return generate_text_report(profile_results)


def generate_text_report(profile_results: list[ProfileResult]) -> str:
    """Generate comprehensive text report with summary and failure details."""
    lines = []

    # Summary section
    lines.append("=" * 70)
    lines.append(" VALIDATION REPORT")
    lines.append("=" * 70)

    total_profiles = len(profile_results)
    passed_profiles = sum(1 for r in profile_results if r.overall_passed)
    failed_profiles = total_profiles - passed_profiles

    # Objective validation counts
    objective_passed = sum(1 for r in profile_results if r.objective_passed)
    objective_failed = total_profiles - objective_passed

    # Type validation counts
    type_passed = sum(1 for r in profile_results if r.type_passed)
    type_failed = total_profiles - type_passed

    lines.append("\nSUMMARY")
    lines.append("-" * 40)
    lines.append(f"Profiles tested: {total_profiles}")
    lines.append(f"\nObjective Validation:")
    lines.append(f"  Passed: {objective_passed}")
    lines.append(f"  Failed: {objective_failed}")
    lines.append(f"\nType Validation:")
    lines.append(f"  Passed: {type_passed}")
    lines.append(f"  Failed: {type_failed}")
    lines.append(f"\nOverall Results:")
    lines.append(f"  ✓ PASSED: {passed_profiles}")
    lines.append(f"  ✗ FAILED: {failed_profiles}")

    # Profiles with failures section
    lines.append("\n" + "=" * 70)
    lines.append(" FAILURE DETAILS")
    lines.append("=" * 70)

    failed_profiles_list = [r for r in profile_results if not r.overall_passed]

    if not failed_profiles_list:
        lines.append("\nNo failures detected. All profiles passed validation.")
    else:
        for result in failed_profiles_list:
            lines.append(f"\nProfile: {result.profile_name}")
            lines.append(f"  Meticulous: {result.meticulous_file}")
            lines.append(f"  Gaggimate: {result.gaggimate_file}")
            lines.append(f"  Overall: {'PASS' if result.overall_passed else 'FAIL'}")

            if result.objective_failures:
                lines.append(f"\n  Objective Failures ({len(result.objective_failures)}):")
                for failure in result.objective_failures:
                    lines.append(f"    - {failure}")

            if result.type_failures:
                lines.append(f"\n  Type Failures ({len(result.type_failures)}):")
                for failure in result.type_failures:
                    lines.append(f"    - {failure}")

            if result.phase_results:
                failed_phases = [r for r in result.phase_results if not r.passed]
                if failed_phases:
                    lines.append(f"\n  Failed Phases ({len(failed_phases)}):")
                    for phase in failed_phases:
                        lines.append(f"    - {phase.phase_match.meticulous_stage.name}")
                        if phase.error_message:
                            lines.append(f"      Error: {phase.error_message}")
                        if phase.deviations:
                            out_of_tolerance = [d for d in phase.deviations if not d.within_tolerance]
                            lines.append(f"      Deviations: {len(phase.deviations)} total, {len(out_of_tolerance)} out of tolerance")

    # Individual profile results section
    lines.append("\n" + "=" * 70)
    lines.append(" INDIVIDUAL PROFILE RESULTS")
    lines.append("=" * 70)

    for result in profile_results:
        status = "✓" if result.overall_passed else "✗"
        lines.append(f"\n{status} {result.profile_name}")
        lines.append(f"  Objective: {'PASS' if result.objective_passed else 'FAIL'}")
        lines.append(f"  Type: {'PASS' if result.type_passed else 'FAIL'}")
        lines.append(f"  Phases: {result.passed_phases}/{result.total_phases} passed")
        lines.append(f"  Deviations: {result.total_deviations}")

    return "\n".join(lines)


def generate_json_report(profile_results: list[ProfileResult]) -> str:
    """Generate comprehensive JSON report."""
    import json

    total_profiles = len(profile_results)
    passed_profiles = sum(1 for r in profile_results if r.overall_passed)
    failed_profiles = total_profiles - passed_profiles

    objective_passed = sum(1 for r in profile_results if r.objective_passed)
    type_passed = sum(1 for r in profile_results if r.type_passed)

    report_data = {
        "summary": {
            "profiles_tested": total_profiles,
            "passed": passed_profiles,
            "failed": failed_profiles,
            "objective_validation": {
                "passed": objective_passed,
                "failed": total_profiles - objective_passed
            },
            "type_validation": {
                "passed": type_passed,
                "failed": total_profiles - type_passed
            }
        },
        "profiles": []
    }

    for result in profile_results:
        profile_data = {
            "name": result.profile_name,
            "files": {
                "meticulous": result.meticulous_file,
                "gaggimate": result.gaggimate_file
            },
            "results": {
                "objective": "pass" if result.objective_passed else "fail",
                "type": "pass" if result.type_passed else "fail",
                "overall": "pass" if result.overall_passed else "fail"
            },
            "phases": {
                "total": result.total_phases,
                "passed": result.passed_phases,
                "deviations": result.total_deviations
            },
            "failures": {
                "objective": result.objective_failures,
                "type": result.type_failures
            }
        }
        report_data["profiles"].append(profile_data)

    return json.dumps(report_data, indent=2)
