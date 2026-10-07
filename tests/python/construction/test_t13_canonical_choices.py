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
from mordheim_construction.eligibility import desktop_call, call, configuration_context, construction_call
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


def test_profile_without_lists_has_empty_access_through_the_real_transport():
    """H1: a canonical profile with no declared list buys nothing, not anything.

    The shared projection must materialize the empty access (never the legacy
    unfiltered `null`) so `validateConstruction` refuses a sword for
    black-orcs/troll through the real MiniRacer transport.
    """
    pack = next(row for row in load_bands('mordheim', ROOT) if row.band['id'] == 'black-orcs')
    row = next(profile for profile in pack.profiles if profile['id'] == 'troll')
    build = FighterBuild('mordheim', band_id='black-orcs', profile_id='troll', main_weapon_id='weapon.fist')
    facts = desktop_call('profileFacts', build, ROOT, package=pack, profile=row)
    # An explicit list, not the legacy unfiltered `null`: only the printed
    # natural-attack concession, never a purchasable weapon.
    assert facts['equipment_access'] == [{'item_id': 'weapon.vomit-attack'}]
    # The attack has no item record, so its offer is informational for the KB,
    # never a refusal: canonical builds select it as their main weapon.
    assert call('equipmentIssue', {'profile': facts, 'item_id': 'weapon.vomit-attack',
        'item': None})['code'] == 'equipment_unknown_item'
    assert call('equipmentIssue', {'profile': facts, 'item_id': 'weapon.sword',
        'item': {'kind': 'close-combat-weapon', 'mechanic_id': 'weapon.sword', 'tags': []}})['code'] == 'equipment_not_permitted'
    attack = FighterBuild('mordheim', band_id='black-orcs', profile_id='troll', main_weapon_id='weapon.vomit-attack')
    consumed = construction_call('validateConstruction', attack,
        configuration_context(attack, pack, row, possession=('weapon.vomit-attack',),
                              slots={'main_weapon_id': 'weapon.vomit-attack'}), root=ROOT)
    assert 'equipment_not_permitted' not in [issue['code'] for issue in consumed]
    context = configuration_context(build, pack, row, possession=('weapon.sword',), slots={'main_weapon_id': 'weapon.fist'})
    codes = [issue['code'] for issue in construction_call('validateConstruction', build, context, root=ROOT)]
    assert 'equipment_not_permitted' in codes


@pytest.mark.parametrize('collection,band,profile,granted', [
    ('mordheim', 'ostlanders', 'ogre', ['combat', 'strength']),
    ('mordheim', 'pit-fighters', 'ogre-pit-fighter', ['combat', 'strength', 'special']),
    ('trollheim', 'chaos-streets-pit-fighters', 'ogre-pit-fighter', ['combat', 'strength', 'special']),
])
def test_promoted_ogre_grant_reaches_only_the_configured_hero(collection, band, profile, granted):
    """H2: the published promotion grant is projected and gated by promotion.

    The canonical Henchman exposes `promotion_skill_access` but never receives
    the tables; the `promotion.hero` build does, and still refuses an academic
    skill. All decisions come from the shared bundle through MiniRacer.
    """
    pack = next(row for row in load_bands(collection, ROOT) if row.band['id'] == band)
    row = next(entry for entry in pack.profiles if entry['id'] == profile)
    plain = FighterBuild('mordheim', collection=collection, band_id=band, profile_id=profile)
    facts = desktop_call('profileFacts', plain, ROOT, package=pack, profile=row)
    assert facts['promotion_skill_access'] == granted
    assert facts['skill_access'] == []
    rookie = desktop_call('skillChoices', plain, ROOT, package=pack, profile=row)
    assert rookie['skill.mighty-blow'] is False
    promoted = desktop_call('skillChoices', FighterBuild('mordheim', collection=collection,
        band_id=band, profile_id=profile, variant_ids=('promotion.hero',)), ROOT,
        package=pack, profile=row)
    assert promoted['skill.mighty-blow'] is True
    assert promoted['skill.arcane-lore'] is False


