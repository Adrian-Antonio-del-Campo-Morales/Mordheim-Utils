"""L05: canonical table membership, configured promotions and complete owned kits."""
from copy import deepcopy
from functools import lru_cache

import pytest

from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.contracts import SPECIAL_RULE_EFFECTS
from mordheim_construction.eligibility import desktop_call, call
from mordheim_construction.selection import available_special_rules, _profile
from mordheim_core.models import Characteristics, DuelContext, FighterBuild
from mordheim_knowledge.loader import knowledge_root, load_bands, validate_rule_runtime

ROOT = knowledge_root()
TABLES = {
    'elf': ('skill.fey', 'skill.chosen-of-the-white-tower', 'skill.fey-quickness'),
    'barbarian': ('skill.hard-to-kill', 'skill.ferocious-charge', 'skill.instinctive-warrior'),
    'imperial-noble': ('skill.trading-flair', 'skill.taunt'),
    'dwarf': ('skill.magic-resistant', 'skill.ferocious-charge', 'skill.monster-slayer', 'skill.berserker'),
}
SUPPORTED = {'skill.hard-to-kill', 'skill.ferocious-charge', 'skill.monster-slayer', 'skill.berserker'}


@lru_cache
def catalogue():
    return CombatCatalogue()


def choice(band, profile, collection='mordheim'):
    return next(row for row in catalogue().profiles(collection, band) if row.profile_id == profile)


@pytest.mark.parametrize('profile,skill', [(p, s) for p, skills in TABLES.items() for s in skills])
def test_named_table_member_is_offered_and_support_is_separate(profile, skill):
    options = {row.id: row for row in catalogue().skills(choice('adventurers-kaz', profile))}
    assert skill in options and options[skill].summary
    assert options[skill].runtime_available == (skill in SUPPORTED)
    assert catalogue().skill_rule_ids((skill,)) == ((skill,), ())
    build = FighterBuild('mordheim', band_id='adventurers-kaz', profile_id=profile, skill_ids=(skill,))
    if skill not in SUPPORTED:
        assert options[skill].unavailable_reason == 'No executable duel mechanic.'
        with pytest.raises(ValueError, match='named skills have no executable duel mechanic'):
            compile_fighter(build)
    else:
        fighter = compile_fighter(build)
        assert fighter.global_effects.tags.count(skill) == 1
        if skill == 'skill.hard-to-kill':
            assert fighter.global_effects.out_of_action_threshold == 6


@pytest.mark.parametrize('profile', TABLES)
def test_named_tables_do_not_leak_to_other_profiles(profile):
    build = FighterBuild('mordheim', band_id='adventurers-kaz', profile_id=profile)
    _, _, package, row, _ = _profile(build, ROOT)
    legal = desktop_call('skillChoices', build, package=package, profile=row)
    assert {s for skills in TABLES.values() for s in skills if legal[s]} == set(TABLES[profile])
    foreign = next(s for skills in TABLES.values() for s in skills if s in SUPPORTED and s not in TABLES[profile])
    with pytest.raises(ValueError, match='skills are not available'):
        compile_fighter(FighterBuild('mordheim', band_id='adventurers-kaz', profile_id=profile, skill_ids=(foreign,)))


@pytest.mark.parametrize('profile', ('halfling-scouts', 'halfling-warriors'))
def test_promoted_halfling_selects_and_executes_shifty(profile):
    build = FighterBuild('mordheim', band_id='halflings-mic', profile_id=profile,
        main_weapon_id='weapon.mace', variant_ids=('promotion.hero',), special_rule_ids=('halfling-elder--shifty',))
    assert 'halfling-elder--shifty' in available_special_rules(build, ROOT)
    assert any(row.rule_id == 'halfling-elder--shifty' and row.runtime_available for row in
               catalogue().skills(choice('halflings-mic', profile), variant_ids=build.variant_ids))
    fighter = compile_fighter(build)
    assert fighter.global_effects.tags.count('skill.shifty') == 1
    other = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 1, 3, 1), main_weapon_id='weapon.mace'))
    dice = StrictDice([{'key': f'round.0.{side}.attack.0.hit', 'value': 1}
                       for side in ('first.shifty', 'second', 'first')])
    decisions = StrictDecisions([])
    state = initialize_duel(fighter, other, dice,
        context=DuelContext(charging=('second',), active_participant='second'))
    assert len(resolve_round(fighter, other, state, dice, decisions).attacks) == 3
    dice.finish(); decisions.finish()


