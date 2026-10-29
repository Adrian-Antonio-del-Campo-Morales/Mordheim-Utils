"""Vectorized engine: Fear, Stupidity and their per-row consequences.

This module ports ``modular/psychology.py`` to batch columns.  The batch keeps
the modular cadence: Stupidity is refreshed for the active player's fighter,
Fear is tested only in the round the two warriors make contact, and each
consequence is written on the rows it belongs to (``stupidity_failed`` in
``CombatState``, ``fear_hit_sixes`` in :class:`PsychologyResources`, and the
caller's initial charge masks).

Only the supplied local facts are read: participants, conditions, sides and
distances come from ``PreparedDuelContext``.  No board position is produced,
no band is searched and no group Psychology is simulated.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass

from mordheim_core.context import PreparedDuelContext
from mordheim_core.dice import DecisionPolicy
from mordheim_core.models import CompiledFighter

from mordheim_combat.vectorized._leadership import (
    LeadershipResources,
    resolve_local_leadership,
    undead_foes_fear_immunity,
)
from mordheim_combat.vectorized._types import CombatState, OUT, STANDING, has

__all__ = [
    "FearOutcome",
    "PsychologyResources",
    "StupidityOutcome",
    "causes_fear",
    "fears_opponent_fire",
    "psychology_resources",
    "resolve_fear",
    "resolve_feral_instinct",
    "resolve_lunatics",
    "resolve_mark_of_shornaal",
    "resolve_mesmerising_dance",
    "resolve_stupidity",
    "undead_foes_fear_immunity",
]


@dataclass(slots=True)
class PsychologyResources:
    """Per-row Psychology facts ``CombatState`` does not carry.

    ``fear_hit_sixes`` is the modular ``FighterState.fear_hit_sixes``: while
    set, a melee attack against that row hits on a natural 6 only.  The round
    driver clears it at the start of each turn, as ``resolve_round`` does.

    The remaining columns are the ``FighterState`` facts the frozen
    ``CombatState`` schema does not own.  They are battle-lived, exactly as the
    modular fighter state is: the driver builds one ledger per side and keeps
    it for the whole duel.
    """

    fear_hit_sixes: np.ndarray
    #: ``FighterState.lunatic_result``: the chart face the Lunatics producer
    #: rolled this round, 0 before the first roll.  Nothing in the accepted
    #: engine reads it; the modular state records it, so the batch does too.
    lunatic_result: np.ndarray
    #: ``FighterState.lunatic_stupidity``: the accumulated Stupidity half of
    #: the printed chart.  ``resolve_stupidity`` reads it as its
    #: ``lunatic_stupidity`` argument.
    lunatic_stupidity: np.ndarray
    #: The once-per-battle ``mark-of-shornaal.passed`` resource of the row that
    #: is tested, kept on the *tested* (target) side as the scalar round keeps
    #: it on the target's ``resources_spent``.
    shornaal_passed: np.ndarray
    #: ``FighterState.feral_instinct_failed``: the own-turn Leadership failure
    #: the modular state records.  Movement is outside the duel, so no phase of
    #: either engine consumes it; the test itself still spends dice and the
    #: fighter's Leadership resources.
    feral_instinct_failed: np.ndarray


def psychology_resources(count: int) -> PsychologyResources:
    """Fresh Psychology resources for ``count`` rows of one fighter."""
    return PsychologyResources(
        fear_hit_sixes=np.zeros(count, dtype=bool),
        lunatic_result=np.zeros(count, dtype=np.int8),
        lunatic_stupidity=np.zeros(count, dtype=bool),
        shornaal_passed=np.zeros(count, dtype=bool),
        feral_instinct_failed=np.zeros(count, dtype=bool),
    )


@dataclass(frozen=True)
class StupidityOutcome:
    """Stupidity consequence of the active player's fighter.

    ``failed`` is aligned to the caller's ``rows``; ``charges`` is a copy of
    that fighter's initial charge mask with the charges a failed Stupidity at
    round zero cancels already cleared.
    """

    failed: np.ndarray
    charges: np.ndarray


@dataclass(frozen=True)
class FearOutcome:
    """Fear consequence of the first round, per row.

    ``first_failed``/``second_failed`` mark the rows whose own Fear test
    cancelled that warrior's charge; ``engaged`` is the contact mask after the
    charge tests.
    """

    first_charges: np.ndarray
    second_charges: np.ndarray
    engaged: np.ndarray
    first_failed: np.ndarray
    second_failed: np.ndarray


def fears_opponent_fire(fighter: CompiledFighter, enemy: CompiledFighter) -> bool:
    """The printed fear of open flame, read from the opponent's supplied facts."""
    return (has(fighter.global_effects, "mechanic.fears-fire")
            and (has(enemy.global_effects, "condition.open-flame")
                 or has(enemy.global_effects, "attack.fire")
                 or any(has(weapon, "attack.fire")
                        for weapon in (enemy.main_weapon, enemy.off_hand) if weapon is not None)))


