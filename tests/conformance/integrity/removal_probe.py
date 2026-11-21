"""Rule-removal probe: does an identity's evidence actually depend on its rule?

A conformance scenario that passes proves little on its own: it may pass equally
with the rule it claims to test removed (dice that never reach the rule's
boundary, a setup another rule already decides, an effect the KB delivers twice).
This probe re-executes every scenario of an identity with that identity's rule
taken away and reports whether anything observable changes.

How the rule is removed
-----------------------
``rule/<collection>/<band>/<entry>/<effect>``
    When a scenario build selects the rule (``special_rule_ids``) the probe
    un-selects it.  Otherwise the identity's effect binding is filtered out of
    every ``mordheim_knowledge.loader.runtime_bindings`` call made by the
    compiler and the eligibility engine, and the eligibility catalogue cache is
    cleared, so the build compiles as if the KB did not bind that effect.
``mechanic/<id>``
    The mechanic id is deleted from every id list (``skill_ids``,
    ``condition_ids``, ``special_rule_ids``, ...) of every build in the scenario.
    When no list holds it — equipment sits in scalar slots such as
    ``main_weapon_id`` or ``armour_id`` — the mechanic's ``execution.yaml`` entry
    is neutralised instead: the compiler still finds the id, so the build stays
    legal, but the entry contributes no tag, bonus or flag.  The removal counts as
    reaching a build only when a compile actually looks the entry up.  An entry
    that carries nothing but its own tag delivers its effect from the item
    catalogue (an armour save, a material's profile), so a scenario that survives
    its neutralisation is reported ``inert``: the removal never touched the effect.
``core/`` identities are not probed (a core rule cannot be removed).

Per-scenario outcome
--------------------
``fails``       the scenario now fails with an ``EvidenceMismatch``: a die, a
                decision, an observation or a declared refusal changed.  This is
                the evidence the scenario discriminates.
``refused``     the build is now refused by construction (any other error), so the
                duel behaviour is never shown with and without the rule.
``survives``    the scenario still passes without the rule.
``inert``       the removal never reached a build (the scenarios never exercise
                the identity's KB grant, e.g. they inject the shared mechanic into a
                hand-built fighter instead of building the band profile).
``baseline-fails``  the scenario already fails with the rule present; its removal
                result says nothing and is not counted.

Per-identity verdict
--------------------
``discriminating``      at least one scenario ``fails``.
``construction-only``   none fails, at least one is ``refused``.
``inert``               every scenario is ``inert``.
``non-discriminating``  otherwise: the evidence passes without the rule.
``untested``            every scenario failed at baseline.

The probe executes the modular engine and reads, never writes, the corpus and
the knowledge base.  It is a measuring tool, not part of the conformance suite:
a verdict is information for authoring and KB review, never an oracle, and a
scenario is never changed to make the probe pass.

Usage (from the repository root)::

    python tests/conformance/integrity/removal_probe.py                 # whole corpus
    python tests/conformance/integrity/removal_probe.py --identity ID   # repeatable
    python tests/conformance/integrity/removal_probe.py --identities-file ids.txt \\
        --json outputs/removal-probe.json --workers 4 --show non-discriminating

Exit status: 0, or 1 with ``--fail-on non-discriminating`` (or another verdict)
when any identity has that verdict.
"""
from __future__ import annotations

import argparse
import collections
import copy
import importlib.util
import json
import multiprocessing
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
VERDICTS = ("discriminating", "construction-only", "inert", "non-discriminating", "untested")

# The removal target is process-global: the filtered ``runtime_bindings`` reads it.
_TARGET = {"rule": None, "effect": None, "mechanic": None, "tag_only": False, "hits": 0}
_STATE: dict = {}


def _import_support():
    """Load the conformance package under its stable name (as conftest does)."""
    if "mordheim_conformance" not in sys.modules:
        package = REPOSITORY_ROOT / "tests" / "conformance"
        spec = importlib.util.spec_from_file_location(
            "mordheim_conformance", package / "__init__.py", submodule_search_locations=[str(package)])
        module = importlib.util.module_from_spec(spec)
        sys.modules["mordheim_conformance"] = module
        spec.loader.exec_module(module)


