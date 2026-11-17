"""Divide the rules-conformance authoring backlog into batches.

The backlog is every admitted ``rule/`` or ``mechanic/`` identity of the clause
inventory that no conformance scenario names.  This tool reads the knowledge
base and the corpus (never writes either) and derives, deterministically:

* the **unit** of authoring — a printed-rule group: an uncovered mechanic
  together with every uncovered rule bound to it (they share one oracle: the
  mechanic through ``skill_ids``, its rules through the real build), plus the
  rule identities that share a binding;
* the **route** each scenario must use (profile build, selection, ``skill_ids``
  on a hand-built fighter, ``condition_ids`` or supplied input, equipment slot,
  admission/refusal pair);
* an **effort** weight: 4 to derive a new contract, 1 to add a member to an
  authored or batch-local model, 1.5 for a construction member, 2 for a triage
  item (a recorded blocker, an operator no engine code reads, a profile that
  does not compile);
* **themes** by engine area, packed into batches of about 50 effort units
  (split above 75), triage first, one-off operators grouped by owner.

Usage (from the repository root, inside the checkout's venv)::

    python tools/conformance/backlog_batches.py --table            # markdown table (TODO.md)
    python tools/conformance/backlog_batches.py --out <work-dir>   # batches.json + <batch>.ids.txt
    python tools/conformance/backlog_batches.py --batch B03        # member identities of one batch

The plan of record is the table in ``TODO.md``; this tool regenerates it as
batches land, and covered identities drop out automatically.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "conformance"))

import yaml  # noqa: E402

from generate_skeletons import declared_identities, read_definitions, relative_path  # noqa: E402
from mordheim_knowledge.loader import knowledge_root, read_yaml  # noqa: E402

KB = knowledge_root()
CASES = REPO / "tests" / "conformance" / "cases"
ENGINE = REPO / "packages" / "python" / "combat-engine" / "mordheim_combat"
CONSTRUCTION = REPO / "packages" / "python" / "roster-construction" / "mordheim_construction"

THEMES = (
    ("psy-immunities", r"psychology-immun|fear-immun|immune-to-psych|cold-blooded|stupidity-exempt|charm-immun|terror-immun"),
    ("psy-tests-and-enemy-effects", r"causes-fear|fear|terror|stupid|fears-fire|accustomed|hypnot|seduc|deceive|enchanting|mesmer|craven|charm|squabble|animosity|gaze"),
    ("hatred-frenzy-and-charge-rages", r"hatred|hate|frenzy|berserk|charge-test|righteous-charge|unstoppable|rage|fury|man-hater|despise|ashamed|inconsisten|haunted|babbling|confound|emissary|solkan|fanatical|devoted|crusader"),
    ("leadership", r"leader|leadership|songster|command\.|bear-handler|dim-witted|oracle|augur|ranald|luck|poetry|insignia|dodgy|rout|own-leadership|relay-orders|mob-|shanty|banter|guiding"),
    ("survival-injury-and-immunity", r"poison-immune|concussion|hard-to-kill|ignore-pain|no-pain|thin-flesh|daemonic-flesh|inured|drug-immun|large-target|construct|undead|resilien|tough|disability|massively|injury|lycanthrope|hillman|ethereal|electrical|mer-creature|suckers|beak|eye-stalks|prehensile|tail|djinn|acid|spines"),
    ("survival-saves-and-rerolls", r"natural-armour|ward|regenerat|save|reroll|parry|dodge|step-aside|shield|scryer|deflect|sidestep|reflexes|iron-fan|wall-of-steel|invincible|estalian|main-gauche|whip-master|excellent"),
)
CONDITION = re.compile(r"^condition\.")
EQUIPMENT = re.compile(r"^(weapon|armour|defence|material|poison|preparation)\.")
CONSTRUCTION_EQUIPMENT = re.compile(r"equipment|loadout|forbid|kit|fixed-equipment|tracker-gear|weapon-knowledge|access-to|slayer-identity")
TARGET, SPLIT, LARGE_GROUP = 50.0, 70.0, 30

ORDER = ("triage-blockers", "psy-immunities", "psy-tests-and-enemy-effects", "hatred-frenzy-and-charge-rages",
         "leadership", "survival-injury-and-immunity", "survival-saves-and-rerolls", "supplied-conditions",
         "equipment-items", "construction-equipment", "construction-skills-and-profile",
         "operators-hirelings", "operators-band-rules")

# A hireling profile that the construction layer refuses for want of KB data (its kit or its
# duel profile) blocks every identity it carries; other refusals need a scenario input instead.
UNCOMPILABLE_MARKERS = ("canonical combat mapping", "canonical duel profile", "complete legal printed kit")


def _yaml(path: pathlib.Path):
    return read_yaml(path)


def _execution_entries() -> dict:
    doc = _yaml(KB / "catalog/mechanics/execution.yaml")
    return {str(row["id"]): row for rows in doc.values() if isinstance(rows, list)
            for row in rows if isinstance(row, dict) and "id" in row}


def _engine_text() -> str:
    """Every consumer that may read an execution tag: the engines and the construction compiler."""
    paths = [*ENGINE.rglob("*.py"), *ENGINE.rglob("*.pyx"), *CONSTRUCTION.rglob("*.py"), *CONSTRUCTION.rglob("*.js")]
    return "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in paths)


def _find_rule(doc: dict, rule_id: str) -> dict | None:
    for row in (doc.get("rules") or []) + (doc.get("skills") or []):
        if isinstance(row, dict) and row.get("id") == rule_id:
            return row
    for profile in doc.get("profiles") or []:
        for row in profile.get("rules") or []:
            if isinstance(row, dict) and row.get("id") == rule_id:
                return row
    return None


_COMPILE_CACHE: dict[str, str | None] = {}


def _hireling_blocker(profile_id: str) -> str | None:
    """The construction refusal of a hireling profile built with no options, if it is a KB gap."""
    if profile_id not in _COMPILE_CACHE:
        from mordheim_core.models import FighterBuild
        from mordheim_construction.compiler import compile_fighter
        from mordheim_knowledge.campaign import load_hirelings
        profile = next((p for p in load_hirelings("mordheim").profiles if p["id"] == profile_id), None)
        blocker = None
        if profile is not None:
            band = f"hirelings.{profile['kind']}.{profile.get('grade') or 'core'}"
            try:
                compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile_id, collection="mordheim"))
            except Exception as error:  # noqa: BLE001 - classify the refusal by its message
                message = str(error).splitlines()[0]
                if any(marker in message for marker in UNCOMPILABLE_MARKERS):
                    blocker = message.split("Error: ")[-1][:160]
        _COMPILE_CACHE[profile_id] = blocker
    return _COMPILE_CACHE[profile_id]


def _condition_effects() -> dict:
    """Condition records whose duel content is carried by sibling effects with their own bindings."""
    doc = _yaml(KB / "catalog/rules/conditions.yaml")
    rows = next((v for v in doc.values() if isinstance(v, list)), []) if isinstance(doc, dict) else []
    carried = set()
    for row in rows:
        effects = (row.get("runtime") or {}).get("effects") or []
        if any(e.get("id") != row.get("id") and e.get("scope") == "YES" and e.get("binding") for e in effects):
            carried.add(str(row.get("id")))
    return carried


def backlog() -> list[dict]:
    """One record per admitted identity without a scenario."""
    definitions = read_definitions(KB)
    covered: set[str] = set()
    for path in CASES.rglob("*.yaml"):
        covered |= declared_identities(path)
    entries = _execution_entries()
    engine = _engine_text()
    mechanics_doc = _yaml(KB / "catalog/mechanics/close-combat.yaml")
    families = {str(row["id"]): family for family, rows in mechanics_doc.items() if isinstance(rows, list)
                for row in rows if isinstance(row, dict) and "id" in row}
    sections = {str(row["id"]): str(((row.get("source_refs") or [{}])[0] or {}).get("section") or "")
                for rows in mechanics_doc.values() if isinstance(rows, list)
                for row in rows if isinstance(row, dict) and "id" in row}
    carried = _condition_effects()
    docs: dict[str, dict] = {}
    covered_bindings: set[str] = set()
    records = []
    for identity, record in definitions.items():
        if identity.startswith("core/"):
            continue
        row = {"identity": identity, "kind": record.kind, "file": "tests/conformance/cases/" + relative_path(identity).as_posix(),
               "source": record.source_file, "covered": identity in covered}
        if record.kind == "rule":
            _, collection, owner, rule_id, effect_id = identity.split("/", 4)
            doc = docs.setdefault(record.source_file, _yaml(KB / record.source_file))
            rule = _find_rule(doc, rule_id) or {}
            runtime = rule.get("runtime") or {}
            effect = next((e for e in runtime.get("effects") or [] if str(e.get("id")) == effect_id), {})
            binding = effect.get("binding") or {}
            row.update(collection=collection, owner=owner, rule_id=rule_id, binding=str(binding.get("id") or ""),
                       binding_kind=str(binding.get("kind") or ""), grant=str(runtime.get("grant") or ""),
                       hireling=owner in ("hired-swords", "dramatis-personae"),
                       section=str((rule.get("source") or {}).get("section") or (rule.get("source_refs") or [{}])[0].get("section") or ""))
            if identity in covered and row["binding"]:
                covered_bindings.add(row["binding"])
        else:
            mechanic = identity.split("/", 1)[1]
            entry = entries.get(mechanic) or {}
            tags = (entry.get("parameters") or {}).get("tags") or []
            row.update(binding=mechanic, binding_kind="mechanic", family=families.get(mechanic, ""),
                       hireling=False, params=sorted((entry.get("parameters") or {}).keys()),
                       section=sections.get(mechanic, ""),
                       engine_reads_tag=mechanic in carried or any(tag in engine for tag in [mechanic, *tags]))
            if identity in covered:
                covered_bindings.add(mechanic)
        records.append(row)
    uncovered = [row for row in records if not row["covered"]]
    for row in uncovered:
        row["model_exists"] = row["binding"] in covered_bindings
    return uncovered


def _route(row: dict) -> str:
    if row["kind"] == "mechanic":
        if EQUIPMENT.match(row["binding"]):
            return "equipment slot"
        if CONDITION.match(row["binding"]):
            return "condition_ids"
        return "skill_ids on a hand-built fighter"
    if row["binding_kind"] in ("profile", "compiler"):
        return "construction (admission/refusal pair)"
    if CONDITION.match(row["binding"]):
        return "condition_ids / supplied input"
    if EQUIPMENT.match(row["binding"]):
        return "equipment slot"
    if row["grant"] == "selectable":
        return "special_rule_ids on the real profile"
    if row["grant"] == "none":
        return "supplied input"
    return "real profile build (automatic grant)"


def _triage_reason(row: dict) -> str | None:
    path = REPO / row["file"]
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if "# authoring_status: PARTIAL" in text:
        return "PARTIAL file with a recorded blocker"
    if row["kind"] == "mechanic" and not row["engine_reads_tag"] and set(row["params"]) <= {"tags"}:
        return "no engine code reads the execution tag"
    if row.get("hireling"):
        profile_id = re.sub(r"\.(rule|skill|patron|item)\..*$", "", row.get("rule_id", ""))
        if _hireling_blocker(profile_id):
            return "hireling profile does not compile"
    return None


def _theme(row: dict) -> str:
    binding = row["binding"]
    if row["kind"] == "rule" and row["binding_kind"] in ("profile", "compiler"):
        return "construction-equipment" if CONSTRUCTION_EQUIPMENT.search(binding) else "construction-skills-and-profile"
    if CONDITION.match(binding):
        return "supplied-conditions"
    if EQUIPMENT.match(binding):
        return "equipment-items"
    for name, pattern in THEMES:
        if re.search(pattern, binding):
            return name
    return "operators-hirelings" if row.get("hireling") else "operators-band-rules"


def groups(rows: list[dict]) -> list[dict]:
    """Printed-rule groups: identities that share a binding (mechanic plus its rules)."""
    by_binding: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        by_binding[row["binding"] or row["identity"]].append(row)
    # One printed rule spread over several mechanics (Disability 1-6, Fungus Brew, Petru...) is
    # one family: the mechanics of a shared printed source section travel together.
    by_section: dict[str, list[str]] = collections.defaultdict(list)
    for binding, members in by_binding.items():
        section = next((m.get("section") for m in members if m["kind"] == "mechanic" and m.get("section")), "")
        if section:
            by_section[section].append(binding)
    for section, bindings in by_section.items():
        if len(bindings) > 1:
            merged = [m for b in sorted(bindings) for m in by_binding.pop(b)]
            by_binding[f"{sorted(bindings)[0]} (+{len(bindings) - 1} of {section})"] = merged
    result = []
    for binding, members in list(by_binding.items()):
        members.sort(key=lambda r: (r["kind"] != "mechanic", r["identity"]))
        if len(members) > LARGE_GROUP and all(m["model_exists"] for m in members):
            # Independent substitutions of one authored model: split by collection so
            # one batch does not swallow the whole component.
            by_collection: dict[str, list[dict]] = collections.defaultdict(list)
            for member in members:
                by_collection[member.get("collection") or "mechanic"].append(member)
            for collection, part in sorted(by_collection.items()):
                result.append(_group(f"{binding} [{collection}]", part, _theme(part[0]), []))
            continue
        triage = [(_triage_reason(m)) for m in members]
        themes = collections.Counter(_theme(m) for m in members)
        theme = "triage-blockers" if any(triage) and not any(m["model_exists"] for m in members) else themes.most_common(1)[0][0]
        if any(triage) and theme != "triage-blockers":
            # Blocked members travel to triage; the rest of the group keeps its theme.
            blocked = [m for m, t in zip(members, triage) if t]
            members = [m for m, t in zip(members, triage) if not t]
            result.append(_group(binding + " (blocked)", blocked, "triage-blockers", [t for t in triage if t]))
            if not members:
                continue
            triage = [None] * len(members)
        result.append(_group(binding, members, theme, [t for t in triage if t]))
    return result


def _group(binding: str, members: list[dict], theme: str, triage: list[str]) -> dict:
    model = any(m["model_exists"] for m in members)
    effort = 0.0
    for index, member in enumerate(members):
        if triage:
            effort += 2.0
        elif member.get("binding_kind") in ("profile", "compiler"):
            effort += 1.5
        elif model or index > 0:
            effort += 1.0
        else:
            effort += 4.0
    # The one-off operators of the band collections are grouped by owner so one source read serves several.
    hireling = sum(1 for m in members if m.get("hireling"))
    if theme.startswith("operators"):
        theme = "operators-hirelings" if hireling * 2 >= len(members) else "operators-band-rules"
    return {"binding": binding, "theme": theme, "effort": effort, "model": model, "triage": sorted(set(triage)),
            "members": [{"identity": m["identity"], "file": m["file"], "route": _route(m),
                         "source": m["source"], "model_exists": m["model_exists"]} for m in members]}


def batches() -> list[dict]:
    rows = backlog()
    by_theme: dict[str, list[dict]] = collections.defaultdict(list)
    for group in groups(rows):
        by_theme[group["theme"]].append(group)
    # A theme too small for a batch of its own joins the next theme of the order.
    for index, theme in enumerate(ORDER[1:-1], 1):
        if 0 < sum(g["effort"] for g in by_theme.get(theme, [])) < TARGET / 3:
            by_theme[ORDER[index + 1]] = by_theme.pop(theme) + by_theme.get(ORDER[index + 1], [])
    result = []
    for theme in ORDER:
        pending = sorted(by_theme.get(theme, []), key=lambda g: (-len(g["members"]), g["binding"]))
        if not pending:
            continue
        total = sum(g["effort"] for g in pending)
        count = max(1, round(total / TARGET)) if total >= SPLIT else 1
        buckets: list[list[dict]] = [[] for _ in range(count)]
        loads = [0.0] * count
        for group in pending:  # largest first, into the lightest bucket
            index = loads.index(min(loads))
            buckets[index].append(group)
            loads[index] += group["effort"]
        for part, bucket in enumerate(buckets, 1):
            if not bucket:
                continue
            name = theme if count == 1 else f"{theme}-{part}"
            members = [m for g in bucket for m in g["members"]]
            result.append({"batch": name, "theme": theme, "identities": len(members),
                           "with_model": sum(1 for m in members if m["model_exists"]),
                           "effort": round(sum(g["effort"] for g in bucket), 1),
                           "routes": dict(collections.Counter(m["route"] for m in members).most_common()),
                           "groups": bucket})
    for index, batch in enumerate(result):
        batch["id"] = f"B{index:02d}"
    return result


def table(plan: list[dict]) -> str:
    lines = ["| Batch | Theme | Ids | Model | Effort | Routes |", "| --- | --- | ---: | ---: | ---: | --- |"]
    for batch in plan:
        short: dict[str, int] = collections.Counter()
        for route, n in batch["routes"].items():
            short[route.split(" (")[0].split(" on ")[0].split(" / ")[0]] += n
        routes = ", ".join(f"{route} {n}" for route, n in short.most_common())
        lines.append(f"| {batch['id']} | {batch['batch']} | {batch['identities']} | {batch['with_model']} | {batch['effort']:g} | {routes} |")
    total = sum(b["identities"] for b in plan)
    lines.append(f"| | **Total** | **{total}** | {sum(b['with_model'] for b in plan)} | {sum(b['effort'] for b in plan):g} | |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--table", action="store_true", help="print the markdown table for TODO.md")
    parser.add_argument("--out", type=pathlib.Path, help="write batches.json and one <id>.ids.txt per batch here")
    parser.add_argument("--batch", help="print the member identities of one batch (its id, e.g. B03)")
    args = parser.parse_args(argv)
    plan = batches()
    if args.table or not (args.out or args.batch):
        print(table(plan))
    if args.batch:
        chosen = next((b for b in plan if b["id"] == args.batch.upper()), None)
        if chosen is None:
            parser.error(f"unknown batch {args.batch}; known: {', '.join(b['id'] for b in plan)}")
        for group in chosen["groups"]:
            for member in group["members"]:
                print(member["identity"])
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "batches.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
        for batch in plan:
            (args.out / f"{batch['id']}.ids.txt").write_text(
                "".join(m["identity"] + "\n" for g in batch["groups"] for m in g["members"]), encoding="utf-8")
        print(f"wrote {args.out / 'batches.json'} and {len(plan)} id lists", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
