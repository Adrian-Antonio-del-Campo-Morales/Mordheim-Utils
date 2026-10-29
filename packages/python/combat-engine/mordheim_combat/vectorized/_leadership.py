"""Vectorized engine: local Leadership tests ported to batch columns.

This module ports ``modular.leadership`` to one call per row set.  Every fact
the scalar function reads that ``CombatState`` does not carry (the
once-per-battle Leadership resources) lives in :class:`LeadershipResources`,
owned by the round driver and threaded through the batch loop.

The supplied local geometry stays caller-supplied: providers, sides, bands and
distances come from ``PreparedDuelContext``.  This module never produces a
position and never searches a whole warband, exactly as the scalar operator
does not.

The scalar ``resolve_local_leadership`` remains the single source of the
rules; this is a per-row projection of its eligibility decisions, its dice and
its resource spending.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, replace

from mordheim_core.context import PreparedDuelContext
from mordheim_core.dice import AlwaysAccept, DecisionPolicy
from mordheim_core.models import CompiledFighter, EffectSet

from mordheim_combat.vectorized._types import CombatState, OUT, STANDING, has


#: The per-battle Leadership resources the modular ``FighterState`` keeps in
#: ``resources_spent``.  ``CombatState`` has no generic resource set, so the
#: batch keeps them per row here; ``True`` means already spent.
@dataclass(slots=True)
class LeadershipResources:
    holy_relic: np.ndarray
    first_failed: np.ndarray
    poetry_first: np.ndarray
    one_roll_reroll: np.ndarray
    ranalds_luck: np.ndarray


def leadership_resources(count: int) -> LeadershipResources:
    """Fresh, unspent Leadership resources for ``count`` rows of one fighter."""
    return LeadershipResources(
        holy_relic=np.zeros(count, dtype=bool),
        first_failed=np.zeros(count, dtype=bool),
        poetry_first=np.zeros(count, dtype=bool),
        one_roll_reroll=np.zeros(count, dtype=bool),
        ranalds_luck=np.zeros(count, dtype=bool),
    )


def _leader_radius(effect: EffectSet) -> int:
    """The printed supplied-Leader radius of one provider's own effect set."""
    return (12 if has(effect, "mechanic.leader-twelve")
            else 4 if has(effect, "mechanic.leader-four")
            else 6)


def _supplied_provider(provider, bands):
    """Printed supplied-provider contract of one nearby local participant.

    Returns ``(radius, consequence)`` or ``None``.  ``consequence`` is one of
    ``leader`` (the provider lends his own Leadership), ``relay`` (the provider
    relays a leader's Leadership, never his own) or ``songster`` (the provider
    grants a re-roll with +1 without lending any value).
    """
    effect = provider.fighter.global_effects
    # Printed Slave Driver: the Overseer lends his Leadership within 3 inches,
    # widened to 6 while he carries a scourge (his own supplied fact).
    if has(effect, "mechanic.slave-driver"):
        scourge = has(effect, "condition.scourge-armed") or any(
            has(weapon, "weapon.pirate-scourge") for weapon in
            (provider.fighter.main_weapon, provider.fighter.off_hand or EffectSet()))
        return (6 if scourge else 3, "leader")
    if has(effect, "mechanic.songster"):
        return (6, "songster")
    if not bands.intersection(effect.tags):
        return None
    # Printed Relay Orders: the Adjutant relays the leader's Leadership within
    # six inches, twelve while he carries Battle Tongue.
    if has(effect, "mechanic.relay-orders"):
        return (_leader_radius(effect), "relay")
    # Printed Songster: a friendly model within six inches re-rolls a failed
    # Leadership test with +1 to Leadership; no Leadership value is lent.
    # The ordinary Leader rule, in its printed radius.
    if has(effect, "mechanic.leader-six"):
        return (6 if has(effect, "mechanic.dim-witted-leader") else _leader_radius(effect), "leader")
    return None


def _relayed_leader(context, provider, bands):
    """The supplied Leader an Adjutant relays, or ``None`` while he cannot use one.

    The printed prerequisite is that the Adjutant is able to use his leader's
    Leadership, so the leader must be supplied on the Adjutant's own side and
    band and be within the Adjutant's own borrow radius.
    """
    for candidate in context.facts.nearby:
        if candidate.participant_id == provider.participant_id:
            continue
        effect = candidate.fighter.global_effects
        if (candidate.side_id != provider.side_id or candidate.condition != "standing"
                or not bands.intersection(effect.tags)
                or not has(effect, "mechanic.leader-six")):
            continue
        if context.distance(provider.participant_id, candidate.participant_id) <= _leader_radius(effect):
            return candidate
    return None


