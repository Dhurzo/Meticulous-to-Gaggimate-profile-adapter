"""Core file I/O operations for profile translation."""

from pathlib import Path
from typing import Any

import orjson

from .exceptions import FileNotFoundTranslationError, InvalidJSONSyntaxError

DEFAULT_OUTPUT_DIR = Path("TranslatedToGaggimate")


def read_meticulous_json(file_path: str | Path) -> dict[str, Any]:
    """Read and parse a Meticulous JSON profile file.

    Args:
        file_path: Path to the Meticulous JSON file

    Returns:
        Parsed JSON data as a dictionary

    Raises:
        FileNotFoundTranslationError: If the file doesn't exist
        InvalidJSONSyntaxError: If the file contains invalid JSON
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundTranslationError(str(path))

    try:
        content = path.read_text()
        data: dict[str, Any] = orjson.loads(content)
        return data
    except orjson.JSONDecodeError as e:
        raise InvalidJSONSyntaxError(str(path), str(e)) from e


def ensure_output_directory(directory: Path | None = None) -> Path:
    """Create output directory if it doesn't exist.

    Args:
        directory: Output directory path (defaults to TranslatedToGaggimate/)

    Returns:
        Path to the created/existing directory
    """
    if directory is None:
        directory = DEFAULT_OUTPUT_DIR

    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_gaggimate_json(
    data: dict[str, Any], output_path: str | Path, output_dir: Path | None = None
) -> Path:
    """Write Gaggimate JSON profile to file.

    Args:
        data: Gaggimate profile data to write
        output_path: Filename for the output file
        output_dir: Output directory (defaults to TranslatedToGaggimate/)

    Returns:
        Path to the written file
    """
    directory = ensure_output_directory(output_dir)
    file_path = directory / Path(output_path).name

    # Convert data to JSON bytes using orjson
    json_bytes = orjson.dumps(data, option=orjson.OPT_INDENT_2)
    file_path.write_bytes(json_bytes)

    return file_path
