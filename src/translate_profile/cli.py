"""CLI interface for the profile translator."""

from pathlib import Path
from typing import Annotated, Callable

import typer
from pydantic import ValidationError

from . import __version__
from .batch_processor import process_batch, validate_and_discover_files
from .core import (
    DEFAULT_OUTPUT_DIR,
    ensure_output_directory,
    read_meticulous_json,
    write_gaggimate_json,
)
from .exceptions import (
    FileNotFoundTranslationError,
    InvalidJSONSyntaxError,
    TranslationError,
)
from .translator import translate_profile

app = typer.Typer(
    name="translate-profile",
    help="Translate espresso extraction profiles from Meticulous JSON format to Gaggimate JSON format.",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"translate-profile version: {__version__}")
        raise typer.Exit(0)


@app.callback()
def callback(
    version: Annotated[
        bool | None,
        typer.Option("--version", "-V", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Translate espresso profiles from Meticulous to Gaggimate format."""
    pass


TRANSITION_MODE_CHOICES: tuple[str, ...] = ("smart", "preserve", "linear", "instant")
DEFAULT_TRANSITION_MODE = "smart"


def validate_transition_mode(
    ctx: typer.Context,
    param: object | None,
    value: str | None,
) -> str:
    """Normalize and validate the transition mode option."""
    if value is None:
        return DEFAULT_TRANSITION_MODE

    normalized = value.lower()
    if normalized not in TRANSITION_MODE_CHOICES:
        raise typer.BadParameter(
            f"Invalid mode '{value}'. Choose from: {', '.join(TRANSITION_MODE_CHOICES)}."
        )
    return normalized


@app.command()
def translate(
    input_file: Annotated[
        Path,
        typer.Argument(
            exists=False,  # Handle file validation manually for custom error handling
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to the input Meticulous JSON profile file.",
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Path for the output Gaggimate JSON file. Defaults to TranslatedToGaggimate/[input_filename].json",
        ),
    ] = None,
    mode: Annotated[
        str,
        typer.Option(
            "--mode",
            "--transition-mode",
            callback=validate_transition_mode,
            case_sensitive=False,
            help="Select the transition mode (smart, preserve, linear, instant).",
        ),
    ] = DEFAULT_TRANSITION_MODE,
) -> None:
    """Translate a Meticulous profile to Gaggimate format.

    INPUT_FILE is required and must be a valid Meticulous JSON file.
    The output will be written to TranslatedToGaggimate/ by default,
    or to the path specified with --output.
    """
    try:
        # Read input file
        typer.echo(f"Reading input file: {input_file}")
        typer.echo(f"Translation mode: {mode}")
        meticulous_data = read_meticulous_json(input_file)

        # Determine output path
        if output is None:
            output_filename = input_file.name
        else:
            output_filename = str(output)

        typer.echo(f"Writing output to: {output_filename}")

        # Call the translation engine
        try:
            gaggimate_data, translation_warnings = translate_profile(
                meticulous_data, transition_mode=mode
            )
        except ValidationError as e:
            # Human-readable Pydantic errors
            error_details = []
            for error in e.errors():
                loc = " -> ".join(str(l) for l in error["loc"])
                msg = error["msg"]
                error_details.append(f"[{loc}]: {msg}")

            raise TranslationError(
                message="Profile validation failed during translation.",
                details="\n".join(error_details),
            )

        # Write output
        output_path = write_gaggimate_json(gaggimate_data, output_filename)
        typer.echo(f"Successfully wrote: {output_path}")

        # Display translation warnings if any
        if translation_warnings:
            typer.echo("\n⚠️  Translation Warnings:")
            for warning in translation_warnings:
                typer.echo(f"  {warning}")

    except FileNotFoundTranslationError as e:
        typer.echo(f"Error: {e.message}", err=True)
        typer.echo(f"Details: {e.details}", err=True)
        raise typer.Exit(1)

    except InvalidJSONSyntaxError as e:
        typer.echo(f"Error: {e.message}", err=True)
        typer.echo(f"Details: {e.details}", err=True)
        raise typer.Exit(1)

    except TranslationError as e:
        typer.echo(f"Error: {e.message}", err=True)
        if e.details:
            typer.echo(f"Details: {e.details}", err=True)
        raise typer.Exit(1)


@app.command()
def translate_batch(
    input_dir: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing Meticulous JSON profile files.",
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output directory. Defaults to TranslatedToGaggimate/",
        ),
    ] = None,
    mode: Annotated[
        str,
        typer.Option(
            "--mode",
            "--transition-mode",
            callback=validate_transition_mode,
            case_sensitive=False,
            help="Select the transition mode for the batch (smart, preserve, linear, instant).",
        ),
    ] = DEFAULT_TRANSITION_MODE,
) -> None:
    """Process all Meticulous profiles in a directory."""
    try:
        typer.echo(f"Translation mode: {mode}")
        # Set output directory
        if output is None:
            output_dir = DEFAULT_OUTPUT_DIR
        else:
            output_dir = output

        # Ensure output directory exists
        output_dir = ensure_output_directory(output_dir)

        # Discover JSON files in input directory
        typer.echo(f"Scanning directory: {input_dir}")
        json_files = validate_and_discover_files(input_dir)
        typer.echo(f"Found {len(json_files)} JSON files")

        # Progress indication before processing starts
        typer.echo("Processing profiles...")

        # Process batch
        result = process_batch(json_files, output_dir, transition_mode=mode)

        # Display comprehensive results summary
        typer.echo(
            f"\n📊 Summary: Processed {result.processed} files, Successful: {result.successful}, Failed: {result.failed}"
        )
        typer.echo(f"Mode: {mode}")

        # Show results for each file with clear status
        typer.echo("\n📋 Results:")
        for detail in result.details:
            if detail["status"] == "success":
                typer.echo(f"  ✅ {detail['file']} → {detail['output']}")
            else:
                typer.echo(f"  ❌ {detail['file']}: {detail['error']}", err=True)

        # Exit with appropriate code
        if result.failed == 0:
            typer.echo(f"\n🎉 All {result.successful} files translated successfully!")
            raise typer.Exit(0)
        else:
            typer.echo(
                f"\n⚠️  {result.failed} of {result.processed} files failed translation.", err=True
            )
            raise typer.Exit(1)

    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("\nUsage examples:")
        typer.echo("  translate-profile translate-batch ./profiles")
        typer.echo("  translate-profile translate-batch ./profiles --output ./output")
        raise typer.Exit(1)

    except typer.Exit as e:
        # Re-raise typer.Exit to preserve exit code
        raise e

    except Exception as e:
        # Catch-all for unexpected errors during batch processing
        typer.echo(f"Unexpected error during batch processing: {e}", err=True)
        raise typer.Exit(1)

    # Explicit exit with success code if no exceptions raised
    raise typer.Exit(0)


def main() -> None:
    """Entry point for the CLI application."""
    app()
