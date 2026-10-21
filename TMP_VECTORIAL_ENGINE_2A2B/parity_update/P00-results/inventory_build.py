"""Build the P00 behaviour/variant inventory from registry + reconciliation.

The inventory is a design snapshot: one row per admitted runtime key, mapped to
the decisive modular operator and to a concrete behaviour/variant obligation.
It never writes the registry and never imports an engine.
"""
from __future__ import annotations

import collections
import csv
import json
import re
from pathlib import Path

from stage_probe import stage

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "sources/knowledge/verification/clause-contracts.csv"
RECON = Path(__file__).resolve().parent / "universe-reconciliation.csv"
OUT = Path(__file__).resolve().parent / "behaviour-inventory.csv"
SUMMARY = Path(__file__).resolve().parent / "behaviour-summary.txt"

BASE = "operator-base"
CASE = "case-preparable"
PEND_OBS = "pending-observable"
PEND_INPUT = "pending-input"
PEND_RULE = "pending-rule"
STRUCT = "structural"
DEFECT = "check-defect"
AMBIG = "consumer-ambiguous"

#: Variants that revision 3 used as catch-alls.  They are never a fallback:
#: every key that used to land here has an explicit decision below.
GENERIC_IDS = {
    "B01.5", "B03.6", "B04.5", "B05.3", "B06.4", "B07.4",
    "B08.5", "B11.4", "B11.7", "B12.3", "B14.4", "B15.3",
}

#: Variants whose keys are separated by their effect contract.  The split is
#: applied only to keys currently assigned to the source variant.
SPLIT_SOURCES = {"B11.2", "B14.1", "B15.2"}

#: Revision 3 numbers reused by the corrected split.  These source variants are
#: moved intact so the new number means one contract only.
MOVED_SOURCES = {
    "B11.3": "B11.6",   # Fear rerolls and modifiers, not Psychology immunity
    "B14.2": "B14.9",   # Leadership reroll auras, not the 12-inch radius
    "B14.3": "B14.13",  # Leadership modifiers, not automatic success
}

SPLIT_EFFECT = {
    # B11: immunity, automatic state and test-dice conventions are different.
    "mechanic.fear-immunity": "B11.2",
    "mechanic.psychology-immunity": "B11.3",
    "mechanic.accustomed-to-fear": "B11.4",
    "mechanic.fear-immunity-undead-chargers": "B11.4",
    "mechanic.cold-blooded-psychology": "B11.5",
    # A frenzy granted by an event is not an initial flag: it is gained after
    # taking an enemy out of action (Great Thirster) or while the followed
    # Vampire is down or killed (Devoted), and lost on its own conditions.
    "mechanic.great-thirster": "B11.7",
    # B14: radius, automatic pass, own value, handler, ally bonus, dice and auras.
    "mechanic.leader-six": "B14.1",
    "mechanic.leader-twelve": "B14.2",
    "mechanic.automatic-leadership": "B14.3",
    "mechanic.own-leadership": "B14.4",
    "mechanic.handler-leadership": "B14.5",
    "mechanic.mob-leadership": "B14.6",
    "mechanic.brood-mentality": "B14.7",
    "mechanic.cold-blooded-leadership": "B14.8",
    "mechanic.undivided-leader": "B14.9",
    "mechanic.wizened-halfling": "B14.9",
    "mechanic.songster": "B14.9",
    "mechanic.devoted": "B14.9",
    "condition.command.raise-our-insignia": "B14.9",
    "mechanic.relay-orders": "B14.10",
    "defence.holy-relic": "B14.11",
    "mechanic.slave-driver": "B14.12",
    "condition.poetry-victorious-leader": "B14.1",
    # B15: recovery, wound maximum, damage reactions and wound side effects.
    "mechanic.curse-of-the-revenant": "B15.2",
    "trait.spines": "B15.4",
    "spines": "B15.4",
    "trait.acid-blood": "B15.4",
    "acid_blood": "B15.4",
    "trait.contagious": "B15.5",
    "mechanic.torturer": "B15.6",
    "skill.monstrous": "B15.3",
}

#: Explicit decisions for every key that revision 3 left in an ``other`` group.
#: The grouping follows the admitted contract, not a substring or a shared
#: consumer.  Effects with one contract share an entry; the key overrides below
#: separate the clauses that do not.
OTHER_EFFECT = {
    "mechanic.shallya-strictures": "B01.5",
    "mechanic.veskit-no-pain": "B07.1",
    "mechanic.inured-to-pain": "B07.3",
    "weapon.arcane-candelabrum": "B03.5",
    "weapon.axe": "B04.1",
    "weapon.bagh-nakh": "B08.2",
    "weapon.cathayan-longsword": "B02.4",
    "weapon.choppa": "B03.3",
    "weapon.cleaver": "B04.1",
    "weapon.dagger": "B04.1",
    "weapon.duelling-pistol": "B02.4",
    "weapon.great-scimitar": "B03.3",
    "material.gromril": "B04.1",
    "weapon.katar": "B04.1",
    "weapon.misericordia": "B04.1",
    "weapon.pistol": "B08.1",
    "weapon.scythe": "B04.1",
    "weapon.shortsword": "B06.1",
    "weapon.starsword": "B06.1",
    "material.normal": "B04.1",
    "mechanic.norse-shieldmaster": "B06.2",
    "skill.shield-mastery": "B06.2",
    "skill.shield-strike": "B08.2",
    "skill.unarmed-fighting": "B08.4",
    "weapon.sun-gauntlet": "B08.1",
    "trait.perfect-killer": "B04.1",
    "weapon.mace": "B07.3",
    "weapon.veskit-claws": "B03.3",
    "rule.slay-large-creature": "B03.3",
    "dance.the-shadows-coil": "B05.1",
    "mechanic.bestial": "B05.1",
    "mechanic.killing-blow": "B02.4",
    "weapon.ladle": "B04.1",
    "hireling.dramatis.marquand": "B01.1",
    "weapon.claw-of-the-old-ones": "B06.1",
    "weapon.dwarf-axe": "B06.1",
    "weapon.elven-greatsword": "B06.1",
    "weapon.katana": "B06.1",
    "weapon.pry-bar": "B06.1",
    "weapon.starblade": "B06.1",
    "weapon.witch-sword": "B06.1",
    "weapon.wizards-staff": "B06.1",
    "weapon.ball-and-chain": "B03.3",
    "weapon.bo": "B08.2",
    "weapon.double-bladed-sword": "B06.2",
    "weapon.scimitar": "B06.1",
    "weapon.unholy-sword": "B06.1",
    "weapon.war-maul": "B06.3",
    "weapon.weeping-blades": "B06.1",
    "weapon.yari-one-handed": "B06.1",
    "weapon.yari-two-handed": "B10.1",
    "mechanic.estalian-technique": "B06.1",
    "weapon.ienh-khain": "B06.1",
    "acid_blood": "B15.4",
    "dance.whirling-death": "B07.3",
    "mechanic.energy-focus": "B03.3",
    "weapon.censer": "B03.3",
    "weapon.flail": "B03.3",
    "weapon.vomit-attack": "B08.5",
    "skill.shifty": "B10.1",
    "mechanic.crude-belch-ogre": "B02.4",
    "band--mutations-tentacle": "B08.5",
    "mechanic.giggle-juice-spray": "B08.5",
    "mechanic.snorri-drunk": "B01.3",
    "mechanic.centaur-trample": "B08.2",
    "mechanic.emissary-khorne": "B08.2",
    "mechanic.hatred-undead": "B02.2",
    "mechanic.disability": "B12.1",
    "defence.holy-relic": "B14.11",
    "mechanic.devoted-to-the-vampire": "B11.7",
    "mechanic.devoted-killer-hatred": "B02.2",
    "condition.command.art-thou-ready-to-die-fighting": "B07.1",
    "condition.command.follow-me-mine-pugnacious-ones": "B02.4",
    "spines": "B15.4",
}