# --- T13 construction restrictions: the delivered contracts, through the adapter ----
# Every expectation below is read from the canonical band package by the real
# CombatCatalogue transport (bandFacts -> profileFacts -> constructionCall), so it
# exercises the same path the editor uses, not a hand-built profile token.


def test_sigmarite_hammer_copy_bound_keeps_the_bearer_exception_and_possession_split():
    c = catalogue()
    sister = choice('sisters-of-sigmar', 'sigmarite-sister')
    matriarch = choice('sisters-of-sigmar', 'sigmarite-matriarch')
    one = {'main_weapon_id': 'weapon.fist'}
    assert c.validate_configuration(sister, possession=('sigmarite_hammer',), slots=one) == ()
    assert [(i['code'], i['rule_id']) for i in
            c.validate_configuration(sister, possession=('sigmarite_hammer',) * 2, slots=one)] \
        == [('equipment_limit_exceeded', 'band--sigmarite-hammer-pair')]
    # One hammer wielded and owned is one copy; only the owned list counts twice.
    assert c.validate_configuration(sister, possession=('sigmarite_hammer',),
        slots={'main_weapon_id': 'sigmarite_hammer'}) == ()
    assert c.validate_configuration(matriarch, possession=('sigmarite_hammer',) * 2, slots=one) == ()
    assert [i['code'] for i in
            c.validate_configuration(matriarch, possession=('sigmarite_hammer',) * 3, slots=one)] \
        == ['equipment_limit_exceeded']
    # A direct selection meets the same verdict as the final configuration.
    assert c.equipment_decisions(sister, ('sigmarite_hammer',), slot='main',
        main_weapon_id='weapon.fist')['sigmarite_hammer'] is None
    assert 'allows 1 for this bearer' in c.equipment_decisions(sister, ('sigmarite_hammer',),
        slot='main', main_weapon_id='sigmarite_hammer')['sigmarite_hammer']
    assert c.equipment_decisions(matriarch, ('sigmarite_hammer',), slot='main',
        main_weapon_id='sigmarite_hammer')['sigmarite_hammer'] is None


def test_knights_errant_must_acquire_a_hand_to_hand_weapon_and_a_dagger_never_satisfies_it():
    c = catalogue()
    slots = {'main_weapon_id': 'weapon.fist'}
    knight = choice('bretonnian-knights-errant-mou', 'knights-errant')
    assert [(i['code'], i['rule_id']) for i in c.validate_configuration(knight, possession=(), slots=slots)] \
        == [('equipment_required_missing', 'knights-errant--hand-to-hand-weapon')]
    assert c.validate_configuration(knight, possession=('sword',), slots=slots) == ()
    assert [i['code'] for i in c.validate_configuration(knight, possession=('dagger',), slots=slots)] \
        == ['equipment_not_permitted', 'equipment_required_missing']
    # The obligation is to buy the weapon, not to fight with it: the active slot stays free.
    assert c.validate_configuration(knight, possession=('mace',), slots=slots) == ()
    # A peer without the printed clause keeps no obligation.
    assert c.validate_configuration(choice('bretonnian-knights-errant-mou', 'squires'), possession=(), slots=slots) == ()


