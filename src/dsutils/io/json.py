"""JSON file read/write utilities."""

import json
import warnings
from pathlib import Path
from typing import TypeAlias

JSON_DATA_TYPES: TypeAlias = dict | list | str | int | float | bool | None


def load_json(file_path: Path | str) -> JSON_DATA_TYPES:
    """Load JSON data from a file.

    Args:
        file_path: Path to the JSON file. Strings are accepted but a
            warning is issued; prefer passing a ``pathlib.Path``.

    Returns:
        The deserialized JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if type(file_path) is str:
        warnings.warn(
            "String paths may break when switching environments",
            UserWarning,
        )

    with open(file_path) as file:
        return json.load(file)


def save_json(file_path: Path | str, data: JSON_DATA_TYPES, indent: int = 2) -> None:
    """Serialize data as JSON and write it to a file.

    Args:
        file_path: Destination path. Strings are accepted but a
            warning is issued; prefer passing a ``pathlib.Path``.
        data: The data to serialize. Must be JSON-serializable.
        indent: Number of spaces for indentation (default ``2``).
    """
    if type(file_path) is str:
        warnings.warn(
            "String paths may break when switching environments",
            UserWarning,
        )

    with open(file_path, "w") as file:
        json.dump(data, file, indent=indent)