def _instructing_leader(context, participant_id, side, bands, inches):
    """A supplied same-band Leader of ``side`` within ``inches`` and in action.

    The printed Devoted clause names the Warrior Priest and the printed Broken
    Spirit clause the Slave Merchant; each is that band's only Leader profile,
    so the supplied Leader of the recipient's own band is that named model.  A
    Warrior Priest who is only Knocked Down still grants the printed re-roll,
    because the clause prints no requirement that he stand.
    """
    for candidate in context.facts.nearby:
        effect = candidate.fighter.global_effects
        if (candidate.side_id != side or candidate.condition == "out"
                or not bands.intersection(effect.tags)
                or not has(effect, "mechanic.leader-six")):
            continue
        if context.distance(participant_id, candidate.participant_id) <= inches:
            return True
    return False


def undead_foes_fear_immunity(fighter: CompiledFighter, opponent: CompiledFighter | None) -> bool:
    """Dreamwalkers of Morr: Fearless Against the Undead Servants of Necromancers.

    The Fear test is skipped only when the Fear-causing opponent itself carries
    one of the canonical duel identities named by the source: a vampire
    (``species.vampire``), a necromancer (``identity.necromancer``), or an
    undead follower (``nature.undead``).  A necromancer need not be Undead,
    and being a spellcaster does not identify one.  Other enemies and other
    Psychology tests retain their ordinary rules.
    """
    return (opponent is not None
            and has(fighter.global_effects, "mechanic.undead-foes-no-fear")
            and (has(opponent.global_effects, "species.vampire")
                 or has(opponent.global_effects, "identity.necromancer")
                 or has(opponent.global_effects, "nature.undead")))


def _personal_die(
    fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
    rng: np.random.Generator, key: str, die: np.ndarray,
    decisions: DecisionPolicy, resources: LeadershipResources | None,
    close_combat: bool, die_rerolled: np.ndarray,
) -> np.ndarray:
    """Port of ``OwnedRollDice.roll`` for one already-drawn die.

    ``die_rerolled`` is this die's own flag, not the test's: the scalar wrapper
    resets ``rerolled`` for every roll request, so a Scryer may repeat each die
    of the same Leadership test.  The per-roll choices are taken once for the
    row set, as every other batch decision in this engine is: a policy that
    depends on the individual row is not asked per row here.
    """
    effects = fighter.global_effects
    # Ranald's Luck: one owned roll is adjusted by one, once per battle.
    if resources is not None and has(effects, "mechanic.ranalds-luck"):
        available = ~resources.ranalds_luck[rows]
        if available.any():
            if decisions.choose(f"{key}.ranalds-luck.plus", fighter):
                die = np.where(available, die + 1, die).astype(np.int16)
                resources.ranalds_luck[rows[available]] = True
            elif decisions.choose(f"{key}.ranalds-luck.minus", fighter):
                die = np.where(available, die - 1, die).astype(np.int16)
                resources.ranalds_luck[rows[available]] = True
    # Oracle / Augur: one owned roll may be re-rolled, once per battle.
    if (resources is not None and ".reroll" not in key
            and any(has(effects, tag) for tag in
                    ("mechanic.oracle", "mechanic.augur-one-roll-reroll"))):
        available = ~resources.one_roll_reroll[rows]
        if available.any() and decisions.choose(f"{key}.one-roll-reroll", fighter):
            die = np.where(available, rng.integers(1, 7, rows.size), die).astype(np.int16)
            resources.one_roll_reroll[rows[available]] = True
            die_rerolled |= available
    # Skill: Luck re-rolls one failed die of its bearer, once per battle.
    if has(effects, "skill.luck") and ".reroll" not in key:
        available = ~state.luck_used[rows] & ~die_rerolled
        if available.any() and decisions.choose(f"{key}.luck", fighter):
            die = np.where(available, rng.integers(1, 7, rows.size), die).astype(np.int16)
            state.luck_used[rows[available]] = True
            die_rerolled |= available
    # Scryer re-rolls an owned close-combat die with no resource: the second
    # result must be accepted, so only this die is left alone once re-rolled;
    # the next die of the same test is a fresh owned roll and may repeat too.
    if close_combat and has(effects, "mechanic.scryer") and ".reroll" not in key:
        available = ~die_rerolled
        if available.any() and decisions.choose(f"{key}.scryer", fighter):
            die = np.where(available, rng.integers(1, 7, rows.size), die).astype(np.int16)
            die_rerolled |= available
    return die