def test_lizardman_poison_application_is_qualified_by_species_and_weapon_kind():
    c = catalogue()

    def codes(profile, weapon, poison):
        return [(i['code'], i.get('rule_id')) for i in c.validate_configuration(profile, possession=(),
            slots={'main_weapon_id': weapon, 'main_poison_id': poison})]

    skink = choice('lizardmen-lus', 'skink-priest')
    saurus = choice('lizardmen-lus', 'saurus-totem-warriors')
    braves = choice('lizardmen-lus', 'skink-braves')
    assert codes(skink, 'short_bow', 'poison.black-venom') == []            # Skink missile
    assert codes(skink, 'weapon.sword', 'poison.black-venom') == [('equipment_forbidden', 'band--skink-poison-application')]
    assert codes(choice('lizardmen-lus', 'skink-great-crests'), 'weapon.sword', 'poison.black-lotus') == [
        ('equipment_forbidden', 'band--skink-poison-application')]
    assert codes(saurus, 'weapon.sword', 'poison.black-venom') == []        # Saurus melee
    assert codes(braves, 'short_bow', 'poison.reptile-venom') == []         # Skink Henchman missile
    assert codes(braves, 'weapon.sword', 'poison.reptile-venom')[0] == (
        'equipment_forbidden', 'band--skink-henchman-poison-application')


def test_house_selection_reaches_the_shared_decision_through_the_catalogue_adapter():
    c = catalogue()
    commander = choice('house-guard-sc', 'commander')
    slots = {'main_weapon_id': 'weapon.fist'}
    assert [i['code'] for i in c.validate_configuration(commander, possession=('rapier',), slots=slots)] \
        == ['equipment_not_permitted']
    assert c.validate_configuration(commander, possession=('rapier',), slots=slots,
        variant_ids=('house.fierezza',)) == ()
    assert [i['code'] for i in c.validate_configuration(commander, possession=('rapier',), slots=slots,
        variant_ids=('house.halcon',))] == ['equipment_not_permitted']
    assert c.equipment_decisions(commander, ('weapon.rapier',), variant_ids=('house.fierezza',))['weapon.rapier'] is None
    assert c.equipment_decisions(commander, ('weapon.rapier',))['weapon.rapier']


def test_sniper_specialisation_transport_keeps_the_silent_master_exclusion():
    c = catalogue()
    poisoner = choice('silent-brotherhood-sc', 'poisoner')
    master = choice('silent-brotherhood-sc', 'silent-master')
    slots = {'main_weapon_id': 'weapon.fist'}
    assert [i['code'] for i in c.validate_configuration(poisoner, possession=('crossbow',), slots=slots)] \
        == ['equipment_not_permitted']
    assert c.validate_configuration(poisoner, possession=('crossbow',), slots=slots,
        variant_ids=('modus-operandi.sniper',)) == ()
    assert [i['code'] for i in c.validate_configuration(poisoner, possession=('crossbow',), slots=slots,
        variant_ids=('modus-operandi.executor',))] == ['equipment_not_permitted']
    # 'not available to the Silent Master' is a conjunctive denial, not a new gate.
    assert [i['code'] for i in c.validate_configuration(master, possession=('crossbow',), slots=slots,
        variant_ids=('modus-operandi.sniper',))] == ['equipment_not_permitted']
    assert c.equipment_decisions(poisoner, ('crossbow',),
        variant_ids=('modus-operandi.sniper',))['crossbow'] is None
    assert c.equipment_decisions(master, ('crossbow',),
        variant_ids=('modus-operandi.sniper',))['crossbow']


def test_sons_of_hashut_blunderbuss_is_a_compulsory_named_item():
    c = catalogue()
    row = choice('sons-of-hashut', 'blunderbuss-chaos-dwarfs')
    slots = {'main_weapon_id': 'weapon.fist'}
    assert [(i['code'], i['rule_id']) for i in c.validate_configuration(row, possession=(), slots=slots)] \
        == [('equipment_required_missing', 'blunderbuss-chaos-dwarfs--equipment-restrictions')]
    assert c.validate_configuration(row, possession=('chaos_dwarf_blunderbuss',), slots=slots) == ()


