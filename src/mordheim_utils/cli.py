"""Central command line interface for the Mordheim Utils project.

``mordheim-utils`` is the single entry point for both graphical applications
and every utility shipped in the repository::

    mordheim-utils --help            # overview of every command
    mordheim-utils benchmark --help  # detailed arguments of one command

Commands that already exist in the Combat Lab CLI delegate to the exact same
parsers, so their help text and behaviour never drift from the lab's own
``mordheim-combat-lab`` entry point.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import platform
import runpy
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Map of ``tests --scope`` names to the pytest paths they select.
SCOPE_PATHS = {
    "all": ("tests",),
    "engines": ("tests/combat", "tests/integration"),
    "modular": ("tests/combat/modular",),
    "vectorized": ("tests/combat/vectorized",),
    "native": ("tests/combat/native",),
    "campaign": ("tests/campaign", "tests/application"),
    "knowledge": ("tests/knowledge", "tests/specs"),
    "verification": ("tests/verification",),
    "construction": ("tests/construction",),
    "ui": ("tests/ui",),
    "cli": ("tests/cli",),
    "architecture": ("tests/architecture",),
}

_COMBINE_KB_SCRIPT = REPO_ROOT / "tools" / "kb" / "combine_kb_yaml.py"


def _version() -> str:
    try:
        return importlib.metadata.version("mordheim-utils")
    except importlib.metadata.PackageNotFoundError:
        return "unknown (editable checkout)"


def _forward_lab_command(name: str, rest: list[str]) -> int:
    """Dispatch to the Combat Lab CLI parser for the given subcommand."""
    from mordheim_combat_lab.cli import commands

    # The lab parser appends the subcommand name to the prog itself.
    parser = commands.build_parser(prog="mordheim-utils")
    args = parser.parse_args([name, *rest])
    if (
        name == "verify"
        and getattr(args, "inventory", False)
        and getattr(args, "require_complete", False)
    ):
        parser.error("--inventory and --require-complete cannot be combined")
    return args.handler(args)


def combat_lab_command(_args: argparse.Namespace) -> int:
    from mordheim_combat_lab.ui.app import main

    return int(main() or 0)


def warband_manager_command(_args: argparse.Namespace) -> int:
    from mordheim_campaign.app import main

    return int(main() or 0)


def _run_pytest(scope: str, pytest_args: list[str]) -> int:
    cleaned = list(pytest_args)
    if cleaned and cleaned[0] == "--":
        cleaned.pop(0)
    command = [sys.executable, "-m", "pytest", *SCOPE_PATHS[scope], *cleaned]
    return subprocess.call(command, cwd=REPO_ROOT)


def tests_command(args: argparse.Namespace) -> int:
    return _run_pytest(args.scope, list(args.pytest_args))


def combine_kb_command(args: argparse.Namespace) -> int:
    """Mirror the two arguments of ``tools/kb/combine_kb_yaml.py``; keep in sync."""
    if not _COMBINE_KB_SCRIPT.is_file():
        print(
            f"combine-kb: script not found at {_COMBINE_KB_SCRIPT}; "
            "this command requires a source checkout",
            file=sys.stderr,
        )
        return 2
    forwarded = []
    if args.kb_path is not None:
        forwarded.append(str(args.kb_path))
    if args.output is not None:
        forwarded.extend(["-o", str(args.output)])
    previous = sys.argv
    sys.argv = [str(_COMBINE_KB_SCRIPT), *forwarded]
    try:
        runpy.run_path(str(_COMBINE_KB_SCRIPT), run_name="__main__")
    finally:
        sys.argv = previous
    return 0


def build_native_command(args: argparse.Namespace) -> int:
    command = [sys.executable, "-m", "pip", "install", "-e", ".", *args.args]
    print("Building the native Cython backend with: " + " ".join(command))
    return subprocess.call(command, cwd=REPO_ROOT)


def doctor_command(_args: argparse.Namespace) -> int:
    print(f"Python: {sys.version.split()[0]} ({platform.platform()})")
    print(f"mordheim-utils: {_version()}")
    for package in ("numpy", "PyYAML", "openpyxl"):
        try:
            print(f"{package}: {importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError:
            print(f"{package}: not installed")
    try:
        from mordheim_combat.vectorized import available_backends

        optimized = available_backends()
        print("optimized combat backends: " + (", ".join(optimized) if optimized else "none"))
        print("modular reference engine: always available")
    except Exception as error:  # pragma: no cover - defensive
        print(f"combat backends: unavailable ({error})")
    try:
        from mordheim_knowledge.loader import knowledge_root

        print(f"knowledge root: {knowledge_root()}")
    except Exception as error:  # pragma: no cover - defensive
        print(f"knowledge root: unavailable ({error})")
    for label, module in (
        ("Combat Lab", "mordheim_combat_lab.ui.app"),
        ("Campaign Manager", "mordheim_campaign.app"),
    ):
        if importlib.util.find_spec(module) is None:
            print(f"{label}: import failed (module not found)")
        else:
            print(f"{label}: importable")
    return 0


#: Combat Lab commands delegated verbatim to their original parser.
LAB_FORWARDED_COMMANDS = frozenset(
    {"benchmark", "parity", "test-report", "verify", "audit", "validate"}
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mordheim-utils",
        description=(
            "Central command line for the Mordheim Utils project: both graphical "
            "applications and every utility (benchmarking, parity, verification, "
            "audits, KB tooling and the test suites)."
        ),
        epilog=(
            "Run `mordheim-utils <command> --help` for the detailed arguments of "
            "any command; the lab commands (benchmark, parity, test-report, verify, "
            "audit, validate) reuse the Combat Lab parsers verbatim."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"mordheim-utils {_version()}"
    )
    commands = parser.add_subparsers(dest="command", metavar="<command>")

    # Applications.
    commands.add_parser(
        "combat-lab", help="open the Combat Lab graphical application"
    ).set_defaults(handler=combat_lab_command)
    commands.add_parser(
        "warband-manager", help="open the Campaign Manager (warband) graphical application"
    ).set_defaults(handler=warband_manager_command)

    # Combat Lab utilities (delegated parsers keep their detailed help).
    for name, help_text in (
        (
            "benchmark",
            "measure the combat engines (modular, NumPy, native) with configurable sizes",
        ),
        ("parity", "certify the vectorized engine against the modular oracle"),
        ("test-report", "generate the human-readable parity and technical test CSVs"),
        ("verify", "run the semantic specifications against the modular engine"),
        ("audit", "generate the auditable rule inventory"),
        ("validate", "validate the KB and structural connections"),
    ):
        commands.add_parser(name, help=help_text)

    # Project-wide utilities.
    tests = commands.add_parser(
        "tests", help="run the pytest suites, filtered by scope"
    )
    tests.add_argument(
        "--scope",
        choices=tuple(SCOPE_PATHS),
        default="all",
        help="test area to run (default: all)",
    )
    tests.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        metavar="[PYTEST_ARGS ...]",
        help="extra arguments forwarded to pytest (e.g. `-k name -x`; a `--` is optional)",
    )
    tests.set_defaults(handler=tests_command)

    combine_kb = commands.add_parser(
        "combine-kb",
        help="combine the KB YAML files into one .txt per subdirectory",
        description=(
            "Thin wrapper around tools/kb/combine_kb_yaml.py; the arguments "
            "mirror that script."
        ),
    )
    combine_kb.add_argument(
        "kb_path", nargs="?", type=Path,
        help="parent/root directory of the KB (default: current directory)",
    )
    combine_kb.add_argument(
        "-o", "--output", type=Path,
        help="output directory (default: kb-combined)",
    )
    combine_kb.set_defaults(handler=combine_kb_command)

    build_native = commands.add_parser(
        "build-native",
        help="compile the native Cython backend (editable install)",
    )
    build_native.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        metavar="-- [PIP_ARGS ...]",
        help="extra arguments forwarded to `pip install -e .`",
    )
    build_native.set_defaults(handler=build_native_command)

    commands.add_parser(
        "doctor",
        help="report the environment, installed engines and KB location",
    ).set_defaults(handler=doctor_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        name = argv[0]
        if name in LAB_FORWARDED_COMMANDS:
            # Full pass-through: the lab parser prints its own detailed help
            # for `--help` and rejects unknown arguments with the same message
            # as `mordheim-combat-lab <command>`.
            return _forward_lab_command(name, list(argv[1:]))
        if name == "tests":
            # Anything the umbrella does not recognize (pytest flags such as
            # `-q`, `-x` or `-k`) is forwarded to pytest, with or without `--`.
            parser = build_parser()
            args, extras = parser.parse_known_args(argv)
            return _run_pytest(args.scope, [*extras, *args.pytest_args])
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    return args.handler(args)