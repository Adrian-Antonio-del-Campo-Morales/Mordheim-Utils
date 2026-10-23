"""Vectorized engine: per-round state machines, batch loop and the
public simulate_duel/available_backends entry points."""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass, replace
from mordheim_core.context import prepare_duel_context
from mordheim_core.dice import DecisionPolicy
from mordheim_core.models import CompiledFighter, DuelContext, DuelRequest, DuelResult, EffectSet, SimulationCancelled
from mordheim_combat.vectorized._types import CombatState, KNOCKED_DOWN, OUT, PARALYZED, STANDING, STUNNED, VectorBatchObservation, _parry_capacity, has
from mordheim_combat.vectorized._operators import _characteristic_test, allocate_attack_weapons, attack_count, effective_initiative, opposed_attack_count, priority, round_weapon_attack_count
from mordheim_combat.vectorized._attacks import _optional_phase_plan, _prepare_weapon_attack, _resolve_weapon, resolve_attacks
from mordheim_combat.vectorized._alchemy import alchemy_resources, resolve_alchemist
from mordheim_combat.vectorized._equipment import equipment_for_rows, phase_equipment, staff_power
from mordheim_combat.vectorized._leadership import leadership_resources, resolve_local_leadership
from mordheim_combat.vectorized._psychology import psychology_resources, resolve_fear, resolve_stupidity
from mordheim_combat.vectorized._recovery import revenant_recovery
from mordheim_combat.vectorized._state import charge_allowed, initialize_fighter, refresh_random_characteristics, require_characteristics, validate_duel_start
from mordheim_combat.phases import unarmed_attack_cap_applies


_WHIPCRACK_TAGS = (
    "weapon.steel-whip", "weapon.beastlash", "weapon.pirate-scourge",
    "weapon.serpent-whip",
)


def _whipcrack_weapon(fighter: CompiledFighter) -> EffectSet | None:
    for weapon in (fighter.main_weapon, fighter.off_hand):
        if weapon is not None and any(has(weapon, tag) for tag in _WHIPCRACK_TAGS):
            return weapon
    return None


def _choose(decisions, key: str, fighter: CompiledFighter) -> bool:
    """The scalar pipeline resolves every round with an accept-all default."""
    return True if decisions is None else decisions.choose(key, fighter)


def _select_attack_replacement(fighter: CompiledFighter, *, first_round: bool,
                               charging: np.ndarray, decisions, key: str
                               ) -> CompiledFighter:
    """Port of ``modular.rounds.select_attack_replacement`` for one pool.

    A whole-pool replacement is chosen once per fighter, as the scalar
    ``DecisionPolicy`` is asked once, and it owns every row of this batch.
    """
    if has(fighter.global_effects, "mechanic.wraith-touch") \
            and _choose(decisions, f"{key}.wraith-touch", fighter):
        return replace(fighter, main_weapon=EffectSet(
            tags=("weapon.fist", "effect.wraith-touch", "effect.no-critical"),
            strength_bonus=-1, target_armour_bonus=1),
            main_weapon_without_poison=None, off_hand=None,
            off_hand_without_poison=None, off_hand_attacks=False, extra_attacks=())
    if fighter.vomit_attack is not None \
            and _choose(decisions, f"{key}.vomit-attack", fighter):
        return replace(fighter, main_weapon=fighter.vomit_attack,
            main_weapon_without_poison=None, off_hand=None,
            off_hand_without_poison=None, off_hand_attacks=False, extra_attacks=())
    if has(fighter.main_weapon, "weapon.serpent-staff") \
            and _choose(decisions, f"{key}.serpent-staff", fighter):
        return replace(fighter, main_weapon=EffectSet(
            tags=("effect.serpent-staff-power",), fixed_strength=4, priority=1),
            off_hand=None, off_hand_attacks=False, extra_attacks=())
    removable = []
    if (has(fighter.global_effects, "mechanic.anvil-head") and first_round
            and bool(np.asarray(charging, dtype=bool).any())
            and not _choose(decisions, f"{key}.anvil-head", fighter)):
        removable.append("mechanic.anvil-head")
    if (has(fighter.global_effects, "mechanic.death-blow")
            and fighter.characteristics.attacks >= 2
            and not _choose(decisions, f"{key}.death-blow", fighter)):
        removable.append("mechanic.death-blow")
    if not removable:
        return fighter
    effects = replace(fighter.global_effects, tags=tuple(
        tag for tag in fighter.global_effects.tags if tag not in removable))
    return replace(fighter, global_effects=effects)


def _select_shifty_weapon(fighter: CompiledFighter, decisions, key: str
                          ) -> CompiledFighter:
    """Port of ``modular.rounds.select_shifty_weapon``: one nominated strike."""
    from mordheim_combat.modular.equipment import is_pistol

    weapon = fighter.main_weapon
    clean = fighter.main_weapon_without_poison
    slot = fighter.main_hand_slot
    off = fighter.off_hand if fighter.off_hand_attacks else None
    if off is not None and not is_pistol(off) and (
        is_pistol(weapon)
        or (off != weapon and not _choose(decisions, f"{key}.main-weapon", fighter))
    ):
        weapon, clean, slot = off, fighter.off_hand_without_poison, fighter.off_hand_slot
    elif is_pistol(weapon) and off is not None and off != weapon:
        if not _choose(decisions, f"{key}.main-weapon", fighter):
            weapon, clean, slot = off, fighter.off_hand_without_poison, fighter.off_hand_slot
    return replace(fighter, main_weapon=weapon, main_weapon_without_poison=clean,
        main_hand_slot=slot, off_hand=None, off_hand_without_poison=None,
        off_hand_attacks=False, extra_attacks=())


def _row_equipment(fighter, replacement, state: CombatState, count: int, *,
                   first_round: bool) -> dict[int, CompiledFighter]:
    """Project one fighter's equipment per simulation row.

    A whole-pool attack replacement (Wraith Touch, vomit, serpent staff) owns
    the weapon for every row, so its projection is reused instead of building
    a second, partially replaced one.
    """
    if replacement is not fighter:
        return {row: replacement for row in range(count)}
    return equipment_for_rows(
        fighter, state, np.arange(count), first_round=first_round,
    )


def _equipment_groups(rows: np.ndarray, attacker_equipment: dict[int, CompiledFighter],
                      defender_equipment: dict[int, CompiledFighter]):
    """Split rows by the equipment pair their simulation projects."""
    if rows.size == 0:
        return []
    grouped: dict[tuple[int, int], list[int]] = {}
    for value in rows:
        row = int(value)
        key = (id(attacker_equipment[row]), id(defender_equipment[row]))
        grouped.setdefault(key, []).append(row)
    return [
        (attacker_equipment[values[0]], defender_equipment[values[0]],
         np.asarray(values, dtype=np.int64))
        for values in grouped.values()
    ]


def _resolve_attacks_by_equipment(
    attacker_equipment, defender_equipment, rows, attacks, charging,
    attacker_state, defender_state, rng, first_round, decisions, prefix="",
    needs_sixes=None, forfeits=None, extra_forfeits=None,
) -> None:
    """Resolve one pool with each row's own effective equipment."""
    if needs_sixes is None:
        needs_sixes = getattr(attacker_state, "fear_hit_sixes", None)
    for attacker, defender, group in _equipment_groups(
            rows, attacker_equipment, defender_equipment):
        resolve_attacks(attacker, defender, group, attacks, charging,
                        attacker_state, defender_state, rng, first_round,
                        decisions, decision_prefix=prefix,
                        needs_sixes=needs_sixes, forfeits=forfeits,
                        extra_forfeits=extra_forfeits)


def _crude_belch_losses(owner: CompiledFighter, enemy: CompiledFighter,
                        owner_state: CombatState, enemy_state: CombatState,
                        rows: np.ndarray, rng: np.random.Generator,
                        leadership, decisions, context, *, first: bool,
                        round_index: int) -> np.ndarray:
    """The Halfling Elder's timed first-attack loss, per row."""
    lost = np.zeros(owner_state.wounds.size, dtype=bool)
    if not has(owner.global_effects, "skill.crude-belch-halfling"):
        return lost
    eligible = rows[(owner_state.condition[rows] == STANDING)
                    & (enemy_state.condition[rows] != OUT)]
    if context is not None and context.facts.contacts is not None:
        own_id = context.facts.first_id if first else context.facts.second_id
        enemy_id = context.facts.second_id if first else context.facts.first_id
        if not any({a, b} == {own_id, enemy_id} for a, b in context.facts.contacts):
            return lost
    if eligible.size == 0:
        return lost
    key = f"round.{round_index}.{'first' if first else 'second'}.crude-belch"
    if not _choose(decisions, key, owner):
        return lost
    passed = resolve_local_leadership(
        enemy, enemy_state, eligible, first=not first, key=f"{key}.leadership",
        rng=rng, context=context, decisions=decisions, resources=leadership,
        opponent=owner, close_combat=True)
    lost[eligible[~passed]] = True
    return lost


def _crude_belch_ogre(owner: CompiledFighter, target_state: CombatState,
                      owner_state: CombatState, rows: np.ndarray,
                      decisions, ledger: "_RoundLedger", side: int,
                      round_index: int) -> None:
    """The Ogre's once-per-battle belch: the enemy strikes at -1 this phase."""
    if not has(owner.global_effects, "mechanic.crude-belch-ogre"):
        return
    eligible = rows[(owner_state.condition[rows] == STANDING)
                    & ~ledger.crude_belch_ogre_used[rows]
                    & (target_state.condition[rows] != OUT)]
    if eligible.size == 0:
        return
    if not _choose(decisions, f"round.{round_index}.{'first' if side == 0 else 'second'}.crude-belch-ogre", owner):
        return
    ledger.crude_belch_ogre_used[eligible] = True
    ledger.hit_penalty[1 - side] += 1


