"""L06 canonical items: source-derived effects through the real modular consumer."""
from functools import lru_cache

import pytest

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.phases import Condition
from mordheim_combat.kernel import require_optimized_support
from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild
from mordheim_core.context import DuelContext


def fighter(band, profile, weapon, **options):
    return compile_fighter(FighterBuild('mordheim', band_id=band, profile_id=profile,
        main_weapon_id=weapon, **options))


def target(*, wounds=1, **options):
    return compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, wounds, 3, 1),
        main_weapon_id='weapon.mace', **options))


def state(unit):
    dice = StrictDice([])
    result = initialize_fighter(unit, dice, 'init')
    dice.finish()
    return result


def attack(attacker, defender, weapon, tape, **context):
    dice = StrictDice([{'key': key, 'value': value} for key, value in tape])
    result = resolve_reference_attack(attacker, defender, state(attacker), state(defender),
        weapon, dice, key='item', **context)
    dice.finish()
    return result


@pytest.mark.parametrize('band,profile,weapon,count', [
    ('silent-brotherhood-sc', 'silent-master', 'weapon.long-daggers', 3),
    ('low-kings-mim', 'racketeer', 'weapon.knuckledusters', 2),
])
def test_local_pairs_add_one_attack_in_the_real_round(band, profile, weapon, count):
    attacker = fighter(band, profile, weapon)
    defender = target()
    dice = StrictDice([
        *({'key': f'round.0.first.attack.{i}.hit', 'value': 1} for i in range(count)),
        {'key': 'round.0.second.attack.0.hit', 'value': 1},
    ])
    initial = initialize_duel(attacker, defender, dice,
        context=DuelContext(charging=(), active_participant='first'))
    result = resolve_round(attacker, defender, initial, dice)
    dice.finish()
    assert len(result.attacks) == count + 1
    assert attacker.main_weapon.strength_bonus == 0
    assert attacker.main_weapon.initiative_bonus == 0
    assert attacker.main_weapon.hit_modifier == 0


def test_long_daggers_parry_once_without_a_pair_reroll():
    defender = fighter('silent-brotherhood-sc', 'poisoner', 'weapon.long-daggers')
    for parry, success in ((5, True), (4, False)):
        result = attack(target(), defender, target().main_weapon,
            [('item.hit', 4), ('item.parry', parry)] + ([] if success else [('item.wound', 1)]))
        assert result.parried is success


@pytest.mark.parametrize('band,profile,weapon', [
    ('silent-brotherhood-sc', 'poisoner', 'weapon.long-daggers'),
    ('low-kings-mim', 'racketeer', 'weapon.knuckledusters'),
])
def test_local_pairs_preserve_normal_strength_armour_and_injury(band, profile, weapon):
    attacker = fighter(band, profile, weapon)
    defender = target(armour_id='armour.light-armour')
    missed = attack(attacker, defender, attacker.main_weapon,
        [('item.hit', 4), ('item.wound', 3)])
    assert not missed.wounded
    # S3 wounds on four; light armour needs six (no dagger +1 save),
    # and injury two knocks down (no borrowed knuckles Concussion).
    result = attack(attacker, defender, attacker.main_weapon,
        [('item.hit', 4), ('item.wound', 4), ('item.armour', 5), ('item.injury.0', 2)])
    assert result.defender.condition == Condition.KNOCKED_DOWN


