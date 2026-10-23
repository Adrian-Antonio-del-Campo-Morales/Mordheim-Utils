"""C05a: the Dwarf and Slayer skill columns open their printed members.

The three Town Crier 6 columns and the promotion-time Born Marksmen grant are
one printed fact per profile: the band publishes the named recipients and the
printed member list through `profile.skill-access`, and the shared module is
what decides whether a skill may be chosen.  Nothing here reads the KB's prose
directly: every expectation is the shared module answering through the real
transport (`profileFacts`, `profileSkillLists`, `skillChoices`), so a member
list that stopped reaching its recipients fails instead of passing on the words
that describe it.
"""
import pytest

from mordheim_construction.eligibility import desktop_call
from mordheim_construction.selection import _profile
from mordheim_construction.source_profiles import prepare_source_profile
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import knowledge_root, load_bands, load_skills

ROOT = knowledge_root()
COLLECTION = "mordheim"

DWARF_TABLE = "band--town-crier-6-dwarf-special-skills"
SLAYER_TABLE = "band--slayer-special-skills"

#: Printed members of the Town Crier 6 Dwarf Special Skills column.  Master of
#: Blades is one printed entry and publishing it as Unbeatable Warrior is what
#: makes the column exact: the Vampire's Sword Master is a different contract.
DWARF_MEMBERS = ("skill.unbeatable-warrior", "skill.tough-as-steel", "skill.thick-skull")
#: Printed members of the Slayer column, per band.
SLAYER_MEMBERS = {
    "dwarf-slayers-kaz": ("skill.ferocious-charge", "skill.monster-slayer", "skill.berserker"),
    "dwarf-slayer-cult-web": ("skill.deathwish", "skill.ferocious-charge", "skill.monster-slayer",
                              "skill.berserker", "skill.deathblow", "skill.axe-mastery",
                              "skill.tough-as-steel", "skill.thick-skull"),
}
#: Printed members whose whole content is outside the duel, by the rule that
#: prints them.  Each one carries an explicit disposition instead of being
#: omitted for lacking a catalogue row.
DISPOSED_MEMBERS = {
    ("dwarf-guildsmen-kaz", "band--town-crier-6-dwarf-special-skills"):
        ("Extra Tough", "Resource Hunter"),
    ("dwarf-slayers-kaz", "band--town-crier-6-dwarf-special-skills"):
        ("Extra Tough", "Resource Hunter"),
    ("dwarf-slayer-cult-web", "band--slayer-special-skills"): ("Relentless",),
}
#: The shared operator each new Slayer member must reach through compilation.
NEW_MEMBERS = {
    "skill.deathwish": ("mechanic.psychology-immunity",),
    "skill.deathblow": ("mechanic.deathblow",),
    "skill.axe-mastery": ("skill.axe-expert", "skill.axe-mastery"),
}
#: The special list each profile publishes, by the rule that publishes it.
EXPECTED = {
    ("dwarf-guildsmen-kaz", "master-craftsman"): {DWARF_TABLE: DWARF_MEMBERS},
    ("dwarf-guildsmen-kaz", "expert-craftsmen"): {DWARF_TABLE: DWARF_MEMBERS},
    ("dwarf-guildsmen-kaz", "apprentices"): {DWARF_TABLE: DWARF_MEMBERS},
    ("dwarf-guildsmen-kaz", "artisans"): {},
    ("dwarf-guildsmen-kaz", "labourers"): {},
    ("dwarf-guildsmen-kaz", "dwarf-thunderers"): {},
    ("dwarf-slayers-kaz", "giant-slayer"): {
        DWARF_TABLE: DWARF_MEMBERS, SLAYER_TABLE: SLAYER_MEMBERS["dwarf-slayers-kaz"]},
    ("dwarf-slayers-kaz", "troll-slayers"): {
        DWARF_TABLE: DWARF_MEMBERS, SLAYER_TABLE: SLAYER_MEMBERS["dwarf-slayers-kaz"]},
    ("dwarf-slayers-kaz", "rememberer"): {DWARF_TABLE: DWARF_MEMBERS},
    ("dwarf-slayers-kaz", "slayers"): {},
    ("dwarf-slayers-kaz", "clansmen"): {},
    ("dwarf-slayer-cult-web", "giant-slayer"): {
        SLAYER_TABLE: SLAYER_MEMBERS["dwarf-slayer-cult-web"]},
    ("dwarf-slayer-cult-web", "doomseeker"): {
        SLAYER_TABLE: SLAYER_MEMBERS["dwarf-slayer-cult-web"]},
    # Not a Slayer: the printed prohibition leaves him no Slayer column at all.
    ("dwarf-slayer-cult-web", "rememberer"): {},
    ("dwarf-slayer-cult-web", "troll-slayers"): {},
    ("dwarf-slayer-cult-web", "stubbles"): {},
    ("dwarf-slayer-cult-web", "axe-hurlers"): {},
}


def _package(band):
    return next(row for row in load_bands(COLLECTION, ROOT) if row.band["id"] == band)


def _profile_row(pack, profile):
    return next(row for row in pack.profiles if row["id"] == profile)


def _build(band, profile, variants=()):
    return FighterBuild(COLLECTION, band_id=band, profile_id=profile, variant_ids=variants)


def _special_skills():
    return {str(row["id"]) for row in load_skills("mordheim", ROOT)
            if str(row.get("category")) == "special"}


