"""combat: Pooled attack resolution and pool-level special rules."""
from __future__ import annotations
from mordheim_combat import phases

from dataclasses import replace
from types import SimpleNamespace
from mordheim_combat.phases import _characteristic_test
from mordheim_combat.modular.aftermath import _react_to_wound
from mordheim_combat.modular.contexts import _attack_strength
from mordheim_combat.modular.contexts import _combined_effect
from mordheim_combat.modular.contexts import _hit_reroll
from mordheim_combat.modular.contexts import _injury_context
from mordheim_combat.modular.contexts import _parry_context
from mordheim_combat.modular.contexts import prepare_armour_context
from mordheim_combat.modular.contexts import prepare_hit_context
from mordheim_combat.modular.contexts import prepare_special_save_context
from mordheim_combat.modular.contexts import prepare_wound_context
from mordheim_combat.modular.contexts import weapon_against_opponent
from mordheim_combat.modular.contexts import OwnedRollDice, _estalian_parry
from mordheim_combat.modular.state import AttackOutcome
from mordheim_combat.modular.state import FighterState
from mordheim_combat.modular.state import require_characteristics
from mordheim_combat.phases import BearHugContext
from mordheim_combat.phases import Condition
from mordheim_combat.phases import Phase
from mordheim_combat.phases import has_tag
from mordheim_combat.phases import resolve_armour
from mordheim_combat.phases import resolve_bear_hug
from mordheim_combat.phases import resolve_hit
from mordheim_combat.phases import resolve_injury
from mordheim_combat.phases import resolve_parry
from mordheim_combat.phases import resolve_special_save
from mordheim_combat.phases import resolve_wound
from mordheim_core.dice import DecisionPolicy
from mordheim_core.dice import DiceSource
from mordheim_core.dice import RollRequest
from mordheim_core.effects import merge_effects
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet


from .attacks import resolve_reference_attack
from .equipment import whipcrack_weapon


def electrical_touch_weapon(defender: CompiledFighter) -> EffectSet:
    return EffectSet(tags=("mechanic.electrical-touch-attack",), automatic_hit=True,
        fixed_strength=5 if has_tag(defender.global_effects, "condition.metal-armour") else 3,
        ignore_armour=True)

def _weapon_for_attack(fighter: CompiledFighter, index: int, count: int, first_round: bool) -> EffectSet:
    if not fighter.off_hand_attacks or fighter.off_hand is None:
        return fighter.main_weapon
    main_pistol = any(phases.has_tag(fighter.main_weapon, tag) for tag in ("weapon.pistol", "weapon.duelling-pistol"))
    off_pistol = any(phases.has_tag(fighter.off_hand, tag) for tag in ("weapon.pistol", "weapon.duelling-pistol"))
    if main_pistol:
        return fighter.off_hand if not first_round or index > 0 else fighter.main_weapon
    if off_pistol and not first_round:
        return fighter.main_weapon
    return fighter.off_hand if index == count - 1 else fighter.main_weapon


def _grapple_lost_attacks(
    weapons: tuple[EffectSet, ...], lost: int, mutant: CompiledFighter,
    decisions: DecisionPolicy, key: str, minimum_attacks: int = 1,
) -> tuple[EffectSet, ...]:
    """Nominate an allocated attack, preserving the warrior's phase minimum.

    A separately timed bonus allows the current pool to fall to zero. Declining
    all offers leaves the actual allocation untouched; no count is reconstructed.
    """

    while lost > 0 and len(weapons) > minimum_attacks:
        for index in range(len(weapons)):
            if decisions.choose(f"{key}.grapple-lost-attack.{index}", mutant):
                weapons = (*weapons[:index], *weapons[index + 1:])
                break
        else:
            return weapons
        lost -= 1
    return weapons