#: Keys whose selected operator and printed contract disagree.  Applied after
#: the variant is resolved, so a contract decision is not overridden by the
#: consumer pipeline that located the key.
FORCED_KEYS = {
    # Gains Frenzy after taking an enemy out of action, and loses it when
    # knocked down, stunned or out; the wound stage only located the key.
    "mechanic/mechanic.great-thirster::whole": "B11.7",
    "rule/mordheim/survivors-of-strigos-sylv/strigoi-vampire--great-thirster/mechanic.great-thirster::whole": "B11.7",
}

KEY_OVERRIDE = {
    "rule/mordheim/black-orcs/orc-nuttaz--savage/profile.equipment-restrictions::mandatory-charge": "B01.5",
    "rule/mordheim/marauders-of-chaos/condemned--inconsistency/profile.random-characteristics::whole": "B01.6",
    "source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified::advancement-lift": "B01.6",
    "source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified::whole--scope--equipment-ban-variable-state": "B09.1",
    "source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified::whole--scope--unarmed-penalty-waiver": "B08.4",
    "source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan.pending-duel::witch-finder--scope--compulsory-charge": "B01.5",
    "source/catalog/hirelings/dramatis-personae/grade-1c.yaml/hireling.dramatis.belandysh-condemned-champion-of-chen.rule.regeneration/unclassified::regeneration-four-plus-blocked-by-fire": "B05.2",
    "core/combat-parry::parry-attempt": "B06.1",
    "core/combat-parry::reroll-and-capacity": "B06.2",
    "source/bands/mordheim/dark-elf-corsairs-mou/profiles.yaml/@/profiles/6/equipment_restrictions/0/unclassified::weapons-and-save": "B05.1",
    "rule/mordheim/tomb-guardians/tomb-scorpions--living/unimplemented.tomb-guardians.tomb-scorpions.living::living": "B11.1",
    "rule/trollheim/khemri-tomb-guardians/tomb-scorpions--living/unimplemented.khemri-tomb-guardians.tomb-scorpions.living::living": "B11.1",
    "source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/1/equipment/fixed_items/0/notes/unclassified::beastlash-beastbane": "B11.1",
    "source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan.pending-duel::witch-finder--scope--inquisitor-state": "B11.3",
    "source/catalog/rules/special-rules.yaml/shared-rule.ere-we-go/unclassified::ere-we-go": "B11.4",
    "rule/mordheim/call-of-the-night-haint-mim/tomb-banshee--ghostly-howl/unimplemented.call-of-the-night-haint-mim.tomb-banshee.ghostly-howl::ghostly-howl": "B11.6",
    "mechanic/mechanic.disability::no-two-weapons-or-weapon-and-shield": "B09.1",
    "mechanic/mechanic.disability::permanent-characteristic-penalty": "B01.1",
    "rule/trollheim/chaos-streets-mordheim-inhabitants/cripples--disability/compiler.disability::no-two-weapons-or-weapon-and-shield": "B09.1",
    "rule/trollheim/chaos-streets-mordheim-inhabitants/cripples--disability/compiler.disability::permanent-characteristic-penalty": "B01.1",
    "mechanic/mechanic.disability::head-injury-stupidity": "B12.1",
    "rule/trollheim/chaos-streets-mordheim-inhabitants/cripples--disability/compiler.disability::head-injury-stupidity": "B12.1",
}