def _charm_gates(owner_first: CompiledFighter, owner_second: CompiledFighter,
                 state_first: CombatState, state_second: CombatState,
                 rows: np.ndarray, rng: np.random.Generator, leadership,
                 decisions, context, ledger: "_RoundLedger", round_index: int,
                 first_player_turn: np.ndarray,
                 ) -> tuple[np.ndarray, np.ndarray]:
    """Leadership gates that bar a warrior's attacks for this phase."""
    blocked_first = np.zeros(state_first.wounds.size, dtype=bool)
    blocked_second = np.zeros(state_second.wounds.size, dtype=bool)
    for owner_is_first in (True, False):
        owner = owner_first if owner_is_first else owner_second
        target = owner_second if owner_is_first else owner_first
        owner_state = state_first if owner_is_first else state_second
        target_state = state_second if owner_is_first else state_first
        blocked = blocked_second if owner_is_first else blocked_first
        target_is_first = not owner_is_first
        label = "second" if owner_is_first else "first"
        eligible = rows[(owner_state.condition[rows] == STANDING)
                        & (target_state.condition[rows] == STANDING)]
        if eligible.size == 0:
            continue
        # The Eye Pendant's wearer turns an Undead attacker's blows aside: the
        # Undead warrior takes the Leadership test and, failing it, strikes no
        # one this phase.  This is an attack restriction, not Psychology.
        if (has(owner.global_effects, "defence.eye-pendant")
                and has(target.global_effects, "nature.undead")):
            passed = resolve_local_leadership(
                target, target_state, eligible, first=target_is_first,
                key=f"round.{round_index}.{label}.eye-pendant", rng=rng,
                context=context, decisions=decisions,
                resources=leadership[1 if owner_is_first else 0],
                opponent=owner, close_combat=True)
            blocked[eligible[~passed]] = True
        # Tranquil Fauna stops attacks, never the charge or established
        # contact.  A qualified animal may lift the bar with the handler's
        # supplied Leadership; an ordinary animal simply cannot strike.
        if (has(owner.global_effects, "mechanic.taal-tranquil-fauna")
                and has(target.global_effects, "species.animal")):
            conditional = any(has(target.global_effects, tag) for tag in
                              ("fauna-animal.handled", "fauna-animal.large-predator"))
            ordinary = (has(target.global_effects, "fauna-animal.ordinary")
                        or has(target.global_effects, "species.normal-animal"))
            if conditional:
                if target.animal_handler_leadership is None:
                    raise ValueError(
                        "Tranquil Fauna requires the qualified Animal Handler's Leadership")
                rolls = rng.integers(1, 7, eligible.size)
                passed = (rolls <= target.animal_handler_leadership) & (rolls != 6)
                blocked[eligible[~passed]] = True
            elif ordinary:
                blocked[eligible] = True
            else:
                raise ValueError(
                    "Tranquil Fauna requires the animal's explicit "
                    "ordinary/handled/large-predator qualification")
        # Hypnotist: an entranced enemy is released by its captor or newly
        # entranced by a successful stare; an entranced warrior strikes no one.
        if has(owner.global_effects, "mechanic.hypnotist"):
            release = eligible[ledger.entranced[eligible]]
            if release.size and _choose(
                    decisions, f"round.{round_index}.{label}.end-hypnosis", owner):
                ledger.entranced[release] = False
            exempt = any(has(target.global_effects, tag) for tag in
                          ("nature.undead", "nature.daemon",
                           "mechanic.psychology-immunity", "mechanic.charm-immunity"))
            targets = eligible[~ledger.entranced[eligible]
                               & ~target_state.frenzy[eligible]]
            if targets.size and not exempt and _choose(
                    decisions, f"round.{round_index}.{label}.hypnotist", target):
                passed = resolve_local_leadership(
                    target, target_state, targets, first=target_is_first,
                    key=f"round.{round_index}.{label}.hypnotist", rng=rng,
                    context=context, decisions=decisions,
                    resources=leadership[1 if owner_is_first else 0],
                    opponent=owner, close_combat=True)
                ledger.entranced[targets[~passed]] = True
        # The two Lahmia powers test the nominated enemy; a failure bars its
        # attacks for this phase (Deceive with its own Leadership only).
        for power, exclusions, name, own_only in (
            ("mechanic.lahmia-deceive",
             ("nature.undead", "nature.daemon", "mechanic.psychology-immunity"),
             "deceive", True),
            ("mechanic.lahmian-hypnotize", ("mechanic.psychology-immunity",),
             "hypnotize", False),
        ):
            if not has(owner.global_effects, power):
                continue
            if any(has(target.global_effects, tag) for tag in exclusions):
                continue
            if not _choose(decisions, f"round.{round_index}.{label}.{name}", target):
                continue
            passed = resolve_local_leadership(
                target, target_state, eligible, first=target_is_first,
                key=f"round.{round_index}.{label}.{name}", rng=rng,
                context=context, decisions=decisions,
                resources=leadership[1 if owner_is_first else 0],
                psychology=True, own_value_only=own_only, opponent=owner,
                close_combat=True)
            blocked[eligible[~passed]] = True
        # Seduction is a lasting control: the victim's own Recovery phase may
        # end it, and until then the victim strikes no one.
        seduction = next((tag for tag in ("mechanic.lahmia-seduction",
                                          "mechanic.lahmian-seduction")
                          if has(owner.global_effects, tag)), None)
        if seduction is not None and not any(
                has(target.global_effects, tag) for tag in
                ("mechanic.psychology-immunity", "nature.undead", "nature.daemon")):
            controlled = eligible[ledger.seduction_controlled[eligible]]
            own_turn = eligible[first_player_turn[eligible] == target_is_first]
            release_rows = np.intersect1d(controlled, own_turn, assume_unique=True)
            if release_rows.size and _choose(
                    decisions, f"round.{round_index}.{label}.seduction-release", target):
                passed = resolve_local_leadership(
                    target, target_state, release_rows, first=target_is_first,
                    key=f"round.{round_index}.{label}.seduction-release", rng=rng,
                    context=context, decisions=decisions,
                    resources=leadership[1 if owner_is_first else 0],
                    opponent=owner, close_combat=True)
                ledger.seduction_controlled[release_rows[passed]] = False
            free = eligible[~ledger.seduction_controlled[eligible]]
            if free.size and _choose(
                    decisions, f"round.{round_index}.{label}.{seduction}.establish", target):
                passed = resolve_local_leadership(
                    target, target_state, free, first=target_is_first,
                    key=f"round.{round_index}.{label}.{seduction}", rng=rng,
                    context=context, decisions=decisions,
                    resources=leadership[1 if owner_is_first else 0],
                    psychology=True, own_value_only=True, opponent=owner,
                    close_combat=True)
                ledger.seduction_controlled[free[~passed]] = True
            blocked[eligible[ledger.seduction_controlled[eligible]]] = True
    return blocked_first, blocked_second


GRAPPLER_TAGS = ("mechanic.gaoler-grapple",)
GRAPPLE_IMMUNITY = ("nature.undead", "nature.daemon", "nature.dead",
                    "mechanic.pain-immunity", "size.large")


def _grapple_declaration(owner: CompiledFighter, target: CompiledFighter,
                         owner_state: CombatState, target_state: CombatState,
                         rows: np.ndarray, decisions, ledger: "_RoundLedger",
                         blocked: np.ndarray, key: str) -> np.ndarray:
    """Port of the Torturer's hold declaration for one side."""
    declared = np.zeros(owner_state.wounds.size, dtype=bool)
    if not any(has(owner.global_effects, tag) for tag in GRAPPLER_TAGS):
        return declared
    if has(owner.global_effects, "condition.mim-no-hand-attacks"):
        return declared
    if any(has(target.global_effects, tag) for tag in GRAPPLE_IMMUNITY):
        return declared
    eligible = rows[
        (owner_state.condition[rows] == STANDING)
        & (target_state.condition[rows] != OUT)
        & ~blocked[rows]
        & ~owner_state.on_fire[rows]
        & ~ledger.animosity_failed[rows]
        & ~owner_state.stupidity_failed[rows]
        & ~owner_state.grappled[rows]
        & ~owner_state.grappling[rows]
    ]
    if eligible.size == 0:
        return declared
    if not _choose(decisions, f"{key}.torturer-grapple", owner):
        return declared
    declared[eligible] = True
    return declared


def _grapple_fighter(owner: CompiledFighter) -> CompiledFighter:
    """The natural-attack projection a declared hold fights with."""
    return replace(owner, main_weapon=EffectSet(tags=("weapon.natural-attacks",)),
        main_weapon_without_poison=None, off_hand=None,
        off_hand_without_poison=None, off_hand_attacks=False,
        extra_attacks=(), main_hand_slot="natural")


def _resolve_grapple(attacker: CompiledFighter, defender: CompiledFighter,
                     rows: np.ndarray, attacker_state: CombatState,
                     defender_state: CombatState, rng: np.random.Generator,
                     first_round: bool, decisions, key: str) -> None:
    """Resolve a declared hold: hit, parries, then the victim's Strength test."""
    from mordheim_combat.vectorized._attacks import _parry_hits

    charging = np.zeros(attacker_state.wounds.size, dtype=bool)
    prepared = _prepare_weapon_attack(
        attacker, defender, EffectSet(tags=("weapon.natural-attacks",)),
        rows, charging, attacker_state, defender_state, rng, first_round,
        needs_sixes=attacker_state.fear_hit_sixes,
    )
    if prepared is None or prepared.hit_rows.size == 0:
        return
    positions = np.searchsorted(prepared.active, prepared.hit_rows)
    values = prepared.rolls[positions]
    natural = prepared.natural[positions] if prepared.natural is not None else values
    hit_rows, _, _ = _parry_hits(
        defender, prepared.effect, prepared.hit_rows, values,
        prepared.strength[positions], defender_state, rng,
        attacker=attacker, attacker_state=attacker_state,
        weapon=prepared.weapon, natural_values=natural,
    )
    if hit_rows.size == 0:
        return
    require_characteristics(defender, defender_state, hit_rows, rng, ("S",))
    escaped = _characteristic_test(
        defender, defender_state.strength[hit_rows] - 2, rng,
        six_always_fails=False,
    )
    held = hit_rows[~escaped]
    defender_state.grappled[held] = True
    attacker_state.grappling[held] = True


def _pool_extra_weapons(attacker: CompiledFighter, charging: np.ndarray,
                        rows: np.ndarray) -> tuple[tuple[int, EffectSet], ...]:
    """The independent contributions ``resolve_attacks`` resolves, with index.

    ``pool_attack_weapons`` leaves the last bite and the eagles to their own
    events, drops every extra behind a whole-pool vomit/wraith replacement and
    only strikes a Horned One when the pool charged.
    """
    if any(has(attacker.main_weapon, tag) for tag in
           ("weapon.vomit-attack", "effect.wraith-touch")):
        return ()
    charging_any = bool(np.asarray(charging, dtype=bool)[rows].any())
    return tuple(
        (index, weapon) for index, weapon in enumerate(attacker.extra_attacks)
        if not any(has(weapon, tag) for tag in
                   ("rule.strikes-last-bite", "rule.eagle-friend"))
        and (charging_any or not has(weapon, "rule.horned-one"))
    )


def _tentacle_forfeit(attacker: CompiledFighter, defended: EffectSet,
                      rows: np.ndarray, attacks: np.ndarray, decisions,
                      ledger: "_RoundLedger", defender_index: int,
                      key: str, *, charging: np.ndarray,
                      whip_rows: np.ndarray) -> tuple[np.ndarray, np.ndarray,
                                                      np.ndarray]:
    """Port of ``_grapple_lost_attacks`` over the complete allocation.

    The modular pool is the hand allocation plus the Whipcrack bonus and the
    bearer's independent extra attacks, in that order.  The nominated position
    is removed from that own order; a row that does not own the position keeps
    its pool, and no row ever falls below one attack (``minimum_attacks=1``).
    Mim without hands arrives with ``attacks == 0`` and no Whipcrack bonus, so
    its pool is exactly the remaining extras.

    Returns the per-row hand position, the rows that lose the Whipcrack attack
    and the index (into ``attacker.extra_attacks``) of the extra that is lost.
    """
    hand_forfeits = np.full(attacks.size, -1, dtype=np.int16)
    whip_forfeits = np.zeros(attacks.size, dtype=bool)
    extra_forfeits = np.full(attacks.size, -1, dtype=np.int16)
    if rows.size == 0:
        return hand_forfeits, whip_forfeits, extra_forfeits
    extras = _pool_extra_weapons(attacker, charging, rows)
    whip = np.asarray(whip_rows, dtype=bool)
    lengths = attacks[rows].astype(np.int16) + whip[rows].astype(np.int16) + len(extras)
    eligible = rows[(lengths > 1)
                    & ~ledger.tentacle_used[defender_index][rows]
                    & has(defended, "rule.tentacle-grapple")
                    & (defended.incoming_attacks_modifier < 0)]
    if eligible.size == 0:
        return hand_forfeits, whip_forfeits, extra_forfeits
    widths = (attacks[eligible].astype(np.int16)
              + whip[eligible].astype(np.int16) + len(extras))
    position = next((index for index in range(int(np.max(widths)))
                     if _choose(decisions, f"{key}.grapple-lost-attack.{index}",
                                attacker)), None)
    if position is None:
        return hand_forfeits, whip_forfeits, extra_forfeits
    applied = np.zeros(attacks.size, dtype=bool)
    for row in eligible:
        hands = int(attacks[row])
        has_whip = bool(whip[row])
        if position < hands:
            hand_forfeits[row] = position
        elif has_whip and position == hands:
            whip_forfeits[row] = True
        else:
            offset = position - hands - int(has_whip)
            if offset < 0 or offset >= len(extras):
                continue
            extra_forfeits[row] = extras[offset][0]
        applied[row] = True
    ledger.tentacle_used[defender_index][applied] = True
    return hand_forfeits, whip_forfeits, extra_forfeits


