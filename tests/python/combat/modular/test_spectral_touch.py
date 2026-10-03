"""Q019 human-accepted expectations on the real modular pipeline.

Synthetic composition fixtures inject the trait; L03 also proves its canonical grant.
"""
from dataclasses import replace

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.aftermath import _react_to_wound
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, EffectSet, FighterBuild


def fighter(spectral=False, wounds=4, strength=3, **options):
    result = compile_fighter(FighterBuild('mordheim',
        Characteristics(3, strength, 3, wounds, 3, 1),
        main_weapon_id=options.pop('main_weapon_id', 'weapon.axe'), **options))
    if spectral:
        result = replace(result, global_effects=replace(result.global_effects,
            tags=(*result.global_effects.tags, 'trait.spectral-touch')))
    return result


def roll(key, value):
    return {'key': key, 'value': value}


def state(unit):
    dice = StrictDice([])
    result = initialize_fighter(unit, dice, 'init')
    dice.finish()
    return result


def attack(a, b, rolls, *, a_state=None, b_state=None, react=True, **options):
    dice, choices = StrictDice(rolls), StrictDecisions([])
    result = resolve_reference_attack(a, b, a_state or state(a), b_state or state(b),
        a.main_weapon, dice, key='a', decisions=choices, **options)
    if react:
        result = _react_to_wound(a, b, result, dice, 'a')
    dice.finish()
    choices.finish()
    return result


@pytest.mark.parametrize('spectral,face,damage', [(True, 6, 1), (True, 5, 0),
                                                (False, 6, 0)])
def test_trigger_and_failed_ordinary_wound(spectral, face, damage):
    result = attack(fighter(spectral), fighter(), [roll('a.hit', face), roll('a.wound', 1)])
    assert result.damage == damage and result.defender.wounds == 4 - damage
    assert result.wounded == bool(damage)


def test_hit_modifier_does_not_turn_five_into_natural_six():
    a = fighter(True)
    a = replace(a, main_weapon=replace(a.main_weapon, hit_modifier=1))
    assert attack(a, fighter(), [roll('a.hit', 5), roll('a.wound', 1)]).damage == 0


def test_final_natural_reroll_six_qualifies():
    a = fighter(True)
    a = replace(a, global_effects=replace(a.global_effects, reroll_hits=True))
    result = attack(a, fighter(), [roll('a.hit', 1), roll('a.hit.reroll', 6), roll('a.wound', 1)])
    assert result.damage == 1


@pytest.mark.parametrize('automatic', ['weapon', 'ws-zero', 'helpless'])
def test_automatic_hit_has_no_natural_six(automatic):
    a, b, options = fighter(True), fighter(), {}
    if automatic == 'weapon':
        a = replace(a, main_weapon=replace(a.main_weapon, automatic_hit=True))
    elif automatic == 'ws-zero':
        b = replace(b, characteristics=replace(b.characteristics, weapon_skill=0))
    else:
        options['helpless_at_start'] = True
    assert attack(a, b, [roll('a.wound', 1)], **options).damage == 0


def test_sweep_characteristic_failure_is_not_hit_die_six():
    a = fighter(True, main_weapon_id='weapon.double-handed-weapon', skill_ids=('skill.sweep',))
    assert attack(a, fighter(), [roll('a.sweep', 6), roll('a.wound', 1)]).damage == 0


@pytest.mark.parametrize('save', [4, 6])
def test_lucky_charm_discards_original_hit_and_extra(save):
    b = fighter(defence_ids=('defence.lucky-charm',))
    result = attack(fighter(True), b, [roll('a.hit', 6), roll('a.lucky-charm', save)])
    assert result.damage == 0 and not result.defender.lucky_charm


def test_failed_charm_does_not_roll_again_for_extra():
    b = fighter(defence_ids=('defence.lucky-charm',))
    result = attack(fighter(True), b,
        [roll('a.hit', 6), roll('a.lucky-charm', 1), roll('a.wound', 1)])
    assert result.damage == 1 and not result.defender.lucky_charm


def test_exceptional_parry_discards_spectral_hit():
    b = fighter(main_weapon_id='weapon.sword')
    b = replace(b, global_effects=replace(b.global_effects,
        tags=(*b.global_effects.tags, 'rule.blood-dragon-sword-master', 'skill.swordmaster')))
    result = attack(fighter(True), b, [roll('a.hit', 6), roll('a.parry', 6)])
    assert result.parried and result.damage == 0