#: Metadata for the variants created or renamed by this correction.  Existing
#: variants keep their entry in ``VARIANTS``.
VARIANT_META = {
    "B01.5": ("B01-initial-state", "compulsory charge or attack restriction",
              PEND_INPUT, "E2E initial_state/duel_context; Shallya and compulsory-charge clauses",
              "G00/G02: supplied pre-battle restriction; G06: per-row target/charge state"),
    "B01.6": ("B01-initial-state", "random characteristic or advancement state",
              PEND_INPUT, "E2E condemned--inconsistency and marauders advancement",
              "G00/G02: supplied initial values; G06: per-turn rolled characteristic"),
    "B11.7": ("B11-fear", "conditional frenzy (Devoted, Great Thirster)",
              PEND_OBS, "E2E devoted-to-the-vampire and great-thirster scenarios",
              "G02/G06: frenzy flag per row; loss on knocked down, stunned or out"),
    "B08.5": ("B08-attack-pool", "attack replacement or opponent attack-pool modifier",
              PEND_RULE, "E2E vomit/tentacle/giggle-juice situations",
              "G03/G04: attack replacement and incoming-attack modifier witness"),
    "B11.2": ("B11-fear", "full Fear immunity (no Fear test)",
              PEND_OBS, "E2E fear-immunity scenarios; no exact operator check",
              "G05/G06: fear-test absence flag for the immune fighter"),
    "B11.3": ("B11-fear", "complete Psychology immunity",
              PEND_OBS, "E2E psychology-immunity scenarios",
              "G05/G06: psychology-test absence flag for the immune fighter"),
    "B11.4": ("B11-fear", "conditional Fear immunity (identity or charge condition)",
              PEND_OBS, "E2E accustomed-to-fear and undead-charger scenarios",
              "G05/G06: identity/charge condition and fear-test absence; positive control with another enemy"),
    "B11.5": ("B11-fear", "Cold-Blooded Psychology: 3D6 keep lowest two",
              PEND_OBS, "E2E cold-blooded-psychology scenarios",
              "G05/G06: test still occurs; witness the three dice and the discarded highest"),
    "B11.6": ("B11-fear", "Fear reroll and Fear-test modifiers",
              PEND_OBS, "E2E fear-reroll/craven/opposite-sex/Slaanesh scenarios",
              "G05/G06: reroll or modifier witness per Fear test"),
    "B14.1": ("B14-leadership", "supplied leader within 6 inches lends Leadership",
              PEND_OBS, "E2E serpent-priestess--leader::a-supplied-leader-at-six-inches-lends-his-leadership",
              "G05/G06: local Leadership value and eligible provider; no third fighter required for the own-value control"),
    "B14.2": ("B14-leadership", "supplied leader within 12 inches lends Leadership",
              PEND_OBS, "E2E inspiring-presence scenarios",
              "G05/G06: 12-inch eligibility and borrowed value"),
    "B14.3": ("B14-leadership", "automatic Leadership success (no test, no radius)",
              PEND_OBS, "E2E automatic-leadership scenarios",
              "G05/G06: auto-pass flag; no nearby leader or ally prerequisite"),
    "B14.4": ("B14-leadership", "own Leadership only; leader borrowing prohibited",
              PEND_OBS, "E2E raging-peasants mob no-leader-benefit",
              "G05/G06: own value used while a nearby leader is present; control without the prohibition"),
    "B14.5": ("B14-leadership", "eligible handler within 6 inches; never the warband leader",
              PEND_OBS, "E2E handler-leadership scenarios",
              "G05/G06: handler identity/value and 6-inch distance; control with an ordinary leader"),
    "B14.6": ("B14-leadership", "per-allied-fighter Leadership bonus before the test",
              PEND_OBS, "E2E raging-peasants mob individual-leadership-bonus",
              "G05/G06: supplied ally count within 3 inches and the raised own value"),
    "B14.7": ("B14-leadership", "Brood Mentality bonus to Stupidity Leadership only",
              PEND_OBS, "E2E brood-mentality scenarios",
              "G05/G06: supplied bonus applied only to the Stupidity test"),
    "B14.8": ("B14-leadership", "Cold-Blooded Leadership: 3D6 keep lowest two",
              PEND_OBS, "E2E cold-blooded-leadership scenarios",
              "G05/G06: test still occurs; witness the three dice and the discarded highest"),
    "B14.9": ("B14-leadership", "Leadership reroll auras and supplied rerolls",
              PEND_OBS, "E2E leadership reroll/undivided/songster/devoted scenarios",
              "G05/G06: reroll witness and provider eligibility/radius"),
    "B14.10": ("B14-leadership", "relay orders: leader value through an adjacent relay within 6 inches",
              PEND_OBS, "E2E relay-orders scenarios",
              "G05/G06: relay identity and distance; the relay never lends its own value"),
    "B14.11": ("B14-leadership", "holy relic: automatically pass the first Leadership test",
              PEND_OBS, "E2E holy-relic scenarios",
              "G05/G06: first-test auto-pass flag; second test is not automatic"),
    "B14.12": ("B14-leadership", "slave driver: supplied overseer value within 3/6 inches",
              PEND_OBS, "E2E slave-driver scenarios",
              "G05/G06: overseer value and source range; ordinary leader borrowing is not used"),
    "B14.13": ("B14-leadership", "Leadership modifiers and penalties",
              PEND_OBS, "E2E broken-spirit/feral-instinct/massively-built scenarios",
              "G05/G06: modifier witness per test; not inferred from terminal wounds"),
    "B15.2": ("B15-aftermath", "revenant recovery at the start of the own turn",
              CASE, "E2E curse-of-the-revenant::a-five-restores-one-lost-wound-at-the-own-turn-start",
              "G06: one 5+ attempt per own turn, capped at the starting total; regeneration save stays B05.2"),
    "B15.3": ("B15-aftermath", "wound maximum increased by the rule",
              PEND_INPUT, "E2E skill.monstrous scenarios",
              "G00/G02: starting Wounds and recoverable maximum; not a healing event"),
    "B15.4": ("B15-aftermath", "damage reaction to losing a wound or to base contact",
              CASE, "E2E acid-blood and spines situations",
              "G03/G06: automatic hit, Strength, no-critical and exact trigger: start of phase vs after losing a wound"),
    "B15.5": ("B15-aftermath", "out-of-action reaction (contagious)",
              PEND_RULE, "E2E contagious scenarios",
              "G06: established out-of-action result, Toughness test and automatic wound; Undead/Possessed exempt"),
    "B15.6": ("B15-aftermath", "wound-triggered characteristic loss (torturer)",
              PEND_OBS, "E2E torturer scenarios",
              "G02/G06: defender Strength after each unsaved wound, cumulative to a minimum of 1"),
}


def symbols(consumer: str) -> set[str]:
    try:
        parts = json.loads(consumer)
    except json.JSONDecodeError:
        parts = [consumer]
    if isinstance(parts, str):
        parts = [parts]
    found: set[str] = set()
    for part in parts:
        if "::" in part:
            found.add(part.split("::")[-1].strip())
        elif "." in part:
            found.add(part.rsplit(".", 1)[-1].strip())
    return found


