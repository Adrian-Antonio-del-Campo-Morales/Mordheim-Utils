#!/usr/bin/env python3
"""Central command line for the Mordheim Utils repository.

A plain developer-facing launcher: pick a command and it runs the matching
Python module or script with the same interpreter. Nothing here is installed
as a package command and there is no parser to duplicate::

    python tools/mordheim-utils.py --help
    python tools/mordheim-utils.py benchmark --help

Delegated commands keep their own parsers (Combat Lab CLI, pytest,
``combine_kb_yaml.py``), so their help text and behaviour never drift.
Running from a source checkout is enough: child processes get the configured
package roots on their ``PYTHONPATH``.

The surface is grouped by task rather than by module: applications, knowledge
base, engines and repository upkeep. Reports live behind one entry point
(``report rules`` / ``report tests``) and the knowledge base has a single gate
(``verify``, with ``--structural`` for the structural-only pass).
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOTS = (
    REPO_ROOT / "packages" / "python" / "combat-engine",
    REPO_ROOT / "packages" / "python" / "roster-construction",
    REPO_ROOT / "packages" / "python" / "core",
    REPO_ROOT / "packages" / "python" / "knowledge",
    REPO_ROOT / "packages" / "python" / "adapters" / "desktop-ui",
    REPO_ROOT / "packages" / "python" / "campaign",
    REPO_ROOT / "apps" / "combat-lab",
    REPO_ROOT / "apps" / "warband-manager-desktop",
)

# Make the in-process commands (doctor) work from a fresh checkout too.
for package_root in reversed(PACKAGE_ROOTS):
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


#: Map of ``tests --scope`` names to the pytest paths they select.
SCOPE_PATHS = {
    "all": ("tests",),
    "engines": ("tests/combat", "tests/integration"),
    "modular": ("tests/combat/modular",),
    "vectorized": ("tests/combat/vectorized",),
    "native": ("tests/combat/native",),
    # The per-change engine gate: the deterministic suites that certify rule
    # behaviour without statistical noise (mirrors the coverage-gate budget).
    "deterministic": ("tests/combat/modular", "tests/combat/vectorized",
                      "tests/combat/test_phases.py", "tests/verification/test_parity.py"),
    "campaign": ("tests/campaign", "tests/application"),
    "knowledge": ("tests/knowledge", "tests/specs"),
    "verification": ("tests/verification",),
    "construction": ("tests/construction",),
    "ui": ("tests/ui",),
    "cli": ("tests/cli",),
    "architecture": ("tests/architecture",),
}

#: Combat Lab subcommands forwarded verbatim to ``python -m mordheim_combat_lab``.
LAB_COMMANDS = ("benchmark", "parity", "coverage-gate", "verify", "calibrate")

#: ``report <kind>`` forwards to the matching Combat Lab report command: the
#: two report generators share one entry point instead of two lookalike names.
REPORT_KINDS = {
    "rules": "audit",
    "tests": "test-report",
}

#: One-line usage shown by ``<command> --help`` for commands whose arguments
#: are not delegated to another parser.
USAGE = {
    "combat-lab": "python tools/mordheim-utils.py combat-lab",
    "warband-manager": "python tools/mordheim-utils.py warband-manager",
    "doctor": "python tools/mordheim-utils.py doctor",
    "build-native": "python tools/mordheim-utils.py build-native [pip install args ...]",
}

#: Command help lines, in the order shown by ``--help``.
COMMANDS = (
    ("combat-lab", "open the Combat Lab graphical application"),
    ("warband-manager", "open the Campaign Manager (warband) graphical application"),
    ("verify", "validate the KB and run the semantic specifications"),
    ("report", "generate the rule and test reports (report rules | report tests)"),
    ("benchmark", "measure the combat engines (modular, NumPy, native) with configurable sizes"),
    ("parity", "certify the vectorized and native engines against the modular oracle"),
    ("coverage-gate", "measure deterministic engine coverage and check the drift budget"),
    ("calibrate", "measure this machine's engine optima and install the calibration profile"),
    ("tests", "run the pytest suites, filtered by --scope"),
    ("run-ci", "run the local equivalent of the CI validation gates before Pages publishing"),
    ("combine-kb", "combine the KB YAML files into one .txt per subdirectory"),
    ("build-native", "compile the native Cython backend (editable install)"),
    ("doctor", "report the environment, installed engines and KB location"),
)

#: Command groups for ``--help``; every name in COMMANDS appears exactly once.
COMMAND_GROUPS = (
    ("Applications", ("combat-lab", "warband-manager")),
    ("Knowledge base", ("verify", "report")),
    ("Engines", ("benchmark", "parity", "coverage-gate", "calibrate")),
    ("Repository", ("tests", "run-ci", "combine-kb", "build-native", "doctor")),
)

COMBINE_KB_SCRIPT = REPO_ROOT / "tools" / "kb" / "combine_kb_yaml.py"
KNOWLEDGE_GENERATOR = REPO_ROOT / "tools" / "knowledge" / "generate_knowledge_web.py"
GENERATED_KNOWLEDGE = REPO_ROOT / "build" / "generated" / "knowledge-web"
WEB_KNOWLEDGE = REPO_ROOT / "apps" / "warband-manager-web" / "public" / "knowledge"
TYPESCRIPT_PACKAGE = REPO_ROOT / "packages" / "typescript"
WEB_APP = REPO_ROOT / "apps" / "warband-manager-web"


def _environment() -> dict:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = os.pathsep.join(
        [*(str(path) for path in PACKAGE_ROOTS), *( [existing] if existing else [])]
    )

    return env


def _run(*argv: str) -> int:
    """Run a child process from the repository root and return its exit code."""
    return subprocess.call(list(argv), cwd=REPO_ROOT, env=_environment())


def _run_module(module: str, *args: str) -> int:
    return _run(sys.executable, "-m", module, *args)


def _run_in(directory: Path, *argv: str) -> int:
    """Run a child process in a repository subdirectory."""
    env = _environment()
    executable = shutil.which(argv[0], path=env.get("PATH")) or argv[0]
    return subprocess.call([executable, *argv[1:]], cwd=directory, env=env)


def _print_usage(name: str, detail: str) -> int:
    print(f"usage: {USAGE[name]}")
    print(f"\n{detail}")
    return 0


def combat_lab_command(args: list[str]) -> int:
    if any(argument in ("-h", "--help") for argument in args):
        return _print_usage(
            "combat-lab", "Open the Combat Lab graphical application (Tkinter).")
    return _run_module("mordheim_combat_lab", "ui")


def warband_manager_command(args: list[str]) -> int:
    if any(argument in ("-h", "--help") for argument in args):
        return _print_usage(
            "warband-manager",
            "Open the Campaign Manager desktop application (Tkinter).")
    return _run_module("mordheim_desktop")


def lab_command(name: str, args: list[str]) -> int:
    return _run_module("mordheim_combat_lab", name, *args)


def report_command(args: list[str]) -> int:
    """``report rules|tests`` -> the matching Combat Lab report command."""
    if not args or args[0] in ("-h", "--help"):
        print("usage: python tools/mordheim-utils.py report <rules|tests> [args ...]")
        print()
        print("  rules   auditable per-rule inventory (CSV/JSON in outputs/audit/)")
        print("  tests   human-readable parity and technical test CSVs")
        print()
        print("Arguments after the kind are forwarded to the report command;")
        print("run `report <kind> --help` for its own options.")
        return 0
    kind, forwarded = args[0], args[1:]
    if kind not in REPORT_KINDS:
        print(
            f"report: unknown kind {kind!r}; choose from "
            + ", ".join(sorted(REPORT_KINDS)),
            file=sys.stderr,
        )
        return 2
    return lab_command(REPORT_KINDS[kind], forwarded)


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


def _stage_knowledge_assets() -> None:
    WEB_KNOWLEDGE.mkdir(parents=True, exist_ok=True)
    for source in GENERATED_KNOWLEDGE.glob("*.json"):
        shutil.copy2(source, WEB_KNOWLEDGE / source.name)


def run_ci_command(args: list[str]) -> int:
    """Run the checks from .github/workflows/ci.yml using local dependencies."""
    if args in (["-h"], ["--help"]):
        print("usage: python tools/mordheim-utils.py run-ci")
        print("\nRun the local CI validation gates before Pages publishing.")
        return 0
    if args:
        print("run-ci: this command does not accept arguments", file=sys.stderr)
        return 2
    for command in ((sys.executable, str(KNOWLEDGE_GENERATOR)),
                    (sys.executable, str(KNOWLEDGE_GENERATOR), "--check")):
        if _run_in(REPO_ROOT, *command):
            return 1
    _stage_knowledge_assets()
    if _run_module("pytest", "tests/web", "tests/contracts", "tests/campaign",
                   "tests/architecture", "tests/knowledge", "-q"):
        return 1
    if _run(sys.executable, str(KNOWLEDGE_GENERATOR), "--check"):
        return 1
    if _run_in(TYPESCRIPT_PACKAGE, "npm", "run", "typecheck"):
        return 1
    if _run_in(TYPESCRIPT_PACKAGE, "npm", "test"):
        return 1
    # Keep the local gate aligned with the explicit CI contract.  The full
    # `npm test` suite below still runs afterwards; this focused invocation
    # makes localization and technical-identifier regressions fail early and
    # uses the conservative Vitest worker/timeout settings required by the
    # exhaustive KB coverage test.
    if _run_in(
        WEB_APP,
        "npx", "vitest", "run", "--pool=forks", "--maxWorkers=1",
        "--testTimeout=200000",
        "src/features/campaign/knowledge-display-coverage.test.tsx",
        "src/features/campaign/ui_i18n.test.ts",
        "src/features/campaign/displayText.test.ts",
        "src/features/campaign/KnowledgeHint.test.tsx",
    ):
        return 1
    for command in (("npm", "run", "typecheck"), ("npm", "run", "lint"),
                    ("npm", "test"), ("npm", "run", "build"),
                    ("npx", "vitest", "run", "src/architecture/boundaries.test.ts")):
        if _run_in(WEB_APP, *command):
            return 1
    return 0


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
    if any(argument in ("-h", "--help") for argument in args):
        return _print_usage(
            "build-native",
            "Build the native Cython backend with `pip install -e .` from the "
            "repository root (any extra arguments are forwarded to pip).")
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
        ("Campaign Manager", "mordheim_desktop.app"),
    ):
        if importlib.util.find_spec(module) is None:
            print(f"{label}: import failed (module not found)")
        else:
            print(f"{label}: importable")
    return 0


def _print_styled(text: str) -> None:
    """Print with the shared repository palette when it is importable."""
    try:
        from mordheim_combat_lab.console import style_help
    except Exception:  # package not importable here: plain text
        sys.stdout.write(text)
        return
    sys.stdout.write(style_help(text))


def _help_text() -> str:
    by_name = dict(COMMANDS)
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
    for label, names in COMMAND_GROUPS:
        width = max(len(name) for name in names)
        lines.append("")
        lines.append(f"  {label}")
        for name in names:
            lines.append(f"    {name:<{width}}  {by_name[name]}")
    lines.extend((
        "",
        "Common tasks:",
        "    doctor                              check the environment first",
        "    tests --scope deterministic         the per-change engine gate",
        "    verify                              knowledge base before touching rules",
        "    report rules                        per-rule implementation inventory",
        "    run-ci                              everything, before publishing",
        "",
        "The engine commands (benchmark, parity, coverage-gate, calibrate) and the "
        "knowledge base gate (verify) run as `python -m mordheim_combat_lab <command>`; "
        "`report rules|tests` forwards to the `audit` and `test-report` lab commands.",
        "",
        "Tab completion (bash/zsh): source tools/completions/mordheim-utils.bash "
        "or mordheim-utils.zsh. Completion covers the command names and, for the "
        "delegated parsers, their options and choice values.",
    ))
    return "\n".join(lines) + "\n"


def _choice_values(choices) -> tuple[str, ...]:
    """Return a tuple of choice strings, or () for unbounded choices (ranges)."""
    if isinstance(choices, (tuple, list, set, frozenset)):
        return tuple(str(item) for item in choices)
    return ()


def _tests_candidates(typed: list[str]) -> list[str]:
    """Candidates after ``tests``: only the --scope values are enumerable;
    the remaining arguments are forwarded to pytest as-is."""
    current = typed[-1] if typed else ""
    previous = typed[-2] if len(typed) >= 2 else None
    if previous == "--scope":
        return sorted(scope for scope in SCOPE_PATHS if scope.startswith(current))
    if current.startswith("--scope="):
        value = current.split("=", 1)[1]
        return [f"--scope={scope}" for scope in SCOPE_PATHS if scope.startswith(value)]
    if current.startswith("-"):
        return ["--scope"]
    return []


def _report_candidates(typed: list[str]) -> list[str]:
    """Candidates after ``report``: the kind, then the report's own options."""
    current = typed[-1] if typed else ""
    if len(typed) <= 1:
        return [kind for kind in REPORT_KINDS if kind.startswith(current)]
    return _lab_candidates(REPORT_KINDS[typed[0]], typed[1:])


