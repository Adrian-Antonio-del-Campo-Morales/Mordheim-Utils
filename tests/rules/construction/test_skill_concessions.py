"""C05b: skill concessions, their printed limits and the Moulder mutations.

Sources (``sources/knowledge``):

* ``bands/mordheim/snotlings-web/special-rules.yaml`` / ``bigsnotz--big-bully``:
  *"The BigSnot immediately learns ONE Strength Skill. A BigSnot may only take
  this skill once each. Cannot be combined with the skill 'Frustratingly
  Tiny'."* — and the same exclusion is printed again in
  ``bullied-goblin--frustratingly-tiny``.
* ``bands/mordheim/skaven-of-clan-moulder-web/special-rules.yaml`` /
  ``band--clan-moulder-special-skills``: *"Clan Moulder heroes may choose to use
  the following Skill list instead of any of the standard Skill tables
  available to them"*, whose members keep their own records.
* ``.../rat-ogres--its-alive``: *"When hired each Rat Ogre must purchase a single
  Mutation from the list in the Mordheim Rulebook"* — the Possessed Warband list
  the KB already publishes as ``band--mutations-*``.

Every case drives the canonical offer (``desktop_call``) and the direct
compilation (``compile_fighter``) of the same member, so an offer that cannot
compile and a compilation that was never offered are both caught.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands, knowledge_root


# The concession is the offer: every case decides what the member may select,
# and the compiled tag only follows an admitted choice.
pytestmark = pytest.mark.phase2_construction

ROOT = knowledge_root()
COLLECTION = "mordheim"
BIG_BULLY = "bigsnotz--big-bully"
FRUSTRATINGLY_TINY = "bullied-goblin--frustratingly-tiny"
STRENGTH_SKILL = "skill.mighty-blow"
SECOND_STRENGTH_SKILL = "skill.resilient"
COMBAT_SKILL = "skill.strike-to-injure"
MOULDER = "skaven-of-clan-moulder-web"
BLACK_HUNGER = "band--clan-moulder-special-skills-black-hunger"
HYPNOTIC_MUSK = "band--clan-moulder-special-skills-hypnotic-musk"
MUTATIONS = ("band--mutations-great-claw", "band--mutations-tentacle")


def package(band_id, collection=COLLECTION):
    return next(pack for pack in load_bands(collection, ROOT) if pack.band["id"] == band_id)


def profile_of(pack, profile_id):
    return next(row for row in pack.profiles if row["id"] == profile_id)


def snotling(profile_id="bigsnotz", **options):
    return FighterBuild(COLLECTION, band_id="snotlings-web", profile_id=profile_id,
                        collection=COLLECTION, **options)


def moulder(profile_id="rat-ogres", **options):
    return FighterBuild(COLLECTION, band_id=MOULDER, profile_id=profile_id,
                        collection=COLLECTION, **options)


def test_the_bigsnot_is_offered_the_strength_table_only_by_taking_big_bully():
    """The concession is the offer: a Strength skill becomes selectable."""
    pack = package("snotlings-web")
    profile = profile_of(pack, "bigsnotz")
    offered = desktop_call("specialRules", snotling(), ROOT, package=pack, profile=profile)
    assert BIG_BULLY in offered
    assert FRUSTRATINGLY_TINY in offered
    plain = desktop_call("skillChoices", snotling(), ROOT, package=pack, profile=profile)
    assert plain[STRENGTH_SKILL] is False
    assert plain[COMBAT_SKILL] is True
    chosen = desktop_call("skillChoices", snotling(special_rule_ids=(BIG_BULLY,)),
                          ROOT, package=pack, profile=profile)
    assert chosen[STRENGTH_SKILL] is True


def test_big_bully_compiles_one_strength_skill_and_refuses_its_printed_limits():
    accepted = compile_fighter(snotling(special_rule_ids=(BIG_BULLY,), skill_ids=(STRENGTH_SKILL,)), ROOT)
    assert STRENGTH_SKILL in accepted.global_effects.tags
    with pytest.raises(ValueError, match="exactly one Strength skill"):
        compile_fighter(snotling(special_rule_ids=(BIG_BULLY,)), ROOT)
    with pytest.raises(ValueError, match="exactly one Strength skill"):
        compile_fighter(snotling(special_rule_ids=(BIG_BULLY,),
                                 skill_ids=(STRENGTH_SKILL, SECOND_STRENGTH_SKILL)), ROOT)
    with pytest.raises(ValueError, match="exactly one Strength skill"):
        compile_fighter(snotling(special_rule_ids=(BIG_BULLY,), skill_ids=(COMBAT_SKILL,)), ROOT)
    # 'A BigSnot may only take this skill once each': the repetition is refused.
    with pytest.raises(ValueError, match="only be taken once"):
        compile_fighter(snotling(special_rule_ids=(BIG_BULLY, BIG_BULLY),
                                 skill_ids=(STRENGTH_SKILL,)), ROOT)
    # Without the concession the same Strength skill is outside the access.
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(snotling(skill_ids=(STRENGTH_SKILL,)), ROOT)


def test_big_bully_and_frustratingly_tiny_refuse_each_other_in_both_orders():
    for order in ((BIG_BULLY, FRUSTRATINGLY_TINY), (FRUSTRATINGLY_TINY, BIG_BULLY)):
        with pytest.raises(ValueError, match="cannot be combined"):
            compile_fighter(snotling(special_rule_ids=order, skill_ids=(STRENGTH_SKILL,)), ROOT)


def test_frustratingly_tiny_stays_available_to_its_other_recipients():
    """The exclusion is a property of the pair, not of the skill everywhere."""
    for profile_id in ("bigsnotz", "scouts", "shaman"):
        assert FRUSTRATINGLY_TINY in desktop_call(
            "specialRules", snotling(profile_id), ROOT,
            package=package("snotlings-web"), profile=profile_of(package("snotlings-web"), profile_id))
        compile_fighter(snotling(profile_id, special_rule_ids=(FRUSTRATINGLY_TINY,)), ROOT)


def test_the_reconciled_rows_keep_their_existing_verdicts():
    """Two C05b pendings were already carried by the shared module."""
    strigoi = lambda **options: FighterBuild(  # noqa: E731 - one local fixture
        COLLECTION, band_id="survivors-of-strigos-sylv", profile_id="strigoi-vampire",
        collection=COLLECTION, **options)
    curse, thirster = "strigoi-vampire--curse-of-the-revenant", "strigoi-vampire--great-thirster"
    with pytest.raises(ValueError, match="requires Great Thirster"):
        compile_fighter(strigoi(special_rule_ids=(curse,)), ROOT)
    compile_fighter(strigoi(special_rule_ids=(curse, thirster)), ROOT)
    # 'A Necrarch Vampire may never acquire Strength skills' already binds its
    # category prohibition, so the profile's own duplicated line is reconciled.
    with pytest.raises(ValueError, match="forbidden"):
        compile_fighter(FighterBuild(COLLECTION, band_id="chaos-streets-undead-bloodlines",
            profile_id="necrarch-vampire", collection="trollheim",
            skill_ids=(STRENGTH_SKILL,)), ROOT)


def test_the_moulder_heroes_reach_their_list_and_henchmen_do_not():
    pack = package(MOULDER)
    for profile_id in ("packmaster", "stormvermin", "apprentices"):
        offered = desktop_call("specialRules", moulder(profile_id), ROOT,
                               package=pack, profile=profile_of(pack, profile_id))
        assert BLACK_HUNGER in offered and HYPNOTIC_MUSK in offered, profile_id
        assert "special" in profile_of(pack, profile_id)["skill_access"]
    for profile_id in ("clanrats", "rat-ogres"):
        offered = desktop_call("specialRules", moulder(profile_id), ROOT,
                               package=pack, profile=profile_of(pack, profile_id))
        assert BLACK_HUNGER not in offered and HYPNOTIC_MUSK not in offered, profile_id
    # The chosen member reaches its own operator, not just the list.
    hero = compile_fighter(moulder("packmaster", special_rule_ids=(BLACK_HUNGER,)), ROOT)
    assert "mechanic.black-hunger" in hero.global_effects.tags


def test_the_rat_ogre_buys_exactly_one_possessed_mutation():
    pack = package(MOULDER)
    rat_ogre = profile_of(pack, "rat-ogres")
    for selected in ((), MUTATIONS):
        offered = desktop_call("selectedRules", moulder(special_rule_ids=selected), ROOT,
                               package=pack, profile=rat_ogre)["rules"]
        assert MUTATIONS[0] in offered and MUTATIONS[1] in offered
        assert "band--mutations-eye-stalks" not in offered
    # The obligation resolves the published Possessed rules themselves: one whose
    # printed content is outside the duel keeps its own recorded disposition.
    assert compile_fighter(moulder(special_rule_ids=(MUTATIONS[0],)), ROOT)
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(moulder(special_rule_ids=("band--mutations-eye-stalks",)), ROOT)
    with pytest.raises(ValueError, match="outside the executable duel runtime"):
        compile_fighter(moulder(special_rule_ids=("band--mutations-daemon-soul",)), ROOT)
    with pytest.raises(ValueError, match="exactly one mutation"):
        compile_fighter(moulder(), ROOT)
    with pytest.raises(ValueError, match="exactly one mutation"):
        compile_fighter(moulder(special_rule_ids=MUTATIONS), ROOT)
    # The purchase is the printed members' only: no other Moulder member may.
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(moulder("packmaster", special_rule_ids=(MUTATIONS[0],)), ROOT)


TWISTKIN = "band--clan-moulder-special-skills-twistkin"


def test_twistkin_is_the_stormvermin_route_to_one_possessed_mutation():
    """'upon taking this skill the Hero must buy a Mutation': the choice is
    construction; its price and its recruitment producer stay external."""
    pack = package(MOULDER)
    storm = profile_of(pack, "stormvermin")
    offered = desktop_call("specialRules", moulder("stormvermin"), ROOT, package=pack, profile=storm)
    assert TWISTKIN in offered
    plain = desktop_call("selectedRules", moulder("stormvermin"), ROOT,
                         package=pack, profile=storm)["rules"]
    assert MUTATIONS[0] not in plain
    chosen = desktop_call("selectedRules", moulder("stormvermin", special_rule_ids=(TWISTKIN,)),
                          ROOT, package=pack, profile=storm)["rules"]
    assert MUTATIONS[0] in chosen and MUTATIONS[1] in chosen
    assert "band--mutations-eye-stalks" not in chosen
    assert compile_fighter(moulder("stormvermin", special_rule_ids=(TWISTKIN, MUTATIONS[0])), ROOT)
    with pytest.raises(ValueError, match="exactly one mutation"):
        compile_fighter(moulder("stormvermin", special_rule_ids=(TWISTKIN,)), ROOT)
    with pytest.raises(ValueError, match="exactly one mutation"):
        compile_fighter(moulder("stormvermin", special_rule_ids=(TWISTKIN, *MUTATIONS)), ROOT)
    # The printed recipient is the Stormvermin Hero, not every Moulder member.
    with pytest.raises(ValueError, match="not available|Stormvermin"):
        compile_fighter(moulder("packmaster", special_rule_ids=(TWISTKIN, MUTATIONS[0])), ROOT)
    # Only the canonical Possessed list is imported.
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(moulder("stormvermin",
            special_rule_ids=(TWISTKIN, "band--mutations-eye-stalks")), ROOT)
