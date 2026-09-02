"""construction.selection: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from mordheim_core.models import Characteristics
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import load_runtime_scope
from mordheim_knowledge.loader import load_simulation_mappings
from mordheim_knowledge.loader import runtime_bindings
import re as re


def _profile(build, root):
    # A free-selection build supplies its whole profile as characteristics.
    # A band/profile build may also supply them: those are player advances
    # over the KB starting profile, while the package still governs legal
    # equipment, skills and special rules.
    if build.characteristics is not None and not build.band_id:
        return build.characteristics, {}, None, None, ()
    for package in load_bands(build.collection, root):
        if package.band.get("id") != build.band_id: continue
        if package.ruleset != build.ruleset:
            raise ValueError(
                f"band {build.collection}/{build.band_id} uses ruleset "
                f"{package.ruleset}, not {build.ruleset}"
            )
        for profile in package.profiles:
            if profile.get("id") != build.profile_id: continue
            exclusions={(row.get("band_id"),row.get("profile_id")):row.get("reason") for row in load_runtime_scope(build.ruleset,root).get("profile_exclusions") or ()}
            reason=exclusions.get((build.band_id,build.profile_id))
            if reason:raise ValueError(f"profile is outside the duel runtime: {build.band_id}/{build.profile_id}: {reason}")
            c = profile["characteristics"]
            if build.band_id == "carnival-of-chaos" and build.profile_id == "plague-cart":
                guardian = next(component for component in profile.get("components") or () if component.get("id") == "guardian")
                c = {**c, **{
                    key: guardian["characteristics"][key]
                    for key in ("WS", "S", "I", "A")
                }}
            values={};random=[]
            for key in ("WS","S","T","W","I","A"):
                value=c.get(key)
                if isinstance(value,int):values[key]=value;continue
                match=re.fullmatch(r"(\d*)D(\d+)(?:\+(\d+))?",str(value),re.IGNORECASE)
                if not match:raise ValueError(f"profile {build.band_id}/{build.profile_id} is not an individual close-combat fighter")
                dice=int(match.group(1) or 1);sides=int(match.group(2));bonus=int(match.group(3) or 0)
                values[key]=dice+bonus;random.append((key,dice,sides,bonus))
            base = Characteristics(values["WS"],values["S"],values["T"],values["W"],values["I"],values["A"])
            return build.characteristics or base, dict(profile.get("combat_traits") or {}), package, profile, tuple(random)
        raise KeyError(f"unknown profile {build.band_id}/{build.profile_id}")
    raise KeyError(f"unknown band {build.collection}/{build.band_id}")


def _profile_allowed_mechanics(package, profile, mechanics, ruleset, root):
    by_option={str(row.get("engine_option")):mid for mid,row in mechanics.items() if row.get("engine_option")}
    mapping={str(row["item_id"]):row for row in load_simulation_mappings(ruleset,root).get("item_mappings") or ()}
    lists={row.get("id"):row for row in package.equipment_lists}
    item_ids=set(profile.get("fixed_equipment") or ())
    for list_id in profile.get("equipment_lists") or ():
        if list_id not in lists: raise ValueError(f"profile references unknown equipment list: {package.band.get('id')}/{profile.get('id')}/{list_id}")
        equipment_list=lists[list_id]
        item_ids.update(str(item.get("item_id")) for item in equipment_list.get("items") or ())
        def loadout_items(value):
            if isinstance(value,str):yield value
            elif isinstance(value,list):
                for entry in value:yield from loadout_items(entry)
            elif isinstance(value,dict):
                for entry in value.values():yield from loadout_items(entry)
        for loadout in equipment_list.get("loadouts") or ():
            item_ids.update(loadout_items(loadout.get("items") or ()))
    allowed=set()
    for item_id in item_ids:
        row=mapping.get(item_id)
        if not row or row.get("status")!="implemented":
            continue
        mechanic_id=row.get("mechanic_id") or by_option.get(str(row.get("engine_option")))
        if mechanic_id in mechanics:
            allowed.add(mechanic_id)
    allowed.update(
        str(binding["id"])
        for rule in _applicable_profile_rules(package, profile)
        for binding in runtime_bindings(rule, "mechanic")
        if binding.get("id") in mechanics
    )
    return allowed


def _applicable_profile_rules(package, profile):
    rule_ids = set(profile.get("rule_ids") or ())
    return tuple(
        rule for rule in package.special_rules
        if rule.get("id") in rule_ids or (
            (rule.get("runtime") or {}).get("grant") == "profile"
            and profile.get("id") in (rule.get("applies_to") or {}).get("profile_ids", ())
        )
    )


def _applicable_rules(package, profile):
    """Return profile and band rules that apply to this concrete fighter."""
    profile_rules = _applicable_profile_rules(package, profile)
    profile_rule_ids = {str(rule.get("id")) for rule in profile_rules}
    band_rules = tuple(
        rule for rule in package.special_rules
        if str(rule.get("id")) not in profile_rule_ids
        and (rule.get("runtime") or {}).get("grant") == "band"
        and rule.get("applies_to", {}).get("band") is True
        and (not rule.get("eligibility") or profile.get("id") in rule.get("eligibility", ()))
    )
    return (*profile_rules, *band_rules)


def _compiler_contract_bindings(rules):
    return tuple(
        binding
        for rule in rules
        if (rule.get("runtime") or {}).get("implemented") == "YES"
        for binding in runtime_bindings(rule, "compiler")
    )


def available_special_rules(build, root):
    """Return editorial warband skills legally available, regardless of duel support."""
    _, _, package, profile, _ = _profile(build, root)
    if package is None or profile is None:
        return ()
    has_special_access = "special" in set(profile.get("skill_access") or ())
    result = []
    for rule in package.special_rules:
        if rule.get("kind") != "warband_skill":
            continue
        eligible = set(rule.get("eligibility") or ())
        applicable = set((rule.get("applies_to") or {}).get("profile_ids") or ())
        if eligible and profile.get("id") not in eligible:
            continue
        if applicable and profile.get("id") not in applicable:
            continue
        if not eligible and not applicable and not has_special_access:
            continue
        result.append(str(rule["id"]))
    # The Streets Troll Slayer explicitly chooses from both his Pit Fighter
    # skills and the Dwarf Treasure Hunter special-skill list.
    contracts = {str(binding["id"]) for binding in _compiler_contract_bindings(_applicable_rules(package, profile))}
    if "compiler.slayer-skill-options" in contracts:
        dwarf_package = next(
            candidate for candidate in load_bands(build.collection, root)
            if candidate.band.get("id") == "chaos-streets-dwarf-treasure-hunters"
        )
        result.extend(
            str(rule["id"])
            for rule in dwarf_package.special_rules
            if rule.get("kind") == "warband_skill"
            and (rule.get("runtime") or {}).get("implemented") == "YES"
        )
    return tuple(sorted(result))


def _profile_rule_mechanics(package, profile):
    """Return automatic profile rules that have an executable mechanic binding."""
    rules = _applicable_rules(package, profile)
    return tuple(
        str(binding["id"])
        for rule in rules
        if (rule.get("runtime") or {}).get("implemented") == "YES"
        and (rule.get("runtime") or {}).get("grant") in {"profile", "band"}
        for binding in runtime_bindings(rule, "mechanic")
    )


def _profile_rule_traits(package, profile):
    traits = {}
    rules=_applicable_rules(package, profile)
    for rule in rules:
        runtime = rule.get("runtime") or {}
        if runtime.get("implemented") != "YES" or runtime.get("grant") not in {"profile", "band"}:
            continue
        for binding in runtime_bindings(rule, "trait"):
            key = str(binding["id"]).removeprefix("trait.").replace("-", "_")
            value = (binding.get("parameters") or {}).get("value")
            if key in traits and traits[key] != value:
                raise ValueError(f"conflicting runtime trait {key} for {package.band.get('id')}/{profile.get('id')}")
            traits[key] = value
    return traits
