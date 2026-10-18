"""combat: Per-round state machine of the modular engine."""
from __future__ import annotations
from mordheim_combat import phases
from mordheim_combat.modular.alchemy import alchemist_addicted, resolve_alchemist

from dataclasses import dataclass, replace
from mordheim_combat.modular.aftermath import _black_hunger
from mordheim_combat.modular.aftermath import _revenant_recovery
from mordheim_combat.modular.aftermath import _characteristic_test
from mordheim_combat.modular.aftermath import _fire_recovery
from mordheim_combat.modular.aftermath import _force_of_will
from mordheim_combat.modular.aftermath import _spines
from mordheim_combat.modular.aftermath import _start_round_state
from mordheim_combat.modular.state import _refresh_random_characteristics, maximum_wounds, require_characteristics
from mordheim_combat.modular.pools import _resolve_attack_pool, electrical_touch_weapon, pool_attack_weapons
from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.psychology import causes_fear, resolve_fear, resolve_stupidity
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.state import AttackOutcome
from mordheim_combat.modular.state import CombatRoundResult
from mordheim_combat.modular.state import DuelState
from mordheim_combat.modular.equipment import equipment_for_state, is_pistol, whipcrack_weapon
from mordheim_combat.phases import AttackPoolContext
from mordheim_combat.phases import Condition
from mordheim_combat.phases import Phase
from mordheim_combat.phases import PriorityContext
from mordheim_combat.phases import build_attacks
from mordheim_combat.phases import first_acts_before
from mordheim_combat.phases import has_tag
from mordheim_combat.phases import resolve_priority
from mordheim_core.dice import AlwaysAccept
from mordheim_core.dice import DecisionPolicy
from mordheim_core.dice import DiceSource
from mordheim_core.dice import RollRequest
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet


def _initiative_bonus(current, fighter) -> int:
    """The Initiative a fighter gained over the value its profile prints.

    A profile that prints no Initiative at all has no base to raise: the
    compiler already refuses a bonus on an absent characteristic, so the delta
    is zero and the comparison falls back to the printed tie roll instead of
    inventing a base for it.
    """
    base = fighter.characteristics.initiative
    if base is None or current.initiative is None:
        return 0
    return current.initiative - base


def _strike_initiative(current, fighter):
    """Initiative of an auxiliary strike, or ``None`` for an absent one."""
    if current.initiative is None:
        return None
    return max(current.initiative_floor, current.initiative
               + fighter.global_effects.initiative_bonus - current.initiative_penalty)


SHADOW_DANCES = (
    "whirling-death", "storm-of-blades", "the-shadows-coil", "woven-mist",
)

# The two Lahmia Vampire powers that open the combat phase with a Leadership
# test on a supplied in-contact enemy: (tag, printed exclusions, key, own value).
# Deceive prints "using its own Leadership" and its failure bars only attacks
# against the Lahmia Vampire; Hypnotize prints no value qualifier and its
# failure bars the target's attacks and makes its assailants hit on +1.
LAHMIA_POWERS = (
    ("mechanic.lahmia-deceive",
     ("nature.undead", "nature.daemon", "mechanic.psychology-immunity"),
     "deceive", True),
    ("mechanic.lahmian-hypnotize",
     ("mechanic.psychology-immunity",),
     "hypnotize", False),
)


# The printed own-turn animosity contracts that suppress the bearer's attacks for
# turn: the ordinary Goblin squabble (a 1) and the Fungus Brew's Rowdy result
# (1-2), which shares the consumer and widens only the printed band.
ANIMOSITY_SOURCES = ("mechanic.goblin-squabble", "mechanic.fungus-rowdy")

# The Dark Jester's printed per-round trick slots.  Confound and Confuse is one
# printed choice with three distinct consequences (the Sidestepper dodge, the
# Babbling Banter modifier pair, the Trip wound replacement), so each round one
# of the three may be active and the choice is supplied by the application, not
# simulated: no round ever activates two tricks of the same rule.
JESTER_TRICK_STATES = ("dodge_trick_active", "banter_trick_active", "trip_trick_active")


def _owned_roll(fighter, current, dice, decisions, request, *, close_combat=False):
    from mordheim_combat.modular.contexts import OwnedRollDice
    owned = OwnedRollDice(dice, fighter, current, decisions, close_combat=close_combat)
    value = owned.roll(request)
    return value, owned.state


@dataclass(frozen=True, slots=True)
class ControlPower:
    """One printed Vampire power that spends a Leadership test to bar a foe.

    ``own_test`` is the Khemrian Seduction's opening test of the Vampire
    herself, ``own_turn_only`` the Lahmia Seduction's "during each Vampire
    turn", ``male_only`` its printed male recipient, ``persistent`` the lasting
    control the two Seduction copies establish (kept on the victim's spent
    resources, ended by the printed Recovery-phase regain test and by the
    printed attack) and ``auto_hit`` Hypnotic Gaze's "all attacks against it hit
    automatically".
    """

    tag: str
    exclusions: tuple[str, ...]
    name: str
    own_value_only: bool = False
    auto_hit: bool = False
    own_turn_only: bool = False
    own_test: bool = False
    male_only: bool = False
    persistent: bool = False


# Hypnotic Gaze and the two Seduction copies.  Each is read from its own printed
# origin, so each carries exactly the exclusions and qualifiers that clause
# prints and never a broader shared list.
CONTROL_POWERS = (
    ControlPower("mechanic.hypnotic-gaze", ("mechanic.psychology-immunity",),
                 "hypnotic-gaze", own_value_only=True, auto_hit=True),
    ControlPower("mechanic.lahmia-seduction",
                 ("mechanic.psychology-immunity", "nature.undead", "nature.daemon",
                  "mechanic.stupidity"),
                 "lahmia-seduction", own_value_only=True, own_turn_only=True,
                 male_only=True, persistent=True),
    ControlPower("mechanic.lahmian-seduction", ("mechanic.psychology-immunity",),
                 "lahmian-seduction", own_value_only=True, own_test=True,
                 persistent=True),
)

# The lasting control of the two Seduction copies lives on the victim's spent
# resources: it must outlive the phase that established it, and the resource
# also names its printed release, because the Khemrian copy ends on any attack
# by the Vampire while the Lahmia copy ends only on one that hits.
SEDUCTION_RESOURCES = ("seduction.controlled.lahmia", "seduction.controlled.lahmian")
CONTROL_RESOURCES = {
    "mechanic.lahmia-seduction": "seduction.controlled.lahmia",
    "mechanic.lahmian-seduction": "seduction.controlled.lahmian",
}
LAHMIA_SEDUCTION_RESOURCE = "seduction.controlled.lahmia"


def select_shadow_dance(fighter, current, decisions, *, key):
    """Apply one learned dance for this combat phase, remembering only the last."""
    available = [dance for dance in SHADOW_DANCES
        if has_tag(fighter.global_effects, f"dance.{dance}")
        and dance != current.last_shadow_dance]
    if current.condition != Condition.STANDING or current.grappled or current.grappling or not available:
        return fighter, replace(current, last_shadow_dance=None)
    selected = next((dance for dance in available
        if decisions.choose(f"{key}.dance.{dance}", tuple(available))), None)
    if selected is None:
        raise ValueError("a Wardancer must choose an available learned Shadow Dance")
    effect = fighter.global_effects
    if selected == "whirling-death":
        effect = replace(effect, injury_modifier=effect.injury_modifier + 1)
    elif selected == "storm-of-blades":
        effect = replace(effect, attacks_bonus=effect.attacks_bonus + 1)
    elif selected == "the-shadows-coil":
        effect = replace(effect, tags=(*effect.tags, "dance.shadows-coil-active"))
    else:
        effect = replace(effect, tags=(*effect.tags, "dance.woven-mist-active"))
    return replace(fighter, global_effects=effect), replace(current, last_shadow_dance=selected)


def _mutated_phase_fighter(base, current, before, after, *, first_round):
    from .mutations import fighter_for_mutations
    previous = equipment_for_state(fighter_for_mutations(base, before), before, first_round=first_round)
    updated = equipment_for_state(fighter_for_mutations(base, after), after, first_round=first_round)
    # Preserve only already-declared local phase effects around the permanent
    # brand projection. Mutation effects themselves are replayed from the source
    # fighter once; source equipment is re-evaluated from its actual inventory.
    added = tuple(tag for tag in current.global_effects.tags if tag not in previous.global_effects.tags)
    removed = set(previous.global_effects.tags)-set(current.global_effects.tags)
    effect = replace(updated.global_effects,
        tags=tuple(dict.fromkeys(tag for tag in (*updated.global_effects.tags,*added) if tag not in removed)),
        attacks_bonus=updated.global_effects.attacks_bonus+current.global_effects.attacks_bonus-previous.global_effects.attacks_bonus,
        weapon_skill_bonus=updated.global_effects.weapon_skill_bonus+current.global_effects.weapon_skill_bonus-previous.global_effects.weapon_skill_bonus,
        out_of_action_threshold=(current.global_effects.out_of_action_threshold
            if current.global_effects.out_of_action_threshold != previous.global_effects.out_of_action_threshold
            else updated.global_effects.out_of_action_threshold))
    return replace(updated, global_effects=effect)


def _inquisitor_brands(first, second, base_first, base_second, state, dice, decisions):
    from .mutations import apply_brand
    from .contexts import OwnedRollDice
    for owner_first in (True, False):
        owner, target = (first,second) if owner_first else (second,first)
        own = state.first if owner_first else state.second
        victim = state.second if owner_first else state.first
        if (not own.active or not victim.active
                or not has_tag(owner.global_effects,'mechanic.solkan-inquisitor')
                or any(has_tag(target.global_effects,tag) for tag in
                    ('nature.undead','identity.chaos-follower','warband-group.chaotic'))):
            continue
        key=f"round.{state.round_index}.{'first' if owner_first else 'second'}.inquisitor"
        owned=OwnedRollDice(dice,owner,own,decisions)
        if owned.roll(RollRequest(f'{key}.judgement')) == 6:
            result=10*owned.roll(RollRequest(f'{key}.mutation.tens'))+owned.roll(RollRequest(f'{key}.mutation.units'))
            option=next((option for option in owner.mutation_options if option.roll==result),None)
            if option is None:
                raise ValueError(f'Inquisitor requires its complete source D66 mutation chart (missing {result})')
            base=base_second if owner_first else base_first
            changed=apply_brand(base,victim,option,owned,decisions,f'{key}.mutation.{result}')
            target=_mutated_phase_fighter(base,target,victim,changed,first_round=state.round_index==0)
            victim=changed
        own=replace(own,resources_spent=own.resources_spent | owned.state.resources_spent)
        if owner_first:
            first,second=owner,target
            state=replace(state,first=own,second=victim)
        else:
            second,first=owner,target
            state=replace(state,second=own,first=victim)
    return first,second,state


def _burning_bodies(first, second, state, dice, decisions):
    if not state.engaged:
        return state
    for owner_first in (True,False):
        owner,target=(first,second) if owner_first else (second,first)
        own=state.first if owner_first else state.second
        victim=state.second if owner_first else state.first
        if (own.active and victim.condition==Condition.STANDING
                and has_tag(owner.global_effects,'mechanic.burning-body')):
            roll,own=_owned_roll(owner,own,dice,decisions,
                RollRequest(f"round.{state.round_index}.{'first' if owner_first else 'second'}.burning-body"), close_combat=True)
            if roll>=min(4,target.global_effects.caught_fire_threshold):
                victim=replace(victim,on_fire=True)
            state=(replace(state,first=own,second=victim) if owner_first
                   else replace(state,second=own,first=victim))
    return state


def _without_combat(first, second, state, dice, decisions, *, advance=False, outcomes=()):
    label = 'first' if state.first_player_turn else 'second'
    fighter = first if state.first_player_turn else second
    current = getattr(state, label)
    recorded = list(outcomes)
    if has_tag(fighter.global_effects, 'condition.black-hunger-active'):
        current, backlash = _black_hunger(fighter, current, dice,
            f"round.{state.round_index}.{label}.black-hunger", decisions=decisions)
        recorded.extend(backlash)
        current = _force_of_will(fighter, current, dice,
            f"round.{state.round_index}.{label}.force.after-black-hunger", decisions=decisions)
    return CombatRoundResult(replace(state, **{label: current},
        round_index=state.round_index+int(advance)), tuple(recorded))


