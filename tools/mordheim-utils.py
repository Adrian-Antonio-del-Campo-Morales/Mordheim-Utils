#!/usr/bin/env python3
"""Central command line for the Mordheim Utils repository.

Four task groups, each with commands and, where useful, named subsections::

    python tools/mordheim-utils.py app combat-lab
    python tools/mordheim-utils.py tests modular mechanics -n 8 --dist=load -q
    python tools/mordheim-utils.py performance benchmark --scenario basic
    python tools/mordheim-utils.py check verify

``app`` launches an application, ``tests`` selects one maintained test area,
``performance`` measures execution and ``check`` runs the validation, report and
local-CI entry points.

Delegated commands keep their own parsers (the Combat Lab CLI, pytest and
Vitest). Local help offers practical examples; --help-full exposes the complete
application parser for performance/check/report commands. Running from a source
checkout is enough: child processes get the configured package roots on their
``PYTHONPATH``.
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
TESTS_ROOT = REPO_ROOT / "tests"
PACKAGE_ROOTS = (
    REPO_ROOT,
    REPO_ROOT / "packages" / "python" / "combat-engine",
    REPO_ROOT / "packages" / "python" / "roster-construction",
    REPO_ROOT / "packages" / "python" / "core",
    REPO_ROOT / "packages" / "python" / "knowledge",
    REPO_ROOT / "apps" / "combat-lab",
)

# Make the in-process diagnostics work from a fresh checkout too.
for package_root in reversed(PACKAGE_ROOTS):
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

KNOWLEDGE_GENERATOR = REPO_ROOT / "tools" / "knowledge" / "generate_knowledge_web.py"
TYPESCRIPT_PACKAGE = REPO_ROOT / "packages" / "typescript"
WEB_APP = REPO_ROOT / "apps" / "warband-manager-web"

#: ``check report <kind>`` forwards to the matching Combat Lab report command.
REPORT_KINDS = {
    "rules": "audit",
    "tests": "test-report",
}

APP_COMMANDS = {
    "combat-lab": "open the desktop Combat Lab (Tkinter)",
    "warband-manager": "start the web Campaign Manager development server",
}

PERFORMANCE_COMMANDS = {
    "benchmark": "measure engine execution for one scenario or pair set",
    "calibrate": "measure and save this machine's engine optima",
}

CHECK_COMMANDS = {
    "verify": "knowledge-base structural verification (Combat Lab `verify`)",
    "report": "generate the rule inventory or the test reports",
    "parity": "statistical parity campaign (Combat Lab `parity`)",
    "coverage": "code-coverage budget gate (Combat Lab `coverage-gate`)",
    "presentation": "web text, translation and presentation audits",
    "ci": "run the local CI validation gates",
}

#: The tests hierarchy.  ``runs`` is what the bare name executes, ``subsections``
#: are the narrower named selections.  A run is ``("pytest", paths)``,
#: ``("vitest", extra_args)`` or ``("diagnostics", ())``.  ``dirs`` is the
#: on-disk area used by ``--list``; it never implies that a runner is selected.
TESTS_SECTIONS = {
    "env": {
        "summary": "environment, dependency and engine diagnostics; no test suite",
        "dirs": (),
        "subsections": {},
        "runs": (("diagnostics", ()),),
        "example_options": "",
    },
    "combat-lab": {
        "summary": "Combat Lab application tests (pytest)",
        "dirs": ("tests/applications/combat_lab",),
        "subsections": {},
        "runs": (("pytest", ("tests/applications/combat_lab",)),),
        "example_options": "-n 8 --dist=load -q",
    },
    "warband-manager": {
        "summary": "Warband Manager tests: Python (pytest) and web (Vitest)",
        "dirs": ("tests/applications/warband_manager",),
        "subsections": {
            "python": (("pytest", ("tests/applications/warband_manager",)),),
            "web": (("vitest", ()),),
        },
        # The two runners take different options, so this selection has no
        # shared default: `tests warband-manager` prints its help.
        "runs": (),
        "example_options": "-n 8 --dist=load -q",
    },
    "modular": {
        "summary": "modular reference engine: individual rules and runtime",
        "dirs": ("tests/engines/modular",),
        "subsections": {
            "mechanics": (("pytest", ("tests/engines/modular/mechanics",)),),
            "runtime": (("pytest", ("tests/engines/modular/runtime",)),),
        },
        "runs": (
            ("pytest", ("tests/engines/modular/mechanics",)),
            ("pytest", ("tests/engines/modular/runtime",)),
        ),
        # runtime/ holds an inner process pool, so only mechanics parallelizes.
        "example_options": "-q",
        "subsection_options": {"mechanics": "-n 8 --dist=load -q"},
    },
    "vectorized": {
        "summary": "NumPy engine: mechanics and runtime",
        "dirs": ("tests/engines/vectorized",),
        "subsections": {
            "mechanics": (("pytest", ("tests/engines/vectorized/mechanics",)),),
            "runtime": (("pytest", ("tests/engines/vectorized/runtime",)),),
        },
        "runs": (
            ("pytest", ("tests/engines/vectorized/mechanics",)),
            ("pytest", ("tests/engines/vectorized/runtime",)),
        ),
        # runtime/ holds an inner process pool, so only mechanics parallelizes.
        "example_options": "-q",
        "subsection_options": {"mechanics": "-n 8 --dist=load -q"},
    },
    "native": {
        "summary": "native engine checks (skipped when the extension is absent)",
        "dirs": ("tests/engines/native",),
        "subsections": {
            "runtime": (("pytest", ("tests/engines/native/runtime",)),),
        },
        # The native suite also has a root-level engine file outside runtime/.
        "runs": (("pytest", ("tests/engines/native",)),),
        "example_options": "-q",
    },
    "kb": {
        "summary": "knowledge base; construction and E2E are separate selections",
        "dirs": ("tests/knowledge", "tests/construction", "tests/integration/e2e"),
        "subsections": {
            "construction": (("pytest", ("tests/construction",)),),
            "e2e": (("pytest", ("tests/integration/e2e",)),),
        },
        # Plain `tests kb` is the knowledge suite only: the construction and
        # E2E batteries are large and must be selected deliberately. The E2E
        # corpus keeps its example serial; CI runs it that way too.
        "runs": (("pytest", ("tests/knowledge",)),),
        "example_options": "-n 8 --dist=load -q",
        "subsection_options": {"construction": "-n 8 --dist=load -q",
                               "e2e": "-q"},
    },
    "parity": {
        "summary": "statistical comparisons and the tooling that checks them",
        "dirs": ("tests/engines/parity", "tests/tooling/parity"),
        "subsections": {
            "statistical": (("pytest", ("tests/engines/parity/statistical",)),),
            "tooling": (("pytest", ("tests/tooling/parity",)),),
        },
        "runs": (
            ("pytest", ("tests/engines/parity/statistical",)),
            ("pytest", ("tests/tooling/parity",)),
        ),
        # The statistical runner creates its own process pools: keep pytest serial.
        "example_options": "-q",
    },
    "shared": {
        "summary": "shared engine contracts and frozen-input integrity",
        "dirs": ("tests/engines/shared",),
        "subsections": {},
        "runs": (("pytest", ("tests/engines/shared",)),),
        "example_options": "-q",
    },
    "tooling": {
        "summary": "repository tooling: architecture, launcher and coverage checks",
        "dirs": ("tests/tooling/architecture", "tests/tooling/launcher",
                 "tests/tooling/coverage"),
        "subsections": {
            "architecture": (("pytest", ("tests/tooling/architecture",)),),
            "web": (("vitest", ("--project", "architecture")),),
            "launcher": (("pytest", ("tests/tooling/launcher",)),),
            "coverage": (("pytest", ("tests/tooling/coverage",)),),
        },
        "runs": (
            ("pytest", ("tests/tooling/architecture", "tests/tooling/launcher",
                        "tests/tooling/coverage")),
        ),
        "example_options": "-q",
        "subsection_options": {"architecture": "-n 8 --dist=load -q",
                               "launcher": "-n 8 --dist=load -q"},
    },
}

#: Python test files are recognised by name; the launcher never rewrites them.
TEST_FILE_SUFFIXES = (".test.ts", ".test.tsx", ".test.mjs")


def _environment() -> dict:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = os.pathsep.join(
        [*(str(path) for path in PACKAGE_ROOTS), *([existing] if existing else [])]
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


def _print_styled(text: str) -> None:
    """Print with the shared repository palette when it is importable."""
    try:
        from mordheim_combat_lab.console import style_help
    except Exception:  # package not importable here: plain text
        sys.stdout.write(text)
        return
    sys.stdout.write(style_help(text))


def _delegated_help(usage: str, detail: str, runs: str, own_options: str,
                    *, examples=(), notes=()) -> int:
    """A compact guide, without executing the delegated command."""
    lines = [f"usage: {usage}", "", detail, "", "Options:"]
    lines.extend("  " + line for line in own_options.splitlines())
    if examples:
        lines.extend(("", "Examples:"))
        lines.extend("  python tools/mordheim-utils.py " + example for example in examples)
    if notes:
        lines.extend(("", "Notes:"))
        lines.extend("  " + note for note in notes)
    lines.extend(("", "Executes:", "  " + runs))
    print("\n".join(lines))
    return 0


# ---------------------------------------------------------------------------
# Application launchers
# ---------------------------------------------------------------------------


def _app_help() -> str:
    lines = [
        "usage: python tools/mordheim-utils.py app <command> [options]",
        "",
        "commands:",
    ]
    for name, summary in APP_COMMANDS.items():
        lines.append(f"  {name:<16} {summary}")
    lines.extend((
        "",
        "Examples:",
        "  python tools/mordheim-utils.py app combat-lab",
        "  python tools/mordheim-utils.py app warband-manager --port 5199 --strictPort",
        "",
        "Options after the command go to the application launcher, not to this tool.",
    ))
    return "\n".join(lines) + "\n"


def app_command(args: list[str]) -> int:
    if not args or args[0] in ("-h", "--help"):
        print(_app_help())
        return 0
    name, forwarded = args[0], args[1:]
    if name not in APP_COMMANDS:
        print(f"app: unknown command {name!r}; use app --help", file=sys.stderr)
        return 2
    if any(argument in ("-h", "--help") for argument in forwarded):
        if name == "combat-lab":
            return _delegated_help(
                "python tools/mordheim-utils.py app combat-lab",
                "Open the Combat Lab graphical application (Tkinter).",
                "python -m mordheim_combat_lab ui",
                "-h, --help  show this guide; no execution options",
                examples=("app combat-lab",),
            )
        return _delegated_help(
            "python tools/mordheim-utils.py app warband-manager [vite args ...]",
            "Start the Campaign Manager development server.",
            "npm run dev in apps/warband-manager-web",
            "--port N      development server port\n--strictPort  fail rather than choose another port",
            examples=("app warband-manager", "app warband-manager --port 5199 --strictPort"),
            notes=("Starts a development server; it does not run application tests.",),
        )
    if name == "combat-lab":
        if forwarded:
            print("app combat-lab: no arguments expected", file=sys.stderr)
            return 2
        return _run_module("mordheim_combat_lab", "ui")
    return _run_in(WEB_APP, "npm", "run", "dev", "--", *forwarded)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def _tests_help(name: str | None = None) -> str:
    if name is None:
        lines = [
            "usage: python tools/mordheim-utils.py tests <section> [subsection ...] [options]",
            "", "Select a responsibility, then narrow it if needed. Nothing runs without a section.",
            "", "Sections:",
        ]
        for key, section in TESTS_SECTIONS.items():
            lines.append(f"  {key:<18} {section['summary']}")
            if section["subsections"]:
                lines.append("    -> " + ", ".join(section["subsections"]))
        lines.extend((
            "", "Find the right command:",
            "  tests modular mechanics -h     rule checks and eight-worker examples",
            "  tests modular runtime -h       execution/state/parallelism checks",
            "  tests kb -h                    knowledge; construction and E2E are separate",
            "  tests warband-manager -h        choose python or web explicitly",
            "  tests parity -h                statistical tests versus runner self-checks",
            "", "Discover versus execute:",
            "  --list                         list files on disk; no imports",
            "  --collect-only                 pytest case collection; imports, no test bodies",
            "  -k EXPRESSION                  filter Python test names",
            "  -n 8 --dist=load               eight pytest workers for independent checks",
            "  --maxWorkers=8                 eight Vitest workers",
            "", "Examples:",
            "  python tools/mordheim-utils.py tests modular mechanics -n 8 --dist=load -q",
            "  python tools/mordheim-utils.py tests modular runtime -q --tb=short",
            "  python tools/mordheim-utils.py tests kb construction -n 8 --dist=load -q",
            "  python tools/mordheim-utils.py tests warband-manager web --maxWorkers=8",
            "", "Use section/subsection names, not engines/modular/runtime as a section.",
            "Explicit existing test paths/node IDs after a section replace its default paths.",
            "No sequencer or phase ordering. Tests with inner pools stay serial in pytest.",
            "`check parity` runs catalogued scenarios; `tests parity` tests that infrastructure",
            "and the existing engine comparisons. See docs/reference/tools.md.",
        ))
        return "\n".join(lines) + "\n"

    section = TESTS_SECTIONS[name]
    prefix = f"python tools/mordheim-utils.py tests {name}"
    details = {
        "env": "Print versions, dependencies, available engines and KB location. No pytest suite runs.",
        "combat-lab": "Test the desktop application's behavior, not a complete combat-rule battery.",
        "warband-manager": "Choose python (persistence/contracts) or web (Vitest). Neither is selected implicitly.",
        "modular": "Mechanics checks game rules. Runtime checks simulation, state, observations and parallelism.",
        "vectorized": "Existing NumPy mechanics/runtime checks; statistical engine equivalence is tested separately.",
        "native": "Test the compiled engine and its runtime. Without the extension tests may skip, not pass.",
        "kb": "The bare section runs knowledge contracts only. construction and e2e are explicit alternatives.",
        "parity": "statistical runs engine comparisons; tooling tests the comparator/runner. Bare selection runs both.",
        "shared": "Common engine contracts and frozen-corpus codec/catalogue integrity; no complete rule battery.",
        "tooling": "Check test/development tools. Python is the bare default; web selects architecture Vitest checks.",
    }
    lines = [f"usage: {prefix}" + (" [subsection ...]" if section["subsections"] else "") + " [options]",
             "", details[name], "", "Default selection:", "  " + _describe_runs(section["runs"])]
    if section["subsections"]:
        lines.extend(("", "Subsections (explicitly replace the default):"))
        for sub, runs in section["subsections"].items():
            lines.append(f"  {sub}")
            lines.append("    " + _describe_runs(runs))
        lines.append(f"  Use tests {name} <subsection> -h for its options and examples.")
    if section["dirs"]:
        lines.extend(("", "Discovery and selection:",
                      f"  tests {name} --list        file listing, no imports; may include subsection files",
                      "  Existing file/directory/node IDs replace the default selection.",
                      "  Quote parameterized node IDs. Multiple subsections select their union."))
    lines.extend(("", "Examples:", *["  " + example for example in _selection_examples(name, section)]))
    if name != "env":
        lines.extend(("", "Runner options:",
                      "  pytest: -k NAME, -q, -v, --tb=short, --durations=10, --collect-only",
                      "  pytest: -n 8 --dist=load only for independent checks; keep inner pools serial.",
                      "  Vitest selections: --maxWorkers=8; pytest flags do not apply.",
                      "  Arguments after -- are passed to the runner, including its own --help."))
    return "\n".join(lines) + "\n"


def _describe_runs(runs) -> str:
    if not runs:
        return "no shared default; choose one of the subsections"
    parts = []
    for kind, payload in runs:
        if kind == "pytest":
            parts.append("pytest " + " ".join(payload))
        elif kind == "vitest":
            extra = " ".join(payload)
            parts.append("Vitest in both workspaces" + (f" ({extra})" if extra else ""))
        else:
            parts.append("environment diagnostics, in process")
    return "; ".join(parts)


def _subsection_help(name: str, sub: str, section) -> str:
    runs = section["subsections"][sub]
    options = section.get("subsection_options", {}).get(sub, section["example_options"])
    prefix = f"python tools/mordheim-utils.py tests {name} {sub}"
    lines = [f"usage: {prefix} [options]", "", "Selection:"]
    lines.extend("  " + _describe_runs((run,)) for run in runs)
    python = any(kind == "pytest" for kind, _ in runs)
    if python:
        lines.extend(("", "Options:",
                      "  --list             files without imports or test execution",
                      "  --collect-only     collect actual cases; imports modules, no bodies",
                      "  -k EXPRESSION      filter names, e.g. leadership or not parallel",
                      "  -q / -v            compact output / individual results",
                      "  --tb=short         short failure tracebacks",
                      "  --durations=10     ten slowest test durations",
                      "  -n 8 --dist=load   eight workers for independent tests only"))
        directories = [path for kind, payload in runs if kind == "pytest" for path in payload]
        lines.extend(("", "Files: " + ", ".join(directories), "", "Examples:",
                      f"  {prefix} {options}".rstrip(),
                      f"  {prefix} --list", f"  {prefix} --collect-only -q"))
        if "-n" in options:
            lines.append(f"  {prefix} -k selected_test -n 8 --dist=load -q --tb=short")
        lines.extend(("", "An explicit existing file or file.py::test_name replaces these paths.",
                      "No prerequisites are added. Collection and tests with internal pools stay serial."))
    else:
        lines.extend(("", "Options:", "  --list          files on disk, without running Vitest",
                      "  --maxWorkers=8  eight Vitest workers",
                      "  --project NAME  filter an existing configured project",
                      "", "Examples:", f"  {prefix} --maxWorkers=8", f"  {prefix} --list",
                      "", "Existing .test.ts/.tsx/.mjs paths and filename filters narrow the selection.",
                      "Vitest runs in both configured workspaces. Pytest-specific options do not apply."))
    return "\n".join(lines) + "\n"


def _selection_examples(name: str, section) -> list[str]:
    prefix = f"python tools/mordheim-utils.py tests {name}"
    options = section["example_options"]
    runs = section["runs"]
    kinds = {kind for kind, _ in runs}
    examples = []
    if kinds == {"diagnostics"}:
        return [prefix]
    if kinds == {"pytest"}:
        examples.append(f"{prefix} {options}".rstrip())
    elif kinds == {"vitest"}:
        examples.append(f"{prefix} --maxWorkers=8")
    per_subsection = section.get("subsection_options", {})
    for sub, sub_runs in section["subsections"].items():
        sub_kinds = {kind for kind, _ in sub_runs}
        if sub_kinds == {"pytest"}:
            sub_options = per_subsection.get(sub, options)
            examples.append(f"{prefix} {sub} {sub_options}".rstrip())
        else:
            examples.append(f"{prefix} {sub} --maxWorkers=8")
    if section["dirs"]:
        examples.append(f"{prefix} --list")
    return examples


def _existing_target(argument: str) -> Path | None:
    """Resolve a positional argument that names an existing test path."""
    raw = argument.partition("::")[0]
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    candidate = candidate.resolve()
    if not candidate.exists() or not candidate.is_relative_to(TESTS_ROOT):
        return None
    return candidate


def _partition_arguments(
    args: list[str], allow_unknown_positionals: bool
) -> tuple[list[str], list[str], list[str]]:
    """Split positional test targets from the runner options.

    Python targets are files, directories and node IDs; web targets are the
    Vitest test files.  A positional token that is not an existing test path is
    an option value only when it follows an option; otherwise it is a mistake,
    unless the selection forwards bare Vitest filename filters.
    """
    python_targets: list[str] = []
    web_targets: list[str] = []
    options: list[str] = []
    previous: str | None = None
    for argument in args:
        target = None if argument.startswith("-") else _existing_target(argument)
        if target is None:
            if (argument.startswith("-")
                    or (previous is not None and previous.startswith("-"))
                    or allow_unknown_positionals):
                options.append(argument)
            else:
                raise ValueError(
                    f"unknown test path or option {argument!r}; use --list to see paths"
                )
        elif target.suffix == ".py" or "::" in argument or target.is_dir():
            python_targets.append(argument)
        elif target.name.endswith(TEST_FILE_SUFFIXES):
            web_targets.append(str(target))
        else:
            if allow_unknown_positionals or (previous is not None
                                             and previous.startswith("-")):
                options.append(argument)
            else:
                raise ValueError(f"not a test file: {argument!r}")
        previous = argument
    return python_targets, web_targets, options


def _list_test_files(
    directories, *, python: bool = True, web: bool = True
) -> list[str]:
    """List test files on disk without importing them.

    ``python``/``web`` keep a selection's listing to the languages its runner
    can execute; the global ``tests --list`` asks for both.
    """
    files = set()
    for relative in directories:
        root = REPO_ROOT / relative
        for path in root.rglob("*") if root.is_dir() else [root]:
            if not path.is_file():
                continue
            if python and path.name.startswith("test_") and path.suffix == ".py":
                files.add(path.relative_to(REPO_ROOT).as_posix())
            elif web and path.name.endswith(TEST_FILE_SUFFIXES):
                files.add(path.relative_to(REPO_ROOT).as_posix())
    return sorted(files)


def _run_vitest(extra: tuple[str, ...], targets: list[str], options: list[str]) -> int:
    # Both workspaces own Vitest projects; an explicit file matches in one of
    # them and the other workspace passes when it has no matching file.
    arguments = [*extra, *targets, *options]
    if targets:
        arguments.append("--passWithNoTests")
    for workspace in (TYPESCRIPT_PACKAGE, WEB_APP):
        status = _run_in(workspace, "npm", "test", "--", *arguments)
        if status:
            return status
    return 0


def tests_command(args: list[str]) -> int:
    if not args or args[0] in ("-h", "--help"):
        print(_tests_help())
        return 0
    if args == ["--list"]:
        directories = sorted({directory for section in TESTS_SECTIONS.values()
                              for directory in section["dirs"]})
        print("\n".join(_list_test_files(directories)))
        return 0
    name = args[0]
    if name.startswith("-"):
        print("tests: choose a selection first; run tests --help", file=sys.stderr)
        return 2
    section = TESTS_SECTIONS.get(name)
    if section is None:
        print(f"tests: unknown selection {name!r}; run tests --help", file=sys.stderr)
        return 2
    rest = args[1:]
    if (len(rest) == 2 and rest[0] in section["subsections"]
            and rest[1] in ("-h", "--help")):
        print(_subsection_help(name, rest[0], section))
        return 0
    own_help_args = rest[:rest.index("--")] if "--" in rest else rest
    if any(argument in ("-h", "--help") for argument in own_help_args):
        print(_tests_help(name))
        return 0

    chosen: list[str] = []
    while rest and rest[0] in section["subsections"]:
        chosen.append(rest.pop(0))
    if chosen:
        runs = tuple(run for sub in chosen for run in section["subsections"][sub])
    else:
        runs = section["runs"]
    if not runs:
        if rest:
            print(f"tests {name}: choose a subsection before passing options",
                  file=sys.stderr)
            return 2
        print(_tests_help(name))
        return 0

    listing = "--list" in rest
    if listing:
        rest = [argument for argument in rest if argument != "--list"]
        if rest:
            print("tests: --list accepts a selection only", file=sys.stderr)
            return 2
        directories = [
            path for kind, payload in runs if kind == "pytest" for path in payload
        ] or list(section["dirs"])
        files = _list_test_files(
            directories,
            python=any(kind == "pytest" for kind, _ in runs),
            web=any(kind == "vitest" for kind, _ in runs),
        )
        if not files:
            if any(kind == "diagnostics" for kind, _ in runs):
                print(f"tests {name}: diagnostics run in process; no test files.")
            else:
                print(f"tests {name}: no test files in "
                      + ", ".join(directories))
            return 0
        print("\n".join(files))
        return 0

    if rest[:1] == ["--"]:
        rest = rest[1:]
    pytest_paths = [
        path for kind, payload in runs if kind == "pytest" for path in payload
    ]
    vitest_runs = [payload for kind, payload in runs if kind == "vitest"]
    diagnostics = any(kind == "diagnostics" for kind, _ in runs)
    try:
        python_targets, web_targets, options = _partition_arguments(
            rest, allow_unknown_positionals=not pytest_paths
        )
    except ValueError as error:
        print(f"tests: {error}", file=sys.stderr)
        return 2
    if diagnostics and (web_targets or options):
        print("tests env: diagnostics take no runner options", file=sys.stderr)
        return 2
    if python_targets and not pytest_paths:
        print("tests: this selection runs Vitest; use a Python selection instead",
              file=sys.stderr)
        return 2
    if web_targets and not vitest_runs:
        print("tests: this selection runs pytest; use a web selection instead",
              file=sys.stderr)
        return 2

    if diagnostics:
        return diagnostics_command()

    status = 0
    if pytest_paths:
        # An explicit file, directory or node ID replaces the selection paths.
        targets = python_targets or pytest_paths
        status = _run_module("pytest", *targets, *options)
        if status:
            return status
    for extra in vitest_runs:
        status = _run_vitest(extra, web_targets, options)
        if status:
            return status
    return status


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


def _performance_help() -> str:
    return """usage: python tools/mordheim-utils.py performance <command> [options]