def _great_thirster_frenzy(attacker: CompiledFighter, attacker_state: CombatState,
                           defender_state: CombatState, rows: np.ndarray) -> None:
    """A Great Thirster that takes a model out of action becomes Frenzied."""
    if rows.size == 0 or not has(attacker.global_effects, "mechanic.great-thirster"):
        return
    killed = rows[(defender_state.condition[rows] == OUT)
                  & (attacker_state.condition[rows] == STANDING)]
    if killed.size:
        attacker_state.frenzy[killed] = True


def _strike_first_fighter(fighter: CompiledFighter, weapon: EffectSet
                          ) -> CompiledFighter:
    """Project one nominated allocated attack, preserving its own hand slot."""
    if weapon == fighter.main_weapon:
        slot, clean = fighter.main_hand_slot, fighter.main_weapon_without_poison
    elif fighter.off_hand is not None and weapon == fighter.off_hand:
        slot, clean = fighter.off_hand_slot, fighter.off_hand_without_poison
    else:
        slot, clean = "natural", None
    return replace(fighter, main_weapon=weapon, main_hand_slot=slot,
        main_weapon_without_poison=clean, off_hand=None,
        off_hand_without_poison=None, off_hand_attacks=False,
        extra_attacks=())


def _nominated_strike(attacker: CompiledFighter, decisions, key: str,
                      rows: np.ndarray, attacks: np.ndarray, *,
                      first_round: bool,
                      ) -> tuple[np.ndarray, CompiledFighter] | None:
    """Port of Instinctual Violence: one allocated attack Strikes First.

    The offers follow the pool's own allocation, so the nominated strike is a
    legal attack of a real weapon and keeps that weapon's profile and slot.
    Declining every offer leaves the ordinary pool untouched.
    """
    if rows.size == 0 or not has(attacker.global_effects,
                                 "mechanic.nominated-strike-first"):
        return None
    widest = int(np.max(attacks[rows]))
    if widest <= 0:
        return None
    allocated = allocate_attack_weapons(attacker, widest, first_round=first_round)
    position = next((index for index in range(len(allocated))
                     if _choose(decisions,
                                f"{key}.strike-first.attack.{index}", attacker)), None)
    if position is None:
        return None
    eligible = rows[attacks[rows] > position]
    if eligible.size == 0:
        return None
    return eligible, _strike_first_fighter(attacker, allocated[position])


SHADOW_DANCES = ("whirling-death", "storm-of-blades", "the-shadows-coil", "woven-mist")
ANIMOSITY_SOURCES = ("mechanic.goblin-squabble", "mechanic.fungus-rowdy")


@dataclass(slots=True)
class _RoundLedger:
    """Per-row round facts ``CombatState`` does not own.

    G02 froze the state schema, so the round-only results live beside it, one
    array per simulation, exactly like G05's LeadershipResources.
    """

    drunken_result: np.ndarray
    animosity_failed: np.ndarray
    crude_belch_ogre_used: np.ndarray
    entranced: np.ndarray
    charm_blocked: np.ndarray
    charm_auto_hit: np.ndarray
    seduction_controlled: np.ndarray
    deathblow_used: np.ndarray
    bitten_result: np.ndarray
    hit_penalty: list[int]
    last_dance: dict[str, str | None]
    #: One per defender: the printed tentacle loss is spent once per battle.
    tentacle_used: list[np.ndarray]


def _round_ledger(count: int) -> _RoundLedger:
    return _RoundLedger(
        drunken_result=np.zeros(count, dtype=np.int8),
        animosity_failed=np.zeros(count, dtype=bool),
        crude_belch_ogre_used=np.zeros(count, dtype=bool),
        entranced=np.zeros(count, dtype=bool),
        charm_blocked=np.zeros(count, dtype=bool),
        charm_auto_hit=np.zeros(count, dtype=bool),
        seduction_controlled=np.zeros(count, dtype=bool),
        deathblow_used=np.zeros(count, dtype=bool),
        bitten_result=np.zeros(count, dtype=np.int8),
        hit_penalty=[0, 0],
        last_dance={"first": None, "second": None},
        tentacle_used=[np.zeros(count, dtype=bool), np.zeros(count, dtype=bool)],
    )


def _apply_opponent_leadership(fighter: CompiledFighter,
                               opponent: CompiledFighter) -> CompiledFighter:
    """Port of ``modular.rounds.apply_opponent_leadership``."""
    from mordheim_combat.vectorized._psychology import causes_fear

    effect = fighter.global_effects
    if (has(opponent.global_effects, "mechanic.enchanting-beauty")
            and not any(has(effect, tag) for tag in ("nature.undead", "nature.daemon"))):
        effect = replace(effect, tags=(*effect.tags, "condition.enchanting-beauty"))
    if has(effect, "mechanic.questing-vow") and causes_fear(opponent, fighter):
        effect = replace(effect, tags=(*effect.tags, "mechanic.leadership-reroll"))
    if effect is fighter.global_effects:
        return fighter
    return replace(fighter, global_effects=effect)


def _select_shadow_dance(fighter: CompiledFighter, ledger: _RoundLedger, side: str,
                         decisions, key: str) -> CompiledFighter:
    """Port of ``modular.rounds.select_shadow_dance`` for one combat phase."""
    available = [dance for dance in SHADOW_DANCES
                 if has(fighter.global_effects, f"dance.{dance}")
                 and dance != ledger.last_dance[side]]
    if not available:
        return fighter
    selected = None
    if decisions is None:
        selected = available[0]
    else:
        for dance in available:
            if decisions.choose(f"{key}.dance.{dance}", tuple(available)):
                selected = dance
                break
    if selected is None:
        raise ValueError("a Wardancer must choose an available learned Shadow Dance")
    ledger.last_dance[side] = selected
    effect = fighter.global_effects
    if selected == "whirling-death":
        effect = replace(effect, injury_modifier=effect.injury_modifier + 1)
    elif selected == "storm-of-blades":
        effect = replace(effect, attacks_bonus=effect.attacks_bonus + 1)
    elif selected == "the-shadows-coil":
        effect = replace(effect, tags=(*effect.tags, "dance.shadows-coil-active"))
    else:
        effect = replace(effect, tags=(*effect.tags, "dance.woven-mist-active"))
    return replace(fighter, global_effects=effect)


def _tagged_rows(fighter: CompiledFighter, mask: np.ndarray,
                 tags: tuple[str, ...]) -> CompiledFighter:
    """A copy carrying ``tags``; callers use it only for the masked rows."""
    if not mask.any():
        return fighter
    return replace(fighter, global_effects=replace(
        fighter.global_effects, tags=(*fighter.global_effects.tags, *tags)))


def _new_state(fighter: CompiledFighter, count: int, rng: np.random.Generator) -> CombatState:
    """Historical entry point; the port lives in ``vectorized._state``."""
    from mordheim_combat.vectorized._state import initialize_fighter
    return initialize_fighter(fighter, count, rng)


def _refresh_random_characteristics(
    fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
    rng: np.random.Generator,
) -> None:
    """Historical entry point; the port lives in ``vectorized._state``."""
    from mordheim_combat.vectorized._state import refresh_random_characteristics
    refresh_random_characteristics(fighter, state, rows, rng)


def _resolve_spines(first: CompiledFighter, second: CompiledFighter,
                    rows: np.ndarray, charge1: np.ndarray, charge2: np.ndarray,
                    state1: CombatState, state2: CombatState,
                    rng: np.random.Generator) -> None:
    """Resolve simultaneous, non-critical Spines hits at phase start."""
    spines=EffectSet(
        tags=("rule.spines", "effect.no-critical"), fixed_strength=1,
        automatic_hit=True, cannot_be_parried=True)
    prepared1=(
        _prepare_weapon_attack(first,second,spines,rows,charge1,state1,state2,rng,False,melee_attack=False)
        if has(first.global_effects,"spines") else None)
    prepared2=(
        _prepare_weapon_attack(second,first,spines,rows,charge2,state2,state1,rng,False,melee_attack=False)
        if has(second.global_effects,"spines") else None)
    if prepared1 is not None:
        _resolve_weapon(first,second,spines,rows,charge1,state1,state2,rng,False,prepared=prepared1,melee_attack=False)
    if prepared2 is not None:
        _resolve_weapon(second,first,spines,rows,charge2,state2,state1,rng,False,prepared=prepared2,melee_attack=False)

def _rescue_force_of_will(fighter: CompiledFighter, state: CombatState,
                          rows: np.ndarray, rng: np.random.Generator) -> None:
    if not has(fighter.global_effects,"mechanic.force-of-will") or rows.size==0:return
    eligible=rows[(state.condition[rows]==OUT)&~state.force_of_will_used[rows]]
    if eligible.size==0:return
    state.force_of_will_used[eligible]=True
    success=_characteristic_test(fighter,state.toughness[eligible],rng)
    rescued=eligible[success]
    state.condition[rescued]=STANDING
    state.wounds[rescued]=1
    state.force_of_will_active[rescued]=True

def _sustain_force_of_will(fighter: CompiledFighter, state: CombatState,
                           rng: np.random.Generator,
                           rows: np.ndarray | None = None) -> None:
    if not has(fighter.global_effects,"mechanic.force-of-will"):return
    eligible = state.force_of_will_active & (state.condition != OUT)
    if rows is not None:
        selected = np.zeros(state.wounds.size, dtype=bool)
        selected[rows] = True
        eligible &= selected
    active=np.flatnonzero(eligible)
    if active.size==0:return
    state.force_of_will_penalty[active]+=1
    target=np.maximum(0,state.toughness[active]-state.force_of_will_penalty[active])
    failed=~_characteristic_test(fighter,target,rng)
    removed=active[failed]
    state.condition[removed]=OUT
    state.force_of_will_active[removed]=False

def _black_hunger_backlash(fighter: CompiledFighter, state: CombatState,
                           rows: np.ndarray, rng: np.random.Generator) -> None:
    if not has(fighter.global_effects,"mechanic.black-hunger") or rows.size==0:return
    active=rows[state.condition[rows]!=OUT]
    if active.size==0:return
    hits=rng.integers(1,4,active.size)
    backlash=EffectSet(tags=("mechanic.black-hunger-backlash","effect.no-critical"),fixed_strength=3,
                       automatic_hit=True,cannot_be_parried=True,ignore_armour=True)
    for index in range(3):
        hit_rows=active[hits>index]
        _resolve_weapon(fighter,fighter,backlash,hit_rows,np.zeros(state.wounds.size,dtype=bool),state,state,rng,False,
            melee_attack=False)
        _rescue_force_of_will(fighter,state,hit_rows,rng)