def causes_fear(fighter: CompiledFighter, enemy: CompiledFighter) -> bool:
    """Whether ``fighter`` causes Fear in ``enemy`` from the supplied facts."""
    if (has(enemy.global_effects, "mechanic.fear-of-snakes")
            and any(has(fighter.global_effects, tag) for tag in
                    ("species.snake", "species.serpent"))):
        return True
    if (has(enemy.global_effects, "mechanic.fear-of-elves")
            and any(has(fighter.global_effects, tag) for tag in
                    ("species.elf", "species.high-elf", "species.dark-elf", "species.wood-elf"))):
        return True
    if (has(fighter.global_effects, "mechanic.fear-beastmen")
            and has(enemy.global_effects, "species.beastman")):
        return True
    if (has(fighter.global_effects, "mechanic.morrs-servant")
            and has(enemy.global_effects, "nature.undead")):
        return True
    if has(fighter.global_effects, "mechanic.beauty-of-the-sea"):
        if not any(has(enemy.global_effects, tag) for tag in ("sex.male", "sex.female")):
            raise ValueError("Beauty of the Sea requires the opponent's explicit male/female fact")
        if has(enemy.global_effects, "sex.female"):
            return True
    if (has(fighter.global_effects, "mechanic.fear-human")
            and has(enemy.global_effects, "species.human")):
        return True
    if fears_opponent_fire(enemy, fighter):
        return True
    if has(fighter.global_effects, "mechanic.causes-fear"):
        return True
    # Beastbane belongs to a wielded weapon and affects animals only. An
    # animal frightening ordinary warriors does not imply the reverse.
    return (has(enemy.global_effects, "species.animal")
            and any(has(weapon, "weapon.beastlash")
                    for weapon in (fighter.main_weapon, fighter.off_hand) if weapon is not None))


