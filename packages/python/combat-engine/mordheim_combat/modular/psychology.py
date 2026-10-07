"""Initial duel charges and source-specific Fear consequences."""
from dataclasses import replace

from mordheim_combat import phases
from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.state import DuelState
from mordheim_core.dice import DecisionPolicy, DiceSource
from mordheim_core.models import CompiledFighter


def fears_opponent_fire(fighter: CompiledFighter, enemy: CompiledFighter) -> bool:
    return (phases.has_tag(fighter.global_effects, "mechanic.fears-fire")
            and (phases.has_tag(enemy.global_effects, "condition.open-flame")
                 or phases.has_tag(enemy.global_effects, "attack.fire")
                 or any(phases.has_tag(weapon, "attack.fire")
                        for weapon in (enemy.main_weapon, enemy.off_hand) if weapon is not None)))


def causes_fear(fighter: CompiledFighter, enemy: CompiledFighter) -> bool:
    if (phases.has_tag(fighter.global_effects, "mechanic.morrs-servant")
            and phases.has_tag(enemy.global_effects, "nature.undead")):
        return True
    if phases.has_tag(fighter.global_effects, "mechanic.beauty-of-the-sea"):
        if not any(phases.has_tag(enemy.global_effects, tag) for tag in ("sex.male", "sex.female")):
            raise ValueError("Beauty of the Sea requires the opponent's explicit male/female fact")
        if phases.has_tag(enemy.global_effects, "sex.female"):
            return True
    if (phases.has_tag(fighter.global_effects, "mechanic.fear-human")
            and phases.has_tag(enemy.global_effects, "species.human")):
        return True
    if fears_opponent_fire(enemy, fighter):
        return True
    if phases.has_tag(fighter.global_effects, "mechanic.causes-fear"):
        return True
    # Beastbane belongs to a wielded weapon and affects animals only. An
    # animal frightening ordinary warriors does not imply the reverse.
    return (phases.has_tag(enemy.global_effects, "species.animal")
            and any(phases.has_tag(weapon, "weapon.beastlash")
                    for weapon in (fighter.main_weapon, fighter.off_hand) if weapon is not None))


def resolve_stupidity(first, second, state, dice, decisions):
    """Refresh the active duelist's Psychology result until its next own turn."""
    is_first = state.first_player_turn
    fighter = first if is_first else second
    current = state.first if is_first else state.second
    if not current.active or not (phases.has_tag(fighter.global_effects, "mechanic.stupidity")
                                  or "disability.6" in current.resources_spent):
        return state
    label = "first" if is_first else "second"
    passed = current.frenzy or phases.has_tag(fighter.global_effects, "condition.stupidity-exempt")
    if not passed:
        passed, current = resolve_local_leadership(
            fighter, state, dice, decisions, f"round.{state.round_index}.{label}.stupidity",
            first=is_first, psychology=current.drunken_result != 1, stupidity=True,
            opponent=second if is_first else first, return_state=True)
    failed = not passed
    current = replace(current, stupidity_failed=failed)
    state = replace(state, **{label: current})
    # The initial voluntary charge cannot establish contact after a failed test.
    if failed and state.round_index == 0 and state.initial_charge_flags[int(not is_first)]:
        charges = list(state.initial_charge_flags)
        charges[int(not is_first)] = False
        state = replace(state, first_charged=charges[0], second_charged=charges[1],
            initial_first_player_turn=is_first, engaged=any(charges),
            failed_charges=state.failed_charges | {label})
    return state


def resolve_fear(
    first: CompiledFighter, second: CompiledFighter, state: DuelState,
    dice: DiceSource, decisions: DecisionPolicy,
) -> DuelState:
    if state.round_index != 0:
        return state
    # Calling both verifies required opponent facts before any roll.
    first_fear, second_fear = causes_fear(first, second), causes_fear(second, first)
    charges = list(state.initial_charge_flags)
    states = [state.first, state.second]
    for index, (target, singer) in enumerate(((first, second), (second, first))):
        if (charges[index] and phases.has_tag(singer.global_effects, "mechanic.beauty-of-the-sea")
                and phases.has_tag(target.global_effects, "sex.male")
                and not phases.has_tag(target.global_effects, "species.animal")):
            passed, states[index] = resolve_local_leadership(target,
                replace(state, first=states[0], second=states[1]), dice, decisions,
                f"round.0.{'first' if index == 0 else 'second'}.beauty-charge",
                first=index == 0, psychology=True, opponent=singer, return_state=True)
            if passed:
                states[index] = states[index].spend("beauty.passed")
            else:
                charges[index] = False
                state = replace(state, failed_charges=state.failed_charges | {"first" if index == 0 else "second"})
    state = replace(state, first=states[0], second=states[1],
        first_charged=charges[0], second_charged=charges[1],
        initial_first_player_turn=state.first_player_turn,
        engaged=state.engaged and (any(charges) or not state.failed_charges))
    if not state.engaged or not (first_fear or second_fear):
        return state
    fighters = (first, second)
    states = [state.first, state.second]
    charges = list(state.initial_charge_flags)
    failed = set(state.failed_charges)

    def morrs_servant(index):
        return (phases.has_tag(fighters[1 - index].global_effects, "mechanic.morrs-servant")
                and phases.has_tag(fighters[index].global_effects, "nature.undead"))

    def needs_test(index):
        if morrs_servant(index):
            # This source expressly overrides Undead Psychology exemptions.
            return states[index].condition == phases.Condition.STANDING and states[1 - index].active
        if fears_opponent_fire(fighters[index], fighters[1 - index]):
            return states[index].condition == phases.Condition.STANDING and states[1 - index].active
        return (states[index].condition == phases.Condition.STANDING
                and states[1 - index].active
                and causes_fear(fighters[1 - index], fighters[index])
                and (not causes_fear(fighters[index], fighters[1 - index])
                     or phases.has_tag(fighters[index].global_effects, "mechanic.craven"))
                and not states[index].frenzy
                and not phases.has_tag(fighters[index].global_effects, "mechanic.fear-immunity")
                and not phases.has_tag(fighters[index].global_effects, "mechanic.psychology-immunity"))

    def test_fear(index, label, suffix):
        ordinary_fear = not (morrs_servant(index) or fears_opponent_fire(fighters[index], fighters[1 - index]))
        passed, states[index] = resolve_local_leadership(
            fighters[index], replace(state, first=states[0], second=states[1]), dice, decisions,
            f"round.0.{label}.fear.{suffix}", first=index == 0,
            psychology=ordinary_fear, fear=ordinary_fear,
            opponent=fighters[1 - index], return_state=True)
        return passed

    # A voluntary charge must succeed before contact/charged reactions exist.
    for index, label in enumerate(("first", "second")):
        if charges[index] and needs_test(index) and not test_fear(index, label, "charge"):
            if phases.has_tag(fighters[index].global_effects, "mechanic.wheelo-impact"):
                states[index] = replace(states[index], fear_hit_sixes=True)
            else:
                charges[index] = False
                failed.add(label)
    engaged = state.engaged and (any(charges) or not failed)
    if engaged:
        for index, label in enumerate(("first", "second")):
            if charges[1 - index] and needs_test(index) and not test_fear(index, label, "charged"):
                states[index] = replace(states[index], fear_hit_sixes=True)
    if (states == [state.first, state.second] and tuple(charges) == state.initial_charge_flags
            and failed == set(state.failed_charges)):
        return state
    return replace(state, first=states[0], second=states[1],
        first_charged=charges[0], second_charged=charges[1],
        initial_first_player_turn=state.first_player_turn,
        failed_charges=frozenset(failed), engaged=engaged)