# (variant id, behaviour, name, predicate, status, reference, dependency)
VARIANTS = (
    # -- B00 routing (not a combat rule) ------------------------------------
    ("B00.1", "B00-routing", "registered key with no runtime operator",
     lambda e, s, f: True,
     STRUCT, "verification/consumers.py::MODULAR_TAG_CONSUMERS",
     "none: routing/admission only; never a duel case"),
    # -- B01 initialization and resources -----------------------------------
    ("B01.1", "B01-initial-state", "profile and characteristic initialization",
     lambda e, s, f: e in {
         "profile.characteristics", "profile.item-modifiers", "profile.skill-access",
         "profile.fist", "mechanic.inconsistency", "mechanic.disability",
         "mechanic.guiding-dream", "mechanic.psychology-immunity",
     },
     PEND_INPUT, "E2E initial_state corpus; contract_probe.py",
     "G00/G02: public initial-state entry; G06: per-row initial fields"),
    ("B01.2", "B01-initial-state", "one-shot resource spend",
     lambda e, s, f: e in {
         "skill.luck", "defence.lucky-charm", "mechanic.force-of-will",
         "mechanic.mark-of-the-old-ones", "mechanic.ranalds-luck",
         "mechanic.snorri-lucky", "mechanic.augur-one-roll-reroll",
     },
     PEND_OBS, "test_duel_replay.py compares resources in exact replay",
     "G06: publish resources in ObservedDuelResult; G02: export resource arrays"),
    ("B01.3", "B01-initial-state", "initial condition or preparation",
     lambda e, s, f: e.startswith("condition.") or e.startswith("preparation.")
     or e == "profile.equipment-restrictions",
     PEND_INPUT, "E2E scenarios with initial_state/duel_context",
     "G00/G02: initial-state injection; absence variant needs the same build without it"),
    ("B01.5", "B01-initial-state", "other initialization-stage rules",
     lambda e, s, f: True,
     PEND_INPUT, "E2E initial_state corpus",
     "G00/G02: public initial-state entry; G06: per-row initial fields"),
    # -- B02 hit -------------------------------------------------------------
    ("B02.1", "B02-hit", "to-hit table and WS boundaries",
     lambda e, s, f: e == "proposed.core.combat-order",
     BASE, "exact operator check hit-targets (11x11 grid, WS 0 and 2x boundary)",
     "none for the table; modifiers and rerolls are separate variants"),
    ("B02.2", "B02-hit", "hatred and first-round hit modifiers",
     lambda e, s, f: "hatred" in e or e in {
         "skill.berserker", "skill.ferocious-charge", "mechanic.bestial",
         "skill.infinite-hatred", "mechanic.kindred-hatred",
     },
     PEND_RULE, "E2E hatred/berserk scenarios; no exact operator check",
     "G03/G06: per-attack hit modifier witness; terminal wounds cannot prove it"),
    ("B02.3", "B02-hit", "hit reroll and defence interaction",
     lambda e, s, f: "_hit_reroll" in s or e in {
         "skill.expert-swordsman", "skill.duellist", "mechanic.amazon-isolationists",
     },
     PEND_RULE, "E2E parry/reroll scenarios; no exact operator check",
     "G03/G06: per-attack reroll witness; do not infer from terminal condition"),
    ("B02.4", "B02-hit", "general to-hit modifiers",
     lambda e, s, f: True,
     PEND_RULE, "semantic fixtures cover individual adapters; E2E situations exist",
     "G03/G06: per-attack hit-target witness or an operator grid row for the effect"),
    # -- B03 wound and strength ---------------------------------------------
    ("B03.1", "B03-wound", "wound table and strength/toughness boundary",
     lambda e, s, f: e == "__no_key__",
     BASE, "exact operator check wound-targets (11x11 grid)",
     "none for the table"),
    ("B03.2", "B03-wound", "poison and poison immunity",
     lambda e, s, f: "poison" in e or e == "trait.poison-immune",
     PEND_RULE, "E2E poison scenarios; semantic fixtures for poison",
     "G03/G06: wound-roll witness or per-attack outcome; poison immunity is not a terminal wound"),
    ("B03.3", "B03-wound", "strength modifiers",
     lambda e, s, f: "_attack_strength" in s or e in {
         "skill.mighty-biceps", "skill.iron-sinews", "skill.strength-of-steel",
         "weapon.double-handed-weapon", "mechanic.titanic-strength",
         "skill.monster-slayer", "skill.monster-slayer-effective-strength-armour",
         "mechanic.retain-flail-morning-star-strength-bonus", "skill.strongman",
     },
     PEND_RULE, "semantic strength fixtures; exact wound table does not exercise modifiers",
     "G03/G06: effective-strength witness per attack"),
    ("B03.4", "B03-wound", "wound reroll and damage modifiers",
     lambda e, s, f: "prepare_wound_context" in s or "_resolve_wound_damage" in s,
     PEND_RULE, "semantic wound fixtures; E2E situations",
     "G03/G06: wound-roll/damage witness; terminal wounds cannot locate the modifier"),
    ("B03.5", "B03-wound", "conditional damage (fire, flammable, critical)",
     lambda e, s, f: e in {
         "trait.flammable", "weapon.brazier-iron", "trait.caught-fire-threshold",
         "skill.strike-to-injure", "mechanic.wolf-rat-bite", "mechanic.wraith-touch",
     },
     PEND_RULE, "E2E flammable/fire scenarios",
     "G03/G06: damage or condition witness tied to the trigger; not generic wounds"),
    ("B03.6", "B03-wound", "other wound-stage rules",
     lambda e, s, f: True,
     PEND_RULE, "E2E/semantic situations by effect",
     "G03/G06: witness or operator grid row for the specific effect"),
    # -- B04 armour ----------------------------------------------------------
    ("B04.1", "B04-armour", "ordinary armour, shield and penetration",
     lambda e, s, f: (e.startswith("armour.") or e.startswith("defence.")
                      or e in {
                          "mechanic.armour-save-bonus", "mechanic.iron-cage",
                          "mechanic.norse-bulwark", "mechanic.untiring",
                          "trait.magical-attacks", "mechanic.killing-blow",
                          "skill.cutthroat", "mechanic.sea-troll-slime",
                      }),
     BASE, "exact operator check armour (default/light/heavy/gromril + shield + 4 effects)",
     "none for the tested harness; other armour effects need their own grid row"),
    ("B04.2", "B04-armour", "natural armour save, stacks, worst and unmodified",
     lambda e, s, f: "natural-armour" in e,
     PEND_RULE, "98 shared-operator keys; exact armour check does not include natural armour",
     "G03: extend the armour operator grid with the natural-armour fields; owner G03/G04"),
    ("B04.3", "B04-armour", "buckler does not improve armour",
     lambda e, s, f: e in {"defence.buckler", "trait.counts-as-buckler", "trait.counts-as-shield"},
     PEND_RULE, "98 shared-operator keys; no exact armour variant for buckler",
     "G03/G04: armour grid row for buckler; parry capacity is a separate obligation"),
    ("B04.4", "B04-armour", "armour negation and strength cap",
     lambda e, s, f: e in {
         "trait.natural-armour-negated-by-magic", "skill.monster-slayer",
         "skill.monster-slayer-effective-strength-armour",
     },
     PEND_RULE, "98 shared-operator keys; armour check has one magical effect only",
     "G03/G04: grid rows for negation and caps"),
    ("B04.5", "B04-armour", "other armour-stage rules",
     lambda e, s, f: True,
     PEND_RULE, "E2E/98 shared-operator keys by effect",
     "G03/G04: grid row or directed case for the effect"),
    # -- B05 special save ----------------------------------------------------
    ("B05.1", "B05-special-save", "ward, step-aside and ethereal save",
     lambda e, s, f: e in {
         "trait.ward-save", "trait.ward-save-mundane-only", "skill.step-aside",
         "skill.elven-agility", "skill.vampire-reflexes", "defence.enchanted-skins",
         "mechanic.gypsy-ward", "defence.all-seeing-eye-of-numas",
         "mechanic.magical-void", "preparation.warpaint", "skill.dodge-sidestepper",
         "mechanic.snorri-lucky",
     } or "ethereal" in e,
     PEND_RULE, "E2E ward/ethereal scenarios; no exact special-save check",
     "G03/G06: special-save target/outcome witness; not terminal wounds"),
    ("B05.2", "B05-special-save", "regeneration and its blockers",
     lambda e, s, f: "regeneration" in e,
     PEND_RULE, "E2E regeneration scenarios; no exact special-save check",
     "G03/G06: per-wound regeneration witness; fire/blessed blocker variants"),
    ("B05.3", "B05-special-save", "other special saves",
     lambda e, s, f: True,
     PEND_RULE, "E2E/semantic situations by effect",
     "G03/G06: special-save witness or operator grid row"),
    # -- B06 parry -----------------------------------------------------------
    ("B06.1", "B06-parry", "parry attempt",
     lambda e, s, f: e in {
         "weapon.sword", "weapon.cathayan-longsword", "weapon.cutlass",
         "weapon.rapier", "weapon.serpent-staff", "weapon.fighting-claws",
         "weapon.long-daggers", "weapon.pirate-scourge", "defence.buckler",
         "trait.counts-as-buckler", "skill.sword-master", "skill.swordmaster",
     },
     CASE, "E2E core/combat-parry::sword-parries-one-hit; P01 q04-parry-attempt",
     "G06: per-attack `parried` array; today only exact replay exposes it"),
    ("B06.2", "B06-parry", "parry reroll and capacity",
     lambda e, s, f: e in {
         "skill.unbeatable-warrior", "skill.miniath", "skill.shield-mastery",
         "skill.defensive-stance", "mechanic.norse-shieldmaster", "skill.axe-master",
         "skill.sword-master", "skill.swordmaster",
     },
     PEND_RULE, "E2E core/combat-parry::sword-and-buckler-reroll-a-failed-parry",
     "G06: parry capacity/reroll witness per attack; P01 c04-parry-reroll must declare buckler"),
    ("B06.3", "B06-parry", "parry denial and special weapons",
     lambda e, s, f: e in {
         "skill.crushing-blow", "weapon.beastlash", "weapon.spiked-gauntlet",
         "weapon.trident", "weapon.sword-breaker", "weapon.steel-whip",
         "mechanic.unpredictable-attack", "mechanic.iron-fan",
         "mechanic.main-gauche-modes",
     },
     PEND_RULE, "E2E parry-denial scenarios",
     "G06: per-attack parry denial witness"),
    ("B06.4", "B06-parry", "other parry-stage rules",
     lambda e, s, f: True,
     PEND_RULE, "E2E/semantic situations by effect",
     "G06: parry witness or operator grid row"),
    # -- B07 injury ----------------------------------------------------------
    ("B07.1", "B07-injury", "injury table and immunities",
     lambda e, s, f: e in {
         "skill.ignore-pain", "skill.hard-to-kill", "trait.concussion-immune",
         "skill.thick-skull", "skill.tough-as-steel", "skill.head-crusher",
         "mechanic.fen-hard-to-kill", "trait.injury-profile",
         "trait.fragile-halflings", "trait.survivor", "skill.jump-up",
         "mechanic.bat-injury-chart", "rule.squishy", "trait.poisonous-injury",
         "trait.injury-reroll-out", "poison.spider-spittle",
     },
     DEFECT, "exact check injury compares phases.injury_condition to itself; "
             "the vectorized injury_conditions projection is not exercised",
     "P03/owner of _vectorized.py: assert vectorized.injury_conditions against "
     "phases.injury_condition before claiming the injury operator"),
    ("B07.2", "B07-injury", "highest injury result and multiple wounds",
     lambda e, s, f: e in {"proposed.core.combat-critical-hits", "skill.web-of-steel"},
     CASE, "E2E core/combat-injury-states::highest-injury-result-applies; "
           "P01 c04-highest-injury has a broken e2e reference",
     "P01 must repair the identity; G06: per-wound condition sequence if one "
     "terminal condition is not discriminating"),
    ("B07.3", "B07-injury", "weapon-specific injury modifiers",
     lambda e, s, f: e.startswith("weapon.") or e.startswith("material."),
     CASE, "E2E injury scenarios by weapon; P01 injury cases",
     "G06: per-wound injury outcome; terminal condition can witness the table, "
     "but not the impact that caused it"),
    ("B07.4", "B07-injury", "other injury-stage rules",
     lambda e, s, f: True,
     PEND_RULE, "E2E/semantic situations by effect",
     "G06: injury witness or operator grid row"),
    # -- B08 attack pool -----------------------------------------------------
    ("B08.1", "B08-attack-pool", "base attack count, off hand and pistol",
     lambda e, s, f: e in {"proposed.core.combat-two-weapons", "weapon.pistol"},
     BASE, "exact operator check attack-pools (ordinary/dagger/pistol/frenzy x "
           "first_round x charging)",
     "none for the tested harness"),
    ("B08.2", "B08-attack-pool", "extra attacks and frenzy",
     lambda e, s, f: e == "trait.frenzy" or e in {
         "skill.extra-attack", "skill.red-fury", "mechanic.frantic",
         "mechanic.black-hunger", "mechanic.death-blow",
         "trait.charge-attack-bonus", "trait.first-round-charge-attack-bonus",
         "mechanic.sabretusk-charge", "mechanic.bull-charge",
         "mechanic.maddened-with-pain", "skill.art-of-silent-death",
         "skill.inspiring-sermon", "skill.web-of-steel",
         "mechanic.ravening-onslaught", "mechanic.anvil-head",
         "dance.storm-of-blades", "mechanic.spawn-special-attacks",
         "skill.sweep", "skill.crude-belch-halfling", "mechanic.whip-master",
         "mechanic.vomit-attack", "mechanic.gaoler-grapple", "mechanic.honorable",
         "mechanic.savage-fury", "condition.rememberer-kaz-support",
     },
     PEND_RULE, "98 shared-operator keys; exact attack-pools only covers frenzy flag",
     "G03: extend the attack-pool grid with the effect; owner G03/G04"),
    ("B08.3", "B08-attack-pool", "weapon-specific attack counts",
     lambda e, s, f: e in {
         "weapon.pike", "weapon.spear", "weapon.chain-sticks",
         "weapon.quarter-staff", "weapon.natural-attacks", "weapon.knuckledusters",
         "weapon.long-boat-hook", "weapon.squig-prodder", "weapon.starsword",
         "weapon.poisoned-daggers", "weapon.veskit-claws",
         "profile.natural-attacks",
     } or e.startswith("profile-rule."),
     PEND_RULE, "98 shared-operator keys; exact attack-pools has no weapon grid",
     "G03/G04: attack-count grid rows per weapon"),
    ("B08.4", "B08-attack-pool", "unarmed penalties and natural attacks",
     lambda e, s, f: e in {
         "skill.unarmed-fighting", "proposed.rule.unarmed-without-penalties",
         "weapon.fist", "mechanic.ogre-unarmed", "profile.fist",
     },
     PEND_RULE, "98 shared-operator keys; exact attack-pools has no unarmed row",
     "G03/G04: unarmed attack-count grid row"),
    ("B08.5", "B08-attack-pool", "other attack-pool rules",
     lambda e, s, f: True,
     PEND_RULE, "E2E/semantic situations by effect",
     "G03/G04: attack-count grid row or directed case"),
    # -- B09 equipment -------------------------------------------------------
    ("B09.1", "B09-equipment", "equipment restrictions (compile-time)",
     lambda e, s, f: e in {"profile.equipment-restrictions", "profile.item-modifiers"},
     STRUCT, "compiler/validate_loadout tests; shared construction",
     "none at runtime; P02 classifies a rejected build as INCOMPATIBLE:construction"),
    ("B09.2", "B09-equipment", "intra-duel equipment loss or transformation",
     lambda e, s, f: e == "mechanic.bitten-transform",
     PEND_INPUT, "E2E the-bitten--transform::transforming-casts-off-the-worn-armour",
     "G02/G06: equipment/profile observation; initial transform state"),
    ("B09.3", "B09-equipment", "netter, whip and weapon equipment state",
     lambda e, s, f: True,
     PEND_OBS, "E2E netter/beastlash scenarios",
     "G05/G06: net/whip condition per row"),
    # -- B10 round and order -------------------------------------------------
    ("B10.1", "B10-round-order", "priority and acting order",
     lambda e, s, f: e in {
         "proposed.core.combat-order", "skill.lightning-reflexes",
         "skill.always-strikes-first", "mechanic.strike-first-vs-skinks-always",
         "mechanic.strike-first-vs-skinks-first-round", "weapon.pike",
         "weapon.spear", "weapon.quarter-staff", "material.ithilmar",
         "skill.strongman", "mechanic.frantic", "weapon.trident",
         "dance.woven-mist",
     },
     BASE, "exact operator check priority (3 fighters x first_round/charging/charged/stood)",
     "the base grid is exact; lightning reflexes, strike-first and pike variants "
     "are not in it and remain pending"),
    ("B10.2", "B10-round-order", "stand-up and recovery order",
     lambda e, s, f: e in {
         "defence.helmet", "defence.cooking-pot-helmet", "skill.jump-up",
     } or "stand-up" in e,
     CASE, "E2E core/combat-injury-states::recovery-belongs-to-the-fighters-own-turn; "
           "P01 c04-stand-up-last",
     "terminal condition/rounds can witness recovery; per-round witness needs G06"),
    ("B10.3", "B10-round-order", "death-blow optional decision",
     lambda e, s, f: e == "mechanic.death-blow" or "death-blow" in e,
     CASE, "E2E mechanic.death-blow::the-bearer-declines-and-attacks-normally",
     "P01 must declare the decision key; missing decision is NOT_RUN:decision-script"),
    ("B10.4", "B10-round-order", "round state and per-round modifiers",
     lambda e, s, f: True,
     PEND_RULE, "E2E round/expect_rounds scenarios",
     "G06: round-indexed state; terminal rounds cannot locate a per-round modifier"),
    # -- B11 fear ------------------------------------------------------------
    ("B11.1", "B11-fear", "causes fear and the fear test",
     lambda e, s, f: e in {
         "mechanic.causes-fear", "mechanic.fear-human", "mechanic.fear-of-elves",
         "mechanic.fear-of-snakes", "mechanic.undead", "mechanic.undead-foes-no-fear",
         "mechanic.haunted-mien", "mechanic.lunatics", "mechanic.beauty-of-the-sea",
         "mechanic.enchanting-beauty", "mechanic.hypnotic-musk", "mechanic.scryer",
         "mechanic.morrs-servant", "weapon.beastlash", "weapon.chainsaw-sword",
         "condition.impetuous-charge", "preparation.elven-wine",
         "mechanic.ashamed-and-afraid",
     },
     PEND_OBS, "E2E minotaur--fear::a-charged-opponent-that-fails-its-fear-test-hits-only-with-sixes",
     "G05: execute the fear phase; G06: publish `fear-hit-sixes` per row"),
    ("B11.2", "B11-fear", "fear and psychology immunity",
     lambda e, s, f: e in {
         "mechanic.fear-immunity", "mechanic.psychology-immunity",
         "mechanic.accustomed-to-fear", "mechanic.cold-blooded-psychology",
         "mechanic.fear-immunity-undead-chargers", "mechanic.undead-foes-no-fear",
     },
     PEND_OBS, "E2E immunity scenarios; no exact operator check",
     "G05/G06: immunity flag or absence of the fear test; the negative variant "
     "needs the same build without immunity"),
    ("B11.3", "B11-fear", "fear reroll and modifiers",
     lambda e, s, f: e in {
         "mechanic.fear-reroll", "mechanic.craven", "mechanic.opposite-sex-charge-test",
         "mechanic.slaanesh-charge-test",
     },
     PEND_OBS, "E2E fear-reroll scenarios",
     "G05/G06: fear reroll witness"),
    ("B11.4", "B11-fear", "conditional Fear immunity (identity or charge condition)",
     lambda e, s, f: e in {
         "mechanic.accustomed-to-fear", "mechanic.fear-immunity-undead-chargers",
     },
     PEND_OBS, "E2E accustomed-to-fear and undead-charger scenarios",
     "G05/G06: identity/charge condition and fear-test absence; positive control "
     "with another enemy"),
    ("B11.7", "B11-fear", "conditional frenzy (Devoted, Great Thirster)",
     lambda e, s, f: e in {
         "mechanic.devoted-to-the-vampire", "mechanic.great-thirster",
     },
     PEND_OBS, "E2E devoted-to-the-vampire and great-thirster scenarios",
     "G02/G06: frenzy flag per row; loss on knocked down, stunned or out"),
    # -- B12 stupidity -------------------------------------------------------
    ("B12.1", "B12-stupidity", "stupidity test",
     lambda e, s, f: e == "mechanic.stupidity",
     PEND_OBS, "E2E stupidity scenarios",
     "G05: execute stupidity; G06: publish `stupidity-failed`"),
    ("B12.2", "B12-stupidity", "stupidity immunity and cold blood",
     lambda e, s, f: e in {
         "mechanic.psychology-immunity", "mechanic.cold-blooded-psychology",
     },
     PEND_OBS, "E2E immunity scenarios",
     "G05/G06: immunity flag; negative variant without immunity"),
    ("B12.3", "B12-stupidity", "other stupidity-stage rules",
     lambda e, s, f: True,
     PEND_OBS, "E2E/semantic situations by effect",
     "G05/G06: stupidity witness per row"),
    # -- B14 leadership ------------------------------------------------------
    ("B14.1", "B14-leadership", "leader radius (six/twelve inches)",
     lambda e, s, f: e in {
         "mechanic.leader-six", "mechanic.leader-twelve", "mechanic.handler-leadership",
         "mechanic.automatic-leadership", "mechanic.mob-leadership",
         "mechanic.own-leadership", "mechanic.undivided-leader",
         "mechanic.slave-driver", "mechanic.brood-mentality",
         "mechanic.cold-blooded-leadership", "mechanic.devoted",
         "mechanic.relay-orders", "mechanic.songster",
         "condition.poetry-victorious-leader", "condition.command.raise-our-insignia",
         "mechanic.wizened-halfling",
     },
     PEND_OBS, "E2E serpent-priestess--leader::a-supplied-leader-at-six-inches-lends-his-leadership",
     "G05: execute local leadership; G06: publish `leadership-first-failed`; "
     "P01 q10 must declare the nearby ally and the 6-inch distance"),
    ("B14.2", "B14-leadership", "leadership rerolls",
     lambda e, s, f: e in {
         "mechanic.leadership-reroll", "mechanic.first-failed-leadership-reroll",
         "mechanic.mandatory-leadership-reroll", "mechanic.fear-reroll",
     },
     PEND_OBS, "E2E leadership reroll scenarios",
     "G05/G06: reroll witness; not a generic leadership test"),
    ("B14.3", "B14-leadership", "leadership modifiers and penalties",
     lambda e, s, f: e in {
         "mechanic.broken-spirit", "condition.massively-built-leadership-penalty",
         "mechanic.feral-instinct", "mechanic.enchanting-beauty",
         "mechanic.mesmerising-dance", "mechanic.savage-fury",
     },
     PEND_OBS, "E2E leadership modifier scenarios",
     "G05/G06: modifier witness; not inferred from terminal wounds"),
    ("B14.4", "B14-leadership", "other leadership-stage rules",
     lambda e, s, f: True,
     PEND_OBS, "E2E/semantic situations by effect",
     "G05/G06: leadership witness per row"),
    # -- B15 aftermath -------------------------------------------------------
    ("B15.1", "B15-aftermath", "black hunger backlash",
     lambda e, s, f: e == "mechanic.black-hunger",
     CASE, "E2E mechanic.black-hunger::the-backlash-ignores-armour; P01 q11",
     "P01 q11 must give the bearer `skill_ids=(\"mechanic.black-hunger\",)`"),
    ("B15.2", "B15-aftermath", "regeneration and revenant recovery",
     lambda e, s, f: "regeneration" in e or e in {
         "mechanic.curse-of-the-revenant", "mechanic.great-thirster",
         "mechanic.spines", "trait.spines", "trait.acid-blood", "acid_blood",
         "mechanic.torturer", "trait.contagious", "skill.monstrous",
     },
     CASE, "E2E curse-of-the-revenant::a-five-restores-one-lost-wound-at-the-own-turn-start",
     "wounds at the turn boundary are observable; `frenzy`/`acid-blood` flags need G02/G06"),
    ("B15.3", "B15-aftermath", "other aftermath rules",
     lambda e, s, f: True,
     PEND_RULE, "E2E/semantic situations by effect",
     "G02/G06: effect-specific witness"),
    # -- ambiguous -----------------------------------------------------------
    ("B99.1", "B99-unmapped", "consumer does not name a decisive operator",
     lambda e, s, f: True,
     AMBIG, "registry consumer string; unlocated-localization.csv",
     "owner of the annex must localize the consumer; never treat as structural"),
)