Measure speed and choose machine settings; this does not validate game rules.

Commands:
  benchmark   measure a scenario or workload on selected engines
  calibrate   survey batches/workers and optionally save machine settings

Start here:
  python tools/mordheim-utils.py performance benchmark -h
  python tools/mordheim-utils.py performance calibrate -h

Measurements run real combats. Keep them isolated from other heavy workloads.
Use --processes 8 for an explicit multicore benchmark; do not wrap it in xdist.
"""


def performance_command(args: list[str]) -> int:
    if not args or args[0] in ("-h", "--help"):
        print(_performance_help())
        return 0
    name, forwarded = args[0], args[1:]
    if name not in PERFORMANCE_COMMANDS:
        print(f"performance: unknown command {name!r}; use performance --help", file=sys.stderr)
        return 2
    if "--help-full" in forwarded:
        return _run_module("mordheim_combat_lab", name, "--help")
    if any(argument in ("-h", "--help") for argument in forwarded):
        if name == "benchmark":
            return _delegated_help(
                "python tools/mordheim-utils.py performance benchmark [options]",
                "Measure engine speed. Select a workload, engine and sample size;\nresults describe performance, not rule correctness or engine equivalence.",
                "python -m mordheim_combat_lab benchmark",
                "--scenario ID      scenario to measure (default: all basic scenarios)\n"
                "--backend ENGINE   modular, numpy or native; accepts several engines\n"
                "--simulations N    duels per scenario\n--processes 8      multicore measurement\n"
                "--warmups N        untimed warm-ups\n--repeats N        timed repetitions\n"
                "--deep            size/batch sweep\n--pair-set SET    mini, fast or full for deep/tts\n"
                "--json            structured output\n--output PATH     save results\n"
                "--help-full       all options, scenario names, defaults and units",
                examples=(
                    "performance benchmark --scenario basic --backend numpy --simulations 1000 --processes 8 --repeats 3",
                    "performance benchmark --deep --pair-set mini --backend numpy --processes 8",
                ), notes=("The small example is a smoke measurement, not a stable benchmark.",),
            )
        return _delegated_help(
            "python tools/mordheim-utils.py performance calibrate [options]",
            "Measure batch sizes and worker configurations for this machine.\nBy default the resulting calibration is installed for future application runs.",
            "python -m mordheim_combat_lab calibrate",
            "--pairs SET        mini, fast or full (default: full)\n"
            "--no-install       measure without installing settings\n"
            "--output PATH      save an additional result file\n--json             structured output\n"
            "--reset            remove installed calibration\n"
            "--help-full        sample-size options and exact defaults",
            examples=("performance calibrate --pairs mini --no-install",
                      "performance calibrate --pairs full",
                      "performance calibrate --reset"),
            notes=("Already surveys worker counts; there is no additional --workers flag.",
                   "Even mini can take minutes; run separately from tests and benchmarks."),
        )
    return _run_module("mordheim_combat_lab", name, *forwarded)


# ---------------------------------------------------------------------------
# Checks and reports
# ---------------------------------------------------------------------------


def _check_help() -> str:
    return """usage: python tools/mordheim-utils.py check <command> [options]

