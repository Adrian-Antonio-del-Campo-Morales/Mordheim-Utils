"""Synthetic, seeded population of realistic close-combat duels.

There is no usage data yet, so the population encodes the game expert's
answers (2026-11-09) on top of the roster and equipment catalogues:

* Warband: uniform over every Mordheim and Trollheim band, all grades.
  Hired Swords and Dramatis Personae are left out.
* Fighter: within the band, each roster member is weighted by how many of it a
  warband can field (``maximum``; an unlimited henchman is capped by the
  band's model limit, a group by its group size). Large creatures are rare
  because they are limited to one.
* Campaign stage: a campaign lasts 4-8 games and the duel happens in a uniform
  game of it; only game 1 is a fresh 500 gc fighter.  Heroes gain on average
  under three advances (Poisson, ``HERO_ADVANCES_PER_GAME`` per played game)
  with a tail above five; henchmen gain half as many, at most +1 per
  characteristic and four advances.  Results follow the printed advance
  tables and stop at the racial maximum.
* Skills: drawn among the skills that matter in a duel and the profile can
  learn; Resilient, Step Aside and Mighty Blow are much more frequent.
* Equipment: weapons are weighted by how many profiles can take them; two
  weapons dominate, the dagger is the most common weapon, two-handed weapons
  and shields are rarer and armour is uncommon.
* Every duel starts with a charge by one of the fighters (random side).

``generate`` writes readable build specs (not compiled blobs) so the population
Advances are the one fact the construction compiler has no input channel for:
a campaign increase is applied to the compiled characteristics afterwards,
bounded by the racial maximum, never by inventing a rule.

The population itself is only the reference.  ``curate`` picks from it the two
frozen sets a performance run uses -- ``realistic-50`` inside
``realistic-100`` -- choosing the duels whose feature shares track the
population, so a plain mean over a set needs no weighting.  ``--write``
freezes them: the duels are added to the precompiled corpus through the one
exporter, the ``--scenarios`` registry is rewritten and the reviewable
population is written beside the baselines.

    python -m tools.verification.realistic_population --draws 1200 --seed 1 --write
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import json
import math
from pathlib import Path
import random
from typing import Mapping, Sequence

import yaml

from mordheim_core.models import DuelContext, FighterBuild

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "sources/knowledge"
CORPUS = ROOT / "tests/engines/fixtures/compiled-cases.json"
REGISTRY = ROOT / "tests/engines/fixtures/realistic_sets.py"
REFERENCE = ROOT / "benchmarks/reference/realistic-population.json"
GENERATOR_PATH = "tools/verification/realistic_population.py"
COLLECTIONS = ("mordheim", "trollheim")

#: The curated sets, smallest first; the smaller is a subset of the larger.
SET_SIZES = (50, 100)
KEY_PREFIX = "realistic/"
MAXIMUM_ROUNDS = 50

HERO_ADVANCES_PER_GAME = 0.7
HENCHMAN_ADVANCE_FACTOR = 0.5
HENCHMAN_MAX_ADVANCES = 4
UNLIMITED_FALLBACK = 5
LOADOUT_ATTEMPTS = 5

# Duel-relevant general skills; weight 8 marks the expert's "much more frequent".
SKILL_WEIGHTS = {
    "skill.resilient": 8, "skill.step-aside": 8, "skill.mighty-blow": 8,
    "skill.expert-swordsman": 1, "skill.jump-up": 1, "skill.lightning-reflexes": 1,
    "skill.strike-to-injure": 1, "skill.strongman": 1, "skill.unstoppable-charge": 1,
    "skill.web-of-steel": 1, "skill.fearsome": 1,
}
# Loadout shapes: two weapons dominate; 2H and shields are rarer.
LOADOUTS = {"paired": 0.60, "single": 0.20, "shield": 0.12, "two-handed": 0.08}
OFF_HAND_DAGGER = 0.6
ARMOUR = {"armour.light-armour": 0.12, "armour.heavy-armour": 0.03}
HELMET = 0.10
STATS = {"WS": "weapon_skill", "S": "strength", "T": "toughness", "W": "wounds",
         "I": "initiative", "A": "attacks", "Ld": "leadership"}
LONG = {v: k for k, v in STATS.items()}


def _yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _racial_maximums():
    data = _yaml(KNOWLEDGE / "catalog/rules/racial-maximums.yaml")["racial_maximums"]
    groups = _yaml(KNOWLEDGE / "registry/warband-groups.yaml")["groups"]
    band_groups: dict[str, list[str]] = {}
    for group in groups:
        if group.get("kind") == "race":
            for band in group.get("band_ids", ()):
                band_groups.setdefault(band, []).append(group["id"])
    by_profile, by_group = {}, {}
    for entry in data:
        caps = {k: v for k, v in entry["characteristics"].items() if k in LONG}
        for key in entry.get("profile_keys") or ():
            by_profile[(key["band_id"], key["profile_id"])] = caps
        for group in entry.get("groups") or ():
            by_group.setdefault(group, caps)
    human = next(e for e in data if e["profile"] == "human")
    human = {k: v for k, v in human["characteristics"].items() if k in LONG}

    def caps(band: str, profile: str, base: dict[str, int]) -> dict[str, int]:
        found = by_profile.get((band, profile))
        if found is None:
            found = next((by_group[g] for g in band_groups.get(band, ()) if g in by_group), None)
        if found is None:  # unknown race: humans, but never below the printed profile
            found = human
        return {stat: max(found.get(stat, base[stat]), base[stat]) for stat in base}
    return caps


def _mappings():
    from mordheim_construction.compiler import _catalogue, mechanic_index
    return (_catalogue("mordheim", "mordheim", None)["mappings"],
            mechanic_index("mordheim", None))


def roster_catalogue():
    """Every (band, profile) member with its weight, profile data and kit options."""
    mappings, mechanics = _mappings()
    caps = _racial_maximums()
    members = []
    for collection in COLLECTIONS:
        for folder in sorted((KNOWLEDGE / "bands" / collection).iterdir()):
            if not (folder / "band.yaml").exists():
                continue
            band = _yaml(folder / "band.yaml")
            profiles = {p["id"]: p for p in _yaml(folder / "profiles.yaml")["profiles"]}
            access_path = folder / "equipment-access.yaml"
            lists = {}
            if access_path.exists():
                lists = {entry["id"]: [item["item_id"] for item in entry.get("items", ())]
                         for entry in _yaml(access_path).get("equipment_lists") or ()}
            roster = band.get("roster") or {}
            band_cap = roster.get("maximum_models") or 15
            entries = []
            for member in roster.get("members") or ():
                profile = profiles.get(member["profile_id"])
                if profile is None:
                    continue
                maximum = member.get("maximum")
                if maximum is None:
                    group = (member.get("group_size") or {}).get("maximum")
                    maximum = min(band_cap, group or UNLIMITED_FALLBACK)
                if not maximum:
                    continue
                items = {mappings[i] for name in profile.get("equipment_lists") or ()
                         for i in lists.get(name, ()) if i in mappings}
                base = {stat: profile["characteristics"].get(short)
                        for short, stat in STATS.items()}
                if not all(isinstance(v, int) for v in base.values()):
                    caps_for = None  # random/unknown profile: no advances
                else:
                    caps_for = caps(band["id"], profile["id"], base)
                entries.append({
                    "collection": collection, "band_id": band["id"],
                    "profile_id": profile["id"], "count": maximum,
                    "kind": profile.get("type", "henchman"),
                    "hero": _is_hero(member, profile),
                    "skill_access": set(profile.get("skill_access") or ()),
                    # Sorted: a set iterates in hash-seed order, which would make
                    # the seeded draws differ from one process to the next.
                    "items": sorted(items), "base": base, "caps": caps_for,
                })
            if entries:
                members.append(entries)
    weapons = Counter(item for band in members for m in band for item in m["items"])
    return members, weapons, mechanics


def _is_hero(member, profile) -> bool:
    # ``type: hero`` is unreliable in the data: a member that can be fielded
    # more than twice or in groups is a henchman whatever its label says.
    if profile.get("type") == "animal":
        return False
    if member.get("group_size") or member.get("maximum") is None or member["maximum"] > 2:
        return False
    return profile.get("type") == "hero"


def _advances(rng: random.Random, member) -> int:
    if member["caps"] is None or member["kind"] == "animal":
        return 0
    length = rng.randint(4, 8)
    played = rng.randint(1, length) - 1
    rate = HERO_ADVANCES_PER_GAME * played
    if not member["hero"]:
        rate *= HENCHMAN_ADVANCE_FACTOR
    count = _poisson(rng, rate)
    return count if member["hero"] else min(count, HENCHMAN_MAX_ADVANCES)


def _poisson(rng: random.Random, mean: float) -> int:
    limit, k, product = math.exp(-mean), 0, rng.random()
    while product > limit:
        k += 1
        product *= rng.random()
    return k


def _hero_advance(rng, stats, caps, skills, learnable):
    roll = rng.randint(1, 6) + rng.randint(1, 6)
    if roll == 6:
        choice = "strength" if rng.randint(1, 6) <= 3 else "attacks"
    elif roll == 7:
        choice = "weapon_skill"  # a melee duel is the subject: WS over BS
    elif roll == 8:
        choice = "initiative" if rng.randint(1, 6) <= 3 else "leadership"
    elif roll == 9:
        choice = "wounds" if rng.randint(1, 6) <= 3 else "toughness"
    else:
        options = [s for s in learnable if s not in skills]
        if options:
            skills.append(rng.choices(options, [SKILL_WEIGHTS[s] for s in options])[0])
        return
    if stats[choice] < caps[choice]:
        stats[choice] += 1


def _henchman_advance(rng, stats, caps, raised):
    for _ in range(20):  # re-roll an already raised or capped characteristic
        roll = rng.randint(1, 6) + rng.randint(1, 6)
        choice = ("initiative" if roll <= 4 else "strength" if roll == 5 else
                  "weapon_skill" if roll <= 7 else "attacks" if roll == 8 else
                  "leadership" if roll == 9 else None)  # 10-12: promotion, ignored
        if choice is None:
            return
        if choice not in raised and stats[choice] < caps[choice]:
            stats[choice] += 1
            raised.add(choice)
            return


def _loadout(rng: random.Random, member, weapons, mechanics):
    items = member["items"]
    if not items or member["kind"] == "animal":
        return {}
    one_handed = [i for i in items if mechanics.get(i, {}).get("hands") == 1
                  and mechanics[i].get("main_hand")]
    off_hand = [i for i in items if mechanics.get(i, {}).get("off_hand")]
    two_handed = [i for i in items if mechanics.get(i, {}).get("hands") == 2]
    shields = [i for i in ("defence.shield", "defence.buckler") if i in items]
    pick = lambda pool: rng.choices(pool, [weapons[i] for i in pool])[0]
    shapes = {k: w for k, w in LOADOUTS.items()
              if (k != "two-handed" or two_handed) and (k != "shield" or shields)
              and (k != "paired" or off_hand)}
    shape = rng.choices(list(shapes), list(shapes.values()))[0]
    kit: dict[str, object] = {}
    if shape == "two-handed":
        kit["main_weapon_id"] = pick(two_handed)
    else:
        kit["main_weapon_id"] = pick(one_handed) if one_handed else "weapon.dagger"
        if shape == "paired":
            kit["off_hand_id"] = ("weapon.dagger" if rng.random() < OFF_HAND_DAGGER
                                  or not off_hand else pick(off_hand))
        elif shape == "shield":
            kit["off_hand_id"] = rng.choice(shields)
    for armour, chance in ARMOUR.items():
        if armour in items and rng.random() < chance:
            kit["armour_id"] = armour
            break
    if "defence.helmet" in items and rng.random() < HELMET:
        kit["defence_ids"] = ["defence.helmet"]
    return kit


def _fighter(rng, catalogue, weapons, mechanics, rejected: Counter):
    """Draw a band and member, then retry illegal loadouts for that member."""
    while True:
        band = rng.choice(catalogue)
        member = rng.choices(band, [m["count"] for m in band])[0]
        advances = _advances(rng, member)
        stats, skills = dict(member["base"]), []
        learnable = [s for s, category in _skill_categories().items()
                     if category in member["skill_access"]]
        raised: set[str] = set()
        for _ in range(advances):
            if member["hero"]:
                _hero_advance(rng, stats, member["caps"], skills, learnable)
            else:
                _henchman_advance(rng, stats, member["caps"], raised)
        increases = {stat: stats[stat] - member["base"][stat] for stat in stats
                     if stats[stat] != member["base"][stat]}
        for _ in range(LOADOUT_ATTEMPTS):
            build = {"collection": member["collection"], "band_id": member["band_id"],
                     "profile_id": member["profile_id"],
                     **_loadout(rng, member, weapons, mechanics)}
            if skills:
                build["skill_ids"] = list(skills)
            spec = {"build": build, "hero": member["hero"], "advances": advances,
                    "increases": increases}
            try:
                return spec, compile_spec(spec)
            except Exception as error:
                rejected[f"compile: {type(error).__name__}: {str(error)[:100]}"] += 1


_SKILL_CATEGORIES: dict[str, str] | None = None


def _skill_categories() -> dict[str, str]:
    global _SKILL_CATEGORIES
    if _SKILL_CATEGORIES is None:
        skills = _yaml(KNOWLEDGE / "catalog/skills/general.yaml")["skills"]
        _SKILL_CATEGORIES = {s["id"]: s["category"] for s in skills if s["id"] in SKILL_WEIGHTS}
    return _SKILL_CATEGORIES


def compile_spec(spec):
    """One fighter spec -> CompiledFighter with its advances applied."""
    from mordheim_construction.compiler import compile_fighter

    build = dict(spec["build"])
    for key in ("skill_ids", "defence_ids"):
        if key in build:
            build[key] = tuple(build[key])
    fighter = compile_fighter(FighterBuild("mordheim", **build))
    if spec["increases"]:
        characteristics = fighter.characteristics
        characteristics = replace(characteristics, **{
            stat: getattr(characteristics, stat) + amount
            for stat, amount in spec["increases"].items()})
        fighter = replace(fighter, characteristics=characteristics)
    return fighter


def _context(charger: str) -> DuelContext:
    return DuelContext(charging=(charger,), active_participant=charger)


def _runs(first, second, context) -> str | None:
    """None when the engine accepts the pair, else the refusal."""
    from mordheim_core.models import DuelRequest
    from mordheim_combat.vectorized import simulate_duel

    try:
        simulate_duel(DuelRequest(first, second, 64, seed=0, batch_size=64,
                                  context=context), backend="numpy")
    except Exception as error:  # engine refusal: resample
        return f"{type(error).__name__}: {error}"[:160]
    return None


def draw_population(draws: int, seed: int):
    """``(duels, rejected)``: ``draws`` runnable duels with their compiled pair."""
    rng = random.Random(seed)
    catalogue, weapons, mechanics = roster_catalogue()
    population, rejected = [], Counter()
    while len(population) < draws:
        (spec_a, first), (spec_b, second) = (
            _fighter(rng, catalogue, weapons, mechanics, rejected) for _ in range(2))
        charger = rng.choice(("first", "second"))
        refusal = _runs(first, second, _context(charger))
        if refusal:
            rejected[f"engine: {refusal[:120]}"] += 1
            continue
        population.append({"first": spec_a, "second": spec_b, "charging": charger,
                           "compiled": (first, second)})
    return population, rejected


# --------------------------------------------------------------------------
# Curation: the traits a duel's engine work actually depends on.
# --------------------------------------------------------------------------

def features(duel) -> dict[str, float]:
    """Indicators the curated sets must reproduce, as 0/1 per duel."""
    first, second = duel["compiled"]
    specs = (duel["first"], duel["second"])
    pair = (first, second)
    heroes = sum(spec["hero"] for spec in specs)
    wounds = max(f.characteristics.wounds for f in pair)
    attacks = max(f.characteristics.attacks for f in pair)
    strength = max(f.characteristics.strength for f in pair)
    toughness = max(f.characteristics.toughness for f in pair)
    builds = [spec["build"] for spec in specs]
    off_hands = [build.get("off_hand_id") for build in builds]
    mains = [build.get("main_weapon_id") for build in builds]
    return {
        "heroes-0": heroes == 0, "heroes-1": heroes == 1, "heroes-2": heroes == 2,
        "wounds-1": wounds == 1, "wounds-2": wounds == 2, "wounds-3+": wounds >= 3,
        "attacks-2+": attacks >= 2,
        "paired": any(o and o.startswith("weapon.") for o in off_hands),
        "shield": any(o and o.startswith("defence.") for o in off_hands),
        "two-handed": any(m == "weapon.double-handed-weapon" for m in mains),
        "single": any(o is None for o in off_hands),
        "dagger": any(m == "weapon.dagger" for m in mains),
        "armour": any("armour_id" in build for build in builds),
        "helmet": any("defence_ids" in build for build in builds),
        "skills": any(build.get("skill_ids") for build in builds),
        "advanced": any(spec["increases"] for spec in specs),
        "trollheim": any(build["collection"] == "trollheim" for build in builds),
        "large": strength >= 5 or toughness >= 5 or wounds >= 3,
        "natural-armour": any(f.natural_armour_save < 7 for f in pair),
        "injury-profile": any(f.injury_profile for f in pair),
        "parry": any(f.main_weapon.parry or (f.off_hand.parry if f.off_hand else False)
                     for f in pair),
        "ward-save": any(f.global_effects.ward_save < 7 for f in pair),
        "concussion": any(f.main_weapon.concussion for f in pair),
    }


def _signature(duel) -> tuple:
    def side(spec):
        build = spec["build"]
        return (build["band_id"], build["profile_id"], build.get("main_weapon_id"),
                build.get("off_hand_id"), build.get("armour_id"),
                tuple(build.get("skill_ids", ())), tuple(sorted(spec["increases"].items())))
    return tuple(sorted((side(duel["first"]), side(duel["second"]))))


def curate(population, size: int, *, within=None) -> list[int]:
    """Indices of ``size`` duels whose feature shares track the population.

    Greedy: repeatedly take the candidate that most reduces the total absolute
    distance between the selected shares and the population shares, breaking
    ties towards unused warbands so the set stays diverse.  ``within`` limits
    the candidates to an already curated set, which is how the smaller set
    stays a subset of the larger one.
    """
    rows = [features(duel) for duel in population]
    names = list(rows[0])
    target = {name: sum(row[name] for row in rows) / len(rows) for name in names}
    candidates = list(range(len(population))) if within is None else list(within)
    chosen: list[int] = []
    totals = dict.fromkeys(names, 0.0)
    seen_signatures, bands = set(), Counter()

    def distance(extra: int) -> float:
        count = len(chosen) + 1
        return sum(abs((totals[name] + rows[extra][name]) / count - target[name])
                   for name in names)

    while len(chosen) < size and candidates:
        best = None
        for index in candidates:
            signature = _signature(population[index])
            if signature in seen_signatures:
                continue
            used = sum(bands[population[index][side]["build"]["band_id"]]
                       for side in ("first", "second"))
            key = (round(distance(index), 9), used, index)
            if best is None or key < best[0]:
                best = (key, index, signature)
        if best is None:
            break
        _key, index, signature = best
        chosen.append(index)
        candidates.remove(index)
        seen_signatures.add(signature)
        for side in ("first", "second"):
            bands[population[index][side]["build"]["band_id"]] += 1
        for name in names:
            totals[name] += rows[index][name]
    return chosen


def fidelity(population, sets: Mapping[str, Sequence[int]]) -> str:
    """How closely each curated set reproduces the population's shares."""
    rows = [features(duel) for duel in population]
    names = list(rows[0])
    share = lambda indices, name: 100 * sum(rows[i][name] for i in indices) / len(indices)
    header = f"{'feature':<16}{'population':>11}" + "".join(f"{name:>12}" for name in sets)
    lines = [header, "-" * len(header)]
    everything = range(len(population))
    for name in names:
        base = share(everything, name)
        cells = "".join(f"{share(indices, name) - base:>+11.1f}%" for indices in sets.values())
        lines.append(f"{name:<16}{base:>10.1f}%{cells}")
    worst = max(
        abs(share(indices, name) - share(everything, name))
        for indices in sets.values() for name in names
    )
    lines.append(f"worst deviation {worst:.1f} points")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Corpus export