def _resolve_fire(victim: CompiledFighter, opponent: CompiledFighter,
                   victim_state: CombatState, opponent_state: CombatState,
                   rng: np.random.Generator,
                   rows: np.ndarray | None = None) -> None:
    """Resolve the Recovery-phase test and S4 hit for warriors on fire."""
    burning=np.flatnonzero(victim_state.on_fire&(victim_state.condition!=OUT))
    if rows is not None:
        burning = np.intersect1d(burning, rows, assume_unique=True)
    if burning.size==0:return
    extinguished=rng.integers(1,7,burning.size)>=4
    victim_state.on_fire[burning[extinguished]]=False
    still_burning=burning[~extinguished]
    if still_burning.size==0:return
    fire=EffectSet(tags=("attack.fire","effect.no-critical"),fixed_strength=4,
                   automatic_hit=True,cannot_be_parried=True)
    source=replace(opponent,main_weapon=fire,off_hand=None,global_effects=EffectSet(),extra_attacks=())
    _resolve_weapon(source,victim,fire,still_burning,np.zeros(victim_state.wounds.size,dtype=bool),
                    opponent_state,victim_state,rng,False,melee_attack=False)

def _resolve_netter_charge(netter: CompiledFighter, target: CompiledFighter,
                           rows: np.ndarray, netter_state: CombatState,
                           target_state: CombatState,
                           rng: np.random.Generator) -> np.ndarray:
    """Resolve Netter's first-round charge reaction and return caught rows."""
    if rows.size == 0 or not has(netter.global_effects,"mechanic.netter"):
        return np.empty(0,dtype=np.int64)
    hits=rng.integers(1,7,rows.size)>=max(2,7-netter.ballistic_skill)
    escape=_characteristic_test(target,target_state.strength[rows],rng)
    caught=rows[hits&~escape]
    target_state.condition[caught]=KNOCKED_DOWN
    return caught

def _resource_observation(state: CombatState) -> tuple[tuple[str, np.ndarray], ...]:
    return (
        ("lucky-charm", ~state.lucky_charm.copy()),
        ("force-of-will", state.force_of_will_used.copy()),
        ("mark-of-the-old-ones", state.mark_of_old_ones_used.copy()),
        ("luck", state.luck_used.copy()),
    )

