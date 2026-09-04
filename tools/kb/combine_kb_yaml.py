#!/usr/bin/env python3
"""Combine the YAML files of each KB directory into separate text files."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from mordheim_combat_lab.console import HelpFormatter as _HelpFormatter
except Exception:  # standalone run without the package importable
    _HelpFormatter = argparse.HelpFormatter


SEPARATOR = "=" * 80


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="combine-kb",
        description=(
            "Generates one .txt per KB subdirectory, combining its .yaml and "
            ".yml files recursively."
        ),
        epilog="Run from a source checkout: python tools/mordheim-utils.py combine-kb",
        formatter_class=_HelpFormatter,
    )
    parser.add_argument(
        "kb_path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        metavar="KB",
        help="Parent/root directory of the KB (default: current directory).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("kb-combined"),
        metavar="DIR",
        help="Output directory (default: kb-combined).",
    )
    return parser.parse_args()


def write_delimiter(output, label: str, file_path: Path, root: Path) -> None:
    """Write the start/end block with file metadata."""
    try:
        relative_path = file_path.relative_to(root)
    except ValueError:
        relative_path = file_path

    output.write(f"{SEPARATOR}\n")
    output.write(f"{label}\n")
    output.write(f"Name: {file_path.name}\n")
    output.write(f"Relative path: {relative_path}\n")
    output.write(f"{SEPARATOR}\n")


def yaml_files_in(directory: Path) -> list[Path]:
    """Return the YAML files of the directory, including its subfolders."""
    return sorted(
        (
            path for path in directory.rglob("*")
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
        ),
        key=lambda path: str(path).lower(),
    )


def main() -> None:
    args = parse_arguments()
    root = args.kb_path.expanduser().resolve()
    output_directory = args.output.expanduser().resolve()

    if not root.is_dir():
        raise SystemExit(f"Error: the KB path is not a valid directory: {root}")

    directories = sorted(
        (path for path in root.iterdir() if path.is_dir() and path.resolve() != output_directory),
        key=lambda path: path.name.lower(),
    )

    output_directory.mkdir(parents=True, exist_ok=True)
    total_files = 0
    for directory in directories:
        yaml_files = yaml_files_in(directory)
        output_path = output_directory / f"{directory.name}.txt"

        with output_path.open("w", encoding="utf-8", newline="\n") as output:
            for file_path in yaml_files:
                write_delimiter(output, "START OF FILE", file_path, root)
                output.write("\n")

                try:
                    output.write(file_path.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    output.write(
                        "[Could not read as UTF-8. "
                        "Convert this file to UTF-8 to include it.]\n"
                    )
                except OSError as error:
                    output.write(f"[Could not read the file: {error}]\n")

                if file_path.stat().st_size:
                    output.write("\n")
                write_delimiter(output, "END OF FILE", file_path, root)
                output.write("\n")

        total_files += len(yaml_files)
        print(f"{directory.name}: {len(yaml_files)} file(s) -> {output_path}")

    print(
        f"Combination finished: {total_files} YAML files across "
        f"{len(directories)} output file(s)."
    )
    print(f"Output directory: {output_directory}")


if __name__ == "__main__":
    main()
