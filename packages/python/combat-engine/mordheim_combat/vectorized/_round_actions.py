"""Vectorized engine: own-turn actions, timed conditions and per-row overlays.

Phase 3 port of the round-start section of ``modular.rounds.resolve_round``
(lines ~270-660) and of its per-round tricks: every function here is a batch
projection of one modular clause, evaluated for one fighter over the rows the
driver hands it.  Dice the modular round draws through ``_owned_roll`` /
``OwnedRollDice`` go through ``vectorized._owned.owned_roll`` so the personal
once-per-battle resources are spent on the same rolls as in the oracle.

Per-row changes to a fighter's *effects* (an extra attack this round, a
condition tag, a changed injury threshold) cannot live on the batch-level
``CompiledFighter``; :class:`RowOverlay` collects them and projects them onto
the per-row equipment dictionary the attack layers read, caching one fighter
copy per distinct overlay.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np

from mordheim_core.models import CompiledFighter, EffectSet
from mordheim_combat.modular.state import maximum_wounds
from mordheim_combat.vectorized._leadership import resolve_local_leadership
from mordheim_combat.vectorized._owned import owned_roll
from mordheim_combat.vectorized._types import (
    DJINN_CURSE, DJINN_LUCK, DJINN_NONE, DJINN_POWER_NAMES,
    KNOCKED_DOWN, OUT, STANDING, CombatState, has,
)

#: ``modular.rounds.JESTER_TRICK_STATES`` — one trick per combat turn.
JESTER_TRICK_STATES = ("dodge_trick_active", "banter_trick_active", "trip_trick_active")

#: Ludwig Petru's timed conditions: (tag, state column, bonus, expiry face).
PETRU_CONDITIONS = (
    ("condition.petru-debilitating", "toughness", -1, 6),
    ("condition.petru-strength", "strength", 1, 1),
    ("condition.petru-resilience", "toughness", 1, 1),
)

#: Column index of each characteristic in ``CombatState.random_modifiers``.
_STAT_ROWS = {"weapon_skill": 0, "strength": 1, "toughness": 2, "initiative": 3, "attacks": 4}


def _choose(decisions, key: str, fighter) -> bool:
    return True if decisions is None else decisions.choose(key, fighter)


# ---------------------------------------------------------------------------
# Per-row effect overlay
# ---------------------------------------------------------------------------
class RowOverlay:
    """Per-row additions to one fighter's ``global_effects`` for this round."""

    __slots__ = ("count", "attack_bonus", "tags", "out_threshold", "_cache")

    def __init__(self, count: int) -> None:
        self.count = int(count)
        self.attack_bonus = np.zeros(count, dtype=np.int16)
        self.tags: dict[str, np.ndarray] = {}
        self.out_threshold = np.zeros(count, dtype=np.int8)
        self._cache: dict[tuple, CompiledFighter] = {}

    def add_attacks(self, rows: np.ndarray, amount: int = 1) -> None:
        self.attack_bonus[rows] += amount

    def add_tag(self, tag: str, rows: np.ndarray) -> None:
        mask = self.tags.get(tag)
        if mask is None:
            mask = np.zeros(self.count, dtype=bool)
            self.tags[tag] = mask
        mask[rows] = True

    def set_out_threshold(self, rows: np.ndarray, value: int) -> None:
        self.out_threshold[rows] = value

    def tagged(self, tag: str) -> np.ndarray:
        mask = self.tags.get(tag)
        return np.zeros(self.count, dtype=bool) if mask is None else mask

    def is_empty(self) -> bool:
        return (not self.attack_bonus.any() and not self.out_threshold.any()
                and not any(mask.any() for mask in self.tags.values()))

    def row_key(self, row: int) -> tuple | None:
        tags = tuple(tag for tag, mask in self.tags.items() if mask[row])
        bonus = int(self.attack_bonus[row])
        threshold = int(self.out_threshold[row])
        if not tags and not bonus and not threshold:
            return None
        return bonus, tags, threshold

    def project(self, base: CompiledFighter, key: tuple) -> CompiledFighter:
        cached = self._cache.get((id(base), key))
        if cached is not None:
            return cached
        bonus, tags, threshold = key
        effect = base.global_effects
        changes = {}
        if tags:
            changes["tags"] = (*effect.tags, *(tag for tag in tags if tag not in effect.tags))
        if bonus:
            changes["attacks_bonus"] = effect.attacks_bonus + bonus
        if threshold:
            changes["out_of_action_threshold"] = threshold
        projected = replace(base, global_effects=replace(effect, **changes))
        self._cache[(id(base), key)] = projected
        return projected

    def apply(self, equipment: dict[int, CompiledFighter]) -> None:
        """Project the overlay onto a per-row equipment dictionary in place."""
        if self.is_empty():
            return
        for row, base in equipment.items():
            key = self.row_key(row)
            if key is not None:
                equipment[row] = self.project(base, key)

    def variants(self, fighter: CompiledFighter, rows: np.ndarray,
                 tags: tuple[str, ...]) -> list[tuple[CompiledFighter, np.ndarray]]:
        """Split ``rows`` by the subset of ``tags`` each row carries.

        For batch-level consumers (the Psychology gates take one fighter),
        each group gets a copy carrying exactly its rows' tags.
        """
        rows = np.asarray(rows, dtype=np.intp)
        present = [tag for tag in tags if tag in self.tags and self.tags[tag][rows].any()]
        if not present:
            return [(fighter, rows)]
        codes = np.zeros(rows.size, dtype=np.int64)
        for index, tag in enumerate(present):
            codes |= self.tags[tag][rows].astype(np.int64) << index
        groups = []
        for code in np.unique(codes):
            subset = rows[codes == code]
            carried = tuple(tag for index, tag in enumerate(present) if code >> index & 1)
            variant = fighter if not carried else replace(fighter, global_effects=replace(
                fighter.global_effects,
                tags=(*fighter.global_effects.tags,
                      *(tag for tag in carried if tag not in fighter.global_effects.tags))))
            groups.append((variant, subset))
        return groups


