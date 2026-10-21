"""Ordered Python tests, loaded only by ``mordheim-utils.py test-sequence``.

Sequential mode uses one pytest collection/session; optional workers run each
phase in its own pytest/xdist session with a barrier between phases.
Native markers select tests, directories identify
backend components. No inventory of test names and no cached success. This is a
conservative category order, not inferred dependencies between individual tests.
Live-product harness checks run after rule/interaction contracts. NumPy/native
component suites and backend parity run after the selected modular checks.

Usage (from the repository root)::

    python tools/mordheim-utils.py test-sequence --sequence-plan -q
    python tools/mordheim-utils.py test-sequence --scope construction -q
    python tools/mordheim-utils.py test-sequence -m 'eligibility or compilation'
    python tools/mordheim-utils.py test-sequence --sequence-from rule_behavior
    python tools/mordheim-utils.py test-sequence --step 1 --workers 4 -q

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


# This list owns execution order only. Category definitions/annotations remain
# in pyproject.toml and the tests. Stable sorting preserves order within a stage.
CATEGORY_ORDER = (
    "architecture", "data_contract", "knowledge_integrity", "data_transport",
    "eligibility", "compilation", "operator", "rule_behavior", "interaction",
    "test_infrastructure", "persistence", "workflow", "presentation",
    "end_to_end", "evidence", "parity", "delivery", "performance",
)

# Numbered selections, not another test inventory. Backend stages are selected
# by the existing component/parameter classification in _stage, regardless of
# their primary category.
STEPS = (
    ("Source contracts and KB integrity", ("architecture", "data_contract", "knowledge_integrity")),
    ("Transport and eligibility", ("data_transport", "eligibility", "shared-parity")),
    ("Compilation and local operators", ("compilation", "operator")),
    ("Individual rule behaviour", ("rule_behavior",)),
    ("Interactions and state sequences", ("interaction",)),
    ("Harnesses, persistence and application workflows", ("test_infrastructure", "persistence", "workflow")),
    ("Presentation", ("presentation",)),
    ("Connected end-to-end acceptance", ("end_to_end",)),
    ("Evidence and coverage bookkeeping", ("evidence",)),
    ("Baseline delivery and performance", ("delivery", "performance")),
    ("Optimized backends and engine parity", ()),
)


def step_number(stage):
    if stage.startswith("optimized/"):
        return len(STEPS)
    return next(number for number, (_, stages) in enumerate(STEPS, 1) if stage in stages)


def pytest_addoption(parser):
    group = parser.getgroup("test sequence", "Ordered Python test execution")
    group.addoption("--sequence-plan", action="store_true",
                    help="Collect and show the ordered selection without executing tests.")
    group.addoption("--sequence-keep-going", action="store_true",
                    help="Explicit alias for the default: continue after failures (incompatible with -x/--maxfail).")
    group.addoption("--sequence-from", metavar="STAGE",
                    help="Start at CATEGORY or optimized/CATEGORY; does not validate earlier stages.")
    group.addoption("--step", type=int, choices=range(1, len(STEPS) + 1), metavar="N",
                    help="Execute only numbered phase N; use test-sequence --steps for the list.")


def _stage(item):
    categories = {mark.name for mark in item.iter_markers()} & set(CATEGORY_ORDER)
    if len(categories) != 1:
        raise pytest.UsageError(
            f"test-sequence requires exactly one primary category: {item.nodeid} "
            f"(found {sorted(categories)})")
    category = categories.pop()
    try:
        relative = item.path.relative_to(item.config.rootpath).as_posix()
    except ValueError as error:
        raise pytest.UsageError(f"sequence item outside the selected root: {item.nodeid}") from error
    backend = any(relative.startswith(f"tests/python/combat/{name}/")
                  for name in ("vectorized", "native"))
    parameters = getattr(getattr(item, "callspec", None), "params", {})
    backend = backend or parameters.get("backend") in ("numpy", "native")
    # Cross-language decisions belong beside shared eligibility, whereas engine
    # parity must wait for the selected oracle checks. This is a component rule,
    # not a list of individual parity tests.
    shared_parity = category == "parity" and relative.startswith("tests/python/construction/")
    rank = CATEGORY_ORDER.index(category)
    if shared_parity:
        return (0, CATEGORY_ORDER.index("eligibility") + .5), "shared-parity"
    return (int(backend or category == "parity"), rank), (
        f"optimized/{category}" if backend or category == "parity" else category)


def pytest_configure(config):
    if config.getoption("step") is not None and config.getoption("sequence_from"):
        raise pytest.UsageError("--step selects one phase; do not combine it with --sequence-from.")
    worker = hasattr(config, "workerinput")
    distributed = (worker or bool(getattr(config.option, "numprocesses", None))
                   or getattr(config.option, "dist", "no") != "no")
    if distributed and (config.getoption("step") is None or config.getoption("sequence_plan")
                        or (not worker and getattr(config.option, "dist", "no") != "loadfile")):
        raise pytest.UsageError("Parallel execution requires one --step and --dist=loadfile; "
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

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_node_collection_finished(self, node, ids):
        # The controller has no pytest Items. xdist already verifies identical
        # worker collections; summarize this single phase, without another
        # per-test metadata protocol or double-counting the workers' copies.
        step = self.config.getoption("step")
        self.stages = dict.fromkeys(ids, f"step {step}: {STEPS[step - 1][0]}")

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, config, items):
        ranked = [(_stage(item), item) for item in items]
        ranked.sort(key=lambda entry: entry[0][0])
        step = config.getoption("step")
        if step is not None:
            excluded = [item for (_, stage), item in ranked if step_number(stage) != step]
            ranked = [entry for entry in ranked if step_number(entry[0][1]) == step]
            config.hook.pytest_deselected(items=excluded)
        start = config.getoption("sequence_from")
        if start:
            if start == "shared-parity":
                minimum = (0, CATEGORY_ORDER.index("eligibility") + .5)
            else:
                category = start.removeprefix("optimized/")
                if category not in CATEGORY_ORDER:
                    raise pytest.UsageError(f"unknown sequence stage {start!r}")
                minimum = (int(start.startswith("optimized/") or category == "parity"),
                           CATEGORY_ORDER.index(category))
            excluded = [item for (key, _), item in ranked if key < minimum]
            ranked = [entry for entry in ranked if entry[0][0] >= minimum]
            config.hook.pytest_deselected(items=excluded)
        items[:] = [item for _, item in ranked]
        self.stages = {item.nodeid: stage for (_, stage), item in ranked}

    def pytest_report_collectionfinish(self):
        if getattr(self.config.option, "numprocesses", None):
            return []  # Workers perform collection; the controller has no Items.
        counts = Counter(self.stages.values())
        lines = ["Python test sequence (one collection; selected paths only):"]
        lines.extend(f"  {stage}: {count}" for stage, count in counts.items())
        lines.append("No prerequisite expansion, build preparation or certification is implied.")
        step = self.config.getoption("step")
        if step is not None:
            lines.append(f"Only step {step}: {STEPS[step - 1][0]}; other phases are not validated.")
        if self.config.getoption("sequence_from"):
            lines.append("Earlier stages omitted explicitly; no saved result was validated.")
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
                f"{stage}: " + ", ".join(f"{count} {outcome}" for outcome, count in results.items()))


def run_parallel(workers, args):
    """Barrier between phases via blocking pytest calls; xdist owns scheduling."""
    parser = argparse.ArgumentParser(prog="test-sequence", add_help=False)
    parser.add_argument("--step", type=int, choices=range(1, len(STEPS) + 1))
    parser.add_argument("--sequence-from")
    parser.add_argument("-x", "--exitfirst", dest="maxfail", action="store_const", const=1)
    parser.add_argument("--maxfail", type=int, default=0)
    selected, forwarded = parser.parse_known_args(args)
    if workers < 1:
        print("test-sequence: --workers must be a positive integer", file=sys.stderr)
        return 2
    if selected.sequence_from:
        print("test-sequence: use --step with --workers; --sequence-from is sequential only", file=sys.stderr)
        return 2
    if any(arg in ("-n", "--numprocesses", "--dist") or arg.startswith(("-n", "--numprocesses=", "--dist="))
           for arg in forwarded):
        print("test-sequence: --workers manages -n and --dist; do not combine them", file=sys.stderr)
        return 2
    base = [sys.executable, "-m", "pytest", "-p", "tools.verification.test_sequence"]
    if selected.maxfail:
        forwarded.append(f"--maxfail={selected.maxfail}")
    # A plan is a single serial collection, even when workers were requested.
    if any(arg in ("--sequence-plan", "--collect-only", "--co") for arg in forwarded):
        phase = ["--step", str(selected.step)] if selected.step else []
        return subprocess.call([*base, *forwarded, *phase])
    if importlib.util.find_spec("xdist") is None:
        print('test-sequence: install development dependencies: python -m pip install -e ".[dev]"',
              file=sys.stderr)
        return 2
    phases = [selected.step] if selected.step else range(1, len(STEPS) + 1)
    results = []
    exit_code = 0
    for phase in phases:
        print(f"\n=== Step {phase}: {STEPS[phase - 1][0]} ({workers} workers, loadfile) ===", flush=True)
        try:
            code = subprocess.call([*base, "-p", "xdist", "-n", str(workers), "--dist=loadfile",
                                    *forwarded, "--step", str(phase)])
        except KeyboardInterrupt:
            code = 130
        results.append((phase, code))
        if code not in (0, 5):
            exit_code = code
            if code != 1 or selected.maxfail:
                break
    print("\nPhase results (process completion is the barrier):", flush=True)
    for phase, code in results:
        status = {0: "passed", 1: "failed", 5: "empty selection (not validated)"}.get(code, f"aborted ({code})")
        print(f"  step {phase}: {status}", flush=True)
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
    for number, (label, stages) in enumerate(STEPS, 1):
        print(f"  {number:2}. {label}: {', '.join(stages) if stages else 'optimized/*'}")
    print("\nRun one: test-sequence --step N (alias: -stepN).")
    print("Optional: --workers N distributes files within each phase; phases remain sequential.")
    print("Combine with --scope to reduce collection; phases do not add prerequisites.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
