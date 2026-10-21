"""P00 read-only reconciliation of the admitted clause universe.

Joins three existing sources, writes nothing but its own outputs:

1. ``sources/knowledge/verification/clause-contracts.csv`` (canonical register,
   read through ``tools/knowledge/clause_registry.py`` helpers' schema: plain
   CSV rows, admitted = ``clause_scope == "YES"``).
2. The principal-key annexes of ``TMP_VECTORIAL_ENGINE_2A2B/G0x_*.md``
   (section ``## Claves principales asignadas``), which give each key exactly
   one owning group (G00-G06).
3. ``tests/E2E/modular-engine/cases/**/*.yaml`` (``audit_id`` + ``covers``),
   which give the existing modular scenarios per key.

Outputs (P00-results/):
- ``universe-reconciliation.csv``: one row per admitted key with owner,
  consumer class, behaviour family, existing E2E scenarios and disposition.
- ``universe-summary.txt``: aggregate counts used in the deliverable.

Run from the repository root:

    python -X utf8 TMP_VECTORIAL_ENGINE_2A2B/parity_update/P00-results/reconcile_universe.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = Path(__file__).resolve().parent
REGISTER = ROOT / "sources/knowledge/verification/clause-contracts.csv"
ANNEXES = (
    "G00_BASE_ADMISION_Y_COORDINACION.md",
    "G01_COMPILACION_COMPARTIDA_Y_ENLACES.md",
    "G02_ESTADO_RECURSOS_Y_MUTACIONES.md",
    "G03_OPERADORES_Y_CONTEXTO_DE_ATAQUE.md",
    "G04_ATAQUES_EQUIPO_Y_REACCIONES.md",
    "G05_PSICOLOGIA_Y_LIDERAZGO_LOCAL.md",
    "G06_RONDAS_RECUPERACION_E_INTEGRACION.md",
)
E2E_CASES = ROOT / "tests/E2E/modular-engine/cases"

#: Runtime modules of the modular oracle, mapped to the behaviour family that
#: P01/P02 must exercise.  Order is precedence: the first family present wins,
#: because it is the layer that carries the printed consequence (see
#: TMP_VECTORIAL_ENGINE_2A2B/README.md, "Cómo se asignaron las cláusulas").
RUNTIME_FAMILIES = (
    ("modular/rounds", "F08-round-orchestration"),
    ("modular/pools", "F05-attack-pool-and-damage"),
    ("modular/attacks", "F05-attack-pool-and-damage"),
    ("modular/psychology", "F09-psychology"),
    ("modular/leadership", "F10-leadership"),
    ("modular/equipment", "F06-equipment-and-loadout"),
    ("modular/aftermath", "F11-aftermath-recovery"),
    ("modular/alchemy", "F11-aftermath-recovery"),
    ("modular/mutations", "F02-mutations-and-characteristics"),
    ("modular/state", "F03-state-and-resources"),
    ("modular/contexts", "F04-attack-context-and-operators"),
    ("combat/phases", "F04-attack-context-and-operators"),
    ("modular/duel", "F08-round-orchestration"),
    ("verification/consumers", "F00-register-inventory"),
)
#: Consumers whose code is the shared compiler/projection: the same function
#: produces the compiled fighter for both engines, so a duel cannot add proof.
SHARED_MARKERS = (
    "mordheim_construction/",
    "packages/typescript/",
    "roster-construction",
    "mordheim_construction.",
    "catalog/mechanics/execution.yaml",
    "mordheim_knowledge/loader.py",
    "kernel.py",
    "combat_compile",
    "tests/python/construction/",
)


def read_register():
    with REGISTER.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_annexes():
    """Return {(id, clause_id): owner} from the G00-G06 principal tables."""
    owners: dict[tuple[str, str], str] = {}
    pattern = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|")
    for name in ANNEXES:
        owner = name.split("_", 1)[0]
        text = (ROOT / "TMP_VECTORIAL_ENGINE_2A2B" / name).read_text(encoding="utf-8")
        section = text.split("## Claves principales asignadas", 1)[1]
        section = section.split("\n## ", 1)[0]
        for line in section.splitlines():
            match = pattern.match(line)
            if not match:
                continue
            key = (match.group(1), match.group(2))
            if key in owners and owners[key] != owner:
                raise SystemExit(f"duplicate principal key {key}: {owners[key]} / {owner}")
            owners[key] = owner
    return owners


def parse_e2e():
    """Return {(audit_id, clause_id): [scenario ids]} from the modular battery."""
    import yaml

    covered: dict[tuple[str, str], list[str]] = defaultdict(list)
    for path in sorted(E2E_CASES.rglob("*.yaml")):
        for scenario in yaml.load(path.read_text(encoding="utf-8"),
                                  Loader=yaml.CSafeLoader) or []:
            audit_id = str(scenario["audit_id"])
            test_id = f"{audit_id}::{scenario['id']}"
            for clause in scenario["covers"]:
                covered[(audit_id, str(clause))].append(test_id)
    return covered


#: The register carries two spellings of the same module reference
#: (``modular/foo.py::func`` and ``mordheim_combat.modular.foo.func``); G00
#: normalises them the same way, so P00 does not invent a third form.
def _normalize(reference: str) -> str:
    return reference.replace(".", "/")


def split_consumers(raw: str) -> list[str]:
    try:
        return [str(item) for item in json.loads(raw)]
    except json.JSONDecodeError:
        return []


def consumer_class(consumers: list[str]):
    """('shared'|'shared-operator'|'runtime'|'mixed'|'unlocated', family).

    ``shared`` is compilation/projection code used by both engines;
    ``shared-operator`` is a clause whose only runtime consumer is
    ``combat/phases`` — the formula both engines call, so the exact operator
    checks (``_vectorized._exact_operator_checks``) are its evidence and a new
    duel adds nothing; ``runtime``/``mixed`` need an executed runtime case.
    ``unlocated`` means the register names no consumer: it is a pending
    localization, never proof that the clause is static (see
    ``localize_unlocated.py``).
    """
    runtime_modules = []
    shared = False
    for consumer in consumers:
        normalized = _normalize(consumer)
        if any(_normalize(marker) in normalized for marker in SHARED_MARKERS):
            shared = True
            continue
        runtime_modules.append(normalized)
    if not consumers:
        return "unlocated", ""
    family = ""
    for consumer in runtime_modules:
        for marker, name in RUNTIME_FAMILIES:
            if _normalize(marker) in consumer:
                family = name
                break
        if family:
            break
    operator_only = bool(runtime_modules) and all(
        "combat/phases" in consumer for consumer in runtime_modules)
    if operator_only:
        return "shared-operator", "F04-attack-context-and-operators"
    if family and shared:
        return "mixed", family
    if family:
        return "runtime", family
    if shared:
        return "shared", ""
    return "unclassified", ""


def main() -> int:
    register = read_register()
    admitted = [row for row in register if row["clause_scope"] == "YES"]
    owners = parse_annexes()
    covered = parse_e2e()

    register_keys = {(row["id"], row["clause_id"]) for row in admitted}
    missing_owner = sorted(register_keys - set(owners))
    extra_owner = sorted(set(owners) - register_keys)

    rows = []
    for row in admitted:
        key = (row["id"], row["clause_id"])
        consumers = split_consumers(row["consumer"])
        klass, family = consumer_class(consumers)
        scenarios = covered.get(key, [])
        if klass == "shared":
            disposition = "shared-compilation (no new duel)"
        elif klass == "shared-operator":
            disposition = "shared-operator formula (exact operator check)"
        elif klass in {"runtime", "mixed"}:
            disposition = "runtime-parity-required"
        elif klass == "unlocated":
            disposition = "unlocated-consumer (localization pending)"
        else:
            disposition = "unclassified-consumer (review)"
        rows.append({
            "id": row["id"],
            "clause_id": row["clause_id"],
            "owner": owners.get(key, ""),
            "consumer_count": len(consumers),
            "consumer_class": klass,
            "behaviour_family": family,
            "e2e_scenarios": len(scenarios),
            "e2e_example": scenarios[0] if scenarios else "",
            "disposition": disposition,
            "effect_id": row["effect_id"],
            "relation": row["relation"],
        })

    out = RESULTS / "universe-reconciliation.csv"
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_owner = Counter(row["owner"] for row in rows)
    by_class = Counter(row["consumer_class"] for row in rows)
    by_disposition = Counter(row["disposition"] for row in rows)
    family_class = Counter((row["behaviour_family"], row["consumer_class"]) for row in rows)
    owner_class = Counter((row["owner"], row["consumer_class"]) for row in rows)
    e2e_covered = sum(1 for row in rows if row["e2e_scenarios"])
    runtime_rows = [row for row in rows
                    if row["consumer_class"] in {"runtime", "mixed"}]
    runtime_e2e = sum(1 for row in runtime_rows if row["e2e_scenarios"])

    lines = [
        "rows_register=%d" % len(register),
        "admitted=%d" % len(admitted),
        "principal_keys_in_annexes=%d" % len(owners),
        "admitted_without_owner=%d" % len(missing_owner),
        "annex_keys_not_admitted=%d" % len(extra_owner),
        "admitted_with_e2e_scenario=%d" % e2e_covered,
        "admitted_without_e2e_scenario=%d" % (len(rows) - e2e_covered),
        "runtime_rows=%d" % len(runtime_rows),
        "runtime_with_e2e_scenario=%d" % runtime_e2e,
        "runtime_without_e2e_scenario=%d" % (len(runtime_rows) - runtime_e2e),
        "",
        "by_owner=" + json.dumps(dict(sorted(by_owner.items()))),
        "by_consumer_class=" + json.dumps(dict(sorted(by_class.items()))),
        "by_disposition=" + json.dumps(dict(sorted(by_disposition.items())), ensure_ascii=False),
        "",
        "family x class:",
        *[f"  {family or '(none)'} {klass} {count}"
          for (family, klass), count in sorted(family_class.items())],
        "",
        "owner x class:",
        *[f"  {owner} {klass} {count}" for (owner, klass), count in sorted(owner_class.items())],
    ]
    if missing_owner:
        lines += ["", "admitted without owner (first 20):"]
        lines += [f"  {key}" for key in missing_owner[:20]]
    if extra_owner:
        lines += ["", "annex keys not admitted (first 20):"]
        lines += [f"  {key}" for key in extra_owner[:20]]
    text = "\n".join(lines) + "\n"
    (RESULTS / "universe-summary.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0 if not missing_owner and not extra_owner else 1


if __name__ == "__main__":
    sys.exit(main())