def test_runtime_distinguishes_planned_and_active_bindings():
    from mordheim_knowledge.loader import runtime_bindings
    rule = {'id': 'test', 'runtime': {'scope': 'LATER', 'implemented': 'NO', 'grant': 'profile',
        'effects': [{'id': 'skill.frenzy', 'scope': 'LATER', 'binding': {'kind': 'mechanic', 'id': 'skill.frenzy'}}]}}
    validate_rule_runtime(rule)
    assert runtime_bindings(rule) == ()
    assert len(runtime_bindings(rule, include_pending=True)) == 1
    active = deepcopy(rule); active['runtime']['implemented'] = 'YES'
    with pytest.raises(ValueError, match='active binding requires scope YES'):
        runtime_bindings(active)
    active['runtime']['scope'] = 'YES'; active['runtime']['effects'][0]['scope'] = 'YES'
    assert len(runtime_bindings(active)) == 1
    active['runtime']['effects'][0].update(binding=None, reason='Not implemented yet.')
    with pytest.raises(ValueError, match='implemented YES effect has no binding'):
        validate_rule_runtime(active)
    active['runtime']['implemented'] = 'NO'; validate_rule_runtime(active)
    assert runtime_bindings(active) == ()
    for collection in ('mordheim', 'trollheim'):
        for pack in load_bands(collection):
            for row in pack.special_rules:
                validate_rule_runtime(row)

def test_loremaster_tower_of_hoeth_whitelist_bounds_use_not_possession():
    """Tower of Hoeth: 'may only use a sword, dagger or Mage Staff in battle'."""
    c = catalogue()
    row = choice('high-elves-lus', 'loremaster')

    def codes(weapon, possession=()):
        return [(i['code'], i.get('rule_id')) for i in c.validate_configuration(row,
            possession=possession, slots={'main_weapon_id': weapon})]

    # The printed set is admitted, in the spelling the catalogue publishes.
    assert codes('weapon.sword') == []
    assert codes('weapon.dagger') == []
    assert codes('mage_staff_of_hoeth') == []
    # Anything outside the printed set may not be *used* ...
    assert codes('weapon.axe') == [('equipment_forbidden', 'loremaster--tower-of-hoeth')]
    assert codes('weapon.double-handed-weapon') == [('equipment_forbidden', 'loremaster--tower-of-hoeth')]
    # ... while merely owning it stays legal: the clause bounds use, not possession.
    assert codes('weapon.sword', possession=('axe', 'great_weapon', 'weapon.spear')) == []
    decisions = c.equipment_decisions(row, ('weapon.sword', 'weapon.axe', 'weapon.spear'),
        slot='main', main_weapon_id='weapon.sword')
    assert decisions['weapon.sword'] is None
    assert 'admits only' in (decisions['weapon.axe'] or '')
    assert 'admits only' in (decisions['weapon.spear'] or '')
    # The clause belongs to the Loremaster alone.
    warden = choice('high-elves-lus', 'sword-wardens')
    assert [i['code'] for i in c.validate_configuration(warden, possession=('axe',),
        slots={'main_weapon_id': 'weapon.axe'})] == []


def test_moot_elder_reuses_the_halfling_list_and_adds_the_pistol_concession():
    """'May buy equipment from the Halfling Equipment List and ... a pistol'."""
    c = catalogue()
    pack = next(p for p in load_bands('mordheim') if p.band['id'] == 'mootlanders')
    elder_row = next(r for r in pack.profiles if r['id'] == 'moot-elder')
    lists = {row['id']: row for row in pack.equipment_lists}
    # The referenced list is the band's own list, declared by reference, and its
    # published name is the 'Halfling Equipment List' of the clause.
    assert elder_row['equipment_lists'] == ['mootlander-equipment-list']
    assert lists['mootlander-equipment-list']['name'] == 'Halfling Equipment List'
    # The concession is the additional item, never a copy of the list rows, and
    # the printed 15 gc price stays creation data the shared decision never sees.
    printed = {item['item_id'] for row in pack.equipment_lists for item in row['items']}
    assert 'pistol' not in printed
    assert 'dagger' in printed and 'sling' in printed
    elder = choice('mootlanders', 'moot-elder')
    slots = {'main_weapon_id': 'weapon.fist'}
    assert c.equipment_decisions(elder, ('weapon.pistol',), slot='main',
        main_weapon_id='weapon.fist')['weapon.pistol'] is None
    # The list restrictions stay in force: an item on no list of the profile is refused.
    assert c.equipment_decisions(elder, ('axe',), slot='main', main_weapon_id='weapon.fist')['axe']
    # The concession reaches no other profile of the band.
    chef = choice('mootlanders', 'master-chef')
    assert c.equipment_decisions(chef, ('weapon.pistol',), slot='main',
        main_weapon_id='weapon.fist')['weapon.pistol']
    assert c.validate_configuration(elder, possession=('dagger', 'sling'), slots=slots) == ()


