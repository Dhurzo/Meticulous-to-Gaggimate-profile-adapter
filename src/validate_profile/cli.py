"""CLI interface for the profile validator."""

from pathlib import Path
from typing import Annotated

import click
import typer

from . import __version__
from .core import (
    TOLERANCES,
    validate_batch as core_validate_batch,
    validate_phase_types,
    validate_profile_pair,
)
from .models import BatchValidationResult, PhaseTypeValidationReport, ProfileValidationResult
from .reporter import ProfileResult, generate_report, print_batch_result, print_profile_result

app = typer.Typer(
    name="validate-profile",
    help="Validate translated espresso extraction profiles by comparing Meticulous and Gaggimate formats.",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"validate-profile version: {__version__}")
        raise typer.Exit(0)


def build_profile_result(
    profile_name: str,
    meticulous_file: Path,
    gaggimate_file: Path,
    objective_result: ProfileValidationResult,
    type_result: PhaseTypeValidationReport | None = None,
) -> ProfileResult:
    """Build a comprehensive ProfileResult from both validation types."""
    objective_failures = []
    type_failures = []

    # Collect objective failures
    for phase_result in objective_result.phase_results:
        if not phase_result.passed:
            objective_failures.append(
                f"Phase '{phase_result.phase_match.meticulous_stage.name}' failed validation"
            )
            if phase_result.error_message:
                objective_failures[-1] += f": {phase_result.error_message}"

    # Collect type failures
    if type_result and type_result.type_mismatches:
        for mismatch in type_result.type_mismatches:
            type_failures.append(
                f"Phase '{mismatch.stage_key}': "
                f"{mismatch.original_type.value} → {mismatch.translated_type.value}"
            )

    if type_result and not type_result.ordering_correct:
        type_failures.append("Phase ordering incorrect: preinfusion phases must come before brew phases")

    # Determine type validation passed status
    type_passed = type_result is None or type_result.overall_passed

    # Overall passed if both objective and type pass
    overall_passed = objective_result.passed and type_passed

    return ProfileResult(
        profile_name=profile_name,
        meticulous_file=str(meticulous_file),
        gaggimate_file=str(gaggimate_file),
        objective_passed=objective_result.passed,
        type_passed=type_passed,
        overall_passed=overall_passed,
        objective_failures=objective_failures,
        type_failures=type_failures,
        phase_results=objective_result.phase_results,
        type_report=type_result,
        total_phases=objective_result.total_phases,
        passed_phases=objective_result.passed_phases,
        total_deviations=objective_result.total_deviations,
    )