Choose a concrete operation; these commands do not form a required sequence.

Data:
  verify        validate KB documents/bindings and try compiling profiles
  report rules  export the rule inventory; no combat correctness certification

Engine scenarios:
  parity        execute catalogued scenarios on modular, or compare candidates

Test quality and outputs:
  coverage      measure code coverage and compare it with the recorded budget
  report tests  generate technical test reports, optionally statistical results

Web and integration workflow:
  presentation  audit web text, translations and visible presentation
  ci            run the configured local checks, typechecks and builds

Examples:
  python tools/mordheim-utils.py check parity --catalog all --backend modular --workers 8 --simulations 1
  python tools/mordheim-utils.py check coverage --json
  python tools/mordheim-utils.py check report rules -h

Use check <command> -h for options, side effects and examples.
These operations can run tests or simulations and write outputs. `tests` selects
pytest/Vitest suites; `check` performs the specific operations described above.
"""


def _check_command_help(name: str) -> int:
    prefix = f"check {name}"
    guides = {
        "verify": (
            "Read KB documents, validate their structure and execution contracts,\n"
            "audit bindings/phases, and try default constructions for band profiles.\n"
            "This is not tests kb and does not execute combat-rule scenarios.",
            "python -m mordheim_combat_lab verify",
            "--knowledge PATH   alternative knowledge root\n--json             structured error/count output\n"
            "--inventory        print inventory instead of running the checks\n"
            "--help-full        complete delegated options",
            ("check verify --json", "check verify --inventory"),
            ("Uses real compilation, not frozen fighters.",),
        ),
        "parity": (
            "Run scenarios from the chosen catalogue. Modular-only execution checks\n"
            "executability; NumPy/native modes compare distributions with modular.",
            "python -m mordheim_combat_lab parity",
            "--catalog NAME     precompiled, battery or all\n"
            "--backend ENGINE   modular (no comparison), numpy, native or all candidates\n"
            "--profile NAME     quick, complete or deep; filters battery only\n"
            "--simulations N    samples per scenario; default: each case's own count\n"
            "--workers 8        workers for modular samples (also accepts auto or 1)\n"
            "--seed N           sample seed\n--require-complete fail if any selected case is blocked\n"
            "--json             structured results\n--output PATH      save a JSON catalogue-run report\n"
            "--help-full        complete options, including historical presets",
            ("check parity --catalog precompiled --backend modular --workers 8 --simulations 1",
             "check parity --catalog battery --backend modular --workers 8 --simulations 1",
             "check parity --catalog all --backend modular --workers 8 --simulations 1",
             "check parity --catalog battery --profile quick --backend numpy --workers 8 --require-complete"),
            ("No profile means all cases of the selected catalogue(s).",
             "Precompiled cases load frozen fighters; battery cases compile their builds.",
             "COMPLETED means executable, not parity approved; blocked cases were not run.",
             "One simulation checks one execution path; eight workers cannot split one duel.",
             "Use --level small|normal|long with precompiled scenarios; historical --pair-set presets remain separate."),
        ),
        "coverage": (
            "Run the configured Python suites under coverage measurement, then check\n"
            "whether previously covered lines and configured area floors remain covered.",
            "python -m mordheim_combat_lab coverage-gate",
            "--suites PATH ...  select suites to measure\n--budget PATH      reference budget file\n"
            "--area-floor A:P   minimum percent for an area (repeatable)\n"
            "--update-budget    replace the recorded budget with this measurement\n"
            "--json             structured output\n--help-full        complete defaults and options",
            ("check coverage --json", "check coverage --update-budget"),
            ("Executes tests. --update-budget writes the baseline; it is not a normal check.",
             "No general worker flag is exposed; do not append --workers or -n."),
        ),
        "presentation": (
            "Check the web's text/translation detector, source presentation flow,\n"
            "resolved-text types and rendered visible text. Requires npm dependencies.",
            "npm run check:presentation in apps/warband-manager-web",
            "-h, --help  this guide; no other options",
            ("check presentation",),
            ("Runs checks and writes audit outputs under outputs/web-presentation/.",),
        ),
        "ci": (
            "Generate/check web KB assets; run the local Python regression selection,\n"
            "eligibility checks, TypeScript/web typechecks, tests, lint and web build.",
            "the configured run_ci_command pipeline",
            "-h, --help  this guide; no other options",
            ("check ci",),
            ("May take substantial time and creates generated/build outputs.",
             "Does not execute the E2E battery or a full engine-parity campaign.",
             "Run those deliberately using tests kb e2e or check parity."),
        ),
    }
    detail, runs, options, examples, notes = guides[name]
    return _delegated_help(
        f"python tools/mordheim-utils.py {prefix} [options]",
        detail, runs, options, examples=examples, notes=notes,
    )


def report_command(args: list[str]) -> int:
    if not args or args[0] in ("-h", "--help"):
        print("usage: python tools/mordheim-utils.py check report <rules|tests> [options]")
        print()
        print("  rules   auditable per-rule inventory (CSV/JSON in outputs/audit/)")
        print("  tests   human-readable parity and technical test CSVs")
        print()
        print("Runs: python -m mordheim_combat_lab audit (rules)")
        print("      python -m mordheim_combat_lab test-report (tests)")
        print()
        print("Options after the kind are forwarded to the report command;")
        print("run `check report <kind> --help` for its own options.")
        return 0
    kind, forwarded = args[0], args[1:]
    if kind not in REPORT_KINDS:
        print(
            f"check report: unknown kind {kind!r}; choose from "
            + ", ".join(sorted(REPORT_KINDS)),
            file=sys.stderr,
        )
        return 2
    if "--help-full" in forwarded:
        return _run_module("mordheim_combat_lab", REPORT_KINDS[kind], "--help")
    if any(arg in ("-h", "--help") for arg in forwarded):
        if kind == "rules":
            return _delegated_help(
                "python tools/mordheim-utils.py check report rules [options]",
                "Export the maintained rule inventory with classifications and scope.\nThis is a data report, not evidence that game rules execute correctly.",
                "python -m mordheim_combat_lab audit",
                "--output PATH   destination directory\n--scope VALUE   YES, NO, LATER or UNCLASSIFIED\n"
                "--family NAME   mechanism-family filter\n--help-full     all inventory filters",
                examples=("check report rules --output outputs/audit",),
                notes=("Writes report files; does not certify E2E or parity coverage.",),
            )
        return _delegated_help(
            "python tools/mordheim-utils.py check report tests [options]",
            "Execute the technical test-report workflow and export its results.\nOptionally add statistical engine comparisons; this can be expensive.",
            "python -m mordheim_combat_lab test-report",
            "--output PATH              report directory\n--statistical              also run statistical comparisons\n"
            "--statistical-simulations N samples per scenario\n--workers 8                modular workers for statistical samples only\n"
            "--seed N                   statistical seed\n--help-full                complete options",
            examples=("check report tests --output outputs/test-report",
                      "check report tests --statistical --workers 8 --output outputs/test-report"),
            notes=("Unlike report rules, this command executes checks, not just inventory export.",),
        )
    return _run_module("mordheim_combat_lab", REPORT_KINDS[kind], *forwarded)


def check_command(args: list[str]) -> int:
    if not args or args[0] in ("-h", "--help"):
        print(_check_help())
        return 0
    name, forwarded = args[0], args[1:]
    if name == "report":
        return report_command(forwarded)
    if name in ("verify", "parity", "coverage", "presentation", "ci"):
        if "--help-full" in forwarded and name in ("verify", "parity", "coverage"):
            lab_name = {"verify": "verify", "parity": "parity", "coverage": "coverage-gate"}[name]
            return _run_module("mordheim_combat_lab", lab_name, "--help")
        if any(argument in ("-h", "--help") for argument in forwarded):
            return _check_command_help(name)
        if name == "presentation":
            if forwarded:
                print("check presentation: no arguments expected", file=sys.stderr)
                return 2
            return _run_in(WEB_APP, "npm", "run", "check:presentation")
        if name == "ci":
            return run_ci_command(forwarded)
        lab_name = {"verify": "verify", "parity": "parity",
                    "coverage": "coverage-gate"}[name]
        return _run_module("mordheim_combat_lab", lab_name, *forwarded)
    print(f"check: unknown command {name!r}; use check --help", file=sys.stderr)
    return 2


# ---------------------------------------------------------------------------
# Local CI and diagnostics
# ---------------------------------------------------------------------------


def run_ci_command(args: list[str]) -> int:
    """Run the checks from .github/workflows/ci.yml using local dependencies."""
    if args:
        print("check ci: this command does not accept arguments", file=sys.stderr)
        return 2
    for command in ((sys.executable, str(KNOWLEDGE_GENERATOR)),
                    (sys.executable, str(KNOWLEDGE_GENERATOR), "--check")):
        if _run_in(REPO_ROOT, *command):
            return 1
    if _run_module("pytest",
                   "tests/applications/warband_manager/persistence/campaign_file",
                   "tests/tooling/architecture", "tests/knowledge",
                   "tests/construction/test_shared_eligibility.py", "-q"):
        return 1
    if _run(sys.executable, str(KNOWLEDGE_GENERATOR), "--check"):
        return 1
    if _run_in(REPO_ROOT, "npm", "run", "check:eligibility"):
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
        "../../tests/applications/warband_manager/features/campaign/knowledge-display-coverage.test.tsx",
        "../../tests/applications/warband_manager/features/campaign/ui_i18n.test.ts",
        "../../tests/applications/warband_manager/features/campaign/displayText.test.ts",
        "../../tests/applications/warband_manager/features/campaign/KnowledgeHint.test.tsx",
    ):
        return 1
    for command in (("npm", "run", "typecheck"), ("npm", "run", "lint"),
                    ("npm", "test"), ("npm", "run", "build"),
                    ("npx", "vitest", "run",
                     "../../tests/tooling/architecture/web-boundaries.test.ts",
                     "../../tests/applications/warband_manager/packaging/bundle-boundaries.test.ts")):
        if _run_in(WEB_APP, *command):
            return 1
    return 0


def diagnostics_command() -> int:
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
    for label, module in (("Combat Lab", "mordheim_combat_lab.ui.app"),):
        if importlib.util.find_spec(module) is None:
            print(f"{label}: import failed (module not found)")
        else:
            print(f"{label}: importable")
    return 0


# ---------------------------------------------------------------------------
# Main help and dispatch
# ---------------------------------------------------------------------------


def _main_help() -> str:
    return """usage: python tools/mordheim-utils.py <group> <command> [options]

