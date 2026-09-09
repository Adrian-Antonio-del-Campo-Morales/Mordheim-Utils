"""application.hire_eligibility: roster-dependent hiring eligibility.

The campaign catalogue declares *static* eligibility per hiring entry
(band/group allow+forbid lists or a boolean ``expression``) and leaves the
roster-dependent part to the application. That part is published as prose on
each hireling profile's ``*.rule.campaign-eligibility`` rule (18 rules in
``catalog/hirelings/**``) — the KB text stays the single source for humans,
and this module is the application's reviewed interpretation of it, keyed by
the canonical rule id so a reader can cross-check every predicate against the
declared ``effect``.

The race/alignment/nature facts the rules reason about are *declared* on the
hireling profiles themselves (``catalog/hirelings/traits.yaml``: elf, dwarf,
human, undead, ogre, evil, spellcaster, priest, fear-causing) and loaded
through ``KnowledgePort.hireling_traits()``; this module no longer keeps
curated trait sets. The only remaining application-side facts are the
warband-side heuristics (band groups from ``registry/warband-groups.yaml``
and profile keywords for band members), which the KB does not declare.

Decisions depend on facts the prototype campaign may not track yet (the
Mercenary variant, currently-employed Hired Swords). The module never
silently guesses: when a rule needs a fact the context does not provide it
returns an explicit ``needs_variant``/``unknown`` decision with the reason,
and callers decide how to present it.

The roster context is intentionally small: the warband identity (whose
race/alignment groups come from ``registry/warband-groups.yaml``), the band
member profile ids, the currently employed Hired Sword profile ids, the
optional Mercenary variant (reikland/middenheim/marienburg/ostermark) and
the canonical trait table the context derives facts from.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from mordheim_campaign.application.knowledge_port import KnowledgePort

# --------------------------------------------------------------------------- #
# Context
# --------------------------------------------------------------------------- #


class DecisionKind(str, Enum):
    """Outcome of evaluating one dynamic eligibility rule."""

    ALLOWED = "allowed"        # the hire is permitted by this rule
    REJECTED = "rejected"      # the hire is forbidden by this rule
    CONDITIONAL = "conditional"  # permitted only on a dice result (acceptance roll)
    NEEDS_VARIANT = "needs_variant"  # requires the Mercenary variant of the context
    UNKNOWN = "unknown"        # the rule needs a fact the context does not carry


@dataclass(frozen=True, slots=True)
class Decision:
    kind: DecisionKind
    rule_id: str
    note: str
    #: Acceptance roll for ``CONDITIONAL``: succeed when the D6 equals or
    #: beats ``roll_ge`` (e.g. ``4+``).
    roll_ge: int | None = None

    @classmethod
    def allowed(cls, rule_id: str, note: str) -> "Decision":
        return cls(DecisionKind.ALLOWED, rule_id, note)

    @classmethod
    def rejected(cls, rule_id: str, note: str) -> "Decision":
        return cls(DecisionKind.REJECTED, rule_id, note)


@dataclass(frozen=True, slots=True)
class WarbandHireContext:
    """Everything a dynamic eligibility rule may read about the employer."""

    collection: str
    band_id: str
    band_groups: frozenset[str]
    member_profile_ids: frozenset[str] = frozenset()
    #: Hired Sword profile ids currently employed by the warband.
    hired_sword_profile_ids: frozenset[str] = frozenset()
    #: Mercenary employer variant: "reikland" | "middenheim" | "marienburg" |
    #: "ostermark". ``None`` means the warband did not choose one (or is not a
    #: Mercenary warband).
    variant: str | None = None
    #: Canonical intrinsic traits of hireling profiles, keyed by profile id
    #: (``catalog/hirelings/traits.yaml`` via ``KnowledgePort.hireling_traits``).
    hireling_traits: Mapping[str, frozenset[str]] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Roster facts (interpretation support)
# --------------------------------------------------------------------------- #
#
# Hireling race/alignment/nature facts come from ``catalog/hirelings/traits.yaml``
# (the canonical, validated declaration; see ``KnowledgePort.hireling_traits``).
# The facts below that are *not* hireling traits stay application-side because
# the KB deliberately does not declare them: warband-group membership is the
# canonical band-side race/alignment signal (``registry/warband-groups.yaml``)
# and profile-keyword heuristics cover the band members of the canonical
# warbands (e.g. the wizard profiles the Witch Hunter rule counts).


#: Warband heroes the witch-hunter rule treats as spellcasters (wizard
#: profiles of the canonical bands, by profile-id keyword).
SPELLCASTER_PROFILE_KEYWORDS = (
    "magister", "matriarch", "priestess", "shaman", "warlock", "necromancer",
    "vampire", "sorcerer", "wizard", "lich",
)

#: Profile keywords that mark fear-causing members for the Ninja Gnoblar rule.
FEAR_PROFILE_KEYWORDS = (
    "possessed", "vampire", "zombie", "ghoul", "beastman", "gor", "ogre",
    "troll", "mutant", "daemon", "plague-bearer", "nurgling", "kroxigor",
    "snotling", "squig", "spawn",
)

#: Employer warbands the Dwarf/Elf/priest rules name as always allowed.
#: This matches ``registry/warband-groups.yaml`` ``warband-group.human-mercenary``.
MERCENARY_EMPLOYER_BANDS = frozenset({
    "mercenaries", "averlanders", "ostlanders", "tileans", "lustria-tileans",
    "trollheim-mercenaries",
})
WITCH_HUNTER_EMPLOYER_BANDS = frozenset({"witch-hunters", "trollheim-witch-hunters"})

#: Bands that choose a Mercenary variant (Reikland/Middenheim/Marienburg/
#: Ostermark) at creation. Only their variant is meaningful for the variant
#: rules; the other ``human-mercenary`` bands have a fixed provenance.
VARIANT_CAPABLE_BANDS = frozenset({"mercenaries", "trollheim-mercenaries"})

#: Mercenary variants.
MERCENARY_VARIANTS = frozenset({"reikland", "middenheim", "marienburg", "ostermark"})

#: Warband groups that imply the employer's roster contains fear-causing
#: creatures regardless of individual profiles.
FEAR_BAND_GROUPS = frozenset({
    "warband-group.undead", "warband-group.beastmen", "warband-group.ogre",
    "warband-group.orc", "warband-group.skaven", "warband-group.chaotic",
})

#: Warband groups whose members the spellcaster/witch-hunter rule counts.
SPELLCASTER_BAND_GROUPS = frozenset({"warband-group.undead", "warband-group.chaotic"})


def _traits_of(profile_ids: frozenset[str], traits: Mapping[str, frozenset[str]]) -> frozenset[str]:
    """Union of the declared traits of the given profile ids."""
    union: set[str] = set()
    for profile_id in profile_ids:
        union |= set(traits.get(profile_id, frozenset()))
    return frozenset(union)


def _has_keyword(profile_ids: frozenset[str], keywords: tuple[str, ...]) -> bool:
    lowered = [pid.casefold() for pid in profile_ids]
    return any(keyword in part for pid in lowered for part in pid.split(".") for keyword in keywords)


# --------------------------------------------------------------------------- #
# Feature resolution
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RosterFacts:
    """Derived facts the rules read; each carries the context it came from."""

    is_mercenary_employer: bool
    is_witch_hunter_employer: bool
    has_elf_member: bool
    has_dwarf_member: bool
    has_human_member: bool
    has_undead_member: bool
    has_fear_causing_member: bool
    has_spellcaster_member: bool
    has_warrior_priest_member: bool
    has_elven_hired_sword: bool
    has_evil_hired_sword: bool
    has_highwayman: bool
    has_roadwarden: bool
    is_middenheim: bool
    variant_capable: bool
    variant_known: bool
    william_auto_employer: bool

    @classmethod
    def build(cls, ctx: WarbandHireContext) -> "RosterFacts":
        member_ids = ctx.member_profile_ids
        hired_ids = ctx.hired_sword_profile_ids
        all_ids = member_ids | hired_ids
        groups = ctx.band_groups
        traits = ctx.hireling_traits
        member_traits = _traits_of(member_ids, traits)
        hired_traits = _traits_of(hired_ids, traits)
        all_traits = member_traits | hired_traits

        # Employer band classification.
        is_mercenary = ctx.band_id in MERCENARY_EMPLOYER_BANDS
        is_witch_hunter = ctx.band_id in WITCH_HUNTER_EMPLOYER_BANDS
        # Races implied by the warband itself (canonical warband-group registry).
        band_elf = bool(groups & {"warband-group.elf", "warband-group.high-elf", "warband-group.dark-elf"})
        band_dwarf = "warband-group.dwarf" in groups
        band_human = "warband-group.human" in groups or "warband-group.human-mercenary" in groups
        band_undead = "warband-group.undead" in groups

        # Mercenary variant facts (Middenheim rules). Only Mercenary warbands
        # choose a variant; the rest of ``human-mercenary`` has fixed origin.
        variant_capable = ctx.band_id in VARIANT_CAPABLE_BANDS
        variant = (ctx.variant or "").strip().casefold()
        variant_known = variant_capable and bool(variant) and variant in MERCENARY_VARIANTS
        is_middenheim = variant == "middenheim"
        # William Schäkestange: automatic employers mirror his static list.
        william_auto = is_mercenary or is_witch_hunter or ctx.band_id == "sisters-of-sigmar"

        spellcaster_members = any(
            _has_keyword({pid}, SPELLCASTER_PROFILE_KEYWORDS) for pid in all_ids
        ) or bool(groups & SPELLCASTER_BAND_GROUPS)
        # Priests never make the roster "spellcaster-tainted" for the Witch Hunter rule.
        priests_only = "priest" in all_traits and not any(
            _has_keyword({pid}, SPELLCASTER_PROFILE_KEYWORDS) for pid in all_ids
        )
        spellcaster_members = spellcaster_members and not priests_only

        return cls(
            is_mercenary_employer=is_mercenary,
            is_witch_hunter_employer=is_witch_hunter,
            has_elf_member=band_elf or "elf" in all_traits,
            has_dwarf_member=band_dwarf or "dwarf" in all_traits,
            has_human_member=band_human or "human" in all_traits,
            has_undead_member=band_undead or "undead" in all_traits,
            has_fear_causing_member=bool(groups & FEAR_BAND_GROUPS)
            or "fear-causing" in hired_traits
            or _has_keyword(all_ids, FEAR_PROFILE_KEYWORDS),
            has_spellcaster_member=spellcaster_members or "spellcaster" in hired_traits,
            has_warrior_priest_member="priest" in all_traits,
            has_elven_hired_sword="elf" in hired_traits,
            has_evil_hired_sword="evil" in hired_traits,
            has_highwayman="hireling.hired-sword.highwayman" in hired_ids,
            has_roadwarden="hireling.hired-sword.roadwarden" in hired_ids,
            is_middenheim=is_middenheim,
            variant_capable=variant_capable,
            variant_known=variant_known,
            william_auto_employer=william_auto,
        )


# --------------------------------------------------------------------------- #
# The 18 dynamic eligibility rules, keyed by canonical rule id
# --------------------------------------------------------------------------- #


def _employer_or_elf(facts: RosterFacts) -> bool:
    return (facts.is_mercenary_employer or facts.is_witch_hunter_employer) or facts.has_elf_member


def evaluate_rule(rule_id: str, ctx: WarbandHireContext) -> Decision:
    """Evaluate one ``*.rule.campaign-eligibility`` rule against a context."""
    facts = RosterFacts.build(ctx)

    # -- Dwarf/Elf employers --------------------------------------------------
    if rule_id == "hireling.hired-sword.dwarf-troll-slayer.rule.campaign-eligibility":
        if _employer_or_elf(facts):
            return Decision.allowed(rule_id, "Mercenaries and Witch Hunters may hire the Dwarf Troll Slayer; a roster that includes Elves may also hire him.")
        return Decision.rejected(rule_id, "Only Mercenaries, Witch Hunters or a roster that includes Elves may hire the Dwarf Troll Slayer.")
    if rule_id == "hireling.hired-sword.dwarf-treasure-hunter.rule.campaign-eligibility":
        if _employer_or_elf(facts):
            return Decision.allowed(rule_id, "Mercenaries and Witch Hunters may hire the Dwarf Treasure Hunter; a roster that includes Elves may also hire him.")
        return Decision.rejected(rule_id, "Only Mercenaries, Witch Hunters or a roster that includes Elves may hire the Dwarf Treasure Hunter.")
    if rule_id == "hireling.hired-sword.runesmith-journeyman.rule.campaign-eligibility":
        if _employer_or_elf(facts):
            return Decision.allowed(rule_id, "Mercenaries and Witch Hunters may hire the Runesmith Journeyman; a roster that includes Elves may also hire him.")
        return Decision.rejected(rule_id, "Only Mercenaries, Witch Hunters or a roster that includes Elves may hire the Runesmith Journeyman.")
    if rule_id == "hireling.hired-sword.elf-ranger.rule.campaign-eligibility":
        allowed = (facts.is_mercenary_employer or facts.is_witch_hunter_employer) or facts.has_dwarf_member
        if allowed:
            return Decision.allowed(rule_id, "Mercenaries and Witch Hunters may hire the Elf Ranger; a roster that includes Dwarfs may also hire him.")
        return Decision.rejected(rule_id, "Only Mercenaries, Witch Hunters or a roster that includes Dwarfs may hire the Elf Ranger.")

    # -- Roster composition ---------------------------------------------------
    if rule_id == "hireling.hired-sword.cathayan-merchant.rule.campaign-eligibility":
        if facts.has_human_member or facts.has_dwarf_member:
            return Decision.allowed(rule_id, "The Cathayan Merchant may be hired when the warband includes Humans or Dwarfs (Battle Monks of Cathay count).")
        return Decision.rejected(rule_id, "The Cathayan Merchant only joins warbands that include Humans or Dwarfs.")
    if rule_id == "hireling.hired-sword.grave-robber.rule.campaign-eligibility":
        if facts.has_undead_member or _has_keyword(ctx.member_profile_ids, ("vampire", "necromancer", "liche")):
            return Decision.allowed(rule_id, "The Grave Robber joins warbands that include a Vampire, Necromancer or Liche.")
        return Decision.rejected(rule_id, "The Grave Robber only joins warbands that include a Vampire, Necromancer or Liche.")
    if rule_id == "hireling.hired-sword.ninja-gnoblar.rule.campaign-eligibility":
        if not facts.has_fear_causing_member:
            return Decision.allowed(rule_id, "The Ninja Gnoblar joins warbands with no fear-causing creatures.")
        return Decision.rejected(rule_id, "The Ninja Gnoblar will not join a warband that contains fear-causing creatures.")
    if rule_id == "hireling.hired-sword.witch-hunter.rule.campaign-eligibility":
        if not facts.has_spellcaster_member:
            return Decision.allowed(rule_id, "The Witch Hunter does not work for warbands with a spellcaster (priests of Sigmar, Ulric, Taal or Morr excepted).")
        return Decision.rejected(rule_id, "The Witch Hunter refuses warbands whose roster contains a spellcaster (except priests of Sigmar, Ulric, Taal or Morr).")

    # -- Hired Sword incompatibilities ---------------------------------------
    if rule_id == "hireling.hired-sword.highwayman.rule.campaign-eligibility":
        if not facts.has_roadwarden:
            return Decision.allowed(rule_id, "The Highwayman may be hired when no Roadwarden serves the warband.")
        return Decision.rejected(rule_id, "The Highwayman cannot be hired by (or remain with) a warband that employs a Roadwarden.")
    if rule_id == "hireling.hired-sword.roadwarden.rule.campaign-eligibility":
        if not facts.has_highwayman:
            return Decision.allowed(rule_id, "The Roadwarden may be hired when no Highwayman serves the warband.")
        return Decision.rejected(rule_id, "The Roadwarden cannot be hired by a warband that employs a Highwayman.")
    if rule_id == "hireling.hired-sword.knight-of-the-white-wolf.rule.campaign-eligibility":
        if not facts.has_warrior_priest_member:
            return Decision.allowed(rule_id, "The Knight of the White Wolf joins warbands without a Warrior Priest.")
        return Decision.rejected(rule_id, "The Knight of the White Wolf will not join (or remain with) a warband that contains a Warrior Priest.")
    if rule_id == "hireling.hired-sword.shadow-warrior.rule.campaign-eligibility":
        if not facts.has_evil_hired_sword:
            return Decision.allowed(rule_id, "The Shadow Warrior joins warbands without evil Hired Swords.")
        return Decision.rejected(rule_id, "The Shadow Warrior cannot be hired by (or remain with) a warband that employs an evil Hired Sword.")
    if rule_id == "hireling.dramatis.dijin-katal-the-renegade-assassin.rule.campaign-eligibility":
        if not facts.has_elven_hired_sword:
            return Decision.allowed(rule_id, "Dijin Katal joins warbands without Elven Hired Swords.")
        return Decision.rejected(rule_id, "Dijin Katal cannot be hired by a warband whose roster contains any type of Elven Hired Sword.")

    # -- Mercenary variant rules ---------------------------------------------
    if rule_id in {
        "hireling.dramatis.maximilian-the-mad.rule.campaign-eligibility",
        "hireling.hired-sword.warrior-priest-of-sigmar.rule.campaign-eligibility",
    }:
        if not facts.variant_capable:
            return Decision.allowed(rule_id, "Not a variant-capable warband; the rule does not apply.")
        if facts.variant_known:
            if facts.is_middenheim:
                return Decision.rejected(rule_id, "Middenheimers may not hire this warrior.")
            return Decision.allowed(rule_id, "The selected Mercenary variant may hire this warrior.")
        return Decision(DecisionKind.NEEDS_VARIANT, rule_id,
                        "Requires the warband's Mercenary variant (Middenheimers are excluded).")
    if rule_id == "hireling.hired-sword.wolf-priest-of-ulric.rule.campaign-eligibility":
        # Static eligibility already restricts this entry to ``human-mercenary``
        # employers; the variant decides whether the hire is Middenheim.
        if facts.variant_capable and facts.variant_known:
            if facts.is_middenheim:
                return Decision.allowed(rule_id, "Middenheim Mercenaries may hire the Wolf Priest of Ulric as a Hero replacement.")
            return Decision.rejected(rule_id, "Only Middenheim Mercenaries may hire the Wolf Priest of Ulric.")
        if facts.variant_capable:
            return Decision(DecisionKind.NEEDS_VARIANT, rule_id,
                            "Only available to Middenheim Mercenaries; select the Mercenary variant to confirm.")
        return Decision.rejected(rule_id, "The Wolf Priest of Ulric is available only to Middenheim Mercenaries.")

    # -- Conditional acceptance ----------------------------------------------
    if rule_id == "hireling.dramatis.william-schakestange-master-bard.rule.campaign-eligibility":
        if facts.william_auto_employer:
            return Decision.allowed(rule_id, "Mercenaries, Sisters of Sigmar and Witch Hunters hire William automatically.")
        if "warband-group.good-aligned" in ctx.band_groups:
            return Decision(DecisionKind.CONDITIONAL, rule_id,
                            "Other good-aligned warbands hire William on a D6 roll of 4+.", roll_ge=4)
        return Decision.rejected(rule_id, "William only joins good-aligned warbands.")

    # -- Composition for Dramatis Personae -----------------------------------
    if rule_id == "hireling.dramatis.grand-master-ippan-shu.rule.campaign-eligibility":
        if facts.has_human_member or facts.has_elf_member:
            return Decision.allowed(rule_id, "Ippan Shu may be hired when the warband includes Humans or Elves.")
        return Decision.rejected(rule_id, "Ippan Shu may only be hired when the warband includes Humans or Elves.")

    raise KeyError(f"no evaluator registered for dynamic rule {rule_id!r}")


# --------------------------------------------------------------------------- #
# Catalogue-facing entry point
# --------------------------------------------------------------------------- #

#: Rule ids the module can evaluate.
KNOWN_RULES = frozenset({
    "hireling.hired-sword.dwarf-troll-slayer.rule.campaign-eligibility",
    "hireling.hired-sword.dwarf-treasure-hunter.rule.campaign-eligibility",
    "hireling.hired-sword.runesmith-journeyman.rule.campaign-eligibility",
    "hireling.hired-sword.elf-ranger.rule.campaign-eligibility",
    "hireling.hired-sword.cathayan-merchant.rule.campaign-eligibility",
    "hireling.hired-sword.grave-robber.rule.campaign-eligibility",
    "hireling.hired-sword.ninja-gnoblar.rule.campaign-eligibility",
    "hireling.hired-sword.witch-hunter.rule.campaign-eligibility",
    "hireling.hired-sword.highwayman.rule.campaign-eligibility",
    "hireling.hired-sword.roadwarden.rule.campaign-eligibility",
    "hireling.hired-sword.knight-of-the-white-wolf.rule.campaign-eligibility",
    "hireling.hired-sword.shadow-warrior.rule.campaign-eligibility",
    "hireling.dramatis.dijin-katal-the-renegade-assassin.rule.campaign-eligibility",
    "hireling.dramatis.maximilian-the-mad.rule.campaign-eligibility",
    "hireling.hired-sword.warrior-priest-of-sigmar.rule.campaign-eligibility",
    "hireling.hired-sword.wolf-priest-of-ulric.rule.campaign-eligibility",
    "hireling.dramatis.william-schakestange-master-bard.rule.campaign-eligibility",
    "hireling.dramatis.grand-master-ippan-shu.rule.campaign-eligibility",
})


def dynamic_rules_for_profile(port: KnowledgePort, profile_id: str) -> tuple[str, ...]:
    """Campaign-eligibility rule ids declared on one hireling profile."""
    catalogue = port.hireling_catalogue()
    rules: list[str] = []
    seen: set[str] = set()
    for row in catalogue.profiles:
        if str(row.get("id") or "") != profile_id:
            continue
        declared = list(row.get("rule_ids") or ())
        for inline in row.get("rules") or ():
            if isinstance(inline, dict) and inline.get("id"):
                declared.append(inline["id"])
        for rule_id in declared:
            rid = str(rule_id)
            if ".campaign-eligibility" in rid and rid in KNOWN_RULES and rid not in seen:
                seen.add(rid)
                rules.append(rid)
        # Top-level declarations in the same file also belong to the profile
        # when referenced by id (e.g. shared hired-swords/rules.yaml entries
        # referenced through rule_ids).
    return tuple(rules)


def context_from_roster(
    port: KnowledgePort,
    *,
    collection: str,
    band_id: str,
    member_profile_ids: frozenset[str] = frozenset(),
    hired_sword_profile_ids: frozenset[str] = frozenset(),
    variant: str | None = None,
) -> WarbandHireContext:
    """Build the hire context from stable ids (port resolves band groups)."""
    groups = frozenset(
        str(group.get("id") or "")
        for group in port.warband_groups()
        if band_id in set(group.get("band_ids") or ())
    )
    return WarbandHireContext(
        collection=collection,
        band_id=band_id,
        band_groups=groups,
        member_profile_ids=frozenset(member_profile_ids),
        hired_sword_profile_ids=frozenset(hired_sword_profile_ids),
        variant=variant,
        hireling_traits=port.hireling_traits(),
    )