# ---------------------------------------------------------------------------
# Round-start state transitions (modular resolve_round, in its order)
# ---------------------------------------------------------------------------
def drenok_berserker(fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
                     rng: np.random.Generator, decisions, key: str) -> None:
    """Drenok's Berserker: fighting at zero Wounds needs a fresh 4+ each turn."""
    if not has(fighter.global_effects, "mechanic.drenok-berserker"):
        return
    fighting = rows[state.drenok_fighting[rows]]
    if fighting.size == 0:
        return
    healed = fighting[state.wounds[fighting] > 0]
    state.drenok_fighting[healed] = False
    testing = fighting[state.wounds[fighting] <= 0]
    if testing.size == 0:
        return
    roll = owned_roll(fighter, state, testing, rng, f"{key}.drenok-berserker",
                      decisions=decisions).values
    keep = roll >= 4
    state.drenok_fighting[testing] = keep
    state.condition[testing[keep]] = STANDING
    state.condition[testing[~keep]] = OUT


def poetry_decay(fighter: CompiledFighter, state: CombatState, rows: np.ndarray) -> None:
    """Poetry's inspiration lapses after round 0: -1 WS, once."""
    spent = rows[state.resources.spent("poetry-inspiration-active")[rows]]
    if spent.size == 0:
        return
    state.weapon_skill[spent] = np.maximum(0, state.weapon_skill[spent] - 1)
    if (has(fighter.global_effects, "mechanic.inconsistency")
            and any(stat == "WS" for stat, *_ in fighter.random_characteristics)):
        state.random_modifiers[_STAT_ROWS["weapon_skill"], spent] -= 1
    state.resources.release("poetry-inspiration-active", spent)