def allocate_attack_weapons(
    fighter: CompiledFighter, count: int, first_round: bool,
    decisions: DecisionPolicy, *, key: str,
) -> tuple[EffectSet, ...]:
    """Choose which distinct melee weapon resolves all but one attack."""
    if phases.has_tag(fighter.main_weapon, "weapon.vomit-attack"):
        return (fighter.main_weapon,) if count > 0 else ()
    if (count > 2 and fighter.off_hand_attacks and fighter.off_hand is not None
            and fighter.main_weapon != fighter.off_hand
            and not any(phases.has_tag(weapon, tag)
                        for weapon in (fighter.main_weapon, fighter.off_hand)
                        for tag in ("weapon.pistol", "weapon.duelling-pistol"))):
        if not decisions.choose(f"{key}.main-weapon-majority", fighter):
            return (*(fighter.off_hand for _ in range(count - 1)), fighter.main_weapon)
    return tuple(_weapon_for_attack(fighter, index, count, first_round) for index in range(count))


def pool_attack_weapons(
    attacker: CompiledFighter, count: int, *, first_round: bool, charging: bool,
    decisions: DecisionPolicy, key: str, single_bonus: bool = False,
    body_slam: bool = False,
) -> tuple[EffectSet, ...]:
    """The ordinary pool's own allocation, in the order the pool resolves it.

    One allocation governs the printed weapon choice, the Whipcrack bonus and
    the bearer's independent extra attacks.  A caller that nominates one of
    these attacks (Instinctual Violence) and the pool that resolves the rest
    therefore read the same weapons: the nominated strike keeps the profile and
    hand slot the pool allocated for that position, and the remainder keeps the
    allocation it was printed with instead of a shorter pool re-deriving one.
    """
    vomit = any(has_tag(attacker.main_weapon, tag) for tag in
                ("weapon.vomit-attack", "effect.wraith-touch"))
    if single_bonus:
        return (attacker.main_weapon,)
    if body_slam:
        return (EffectSet(tags=("mechanic.body-slam",), strength_bonus=1, hit_modifier=1),)
    whip = whipcrack_weapon(attacker) if not vomit and first_round and charging else None
    weapons = allocate_attack_weapons(
        attacker, count - int(whip is not None), first_round, decisions, key=key)
    if whip is not None:
        weapons += (whip,)
    if not vomit:
        weapons += tuple(weapon for weapon in attacker.extra_attacks
                         if not any(has_tag(weapon, tag) for tag in
                                    ("rule.strikes-last-bite", "rule.eagle-friend"))
                         and (charging or not has_tag(weapon, "rule.horned-one")))
    return weapons


def _prepared_hit(prepared: AttackOutcome):
    from mordheim_combat.phases import HitResult

    return HitResult(prepared.hit_target or 0, prepared.hit_roll if prepared.hit_roll is not None else 0, prepared.hit)