def install() -> None:
    """Route every consumer's ``runtime_bindings`` through the removal filter (idempotent)."""
    if _STATE.get("installed"):
        return
    _import_support()
    import mordheim_knowledge.loader as loader
    import mordheim_construction.compiler as compiler
    import mordheim_construction.eligibility as eligibility
    import mordheim_construction.selection as selection
    from mordheim_conformance.execution.dice import EvidenceMismatch
    from mordheim_conformance.execution.runner import check_case
    from mordheim_knowledge.clauses import knowledge_root

    original = loader.runtime_bindings

    def filtered(rule, kind=None, *, include_pending=False):
        result = original(rule, kind, include_pending=include_pending)
        if _TARGET["rule"] is None or rule.get("id") != _TARGET["rule"]:
            return result
        removed = [effect.get("binding") for effect in (rule.get("runtime") or {}).get("effects") or ()
                   if effect.get("id") == _TARGET["effect"]]
        kept = tuple(binding for binding in result if not any(binding is gone for gone in removed))
        if len(kept) != len(result):
            _TARGET["hits"] += 1
        return kept

    # Every module that imported the function by name holds its own reference.
    for module in (loader, compiler, selection, eligibility):
        module.runtime_bindings = filtered

    from mordheim_core.effects import ExecutionEffect
    from mordheim_core.models import EffectSet
    original_index = compiler.effect_index

    class _Counting(dict):
        def __getitem__(self, key):
            if key == _TARGET["mechanic"]:
                _TARGET["hits"] += 1
            return super().__getitem__(key)

    def neutralised(ruleset, root=None):
        index = original_index(ruleset, root)  # cached: copied, never mutated
        target = _TARGET["mechanic"]
        if target is None or target not in index:
            return index
        result = _Counting(index)
        entry = index[target]
        result[target] = ExecutionEffect(EffectSet(), entry.trigger, entry.application, entry.stacking)
        return result

    # Only the compiler applies the index; the engine reads the compiled fighter.
    compiler.effect_index = neutralised
    _STATE.update(installed=True, eligibility=eligibility, check=check_case,
                  mismatch=EvidenceMismatch, root=knowledge_root())


def _builds(case: dict) -> list[dict]:
    builds = [case.get("fighters", {}).get(side) for side in ("first", "second")]
    builds += [participant.get("fighter") for participant in (case.get("duel_context") or {}).get("nearby") or ()]
    return [build for build in builds if isinstance(build, dict)]


def _execute(case: dict) -> str:
    _STATE["eligibility"]._catalogue.cache_clear()
    try:
        _STATE["check"](case, _STATE["root"])
    except _STATE["mismatch"]:
        return "fails"
    except Exception:  # noqa: BLE001 - any other error is a construction or runtime refusal
        return "refused"
    return "passes"


def _remove(identity: str, case: dict) -> bool:
    """Apply the removal to a copy of ``case``; False when it cannot reach any build."""
    kind = identity.split("/", 1)[0]
    if kind == "rule":
        entry, effect = identity.split("/")[3:5]
        selected = [build for build in _builds(case) if entry in (build.get("special_rule_ids") or ())]
        if selected and not case.get("expect_error"):
            for build in selected:
                build["special_rule_ids"] = [rule for rule in build["special_rule_ids"] if rule != entry]
            _TARGET.update(rule=None, effect=None, hits=1)
        else:
            _TARGET.update(rule=entry, effect=effect, hits=0)
        return True
    mechanic = identity.split("/", 1)[1]
    touched = False
    for build in _builds(case):
        for key, value in list(build.items()):
            if isinstance(value, list) and mechanic in value:
                build[key] = [item for item in value if item != mechanic]
                touched = True
    if touched:
        _TARGET.update(rule=None, effect=None, mechanic=None, tag_only=False, hits=1)
        return True
    from mordheim_knowledge.loader import load_execution_contract
    entry = next((row for row in load_execution_contract("mordheim").get("mechanics") or ()
                  if str(row.get("id")) == mechanic), None)
    if entry is None:
        _TARGET.update(rule=None, effect=None, mechanic=None, tag_only=False, hits=0)
        return False
    _TARGET.update(rule=None, effect=None, mechanic=mechanic, hits=0,
                   tag_only=set(entry.get("parameters") or {}) <= {"tags"})
    return True


