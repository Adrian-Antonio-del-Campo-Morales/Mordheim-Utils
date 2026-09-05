"""Dynamic hireling campaign-eligibility: the 18 roster-dependent rules.

The predicates interpret the prose ``*.rule.campaign-eligibility`` effect of
``catalog/hirelings/**``; the KB text stays canonical and each assertion
names the rule id it pins.
"""
from mordheim_campaign.application.hire_eligibility import (
    KNOWN_RULES,
    DecisionKind,
    context_from_roster,
    dynamic_rules_for_profile,
    evaluate_rule,
)
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_catalogue import PostBattleCatalogue


def _port() -> KnowledgePort:
    return KnowledgePort()


def _ctx(port, band_id, *, member=(), hired=(), variant=None, collection="mordheim"):
    return context_from_roster(
        port,
        collection=collection,
        band_id=band_id,
        member_profile_ids=frozenset(member),
        hired_sword_profile_ids=frozenset(hired),
        variant=variant,
    )


def test_every_dynamic_rule_is_declared_on_a_hireling_profile():
    port = _port()
    declared = {
        rule_id
        for row in port.hireling_catalogue().profiles
        for rule_id in dynamic_rules_for_profile(port, str(row.get("id") or ""))
    }
    assert declared == KNOWN_RULES


def _decide(port, profile_id, ctx):
    return [
        evaluate_rule(rule_id, ctx)
        for rule_id in dynamic_rules_for_profile(port, profile_id)
    ]


def test_dwarf_and_elf_employer_rules_sisters():
    """sisters-of-sigmar: not Mercenaries/Witch Hunters and no Elf/Dwarf member."""
    port = _port()
    ctx = _ctx(port, "sisters-of-sigmar")
    for profile in (
        "hireling.hired-sword.dwarf-troll-slayer",
        "hireling.hired-sword.dwarf-treasure-hunter",
        "hireling.hired-sword.runesmith-journeyman",
    ):
        decisions = _decide(port, profile, ctx)
        assert decisions and all(d.kind == DecisionKind.REJECTED for d in decisions), profile
    # Elf Ranger looks for Dwarf employers; Sisters are humans.
    decisions = _decide(port, "hireling.hired-sword.elf-ranger", ctx)
    assert decisions and decisions[0].kind == DecisionKind.REJECTED


def test_elf_presence_opens_the_dwarf_hires_and_dwarf_opens_elf_ranger():
    port = _port()
    # A Mercenary warband that employs an Elf Ranger may hire Dwarf specialists.
    ctx = _ctx(port, "mercenaries", hired=("hireling.hired-sword.elf-ranger",))
    for profile in (
        "hireling.hired-sword.dwarf-troll-slayer",
        "hireling.hired-sword.dwarf-treasure-hunter",
        "hireling.hired-sword.runesmith-journeyman",
    ):
        decisions = _decide(port, profile, ctx)
        assert decisions and all(d.kind == DecisionKind.ALLOWED for d in decisions), profile
    # …and a roster with a Dwarf lets the same warband hire the Elf Ranger.
    ctx = _ctx(port, "mercenaries", hired=("hireling.hired-sword.dwarf-troll-slayer",))
    decisions = _decide(port, "hireling.hired-sword.elf-ranger", ctx)
    assert decisions and decisions[0].kind == DecisionKind.ALLOWED