def _resolve_prepared_defences(
    attacker: CompiledFighter,
    defender: CompiledFighter,
    attacker_state: FighterState,
    defender_state: FighterState,
    prepared_attacks: tuple[tuple[EffectSet, AttackOutcome], ...],
    dice: DiceSource,
    *,
    keys: tuple[str, ...],
    first_round: bool,
    charging: bool,
    helpless: bool,
    decisions: DecisionPolicy | None = None,
    deathblow: bool = False,
) -> tuple[FighterState, FighterState, dict[int, AttackOutcome]]:
    """Resolve per-hit defences after every hit roll is known.

    Lucky Charm reacts to the first successful hit in attack order. Parries are
    then offered from the highest remaining hit roll downwards. Unparryable
    attacks do not consume capacity, and a charm save leaves that capacity
    available for the next eligible hit.
    """
    resolved: dict[int, AttackOutcome] = {}
    successful = [
        index for index, (_, prepared) in enumerate(prepared_attacks)
        if prepared.hit
    ]

    if has_tag(defender.global_effects, "mechanic.ethereal-hit-save"):
        for index in successful:
            weapon, prepared = prepared_attacks[index]
            own = OwnedRollDice(dice, defender, defender_state, decisions, modifiable=False)
            incoming = _combined_effect(attacker, weapon)
            if (not has_tag(incoming, "attack.magical")
                    and own.roll(RollRequest(f"{keys[index]}.ethereal")) >= defender.global_effects.ethereal_hit_save):
                resolved[index] = replace(prepared, saved=True, defender=replace(defender_state,
                    resources_spent=defender_state.resources_spent | own.state.resources_spent))
            defender_state = replace(defender_state,
                resources_spent=defender_state.resources_spent | own.state.resources_spent)
    successful = [index for index in successful if index not in resolved]
    if has_tag(defender.global_effects, "mechanic.marks-of-ranald"):
        for index in successful:
            own = OwnedRollDice(dice, defender, defender_state, decisions, modifiable=False)
            if own.roll(RollRequest(f"{keys[index]}.marks-of-ranald")) >= 6:
                resolved[index] = replace(prepared_attacks[index][1], saved=True, defender=replace(defender_state,
                    resources_spent=defender_state.resources_spent | own.state.resources_spent))
            defender_state = replace(defender_state,
                resources_spent=defender_state.resources_spent | own.state.resources_spent)
    successful = [index for index in successful if index not in resolved]
    if defender_state.lucky_charm and successful:
        index = successful[0]
        weapon, prepared = prepared_attacks[index]
        outcome = resolve_reference_attack(
            attacker, defender, attacker_state, defender_state, weapon, dice,
            key=keys[index], first_round=first_round, charging=charging,
            helpless_at_start=helpless or prepared.knocked_down_target, stunned_at_start=False, prepared_hit=_prepared_hit(prepared), disarm_slot=prepared.disarm_slot,
            natural_hit_six=prepared.natural_hit_six,
            defences_only=True, parry_allowed=False, ethereal_resolved=True,
            marks_resolved=True, decisions=decisions, deathblow=deathblow,
        )
        attacker_state, defender_state = outcome.attacker, outcome.defender
        if outcome.saved:
            resolved[index] = replace(
                outcome, hit_roll=prepared.hit_roll,
                hit_target=prepared.hit_target,
            )

    candidates = sorted(
        (index for index in successful if index not in resolved),
        key=lambda index: prepared_attacks[index][1].hit_roll or 0,
        reverse=True,
    )
    for index in candidates:
        if defender_state.parries_remaining <= 0 or (not attacker_state.active and not deathblow):
            break
        weapon, prepared = prepared_attacks[index]
        if (prepared.natural_hit_six and not phases.has_tag(
                defender.global_effects, "rule.blood-dragon-sword-master")
                and not _estalian_parry(defender)):
            # A natural six cannot be parried. With one available
            # attempt it also closes the normal parry window.
            # Exceptional two-parry capacity may still defend a lower hit.
            if defender_state.parries_remaining > 1:
                continue
            defender_state = replace(defender_state, parries_remaining=0)
            break
        outcome = resolve_reference_attack(
            attacker, defender, attacker_state, defender_state, weapon, dice,
            key=keys[index], first_round=first_round, charging=charging,
            helpless_at_start=helpless or prepared.knocked_down_target, stunned_at_start=False, prepared_hit=_prepared_hit(prepared), disarm_slot=prepared.disarm_slot,
            natural_hit_six=prepared.natural_hit_six,
            defences_only=True, ethereal_resolved=True, marks_resolved=True,
            decisions=decisions, deathblow=deathblow,
        )
        attacker_state, defender_state = outcome.attacker, outcome.defender
        if outcome.parried:
            resolved[index] = replace(
                outcome, hit_roll=prepared.hit_roll,
                hit_target=prepared.hit_target,
            )

    return attacker_state, defender_state, resolved