def probe_scenario(identity: str, case: dict) -> str:
    """Outcome of one scenario of ``identity`` with the identity's rule removed."""
    install()
    _TARGET.update(rule=None, effect=None, mechanic=None, tag_only=False, hits=0)
    if _execute(copy.deepcopy(case)) != "passes":
        return "baseline-fails"
    mutated = copy.deepcopy(case)
    reached = _remove(identity, mutated)
    try:
        outcome = _execute(mutated) if reached else "inert"
        if outcome == "passes":
            reached = _TARGET["hits"] and not (_TARGET["mechanic"] and _TARGET["tag_only"])
            outcome = "survives" if reached else "inert"
    finally:
        _TARGET.update(rule=None, effect=None, mechanic=None, tag_only=False, hits=0)
        _STATE["eligibility"]._catalogue.cache_clear()
    return outcome


def verdict(outcomes: dict[str, str]) -> str:
    counted = {outcome for outcome in outcomes.values() if outcome != "baseline-fails"}
    if not counted:
        return "untested"
    if "fails" in counted:
        return "discriminating"
    if "refused" in counted:
        return "construction-only"
    if counted == {"inert"}:
        return "inert"
    return "non-discriminating"


def probe_identity(identity: str, cases: list[tuple[str, dict]]) -> dict:
    outcomes = {scenario_id: probe_scenario(identity, case) for scenario_id, case in cases}
    return {"verdict": verdict(outcomes), "scenarios": outcomes}


def _work(job):
    identity, cases = job
    return identity, probe_identity(identity, cases)


def run(identities: set[str] | None = None, workers: int = 4) -> dict[str, dict]:
    """Probe every admitted ``rule/`` and ``mechanic/`` identity that has scenarios."""
    install()
    from mordheim_conformance.corpus import group_by_audit, load_corpus
    from mordheim_knowledge.clauses import load_identities
    admitted = {record.identity for record in load_identities() if record.admitted}
    jobs = [(identity, [(scenario.scenario_id, scenario.case) for scenario in group])
            for identity, group in sorted(group_by_audit(load_corpus()).items())
            if identity.split("/", 1)[0] in ("rule", "mechanic") and identity in admitted
            and (identities is None or identity in identities)]
    if workers <= 1 or len(jobs) < 2:
        return dict(map(_work, jobs))
    # Forked workers inherit the installed filter and the loaded KB.
    with multiprocessing.get_context("fork").Pool(workers) as pool:
        return dict(pool.imap_unordered(_work, jobs, chunksize=8))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-run conformance scenarios with each identity's rule removed and report "
                    "which identities' evidence actually depends on the rule.")
    parser.add_argument("--identity", action="append", default=[], help="audit id to probe (repeatable)")
    parser.add_argument("--identities-file", type=Path, help="file with one audit id per line")
    parser.add_argument("--workers", type=int, default=4, help="worker processes (default 4; 1 = serial)")
    parser.add_argument("--json", type=Path, help="write the per-scenario outcomes to this JSON file")
    parser.add_argument("--show", action="append", choices=VERDICTS, default=[],
                        help="list the identities with this verdict (repeatable)")
    parser.add_argument("--fail-on", action="append", choices=VERDICTS, default=[],
                        help="exit 1 when any identity has this verdict (repeatable)")
    args = parser.parse_args(argv)
    wanted = set(args.identity)
    if args.identities_file:
        wanted |= {line.strip() for line in args.identities_file.read_text(encoding="utf-8").splitlines()
                   if line.strip()}
    result = run(wanted or None, args.workers)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=1, sort_keys=True), encoding="utf-8")
    counts = collections.Counter((identity.split("/", 1)[0], row["verdict"]) for identity, row in result.items())
    print(f"Rule-removal probe: {len(result)} identities")
    for kind in ("rule", "mechanic"):
        line = ", ".join(f"{name} {counts[(kind, name)]}" for name in VERDICTS if counts[(kind, name)])
        if line:
            print(f"  {kind}: {line}")
    for name in args.show:
        print(f"\n{name}:")
        for identity, row in sorted(result.items()):
            if row["verdict"] == name:
                print(f"  {identity}")
                for scenario_id, outcome in sorted(row["scenarios"].items()):
                    print(f"      {outcome:15} {scenario_id}")
    failing = [identity for identity, row in result.items() if row["verdict"] in args.fail_on]
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