def timed_conditions(fighter: CompiledFighter, overlay: RowOverlay, rows: np.ndarray, *,
                     round_index: int, owner_first: bool, initial_first_turn: np.ndarray,
                     charged_by_opponent: np.ndarray) -> None:
    """The per-row half of the supplied timed conditions (rounds.py ~330-346).

    Righteous Charge depends on who charged and Art Thou Ready on who owns the
    first player turn, so both are overlays; the batch-uniform conditions
    (Follow Me, Poetry's first-round attack, Raise Our Insignia) are tagged on
    the batch fighter by the driver.
    """
    effect = fighter.global_effects
    if (round_index == 0 and fighter.mounted
            and has(effect, "condition.righteous-charge")):
        charged = rows[charged_by_opponent[rows]]
        for tag in ("condition.righteous-charge-active", "mechanic.causes-fear",
                    "mechanic.psychology-immunity"):
            overlay.add_tag(tag, charged)
    if has(effect, "condition.command.art-thou-ready-to-die-fighting"):
        limit = np.where(initial_first_turn[rows] == owner_first, 2, 1)
        overlay.set_out_threshold(rows[round_index < limit], 6)


def feral_instinct(fighter: CompiledFighter, state: CombatState, rows: np.ndarray, *,
                   first: bool, key: str, rng, leadership, decisions, context,
                   opponent: CompiledFighter) -> None:
    """Feral Instinct: an own-turn Leadership test whose failure is recorded."""
    if not has(fighter.global_effects, "mechanic.feral-instinct"):
        return
    active = rows[state.condition[rows] != OUT]
    if active.size == 0:
        return
    passed = resolve_local_leadership(
        fighter, state, active, first=first, key=f"{key}.feral-instinct", rng=rng,
        context=context, decisions=decisions, resources=leadership, opponent=opponent)
    state.feral_instinct_failed[active] = ~passed


def petru_expiry(fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
                 rng: np.random.Generator, decisions, key: str) -> None:
    """Petru's timed conditions: an own-turn D6 on the printed face ends them."""
    active = rows[state.condition[rows] != OUT]
    for tag, stat, bonus, expiry in PETRU_CONDITIONS:
        if not has(fighter.global_effects, tag) or active.size == 0:
            continue
        pending = active[state.resources.available(tag, active)]
        if pending.size == 0:
            continue
        roll = owned_roll(fighter, state, pending, rng,
                          f"{key}.{tag.removeprefix('condition.')}", decisions=decisions).values
        expired = pending[roll == expiry]
        if expired.size == 0:
            continue
        state.resources.spend(tag, expired)
        column = getattr(state, stat)
        column[expired] = np.maximum(1, column[expired] - bonus)
        state.random_modifiers[_STAT_ROWS[stat], expired] -= bonus


def danse_macabre(fighter: CompiledFighter, state: CombatState, rows: np.ndarray, *,
                  first: bool, key: str, rng, leadership, decisions, context,
                  opponent: CompiledFighter, round_index: int,
                  own_charges: np.ndarray) -> np.ndarray:
    """Danse Macabre: the controlled warrior tests each own turn.

    Returns the rows whose round-0 charge a failed test cancels; the driver
    clears those charges and disengages the rows, as it does for Stupidity.
    """
    controlled = rows[(state.condition[rows] != OUT) & state.danse_macabre_controlled[rows]]
    if controlled.size == 0:
        return controlled
    passed = resolve_local_leadership(
        fighter, state, controlled, first=first, key=f"{key}.danse-macabre", rng=rng,
        context=context, decisions=decisions, resources=leadership, opponent=opponent)
    state.danse_macabre_controlled[controlled] = ~passed
    if round_index != 0:
        return np.zeros(0, dtype=np.intp)
    return controlled[~passed & own_charges[controlled]]


def herb_lore(fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
              rng: np.random.Generator, decisions, key: str, *,
              lost_turn: np.ndarray) -> None:
    """Herb Lore: an own-turn 4+ heals one Wound up to the printed maximum."""
    effect = fighter.global_effects
    # ``herb-lore-outside-combat`` needs a disengaged row; a row that is no
    # longer engaged has already left the batch, so only the in-combat clause
    # can act here.
    if not has(effect, "mechanic.herb-lore"):
        return
    maximum = fighter.characteristics.wounds + int(has(effect, "skill.monstrous"))
    eligible = rows[(state.condition[rows] != OUT) & ~lost_turn[rows]
                    & ~(state.grappled[rows] | state.grappling[rows] | state.netted[rows])
                    & (state.wounds[rows] < maximum)]
    if eligible.size == 0 or not _choose(decisions, f"{key}.herb-lore", fighter):
        return
    roll = owned_roll(fighter, state, eligible, rng, f"{key}.herb-lore",
                      decisions=decisions).values
    healed = eligible[roll >= 4]
    state.wounds[healed] = np.minimum(maximum, state.wounds[healed] + 1)