def test_mercenary_variant_rules():
    port = _port()
    ctx = _ctx(port, "mercenaries")
    decisions = _decide(port, "hireling.hired-sword.warrior-priest-of-sigmar", ctx)
    assert decisions and decisions[0].kind == DecisionKind.NEEDS_VARIANT
    decisions = _decide(port, "hireling.hired-sword.wolf-priest-of-ulric", ctx)
    assert decisions and decisions[0].kind == DecisionKind.NEEDS_VARIANT

    middenheim = _ctx(port, "mercenaries", variant="middenheim")
    decisions = _decide(port, "hireling.hired-sword.wolf-priest-of-ulric", middenheim)
    assert decisions and decisions[0].kind == DecisionKind.ALLOWED
    decisions = _decide(port, "hireling.hired-sword.warrior-priest-of-sigmar", middenheim)
    assert decisions and decisions[0].kind == DecisionKind.REJECTED

    reikland = _ctx(port, "mercenaries", variant="reikland")
    decisions = _decide(port, "hireling.hired-sword.wolf-priest-of-ulric", reikland)
    assert decisions and decisions[0].kind == DecisionKind.REJECTED
    decisions = _decide(port, "hireling.dramatis.maximilian-the-mad", reikland)
    assert decisions and decisions[0].kind == DecisionKind.ALLOWED
    decisions = _decide(port, "hireling.dramatis.maximilian-the-mad", middenheim)
    assert decisions and decisions[0].kind == DecisionKind.REJECTED

    # Fixed-provenance human-mercenary bands are never Middenheimers.
    tilean = _ctx(port, "tileans", variant="middenheim")
    decisions = _decide(port, "hireling.hired-sword.wolf-priest-of-ulric", tilean)
    assert decisions and decisions[0].kind == DecisionKind.REJECTED


def test_highwayman_roadwarden_mutual_exclusion():
    port = _port()
    clean = _ctx(port, "mercenaries")
    assert _decide(port, "hireling.hired-sword.highwayman", clean)[0].kind == DecisionKind.ALLOWED
    assert _decide(port, "hireling.hired-sword.roadwarden", clean)[0].kind == DecisionKind.ALLOWED

    with_roadwarden = _ctx(port, "mercenaries", hired=("hireling.hired-sword.roadwarden",))
    assert _decide(port, "hireling.hired-sword.highwayman", with_roadwarden)[0].kind == DecisionKind.REJECTED
    with_highwayman = _ctx(port, "mercenaries", hired=("hireling.hired-sword.highwayman",))
    assert _decide(port, "hireling.hired-sword.roadwarden", with_highwayman)[0].kind == DecisionKind.REJECTED


def test_witch_hunter_spellcaster_restriction():
    port = _port()
    clean = _ctx(port, "mercenaries")
    decisions = _decide(port, "hireling.hired-sword.witch-hunter", clean)
    assert decisions and decisions[0].kind == DecisionKind.ALLOWED

    with_warlock = _ctx(port, "mercenaries", hired=("hireling.hired-sword.warlock",))
    decisions = _decide(port, "hireling.hired-sword.witch-hunter", with_warlock)
    assert decisions and decisions[0].kind == DecisionKind.REJECTED

    # Priests of Sigmar/Ulric/Taal/Morr do not count as spellcasters.
    with_priest = _ctx(port, "mercenaries", hired=("hireling.hired-sword.priest-of-morr",))
    decisions = _decide(port, "hireling.hired-sword.witch-hunter", with_priest)
    assert decisions and decisions[0].kind == DecisionKind.ALLOWED


def test_roster_composition_rules():
    port = _port()
    sisters = _ctx(port, "sisters-of-sigmar")
    # Cathayan Merchant: Humans/Dwarfs → Sisters are human.
    assert _decide(port, "hireling.hired-sword.cathayan-merchant", sisters)[0].kind == DecisionKind.ALLOWED
    # Grave Robber: needs Vampire/Necromancer/Liche.
    undead = _ctx(port, "undead")
    assert _decide(port, "hireling.hired-sword.grave-robber", undead)[0].kind == DecisionKind.ALLOWED
    assert _decide(port, "hireling.hired-sword.grave-robber", sisters)[0].kind == DecisionKind.REJECTED
    # Ippan Shu: Humans or Elves.
    assert _decide(port, "hireling.dramatis.grand-master-ippan-shu", sisters)[0].kind == DecisionKind.ALLOWED
    assert _decide(port, "hireling.dramatis.grand-master-ippan-shu", _ctx(port, "skaven-clan-eshin"))[0].kind == DecisionKind.REJECTED
    # Dijin Katal: no Elven Hired Sword on the roster.
    assert _decide(port, "hireling.dramatis.dijin-katal-the-renegade-assassin", sisters)[0].kind == DecisionKind.ALLOWED
    with_elf = _ctx(port, "mercenaries", hired=("hireling.hired-sword.elf-mage",))
    assert _decide(port, "hireling.dramatis.dijin-katal-the-renegade-assassin", with_elf)[0].kind == DecisionKind.REJECTED


