"""T13 M5 hatred front: the canonical Hatred bindings of the admitted clauses.

These clauses are data/connection clauses, so the discriminator is the recorded
contract of the printed recipient: the hireling catalogue is read from its
canonical YAML, so a binding that is dropped, pointed at the wrong operator, or
widened past the printed enemy list fails here.  The programme's hiring loader
carries only its own curated 44-rule view, which is why the records are read
from the catalogue documents themselves.

A compile-based witness is deliberately absent.  ``combat_packages`` admits only
the promoted grade-2b hirelings as duel participants, so compiling a grade-1a,
1b, 1c or dramatis-1a/1b profile cannot exhibit a combat tag; that projection gap
stays recorded for the coordinator instead of being asserted as working here.
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
CATALOGUE = ROOT / "sources/knowledge/catalog/hirelings"

PROFILES: dict[str, dict] = {}
RULES: dict[str, dict] = {}
for _path in sorted(CATALOGUE.rglob("*.yaml")):
    _document = yaml.safe_load(_path.read_text(encoding="utf-8"))
    if not isinstance(_document, dict):
        continue
    for _profile in _document.get("profiles") or ():
        PROFILES[_profile["id"]] = _profile
        for _rule in _profile.get("rules") or ():
            RULES[_rule["id"]] = _rule
    for _rule in _document.get("rules") or ():
        RULES.setdefault(_rule["id"], _rule)

# Operators that express a Hatred relationship.  A record may declare one of
# these only for the enemy category it actually selects.
HATRED_PREFIX = "mechanic.hatred-"
HATRED_EXACT = (
    "mechanic.kindred-hatred",
    "mechanic.burn-the-witch",
    "mechanic.profound-hatred",
    "mechanic.ulric-intense-rivals",
    "mechanic.amazon-isolationists",
)


def _profile(profile_id: str) -> dict:
    return PROFILES[profile_id]


def _profile_rules(profile_id: str) -> list[dict]:
    profile = _profile(profile_id)
    records = list(profile.get("rules") or ())
    for rule_id in profile.get("rule_ids") or ():
        if rule_id in RULES and all(row["id"] != rule_id for row in records):
            records.append(RULES[rule_id])
    return records


def _record(profile_id: str, rule_name: str) -> dict:
    rule_id = "%s.rule.%s" % (profile_id, rule_name)
    assert rule_id in {row["id"] for row in _profile_rules(profile_id)}
    return RULES[rule_id]


def _operators(profile_id: str) -> set[str]:
    """Every canonical operator id the profile's own rules declare."""
    declared: set[str] = set()
    for record in _profile_rules(profile_id):
        runtime = (record or {}).get("runtime") or {}
        for effect in runtime.get("effects") or ():
            binding = effect.get("binding") or {}
            if binding.get("id"):
                declared.add(str(binding["id"]))
    return declared


def _hatred_operators(profile_id: str) -> set[str]:
    return {
        operator for operator in _operators(profile_id)
        if operator.startswith(HATRED_PREFIX) or operator in HATRED_EXACT
    }


def _band_rule(path: str, rule_id: str) -> dict:
    document = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    return next(rule for rule in document["rules"] if rule["id"] == rule_id)


# --- Orcs and Goblins -------------------------------------------------------

def test_hate_orcs_and_goblins_is_bound_only_where_the_source_prints_it():
    for profile_id in ("hireling.hired-sword.dwarf-pathfinder",
                       "hireling.hired-sword.dwarf-treasure-hunter"):
        assert "mechanic.hatred-orcs-goblins" in _operators(profile_id)
    # Negative control: the Grave Robber of the same catalogue prints Undead only.
    assert "mechanic.hatred-orcs-goblins" not in _hatred_operators(
        "hireling.hired-sword.grave-robber")


# --- Dark Elves and High Elves (kindred hatred) -----------------------------

