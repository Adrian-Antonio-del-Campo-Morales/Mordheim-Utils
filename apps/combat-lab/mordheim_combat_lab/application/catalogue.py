"""application: Catalogue options read model for the UI."""
from __future__ import annotations

from dataclasses import dataclass
from mordheim_core.models import FighterBuild
from mordheim_construction.eligibility import call, construction_call, configuration_context, desktop_call, package_facts
from mordheim_knowledge.loader import BandPackage
from mordheim_construction.combat_packages import combat_packages
from mordheim_knowledge.loader import load_collections
from mordheim_knowledge.loader import load_conditions
from mordheim_knowledge.loader import load_mechanics
from mordheim_knowledge.loader import load_racial_maximums
from mordheim_knowledge.loader import load_runtime_scope
from mordheim_knowledge.loader import load_shared_rules
from mordheim_knowledge.loader import load_simulation_mappings
from mordheim_knowledge.loader import load_skills
from mordheim_knowledge.campaign import load_warband_groups
from mordheim_knowledge.i18n import display_effect
from mordheim_knowledge.i18n import display_name


@dataclass(frozen=True, slots=True)
class ProfileChoice:
    collection: str
    band_id: str
    profile_id: str
    name: str


@dataclass(frozen=True, slots=True)
class SkillChoice:
    id: str
    name: str
    category: str
    summary: str
    unavailable_reason: str | None = None
    selection_kind: str = "skill"
    rule_id: str | None = None
    runtime_available: bool = True


@dataclass(frozen=True, slots=True)
class ProfileRule:
    id: str
    name: str
    effect: str
    runtime_grant: bool


@dataclass(frozen=True, slots=True)
class ConditionChoice:
    """A canonical condition the caller may supply as a current warrior fact.

    The id is what the construction contract receives; the label is display
    only. The choice list comes from the KB catalogue, so the editor never
    keeps a second interpretation of a condition.
    """
    id: str
    name: str
    summary: str



#: Canonical bindings that lift the two-hand loadout restriction. The rule
#: that carries one is selectable, so the exception is a fact of the current
#: selection; the shared module reports the binding id and this adapter only
#: maps it onto the loadout decision.
HAND_EXCEPTION_BINDINGS = frozenset({
    "compiler.ignore-difficult-to-use-restrictions", "compiler.master-of-arms",
})

#: Race-group suffix → ``profile`` key of ``catalog/rules/racial-maximums.yaml``.
#: Mirrors the campaign engine's band-race heuristics; groups the KB declares
#: without a single racial-maximum table (lizardmen resolve per profile,
#: mixed-race, pygmy) stay unresolved instead of guessing.
_GROUP_RACE = {
    "human": "human", "chaos-human": "human", "human-mercenary": "human",
    "undead": "human", "elf": "elf", "high-elf": "elf", "dark-elf": "elf",
    "dwarf": "dwarf", "chaos-dwarf": "dwarf", "skaven": "skaven",
    "ogre": "ogre", "goblin": "goblin", "orc": "orc",
    "halfling": "halfling", "beastmen": "other_beastmen",
}

#: Racial-maximum characteristic field → the editor's display key.
_MAXIMUM_FIELDS = {
    "WS": "weapon_skill", "S": "strength", "T": "toughness",
    "W": "wounds", "I": "initiative", "A": "attacks",
}


