#!/usr/bin/env python3
"""Central command line for the Mordheim Utils repository.

A plain developer-facing launcher: pick a command and it runs the matching
Python module or script with the same interpreter. Nothing here is installed
as a package command and there is no parser to duplicate::

    python tools/mordheim-utils.py --help
    python tools/mordheim-utils.py benchmark --help

Delegated commands keep their own parsers (Combat Lab CLI and pytest), so
their help text and behaviour never drift.
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
    REPO_ROOT / "apps" / "combat-lab",
)

# Make the in-process commands (doctor) work from a fresh checkout too.
for package_root in reversed(PACKAGE_ROOTS):
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


#: Map of ``tests --scope`` names to the pytest paths they select.
SCOPE_PATHS = {
    "all": ("tests",),
    "engines": ("tests/engines",),
    "modular": ("tests/engines/modular",),
    "vectorized": ("tests/engines/vectorized",),
    "native": ("tests/engines/native",),
    "e2e": ("tests/rules/integration/e2e",),
    # The per-change engine gate: the deterministic suites that certify rule
    # behaviour without statistical noise (mirrors the coverage-gate budget).
    "deterministic": ("tests/engines/modular", "tests/engines/vectorized",
                      "tests/engines/shared/test_phases.py", "tests/engines/shared/test_duel_context.py",
                      "tests/engines/shared/test_exact_phases.py", "tests/engines/shared/test_interactions.py",
                      "tests/engines/parity/test_duel_replay.py",
                      "tests/engines/parity/test_parity.py"),
    "knowledge": ("tests/rules/knowledge", "tests/rules/integration/specs"),
    "verification": ("tests/engines/parity/test_duel_replay.py",
                      "tests/engines/parity/test_parity.py",
                      "tests/engines/parity/test_parity_battery_cases.py",
                      "tests/engines/parity/test_parity_battery_runner.py",
                      "tests/engines/parity/test_truncation_parity.py",
                      "tests/tooling/verification",
                      "tests/rules/integration/test_semantics.py",
                      "tests/rules/integration/test_structural.py"),
    "construction": ("tests/rules/construction",),
    "ui": ("tests/applications/combat_lab/ui",),
    "cli": ("tests/tooling/launcher", "tests/applications/combat_lab/cli",
            "tests/engines/parity/benchmarks"),
    "architecture": ("tests/tooling/architecture",),
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
    "campaign-manager": "python tools/mordheim-utils.py campaign-manager [vite args ...]",
    "doctor": "python tools/mordheim-utils.py doctor",
    "check-presentation": "python tools/mordheim-utils.py check-presentation",
}

#: Command help lines, in the order shown by ``--help``.
COMMANDS = (
    ("combat-lab", "open the Combat Lab graphical application"),
    ("campaign-manager", "start the web Campaign Manager development server"),
    ("verify", "validate the KB and run the semantic specifications"),
    ("report", "generate the rule and test reports (report rules | report tests)"),
    ("benchmark", "measure the combat engines (modular, NumPy, native) with configurable sizes"),
    ("parity", "certify the vectorized and native engines against the modular oracle"),
    ("coverage-gate", "measure deterministic engine coverage and check the drift budget"),
    ("calibrate", "measure this machine's engine optima and install the calibration profile"),
    ("tests", "run the pytest suites, filtered by --scope"),
    ("test-sequence", "run Python tests in the project's functional dependency phases (pytest options)"),
    ("check-presentation", "test the GUI text detector and run the strict, deep and dynamic completeness audits"),
    ("run-ci", "run the local equivalent of the CI validation gates before Pages publishing"),
    ("doctor", "report the environment, installed engines and KB location"),
)

#: Command groups for ``--help``; every name in COMMANDS appears exactly once.
COMMAND_GROUPS = (
    ("Applications", ("combat-lab", "campaign-manager")),
    ("Knowledge base", ("verify", "report")),
    ("Engines", ("benchmark", "parity", "coverage-gate", "calibrate")),
    ("Repository", ("tests", "test-sequence", "check-presentation", "run-ci", "doctor")),
)

KNOWLEDGE_GENERATOR = REPO_ROOT / "tools" / "knowledge" / "generate_knowledge_web.py"
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


def check_presentation_command(args: list[str]) -> int:
    if any(argument in ("-h", "--help") for argument in args):
        return _print_usage(
            "check-presentation",
            "Run the web detector tests, the strict deep GUI text audit and the "
            "dynamic visible-completeness audit (rendered surfaces, ES/EN, old "
            "formats). Requires npm and installed web dependencies. Findings of "
            "either layer return a nonzero exit code; reports: "
            "outputs/web-presentation/gui-text-audit-deep.{json,md} and "
            "outputs/web-presentation/gui-text-completeness.{json,md}.")
    if args:
        print("check-presentation: no arguments expected", file=sys.stderr)
        return 2
    return _run_in(WEB_APP, "npm", "run", "check:presentation")


def combat_lab_command(args: list[str]) -> int:
    if any(argument in ("-h", "--help") for argument in args):
        return _print_usage(
            "combat-lab", "Open the Combat Lab graphical application (Tkinter).")
    return _run_module("mordheim_combat_lab", "ui")


def campaign_manager_command(args: list[str]) -> int:
    if any(argument in ("-h", "--help") for argument in args):
        return _print_usage(
            "campaign-manager",
            "Start the web Campaign Manager development server. Extra arguments "
            "are forwarded to Vite (for example, `--port 5199 --strictPort`).")
    return _run_in(WEB_APP, "npm", "run", "dev", "--", *args)


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


def tests_command(args: list[str], *, ordered: bool = False) -> int:
    own_args = args[:args.index("--")] if "--" in args else args
    if ordered and any(arg in ("-h", "--help") for arg in own_args):
        print("usage: python tools/mordheim-utils.py test-sequence [options] [pytest args ...]")
        print("""