def resolve_stupidity(
    first: CompiledFighter, second: CompiledFighter,
    state_first: CombatState, state_second: CombatState, rows: np.ndarray, *,
    first_player_turn: bool, round_index: int, charges: np.ndarray,
    rng: np.random.Generator, leadership: LeadershipResources,
    decisions: DecisionPolicy | None = None,
    context: PreparedDuelContext | None = None,
    lunatic_stupidity: np.ndarray | None = None,
    drunken_result: np.ndarray | None = None,
    key_prefix: str | None = None,
) -> StupidityOutcome:
    """Batch port of ``modular.psychology.resolve_stupidity``.

    Only the active player's fighter tests, exactly as the scalar operator
    reads ``state.first_player_turn``.  ``charges`` is that fighter's initial
    charge mask; a failure at round zero cannot establish contact, so the
    returned copy clears exactly the charged rows that failed.
    """
    rows = np.asarray(rows, dtype=np.intp)
    updated_charges = np.array(charges, dtype=bool, copy=True)
    failed = np.zeros(rows.size, dtype=bool)
    if rows.size == 0:
        return StupidityOutcome(failed, updated_charges)
    label = "first" if first_player_turn else "second"
    fighter = first if first_player_turn else second
    state = state_first if first_player_turn else state_second
    effects = fighter.global_effects
    lunatic = (np.zeros(rows.size, dtype=bool) if lunatic_stupidity is None
               else np.asarray(lunatic_stupidity, dtype=bool)[rows])
    gated = (state.condition[rows] != OUT) & (
        lunatic
        | has(effects, "mechanic.stupidity")
        | (state.disability[rows] == 6)
    )
    positions = np.flatnonzero(gated)
    if positions.size == 0:
        return StupidityOutcome(failed, updated_charges)
    selected = rows[positions]
    passed = state.frenzy[selected] | has(effects, "condition.stupidity-exempt")
    if round_index == 0 and has(effects, "condition.impetuous-charge"):
        passed |= np.asarray(charges, dtype=bool)[selected]
    participant_id = (None if context is None
                      else context.facts.first_id if first_player_turn
                      else context.facts.second_id)
    supplied_hero = has(effects, "condition.disability-hero-nearby")
    disability = (state.disability[selected] == 6) & ~passed
    if disability.any():
        # The permanent table result of 6 keeps the warrior Stupid; a supplied
        # Hero of its side within six inches, or the supplied nearby-Hero fact
        # when no Hero record contradicts it, lets it act.
        heroes = (() if context is None
                  else tuple(record for record in context.facts.nearby
                             if has(record.fighter.global_effects, "fighter-kind.hero")))
        near_hero = context is not None and any(
            record.side_id == context.participant(participant_id).side_id
            and record.condition != "out"
            and context.distance(participant_id, record.participant_id) <= 6
            for record in heroes
        )
        passed |= disability & (near_hero or (supplied_hero and not heroes))
    if context is not None:
        side = context.participant(participant_id).side_id
    # The printed Rat Ogre exemption: a Skaven Hero supplied within six inches
    # exempts the bearer, with no Stupidity test at all.  The nearby records and
    # distances are caller-supplied duel facts; the clause never simulates the
    # surrounding warband or a board.  The bearer's own warband group scopes the
    # concession to the Skaven warriors that print it.
    printed_bands = ("band.skaven-of-clan-mors-kaz",
                     "band.skaven-of-clan-moulder-web",
                     "band.skaven-of-clan-pristekk-sc")
    own_band = next((band for band in printed_bands if has(effects, band)), None)
    if (context is not None and has(effects, "mechanic.stupidity")
            and (has(effects, "warband-group.skaven") or own_band is not None)):
        exempting = tuple(
            record for record in context.facts.nearby
            if record.side_id == side and record.condition != "out"
            and has(record.fighter.global_effects, "fighter-kind.hero")
            and (has(record.fighter.global_effects, "species.skaven")
                 or (own_band is not None
                     and has(record.fighter.global_effects, own_band)))
        )
        if exempting and any(
                context.distance(participant_id, record.participant_id) <= 6
                for record in exempting):
            passed |= ~passed
    if has(effects, "mechanic.bear-handler-recipient"):
        providers = (() if context is None
                     else tuple(record for record in context.facts.nearby
                                if has(record.fighter.global_effects, "mechanic.bear-handler")))
        near_handler = context is not None and any(
            record.side_id == side and record.condition != "out"
            and context.distance(participant_id, record.participant_id) <= 6
            for record in providers
        )
        # The supplied condition is the qualified nearby Tamer fact. Explicit
        # provider records take precedence when they contradict that fact.
        supplied = has(effects, "condition.bear-handler-nearby")
        passed |= ~passed & (near_handler or (supplied and not providers))
    remaining = ~passed
    if remaining.any():
        drunken = (np.ones(selected.size, dtype=bool) if drunken_result is None
                   else np.asarray(drunken_result)[selected] != 1)
        psych = drunken & ~lunatic[positions]
        # The Leadership helper indexes a per-row mask by simulation row, so the
        # gated results are projected back onto the fighter's own row space.
        psych_rows = np.ones(state.wounds.size, dtype=bool)
        psych_rows[selected] = psych
        tested = selected[remaining]
        test_passed = resolve_local_leadership(
            fighter, state, tested, first=first_player_turn,
            key=f"{key_prefix or f'round.{round_index}'}.{label}.stupidity",
            context=context, rng=rng, decisions=decisions, resources=leadership,
            stupidity=True, psychology=psych_rows,
            opponent=second if first_player_turn else first,
        )
        passed[remaining] = test_passed
    failure = ~passed
    state.stupidity_failed[selected] = failure
    failed[positions] = failure
    if round_index == 0:
        cancelling = selected[failure & np.asarray(charges, dtype=bool)[selected]]
        updated_charges[cancelling] = False
    return StupidityOutcome(failed, updated_charges)