def rousing_sermon(fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
                   decisions, key: str, round_index: int, overlay: RowOverlay, *,
                   lost_turn: np.ndarray) -> None:
    """Rousing Sermon: once per battle, +1 Attack in the preacher's own phase."""
    sermon_key = f"round.{round_index}.rousing-sermon"
    if has(fighter.global_effects, "mechanic.rousing-sermon"):
        eligible = rows[np.isin(state.condition[rows], (STANDING, KNOCKED_DOWN))
                        & ~lost_turn[rows]
                        & ~(state.grappled[rows] | state.grappling[rows] | state.netted[rows])
                        & state.resources.available("rousing-sermon", rows)]
        if eligible.size and _choose(decisions, f"{key}.rousing-sermon", fighter):
            state.resources.spend("rousing-sermon", eligible)
            state.resources.spend(sermon_key, eligible)
    preaching = rows[state.resources.spent(sermon_key)[rows]]
    if preaching.size:
        overlay.add_attacks(preaching)


def black_hunger(fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
                 round_index: int, overlay: RowOverlay) -> np.ndarray:
    """Black Hunger: +1 Attack and the active condition in the bearer's turn.

    Returns the rows that carry the condition this round (the backlash rows).
    """
    if not has(fighter.global_effects, "mechanic.black-hunger"):
        return np.zeros(0, dtype=np.intp)
    active = rows[(state.condition[rows] != OUT)
                  & ~(state.grappled[rows] | state.grappling[rows] | state.netted[rows])]
    if active.size:
        overlay.add_attacks(active)
        overlay.add_tag("condition.black-hunger-active", active)
        state.resources.spend(f"black-hunger-active.{round_index}", active)
    return active


def lunatics(fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
             rng: np.random.Generator, decisions, key: str) -> None:
    """Lunatics: each turn a D6 grants Frenzy (1-3) or Stupidity (4-6)."""
    if not has(fighter.global_effects, "mechanic.lunatics") or rows.size == 0:
        return
    roll = owned_roll(fighter, state, rows, rng, f"{key}.lunatics", decisions=decisions).values
    state.lunatic_result[rows] = roll
    state.frenzy[rows] |= roll <= 3
    state.lunatic_stupidity[rows] |= roll >= 4


def persistent_frenzy(fighter: CompiledFighter, state: CombatState, rows: np.ndarray) -> None:
    """Persistent Frenzy is restored at the start of every round."""
    worn = has(fighter.global_effects, "mechanic.persistent-frenzy")
    bare = has(fighter.global_effects_without_equipment, "mechanic.persistent-frenzy")
    if not (worn or bare):
        return
    cast_off = state.equipment_cast_off[rows]
    state.frenzy[rows] |= np.where(cast_off, bare, worn)


def clamp_wounds(fighter: CompiledFighter, state: CombatState, rows: np.ndarray) -> None:
    """A Wound an item folded into the profile cannot outlive the item."""
    state.wounds[rows] = np.minimum(state.wounds[rows], maximum_wounds(fighter))


