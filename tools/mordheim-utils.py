#!/usr/bin/env python3
"""Central command line for the Mordheim Utils repository.

A plain developer-facing launcher: pick a command and it runs the matching
Python module or script with the same interpreter. Nothing here is installed
as a package command and there is no parser to duplicate::

    python tools/mordheim-utils.py --help
    python tools/mordheim-utils.py benchmark --help

Delegated commands keep their own parsers (Combat Lab CLI, pytest,
``combine_kb_yaml.py``), so their help text and behaviour never drift.
Running from a source checkout is enough: child processes get ``src/`` on
their ``PYTHONPATH``.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"

# Make the in-process commands (doctor) work from a fresh checkout too.
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

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

#: Combat Lab subcommands forwarded verbatim to ``python -m mordheim_combat_lab``.
LAB_COMMANDS = ("benchmark", "parity", "test-report", "verify", "audit", "validate")

#: Command help lines, in the order shown by ``--help``.
COMMANDS = (
    ("combat-lab", "open the Combat Lab graphical application"),
    ("warband-manager", "open the Campaign Manager (warband) graphical application"),
    ("benchmark", "measure the combat engines (modular, NumPy, native) with configurable sizes"),
    ("parity", "certify the vectorized engine against the modular oracle"),
    ("test-report", "generate the human-readable parity and technical test CSVs"),
    ("verify", "run the semantic specifications against the modular engine"),
    ("audit", "generate the auditable rule inventory"),
    ("validate", "validate the KB and structural connections"),
    ("tests", "run the pytest suites, filtered by --scope"),
    ("combine-kb", "combine the KB YAML files into one .txt per subdirectory"),
    ("build-native", "compile the native Cython backend (editable install)"),
    ("doctor", "report the environment, installed engines and KB location"),
)

COMBINE_KB_SCRIPT = REPO_ROOT / "tools" / "kb" / "combine_kb_yaml.py"


def _environment() -> dict:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(SRC) + (os.pathsep + existing if existing else "")
    return env


def _run(*argv: str) -> int:
    """Run a child process from the repository root and return its exit code."""
    return subprocess.call(list(argv), cwd=REPO_ROOT, env=_environment())


def _run_module(module: str, *args: str) -> int:
    return _run(sys.executable, "-m", module, *args)


def combat_lab_command(_args: list[str]) -> int:
    return _run_module("mordheim_combat_lab", "ui")


def warband_manager_command(_args: list[str]) -> int:
    return _run_module("mordheim_campaign")


def lab_command(name: str, args: list[str]) -> int:
    return _run_module("mordheim_combat_lab", name, *args)


def tests_command(args: list[str]) -> int:
    scope = "all"
    forwarded: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--scope":
            if index + 1 >= len(args):
                print("tests: --scope requires a value", file=sys.stderr)
                return 2
            scope = args[index + 1]
            index += 2
            continue
        if arg.startswith("--scope="):
            scope = arg.split("=", 1)[1]
            index += 1
            continue
        forwarded.append(arg)
        index += 1
    if scope not in SCOPE_PATHS:
        print(
            f"tests: unknown scope {scope!r}; choose from "
            + ", ".join(SCOPE_PATHS),
            file=sys.stderr,
        )
        return 2
    if forwarded and forwarded[0] == "--":
        forwarded.pop(0)
    return _run_module("pytest", *SCOPE_PATHS[scope], *forwarded)


def combine_kb_command(args: list[str]) -> int:
    if not COMBINE_KB_SCRIPT.is_file():
        print(
            f"combine-kb: script not found at {COMBINE_KB_SCRIPT}; "
            "this command requires a source checkout",
            file=sys.stderr,
        )
        return 2
    return _run(sys.executable, str(COMBINE_KB_SCRIPT), *args)


def build_native_command(args: list[str]) -> int:
    command = [sys.executable, "-m", "pip", "install", "-e", ".", *args]
    print("Building the native Cython backend with: " + " ".join(command))
    return _run(*command)


def doctor_command() -> int:
    print(f"Python: {sys.version.split()[0]} ({platform.platform()})")
    try:
        version = importlib.metadata.version("mordheim-utils")
    except importlib.metadata.PackageNotFoundError:
        version = "not installed (source checkout)"
    print(f"mordheim-utils: {version}")
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


def _help_text() -> str:
    width = max(len(name) for name, _ in COMMANDS)
    lines = [
        "usage: python tools/mordheim-utils.py <command> [args ...]",
        "",
        "Central command line for the Mordheim Utils project: the two graphical "
        "applications and every utility, run from a source checkout. Detailed "
        "arguments of a delegated command come from the command itself "
        "(`<command> --help` opens its own parser).",
        "",
        "commands:",
    ]
    for name, help_text in COMMANDS:
        lines.append(f"  {name:<{width}}  {help_text}")
    lines.extend((
        "",
        "The lab commands (benchmark, parity, test-report, verify, audit, validate) "
        "run as `python -m mordheim_combat_lab <command>`; the underlying modules "
        "and scripts remain callable directly.",
    ))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw or raw[0] in ("-h", "--help"):
        print(_help_text(), end="")
        return 0
    if raw[0] == "--version":
        try:
            version = importlib.metadata.version("mordheim-utils")
        except importlib.metadata.PackageNotFoundError:
            version = "not installed (source checkout)"
        print(f"mordheim-utils {version}")
        return 0
    name, args = raw[0], raw[1:]
    if name == "combat-lab":
        return combat_lab_command(args)
    if name == "warband-manager":
        return warband_manager_command(args)
    if name == "tests":
        return tests_command(args)
    if name == "combine-kb":
        return combine_kb_command(args)
    if name == "build-native":
        return build_native_command(args)
    if name == "doctor":
        return doctor_command()
    if name in LAB_COMMANDS:
        return lab_command(name, args)
    print(f"mordheim-utils: unknown command {name!r}", file=sys.stderr)
    print(
        "Run `python tools/mordheim-utils.py --help` to list the commands.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