def _simulate_batch_core(first: CompiledFighter, second: CompiledFighter, count: int,
                         rng: np.random.Generator, maximum_rounds: int,
                         decisions: DecisionPolicy | None = None,
                         *, observe: bool = False, context: DuelContext | None = None
                         ) -> tuple[int, int, int] | VectorBatchObservation:
    from mordheim_combat.kernel import require_optimized_support
    require_optimized_support(first, second, backend="numpy")
    prepared = prepare_duel_context(first, second, context)
    # The supplied snapshot is validated before any row initialises, exactly as
    # ``initialize_duel`` does; the returned flags are the declared charges.
    declared = validate_duel_start(first, second, context)
    # G02's lazy cadence: an Inconsistency value is drawn by the operation that
    # first reads it, not eagerly when the batch initialises.
    state1 = initialize_fighter(first, count, rng, lazy_inconsistency=True)
    state2 = initialize_fighter(second, count, rng, lazy_inconsistency=True)
    original_first, original_second = first, second
    allowed = (charge_allowed(first, second), charge_allowed(second, first))
    if declared is not None:
        first_charges = np.full(count, declared[0], dtype=bool)
        second_charges = np.full(count, declared[1], dtype=bool)
        charge_roll = np.zeros(count, dtype=bool)
    else:
        # Only legal initial chargers are sampled; a fighter that cannot charge
        # never receives the flag, and the other one takes the attempt.  A
        # declared snapshot keeps the historical draw count (none).
        charge_roll = rng.random(count) < .5
        first_charges = charge_roll & allowed[0]
        second_charges = ~charge_roll & allowed[1]
    base_contact = (
        prepared is not None and prepared.facts.contacts is not None
        and any({a, b} == {prepared.facts.first_id, prepared.facts.second_id}
                for a, b in prepared.facts.contacts)
    )
    if base_contact:
        # Established contact is not an in-range attempt: neither duelist owns
        # a charge, while the sampled roll still owns the player turn.
        first_charges[:] = False
        second_charges[:] = False
    sampled_contact = (
        prepared is None or prepared.facts.contacts is None or base_contact
    )
    engaged = (np.ones(count, dtype=bool) if sampled_contact
               else (first_charges | second_charges))
    initial_first_turn = (charge_roll & allowed[0]) if base_contact else first_charges.copy()
    if prepared is not None and prepared.facts.active_participant is not None:
        initial_first_turn = np.full(count, prepared.first_player_turn(True), dtype=bool)        # G05's two ledgers stay separate: Psychology owns the Fear result, while the
    # Leadership helpers spend the per-battle rerolls and relics.  G06's alchemy
    # ledger owns the two facts ``CombatState`` does not carry.
    leadership = (leadership_resources(count), leadership_resources(count))
    psychology = (psychology_resources(count), psychology_resources(count))
    alchemy = (alchemy_resources(count), alchemy_resources(count))
    ledger = _round_ledger(count)
    rounds = np.zeros(count, dtype=np.int64) if observe else None
    optional = _optional_phase_plan(first, second)
    entangle_effect = (
        EffectSet(tags=("effect.chained-squig-entangle",),fixed_strength=3,automatic_hit=True)
        if optional.first_entangle or optional.second_entangle else None
    )
    for round_index in range(maximum_rounds):
        unresolved = (state1.condition != OUT) & (state2.condition != OUT) & engaged
        if not unresolved.any():
            break
        if round_index:
            active_rows = np.flatnonzero(unresolved)
            refresh_random_characteristics(
                original_first, state1, active_rows, rng, lazy_inconsistency=True)
            refresh_random_characteristics(
                original_second, state2, active_rows, rng, lazy_inconsistency=True)
        first = phase_equipment(original_first, first_round=round_index == 0)
        second = phase_equipment(original_second, first_round=round_index == 0)
        first_player_turn = initial_first_turn if round_index % 2 == 0 else ~initial_first_turn
        if round_index:
            if optional.first_force_of_will:
                _sustain_force_of_will(first,state1,rng,active_rows)
            if optional.second_force_of_will:
                _sustain_force_of_will(second,state2,rng,active_rows)
            if optional.first_can_burn:
                _resolve_fire(first,second,state1,state2,rng,np.flatnonzero(unresolved & first_player_turn))
            if optional.second_can_burn:
                _resolve_fire(second,first,state2,state1,rng,np.flatnonzero(unresolved & ~first_player_turn))
            if optional.first_force_of_will:
                _rescue_force_of_will(first, state1, active_rows, rng)
            if optional.second_force_of_will:
                _rescue_force_of_will(second, state2, active_rows, rng)
        unresolved = (state1.condition != OUT) & (state2.condition != OUT) & engaged
        if not unresolved.any():
            break
        active_rows = np.flatnonzero(unresolved)
        if rounds is not None:
            rounds[unresolved] += 1
        state1.parry_used[:] = False; state2.parry_used[:] = False
        state1.seaguard_used[:] = False; state2.seaguard_used[:] = False
        state1.corruption_used[:] = False; state2.corruption_used[:] = False
        state1.parry_remaining[:] = _parry_capacity(first)
        state2.parry_remaining[:] = _parry_capacity(second)
        state1.critical_used[:] = False; state2.critical_used[:] = False
        state1.attack_penalty[:] = 0; state2.attack_penalty[:] = 0
        state1.hampered_main[:] = 0; state2.hampered_main[:] = 0
        state1.hampered_off[:] = 0; state2.hampered_off[:] = 0
        # ``mechanic.spawn-special-attacks`` replaces the built pool after the
        # attack count (resolve_spawn_attack_count): one die per warrior and
        # round, never behind a whole-pool vomit/wraith replacement.
        # A netted fighter spends its own turn cutting free: it drops to Knocked
        # Down and does not stand in that same turn (modular freed_from_net).
        netted1 = (state1.netted & first_player_turn
                   & np.isin(state1.condition, (STANDING, KNOCKED_DOWN)))
        netted2 = (state2.netted & ~first_player_turn
                   & np.isin(state2.condition, (STANDING, KNOCKED_DOWN)))
        state1.netted[netted1] = False
        state2.netted[netted2] = False
        state1.condition[netted1] = KNOCKED_DOWN
        state2.condition[netted2] = KNOCKED_DOWN
        stunned1 = (state1.condition == STUNNED) & first_player_turn
        stunned2 = (state2.condition == STUNNED) & ~first_player_turn
        stood1 = (state1.condition == KNOCKED_DOWN) & first_player_turn & ~netted1
        stood2 = (state2.condition == KNOCKED_DOWN) & ~first_player_turn & ~netted2
        state1.condition[stunned1] = KNOCKED_DOWN; state2.condition[stunned2] = KNOCKED_DOWN
        state1.condition[stood1 & ~stunned1] = STANDING; state2.condition[stood2 & ~stunned2] = STANDING
        paralyzed1 = (state1.condition == PARALYZED) & first_player_turn
        paralyzed2 = (state2.condition == PARALYZED) & ~first_player_turn
        paralyzed_rows1=np.flatnonzero(paralyzed1)
        paralyzed_rows2=np.flatnonzero(paralyzed2)
        if paralyzed_rows1.size:
            recover1=_characteristic_test(first,state1.toughness[paralyzed_rows1],rng)
            state1.condition[paralyzed_rows1[recover1]] = STANDING
        if paralyzed_rows2.size:
            recover2=_characteristic_test(second,state2.toughness[paralyzed_rows2],rng)
            state2.condition[paralyzed_rows2[recover2]] = STANDING
        # Grapple: the victim tests Strength-2 on its own turn (a natural six
        # always fails, Blessed Sight rerolls); the hold also ends when the
        # holder is no longer Standing or the victim is out of action.
        for holder_state, victim_state, holder, victim in (
                (state1, state2, first, second),
                (state2, state1, second, first)):
            # The printed escape test repeats at the start of every close-combat
            # phase, not only on one player's turn.
            held = engaged & holder_state.grappling & victim_state.grappled
            if not held.any():
                continue
            held_rows = np.flatnonzero(held)
            released = holder_state.condition[held_rows] != STANDING
            released |= victim_state.condition[held_rows] == OUT
            test_rows = held_rows[~released]
            if test_rows.size:
                require_characteristics(victim, victim_state, test_rows, rng, ("S",))
                escaped = _characteristic_test(
                    victim, victim_state.strength[test_rows] - 2, rng,
                    six_always_fails=False)
                released[np.flatnonzero(~released)[escaped]] = True
            holder_state.grappling[held_rows[released]] = False
            victim_state.grappled[held_rows[released]] = False
        first_round = round_index == 0
        # Own-turn recovery runs before the Psychology gates, as in
        # ``resolve_round``: Revenant, then the Alchemist's brew, then
        # Stupidity and (round zero only) Fear.
        # Fear's ``hit_sixes`` is a per-round fact: the modular clears it at the
        # start of every round, before the Psychology gates run again.
        psychology[0].fear_hit_sixes[:] = False
        psychology[1].fear_hit_sixes[:] = False
        own_first = np.flatnonzero(unresolved & first_player_turn)
        own_second = np.flatnonzero(unresolved & ~first_player_turn)
        revenant_recovery(first, state1, own_first, rng)
        revenant_recovery(second, state2, own_second, rng)
        resolve_alchemist(first, state1, own_first, rng, alchemy[0], decisions)
        resolve_alchemist(second, state2, own_second, rng, alchemy[1], decisions)
        # Bitten transform: rolled on the bearer's own turn; 6 enters the form
        # and casts the equipment off, 1 reverts.  The form survives the turn
        # that rolled it and the equipment stays lost.
        for fighter, state, own_rows in ((first, state1, own_first),
                                         (second, state2, own_second)):
            if not has(fighter.global_effects, "mechanic.bitten-transform"):
                continue
            rows = own_rows[~(state.transformed[own_rows] & engaged[own_rows])]
            if rows.size == 0:
                continue
            rolls = rng.integers(1, 7, rows.size)
            ledger.bitten_result[rows] = rolls
            enter = rows[rolls == 6]
            leave = rows[rolls == 1]
            state.transformed[enter] = True
            state.equipment_cast_off[enter] = True
            state.transformed[leave] = False
            state.frenzy[rows] = state.transformed[rows] | has(fighter.global_effects, "frenzy")
        # Centigor Drunk: a fresh result each own turn, lapsing when the turn
        # passes.  A 6 grants Frenzy; a 1 prints Stupidity for that turn only.
        drunk1 = own_first[has(first.global_effects, "mechanic.centigor-drunken")]
        if drunk1.size:
            rolls = rng.integers(1, 7, drunk1.size)
            ledger.drunken_result[drunk1] = rolls
            state1.frenzy[drunk1] = rolls == 6
            state1.stupidity_failed[drunk1] = False
        drunk2 = own_second[has(second.global_effects, "mechanic.centigor-drunken")]
        if drunk2.size:
            rolls = rng.integers(1, 7, drunk2.size)
            ledger.drunken_result[drunk2] = rolls
            state2.frenzy[drunk2] = rolls == 6
            state2.stupidity_failed[drunk2] = False
        expired1 = ~first_player_turn & (ledger.drunken_result != 0)
        if expired1.any():
            ledger.drunken_result[expired1] = 0
            state1.stupidity_failed[expired1] = False
            state1.frenzy[expired1] = has(first.global_effects, "frenzy")
        expired2 = first_player_turn & (ledger.drunken_result != 0)
        if expired2.any():
            ledger.drunken_result[expired2] = 0
            state2.stupidity_failed[expired2] = False
            state2.frenzy[expired2] = has(second.global_effects, "frenzy")
        # Animosity is tested only in the warrior's own turn: a 1 fails, and the
        # Fungus Brew's Rowdy result widens the band to 1-2.
        ledger.animosity_failed[:] = False
        if any(has(first.global_effects, tag) for tag in ANIMOSITY_SOURCES):
            rows = own_first[state1.condition[own_first] == STANDING]
            if rows.size:
                threshold = 2 if has(first.global_effects, "mechanic.fungus-rowdy") else 1
                ledger.animosity_failed[rows] = rng.integers(1, 7, rows.size) <= threshold
        if any(has(second.global_effects, tag) for tag in ANIMOSITY_SOURCES):
            rows = own_second[state2.condition[own_second] == STANDING]
            if rows.size:
                threshold = 2 if has(second.global_effects, "mechanic.fungus-rowdy") else 1
                ledger.animosity_failed[rows] = rng.integers(1, 7, rows.size) <= threshold
        # The player turn is per row, so each side's Stupidity gate is resolved
        # over its own active rows instead of assuming one scalar turn.  Rows
        # whose Drunk result is 1 carry the this-turn Stupidity the result
        # prints, so they are tested with a tagged copy of their fighter.
        sober_first = own_first[ledger.drunken_result[own_first] != 1]
        stupidity_first = resolve_stupidity(
            first, second, state1, state2, sober_first,
            first_player_turn=True, round_index=round_index,
            charges=first_charges, rng=rng, leadership=leadership[0],
            decisions=decisions, context=prepared,
            key_prefix=f"round.{round_index}",
        )
        first_charges = stupidity_first.charges
        drunk_rows1 = own_first[ledger.drunken_result[own_first] == 1]
        if drunk_rows1.size:
            drunk_first = resolve_stupidity(
                _tagged_rows(first, drunk_rows1,
                             ("mechanic.stupidity", "mechanic.psychology-immunity")),
                second, state1, state2, drunk_rows1,
                first_player_turn=True, round_index=round_index,
                charges=first_charges, rng=rng, leadership=leadership[0],
                decisions=decisions, context=prepared,
                key_prefix=f"round.{round_index}.drunk",
            )
            first_charges = drunk_first.charges
        sober_second = own_second[ledger.drunken_result[own_second] != 1]
        stupidity_second = resolve_stupidity(
            first, second, state1, state2, sober_second,
            first_player_turn=False, round_index=round_index,
            charges=second_charges, rng=rng, leadership=leadership[1],
            decisions=decisions, context=prepared,
            key_prefix=f"round.{round_index}",
        )
        second_charges = stupidity_second.charges
        drunk_rows2 = own_second[ledger.drunken_result[own_second] == 1]
        if drunk_rows2.size:
            drunk_second = resolve_stupidity(
                first, _tagged_rows(second, drunk_rows2,
                                    ("mechanic.stupidity", "mechanic.psychology-immunity")),
                state1, state2, drunk_rows2,
                first_player_turn=False, round_index=round_index,
                charges=second_charges, rng=rng, leadership=leadership[1],
                decisions=decisions, context=prepared,
                key_prefix=f"round.{round_index}.drunk",
            )
            second_charges = drunk_second.charges
        if first_round:
            fear = resolve_fear(
                first, second, state1, state2, np.flatnonzero(unresolved),
                round_index=0, engaged=engaged, first_charges=first_charges,
                second_charges=second_charges, rng=rng, resources=psychology,
                leadership=leadership, decisions=decisions, context=prepared,
                key_prefix=f"round.{round_index}",
            )
            first_charges, second_charges = fear.first_charges, fear.second_charges
            # Fear's mask belongs to the resolution, not only to Psychology:
            # every attack path reads the same per-row fact.
            state1.fear_hit_sixes[:] = psychology[0].fear_hit_sixes
            state2.fear_hit_sixes[:] = psychology[1].fear_hit_sixes
            engaged = fear.engaged
            unresolved = unresolved & engaged
            if not unresolved.any():
                break
            active_rows = np.flatnonzero(unresolved)
        charge1 = first_charges if first_round else np.zeros(count,dtype=bool)
        charge2 = second_charges if first_round else np.zeros(count,dtype=bool)
        if first_round:
            if optional.first_netter:
                rows=np.flatnonzero(unresolved&charge1)
                _resolve_netter_charge(first,second,rows,state1,state2,rng)
            if optional.second_netter:
                rows=np.flatnonzero(unresolved&charge2)
                _resolve_netter_charge(second,first,rows,state2,state1,rng)
        if optional.first_spines or optional.second_spines:
            _resolve_spines(first,second,active_rows,charge1,charge2,state1,state2,rng)
        if optional.first_force_of_will:
            _rescue_force_of_will(first,state1,active_rows,rng)
        if optional.second_force_of_will:
            _rescue_force_of_will(second,state2,active_rows,rng)
        if optional.second_entangle:
            entangled1=np.flatnonzero(state1.entangled&(state2.condition==STANDING)&unresolved)
            _resolve_weapon(second,first,entangle_effect,entangled1,charge2,state2,state1,rng,False,
                            needs_sixes=state2.fear_hit_sixes)
        if optional.first_entangle:
            entangled2=np.flatnonzero(state2.entangled&(state1.condition==STANDING)&unresolved)
            _resolve_weapon(first,second,entangle_effect,entangled2,charge1,state1,state2,rng,False,
                            needs_sixes=state1.fear_hit_sixes)
        charged1, charged2 = charge2, charge1
        # The Ogre's belch is a once-per-battle -1 To Hit on the enemy.
        _crude_belch_ogre(first, state2, state1, active_rows, decisions,
                          ledger, 0, round_index)
        _crude_belch_ogre(second, state1, state2, active_rows, decisions,
                          ledger, 1, round_index)
        if ledger.hit_penalty[0]:
            first = replace(first, global_effects=replace(
                first.global_effects,
                hit_modifier=first.global_effects.hit_modifier - ledger.hit_penalty[0]))
        if ledger.hit_penalty[1]:
            second = replace(second, global_effects=replace(
                second.global_effects,
                hit_modifier=second.global_effects.hit_modifier - ledger.hit_penalty[1]))
        # Opponent-supplied Leadership facts, then the phase's dance, then the
        # whole-pool declaration: the same order the scalar round uses.
        first = _apply_opponent_leadership(first, second)
        second = _apply_opponent_leadership(second, first)
        first = staff_power(first, decisions, f'round.{round_index}.first')
        second = staff_power(second, decisions, f'round.{round_index}.second')
        first = _select_shadow_dance(
            first, ledger, 'first', decisions, f'round.{round_index}.first')
        second = _select_shadow_dance(
            second, ledger, 'second', decisions, f'round.{round_index}.second')
        attack_first = _select_attack_replacement(
            first, first_round=first_round, charging=charge1,
            decisions=decisions, key=f'round.{round_index}.first')
        attack_second = _select_attack_replacement(
            second, first_round=first_round, charging=charge2,
            decisions=decisions, key=f'round.{round_index}.second')
        if has(attack_first.main_weapon, 'effect.serpent-staff-power'):
            state1.parry_remaining[:] = 0
        if has(attack_second.main_weapon, 'effect.serpent-staff-power'):
            state2.parry_remaining[:] = 0
        equipment1 = _row_equipment(
            original_first, attack_first, state1, count, first_round=first_round)
        equipment2 = _row_equipment(
            original_second, attack_second, state2, count, first_round=first_round)
        # Lazy Inconsistency: the first phase that reads WS/S/T/I/A draws each
        # value once for the round and reuses it.
        require_characteristics(first, state1, active_rows, rng,
                                ("WS", "S", "T", "I", "A"))
        require_characteristics(second, state2, active_rows, rng,
                                ("WS", "S", "T", "I", "A"))
        # Charm gates act before the pool is counted (Eye Pendant, Tranquil
        # Fauna).  A failed gate bars that warrior's attacks this phase.
        blocked1, blocked2 = _charm_gates(
            first, second, state1, state2, active_rows, rng, leadership,
            decisions, prepared, ledger, round_index, first_player_turn)
        ledger.charm_blocked[:] = blocked1 | blocked2
        blocked_first = blocked1
        blocked_second = blocked2
        # Gaoler Grapple: a Torturer may declare a hold instead of his pool.
        # The declaration is one choice per side, as the scalar pipeline asks
        # it once, and it owns only the rows it is legal for.
        grapple1 = _grapple_declaration(
            attack_first, second, state1, state2, active_rows, decisions, ledger,
            blocked_first, f'round.{round_index}.first')
        grapple2 = _grapple_declaration(
            attack_second, first, state2, state1, active_rows, decisions, ledger,
            blocked_second, f'round.{round_index}.second')
        if grapple1.any():
            held = _grapple_fighter(attack_first)
            for row in np.flatnonzero(grapple1):
                equipment1[int(row)] = held
        if grapple2.any():
            held = _grapple_fighter(attack_second)
            for row in np.flatnonzero(grapple2):
                equipment2[int(row)] = held
        attacks1 = np.zeros(count, dtype=np.int16)
        attacks2 = np.zeros(count, dtype=np.int16)
        # Mim without hands: the hand pool contributes nothing, while the
        # independently scheduled contributions keep their own events.
        mim1 = has(attack_first.global_effects, "condition.mim-no-hand-attacks")
        mim2 = has(attack_second.global_effects, "condition.mim-no-hand-attacks")
        # Both hands are forfeited, but a warrior whose extra attacks are their
        # own event keeps that event in the round order: ``remaining = max(1,
        # count) if extra else 0`` in the modular round.
        mim_extra1 = mim1 & bool(attack_first.extra_attacks)
        mim_extra2 = mim2 & bool(attack_second.extra_attacks)
        shifty1 = (first_round & charged1 & (not mim1)
                   & has(attack_first.global_effects, "skill.shifty")
                   & (not has(attack_first.main_weapon, "effect.serpent-staff-power"))
                   & (not (has(attack_first.main_weapon, "weapon.fist")
                       and unarmed_attack_cap_applies(attack_first.global_effects))))
        shifty2 = (first_round & charged2 & (not mim2)
                   & has(attack_second.global_effects, "skill.shifty")
                   & (not has(attack_second.main_weapon, "effect.serpent-staff-power"))
                   & (not (has(attack_second.main_weapon, "weapon.fist")
                       and unarmed_attack_cap_applies(attack_second.global_effects))))
        groups = _equipment_groups(active_rows, equipment1, equipment2)
        for a_f, d_f, group in groups:
            attacks1[group] = attack_count(
                a_f, charge1[group], first_round, state1.frenzy[group],
                charged1[group], state1.attack_penalty[group],
                state1.wounds[group] < a_f.characteristics.wounds,
                state1.attacks[group], player_turn=first_player_turn[group])
            attacks2[group] = attack_count(
                d_f, charge2[group], first_round, state2.frenzy[group],
                charged2[group], state2.attack_penalty[group],
                state2.wounds[group] < d_f.characteristics.wounds,
                state2.attacks[group], player_turn=(~first_player_turn)[group])
            # Spawn special attacks replace the built pool after the attack
            # count: one D6+1 per warrior and round (``resolve_spawn_attack_
            # count``), with the vomit replacement as the only printed
            # exception.
            if (has(a_f.global_effects, "mechanic.spawn-special-attacks")
                    and not has(a_f.main_weapon, "weapon.vomit-attack")):
                attacks1[group] = rng.integers(1, 7, group.size, dtype=np.int16) + 1
            if (has(d_f.global_effects, "mechanic.spawn-special-attacks")
                    and not has(d_f.main_weapon, "weapon.vomit-attack")):
                attacks2[group] = rng.integers(1, 7, group.size, dtype=np.int16) + 1
            if first_round:
                attacks1[group] += shifty1[group].astype(np.int16)
                attacks2[group] += shifty2[group].astype(np.int16)
            attacks1[group] = round_weapon_attack_count(
                a_f, d_f, attacks1[group], first_round=first_round,
                charging=charge1[group], charged=charged1[group])
            attacks2[group] = round_weapon_attack_count(
                d_f, a_f, attacks2[group], first_round=first_round,
                charging=charge2[group], charged=charged2[group])
            attacks1[group] = opposed_attack_count(
                a_f, d_f, attacks1[group], first_round=first_round,
                defer_grapple=True)
            attacks2[group] = opposed_attack_count(
                d_f, a_f, attacks2[group], first_round=first_round,
                defer_grapple=True)
        whip1 = _whipcrack_weapon(attack_first)
        whip2 = _whipcrack_weapon(attack_second)
        whip1_active = bool(
            first_round and whip1 is not None
            and (charge1 | charged1).any()
        )
        whip2_active = bool(
            first_round and whip2 is not None
            and (charge2 | charged2).any()
        )
        whip1_rows = (charge1 | charged1) if whip1_active else np.zeros(count, dtype=bool)
        whip2_rows = (charge2 | charged2) if whip2_active else np.zeros(count, dtype=bool)
        whip1_rows &= attacks1 > 0
        whip2_rows &= attacks2 > 0
        ordinary_attacks1 = attacks1 - whip1_rows.astype(np.int16) - shifty1.astype(np.int16)
        ordinary_attacks2 = attacks2 - whip2_rows.astype(np.int16) - shifty2.astype(np.int16)
        # A held warrior and his holder contribute no independent pool; a
        # declared hold fights with its single natural attack.
        attacks1[state1.grappled | state1.grappling] = 0
        attacks2[state2.grappled | state2.grappling] = 0
        attacks1[grapple1] = np.minimum(1, attacks1[grapple1])
        attacks2[grapple2] = np.minimum(1, attacks2[grapple2])
        # Crude Belch: the Halfling Elder's timed first-attack loss is separate
        # from the count clamps, so it removes one ordinary allocation.
        loss_on_first = np.zeros(count, dtype=bool)
        loss_on_second = np.zeros(count, dtype=bool)
        before_loss1 = attacks1.copy()
        before_loss2 = attacks2.copy()
        if first_round:
            loss_on_second = _crude_belch_losses(
                first, second, state1, state2, active_rows, rng, leadership[0],
                decisions, prepared, first=True, round_index=round_index)
            loss_on_first = _crude_belch_losses(
                second, first, state2, state1, active_rows, rng, leadership[1],
                decisions, prepared, first=False, round_index=round_index)
            ordinary_attacks1 = np.maximum(0, ordinary_attacks1 - loss_on_first)
            ordinary_attacks2 = np.maximum(0, ordinary_attacks2 - loss_on_second)
            attacks1 = np.maximum(0, attacks1 - loss_on_first)
            attacks2 = np.maximum(0, attacks2 - loss_on_second)
        # Noble: a pool of one reduced by a source loss keeps that attack when
        # an independent contribution (an extra natural attack, or the Stomp
        # against a Knocked Down foe) is still available.
        extra1 = any(charge1.any() or not has(weapon, "rule.horned-one")
                     for weapon in attack_first.extra_attacks)
        extra1 = extra1 or (has(attack_first.global_effects, "mechanic.noblesse-stomp")
                            and bool((state2.condition[active_rows] == KNOCKED_DOWN).any()))
        extra2 = any(charge2.any() or not has(weapon, "rule.horned-one")
                     for weapon in attack_second.extra_attacks)
        extra2 = extra2 or (has(attack_second.global_effects, "mechanic.noblesse-stomp")
                            and bool((state1.condition[active_rows] == KNOCKED_DOWN).any()))
        attacks1[(before_loss1 == 1) & loss_on_first & extra1] = 1
        attacks2[(before_loss2 == 1) & loss_on_second & extra2] = 1
        # Deathblow reads "the remainder of his attacks": the allocated pool is
        # captured before any readiness gate can zero it.
        deathblow_pool1 = attacks1.copy()
        deathblow_pool2 = attacks2.copy()
        # A warrior silenced by Stupidity, Animosity, a charm gate, fire, a net
        # or a spent lost turn contributes no pool at all.
        silent1 = (state1.stupidity_failed | ledger.animosity_failed
                   | blocked_first | state1.netted | state1.on_fire
                   | grapple1 | state1.grappled | state1.grappling)
        silent2 = (state2.stupidity_failed | ledger.animosity_failed
                   | blocked_second | state2.netted | state2.on_fire
                   | grapple2 | state2.grappled | state2.grappling)
        lost_turn1 = state1.massively_built_lost_turn & first_player_turn
        lost_turn2 = state2.massively_built_lost_turn & ~first_player_turn
        silent1 |= lost_turn1
        silent2 |= lost_turn2
        if lost_turn1.any():
            state1.massively_built_lost_turn[lost_turn1] = False
        if lost_turn2.any():
            state2.massively_built_lost_turn[lost_turn2] = False
        attacks1[silent1] = 0
        attacks2[silent2] = 0
        ordinary_attacks1[silent1] = 0
        ordinary_attacks2[silent2] = 0
        # Mim without hands: the hand pool carries nothing, while the
        # independently scheduled contributions still resolve in the ordinary
        # pool's own priority slot (never as a pre-emptive event).
        attacks1[mim1] = 0
        attacks2[mim2] = 0
        ordinary_attacks1[mim1] = 0
        ordinary_attacks2[mim2] = 0
        # ``pool_attack_weapons`` appends the Whipcrack bonus at the position
        # Mim's forfeit range always reaches, so that bonus is lost too.
        if mim1:
            whip1_rows[:] = False
        if mim2:
            whip2_rows[:] = False
        # Tentacle Grapple: one nominated allocation is removed from the real
        # weapon sequence, once per battle and never below the minimum.
        forfeit1, tentacle_whip1, tentacle_extra1 = _tentacle_forfeit(
            attack_first, second.global_effects,
            np.flatnonzero(unresolved & ~silent1),
            ordinary_attacks1, decisions, ledger, 1,
            f'round.{round_index}.first',
            charging=charge1, whip_rows=whip1_rows)
        forfeit2, tentacle_whip2, tentacle_extra2 = _tentacle_forfeit(
            attack_second, first.global_effects,
            np.flatnonzero(unresolved & ~silent2),
            ordinary_attacks2, decisions, ledger, 0,
            f'round.{round_index}.second',
            charging=charge2, whip_rows=whip2_rows)
        whip1_rows &= ~tentacle_whip1
        whip2_rows &= ~tentacle_whip2
        # Instinctual Violence nominates one allocation for the Strike First
        # tier; the ordinary pool then resolves the same allocation minus it.
        strike1 = _nominated_strike(
            attack_first, decisions, f'round.{round_index}.first',
            np.flatnonzero(unresolved & ~silent1 & (ordinary_attacks1 > 0)),
            ordinary_attacks1, first_round=first_round)
        strike2 = _nominated_strike(
            attack_second, decisions, f'round.{round_index}.second',
            np.flatnonzero(unresolved & ~silent2 & (ordinary_attacks2 > 0)),
            ordinary_attacks2, first_round=first_round)
        strike1_rows = np.zeros(count, dtype=bool)
        strike2_rows = np.zeros(count, dtype=bool)
        if strike1 is not None:
            strike1_rows[strike1[0]] = True
            ordinary_attacks1[strike1[0]] -= 1
        if strike2 is not None:
            strike2_rows[strike2[0]] = True
            ordinary_attacks2[strike2[0]] -= 1
        # Noblesse Stomp: a Knight adds one natural attack against a Knocked
        # Down opponent, immediately after his own ordinary event.
        stomp1_rows = np.zeros(count, dtype=bool)
        stomp2_rows = np.zeros(count, dtype=bool)
        if has(attack_first.global_effects, 'mechanic.noblesse-stomp'):
            stomp1_rows = (unresolved & ~silent1
                           & (state1.condition == STANDING)
                           & (state2.condition == KNOCKED_DOWN) & (attacks1 > 0)
                           & (not has(attack_first.main_weapon,
                                  'effect.serpent-staff-power')))
        if has(attack_second.global_effects, 'mechanic.noblesse-stomp'):
            stomp2_rows = (unresolved & ~silent2
                           & (state2.condition == STANDING)
                           & (state1.condition == KNOCKED_DOWN) & (attacks2 > 0)
                           & (not has(attack_second.main_weapon,
                                  'effect.serpent-staff-power')))
        stomp1_fighter = replace(
            attack_first, main_weapon=EffectSet(tags=('rule.noblesse-stomp',)),
            main_weapon_without_poison=None, off_hand=None,
            off_hand_without_poison=None, off_hand_attacks=False,
            extra_attacks=(), main_hand_slot='natural')
        stomp2_fighter = replace(
            attack_second, main_weapon=EffectSet(tags=('rule.noblesse-stomp',)),
            main_weapon_without_poison=None, off_hand=None,
            off_hand_without_poison=None, off_hand_attacks=False,
            extra_attacks=(), main_hand_slot='natural')
        # Priority and Initiative read the same per-group fighters: a backup
        # weapon or a mutation can change the weapon's priority tier.
        p1 = np.zeros(count, dtype=np.int8)
        p2 = np.zeros(count, dtype=np.int8)
        i1 = np.zeros(count, dtype=np.int32)
        i2 = np.zeros(count, dtype=np.int32)
        for a_f, d_f, group in groups:
            p1[group] = priority(a_f, d_f, first_round, charge1[group],
                                 charged1[group], stood1[group])
            p2[group] = priority(d_f, a_f, first_round, charge2[group],
                                 charged2[group], stood2[group])
            i1[group] = effective_initiative(a_f, state1)[group]
            i2[group] = effective_initiative(d_f, state2)[group]
        first_acts=(p1>p2)|((p1==p2)&(i1>i2));ties=(p1==p2)&(i1==i2)
        first_acts[ties]=rng.random(int(ties.sum()))<.5
        # Acting order per row: the fighter that won priority acts first, then
        # the opponent replies; whipcrack events keep their own Strike First
        # tier.  Scores are computed in int32: priority() returns int8, and
        # p * 100 overflows it for any tier above 1 (Frantic's 10 became -24,
        # silently demoting Strike-First fighters behind ordinary weapons —
        # the frenzy-vs-w2 deep-matrix divergence).
        priority_tie = (p1 == p2) & (i1 == i2)
        # Electrical Touch resolves the tie by deferring the choice to the
        # electric weapon's own strike-first effect.
        if any(has(f.global_effects, "mechanic.electrical-touch")
               for f in (first, second)):
            first_acts[priority_tie] = True
        # Shifty's nominated strike keeps its own weapon and enters the order at
        # that weapon's priority tier, not after the ordinary pool.
        shifty1_fighter = (
            _select_shifty_weapon(attack_first, decisions,
                                  f'round.{round_index}.first.shifty')
            if shifty1.any() else attack_first)
        shifty2_fighter = (
            _select_shifty_weapon(attack_second, decisions,
                                  f'round.{round_index}.second.shifty')
            if shifty2.any() else attack_second)
        sp1 = (priority(shifty1_fighter, second, first_round, charge1, charged1, stood1)
               if shifty1.any() else np.full(count, -1, dtype=np.int8))
        sp2 = (priority(shifty2_fighter, first, first_round, charge2, charged2, stood2)
               if shifty2.any() else np.full(count, -1, dtype=np.int8))
        # The nominated strike is a Strike First contribution: a non-negative
        # priority is raised to the first tier, exactly as the scalar pipeline
        # does, so it is not appended after the bearer's ordinary pool.  When
        # that puts it on its own ordinary event's tier and Initiative, the
        # strike resolves first.
        own_tie1 = shifty1 & (np.maximum(1, sp1.astype(np.int32))
                              == p1.astype(np.int32))
        own_tie2 = shifty2 & (np.maximum(1, sp2.astype(np.int32))
                              == p2.astype(np.int32))
        event_scores = np.stack((
            p1.astype(np.int32) * 100 + i1 + (priority_tie & first_acts),
            p2.astype(np.int32) * 100 + i2 + (priority_tie & ~first_acts),
            np.where(whip1_rows, 100 + i1, -10000),
            np.where(whip2_rows, 100 + i2, -10000),
            np.where(shifty1, np.maximum(1, sp1.astype(np.int32)) * 100 + i1
                     + own_tie1.astype(np.int32), -10000),
            np.where(shifty2, np.maximum(1, sp2.astype(np.int32)) * 100 + i2
                     + own_tie2.astype(np.int32), -10000),
            np.where(strike1_rows, 100 + i1, -10000),
            np.where(strike2_rows, 100 + i2, -10000),
            np.where(stomp1_rows, p1.astype(np.int32) * 100 + i1, -10000),
            np.where(stomp2_rows, p2.astype(np.int32) * 100 + i2, -10000),
        )).astype(np.int32)
        event_order = np.argsort(-event_scores, axis=0, kind="stable")
        whip1_fighter = (
            replace(attack_first, main_weapon=whip1, off_hand=None,
                    off_hand_attacks=False, extra_attacks=())
            if whip1 is not None else attack_first
        )
        whip2_fighter = (
            replace(attack_second, main_weapon=whip2, off_hand=None,
                    off_hand_attacks=False, extra_attacks=())
            if whip2 is not None else attack_second
        )

        # A declared hold resolves as its own single natural attack: a hit that
        # is not parried forces the victim's Strength-2 test, and failure puts
        # both warriors in the hold.
        if grapple1.any():
            _resolve_grapple(
                attack_first, second, np.flatnonzero(grapple1 & unresolved),
                state1, state2, rng, first_round, decisions,
                f'round.{round_index}.first.grapple')
        if grapple2.any():
            _resolve_grapple(
                attack_second, first, np.flatnonzero(grapple2 & unresolved),
                state2, state1, rng, first_round, decisions,
                f'round.{round_index}.second.grapple')
        # Eagles are separate Strike First contributions directed by their
        # Priestess, resolved before the warriors' own pools.
        for attacker, defender, a_state, d_state, charge, other, label in (
            (attack_first, second, state1, state2, charge1, equipment2, 'first'),
            (attack_second, first, state2, state1, charge2, equipment1, 'second'),
        ):
            rows = np.flatnonzero(unresolved & (a_state.condition == STANDING))
            for bird_index, weapon in enumerate(
                    w for w in attacker.extra_attacks if has(w, "rule.eagle-friend")):
                if rows.size == 0:
                    continue
                eagle = replace(attacker, main_weapon=weapon, off_hand=None,
                                off_hand_attacks=False, extra_attacks=())
                _resolve_attacks_by_equipment(
                    {row: eagle for row in range(count)}, other, rows,
                    np.ones(count, dtype=np.int16), charge, a_state, d_state,
                    rng, first_round, decisions,
                    f'round.{round_index}.{label}.eagle.{bird_index}')
        for event_index in range(10):
            event = event_order[event_index]
            rows_first = np.flatnonzero(
                unresolved & (state1.condition == STANDING)
                & (event == 0) & ((ordinary_attacks1 > 0)
                                  | (mim_extra1 & ~silent1))
            )
            rows_second = np.flatnonzero(
                unresolved & (state2.condition == STANDING)
                & (event == 1) & ((ordinary_attacks2 > 0)
                                  | (mim_extra2 & ~silent2))
            )
            rows_whip1 = np.flatnonzero(
                unresolved & (state1.condition == STANDING)
                & (event == 2) & whip1_rows
            )
            rows_whip2 = np.flatnonzero(
                unresolved & (state2.condition == STANDING)
                & (event == 3) & whip2_rows
            )
            rows_shifty1 = np.flatnonzero(
                unresolved & (state1.condition == STANDING)
                & (event == 4) & shifty1 & ~silent1
            )
            rows_shifty2 = np.flatnonzero(
                unresolved & (state2.condition == STANDING)
                & (event == 5) & shifty2 & ~silent2
            )
            rows_strike1 = np.flatnonzero(
                unresolved & (state1.condition == STANDING)
                & (event == 6) & strike1_rows)
            rows_strike2 = np.flatnonzero(
                unresolved & (state2.condition == STANDING)
                & (event == 7) & strike2_rows)
            rows_stomp1 = np.flatnonzero(
                unresolved & (state1.condition == STANDING)
                & (event == 8) & stomp1_rows)
            rows_stomp2 = np.flatnonzero(
                unresolved & (state2.condition == STANDING)
                & (event == 9) & stomp2_rows)
            if rows_first.size:
                _resolve_attacks_by_equipment(equipment1, equipment2, rows_first,
                    ordinary_attacks1, charge1, state1, state2, rng, first_round,
                    decisions, f'round.{round_index}.first', forfeits=forfeit1,
                    extra_forfeits=tentacle_extra1)
                ledger.deathblow_used[rows_first] = True
                _great_thirster_frenzy(attack_first, state1, state2, rows_first)
                if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows_first,rng)
                if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows_first,rng)
            if rows_second.size:
                _resolve_attacks_by_equipment(equipment2, equipment1, rows_second,
                    ordinary_attacks2, charge2, state2, state1, rng, first_round,
                    decisions, f'round.{round_index}.second', forfeits=forfeit2,
                    extra_forfeits=tentacle_extra2)
                ledger.deathblow_used[rows_second] = True
                _great_thirster_frenzy(attack_second, state2, state1, rows_second)
                if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows_second,rng)
                if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows_second,rng)
            if rows_whip1.size:
                _resolve_attacks_by_equipment(
                    {row: whip1_fighter for row in range(count)}, equipment2,
                    rows_whip1, np.ones(count,dtype=np.int16), charge1, state1,
                    state2, rng, first_round, decisions,
                    f'round.{round_index}.first.whipcrack')
                _great_thirster_frenzy(whip1_fighter, state1, state2, rows_whip1)
                if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows_whip1,rng)
                if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows_whip1,rng)
            if rows_whip2.size:
                _resolve_attacks_by_equipment(
                    {row: whip2_fighter for row in range(count)}, equipment1,
                    rows_whip2, np.ones(count,dtype=np.int16), charge2, state2,
                    state1, rng, first_round, decisions,
                    f'round.{round_index}.second.whipcrack')
                _great_thirster_frenzy(whip2_fighter, state2, state1, rows_whip2)
                if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows_whip2,rng)
                if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows_whip2,rng)
            if rows_shifty1.size:
                _resolve_attacks_by_equipment(
                    {row: shifty1_fighter for row in range(count)}, equipment2,
                    rows_shifty1, np.ones(count, dtype=np.int16), charge1,
                    state1, state2, rng, first_round, decisions,
                    f'round.{round_index}.first.shifty')
                _great_thirster_frenzy(shifty1_fighter, state1, state2, rows_shifty1)
                if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows_shifty1,rng)
                if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows_shifty1,rng)
            if rows_shifty2.size:
                _resolve_attacks_by_equipment(
                    {row: shifty2_fighter for row in range(count)}, equipment1,
                    rows_shifty2, np.ones(count, dtype=np.int16), charge2,
                    state2, state1, rng, first_round, decisions,
                    f'round.{round_index}.second.shifty')
                _great_thirster_frenzy(shifty2_fighter, state2, state1, rows_shifty2)
                if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows_shifty2,rng)
                if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows_shifty2,rng)
            if rows_strike1.size:
                _resolve_attacks_by_equipment(
                    {row: strike1[1] for row in range(count)}, equipment2,
                    rows_strike1, np.ones(count, dtype=np.int16), charge1,
                    state1, state2, rng, first_round, decisions,
                    f'round.{round_index}.first.strike-first')
            if rows_strike2.size:
                _resolve_attacks_by_equipment(
                    {row: strike2[1] for row in range(count)}, equipment1,
                    rows_strike2, np.ones(count, dtype=np.int16), charge2,
                    state2, state1, rng, first_round, decisions,
                    f'round.{round_index}.second.strike-first')
            if rows_stomp1.size:
                _resolve_attacks_by_equipment(
                    {row: stomp1_fighter for row in range(count)}, equipment2,
                    rows_stomp1, np.ones(count, dtype=np.int16), charge1,
                    state1, state2, rng, first_round, decisions,
                    f'round.{round_index}.first.stomp')
            if rows_stomp2.size:
                _resolve_attacks_by_equipment(
                    {row: stomp2_fighter for row in range(count)}, equipment1,
                    rows_stomp2, np.ones(count, dtype=np.int16), charge2,
                    state2, state1, rng, first_round, decisions,
                    f'round.{round_index}.second.stomp')
        # The Priest's bite is its own final event, after both pools.
        for attacker, defender, a_state, d_state, charge, other, label in (
            (attack_first, second, state1, state2, charge1, equipment2, 'first'),
            (attack_second, first, state2, state1, charge2, equipment1, 'second'),
        ):
            rows = np.flatnonzero(unresolved & (a_state.condition != OUT))
            for bite_index, weapon in enumerate(
                    w for w in attacker.extra_attacks
                    if has(w, "rule.strikes-last-bite")):
                if rows.size == 0:
                    continue
                bite = replace(attacker, main_weapon=weapon, off_hand=None,
                               off_hand_attacks=False, extra_attacks=())
                _resolve_attacks_by_equipment(
                    {row: bite for row in range(count)}, other, rows,
                    np.ones(count, dtype=np.int16), charge, a_state, d_state,
                    rng, first_round, decisions,
                    f'round.{round_index}.{label}.last-bite.{bite_index}')
        # Deathblow: a Slayer taken out before his own allocation still strikes
        # with the pool captured above; once he has struck, the skill is spent.
        for attacker, defender, a_state, d_state, charge, mine, other, pool, label in (
            (attack_first, second, state1, state2, charge1, equipment1, equipment2,
             deathblow_pool1, 'first'),
            (attack_second, first, state2, state1, charge2, equipment2, equipment1,
             deathblow_pool2, 'second'),
        ):
            rows = np.flatnonzero(
                unresolved & (a_state.condition == OUT)
                & ~ledger.deathblow_used
                & has(attacker.global_effects, "mechanic.death-blow")
                & (pool > 0))
            if rows.size == 0:
                continue
            ledger.deathblow_used[rows] = True
            _resolve_attacks_by_equipment(
                mine, other, rows, pool, charge, a_state, d_state, rng,
                first_round, decisions,
                f'round.{round_index}.{label}.death-blow')
        if optional.first_black_hunger:
            _black_hunger_backlash(first,state1,active_rows,rng)
        if optional.second_black_hunger:
            _black_hunger_backlash(second,state2,active_rows,rng)
    a=int(np.count_nonzero((state2.condition==OUT)&(state1.condition!=OUT)))
    b=int(np.count_nonzero((state1.condition==OUT)&(state2.condition!=OUT)))
    if observe:
        winner = np.zeros(count, dtype=np.int8)
        winner[(state2.condition == OUT) & (state1.condition != OUT)] = 1
        winner[(state1.condition == OUT) & (state2.condition != OUT)] = -1
        return VectorBatchObservation(
            winner=winner,
            rounds=rounds if rounds is not None else np.zeros(count, dtype=np.int64),
            first_wounds=state1.wounds.copy(),
            second_wounds=state2.wounds.copy(),
            first_condition=state1.condition.copy(),
            second_condition=state2.condition.copy(),
            first_resources=_resource_observation(state1),
            second_resources=_resource_observation(state2),
        )
    return a,b,count-a-b