def test_dame_of_the_mare_ancient_armour_is_intrinsic_and_not_substitutable():
    """'may never be removed, traded or stolen ... provides a 5+ save'."""
    c = catalogue()
    row = choice('order-of-the-mare-web', 'dame-of-the-mare')
    slots = {'main_weapon_id': 'weapon.sword'}
    # The armour is part of the printed kit, so its presence is never refused ...
    assert c.validate_configuration(row, possession=('dame_ancient_armour', 'sword'), slots=slots) == ()
    # ... and no armour line replaces it: she has no armour access at all.
    for armour in ('armour.light-armour', 'armour.heavy-armour'):
        assert [i['code'] for i in c.validate_configuration(row, possession=(armour,), slots=slots)] \
            == ['equipment_not_permitted']
    # The constant save reaches the warrior once: the profile's own rule carries
    # it, and no second armour save is added (`armour_target` keeps the better of
    # `armour_save` and `natural_armour_save`).
    fighter = compile_fighter(FighterBuild('mordheim', band_id='order-of-the-mare-web',
        profile_id='dame-of-the-mare', main_weapon_id='weapon.sword'))
    assert fighter.natural_armour_save == 5
    assert fighter.natural_armour_unmodified is True
    assert fighter.global_effects.natural_armour_negated_by_magic is True
    assert fighter.armour_save == 7
    # The clause is the Dame's; the Companion Filly is a different printed line.
    assert compile_fighter(FighterBuild('mordheim', band_id='order-of-the-mare-web',
        profile_id='companion-filly')).natural_armour_save == 7


def test_shoota_team_bounds_missile_weapons_by_units_and_exempts_pebbles():
    """'May only purchase ONE non-pebble or non-slingshot missile weapon'."""
    c = catalogue()
    team = choice('snotlings-web', 'shoota-teams')
    slots = {'main_weapon_id': 'weapon.fist'}

    def codes(possession):
        return [(i['code'], i.get('rule_id')) for i in
                c.validate_configuration(team, possession=possession, slots=slots)]

    assert codes(('crossbow',)) == []
    # The printed exemptions are left out of the count instead of refused.
    assert codes(('small_pebble', 'slingshot', 'small_pebble')) == []
    assert codes(('crossbow', 'blunderbuss', 'small_pebble')) == [
        ('equipment_limit_exceeded', 'shoota-teams--one-missile-weapon')]
    # Units, not distinct ids: two copies of one weapon are two.
    assert codes(('crossbow', 'crossbow')) == [
        ('equipment_limit_exceeded', 'shoota-teams--one-missile-weapon')]
    # The bound is the team's possession clause, not an active-slot rule: the
    # wielded weapon is the same item the kit already carries.
    assert c.validate_configuration(team, possession=('crossbow', 'blunderbuss'),
        slots={'main_weapon_id': 'crossbow'})[0]['code'] == 'equipment_limit_exceeded'


