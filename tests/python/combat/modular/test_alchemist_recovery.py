"""Source effects and the approved own-turn timing, through canonical builds."""
from mordheim_combat.modular.alchemy import resolve_alchemist
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


def scientist(*conditions, **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="masters-of-horror-sylv", profile_id="mad-scientist",
        main_weapon_id="weapon.mace", condition_ids=conditions, **options))


def start(owner):
    enemy = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 1, 1),
                                       main_weapon_id="weapon.mace"))
    return enemy, initialize_duel(owner, enemy, StrictDice([]),
                                 context=DuelContext(charging=(), active_participant="first"))


def play(owner, enemy, state, *rolls, blocked=False):
    key = f"round.{state.round_index}"
    values = list(rolls)
    if not blocked:
        values.append((f"{key}.first.attack.0.hit", 1))
    values.append((f"{key}.second.attack.0.hit", 1))
    dice = StrictDice([{"key": k, "value": v} for k, v in values])
    decisions = StrictDecisions([])
    result = resolve_round(owner, enemy, state, dice, decisions)
    dice.finish()
    decisions.finish()
    return result.state


def test_backley_retries_only_on_own_turn_and_stops_after_passing():
    owner = scientist("condition.alchemist-backleys-brew")
    enemy, state = start(owner)
    assert (state.first.strength, state.first.initiative) == (2, 3)
    state = play(owner, enemy, state, ("round.0.first.alchemist-backley", 4))
    assert (state.first.strength, state.first.initiative) == (2, 3)
    state = play(owner, enemy, state)  # Opponent's turn: no test.
    state = play(owner, enemy, state, ("round.2.first.alchemist-backley", 3))
    assert (state.first.strength, state.first.initiative) == (3, 4)
    state = play(owner, enemy, state)
    state = play(owner, enemy, state)  # Own turn after recovery: no further test.
    assert (state.first.strength, state.first.initiative) == (3, 4)


def test_addiction_six_releases_actions_and_grants_vigortia_once():
    owner = scientist("condition.alchemist-addicted")
    enemy, state = start(owner)
    state = play(owner, enemy, state, ("round.0.first.alchemist-brew", 5), blocked=True)
    assert (state.first.strength, state.first.toughness) == (3, 3)
    state = play(owner, enemy, state, blocked=True)
    state = play(owner, enemy, state, ("round.2.first.alchemist-brew", 6))
    assert (state.first.strength, state.first.toughness) == (4, 4)
    state = play(owner, enemy, state)
    state = play(owner, enemy, state)
    assert (state.first.strength, state.first.toughness) == (4, 4)
    # A caller already supplying Vigortia does not receive its bonus twice.
    prepared = scientist("condition.alchemist-addicted", "condition.alchemist-aberrantius-vigortia")
    _, initial = start(prepared)
    dice = StrictDice([{"key": "prepared.alchemist-brew", "value": 6}])
    released = resolve_alchemist(prepared, initial.first, dice, StrictDecisions([]), "prepared")
    dice.finish()
    assert (released.strength, released.toughness) == (4, 4)


def test_backley_at_the_stat_floor_does_not_award_a_free_point_on_recovery():
    owner = scientist("condition.alchemist-backleys-brew",
                      characteristics=Characteristics(3, 1, 3, 1, 1, 1))
    _, state = start(owner)
    assert (state.first.strength, state.first.initiative) == (1, 1)
    dice = StrictDice([{"key": "floor.alchemist-backley", "value": 3}])
    restored = resolve_alchemist(owner, state.first, dice, StrictDecisions([]), "floor")
    dice.finish()
    assert (restored.strength, restored.initiative) == (1, 1)