App launchers:
  app combat-lab              open the desktop application
  app warband-manager         start the web development server

Tests:
  tests env                   show environment/dependency diagnostics
  tests combat-lab            desktop application tests
  tests warband-manager       choose Python or web tests
  tests modular               rule mechanics and reference-engine runtime
  tests vectorized            NumPy mechanics and runtime
  tests native                native-engine tests (extension required)
  tests kb                    KB contracts; construction/E2E are subsections
  tests parity                statistical comparison tests and runner checks
  tests shared                common engine contracts and frozen inputs
  tests tooling               launcher, architecture and coverage-tool checks

Performance:
  performance benchmark       measure engine speed on selected scenarios
  performance calibrate       measure and optionally save machine settings

Checks and reports:
  check parity                run catalogued scenarios or compare engine samples
  check verify                validate KB structure/bindings and compile profiles
  check coverage              measure tests' code coverage against a budget
  check report rules          export the rule inventory
  check report tests          execute checks and export test reports
  check presentation          audit web text, translations and presentation
  check ci                    local regression checks, typechecks and web build

Start here:
  python tools/mordheim-utils.py tests modular mechanics -h
  python tools/mordheim-utils.py tests modular mechanics -n 8 --dist=load -q
  python tools/mordheim-utils.py check parity --catalog all --backend modular --workers 8 --simulations 1

