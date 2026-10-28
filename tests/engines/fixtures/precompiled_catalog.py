"""The precompiled scenario catalogue: one set of 43 frozen duel scenarios.

Every scenario addresses the frozen corpus at
``tests/engines/fixtures/compiled-cases.json`` through its uniform key
``scenario/<name>``: consumers load the precompiled pair from that JSON, and
nothing here compiles a fighter or falls back to the compiler.

The catalogue is a single family. ``basic``, ``defences``, ``stateful`` and
``long`` used to exist twice — a benchmark copy and a deep copy of the same
compiled pair — and are one entry each now. ``multiattack`` keeps both
variants because their first fighter differs: ``multiattack-a3-t3`` is the
3-attack, T3 build and ``multiattack-a2-t4`` the 2-attack, T4 one.

Selection is expressed as three cumulative levels — ``small`` contained in
``normal``, contained in ``long`` — over these definitions, and ``small`` is
the default. A level selects scenarios only; each scenario keeps its own round
limit.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    first: FighterBuild
    second: FighterBuild
    maximum_rounds: int = 50
    # Synthetic attack tags let a scenario exercise a consumer whose catalogue
    # currently has no selectable producer (notably blessed attacks), without
    # changing the construction or combat implementations.
    first_attack_tags: tuple[str, ...] = ()
    second_attack_tags: tuple[str, ...] = ()

    @property
    def id(self) -> str:
        """Scenario name exposed to existing application consumers."""
        return self.name

ORDINARY = Characteristics(3, 3, 3, 1, 3, 1)
VETERAN = Characteristics(4, 4, 4, 2, 4, 2)
DURABLE = Characteristics(2, 2, 5, 4, 2, 1)

# Synthetic-profile convention from ``battery_catalogue``: Leadership 7 is a
# scenario input, not a rule-derived profile value.
SYNTHETIC_LEADERSHIP = 7
VETERAN_WITH_LEADERSHIP = Characteristics(
    4, 4, 4, 2, 4, 2, leadership=SYNTHETIC_LEADERSHIP
)


def _synthetic(characteristics: Characteristics) -> Characteristics:
    """Supply the synthetic scenario's Leadership without overriding an explicit one."""
    if characteristics.leadership is not None:
        return characteristics
    return replace(characteristics, leadership=SYNTHETIC_LEADERSHIP)


def _build(*, characteristics=None, main_weapon_id: str = "weapon.dagger",
           off_hand_id: str | None = None, armour_id: str = "armour.no-armour",
           defence_ids: tuple[str, ...] = (), band_id: str | None = None,
           profile_id: str | None = None, special_rule_ids: tuple[str, ...] = (),
           skill_ids: tuple[str, ...] = (), trait_overrides: dict[str, object] | None = None,
           collection: str = "mordheim") -> FighterBuild:
    """Build a FighterBuild for the scenario matrix with explicit knobs.

    ``characteristics`` and the ``band_id``/``profile_id`` pair are mutually
    exclusive ways to describe the fighter (mirroring ``FighterBuild``); a
    characteristics-less profile build must never silently receive the
    ordinary profile.
    """
    if band_id is None and characteristics is None:
        characteristics = ORDINARY
    if band_id is None:
        characteristics = _synthetic(characteristics)
    return FighterBuild(
        "mordheim", characteristics, band_id=band_id, profile_id=profile_id,
        main_weapon_id=main_weapon_id, off_hand_id=off_hand_id, armour_id=armour_id,
        defence_ids=defence_ids,        special_rule_ids=special_rule_ids,
        skill_ids=skill_ids, trait_overrides=trait_overrides or {}, collection=collection,
    )