@pytest.mark.parametrize('extra_save,ordinary_save,damage', [(6, 6, 0), (6, 1, 1),
                                                          (1, 6, 1), (1, 1, 2)])
def test_each_contribution_has_own_armour_save(extra_save, ordinary_save, damage):
    b = fighter(armour_id='armour.heavy-armour')
    result = attack(fighter(True), b, [roll('a.hit', 6),
        roll('a.spectral-touch.armour', extra_save), roll('a.wound', 4),
        roll('a.armour', ordinary_save)])
    assert result.damage == damage and result.defender.wounds == 4 - damage


@pytest.mark.parametrize('save_kind', ['ward', 'regeneration'])
@pytest.mark.parametrize('face,damage', [(6, 0), (1, 1)])
def test_extra_obeys_special_saves(save_kind, face, damage):
    b = fighter()
    b = replace(b, global_effects=replace(b.global_effects,
        **{'ward_save' if save_kind == 'ward' else 'regeneration_save': 4}))
    result = attack(fighter(True), b, [roll('a.hit', 6),
        roll(f'a.spectral-touch.special.{save_kind}', face), roll('a.wound', 1)])
    assert result.damage == damage


def test_extra_removal_stops_ordinary_and_reacts_once():
    a, b = fighter(True), fighter(wounds=1, trait_overrides={'acid_blood': True})
    result = attack(a, b, [roll('a.hit', 6), roll('a.spectral-touch.injury.0', 6),
        roll('a.spectral-touch.acid-blood.0.wound', 4)])
    assert result.defender.condition == phases.Condition.OUT
    assert result.damage == 1 and result.attacker.wounds == 3


def test_both_contributions_react_once():
    b = fighter(trait_overrides={'acid_blood': True})
    result = attack(fighter(True), b, [roll('a.hit', 6),
        roll('a.spectral-touch.acid-blood.0.wound', 4), roll('a.wound', 4),
        roll('a.acid-blood.0.wound', 4)])
    assert result.damage == 2 and result.defender.wounds == result.attacker.wounds == 2


@pytest.mark.parametrize('rescue', [1, 6])
def test_rescue_is_immediate_before_ordinary_wound(rescue):
    b = fighter(wounds=1, skill_ids=('mechanic.force-of-will',))
    rolls = [roll('a.hit', 6), roll('a.spectral-touch.injury.0', 6),
        roll('a.spectral-touch.force-of-will.rescue', rescue)]
    if rescue == 1:
        rolls.append(roll('a.wound', 1))
    result = attack(fighter(True), b, rolls)
    assert 'force-of-will' in result.defender.resources_spent
    assert result.defender.condition == (phases.Condition.STANDING if rescue == 1 else phases.Condition.OUT)


@pytest.mark.parametrize('injury', [1, 3])
def test_extra_knockdown_or_stun_does_not_auto_finish_continuation(injury):
    result = attack(fighter(True), fighter(wounds=1), [roll('a.hit', 6),
        roll('a.spectral-touch.injury.0', injury), roll('a.wound', 1)])
    assert result.damage == 1 and result.defender.condition == (
        phases.Condition.KNOCKED_DOWN if injury == 1 else phases.Condition.STUNNED)


def test_extra_does_not_use_critical_capacity_or_weapon_damage_die():
    a = fighter(True)
    a = replace(a, main_weapon=replace(a.main_weapon, damage=4, damage_die_sides=3))
    result = attack(a, fighter(), [roll('a.hit', 6), roll('a.wound', 1)])
    assert result.damage == 1 and result.attacker.critical_available


def test_ordinary_critical_does_not_double_extra():
    result = attack(fighter(True), fighter(),
        [roll('a.hit', 6), roll('a.wound', 6), roll('a.critical', 3)])
    assert result.damage == 3 and not result.attacker.critical_available


def pool(a, b, rolls, count=1):
    dice, choices = StrictDice(rolls), StrictDecisions([])
    result = _resolve_attack_pool(a, b, state(a), state(b), count, dice, key='p',
        first_round=False, charging=False, decisions=choices)
    dice.finish()
    choices.finish()
    return result


def test_repeated_pool_sixes_each_add_one_wound_after_hit_preparation():
    a = fighter(True)
    sa, sb, outcomes = pool(a, fighter(), [roll('p.attack.0.hit', 6),
        roll('p.attack.1.hit', 6), roll('p.attack.0.wound', 1), roll('p.attack.1.wound', 1)], 2)
    assert sb.wounds == 2 and [r.damage for r in outcomes] == [1, 1]
    assert sa.critical_available