def _lab_candidates(command: str, typed: list[str]) -> list[str]:
    """Candidates for a lab command, introspected from its real argparse parser
    so the completion never drifts from the actual options."""
    current = typed[-1] if typed else ""
    previous = typed[-2] if len(typed) >= 2 else None
    try:
        from mordheim_combat_lab.cli.commands import build_parser
    except Exception:
        return []
    parser = build_parser()
    subparsers = next(
        (action for action in parser._actions
         if action.__class__.__name__ == "_SubParsersAction"),
        None,
    )
    if subparsers is None or command not in subparsers.choices:
        return []
    subparser = subparsers.choices[command]
    valued: dict[str, tuple[bool, object]] = {}
    for action in subparser._actions:
        if not action.option_strings or action.__class__.__name__ == "_HelpAction":
            continue
        takes_value = action.nargs != 0
        for option in action.option_strings:
            valued[option] = (takes_value, action.choices)
    options = sorted(valued)
    if current.startswith("-"):
        return [option for option in options if option.startswith(current)]
    if previous in valued:
        takes_value, choices = valued[previous]
        values = _choice_values(choices)
        if takes_value and values:
            return [value for value in values if value.startswith(current)]
        if takes_value:
            return []  # free-form value; let the shell fall back to files
        if not current:
            return [option for option in options if option != previous]
        return []
    if not current:
        return options
    return []


