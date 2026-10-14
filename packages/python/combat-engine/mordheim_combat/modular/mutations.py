"""Source-defined MiM brands acquired by one of the two current duelists."""
from dataclasses import replace

from mordheim_core.dice import RollRequest
from mordheim_core.effects import merge_effects
from mordheim_core.models import EffectSet
from mordheim_combat.phases import has_tag
from .contexts import OwnedRollDice


_LIVE = {'weapon_skill', 'strength', 'toughness', 'initiative', 'attacks'}
_BITES = ('rule.bite-attack', 'rule.strikes-last-bite', 'rule.hillman-bite', 'rule.poisonous-bite')
_TAILS = ('rule.scorpion-tail', 'rule.prehensile-tail', 'rule.spiked-tail')


def _inventory(fighter, current):
    return fighter.mutation_equipment if current.mutation_equipment is None else current.mutation_equipment


def _hands(fighter, current):
    extra = [item.slot for item in _inventory(fighter, current)
        if item.slot and item.slot.startswith('extra')]
    return tuple(dict.fromkeys(('main', 'off', *extra,
        *(f'extra.{index}' for index in range(sum(m.roll == 41 for m in current.mutations))))))


def _lost(current, slot):
    return f'lost:{slot}' in current.mutated_hands


def _choose_hand(fighter, current, decisions, key):
    available = [slot for slot in _hands(fighter, current) if not _lost(current, slot)]
    ordinary = [slot for slot in available if not any(
        f'{kind}:{slot}' in current.mutated_hands for kind in ('claw', 'limb'))]
    available = [*ordinary, *(slot for slot in available if slot not in ordinary)]
    return next((slot for slot in available if decisions is not None
        and decisions.choose(f'{key}.hand.{slot}', fighter)), available[0] if available else None)


def _stow_hand(fighter, current, slot, *, weapons_only=False):
    items = tuple(replace(item, slot=None) if item.slot == slot
        and (not weapons_only or item.kind == 'weapon') else item
        for item in _inventory(fighter, current))
    # A two-handed object cannot stay active when either required hand is lost.
    items = tuple(replace(item, slot=None) if item.slot is not None
        and item.kind == 'weapon' and (item.effect.two_handed or item.effect.paired) else item for item in items)
    return replace(current, mutation_equipment=items)


def _equip_limb(fighter, current, slot, decisions, key):
    if (has_tag(fighter.global_effects, 'nature.possessed')
            or current.transformed or current.equipment_cast_off or current.hillman_wolf):
        return current
    items = list(_inventory(fighter, current))
    for index, item in enumerate(items):
        melee = item.kind == 'weapon' and any(tag.startswith('weapon.') for tag in item.effect.tags)
        shield = item.kind == 'defence' and any(has_tag(item.effect, tag) for tag in ('defence.shield', 'defence.buckler'))
        prohibited = (any(m.roll == 61 for m in current.mutations) and not _burning_item_allowed(item)
            or slot != 'tail' and sum(value.startswith('limb:') for value in current.mutated_hands) >= 2
            or melee and current.atrophied_arms and any(other is not item and other.kind == 'weapon'
                and other.slot in _hands(fighter, current) for other in items))
        if (not prohibited and item.slot != slot and (melee or shield) and not item.effect.two_handed and not item.effect.paired
                and decisions is not None and decisions.choose(f'{key}.equip.{index}', item)):
            items[index] = replace(item, slot=slot)
            return replace(current, mutation_equipment=tuple(items))
    return replace(current, mutation_equipment=tuple(items))


def _burning_item_allowed(item):
    protected = any(has_tag(item.effect, tag) for tag in
        ('attack.magical', 'material.magical', 'material.gromril', 'material.ithilmar'))
    armour = item.kind == 'armour' or item.kind == 'defence' and any(
        has_tag(item.effect, tag) for tag in ('defence.shield', 'defence.buckler', 'defence.helmet',
            'defence.cooking-pot-helmet', 'defence.sea-dragon-cloak', 'defence.wolf-pelt-cloak'))
    return protected or not (item.kind == 'weapon' or armour)