#: Effect-level overrides.  The consumer pipeline frequently ends in a shared
#: test resolver (``resolve_local_leadership``, ``resolve_round``), which would
#: hide the rule's own operator.  The effect id names the rule; these ordered
#: keyword rules give it the decisive behaviour.  Anything not matched keeps
#: the consumer-stage fallback.
_EFFECT_RULES = (
    (("proposed.core.combat-critical-hits",), "B07-injury"),
    (("causes-fear", "fear-immunity", "fear-of-", "fear-human", "fear-reroll",
      "fear-hit", "psychology-immunity", "accustomed-to-fear",
      "cold-blooded-psychology", "undead-foes-no-fear", "haunted-mien",
      "lunatics", "beauty-of-the-sea", "enchanting-beauty", "hypnotic-musk",
      "scryer", "morrs-servant", "ashamed-and-afraid", "craven",
      "opposite-sex-charge-test", "slaanesh-charge-test", "undead"), "B11-fear"),
    (("stupidity",), "B12-stupidity"),
    (("leader-", "leadership", "handler-leadership", "automatic-leadership",
      "mob-leadership", "own-leadership", "undivided-leader", "slave-driver",
      "brood-mentality", "devoted", "songster", "relay-orders",
      "wizened-halfling", "poetry-victorious-leader", "command."),
     "B14-leadership"),
    (("natural-armour",), "B04-armour"),
    (("ignore-pain", "hard-to-kill", "thick-skull", "concussion", "injury-profile",
      "fragile", "survivor", "head-crusher", "tough-as-steel", "bat-injury-chart",
      "squishy", "poisonous-injury", "injury-reroll", "jump-up"), "B07-injury"),
    (("regeneration",), "B05-special-save"),
    (("ward-save", "step-aside", "ethereal", "elven-agility", "vampire-reflexes",
      "enchanted-skins", "gypsy-ward", "magical-void", "warpaint",
      "dodge-sidestepper"), "B05-special-save"),
    (("frenzy", "extra-attack", "red-fury", "charge-attack", "sabretusk",
      "bull-charge", "maddened-with-pain", "art-of-silent-death",
      "inspiring-sermon", "web-of-steel", "ravening-onslaught", "anvil-head",
      "spawn-special", "sweep", "crude-belch", "whip-master", "vomit-attack",
      "gaoler-grapple", "honorable", "savage-fury", "frantic",
      "ethereal-hit-save"), "B08-attack-pool"),
    (("black-hunger",), "B15-aftermath"),
    (("death-blow",), "B10-round-order"),
    (("poison",), "B03-wound"),
    (("mighty-biceps", "iron-sinews", "strongman", "titanic-strength",
      "double-handed-weapon", "strength-of-steel", "monster-slayer",
      "retain-flail"), "B03-wound"),
    (("armour", "shield", "buckler"), "B04-armour"),
    (("parry", "sword-master", "swordmaster", "shield-mastery",
      "defensive-stance", "unbeatable-warrior", "miniath", "axe-master",
      "crushing-blow", "beastlash", "spiked-gauntlet", "trident",
      "sword-breaker", "steel-whip", "iron-fan", "main-gauche"), "B06-parry"),
    (("hatred", "berserker", "ferocious-charge", "expert-swordsman", "duellist",
      "cloud-of-flies", "hellblade", "bellowing", "burn-the-witch",
      "noble-disdain", "sea-troll", "infallible", "righteous-fury",
      "weapons-of-the-north", "ulric", "foul-odour", "frustratingly-tiny",
      "pikewall", "seaguard", "dueling-pride", "axe-expert", "blessed-sight",
      "crack-shot", "unstoppable-charge", "unholy-stink", "knife-fighting"),
     "B02-hit"),
    (("flammable", "brazier", "caught-fire", "strike-to-injure", "wolf-rat",
      "wraith-touch"), "B03-wound"),
    (("condition.netted", "netter", "bitten-transform", "equipment"), "B09-equipment"),
    (("luck", "force-of-will", "mark-of-the-old-ones", "ranalds-luck",
      "snorri-lucky", "augur-one-roll"), "B01-initial-state"),
    (("condition.", "preparation.", "profile."), "B01-initial-state"),
    (("initiative", "priority", "lightning-reflexes", "strike-first", "pike",
      "spear", "quarter-staff", "ithilmar"), "B10-round-order"),
    (("revenant", "spines", "acid-blood", "torturer", "contagious", "monstrous"),
     "B15-aftermath"),
)