def test_mark_manufactured_six_is_not_natural_even_after_pool_transport():
    a = fighter(True, skill_ids=('mechanic.mark-of-the-old-ones',))
    a = replace(a, main_weapon=replace(a.main_weapon, hit_modifier=-2))
    sa, sb, outcomes = pool(a, fighter(), [roll('p.attack.0.hit', 1), roll('p.attack.0.wound', 1)])
    assert 'mark-of-the-old-ones' in sa.resources_spent
    assert outcomes[0].hit_roll == 6 and outcomes[0].damage == 0 and sb.wounds == 4


def test_real_spirit_host_receives_the_trait_without_fixture_injection():
    a = compile_fighter(FighterBuild('mordheim', band_id='call-of-the-night-haint-mim',
        profile_id='spirit-hosts'))
    assert a.global_effects.tags.count('trait.spectral-touch') == 1
    result = attack(a, fighter(), [roll('a.hit', 6), roll('a.wound', 1)])
    assert result.damage == 1


@pytest.mark.parametrize('armour_face,damage', [(4, 1), (5, 0)])
def test_extra_uses_actual_attack_strength_and_penetration(armour_face, damage):
    # Heavy armour 5+, S4 makes 6+, dagger's +1 brings it back to 5+.
    a = fighter(True, strength=4, main_weapon_id='weapon.dagger')
    result = attack(a, fighter(armour_id='armour.heavy-armour'),
        [roll('a.hit', 6), roll('a.spectral-touch.armour', armour_face), roll('a.wound', 1)])
    assert result.damage == damage


def test_extra_respects_magic_specific_natural_armour_and_ward():
    a, b = fighter(True), fighter()
    a = replace(a, main_weapon=replace(a.main_weapon,
        tags=(*a.main_weapon.tags, 'attack.magical')))
    b = replace(b, natural_armour_save=4, global_effects=replace(b.global_effects,
        natural_armour_negated_by_magic=True, ward_save=4, ward_save_mundane_only=True))
    assert attack(a, b, [roll('a.hit', 6), roll('a.wound', 1)]).damage == 1


def test_extra_is_one_even_with_fire_and_flammable():
    a, b = fighter(True), fighter()
    a = replace(a, main_weapon=replace(a.main_weapon, tags=(*a.main_weapon.tags, 'attack.fire')))
    b = replace(b, global_effects=replace(b.global_effects, tags=(*b.global_effects.tags, 'flammable')))
    assert attack(a, b, [roll('a.hit', 6), roll('a.wound', 1)]).damage == 1


def test_extra_immediate_save_consumes_luck_before_ordinary_save():
    b = fighter(armour_id='armour.heavy-armour', skill_ids=('skill.luck',))
    result = attack(fighter(True), b, [roll('a.hit', 6),
        roll('a.spectral-touch.armour', 1), roll('a.spectral-touch.armour.reroll', 6),
        roll('a.wound', 4), roll('a.armour', 1)])
    assert result.damage == 1 and 'luck' in result.defender.resources_spent


def test_extra_acid_blood_removing_attacker_cancels_ordinary():
    b = fighter(trait_overrides={'acid_blood': True})
    result = attack(fighter(True, wounds=1), b, [roll('a.hit', 6),
        roll('a.spectral-touch.acid-blood.0.wound', 4),
        roll('a.spectral-touch.acid-blood.0.injury.0', 6)])
    assert result.attacker.condition == phases.Condition.OUT and result.defender.wounds == 3
    assert result.damage == 1


def test_stun_then_successful_ordinary_wound_still_rolls_injury():
    result = attack(fighter(True), fighter(wounds=1), [roll('a.hit', 6),
        roll('a.spectral-touch.injury.0', 3), roll('a.wound', 4), roll('a.injury.0', 1)])
    assert result.damage == 2 and result.defender.condition == phases.Condition.STUNNED


def test_ordinary_critical_armour_denial_cannot_retroactively_deny_extra_save():
    result = attack(fighter(True), fighter(armour_id='armour.heavy-armour'),
        [roll('a.hit', 6), roll('a.spectral-touch.armour', 6),
         roll('a.wound', 6), roll('a.critical', 3)])
    assert result.damage == 2 and result.critical


