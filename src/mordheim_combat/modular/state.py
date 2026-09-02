"""combat.modular.state: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations
from mordheim_combat import phases

from dataclasses import dataclass
from dataclasses import replace
from mordheim_combat.phases import Condition
from mordheim_combat.phases import Phase
from mordheim_combat.phases import has_tag
from mordheim_core.dice import DiceSource
from mordheim_core.dice import RollRequest
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet


@dataclass(frozen=True, slots=True)
class FighterState:
    wounds: int
    condition: Condition = Condition.STANDING
    frenzy: bool = False
    lucky_charm: bool = False
    resources_spent: frozenset[str] = frozenset()
    on_fire: bool = False
    entangled: bool = False
    attack_penalty: int = 0
    initiative_penalty: int = 0
    initiative_floor: int = 1
    parries_remaining: int = 0
    critical_available: bool = True
    force_of_will_active: bool = False
    force_of_will_penalty: int = 0
    weapon_skill: int = 0
    strength: int = 0
    toughness: int = 0
    initiative: int = 0
    attacks: int = 0

    @property
    def active(self) -> bool:
        return self.condition != Condition.OUT

    def spend(self, resource: str) -> "FighterState":
        return replace(self, resources_spent=self.resources_spent | {resource})


@dataclass(frozen=True, slots=True)
class DuelState:
    first: FighterState
    second: FighterState
    round_index: int = 0
    first_charged: bool = True
    trace: tuple[Phase, ...] = ()


@dataclass(frozen=True, slots=True)
class AttackOutcome:
    attacker: FighterState
    defender: FighterState
    hit: bool = False
    hit_roll: int | None = None
    hit_target: int | None = None
    parried: bool = False
    wounded: bool = False
    saved: bool = False
    damage: int = 0
    critical: bool = False
    trace: tuple[Phase, ...] = ()


@dataclass(frozen=True, slots=True)
class CombatRoundResult:
    state: DuelState
    attacks: tuple[AttackOutcome, ...]


def _parry_capacity(fighter: CompiledFighter) -> int:
    effects = fighter.global_effects
    available = sum((
        fighter.main_weapon.parry,
        bool(fighter.off_hand and fighter.off_hand.parry),
        effects.parry,
        phases.has_tag(effects, "skill.miniath"),
        phases.has_tag(effects, "skill.axe-master") and any(
            phases.has_tag(weapon, tag)
            for weapon in (fighter.main_weapon, fighter.off_hand or EffectSet())
            for tag in ("weapon.axe", "weapon.dwarf-axe")
        ),
        phases.has_tag(effects, "skill.shield-mastery")
        and phases.has_tag(effects, "defence.shield"),
    ))
    return min(2 if phases.has_tag(effects, "skill.unbeatable-warrior") else 1, int(available))


def initialize_fighter(fighter: CompiledFighter, dice: DiceSource, key: str) -> FighterState:
    values = {
        "WS": fighter.characteristics.weapon_skill,
        "S": fighter.characteristics.strength,
        "T": fighter.characteristics.toughness + fighter.global_effects.toughness_bonus,
        "I": fighter.characteristics.initiative,
        "A": fighter.characteristics.attacks,
    }
    for characteristic, count, sides, bonus in fighter.random_characteristics:
        values[characteristic] = sum(
            dice.roll(RollRequest(f"{key}.characteristic.{characteristic}.{index}", sides))
            for index in range(count)
        ) + bonus
    if phases.has_tag(fighter.global_effects, "preparation.crimson-shade"):
        values["I"] += dice.roll(RollRequest(f"{key}.crimson-shade", 3))
    disability = 0
    if phases.has_tag(fighter.global_effects, "mechanic.disability"):
        disability = dice.roll(RollRequest(f"{key}.disability"))
        affected = {1: "I", 2: "WS", 4: "T", 5: "S"}.get(disability)
        if affected:
            values[affected] = max(1, values[affected] - 1)
    wounds = fighter.characteristics.wounds + int(phases.has_tag(fighter.global_effects, "skill.monstrous"))
    return FighterState(
        wounds=wounds,
        frenzy=fighter.global_effects.frenzy,
        lucky_charm=phases.has_tag(fighter.global_effects, "defence.lucky-charm"),
        parries_remaining=_parry_capacity(fighter),
        weapon_skill=values["WS"], strength=values["S"], toughness=values["T"],
        initiative=values["I"], attacks=values["A"],
        resources_spent=frozenset({f"disability.{disability}"}) if disability else frozenset(),
    )


def initialize_duel(
    first: CompiledFighter, second: CompiledFighter, dice: DiceSource,
) -> DuelState:
    if any("weapon.lance" in fighter.main_weapon.tags for fighter in (first, second)):
        raise ValueError(
            "weapon.lance is outside the one-against-one runtime: mounted combat is not supported"
        )
    first_charged = dice.roll(RollRequest("duel.charge")) >= 4
    return DuelState(
        initialize_fighter(first, dice, "first"),
        initialize_fighter(second, dice, "second"),
        first_charged=first_charged,
        trace=(Phase.DUEL_START,),
    )