@pytest.mark.parametrize('profile', ('piggies', 'village-ogre'))
def test_configured_hero_type_does_not_make_a_non_halfling_a_shifty_recipient(profile):
    build = FighterBuild('mordheim', band_id='halflings-mic', profile_id=profile, variant_ids=('promotion.hero',))
    assert 'halfling-elder--shifty' not in available_special_rules(build, ROOT)


@pytest.mark.parametrize('off', ('weapon.mace', 'weapon.dagger'))
def test_runt_active_limit_and_promoted_exception(off):
    kwargs = dict(band_id='snotlings-web', profile_id='runts', main_weapon_id='weapon.mace', off_hand_id=off)
    with pytest.raises(ValueError, match='at most 1 one-handed weapon at a time'):
        compile_fighter(FighterBuild('mordheim', **kwargs))
    assert compile_fighter(FighterBuild('mordheim', **kwargs, variant_ids=('promotion.hero',))).off_hand_attacks


def test_runt_ownership_is_not_active_weapon_count_and_armour_guard_survives():
    ch = choice('snotlings-web', 'runts')
    assert catalogue().validate_configuration(ch, possession=('club', 'dagger'), slots={'main_weapon_id': 'weapon.mace'}) == ()
    dual = catalogue().validate_configuration(ch, possession=('club', 'dagger'),
        slots={'main_weapon_id': 'weapon.mace', 'off_hand_id': 'weapon.dagger'})
    assert dual[0]['code'] == 'equipment_limit_exceeded' and dual[0]['rule_id'] == 'runts--teeny-hands'
    assert catalogue().equipment_decisions(ch, ('weapon.dagger',), slot='off', main_weapon_id='weapon.mace')['weapon.dagger']
    assert catalogue().validate_configuration(ch, possession=('club', 'dagger'),
        slots={'main_weapon_id': 'weapon.mace', 'off_hand_id': 'weapon.dagger'}, variant_ids=('promotion.hero',)) == ()
    with pytest.raises(ValueError, match='armour is forbidden'):
        compile_fighter(FighterBuild('mordheim', band_id='snotlings-web', profile_id='runts', off_hand_id='defence.shield'))
    assert compile_fighter(FighterBuild('mordheim', band_id='snotlings-web', profile_id='runts',
        off_hand_id='defence.shield', variant_ids=('promotion.hero',))).off_hand is not None


def test_outlaw_complete_kit_runs_the_real_catalogue_transport():
    c = catalogue(); ch = choice('outlaws-of-stirwood-forest-redux-fbg', 'bandit-leader')
    slots = {'main_weapon_id': 'weapon.fist'}
    assert [i['code'] for i in c.validate_configuration(ch, possession=(), slots=slots)] == ['equipment_required_missing']
    assert c.validate_configuration(ch, possession=('bow',), slots=slots) == ()
    assert 'equipment_limit_exceeded' in [i['code'] for i in c.validate_configuration(ch, possession=('bow', 'short_bow'), slots=slots)]
    assert 'equipment_not_permitted' in [i['code'] for i in c.validate_configuration(ch, possession=('crossbow',), slots=slots)]
    # The access refusal must not conceal a missing token consumer if access widens.
    pack, row, build = c._selection_context(ch)
    facts = c._profile_facts(pack, row, build)
    assert call('equipmentIssue', {'profile': {**facts, 'equipment_access': None}, 'item_id': 'crossbow',
        'item': {'kind': 'ranged-weapon', 'mechanic_id': None, 'tags': ['crossbow']}})['code'] == 'equipment_forbidden'
    assert c.validate_configuration(choice('outlaws-of-stirwood-forest-redux-fbg', 'cleric'), possession=(), slots=slots) == ()


@pytest.mark.parametrize('owned', [(), ('bow',), ('bow', 'short_bow')])
def test_cleric_bow_exemption_preserves_one_missile_limit(owned):
    ch = choice('outlaws-of-stirwood-forest-redux-fbg', 'cleric')
    codes = [i['code'] for i in catalogue().validate_configuration(ch, possession=owned,
        slots={'main_weapon_id': 'weapon.fist'})]
    assert codes == (['equipment_limit_exceeded'] if len(owned) > 1 else [])
    build = FighterBuild('mordheim', band_id=ch.band_id, profile_id=ch.profile_id,
        main_weapon_id='weapon.fist', owned_item_ids=owned)
    if len(owned) > 1:
        with pytest.raises(ValueError, match='carries 2 missile weapons'):
            compile_fighter(build)
    else:
        assert compile_fighter(build).missile_weapon_limit == 1


