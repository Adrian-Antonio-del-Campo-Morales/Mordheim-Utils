"""T13 A-block: printed additional attacks (Spiked Tail, Sword-Gnoblar).

Sources (``sources/knowledge``):

1. ``bands/mordheim/lords-of-the-marsh-mim/special-rules.yaml`` /
   ``fimir-warriors--spiked-tail`` and ``young-nobles--spiked-tail``: *"the ...
   gains an extra tail attack in each hand-to-hand combat phase at the Fimir's
   Strength +1."*  Both print the same clause and differ only in the recipient.
2. ``catalog/items/weapons-close-combat.yaml`` / ``sword_gnoblar`` (Ogres only):
   *"An Ogre with a Sword-Gnoblar gains one extra Strength 2 attack in Close
   Combat, at the weapon skill of the owning model ... at the same time as the
   owning Hero's attacks."*

The expectations are read from those clauses, never from the compiled output.
Both families share one operator - an additional profile appended to the
bearer's attack pool - so one module covers them.  Combat evidence for the same
clauses lives in
``tests/python/combat/modular/test_t13_spiked_tail_and_sword_gnoblar_combat.py``.
"""
from __future__ import annotations

from pathlib import Path

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import read_yaml, runtime_bindings

ROOT = Path(__file__).resolve().parents[3]
KB = ROOT / "sources" / "knowledge"
LORDS_OF_THE_MARSH = KB / "bands" / "mordheim" / "lords-of-the-marsh-mim" / "special-rules.yaml"


def compiled(band_id: str, profile_id: str, **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id, **options))


def rule(path: Path, rule_id: str) -> dict:
    return next(row for row in read_yaml(path)["rules"] if row["id"] == rule_id)


def tail(fighter):
    return [effect for effect in fighter.extra_attacks if "rule.spiked-tail" in effect.tags]


def gnoblar(fighter):
    return [effect for effect in fighter.extra_attacks if "rule.sword-gnoblar" in effect.tags]


# ---------------------------------------------------------------------------
# source publication
# ---------------------------------------------------------------------------
def test_spiked_tail_rule_publishes_the_repeated_strength_plus_one_clause():
    text = " ".join(str(rule(LORDS_OF_THE_MARSH, "fimir-warriors--spiked-tail")["effect"]).split())
    assert "extra tail attack in each hand-to-hand combat phase" in text
    assert "Strength +1" in text


def test_spiked_tail_binds_an_executable_contract_for_each_recipient():
    for rule_id in ("fimir-warriors--spiked-tail", "young-nobles--spiked-tail"):
        row = rule(LORDS_OF_THE_MARSH, rule_id)
        assert row["runtime"]["implemented"] == "YES"
        assert runtime_bindings(row, "compiler") == (
            {"kind": "compiler", "id": f"profile-rule.{rule_id}"},
        )


# ---------------------------------------------------------------------------
# compiled recipients
# ---------------------------------------------------------------------------
def test_spiked_tail_reaches_both_printed_recipients_at_strength_plus_one():
    for band, profile in (("lords-of-the-marsh-mim", "fimir-warriors"),
                          ("lords-of-the-marsh-mim", "young-nobles")):
        effects = tail(compiled(band, profile))
        assert len(effects) == 1
        # Strength +1 relative to the bearer, not a fixed value.
        assert effects[0].fixed_strength == 0
        assert effects[0].strength_bonus == 1


def test_spiked_tail_stays_absent_from_a_non_recipient():
    assert tail(compiled("lords-of-the-marsh-mim", "shearls")) == []


def test_sword_gnoblar_adds_one_fixed_strength_two_attack():
    effects = gnoblar(compiled("maneaters", "captain", main_weapon_id="weapon.sword",
                               owned_item_ids=("sword_gnoblar",)))
    assert len(effects) == 1
    assert effects[0].fixed_strength == 2
    assert effects[0].strength_bonus == 0


def test_sword_gnoblar_contribution_requires_the_item():
    assert gnoblar(compiled("maneaters", "captain", main_weapon_id="weapon.sword")) == []