def _leadership_dice(
    fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
    rng: np.random.Generator, key: str, count: int,
    decisions: DecisionPolicy, resources: LeadershipResources | None,
    close_combat: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """Draw ``count`` owned d6 per row; return them and the re-rolled mask.

    The returned mask covers the whole test (the scalar ``_rerolled_results``
    gate for the final Leadership re-roll), while each die keeps its own flag so
    a per-die resource such as Scryer can repeat every die independently.
    """
    results = np.empty((count, rows.size), dtype=np.int16)
    any_rerolled = np.zeros(rows.size, dtype=bool)
    for index in range(count):
        die = rng.integers(1, 7, rows.size).astype(np.int16)
        if decisions is not None:
            die_rerolled = np.zeros(rows.size, dtype=bool)
            die = _personal_die(
                fighter, state, rows, rng, f"{key}.{index}", die,
                decisions, resources, close_combat, die_rerolled,
            )
            any_rerolled |= die_rerolled
        results[index] = die
    return results, any_rerolled


def _test_total(rolls: np.ndarray, *, discard_highest: bool,
                discard_lowest: bool,
                discard_highest_rows: np.ndarray | None = None) -> np.ndarray:
    """Port of ``phases.resolve_leadership``'s two/three-die reading."""
    if discard_lowest:
        return rolls.sum(axis=0) - rolls.min(axis=0)
    if discard_highest:
        return rolls.sum(axis=0) - rolls.max(axis=0)
    if discard_highest_rows is not None and discard_highest_rows.any():
        two = rolls[:2].sum(axis=0)
        if discard_highest_rows.all():
            return rolls.sum(axis=0) - rolls.max(axis=0)
        return np.where(discard_highest_rows, rolls.sum(axis=0) - rolls.max(axis=0), two)
    return rolls.sum(axis=0)


def resolve_local_leadership(
    fighter: CompiledFighter, state: CombatState, rows: np.ndarray, *,
    first: bool, key: str, rng: np.random.Generator,
    context: PreparedDuelContext | None = None,
    decisions: DecisionPolicy | None = None,
    resources: LeadershipResources | None = None,
    psychology: bool | np.ndarray = False, stupidity: bool = False,
    fear: bool = False, discard_lowest: bool = False,
    opponent: CompiledFighter | None = None, own_value_only: bool = False,
    contacting: bool = True, close_combat: bool = False,
    opponent_charges: np.ndarray | None = None,
) -> np.ndarray:
    """Batch port of ``modular.leadership.resolve_local_leadership``.

    ``rows`` names the simulations whose operation takes the test; the
    returned boolean array is aligned to ``rows``.  Only those rows are rolled
    and only those rows spend a resource.  ``psychology`` may be a per-row mask
    because the drunken result that gates it is per row; every other switch is
    a property of the compiled fighter.

    ``opponent_charges`` is the opponent's per-row charge mask, read by the
    printed ``fear-immunity-undead-chargers`` exemption.
    """
    rows = np.asarray(rows, dtype=np.intp)
    if rows.size == 0:
        return np.zeros(0, dtype=bool)
    # The scalar operator resolves a missing opponent from the supplied context
    # before it reads any opponent-side fact, the Fear exemptions included.
    if opponent is None and context is not None:
        enemy_id = context.facts.second_id if first else context.facts.first_id
        opponent = context.participant(enemy_id).fighter
    # A per-row charge mask is the batch contract; a single supplied fact is
    # broadcast so a caller with one snapshot need not build an array.
    opponent_charge = (
        None if opponent_charges is None
        else np.broadcast_to(np.asarray(opponent_charges, dtype=bool), state.wounds.shape)
    )
    # The scalar pipeline resolves every duel with a policy; ``None`` is this
    # engine's accept-all default, so the personal roll resources are offered
    # exactly as ``OwnedRollDice`` offers them.
    policy = decisions or AlwaysAccept()
    effects = fighter.global_effects
    first_failure = has(effects, "mechanic.first-failed-leadership-reroll")
    poetry = has(effects, "condition.poetry-victorious-leader")
    holy_relic = has(effects, "defence.holy-relic")
    # ``skill.luck`` spends ``CombatState.luck_used``, so it needs no ledger;
    # only the resources without a column require one.
    roll_resource = any(has(effects, tag) for tag in
                        ("mechanic.ranalds-luck", "mechanic.oracle",
                         "mechanic.augur-one-roll-reroll"))
    if resources is None and (first_failure or holy_relic or roll_resource or poetry):
        # The scalar operator refuses to run a persistent resource without the
        # fighter state that carries it; dropping the spend silently would make
        # the second call in the same battle replay a used resource.
        raise ValueError("persistent Leadership resource requires the returned fighter state")
    passed = np.ones(rows.size, dtype=bool)
    settled = np.zeros(rows.size, dtype=bool)
    psychology_mask = (np.full(rows.size, bool(psychology)) if np.ndim(psychology) == 0
                       else np.asarray(psychology, dtype=bool)[rows])
    if psychology_mask.any():
        settled |= state.frenzy[rows] & psychology_mask
        settled |= has(effects, "mechanic.psychology-immunity") & psychology_mask
    if fear:
        # Instinctual Violence prints the exemption only for an Undead charger,
        # so both the opponent's identity and the direction of the charge are
        # read.
        if (has(effects, "mechanic.fear-immunity-undead-chargers")
                and opponent is not None
                and has(opponent.global_effects, "nature.undead")
                and opponent_charge is not None):
            settled |= opponent_charge[rows]
        if has(effects, "mechanic.fear-immunity"):
            settled |= True
        if undead_foes_fear_immunity(fighter, opponent):
            settled |= True
    if has(effects, "mechanic.automatic-leadership"):
        settled |= True
    if holy_relic and resources is not None:
        available = ~settled & ~resources.holy_relic[rows]
        if available.any():
            resources.holy_relic[rows[available]] = True
            settled |= available
    pending = ~settled
    if not pending.any():
        return passed
    if has(effects, "mechanic.sigmar-enlightened"):
        enemy = opponent
        if enemy is None and context is not None:
            enemy_id = context.facts.second_id if first else context.facts.first_id
            enemy = context.participant(enemy_id).fighter
        if enemy is None:
            raise ValueError("Enlightened requires the duel opponent's explicit facts")
        if any(has(enemy.global_effects, tag) for tag in (
                "species.orc", "species.goblin", "warband-group.chaotic", "nature.daemon",
                "nature.possessed", "identity.chaos-follower")):
            settled |= True
            pending = ~settled
            if not pending.any():
                return passed

    value = fighter.characteristics.leadership
    # Handle Animal belongs to the Herder, not to the animal receiving his
    # Leadership. Canonical identity scopes this provider-only concession.
    squig_recipient = fighter.fighter_id == "night-goblins-web:cave-squigs"
    handler_only = (squig_recipient
                    or has(effects, "mechanic.handler-leadership"))
    if handler_only and fighter.stupidity_leadership is not None:
        value = fighter.stupidity_leadership
    supplied_reroll = False
    songster_reroll = False
    if context is not None:
        participant_id = context.facts.first_id if first else context.facts.second_id
        side = context.participant(participant_id).side_id
        # A local side and canonical band identify this supported warband group.
        # Do not lend a leader's value to opposing or foreign-band participants.
        bands = {tag for tag in effects.tags if tag.startswith("band.")}
        if handler_only and not own_value_only:
            for provider in context.facts.nearby:
                provider_effect = provider.fighter.global_effects
                if squig_recipient:
                    eligible = (provider.fighter.fighter_id == "night-goblins-web:squig-herder"
                                and bands.intersection(provider_effect.tags)
                                and has(provider_effect, "mechanic.handler-leadership"))
                    prodder = any(has(weapon, "weapon.squig-prodder")
                                  for weapon in (provider.fighter.main_weapon,
                                                 provider.fighter.off_hand or EffectSet()))
                    radius = 12 if prodder else 6
                else:
                    eligible = has(provider_effect, "mechanic.bear-handler")
                    radius = 6
                if (provider.side_id == side and provider.condition != "out"
                        and eligible
                        and context.distance(participant_id, provider.participant_id) <= radius
                        and policy.choose(f"{key}.handler.{provider.participant_id}", fighter)):
                    value = provider.fighter.characteristics.leadership
                    break
        if has(effects, "mechanic.broken-spirit"):
            # Printed Broken Spirit: the Eunuch automatically passes while the
            # Slave Merchant is not out of action.  The clause prints no range,
            # so the supplied leader's distance is not read at all.
            for candidate in context.facts.nearby:
                effect = candidate.fighter.global_effects
                if (candidate.side_id == side and candidate.condition != "out"
                        and bands.intersection(effect.tags)
                        and has(effect, "mechanic.leader-six")):
                    return passed
        if (has(effects, "mechanic.devoted")
                and _instructing_leader(context, participant_id, side, bands, 12)):
            # Printed Devoted: the Hound re-rolls a failed Leadership check
            # while the Warrior Priest is within twelve inches.
            supplied_reroll = True
        # Printed Songster: any friendly model within six inches of the supplied
        # Minstrel may re-roll a failed Leadership test with +1 to Leadership.
        # The clause qualifies the recipient, not the Minstrel, so the gift does
        # not depend on the recipient borrowing a leader's value and a Knocked
        # Down Minstrel still sings; only his being out of action ends it.
        for provider in context.facts.nearby:
            contract = _supplied_provider(provider, bands)
            if (provider.side_id != side or provider.condition == "out"
                    or contract is None or contract[1] != "songster"):
                continue
            if context.distance(participant_id, provider.participant_id) <= contract[0]:
                songster_reroll = True
        if (not handler_only and not own_value_only
                and not has(effects, "mechanic.own-leadership")):
            usable = []
            for provider in context.facts.nearby:
                if (provider.side_id != side or provider.condition != "standing"
                        or has(provider.fighter.global_effects, "condition.mouth-sewn")):
                    continue
                if (has(provider.fighter.global_effects, "mechanic.slave-driver")
                        and not has(effects, "identity.slave")):
                    continue
                contract = _supplied_provider(provider, bands)
                if contract is None:
                    continue
                radius, consequence = contract
                if context.distance(participant_id, provider.participant_id) > radius:
                    continue
                if consequence == "songster":
                    songster_reroll = True
                    continue
                if consequence == "relay":
                    relayed = _relayed_leader(context, provider, bands)
                    if relayed is None:
                        continue
                    usable.append((provider, provider.fighter.global_effects,
                                   relayed.fighter.characteristics.leadership))
                else:
                    usable.append((provider, provider.fighter.global_effects,
                                   7 if has(provider.fighter.global_effects, "mechanic.dim-witted-leader")
                                   else provider.fighter.characteristics.leadership))
            # Second in Command: the printed fallback Leader is offered only while
            # no other standing leader of the same warband can lend his Leadership
            # (directly or through a relay), and a fallback never suppresses
            # itself.  A knocked-down or absent senior leader leaves the fallback.
            senior = any(not has(provider_effect, "mechanic.leader-fallback")
                         for _, provider_effect, _ in usable)
            borrowed = False
            for provider, provider_effect, lent in usable:
                supplied_reroll = supplied_reroll or has(provider_effect, "mechanic.undivided-leader") or (
                    has(provider_effect, "mechanic.wizened-halfling")
                    and has(effects, "species.halfling"))
                if senior and has(provider_effect, "mechanic.leader-fallback"):
                    continue
                if not borrowed and policy.choose(
                        f"{key}.leader.{provider.participant_id}", fighter):
                    value = lent
                    borrowed = True
    values = np.full(rows.size, -1 if value is None else int(value), dtype=np.int32)
    if poetry and resources is not None:
        available = ~resources.poetry_first[rows] & pending
        if available.any():
            resources.poetry_first[rows[available]] = True
            if value is not None:
                values[available] += 1
    # Printed Mob: the caller supplies how many other allied Peasants are within
    # three inches, so the printed +1 Leadership each is added without
    # simulating the group or any table position.
    if value is not None and has(effects, "mechanic.mob-leadership"):
        values += fighter.mob_allies
    # Enchanting Beauty is the opponent's fact projected onto this fighter by
    # `apply_opponent_leadership`; the condition already carries the printed
    # Undead/Daemon exemption. Only base contact applies it, so a charge's own
    # out-of-contact test is untouched.
    if (contacting and value is not None
            and has(effects, "condition.enchanting-beauty")):
        values -= 1
    # Ghostly Howl: the tested enemy's Leadership drops by D6 on a fear test
    # while the howling bearer faces it.  The duel supplies the proximity of its
    # two participants; the printed 6" radius to any other unit stays outside.
    if (fear and value is not None and opponent is not None
            and has(opponent.global_effects, "mechanic.ghostly-howl")):
        values -= rng.integers(1, 7, rows.size).astype(np.int32)
    if stupidity and value is not None:
        values += fighter.stupidity_leadership_bonus
    if (values < 0).any():
        raise ValueError("Leadership test requires explicit non-negative integer Leadership")
    # The tested model keeps its dice benefit when borrowing a leader's value.
    # Leadership's own Cold Blooded is a property of the fighter; the
    # psychology half is per row because the drunken result gates it.
    cold_blooded_psychology = (has(effects, "mechanic.cold-blooded-psychology")
                               & psychology_mask)
    discard_highest = has(effects, "mechanic.cold-blooded-leadership")
    # Only the rows that actually test are rolled: a settled row spends no die
    # and no per-roll resource.
    pending_positions = np.flatnonzero(pending)
    tested_rows = rows[pending_positions]
    tested_values = values[pending_positions]
    tested_psychology = cold_blooded_psychology[pending_positions]
    count = 3 if (discard_lowest or discard_highest or tested_psychology.any()) else 2
    rolls, die_rerolled = _leadership_dice(
        fighter, state, tested_rows, rng, key, count, policy, resources,
        close_combat=close_combat,
    )
    roll_passed = _test_total(
        rolls, discard_highest=discard_highest and not discard_lowest,
        discard_lowest=discard_lowest, discard_highest_rows=tested_psychology,
    ) <= tested_values
    passed[pending_positions] = roll_passed
    # Declining the first failure does not reserve a later failure instead.
    first_failed_rows = np.zeros(tested_rows.size, dtype=bool)
    if first_failure and resources is not None:
        first_failed_rows = ~resources.first_failed[tested_rows] & ~roll_passed
        if first_failed_rows.any():
            resources.first_failed[tested_rows[first_failed_rows]] = True
    mandatory = has(effects, "mechanic.mandatory-leadership-reroll")
    eligible = (first_failed_rows | mandatory | supplied_reroll | songster_reroll
                | has(effects, "mechanic.leadership-reroll")
                | has(effects, "condition.command.raise-our-insignia-active")
                | (fear and has(effects, "mechanic.fear-reroll")))
    rerollable = ~roll_passed & ~die_rerolled & eligible
    if rerollable.any() and (mandatory or policy.choose(f"{key}.reroll", fighter)):
        # Reuse the chosen threshold and dice convention; never re-roll a roll
        # that a personal resource already re-rolled.
        reroll_values = np.where(
            songster_reroll, np.minimum(10, tested_values + 1), tested_values,
        )[rerollable]
        reroll_rows = tested_rows[rerollable]
        rerolls, _ = _leadership_dice(
            fighter, state, reroll_rows, rng, f"{key}.reroll", count,
            policy, resources, close_combat=close_combat,
        )
        reroll_passed = _test_total(
            rerolls, discard_highest=discard_highest and not discard_lowest,
            discard_lowest=discard_lowest,
            discard_highest_rows=tested_psychology[rerollable],
        ) <= reroll_values
        passed[pending_positions[rerollable]] = reroll_passed
    return passed


# ---------------------------------------------------------------------------
# Command conditions issued before the duel
#
# ``modular/rounds.py`` opens every round with one block that lights the
# already-active individual Command effects its comment describes: "Only
# already-active individual Command effects are supplied; no casting, no
# issuing Knight, no range and no group lifecycle is simulated."  The three
# Commands below are that block's Leadership-side members; the round driver
# owns the call, exactly as the scalar round owns the block.
# ---------------------------------------------------------------------------

#: Printed exclusion of ``mechanic.sea-shanty``: the song reaches a living
#: recipient only.  ``modular/rounds.py`` inlines this same tuple beside the
#: test; it is a clause of the Shanty, not a shared engine predicate.
SEA_SHANTY_NON_LIVING_TAGS = (
    "nature.undead", "nature.possessed", "nature.daemon",
    "nature.construct", "nature.non-living",
)


def _with_tags(fighter: CompiledFighter, *tags: str) -> CompiledFighter:
    """A copy of ``fighter`` whose global effects also carry ``tags``."""
    effect = fighter.global_effects
    return replace(fighter, global_effects=replace(effect, tags=(*effect.tags, *tags)))


def apply_command_conditions(fighter: CompiledFighter, *, round_index: int,
                             ) -> CompiledFighter:
    """Light this round's Leadership-side Command conditions on one bearer.

    Port of the two Command clauses ``modular/rounds.py`` resolves in its
    round-opening block:

    * ``condition.command.follow-me-mine-pugnacious-ones`` adds
      ``condition.command.follow-me-active`` in the opening round only.  The
      consequence (its +1 To Hit in melee) is already ported in
      ``vectorized/_operators.py``, which reads the ``-active`` tag.
    * ``condition.command.raise-our-insignia`` adds
      ``condition.command.raise-our-insignia-active`` in the opening round
      only.  The consequence (the failed-Leadership re-roll) is already ported
      in ``resolve_local_leadership`` above, which reads the ``-active`` tag.
      The round driver must call :func:`expire_raise_our_insignia` at the
      Shooting boundary, as the scalar round does.

    The same oracle block also lights ``condition.righteous-charge-active``
    and the Poetry attack bonus; neither is a Leadership rule and neither is
    applied here.
    """
    if round_index != 0:
        return fighter
    effect = fighter.global_effects
    tags = []
    if has(effect, "condition.command.follow-me-mine-pugnacious-ones"):
        tags.append("condition.command.follow-me-active")
    if has(effect, "condition.command.raise-our-insignia"):
        tags.append("condition.command.raise-our-insignia-active")
    return _with_tags(fighter, *tags) if tags else fighter


def expire_raise_our_insignia(fighter: CompiledFighter) -> CompiledFighter:
    """Drop ``condition.command.raise-our-insignia-active`` from one bearer.

    Raise Our Insignia expires at the Shooting boundary: after the supplied
    Recovery/Movement tests (Stupidity and the opening round's Fear, both of
    which still enjoy the re-roll) and before that phase's melee.  The scalar
    round strips the tag at exactly that point.
    """
    effect = fighter.global_effects
    if not has(effect, "condition.command.raise-our-insignia-active"):
        return fighter
    return replace(fighter, global_effects=replace(effect, tags=tuple(
        tag for tag in effect.tags
        if tag != "condition.command.raise-our-insignia-active")))


def apply_death_fighting(
    fighter: CompiledFighter, *, round_index: int, owner_first: bool,
    initial_first_turn: np.ndarray,
) -> tuple[CompiledFighter, np.ndarray | None]:
    """Port of ``condition.command.art-thou-ready-to-die-fighting``.

    The printed Command raises its bearer's out-of-action threshold to 6 (the
    Hard to Kill chart) while it lasts.  The scalar round writes

    ``round_index < (2 if initial_first == owner_first else 1)``

    so the bearer keeps the threshold for the opening round always, and for
    the second round only while he owned the opening player turn.  That owner
    is a per-row fact in this engine (``initial_first_turn``), so the second
    round is a row mask rather than a property of the compiled fighter.

    Returns ``(fighter, rows)``.  ``fighter`` already carries the raised
    threshold whenever every row is covered (the opening round), so the usual
    case needs no row work at all.  ``rows`` is the boolean mask the driver
    must still patch per row (the second round), or ``None`` when there is
    nothing left to do.  Feed ``rows`` straight to
    :func:`patch_death_fighting` once the per-row equipment is projected.
    """
    if not has(fighter.global_effects, "condition.command.art-thou-ready-to-die-fighting"):
        return fighter, None
    if round_index == 0:
        return with_death_fighting_threshold(fighter), None
    if round_index > 1:
        return fighter, None
    # The second round belongs to the bearer only while he opened the duel.
    owner_opened = np.asarray(initial_first_turn, dtype=bool)
    rows = owner_opened if owner_first else ~owner_opened
    if rows.all():
        return with_death_fighting_threshold(fighter), None
    return (fighter, rows) if rows.any() else (fighter, None)


def with_death_fighting_threshold(fighter: CompiledFighter) -> CompiledFighter:
    """One bearer whose injury chart only puts him out on a natural six."""
    return replace(fighter, global_effects=replace(
        fighter.global_effects, out_of_action_threshold=6))


def patch_death_fighting(equipment: dict[int, CompiledFighter],
                         rows: np.ndarray | None,
                         active: np.ndarray | None = None) -> None:
    """Raise the out-of-action threshold of ``rows`` in a per-row projection.

    ``equipment`` is the driver's row -> ``CompiledFighter`` map (the same one
    Black Hunger patches).  ``rows`` is the mask :func:`apply_death_fighting`
    returned; ``active`` optionally restricts the patch to the rows the round
    still resolves.  A ``None`` mask is a no-op, so the driver needs no branch.
    """
    if rows is None:
        return
    selected = rows if active is None else rows & np.asarray(active, dtype=bool)
    for value in np.flatnonzero(selected):
        row = int(value)
        equipment[row] = with_death_fighting_threshold(equipment[row])


def sea_shanty_losses(
    owner: CompiledFighter, target: CompiledFighter,
    owner_state: CombatState, target_state: CombatState,
    rows: np.ndarray, rng: np.random.Generator,
    resources: LeadershipResources | None, decisions: DecisionPolicy | None,
    context: PreparedDuelContext | None, *, first: bool, round_index: int,
    first_player_turn: np.ndarray, engaged: np.ndarray,
) -> np.ndarray:
    """The Sea Shanty's optional contact song, per row.

    Port of the Shanty branch of ``modular/rounds.py``'s combat-phase loop.
    The singer is in base contact with his listener; the listener takes a
    close-combat Leadership test and loses one attack this phase when he
    fails.  Two printed sources share the behaviour and differ only in who may
    be sung to:

    * ``mechanic.sea-shanty`` reaches a living recipient only (the
      :data:`SEA_SHANTY_NON_LIVING_TAGS` exclusion) and is sung in the
      singer's own player turn.
    * ``mechanic.sea-shanty-psychology`` is a Psychology source instead: it
      excludes a Frenzied listener and a Psychology-immune one, and carries no
      own-turn restriction at all.

    A bearer of both sings the plain Shanty, as the scalar ``next(...)`` over
    the two tags does.

    ``resources`` is the **listener's** Leadership ledger, not the singer's:
    the test belongs to ``target``.  ``first`` names the singer's side.  The
    returned boolean array is aligned to the whole batch and marks the rows
    where ``target`` loses one attack; the driver folds it into the same
    attack-pool loss it already applies for the Halfling Elder's belch.
    """
    size = owner_state.wounds.size
    lost = np.zeros(size, dtype=bool)
    effect = owner.global_effects
    shanty = next((tag for tag in ("mechanic.sea-shanty", "mechanic.sea-shanty-psychology")
                   if has(effect, tag)), None)
    if shanty is None:
        return lost
    # Supplied contact decides the song, exactly as the scalar round reads it:
    # a supplied contact list replaces the sampled engagement outright.
    contacting = np.asarray(engaged, dtype=bool)
    if context is not None and context.facts.contacts is not None:
        own_id = context.facts.first_id if first else context.facts.second_id
        enemy_id = context.facts.second_id if first else context.facts.first_id
        if not any({a, b} == {own_id, enemy_id} for a, b in context.facts.contacts):
            return lost
        contacting = np.ones(size, dtype=bool)
    own_turn = np.asarray(first_player_turn, dtype=bool)
    if not first:
        own_turn = ~own_turn
    excluded = np.zeros(size, dtype=bool)
    if shanty == "mechanic.sea-shanty":
        if any(has(target.global_effects, tag) for tag in SEA_SHANTY_NON_LIVING_TAGS):
            return lost
        # The plain Shanty is sung in its own player turn only.
        own_shanty_phase = own_turn
    else:
        if has(target.global_effects, "mechanic.psychology-immunity"):
            return lost
        # Frenzy is a per-row fact of the listener, so its exclusion is too.
        excluded = target_state.frenzy
        own_shanty_phase = np.ones(size, dtype=bool)
    # A Massively Built warrior who spent this round's turn sings nothing.
    lost_owner_turn = owner_state.massively_built_lost_turn & own_turn
    eligible = np.zeros(size, dtype=bool)
    eligible[np.asarray(rows, dtype=np.intp)] = True
    eligible &= contacting & own_shanty_phase & ~excluded & ~lost_owner_turn
    eligible &= (owner_state.condition == STANDING) & ~owner_state.stupidity_failed
    eligible &= ~(owner_state.grappled | owner_state.grappling)
    eligible &= target_state.condition != OUT
    tested = np.flatnonzero(eligible)
    if tested.size == 0:
        return lost
    key = f"round.{round_index}.{'first' if first else 'second'}.sea-shanty"
    policy = decisions or AlwaysAccept()
    if not policy.choose(key, owner):
        return lost
    passed = resolve_local_leadership(
        target, target_state, tested, first=not first, key=f"{key}.leadership",
        rng=rng, context=context, decisions=decisions, resources=resources,
        opponent=owner, close_combat=True)
    lost[tested[~passed]] = True
    return lost