@pytest.mark.parametrize('band,profile,weapon,item', [
    ('silent-brotherhood-sc', 'poisoner', 'weapon.long-daggers', 'long_daggers'),
    ('low-kings-mim', 'racketeer', 'weapon.knuckledusters', 'knuckledusters'),
])
def test_local_pair_access_hands_and_unported_boundary(band, profile, weapon, item):
    c = catalogue()
    choice = next(row for row in c.profiles('mordheim', band) if row.profile_id == profile)
    assert weapon in dict(c.weapons(choice))
    assert not c.validate_configuration(choice, possession=(item,),
        slots={'main_weapon_id': weapon})
    unit = fighter(band, profile, weapon)
    for off in ('weapon.dagger', 'defence.shield'):
        with pytest.raises(ValueError, match='occupies both hands'):
            fighter(band, profile, weapon, off_hand_id=off)
    with pytest.raises(ValueError, match='equipment is not available'):
        fighter('grave-robbers-sylv', 'graver', weapon)
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(unit, target())
    if item == 'long_daggers':
        for henchman in ('brotherhood-agents', 'brotherhood-novices'):
            ordinary = next(row for row in c.profiles('mordheim', band) if row.profile_id == henchman)
            assert weapon not in dict(c.weapons(ordinary))
            with pytest.raises(ValueError, match='equipment is not available'):
                fighter(band, henchman, weapon)
            promoted = fighter(band, henchman, weapon, variant_ids=('promotion.hero',))
            assert promoted.main_weapon.paired


# Printed +1 Strength weapons wound T3 on 3; ordinary S3 weapons need 4.
# A printed concussion clause changes injury face 2 from knocked down to stunned.
@pytest.mark.parametrize('band,profile,weapon,wound,condition', [
    ('grave-robbers-sylv', 'graver', 'weapon.pry-bar', 4, Condition.STUNNED),
    ('nipponese-expedition-web', 'ashigaru', 'weapon.kanabo', 3, Condition.STUNNED),
    ('sorcerous-society-lotd4', 'magus', 'weapon.wizards-staff', 4, Condition.STUNNED),
    ('pirates-of-the-cathayan-sea-sar', 'disgraced-warlord', 'weapon.katana', 3, Condition.KNOCKED_DOWN),
    ('sea-ghosts-mim', 'feast-master', 'weapon.halberd', 3, Condition.KNOCKED_DOWN),
    ('metal-mongers-mim', 'pirate-rats', 'weapon.mace', 4, Condition.STUNNED),
])
def test_canonical_profile_resolves_the_printed_weapon(band, profile, weapon, wound, condition):
    c = catalogue()
    choice = next(row for row in c.profiles('mordheim', band) if row.profile_id == profile)
    assert weapon in dict(c.weapons(choice))
    attacker = fighter(band, profile, weapon)
    result = attack(attacker, target(), attacker.main_weapon,
        [('item.hit', 4), ('item.wound', wound), ('item.injury.0', 2)])
    assert result.defender.condition == condition


@pytest.mark.parametrize('weapon,band,profile', [
    ('weapon.pry-bar', 'grave-robbers-sylv', 'graver'),
    ('weapon.wizards-staff', 'sorcerous-society-lotd4', 'magus'),
    ('weapon.katana', 'pirates-of-the-cathayan-sea-sar', 'disgraced-warlord'),
])
def test_new_parrying_profiles_use_the_existing_defence(weapon, band, profile):
    defender = fighter(band, profile, weapon)
    result = attack(target(), defender, target().main_weapon,
        [('item.hit', 4), ('item.parry', 5)])
    assert result.parried


def test_darksteel_uses_critical_damage_and_wicked_edge_not_wound_rerolls():
    c = catalogue()
    choice = next(row for row in c.profiles('mordheim', 'druchii-mic') if row.profile_id == 'noble')
    assert 'material.dark-elf-blade' in dict(c.materials(choice))
    attacker = fighter('druchii-mic', 'noble', 'weapon.sword', main_material_id='material.dark-elf-blade')
    assert attacker.main_weapon.critical_injury_bonus == 1
    assert not attacker.main_weapon.reroll_wounds
    result = attack(attacker, target(), attacker.main_weapon,
        [('item.hit', 4), ('item.wound', 4), ('item.injury.0', 2)])
    assert result.defender.condition == Condition.STUNNED
    # The printed +1 moves critical face 2 into the armour-ignoring bracket.
    armoured = target(wounds=3, armour_id='armour.light-armour')
    critical = attack(attacker, armoured, attacker.main_weapon,
        [('item.hit', 4), ('item.wound', 6), ('item.critical', 2)])
    assert critical.critical and critical.defender.wounds == 1
    ordinary = fighter('druchii-mic', 'noble', 'weapon.sword')
    saved = attack(ordinary, armoured, ordinary.main_weapon,
        [('item.hit', 4), ('item.wound', 6), ('item.critical', 2), ('item.armour', 6)])
    assert saved.saved and saved.defender.wounds == 3
    with pytest.raises(ValueError, match='equipment is not available'):
        fighter('druchii-mic', 'corsairs', 'weapon.sword', main_material_id='material.dark-elf-blade')