def resolve_round(
    first: CompiledFighter, second: CompiledFighter, state: DuelState,
    dice: DiceSource, decisions: DecisionPolicy | None = None,
) -> CombatRoundResult:
    """Resolve one complete scalar round through the fixed phase pipeline."""
    decisions = decisions or AlwaysAccept()
    # Massively Built's supplied failed check costs the target its whole next
    # turn, so no optional action of that turn is available either: the printed
    # outcome is not limited to the attack pool.  Read that pending fact once,
    # before any own-turn action is resolved; the state itself stays set until
    # the attack step spends it, so every consumer below sees the same fact.
    lost_turn = (state.first.massively_built_lost_turn if state.first_player_turn
                 else state.second.massively_built_lost_turn)
    # Drenok's Berserker is not the Slayer charging skill: while fighting at
    # zero Wounds it requires a fresh 4+ each subsequent player turn.
    if state.first.active and state.second.active:
        for label, fighter in (('first', first), ('second', second)):
            current = getattr(state, label)
            if current.drenok_fighting and current.wounds > 0:
                state = replace(state, **{label: replace(current, drenok_fighting=False)})
            elif current.drenok_fighting and has_tag(fighter.global_effects, 'mechanic.drenok-berserker'):
                roll, current = _owned_roll(fighter, current, dice, decisions,
                    RollRequest(f'round.{state.round_index}.{label}.drenok-berserker'))
                state = replace(state, **{label: replace(current, drenok_fighting=roll >= 4,
                    condition=Condition.STANDING if roll >= 4 else Condition.OUT)})
        if not state.first.active or not state.second.active:
            return _without_combat(first, second, state, dice, decisions, advance=True)
    compiled_first,compiled_second=first,second
    if state.first.mutations or state.second.mutations:
        from .mutations import fighter_for_mutations
        first=fighter_for_mutations(first,state.first)
        second=fighter_for_mutations(second,state.second)
    for label, fighter in (('first', first), ('second', second)):
        current = getattr(state, label)
        if has_tag(fighter.global_effects, 'mechanic.inconsistency') and current.random_round != state.round_index:
            state = replace(state, **{label: replace(current, random_rolled=frozenset(), random_round=state.round_index)})
    if state.round_index == 0:
        for fighter, target in ((first, state.second), (second, state.first)):
            if has_tag(fighter.global_effects, 'condition.impetuous-charge') and target.condition != Condition.STANDING:
                raise ValueError('A supplied compelled Impetuous charge requires its standing opponent')
    if state.round_index == 0:
        for owner_first, fighter in ((True, first), (False, second)):
            if (has_tag(fighter.global_effects, 'condition.impetuous-charge')
                    and not (lost_turn and owner_first == state.first_player_turn)
                    and decisions.choose(f"round.0.{'first' if owner_first else 'second'}.impetuous-avoid-compulsion", fighter)):
                passed, current = resolve_local_leadership(fighter, state, dice, decisions,
                    f"round.0.{'first' if owner_first else 'second'}.impetuous-release",
                    first=owner_first, opponent=second if owner_first else first, return_state=True)
                state = replace(state, **{'first' if owner_first else 'second': current})
                if passed:
                    fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                        tags=tuple(tag for tag in fighter.global_effects.tags if tag != 'condition.impetuous-charge')))
                    if owner_first: first = fighter
                    else: second = fighter
    if state.round_index > 0:
        for label in ('first','second'):
            current=getattr(state,label)
            if 'poetry-inspiration-active' in current.resources_spent:
                modifiers=dict(current.random_modifiers)
                if 'WS' in modifiers: modifiers['WS']-=1
                current=replace(current,weapon_skill=max(0,current.weapon_skill-1),
                    random_modifiers=tuple(modifiers.items()),
                    resources_spent=current.resources_spent-{'poetry-inspiration-active'})
                state=replace(state,**{label:current})
    # Only already-active individual Command effects are supplied; no casting,
    # issuing Knight, range or group lifecycle is simulated.
    initial_first = (state.first_charged if state.initial_first_player_turn is None
                     else state.initial_first_player_turn)
    for owner_first, fighter in ((True, first), (False, second)):
        effect = fighter.global_effects
        if (state.round_index == 0 and fighter.mounted
                and state.initial_charge_flags[int(not owner_first)]
                and has_tag(effect, "condition.righteous-charge")):
            effect = replace(effect, tags=(*effect.tags, "condition.righteous-charge-active",
                "mechanic.causes-fear", "mechanic.psychology-immunity"))
        if (state.round_index == 0 and has_tag(effect,
                "condition.command.follow-me-mine-pugnacious-ones")):
            effect = replace(effect, tags=(*effect.tags, "condition.command.follow-me-active"))
        if (state.round_index < (2 if initial_first == owner_first else 1)
                and has_tag(effect, "condition.command.art-thou-ready-to-die-fighting")):
            effect = replace(effect, out_of_action_threshold=6)
        if state.round_index == 0 and has_tag(effect,'condition.poetry-inspired'):
            effect=replace(effect,attacks_bonus=effect.attacks_bonus+1)
        if (state.round_index == 0 and has_tag(effect, 'condition.command.raise-our-insignia')):
            effect = replace(effect, tags=(*effect.tags, 'condition.command.raise-our-insignia-active'))
        fighter = replace(fighter, global_effects=effect)
        if owner_first:
            first = fighter
        else:
            second = fighter
    label = "first" if state.first_player_turn else "second"
    fighter = first if state.first_player_turn else second
    from mordheim_combat.modular.contexts import OwnedRollDice
    owned = OwnedRollDice(dice, fighter, getattr(state, label), decisions)
    current = _revenant_recovery(fighter, getattr(state, label), owned,
                                f"round.{state.round_index}.{label}.revenant")
    current = replace(current, resources_spent=current.resources_spent | owned.state.resources_spent)
    current = resolve_alchemist(fighter, current, dice, decisions,
                                f"round.{state.round_index}.{label}")
    state = replace(state, **{label: current})
    if has_tag(fighter.global_effects, 'mechanic.feral-instinct') and current.active:
        passed, current = resolve_local_leadership(fighter, state, dice, decisions,
            f"round.{state.round_index}.{label}.feral-instinct", first=state.first_player_turn,
            opponent=second if state.first_player_turn else first, return_state=True)
        current = replace(current, feral_instinct_failed=not passed)
        state = replace(state, **{label: current})
    for tag, stat, bonus, expiry in (("condition.petru-debilitating", "toughness", -1, 6),
        ("condition.petru-strength", "strength", 1, 1),
        ("condition.petru-resilience", "toughness", 1, 1)):
        if current.active and has_tag(fighter.global_effects, tag) and tag not in current.resources_spent:
            roll, current = _owned_roll(fighter, current, dice, decisions,
                RollRequest(f"round.{state.round_index}.{label}.{tag.removeprefix('condition.')}"))
            if roll == expiry:
                current = replace(current.spend(tag), **{stat: max(1, getattr(current, stat)-bonus)})
                modifier_stat = 'S' if stat == 'strength' else 'T'
                modifiers = dict(current.random_modifiers)
                modifiers[modifier_stat] = modifiers.get(modifier_stat, 0)-bonus
                current = replace(current, random_modifiers=tuple(modifiers.items()))
    if current.active and current.danse_macabre_controlled:
        passed, current = resolve_local_leadership(fighter,
            replace(state, **{label: current}), dice, decisions,
            f"round.{state.round_index}.{label}.danse-macabre", first=state.first_player_turn,
            opponent=second if state.first_player_turn else first, return_state=True)
        current = replace(current, danse_macabre_controlled=not passed)
        if not passed and state.round_index == 0 and state.initial_charge_flags[int(not state.first_player_turn)]:
            charges = list(state.initial_charge_flags)
            charges[int(not state.first_player_turn)] = False
            state = replace(state, first_charged=charges[0], second_charged=charges[1],
                engaged=state.engaged and any(charges), failed_charges=state.failed_charges | {label})
    maximum = fighter.characteristics.wounds + int(has_tag(fighter.global_effects, "skill.monstrous"))
    if (current.active and not lost_turn and not (current.grappled or current.grappling or current.netted)
            and current.wounds < maximum
            and (has_tag(fighter.global_effects, "mechanic.herb-lore")
                 or not state.engaged and has_tag(fighter.global_effects, "mechanic.herb-lore-outside-combat"))
            and decisions.choose(f"round.{state.round_index}.{label}.herb-lore", fighter)):
        roll, current = _owned_roll(fighter, current, dice, decisions,
            RollRequest(f"round.{state.round_index}.{label}.herb-lore"))
        if roll >= 4:
            current = replace(current, wounds=min(maximum, current.wounds+1))
    state = replace(state, **{label: current})
    # The Sermon's self-bonus belongs to the active player's combat phase only.
    sermon_key = f"round.{state.round_index}.rousing-sermon"
    if (current.condition in (phases.Condition.STANDING, phases.Condition.KNOCKED_DOWN)
            and not lost_turn and not (current.grappled or current.grappling or current.netted)
            and has_tag(fighter.global_effects, "mechanic.rousing-sermon")
            and "rousing-sermon" not in current.resources_spent
            and decisions.choose(f"round.{state.round_index}.{label}.rousing-sermon", fighter)):
        current = current.spend("rousing-sermon").spend(sermon_key)
        state = replace(state, **{label: current})
    if sermon_key in current.resources_spent:
        fighter = replace(fighter, global_effects=replace(fighter.global_effects,
            attacks_bonus=fighter.global_effects.attacks_bonus + 1))
        if state.first_player_turn:
            first = fighter
        else:
            second = fighter
    if (current.active and not (current.grappled or current.grappling or current.netted)
            and has_tag(fighter.global_effects, 'mechanic.black-hunger')):
        fighter = replace(fighter, global_effects=replace(fighter.global_effects,
            attacks_bonus=fighter.global_effects.attacks_bonus+1,
            tags=(*fighter.global_effects.tags, 'condition.black-hunger-active')))
        current = current.spend(f'black-hunger-active.{state.round_index}')
        state = replace(state, **{label: current})
        if state.first_player_turn: first = fighter
        else: second = fighter
    first, second = (apply_opponent_leadership(first, second, state),
                     apply_opponent_leadership(second, first, state))
    # Transform belongs to the bearer's own turn and is read before the round's
    # equipment is projected, because entering the form discards equipment in
    # that same turn.  The roll happens whether or not blows are exchanged; only
    # a Transformed bearer in combat is exempt, and the form outlives the turn
    # that rolled it.
    for is_first in (True, False):
        fighter = first if is_first else second
        if not has_tag(fighter.global_effects, "mechanic.bitten-transform"):
            continue
        current = state.first if is_first else state.second
        label = "first" if is_first else "second"
        # Madness prints "Stupidity this turn", so the failure it caused is
        # bounded by the turn that rolled it: the result is dropped here, and
        # with it the one Stupidity failure that the result of 1 caused, so a
        # Madness never bars a later phase.
        madness_this_turn = bool(getattr(current, "bitten_result", 0) == 1)
        current = replace(current, bitten_result=0,
            stupidity_failed=current.stupidity_failed and not madness_this_turn)
        if is_first == state.first_player_turn and not (current.transformed and state.engaged):
            roll, current = _owned_roll(fighter, current, dice, decisions,
                RollRequest(f"round.{state.round_index}.{label}.bitten"))
            if roll == 1:
                # Reverting is a result of 1, not an injury: the discarded form
                # stays gone and the equipment it cast off is not recovered.
                current = replace(current, bitten_result=1, transformed=False)
            elif roll == 6:
                current = replace(current, bitten_result=6, transformed=True, equipment_cast_off=True)
            else:
                current = replace(current, bitten_result=roll)
        # A Transformed Bitten keeps the Frenzy the form prints; the form is lost
        # only to the printed result of 1.
        surviving_effects = (fighter.global_effects_without_equipment if current.equipment_cast_off
                             else fighter.global_effects)
        current = replace(current, frenzy=surviving_effects.frenzy or current.transformed)
        if current.transformed:
            # "suffer no penalties for fighting unarmed" is the penalty-removal
            # the attack pool already consumes; it lasts exactly as long as the
            # form does and never forces the fists on a retained dagger.
            fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                tags=(*fighter.global_effects.tags, "rule.unarmed-without-penalties")))
        state = replace(state, **{"first" if is_first else "second": current})
        if is_first:
            first = fighter
        else:
            second = fighter
    # Lunatics prints EACH turn, so the producer runs every player turn.
    # Preserve the recovered consumer's accumulated Frenzy/Stupidity state;
    # duration/stacking is still an explicit open source question, not a
    # settled interpretation inferred from these compatibility checks.
    # This profile's own grants are not cancelled by its Psychology immunity;
    # ordinary Frenzy still skips Stupidity while held.
    for is_first in (True, False):
        fighter = first if is_first else second
        if not has_tag(fighter.global_effects, "mechanic.lunatics"):
            continue
        label = "first" if is_first else "second"
        current = state.first if is_first else state.second
        roll, current = _owned_roll(fighter, current, dice, decisions,
            RollRequest(f"round.{state.round_index}.{label}.lunatics"))
        current = replace(current, lunatic_result=roll,
            frenzy=current.frenzy or roll <= 3,
            lunatic_stupidity=current.lunatic_stupidity or roll >= 4)
        state = replace(state, **{label: current})
    first_state = replace(state.first, fear_hit_sixes=False)
    second_state = replace(state.second, fear_hit_sixes=False)
    if has_tag(first.global_effects_without_equipment if first_state.equipment_cast_off else first.global_effects, 'mechanic.persistent-frenzy'):
        first_state = replace(first_state, frenzy=True)
    if has_tag(second.global_effects_without_equipment if second_state.equipment_cast_off else second.global_effects, 'mechanic.persistent-frenzy'):
        second_state = replace(second_state, frenzy=True)
    original_first, original_second = first, second
    outcomes: list[AttackOutcome] = []
    first_round = state.round_index == 0
    first_misses = second_misses = False
    if not first_round:
        first_state = _refresh_random_characteristics(
            first, first_state, dice, f"round.{state.round_index}.first", decisions
        )
        second_state = _refresh_random_characteristics(
            second, second_state, dice, f"round.{state.round_index}.second", decisions
        )
    first = equipment_for_state(first, first_state, first_round=first_round)
    second = equipment_for_state(second, second_state, first_round=first_round)
    # Equipment that is gone takes its numeric bonuses with it, so a Wound an
    # item folded into the profile cannot exceed the surviving maximum.
    first_state = replace(first_state, wounds=min(first_state.wounds, maximum_wounds(first)))
    second_state = replace(second_state, wounds=min(second_state.wounds, maximum_wounds(second)))
    for owner_first, fighter in ((True, first), (False, second)):
        current = first_state if owner_first else second_state
        if current.equipment_cast_off:
            active = f'black-hunger-active.{state.round_index}' in current.resources_spent
            sermon = sermon_key in current.resources_spent
            inspiration = state.round_index == 0 and has_tag(fighter.global_effects,'condition.poetry-inspired')
            if active or sermon or inspiration:
                fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                    attacks_bonus=fighter.global_effects.attacks_bonus+int(active)+int(sermon)+int(inspiration),
                    tags=(*fighter.global_effects.tags, *(('condition.black-hunger-active',) if active else ()))))
            fighter = apply_opponent_leadership(fighter, second if owner_first else first, state)
            if owner_first: first = fighter
            else: second = fighter
    if not first_round:
        first_state = _force_of_will(first, first_state, dice, f"round.{state.round_index}.first.force", sustain=True, decisions=decisions)
        second_state = _force_of_will(second, second_state, dice, f"round.{state.round_index}.second.force", sustain=True, decisions=decisions)
        if state.first_player_turn:
            first_state, second_state, fire = _fire_recovery(
                first, second, first_state, second_state, dice, f"round.{state.round_index}.first.fire", decisions=decisions)
        else:
            second_state, first_state, fire = _fire_recovery(
                second, first, second_state, first_state, dice, f"round.{state.round_index}.second.fire", decisions=decisions)
        outcomes.extend(fire)
    for owner_first, fighter in ((True, first), (False, second)):
        current = first_state if owner_first else second_state
        if owner_first != state.first_player_turn or current.condition != Condition.PARALYZED:
            continue
        current = require_characteristics(fighter, current, dice,
            f"round.{state.round_index}.{'first' if owner_first else 'second'}", ('T',), decisions)
        owned = OwnedRollDice(dice, fighter, current, decisions)
        recovered = _characteristic_test(current.toughness, owned,
            f"round.{state.round_index}.{'first' if owner_first else 'second'}.paralysis",
            reroll=phases.has_tag(fighter.global_effects, 'skill.blessed-sight'))
        current = replace(current, resources_spent=current.resources_spent | owned.state.resources_spent,
            condition=Condition.STANDING if recovered else current.condition)
        if owner_first: first_state = current
        else: second_state = current
    # Cutting free is the supplied Netter victim's own recovery, not a new shot.
    # A stunned victim first recovers to Knocked Down and stays caught this turn.
    freed_from_net = set()
    for owner_first in (True, False):
        current = first_state if owner_first else second_state
        if (owner_first == state.first_player_turn and current.netted
                and current.condition in (Condition.STANDING, Condition.KNOCKED_DOWN)):
            current = replace(current, netted=False, condition=Condition.KNOCKED_DOWN)
            freed_from_net.add(owner_first)
            if owner_first: first_state = current
            else: second_state = current
    first_state, first_stood = _start_round_state(first, first_state, recover=state.first_player_turn)
    second_state, second_stood = _start_round_state(second, second_state, recover=not state.first_player_turn)
    for owner_first, fighter in ((True, first), (False, second)):
        current = first_state if owner_first else second_state
        if not has_tag(fighter.global_effects, 'mechanic.djinns-curse'):
            continue
        if owner_first == state.first_player_turn:
            selected = None
            if (not lost_turn and current.condition == Condition.STANDING
                    and owner_first not in freed_from_net
                    and not (current.grappled or current.grappling)):
                selected = next((power for power in ('curse', 'luck')
                    if power != current.last_djinn_power and decisions.choose(
                        f"round.{state.round_index}.{'first' if owner_first else 'second'}.djinn-power.{power}", fighter)), None)
            current = replace(current, djinn_power=selected, last_djinn_power=selected)
        if current.djinn_power:
            fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                tags=(*fighter.global_effects.tags, f'condition.djinns-{current.djinn_power}-active')))
        if owner_first: first, first_state = fighter, current
        else: second, second_state = fighter, current
    for holder_first, holder in ((True, first), (False, second)):
        own = first_state if holder_first else second_state
        victim = second_state if holder_first else first_state
        target = second if holder_first else first
        if not state.engaged or not own.grappling or not victim.grappled:
            continue
        released = own.condition != Condition.STANDING or not victim.active
        if not released:
            key = f"round.{state.round_index}.{'second' if holder_first else 'first'}.grapple-escape"
            victim = require_characteristics(target, victim, dice, key, ('S',), decisions)
            owned = OwnedRollDice(dice, target, victim, decisions, close_combat=True)
            released = _characteristic_test(victim.strength-2, owned, key, six_fails=False,
                reroll=has_tag(target.global_effects, 'skill.blessed-sight'))
            victim = replace(victim, resources_spent=victim.resources_spent | owned.state.resources_spent)
        if released:
            own, victim = replace(own, grappling=False), replace(victim, grappled=False)
        if holder_first: first_state, second_state = own, victim
        else: second_state, first_state = own, victim
    # Drunken results apply only during the Centigor player's current turn.
    if first_state.drunken_result and not state.first_player_turn:
        first_state = replace(first_state, drunken_result=0, stupidity_failed=False, frenzy=first.global_effects.frenzy)
    if second_state.drunken_result and state.first_player_turn:
        second_state = replace(second_state, drunken_result=0, stupidity_failed=False, frenzy=second.global_effects.frenzy)
    if has_tag(first.global_effects, "mechanic.centigor-drunken") and state.first_player_turn:
        roll, first_state = _owned_roll(first, first_state, dice, decisions,
            RollRequest(f"round.{state.round_index}.first.drunken"))
        first_state = replace(first_state, drunken_result=roll, frenzy=roll == 6, stupidity_failed=False)
    if has_tag(second.global_effects, "mechanic.centigor-drunken") and not state.first_player_turn:
        roll, second_state = _owned_roll(second, second_state, dice, decisions,
            RollRequest(f"round.{state.round_index}.second.drunken"))
        second_state = replace(second_state, drunken_result=roll, frenzy=roll == 6, stupidity_failed=False)
    for is_first in (True, False):
        current = first_state if is_first else second_state
        fighter = first if is_first else second
        if current.drunken_result in (1, 6):
            tags = (*fighter.global_effects.tags, "mechanic.psychology-immunity")
            if current.drunken_result == 1:
                tags += ("mechanic.stupidity",)
            fighter = replace(fighter, global_effects=replace(fighter.global_effects, tags=tags))
            if is_first:
                first = fighter
            else:
                second = fighter
        # Madness is a this-turn Stupidity, granted to the bearer of the result
        # and to no other Psychology consequence.
        if bool(getattr(current, "bitten_result", 0) == 1):
            fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                tags=(*fighter.global_effects.tags, "mechanic.stupidity")))
            if is_first:
                first = fighter
            else:
                second = fighter
    # Devoted to the Vampire re-reads the supplied condition of the Lahmian
    # Vampire its recipient follows every combat phase.  Its Frenzy is therefore
    # the only Frenzy that ends by itself: when she stands up, and when her
    # killer dies.  It is never confused with a permanent or rolled Frenzy.
    for is_first in (True, False):
        fighter = first if is_first else second
        if not has_tag(fighter.global_effects, "mechanic.devoted-to-the-vampire"):
            continue
        current = first_state if is_first else second_state
        killer = second_state if is_first else first_state
        avenging = (has_tag(fighter.global_effects, "condition.devoted-vampire-killed")
                    and killer.condition != Condition.OUT)
        caused = avenging or has_tag(fighter.global_effects, "condition.devoted-vampire-down")
        if caused:
            current = replace(current, frenzy=True, devoted_frenzy=True)
        elif current.devoted_frenzy:
            current = replace(current, frenzy=fighter.global_effects.frenzy, devoted_frenzy=False)
        if avenging:
            fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                tags=(*fighter.global_effects.tags, "condition.devoted-killer-hatred")))
        if is_first:
            first, first_state = fighter, current
        else:
            second, second_state = fighter, current
    for is_first, fighter in ((True, first), (False, second)):
        current = first_state if is_first else second_state
        failed = False
        if (is_first == state.first_player_turn and current.condition == Condition.STANDING
                and any(has_tag(fighter.global_effects, tag) for tag in ANIMOSITY_SOURCES)):
            label = "first" if is_first else "second"
            # The Fungus Brew's Rowdy result widens the printed own-turn band to
            # 1-2; the ordinary goblin squabble still fails on a 1 only.
            threshold = 2 if has_tag(fighter.global_effects, "mechanic.fungus-rowdy") else 1
            roll, current = _owned_roll(fighter, current, dice, decisions,
                RollRequest(f"round.{state.round_index}.{label}.animosity"))
            failed = roll <= threshold
        current = replace(current, animosity_failed=failed)
        if is_first:
            first_state = current
        else:
            second_state = current
    state = resolve_stupidity(first, second, replace(state, first=first_state, second=second_state), dice, decisions)
    first_state, second_state = state.first, state.second
    if not state.engaged:
        return _without_combat(first, second, state, dice, decisions, advance=True, outcomes=outcomes)
    if first_round:
        state = resolve_fear(first, second, replace(state, first=first_state, second=second_state), dice, decisions)
        first_state, second_state = state.first, state.second
        if not state.engaged:
            return _without_combat(first, second, state, dice, decisions, advance=True, outcomes=outcomes)
        # Raise Our Insignia expires at the Shooting boundary, after the
        # supplied Recovery/Movement tests and before this phase's melee.
        first = replace(first, global_effects=replace(first.global_effects,
            tags=tuple(tag for tag in first.global_effects.tags
                       if tag != 'condition.command.raise-our-insignia-active')))
        second = replace(second, global_effects=replace(second.global_effects,
            tags=tuple(tag for tag in second.global_effects.tags
                       if tag != 'condition.command.raise-our-insignia-active')))
        second_misses, state = resolve_crude_belch(first, second, state, dice, decisions, first=True)
        first_misses, state = resolve_crude_belch(second, first, state, dice, decisions, first=False)
        first_state, second_state = state.first, state.second
    first,second,state=_inquisitor_brands(first,second,compiled_first,compiled_second,
        replace(state,first=first_state,second=second_state),dice,decisions)
    first_state,second_state=state.first,state.second
    from .mutations import select_mutation_tail
    for owner_first,base in ((True,compiled_first),(False,compiled_second)):
        current=first_state if owner_first else second_state
        fighter=first if owner_first else second
        if (current.mutations and current.condition==Condition.STANDING
                and not (current.grappled or current.grappling or current.stupidity_failed)):
            selected=select_mutation_tail(base,current,decisions,
                f"round.{state.round_index}.{'first' if owner_first else 'second'}.mutation")
            fighter=_mutated_phase_fighter(base,fighter,current,selected,first_round=first_round)
            if owner_first: first,first_state=fighter,selected
            else: second,second_state=fighter,selected
    original_first,original_second=first,second
    for owner_first, fighter in ((True, first), (False, second)):
        off = fighter.off_hand
        if (not state.engaged or off is None or not has_tag(off, 'weapon.main-gauche')
                or not has_tag(fighter.global_effects, 'mechanic.main-gauche-modes')):
            continue
        parry = decisions.choose(f"round.{state.round_index}.{'first' if owner_first else 'second'}.main-gauche-parry", fighter)
        clean = fighter.off_hand_without_poison or off
        if not parry:
            off = replace(off, parry=False, tags=(*off.tags, 'weapon.dagger'), target_armour_bonus=1)
            clean = replace(clean, parry=False, tags=(*clean.tags, 'weapon.dagger'), target_armour_bonus=1)
        fighter = replace(fighter, off_hand=off, off_hand_without_poison=clean, off_hand_attacks=not parry)
        if owner_first: first = fighter
        else: second = fighter
    # The Dark Jester's Confound and Confuse: the printed chooser names one
    # trick per combat turn, so each of the three printed tricks is offered and
    # the first accepted selection lights exactly its own slot.  The shared
    # selection condition ("one trick per round") is the trick record's own
    # fact, supplied by the trick rules themselves, never a simulated
    # subsystem; a bearer that accepts no offer keeps every slot dark.
    for is_first in (True, False):
        fighter = first if is_first else second
        if not state.engaged or not has_tag(fighter.global_effects, "mechanic.confound-and-confuse"):
            continue
        label = "first" if is_first else "second"
        current = first_state if is_first else second_state
        if current.grappled or current.grappling:
            continue
        accepted = []
        for slot in JESTER_TRICK_STATES:
            if decisions.choose(f"round.{state.round_index}.{label}.jester-trick.{slot}", fighter):
                accepted.append(slot)
                break
        current = replace(current, resources_spent=current.resources_spent - {"jester.trip"},
            **{slot: slot in accepted for slot in JESTER_TRICK_STATES})
        if is_first: first_state = current
        else: second_state = current
    if state.engaged:
        first, first_state = select_shadow_dance(first, first_state, decisions,
            key=f"round.{state.round_index}.first")
        second, second_state = select_shadow_dance(second, second_state, decisions,
            key=f"round.{state.round_index}.second")
    first_loss = second_loss = 0
    for owner, target, owner_first in ((first, second, True), (second, first, False)):
        own = first_state if owner_first else second_state
        enemy = second_state if owner_first else first_state
        label = 'first' if owner_first else 'second'
        context = state.context
        contacting = state.engaged
        if context is not None and context.facts.contacts is not None:
            contacting = any(set(pair) == {context.facts.first_id, context.facts.second_id}
                             for pair in context.facts.contacts)
        if (contacting and own.condition == Condition.STANDING and not own.stupidity_failed
                and not (own.grappled or own.grappling) and enemy.active):
            shanty = next((tag for tag in ("mechanic.sea-shanty", "mechanic.sea-shanty-psychology")
                           if has_tag(owner.global_effects, tag)), None)
            excluded = (shanty == "mechanic.sea-shanty" and any(has_tag(target.global_effects, tag)
                for tag in ("nature.undead", "nature.possessed", "nature.daemon", "nature.construct", "nature.non-living")))
            excluded = excluded or (shanty == "mechanic.sea-shanty-psychology"
                and (enemy.frenzy or has_tag(target.global_effects, "mechanic.psychology-immunity")))
            own_shanty_phase = shanty != 'mechanic.sea-shanty' or owner_first == state.first_player_turn
            lost_owner_turn = lost_turn and owner_first == state.first_player_turn
            if (shanty and own_shanty_phase and not lost_owner_turn and not excluded
                    and decisions.choose(f"round.{state.round_index}.{label}.sea-shanty", owner)):
                passed, enemy = resolve_local_leadership(target,
                    replace(state, first=first_state if owner_first else enemy,
                            second=enemy if owner_first else second_state), dice, decisions,
                    f"round.{state.round_index}.{label}.sea-shanty.leadership",
                    first=not owner_first, opponent=owner, return_state=True, close_combat=True)
                if not passed:
                    if owner_first: second_loss += 1
                    else: first_loss += 1
            if (has_tag(owner.global_effects, "mechanic.crude-belch-ogre")
                    and "crude-belch-ogre" not in own.resources_spent and not lost_owner_turn
                    and decisions.choose(f"round.{state.round_index}.{label}.crude-belch-ogre", owner)):
                own = own.spend("crude-belch-ogre")
                passed, enemy = resolve_local_leadership(target,
                    replace(state, first=first_state if owner_first else enemy,
                            second=enemy if owner_first else second_state), dice, decisions,
                    f"round.{state.round_index}.{label}.crude-belch-ogre.leadership",
                    first=not owner_first, opponent=owner, return_state=True, close_combat=True)
                if not passed:
                    target = replace(target, global_effects=replace(target.global_effects,
                        hit_modifier=target.global_effects.hit_modifier-1))
        if owner_first:
            first_state, second_state, second = own, enemy, target
        else:
            second_state, first_state, first = own, enemy, target
    # Both dances act from the same combat-start snapshot; defence remains available.
    for owner, target, target_first in ((first, second, False), (second, first, True)):
        current = first_state if target_first else second_state
        owner_state = second_state if target_first else first_state
        blocked = False
        if (owner_state.condition == Condition.STANDING and not owner_state.stupidity_failed
                and not (owner_state.grappled or owner_state.grappling)
                and current.condition == Condition.STANDING
                and has_tag(owner.global_effects, "mechanic.mesmerising-dance")
                and not any(has_tag(target.global_effects, tag) for tag in
                    ("nature.undead", "species.lizardman", "mechanic.charm-immunity"))):
            passed, current = resolve_local_leadership(target,
                replace(state, first=current if target_first else first_state,
                    second=second_state if target_first else current), dice, decisions,
                f"round.{state.round_index}.{'first' if target_first else 'second'}.mesmerising-dance",
                first=target_first, opponent=owner, return_state=True, close_combat=True)
            blocked = not passed
        if (has_tag(owner.global_effects, "mechanic.beauty-of-the-sea")
                and has_tag(target.global_effects, "sex.male")
                and not has_tag(target.global_effects, "species.animal")
                and state.initial_charge_flags[int(target_first)]
                and "beauty.passed" not in current.resources_spent
                and current.condition == Condition.STANDING and owner_state.active):
            passed, current = resolve_local_leadership(target,
                replace(state, first=current if target_first else first_state,
                    second=second_state if target_first else current), dice, decisions,
                f"round.{state.round_index}.{'first' if target_first else 'second'}.beauty",
                first=target_first, psychology=True, opponent=owner, return_state=True, close_combat=True)
            if passed:
                current = current.spend("beauty.passed")
            else:
                blocked = True
        # This is an attack restriction, not Psychology: Undead immunity does
        # not waive it, nor does a successful test persist into another turn.
        if (state.engaged and owner_state.active and current.active
                and current.condition == Condition.STANDING
                and has_tag(owner.global_effects, "defence.eye-pendant")
                and has_tag(target.global_effects, "nature.undead")):
            passed, current = resolve_local_leadership(target,
                replace(state, first=current if target_first else first_state,
                    second=second_state if target_first else current), dice, decisions,
                f"round.{state.round_index}.{'first' if target_first else 'second'}.eye-pendant",
                first=target_first, opponent=owner, return_state=True, close_combat=True)
            blocked = blocked or not passed
        auto_hit = False
        resource = "mark-of-shornaal.passed"
        if (owner_state.condition == Condition.STANDING and not owner_state.stupidity_failed
                and not (owner_state.grappled or owner_state.grappling)
                and current.condition == Condition.STANDING
                and has_tag(owner.global_effects, "mechanic.mark-of-shornaal")
                and resource not in current.resources_spent
                and not has_tag(target.global_effects, "mechanic.charm-immunity")):
            passed, current = resolve_local_leadership(target,
                replace(state, first=current if target_first else first_state,
                    second=second_state if target_first else current), dice, decisions,
                f"round.{state.round_index}.{'first' if target_first else 'second'}.shornaal",
                first=target_first, psychology=True, discard_lowest=True, opponent=owner, return_state=True, close_combat=True)
            if passed:
                current = current.spend(resource)
            else:
                blocked = auto_hit = True
        current = replace(current, charm_attack_blocked=blocked, charm_auto_hit=auto_hit)
        if target_first:
            first_state = current
        else:
            second_state = current
    for owner, target, target_first in ((first, second, False), (second, first, True)):
        current = first_state if target_first else second_state
        owner_state = second_state if target_first else first_state
        owner_label = "second" if target_first else "first"
        if has_tag(owner.global_effects, "mechanic.hypnotist"):
            if current.entranced and not (owner_state.grappled or owner_state.grappling) and decisions.choose(
                    f"round.{state.round_index}.{owner_label}.end-hypnosis", owner):
                current = replace(current, entranced=False)
            if (owner_state.condition == Condition.STANDING and not owner_state.stupidity_failed
                and not (owner_state.grappled or owner_state.grappling)
                    and current.condition == Condition.STANDING and not current.frenzy
                    and not any(has_tag(target.global_effects, tag) for tag in
                        ("nature.undead", "nature.daemon", "mechanic.psychology-immunity", "mechanic.charm-immunity"))
                    and decisions.choose(f"round.{state.round_index}.{owner_label}.hypnotist", target)):
                passed, current = resolve_local_leadership(target,
                    replace(state, first=current if target_first else first_state,
                        second=second_state if target_first else current), dice, decisions,
                    f"round.{state.round_index}.{owner_label}.hypnotist", first=target_first,
                    opponent=owner, return_state=True, close_combat=True)
                current = replace(current, entranced=not passed)
            if target_first:
                first_state = current
            else:
                second_state = current
    # Tranquil Fauna prevents attacks, never the charge or established contact.
    for owner, target, target_first in ((first, second, False), (second, first, True)):
        current = first_state if target_first else second_state
        own = second_state if target_first else first_state
        if (own.active and current.condition == Condition.STANDING
                and has_tag(owner.global_effects, "mechanic.taal-tranquil-fauna")
                and has_tag(target.global_effects, "species.animal")):
            conditional = any(has_tag(target.global_effects, tag) for tag in
                ("fauna-animal.handled", "fauna-animal.large-predator"))
            ordinary = has_tag(target.global_effects, "fauna-animal.ordinary") or has_tag(target.global_effects, "species.normal-animal")
            if not conditional and not ordinary:
                raise ValueError("Tranquil Fauna requires the animal's explicit ordinary/handled/large-predator qualification")
            blocked = True
            if conditional:
                if target.animal_handler_leadership is None:
                    raise ValueError("Tranquil Fauna requires the qualified Animal Handler's Leadership")
                # Only the qualified handler's supplied value belongs to this test;
                # do not borrow a nearby leader or the animal's Psychology exemptions.
                passed = phases.resolve_leadership(target.animal_handler_leadership, dice,
                    f"round.{state.round_index}.{'first' if target_first else 'second'}.tranquil-fauna")
                blocked = not passed
            current = replace(current, charm_attack_blocked=current.charm_attack_blocked or blocked)
        if target_first:
            first_state = current
        else:
            second_state = current
    # The Lahmia powers act once per turn, which one combat phase satisfies; the
    # duel has a single opponent, so the printed "may attack another model in
    # base contact" remainder has no second target to name and is recorded
    # rather than simulated.
    hypnotized = [False, False]
    for power, exclusions, name, own_only in LAHMIA_POWERS:
        for target_first in (False, True):
            owner = second if target_first else first
            target = first if target_first else second
            if not has_tag(owner.global_effects, power):
                continue
            current = first_state if target_first else second_state
            owner_state = second_state if target_first else first_state
            label = "first" if target_first else "second"
            if (owner_state.condition != Condition.STANDING or owner_state.stupidity_failed
                    or owner_state.grappled or owner_state.grappling
                    or current.condition != Condition.STANDING):
                continue
            if any(has_tag(target.global_effects, tag) for tag in exclusions):
                continue
            if not decisions.choose(f"round.{state.round_index}.{label}.{name}", target):
                continue
            if own_only:
                passed, current = resolve_local_leadership(target,
                    replace(state, first=current if target_first else first_state,
                        second=second_state if target_first else current), dice, decisions,
                    f"round.{state.round_index}.{label}.{name}", first=target_first,
                    psychology=True, return_state=True, own_value_only=True, opponent=owner, close_combat=True)
            else:
                passed, current = resolve_local_leadership(target,
                    replace(state, first=current if target_first else first_state,
                        second=second_state if target_first else current), dice, decisions,
                    f"round.{state.round_index}.{label}.{name}", first=target_first,
                    psychology=True, return_state=True, close_combat=True)
            if not passed:
                current = replace(current, charm_attack_blocked=True)
                if power == "mechanic.lahmian-hypnotize":
                    # Index 0 is the first participant: the target is first
                    # exactly when it was tested as such.
                    hypnotized[0 if target_first else 1] = True
            # The test's own consumption (a carried relic, a first-failure
            # reroll) must persist on the success path too, so the returned state
            # is stored whether the power passed or failed.
            if target_first:
                first_state = current
            else:
                second_state = current

    def _store(target_is_first, updated):
        """Store one participant's updated state beside its sibling."""
        return ((updated, second_state) if target_is_first
                else (first_state, updated))

    # Hypnotic Gaze and the two Seduction copies.  The gaze bars the target for
    # the phase and makes every attack against it hit automatically; each
    # Seduction establishes a lasting control that the victim's own Recovery
    # phase may end and that the printed attack releases (see the release below
    # the attack resolution).
    for power in CONTROL_POWERS:
        for target_first in (False, True):
            owner = second if target_first else first
            target = first if target_first else second
            if not has_tag(owner.global_effects, power.tag):
                continue
            current = first_state if target_first else second_state
            owner_state = second_state if target_first else first_state
            label = "first" if target_first else "second"
            key = f"round.{state.round_index}.{label}.{power.name}"
            controlled = bool(current.resources_spent.intersection(SEDUCTION_RESOURCES))
            if any(has_tag(target.global_effects, tag) for tag in power.exclusions):
                # The printed exemption also ends a control this clause could not
                # have established on such a model.
                if controlled:
                    current = replace(current, resources_spent=(
                        current.resources_spent - set(SEDUCTION_RESOURCES)))
                first_state, second_state = _store(target_first, current)
                continue
            if controlled:
                if (state.first_player_turn == target_first
                        and current.condition == Condition.STANDING
                        and decisions.choose(f"{key}.regain-control", target)):
                    # Printed Recovery phase: the warrior's own turn offers its
                    # owner the Leadership test that throws the control off.
                    passed, current = resolve_local_leadership(target,
                        replace(state, first=current if target_first else first_state,
                            second=second_state if target_first else current),
                        dice, decisions, f"{key}.regain-control", first=target_first,
                        opponent=owner, return_state=True)
                    if passed:
                        current = replace(current, resources_spent=(
                            current.resources_spent - set(SEDUCTION_RESOURCES)))
                        controlled = False
                if controlled:
                    # A controlled warrior strikes nobody while the control
                    # holds; the printed bar is re-derived here because the charm
                    # flag is reset with each phase.
                    current = replace(current, charm_attack_blocked=True)
            if (owner_state.condition != Condition.STANDING or owner_state.stupidity_failed
                    or owner_state.grappled or owner_state.grappling
                    or current.condition != Condition.STANDING
                    or controlled
                    or (power.own_turn_only
                        and state.first_player_turn != (not target_first))):
                first_state, second_state = _store(target_first, current)
                continue
            if power.male_only:
                # Printed "one male enemy": the fact is supplied, never inferred
                # from the profile or the warband.
                if not any(has_tag(target.global_effects, tag)
                           for tag in ("sex.male", "sex.female")):
                    raise ValueError(
                        "Lahmia Seduction requires the opponent's explicit male/female fact")
                if not has_tag(target.global_effects, "sex.male"):
                    first_state, second_state = _store(target_first, current)
                    continue
            if power.own_test:
                # The Khemrian copy prints the Vampire's own Leadership test
                # before her choice, so a failure leaves the victim alone.
                owner_label = "first" if not target_first else "second"
                passed, owner_state = resolve_local_leadership(owner,
                    replace(state, first=current if target_first else owner_state,
                        second=owner_state if target_first else current),
                    dice, decisions,
                    f"round.{state.round_index}.{owner_label}.{power.name}.own-test",
                    first=not target_first, opponent=target, return_state=True, close_combat=True)
                first_state, second_state = (
                    (first_state, owner_state) if target_first
                    else (owner_state, second_state))
                if not passed:
                    continue
            if not decisions.choose(key, target):
                continue
            passed, current = resolve_local_leadership(target,
                replace(state, first=current if target_first else first_state,
                    second=second_state if target_first else current), dice, decisions,
                key, first=target_first, psychology=True,
                opponent=owner, return_state=True, close_combat=True)
            if not passed:
                current = replace(current, charm_attack_blocked=True,
                    charm_auto_hit=current.charm_auto_hit or power.auto_hit)
                if power.persistent:
                    current = replace(current, resources_spent=(
                        current.resources_spent | {CONTROL_RESOURCES[power.tag]}))
            first_state, second_state = _store(target_first, current)
    for index, target in enumerate((first, second)):
        if hypnotized[index]:
            # Every attack directed against the hypnotized model gains +1 To Hit
            # for the rest of that turn.
            tagged = replace(target.global_effects,
                tags=(*target.global_effects.tags, "condition.hypnotized"))
            if index:
                second = replace(second, global_effects=tagged)
            else:
                first = replace(first, global_effects=tagged)
    first_charged, second_charged = state.initial_charge_flags
    first_charging = first_round and first_charged
    second_charging = first_round and second_charged
    # Keep incoming charge provenance separate from the duelist's own charge.
    for side, charged in (("first", second_charging), ("second", first_charging)):
        fighter = first if side == "first" else second
        if charged:
            fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                tags=(*fighter.global_effects.tags, "condition.being-charged")))
        if side == "first":
            first = fighter
        else:
            second = fighter
    # Netter's shot/failed-movement producer is outside this duel. A caught
    # victim enters through the supplied condition.netted recovery route.
    # A Wheelo's collision is resolved before crew and enemy weapon blows.
    for owner, target, owner_first, charging in (
            (first, second, True, first_charging), (second, first, False, second_charging)):
        own = first_state if owner_first else second_state
        other = second_state if owner_first else first_state
        counter = (first_round and (second_charging if owner_first else first_charging)
                   and has_tag(owner.global_effects, "wheelo.fitting.spear"))
        if not ((charging or counter) and own.active and other.active and not own.charm_attack_blocked
                and has_tag(owner.global_effects, "mechanic.wheelo-impact")):
            continue
        label = "first" if owner_first else "second"
        count = 1
        if charging:
            roll, own = _owned_roll(owner, own, dice, decisions,
                RollRequest(f"round.0.{label}.impact-count"), close_combat=True)
            count = (roll+1)//2
        morning_star = (has_tag(owner.global_effects, "wheelo.fitting.morning-star")
                        and "wheelo.first-impact" not in own.resources_spent)
        own = replace(own, resources_spent=own.resources_spent | {"wheelo.first-impact"})
        collision = replace(owner, global_effects=EffectSet())
        weapon = EffectSet(fixed_strength=5 if morning_star else 4, automatic_hit=True,
            cannot_be_parried=True,
            armour_penetration=int(has_tag(owner.global_effects, "wheelo.fitting.axe")),
            concussion=has_tag(owner.global_effects, "wheelo.fitting.club"))
        from mordheim_combat.modular.aftermath import _react_to_wound
        for index in range(count):
            if not own.active or not other.active:
                break
            key = f"round.0.{label}.impact.{index}"
            result = resolve_reference_attack(collision, target, own, other, weapon, dice,
                key=key, melee_attack=False, decisions=decisions)
            result = _react_to_wound(owner, target, result, dice, key, decisions=decisions)
            own, other = result.attacker, result.defender
            outcomes.append(result)
        if owner_first:
            first_state, second_state = own, other
        else:
            second_state, first_state = own, other
    # Mantle of Crows (the Crow Master) opens each combat phase: every enemy in
    # base contact - in this 1v1 duel, the single opponent - suffers one
    # automatic Strength 2 hit before any blows are struck, with no to-hit
    # roll. This is a hand-to-hand hit, so contact defences and Thin Flesh
    # apply, but the isolated attacker contributes no personal weapon effects.
    for owner, target, target_first in ((first, second, False), (second, first, True)):
        own = second_state if target_first else first_state
        other = first_state if target_first else second_state
        if not (has_tag(owner.global_effects, "mechanic.mantle-of-crows")
                and own.active and other.active):
            continue
        crows = EffectSet(
            tags=("mechanic.mantle-of-crows",),
            fixed_strength=2, automatic_hit=True, cannot_be_parried=True,
        )
        label = "first" if target_first else "second"
        attack_key = f"round.{state.round_index}.{label}.mantle-of-crows"
        # Fixed-strength crows are not the bearer's weapon blows: no personal
        # poison, hit, damage or Strength contribution is inherited.
        crow_attacker = replace(owner, global_effects=EffectSet())
        result = resolve_reference_attack(crow_attacker, target, own, other, crows, dice,
            key=attack_key, decisions=decisions)
        from mordheim_combat.modular.aftermath import _react_to_wound
        result = _react_to_wound(owner, target, result, dice, attack_key, decisions=decisions)
        if target_first:
            second_state = result.attacker
            first_state = result.defender
        else:
            first_state = result.attacker
            second_state = result.defender
        outcomes.append(result)
    # Resolve both Spines attacks from one snapshot.  A simultaneous mutation
    # still retaliates when the opposing Spines hit takes it out of action.
    before_first, before_second = first_state, second_state
    first_state, second_state, first_spines = _spines(
        first, second, before_first, before_second, dice,
        f"round.{state.round_index}.first.spines", decisions=decisions,
    )
    second_spines_owner, first_state, second_spines = _spines(
        second, first, before_second, first_state, dice,
        f"round.{state.round_index}.second.spines", decisions=decisions,
    )
    second_state = replace(second_state, resources_spent=(
        second_state.resources_spent | second_spines_owner.resources_spent))
    outcomes.extend((*first_spines, *second_spines))
    entangle = EffectSet(
        tags=("effect.chained-squig-entangle",), fixed_strength=3,
        automatic_hit=True,
    )
    if first_state.entangled and second_state.condition == Condition.STANDING:
        result = resolve_reference_attack(
            second, first, second_state, first_state, entangle, dice,
            key=f"round.{state.round_index}.first.entangled", decisions=decisions,
        )
        second_state, first_state = result.attacker, result.defender
        outcomes.append(result)
    if second_state.entangled and first_state.condition == Condition.STANDING:
        result = resolve_reference_attack(
            first, second, first_state, second_state, entangle, dice,
            key=f"round.{state.round_index}.second.entangled", decisions=decisions,
        )
        first_state, second_state = result.attacker, result.defender
        outcomes.append(result)
    first_state = _force_of_will(first, first_state, dice, f"round.{state.round_index}.first.force.after-spines", decisions=decisions)
    second_state = _force_of_will(second, second_state, dice, f"round.{state.round_index}.second.force.after-spines", decisions=decisions)

    grapple_selections = {}
    for owner_first, fighter, target in ((True, first, second), (False, second, first)):
        current = first_state if owner_first else second_state
        enemy = second_state if owner_first else first_state
        if has_tag(fighter.global_effects,'condition.mim-no-hand-attacks'):
            grapple_selections[owner_first]=False
            continue
        if (current.condition == Condition.STANDING and enemy.active
                and not (current.on_fire or current.animosity_failed or current.stupidity_failed
                    or current.charm_attack_blocked or current.danse_macabre_controlled
                    or current.grappled or current.grappling)
                and has_tag(fighter.global_effects, 'mechanic.gaoler-grapple')
                and not any(has_tag(target.global_effects, tag) for tag in
                    ('nature.undead', 'nature.daemon', 'mechanic.pain-immunity', 'size.large'))):
            grapple_selections[owner_first] = decisions.choose(
                f"round.{state.round_index}.{'first' if owner_first else 'second'}.torturer-grapple", fighter)
    def grapple_equipment(fighter, owner_first):
        if not grapple_selections.get(owner_first):
            return fighter
        return replace(fighter, main_weapon=EffectSet(tags=('weapon.natural-attacks',)),
            off_hand=None, off_hand_attacks=False, extra_attacks=(), main_hand_slot='natural',
            main_weapon_without_poison=None, off_hand_without_poison=None)
    first_attack_fighter = first if (first_state.stupidity_failed or first_state.grappled or first_state.grappling) else select_attack_replacement(
        first, first_round=first_round, charging=first_charging,
        decisions=decisions, key=f"round.{state.round_index}.first",
    )
    second_attack_fighter = second if (second_state.stupidity_failed or second_state.grappled or second_state.grappling) else select_attack_replacement(
        second, first_round=first_round, charging=second_charging,
        decisions=decisions, key=f"round.{state.round_index}.second",
    )
    first_attack_fighter = grapple_equipment(first_attack_fighter, True)
    second_attack_fighter = grapple_equipment(second_attack_fighter, False)
    # Ferocious Charge prints that the Slayer "may" double his Attacks and
    # "suffers" -1 To Hit that turn.  The doubling is a declaration, so the
    # charge round asks before either half is applied; declining keeps the
    # ordinary pool and to-hit.  Only this round's local copy loses the tag,
    # so the compiled fighter keeps the skill and the choice expires with the
    # charge.
    def declare_ferocious_charge(fighter, charging, label):
        if not (first_round and charging
                and has_tag(fighter.global_effects, "skill.ferocious-charge")):
            return fighter
        if lost_turn and label == ("first" if state.first_player_turn else "second"):
            return fighter
        if decisions.choose(
                f"round.{state.round_index}.{label}.ferocious-charge", fighter):
            return fighter
        return replace(fighter, global_effects=replace(fighter.global_effects,
            tags=tuple(tag for tag in fighter.global_effects.tags
                       if tag != "skill.ferocious-charge")))
    first_attack_fighter = declare_ferocious_charge(
        first_attack_fighter, first_charging, 'first')
    second_attack_fighter = declare_ferocious_charge(
        second_attack_fighter, second_charging, 'second')
    if has_tag(first_attack_fighter.main_weapon, "effect.serpent-staff-power"):
        first_state = replace(first_state, parries_remaining=0)
    if has_tag(second_attack_fighter.main_weapon, "effect.serpent-staff-power"):
        second_state = replace(second_state, parries_remaining=0)
    first_priority = phases.resolve_priority(PriorityContext(
        first_attack_fighter, second, first_round, first_charging, second_charging, first_stood,
        first_state.initiative_penalty,
        initiative_bonus=_initiative_bonus(first_state, first),
        initiative_floor=first_state.initiative_floor,
    ))
    second_priority = phases.resolve_priority(PriorityContext(
        second_attack_fighter, first, first_round, second_charging, first_charging, second_stood,
        second_state.initiative_penalty,
        initiative_bonus=_initiative_bonus(second_state, second),
        initiative_floor=second_state.initiative_floor,
    ))
    eligible = tuple(current.condition == Condition.STANDING and opponent.active
        and not (current.on_fire or current.animosity_failed or current.stupidity_failed or current.grappled or current.grappling
                 or current.charm_attack_blocked or current.danse_macabre_controlled
                 or alchemist_addicted(fighter, current))
        for fighter, current, opponent in ((first, first_state, second_state),
                                         (second, second_state, first_state)))
    if all(eligible) and first_priority.priority == second_priority.priority:
        first_state = require_characteristics(first, first_state, dice,
            f"round.{state.round_index}.first", ('I',), decisions)
        second_state = require_characteristics(second, second_state, dice,
            f"round.{state.round_index}.second", ('I',), decisions)
        first_priority = phases.resolve_priority(PriorityContext(
            first_attack_fighter, second, first_round, first_charging, second_charging, first_stood,
            first_state.initiative_penalty,
            initiative_bonus=_initiative_bonus(first_state, first),
            initiative_floor=first_state.initiative_floor))
        second_priority = phases.resolve_priority(PriorityContext(
            second_attack_fighter, first, first_round, second_charging, first_charging, second_stood,
            second_state.initiative_penalty,
            initiative_bonus=_initiative_bonus(second_state, second),
            initiative_floor=second_state.initiative_floor))
    deferred_electrical_tie = (first_priority == second_priority and any(
        has_tag(fighter.global_effects, 'mechanic.electrical-touch')
        for fighter in (first, second)))
    first_acts = True if deferred_electrical_tie else phases.first_acts_before(
        first_priority, second_priority, dice, key=f"round.{state.round_index}.priority-tie")
    first_count = phases.build_attacks(AttackPoolContext(
        first_attack_fighter, first_round, first_charging, second_charging,
        first_state.frenzy, first_state.wounds < (first_state.starting_wounds or first.characteristics.wounds),
        0, first_state.attacks, state.first_player_turn,
    )).attacks
    second_count = phases.build_attacks(AttackPoolContext(
        second_attack_fighter, first_round, second_charging, first_charging,
        second_state.frenzy, second_state.wounds < (second_state.starting_wounds or second.characteristics.wounds),
        0, second_state.attacks, not state.first_player_turn,
    )).attacks
    for owner_first, fighter, count in ((True, first_attack_fighter, first_count),
                                      (False, second_attack_fighter, second_count)):
        current = first_state if owner_first else second_state
        owned = OwnedRollDice(dice, fighter, current, decisions, close_combat=True)
        count = resolve_spawn_attack_count(fighter, count, owned,
            f"round.{state.round_index}.{'first' if owner_first else 'second'}.spawn-attacks")
        current = replace(current, resources_spent=current.resources_spent | owned.state.resources_spent)
        if owner_first: first_state, first_count = current, count
        else: second_state, second_count = current, count
    first_shifty = (first_round and second_charging and has_tag(first.global_effects, "skill.shifty")
        and not has_tag(first_attack_fighter.main_weapon, "effect.serpent-staff-power"))
    second_shifty = (first_round and first_charging and has_tag(second.global_effects, "skill.shifty")
        and not has_tag(second_attack_fighter.main_weapon, "effect.serpent-staff-power"))
    # Add after Frenzy, before whole-warrior attack reductions. Split off only
    # this one attack below; ordinary attacks retain their original priority.
    if first_shifty and not (has_tag(first_attack_fighter.main_weapon, "weapon.fist")
            and phases.unarmed_attack_cap_applies(first.global_effects)):
        first_count += 1
    if second_shifty and not (has_tag(second_attack_fighter.main_weapon, "weapon.fist")
            and phases.unarmed_attack_cap_applies(second.global_effects)):
        second_count += 1
    first_count = apply_round_weapon_attack_modifiers(
        first, second, first_count, first_round=first_round,
        charging=first_charging, charged=second_charging,
    )
    second_count = apply_round_weapon_attack_modifiers(
        second, first, second_count, first_round=first_round,
        charging=second_charging, charged=first_charging,
    )
    first_count = apply_opponent_attack_modifiers(
        first, second, first_count, first_round=first_round, defer_grapple=True)
    second_count = apply_opponent_attack_modifiers(
        second, first, second_count, first_round=first_round, defer_grapple=True)
    # A source loss removes one ordinary allocation, not every independent
    # natural/companion contribution when the base characteristic reaches zero.
    attack_forfeits = {}
    adjusted = []
    for owner_first, fighter, target, count, loss, charging in (
            (True, first_attack_fighter, second_state, first_count, first_loss, first_charging),
            (False, second_attack_fighter, first_state, second_count, second_loss, second_charging)):
        remaining = max(0, count-loss)
        extra = any(charging or not has_tag(weapon, 'rule.horned-one')
                    for weapon in fighter.extra_attacks)
        extra = extra or (has_tag(fighter.global_effects, 'mechanic.noblesse-stomp')
                          and target.condition == Condition.KNOCKED_DOWN)
        if has_tag(fighter.global_effects,'condition.mim-no-hand-attacks'):
            remaining = max(1,count) if extra else 0
            attack_forfeits['first' if owner_first else 'second'] = tuple(range(max(1,count)))
        elif count == loss == 1 and extra:
            remaining = 1
            attack_forfeits['first' if owner_first else 'second'] = (0,)
        adjusted.append(remaining)
    first_count, second_count = adjusted
    # Massively Built prints that the failed target loses "his entire next turn
    # as he stands dumbfounded".  The one-against-one combat phase models that
    # turn through the attacks it carries, so the supplied pending state spends
    # itself here, on the target's own turn only: its whole contribution is
    # gone for that phase and the state is cleared.  The other player's turn is
    # untouched, so retaliation is never suppressed, and the target is never
    # treated as Stunned or Knocked Down.
    if lost_turn:
        # Spend the supplied outcome once: every own-turn consumer above read
        # the captured fact, and only the attack pool is left to silence.
        if state.first_player_turn:
            first_count = 0
            first_state = replace(first_state, massively_built_lost_turn=False)
        else:
            second_count = 0
            second_state = replace(second_state, massively_built_lost_turn=False)
    # Printed Deathblow reads "the remainder of his attacks": the pool the
    # phase allocated is captured here, before the bearer's own readiness can
    # zero it, so a Slayer taken out of action later in this same phase reuses
    # exactly this allocation instead of deriving a second one.
    deathblow_pool = {'first': first_count, 'second': second_count}
    if first_state.on_fire or first_state.animosity_failed or first_state.stupidity_failed or first_state.charm_attack_blocked or first_state.danse_macabre_controlled or first_state.grappled or first_state.grappling or alchemist_addicted(first, first_state) or first_state.condition != Condition.STANDING:
        first_count = 0
    if second_state.on_fire or second_state.animosity_failed or second_state.stupidity_failed or second_state.charm_attack_blocked or second_state.danse_macabre_controlled or second_state.grappled or second_state.grappling or alchemist_addicted(second, second_state) or second_state.condition != Condition.STANDING:
        second_count = 0
    if grapple_selections.get(True): first_count = min(1, first_count)
    if grapple_selections.get(False): second_count = min(1, second_count)
    first_shifty = first_shifty and first_count > 0 and not grapple_selections.get(True) and not has_tag(first.global_effects,'condition.mim-no-hand-attacks')
    second_shifty = second_shifty and second_count > 0 and not grapple_selections.get(False) and not has_tag(second.global_effects,'condition.mim-no-hand-attacks')
    # The Priest's bite is its own final event, after both warriors' weapon
    # attacks. Ordinary pools exclude this separately scheduled contribution.
    last_attacks = []
    for attacker, defender, is_first, count, label in (
        (first_attack_fighter, second, True, first_count, 'first'),
        (second_attack_fighter, first, False, second_count, 'second'),
    ):
        if count > 0:
            for weapon in attacker.extra_attacks:
                if has_tag(weapon, 'rule.strikes-last-bite'):
                    bite = replace(attacker, main_weapon=weapon, off_hand=None,
                        off_hand_attacks=False, extra_attacks=(), main_hand_slot='natural',
                        main_weapon_without_poison=None, off_hand_without_poison=None)
                    current = first_state if is_first else second_state
                    initiative = _strike_initiative(current, attacker)
                    last_attacks.append((bite, defender, is_first, 1,
                        phases.PriorityResult(-2, initiative), f'{label}.last-bite'))
    events = [
        (first_attack_fighter, second, True, first_count - int(first_shifty), first_priority, 'first'),
        (second_attack_fighter, first, False, second_count - int(second_shifty), second_priority, 'second'),
    ]
    if not first_acts:
        events.reverse()
    for attacker, defender, is_first, count, priority in (
        (first_attack_fighter, second, True, first_count, first_priority),
        (second_attack_fighter, first, False, second_count, second_priority)):
        if (count > 0 and not grapple_selections.get(is_first) and has_tag(attacker.global_effects, "mechanic.noblesse-stomp")
                and not has_tag(attacker.main_weapon, "effect.serpent-staff-power")):
            stomp = replace(attacker, main_weapon=EffectSet(tags=('rule.noblesse-stomp',)),
                off_hand=None, off_hand_attacks=False, extra_attacks=(),
                main_weapon_without_poison=None, off_hand_without_poison=None,
                main_hand_slot='natural')
            index = next(i for i, event in enumerate(events) if event[2] == is_first)
            events.insert(index+1, (stomp, defender, is_first, 1, priority,
                f"{'first' if is_first else 'second'}.stomp"))
    # A charged whip's bonus has its own Strike First timing. Its ordinary
    # attacks retain their own priority and cannot borrow that bonus's tier.
    for owner, charged in ((True, second_charging), (False, first_charging)):
        for index, event in enumerate(events):
            attacker, defender, is_first, count, priority, label = event
            whip = whipcrack_weapon(attacker)
            if is_first != owner or not charged or not count or whip is None:
                continue
            events[index] = (*event[:3], count - 1, priority, label)
            bonus_fighter = replace(attacker, main_weapon=whip, off_hand=None,
                off_hand_attacks=False, extra_attacks=(), main_hand_slot=(
                    attacker.main_hand_slot if whip == attacker.main_weapon else attacker.off_hand_slot))
            bonus_priority = phases.PriorityResult(1, priority.initiative)
            bonus = (bonus_fighter, defender, is_first, 1, bonus_priority, f'{label}.whipcrack')
            position = len(events)
            for candidate_index, candidate in enumerate(events):
                if phases.first_acts_before(bonus_priority, candidate[4], dice,
                        key=f'round.{state.round_index}.{label}.whip-priority-tie'):
                    position = candidate_index
                    break
            events.insert(position, bonus)
            break
    # Ties belong to the two warriors at a given tier/Initiative, not to every
    # event. Reuse the ordinary tie when their bonus attacks share that tier.
    ties = {first_priority: first_acts} if first_priority == second_priority and not deferred_electrical_tie else {}
    # Instinctual Violence: the bearer nominates which of his own allocated
    # attacks takes the Strike First tier.  The offers follow the pool's own
    # allocation -- the printed weapon choice, the Whipcrack bonus and the
    # bearer's independent extra attacks, in the order the pool resolves them --
    # so the nominated strike is a legal attack of a real weapon, keeps that
    # weapon's profile and hand slot, and is never a weapon the pool did not
    # allocate.  Declining every offer leaves the ordinary pool untouched.  The
    # ordinary pool then resolves the very same allocation minus the nominated
    # position: nothing is duplicated, no attack is lost, and the remainder
    # keeps the allocation it was printed with.  Every other attack keeps its
    # printed priority.
    pool_allocations = {}
    for owner_first in (True, False):
        attacker = first_attack_fighter if owner_first else second_attack_fighter
        if not has_tag(attacker.global_effects, "mechanic.nominated-strike-first"):
            continue
        label = 'first' if owner_first else 'second'
        index = next((i for i, event in enumerate(events)
                      if event[2] == owner_first and event[5] == label), None)
        if index is None:
            continue
        event = events[index]
        count = event[3]
        if count <= 0 or grapple_selections.get(owner_first):
            continue
        allocated = pool_attack_weapons(
            attacker, count, first_round=first_round,
            charging=first_charging if owner_first else second_charging,
            decisions=decisions, key=f'round.{state.round_index}.{label}')
        pool_allocations[label] = allocated
        nomination = next((position for position in range(len(allocated)) if decisions.choose(
            f'round.{state.round_index}.{label}.strike-first.attack.{position}', attacker)), None)
        if nomination is None:
            continue
        strike = _strike_first_fighter(attacker, allocated[nomination])
        current = first_state if owner_first else second_state
        strike_priority = phases.PriorityResult(1, _strike_initiative(current, attacker))
        attack_forfeits[label] = (*attack_forfeits.get(label, ()), nomination)
        bonus = (strike, event[1], owner_first, 1, strike_priority, f'{label}.strike-first')
        position = len(events)
        for candidate_index, candidate in enumerate(events):
            candidate_priority = candidate[4]
            if candidate_priority == strike_priority:
                if candidate[2] == owner_first:
                    before = True
                else:
                    if strike_priority not in ties:
                        winner = phases.first_acts_before(strike_priority, candidate_priority, dice,
                            key=f'round.{state.round_index}.{label}.strike-first-priority-tie')
                        ties[strike_priority] = winner if owner_first else not winner
                    before = ties[strike_priority] == owner_first
            else:
                before = phases.priority_order(strike_priority) > phases.priority_order(candidate_priority)
            if before:
                position = candidate_index
                break
        events.insert(position, bonus)
    for attacker, defender, is_first, active, stood, fighter_state in (
        (first, second, True, first_shifty, first_stood, first_state),
        (second, first, False, second_shifty, second_stood, second_state),
    ):
        if not active:
            continue
        label = 'first' if is_first else 'second'
        bonus_fighter = select_shifty_weapon(attacker, decisions, key=f"round.{state.round_index}.{label}.shifty")
        bonus_priority = resolve_priority(PriorityContext(
            bonus_fighter, defender, first_round, first_charging if is_first else second_charging,
            second_charging if is_first else first_charging, stood, fighter_state.initiative_penalty,
            initiative_bonus=_initiative_bonus(fighter_state, attacker),
            initiative_floor=fighter_state.initiative_floor,
        ))
        if bonus_priority.priority >= 0:
            bonus_priority = replace(bonus_priority, priority=max(1, bonus_priority.priority))
        bonus = (bonus_fighter, defender, is_first, 1, bonus_priority, f'{label}.shifty')
        position = len(events)
        for index, candidate in enumerate(events):
            candidate_priority = candidate[4]
            if bonus_priority == candidate_priority:
                if candidate[2] == is_first:
                    before = True
                else:
                    if bonus_priority not in ties:
                        # Whipcrack may already have resolved this exact tie.
                        peer = next((i for i, event in enumerate(events)
                            if event[2] == is_first and event[4] == bonus_priority), None)
                        winner = (peer < index if peer is not None else
                            first_acts_before(bonus_priority, candidate_priority, dice,
                                key=f"round.{state.round_index}.{label}.shifty-priority-tie"))
                        ties[bonus_priority] = winner if is_first else not winner
                    before = ties[bonus_priority] == is_first
            else:
                before = phases.priority_order(bonus_priority) > phases.priority_order(candidate_priority)
            if before:
                position = index
                break
        events.insert(position, bonus)
    # Eagles are separate Strike First weapon contributions directed by their
    # Priestess, not independent combatants or extra copies of her hand weapon.
    for attacker, defender, is_first, count in (
            (first, second, True, first_count), (second, first, False, second_count)):
        if count <= 0 or grapple_selections.get(is_first) or any(has_tag(defender.global_effects, tag) for tag in
                ("mechanic.taal-tranquil-fauna", "mechanic.animal-friendship", "animal_friendship")):
            continue
        current = first_state if is_first else second_state
        priority = phases.PriorityResult(1, _strike_initiative(current, attacker))
        for bird_index, weapon in enumerate(weapon for weapon in attacker.extra_attacks
                                           if has_tag(weapon, "rule.eagle-friend")):
            eagle = replace(attacker, main_weapon=weapon, off_hand=None, off_hand_attacks=False,
                extra_attacks=(), main_hand_slot='companion', main_weapon_without_poison=None,
                off_hand_without_poison=None)
            label = f"{'first' if is_first else 'second'}.eagle.{bird_index}"
            position = len(events)
            for index, candidate in enumerate(events):
                if priority == candidate[4]:
                    if candidate[2] == is_first:
                        before = True
                    else:
                        if priority not in ties:
                            winner = first_acts_before(priority, candidate[4], dice,
                                key=f"round.{state.round_index}.eagle-priority-tie")
                            ties[priority] = winner if is_first else not winner
                        before = ties[priority] == is_first
                else:
                    before = phases.priority_order(priority) > phases.priority_order(candidate[4])
                if before:
                    position = index
                    break
            events.insert(position, (eagle, defender, is_first, 1, priority, label))
    if len(last_attacks) == 2 and not first_acts_before(
            last_attacks[0][4], last_attacks[1][4], dice,
            key=f'round.{state.round_index}.last-bite-priority-tie'):
        last_attacks.reverse()
    events.extend(last_attacks)
    electrical_forfeits = {}
    for owner_first in (True, False):
        current = first_state if owner_first else second_state
        fighter = first if owner_first else second
        target = second if owner_first else first
        if (grapple_selections.get(owner_first) or not has_tag(fighter.global_effects, 'mechanic.electrical-touch')
                or state.round_index < current.electrical_available_at
                or current.condition != Condition.STANDING
                or current.grappled or current.grappling):
            continue
        selected = None
        for index, event in enumerate(events):
            attacker, defender, is_first, count, priority, event_label = event
            if (is_first != owner_first or count <= 0 or attacker.main_hand_slot == 'companion'
                    or event_label.endswith('.stomp') and (second_state if owner_first else first_state).condition != Condition.KNOCKED_DOWN):
                continue
            timed = '.' in event_label
            extra = (sum(not any(has_tag(weapon, tag) for tag in
                    ('rule.strikes-last-bite', 'rule.eagle-friend'))
                    and ((first_charging if owner_first else second_charging)
                         or not has_tag(weapon, 'rule.horned-one'))
                    for weapon in attacker.extra_attacks) if not timed else 0)
            for attack_index in range(count+extra):
                if attack_index in attack_forfeits.get(event_label, ()):
                    continue
                if decisions.choose(f"round.{state.round_index}.{event_label}.electrical-touch.forfeit.{attack_index}", fighter):
                    selected = index, event, attack_index
                    break
            if selected is not None:
                break
        if selected is None:
            continue
        index, event, attack_index = selected
        if '.' in event[5]:
            events[index] = (*event[:3], 0, *event[4:])
        else:
            electrical_forfeits[event[5]] = attack_index
        jolt = replace(fighter, main_weapon=electrical_touch_weapon(target), off_hand=None,
            off_hand_attacks=False, extra_attacks=(), main_hand_slot='natural',
            main_weapon_without_poison=None, off_hand_without_poison=None)
        jolt_priority = resolve_priority(PriorityContext(jolt, target, first_round,
            first_charging if owner_first else second_charging,
            second_charging if owner_first else first_charging,
            first_stood if owner_first else second_stood, current.initiative_penalty,
            initiative_bonus=_initiative_bonus(current, fighter)+1,
            initiative_floor=current.initiative_floor))
        label = f"{'first' if owner_first else 'second'}.electrical-touch"
        position = len(events)
        for index, candidate in enumerate(events):
            if candidate[3] <= 0:
                continue
            if jolt_priority == candidate[4]:
                if candidate[2] == owner_first:
                    before = True
                else:
                    if jolt_priority not in ties:
                        winner = first_acts_before(jolt_priority, candidate[4], dice,
                            key=f"round.{state.round_index}.{label}.priority-tie")
                        ties[jolt_priority] = winner if owner_first else not winner
                    before = ties[jolt_priority] == owner_first
            else:
                before = phases.priority_order(jolt_priority) > phases.priority_order(candidate[4])
            if before:
                position = index
                break
        events.insert(position, (jolt, target, owner_first, 1, jolt_priority, label))
    if deferred_electrical_tie:
        # Only actual remaining contributions need the ordinary tie. Replacing
        # the sole attack with a faster jolt must not roll an unused tie.
        def remaining(event):
            fighter, _, _, count, _, label = event
            if count <= 0:
                return False
            extra = sum(not any(has_tag(weapon, tag) for tag in
                ('rule.strikes-last-bite', 'rule.eagle-friend')) for weapon in fighter.extra_attacks)
            return count+extra > len(set(attack_forfeits.get(label, ())) | ({electrical_forfeits[label]} if label in electrical_forfeits else set()))
        sides = {side: {event[4] for event in events if event[2] == side and remaining(event)}
                 for side in (True, False)}
        for priority in sides[True].intersection(sides[False]):
            if priority not in ties:
                ties[priority] = first_acts_before(priority, priority, dice,
                    key=f"round.{state.round_index}.priority-tie")
        events.sort(key=lambda event: (*phases.priority_order(event[4]),
            int(event[2] == ties.get(event[4], True))), reverse=True)
    already_attacked = {True: False, False: False}
    # A nominated early attack does not exhaust the later ordinary pool.
    # Its allocated slot is already excluded by attack_forfeits below.
    deathblow_active = {True: False, False: False}
    # Seduction's printed release reads the round's own attacks: while a control
    # holds, its victim cannot strike, so the attack that can end it is the
    # Vampire's (see the release below the attack resolution).
    control_attacked = {True: False, False: False}
    control_hits = {True: False, False: False}
    for event_index, (attacker, defender, is_first, count, _, label) in enumerate(events):
        current = first_state if is_first else second_state
        opponent_state = second_state if is_first else first_state
        if (label in ('first', 'second') and has_tag(attacker.global_effects, 'mechanic.inconsistency')
                and current.condition == Condition.STANDING and opponent_state.active
                and not (current.on_fire or current.animosity_failed or current.stupidity_failed
                         or current.charm_attack_blocked or current.danse_macabre_controlled)):
            current = require_characteristics(attacker, current, dice,
                f"round.{state.round_index}.{label}", ('A',), decisions)
            count = phases.build_attacks(AttackPoolContext(attacker, first_round,
                first_charging if is_first else second_charging,
                second_charging if is_first else first_charging, current.frenzy,
                current.wounds < (current.starting_wounds or attacker.characteristics.wounds), 0, current.attacks,
                state.first_player_turn == is_first)).attacks
            count = apply_round_weapon_attack_modifiers(attacker, defender, count,
                first_round=first_round, charging=first_charging if is_first else second_charging,
                charged=second_charging if is_first else first_charging)
            count = apply_opponent_attack_modifiers(attacker, defender, count,
                first_round=first_round, defer_grapple=True)
            count = max(0, count-(first_loss if is_first else second_loss))
            if is_first: first_state = current
            else: second_state = current
        if current.hillman_wolf:
            source = original_first if is_first else original_second
            attacker = equipment_for_state(source, current, first_round=first_round)
            count = current.attacks
            defender = second if is_first else first
        opposing = second_state if is_first else first_state
        if label.endswith('.stomp') and opposing.condition != Condition.KNOCKED_DOWN:
            continue
        if opposing.hillman_wolf:
            defender = equipment_for_state(original_second if is_first else original_first,
                opposing, first_round=first_round)
        initial = before_first if is_first else before_second
        if (label in ('first', 'second')
                and current.broken_hands != initial.broken_hands):
            # Disarm or Trap Blade may remove a weapon before this ordinary
            # activation. The reply uses surviving equipment, not the old pool.
            source = original_first if is_first else original_second
            usable = equipment_for_state(replace(source, global_effects=attacker.global_effects),
                current, first_round=first_round)
            count = max(0, count - int(attacker.off_hand_attacks and not usable.off_hand_attacks))
            if has_tag(usable.main_weapon, 'weapon.fist') and phases.unarmed_attack_cap_applies(usable.global_effects):
                count = min(count, 1)
            attacker = usable
        # Kusara's minimum belongs to the warrior's whole phase, including
        # separately timed Whipcrack attacks. Consume each suppression once.
        other_attacks = already_attacked[is_first] or any(
            event[2] == is_first and event[3] > len(attack_forfeits.get(event[5], ()))
            for event in events[event_index + 1:])
        minimum_attacks = 0 if other_attacks else 1

        if (label in ('first', 'second') and not deathblow_active[is_first]
                and current.condition == Condition.OUT
                and has_tag(attacker.global_effects, 'mechanic.deathblow')):
            deathblow_active[is_first] = decisions.choose(
                f"round.{state.round_index}.{label}.deathblow", attacker)
        if deathblow_active[is_first] and count <= 0:
            count = deathblow_pool['first' if is_first else 'second']
        if is_first:
            first_state, second_state, resolved = _resolve_attack_pool(
                attacker, defender, first_state, second_state,
                count, dice,
                key=f"round.{state.round_index}.{label}", first_round=first_round,
                charging=first_charging, decisions=decisions,
                defender_condition_at_start=before_second.condition,
                minimum_attacks=minimum_attacks,
                single_bonus=label.endswith(('.shifty', '.last-bite', '.stomp', '.electrical-touch', '.whipcrack')) or '.eagle.' in label,
                miss_first_attack=first_misses, forfeit_index=electrical_forfeits.get(label),
                forfeit_indices=attack_forfeits.get(label, ()),
                allocated_weapons=pool_allocations.get(label),
                grapple_declared=grapple_selections.get(is_first) if label in ('first','second') else False,
                deathblow=deathblow_active[is_first],
            )
        else:
            second_state, first_state, resolved = _resolve_attack_pool(
                attacker, defender, second_state, first_state,
                count, dice,
                key=f"round.{state.round_index}.{label}", first_round=first_round,
                charging=second_charging, decisions=decisions,
                defender_condition_at_start=before_first.condition,
                minimum_attacks=minimum_attacks,
                single_bonus=label.endswith(('.shifty', '.last-bite', '.stomp', '.electrical-touch', '.whipcrack')) or '.eagle.' in label,
                miss_first_attack=second_misses, forfeit_index=electrical_forfeits.get(label),
                forfeit_indices=attack_forfeits.get(label, ()),
                allocated_weapons=pool_allocations.get(label),
                grapple_declared=grapple_selections.get(is_first) if label in ('first','second') else False,
                deathblow=deathblow_active[is_first],
            )
        if resolved and label.endswith('.electrical-touch'):
            owner = first_state if is_first else second_state
            recharge, owner = _owned_roll(attacker, owner, dice, decisions,
                RollRequest(f"round.{state.round_index}.{label}.recharge", sides=3), close_combat=True)
            owner = replace(owner, electrical_available_at=state.round_index+recharge)
            if is_first: first_state = owner
            else: second_state = owner
        if resolved:
            if is_first: first_misses = False
            else: second_misses = False
            control_attacked[is_first] = True
            control_hits[is_first] = control_hits[is_first] or any(
                outcome.hit for outcome in resolved)
        already_attacked[is_first] = already_attacked[is_first] or bool(resolved)
        outcomes.extend(resolved)
        first_state = _force_of_will(first, first_state, dice, f"round.{state.round_index}.first.force.after-attack", decisions=decisions)
        second_state = _force_of_will(second, second_state, dice, f"round.{state.round_index}.second.force.after-attack", decisions=decisions)

    if state.first_player_turn and has_tag(first.global_effects, 'condition.black-hunger-active'):
        first_state, backlash = _black_hunger(first, first_state, dice, f"round.{state.round_index}.first.black-hunger", decisions=decisions)
        outcomes.extend(backlash)
    first_state = _force_of_will(
        first, first_state, dice, f"round.{state.round_index}.first.force.after-black-hunger", decisions=decisions
    )
    if not state.first_player_turn and has_tag(second.global_effects, 'condition.black-hunger-active'):
        second_state, backlash = _black_hunger(second, second_state, dice, f"round.{state.round_index}.second.black-hunger", decisions=decisions)
        outcomes.extend(backlash)
    second_state = _force_of_will(
        second, second_state, dice, f"round.{state.round_index}.second.force.after-black-hunger", decisions=decisions
    )
    state=_burning_bodies(first,second,replace(state,first=first_state,second=second_state),dice,decisions)
    first_state,second_state=state.first,state.second
    # Seduction's printed release.  The Khemrian copy ends the control when the
    # Vampire attacks her victim at all; the Lahmia copy only when an attack
    # hits.  A control that was not attacked survives into the next phase, where
    # the victim's own Recovery-phase test may still throw it off.
    for target_first in (True, False):
        current = first_state if target_first else second_state
        held = current.resources_spent.intersection(SEDUCTION_RESOURCES)
        if not held or not control_attacked[not target_first]:
            continue
        if control_hits[not target_first] or LAHMIA_SEDUCTION_RESOURCE not in held:
            current = replace(current, resources_spent=(
                current.resources_spent - set(SEDUCTION_RESOURCES)))
            if target_first:
                first_state = current
            else:
                second_state = current
    trace = tuple(dict.fromkeys((
        *(state.trace if state.round_index == 0 else ()), Phase.PRIORITY, Phase.ATTACKS,
        *(phase for outcome in outcomes for phase in outcome.trace), Phase.AFTERMATH,
    )))
    return CombatRoundResult(
        replace(state, first=first_state, second=second_state,
                round_index=state.round_index + 1, trace=trace),
        tuple(outcomes),
    )