@app.callback()
def callback(
    version: Annotated[
        bool | None,
        typer.Option("--version", "-V", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Validate espresso profiles translated from Meticulous to Gaggimate format."""
    pass


@app.command()
def validate(
    meticulous_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to the source Meticulous JSON profile file.",
        ),
    ],
    gaggimate_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to the translated Gaggimate JSON profile file.",
        ),
    ],
    verbose: Annotated[
        bool,
        typer.Option("-v", "--verbose", help="Show detailed validation information."),
    ] = False,
) -> None:
    """Validate a single profile pair.

    Compares a Meticulous profile with its translated Gaggimate counterpart.
    """
    typer.echo(f"Validating profile: {meticulous_file.name} → {gaggimate_file.name}")

    result = validate_profile_pair(meticulous_file, gaggimate_file)

    print_profile_result(result, verbose=verbose)

    # Exit with appropriate code
    if result.passed:
        typer.echo(f"\n✓ Validation PASSED")
        raise typer.Exit(0)
    else:
        typer.echo(f"\n✗ Validation FAILED")
        raise typer.Exit(1)


@app.command()
def validate_batch(
    profiles_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing Meticulous JSON profile files.",
        ),
    ],
    gaggimate_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing translated Gaggimate JSON profile files.",
        ),
    ],
    verbose: Annotated[
        bool,
        typer.Option("-v", "--verbose", help="Show detailed validation information."),
    ] = False,
    verbose_phases: Annotated[
        bool,
        typer.Option("-V", "--verbose-phases", help="Show detailed phase-by-phase validation."),
    ] = False,
) -> None:
    """Validate all profiles in a directory.

    Finds all matching profile pairs between Meticulous and Gaggimate directories
    and validates each pair.
    """
    typer.echo(f"Scanning directories...")
    typer.echo(f"  Meticulous profiles: {profiles_dir}")
    typer.echo(f"  Gaggimate profiles: {gaggimate_dir}")

    result = core_validate_batch(profiles_dir, gaggimate_dir)

    print_batch_result(result, verbose=verbose or verbose_phases)

    # Exit with appropriate code
    if result.failed_profiles == 0:
        typer.echo(f"\n✓ All {result.total_profiles} profiles validated successfully!")
        raise typer.Exit(0)
    else:
        typer.echo(
            f"\n✗ {result.failed_profiles} of {result.total_profiles} profiles failed validation."
        )
        raise typer.Exit(1)


@app.command()
def validate_type(
    original: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to original Meticulous profile",
        ),
    ],
    translated: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to translated Gaggimate profile",
        ),
    ],
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed type comparison"),
    ] = False,
) -> None:
    """Validate that phase types are preserved (preinfusion, bloom, extraction)."""
    try:
        report = validate_phase_types(original, translated)

        typer.echo(f"Phase Type Validation: {report.profile_name}")
        typer.echo("=" * 50)

        typer.echo(f"Phases checked: {report.phases_checked}")
        typer.echo(f"Ordering correct: {'✓' if report.ordering_correct else '✗'}")

        if report.type_mismatches:
            typer.echo(f"\nType Mismatches ({len(report.type_mismatches)}):")
            for mismatch in report.type_mismatches:
                typer.echo(
                    f"  ✗ {mismatch.stage_key}: {mismatch.original_type.value} → {mismatch.translated_type.value}"
                )
        else:
            typer.echo(f"\n✓ All {report.phases_checked} phases have correct types")

        typer.echo(f"\n{report.summary}")

        if not report.overall_passed:
            typer.echo("\n❌ FAILED - Phase type validation failed")
            raise typer.Exit(1)
        else:
            typer.echo("\n✓ PASSED - Phase types preserved correctly")

    except Exception as e:
        typer.echo(f"❌ ERROR: {e}", err=True)
        raise typer.Exit(1)


def main() -> None:
    """Entry point for the CLI application."""
    typer.echo("Profile Validation Tools")
    typer.echo("Commands: validate, validate-batch, validate-type, report")
    app()


@app.command()
def report(
    profiles_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing Meticulous JSON profile files.",
        ),
    ],
    gaggimate_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing translated Gaggimate JSON profile files.",
        ),
    ],
    format: Annotated[
        str,
        typer.Option("--format", "-f", help="Report output format",
                      click_type=click.Choice(['text', 'json'])),
    ] = "text",
    summary: Annotated[
        bool,
        typer.Option("--summary", "-s", help="Show only pass/fail summary"),
    ] = False,
) -> None:
    """Generate comprehensive validation report for all profiles.

    Runs both objective and type validation, then generates a comprehensive
    report with pass/fail counts and failure details.
    """
    typer.echo("Generating comprehensive validation report...")
    typer.echo(f"  Meticulous profiles: {profiles_dir}")
    typer.echo(f"  Gaggimate profiles: {gaggimate_dir}")
    typer.echo(f"  Format: {format}")
    if summary:
        typer.echo("  Mode: Summary only")
    typer.echo("")

    profile_results: list[ProfileResult] = []

    meticulous_files = list(profiles_dir.glob("*.json"))
    if not meticulous_files:
        typer.echo("No JSON files found in profiles directory.")
        raise typer.Exit(2)

    for meticulous_file in sorted(meticulous_files):
        profile_name = meticulous_file.stem
        gaggimate_file = gaggimate_dir / meticulous_file.name

        if not gaggimate_file.exists():
            typer.echo(f"  ⚠ Skipping {profile_name}: translated file not found")
            continue

        try:
            objective_result = validate_profile_pair(meticulous_file, gaggimate_file)
            type_result = validate_phase_types(meticulous_file, gaggimate_file)

            profile_result = build_profile_result(
                profile_name=profile_name,
                meticulous_file=meticulous_file,
                gaggimate_file=gaggimate_file,
                objective_result=objective_result,
                type_result=type_result,
            )
            profile_results.append(profile_result)

        except Exception as e:
            typer.echo(f"  ✗ {profile_name}: Error - {e}")
            error_result = ProfileResult(
                profile_name=profile_name,
                meticulous_file=str(meticulous_file),
                gaggimate_file=str(gaggimate_file),
                objective_passed=False,
                type_passed=False,
                overall_passed=False,
                objective_failures=[f"Validation error: {e}"],
            )
            profile_results.append(error_result)

    if not profile_results:
        typer.echo("No profiles were processed.")
        raise typer.Exit(2)

    if format.lower() == "json":
        report_output = generate_report(profile_results, format="json")
        typer.echo(report_output)
    else:
        if summary:
            typer.echo(generate_summary_only(profile_results))
        else:
            typer.echo(generate_report(profile_results, format="text"))

    passed = sum(1 for r in profile_results if r.overall_passed)
    failed = len(profile_results) - passed

    typer.echo("")
    if failed == 0:
        typer.echo(f"✓ All {passed} profiles passed validation!")
        raise typer.Exit(0)
    else:
        typer.echo(f"✗ {failed} of {len(profile_results)} profiles failed validation.")
        raise typer.Exit(1)


def generate_summary_only(profile_results: list[ProfileResult]) -> str:
    """Generate brief summary output."""
    total = len(profile_results)
    passed = sum(1 for r in profile_results if r.overall_passed)
    failed = total - passed

    lines = []
    lines.append("=" * 50)
    lines.append(" VALIDATION SUMMARY")
    lines.append("=" * 50)
    lines.append(f"\nProfiles tested: {total}")
    lines.append(f"  ✓ PASSED: {passed}")
    lines.append(f"  ✗ FAILED: {failed}")

    if failed > 0:
        lines.append("\nFailed profiles:")
        for r in profile_results:
            if not r.overall_passed:
                reasons = []
                if not r.objective_passed:
                    reasons.append("objective")
                if not r.type_passed:
                    reasons.append("type")
                lines.append(f"  - {r.profile_name} ({', '.join(reasons)})")

    return "\n".join(lines)