def test_plague_monk_robes_protect_once_for_both_named_profiles():
    """'robes offer protection equal to soft leather and count as light armour'."""
    for profile_id in ('plague-priest', 'plague-champion'):
        plain = compile_fighter(FighterBuild('mordheim', band_id='skaven-of-clan-pestilens-mou',
            profile_id=profile_id, main_weapon_id='weapon.sword'))
        assert plain.natural_armour_save == 6   # soft leather
        assert plain.armour_save == 7           # no second, worn save
        worn = compile_fighter(FighterBuild('mordheim', band_id='skaven-of-clan-pestilens-mou',
            profile_id=profile_id, main_weapon_id='weapon.sword', armour_id='armour.light-armour'))
        # Combined with the scattered pieces the robes *are* light armour: one 6+
        # save, never two (the engine keeps the better of the two).
        assert (worn.armour_save, worn.natural_armour_save) == (6, 6)
    # A profile the clause does not name keeps no robe save.
    assert compile_fighter(FighterBuild('mordheim', band_id='skaven-of-clan-pestilens-mou',
        profile_id='monk-initiate', main_weapon_id='weapon.sword')).natural_armour_save == 7


def test_ghutani_flagellants_townsmen_note_is_a_list_reference():
    """'Restricted to Townsmen.' names the bearer of the list, not a prohibition."""
    c = catalogue()
    pack = next(p for p in load_bands('mordheim') if p.band['id'] == 'ghutani-rel')
    assert next(r for r in pack.profiles if r['id'] == 'flagellants')['equipment_lists'] \
        == ['townsmen-equipment-list']
    # The band rule prints the access in prose: the Flagellants choose equipment
    # from the Townsmen list, so the note is already realised by the declared list.
    rule = next(r for r in pack.special_rules if r['id'] == 'band--ghutani-flagellants')
    assert 'Townsmen equipment list' in rule['effect']
    bear = choice('ghutani-rel', 'flagellants')
    slots = {'main_weapon_id': 'weapon.fist'}
    # The real access decides both ways, and no invented prohibition travels with it.
    assert c.validate_configuration(bear, possession=('sword', 'sling'), slots=slots) == ()
    assert [i['code'] for i in c.validate_configuration(bear, possession=('bow',), slots=slots)] \
        == ['equipment_not_permitted']
    townsmen = choice('ghutani-rel', 'townsmen')
    assert c.validate_configuration(townsmen, possession=('sword',), slots=slots) == ()


# ---------------------------------------------------------------------------
# Supplied canonical conditions (KB-CONDITIONS-RUNTIME / FACT-CONDITION-MAPPING)
# ---------------------------------------------------------------------------

def _condition_build(condition_ids, **traits):
    return FighterBuild('mordheim', Characteristics(3, 3, 3, 1, 3, 1),
                        condition_ids=tuple(condition_ids), trait_overrides=traits)


@pytest.mark.parametrize('condition_id,tag,flag', [
    ('campaign.condition.causes-fear', 'mechanic.causes-fear', None),
    ('campaign.condition.immune-to-fear', 'mechanic.fear-immunity', None),
    ('campaign.condition.stupidity', 'mechanic.stupidity', None),
    ('condition.immune-to-psychology', 'mechanic.psychology-immunity', None),
    ('condition.hatred', 'skill.hatred', None),
    ('campaign.condition.frenzy', None, 'frenzy'),
])
def test_supplied_condition_id_resolves_once_to_its_declared_operator(condition_id, tag, flag):
    fighter = compile_fighter(_condition_build((condition_id,)))
    assert tag is None or fighter.global_effects.tags.count(tag) == 1
    assert flag is None or getattr(fighter.global_effects, flag) is True
    # The same condition supplied twice, or reached through a second route,
    # never applies its effect twice.
    second_route = {'causes_fear': True} if tag == 'mechanic.causes-fear' else {
        'frenzy': True} if flag == 'frenzy' else {}
    double = compile_fighter(_condition_build((condition_id, condition_id), **second_route))
    assert tag is None or double.global_effects.tags.count(tag) == 1
    assert flag is None or getattr(double.global_effects, flag) is True