def _declared_unpredictable_attack(
    weapons: tuple[EffectSet, ...], decisions: DecisionPolicy | None, key: str,
    attacker: CompiledFighter,
) -> int | None:
    """The printed Unpredictable declaration: which allocated attack is unparriable.

    *"The Hero may declare one of its attacks Unpredictable; that attack cannot
    be parried by the opponent."*  The declaration is taken when the pool is
    resolved, before any attack is rolled, and it nominates exactly one attack:
    each allocated attack is offered in allocation order and the first accepted
    one is the declaration, so the bearer's choice decides which attack the
    defender cannot parry.  A bearer that declares none leaves every attack
    parryable.  With no decision policy the pool keeps the established default
    the optimized drivers also take and the first allocated attack carries the
    declaration.
    """
    for index in range(len(weapons)):
        if decisions is None or decisions.choose(f"{key}.unpredictable-attack.{index}", attacker):
            return index
    return None


def _resolve_attack_pool(attacker, defender, attacker_state, defender_state, count, dice, **options):
    first, second, outcomes = _resolve_attack_pool_body(
        attacker, defender, attacker_state, defender_state, count, dice, **options)
    marker = f"rememberer-active.{options['key']}"
    return replace(first, resources_spent=first.resources_spent - {marker}), second, outcomes