def djinn_power(fighter: CompiledFighter, state: CombatState, own_rows: np.ndarray,
                all_rows: np.ndarray, decisions, key: str, overlay: RowOverlay, *,
                lost_turn: np.ndarray, freed_from_net: np.ndarray) -> None:
    """Djinn's Curse: one power per own turn, never the same twice running.

    The chosen power's condition is carried by the bearer's rows in every
    phase until its next own turn; ``condition.djinns-curse-active`` and
    ``condition.djinns-luck-active`` are consumed by the attack contexts.
    """
    if not has(fighter.global_effects, "mechanic.djinns-curse"):
        return
    eligible = own_rows[(state.condition[own_rows] == STANDING) & ~lost_turn[own_rows]
                        & ~freed_from_net[own_rows]
                        & ~(state.grappled[own_rows] | state.grappling[own_rows])]
    selected = np.full(own_rows.size, DJINN_NONE, dtype=np.int8)
    chosen = np.zeros(own_rows.size, dtype=bool)
    eligible_mask = np.isin(own_rows, eligible)
    for code in (DJINN_CURSE, DJINN_LUCK):
        candidates = eligible_mask & ~chosen & (state.last_djinn_power[own_rows] != code)
        if candidates.any() and _choose(decisions, f"{key}.djinn-power.{DJINN_POWER_NAMES[code]}", fighter):
            selected[candidates] = code
            chosen |= candidates
    state.djinn_power[own_rows] = selected
    state.last_djinn_power[own_rows] = selected
    for code, name in DJINN_POWER_NAMES.items():
        active = all_rows[state.djinn_power[all_rows] == code]
        if active.size:
            overlay.add_tag(f"condition.djinns-{name}-active", active)


def devoted_to_the_vampire(fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
                           killer_state: CombatState, overlay: RowOverlay) -> None:
    """Devoted to the Vampire: the supplied Lahmian's plight grants Frenzy."""
    effect = fighter.global_effects
    if not has(effect, "mechanic.devoted-to-the-vampire") or rows.size == 0:
        return
    avenging = (has(effect, "condition.devoted-vampire-killed")
                & (killer_state.condition[rows] != OUT))
    caused = avenging | has(effect, "condition.devoted-vampire-down")
    granted = rows[caused]
    state.frenzy[granted] = True
    state.devoted_frenzy[granted] = True
    lapsed = rows[~caused & state.devoted_frenzy[rows]]
    state.frenzy[lapsed] = bool(effect.frenzy)
    state.devoted_frenzy[lapsed] = False
    overlay.add_tag("condition.devoted-killer-hatred", rows[avenging])


def main_gauche_modes(fighter: CompiledFighter, decisions, key: str) -> CompiledFighter:
    """Main Gauche: parry this round or strike with it as a dagger."""
    off = fighter.off_hand
    if (off is None or not has(off, "weapon.main-gauche")
            or not has(fighter.global_effects, "mechanic.main-gauche-modes")):
        return fighter
    parry = _choose(decisions, f"{key}.main-gauche-parry", fighter)
    clean = fighter.off_hand_without_poison or off
    if not parry:
        off = replace(off, parry=False, tags=(*off.tags, "weapon.dagger"), target_armour_bonus=1)
        clean = replace(clean, parry=False, tags=(*clean.tags, "weapon.dagger"), target_armour_bonus=1)
    return replace(fighter, off_hand=off, off_hand_without_poison=clean,
                   off_hand_attacks=not parry)


def jester_tricks(fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
                  decisions, key: str) -> None:
    """Confound and Confuse: one of the three printed tricks per combat turn."""
    if not has(fighter.global_effects, "mechanic.confound-and-confuse"):
        return
    free = rows[~(state.grappled[rows] | state.grappling[rows])]
    if free.size == 0:
        return
    accepted = next((slot for slot in JESTER_TRICK_STATES
                     if _choose(decisions, f"{key}.jester-trick.{slot}", fighter)), None)
    state.resources.release("jester.trip", free)
    for slot in JESTER_TRICK_STATES:
        getattr(state, slot)[free] = slot == accepted


def select_tails(base: CompiledFighter, state: CombatState, rows: np.ndarray,
                 decisions, key: str) -> None:
    """Per-round tail selection for rows that carry a mutation."""
    from mordheim_combat.modular.mutations import select_mutation_tail
    from mordheim_combat.vectorized._mutations import read_mutation_state, write_mutation_state

    for value in rows:
        row = int(value)
        if (not state.mutations[row] or state.condition[row] != STANDING
                or state.grappled[row] or state.grappling[row] or state.stupidity_failed[row]):
            continue
        current = read_mutation_state(state, row)
        write_mutation_state(state, row, select_mutation_tail(base, current, decisions, key))