def apply_opponent_leadership(
    fighter: CompiledFighter, opponent: CompiledFighter, state: DuelState,
) -> CompiledFighter:
    """Apply the Leadership facts an opponent supplies to this fighter.

    Questing Vow qualifies all local Leadership tests against a Fear-causer, and
    Enchanting Beauty drops the Leadership of a *living* contacting enemy.  The
    printed clause exempts Undead and Daemons and names nothing else, so a
    Possessed, Chaos-mutated or otherwise non-living-typed mortal is still
    affected; only those two natures keep the source's exemption.
    """
    effect = fighter.global_effects
    if (has_tag(opponent.global_effects, "mechanic.enchanting-beauty")
            and not any(has_tag(effect, tag) for tag in ("nature.undead", "nature.daemon"))):
        effect = replace(effect, tags=(*effect.tags, "condition.enchanting-beauty"))
    if (has_tag(effect, "mechanic.questing-vow")
            and (state.engaged or any(state.initial_charge_flags))
            and causes_fear(opponent, fighter)):
        effect = replace(effect, tags=(*effect.tags, "mechanic.leadership-reroll"))
    if effect is fighter.global_effects:
        return fighter
    return replace(fighter, global_effects=effect)


def select_shifty_weapon(
    fighter: CompiledFighter, decisions: DecisionPolicy, *, key: str,
) -> CompiledFighter:
    """Project one nominated melee attack, preserving its original hand slot.

    Mixed kits retain their melee nomination. The F005 user ruling permits a
    pistol-only bonus as a separate strike in addition to the ordinary pistol pool.
    """
    weapon, clean, slot = fighter.main_weapon, fighter.main_weapon_without_poison, fighter.main_hand_slot
    off = fighter.off_hand if fighter.off_hand_attacks else None
    if off is not None and not is_pistol(off) and (
        is_pistol(weapon) or (off != weapon and not decisions.choose(f'{key}.main-weapon', fighter))
    ):
        weapon, clean, slot = off, fighter.off_hand_without_poison, fighter.off_hand_slot
    elif is_pistol(weapon) and off is not None and off != weapon:
        if not decisions.choose(f'{key}.main-weapon', fighter):
            weapon, clean, slot = off, fighter.off_hand_without_poison, fighter.off_hand_slot
    return replace(fighter, main_weapon=weapon, main_weapon_without_poison=clean,
        main_hand_slot=slot, off_hand=None, off_hand_without_poison=None,
        off_hand_attacks=False, extra_attacks=())