def test_dark_elves_and_high_elves_are_distinct_categories():
    assert "mechanic.hatred-dark-elves" in _operators("hireling.hired-sword.shadow-warrior")
    for profile_id in ("hireling.hired-sword.dark-elf-assassin",
                       "hireling.dramatis.dijin-katal-the-renegade-assassin"):
        assert "mechanic.hatred-high-elves" in _operators(profile_id)
    # Negative control: a Dark Elf hater is not a High Elf hater.
    assert "mechanic.hatred-high-elves" not in _hatred_operators(
        "hireling.hired-sword.shadow-warrior")
    assert "mechanic.hatred-dark-elves" not in _hatred_operators(
        "hireling.hired-sword.dwarf-treasure-hunter")


# --- Undead, Ulric and Isolationists ----------------------------------------

def test_undead_ulric_and_isolationist_bindings():
    assert "mechanic.hatred-undead" in _operators("hireling.hired-sword.grave-robber")
    assert "mechanic.ulric-intense-rivals" in _operators("hireling.hired-sword.wolf-priest-of-ulric")
    penthesilea = "hireling.dramatis.penthesilea-mark-of-the-serpent"
    assert "mechanic.amazon-isolationists" in _operators(penthesilea)
    assert "mechanic.hatred-human-warband" in _operators(penthesilea)
    # Negative controls: each printed category stays on its own recipient.
    assert "mechanic.hatred-undead" not in _hatred_operators(
        "hireling.hired-sword.dwarf-pathfinder")
    assert "mechanic.ulric-intense-rivals" not in _hatred_operators(
        "hireling.hired-sword.gaoler")
    assert "mechanic.amazon-isolationists" not in _hatred_operators(
        "hireling.hired-sword.duellist")


# --- The Gaoler's bounded comparison ----------------------------------------

def test_gaoler_keeps_the_exact_undead_half_only():
    """The warband-level Chaotic category is not the printed per-model identity."""
    operators = _operators("hireling.hired-sword.gaoler")
    assert "mechanic.hatred-undead" in operators
    assert "mechanic.hatred-chaotic-warband" not in operators
    record = _record("hireling.hired-sword.gaoler", "hatred")
    unbound = [effect for effect in record["runtime"]["effects"] if effect.get("binding") is None]
    assert len(unbound) == 1
    assert "Chaos" in unbound[0]["reason"]


# --- Clauses that must stay unbound on their bearer -------------------------

def test_target_imposed_and_undefined_hatred_stay_unbound():
    # Traitor imposes Hatred on the opposing greenskin, not on this bearer.
    assert _hatred_operators("hireling.hired-sword.hobgoblin-scout") == set()
    # Fighting Undead's source text, recipient and filter are not carried.
    assert _hatred_operators(
        "hireling.dramatis.countess-marianna-chevaux-vampire-assassin") == set()


# --- Free the Slaves! targets the opponent's own supplied slaver identity ---

def test_free_the_slaves_binds_the_slaver_identity_not_a_warband_category():
    for path, prefix in (
        ("sources/knowledge/bands/mordheim/pit-fighters/special-rules.yaml", "pit-fighters"),
        ("sources/knowledge/bands/trollheim/chaos-streets-pit-fighters/special-rules.yaml",
         "chaos-streets-pit-fighters"),
    ):
        rule = _band_rule(path, "band--free-the-slaves")
        assert rule["rule_ref"] == "shared-rule.free-the-slaves"
        runtime = rule["runtime"]
        assert runtime["scope"] == "YES"
        assert runtime["implemented"] == "YES"
        effects = runtime["effects"]
        assert len(effects) == 1
        # The printed group is the slaver itself, so the operator reads the
        # opponent's own slaver identity and never a warband category: no
        # warband-group operator is bound to a category the source omits.
        assert effects[0]["id"] == "mechanic.hatred-slavers"
        assert effects[0]["binding"] == {"kind": "mechanic", "id": "mechanic.hatred-slavers"}
        assert prefix  # the two printed bands are the only carriers of the rule
