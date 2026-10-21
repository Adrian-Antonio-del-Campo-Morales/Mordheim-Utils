"""Ordered Python tests, loaded only by ``mordheim-utils.py test-sequence``.

The functional phases follow the project's dependency order, not duration or
framework: preflight, KB contracts, construction, modular rules, modular
engine/oracle, vectorized engine, native engine, application. Performance,
packaging and evidence are additional categories outside that sequence and run
only when requested (``--extras`` or ``--sequence-category``).

Sequential mode uses one pytest collection/session; optional workers run each
selected category in its own pytest/xdist session with a barrier between
categories. The explicit per-item marker is the only ordering key: a test that
executes a backend is marked with that backend's phase, including the matching
item of a backend parametrization.

Usage (from the repository root)::

    python tools/mordheim-utils.py test-sequence --steps
    python tools/mordheim-utils.py test-sequence --sequence-plan -q
    python tools/mordheim-utils.py test-sequence --scope construction -q
    python tools/mordheim-utils.py test-sequence --step 2 --workers 4 -q
    python tools/mordheim-utils.py test-sequence --sequence-from phase3_rules
    python tools/mordheim-utils.py test-sequence --extras -q
    python tools/mordheim-utils.py test-sequence --sequence-category performance

Selected paths/markers do not automatically include prerequisites. Preparation
of generated data/builds remains explicit. JavaScript runners are not included.
"""
from __future__ import annotations

from collections import Counter
import argparse
import importlib.util
import subprocess
import sys

import pytest


#: Functional phases, in dependency order. This tuple owns execution order only;
#: the marker definitions and the per-item annotations live with the tests.
PHASES = (
    ("phase0_preflight", "Preflight: architecture and test infrastructure"),
    ("phase1_kb_contracts", "KB and contracts"),
    ("phase2_construction", "Warrior construction"),
    ("phase3_rules", "Modular rules and operators"),
    ("phase4_modular", "Modular engine and oracle"),
    ("phase5_vectorized", "Vectorized engine and oracle parity"),
    ("phase6_native", "Native engine and oracle parity"),
    ("phase7_warband", "Warband Manager and application tier"),
)

#: Categories outside the functional sequence. They are never run by default;
#: ``--extras`` appends all of them and ``--sequence-category`` selects one.
EXTRA_CATEGORIES = ("evidence", "packaging", "performance")

CATEGORY_ORDER = tuple(name for name, _ in PHASES) + EXTRA_CATEGORIES
LABELS = dict(PHASES)
LABELS.update({
    "evidence": "Evidence generation and verification",
    "packaging": "Packaging and published artefacts",
    "performance": "Performance and delivery budgets",
})

PHASE_NAMES = tuple(name for name, _ in PHASES)


def _phase_index(name):
    try:
        return PHASE_NAMES.index(name)
    except ValueError as error:
        raise pytest.UsageError(f"unknown functional phase {name!r}") from error


def pytest_addoption(parser):
    group = parser.getgroup("test sequence", "Ordered Python test execution")
    group.addoption("--sequence-plan", action="store_true",
                    help="Collect and show the ordered selection without executing tests.")
    group.addoption("--sequence-keep-going", action="store_true",
                    help="Explicit alias for the default: continue after failures (incompatible with -x/--maxfail).")
    group.addoption("--sequence-from", metavar="PHASE",
                    help="Start at a functional phase id (phase0_preflight..phase7_warband); "
                         "does not validate earlier phases.")
    group.addoption("--step", type=int, choices=range(len(PHASES)), metavar="N",
                    help="Execute only functional phase N (0..7); use test-sequence --steps for the list.")
    group.addoption("--extras", action="store_true",
                    help="Run evidence, packaging and performance after the selected functional phases.")
    group.addoption("--sequence-category", metavar="NAME",
                    choices=EXTRA_CATEGORIES,
                    help="Run only one additional category (evidence, packaging or performance).")


def _category(item):
    categories = {mark.name for mark in item.iter_markers()} & set(CATEGORY_ORDER)
    if len(categories) != 1:
        raise pytest.UsageError(
            f"test-sequence requires exactly one phase category: {item.nodeid} "
            f"(found {sorted(categories)})")
    return categories.pop()