def _charge_gate(target: CompiledFighter, singer: CompiledFighter) -> str | None:
    """The charge gate a Fear-causing singer imposes, or ``None``."""
    if (has(target.global_effects, "mechanic.ashamed-and-afraid")
            and has(singer.global_effects, "identity.sigmarite-opponent")):
        return "ashamed-and-afraid"
    if has(singer.global_effects, "mechanic.slaanesh-charge-test"):
        return "slaanesh-charge"
    if (has(singer.global_effects, "mechanic.hypnotic-musk")
            and not target.mounted
            and not has(target.global_effects, "condition.goading-charge")
            and any(has(target.global_effects, tag) for tag in
                    ("species.animal", "species.normal-animal", "species.beast"))):
        return "hypnotic-musk-charge"
    if has(singer.global_effects, "mechanic.opposite-sex-charge-test"):
        sexes = tuple(next((sex for sex in ("male", "female")
                            if has(f.global_effects, "sex." + sex)), None)
                      for f in (target, singer))
        if None in sexes:
            raise ValueError("Charismatic requires both duelists' explicit male/female facts")
        if sexes[0] != sexes[1]:
            return "charismatic-charge"
    return None


def resolve_fear(
    first: CompiledFighter, second: CompiledFighter,
    state_first: CombatState, state_second: CombatState, rows: np.ndarray, *,
    round_index: int, engaged: np.ndarray, first_charges: np.ndarray,
    second_charges: np.ndarray, rng: np.random.Generator,
    resources: tuple[PsychologyResources, PsychologyResources] | None = None,
    leadership: tuple[LeadershipResources, LeadershipResources] | None = None,
    decisions: DecisionPolicy | None = None,
    context: PreparedDuelContext | None = None,
    key_prefix: str = "round.0",
) -> FearOutcome:
    """Batch port of ``modular.psychology.resolve_fear``.

    ``rows`` names the simulations in contact this phase and ``engaged`` is
    their contact mask.  A failed voluntary charge clears the row's charge; a
    failed test after being charged sets ``fear_hit_sixes`` on that row.

    Two ledgers are kept apart, as the scalar operator keeps them: ``resources``
    is the Psychology ledger this phase writes, while ``leadership`` holds the
    per-battle resources the Leadership test spends (Holy Relic, re-rolls,
    Ranald's Luck, Scryer...).  When ``resources`` is omitted the consequence is
    written to a throwaway ledger; ``leadership`` must be supplied for any row
    whose fighter carries such a resource.
    """
    charge_masks = [np.array(first_charges, dtype=bool, copy=True),
                    np.array(second_charges, dtype=bool, copy=True)]
    engaged_mask = np.array(engaged, dtype=bool, copy=True)
    failed = [np.zeros(engaged_mask.size, dtype=bool),
              np.zeros(engaged_mask.size, dtype=bool)]
    if resources is None:
        resources = (psychology_resources(engaged_mask.size),
                     psychology_resources(engaged_mask.size))
    outcome = FearOutcome(charge_masks[0], charge_masks[1], engaged_mask,
                          failed[0], failed[1])
    if round_index != 0:
        return outcome
    active = np.asarray(rows, dtype=np.intp)
    active = active[engaged_mask[active]]
    if active.size == 0:
        return outcome
    fighters = (first, second)
    states = (state_first, state_second)

    def ledger(index: int) -> LeadershipResources | None:
        """The Leadership resources of one side, if the caller supplies them."""
        return None if leadership is None else leadership[index]
    # Calling both verifies required opponent facts before any roll.
    first_fear, second_fear = causes_fear(first, second), causes_fear(second, first)
    # A voluntary charge must succeed before contact/charged reactions exist.
    for index, label in enumerate(("first", "second")):
        target, singer = fighters[index], fighters[1 - index]
        gate = _charge_gate(target, singer)
        compelled = has(target.global_effects, "condition.impetuous-charge")
        if gate is not None:
            testing = active[charge_masks[index][active]]
            if testing.size:
                passed = resolve_local_leadership(
                    target, states[index], testing, first=index == 0,
                    key=f"{key_prefix}.{label}.{gate}", context=context, rng=rng,
                    decisions=decisions, resources=ledger(index),
                    opponent=singer, contacting=False,
                )
                lost = testing[~passed]
                charge_masks[index][lost] = False
                failed[index][lost] = True
        if (has(singer.global_effects, "mechanic.beauty-of-the-sea")
                and has(target.global_effects, "sex.male")
                and not has(target.global_effects, "species.animal")
                and not compelled):
            testing = active[charge_masks[index][active]]
            if testing.size:
                passed = resolve_local_leadership(
                    target, states[index], testing, first=index == 0,
                    key=f"{key_prefix}.{label}.beauty-charge", context=context,
                    rng=rng, decisions=decisions, resources=ledger(index),
                    psychology=True, opponent=singer,
                )
                # The scalar operator also spends ``beauty.passed``; nothing in
                # the accepted engine reads that fact afterwards.
                lost = testing[~passed]
                charge_masks[index][lost] = False
                failed[index][lost] = True
    engaged_mask &= (
        (charge_masks[0] | charge_masks[1]) | ~(failed[0] | failed[1])
    )
    if not engaged_mask.any() or not (first_fear or second_fear):
        return FearOutcome(charge_masks[0], charge_masks[1], engaged_mask,
                           failed[0], failed[1])

    def morrs_servant(index: int) -> bool:
        return (has(fighters[1 - index].global_effects, "mechanic.morrs-servant")
                and has(fighters[index].global_effects, "nature.undead"))

    def needs_test(index: int) -> np.ndarray:
        fighter, enemy = fighters[index], fighters[1 - index]
        current, other = states[index], states[1 - index]
        charging = charge_masks[index]
        base = (current.condition == STANDING) & (other.condition != OUT)
        # These three printed exemptions remove the test entirely for the rows
        # they name, so the branches below never re-add them.
        exempt = np.zeros(base.size, dtype=bool)
        if has(fighter.global_effects, "mechanic.ere-we-go"):
            exempt |= charging
        if has(fighter.global_effects, "condition.impetuous-charge"):
            exempt |= charging
        if (has(fighter.global_effects, "mechanic.accustomed-to-fear")
                and any(has(enemy.global_effects, tag) for tag in
                        ("species.vampire", "undead-kind.skeleton", "undead-kind.spirit"))):
            exempt |= True
        special = morrs_servant(index) or fears_opponent_fire(fighter, enemy)
        result = base & special & ~exempt
        result |= (
            base & ~exempt & (not special)
            & causes_fear(enemy, fighter)
            & (not causes_fear(fighter, enemy)
               or has(fighter.global_effects, "mechanic.craven"))
            & ~current.frenzy
            & (not has(fighter.global_effects, "mechanic.fear-immunity"))
            & (not undead_foes_fear_immunity(fighter, enemy))
            & (not has(fighter.global_effects, "mechanic.psychology-immunity"))
        )
        return result

    def test_fear(index: int, label: str, suffix: str,
                  testing: np.ndarray) -> np.ndarray:
        fighter, enemy = fighters[index], fighters[1 - index]
        ordinary = not (morrs_servant(index) or fears_opponent_fire(fighter, enemy))
        passed = resolve_local_leadership(
            fighter, states[index], testing, first=index == 0,
            key=f"{key_prefix}.{label}.fear.{suffix}", context=context, rng=rng,
            decisions=decisions, resources=ledger(index),
            psychology=ordinary, fear=ordinary, opponent=enemy,
            contacting=suffix != "charge", close_combat=suffix == "charged",
            opponent_charges=charge_masks[1 - index],
        )
        return passed

    for index, label in enumerate(("first", "second")):
        testing = active[
            charge_masks[index][active] & engaged_mask[active] & needs_test(index)[active]
        ]
        if testing.size == 0:
            continue
        passed = test_fear(index, label, "charge", testing)
        lost = testing[~passed]
        if lost.size == 0:
            continue
        if has(fighters[index].global_effects, "mechanic.wheelo-impact"):
            resources[index].fear_hit_sixes[lost] = True
        else:
            charge_masks[index][lost] = False
            failed[index][lost] = True
    engaged_mask &= (
        (charge_masks[0] | charge_masks[1]) | ~(failed[0] | failed[1])
    )
    if engaged_mask.any():
        for index, label in enumerate(("first", "second")):
            testing = active[
                engaged_mask[active] & charge_masks[1 - index][active]
                & needs_test(index)[active]
            ]
            if testing.size == 0:
                continue
            passed = test_fear(index, label, "charged", testing)
            resources[index].fear_hit_sixes[testing[~passed]] = True
    return FearOutcome(charge_masks[0], charge_masks[1], engaged_mask,
                       failed[0], failed[1])