Run Python tests in the project's functional dependency phases, with one
pytest collection and session. Phases 0..7 follow the project's dependencies:
  0 preflight (architecture, test infrastructure)  1 KB and contracts
  2 warrior construction                           3 modular rules/operators
  4 modular engine/oracle                          5 vectorized engine + parity
  6 native engine + parity                          7 Warband Manager/application
Evidence, packaging and performance are additional categories outside that
sequence and run only when requested. The default continues after failures,
returning an unsuccessful exit status if any test fails. Use -x to stop at the
first failure.

Options:
  --steps                 List the phases and additional categories (no collection).
  --step N / -stepN       Execute only functional phase N (0..7).
  --sequence-category NAME
                          Execute only one additional category: evidence,
                          packaging or performance.
  --extras                Run evidence, packaging and performance after the
                          selected functional phases.
  --workers N             Use N processes within each category (default: 1).
                          Complete a category before starting the next one.
  --output FILE           Save combined console output as UTF-8 text (overwrite).
                          Output remains visible on screen, including failures.
  --scope NAME            Select an existing Python component (default: all).
  --sequence-plan         Collect and display the ordered selection; run no tests.
  --sequence-from PHASE   Start at a functional phase id (phase0_preflight ..
                          phase7_warband); earlier phases are omitted, not
                          validated from a previous run.
  --sequence-keep-going   Explicit alias for the default continuation behaviour.
                          Cannot combine with -x/--maxfail.
  -x / --maxfail N        Stop after one failure, or after N failures.
  -m EXPRESSION           Select phase categories using pytest markers.
  -k EXPRESSION           Further filter test names using pytest.
  -q / -qq               Reduce output; -qq is useful for large collection plans.
  -h, --help             Show this help without collecting or executing tests.
  -- --help              Show the complete pytest and sequence-plugin help.
""")
        print("Scopes: " + ", ".join(SCOPE_PATHS))
        print("""
Examples:
  python tools/mordheim-utils.py test-sequence --steps
  python tools/mordheim-utils.py test-sequence -step0 -q
  python tools/mordheim-utils.py test-sequence -step2 --workers 4 -q
  python tools/mordheim-utils.py test-sequence --workers 4 -q
  python tools/mordheim-utils.py test-sequence --workers 4 -q --output reports/tests.txt
  python tools/mordheim-utils.py test-sequence --step 2 --scope construction -q
  python tools/mordheim-utils.py test-sequence --sequence-plan -qq
  python tools/mordheim-utils.py test-sequence --scope construction -q
  python tools/mordheim-utils.py test-sequence -m "phase1_kb_contracts or phase2_construction" -q
  python tools/mordheim-utils.py test-sequence --sequence-from phase3_rules -q
  python tools/mordheim-utils.py test-sequence --extras -q
  python tools/mordheim-utils.py test-sequence --sequence-category performance -q
  python tools/mordheim-utils.py test-sequence --sequence-keep-going -q