# --------------------------------------------------------------------------

def _case_spec(key: str, duel) -> dict:
    first, second = duel["compiled"]
    return {
        "case_key": key,
        "origin": {"kind": "benchmark", "node_id": key, "path": GENERATOR_PATH},
        "fighters": {"first": first, "second": second},
        "context": _context(duel["charging"]),
        "limits": {"simulations": None, "seed": None, "batch_size": None,
                   "maximum_rounds": MAXIMUM_ROUNDS},
    }


def _existing_spec(case) -> dict:
    """One already frozen case, re-expressed as an exporter input."""
    return {
        "case_key": case.case_key,
        "origin": {"kind": case.origin.kind, "node_id": case.origin.node_id,
                   "path": case.origin.path, "sha256": case.origin.sha256},
        "fighters": {"first": case.first, "second": case.second},
        "context": case.context,
        "auxiliary_participants": list(case.auxiliary_participants),
        "initial_state": case.initial_state,
        "dice": list(case.dice), "decisions": list(case.decisions),
        "limits": {"simulations": case.limits.simulations, "seed": case.limits.seed,
                   "batch_size": case.limits.batch_size,
                   "maximum_rounds": case.limits.maximum_rounds},
        "benchmark": case.benchmark, "expectations": case.expectations,
    }


def write_corpus(population, keys: Sequence[str], indices: Sequence[int]) -> str:
    """Add the curated duels to the frozen corpus through the only exporter.

    Every case already in the corpus is re-expressed from its decoded form, so
    the document stays a single exporter product and the existing fingerprints
    are reproduced rather than edited.
    """
    import json as _json

    from tools.knowledge.export_compiled_cases import export_cases
    from tools.verification.compiled_cases import load_cases

    document = _json.loads(CORPUS.read_text(encoding="utf-8"))
    cases = load_cases(CORPUS)
    kept = [_existing_spec(case) for case in cases.values()
            if not case.case_key.startswith(KEY_PREFIX)]
    added = [_case_spec(key, population[index]) for key, index in zip(keys, indices)]
    plan = {"cases": [*kept, *added], "revision": document["source"]["revision"],
            "files": document["source"]["files"]}
    receipt = export_cases(plan, kb_root=KNOWLEDGE, destination=CORPUS)
    return f"corpus {receipt.case_count} cases ({len(added)} realistic), {CORPUS}"


