"""
Results Writer Module

This module provides functionality to write workflow results to JSON files.
It handles serialization and ensures proper formatting of output data.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


# Default output directory relative to module
MODULE_DIR = Path(__file__).parent
DEFAULT_OUTPUT_DIR = MODULE_DIR / "output"


class ResultsWriter:
    """
    Write workflow results to JSON files.

    This class handles serialization of results data to JSON format,
    with proper formatting and error handling.

    Example:
        writer = ResultsWriter()
        writer.write(results, "output/results.json")

        # Or with custom output directory
        writer = ResultsWriter(output_dir="custom/path")
        writer.write(results, "results.json")
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the results writer.

        Args:
            output_dir: Directory for output files. If None, uses default
                       output directory relative to module location.
        """
        if output_dir is None:
            self.output_dir = DEFAULT_OUTPUT_DIR
        else:
            self.output_dir = Path(output_dir)

    def write(
        self,
        results: Dict[str, Any],
        filename: str = "results.json",
        indent: int = 2
    ) -> Path:
        """
        Write results to JSON file.

        Args:
            results: Dictionary of results to write
            filename: Output filename (relative to output_dir or absolute)
            indent: JSON indentation level (default: 2)

        Returns:
            Path to written file

        Raises:
            OSError: If unable to write to file
        """
        # Determine output path
        output_path = Path(filename)
        if not output_path.is_absolute():
            output_path = self.output_dir / filename

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=indent, ensure_ascii=False)

        return output_path

    def write_pretty(
        self,
        results: Dict[str, Any],
        filename: str = "results.json"
    ) -> Path:
        """
        Write results with pretty formatting (4-space indent).

        Args:
            results: Dictionary of results to write
            filename: Output filename

        Returns:
            Path to written file
        """
        return self.write(results, filename, indent=4)

    def write_compact(
        self,
        results: Dict[str, Any],
        filename: str = "results.json"
    ) -> Path:
        """
        Write results in compact format (no indentation).

        Args:
            results: Dictionary of results to write
            filename: Output filename

        Returns:
            Path to written file
        """
        return self.write(results, filename, indent=None)


def serialize_results(results: Dict[str, Any]) -> str:
    """
    Serialize results to JSON string.

    Args:
        results: Dictionary of results

    Returns:
        JSON string representation
    """
    return json.dumps(results, indent=2, ensure_ascii=False)