@pytest.mark.parametrize('owned,allowed,reason', [
    (None, True, ''), ((), False, 'includes no "bow"'), (('bow',), True, ''),
    (('bow', 'short_bow'), False, 'missile weapons'), (('crossbow',), False, 'not on any equipment list'),
])
def test_compiler_checks_a_supplied_owned_kit_without_folding_holstered_items(owned, allowed, reason):
    build = FighterBuild('mordheim', band_id='outlaws-of-stirwood-forest-redux-fbg',
        profile_id='bandit-leader', main_weapon_id='weapon.fist', owned_item_ids=owned)
    if allowed:
        compiled = compile_fighter(build)
        control = compile_fighter(FighterBuild('mordheim', band_id=build.band_id,
            profile_id=build.profile_id, main_weapon_id=build.main_weapon_id))
        assert compiled == control
    else:
        with pytest.raises(ValueError, match=reason):
            compile_fighter(build)


@pytest.mark.parametrize('band,profile,prefix,other', [
    ('sea-ghosts-mim', 'feast-master', 'band--dance-', 'wayfinder'),
    ('araby-smugglers-sar', 'rais', 'band--skill-pious-fury', 'crew'),
    ('protectorate-of-sigmar-lotd3', 'warrior-priest', 'band--special-skill-utter-determination', 'templar'),
    ('protectorate-of-sigmar-lotd3', 'warrior-priest', 'band--special-skill-rousing-sermon', 'templar'),
])
def test_source_backed_pending_options_have_recipients_without_activation(band, profile, prefix, other):
    build = FighterBuild('mordheim', band_id=band, profile_id=profile)
    ids = [rid for rid in available_special_rules(build, ROOT) if rid.startswith(prefix)]
    assert len(ids) == (4 if prefix == 'band--dance-' else 1)
    assert set(ids).isdisjoint(available_special_rules(FighterBuild('mordheim', band_id=band, profile_id=other), ROOT))
    for rid in ids:
        with pytest.raises(ValueError, match='outside the executable duel runtime'):
            compile_fighter(FighterBuild('mordheim', band_id=band, profile_id=profile, special_rule_ids=(rid,)))


def test_bloodline_is_a_configured_ability_not_a_foreign_profile_skill():
    c = catalogue()
    assert any(row.id == 'vampire--bloodline' and not row.runtime_available for row in c.selectable_rules(choice('strigoi-kaz', 'vampire')))
    assert all(row.id != 'vampire--bloodline' for row in c.selectable_rules(choice('strigoi-kaz', 'charnel-guard')))


def test_iron_sinews_has_one_route_and_keeps_mordheim_source_gate():
    assert 'band--strigoi-power-iron-sinews' not in SPECIAL_RULE_EFFECTS
    base = dict(collection='trollheim', band_id='chaos-streets-undead-bloodlines', profile_id='strigoi-vampire')
    ordinary = compile_fighter(FighterBuild('mordheim', **base))
    granted = compile_fighter(FighterBuild('mordheim', **base, special_rule_ids=('band--strigoi-power-iron-sinews',)))
    assert granted.characteristics.strength == ordinary.characteristics.strength
    assert granted.global_effects.strength_bonus - ordinary.global_effects.strength_bonus == 1
    # Mordheim's printed Iron Sinews is a clause inside Bloodline, not this selectable Trollheim id.
    with pytest.raises(ValueError, match='outside the executable duel runtime'):
        compile_fighter(FighterBuild('mordheim', band_id='strigoi-kaz', profile_id='vampire', special_rule_ids=('vampire--bloodline',)))


def test_later_yes_means_bound_operator_and_not_an_unbound_promise():
    rule = {'id': 'test', 'runtime': {'scope': 'LATER', 'implemented': 'YES', 'grant': 'profile',
        'effects': [{'id': 'skill.frenzy', 'scope': 'LATER', 'binding': {'kind': 'mechanic', 'id': 'skill.frenzy'}}]}}
    validate_rule_runtime(rule)
    bad = deepcopy(rule); bad['runtime']['effects'][0].update(binding=None, reason='Not implemented yet.')
    with pytest.raises(ValueError, match='no executable binding'):
        validate_rule_runtime(bad)
    bad['runtime']['implemented'] = 'NO'; validate_rule_runtime(bad)
    # Every current canonical rule obeys the contract, including retained bound LATER/YES records.
    for collection in ('mordheim', 'trollheim'):
        for pack in load_bands(collection):
            for row in pack.special_rules:
                validate_rule_runtime(row)