@pytest.mark.parametrize('weapon,band,profile', [
    ('weapon.kanabo', 'nipponese-expedition-web', 'ashigaru'),
    ('weapon.wizards-staff', 'sorcerous-society-lotd4', 'magus'),
    ('weapon.katana', 'pirates-of-the-cathayan-sea-sar', 'disgraced-warlord'),
])
def test_two_handed_profiles_refuse_an_additional_weapon_and_unported_execution(weapon, band, profile):
    unit = fighter(band, profile, weapon)
    with pytest.raises(ValueError, match='occupies both hands'):
        fighter(band, profile, weapon, off_hand_id='weapon.dagger')
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(unit, target())


def test_skull_busta_strength_expires_and_concussion_remains():
    attacker = fighter('savage-orcs-kaz', 'boyz', 'weapon.skull-busta')
    for first_round in (True, False):
        result = attack(attacker, target(), attacker.main_weapon,
            [('item.hit', 4), ('item.wound', 3)] + ([] if not first_round else [('item.injury.0', 2)]),
            first_round=first_round)
        assert result.wounded is first_round
        if first_round:
            assert result.defender.condition == Condition.STUNNED
    later = attack(attacker, target(), attacker.main_weapon,
        [('item.hit', 4), ('item.wound', 4), ('item.injury.0', 2)])
    assert later.defender.condition == Condition.STUNNED


@pytest.mark.parametrize('helmet,face,condition', [
    ('defence.helmet', 5, Condition.STUNNED),
    ('defence.helmet', 6, Condition.KNOCKED_DOWN),
    ('defence.cooking-pot-helmet', 5, Condition.STUNNED),
])
def test_skull_busta_basha_changes_only_the_used_weapon_helmet_save(helmet, face, condition):
    attacker = fighter('savage-orcs-kaz', 'boyz', 'weapon.skull-busta')
    defender = target(defence_ids=(helmet,))
    result = attack(attacker, defender, attacker.main_weapon,
        [('item.hit', 4), ('item.wound', 4), ('item.injury.0', 2), ('item.helmet', face)])
    assert result.defender.condition == condition
    ordinary = fighter('savage-orcs-kaz', 'boyz', 'weapon.mace')
    control = attack(ordinary, defender, ordinary.main_weapon,
        [('item.hit', 4), ('item.wound', 4), ('item.injury.0', 2), ('item.helmet', face)])
    assert control.defender.condition == Condition.KNOCKED_DOWN


def test_skull_busta_preserves_no_pain_and_thick_skull_reactions():
    attacker = fighter('savage-orcs-kaz', 'boyz', 'weapon.skull-busta')
    for defender, extra in (
        (target(skill_ids=('skill.ignore-pain',)), []),
        (target(skill_ids=('skill.thick-skull',), defence_ids=('defence.helmet',)),
            [('item.thick-skull', 2)]),
    ):
        result = attack(attacker, defender, attacker.main_weapon,
            [('item.hit', 4), ('item.wound', 4), ('item.injury.0', 2), *extra])
        assert result.defender.condition == Condition.KNOCKED_DOWN