def test_on_hit_kusara_effect_is_not_replayed_by_extra_wound():
    result = attack(fighter(True, main_weapon_id='weapon.kusara-kama'), fighter(),
        [roll('a.hit', 6), roll('a.wound', 1)])
    assert result.damage == 1 and result.defender.attack_penalty == 1


def test_pool_charm_blocks_only_first_six_and_consumes_once():
    _, sb, outcomes = pool(fighter(True), fighter(defence_ids=('defence.lucky-charm',)),
        [roll('p.attack.0.hit', 6), roll('p.attack.1.hit', 6),
         roll('p.attack.0.lucky-charm', 6), roll('p.attack.1.wound', 1)], 2)
    assert not sb.lucky_charm and sb.wounds == 3
    assert [o.damage for o in outcomes] == [0, 1]


def test_pool_lethal_extra_cancels_later_prepared_hit_wounds():
    _, sb, outcomes = pool(fighter(True), fighter(wounds=1),
        [roll('p.attack.0.hit', 6), roll('p.attack.1.hit', 6),
         roll('p.attack.0.spectral-touch.injury.0', 6)], 2)
    assert sb.condition == phases.Condition.OUT and len(outcomes) == 1


def test_barrage_new_six_establishes_extra_and_stops_despite_ordinary_failure():
    a, b = fighter(True, main_weapon_id='weapon.rapier'), fighter()
    dice = StrictDice([roll('p.attack.0.hit', 5), roll('p.attack.0.wound', 1),
        roll('p.attack.0.barrage.1.hit', 6),
        roll('p.attack.0.barrage.1.spectral-touch.armour', 1),
        roll('p.attack.0.barrage.1.wound', 1)])
    choices = StrictDecisions([{'key': 'p.attack.0.barrage', 'value': True}])
    _, sb, outcomes = _resolve_attack_pool(a, b, state(a), state(b), 1, dice,
        key='p', first_round=False, charging=False, decisions=choices)
    dice.finish()
    choices.finish()
    assert sb.wounds == 3 and outcomes[0].damage == 1
    assert outcomes[0].damage_already_reacted == 1 and outcomes[0].wounded


def test_barrage_new_six_reacts_to_extra_and_ordinary_damage_once_each():
    a = fighter(True, main_weapon_id='weapon.rapier')
    b = fighter(trait_overrides={'acid_blood': True})
    dice = StrictDice([roll('a.hit', 5), roll('a.wound', 1),
        roll('a.barrage.1.hit', 6), roll('a.barrage.1.spectral-touch.armour', 1),
        roll('a.barrage.1.spectral-touch.acid-blood.0.wound', 4),
        roll('a.barrage.1.wound', 4), roll('a.barrage.1.armour', 1),
        roll('a.acid-blood.0.wound', 4)])
    choices = StrictDecisions([{'key': 'a.barrage', 'value': True}])
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, dice,
        key='a', decisions=choices)
    result = _react_to_wound(a, b, result, dice, 'a')
    dice.finish()
    choices.finish()
    assert result.damage == 2 and result.defender.wounds == result.attacker.wounds == 2
    assert result.damage_already_reacted == 2 and result.reactions_resolved and result.wounded


@pytest.mark.parametrize('mutation', ['remove-trigger', 'suppress-continuation'])
def test_semantic_expectations_detect_isolated_mutations(monkeypatch, mutation):
    from pathlib import Path
    from mordheim_combat.modular import attacks
    source = Path(attacks.__file__).read_text(encoding='utf-8')
    if mutation == 'remove-trigger':
        source = source.replace('if natural_hit_six and phases.has_tag(effect, "trait.spectral-touch"):',
            'if False and phases.has_tag(effect, "trait.spectral-touch"):', 1)
    else:
        source = source.replace('    wound_context = prepare_wound_context(',
            '    return AttackOutcome(attacker_state, defender_state, hit=True)\n'
            '    wound_context = prepare_wound_context(', 1)
    namespace = {'__name__': 'spectral_touch_isolated_mutant'}
    exec(compile(source, '<isolated spectral mutation>', 'exec'), namespace)
    monkeypatch.setattr(attacks, '_resolve_reference_attack_once', namespace['_resolve_reference_attack_once'])
    with pytest.raises(AssertionError):
        test_trigger_and_failed_ordinary_wound(True, 6, 1)