def _strike_first_fighter(fighter: CompiledFighter, weapon: EffectSet) -> CompiledFighter:
    """Project one nominated allocated attack, preserving its own hand slot.

    The nominated strike keeps the profile of the weapon the pool allocated for
    it and the slot that weapon is carried in, so it never borrows the other
    hand's characteristics and leaves no duplicate behind.
    """
    if weapon == fighter.main_weapon:
        slot, clean = fighter.main_hand_slot, fighter.main_weapon_without_poison
    elif fighter.off_hand is not None and weapon == fighter.off_hand:
        slot, clean = fighter.off_hand_slot, fighter.off_hand_without_poison
    else:
        slot, clean = 'natural', None
    return replace(fighter, main_weapon=weapon, main_hand_slot=slot,
        main_weapon_without_poison=clean, off_hand=None, off_hand_without_poison=None,
        off_hand_attacks=False, extra_attacks=())


def select_attack_replacement(
    fighter: CompiledFighter, *, first_round: bool, charging: bool,
    decisions: DecisionPolicy, key: str,
) -> CompiledFighter:
    """Apply optional whole-pool replacements before attack count and resolution."""
    if (has_tag(fighter.global_effects, "mechanic.wraith-touch")
            and decisions.choose(f"{key}.wraith-touch", fighter)):
        return replace(fighter, main_weapon=EffectSet(
            tags=("weapon.fist", "effect.wraith-touch", "effect.no-critical"),
            strength_bonus=-1, target_armour_bonus=1),
            main_weapon_without_poison=None, off_hand=None, off_hand_without_poison=None,
            off_hand_attacks=False, extra_attacks=())
    if fighter.vomit_attack is not None and decisions.choose(f"{key}.vomit-attack", fighter):
        return replace(fighter, main_weapon=fighter.vomit_attack,
            main_weapon_without_poison=None, off_hand=None, off_hand_without_poison=None,
            off_hand_attacks=False, extra_attacks=())
    if (has_tag(fighter.main_weapon, "weapon.serpent-staff")
            and decisions.choose(f"{key}.serpent-staff", fighter)):
        return replace(fighter, main_weapon=EffectSet(
            tags=("effect.serpent-staff-power",), fixed_strength=4, priority=1),
            off_hand=None, off_hand_attacks=False, extra_attacks=())
    removable = []
    if (has_tag(fighter.global_effects, "mechanic.anvil-head")
            and first_round and charging
            and not decisions.choose(f"{key}.anvil-head", fighter)):
        removable.append("mechanic.anvil-head")
    if (has_tag(fighter.global_effects, "mechanic.death-blow")
            and fighter.characteristics.attacks >= 2
            and not decisions.choose(f"{key}.death-blow", fighter)):
        removable.append("mechanic.death-blow")
    if not removable:
        return fighter
    effects = replace(
        fighter.global_effects,
        tags=tuple(tag for tag in fighter.global_effects.tags if tag not in removable),
    )
    return replace(fighter, global_effects=effects)