def simulate_batch(first: CompiledFighter, second: CompiledFighter, count: int,
                   rng: np.random.Generator, maximum_rounds: int,
                   decisions: DecisionPolicy | None = None, *,
                   context: DuelContext | None = None) -> tuple[int, int, int]:
    result = _simulate_batch_core(first, second, count, rng, maximum_rounds, decisions, context=context)
    assert isinstance(result, tuple)
    return result

def simulate_batch_observed(first: CompiledFighter, second: CompiledFighter, count: int,
                            rng: np.random.Generator, maximum_rounds: int,
                            decisions: DecisionPolicy | None = None, *,
                            context: DuelContext | None = None) -> VectorBatchObservation:
    result = _simulate_batch_core(
        first, second, count, rng, maximum_rounds, decisions, observe=True, context=context,
    )
    assert isinstance(result, VectorBatchObservation)
    return result

def available_backends() -> tuple[str, ...]:
    """Return executable production backends in selection order."""
    try:
        from mordheim_combat import _combat_native
    except ImportError:
        return ("numpy",)
    from mordheim_combat.kernel import EFFECT_VALUE_FIELDS
    compatible = getattr(_combat_native, 'N_EFFECT_FIELDS', None) == len(EFFECT_VALUE_FIELDS)
    return ("native", "numpy") if hasattr(_combat_native, "simulate_duel") and compatible else ("numpy",)