Limits:
  Python only: Vitest and node:test are not included; the TypeScript/web
  categories are selected with the annotated Vitest projects (see the reference).
  Scopes and filters do not automatically add prerequisites. Generated inputs and
  builds must be prepared separately. Ordering uses the per-item phase marker,
  not an inferred dependency graph: a parametrized item carries the category of
  the backend it executes. Parallel mode uses xdist/loadfile: no ordering between
  files within a category. Each category/worker repeats collection. --workers 1
  retains a single sequential pytest session. Parallel mode does not support
  --sequence-from; use --step or --sequence-category. Plans stay sequential.
  Plan mode imports modules and loads test data. Skips do not prove correctness;
  successful selected tests do not imply full certification. No success is cached.
  Category filtering happens after module import. Use --scope to avoid collecting
  unrelated components; --steps is the fast static list.

Reference: docs/reference/test-sequence.md
""")
        return 0
    if ordered:
        for index, arg in enumerate(own_args):
            if arg == "--output" or arg.startswith("--output="):
                value = arg.split("=", 1)[1] if "=" in arg else (
                    args[index + 1] if index + 1 < len(own_args) else "")
                if not value or ("=" not in arg and value.startswith("-")):
                    print("test-sequence: --output requires a file path", file=sys.stderr)
                    return 2
                remaining = args[:index] + args[index + (1 if "=" in arg else 2):]
                destination = Path(value).resolve()
                try:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with destination.open("w", encoding="utf-8") as report:
                        env = _environment()
                        env["PYTHONIOENCODING"] = "utf-8"
                        with subprocess.Popen(
                            [sys.executable, "-u", str(Path(__file__).resolve()),
                             "test-sequence", *remaining],
                            cwd=REPO_ROOT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                            errors="replace",
                        ) as process:
                            for line in process.stdout:
                                print(line, end="", flush=True)
                                report.write(line)
                                report.flush()
                            return process.wait()
                except OSError as exc:
                    print(f"test-sequence: cannot save report to {destination}: {exc}",
                          file=sys.stderr)
                    return 2
    if ordered and "--steps" in args:
        if args != ["--steps"]:
            print("test-sequence: --steps is a static list; use it without other options", file=sys.stderr)
            return 2
        return _run_module("tools.verification.test_sequence", "--steps")
    if ordered:
        args = ["--step=" + arg[5:] if arg.startswith("-step") and arg[5:].isdigit()
                else arg for arg in args]
    scope = "all"
    workers = 1
    forwarded: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if ordered and (arg == "--workers" or arg.startswith("--workers=")):
            value = arg.split("=", 1)[1] if "=" in arg else (args[index + 1] if index + 1 < len(args) else "")
            try:
                workers = int(value)
                if workers < 1:
                    raise ValueError
            except ValueError:
                print("test-sequence: --workers requires a positive integer", file=sys.stderr)
                return 2
            index += 1 if "=" in arg else 2
            continue
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
    if ordered and workers > 1:
        return _run_module("tools.verification.test_sequence", "--workers", str(workers),
                           "--", *SCOPE_PATHS[scope], *forwarded)
    plugins = ("-p", "tools.verification.test_sequence") if ordered else ()
    return _run_module("pytest", *plugins, *SCOPE_PATHS[scope], *forwarded)


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
    if _run_module("pytest", "tests/rules/knowledge/web",
                   "tests/applications/warband_manager/persistence/campaign_file",
                   "tests/tooling/architecture", "tests/rules/knowledge",
                   "tests/rules/construction/test_shared_eligibility.py", "-q"):
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
    for label, module in (("Combat Lab", "mordheim_combat_lab.ui.app"),):
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
        "    test-sequence --help                ordered Python tests: options and examples",
        "    test-sequence --steps               list numbered phases without collecting",
        "    test-sequence --sequence-plan -qq    preview the order without running tests",
        "    tests --scope deterministic         the per-change engine gate",
        "    verify                              knowledge base before touching rules",
        "    report rules                        per-rule implementation inventory",
        "    run-ci                              everything, before publishing",
        "",
        "The engine commands (benchmark, parity, coverage-gate, calibrate) and the "
        "knowledge base gate (verify) run as `python -m mordheim_combat_lab <command>`; "
        "`report rules|tests` forwards to the `audit` and `test-report` lab commands.",
    ))
    return "\n".join(lines) + "\n"


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
    if name == "campaign-manager":
        return campaign_manager_command(args)
    if name == "report":
        return report_command(args)
    if name == "tests":
        return tests_command(args)
    if name == "test-sequence":
        return tests_command(args, ordered=True)
    if name == "check-presentation":
        return check_presentation_command(args)
    if name == "run-ci":
        return run_ci_command(args)
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