def resolve_crude_belch(owner, enemy, state, dice, decisions, *, first: bool):
    """Return the duel enemy's timed first-attack loss, separate from count clamps."""
    if not has_tag(owner.global_effects, "skill.crude-belch-halfling"):
        return False, state
    owner_state = state.first if first else state.second
    enemy_state = state.second if first else state.first
    if owner_state.condition != Condition.STANDING or not enemy_state.active:
        return False, state
    context = state.context
    if context is not None:
        own_id = context.facts.first_id if first else context.facts.second_id
        enemy_id = context.facts.second_id if first else context.facts.first_id
        contacts = context.facts.contacts
        # The duel has two mutable combat states. Do not silently omit another
        # supplied enemy that the printed area effect must also affect.
        own_side = context.participant(own_id).side_id
        if any(own_id in pair and context.participant(next(pid for pid in pair if pid != own_id)).side_id != own_side
               and enemy_id not in pair for pair in contacts or ()):
            raise ValueError("Crude Belch additional enemy contacts require multi-participant resolution")
        if contacts is not None and not any({a, b} == {own_id, enemy_id} for a, b in contacts):
            return False, state
    key = f"round.{state.round_index}.{'first' if first else 'second'}.crude-belch"
    if not decisions.choose(key, owner):
        return False, state
    passed, current = resolve_local_leadership(
        enemy, state, dice, decisions, key + '.leadership', first=not first,
        opponent=owner, return_state=True, close_combat=True)
    return not passed, replace(state, **{"second" if first else "first": current})


