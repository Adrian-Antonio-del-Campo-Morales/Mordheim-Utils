"""T09 mandatory-variant parity: the published options stay true to the KB.

``roster.requires_variant_selection`` demands a choice the application must ask
for before the warband is usable, and ``band.yaml`` ``variants`` publishes the
options.  Their construction consequences are resolved by the Web contract
(``packages/typescript/domain/campaign/construction.ts``) and by the shared
compiler (``mordheim_construction.restrictions``), so the three must agree on
the same ids and the same slots:

- every band that demands the choice publishes at least one option (zero
  mandatory options missing), each with a display name in both locales;
- ``khemri-lahmian-brotherhood`` publishes ``background.foreign`` and
  ``background.native`` — the ids ``compiler.foreign-or-native-background`` and
  the accepted semantic spec consume — and each option activates the
  ``<background>-<family>-equipment-list`` lists the band really publishes;
- ``chaos-streets-undead-bloodlines`` publishes one option per ``profiles.yaml``
  ``bloodline`` value, and nothing else;
- the option opens exactly the roster slots the roster gates with ``maximum: 0``,
  and the bound it publishes is the printed one: ``source.section`` states
  ``0-N`` for a capped Henchman group and ``1 <Name>`` for the single leader;
- a gated slot whose printed cap the KB does not publish is pinned here as the
  declared gap instead of drifting silently;
- the profile-side list binding the option resolves (a member that declares the
  two candidate lists keeps the chosen one) is published, not implied by prose;
- the shared compiler's own Foreign/Native sets are the same four profiles.

The gate only reads ``sources/knowledge``, the accepted specs and the shared
compiler source.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from mordheim_knowledge.loader import load_bands, load_collections

ROOT = Path(__file__).resolve().parents[3]
KB = ROOT / "sources" / "knowledge"
SPECS = ROOT / "tests" / "specs" / "semantic" / "grants"

KHEMRI = "khemri-lahmian-brotherhood"
BLOODLINES = "chaos-streets-undead-bloodlines"
BACKGROUND_IDS = ("background.foreign", "background.native")
BACKGROUND_ONLY = re.compile(r"^(foreign|native)\s+background\s+only\.$", re.IGNORECASE)
PRINTED_CAP = re.compile(r"^0-(\d+)\b")
PRINTED_LEADER = re.compile(r"^1\s+\S")
UNDEAD_FAMILY = re.compile(r"undead\s+(?:warband\s+)?equipment\s+list", re.IGNORECASE)
BELOVED_FAMILY = re.compile(r"beloved\s+(?:warband\s+)?equipment\s+list", re.IGNORECASE)
#: Gated slots whose printed cap the KB does not publish: `jackals` is listed
#: under the heading `Jackals`, without a `0-N` range, so the option opens it
#: with no bound and the Web contract reports the pending maximum.
DECLARED_CAP_GAPS = {("trollheim", KHEMRI, "jackals")}


def _packages() -> dict[tuple[str, str], object]:
    out = {}
    for collection in (row["id"] for row in load_collections()):
        for package in load_bands(str(collection), KB):
            out[(str(collection), str(package.band["id"]))] = package
    return out


def _members(package) -> dict[str, dict]:
    return {
        str(member["profile_id"]): member
        for member in (package.band.get("roster") or {}).get("members") or ()
    }


def _profiles(package) -> dict[str, dict]:
    return {str(profile["id"]): profile for profile in package.profiles}


def _gated(package) -> set[str]:
    return {profile_id for profile_id, member in _members(package).items() if member["maximum"] == 0}


def _opened(package) -> set[str]:
    return {
        str(row["profile_id"])
        for variant in package.band["variants"]
        for row in variant.get("roster_members") or ()
    }


def test_every_band_that_demands_a_choice_publishes_options():
    missing = []
    for (collection, band_id), package in _packages().items():
        roster = package.band.get("roster") or {}
        if roster.get("requires_variant_selection") and not package.band.get("variants"):
            missing.append(f"{collection}/{band_id}")
        for variant in package.band.get("variants") or ():
            assert str(variant["id"]).strip(), variant
            assert str(variant["name"]).strip(), variant
            assert str(variant["name_i18n"]["es"]).strip(), variant
    assert missing == [], (
        "a band that declares roster.requires_variant_selection must publish its "
        f"options in band.yaml `variants`: {missing}"
    )


def test_every_mandatory_choice_opens_exactly_the_gated_slots():
    for (collection, band_id), package in _packages().items():
        roster = package.band.get("roster") or {}
        if not roster.get("requires_variant_selection"):
            # The `maximum: 0` marker belongs to the mandatory choice only: a
            # band that does not demand it publishes no gated slot.
            assert _gated(package) == set(), (
                f"{collection}/{band_id} gates {sorted(_gated(package))} without declaring "
                "roster.requires_variant_selection"
            )
            continue
        gated, opened, members = _gated(package), _opened(package), _members(package)
        assert gated <= opened, (
            f"{collection}/{band_id}: gated slots no published option opens: {sorted(gated - opened)}"
        )
        assert opened <= set(members), (
            f"{collection}/{band_id}: an option opens a slot the roster does not declare: "
            f"{sorted(opened - set(members))}"
        )
        for variant in package.band["variants"]:
            for row in variant.get("roster_members") or ():
                profile_id = str(row["profile_id"])
                assert profile_id in members, f"{band_id}/{variant['id']}: unknown slot {profile_id}"
                assert members[profile_id]["maximum"] == 0, (
                    f"{band_id}/{variant['id']}: {profile_id} is not gated by the roster "
                    f"(its published maximum is {members[profile_id]['maximum']!r}); an option "
                    "may only open a slot the roster marks `maximum: 0`"
                )


def test_published_bounds_are_the_printed_ones():
    checked = 0
    for (collection, band_id), package in _packages().items():
        if not (package.band.get("roster") or {}).get("requires_variant_selection"):
            continue
        profiles = _profiles(package)
        for variant in package.band["variants"]:
            for row in variant.get("roster_members") or ():
                profile_id = str(row["profile_id"])
                profile = profiles.get(profile_id)
                assert profile is not None, (
                    f"{band_id}/{variant['id']}: {profile_id} has no profile row, so its "
                    "printed bound cannot be checked"
                )
                section = str(profile["source"]["section"])
                cap = PRINTED_CAP.match(section)
                if cap:
                    assert row.get("maximum") == int(cap.group(1)), (
                        f"{profile_id}: the printed heading {section!r} publishes 0-{cap.group(1)} "
                        f"but the option opens it with {row.get('maximum')!r}"
                    )
                    checked += 1
                elif PRINTED_LEADER.match(section):
                    assert row.get("minimum") == 1 and row.get("maximum") == 1, (
                        f"{profile_id}: the printed heading {section!r} publishes a single model, "
                        f"but the option opens it as {row.get('minimum')!r}/{row.get('maximum')!r}"
                    )
                    checked += 1
                else:
                    assert (collection, band_id, profile_id) in DECLARED_CAP_GAPS, (
                        f"{profile_id}: the printed cap is not published ({section!r}); either "
                        "publish it in roster_members or declare the gap in DECLARED_CAP_GAPS"
                    )
    assert checked >= 5, checked


def test_khemri_publishes_the_canonical_background_ids():
    package = _packages()[("trollheim", KHEMRI)]
    variants = package.band["variants"]
    assert tuple(str(row["id"]) for row in variants) == BACKGROUND_IDS
    for row in variants:
        assert row["rule_ids"] == ["band--background-selection"], row
    # The choice rule is the printed one and stays bound to the shared contract.
    rule = next(r for r in package.special_rules if r["id"] == "band--background-selection")
    binding = rule["runtime"]["effects"][0]["binding"]
    assert binding["kind"] == "compiler"
    assert binding["id"] == "compiler.foreign-or-native-background"


def test_every_background_option_names_published_equipment_lists():
    package = _packages()[("trollheim", KHEMRI)]
    lists = {str(row["id"]) for row in package.equipment_lists}
    profiles = _profiles(package)
    for row in package.band["variants"]:
        background = str(row["id"]).split(".", 1)[1]
        published = sorted(list_id for list_id in lists if list_id.startswith(f"{background}-"))
        assert published, (
            f"{row['id']} publishes no {background}-*-equipment-list; the option has no "
            "equipment consequence to apply"
        )
        assert sorted(str(value) for value in row["equipment_lists"]) == published, row
        for list_id in published:
            family = "beloved" if "beloved" in list_id else "undead"
            for profile_id, profile in profiles.items():
                restriction = " / ".join(str(text) for text in profile["equipment_restrictions"])
                declares_family = (
                    BELOVED_FAMILY.search(restriction) if family == "beloved" else UNDEAD_FAMILY.search(restriction)
                )
                if not declares_family:
                    continue
                candidate = f"{background}-{family}-equipment-list"
                declared = {str(value) for value in profile["equipment_lists"]}
                if declared:
                    assert candidate in declared or any(
                        value.endswith(f"-{family}-equipment-list") for value in declared
                    ), f"{profile_id} declares {sorted(declared)} but not {candidate}"


def test_khemri_profile_lists_follow_the_printed_background_restrictions():
    package = _packages()[("trollheim", KHEMRI)]
    profiles = _profiles(package)
    restricted = {
        profile_id: BACKGROUND_ONLY.match(str(text).strip()).group(1).lower()
        for profile_id, profile in profiles.items()
        for text in profile["equipment_restrictions"]
        if BACKGROUND_ONLY.match(str(text).strip())
    }
    assert restricted == {
        "blood-slaves": "foreign",
        "black-hounds": "foreign",
        "spirits": "native",
        "jackals": "native",
    }, restricted
    for profile_id, background in restricted.items():
        declared = {str(value) for value in profiles[profile_id]["equipment_lists"]}
        expected = (
            set()
            if profile_id in {"black-hounds", "jackals"}
            else {f"{background}-undead-equipment-list"}
        )
        assert declared == expected, (
            f"{profile_id} is restricted to the {background} background, so it may only "
            f"declare {sorted(expected)}; it declares {sorted(declared)}"
        )
    # A profile assigned the background's list declares both candidates and keeps
    # the chosen one when the contract intersects them.
    assigned = {
        profile_id: {str(value) for value in profile["equipment_lists"]}
        for profile_id, profile in profiles.items()
        if profile["equipment_lists"]
    }
    for profile_id, declared in assigned.items():
        if profile_id in restricted:
            continue
        assert declared == {
            "foreign-undead-equipment-list",
            "native-undead-equipment-list",
        } or declared == {
            "foreign-beloved-equipment-list",
            "native-beloved-equipment-list",
        }, f"{profile_id} declares {sorted(declared)}"


def test_the_shared_compiler_reads_the_same_four_profiles():
    package = _packages()[("trollheim", KHEMRI)]
    opened = {
        str(row["profile_id"]): str(variant["id"]).split(".", 1)[1]
        for variant in package.band["variants"]
        for row in variant.get("roster_members") or ()
    }
    from mordheim_core.models import FighterBuild
    from mordheim_construction.eligibility import desktop_call

    for profile_id, background in opened.items():
        profile = next(row for row in package.profiles if row['id'] == profile_id)
        for selected in ('foreign', 'native'):
            build = FighterBuild('mordheim', collection='trollheim', band_id=KHEMRI,
                                 profile_id=profile_id, main_weapon_id='weapon.natural-attacks',
                                 variant_ids=(f'background.{selected}',))
            verdict = desktop_call('profileSelections', build, KB, package=package,
                                   profile=profile,
                                   compiler_contracts=('compiler.foreign-or-native-background',))
            if selected != background:
                assert verdict == f'{profile_id} requires the {background.title()} background'
            else:
                assert verdict is None, verdict


def test_bloodline_options_follow_the_profile_bloodlines():
    package = _packages()[("trollheim", BLOODLINES)]
    profiles = _profiles(package)
    declared = {str(profile["bloodline"]) for profile in profiles.values() if profile.get("bloodline")}
    assert declared == {"von-carstein", "lahmia", "blood-dragon", "necrarch", "strigoi"}, declared
    variants = package.band["variants"]
    option_ids = [str(row["id"]) for row in variants]
    assert sorted(option_ids) == sorted(declared), option_ids
    for row in variants:
        assert "band--choose-bloodline" in row["rule_ids"], row
        assert "band--vampiric-powers" in row["rule_ids"], row
        slug = str(row["id"])
        vampire = f"{slug}-vampire"
        assert vampire in _members(package), f"{slug} has no {vampire} roster slot"
        assert str(profiles[vampire]["bloodline"]) == slug
        assert {
            str(slot["profile_id"]) for slot in row["roster_members"]
        } == {vampire, *({"carrion-ghoul"} if slug == "strigoi" else set())}, row


def test_the_accepted_specs_use_the_published_ids():
    spec = yaml.safe_load((SPECS / "khemri-background.yaml").read_text(encoding="utf-8"))
    used = set()
    for specification in spec["specifications"]:
        for case in specification["cases"]:
            for choice in ((case.get("context") or {}).get("choices") or {}).values():
                used.update(str(value) for value in choice.get("variant_ids") or ())
            used.update(str(value) for value in (case.get("attacker") or {}).get("variant_ids") or ())
    assert used, "the accepted spec must exercise the background ids"
    assert used <= set(BACKGROUND_IDS), (
        f"the accepted semantic spec uses ids the KB does not publish: {sorted(used - set(BACKGROUND_IDS))}"
    )