def pytest_configure(config):
    step = config.getoption("step")
    start = config.getoption("sequence_from")
    extras = config.getoption("extras")
    category = config.getoption("sequence_category")
    if step is not None and start:
        raise pytest.UsageError("--step selects one phase; do not combine it with --sequence-from.")
    if start and start not in PHASE_NAMES:
        raise pytest.UsageError(
            "--sequence-from accepts a functional phase id: " + ", ".join(PHASE_NAMES))
    if category is not None and (step is not None or start or extras):
        raise pytest.UsageError(
            "--sequence-category selects one additional category; do not combine it "
            "with --step, --sequence-from or --extras.")
    worker = hasattr(config, "workerinput")
    distributed = (worker or bool(getattr(config.option, "numprocesses", None))
                   or getattr(config.option, "dist", "no") != "no")
    if distributed and ((step is None and not extras and category is None)
                        or config.getoption("sequence_plan")
                        or (not worker and getattr(config.option, "dist", "no") != "loadfile")):
        raise pytest.UsageError("Parallel execution requires one --step, --extras or "
                                "--sequence-category and --dist=loadfile; "
                                "use test-sequence --workers N to coordinate phases.")
    if config.getoption("sequence_keep_going"):
        if config.option.maxfail:
            raise pytest.UsageError("--sequence-keep-going cannot be combined with -x/--maxfail.")
    if config.getoption("sequence_plan"):
        config.option.collectonly = True
    config.pluginmanager.register(Sequence(config), "ordered-test-sequence")


class Sequence:
    def __init__(self, config):
        self.config = config
        self.stages = {}
        self.outcomes = {}
        self.current = None

    def _allowed(self):
        """Category ids this session executes, in order."""
        step = self.config.getoption("step")
        start = self.config.getoption("sequence_from")
        extras = self.config.getoption("extras")
        category = self.config.getoption("sequence_category")
        if category is not None:
            return {category}
        if step is not None:
            allowed = {PHASE_NAMES[step]}
        elif start:
            allowed = set(PHASE_NAMES[_phase_index(start):])
        else:
            allowed = set(PHASE_NAMES)
        if extras:
            allowed |= set(EXTRA_CATEGORIES)
        return allowed

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_node_collection_finished(self, node, ids):
        # The controller has no pytest Items. xdist already verifies identical
        # worker collections; summarize this single category, without another
        # per-test metadata protocol or double-counting the workers' copies.
        step = self.config.getoption("step")
        category = self.config.getoption("sequence_category")
        if category is not None:
            selected = category
        elif step is not None:
            selected = PHASE_NAMES[step]
        else:
            selected = None
        # Always an actual category id: the terminal summary reads it, so a
        # display label here would raise KeyError instead of printing a count.
        self.stages = dict.fromkeys(ids, selected) if selected else {}

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, config, items):
        allowed = self._allowed()
        ranked = [(_category(item), item) for item in items]
        ranked.sort(key=lambda entry: CATEGORY_ORDER.index(entry[0]))
        excluded = [item for category, item in ranked if category not in allowed]
        ranked = [entry for entry in ranked if entry[0] in allowed]
        if excluded:
            config.hook.pytest_deselected(items=excluded)
        items[:] = [item for _, item in ranked]
        self.stages = {item.nodeid: category for category, item in ranked}

    def pytest_report_collectionfinish(self):
        if getattr(self.config.option, "numprocesses", None):
            return []  # Workers perform collection; the controller has no Items.
        counts = Counter(self.stages.values())
        lines = ["Python test sequence (one collection; selected paths only):"]
        lines.extend(f"  {category}: {count} ({LABELS[category]})"
                     for category, count in counts.items())
        lines.append("No prerequisite expansion, build preparation or certification is implied.")
        step = self.config.getoption("step")
        category = self.config.getoption("sequence_category")
        if step is not None:
            lines.append(f"Only phase {step} ({PHASE_NAMES[step]}); other phases are not validated.")
        if category is not None:
            lines.append(f"Only the additional category {category}; the functional sequence is not validated.")
        if self.config.getoption("sequence_from"):
            lines.append("Earlier phases omitted explicitly; no saved result was validated.")
        if self.config.getoption("extras"):
            lines.append("Additional categories requested with --extras; they are outside the functional sequence.")
        return lines

    def pytest_runtest_logstart(self, nodeid):
        stage = self.stages.get(nodeid)
        if stage is None:
            return
        if stage != self.current:
            terminal = self.config.pluginmanager.get_plugin("terminalreporter")
            if terminal:
                terminal.write_sep("-", f"sequence: {stage}")
            self.current = stage

    def pytest_runtest_logreport(self, report):
        if report.failed:
            self.outcomes[report.nodeid] = "failed"
        elif self.outcomes.get(report.nodeid) != "failed":
            if report.skipped:
                self.outcomes[report.nodeid] = "skipped"
            elif report.when == "call":
                self.outcomes[report.nodeid] = "passed"

    def pytest_terminal_summary(self, terminalreporter):
        if self.config.option.collectonly:
            return
        terminalreporter.write_sep("=", "Sequence results (skips are not verification)")
        for stage in dict.fromkeys(self.stages.values()):
            results = Counter(self.outcomes.get(nodeid, "not-run")
                              for nodeid, selected in self.stages.items() if selected == stage)
            terminalreporter.write_line(
                f"{stage}: "
                + ", ".join(f"{count} {outcome}" for outcome, count in results.items()))