def _operation(value, operation, operand):
    if value is None:
        return None
    if operation == 'add':
        return value + operand
    if operation == 'set':
        return operand
    if operation == 'halve-ceil':
        return (value + operand - 1) // operand
    raise ValueError(f'Unsupported declared mutation operation: {operation}')


def _profile(fighter, mutations, equipment=None):
    values = {name: getattr(fighter.characteristics, name) for name in (
        'weapon_skill', 'strength', 'toughness', 'wounds', 'initiative', 'attacks', 'movement', 'leadership')}
    if equipment is not None:
        for items, sign in ((fighter.mutation_equipment, -1), (equipment, 1)):
            for item in items:
                if item.slot is not None:
                    for stat, amount in item.stat_bonuses:
                        if values[stat] is not None: values[stat] += sign * amount
    natural, worst, locked = fighter.natural_armour_save, fighter.natural_armour_worst_save, False
    for mutation in mutations:
        for stat, operation, operand in mutation.stat_ops:
            if stat in ('natural_armour_save', 'natural_armour_worst_save'):
                if stat == 'natural_armour_save': natural = min(natural, operand)
                else: worst = min(worst, operand)
            elif not (locked and stat in ('toughness', 'wounds')):
                result = _operation(values[stat], operation, operand)
                values[stat] = (None if result is None else max(0, result))
        locked = locked or mutation.roll == 63
    return replace(fighter.characteristics, **values), natural, worst


def _effect(mutation):
    tags = {46: ('mechanic.mim-regeneration',),
        61: ('mechanic.burning-body', 'rule.unarmed-without-penalties'),
        62: ('mechanic.plague-carrier',), 63: ('condition.crystalline-body',)}.get(mutation.roll, ())
    return merge_effects(mutation.effect, EffectSet(tags=tags))


def _physical_effect(fighter, current, item):
    if item is None: return None, None
    index = next((index for index, held in enumerate(_inventory(fighter, current)) if held is item), None)
    original = fighter.mutation_equipment[index] if index is not None else None
    if original is not None and item.effect == original.effect:
        if original.slot == 'main': return fighter.main_weapon, fighter.main_weapon_without_poison
        if original.slot == 'off': return fighter.off_hand, fighter.off_hand_without_poison
    return item.effect, item.effect_without_poison


def _extra_attacks(fighter, current, *, select_tail=True, without_poison=False):
    clean = dict(fighter.extra_attacks_without_poison) if without_poison else {}
    extra = [clean.get(attack, attack) for attack in fighter.extra_attacks]
    for mutation in current.mutations:
        if mutation.roll == 42:
            index = next((i for i, attack in enumerate(extra) if any(has_tag(attack, tag) for tag in _BITES)), None)
            if index is None:
                extra.extend(mutation.extra_attacks)
            else:
                extra[index] = replace(extra[index], fixed_strength=5,
                    tags=tuple(dict.fromkeys((*extra[index].tags, 'rule.poisonous-bite'))))
        elif mutation.roll in (52, 55):
            if not any(any(has_tag(attack, tag) for tag in _BITES) for attack in extra):
                extra.extend(mutation.extra_attacks)
        elif mutation.roll == 44:
            if not any(any(has_tag(attack, tag) for tag in _TAILS) for attack in extra):
                extra.extend(mutation.extra_attacks)
        else:
            extra.extend(mutation.extra_attacks)
    cast_off = current.transformed or current.equipment_cast_off or current.hillman_wolf
    tail_item = next((item for item in _inventory(fighter, current) if item.slot == 'tail'), None) if not cast_off else None
    if tail_item is not None:
        extra = [attack for attack in extra if not has_tag(attack, 'rule.prehensile-tail')]
    for item in _inventory(fighter, current):
        if cast_off: continue
        if item.slot and (item.slot.startswith('extra.') or item.slot == 'tail') and item.kind == 'weapon':
            physical, clean = _physical_effect(fighter, current, item)
            extra.append(merge_effects(clean if without_poison and clean is not None else physical,
                EffectSet(tags=(f'mutation.hand.{item.slot}', 'mutation.carried-weapon',
                *(("rule.prehensile-tail",) if item.slot == 'tail' else ())))))
        elif item.slot == 'tail' and item.kind == 'defence':
            extra.append(EffectSet(tags=('rule.prehensile-tail', 'mutation.shield-tail')))
    extra = [attack for attack in extra if not any(
        has_tag(attack, f'mutation.hand.{slot}') and _lost(current, slot) for slot in _hands(fighter, current))
    ]
    claws = set()
    retained = []
    for attack in reversed(extra):
        hand = next((slot for slot in _hands(fighter, current) if has_tag(attack, f'mutation.hand.{slot}')), None)
        if has_tag(attack, 'rule.great-claw') and hand is not None:
            if f'claw:{hand}' not in current.mutated_hands or hand in claws: continue
            claws.add(hand)
        retained.append(attack)
    extra = list(reversed(retained))
    if select_tail and any(m.roll in (44, 54) for m in current.mutations):
        tails = [attack for attack in extra if any(has_tag(attack, tag) for tag in _TAILS)]
        chosen = next((int(value.rsplit('.', 1)[1]) for value in current.resources_spent
                       if value.startswith('mutation-tail.')), 0)
        selected = min(chosen, len(tails)-1)
        index = -1
        retained = []
        for attack in extra:
            if any(has_tag(attack, tag) for tag in _TAILS):
                index += 1
                if index != selected: continue
            retained.append(attack)
        extra = retained
    return tuple(attack for attack in extra if not select_tail or not has_tag(attack, 'mutation.shield-tail'))