def behaviour_for(effect: str, fallback: str) -> str:
    if fallback in {"B00-routing", "B99-unmapped"}:
        return fallback
    if not effect:
        return fallback
    for needles, behaviour in _EFFECT_RULES:
        if any(needle in effect for needle in needles):
            return behaviour
    return fallback


def _meta(variant_id: str, fallback: tuple | None = None) -> tuple:
    """Return ``(id, name, status, reference, dependency)`` for a variant."""
    if variant_id in VARIANT_META:
        behaviour, name, status, reference, dependency = VARIANT_META[variant_id]
        return variant_id, name, status, reference, dependency
    for candidate in VARIANTS:
        if candidate[0] == variant_id:
            return candidate[0], candidate[2], candidate[4], candidate[5], candidate[6]
    if fallback is not None and fallback[0] == variant_id:
        return fallback
    raise KeyError(variant_id)


def variant_for(row, behaviour: str, syms: set[str]):
    effect = row["effect_id"] or ""
    key = f"{row['id']}::{row['clause_id']}"
    family = ""
    special = {
        ("core/combat-injury-states", "highest-result"): (
            "B07.2", "highest injury result and multiple wounds", CASE,
            "E2E core/combat-injury-states::highest-injury-result-applies",
            "P01 must repair the identity; G06: per-wound condition sequence",
        ),
        ("core/combat-injury-states", "chart"): (
            "B07.1", "injury table and immunities", DEFECT,
            "exact check injury compares phases.injury_condition to itself",
            "P03: assert vectorized.injury_conditions against phases.injury_condition",
        ),
        ("core/combat-injury-states", "stand-up-strikes-last"): (
            "B10.2", "stand-up and recovery order", CASE,
            "E2E core/combat-injury-states::recovery-belongs-to-the-fighters-own-turn",
            "P01 must declare the knocked-down initial condition",
        ),
    }.get((row["id"], row["clause_id"]))
    if special is not None:
        return special
    fallback = None
    for candidate in VARIANTS:
        variant_id, owner, name, predicate, status, reference, dependency = candidate
        if owner != behaviour:
            continue
        fallback = (variant_id, name, status, reference, dependency)
        if predicate(effect, syms, family):
            break
    if fallback is None:
        raise ValueError(f"no concrete variant for {key} ({effect!r}, {behaviour})")

    variant_id = fallback[0]
    if key in FORCED_KEYS:
        return _meta(FORCED_KEYS[key], fallback)
    if variant_id in MOVED_SOURCES:
        variant_id = MOVED_SOURCES[variant_id]
    elif variant_id in SPLIT_SOURCES:
        variant_id = SPLIT_EFFECT.get(effect, variant_id)
    elif variant_id in GENERIC_IDS:
        variant_id = KEY_OVERRIDE.get(key) or OTHER_EFFECT.get(effect)
        if variant_id is None and "trait-fact" in key:
            variant_id = "B11.1"
        if variant_id is None:
            raise ValueError(f"generic key has no explicit decision: {key} ({effect!r})")

    return _meta(variant_id, fallback)