def write_registry(sets: Mapping[str, Sequence[str]], seed: int, draws: int) -> str:
    """Rewrite the frozen registry the ``--scenarios`` vocabulary reads."""
    lines = [
        '"""The curated realistic duel sets, as ``--scenarios`` values.',
        "",
        "Frozen selection, not a sampler: the keys below address cases already in",
        "``tests/engines/fixtures/compiled-cases.json``, so a tool runs them without",
        "compiling a fighter.  ``realistic-50`` is contained in ``realistic-100``,",
        "the way the precompiled levels are cumulative.",
        "",
        f"Both sets were curated by ``tools/verification/realistic_population.py``",
        f"(seed {seed}, {draws} draws) to reproduce the feature shares of a",
        "synthetic population built from the rosters, the equipment lists and a",
        "game expert's answers on how Mordheim is actually played.  Regenerating",
        "with the same seed reproduces this file.",
        '"""',
        "from __future__ import annotations",
        "",
        "",
        "#: Set name to its case keys, in curation order; cumulative.",
        "REALISTIC_SETS: dict[str, tuple[str, ...]] = {",
    ]
    for name, keys in sets.items():
        lines.append(f"    {name!r}: (")
        lines.extend(f"        {key!r}," for key in keys)
        lines.append("    ),")
    lines += [
        "}",
        "",
        "#: The selection values this module owns, in containment order.",
        "REALISTIC_LEVELS: tuple[str, ...] = tuple(REALISTIC_SETS)",
        "",
        "",
        "def is_realistic_token(token: str) -> bool:",
        '    """Whether ``token`` names a curated set or one of its cases."""',
        "    return token in REALISTIC_SETS or any(",
        "        token in keys for keys in REALISTIC_SETS.values())",
        "",
        "",
        "def realistic_keys(token: str) -> tuple[str, ...]:",
        '    """The case keys ``token`` selects, in order."""',
        "    if token in REALISTIC_SETS:",
        "        return REALISTIC_SETS[token]",
        "    return (token,)",
        "",
    ]
    REGISTRY.write_text("\n".join(lines), encoding="utf-8")
    return f"registry {REGISTRY}"


