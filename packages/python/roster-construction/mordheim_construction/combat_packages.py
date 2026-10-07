"""Canonical participant projections; campaign hiring and ownership stay outside."""
from __future__ import annotations

from copy import deepcopy

from mordheim_knowledge.campaign import load_hirelings, load_hireling_traits
from mordheim_knowledge.loader import BandPackage, knowledge_root, load_bands


def combat_packages(collection, root=None):
    bands = tuple(load_bands(collection, root))
    yield from bands
    if collection != "mordheim":
        return
    catalogue = load_hirelings("mordheim", root)
    traits = {row["profile_id"]: row["traits"] for row in load_hireling_traits("mordheim", root)}
    # The current 2A/2B work admits the promoted 2B hireling catalogue. Other
    # grades retain their existing campaign paths until their duel review.
    for kind in ("hired-sword", "dramatis-personae"):
        native = [p for p in catalogue.profiles if p.get("grade") == "2b" and p["kind"] == kind]
        if not native:
            continue
        profiles, lists, rules = [], [], []
        for source in native:
            profile = dict(source)
            profile["type"] = "hero"
            profile["hireling_equipment"] = deepcopy(source.get("equipment") or {})
            # Printed item-specific qualifications, not generic alias changes.
            for entry in profile["hireling_equipment"].get("fixed_items", ()):
                if source["id"] == "hireling.hired-sword.crimashin" and entry["item_id"] == "dagger":
                    entry["material_id"] = "material.gromril"
                if source["id"] == "hireling.hired-sword.holy-man" and entry["item_id"] == "staff":
                    entry["mechanic_id"] = "weapon.double-handed-weapon"
            intrinsic = list(source.get("rules") or [])
            if source["id"] == "hireling.hired-sword.sister-of-sigmar":
                sisters = next(pack for pack in bands if pack.band["id"] == "sisters-of-sigmar")
                for original in sisters.special_rules:
                    # The Matriarch-only skill is not granted to this hired Sister.
                    if original.get("kind") != "warband_skill" or "sister-superior" not in original.get("eligibility", ()):
                        continue
                    option = deepcopy(original)
                    option["eligibility"] = [source["id"]]
                    option["applies_to"] = {"profile_ids": [source["id"]]}
                    if option["runtime"]["scope"] == "NO":
                        # A legal starting choice with no melee effect still counts.
                        option["runtime"] = {"grant": "selectable", "scope": "YES", "implemented": "YES",
                            "effects": [*option["runtime"]["effects"], {
                                "id": option["id"] + ".starting-choice", "scope": "YES",
                                "binding": {"kind": "compiler", "id": "compiler.sister-special-skills"}}]}
                    intrinsic.append(option)
            profile["rule_ids"] = list(dict.fromkeys((*source.get("rule_ids", ()), *(r["id"] for r in intrinsic))))
            facts = set(traits.get(source["id"], ()))
            combat = {"starting_skills": list(source.get("starting_skill_ids") or ())}
            if "fear-causing" in facts:
                combat["causes_fear"] = True
            if "undead" in facts:
                combat["creature_kind"] = "undead"
            for species in ("human", "dwarf", "ogre", "orc", "goblin", "skaven", "halfling", "beastman"):
                if species in facts:
                    combat["species"] = species
            profile["combat_traits"] = combat
            list_id = source["id"] + ".kit"
            equipment = profile["hireling_equipment"]
            entries = [*equipment.get("fixed_items", ()), *equipment.get("optional_items", ())]
            for group in equipment.get("choices", ()):
                for option in group.get("options", ()):
                    entries.extend(option.get("items", ()))
            offered = list(dict.fromkeys([*(e["item_id"] for e in entries),
                *(item["id"] for item in equipment.get("unique_equipment", ())) ]))
            if any(e.get("mechanic_id") == "weapon.double-handed-weapon" for e in entries):
                offered.append("two_handed_weapon")
            if any(e.get("material_id") == "material.gromril" for e in entries):
                offered.append("gromril_weapon")
            lists.append({"id": list_id, "items": [{"item_id": item} for item in offered]})
            profile["equipment_lists"] = [list_id]
            profile["fixed_equipment"] = []
            profile["equipment_restrictions"] = []
            profiles.append(profile)
            for source_rule in intrinsic:
                rules.append({**source_rule, "applies_to": {"profile_ids": [source["id"]]},
                              "kind": "warband_skill" if source_rule.get("kind") == "warband_skill" or source_rule["id"] in source.get("special_skill_rule_ids", ()) else "profile"})
        title = "Hired Swords · 2B" if kind == "hired-sword" else "Dramatis Personae · 2B"
        yield BandPackage(collection, "mordheim",
            {"id": f"hirelings.{kind}.2b", "name": title,
             "name_i18n": {"es": "Espadas a Sueldo · 2B" if kind == "hired-sword" else title}, "categories": ["2b"]},
            tuple(profiles), tuple(lists), tuple(rules), (root or knowledge_root()) / "catalog/hirelings")