def _resolve_attack_pool_body(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    count: int, dice: DiceSource, *, key: str, first_round: bool, charging: bool,
    decisions: DecisionPolicy,
    defender_condition_at_start: Condition | None = None,
    minimum_attacks: int = 1,
    single_bonus: bool = False,
    miss_first_attack: bool = False,
    forfeit_index: int | None = None,
    forfeit_indices: tuple[int, ...] = (),
    grapple_declared: bool | None = None,
    allocated_weapons: tuple[EffectSet, ...] | None = None,
    deathblow: bool = False,
) -> tuple[FighterState, FighterState, tuple[AttackOutcome, ...]]:
    outcomes: list[AttackOutcome] = []
    # Printed Deathblow: a Slayer taken out of action in hand-to-hand is
    # entitled to the attacks he has still to make, and the printed clause says
    # he may use it even while Knocked Down or Stunned.  Only that readiness
    # condition is relaxed; being out of action is what triggers the pool, so
    # the caller sets the flag for the remainder and nothing else.
    if (count <= 0 or attacker_state.animosity_failed or attacker_state.charm_attack_blocked or attacker_state.entranced
            or attacker_state.grappled or attacker_state.grappling
            or (attacker_state.condition != Condition.STANDING and not deathblow)
            or not defender_state.active):
        return attacker_state, defender_state, ()
    if (has_tag(attacker.global_effects, "mechanic.honorable")
            and defender_state.condition in (Condition.KNOCKED_DOWN, Condition.STUNNED)):
        return attacker_state, defender_state, ()
    initial_condition = defender_state.condition if defender_condition_at_start is None else defender_condition_at_start
    forfeits = set(forfeit_indices)
    if forfeit_index is not None:
        forfeits.add(forfeit_index)
    explicit_hit = has_tag(attacker.main_weapon, "mechanic.electrical-touch-attack")
    grapple_immune = any(has_tag(defender.global_effects, tag) for tag in (
        "nature.undead", "nature.daemon", "nature.dead", "mechanic.pain-immunity", "size.large"))
    if (not single_bonus and has_tag(attacker.global_effects, "mechanic.gaoler-grapple")
            and not grapple_immune and (grapple_declared if grapple_declared is not None
                else decisions.choose(f"{key}.torturer-grapple", attacker))):
        weapon = EffectSet(tags=("weapon.natural-attacks",))
        attack_key = f"{key}.grapple"
        if miss_first_attack:
            return attacker_state, defender_state, (AttackOutcome(attacker_state, defender_state, trace=(Phase.HIT,)),)
        result = resolve_reference_attack(attacker, defender, attacker_state, defender_state,
            weapon, dice, key=attack_key, first_round=first_round, charging=charging,
            helpless_at_start=initial_condition == Condition.KNOCKED_DOWN,
            stunned_at_start=False, hit_only=True, decisions=decisions)
        if result.hit:
            result = resolve_reference_attack(attacker, defender, result.attacker, result.defender,
                weapon, dice, key=attack_key, first_round=first_round, charging=charging,
                prepared_hit=_prepared_hit(result), disarm_slot=result.disarm_slot, natural_hit_six=result.natural_hit_six,
                defences_only=True, decisions=decisions)
        if result.hit and not result.parried and not result.saved:
            target_state = require_characteristics(defender, result.defender, dice,
                f"{attack_key}.defender", {"S"}, decisions)
            owned = OwnedRollDice(dice, defender, target_state, decisions, close_combat=True)
            escaped = _characteristic_test(target_state.strength - 2, owned,
                f"{attack_key}.strength", six_fails=False,
                reroll=has_tag(defender.global_effects, "skill.blessed-sight"))
            target_state = replace(target_state, resources_spent=(
                target_state.resources_spent | owned.state.resources_spent), grappled=not escaped)
            result = replace(result, attacker=replace(result.attacker, grappling=not escaped),
                defender=target_state)
        return result.attacker, result.defender, (result,)
    if initial_condition == Condition.STUNNED and not explicit_hit:
        extra_count = sum(not any(has_tag(weapon, tag) for tag in
            ("rule.strikes-last-bite", "rule.eagle-friend"))
            and (charging or not has_tag(weapon, "rule.horned-one"))
            for weapon in attacker.extra_attacks) if not single_bonus else 0
        if count + extra_count - sum(0 <= index < count + extra_count for index in forfeits) <= 0:
            return attacker_state, defender_state, ()
        if miss_first_attack:
            outcomes.append(AttackOutcome(attacker_state, defender_state, trace=(Phase.HIT,)))
            available_extra = not single_bonus and any(
                not any(has_tag(weapon, tag) for tag in ("rule.strikes-last-bite", "rule.eagle-friend"))
                and (charging or not phases.has_tag(weapon, "rule.horned-one"))
                for weapon in attacker.extra_attacks)
            if count == 1 and not available_extra:
                return attacker_state, defender_state, tuple(outcomes)
        result = resolve_reference_attack(attacker, defender, attacker_state, defender_state,
            attacker.main_weapon, dice, key=f"{key}.finish", stunned_at_start=True)
        result = _react_to_wound(attacker, defender, result, dice, f"{key}.finish", decisions=decisions)
        return result.attacker, result.defender, (*outcomes, result)
    helpless = initial_condition == Condition.KNOCKED_DOWN and not explicit_hit
    vomit = any(phases.has_tag(attacker.main_weapon, tag) for tag in
        ("weapon.vomit-attack", "effect.wraith-touch"))
    use_bull_charge = (
        not single_bonus and not vomit and first_round and charging
        and phases.has_tag(attacker.global_effects, "mechanic.bull-charge")
        and decisions.choose(f"{key}.bull-charge", attacker)
    )
    if use_bull_charge:
        if miss_first_attack:
            return attacker_state, defender_state, (AttackOutcome(attacker_state, defender_state, trace=(Phase.HIT,)),)
        bull = EffectSet(tags=("mechanic.bull-charge",), hit_modifier=1)
        result = resolve_reference_attack(
            attacker, defender, attacker_state, defender_state, bull, dice,
            key=f"{key}.bull-charge", first_round=True, charging=True,
            helpless_at_start=helpless, stunned_at_start=False, decisions=decisions,
        )
        if (result.hit and not result.parried and not result.saved
                and result.defender.condition == Condition.STANDING):
            result = replace(result, defender=replace(result.defender, condition=Condition.KNOCKED_DOWN,
                frenzy=result.defender.frenzy and has_tag(defender.global_effects, "mechanic.persistent-frenzy")))
        result = _react_to_wound(attacker, defender, result, dice, f"{key}.bull-charge", decisions=decisions)
        return result.attacker, result.defender, (result,)

    use_body_slam = (
        not single_bonus and not vomit and first_round and charging
        and phases.has_tag(attacker.global_effects, "mechanic.body-slam")
        and decisions.choose(f"{key}.body-slam", attacker)
    )
    if single_bonus or use_body_slam:
        weapons = pool_attack_weapons(
            attacker, count, first_round=first_round, charging=charging,
            decisions=decisions, key=key, single_bonus=single_bonus, body_slam=use_body_slam)
    elif allocated_weapons is not None:
        # Instinctual Violence's nominated strike was taken from this very
        # allocation, so the pool resolves the remainder without re-drawing it.
        weapons = allocated_weapons
    else:
        weapons = pool_attack_weapons(
            attacker, count, first_round=first_round, charging=charging,
            decisions=decisions, key=key)
    # Filter the original allocation together, so two forfeits never shift a
    # later nominated hand/natural attack onto a different slot.
    weapons = tuple(weapon for index, weapon in enumerate(weapons) if index not in forfeits)
    if (defender.global_effects.incoming_attacks_modifier < 0
            and phases.has_tag(defender.global_effects, "rule.tentacle-grapple")
            and "tentacle-grapple" not in defender_state.resources_spent):
        remaining = _grapple_lost_attacks(
            weapons, 1, defender, decisions, key, minimum_attacks)
        if len(remaining) < len(weapons):
            # One loss for the entire phase, even with Shifty/Whipcrack pools.
            defender_state = defender_state.spend("tentacle-grapple")
        weapons = remaining
    if attacker_state.attack_penalty:
        # Kusara Kama chooses the affected hand after hitting, before the
        # opponent's reply is resolved. Remove that hand's attack, retaining
        # the published minimum of one attack for the warrior.
        remaining = list(weapons)
        hands = attacker_state.hampered_hands or (attacker.main_hand_slot,) * attacker_state.attack_penalty
        pending_hands = list(hands)
        for hand in hands:
            target = attacker.main_weapon if hand == attacker.main_hand_slot else attacker.off_hand
            if len(remaining) > minimum_attacks and target is not None and target in remaining:
                remaining.remove(target)
                pending_hands.remove(hand)
        attacker_state = replace(attacker_state, attack_penalty=len(pending_hands),
            hampered_hands=tuple(pending_hands))
        weapons = tuple(remaining)
    weapons = tuple(weapon_against_opponent(attacker, defender, weapon) for weapon in weapons)
    if (not single_bonus and "giggle-juice" not in attacker_state.resources_spent
            and has_tag(attacker.global_effects, "mechanic.giggle-juice-spray")):
        selected = next((index for index in range(len(weapons))
            if decisions.choose(f"{key}.giggle-juice-attack.{index}", attacker)), None)
        if selected is not None:
            attacker_state = attacker_state.spend("giggle-juice")
            spray = EffectSet(tags=("mechanic.giggle-juice-spray-attack",),
                automatic_hit=True, fixed_strength=2, injury_modifier=1)
            weapons = (*weapons[:selected], spray, *weapons[selected + 1:])
    if weapons and phases.has_tag(attacker.global_effects, "mechanic.unpredictable-attack"):
        declared = _declared_unpredictable_attack(weapons, decisions, key, attacker)
        if declared is not None:
            weapons = (*weapons[:declared],
                       merge_effects(weapons[declared], EffectSet(cannot_be_parried=True)),
                       *weapons[declared + 1:])

    prepared_attacks: list[tuple[EffectSet, AttackOutcome]] = []
    attack_keys = []
    pending_weapons = list(weapons)
    # Onslaught's new hit rolls join the same collective preparation. Iterating
    # the growing list permits further natural sixes to generate further attacks.
    for index, weapon in enumerate(pending_weapons):
        attack_keys.append(f"{key}.attack.{index}")
        if miss_first_attack and index == 0:
            # Preserve weapon allocation: the first attack misses without a die.
            # Reducing count earlier would incorrectly substitute the other hand.
            prepared = AttackOutcome(attacker_state, defender_state, trace=(Phase.HIT,))
        else:
            prepared = resolve_reference_attack(
                attacker, defender, attacker_state, defender_state, weapon, dice,
                key=attack_keys[index], first_round=first_round,
                charging=charging, helpless_at_start=helpless, stunned_at_start=False, hit_only=True,
                decisions=decisions,
                rememberer_pool_key=key,
                deathblow=deathblow,
            )
        attacker_state, defender_state = prepared.attacker, prepared.defender
        prepared_attacks.append((weapon, prepared))
        if prepared.natural_hit_six and has_tag(attacker.global_effects, "mechanic.ravening-onslaught"):
            pending_weapons.append(weapon)
    weapons = tuple(pending_weapons)
    attack_keys = tuple(attack_keys)
    prepared_tuple = tuple(prepared_attacks)
    attacker_state, defender_state, defended = _resolve_prepared_defences(
        attacker, defender, attacker_state, defender_state, prepared_tuple, dice,
        keys=attack_keys, first_round=first_round, charging=charging,
        helpless=helpless,
        decisions=decisions,
        deathblow=deathblow,
    )

    # Bear Hug replaces two successful, undefended hits before wound
    # resolution. Its opposed roll is independently exhaustive; this branch
    # verifies only the state-transfer sequence in the scalar orchestrator.
    if (attacker.global_effects.bear_hug and len(weapons) >= 2
            and (not has_tag(attacker.global_effects, "rule.bear-hug-unarmed")
                 or all(has_tag(weapon, "weapon.fist") for weapon in weapons[:2]))):
        surviving = [
            prepared.hit and index not in defended
            for index, (_, prepared) in enumerate(prepared_tuple[:2])
        ]
        if sum(surviving) >= 2:
            attacker_state = require_characteristics(attacker, attacker_state, dice,
                f"{key}.attacker", {"S"}, decisions)
            defender_state = require_characteristics(defender, defender_state, dice,
                f"{key}.defender", {"S"}, decisions)
        hug_dice = {
            f"{key}.bear-hug.attacker": OwnedRollDice(dice, attacker, attacker_state, decisions, close_combat=True),
            f"{key}.bear-hug.defender": OwnedRollDice(dice, defender, defender_state, decisions, close_combat=True),
        }
        hug = phases.resolve_bear_hug(BearHugContext(
            sum(surviving),
            attacker_state.strength, defender_state.strength,
            key=f"{key}.bear-hug",
        ), SimpleNamespace(roll=lambda request: hug_dice[request.key].roll(request)), decisions)
        attacker_state = replace(attacker_state, resources_spent=attacker_state.resources_spent
            | hug_dice[f"{key}.bear-hug.attacker"].state.resources_spent)
        defender_state = replace(defender_state, resources_spent=defender_state.resources_spent
            | hug_dice[f"{key}.bear-hug.defender"].state.resources_spent)
        if hug.chosen:
            if hug.wounded:
                automatic = EffectSet(
                    tags=("effect.automatic-wound", "effect.no-critical"),
                    automatic_hit=True, cannot_be_parried=True, ignore_armour=True,
                )
                result = resolve_reference_attack(
                    attacker, defender, attacker_state, defender_state, automatic, dice,
                    key=f"{key}.bear-hug.result", first_round=first_round,
                    charging=charging, helpless_at_start=helpless, stunned_at_start=False,
                    decisions=decisions, single_wound=True,
                )
                result = _react_to_wound(attacker, defender, result, dice, f"{key}.bear-hug.result", decisions=decisions)
                attacker_state, defender_state = result.attacker, result.defender
                outcomes.append(result)
        else:
            for index, (weapon, success) in enumerate(zip(weapons[:2], surviving)):
                if not success or not defender_state.active:
                    continue
                result = resolve_reference_attack(
                    attacker, defender, attacker_state, defender_state, weapon, dice,
                    key=attack_keys[index], first_round=first_round,
                    charging=charging, helpless_at_start=helpless, stunned_at_start=False,
                    prepared_hit=_prepared_hit(prepared_tuple[index][1]), disarm_slot=prepared_tuple[index][1].disarm_slot,
                    natural_hit_six=prepared_tuple[index][1].natural_hit_six,
                    defences_resolved=True, decisions=decisions,
                )
                result = replace(
                    result, hit_roll=prepared_tuple[index][1].hit_roll,
                    hit_target=prepared_tuple[index][1].hit_target,
                )
                result = _react_to_wound(
                    attacker, defender, result, dice,
                    f"{key}.bear-hug.normal.{index}",
                    decisions=decisions,
                )
                attacker_state, defender_state = result.attacker, result.defender
                outcomes.append(result)
        for index, (weapon, prepared) in enumerate(prepared_tuple[2:], start=2):
            if not defender_state.active or not prepared.hit:
                continue
            if index in defended:
                continue
            result = resolve_reference_attack(
                attacker, defender, attacker_state, defender_state, weapon, dice,
                key=attack_keys[index], first_round=first_round,
                charging=charging, helpless_at_start=helpless or prepared.knocked_down_target, stunned_at_start=False,
                prepared_hit=_prepared_hit(prepared), disarm_slot=prepared.disarm_slot,
                natural_hit_six=prepared.natural_hit_six, defences_resolved=True,
                decisions=decisions, deathblow=deathblow,
            )
            result = replace(
                result, hit_roll=prepared.hit_roll, hit_target=prepared.hit_target
            )
            result = _react_to_wound(
                attacker, defender, result, dice, f"{key}.attack.{index}",
                decisions=decisions,
            )
            attacker_state, defender_state = result.attacker, result.defender
            outcomes.append(result)
        return attacker_state, defender_state, tuple(outcomes)

    for index, (weapon, prepared) in enumerate(prepared_attacks):
        if not prepared.hit:
            outcomes.append(prepared)
            continue
        if index in defended:
            outcomes.append(defended[index])
            continue
        if (not attacker_state.active and not deathblow) or not defender_state.active:
            break
        result = resolve_reference_attack(
            attacker, defender, attacker_state, defender_state, weapon, dice,
            key=f"{key}.attack.{index}", first_round=first_round,
            charging=charging, helpless_at_start=helpless or prepared.knocked_down_target, stunned_at_start=False,
            prepared_hit=_prepared_hit(prepared), disarm_slot=prepared.disarm_slot,
            natural_hit_six=prepared.natural_hit_six, defences_resolved=True,
            decisions=decisions, deathblow=deathblow,
        )
        result = replace(
            result, hit_roll=prepared.hit_roll, hit_target=prepared.hit_target
        )
        result = _react_to_wound(attacker, defender, result, dice, f"{key}.attack.{index}", decisions=decisions)
        attacker_state, defender_state = result.attacker, result.defender
        outcomes.append(result)
        # Anvil Head replaces charge attacks only: the D3 wound expansion is
        # inert outside a charge (Khemri, Necromantic Modification / Anvil Head).
        if (not single_bonus and not vomit and result.hit and not result.parried and first_round and charging
                and phases.has_tag(_combined_effect(attacker, weapon), "mechanic.anvil-head")):
            own = OwnedRollDice(dice, attacker, attacker_state, decisions, close_combat=True)
            repeats = own.roll(RollRequest(f"{key}.attack.{index}.anvil-hits", 3)) - 1
            attacker_state = replace(attacker_state,
                resources_spent=attacker_state.resources_spent | own.state.resources_spent)
            repeated = merge_effects(weapon, EffectSet(automatic_hit=True, cannot_be_parried=True))
            for repeat_index in range(repeats):
                extra = resolve_reference_attack(
                    attacker, defender, attacker_state, defender_state, repeated, dice,
                    key=f"{key}.attack.{index}.anvil.{repeat_index}",
                    first_round=first_round, charging=charging,
                    helpless_at_start=helpless, stunned_at_start=False, decisions=decisions,
                    deathblow=deathblow,
                )
                extra = _react_to_wound(
                    attacker, defender, extra, dice,
                    f"{key}.attack.{index}.anvil.{repeat_index}",
                    decisions=decisions,
                )
                attacker_state, defender_state = extra.attacker, extra.defender
                outcomes.append(extra)
                if not defender_state.active:
                    break
    return attacker_state, defender_state, tuple(outcomes)