def _choosable(pack, row, build):
    """Every special skill the shared module admits for this profile."""
    choices = desktop_call("skillChoices", build, ROOT, package=pack, profile=row)
    return {skill_id for skill_id in _special_skills() if choices.get(skill_id)}


@pytest.mark.phase2_construction
def test_each_column_publishes_its_printed_members_to_its_named_recipients():
    for (band, profile), expected in EXPECTED.items():
        pack = _package(band)
        row = _profile_row(pack, profile)
        build = _build(band, profile)
        lists = desktop_call("profileSkillLists", build, ROOT, package=pack, profile=row)
        published = {entry["rule_id"]: tuple(entry["skills"]) for entry in lists
                     if entry["category"] == "special"}
        assert published == expected, (band, profile, published)
        # The module's own answer for every special skill in the catalogue is
        # exactly the union of the published lists: a named member is choosable
        # and every other special skill is refused.
        assert _choosable(pack, row, build) == {skill for members in expected.values()
                                                for skill in members}, (band, profile)


@pytest.mark.phase2_construction
def test_master_of_blades_is_one_entry_and_never_the_vampire_contract():
    """One printed Master of Blades entry publishes exactly one skill."""
    for band, profile in (("dwarf-guildsmen-kaz", "master-craftsman"),
                          ("dwarf-slayers-kaz", "giant-slayer")):
        pack = _package(band)
        row = _profile_row(pack, profile)
        build = _build(band, profile)
        choices = desktop_call("skillChoices", build, ROOT, package=pack, profile=row)
        assert choices["skill.unbeatable-warrior"] is True, (band, profile)
        assert choices["skill.sword-master"] is False, (band, profile)


@pytest.mark.phase2_construction
def test_each_new_slayer_member_reaches_its_shared_operator_through_compilation():
    """The three omitted members are executable choices, not catalogue prose."""
    from mordheim_construction.compiler import compile_fighter
    for skill_id, expected in NEW_MEMBERS.items():
        unit = compile_fighter(FighterBuild(COLLECTION, band_id="dwarf-slayer-cult-web",
            profile_id="giant-slayer", main_weapon_id="weapon.axe", skill_ids=(skill_id,)), ROOT)
        for tag in expected:
            assert tag in unit.global_effects.tags, (skill_id, tag)


@pytest.mark.phase1_kb_contracts
def test_printed_members_outside_the_duel_carry_their_own_disposition():
    """A printed member with no duel consequence is disposed, never dropped."""
    for (band, rule_id), members in DISPOSED_MEMBERS.items():
        rule = next(row for row in _package(band).special_rules if row["id"] == rule_id)
        reasons = " ".join(str(effect.get("reason") or "")
                           for effect in (rule.get("runtime") or {}).get("effects") or ()
                           if effect.get("binding") is None)
        for member in members:
            assert member in reasons, (band, rule_id, member)


@pytest.mark.phase2_construction
def test_born_marksmen_opens_shooting_only_for_the_promoted_axe_hurler():
    pack = _package("dwarf-slayer-cult-web")
    row = _profile_row(pack, "axe-hurlers")
    facts = desktop_call("profileFacts", _build("dwarf-slayer-cult-web", "axe-hurlers"), ROOT,
                         package=pack, profile=row)
    # The unpromoted Henchman never reads the printed grant as its own access.
    assert facts["skill_access"] == []
    assert "shooting" not in [entry["category"] for entry in facts["skill_lists"]]
    promoted = _build("dwarf-slayer-cult-web", "axe-hurlers", ("promotion.hero",))
    facts = desktop_call("profileFacts", promoted, ROOT, package=pack, profile=row)
    assert facts["promotion_skill_access"] == ["shooting"]
    assert "shooting" in facts["skill_access"]
    shooting = [entry for entry in facts["skill_lists"] if entry["category"] == "shooting"]
    assert [entry["rule_id"] for entry in shooting] == ["axe-hurlers--born-marksmen"]
    assert shooting[0]["skills"], "the printed Shooting list is published, not the whole catalogue"
    choices = desktop_call("skillChoices", promoted, ROOT, package=pack, profile=row)
    assert choices["skill.quick-shot"] is True
    assert choices["skill.ferocious-charge"] is False


def _supplied(band, profile, **overrides):
    build = FighterBuild(COLLECTION, band_id=band, profile_id=profile, trait_overrides=overrides)
    return prepare_source_profile(build, *_profile(build, ROOT), ROOT)


@pytest.mark.phase2_construction
def test_the_supplied_human_rememberer_takes_speed_and_never_the_dwarf_column():
    """The printed Skill Table gives the Human line Speed where the Dwarf has Special."""
    build, _, _, package, profile, _ = _supplied("dwarf-slayers-kaz", "rememberer", species="human")
    assert profile["skill_access"] == ["combat", "shooting", "academic", "speed"]
    assert desktop_call("profileSkillLists", build, ROOT, package=package, profile=profile) == []
    assert desktop_call("skillChoices", build, ROOT,
                        package=package, profile=profile)["skill.tough-as-steel"] is False
    dwarf_build, _, _, package, profile, _ = _supplied("dwarf-slayers-kaz", "rememberer")
    assert "special" in profile["skill_access"]
    lists = desktop_call("profileSkillLists", dwarf_build, ROOT, package=package, profile=profile)
    assert [entry["rule_id"] for entry in lists] == [DWARF_TABLE]