# Per-batch stream derivation for the NumPy driver.
# The native backend seeds one stream per batch, which makes its batches
# independent, reproducible work units.  The NumPy driver used to carry a
# single Generator across the whole sample, so its batches were not
# splittable.  Deriving a generator per batch from (seed, batch_index) keeps
# every draw site untouched while turning each batch into an independent
# unit: a large sample can now be split across processes batch by batch and
# the totals are bit-for-bit identical to the sequential run.  Batch 0 keeps
# the historical seed, so single-batch samples (<= one batch_size) are
# unchanged.
_BATCH_STREAM_SALT = 0x9E3779B97F4A7C15  # golden-ratio constant (as native)


def _batch_seed(seed: int, batch_index: int) -> int:
    return (seed + batch_index * _BATCH_STREAM_SALT) % (1 << 32)


def batch_plan(simulations: int, batch_size: int) -> tuple[int, ...]:
    """Canonical per-batch duel counts: full batches plus a final partial."""
    full, remainder = divmod(simulations, batch_size)
    return (batch_size,) * full + ((remainder,) if remainder else ())


#: Historical internal alias (the canonical name is the public ``batch_plan``).
_batch_sizes = batch_plan


def _run_one_batch(first: CompiledFighter, second: CompiledFighter, count: int,
                   seed: int, batch_index: int, maximum_rounds: int,
                   decisions: DecisionPolicy | None,
                   context: DuelContext | None = None) -> tuple[int, int, int]:
    """Simulate exactly one batch on its own independent stream."""
    rng = np.random.default_rng(
        seed if batch_index == 0 else _batch_seed(seed, batch_index))
    return simulate_batch(first, second, count, rng, maximum_rounds, decisions, context=context)