def _label(first: bool) -> str:
    """The modular side label a roll key is built from."""
    return "first" if first else "second"


def _prefix(key_prefix: str | None, round_index: int) -> str:
    """The round prefix the scalar operator builds its roll keys from."""
    return key_prefix if key_prefix is not None else f"round.{round_index}"


def resolve_feral_instinct(
    fighter: CompiledFighter, opponent: CompiledFighter, state: CombatState,
    rows: np.ndarray, *, first: bool, round_index: int,
    rng: np.random.Generator, resources: PsychologyResources,
    leadership: LeadershipResources | None = None,
    decisions: DecisionPolicy | None = None,
    context: PreparedDuelContext | None = None,
    key_prefix: str | None = None,
) -> np.ndarray:
    """Batch port of the Feral Instinct block in ``modular.rounds.resolve_round``.

    The Sabretusk's keeper is out of the duel, so the printed consequence is a
    movement restriction the duel never applies.  What the scalar round *does*
    is take the Leadership test on the beast's own turn and record the failure
    on its fighter state, which spends that row's Leadership resources and its
    dice.  ``rows`` must therefore be the active player's own rows, exactly as
    ``resolve_round`` reads ``state.first_player_turn`` before it tests.

    The returned mask is aligned to ``rows``; only tested rows are written, so a
    row that is out of action keeps the result its last own turn recorded.
    """
    rows = np.asarray(rows, dtype=np.intp)
    failed = np.zeros(rows.size, dtype=bool)
    if rows.size == 0 or not has(fighter.global_effects, "mechanic.feral-instinct"):
        return failed
    # ``current.active`` is ``condition != OUT``; the test has no other gate.
    positions = np.flatnonzero(state.condition[rows] != OUT)
    if positions.size == 0:
        return failed
    tested = rows[positions]
    passed = resolve_local_leadership(
        fighter, state, tested, first=first,
        key=f"{_prefix(key_prefix, round_index)}.{_label(first)}.feral-instinct",
        rng=rng, context=context, decisions=decisions, resources=leadership,
        opponent=opponent,
    )
    resources.feral_instinct_failed[tested] = ~passed
    failed[positions] = ~passed
    return failed