def resolve_spawn_attack_count(
    fighter: CompiledFighter, ordinary_count: int, dice: DiceSource, key: str,
) -> int:
    if has_tag(fighter.main_weapon, "weapon.vomit-attack"):
        return ordinary_count
    if phases.has_tag(fighter.global_effects, "mechanic.spawn-special-attacks"):
        return dice.roll(RollRequest(key)) + 1
    return ordinary_count


def apply_opponent_attack_modifiers(
    attacker: CompiledFighter, defender: CompiledFighter, count: int, *, first_round: bool,
    defer_grapple: bool = False,
) -> int:
    if not count:
        return 0
    if (
        (phases.has_tag(defender.global_effects, "animal_friendship")
         or phases.has_tag(defender.global_effects, "mechanic.animal-friendship"))
        and phases.has_tag(attacker.global_effects, "species.normal-animal")
    ):
        return 0
    if (
        first_round
        and phases.has_tag(defender.global_effects, "skill.sigmar-s-sign")
        and phases.has_tag(attacker.global_effects, "undead_or_possessed")
        and not phases.has_tag(attacker.global_effects, "nature.daemon")
    ):
        count = max(1, count - 1)
    modifier = defender.global_effects.incoming_attacks_modifier
    if defer_grapple and modifier < 0 and has_tag(defender.global_effects, "rule.tentacle-grapple"):
        # Keep Tentacle's one optional loss for the allocated pool; other
        # incoming reductions retain their usual count/floor semantics.
        modifier += 1
    return max(1, count + modifier)


def apply_round_weapon_attack_modifiers(
    attacker: CompiledFighter, defender: CompiledFighter, count: int, *,
    first_round: bool, charging: bool, charged: bool,
) -> int:
    """Apply weapon rules that change the pool because either fighter charged."""
    if not count or not first_round:
        return count
    if whipcrack_weapon(attacker) is not None and (charging or charged):
        count += 1
    if phases.has_tag(defender.main_weapon, "weapon.boar-spear") and charging:
        count = max(1, count - 1)
    return count
