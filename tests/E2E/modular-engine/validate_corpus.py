"""Engine-free structural validator and report for the declarative corpus.

Run from any directory:

``python tests/E2E/modular-engine/validate_corpus.py [corpus_directory]
[--require-complete]``

The tool imports nothing from the combat packages: it reuses ``corpus.py``
(the battery's own loading and static scenario contract) and
``test_inventory.py`` (the canonical-register reading and the declared
coverage report) through the package name ``mordheim_modular_e2e``, exactly as
pytest's ``conftest.py`` registers the hyphenated directory.  It never
rewrites the register, never re-derives a second normative policy, and never
measures scaffold staleness — generative source snapshots are a separate
concern retained by ``generate_skeletons.py``.

Exit codes: ``0`` when nothing failed (reported gaps stay reported and do not
pretend completeness), ``1`` on integrity problems (a file or scenario that
fails to load or validate, unknown or duplicate references), ``2`` when
``--require-complete`` was requested and any admitted identity still lacks
scenarios or admits an uncovered clause.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PACKAGE_NAME = "mordheim_modular_e2e"
AUTHORING_STATUSES = ("TODO", "PARTIAL", "AUTHORED", "REVIEWED")
#: Clause markers the authoring grammar publishes, with the only matching status.
MARKER_STATUSES = {"PARTIAL": {"PARTIAL"}, "AUTHORED": {"AUTHORED", "REVIEWED"}}


def _import_support():
    """Import corpus and test_inventory through their canonical package name.

    Mirrors ``conftest.py``: the hyphenated directory is registered as
    ``mordheim_modular_e2e`` so every reading is the very module the test
    battery uses; no combat, engine or runner module is imported.
    """
    if PACKAGE_NAME not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            PACKAGE_NAME, HERE / "__init__.py",
            submodule_search_locations=[str(HERE)])
        package = importlib.util.module_from_spec(spec)
        sys.modules[PACKAGE_NAME] = package
        spec.loader.exec_module(package)
    corpus = importlib.import_module(f"{PACKAGE_NAME}.corpus")
    inventory = importlib.import_module(f"{PACKAGE_NAME}.test_inventory")
    return corpus, inventory


class Finding:
    """One reportable observation with its section and file context."""

    def __init__(self, section: str, message: str, source: str | None = None):
        self.section = section
        self.message = message
        self.source = source

    def render(self) -> str:
        return f"  {self.message}" + (f"  [{self.source}]" if self.source else "")


def load_strictly(corpus, directory: Path):
    """Load the corpus file by file, collecting every failure instead of aborting.

    Reuses ``corpus.validate_scenario`` (the battery's own per-scenario
    validation) and the loader's duplicate-identity rule, but reports
    per-item independent findings so one defect never hides the rest.
    """
    scenarios = []
    findings: list[Finding] = []
    declared: dict[str, str] = {}
    duplicates: list[tuple[str, str, str]] = []
    files = sorted(directory.rglob("*.yaml"))
    for path in files:
        source = path.relative_to(directory).as_posix()
        try:
            documents = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as error:
            findings.append(Finding("integrity", f"unreadable file: {error}", source))
            continue
        except yaml.YAMLError as error:
            findings.append(Finding("integrity", f"invalid YAML: {str(error).splitlines()[0]}",
                                    source))
            continue
        if documents is None:
            documents = []
        if not isinstance(documents, list):
            findings.append(Finding("integrity", "a corpus file must be a list of scenarios",
                                    source))
            continue
        for index, raw in enumerate(documents):
            try:
                scenario = corpus.validate_scenario(raw, source, index)
            except corpus.CorpusError as error:
                findings.append(Finding("integrity", str(error), source))
                continue
            if scenario.test_id in declared:
                duplicates.append((scenario.test_id, source, declared[scenario.test_id]))
                continue
            declared[scenario.test_id] = source
            scenarios.append(scenario)
    return scenarios, findings, duplicates, files


def declared_references(inventory, scenarios):
    """Look up every declared identity and clause reference in the register."""
    declared, admitted, admitted_ids = inventory.read_register()
    unknown_identities = []
    unknown_clauses = []
    for scenario in scenarios:
        if scenario.audit_id not in declared:
            unknown_identities.append(scenario)
            continue
        for clause in scenario.covers:
            if clause not in declared[scenario.audit_id]:
                unknown_clauses.append((scenario, clause))
    return declared, admitted, admitted_ids, unknown_identities, unknown_clauses


AUTHORING_LINE = re.compile(r"^# authoring_status:\s*(\S+).*$", re.MULTILINE)
EXECUTION_LINE = re.compile(r"^# execution_status:\s*(\S+).*$", re.MULTILINE)
CLAUSE_LINE = re.compile(r"^# Clause:\s*([^\s(]+)\s*\(scope:\s*([A-Za-z]+)\)\s*$", re.MULTILINE)
MARKER_LINE = re.compile(r"^# (PARTIAL|AUTHORED)\[([^\]]+)\]", re.MULTILINE)


def authoring_metadata(text: str, scenarios) -> tuple[dict, list[Finding]]:
    """Authoring metadata of one file plus its own comment-grammar conflicts."""
    findings: list[Finding] = []
    statuses = AUTHORING_LINE.findall(text)
    status = statuses[0] if statuses else None
    executions = EXECUTION_LINE.findall(text)
    clauses = dict(CLAUSE_LINE.findall(text))
    markers: dict[str, list[str]] = {"PARTIAL": [], "AUTHORED": []}
    for kind, tag in MARKER_LINE.findall(text):
        markers[kind].append(tag.strip())
    metadata = {
        "status": status,
        "execution_status": executions[0] if executions else None,
        "empty_body": not scenarios,
        "clause_tags": sorted(clauses),
        "markers": markers,
    }
    if status is None:
        findings.append(Finding("authoring", "no `# authoring_status:` line"))
    elif status not in AUTHORING_STATUSES:
        findings.append(Finding("authoring", f"unknown authoring_status {status!r}"))
    if not executions:
        findings.append(Finding("authoring", "no `# execution_status:` line"))
    for kind, tags in sorted(markers.items()):
        for tag in tags:
            if tag not in clauses:
                findings.append(Finding(
                    "authoring", f"marker {kind}[{tag}] does not name a declared clause"))
    if status in ("AUTHORED", "PARTIAL") and not markers[status]:
        findings.append(Finding(
            "authoring", f"authoring_status {status} without any {status}[...] marker"))
    # Mixed markers across different clauses are the established grammar: a
    # PARTIAL file carries AUTHORED markers for the clauses it finished.  The
    # state conflicts are per clause (both markers on one tag) and the states
    # that may not sit with a held-clause marker at all.
    double = sorted(set(markers["PARTIAL"]) & set(markers["AUTHORED"]))
    for tag in double:
        findings.append(Finding(
            "authoring",
            f"clause {tag!r} carries both PARTIAL and AUTHORED markers"))
    if status in ("REVIEWED", "TODO"):
        held = sorted(set(markers["PARTIAL"]) - set(markers["AUTHORED"]))
        if held:
            findings.append(Finding(
                "authoring",
                f"authoring_status {status} with PARTIAL (held-clause) markers {held}"))
    if status == "AUTHORED" and not scenarios:
        findings.append(Finding("authoring", "AUTHORED with an empty scenario body"))
    if status == "AUTHORED":
        covered = {clause for scenario in scenarios for clause in scenario.covers}
        pending = [tag for tag, scope in clauses.items() if scope == "YES" and tag not in covered]
        if pending:
            findings.append(Finding(
                "authoring",
                f"AUTHORED with in-scope clauses not covered here: {sorted(pending)}"))
    return metadata, findings


def report(corpus, inventory, directory: Path, require_complete: bool) -> int:
    scenarios, integrity, duplicates, files = load_strictly(corpus, directory)
    declared, admitted, admitted_ids, unknown_identities, unknown_clauses = (
        declared_references(inventory, scenarios))
    authoring: list[Finding] = []
    metadata_rows = []
    statuses: dict[str, int] = {name: 0 for name in AUTHORING_STATUSES}
    statuses["missing"] = 0
    empty = 0
    executable = 0
    for path in files:
        source = path.relative_to(directory).as_posix()
        file_scenarios = [s for s in scenarios if s.source == source]
        metadata, findings = authoring_metadata(path.read_text(encoding="utf-8"), file_scenarios)
        for finding in findings:
            finding.source = source
            authoring.append(finding)
        if metadata["status"] in statuses:
            statuses[metadata["status"]] += 1
        else:
            statuses["missing"] += 1
        empty += int(metadata["empty_body"])
        executable += int(metadata["execution_status"] == "UNEXECUTED")
        metadata_rows.append((source, metadata))
    retired = sorted({scenario.audit_id for scenario in scenarios
                      if scenario.audit_id not in declared})

    lines: list[str] = []
    lines.append("Corpus structural validation")
    lines.append(f"  corpus directory: {directory}")
    lines.append(f"  files scanned: {len(files)}; scenarios declared: {len(scenarios)}")

    lines.append("")
    lines.append("Integrity")
    for finding in integrity:
        lines.append(finding.render())
    for test_id, source, first in duplicates:
        finding = Finding("integrity",
                          f"duplicate scenario {test_id!r} (first declared in {first})", source)
        lines.append(finding.render())
    lines.append(f"  unknown audit_id declarations: "
                 f"{len({u.audit_id for u in unknown_identities})} identities, "
                 f"{len(unknown_identities)} scenarios")
    for scenario in unknown_identities[:10]:
        lines.append(f"    {scenario.test_id!r}")
    if len(unknown_identities) > 10:
        lines.append(f"    ... {len(unknown_identities) - 10} more")
    lines.append(f"  unknown clause references: {len(unknown_clauses)}")
    for scenario, clause in unknown_clauses[:10]:
        lines.append(f"    {scenario.test_id!r} covers {clause!r}")
    if len(unknown_clauses) > 10:
        lines.append(f"    ... {len(unknown_clauses) - 10} more")

    lines.append("")
    lines.append("Authoring metadata")
    lines.append("  authoring_status counts: " + ", ".join(
        f"{name}={count}" for name, count in statuses.items()))
    lines.append(f"  files with an empty body: {empty}")
    lines.append(f"  authoring metadata conflicts: {len(authoring)} findings")
    for finding in authoring:
        lines.append(finding.render())

    lines.append("")
    lines.append("Declared coverage (register as it stands; staleness is not measured here)")
    coverage = inventory.coverage(scenarios)
    lines.extend("  " + line for line in coverage.render().splitlines())

    lines.append("")
    lines.append("Retired from the register (reported separately, never as pending authoring)")
    lines.append(f"  audit identities with scenarios but no register row: {len(retired)}")
    for identity in retired[:20]:
        lines.append(f"    {identity}")
    if len(retired) > 20:
        lines.append(f"    ... {len(retired) - 20} more")

    exit_code = 0
    if integrity or duplicates or unknown_identities or unknown_clauses:
        exit_code = 1
    if require_complete:
        gaps = coverage.uncovered()
        if coverage.missing_ids or gaps:
            exit_code = max(exit_code, 2)
            lines.append("")
            lines.append("--require-complete: the declared corpus is not complete yet")
    elif coverage.missing_ids or coverage.uncovered():
        lines.append("")
        lines.append("  reported gaps are information only; run with --require-complete "
                     "to fail on them")

    print("\n".join(lines))
    return exit_code


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("corpus_directory", nargs="?", default=None,
                        help="explicit cases directory (default: the corpus next to this script)")
    parser.add_argument("--corpus-dir", default=None,
                        help="alternative spelling for the explicit corpus directory")
    parser.add_argument("--require-complete", action="store_true",
                        help="fail (exit 2) if any admitted identity or clause is uncovered")
    arguments = parser.parse_args(argv)
    corpus, inventory = _import_support()
    directory = Path(arguments.corpus_dir or arguments.corpus_directory
                     or corpus.CASES_DIRECTORY)
    return report(corpus, inventory, directory, arguments.require_complete)


if __name__ == "__main__":
    raise SystemExit(main())