def write_reference(population, rejected, sets, seed: int) -> str:
    """The reviewable population and the curation result, outside the suites."""
    chosen = {name: set(indices) for name, indices in sets.items()}
    duels = []
    for index, duel in enumerate(population):
        duels.append({
            "index": index, "charging": duel["charging"],
            "sets": [name for name, indices in chosen.items() if index in indices],
            "features": {name: int(value) for name, value in features(duel).items()},
            "first": {k: v for k, v in duel["first"].items()},
            "second": {k: v for k, v in duel["second"].items()},
        })
    document = {"schema": "mordheim-realistic-population", "schema_version": 2,
                "seed": seed, "duels": duels,
                "rejected": dict(rejected.most_common())}
    REFERENCE.parent.mkdir(parents=True, exist_ok=True)
    REFERENCE.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n",
                         encoding="utf-8")
    return f"reference {len(duels)} draws, {REFERENCE}"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--draws", type=int, default=1200,
                        help="population the curated sets are selected from")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--write", action="store_true",
                        help="write the corpus, the registry and the reference")
    args = parser.parse_args(argv)

    population, rejected = draw_population(args.draws, args.seed)
    large = curate(population, SET_SIZES[-1])
    small = curate(population, SET_SIZES[0], within=large)
    order = {index: position for position, index in enumerate(large)}
    small.sort(key=order.__getitem__)
    keys = {index: f"{KEY_PREFIX}{position:03d}" for position, index in enumerate(large)}
    sets = {f"realistic-{SET_SIZES[0]}": small, f"realistic-{SET_SIZES[-1]}": large}

    print(fidelity(population, sets))
    print(f"\ndrew {len(population)} duels, {sum(rejected.values())} redrawn")
    if not args.write:
        print("nothing written; pass --write to freeze the sets")
        return
    print(write_reference(population, rejected, sets, args.seed))
    print(write_corpus(population, [keys[i] for i in large], large))
    print(write_registry({name: tuple(keys[i] for i in indices)
                          for name, indices in sets.items()}, args.seed, args.draws))


if __name__ == "__main__":
    main()