def resolve_lunatics(
    fighter: CompiledFighter, state: CombatState, rows: np.ndarray, *,
    first: bool, round_index: int, rng: np.random.Generator,
    resources: PsychologyResources, key_prefix: str | None = None,
) -> np.ndarray:
    """Batch port of the Lunatics producer in ``modular.rounds.resolve_round``.

    The printed chart is rolled for *both* warriors every round, not only on
    the roller's own turn: ``resolve_round`` loops ``is_first in (True, False)``
    with no turn and no condition gate, so this port does not add one either.
    A 1-3 grants Frenzy and a 4-6 the turn's Stupidity, and both halves
    accumulate -- the scalar round keeps ``current.frenzy or ...`` and
    ``current.lunatic_stupidity or ...``.  Duration and stacking remain the
    open source question the oracle flags; nothing is inferred here.

    The returned array is the per-``rows`` chart face.
    """
    rows = np.asarray(rows, dtype=np.intp)
    if rows.size == 0 or not has(fighter.global_effects, "mechanic.lunatics"):
        return np.zeros(rows.size, dtype=np.int8)
    rolls = rng.integers(1, 7, rows.size).astype(np.int8)
    resources.lunatic_result[rows] = rolls
    state.frenzy[rows] |= rolls <= 3
    resources.lunatic_stupidity[rows] |= rolls >= 4
    return rolls


#: The printed exclusions of the Amazon dance: the charmed foe must be able to
#: be charmed at all.
MESMERISING_DANCE_IMMUNITY = ("nature.undead", "species.lizardman",
                              "mechanic.charm-immunity")


def _charm_source_rows(owner_state: CombatState, target_state: CombatState,
                       rows: np.ndarray) -> np.ndarray:
    """Rows where a charming owner can perform and the target can be charmed.

    Both printed gates read the same facts the scalar round reads before either
    dance: the performer stands, is not held, is not holding and did not fail
    its Stupidity this turn, and the victim stands.
    """
    return rows[
        (owner_state.condition[rows] == STANDING)
        & ~owner_state.stupidity_failed[rows]
        & ~owner_state.grappled[rows]
        & ~owner_state.grappling[rows]
        & (target_state.condition[rows] == STANDING)
    ]