def test_skull_busta_canonical_access_active_combinations_and_modular_boundary():
    c = catalogue()
    choice = next(row for row in c.profiles('mordheim', 'savage-orcs-kaz') if row.profile_id == 'boyz')
    assert 'weapon.skull-busta' in dict(c.weapons(choice))
    unit = fighter(choice.band_id, choice.profile_id, 'weapon.skull-busta', off_hand_id='defence.shield')
    assert unit.off_hand is not None
    gobbo = next(row for row in c.profiles('mordheim', 'savage-orcs-kaz') if row.profile_id == 'gobbo-boyz')
    assert 'weapon.skull-busta' not in dict(c.weapons(gobbo))
    for profile in ('gobbo-boyz',):
        with pytest.raises(ValueError, match='equipment is not available'):
            fighter('savage-orcs-kaz', profile, 'weapon.skull-busta')
    with pytest.raises(ValueError, match='while mounted'):
        fighter('savage-orcs-kaz', 'boyz', 'weapon.skull-busta', mounted=True)
    for off in ('weapon.mace', 'defence.buckler'):
        with pytest.raises(ValueError, match='only be combined with shields'):
            fighter('savage-orcs-kaz', 'boyz', 'weapon.skull-busta', off_hand_id=off)
        issues = c.validate_configuration(choice, possession=('skull_busta',),
            slots={'main_weapon_id': 'weapon.skull-busta', 'off_hand_id': off})
        assert any('only be combined with shields' in issue['message'] for issue in issues)
    with pytest.raises(ValueError, match='equipment is not available'):
        fighter('grave-robbers-sylv', 'graver', 'weapon.skull-busta')
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(unit, target())


def test_spirit_knife_is_local_to_the_used_hand_and_keeps_its_armour_modifier():
    attacker = fighter('call-of-the-night-haint-mim', 'cairn-wraith', 'weapon.mace',
        off_hand_id='weapon.spirit-knife')
    assert 'trait.spectral-touch' not in attacker.global_effects.tags
    assert attacker.off_hand.target_armour_bonus == 1
    assert attacker.off_hand.strength_bonus == 0
    for weapon, hit, remaining in ((attacker.main_weapon, 6, 2),
                                   (attacker.off_hand, 5, 2), (attacker.off_hand, 6, 1)):
        tape = [('item.hit', hit)]
        if weapon is attacker.off_hand and hit == 6:
            # The dagger's +1 enemy save also applies to the extra wound.
            tape.append(('item.spectral-touch.armour', 1))
        tape.append(('item.wound', 1))
        result = attack(attacker, target(wounds=2), weapon,
            tape)
        assert result.defender.wounds == remaining
        assert result.damage == 2 - remaining
    saved = attack(attacker, target(wounds=2, armour_id='armour.light-armour'), attacker.off_hand,
        [('item.hit', 6), ('item.spectral-touch.armour', 5), ('item.wound', 1)])
    assert saved.defender.wounds == 2
    with pytest.raises(ValueError, match='Spectral Touch'):
        require_optimized_support(attacker, target())


@lru_cache
def catalogue():
    return CombatCatalogue()


def test_source_specific_recipient_exceptions_are_used_by_the_catalogue_and_compiler():
    c = catalogue()
    cases = [('cairn-wraith', (), True), ('tomb-banshee', (), True),
             ('corpse-master', (), False), ('malignant-spirits', (), True),
             ('revenants', (), False), ('revenants', ('promotion.hero',), True)]
    for profile, variants, allowed in cases:
        choice = next(row for row in c.profiles('mordheim', 'call-of-the-night-haint-mim') if row.profile_id == profile)
        issues = c.validate_configuration(choice, possession=('spirit_knife',),
            slots={'main_weapon_id': 'weapon.spirit-knife'}, variant_ids=variants)
        assert bool(issues) is not allowed
        if not variants:
            assert ('weapon.spirit-knife' in dict(c.weapons(choice))) is allowed
        if allowed:
            assert 'trait.spectral-touch' in fighter(choice.band_id, profile, 'weapon.spirit-knife', variant_ids=variants).main_weapon.tags
        else:
            with pytest.raises(ValueError, match='equipment is not available'):
                fighter(choice.band_id, profile, 'weapon.spirit-knife')
    # Heroes-only belongs to the Pirate list; the Nippon list admits Henchmen.
    fighter('nipponese-expedition-web', 'ashigaru', 'weapon.katana')
    fighter('pirates-of-the-cathayan-sea-sar', 'dragon-monk', 'weapon.katana')
    with pytest.raises(ValueError, match='equipment is not available'):
        fighter('pirates-of-the-cathayan-sea-sar', 'deck-hands', 'weapon.katana')
    with pytest.raises(ValueError, match='equipment is not available'):
        fighter('pirates-of-the-cathayan-sea-sar', 'martial-artists', 'weapon.katana')