def inquisitor_brands(owner: CompiledFighter, target: CompiledFighter,
                      base_target: CompiledFighter, owner_state: CombatState,
                      target_state: CombatState, rows: np.ndarray,
                      rng: np.random.Generator, decisions, key: str) -> None:
    """Solkan's Inquisitor: a judgement of 6 brands the enemy with a D66 mark."""
    from mordheim_combat.vectorized._mutations import apply_brand_row
    from mordheim_combat.vectorized._owned import OwnedRowDice

    if not has(owner.global_effects, "mechanic.solkan-inquisitor"):
        return
    if any(has(target.global_effects, tag) for tag in
           ("nature.undead", "identity.chaos-follower", "warband-group.chaotic")):
        return
    active = rows[(owner_state.condition[rows] != OUT) & (target_state.condition[rows] != OUT)]
    if active.size == 0:
        return
    judgement = owned_roll(owner, owner_state, active, rng, f"{key}.judgement",
                           decisions=decisions).values
    branded = active[judgement == 6]
    if branded.size == 0:
        return
    tens = owned_roll(owner, owner_state, branded, rng, f"{key}.mutation.tens",
                      decisions=decisions).values
    units = owned_roll(owner, owner_state, branded, rng, f"{key}.mutation.units",
                       decisions=decisions).values
    options = {option.roll: option for option in owner.mutation_options}
    for row, result in zip(branded, 10 * tens + units):
        option = options.get(int(result))
        if option is None:
            raise ValueError(
                f"Inquisitor requires its complete source D66 mutation chart (missing {int(result)})")
        # The brand's own dice are the Inquisitor's owned rolls (modular
        # ``_inquisitor_brands`` hands ``apply_brand`` its ``owned`` wrapper).
        apply_brand_row(base_target, target_state, int(row), option, rng, decisions,
                        f"{key}.mutation.{int(result)}",
                        dice=OwnedRowDice(owner, owner_state, int(row), rng, decisions))


def sea_shanty_losses(owner: CompiledFighter, target: CompiledFighter,
                      owner_state: CombatState, target_state: CombatState,
                      rows: np.ndarray, rng: np.random.Generator, leadership, decisions,
                      context, *, owner_first: bool, first_player_turn: np.ndarray,
                      lost_turn: np.ndarray, round_index: int,
                      contacting: bool) -> np.ndarray:
    """Sea Shanty: the enemy tests Leadership or loses one attack this phase."""
    lost = np.zeros(owner_state.wounds.size, dtype=bool)
    shanty = next((tag for tag in ("mechanic.sea-shanty", "mechanic.sea-shanty-psychology")
                   if has(owner.global_effects, tag)), None)
    if shanty is None or not contacting:
        return lost
    if shanty == "mechanic.sea-shanty" and any(has(target.global_effects, tag) for tag in
            ("nature.undead", "nature.possessed", "nature.daemon", "nature.construct",
             "nature.non-living")):
        return lost
    eligible = rows[(owner_state.condition[rows] == STANDING) & ~owner_state.stupidity_failed[rows]
                    & ~(owner_state.grappled[rows] | owner_state.grappling[rows])
                    & (target_state.condition[rows] != OUT)]
    if shanty == "mechanic.sea-shanty-psychology":
        if has(target.global_effects, "mechanic.psychology-immunity"):
            return lost
        eligible = eligible[~target_state.frenzy[eligible]]
    own_turn = first_player_turn[eligible] == owner_first
    if shanty == "mechanic.sea-shanty":
        eligible = eligible[own_turn]
        own_turn = np.ones(eligible.size, dtype=bool)
    eligible = eligible[~(lost_turn[eligible] & own_turn)]
    label = "first" if owner_first else "second"
    if eligible.size == 0 or not _choose(decisions, f"round.{round_index}.{label}.sea-shanty", owner):
        return lost
    passed = resolve_local_leadership(
        target, target_state, eligible, first=not owner_first,
        key=f"round.{round_index}.{label}.sea-shanty.leadership", rng=rng,
        context=context, decisions=decisions, resources=leadership, opponent=owner,
        close_combat=True)
    lost[eligible[~passed]] = True
    return lost