def test_cold_blooded_condition_keeps_the_two_printed_origins():
    """Lizardmen and Fimir print different Cold-Blooded scopes; no universal variant."""
    def compiled(origin=None):
        traits = {} if origin is None else {'cold_blooded_origin': origin}
        return compile_fighter(_condition_build(('condition.cold-blooded',), **traits))
    lizardmen, fimir = compiled('lizardmen'), compiled('fimir')
    assert lizardmen.global_effects.tags.count('mechanic.cold-blooded-psychology') == 1
    assert 'mechanic.cold-blooded-leadership' not in lizardmen.global_effects.tags
    assert fimir.global_effects.tags.count('mechanic.cold-blooded-leadership') == 1
    assert 'mechanic.cold-blooded-psychology' not in fimir.global_effects.tags
    for invalid in (None, 'skink'):
        with pytest.raises(ValueError, match='cold_blooded_origin'):
            compiled(invalid)


def test_rules_definitions_and_unbound_condition_ids_are_refused():
    """condition.fear is the printed rule; the catalogue declares its disposition."""
    with pytest.raises(ValueError, match='outside the executable duel runtime'):
        compile_fighter(_condition_build(('condition.fear',)))
    with pytest.raises(ValueError, match='outside the executable duel runtime'):
        compile_fighter(_condition_build(('condition.terror',)))
    with pytest.raises(ValueError, match='unknown canonical condition'):
        compile_fighter(_condition_build(('condition.not-a-condition',)))


def test_catalogue_declares_the_closed_condition_set_and_its_bindings():
    from mordheim_knowledge.loader import load_conditions, runtime_bindings
    rows = {row['id']: row for row in load_conditions('mordheim', ROOT)}
    bound = {
        'campaign.condition.causes-fear', 'campaign.condition.frenzy',
        'campaign.condition.immune-to-fear', 'campaign.condition.stupidity',
        'condition.cold-blooded', 'condition.hatred', 'condition.immune-to-psychology',
    }
    assert bound <= set(rows)
    for condition_id in bound:
        runtime = rows[condition_id]['runtime']
        assert runtime['implemented'] == 'YES' and runtime_bindings(rows[condition_id])
        assert {e['scope'] for e in runtime['effects'] if e['binding']} == {'YES'}
    fear = rows['condition.fear']['runtime']
    assert fear['implemented'] == 'NO' and fear['grant'] == 'none'
    assert all(e['binding'] is None and e.get('reason') for e in fear['effects'])
    cold = rows['condition.cold-blooded']['runtime']
    assert cold['variant_fact'] == 'cold_blooded_origin'
    assert {e['variant'] for e in cold['effects']} == {'lizardmen', 'fimir'}


def test_condition_validation_rejects_a_malformed_declaration():
    from mordheim_knowledge.loader import load_conditions, validate_rule_runtime
    with pytest.raises(ValueError, match='implemented YES effect has no binding'):
        validate_rule_runtime({'id': 'condition.broken', 'runtime': {
            'scope': 'YES', 'implemented': 'YES', 'grant': 'none',
            'effects': [{'id': 'mechanic.causes-fear', 'scope': 'YES', 'binding': None,
                         'reason': 'not actually implemented'}]}},
            context='condition')
    with pytest.raises(ValueError, match='unknown profile binding'):
        validate_rule_runtime({'id': 'condition.broken', 'runtime': {
            'scope': 'YES', 'implemented': 'YES', 'grant': 'none',
            'effects': [{'id': 'mechanic.causes-fear', 'scope': 'YES', 'binding': {
                'kind': 'profile', 'id': 'profile.not-a-binding'}}]}}, context='condition')
    # The loader reads the caller's root, never a silent global default.
    assert load_conditions('mordheim', ROOT)[0]['id'] == 'campaign.condition.frenzy'
    with pytest.raises(ValueError):
        load_conditions('not-a-ruleset', ROOT)
