"""KB-backed post-battle resolution: serious injuries, exploration, rarity.

Every expectation is pinned to the published campaign catalogue rows the
resolver reads (``serious-injuries.yaml``, ``exploration-and-income.yaml``,
``trading-and-rarity.yaml`` + ``trading-post.yaml``).
"""
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_resolution import PostBattleResolver


def _resolver() -> PostBattleResolver:
    return PostBattleResolver(KnowledgePort())


def test_hero_serious_injury_rows_are_kb_rows():
    resolver = _resolver()
    expectations = {
        11: "Dead", 15: "Dead",
        16: "Multiple Injuries", 21: "Multiple Injuries",
        22: "Leg Wound", 24: "Madness", 25: "Smashed Leg",
        31: "Blinded In One Eye", 46: "Full Recovery", 55: "Full Recovery",
        56: "Bitter Enmity", 61: "Captured", 62: "Hardened",
        66: "Survives Against The Odds",
    }
    for d66, expected in expectations.items():
        outcome = resolver.resolve_hero_serious_injury(d66)
        assert outcome.result == expected, (d66, outcome)
    dead = resolver.resolve_hero_serious_injury(11)
    assert dead.effects == ("removes the warrior from the roster",)
    leg = resolver.resolve_hero_serious_injury(22)
    assert "movement" in leg.effects[0] and "-1" in leg.effects[0]
    multiple = resolver.resolve_hero_serious_injury(21)
    assert multiple.follow_up is not None and "again" in multiple.follow_up
    # Madness needs the follow-up D6 subtable.
    madness = resolver.resolve_hero_serious_injury(24)
    assert madness.follow_up is not None


def test_advance_thresholds_rating_and_racial_maximums_come_from_the_kb():
    """The app-owned looking-glass values are read from the KB, not constants."""
    resolver = _resolver()
    # experience-and-advances.yaml "advance_thresholds" block.
    assert resolver.advance_thresholds("hero")
    assert resolver.advance_thresholds("hero")[:4] == (20, 40, 65, 90)
    assert resolver.advance_thresholds("henchman")[:4] == (8, 16, 25, 35)
    # warband-rating.yaml: 5 per model + 1 per XP.
    assert resolver.warband_rating(models=8, experience=85) == 125
    # catalog/rules/racial-maximums.yaml: caps keyed by race.
    maximums = resolver.racial_maximums()
    assert maximums["human"]["WS"] == 6
    assert maximums["human"]["S"] == 4
    assert maximums["elf"]["M"] == 5
    assert maximums["elf"]["I"] == 9


def test_hero_d66_chart_regions_follow_row_major_order():
    resolver = _resolver()
    # Row 16-21 covers the corner rolls 16 and 21 (nothing sits between them
    # in printed order); both are Multiple Injuries.
    assert resolver.resolve_hero_serious_injury(16).result == "Multiple Injuries"
    assert resolver.resolve_hero_serious_injury(21).result == "Multiple Injuries"
    # 41-55 covers the recovery square 41-46 and 51-55; 56 is separate.
    for d66 in (41, 44, 46, 51, 55):
        assert resolver.resolve_hero_serious_injury(d66).result == "Full Recovery", d66
    assert resolver.resolve_hero_serious_injury(56).result == "Bitter Enmity"
    # 62-63 covers both corners.
    assert resolver.resolve_hero_serious_injury(62).result == "Hardened"
    assert resolver.resolve_hero_serious_injury(63).result == "Hardened"


def test_henchman_survival_chart():
    resolver = _resolver()
    assert resolver.resolve_henchman_serious_injury(1).result == "Removed"
    assert resolver.resolve_henchman_serious_injury(2).result == "Removed"
    for roll in (3, 4, 5, 6):
        outcome = resolver.resolve_henchman_serious_injury(roll)
        assert outcome.result == "Full Recovery"
        assert not outcome.effects


def test_exploration_shards_by_total():
    resolver = _resolver()
    assert resolver.resolve_exploration((1, 1, 1, 1)).shards == 1   # total 4
    assert resolver.resolve_exploration((3, 3, 5, 6)).shards == 3   # total 17
    assert resolver.resolve_exploration((6, 6, 6, 6)).shards == 4   # total 24
    # Empty roll yields no shards and no match.
    assert resolver.resolve_exploration(()).shards == 0


def test_exploration_matching_dice_special_results():
    resolver = _resolver()
    pair = resolver.resolve_exploration((3, 3, 5, 6))
    assert pair.matches == ((3, 2, "Corpse"),)
    assert "Corpse" in pair.matching_dice_note
    triple = resolver.resolve_exploration((2, 2, 2, 5))
    assert triple.matches == ((2, 3, "Smithy"),)
    # No special when every die differs.
    plain = resolver.resolve_exploration((1, 2, 4, 6))
    assert plain.matches == ()
    # Largest set wins over a smaller pair.
    mixed = resolver.resolve_exploration((4, 4, 4, 5, 5))
    assert mixed.matches == ((4, 3, "Fletcher"),)


def test_exploration_dice_allocation_caps_at_six():
    resolver = _resolver()
    assert resolver.exploration_dice(surviving_heroes=4, warband_won=False) == 4
    assert resolver.exploration_dice(surviving_heroes=4, warband_won=True) == 5
    assert resolver.exploration_dice(surviving_heroes=9, warband_won=True) == 6
    assert resolver.exploration_dice(surviving_heroes=0, warband_won=False) == 0


def test_rarity_search_against_trading_post():
    resolver = _resolver()
    # Holy Tome is rare 8 in the Trading Post (100 + D6x10).
    success = resolver.resolve_rarity_search("holy_tome", 8)
    assert success.rarity == 8 and success.success
    failure = resolver.resolve_rarity_search("holy_tome", 7)
    assert not failure.success
    # Common items need no test.
    dagger = resolver.resolve_rarity_search("dagger", 2)
    assert dagger.rarity is None and dagger.success
    # Modifiers shift the target down (e.g. +1 to rare rolls).
    with_modifier = resolver.resolve_rarity_search("holy_tome", 7, modifiers=1)
    assert with_modifier.success
    # Items without a sellable Trading Post row cannot be searched.
    assert not resolver.resolve_rarity_search("hochland_long_rifle", 12).success
