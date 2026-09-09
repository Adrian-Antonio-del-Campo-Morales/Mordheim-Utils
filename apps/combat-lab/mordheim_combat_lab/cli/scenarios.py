"""Benchmark scenario definitions: pure data, no combat-engine imports.

Extracted from ``benchmarking`` so the CLI parser (``commands.build_parser``)
can read ``DEEP_SCENARIOS`` for argument choices without pulling the whole
combat engines into ``sys.modules``. Importing ``mordheim_combat`` here would
silently break the ``coverage-gate`` measurement of every pre-imported module
(tracer sees no executed bodies for modules compiled before ``cov.start()``).

Run/execution logic (``run_benchmark``, payloads, reports, progress) stays in
``benchmarking``; this module only defines *which* fighters each scenario
builds. ``compile_benchmark_fighters`` also stays in ``benchmarking``: it is
the one place where definitions meet the compiler.
"""
from __future__ import annotations

from dataclasses import dataclass

from mordheim_core.models import FighterBuild
from mordheim_core.models import Characteristics


@dataclass(frozen=True, slots=True)
class BenchmarkScenario:
    id: str
    first: FighterBuild
    second: FighterBuild
    maximum_rounds: int = 50
    # Benchmark-only attack tags let the matrix exercise a consumer whose
    # catalogue currently has no selectable producer (notably blessed
    # attacks), without changing the construction or combat implementations.
    first_attack_tags: tuple[str, ...] = ()
    second_attack_tags: tuple[str, ...] = ()

ORDINARY = Characteristics(3, 3, 3, 1, 3, 1)
VETERAN = Characteristics(4, 4, 4, 2, 4, 2)
DURABLE = Characteristics(2, 2, 5, 4, 2, 1)


def benchmark_scenarios() -> tuple[BenchmarkScenario, ...]:
    ordinary = ORDINARY
    veteran = VETERAN
    durable = DURABLE
    return (
        BenchmarkScenario(
            "basic",
            FighterBuild("mordheim", ordinary),
            FighterBuild("mordheim", ordinary),
        ),
        BenchmarkScenario(
            "multiattack",
            FighterBuild("mordheim", Characteristics(4, 4, 3, 2, 4, 3),
                         main_weapon_id="weapon.axe", off_hand_id="weapon.dagger"),
            FighterBuild("mordheim", veteran, armour_id="armour.heavy-armour"),
        ),
        BenchmarkScenario(
            "defences",
            FighterBuild("mordheim", veteran, main_weapon_id="weapon.sword",
                         off_hand_id="defence.buckler", armour_id="armour.light-armour"),
            FighterBuild("mordheim", veteran, main_weapon_id="weapon.dwarf-axe",
                         off_hand_id="defence.shield", armour_id="armour.gromril-armour"),
        ),
        BenchmarkScenario(
            "stateful",
            FighterBuild(
                "mordheim", band_id="pit-fighters", profile_id="pit-king",
                special_rule_ids=("band--pit-fighter-skill-force-of-will",),
            ),
            FighterBuild("mordheim", veteran, main_weapon_id="weapon.brazier-iron"),
        ),
        BenchmarkScenario(
            "long",
            FighterBuild("mordheim", durable, armour_id="armour.gromril-armour",
                         off_hand_id="defence.shield"),
            FighterBuild("mordheim", durable, armour_id="armour.gromril-armour",
                         off_hand_id="defence.shield"),
            maximum_rounds=75,
        ),
    )