@pytest.mark.parametrize('injury,condition', [
    (1, Condition.STUNNED), (2, Condition.STUNNED),
    (4, Condition.STUNNED), (5, Condition.OUT),
])
def test_shock_rod_uses_printed_injury_boundaries(injury, condition):
    attacker = fighter('skaven-of-clan-pristekk-sc', 'packmasters', 'weapon.shock-rod')
    result = attack(attacker, target(), attacker.main_weapon,
        [('item.hit', 4), ('item.wound', 3), ('item.injury.0', injury)])
    assert result.defender.condition == condition
    assert not result.critical


def test_shock_rod_keeps_defensive_reactions_and_ordinary_weapon_control():
    attacker = fighter('skaven-of-clan-pristekk-sc', 'packmasters', 'weapon.shock-rod')
    # Free defensive configurations exercise existing reactions, not access claims.
    for defender, extra in ((target(skill_ids=('skill.ignore-pain',)), []),
                            (target(defence_ids=('defence.helmet',)), [('item.helmet', 4)])):
        result = attack(attacker, defender, attacker.main_weapon,
            [('item.hit', 4), ('item.wound', 3), ('item.injury.0', 1), *extra])
        assert result.defender.condition == Condition.KNOCKED_DOWN
    ordinary = fighter('skaven-of-clan-pristekk-sc', 'packmasters', 'weapon.mace')
    result = attack(ordinary, target(), ordinary.main_weapon,
        [('item.hit', 4), ('item.wound', 3), ('item.injury.0', 1)])
    assert result.defender.condition == Condition.KNOCKED_DOWN


def test_shock_rod_strikes_before_faster_enemy_in_real_round():
    attacker = fighter('skaven-of-clan-pristekk-sc', 'packmasters', 'weapon.shock-rod')
    defender = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 1, 8, 1),
        main_weapon_id='weapon.mace'))
    dice = StrictDice([
        {'key': 'round.0.first.attack.0.hit', 'value': 4},
        {'key': 'round.0.first.attack.0.wound', 'value': 3},
        {'key': 'round.0.first.attack.0.injury.0', 'value': 1},
    ])
    initial = initialize_duel(attacker, defender, dice,
        context=DuelContext(charging=(), active_participant='first'))
    result = resolve_round(attacker, defender, initial, dice)
    dice.finish()
    assert result.state.second.condition == Condition.STUNNED
    assert len(result.attacks) == 1


def test_shock_rod_access_two_hands_and_modular_boundary():
    c = catalogue()
    for profile, allowed in (('chieftain', True), ('packmasters', True),
                             ('sorcerer', False), ('underlings', False), ('clanrats', False)):
        choice = next(row for row in c.profiles('mordheim', 'skaven-of-clan-pristekk-sc')
            if row.profile_id == profile)
        assert ('weapon.shock-rod' in dict(c.weapons(choice))) is allowed
        if not allowed:
            with pytest.raises(ValueError, match='equipment is not available'):
                fighter(choice.band_id, profile, 'weapon.shock-rod')
    unit = fighter('skaven-of-clan-pristekk-sc', 'packmasters', 'weapon.shock-rod')
    assert unit.main_weapon.strength_bonus == 0
    with pytest.raises(ValueError, match='occupies both hands'):
        fighter('skaven-of-clan-pristekk-sc', 'packmasters', 'weapon.shock-rod', off_hand_id='weapon.dagger')
    with pytest.raises(ValueError, match='equipment is not available'):
        fighter('grave-robbers-sylv', 'graver', 'weapon.shock-rod')
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(unit, target())