def _command_candidates(words: list[str]) -> list[str]:
    """Return the completion candidates for the words typed after the launcher
    program name (the last word may be the partially typed token)."""
    names = [name for name, _ in COMMANDS]
    if not words:
        return names
    if len(words) == 1:
        current = words[0]
        return [name for name in names if name.startswith(current)]
    head, rest = words[0], words[1:]
    if head == "tests":
        return _tests_candidates(rest)
    if head == "report":
        return _report_candidates(rest)
    if head in LAB_COMMANDS:
        return _lab_candidates(head, rest)
    return []


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw or raw[0] in ("-h", "--help"):
        _print_styled(_help_text())
        return 0
    if raw[0] == "--version":
        try:
            version = importlib.metadata.version("mordheim-utils")
        except importlib.metadata.PackageNotFoundError:
            version = "not installed (source checkout)"
        print(f"mordheim-utils {version}")
        return 0
    name, args = raw[0], raw[1:]
    if name in ("doctor",) and any(argument in ("-h", "--help") for argument in args):
        return _print_usage(
            "doctor",
            "Report the Python version, installed engines and KB location, "
            "then exit.")
    if name == "combat-lab":
        return combat_lab_command(args)
    if name == "warband-manager":
        return warband_manager_command(args)
    if name == "report":
        return report_command(args)
    if name == "tests":
        return tests_command(args)
    if name == "run-ci":
        return run_ci_command(args)
    if name == "combine-kb":
        return combine_kb_command(args)
    if name == "build-native":
        return build_native_command(args)
    if name == "doctor":
        return doctor_command()
    if name == "_complete":
        for candidate in _command_candidates(args):
            print(candidate)
        return 0
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