def select_mutation_tail(fighter, current, decisions, key):
    """Select the source's single tail for this phase, without spending a use."""
    clean = replace(current, resources_spent=frozenset(value for value in current.resources_spent
        if not value.startswith('mutation-tail.')))
    if not any(m.roll in (44, 54) for m in current.mutations):
        return clean
    tails = [attack for attack in _extra_attacks(fighter, clean, select_tail=False)
             if any(has_tag(attack, tag) for tag in _TAILS)]
    selected = next((index for index, attack in enumerate(tails) if decisions is not None
        and decisions.choose(f'{key}.tail.{index}', attack)), 0)
    return clean.spend(f'mutation-tail.{selected}') if tails else clean


def _equipment_projection(fighter, current, effect):
    if current.mutation_equipment is None:
        return fighter, effect
    items = [item for item in current.mutation_equipment if item.slot is not None]
    tails = [attack for attack in _extra_attacks(fighter, current, select_tail=False)
             if any(has_tag(attack, tag) for tag in _TAILS)]
    chosen_tail = next((int(value.rsplit('.', 1)[1]) for value in current.resources_spent
                       if value.startswith('mutation-tail.')), 0)
    uses_tail_item = bool(tails and any(has_tag(tails[min(chosen_tail, len(tails)-1)], tag)
        for tag in ('mutation.hand.tail', 'mutation.shield-tail')))
    items = [item for item in items if item.slot != 'tail' or uses_tail_item]
    effect = fighter.global_effects_without_equipment
    shield_skills = fighter.skill_effects_only
    for item in items:
        if item.kind != 'weapon':
            effect = merge_effects(effect, item.effect)
        elif item.slot and (item.slot.startswith('extra.') or item.slot == 'tail') and item.effect.parry:
            effect = merge_effects(effect, EffectSet(parry=True))
        if item.kind == 'defence' and any(has_tag(item.effect, tag) for tag in ('defence.shield', 'defence.buckler')):
            shield_skills = merge_effects(shield_skills, item.effect)
    for mutation in current.mutations:
        effect = merge_effects(effect, _effect(mutation))
    main_item = next((item for item in items if item.slot == 'main' and item.kind == 'weapon'), None)
    off_item = next((item for item in items if item.slot == 'off'), None)
    limbs = [limb for limb in current.mutation_weapon_limbs if not any(
        has_tag(limb, f'mutation.hand.{slot}') and _lost(current, slot) for slot in _hands(fighter, current))]
    main, main_clean = _physical_effect(fighter, current, main_item)
    off, off_clean = _physical_effect(fighter, current, off_item)
    main_slot, off_slot = ('main' if main_item else 'unarmed'), 'off'
    if main is None and limbs:
        main, main_slot = limbs.pop(0), 'mutation.limb'
        main_clean = None
    if main is None and off_item and off_item.kind == 'weapon':
        main, main_clean, main_slot, off, off_clean = off, off_clean, 'off', None, None
    if off is None and limbs:
        off, off_slot = limbs.pop(0), 'mutation.limb.off'
        off_clean = None
    main = main or fighter.unarmed_weapon or EffectSet(tags=('weapon.fist',), strength_bonus=-1, target_armour_bonus=1)
    helmet = min((4 if has_tag(item.effect, 'defence.helmet') else 5
        for item in items if any(has_tag(item.effect, tag) for tag in ('defence.helmet', 'defence.cooking-pot-helmet'))), default=7)
    return replace(fighter, main_weapon=main, off_hand=off,
        main_hand_slot=main_slot, off_hand_slot=off_slot,
        main_weapon_without_poison=main_clean, off_hand_without_poison=off_clean,
        off_hand_attacks=off is not None and (off_item is None or off_item.kind == 'weapon'),
        armour_save=max(1, 7-effect.armour_save_bonus), helmet_save=helmet,
        shield_and_skill_effects=shield_skills), effect