def resolve_mesmerising_dance(
    owner: CompiledFighter, target: CompiledFighter,
    owner_state: CombatState, target_state: CombatState, rows: np.ndarray, *,
    target_is_first: bool, round_index: int, rng: np.random.Generator,
    blocked: np.ndarray, leadership: LeadershipResources | None = None,
    decisions: DecisionPolicy | None = None,
    context: PreparedDuelContext | None = None,
    key_prefix: str | None = None,
) -> np.ndarray:
    """Batch port of the Mesmerising Dance gate in ``modular.rounds.resolve_round``.

    An individual charm test at the start of the combat phase: the victim takes
    an ordinary Leadership test in close combat and, failing it, strikes no one
    this phase.  Defence is untouched -- the gate writes only ``blocked``.
    Undead, Lizardmen and anything printed charm-immune never test at all.

    ``blocked`` is the victim side's full-batch attack bar, updated in place,
    and the returned mask is aligned to ``rows``.
    """
    rows = np.asarray(rows, dtype=np.intp)
    newly_blocked = np.zeros(rows.size, dtype=bool)
    if rows.size == 0 or not has(owner.global_effects, "mechanic.mesmerising-dance"):
        return newly_blocked
    if any(has(target.global_effects, tag) for tag in MESMERISING_DANCE_IMMUNITY):
        return newly_blocked
    testing = _charm_source_rows(owner_state, target_state, rows)
    if testing.size == 0:
        return newly_blocked
    passed = resolve_local_leadership(
        target, target_state, testing, first=target_is_first,
        key=f"{_prefix(key_prefix, round_index)}.{_label(target_is_first)}.mesmerising-dance",
        rng=rng, context=context, decisions=decisions, resources=leadership,
        opponent=owner, close_combat=True)
    lost = testing[~passed]
    blocked[lost] = True
    newly_blocked[np.isin(rows, lost)] = True
    return newly_blocked


def resolve_mark_of_shornaal(
    owner: CompiledFighter, target: CompiledFighter,
    owner_state: CombatState, target_state: CombatState, rows: np.ndarray, *,
    target_is_first: bool, round_index: int, rng: np.random.Generator,
    resources: PsychologyResources, blocked: np.ndarray,
    auto_hit: np.ndarray | None = None,
    leadership: LeadershipResources | None = None,
    decisions: DecisionPolicy | None = None,
    context: PreparedDuelContext | None = None,
    key_prefix: str | None = None,
) -> np.ndarray:
    """Batch port of the Mark of Shornaal gate in ``modular.rounds.resolve_round``.

    Three dice discarding the lowest, taken as a Psychology test, and once a row
    has passed it never tests again for the rest of the battle
    (``mark-of-shornaal.passed`` on the *victim's* spent resources, kept here in
    that side's :class:`PsychologyResources`).  A failure both bars the victim's
    attacks and makes every incoming hit automatic.

    ``resources`` and ``leadership`` are the *victim's* ledgers, because the
    victim is the model that tests and that spends.  ``blocked`` and
    ``auto_hit`` are the victim side's full-batch arrays, updated in place; the
    returned mask of newly failed rows is aligned to ``rows``.
    """
    rows = np.asarray(rows, dtype=np.intp)
    newly_failed = np.zeros(rows.size, dtype=bool)
    if rows.size == 0 or not has(owner.global_effects, "mechanic.mark-of-shornaal"):
        return newly_failed
    if has(target.global_effects, "mechanic.charm-immunity"):
        return newly_failed
    testing = _charm_source_rows(owner_state, target_state, rows)
    testing = testing[~resources.shornaal_passed[testing]]
    if testing.size == 0:
        return newly_failed
    passed = resolve_local_leadership(
        target, target_state, testing, first=target_is_first,
        key=f"{_prefix(key_prefix, round_index)}.{_label(target_is_first)}.shornaal",
        rng=rng, context=context, decisions=decisions, resources=leadership,
        psychology=True, discard_lowest=True, opponent=owner, close_combat=True)
    resources.shornaal_passed[testing[passed]] = True
    lost = testing[~passed]
    blocked[lost] = True
    if auto_hit is not None:
        auto_hit[lost] = True
    newly_failed[np.isin(rows, lost)] = True
    return newly_failed