def _phase_sessions(selected):
    """One blocking pytest session per selected category, in execution order."""
    if selected.sequence_category is not None:
        return [(selected.sequence_category,
                 ["--sequence-category", selected.sequence_category])]
    numbers = [selected.step] if selected.step is not None else range(len(PHASES))
    sessions = [(PHASE_NAMES[number], ["--step", str(number)]) for number in numbers]
    if selected.extras:
        sessions += [(name, ["--sequence-category", name]) for name in EXTRA_CATEGORIES]
    return sessions


def run_parallel(workers, args):
    """Barrier between categories via blocking pytest calls; xdist schedules."""
    parser = argparse.ArgumentParser(prog="test-sequence", add_help=False)
    parser.add_argument("--step", type=int, choices=range(len(PHASES)))
    parser.add_argument("--sequence-from")
    parser.add_argument("--extras", action="store_true")
    parser.add_argument("--sequence-category", choices=EXTRA_CATEGORIES)
    parser.add_argument("-x", "--exitfirst", dest="maxfail", action="store_const", const=1)
    parser.add_argument("--maxfail", type=int, default=0)
    selected, forwarded = parser.parse_known_args(args)
    if workers < 1:
        print("test-sequence: --workers must be a positive integer", file=sys.stderr)
        return 2
    if selected.sequence_from:
        print("test-sequence: use --step, --extras or --sequence-category with --workers; "
              "--sequence-from is sequential only", file=sys.stderr)
        return 2
    if selected.sequence_category is not None and (selected.step is not None or selected.extras):
        print("test-sequence: --sequence-category runs alone; do not combine it with "
              "--step or --extras", file=sys.stderr)
        return 2
    if any(arg in ("-n", "--numprocesses", "--dist")
           or arg.startswith(("-n", "--numprocesses=", "--dist=")) for arg in forwarded):
        print("test-sequence: --workers manages -n and --dist; do not combine them", file=sys.stderr)
        return 2
    base = [sys.executable, "-m", "pytest", "-p", "tools.verification.test_sequence"]
    if selected.maxfail:
        forwarded.append(f"--maxfail={selected.maxfail}")
    # A plan is a single serial collection, even when workers were requested.
    if any(arg in ("--sequence-plan", "--collect-only", "--co") for arg in forwarded):
        phase = []
        if selected.step is not None:
            phase = ["--step", str(selected.step)]
        elif selected.sequence_category is not None:
            phase = ["--sequence-category", selected.sequence_category]
        elif selected.extras:
            phase = ["--extras"]
        return subprocess.call([*base, *forwarded, *phase])
    if importlib.util.find_spec("xdist") is None:
        print('test-sequence: install development dependencies: python -m pip install -e ".[dev]"',
              file=sys.stderr)
        return 2
    phases = _phase_sessions(selected)
    results = []
    exit_code = 0
    for name, phase in phases:
        print(f"\n=== {LABELS[name]} ({workers} workers, loadfile) ===", flush=True)
        try:
            code = subprocess.call([*base, "-p", "xdist", "-n", str(workers),
                                    "--dist=loadfile", *forwarded, *phase])
        except KeyboardInterrupt:
            code = 130
        results.append((name, code))
        if code not in (0, 5):
            exit_code = code
            if code != 1 or selected.maxfail:
                break
    print("\nPhase results (process completion is the barrier):", flush=True)
    for name, code in results:
        status = {0: "passed", 1: "failed", 5: "empty selection (not validated)"}.get(
            code, f"aborted ({code})")
        print(f"  {name}: {status}", flush=True)
    return exit_code or (0 if any(code == 0 for _, code in results) else 5)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args != ["--steps"]:
        parser = argparse.ArgumentParser(prog="test-sequence")
        parser.add_argument("--workers", type=int, required=True)
        options, forwarded = parser.parse_known_args(args)
        if forwarded[:1] == ["--"]:
            forwarded = forwarded[1:]
        return run_parallel(options.workers, forwarded)

    print("Python test phases (static list; no collection or test execution):")
    print("Functional phases, executed in this order:")
    for number, (name, label) in enumerate(PHASES):
        print(f"  {number:2}. {name}: {label}")
    print("\nAdditional categories, outside the functional sequence:")
    for name in EXTRA_CATEGORIES:
        print(f"    {name}: {LABELS[name]}")
    print("\nRun one phase: test-sequence --step N (alias: -stepN).")
    print("Run from a phase: test-sequence --sequence-from phaseN_name.")
    print("Run all additional categories after the phases: test-sequence --extras.")
    print("Run one additional category: test-sequence --sequence-category NAME.")
    print("Optional: --workers N distributes files within each category; categories remain sequential.")
    print("Combine with --scope to reduce collection; phases do not add prerequisites.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