def fighter_for_mutations(fighter, current):
    if not current.mutations:
        return fighter
    characteristics, natural, worst = _profile(fighter, current.mutations, current.mutation_equipment)
    effect = fighter.global_effects
    for mutation in current.mutations:
        effect = merge_effects(effect, _effect(mutation))
    result, effect = _equipment_projection(fighter, current, effect)
    retained, skills = fighter.global_effects_without_equipment, fighter.skill_effects_only
    for mutation in current.mutations:
        retained = merge_effects(retained, _effect(mutation))
        skills = merge_effects(skills, _effect(mutation))
    if all(_lost(current, slot) for slot in _hands(fighter, current)):
        effect = merge_effects(effect, EffectSet(tags=('condition.mim-no-hand-attacks',)))
        retained = merge_effects(retained, EffectSet(tags=('condition.mim-no-hand-attacks',)))
    stacks = fighter.natural_armour_stacks or any(m.roll == 43 for m in current.mutations)
    armour = result.armour_save
    if stacks:
        # Recompose from the retained physical suit, shield and innate/skill
        # contributions, rather than reverse a possibly capped armour total.
        if current.mutation_equipment is None:
            armour = 7-effect.armour_save_bonus-sum(item.effect.armour_save_bonus
                for item in fighter.mutation_equipment if item.slot is not None and item.kind == 'armour')
        armour -= 7-natural
    extra = _extra_attacks(fighter, current)
    clean_extra = _extra_attacks(fighter, current, without_poison=True)
    return replace(result, characteristics=characteristics, global_effects=effect,
        mutation_equipment=_inventory(fighter, current),
        global_effects_without_equipment=retained, skill_effects_only=skills,
        armour_save=max(1, armour),
        natural_armour_save=natural, natural_armour_worst_save=worst,
        natural_armour_stacks=stacks,
        extra_attacks=extra, extra_attacks_without_poison=tuple((attack, clean)
            for attack, clean in zip(extra, clean_extra) if attack != clean))


