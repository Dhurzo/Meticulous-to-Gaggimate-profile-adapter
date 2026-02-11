"""Batch processing functionality for translating multiple profiles."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
from rich.progress import track

from .core import DEFAULT_OUTPUT_DIR, read_meticulous_json, write_gaggimate_json
from .translator import translate_profile, TRANSITION_MODE_SMART


@dataclass
class BatchResult:
    """Results from batch processing operations."""

    processed: int
    successful: int
    failed: int
    details: list[dict[str, Any]]


def validate_and_discover_files(input_dir: Path) -> list[Path]:
    """Validate input directory and discover JSON files.

    Args:
        input_dir: Directory path to search for JSON files

    Returns:
        List of Path objects for discovered JSON files

    Raises:
        typer.BadParameter: If directory doesn't exist or contains no JSON files
    """
    if not input_dir.exists():
        raise typer.BadParameter(f"Directory does not exist: {input_dir}")

    if not input_dir.is_dir():
        raise typer.BadParameter(f"Path is not a directory: {input_dir}")

    json_files = list(input_dir.glob("*.json"))

    if not json_files:
        raise typer.BadParameter(f"No JSON files found in directory: {input_dir}")

    return json_files


def process_batch(
    files: list[Path],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    transition_mode: str = TRANSITION_MODE_SMART,
) -> BatchResult:
    """Process a batch of Meticulous profile files.

    Args:
        files: List of JSON file paths to process
        output_dir: Directory where translated files will be written

    Returns:
        BatchResult with processing statistics and per-file details
    """
    results = []

    for file_path in track(files, description="Processing profiles..."):
        try:
            # Read Meticulous JSON
            meticulous_data = read_meticulous_json(file_path)

            # Translate to Gaggimate format
            gaggimate_data = translate_profile(meticulous_data, transition_mode=transition_mode)

            # Write Gaggimate JSON to output directory
            output_path = write_gaggimate_json(gaggimate_data, file_path.name, output_dir)

            results.append(
                {
                    "file": file_path.name,
                    "status": "success",
                    "output": str(output_path),
                    "input_path": str(file_path),
                }
            )

        except Exception as e:
            results.append(
                {
                    "file": file_path.name,
                    "status": "failed",
                    "error": str(e),
                    "input_path": str(file_path),
                }
            )

    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful

    return BatchResult(
        processed=len(results), successful=successful, failed=failed, details=results
    )
