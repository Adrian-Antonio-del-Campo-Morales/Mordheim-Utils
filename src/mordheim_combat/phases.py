"""combat.phases: responsibility extracted without altering the rules."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from enum import Enum
from enum import IntEnum
from mordheim_core.dice import DecisionPolicy
from mordheim_core.dice import DiceSource
from mordheim_core.dice import RollRequest
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet


class Condition(IntEnum):
    STANDING = 0
    KNOCKED_DOWN = 1
    STUNNED = 2
    PARALYZED = 3
    OUT = 4


class Phase(str, Enum):
    DUEL_START = "duel_start"
    PRIORITY = "priority"
    ATTACKS = "attacks"
    HIT = "hit"
    PARRY = "parry"
    WOUND = "wound"
    ARMOUR = "armour"
    SPECIAL_SAVE = "special_save"
    INJURY = "injury"
    AFTERMATH = "aftermath"


PHASE_ORDER = tuple(Phase)


def has_tag(effect: EffectSet, tag: str) -> bool:
    return tag in effect.tags


def ignores_unarmed_penalties(effect: EffectSet) -> bool:
    return any(has_tag(effect, tag) for tag in (
        "skill.unarmed-fighting", "skill.art-of-silent-death",
        "guardian_unarmed", "rule.unarmed-without-penalties",
    ))


def to_hit_target(attacker_ws: int, defender_ws: int) -> int:
    if min(attacker_ws, defender_ws) < 0:
        raise ValueError("Weapon Skill cannot be negative")
    return 0 if defender_ws == 0 else 3 if attacker_ws > defender_ws else 5 if defender_ws > 2 * attacker_ws else 4


def wound_target(strength: int, toughness: int, maximum: int = 7) -> int:
    if min(strength, toughness) < 0:
        raise ValueError("Strength and Toughness cannot be negative")
    difference = strength - toughness
    target = 2 if difference >= 2 else 3 if difference == 1 else 4 if difference == 0 else 5 if difference == -1 else 6 if difference >= -3 else 7
    return min(target, maximum)


@dataclass(frozen=True, slots=True)
class RoundState:
    """Minimal immutable ledger transferred between combat phases."""

    round_index: int
    attacks: int = 0
    hits: int = 0
    wounds: int = 0
    resources_spent: frozenset[str] = frozenset()
    trace: tuple[Phase, ...] = ()

    def after(self, phase: Phase, **changes: object) -> "RoundState":
        values = {
            "round_index": self.round_index,
            "attacks": self.attacks,
            "hits": self.hits,
            "wounds": self.wounds,
            "resources_spent": self.resources_spent,
            "trace": (*self.trace, phase),
        }
        values.update(changes)
        return RoundState(**values)


@dataclass(frozen=True, slots=True)
class PriorityContext:
    fighter: CompiledFighter
    opponent: CompiledFighter
    first_round: bool = False
    charging: bool = False
    charged: bool = False
    stood_up: bool = False
    initiative_penalty: int = 0
    initiative_bonus: int = 0
    initiative_floor: int = 1


@dataclass(frozen=True, slots=True)
class PriorityResult:
    priority: int
    initiative: int


def first_acts_before(first: PriorityResult, second: PriorityResult,
                      dice: DiceSource, *, key: str = "priority-tie") -> bool:
    """Resolve tier, Initiative, then an unbiased tie using the shared contract."""
    if first == second:
        return dice.roll(RollRequest(key)) >= 4
    return (first.priority, first.initiative) > (second.priority, second.initiative)


def resolve_priority(context: PriorityContext) -> PriorityResult:
    fighter, opponent = context.fighter, context.opponent
    weapon_priority = fighter.main_weapon.priority
    if fighter.global_effects.strongman and weapon_priority < 0 and (
        fighter.main_weapon.two_handed or has_tag(fighter.main_weapon, "weapon.broadsword")
    ):
        weapon_priority = 0
    if has_tag(fighter.main_weapon, "weapon.long-boat-hook") and not context.first_round:
        weapon_priority = 0
    # The spear's Strike First only applies in the first turn of hand-to-hand
    # combat (mordheimer.net, close-combat weapons / Strike First), mirroring
    # the long-boat-hook's first-round scope.
    if has_tag(fighter.main_weapon, "weapon.spear") and not context.first_round:
        weapon_priority = 0
    value = weapon_priority + fighter.global_effects.priority
    if has_tag(fighter.main_weapon, "weapon.trident") and context.charged:
        value = max(value, 1)
    if has_tag(fighter.global_effects, "mechanic.strike-first-vs-skinks-always") and has_tag(opponent.global_effects, "species.skink"):
        value = 20
    if context.first_round:
        # A charge does not override an explicit Strike Last weapon.
        if weapon_priority >= 0:
            value = max(value, int(context.charging))
        if has_tag(fighter.global_effects, "mechanic.strike-first-vs-skinks-first-round") and has_tag(opponent.global_effects, "species.skink"):
            value = 20
        if has_tag(fighter.global_effects, "skill.lightning-reflexes") and context.charged:
            value = max(value, 1)
        # Spears and chargers share Strike First; the FAQ resolves ties by I.
    # Lost Innocence explicitly retains strike-first when standing up.
    if context.stood_up and not has_tag(fighter.global_effects, "skill.always-strikes-first"):
        value = -1
    initiative = max(
        context.initiative_floor,
        fighter.characteristics.initiative
        + fighter.global_effects.initiative_bonus
        + fighter.main_weapon.initiative_bonus
        + (fighter.off_hand.initiative_bonus if fighter.off_hand is not None else 0)
        + context.initiative_bonus
        - context.initiative_penalty,
    )
    return PriorityResult(value, initiative)


@dataclass(frozen=True, slots=True)
class AttackPoolContext:
    fighter: CompiledFighter
    first_round: bool = False
    charging: bool = False
    charged: bool = False
    frenzy: bool | None = None
    wounded: bool = False
    attack_penalty: int = 0
    base_attacks: int | None = None


@dataclass(frozen=True, slots=True)
class AttackPoolResult:
    attacks: int


def build_attacks(context: AttackPoolContext) -> AttackPoolResult:
    """Pure scalar attack-pool operator; it never calls the NumPy engine."""

    fighter = context.fighter
    effect = fighter.global_effects
    base_characteristic = (
        fighter.characteristics.attacks
        if context.base_attacks is None else context.base_attacks
    )
    extra_weapon_attack = int(fighter.off_hand_attacks or fighter.main_weapon.paired)
    attacks = (
        base_characteristic
        + effect.attacks_bonus
        + fighter.main_weapon.attacks_bonus
        + (fighter.off_hand.attacks_bonus if fighter.off_hand is not None else 0)
    )
    if context.wounded and has_tag(effect, "maddened_with_pain"):
        attacks += 1
    if context.charging:
        attacks += effect.charge_attacks_bonus
    if context.first_round and context.charging:
        attacks += effect.first_round_charge_attacks_bonus
    if has_tag(fighter.main_weapon, "weapon.fist") and not ignores_unarmed_penalties(effect):
        attacks = 1
        extra_weapon_attack = 0
    if has_tag(effect, "skill.unarmed-fighting") and has_tag(fighter.main_weapon, "weapon.fist"):
        attacks += 1
    if has_tag(effect, "skill.art-of-silent-death") and any(
        has_tag(fighter.main_weapon, tag)
        for tag in ("weapon.fist", "weapon.fighting-claws")
    ):
        attacks += 1
    if has_tag(effect, "skill.inspiring-sermon"):
        attacks += 1
    if context.first_round:
        attacks += fighter.main_weapon.first_round_attacks_bonus
    frenzy = effect.frenzy if context.frenzy is None else context.frenzy
    if frenzy:
        attacks *= 2
    if context.first_round and context.charging and has_tag(effect, "skill.ferocious-charge"):
        attacks *= 2
    # Core combat: the one attack from a second weapon is added after other
    # modifiers; frenzy must not duplicate that extra attack.
    attacks += extra_weapon_attack
    if has_tag(fighter.main_weapon, "weapon.fist") and not ignores_unarmed_penalties(effect):
        attacks = min(attacks, 1)
    if has_tag(fighter.main_weapon, "weapon.vomit-attack"):
        attacks = 1
    if has_tag(effect, "skill.sweep") and fighter.main_weapon.two_handed:
        attacks = 1
    main_pistol = any(has_tag(fighter.main_weapon, tag) for tag in ("weapon.pistol", "weapon.duelling-pistol"))
    off_pistol = bool(fighter.off_hand and any(
        has_tag(fighter.off_hand, tag) for tag in ("weapon.pistol", "weapon.duelling-pistol")
    ))
    if main_pistol:
        if context.first_round:
            if off_pistol:
                attacks = 2
            elif not fighter.off_hand_attacks:
                attacks = 1
        elif fighter.off_hand_attacks:
            attacks = max(0, attacks - 1)
        else:
            attacks = 0
    elif off_pistol and not context.first_round:
        attacks = max(0, attacks - 1)
    if context.first_round and context.charging and any(
        has_tag(effect, tag) for tag in ("mechanic.body-slam", "mechanic.bull-charge", "mechanic.anvil-head")
    ):
        attacks = 1
    if has_tag(effect, "mechanic.death-blow") and fighter.characteristics.attacks >= 2:
        attacks = 1
    if has_tag(effect, "mechanic.energy-focus") and any(
        has_tag(fighter.main_weapon, tag) for tag in ("weapon.fist", "weapon.natural-attacks")
    ):
        attacks = max(0, attacks - effect.energy_focus_attacks)
    if has_tag(fighter.main_weapon, "effect.serpent-staff-power"):
        attacks = 1
    return AttackPoolResult(max(0, attacks - context.attack_penalty))


@dataclass(frozen=True, slots=True)
class HitContext:
    attacker_ws: int
    defender_ws: int
    modifier: int = 0
    automatic: bool = False
    reroll: bool = False
    key: str = "hit"


@dataclass(frozen=True, slots=True)
class HitResult:
    target: int
    roll: int
    success: bool
    rerolled: bool = False


def resolve_hit(context: HitContext, dice: DiceSource) -> HitResult:
    if context.defender_ws == 0:
        # An automatic hit has no natural die face for poison/other triggers.
        return HitResult(0, 0, True)
    target = max(2, min(6, to_hit_target(context.attacker_ws, context.defender_ws) - context.modifier))
    if context.automatic:
        return HitResult(target, 0, True)
    roll = dice.roll(RollRequest(context.key))
    success = roll >= target
    rerolled = False
    if not success and context.reroll:
        roll = dice.roll(RollRequest(f"{context.key}.reroll"))
        success = roll >= target
        rerolled = True
    return HitResult(target, roll, success, rerolled)


@dataclass(frozen=True, slots=True)
class ParryContext:
    hit_roll: int
    attacker_strength: int
    defender_strength: int
    available: bool = True
    cannot_be_parried: bool = False
    match_allowed: bool = False
    fixed_target: int | None = None
    reroll: bool = False
    key: str = "parry"
    can_parry_six: bool = False


@dataclass(frozen=True, slots=True)
class ParryResult:
    attempted: bool
    blocked: bool
    roll: int | None = None
    rerolled: bool = False


def resolve_parry(context: ParryContext, dice: DiceSource) -> ParryResult:
    eligible = (
        context.available
        and not context.cannot_be_parried
        and (context.hit_roll != 6 or context.can_parry_six)
        and context.attacker_strength < 2 * context.defender_strength
    )
    if not eligible:
        return ParryResult(False, False)

    def succeeds(value: int) -> bool:
        if context.fixed_target is not None:
            return value >= context.fixed_target
        return value >= context.hit_roll if context.match_allowed else value > context.hit_roll

    roll = dice.roll(RollRequest(context.key))
    blocked = succeeds(roll)
    rerolled = False
    if not blocked and context.reroll:
        roll = dice.roll(RollRequest(f"{context.key}.reroll"))
        blocked = succeeds(roll)
        rerolled = True
    return ParryResult(True, blocked, roll, rerolled)


@dataclass(frozen=True, slots=True)
class WoundContext:
    strength: int
    toughness: int
    modifier: int = 0
    maximum_target: int = 7
    automatic: bool = False
    reroll: bool = False
    critical_threshold: int = 6
    critical_available: bool = True
    key: str = "wound"
    critical_on_reroll: bool = True
    failure_still_wounds: bool = False


@dataclass(frozen=True, slots=True)
class WoundResult:
    target: int
    roll: int
    success: bool
    critical: bool
    rerolled: bool = False


def resolve_wound(context: WoundContext, dice: DiceSource) -> WoundResult:
    target = max(2, wound_target(context.strength, context.toughness, context.maximum_target) - context.modifier)
    if context.automatic:
        return WoundResult(target, 0, True, False)
    roll = dice.roll(RollRequest(context.key))
    success = roll >= target
    rerolled = False
    if not success and context.reroll:
        roll = dice.roll(RollRequest(f"{context.key}.reroll"))
        success = roll >= target
        rerolled = True
    rolled_success = success
    success = success or context.failure_still_wounds
    critical = (rolled_success and context.critical_available and target < 6
                and roll >= context.critical_threshold
                and (not rerolled or context.critical_on_reroll))
    return WoundResult(target, roll, success, critical, rerolled)


@dataclass(frozen=True, slots=True)
class ArmourContext:
    armour_save: int
    natural_armour_save: int = 7
    natural_armour_worst_save: int = 7
    natural_armour_unmodified: bool = False
    strength: int = 3
    armour_penetration: int = 0
    target_armour_bonus: int = 0
    ignore_armour: bool = False
    armour_save_floor: int = 7
    armour_cannot_be_ignored: bool = False
    magical_attack: bool = False
    natural_armour_negated_by_magic: bool = False
    key: str = "armour"


@dataclass(frozen=True, slots=True)
class CriticalResult:
    damage: int = 1
    ignore_armour: bool = False
    injury_modifier: int = 0


def resolve_critical(dice: DiceSource, *, key: str, modifier: int = 0) -> CriticalResult:
    """Basic Mordheim table; optional weapon-family charts are a separate ruleset."""
    result = dice.roll(RollRequest(key)) + modifier
    return CriticalResult(damage=2, ignore_armour=result >= 3,
                          injury_modifier=2 if result >= 5 else 0)


@dataclass(frozen=True, slots=True)
class ArmourResult:
    target: int
    eligible: bool
    roll: int | None
    saved: bool


def armour_target(context: ArmourContext) -> int:
    modifier = max(0, context.strength - 3) + context.armour_penetration - context.target_armour_bonus
    armour = context.armour_save + modifier
    natural = context.natural_armour_save
    if not context.natural_armour_unmodified:
        natural += modifier
    natural = min(natural, context.natural_armour_worst_save)
    if context.natural_armour_negated_by_magic and context.magical_attack:
        natural = 7
    target = min(armour, natural)
    if context.ignore_armour:
        target = context.armour_save_floor if context.armour_cannot_be_ignored and not context.magical_attack else 7
    if context.armour_save_floor <= 6 and not (context.ignore_armour and context.magical_attack):
        target = min(target, context.armour_save_floor)
    return target


def resolve_armour(context: ArmourContext, dice: DiceSource) -> ArmourResult:
    target = armour_target(context)
    if target > 6:
        return ArmourResult(target, False, None, False)
    roll = dice.roll(RollRequest(context.key))
    return ArmourResult(target, True, roll, roll >= max(2, target))


@dataclass(frozen=True, slots=True)
class SpecialSaveContext:
    ward_save: int = 7
    regeneration_save: int = 7
    ward_blocked: bool = False
    regeneration_blocked: bool = False
    key: str = "special_save"


@dataclass(frozen=True, slots=True)
class SpecialSaveResult:
    saved: bool
    source: str | None = None
    ward_roll: int | None = None
    regeneration_roll: int | None = None


def resolve_special_save(context: SpecialSaveContext, dice: DiceSource) -> SpecialSaveResult:
    if context.ward_save <= 6 and not context.ward_blocked:
        roll = dice.roll(RollRequest(f"{context.key}.ward"))
        if roll >= context.ward_save:
            return SpecialSaveResult(True, "ward", ward_roll=roll)
    else:
        roll = None
    if context.regeneration_save <= 6 and not context.regeneration_blocked:
        regeneration_roll = dice.roll(RollRequest(f"{context.key}.regeneration"))
        if regeneration_roll >= context.regeneration_save:
            return SpecialSaveResult(True, "regeneration", roll, regeneration_roll)
        return SpecialSaveResult(False, None, roll, regeneration_roll)
    return SpecialSaveResult(False, None, roll, None)


@dataclass(frozen=True, slots=True)
class InjuryContext:
    modifier: int = 0
    critical_bonus: int = 0
    out_threshold: int = 5
    injury_profile: int = 0
    hard_to_kill: bool = False
    true_grit: bool = False
    concussion: bool = False
    concussion_immune: bool = False
    fragile: bool = False
    poisonous: bool = False
    survivor: bool = False
    initial_condition: Condition = Condition.STANDING
    head_crusher: bool = False
    ignore_pain: bool = False
    jump_up: bool = False
    mandrake: bool = False
    key: str = "injury"


@dataclass(frozen=True, slots=True)
class InjuryResult:
    total: int
    condition: Condition


def injury_condition(total: int, context: InjuryContext) -> Condition:
    result = Condition.OUT if total >= context.out_threshold else Condition.STUNNED if total >= 3 else Condition.KNOCKED_DOWN
    if context.hard_to_kill:
        result = Condition.OUT if total >= 6 else Condition.STUNNED if total >= 3 else Condition.KNOCKED_DOWN
    if context.true_grit:
        result = Condition.OUT if total >= 6 else Condition.STUNNED if total >= 4 else Condition.KNOCKED_DOWN
    if context.concussion and not context.concussion_immune and 2 <= total <= 4:
        result = Condition.STUNNED
    if context.injury_profile == 1:
        result = Condition.OUT if total >= 4 else Condition.STUNNED if total >= 2 else Condition.KNOCKED_DOWN
    elif context.injury_profile == 3:
        result = Condition.OUT if total >= 4 else Condition.KNOCKED_DOWN
    if context.fragile and total == 2:
        result = Condition.STUNNED
    if context.poisonous:
        result = Condition.OUT if total >= 5 else Condition.STUNNED if total >= 2 else Condition.KNOCKED_DOWN
    if context.survivor and context.initial_condition == Condition.STANDING and result == Condition.OUT:
        result = Condition.STUNNED
    if context.head_crusher and result == Condition.KNOCKED_DOWN:
        result = Condition.STUNNED
    knocked_down_by_no_pain = context.ignore_pain and result == Condition.STUNNED
    if knocked_down_by_no_pain:
        result = Condition.KNOCKED_DOWN
    if context.jump_up and result == Condition.KNOCKED_DOWN and not knocked_down_by_no_pain:
        result = Condition.STANDING
    if context.mandrake and result == Condition.STUNNED:
        result = Condition.KNOCKED_DOWN
    return result


def resolve_injury(context: InjuryContext, dice: DiceSource) -> InjuryResult:
    total = dice.roll(RollRequest(context.key)) + context.modifier + context.critical_bonus
    return InjuryResult(total, injury_condition(total, context))


@dataclass(frozen=True, slots=True)
class StunReactionContext:
    condition: Condition
    thick_skull: bool = False
    helmet_save: int = 7
    key: str = "stun_reaction"


@dataclass(frozen=True, slots=True)
class StunReactionResult:
    condition: Condition
    attempted: bool
    converted: bool
    threshold: int | None = None
    roll: int | None = None


def resolve_stun_reaction(context: StunReactionContext, dice: DiceSource) -> StunReactionResult:
    """Apply Thick Skull or Helmet after the injury table, never both.

    Thick Skull replaces the ordinary Helmet reaction and improves its 3+
    threshold to 2+ while a helmet is worn. Non-Stunned outcomes consume no
    die.
    """
    if context.condition != Condition.STUNNED:
        return StunReactionResult(context.condition, False, False)
    if context.thick_skull:
        threshold = 2 if context.helmet_save <= 4 else 3
        key = f"{context.key}.thick-skull"
    elif context.helmet_save <= 6:
        threshold = context.helmet_save
        key = f"{context.key}.helmet"
    else:
        return StunReactionResult(context.condition, False, False)
    roll = dice.roll(RollRequest(key))
    converted = roll >= threshold
    condition = Condition.KNOCKED_DOWN if converted else Condition.STUNNED
    return StunReactionResult(condition, True, converted, threshold, roll)


@dataclass(frozen=True, slots=True)
class BearHugContext:
    successful_hits: int
    attacker_strength: int
    defender_strength: int
    key: str = "bear_hug"


@dataclass(frozen=True, slots=True)
class BearHugResult:
    available: bool
    chosen: bool
    wounded: bool
    armour_allowed: bool = True
    attacker_roll: int | None = None
    defender_roll: int | None = None


def bear_hug_wins(
    attacker_roll: int, attacker_strength: int, defender_roll: int, defender_strength: int
) -> bool:
    return attacker_roll + attacker_strength >= defender_roll + defender_strength


def resolve_bear_hug(
    context: BearHugContext, dice: DiceSource, decisions: DecisionPolicy
) -> BearHugResult:
    if context.successful_hits < 2:
        return BearHugResult(False, False, False)
    if not decisions.choose(context.key, context):
        return BearHugResult(True, False, False)
    attacker_roll = dice.roll(RollRequest(f"{context.key}.attacker"))
    defender_roll = dice.roll(RollRequest(f"{context.key}.defender"))
    wounded = bear_hug_wins(
        attacker_roll,context.attacker_strength,defender_roll,context.defender_strength
    )
    return BearHugResult(True, True, wounded, False, attacker_roll, defender_roll)


@dataclass(frozen=True, slots=True)
class StrikeContext:
    hit: HitContext
    wound: WoundContext
    armour: ArmourContext
    parry: ParryContext | None = None
    special_save: SpecialSaveContext = SpecialSaveContext()
    injury: InjuryContext = InjuryContext()


@dataclass(frozen=True, slots=True)
class StrikeResult:
    hit: HitResult
    parry: ParryResult | None
    wound: WoundResult | None
    armour: ArmourResult | None
    special_save: SpecialSaveResult | None
    injury: InjuryResult | None
    trace: tuple[Phase, ...]


def resolve_attack(context: StrikeContext, dice: DiceSource) -> StrikeResult:
    """Resolve the ordinary single-attack pipeline in its contractual order."""

    hit = resolve_hit(context.hit, dice)
    trace = [Phase.HIT]
    if not hit.success:
        return StrikeResult(hit, None, None, None, None, None, tuple(trace))
    parry = None
    if context.parry is not None:
        parry = resolve_parry(replace(context.parry,hit_roll=hit.roll),dice)
        trace.append(Phase.PARRY)
        if parry.blocked:
            return StrikeResult(hit,parry,None,None,None,None,tuple(trace))
    wound = resolve_wound(context.wound, dice)
    trace.append(Phase.WOUND)
    if not wound.success:
        return StrikeResult(hit,parry,wound,None,None,None,tuple(trace))
    armour = resolve_armour(context.armour, dice)
    trace.append(Phase.ARMOUR)
    if armour.saved:
        return StrikeResult(hit,parry,wound,armour,None,None,tuple(trace))
    special = resolve_special_save(context.special_save, dice)
    trace.append(Phase.SPECIAL_SAVE)
    if special.saved:
        return StrikeResult(hit,parry,wound,armour,special,None,tuple(trace))
    injury = resolve_injury(context.injury, dice)
    trace.append(Phase.INJURY)
    return StrikeResult(hit,parry,wound,armour,special,injury,tuple(trace))


@dataclass(frozen=True, slots=True)
class RoundContext:
    round_index: int
    strikes: tuple[StrikeContext, ...]


@dataclass(frozen=True, slots=True)
class RoundResult:
    state: RoundState
    strikes: tuple[StrikeResult, ...]


def resolve_strike_sequence(context: RoundContext, dice: DiceSource) -> RoundResult:
    """Reduced sequence to verify the composition of ordinary strikes.

    Catalogue-specific attack generation and priority are independently tested;
    the round contract proves that ordinary strikes traverse the resolution
    phases in order and transfer only successful outcomes onward.
    """

    results = tuple(resolve_attack(strike,dice) for strike in context.strikes)
    ordered_trace: list[Phase] = []
    if context.round_index == 0:
        ordered_trace.append(Phase.DUEL_START)
    ordered_trace.extend((Phase.PRIORITY,Phase.ATTACKS))
    for phase in (Phase.HIT,Phase.PARRY,Phase.WOUND,Phase.ARMOUR,Phase.SPECIAL_SAVE,Phase.INJURY):
        if any(phase in result.trace for result in results):
            ordered_trace.append(phase)
    ordered_trace.append(Phase.AFTERMATH)
    wounds = sum(
        int(result.wound is not None and result.wound.success
            and (result.armour is None or not result.armour.saved)
            and (result.special_save is None or not result.special_save.saved))
        for result in results
    )
    state = RoundState(
        context.round_index,
        attacks=len(results),
        hits=sum(result.hit.success for result in results),
        wounds=wounds,
        trace=tuple(ordered_trace),
    )
    return RoundResult(state,results)


def _characteristic_test(
    value: int, dice: DiceSource, key: str, *, six_fails: bool = True,
    reroll: bool = False,
) -> bool:
    roll = dice.roll(RollRequest(key))
    passed = roll <= value and not (six_fails and roll == 6)
    if not passed and reroll:
        roll = dice.roll(RollRequest(f"{key}.reroll"))
        passed = roll <= value and not (six_fails and roll == 6)
    return passed