class CombatCatalogue:
    """Small index used by the new UI selectors."""

    def __init__(self, ruleset: str = "mordheim"):
        self.ruleset = ruleset
        self._packages = {
            (package.collection, str(package.band["id"])): package
            for collection in load_collections()
            if ruleset in collection.get("rulesets", ())
            for package in combat_packages(str(collection["id"]))
            if package.ruleset == ruleset
        }
        self._mechanics = {
            str(row["id"]): row
            for family in ("weapons", "defences", "armours", "materials", "preparations", "poisons")
            for row in load_mechanics(ruleset).get(family, ())
        }
        self._skill_mechanics = {str(row["id"]) for row in load_mechanics(ruleset).get("skills", ())}
        exclusions = load_runtime_scope(ruleset).get("mechanic_exclusions") or ()
        self._excluded_mechanics = {str(row["id"]) for row in exclusions}
        self._excluded_mechanic_reasons = {
            str(row["id"]): str(row.get("reason") or "").strip()
            for row in exclusions
        }
        option_to_id = {str(row.get("engine_option")): item_id for item_id, row in self._mechanics.items()}
        self._shared_rules = load_shared_rules(ruleset)
        self._item_mechanics = {
            str(row["item_id"]): option_to_id[str(row["engine_option"])]
            for row in load_simulation_mappings(ruleset).get("item_mappings", ())
            if row.get("status") == "implemented" and str(row.get("engine_option")) in option_to_id
        }
        self._global_costs = self._costs_for_packages(tuple(self._packages.values()))

    def collections(self) -> tuple[tuple[str, str], ...]:
        return tuple((str(row["id"]), str(row.get("name") or row["id"])) for row in load_collections() if self.ruleset in row.get("rulesets", ()))

    def bands(self, collection: str, categories: set[str] | None = None) -> tuple[BandPackage, ...]:
        """Return bands in a collection, optionally filtered by source grade.

        Categories are KB metadata (``core``, ``1a``, ``1b``, ``1c`` and
        ``trollheim``), rather than a second catalogue.  This lets the legacy
        collections picker filter the same stable profile IDs used by runtime.
        """
        selected = {value.casefold() for value in categories or ()}
        return tuple(
            package for (package_collection, _), package in self._packages.items()
            if package_collection == collection
            and (not selected or selected.intersection({str(value).casefold() for value in package.band.get("categories") or ()}))
        )

    def bands_for_categories(self, categories: set[str] | None = None) -> tuple[BandPackage, ...]:
        """Return executable bands from every enabled legacy collection grade."""
        return tuple(package for collection, _name in self.collections() for package in self.bands(collection, categories))

    def profiles(self, collection: str, band_id: str) -> tuple[ProfileChoice, ...]:
        package = self._packages[(collection, band_id)]
        return tuple(ProfileChoice(collection, band_id, str(row["id"]), str(row["name"])) for row in package.profiles if row.get("characteristics"))

    def profile(self, choice: ProfileChoice) -> dict:
        """Return profile data for display, not editable UI state."""
        package = self._packages[(choice.collection, choice.band_id)]
        return next(row for row in package.profiles if row["id"] == choice.profile_id)

    def mechanic(self, mechanic_id: str) -> dict:
        """Return the normalized mechanic metadata used for UI constraints."""
        return self._mechanics[mechanic_id]

    def localized_name(self, item_id: str | None, fallback: str | None = None) -> str:
        """Display name of one mechanics record in the active KB locale.

        Sentinel values (``None`` for "no selection") fall back to the provided
        English literal, which the caller translates through the UI catalogue;
        known ids resolve through ``name_i18n`` so the reviewed Spanish name
        wins when it exists.
        """
        if item_id is None:
            return str(fallback or "")
        record = self._mechanics.get(item_id)
        if record is None:
            return str(fallback or item_id)
        return display_name(record, fallback or item_id)

    def skills(self, choice: ProfileChoice | None, *, variant_ids: tuple[str, ...] = ()) -> tuple[SkillChoice, ...]:
        """Return every general category plus the selected band's special skills."""
        profile = self.profile(choice) if choice else None
        legal = None
        named = set()
        if choice is not None:
            package = self._packages[(choice.collection, choice.band_id)]
            build = FighterBuild(self.ruleset, collection=choice.collection,
                                 band_id=choice.band_id, profile_id=choice.profile_id, variant_ids=variant_ids)
            legal = desktop_call("skillChoices", build, package=package, profile=profile)
            named = {skill_id for table in desktop_call("profileSkillLists", build, package=package, profile=profile)
                     for skill_id in table["skills"]}
        banned = self._banned_skill_categories(choice)
        general = tuple(
            SkillChoice(
                str(skill["id"]),
                str(skill["name"]),
                str(skill["category"]),
                str(skill.get("effect") or ""),
                banned.get(str(skill.get("category") or "")) or self._skill_unavailable_reason(skill),
                runtime_available=(
                    (legal is None or legal.get(str(skill["id"]), False))
                    and self._catalogue_skill_is_available(skill)
                ),
            )
            for skill in load_skills(self.ruleset)
            if str(skill.get("category") or "") != "special" or str(skill["id"]) in named
        )
        return (*general, *self._warband_skills(choice, variant_ids=variant_ids))

    def _banned_skill_categories(self, choice: ProfileChoice | None) -> dict[str, str]:
        """Skill categories a profile may never acquire, with the KB reason.

        Profile rules with an implemented ``compiler.forbid-skill-categories``
        binding forbid whole categories independently of ``skill_access``, so
        the editor disables them even if a campaign advance would later grant
        the list."""
        if choice is None:
            return {}
        package = self._packages[(choice.collection, choice.band_id)]
        profile = self.profile(choice)
        banned = call("bannedSkillCategories", package_facts(package), profile)
        rules = {str(rule["id"]): rule for rule in package.special_rules}
        return {category: self._rule_text(rules[rule_id]) for category, rule_id in banned.items()}

    def in_scope_skill_ids(self, skills) -> set[str]:
        """Return skill IDs executable by the current one-against-one runtime."""
        return {
            skill.id for skill in skills
            if skill.runtime_available and skill.id not in self._excluded_mechanics
        }

    def skill_rule_ids(self, selected_ids) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Split UI selections into ordinary skill IDs and band-rule IDs."""
        choices = {skill.id: skill for skill in self.skills(None)}
        named_ids = {str(skill["id"]) for skill in load_skills(self.ruleset)}
        ordinary, special = [], []
        for selected_id in selected_ids:
            skill = choices.get(selected_id)
            if skill is None:
                if selected_id in named_ids:
                    ordinary.append(selected_id)
                continue
            if skill.selection_kind == "warband_skill" and skill.rule_id:
                special.append(skill.rule_id)
            else:
                ordinary.append(skill.id)
        return tuple(ordinary), tuple(special)

    def skill_ui_ids(self, choice: ProfileChoice | None, skill_ids, special_rule_ids) -> tuple[str, ...]:
        """Map persisted build IDs back to the unique IDs used by the Canvas."""
        result = list(skill_ids)
        wanted = set(special_rule_ids)
        result.extend(skill.id for skill in self._warband_skills(choice) if skill.rule_id in wanted)
        return tuple(result)

    def _skill_unavailable_reason(self, skill: dict) -> str | None:
        """Expose the KB explanation for a disabled, out-of-scope skill."""
        runtime = skill.get("runtime") or {}
        if runtime.get("scope") == "YES" and runtime.get("implemented") == "YES":
            return None
        for effect in runtime.get("effects") or ():
            reason = str(effect.get("reason") or "").strip()
            if reason:
                return reason
        return self._excluded_mechanic_reasons.get(str(skill["id"])) or (
            "No executable duel mechanic." if str(skill["id"]) not in self._skill_mechanics else None)

    def _catalogue_skill_is_available(self, skill: dict) -> bool:
        runtime = skill.get("runtime")
        if runtime:
            return runtime.get("scope") == "YES" and runtime.get("implemented") == "YES"
        return str(skill["id"]) in self._skill_mechanics and str(skill["id"]) not in self._excluded_mechanics

    def _rule_text(self, rule: dict) -> str:
        """Resolve a band rule's display prose, following ``rule_ref``.

        ``rule_ref`` rules render the shared catalogue record (its ``effect``
        is the single source of prose); every record goes through
        :func:`mordheim_knowledge.i18n.display_effect` so the active locale
        wins when a translation exists.
        """
        ref = str(rule.get("rule_ref") or "")
        record = self._shared_rules.get(ref) if ref else rule
        if not isinstance(record, dict):
            return ""
        return display_effect(record)

    def conditions(self) -> tuple[ConditionChoice, ...]:
        """Canonical conditions the duel runtime can carry as supplied facts."""
        return tuple(
            ConditionChoice(str(row["id"]), display_name(row, str(row["id"])), display_effect(row))
            for row in load_conditions(self.ruleset)
            if (row.get("runtime") or {}).get("implemented") == "YES"
        )

    @staticmethod
    def _rule_unavailable_reason(rule: dict) -> str | None:
        runtime = rule.get("runtime") or {}
        if runtime.get("scope") == "YES" and runtime.get("implemented") == "YES":
            return None
        for effect in runtime.get("effects") or ():
            reason = str(effect.get("reason") or "").strip()
            if reason:
                return reason
        if runtime.get("implemented") != "YES":
            return "Not implemented for duel simulations."
        return "Outside the current duel simulation scope."

    @staticmethod
    def _warband_skill_id(package: BandPackage, rule: dict) -> str:
        return f"warband-skill:{package.collection}:{package.band['id']}:{rule['id']}"

    def _warband_skills(self, choice: ProfileChoice | None, *, variant_ids: tuple[str, ...] = ()) -> tuple[SkillChoice, ...]:
        packages = (
            (self._packages[(choice.collection, choice.band_id)],)
            if choice is not None else tuple(self._packages.values())
        )
        profile = self.profile(choice) if choice is not None else None
        eligible_ids = None
        if choice is not None:
            build = FighterBuild(self.ruleset, collection=choice.collection,
                                 band_id=choice.band_id, profile_id=choice.profile_id, variant_ids=variant_ids)
            eligible_ids = set(desktop_call("specialRules", build,
                              package=packages[0], profile=profile))
        result = []
        for package in packages:
            band_name = str(package.band.get("name") or package.band["id"])
            for rule in package.special_rules:
                if rule.get("kind") != "warband_skill":
                    continue
                runtime = rule.get("runtime") or {}
                eligible = eligible_ids is None or str(rule["id"]) in eligible_ids
                result.append(SkillChoice(
                    self._warband_skill_id(package, rule),
                    (
                        f"{rule.get('name') or rule['id']} · {band_name}"
                        if choice is None
                        else str(rule.get("name") or rule["id"])
                    ),
                    "special",
                    self._rule_text(rule),
                    self._rule_unavailable_reason(rule),
                    "warband_skill",
                    str(rule["id"]),
                    eligible
                    and runtime.get("scope") == "YES"
                    and runtime.get("implemented") == "YES",
                ))
        return tuple(result)

    def characteristic_maximums(self, choice: ProfileChoice | None) -> dict[str, int]:
        """Racial maximum characteristics for one profile, in editor keys.

        Resolves the race from ``registry/warband-groups.yaml`` (the same
        warband-side heuristic the campaign engine applies) and the maximums
        from ``catalog/rules/racial-maximums.yaml``. Groups without a single
        racial-maximum table return no maximum so the UI never invents one.
        """
        if choice is None:
            return {}
        group_id = next(
            (str(group["id"]) for group in load_warband_groups(self.ruleset)
             if choice.band_id in set(group.get("band_ids") or ())
             and str(group["id"]).removeprefix("warband-group.") in _GROUP_RACE),
            None,
        )
        if group_id is None:
            return {}
        race = _GROUP_RACE[str(group_id).removeprefix("warband-group.")]
        table = next(
            (row for row in load_racial_maximums(self.ruleset) if str(row.get("profile")) == race),
            None,
        )
        if table is None:
            return {}
        declared = table.get("characteristics") or {}
        return {
            key: int(declared[field]) for key, field in _MAXIMUM_FIELDS.items()
            if field in declared
        }

    def profile_rules(self, choice: ProfileChoice | None) -> tuple[ProfileRule, ...]:
        """Return editorial profile rules together with their runtime status."""
        if choice is None:
            return ()
        package = self._packages[(choice.collection, choice.band_id)]
        profile = self.profile(choice)
        rule_ids = set(profile.get("rule_ids") or ())
        return tuple(
            ProfileRule(
                str(rule["id"]),
                str(rule["name"]),
                self._rule_text(rule),
                bool(
                    (rule.get("runtime") or {}).get("implemented") == "YES"
                    and (rule.get("runtime") or {}).get("grant") in {"profile", "band"}
                ),
            )
            for rule in package.special_rules
            if rule.get("id") in rule_ids
        )

    def selectable_rules(self, choice: ProfileChoice | None) -> tuple[SkillChoice, ...]:
        """Return legal non-skill options, including unavailable ones for display."""
        if choice is None:
            return ()
        package = self._packages[(choice.collection, choice.band_id)]
        build = FighterBuild(self.ruleset, collection=choice.collection, band_id=choice.band_id, profile_id=choice.profile_id)
        eligible = set(desktop_call("configuredRules", build, package=package, profile=self.profile(choice)))
        return tuple(
            SkillChoice(
                str(rule["id"]),
                str(rule["name"]),
                str(rule.get("kind") or "selectable rule").replace("_", " ").title(),
                self._rule_text(rule),
                self._rule_unavailable_reason(rule),
                str(rule.get("kind") or "selectable_rule"),
                str(rule["id"]),
                (rule.get("runtime") or {}).get("scope") == "YES"
                and (rule.get("runtime") or {}).get("implemented") == "YES",
            )
            for rule in package.special_rules
            if rule.get("kind") != "warband_skill"
            and (rule.get("runtime") or {}).get("grant") == "selectable"
            and str(rule["id"]) in eligible
        )

    def weapons(self, choice: ProfileChoice | None) -> tuple[tuple[str, str], ...]:
        return self._equipment(choice, "weapons", lambda row: row.get("main_hand"))

    def off_hand_options(self, choice: ProfileChoice | None) -> tuple[tuple[str | None, str], ...]:
        options = self._equipment(
            choice,
            ("weapons", "defences"),
            lambda row: row.get("off_hand") or row.get("id") in {"defence.shield", "defence.buckler", "defence.kite-shield"},
        )
        return ((None, "Free hand"), *options)

    def armours(self, choice: ProfileChoice | None) -> tuple[tuple[str, str], ...]:
        return (("armour.no-armour", "No armour"), *self._equipment(choice, "armours", lambda _row: True))

    def helmets(self, choice: ProfileChoice | None) -> tuple[tuple[str | None, str], ...]:
        options = self._equipment(
            choice,
            "defences",
            lambda row: row.get("id") in {"defence.helmet", "defence.cooking-pot-helmet"},
        )
        return ((None, "No helmet"), *options)

    def materials(self, choice: ProfileChoice | None) -> tuple[tuple[str, str], ...]:
        return (("material.normal", "Normal"), *self._equipment(choice, "materials", lambda _row: True))

    def preparations(self, choice: ProfileChoice | None) -> tuple[tuple[str | None, str], ...]:
        return ((None, "No preparation"), *self._equipment(choice, "preparations", lambda _row: True))

    def poisons(self, choice: ProfileChoice | None) -> tuple[tuple[str | None, str], ...]:
        return ((None, "No poison"), *self._equipment(choice, "poisons", lambda _row: True))

    def cost(self, mechanic_id: str | None, choice: ProfileChoice | None) -> float | None:
        """Lowest legal acquisition cost for one executable mechanic."""
        if mechanic_id is None or mechanic_id in {"armour.no-armour", "material.normal"}:
            return 0.0
        if choice is None:
            return self._global_costs.get(mechanic_id)
        package = self._packages[(choice.collection, choice.band_id)]
        profile = self.profile(choice)
        allowed_lists = set(profile.get("equipment_lists") or ())
        costs = self._costs_for_packages((package,), allowed_lists)
        return costs.get(mechanic_id, self._global_costs.get(mechanic_id))

    def _costs_for_packages(self, packages: tuple[BandPackage, ...], allowed_lists: set[str] | None = None) -> dict[str, float]:
        costs: dict[str, float] = {}
        for package in packages:
            for equipment_list in package.equipment_lists:
                if allowed_lists is not None and str(equipment_list.get("id")) not in allowed_lists:
                    continue
                for item in equipment_list.get("items") or ():
                    mechanic_id = self._item_mechanics.get(str(item.get("item_id")))
                    cost = item.get("cost")
                    if mechanic_id is None or not isinstance(cost, (int, float)):
                        continue
                    costs[mechanic_id] = min(costs.get(mechanic_id, float(cost)), float(cost))
        return costs

    def _equipment(self, choice, families, allowed) -> tuple[tuple[str, str], ...]:
        return self._profile_equipment(choice, families, allowed) if choice else self._runtime_equipment(families, allowed)

    def _selection_context(self, choice: ProfileChoice, *, variant_ids: tuple[str, ...] = ()):
        """Project the editor's current selections as shared-module facts.

        The adapter supplies facts; the shared module interprets their rule
        meaning. Item ownership and the active duel loadout stay distinct:
        only the loadout slots are projected here.
        """
        package = self._packages[(choice.collection, choice.band_id)]
        profile = next(row for row in package.profiles if row["id"] == choice.profile_id)
        build = FighterBuild(self.ruleset, collection=choice.collection,
                             band_id=choice.band_id, profile_id=choice.profile_id, variant_ids=variant_ids)
        return package, profile, build

    def validate_configuration(self, choice: ProfileChoice, *, possession: tuple[str, ...],
                               slots: dict, variant_ids: tuple[str, ...] = ()) -> tuple[dict, ...]:
        """Validate a supplied complete kit and its distinct active loadout.

        Item ids may include legal equipment without a duel mechanic. This
        validates construction, not shooting or campaign purchases.
        """
        package, profile, build = self._selection_context(choice, variant_ids=variant_ids)
        facts = configuration_context(build, package, profile, possession=possession, slots=slots)
        return tuple(construction_call("validateConstruction", build, facts))

    def equipment_decisions(self, choice: ProfileChoice, item_ids, *, slot: str = "main",
                            main_weapon_id: str | None = None,
                            off_hand_id: str | None = None,
                            main_poison_id: str | None = None,
                            off_poison_id: str | None = None,
                            skills: tuple[str, ...] = (),
                            exception_rule_ids: tuple[str, ...] = (),
                            variant_ids: tuple[str, ...] = ()) -> dict[str, str | None]:
        """Shared decision per candidate item, in one transport call.

        Returns the blocking reason per item id (``None`` when the choice is
        permitted), so the editor can show incompatible options disabled with
        their motive instead of filtering them out or deciding locally. The
        installed catalogue supplies the canonical item facts of every
        candidate, so a large comparison still submits a single batch.
        """
        package, profile, build = self._selection_context(choice, variant_ids=variant_ids)
        selections = [{"id": str(item_id), "kind": "equipment", "slot": slot}
                      for item_id in item_ids]
        selections.extend(entry for entry in (
            self._hand_fact(main_weapon_id), self._hand_fact(off_hand_id)) if entry)
        facts = self._declared_facts(
            package, profile, build, selections,
            main_weapon_id=main_weapon_id, off_hand_id=off_hand_id,
            main_poison_id=main_poison_id, off_poison_id=off_poison_id,
            skills=skills, exception_rule_ids=exception_rule_ids)
        proposals = [{"kind": "add", "id": str(item_id), "slot": slot} for item_id in item_ids]
        decisions = construction_call("selectionDecisions", build, facts, proposals)
        result: dict[str, str | None] = {}
        for decision in decisions:
            issues = list(decision.get("issues") or ())
            reports = list(decision.get("reports") or ())
            blocked = next((str(issue.get("message")) for issue in issues), None)
            if blocked is None and reports:
                blocked = str(reports[0].get("message"))
            result[str(decision["proposal"]["id"])] = blocked
        return result

    def _hand_fact(self, item_id: str | None) -> dict | None:
        """Canonical hand count of one mechanic, when the catalogue declares it.

        `hands` is a mechanic fact, not an item fact, so the adapter projects it
        explicitly: the shared module must not guess a hand count.
        """
        if not item_id or item_id not in self._mechanics:
            return None
        hands = self._mechanics[item_id].get("hands")
        return {"id": item_id, "kind": "equipment", "hands": hands} if isinstance(hands, int) else None

    def selection_decisions(self, choice: ProfileChoice, proposals, *, main_weapon_id=None,
                            off_hand_id=None, main_poison_id=None, off_poison_id=None,
                            skills: tuple[str, ...] = (),
                            exception_rule_ids: tuple[str, ...] = (),
                            variant_ids: tuple[str, ...] = ()) -> dict[str, str | None]:
        """Shared verdict per raw proposal, keyed by the proposed entry id.

        The same batch primitive the editor uses, exposed for the comparison
        tabs so a large candidate list still submits a single transport call.
        """
        package, profile, build = self._selection_context(choice, variant_ids=variant_ids)
        selections = [{"id": str(proposal["id"]), "kind": "equipment",
                       "slot": proposal.get("slot", "main")} for proposal in proposals]
        selections.extend(entry for entry in (
            self._hand_fact(main_weapon_id), self._hand_fact(off_hand_id)) if entry)
        facts = self._declared_facts(
            package, profile, build, selections,
            main_weapon_id=main_weapon_id, off_hand_id=off_hand_id,
            main_poison_id=main_poison_id, off_poison_id=off_poison_id,
            skills=skills, exception_rule_ids=exception_rule_ids)
        decisions = construction_call("selectionDecisions", build, facts, list(proposals))
        return {
            str(decision["proposal"]["id"]): next(
                (str(issue["message"]) for issue in decision.get("issues") or ()),
                str((decision.get("reports") or [{}])[0].get("message")) if decision.get("reports") else None,
            )
            for decision in decisions
        }

    def _declared_facts(self, package, profile, build, selections, *, main_weapon_id=None,
                        off_hand_id=None, main_poison_id=None, off_poison_id=None,
                        skills: tuple[str, ...] = (), exception_rule_ids: tuple[str, ...] = ()) -> dict:
        """A single-selection comparison context, with the whole-set facts.

        A direct selection is decided against the same band limits and loaded
        poisons the final validation reads: the band-wide prohibition tokens, the
        whole-set equipment limits and the active poisons travel with the
        candidate instead of being resolved only when the kit is confirmed.
        """
        band = desktop_call("bandFacts", build, package=package, profile=profile)
        return {
            "profile": self._profile_facts(package, profile, build),
            "items": {}, "skills": {skill_id: self._skill_facts(skill_id) for skill_id in skills},
            "selections": selections,
            "slots": {"main_weapon_id": main_weapon_id, "off_hand_id": off_hand_id,
                      "main_poison_id": main_poison_id, "off_poison_id": off_poison_id},
            "limits": band["equipment_limits"], "band_forbids": band["equipment_forbids"],
            "operation": {"product": "combat-lab",
                          "ignores_hand_restrictions": list(exception_rule_ids)},
        }

    def _profile_facts(self, package, profile, build) -> dict:
        """Shared `ProfileFacts` projection of one canonical profile.

        The projection resolves the declared equipment lists through the
        installed catalogue (the same materialisation the offering operation
        uses), so access enforcement and offered options cannot drift apart.
        The catalogue belongs to the installed transport, not to the adapter.
        """
        return desktop_call("profileFacts", build, package=package, profile=profile)

    def _skill_facts(self, skill_id: str) -> dict | None:
        row = next((row for row in load_skills(self.ruleset) if str(row["id"]) == skill_id), None)
        if row is None:
            return None
        return {"id": skill_id, "category": str(row.get("category") or ""),
                "kind": str(row.get("kind") or "general")}

    def hand_exception_rule_ids(self, choice: ProfileChoice | None,
                                selected_rule_ids: tuple[str, ...] = ()) -> tuple[str, ...]:
        """Canonical rules whose binding lifts the two-hand loadout limit.

        The exception is a rule the warrior may select (Arms Master, Master of
        Arms), so the fact depends on the current selection, not only on the
        profile. The shared module owns the rule meaning: this adapter asks it
        which selected bindings carry the exception and never keeps its own
        rule-id table.
        """
        if choice is None:
            return ()
        package, _profile, build = self._selection_context(choice)
        selected = tuple(dict.fromkeys((*selected_rule_ids, *build.special_rule_ids)))
        if not selected:
            return ()
        bindings = call("selectedRuleBindings", package_facts(package), list(selected))
        return tuple(sorted({str(binding["id"]) for binding in bindings
                             if str(binding.get("id")) in HAND_EXCEPTION_BINDINGS}))

    def _profile_equipment(self, choice: ProfileChoice, families, allowed) -> tuple[tuple[str, str], ...]:
        package = self._packages[(choice.collection, choice.band_id)]
        profile = next(row for row in package.profiles if row["id"] == choice.profile_id)
        build = FighterBuild(self.ruleset, collection=choice.collection,
                             band_id=choice.band_id, profile_id=choice.profile_id)
        item_ids = desktop_call("catalogueEquipment", build, package=package, profile=profile)
        if isinstance(families, str):
            families = (families,)
        prefixes = tuple({"weapons": "weapon.", "defences": "defence.", "armours": "armour.", "materials": "material.", "preparations": "preparation.", "poisons": "poison."}[family] for family in families)
        result = {item_id for item_id in item_ids
                  if item_id in self._mechanics and item_id.startswith(prefixes)
                  and allowed(self._mechanics[item_id])}
        return tuple(sorted(((item_id, str(self._mechanics[item_id]["name"])) for item_id in result), key=lambda item: item[1]))

    def _runtime_equipment(self, families, allowed) -> tuple[tuple[str, str], ...]:
        if isinstance(families, str):
            families = (families,)
        prefixes = tuple({"weapons": "weapon.", "defences": "defence.", "armours": "armour.", "materials": "material.", "preparations": "preparation.", "poisons": "poison."}[family] for family in families)
        result = {
            item_id for item_id, row in self._mechanics.items()
            if item_id.startswith(prefixes) and item_id not in self._excluded_mechanics and allowed(row)
        }
        return tuple(sorted(((item_id, str(self._mechanics[item_id]["name"])) for item_id in result), key=lambda item: item[1]))