def _build(*, characteristics=None, main_weapon_id: str = "weapon.dagger",
           off_hand_id: str | None = None, armour_id: str = "armour.no-armour",
           defence_ids: tuple[str, ...] = (), band_id: str | None = None,
           profile_id: str | None = None, special_rule_ids: tuple[str, ...] = (),
           skill_ids: tuple[str, ...] = (), trait_overrides: dict[str, object] | None = None,
           collection: str = "mordheim") -> FighterBuild:
    """Build a FighterBuild for the deep scenario matrix with explicit knobs.

    ``characteristics`` and the ``band_id``/``profile_id`` pair are mutually
    exclusive ways to describe the fighter (mirroring ``FighterBuild``); a
    characteristics-less profile build must never silently receive the
    ordinary profile.
    """
    if band_id is None and characteristics is None:
        characteristics = ORDINARY
    return FighterBuild(
        "mordheim", characteristics, band_id=band_id, profile_id=profile_id,
        main_weapon_id=main_weapon_id, off_hand_id=off_hand_id, armour_id=armour_id,
        defence_ids=defence_ids,        special_rule_ids=special_rule_ids,
        skill_ids=skill_ids, trait_overrides=trait_overrides or {}, collection=collection,
    )

DEEP_SCENARIOS: tuple[BenchmarkScenario, ...] = (
    # Standard certification families first (same ids as benchmark_scenarios).
    BenchmarkScenario("basic", _build(), _build()),
    BenchmarkScenario(
        "multiattack",
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe", off_hand_id="weapon.dagger"),
        _build(characteristics=VETERAN, armour_id="armour.heavy-armour"),
    ),
    BenchmarkScenario(
        "defences",
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               off_hand_id="defence.buckler", armour_id="armour.light-armour"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.dwarf-axe",
               off_hand_id="defence.shield", armour_id="armour.gromril-armour"),
    ),
    BenchmarkScenario(
        "stateful",
        _build(band_id="pit-fighters", profile_id="pit-king",
               special_rule_ids=("band--pit-fighter-skill-force-of-will",)),
        _build(characteristics=VETERAN, main_weapon_id="weapon.brazier-iron"),
    ),
    BenchmarkScenario(
        "long",
        _build(characteristics=DURABLE, armour_id="armour.gromril-armour",
               off_hand_id="defence.shield"),
        _build(characteristics=DURABLE, armour_id="armour.gromril-armour",
               off_hand_id="defence.shield"),
        maximum_rounds=75,
    ),
    # Archetype matrix: profiles x equipment families beyond the five core ones.
    BenchmarkScenario(
        "elite-vs-durable",
        _build(characteristics=Characteristics(5, 4, 4, 2, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
        _build(characteristics=DURABLE, armour_id="armour.gromril-armour",
               off_hand_id="defence.shield"),
    ),
    BenchmarkScenario(
        "axes-vs-light",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.axe"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               armour_id="armour.light-armour"),
    ),
    BenchmarkScenario(
        "glass-vs-tank",
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2)),
        _build(characteristics=DURABLE, armour_id="armour.heavy-armour",
               off_hand_id="defence.shield"),
    ),
    BenchmarkScenario(
        "two-weapons-vs-parry",
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               off_hand_id="weapon.dagger"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               off_hand_id="defence.buckler"),
    ),
    BenchmarkScenario(
        "heavy-clash",
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
    ),
    BenchmarkScenario(
        "fencer-mirror",
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    BenchmarkScenario(
        "brute-vs-fencer",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.axe"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    BenchmarkScenario(
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
    BenchmarkScenario(
        "sigmarite-vs-undead",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.sigmarite-hammer"),
        _build(band_id="tomb-guardians", profile_id="skeleton-warriors"),
    ),
    # 2. Regeneration (4+) blocked by fire: troll vs a burning brazier-iron.
    BenchmarkScenario(
        "regen-vs-fire",
        _build(band_id="orc-mob", profile_id="troll"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.brazier-iron"),
    ),
    # 3. Natural armour negated by magic + magical attacks + extra bite:
    #    lizardmen scaly skin vs a carnival daemon's attack.magical.
    BenchmarkScenario(
        "natural-armour-vs-magic",
        _build(band_id="lizardmen", profile_id="saurus-braves"),
        _build(band_id="carnival-of-chaos", profile_id="plague-bearers"),
    ),
    # 4. Pistols: ballistic-skilled shot, fixed strength, armour
    #    penetration and the crack-shot first-round path vs a parry defence.
    BenchmarkScenario(
        "pistol-vs-parry",
        _build(characteristics=VETERAN, main_weapon_id="weapon.duelling-pistol"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    # 5. Concussion + critical-injury bonus vs dwarfs: concussion
    #    immunity, hard-to-kill and the out-of-action threshold of 6.
    BenchmarkScenario(
        "concussion-vs-dwarf",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.draich"),
        _build(band_id="dwarf-rangers", profile_id="beardlings"),
    ),
    # 6. Frenzy + always strikes first: fanatic priority 10 and its
    #    frenzy-boosted attacks vs a shielded heavy.
    BenchmarkScenario(
        "frenzy-vs-heavy",
        _build(band_id="night-goblins-mic", profile_id="fanatics"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
    ),
    # 7. Paired poisoned blades (black-lotus auto-wound) vs a poison-
    #    immune undead beast: poison-blocked and paired-attack paths.
    BenchmarkScenario(
        "paired-poison-vs-undead",
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.weeping-blades"),
        _build(band_id="undead", profile_id="dire-wolves"),
    ),
    # 8. Two-handed great weapon: strength bonus, both hands occupied,
    #    initiative penalty vs gromril armour and a shield.
    BenchmarkScenario(
        "great-weapon-vs-tank",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.double-handed-weapon"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               armour_id="armour.gromril-armour", off_hand_id="defence.shield"),
    ),
    # 9. Ward save vs a magical attacker: enchanted skins against a
    #    daemon's attack.magical (also cloud of flies, poison immunity).
    BenchmarkScenario(
        "ward-vs-magic",
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               defence_ids=("defence.enchanted-skins",)),
        _build(band_id="carnival-of-chaos", profile_id="nurglings"),
    ),
    # 10. Unarmed combat: fists/natural attacks, unarmed criticals and
    #     the monk strictures vs a cannot-be-parried whip.
    BenchmarkScenario(
        "unarmed-vs-steel",
        _build(band_id="battle-monks-of-cathay", profile_id="dragon-monks"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.steel-whip"),
    ),
    # 11. Injury profile 1 (out of action on 4+) vs an armour-ignoring
    #     weapon with an injury modifier (death-knife).
    BenchmarkScenario(
        "injury-profile-vs-death-knife",
        _build(band_id="night-goblins-web", profile_id="snotlings"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.death-knife"),
    ),
    # 12. Entangle: the chained squig's fixed-strength, cannot-be-parried
    #     attack entangles its victim vs a parrying fencer.
    BenchmarkScenario(
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
    # truncation sweep covers every deep pair, so resolution-timing
    # defects show at intermediate horizons even when aggregate rates
    # agree.
    # 13. Four hits per pool vs a single parry: the unparryable
    #     natural-6 co-occurrence (6 + another hit in the same pool)
    #     fires far more often than in two-weapons-vs-parry, so a
    #     wasted parry on a 6 moves the first-winner rate measurably.
    BenchmarkScenario(
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
    BenchmarkScenario(
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
    BenchmarkScenario(
        "frenzy-vs-w2",
        _build(band_id="night-goblins-mic", profile_id="fanatics"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe"),
    ),
    # 16. Mirror of elite-vs-durable with the durable side first: the
    #     unresolved rate stays ~1%, so the timing class is certified
    #     from both directions and any direction-dependent drift shows.
    BenchmarkScenario(
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
    BenchmarkScenario(
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
    BenchmarkScenario(
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
    BenchmarkScenario(
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
    BenchmarkScenario(
        "cathayan-longsword-vs-sword",
        _build(characteristics=Characteristics(4, 4, 3, 2, 4, 2),
               main_weapon_id="weapon.cathayan-longsword"),
        _build(characteristics=Characteristics(4, 4, 3, 2, 4, 2),
               main_weapon_id="weapon.sword"),
    ),
    # 21. The runtime has a blessed-regeneration consumer but no selectable
    #     blessed weapon in the current KB.  The attack tag is therefore a
    #     benchmark-only synthetic input; construction and engine code stay
    #     untouched while the Strigoi regeneration blocker is exercised.
    #     Modular calibration (seed 2026, 10k duels): 23.720% / 76.280% /
    #     0.000% first wins / second wins / unresolved.
    BenchmarkScenario(
        "blessed-vs-regen",
        _build(characteristics=Characteristics(4, 4, 4, 2, 4, 2),
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
    # to this benchmark matrix and do not alter the KB or combat engines.
    # 22. Khemri's fragile profile 3 against the last-wound profile 4.
    BenchmarkScenario(
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
    BenchmarkScenario(
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
    BenchmarkScenario(
        "resilient-vs-high-strength",
        _build(characteristics=Characteristics(4, 4, 5, 2, 4, 2),
               main_weapon_id="weapon.sword", skill_ids=("skill.resilient",)),
        _build(characteristics=Characteristics(4, 5, 4, 2, 3, 2),
               main_weapon_id="weapon.double-handed-weapon"),
    ),
    # 25. Charging WS and charging Strength bonuses on the same attacker.
    BenchmarkScenario(
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
    # intentionally benchmark-only because no single legal profile combines
    # these equipment families.
    BenchmarkScenario(
        "first-round-opener",
        _build(characteristics=Characteristics(4, 4, 4, 2, 5, 2),
               main_weapon_id="weapon.chain-sticks",
               trait_overrides={"first_round_charge_attack_bonus": True}),
        _build(characteristics=Characteristics(4, 4, 4, 2, 4, 2),
               main_weapon_id="weapon.flail",
               skill_ids=("skill.strength-of-steel",)),
    ),
    # 27. Condemned's per-duel random WS/S/T/A values versus a stable profile.
    BenchmarkScenario(
        "random-characteristics-vs-stable",
        _build(band_id="marauders-of-chaos", profile_id="condemned",
               main_weapon_id="weapon.natural-attacks"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword"),
    ),
    # 28. Bear Hug needs two successful hits; the benchmark-only fire tag also
    # makes the Scarecrow's caught-fire threshold observable in normal hits.
    BenchmarkScenario(
        "trained-bear-vs-scarecrow",
        _build(band_id="kislevites", profile_id="trained-bear"),
        _build(band_id="restless-dead", profile_id="scarecrows"),
        first_attack_tags=("attack.fire",),
    ),
    # 29. Silent Walker supplies a 5+ mundane-only ward; Cold One Beasthounds
    # supply unmodified natural armour. The magical attack tag intentionally
    # covers the ward-negation branch; the mundane ward branch remains a
    # documented follow-up because this is one pair, not two variants.
    BenchmarkScenario(
        "silent-walker-vs-cold-one",
        _build(band_id="lustria-pygmies", profile_id="silent-walker",
               main_weapon_id="weapon.dagger", collection="trollheim"),
        _build(band_id="dark-elves", profile_id="cold-one-beasthounds",
               main_weapon_id="weapon.natural-attacks"),
        second_attack_tags=("attack.magical",),
    ),

)


# The full matrix remains the default and is intentionally stable: several
# triage tools and historical regression probes refer to these ids directly.
FULL_DEEP_SCENARIO_IDS: tuple[str, ...] = tuple(
    scenario.id for scenario in DEEP_SCENARIOS
)

# Fast certification keeps one representative of every currently covered
# mechanic family, while dropping pure baselines, mirrors and stronger/weaker
# duplicates.  It also keeps the three known orchestration amplifiers, the
# long-round timing/Ithilmar representatives and the four recently added
# coverage boundaries.  The set is deliberately expressed as ids rather than
# a second copy of the scenario definitions.
FAST_DEEP_SCENARIO_IDS: tuple[str, ...] = (
    "defences",
    "stateful",
    "sigmarite-vs-undead",
    "regen-vs-fire",
    "natural-armour-vs-magic",
    "pistol-vs-parry",
    "concussion-vs-dwarf",
    "paired-poison-vs-undead",
    "ward-vs-magic",
    "unarmed-vs-steel",
    "injury-profile-vs-death-knife",
    "entangle-vs-fencer",
    "triple-weapon-vs-parry",
    "a2-vs-w1-stun",
    "frenzy-vs-w2",
    "elite-vs-durable",
    "heavy-grind",
    "ithilmar-duel",
    "skills-vs-hitter",
    "helmet-vs-injury-profile-2",
    "cathayan-longsword-vs-sword",
    "blessed-vs-regen",
    "injury-profile-3-vs-4",
    "skill-stack-vs-hitter",
    "resilient-vs-high-strength",
    "charge-skills-vs-tank",
    "first-round-opener",
    "random-characteristics-vs-stable",
    "trained-bear-vs-scarecrow",
    "silent-walker-vs-cold-one",
)

# Mini selection: one cheap pair for every cost/behaviour axis a numpy<->native
# performance sweep should observe without paying for a full certification
# matrix. Expressed as ids, like the fast set.
MINI_DEEP_SCENARIO_IDS: tuple[str, ...] = (
    "basic",                      # cheapest duel: per-batch fixed overhead
    "multiattack",                # typical mid-size attack pool
    "heavy-grind",                # 75-round grind: the most expensive scenario
    "sigmarite-vs-undead",        # conditional extra attacks + undead interaction
    "regen-vs-fire",              # special saves (regeneration blocked by fire)
    "natural-armour-vs-magic",    # stacked save layers + extra bite
    "paired-poison-vs-undead",    # auto-wound poison + paired weapons
    "frenzy-vs-w2",               # frenzy doubles the pool size
    "entangle-vs-fencer",         # pool manipulation with reaction logic
    "random-characteristics-vs-stable",  # per-duel random characteristics path
)

DEEP_SCENARIO_SET_IDS: dict[str, tuple[str, ...]] = {
    "mini": MINI_DEEP_SCENARIO_IDS,
    "fast": FAST_DEEP_SCENARIO_IDS,
    "full": FULL_DEEP_SCENARIO_IDS,
}

def deep_test_scenarios(pair_set: str = "full") -> tuple[BenchmarkScenario, ...]:
    """Return one of the maintained deep-testing pair sets.

    ``full`` is the maintained 42-pair matrix. ``fast`` is a 30-pair
    coverage-oriented subset: it retains every distinct non-default compiled
    effect axis represented by the current full matrix (including the
    synthetic blessed boundary), the long-round timing representative, the
    high-value orchestration amplifiers and every newly added rule-family
    boundary, while omitting redundant baselines and mirrors. It deliberately
    keeps ``heavy-grind`` and ``ithilmar-duel`` because they add the only
    long-round and Ithilmar axes otherwise lost from the fast set.

    ``mini`` is a 10-pair performance-survey subset: one cheap-to-expensive
    representative per cost axis (batch overhead, typical pool, 75-round
    grind) and per behaviour family (conditional attacks, special saves,
    stacked saves, poison, frenzy, pool manipulation, random
    characteristics).

    The set selection is benchmark metadata only. It does not alter fighter
    construction or any combat/KB implementation. ``blessed-vs-regen`` still
    uses the benchmark-only ``attack.blessed`` tag described above.
    """
    try:
        selected_ids = DEEP_SCENARIO_SET_IDS[pair_set]
    except KeyError as error:
        raise ValueError(
            f"unknown deep pair set {pair_set!r}; choose 'mini', 'fast' or 'full'"
        ) from error
    by_id = {scenario.id: scenario for scenario in DEEP_SCENARIOS}
    return tuple(by_id[scenario_id] for scenario_id in selected_ids)
