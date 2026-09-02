"""application.catalogue: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from dataclasses import dataclass
from mordheim_knowledge.loader import BandPackage
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import load_collections
from mordheim_knowledge.loader import load_mechanics
from mordheim_knowledge.loader import load_runtime_scope
from mordheim_knowledge.loader import load_simulation_mappings
from mordheim_knowledge.loader import load_skills


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


class CombatCatalogue:
    """Small index used by the new UI selectors."""

    def __init__(self, ruleset: str = "mordheim"):
        self.ruleset = ruleset
        self._packages = {
            (package.collection, str(package.band["id"])): package
            for collection in load_collections()
            if ruleset in collection.get("rulesets", ())
            for package in load_bands(str(collection["id"]))
            if package.ruleset == ruleset
        }
        self._mechanics = {
            str(row["id"]): row
            for family in ("weapons", "defences", "armours", "materials", "preparations", "poisons")
            for row in load_mechanics(ruleset).get(family, ())
        }
        exclusions = load_runtime_scope(ruleset).get("mechanic_exclusions") or ()
        self._excluded_mechanics = {str(row["id"]) for row in exclusions}
        self._excluded_mechanic_reasons = {
            str(row["id"]): str(row.get("reason") or "").strip()
            for row in exclusions
        }
        option_to_id = {str(row.get("engine_option")): item_id for item_id, row in self._mechanics.items()}
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
        return tuple(ProfileChoice(collection, band_id, str(row["id"]), str(row["name"])) for row in package.profiles)

    def profile(self, choice: ProfileChoice) -> dict:
        """Return profile data for display, not editable UI state."""
        package = self._packages[(choice.collection, choice.band_id)]
        return next(row for row in package.profiles if row["id"] == choice.profile_id)

    def mechanic(self, mechanic_id: str) -> dict:
        """Return the normalized mechanic metadata used for UI constraints."""
        return self._mechanics[mechanic_id]

    def skills(self, choice: ProfileChoice | None) -> tuple[SkillChoice, ...]:
        """Return every general category plus the selected band's special skills."""
        profile = self.profile(choice) if choice else None
        allowed_categories = set(profile.get("skill_access") or ()) if profile else None
        general = tuple(
            SkillChoice(
                str(skill["id"]),
                str(skill["name"]),
                str(skill["category"]),
                str(skill.get("summary") or ""),
                self._skill_unavailable_reason(skill),
                runtime_available=(
                    (allowed_categories is None or str(skill.get("category") or "") in allowed_categories)
                    and self._catalogue_skill_is_available(skill)
                ),
            )
            for skill in load_skills(self.ruleset)
            if str(skill.get("category") or "") != "special"
        )
        return (*general, *self._warband_skills(choice))

    def in_scope_skill_ids(self, skills) -> set[str]:
        """Return skill IDs executable by the current one-against-one runtime."""
        return {
            skill.id for skill in skills
            if skill.runtime_available and skill.id not in self._excluded_mechanics
        }

    def skill_rule_ids(self, selected_ids) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Split UI selections into ordinary skill IDs and band-rule IDs."""
        choices = {skill.id: skill for skill in self.skills(None)}
        ordinary, special = [], []
        for selected_id in selected_ids:
            skill = choices.get(selected_id)
            if skill is None:
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
        return self._excluded_mechanic_reasons.get(str(skill["id"])) or None

    def _catalogue_skill_is_available(self, skill: dict) -> bool:
        runtime = skill.get("runtime")
        if runtime:
            return runtime.get("scope") == "YES" and runtime.get("implemented") == "YES"
        return str(skill["id"]) not in self._excluded_mechanics

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

    def _warband_skills(self, choice: ProfileChoice | None) -> tuple[SkillChoice, ...]:
        packages = (
            (self._packages[(choice.collection, choice.band_id)],)
            if choice is not None else tuple(self._packages.values())
        )
        profile = self.profile(choice) if choice is not None else None
        has_special_access = choice is None or "special" in set(profile.get("skill_access") or ())
        result = []
        for package in packages:
            band_name = str(package.band.get("name") or package.band["id"])
            for rule in package.special_rules:
                if rule.get("kind") != "warband_skill":
                    continue
                runtime = rule.get("runtime") or {}
                eligible = (
                    choice is None
                    or (
                        has_special_access
                        and (
                            not (rule.get("eligibility") or ())
                            or choice.profile_id in rule.get("eligibility", ())
                        )
                    )
                )
                result.append(SkillChoice(
                    self._warband_skill_id(package, rule),
                    (
                        f"{rule.get('name') or rule['id']} · {band_name}"
                        if choice is None
                        else str(rule.get("name") or rule["id"])
                    ),
                    "special",
                    str(rule.get("effect") or ""),
                    self._rule_unavailable_reason(rule),
                    "warband_skill",
                    str(rule["id"]),
                    eligible
                    and runtime.get("scope") == "YES"
                    and runtime.get("implemented") == "YES",
                ))
        return tuple(result)

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
                str(rule.get("effect") or ""),
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
        return tuple(
            SkillChoice(
                str(rule["id"]),
                str(rule["name"]),
                str(rule.get("kind") or "selectable rule").replace("_", " ").title(),
                str(rule.get("effect") or ""),
                self._rule_unavailable_reason(rule),
                str(rule.get("kind") or "selectable_rule"),
                str(rule["id"]),
                (rule.get("runtime") or {}).get("scope") == "YES"
                and (rule.get("runtime") or {}).get("implemented") == "YES",
            )
            for rule in package.special_rules
            if rule.get("kind") != "warband_skill"
            and (rule.get("runtime") or {}).get("grant") == "selectable"
            and (not rule.get("eligibility") or choice.profile_id in rule.get("eligibility", ()))
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

    def _profile_equipment(self, choice: ProfileChoice, families, allowed) -> tuple[tuple[str, str], ...]:
        package = self._packages[(choice.collection, choice.band_id)]
        profile = next(row for row in package.profiles if row["id"] == choice.profile_id)
        lists = {str(row["id"]): row for row in package.equipment_lists}
        item_ids = set(profile.get("fixed_equipment") or ())
        list_ids=list(profile.get("equipment_lists") or ())
        extra_lists=[]
        if choice.band_id == "lustria-pirates":
            mercenary=self._packages[("mordheim","mercenaries")]
            extra_lists.extend(mercenary.equipment_lists)
        if choice.band_id == "khemri-lahmian-brotherhood" and not list_ids:
            role="beloved" if choice.profile_id=="beloved" else "undead"
            list_ids.append(f"foreign-{role}-equipment-list")
        for list_id in list_ids:
            equipment_list=lists[str(list_id)]
            item_ids.update(str(row["item_id"]) for row in equipment_list.get("items") or ())
            def loadout_items(value):
                if isinstance(value,str):yield value
                elif isinstance(value,list):
                    for entry in value:yield from loadout_items(entry)
                elif isinstance(value,dict):
                    for entry in value.values():yield from loadout_items(entry)
            for loadout in equipment_list.get("loadouts") or ():
                item_ids.update(loadout_items(loadout.get("items") or ()))
        for equipment_list in extra_lists:
            item_ids.update(str(row["item_id"]) for row in equipment_list.get("items") or ())
        if isinstance(families, str):
            families = (families,)
        prefixes = tuple({"weapons": "weapon.", "defences": "defence.", "armours": "armour.", "materials": "material.", "preparations": "preparation.", "poisons": "poison."}[family] for family in families)
        result = {
            self._item_mechanics[item_id]
            for item_id in item_ids
            if item_id in self._item_mechanics
            and self._item_mechanics[item_id].startswith(prefixes)
            and allowed(self._mechanics[self._item_mechanics[item_id]])
        }
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