def apply_brand(fighter, current, option, dice, decisions, key):
    """Apply one explicit chart result without rerolling, buying or spawning gear."""
    old, _, _ = _profile(fighter, current.mutations, current.mutation_equipment)
    owned = dice if isinstance(dice, OwnedRollDice) else OwnedRollDice(dice, fighter, current, decisions)
    result = current
    if option.roll == 25:
        slot = _choose_hand(fighter, result, decisions, key)
        if slot is not None:
            result = _stow_hand(fighter, result, slot, weapons_only=True)
            result = replace(result, mutated_hands=(*(value for value in result.mutated_hands
                if value not in (f'claw:{slot}',f'limb:{slot}')), f'claw:{slot}'),
                mutation_weapon_limbs=tuple(limb for limb in result.mutation_weapon_limbs
                    if not has_tag(limb,f'mutation.hand.{slot}')))
            option = replace(option, extra_attacks=tuple(merge_effects(attack,
                EffectSet(tags=(f'mutation.hand.{slot}',))) for attack in option.extra_attacks))
    elif option.roll == 41:
        slot = f'extra.{sum(m.roll == 41 for m in current.mutations)}'
        result = _equip_limb(fighter, result, slot, decisions, key)
        if has_tag(fighter.global_effects, 'nature.possessed'):
            option = replace(option, extra_attacks=(EffectSet(tags=('weapon.natural-attacks', f'mutation.hand.{slot}')),))
    elif option.roll == 44:
        result = _equip_limb(fighter, result, 'tail', decisions, key)
    elif option.roll == 61:
        result = replace(result, mutation_equipment=tuple(replace(item, slot=None)
            if not _burning_item_allowed(item) else item for item in _inventory(fighter, result)))
    elif option.roll == 65:
        face = owned.roll(RollRequest(f'{key}.limb', 6))
        if not option.limb_forms: raise ValueError('Beweaponed Extremities requires its six source weapon forms')
        slot = _choose_hand(fighter, result, decisions, key)
        if slot is not None:
            limb = merge_effects(replace(option.limb_forms[min(6, max(1, face))-1], two_handed=False),
                EffectSet(tags=(f'mutation.hand.{slot}',)))
            result = _stow_hand(fighter, result, slot)
            result = replace(result, mutation_weapon_limbs=(*(previous for previous in result.mutation_weapon_limbs
                if not has_tag(previous,f'mutation.hand.{slot}')), limb),
                mutated_hands=(*(value for value in result.mutated_hands
                if value not in (f'claw:{slot}',f'limb:{slot}')), f'limb:{slot}'))
            if sum(value.startswith('limb:') for value in result.mutated_hands) >= 2:
                result = replace(result, mutation_equipment=tuple(replace(item, slot=None)
                    if item.slot in _hands(fighter, result) else item for item in _inventory(fighter, result)))
    elif option.roll == 66:
        face = owned.roll(RollRequest(f'{key}.atrophy', 6))
        if face <= 1:
            option = replace(option, effect=merge_effects(option.effect, EffectSet(tags=('mechanic.stupidity',))))
        elif face <= 4:
            slot = _choose_hand(fighter, result, decisions, key)
            if slot is not None:
                result = _stow_hand(fighter, result, slot)
                result = replace(result, mutated_hands=(*result.mutated_hands, f'lost:{slot}'),
                    atrophied_arms=result.atrophied_arms+1)
                weapons = [item for item in _inventory(fighter, result) if item.slot in _hands(fighter, result)
                    and item.kind == 'weapon']
                keep = next((item for item in weapons if decisions is not None
                    and decisions.choose(f'{key}.retain.{item.slot}', item)), weapons[0] if weapons else None)
                result = replace(result, mutation_equipment=tuple(replace(item, slot=None)
                    if item in weapons and item is not keep else item for item in _inventory(fighter, result)))
        else:
            result = replace(result, atrophied_legs=result.atrophied_legs+1)
            option = replace(option, stat_ops=(*option.stat_ops,
                ('movement', 'set', 0) if result.atrophied_legs >= 2 else ('movement', 'halve-ceil', 2)))
    result = replace(result, mutations=(*result.mutations, option))
    new, _, _ = _profile(fighter, result.mutations, result.mutation_equipment)
    changes = {stat: max(0,
        getattr(current, stat) + getattr(new, stat) - getattr(old, stat)) for stat in _LIVE}
    if new.wounds != old.wounds:
        changes['wounds'] = (min(current.wounds, new.wounds) if option.roll == 63
            else current.wounds + new.wounds - old.wounds)
    if not isinstance(dice, OwnedRollDice):
        result = replace(result, resources_spent=result.resources_spent | owned.state.resources_spent)
    from .state import _parry_capacity
    previous = fighter_for_mutations(fighter, current)
    projected = fighter_for_mutations(fighter, result)
    changes['parries_remaining'] = max(0, current.parries_remaining
        + _parry_capacity(projected) - _parry_capacity(previous))
    return replace(result, **changes)
