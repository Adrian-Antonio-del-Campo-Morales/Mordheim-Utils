"""construction: Free-selection and profile-based fighter build construction."""
from __future__ import annotations

from mordheim_core.models import Characteristics
from mordheim_construction.combat_packages import combat_packages
from mordheim_knowledge.loader import load_runtime_scope
from mordheim_knowledge.loader import runtime_bindings
from mordheim_construction.eligibility import call, desktop_call, package_facts
import re as re
from dataclasses import replace


def _profile(build, root):
    # A free-selection build supplies its whole profile as characteristics.
    # A band/profile build may also supply them: those are player advances
    # over the KB starting profile, while the package still governs legal
    # equipment, skills and special rules.
    if build.characteristics is not None and not build.band_id:
        return build.characteristics, {}, None, None, ()
    for package in combat_packages(build.collection, root):
        if package.band.get("id") != build.band_id: continue
        if package.ruleset != build.ruleset:
            raise ValueError(
                f"band {build.collection}/{build.band_id} uses ruleset "
                f"{package.ruleset}, not {build.ruleset}"
            )
        for profile in package.profiles:
            if profile.get("id") != build.profile_id: continue
            if build.variant_ids:
                profile = call("configuredProfile", profile, build.variant_ids)
            exclusions={(row.get("band_id"),row.get("profile_id")):row.get("reason") for row in load_runtime_scope(build.ruleset,root).get("profile_exclusions") or ()}
            reason=exclusions.get((build.band_id,build.profile_id))
            if reason:raise ValueError(f"profile is outside the duel runtime: {build.band_id}/{build.profile_id}: {reason}")
            if "hireling_equipment" in profile:
                if profile.get("normalization_status") != "normalized" or not profile.get("characteristics"):
                    raise ValueError(f"hireling has no canonical duel profile: {profile['id']}")
                pending = [r['id'] for r in package.special_rules
                    if profile['id'] in (r.get('applies_to') or {}).get('profile_ids', ())
                    and (not r.get('runtime') or ((r['runtime'].get('grant') == 'profile')
                        and r['runtime'].get('scope') != 'NO' and r['runtime'].get('implemented') != 'YES'))]
                if pending:
                    raise ValueError(f"hireling intrinsic duel clauses are pending: {pending}")
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
            contextual = {name: c.get(key) if isinstance(c.get(key), int) else None
                          for key, name in (("M", "movement"), ("Ld", "leadership"))}
            base = Characteristics(values["WS"],values["S"],values["T"],values["W"],values["I"],values["A"], **contextual)
            if build.characteristics is not None:
                base = replace(build.characteristics, **{
                    name: getattr(build.characteristics, name) if getattr(build.characteristics, name) is not None else value
                    for name, value in contextual.items()
                })
            return base, dict(profile.get("combat_traits") or {}), package, profile, tuple(random)
        raise KeyError(f"unknown profile {build.band_id}/{build.profile_id}")
    raise KeyError(f"unknown band {build.collection}/{build.band_id}")


def _applicable_profile_rules(package, profile):
    ids = {row["id"] for row in call("applicableProfileRules", package_facts(package), profile)}
    return tuple(rule for rule in package.special_rules if rule.get("id") in ids)


def _applicable_rules(package, profile):
    ids = [row["id"] for row in call("applicableRules", package_facts(package), profile)]
    by_id = {rule.get("id"): rule for rule in package.special_rules}
    return tuple(by_id[rule_id] for rule_id in ids)


def available_special_rules(build, root):
    """Editorial eligibility is shared; duel runtime support is a later check."""
    _, _, package, profile, _ = _profile(build, root)
    if package is None or profile is None:
        return ()
    return tuple(desktop_call("specialRules", build, root, package=package, profile=profile))


def _profile_rule_mechanics(package, profile):
    """Return automatic profile rules that have an executable mechanic binding."""
    rules = _applicable_rules(package, profile)
    return tuple(
        str(binding["id"])
        for rule in rules
        if (rule.get("runtime") or {}).get("implemented") == "YES"
        and (rule.get("runtime") or {}).get("grant") in {"profile", "band"}
        for binding in runtime_bindings(rule, "mechanic")
        if not (binding.get("parameters") or {}).get("profile_ids")
        or profile["id"] in binding["parameters"]["profile_ids"]
    )


def _profile_rule_traits(package, profile):
    """Runtime traits of the rules that apply to one profile.

    A rule granted to the profile replaces the band-wide default for the same
    trait key instead of stacking with it: Treekin's Redwood raises Bark Skin to
    4+ for that profile alone. Two rules of the same scope with different values
    are still ambiguous and stay refused.
    """
    traits = {}
    owner = {}
    rules=_applicable_rules(package, profile)
    for rule in rules:
        runtime = rule.get("runtime") or {}
        if runtime.get("implemented") != "YES" or runtime.get("grant") not in {"profile", "band"}:
            continue
        grant = str(runtime.get("grant"))
        for binding in runtime_bindings(rule, "trait"):
            key = str(binding["id"]).removeprefix("trait.").replace("-", "_")
            value = (binding.get("parameters") or {}).get("value")
            previous = owner.get(key)
            if previous is not None and traits[key] != value:
                if previous == grant:
                    raise ValueError(f"conflicting runtime trait {key} for {package.band.get('id')}/{profile.get('id')}")
                if previous == "profile":
                    continue
            traits[key] = value
            owner[key] = grant
    return traits