def test_evil_hired_sword_and_fear_rules():
    port = _port()
    # Shadow Warrior refuses evil Hired Swords.
    with_dark_elf = _ctx(port, "mercenaries", hired=("hireling.hired-sword.dark-elf-assassin",))
    assert _decide(port, "hireling.hired-sword.shadow-warrior", with_dark_elf)[0].kind == DecisionKind.REJECTED
    # Knight of the White Wolf refuses Warrior Priests.
    with_priest = _ctx(port, "mercenaries", hired=("hireling.hired-sword.warrior-priest-of-sigmar",))
    assert _decide(port, "hireling.hired-sword.knight-of-the-white-wolf", with_priest)[0].kind == DecisionKind.REJECTED
    # Ninja Gnoblar: no fear-causing creatures.
    with_ogre = _ctx(port, "mercenaries", hired=("hireling.hired-sword.ogre-bodyguard",))
    assert _decide(port, "hireling.hired-sword.ninja-gnoblar", with_ogre)[0].kind == DecisionKind.REJECTED


def test_william_auto_vs_conditional_good_aligned():
    port = _port()
    mercenaries = _ctx(port, "mercenaries")
    decision = _decide(port, "hireling.dramatis.william-schakestange-master-bard", mercenaries)[0]
    assert decision.kind == DecisionKind.ALLOWED
    kislevites = _ctx(port, "kislevites")
    decision = _decide(port, "hireling.dramatis.william-schakestange-master-bard", kislevites)[0]
    assert decision.kind == DecisionKind.CONDITIONAL
    assert decision.roll_ge == 4
    cult = _ctx(port, "cult-of-the-possessed")
    decision = _decide(port, "hireling.dramatis.william-schakestange-master-bard", cult)[0]
    assert decision.kind == DecisionKind.REJECTED


def test_catalogue_hides_ineligible_and_annotates_conditional_offers():
    port = _port()
    sisters = PostBattleCatalogue(port, "mordheim", "sisters-of-sigmar")
    swords = {offer.profile_id.split(".")[-1]: offer for offer in sisters.hired_swords()}
    # The six roster-dependent entries resolve: no Dwarf specialists for Sisters…
    assert "dwarf-troll-slayer" not in swords
    assert "dwarf-treasure-hunter" not in swords
    assert "elf-ranger" not in swords
    assert "grave-robber" not in swords
    # …but the human-composition merchant is available.
    assert "cathayan-merchant" in swords
    william = next(offer for offer in sisters.dramatis_personae()
                   if offer.profile_id.split(".")[-1] == "william-schakestange-master-bard")
    assert william.eligibility == "eligible"

    # A variant-capable mercenary catalogue reacts to the variant.
    mercenaries = PostBattleCatalogue(port, "mordheim", "mercenaries", variant="middenheim")
    by_name = {offer.profile_id.split(".")[-1]: offer for offer in mercenaries.hired_swords()}
    assert "wolf-priest-of-ulric" in by_name
    assert "warrior-priest-of-sigmar" not in by_name
    reikland = PostBattleCatalogue(port, "mordheim", "mercenaries", variant="reikland")
    by_name = {offer.profile_id.split(".")[-1]: offer for offer in reikland.hired_swords()}
    assert "wolf-priest-of-ulric" not in by_name
    assert "warrior-priest-of-sigmar" in by_name