def behaviour_for_key(row, fallback: str) -> str:
    if row["id"] == "core/combat-injury-states":
        if row["clause_id"] == "stand-up-strikes-last":
            return "B10-round-order"
        return "B07-injury"
    return behaviour_for(row["effect_id"], fallback)


def main() -> None:
    rows = list(csv.DictReader(REGISTRY.open(encoding="utf-8")))
    rec = {
        (r["id"], r["clause_id"]): r
        for r in csv.DictReader(RECON.open(encoding="utf-8"))
    }
    runtime = [
        r for r in rows
        if rec.get((r["id"], r["clause_id"]), {}).get("consumer_class") in {"runtime", "mixed"}
    ]
    output = []
    counts = collections.Counter()
    owners = {candidate[0]: candidate[1] for candidate in VARIANTS}
    owners.update({variant_id: meta[0] for variant_id, meta in VARIANT_META.items()})
    for row in runtime:
        recon = rec[(row["id"], row["clause_id"])]
        behaviour = behaviour_for_key(row, stage(row["consumer"]))
        syms = symbols(row["consumer"])
        variant_id, name, status, reference, dependency = variant_for(row, behaviour, syms)
        behaviour = owners.get(variant_id, behaviour)
        counts[(behaviour, variant_id, name, status)] += 1
        output.append({
            "key": f"{row['id']}::{row['clause_id']}",
            "id": row["id"],
            "clause_id": row["clause_id"],
            "owner": recon["owner"],
            "family": recon["behaviour_family"],
            "consumer_class": recon["consumer_class"],
            "effect_id": row["effect_id"],
            "behaviour_id": behaviour,
            "variant_id": variant_id,
            "variant": name,
            "status": status,
            "reference": reference,
            "dependency": dependency,
        })
    output.sort(key=lambda item: (item["behaviour_id"], item["variant_id"], item["key"]))
    OUT.write_text("", encoding="utf-8")
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)

    lines = [f"rows={len(output)}"]
    for (behaviour, variant, name, status), count in sorted(counts.items()):
        lines.append(f"{behaviour}\t{variant}\t{count}\t{status}\t{name}")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