def mantle_of_crows(owner: CompiledFighter, target: CompiledFighter,
                    owner_state: CombatState, target_state: CombatState,
                    rows: np.ndarray, rng: np.random.Generator, first_round: bool,
                    decisions, key: str) -> None:
    """Mantle of Crows: one automatic Strength 2 hit opens each combat phase."""
    from mordheim_combat.vectorized._attacks import _resolve_weapon

    if not has(owner.global_effects, "mechanic.mantle-of-crows"):
        return
    active = rows[(owner_state.condition[rows] != OUT) & (target_state.condition[rows] != OUT)]
    if active.size == 0:
        return
    from mordheim_combat.vectorized._driver import _great_thirster_frenzy, _rescue_force_of_will

    crows = EffectSet(tags=("mechanic.mantle-of-crows",), fixed_strength=2,
                      automatic_hit=True, cannot_be_parried=True)
    crow_attacker = replace(owner, global_effects=EffectSet())
    _resolve_weapon(crow_attacker, target, crows, active,
                    np.zeros(owner_state.wounds.size, dtype=bool), owner_state,
                    target_state, rng, first_round, decisions=decisions, key=key,
                    reaction_source=owner)
    # ``_react_to_wound(owner, target, ...)``: the victim's immediate rescue
    # and the owner's Great Thirster reaction.
    _rescue_force_of_will(target, target_state, active, rng, decisions, f"{key}.force-of-will")
    _great_thirster_frenzy(owner, owner_state, target_state, active)


def wheelo_impact(owner: CompiledFighter, target: CompiledFighter,
                  owner_state: CombatState, target_state: CombatState,
                  rows: np.ndarray, rng: np.random.Generator, decisions, *,
                  owner_first: bool, charging: np.ndarray, charged: np.ndarray,
                  blocked: np.ndarray) -> None:
    """The Wheelo's collision on the charge (or the spear's counter-charge)."""
    from mordheim_combat.vectorized._attacks import _resolve_weapon

    effect = owner.global_effects
    if not has(effect, "mechanic.wheelo-impact"):
        return
    counter = charged & has(effect, "wheelo.fitting.spear")
    active = rows[(charging[rows] | counter[rows]) & (owner_state.condition[rows] != OUT)
                  & (target_state.condition[rows] != OUT) & ~blocked[rows]]
    if active.size == 0:
        return
    from mordheim_combat.vectorized._driver import _great_thirster_frenzy, _rescue_force_of_will

    label = "first" if owner_first else "second"
    count = np.ones(active.size, dtype=np.int16)
    rolling = charging[active]
    if rolling.any():
        roll = owned_roll(owner, owner_state, active[rolling], rng,
                          f"round.0.{label}.impact-count", decisions=decisions,
                          close_combat=True).values
        count[rolling] = (roll + 1) // 2
    first_impact = owner_state.resources.available("wheelo.first-impact", active)
    owner_state.resources.spend("wheelo.first-impact", active)
    collision = replace(owner, global_effects=EffectSet())
    penetration = int(has(effect, "wheelo.fitting.axe"))
    club = has(effect, "wheelo.fitting.club")
    morning_star = has(effect, "wheelo.fitting.morning-star")
    for strength, selector in ((5, first_impact & morning_star), (4, ~(first_impact & morning_star))):
        group = active[selector]
        group_count = count[selector]
        if group.size == 0:
            continue
        weapon = EffectSet(fixed_strength=strength, automatic_hit=True, cannot_be_parried=True,
                           armour_penetration=penetration, concussion=club)
        for index in range(int(group_count.max())):
            hit_rows = group[(group_count > index)
                             & (owner_state.condition[group] != OUT)
                             & (target_state.condition[group] != OUT)]
            if hit_rows.size == 0:
                break
            impact_key = f"round.0.{label}.impact.{index}"
            _resolve_weapon(collision, target, weapon, hit_rows,
                            np.zeros(owner_state.wounds.size, dtype=bool), owner_state,
                            target_state, rng, True, melee_attack=False,
                            decisions=decisions, key=impact_key, reaction_source=owner)
            _rescue_force_of_will(target, target_state, hit_rows, rng, decisions,
                                  f"{impact_key}.force-of-will")
            _great_thirster_frenzy(owner, owner_state, target_state, hit_rows)