@pytest.mark.parametrize('saved', [False, True])
@pytest.mark.parametrize('path', ['attack', 'pool', 'replay'])
def test_established_extra_wound_prevents_barrage_even_when_saved(saved, path):
    # R4 concerns a wound established, not damage after saving. Strict empty
    # decisions forbid even offering another attack after the ordinary roll fails.
    a, b = fighter(True, main_weapon_id='weapon.rapier'), fighter()
    key = {'attack': 'a', 'pool': 'p.attack.0', 'replay': 'round.0.first.attack.0'}[path]
    rolls = [roll(f'{key}.hit', 6), roll(f'{key}.spectral-touch.armour', 6 if saved else 1),
             roll(f'{key}.wound', 1)]
    if path == 'replay':
        from mordheim_combat_lab.verification.parity._replay import replay_duel
        from mordheim_core.models import DuelContext
        rolls.append(roll('round.0.second.attack.0.hit', 1))
        result = replay_duel(a, b, backend='modular', rolls=rolls,
            context=DuelContext(charging=('first',), active_participant='first'))
        assert result.winner == 2 and result.rounds == 1
        assert result.wounds == (4, 4 if saved else 3)
        assert result.conditions == (0, 0) and result.decisions == ()
        return
    dice, choices = StrictDice(rolls), StrictDecisions([])
    if path == 'pool':
        _, sb, outcomes = _resolve_attack_pool(a, b, state(a), state(b), 1, dice,
            key='p', first_round=False, charging=False, decisions=choices)
        result = outcomes[0]
        assert sb.wounds == 4 - int(not saved)
    else:
        result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, dice,
            key=key, decisions=choices)
    dice.finish()
    choices.finish()
    assert result.wounded and not result.barrage_available
    assert result.damage == result.damage_already_reacted == int(not saved)
    assert result.defender.wounds == 4 - int(not saved)


def test_natural_six_without_spectral_touch_keeps_barrage_after_failed_wound():
    a, b = fighter(main_weapon_id='weapon.rapier'), fighter()
    dice = StrictDice([roll('a.hit', 6), roll('a.wound', 1),
        roll('a.barrage.1.hit', 5), roll('a.barrage.1.wound', 4),
        roll('a.barrage.1.armour', 1)])
    choices = StrictDecisions([{'key': 'a.barrage', 'value': True}])
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, dice,
        key='a', decisions=choices)
    dice.finish()
    choices.finish()
    assert result.damage == 1 and result.wounded and result.defender.wounds == 3


@pytest.mark.parametrize('mutation', ['remove-wound-prerequisite', 'use-unsaved-damage'])
def test_barrage_prerequisite_detects_isolated_mutations(monkeypatch, mutation):
    from pathlib import Path
    import sys
    from mordheim_combat.modular import attacks
    source = Path(attacks.__file__).read_text(encoding='utf-8')
    anchor = 'not result.barrage_available or result.wounded or not result.attacker.active'
    assert source.count(anchor) == 1
    replacement = ('not result.barrage_available or not result.attacker.active'
        if mutation == 'remove-wound-prerequisite' else
        'not result.barrage_available or result.damage > 0 or not result.attacker.active')
    namespace = {'__name__': 'barrage_prerequisite_isolated_mutant'}
    exec(compile(source.replace(anchor, replacement, 1), '<isolated Barrage mutation>', 'exec'), namespace)
    monkeypatch.setattr(sys.modules[__name__], 'resolve_reference_attack', namespace['resolve_reference_attack'])
    with pytest.raises(AssertionError):
        test_established_extra_wound_prevents_barrage_even_when_saved(True, 'attack')


def test_pending_spirit_host_tag_reaches_actual_modular_duel_driver():
    from mordheim_combat_lab.verification.parity._replay import replay_duel
    from mordheim_core.models import DuelContext
    a = compile_fighter(FighterBuild('mordheim', band_id='call-of-the-night-haint-mim',
        profile_id='spirit-hosts'))
    a = replace(a, global_effects=replace(a.global_effects,
        tags=(*a.global_effects.tags, 'trait.spectral-touch')))
    result = replay_duel(a, fighter(wounds=1), backend='modular',
        context=DuelContext(charging=('first',), active_participant='first'), rolls=[
            roll('round.0.first.attack.0.hit', 6),
            roll('round.0.first.attack.1.hit', 1), roll('round.0.first.attack.2.hit', 1),
            roll('round.0.first.attack.0.spectral-touch.injury.0', 6)])
    assert result.winner == 0 and result.rounds == 1
    assert result.wounds == (3, 0) and result.conditions == (0, int(phases.Condition.OUT))