Help and discovery:
  <group> -h                  commands within a group
  <group> <command> -h        purpose, default selection, options and examples
  tests <section> <sub> -h    details of one test subsection
  tests <section> --list      list test files without importing them
  <delegated command> --help-full
                              complete underlying options for performance/check/report
  --version                   launcher version

No arguments display help. Examples are choices, not a required sequence.
`tests parity` checks tests; `check parity` executes catalogued engine scenarios.
Eight workers are examples, not forced defaults. Keep inner-pool tests serial.
Guide: docs/reference/tools.md
"""


GROUPS = {
    "app": app_command,
    "tests": tests_command,
    "performance": performance_command,
    "check": check_command,
}


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw or raw[0] in ("-h", "--help"):
        _print_styled(_main_help())
        return 0
    if raw[0] == "--version":
        try:
            version = importlib.metadata.version("mordheim-utils")
        except importlib.metadata.PackageNotFoundError:
            version = "not installed (source checkout)"
        print(f"mordheim-utils {version}")
        return 0
    name, args = raw[0], raw[1:]
    handler = GROUPS.get(name)
    if handler is None:
        print(f"mordheim-utils: unknown group {name!r}", file=sys.stderr)
        print("Run `python tools/mordheim-utils.py --help` for the groups.",
              file=sys.stderr)
        return 2
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