def _simulate_duel_numpy(request: DuelRequest) -> DuelResult:
    first_wins = second_wins = unresolved = 0
    for batch_index, count in enumerate(_batch_sizes(
            request.simulations, request.batch_size)):
        if request.cancel_event is not None and request.cancel_event.is_set():
            raise SimulationCancelled("simulation cancelled")
        x, y, z = _run_one_batch(
            request.first, request.second, count, request.seed, batch_index,
            request.maximum_rounds, request.decision_policy, request.context,
        )
        first_wins += x
        second_wins += y
        unresolved += z
    return DuelResult(first_wins, second_wins, unresolved, request.simulations)


def batch_segment(first: CompiledFighter, second: CompiledFighter,
                  start: int, stop: int, simulations: int,
                  batch_size: int, seed: int, maximum_rounds: int,
                  decisions: DecisionPolicy | None,
                   context: DuelContext | None = None) -> tuple[int, int, int]:
    """Run whole batches ``[start, stop)`` of the canonical plan.

    Process-pool entry point for parallel execution over the batch plan:
    callers (``simulate_duel_parallel``, benchmark pools) submit contiguous
    ``[start, stop)`` plan ranges and sum the returned totals.
    """
    sizes = _batch_sizes(simulations, batch_size)
    first_wins = second_wins = unresolved = 0
    for batch_index in range(start, stop):
        x, y, z = _run_one_batch(
            first, second, sizes[batch_index], seed, batch_index,
            maximum_rounds, decisions, context,
        )
        first_wins += x
        second_wins += y
        unresolved += z
    return first_wins, second_wins, unresolved


#: Historical internal alias (the canonical name is the public ``batch_segment``).
_run_batch_segment = batch_segment


def simulate_duel_parallel(request: DuelRequest, *,
                           workers: int | None = None) -> DuelResult:
    """Bit-for-bit parallel equivalent of the NumPy driver.

    The sample is partitioned along whole batches (each batch has its own
    stream derived from the seed), so any worker split reproduces the
    sequential ``simulate_duel(backend="numpy")`` totals exactly.  Processes
    are required because the NumPy hot loops hold the GIL.  ``workers``
    defaults to the machine's core count and is capped at the number of
    batches; ``cancel_event`` is honoured between completed segments.
    """
    from concurrent.futures import ProcessPoolExecutor
    from concurrent.futures import as_completed
    import os

    from mordheim_combat.kernel import require_optimized_support
    require_optimized_support(request.first, request.second, backend="numpy")
    sizes = _batch_sizes(request.simulations, request.batch_size)
    total = len(sizes)
    available = workers if workers is not None else os.cpu_count() or 1
    workers_used = max(1, min(available, total))
    base, extra = divmod(total, workers_used)
    segments = []
    start = 0
    for index in range(workers_used):
        count = base + (1 if index < extra else 0)
        segments.append((start, start + count))
        start += count
    first_wins = second_wins = unresolved = 0
    with ProcessPoolExecutor(max_workers=workers_used) as pool:
        futures = [
            pool.submit(
                _run_batch_segment, request.first, request.second,
                start, stop, request.simulations, request.batch_size,
                request.seed, request.maximum_rounds,
                request.decision_policy, request.context,
            )
            for start, stop in segments
        ]
        try:
            for future in as_completed(futures):
                if request.cancel_event is not None and request.cancel_event.is_set():
                    raise SimulationCancelled("parallel simulation cancelled")
                x, y, z = future.result()
                first_wins += x
                second_wins += y
                unresolved += z
        finally:
            for future in futures:
                future.cancel()
    return DuelResult(first_wins, second_wins, unresolved, request.simulations)

def simulate_duel(request: DuelRequest, *, backend: str = "auto") -> DuelResult:
    """Run a duel through the selected backend without changing `DuelRequest`."""
    if backend not in {"auto", "numpy", "native"}:
        raise ValueError(f"unknown combat backend: {backend}")
    from mordheim_combat.kernel import require_optimized_support
    selected = available_backends()[0] if backend == "auto" else backend
    require_optimized_support(request.first, request.second, backend=selected)
    if selected == "numpy":
        return _simulate_duel_numpy(request)
    try:
        from mordheim_combat import _combat_native
    except ImportError as error:
        raise RuntimeError("native combat backend is not available") from error
    if not hasattr(_combat_native, "simulate_duel"):
        raise RuntimeError("native combat backend is not available")
    from mordheim_combat.kernel import EFFECT_VALUE_FIELDS
    if getattr(_combat_native, 'N_EFFECT_FIELDS', None) != len(EFFECT_VALUE_FIELDS):
        raise RuntimeError("native combat effect layout is stale; rebuild with `python -m pip install -e .`")
    from mordheim_combat.kernel import compile_duel_plan

    plan = compile_duel_plan(
        request.first, request.second, context=request.context, backend="native",
    )
    if request.context is not None and getattr(_combat_native, "CONTEXT_VERSION", None) != 1:
        if backend == "native":
            raise RuntimeError("native combat context layout is stale; rebuild the extension")
        return _simulate_duel_numpy(request)
    if not plan.optimization_eligible:
        if backend == "native":
            raise RuntimeError("native combat backend does not support this duel plan")
        return _simulate_duel_numpy(request)
    supports = getattr(_combat_native, "supports_plan", lambda _plan: False)
    if not supports(plan):
        if backend == "native":
            raise RuntimeError("native combat backend does not support this duel plan")
        return _simulate_duel_numpy(request)
    return _combat_native.simulate_duel(request, plan)