SCENARIOS: tuple[Scenario, ...] = (
    Scenario("basic", _build(), _build()),
    # Both multiattack variants survive: only the first fighter differs.
    Scenario(
        "multiattack-a3-t3",
        _build(characteristics=Characteristics(4, 4, 3, 2, 4, 3),
               main_weapon_id="weapon.axe", off_hand_id="weapon.dagger"),
        _build(characteristics=VETERAN, armour_id="armour.heavy-armour"),
    ),
    Scenario(
        "multiattack-a2-t4",
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe", off_hand_id="weapon.dagger"),
        _build(characteristics=VETERAN, armour_id="armour.heavy-armour"),
    ),
    Scenario(
        "defences",
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               off_hand_id="defence.buckler", armour_id="armour.light-armour"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.dwarf-axe",
               off_hand_id="defence.shield", armour_id="armour.gromril-armour"),
    ),
    Scenario(
        "stateful",
        _build(band_id="pit-fighters", profile_id="pit-king",
               special_rule_ids=("band--pit-fighter-skill-force-of-will",)),
        _build(characteristics=VETERAN, main_weapon_id="weapon.brazier-iron"),
    ),
    Scenario(
        "long",
        _build(characteristics=DURABLE, armour_id="armour.gromril-armour",
               off_hand_id="defence.shield"),
        _build(characteristics=DURABLE, armour_id="armour.gromril-armour",
               off_hand_id="defence.shield"),
        maximum_rounds=75,
    ),
    # Archetype matrix: profiles x equipment families beyond the five core ones.
    Scenario(
        "elite-vs-durable",
        _build(characteristics=Characteristics(5, 4, 4, 2, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
        _build(characteristics=DURABLE, armour_id="armour.gromril-armour",
               off_hand_id="defence.shield"),
    ),
    Scenario(
        "axes-vs-light",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.axe"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               armour_id="armour.light-armour"),
    ),
    Scenario(
        "glass-vs-tank",
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2)),
        _build(characteristics=DURABLE, armour_id="armour.heavy-armour",
               off_hand_id="defence.shield"),
    ),
    Scenario(
        "two-weapons-vs-parry",
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               off_hand_id="weapon.dagger"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               off_hand_id="defence.buckler"),
    ),
    Scenario(
        "heavy-clash",
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
    ),
    Scenario(
        "fencer-mirror",
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    Scenario(
        "brute-vs-fencer",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.axe"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    Scenario(
        "ithilmar-duel",
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               armour_id="armour.ithilmar-armour"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               armour_id="armour.ithilmar-armour"),
    ),
    # Mechanic-coverage extension (2026-09-04): each pair targets an engine
    # behaviour family the profile/equipment archetypes above never exercise.
    # They were selected with a coverage fingerprint (distinct effect axes)
    # against the catalogue; together they cover the distinct executable
    # effect axes represented by the current runtime scope. NumPy matches the
    # modular oracle on every pair at 10k
    # duels; the native port still lags on several (see
    # docs/guides/develop-and-release.md, "Current status").
    # 1. Undead family: sigmarite hammer bonus vs undead_or_possessed,
    #    poison immunity and ignore-pain injury resolution.
    Scenario(
        "sigmarite-vs-undead",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1,
                                               leadership=SYNTHETIC_LEADERSHIP),
               main_weapon_id="weapon.sigmarite-hammer"),
        _build(band_id="tomb-guardians", profile_id="skeleton-warriors"),
    ),
    # 2. Regeneration (4+) blocked by fire: troll vs a burning brazier-iron.
    Scenario(
        "regen-vs-fire",
        _build(band_id="orc-mob", profile_id="troll"),
        _build(characteristics=VETERAN_WITH_LEADERSHIP,
               main_weapon_id="weapon.brazier-iron"),
    ),
    # 3. Natural armour negated by magic + magical attacks + extra bite:
    #    lizardmen scaly skin vs a carnival daemon's attack.magical.
    Scenario(
        "natural-armour-vs-magic",
        _build(band_id="lizardmen", profile_id="saurus-braves"),
        _build(band_id="carnival-of-chaos", profile_id="plague-bearers"),
    ),
    # 4. Pistols: ballistic-skilled shot, fixed strength, armour
    #    penetration and the crack-shot first-round path vs a parry defence.
    Scenario(
        "pistol-vs-parry",
        _build(characteristics=VETERAN, main_weapon_id="weapon.duelling-pistol"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    # 5. Concussion + critical-injury bonus vs dwarfs: concussion
    #    immunity, hard-to-kill and the out-of-action threshold of 6.
    Scenario(
        "concussion-vs-dwarf",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.draich"),
        _build(band_id="dwarf-rangers", profile_id="beardlings"),
    ),
    # 6. Frenzy + always strikes first: fanatic priority 10 and its
    #    frenzy-boosted attacks vs a shielded heavy.
    Scenario(
        "frenzy-vs-heavy",
        _build(band_id="night-goblins-mic", profile_id="fanatics"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
    ),
    # 7. Paired poisoned blades (black-lotus auto-wound) vs a poison-
    #    immune undead beast: poison-blocked and paired-attack paths.
    Scenario(
        "paired-poison-vs-undead",
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2,
                                               leadership=SYNTHETIC_LEADERSHIP),
               main_weapon_id="weapon.weeping-blades"),
        _build(band_id="undead", profile_id="dire-wolves"),
    ),
    # 8. Two-handed great weapon: strength bonus, both hands occupied,
    #    initiative penalty vs gromril armour and a shield.
    Scenario(
        "great-weapon-vs-tank",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.double-handed-weapon"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               armour_id="armour.gromril-armour", off_hand_id="defence.shield"),
    ),
    # 9. Ward save vs a magical attacker: enchanted skins against a
    #    daemon's attack.magical (also cloud of flies, poison immunity).
    Scenario(
        "ward-vs-magic",
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               defence_ids=("defence.enchanted-skins",)),
        _build(band_id="carnival-of-chaos", profile_id="nurglings"),
    ),
    # 10. Unarmed combat: fists/natural attacks, unarmed criticals and
    #     the monk strictures vs a cannot-be-parried whip.
    Scenario(
        "unarmed-vs-steel",
        _build(band_id="battle-monks-of-cathay", profile_id="dragon-monks"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.steel-whip"),
    ),
    # 11. Injury profile 1 (out of action on 4+) vs an armour-ignoring
    #     weapon with an injury modifier (death-knife).
    Scenario(
        "injury-profile-vs-death-knife",
        _build(band_id="night-goblins-web", profile_id="snotlings"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.death-knife"),
    ),
    # 12. Entangle: the chained squig's fixed-strength, cannot-be-parried
    #     attack entangles its victim vs a parrying fencer.
    Scenario(
        "entangle-vs-fencer",
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.chained-squig"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    # Timing and parry amplifiers (2026-09-04): pairs selected so the
    # failure classes found in the first deep certification (natural-6
    # parry waste, stunned-defender follow-up, frenzy re-doubling,
    # per-round timing drift on grinds) are exercised at higher
    # statistical power than the profile archetypes above.  The
    # truncation sweep covers every scenario, so resolution-timing
    # defects show at intermediate horizons even when aggregate rates
    # agree.
    # 13. Four hits per pool vs a single parry: the unparryable
    #     natural-6 co-occurrence (6 + another hit in the same pool)
    #     fires far more often than in two-weapons-vs-parry, so a
    #     wasted parry on a 6 moves the first-winner rate measurably.
    Scenario(
        "triple-weapon-vs-parry",
        _build(characteristics=Characteristics(4, 4, 3, 2, 4, 3),
               main_weapon_id="weapon.axe", off_hand_id="weapon.dagger"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    # 14. Two attacks vs a W1 injury-profile-1 defender: the first
    #     attack stuns at 0 wounds in roughly a quarter of the duels,
    #     so the follow-up attack's stunned-defender auto-out-of-action
    #     path is heavily exercised (visible at the round-1/round-2
    #     horizons of the truncation sweep).
    Scenario(
        "a2-vs-w1-stun",
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe"),
        _build(band_id="night-goblins-web", profile_id="snotlings"),
    ),
    # 15. Frenzy amplifier with a measurable rare-win rate: the fanatic
    #     keeps frenzy + always-strikes-first, but the defender drops
    #     its armour so the fanatic's base rate rises from ~2% to ~8%
    #     (no W2+frenzy profile exists; every frenzy grant is a W1
    #     profile rule).  A relative frenzy defect is far above the
    #     six-sigma gate at this base rate.
    Scenario(
        "frenzy-vs-w2",
        _build(band_id="night-goblins-mic", profile_id="fanatics"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe"),
    ),
    # 16. Mirror of elite-vs-durable with the durable side first: the
    #     unresolved rate stays ~1%, so the timing class is certified
    #     from both directions and any direction-dependent drift shows.
    Scenario(
        "durable-vs-elite",
        _build(characteristics=DURABLE, armour_id="armour.gromril-armour",
               off_hand_id="defence.shield"),
        _build(characteristics=Characteristics(5, 4, 4, 2, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    # 17. Heavy grind at 75 rounds: both sides W3/T4, heavy armour and
    #     shield; ~14% of duels reach the horizon.  Per-round
    #     accumulation is maximised, so timing/orchestration drift in
    #     the resolution ledger shows at the long horizons.
    Scenario(
        "heavy-grind",
        _build(characteristics=Characteristics(3, 3, 4, 3, 3, 1),
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
        _build(characteristics=Characteristics(3, 3, 4, 3, 3, 1),
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
        maximum_rounds=75,
    ),
    # 18. Three independent skill consumers in one durable fighter:
    #     Strongman changes two-handed priority, Thick Skull changes stunned
    #     reactions, and Step Aside supplies a post-armour special save.
    #     Modular calibration (seed 2026, 10k duels): 79.710% / 20.290% /
    #     0.000% first wins / second wins / unresolved.
    Scenario(
        "skills-vs-hitter",
        _build(characteristics=Characteristics(4, 4, 4, 2, 4, 2),
               main_weapon_id="weapon.double-handed-weapon",
               skill_ids=("skill.strongman", "skill.thick-skull", "skill.step-aside")),
        _build(characteristics=Characteristics(4, 5, 4, 2, 3, 2),
               main_weapon_id="weapon.axe"),
    ),
    # 19. Helmet protection is exercised on one side while the opposing
    #     W1 Raging Peasant uses injury profile 2 (out on any unsaved wound).
    #     Modular calibration (seed 2026, 10k duels): 91.140% / 8.860% /
    #     0.000% first wins / second wins / unresolved.
    Scenario(
        "helmet-vs-injury-profile-2",
        _build(characteristics=Characteristics(4, 4, 3, 2, 4, 1),
               main_weapon_id="weapon.sword", defence_ids=("defence.helmet",)),
        _build(band_id="battle-monks-of-cathay", profile_id="raging-peasants"),
    ),
    # 20. The Cathayan Longsword's +1 WS/+1 Initiative face the same profile
    #     with an ordinary sword. Its armour-penetration field is retained by
    #     the current normalized combat entry as a separate engine axis.
    #     Modular calibration (seed 2026, 10k duels): 66.190% / 33.810% /
    #     0.000% first wins / second wins / unresolved.
    Scenario(
        "cathayan-longsword-vs-sword",
        _build(characteristics=Characteristics(4, 4, 3, 2, 4, 2),
               main_weapon_id="weapon.cathayan-longsword"),
        _build(characteristics=Characteristics(4, 4, 3, 2, 4, 2),
               main_weapon_id="weapon.sword"),
    ),
    # 21. The runtime has a blessed-regeneration consumer but no selectable
    #     blessed weapon in the current KB.  The attack tag is therefore a
    #     synthetic input; construction and engine code stay
    #     untouched while the Strigoi regeneration blocker is exercised.
    #     Modular calibration (seed 2026, 10k duels): 23.720% / 76.280% /
    #     0.000% first wins / second wins / unresolved.
    Scenario(
        "blessed-vs-regen",
        _build(characteristics=VETERAN_WITH_LEADERSHIP,
               main_weapon_id="weapon.sword"),
        _build(
            band_id="chaos-streets-undead-bloodlines", profile_id="strigoi-vampire",
            collection="trollheim",
            special_rule_ids=("band--strigoi-power-curse-of-the-reborn",),
        ),
        first_attack_tags=("attack.blessed",),
    ),
    # Coverage-completion tranche (2026-09-05). These probes are deliberately
    # narrow: they add the remaining reachable effect axes without adding
    # broad matchup variants. Synthetic trait/skill combinations are confined
    # to this catalogue and do not alter the KB or combat engines.
    # 22. Khemri's fragile profile 3 against the last-wound profile 4.
    Scenario(
        "injury-profile-3-vs-4",
        _build(characteristics=Characteristics(4, 4, 4, 2, 4, 2),
               main_weapon_id="weapon.sword",
               trait_overrides={"injury_profile": 3}),
        _build(characteristics=Characteristics(4, 4, 4, 2, 4, 2),
               main_weapon_id="weapon.axe",
               trait_overrides={"injury_profile": 4}),
    ),
    # 23. Composite consumers for wound modifiers, hit re-rolls, extra
    # attacks and wound re-rolls, against a plain high-strength hitter.
    Scenario(
        "skill-stack-vs-hitter",
        _build(characteristics=Characteristics(4, 4, 4, 2, 4, 2),
               main_weapon_id="weapon.sword",
               skill_ids=("skill.expert-fighter", "skill.infinite-hatred",
                          "skill.red-fury", "skill.sure-strike")),
        _build(characteristics=Characteristics(4, 5, 4, 2, 3, 2),
               main_weapon_id="weapon.axe"),
    ),
    # 24. Resilient modifies incoming strength without modifying armour
    # saves; the opposing double-handed weapon makes the boundary frequent.
    Scenario(
        "resilient-vs-high-strength",
        _build(characteristics=Characteristics(4, 4, 5, 2, 4, 2),
               main_weapon_id="weapon.sword", skill_ids=("skill.resilient",)),
        _build(characteristics=Characteristics(4, 5, 4, 2, 3, 2),
               main_weapon_id="weapon.double-handed-weapon"),
    ),
    # 25. Charging WS and charging Strength bonuses on the same attacker.
    Scenario(
        "charge-skills-vs-tank",
        _build(characteristics=Characteristics(4, 4, 4, 2, 5, 2),
               main_weapon_id="weapon.sword",
               skill_ids=("skill.unstoppable-charge", "skill.strength-of-steel")),
        _build(characteristics=DURABLE, main_weapon_id="weapon.axe",
               armour_id="armour.gromril-armour", off_hand_id="defence.shield"),
    ),
    # 26. Synthetic opener combining the first-round attack bonus from
    # Chain-Sticks, the profile/charge attack bonus, and first-round weapon
    # strength; Strength of Steel adds the charge-strength branch. This is
    # intentionally synthetic because no single legal profile combines
    # these equipment families.
    Scenario(
        "first-round-opener",
        _build(characteristics=Characteristics(4, 4, 4, 2, 5, 2),
               main_weapon_id="weapon.chain-sticks",
               trait_overrides={"first_round_charge_attack_bonus": True}),
        _build(characteristics=Characteristics(4, 4, 4, 2, 4, 2),
               main_weapon_id="weapon.flail",
               skill_ids=("skill.strength-of-steel",)),
    ),
    # 27. Condemned's per-duel random WS/S/T/A values versus a stable profile.
    Scenario(
        "random-characteristics-vs-stable",
        _build(band_id="marauders-of-chaos", profile_id="condemned",
               main_weapon_id="weapon.natural-attacks"),
        _build(characteristics=VETERAN_WITH_LEADERSHIP,
               main_weapon_id="weapon.sword"),
    ),
    # 28. Bear Hug needs two successful hits; the synthetic fire tag also
    # makes the Scarecrow's caught-fire threshold observable in normal hits.
    Scenario(
        "trained-bear-vs-scarecrow",
        _build(band_id="kislevites", profile_id="trained-bear"),
        _build(band_id="restless-dead", profile_id="scarecrows"),
        first_attack_tags=("attack.fire",),
    ),
    # 29. Silent Walker supplies a 5+ mundane-only ward; Cold One Beasthounds
    # supply unmodified natural armour. The magical attack tag intentionally
    # covers the ward-negation branch; the mundane ward branch remains a
    # documented follow-up because this is one pair, not two variants.
    Scenario(
        "silent-walker-vs-cold-one",
        _build(band_id="lustria-pygmies", profile_id="silent-walker",
               main_weapon_id="weapon.dagger", collection="trollheim"),
        _build(band_id="dark-elves", profile_id="cold-one-beasthounds",
               main_weapon_id="weapon.natural-attacks"),
        second_attack_tags=("attack.magical",),
    ),

)


#: Level order: each level contains the previous one and ``long`` contains
#: every scenario of the catalogue.
LEVELS = ("small", "normal", "long")

#: Cheap smoke set: one representative per cost axis, no 75-round grind and no
#: heavy attack pool.  This is the default for a quick parity or performance
#: sample.
SMALL_SCENARIO_NAMES: tuple[str, ...] = (
    "basic",                     # cheapest duel: per-batch fixed overhead
    "defences",                  # armour, shields and parries
    "stateful",                  # one-shot resource and per-round state
    "sigmarite-vs-undead",       # conditional extra attacks + undead rules
    "regen-vs-fire",             # special saves, regeneration blocked by fire
    "pistol-vs-parry",           # ballistic profile and a parry defence
    "entangle-vs-fencer",        # pool manipulation with reaction logic
    "ward-vs-magic",             # ward save against a magical attacker
)

#: Breadth set: every rule family has a representative, including both
#: multiattack variants and the profile-heavy duels, without the long grinds.
NORMAL_SCENARIO_NAMES: tuple[str, ...] = SMALL_SCENARIO_NAMES + (
    "multiattack-a3-t3",
    "multiattack-a2-t4",
    "elite-vs-durable",
    "axes-vs-light",
    "glass-vs-tank",
    "two-weapons-vs-parry",
    "fencer-mirror",
    "brute-vs-fencer",
    "ithilmar-duel",
    "natural-armour-vs-magic",
    "concussion-vs-dwarf",
    "paired-poison-vs-undead",
    "great-weapon-vs-tank",
    "unarmed-vs-steel",
    "injury-profile-vs-death-knife",
    "helmet-vs-injury-profile-2",
    "cathayan-longsword-vs-sword",
    "injury-profile-3-vs-4",
    "resilient-vs-high-strength",
    "charge-skills-vs-tank",
    "first-round-opener",
    "blessed-vs-regen",
)

#: Full set: every maintained scenario, so ``long`` adds the expensive combats
#: — the two 75-round grinds, the heaviest attack pools and the long skill
#: stacks — plus the remaining profile duels.  Levels never change a
#: scenario's round limit.
LONG_SCENARIO_NAMES: tuple[str, ...] = tuple(
    scenario.name for scenario in SCENARIOS
)

LEVEL_SCENARIOS: dict[str, tuple[str, ...]] = {
    "small": SMALL_SCENARIO_NAMES,
    "normal": NORMAL_SCENARIO_NAMES,
    "long": LONG_SCENARIO_NAMES,
}

#: The uniform frozen-corpus key of every scenario.
SCENARIO_KEYS: dict[str, str] = {
    scenario.name: f"scenario/{scenario.name}" for scenario in SCENARIOS
}


def scenario_key(name: str) -> str:
    """Corpus key of a maintained scenario (``scenario/<name>``)."""
    try:
        return SCENARIO_KEYS[name]
    except KeyError as error:
        raise KeyError(f"unknown scenario {name!r}") from error


def scenarios_for_level(level: str = "small") -> tuple[Scenario, ...]:
    """Return the scenarios of one cumulative level (``small`` by default)."""
    try:
        names = LEVEL_SCENARIOS[level]
    except KeyError as error:
        raise ValueError(
            f"unknown level {level!r}; choose one of {', '.join(LEVELS)}"
        ) from error
    by_name = {scenario.name: scenario for scenario in SCENARIOS}
    return tuple(by_name[name] for name in names)
