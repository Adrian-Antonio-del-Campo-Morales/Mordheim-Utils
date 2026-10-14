"""combat: Fighter and duel state with immutable transitions."""
from __future__ import annotations
from mordheim_combat import phases

from dataclasses import dataclass
from dataclasses import replace
from mordheim_combat.phases import Condition
from mordheim_combat.phases import Phase
from mordheim_combat.phases import has_tag
from mordheim_core.dice import DiceSource
from mordheim_core.dice import DecisionPolicy
from mordheim_core.dice import RollRequest
from mordheim_core.context import PreparedDuelContext, prepare_duel_context
from mordheim_core.models import CompiledFighter
from mordheim_core.models import DuelContext
from mordheim_core.models import EffectSet, MutationOption, CarriedEquipment


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
    torture_strength_loss: int = 0
    toughness: int = 0
    initiative: int = 0
    attacks: int = 0
    broken_hands: frozenset[str] = frozenset()
    hampered_hands: tuple[str, ...] = ()
    fear_hit_sixes: bool = False
    stupidity_failed: bool = False
    charm_attack_blocked: bool = False
    charm_auto_hit: bool = False
    entranced: bool = False
    guiding_dream_result: int = 0
    drunken_result: int = 0
    animosity_failed: bool = False
    last_shadow_dance: str | None = None
    dodge_trick_active: bool = False
    banter_trick_active: bool = False
    trip_trick_active: bool = False
    mouth_sewn: bool = False
    hillman_wolf: bool = False
    devoted_frenzy: bool = False
    transformed: bool = False
    equipment_cast_off: bool = False
    bitten_result: int = 0
    lunatic_result: int = 0
    lunatic_stupidity: bool = False
    feral_instinct_failed: bool = False
    danse_macabre_controlled: bool = False
    random_rolled: frozenset[str] = frozenset()
    random_modifiers: tuple[tuple[str, int], ...] = ()
    random_round: int = -1
    starting_wounds: int = 0
    djinn_power: str | None = None
    last_djinn_power: str | None = None
    electrical_available_at: int = 0
    grappled: bool = False
    grappling: bool = False
    netted: bool = False
    mutations: tuple[MutationOption, ...] = ()
    mutation_weapon_limbs: tuple[EffectSet, ...] = ()
    atrophied_arms: int = 0
    atrophied_legs: int = 0
    mutated_hands: tuple[str, ...] = ()
    mutation_equipment: tuple[CarriedEquipment, ...] | None = None

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
    context: PreparedDuelContext | None = None
    second_charged: bool | None = None
    initial_first_player_turn: bool | None = None
    engaged: bool = True
    failed_charges: frozenset[str] = frozenset()

    @property
    def initial_charge_flags(self) -> tuple[bool, bool]:
        return self.first_charged, (
            not self.first_charged if self.second_charged is None else self.second_charged
        )

    @property
    def first_player_turn(self) -> bool:
        """Each iteration is one combat phase in an alternating player turn."""
        initial = (self.first_charged if self.initial_first_player_turn is None
                   else self.initial_first_player_turn)
        return initial == (self.round_index % 2 == 0)


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
    barrage_available: bool = False
    damage_already_reacted: int = 0
    reactions_resolved: bool = False
    natural_hit_six: bool = False
    melee_attack: bool = True
    knocked_down_target: bool = False


@dataclass(frozen=True, slots=True)
class CombatRoundResult:
    state: DuelState
    attacks: tuple[AttackOutcome, ...]


def _parry_capacity(fighter: CompiledFighter) -> int:
    effects = fighter.global_effects
    available = sum((
        fighter.main_weapon.parry,
        bool(fighter.off_hand and fighter.off_hand.parry),
        int(phases.has_tag(fighter.main_weapon, "weapon.double-bladed-sword")),
        effects.parry,
        phases.has_tag(effects, "skill.miniath"),
        phases.has_tag(effects, "skill.chosen-of-the-white-tower"),
        phases.has_tag(effects, "skill.instinctive-warrior") and any(
            phases.has_tag(weapon, "weapon.double-handed-weapon")
            for weapon in (fighter.main_weapon, fighter.off_hand or EffectSet())),
        phases.has_tag(effects, "skill.axe-master") and any(
            phases.has_tag(weapon, tag)
            for weapon in (fighter.main_weapon, fighter.off_hand or EffectSet())
            for tag in ("weapon.axe", "weapon.dwarf-axe")
        ),
        phases.has_tag(effects, "skill.shield-mastery")
        and phases.has_tag(effects, "defence.shield"),
    ))
    two_parries = (
        phases.has_tag(effects, "skill.unbeatable-warrior")
        or phases.has_tag(fighter.main_weapon, "weapon.double-bladed-sword")
    )
    return min(2 if two_parries else 1, int(available))



def _refresh_random_characteristics(
    fighter: CompiledFighter, state: FighterState, dice: DiceSource, key: str,
    decisions: DecisionPolicy | None = None,
) -> FighterState:
    """Roll variable profile characteristics once for the current turn."""
    random_stats = {characteristic for characteristic, *_ in fighter.random_characteristics}
    if phases.has_tag(fighter.global_effects, 'mechanic.inconsistency'):
        return state
    # Condemned/Inconsistency refreshes WS, S, T and A once per turn.
    # Spawn's random A is a separate D6+1 attack-count rule handled by rounds.
    if not {"WS", "S", "T", "A"}.issubset(random_stats):
        return state
    from mordheim_combat.modular.contexts import OwnedRollDice
    dice = OwnedRollDice(dice, fighter, state, decisions)
    values: dict[str, int] = {}
    for characteristic, count, sides, bonus in fighter.random_characteristics:
        values[characteristic] = sum(
            dice.roll(RollRequest(f"{key}.characteristic.{characteristic}.{index}", sides))
            for index in range(count)
        ) + bonus
    return replace(
        state,
        weapon_skill=values.get("WS", state.weapon_skill),
        strength=(max(1, values["S"] - state.torture_strength_loss)
                  if "S" in values else state.strength),
        toughness=values.get("T", state.toughness - fighter.global_effects.toughness_bonus)
            + fighter.global_effects.toughness_bonus,
        initiative=values.get("I", state.initiative),
        attacks=values.get("A", state.attacks),
        resources_spent=state.resources_spent | dice.state.resources_spent,
    )

def require_characteristics(fighter, state, dice, key, needed, decisions=None):
    """Roll only an Inconsistency value the current operation actually needs."""
    if not phases.has_tag(fighter.global_effects, 'mechanic.inconsistency'):
        return state
    from mordheim_combat.modular.contexts import OwnedRollDice
    owned = OwnedRollDice(dice, fighter, state, decisions)
    attributes = {'WS': 'weapon_skill', 'S': 'strength', 'T': 'toughness',
                  'I': 'initiative', 'A': 'attacks'}
    changes = {}
    rolled = set(state.random_rolled)
    for stat, count, sides, bonus in fighter.random_characteristics:
        if stat not in needed or stat in rolled:
            continue
        raw = sum(owned.roll(RollRequest(f'{key}.characteristic.{stat}.{index}', sides))
                  for index in range(count)) + bonus
        attr = attributes[stat]
        delta = dict(state.random_modifiers).get(stat, 0)
        if stat == 'S':
            delta -= state.torture_strength_loss
        changes[attr] = max(1, raw+delta)
        rolled.add(stat)
    return replace(state, **changes, random_rolled=frozenset(rolled),
        resources_spent=state.resources_spent | owned.state.resources_spent)


def maximum_wounds(fighter: CompiledFighter) -> int:
    """The Wound total the compiled fighter may hold at once."""
    return (fighter.characteristics.wounds
            + int(phases.has_tag(fighter.global_effects, "skill.monstrous"))
            + int(phases.has_tag(fighter.global_effects, "condition.petru-fortitude")))


def initialize_fighter(fighter: CompiledFighter, dice: DiceSource, key: str,
                       decisions: DecisionPolicy | None = None) -> FighterState:
    from mordheim_combat.modular.contexts import OwnedRollDice
    dice = OwnedRollDice(dice, fighter, FighterState(fighter.characteristics.wounds), decisions)
    values = {
        "WS": fighter.characteristics.weapon_skill,
        "S": fighter.characteristics.strength,
        "T": fighter.characteristics.toughness + fighter.global_effects.toughness_bonus,
        "I": fighter.characteristics.initiative,
        "A": fighter.characteristics.attacks,
    }
    inconsistency = phases.has_tag(fighter.global_effects, 'mechanic.inconsistency')
    for characteristic, count, sides, bonus in (() if inconsistency else fighter.random_characteristics):
        values[characteristic] = sum(
            dice.roll(RollRequest(f"{key}.characteristic.{characteristic}.{index}", sides))
            for index in range(count)
        ) + bonus
    if phases.has_tag(fighter.global_effects, "preparation.crimson-shade"):
        values["I"] += dice.roll(RollRequest(f"{key}.crimson-shade", 3))
    for tag, stat, bonus in (("condition.petru-debilitating", "T", -1),
        ("condition.petru-strength", "S", 1), ("condition.petru-resilience", "T", 1),
        ("condition.alchemist-resilience", "T", 1), ("condition.alchemist-strength", "S", 1),
        ("condition.alchemist-aberrantius-vigortia", "S", 1),
        ("condition.alchemist-aberrantius-vigortia", "T", 1),
        ("condition.alchemist-backleys-brew", "S", -1), ("condition.alchemist-backleys-brew", "I", -1)):
        if phases.has_tag(fighter.global_effects, tag):
            values[stat] = values[stat] + bonus if inconsistency else max(1, values[stat]+bonus)
    poetry = phases.has_tag(fighter.global_effects,'condition.poetry-inspired')
    if poetry:
        values['WS'] += 1
    disability = 0
    if phases.has_tag(fighter.global_effects, "mechanic.disability"):
        disability = dice.roll(RollRequest(f"{key}.disability"))
        affected = {1: "I", 2: "WS", 4: "T", 5: "S"}.get(disability)
        if affected:
            values[affected] = max(1, values[affected] - 1)
    guiding_dream = (dice.roll(RollRequest(f"{key}.guiding-dream"))
                     if phases.has_tag(fighter.global_effects, "mechanic.guiding-dream") else 0)
    nominated = phases.has_tag(fighter.global_effects, "condition.guiding-dream-target")
    if nominated and guiding_dream in (4, 5):
        values["S"] += 1
    wounds = maximum_wounds(fighter)
    return FighterState(
        wounds=wounds,
        netted=phases.has_tag(fighter.global_effects, "condition.netted"),
        condition=Condition.KNOCKED_DOWN if phases.has_tag(fighter.global_effects, "condition.netted") else Condition.STANDING,
        starting_wounds=wounds,
        guiding_dream_result=guiding_dream,
        danse_macabre_controlled=phases.has_tag(fighter.global_effects, "condition.danse-macabre-controlled"),
        frenzy=(phases.has_tag(fighter.global_effects, 'mechanic.persistent-frenzy') or
                (fighter.global_effects.frenzy or (nominated and guiding_dream == 6))
                and not phases.has_tag(fighter.global_effects,'condition.netted')
                and (not phases.has_tag(fighter.global_effects, "mechanic.psychology-immunity")
                     or phases.has_tag(fighter.global_effects, "condition.snorri-frenzy"))),
        stupidity_failed=(phases.has_tag(fighter.global_effects, "condition.stupidity-failed")
                          and not phases.has_tag(fighter.global_effects, "condition.stupidity-exempt")
                          and not fighter.global_effects.frenzy
                          and not phases.has_tag(fighter.global_effects, "mechanic.psychology-immunity")),
        lucky_charm=phases.has_tag(fighter.global_effects, "defence.lucky-charm"),
        parries_remaining=_parry_capacity(fighter),
        weapon_skill=values["WS"], strength=values["S"], toughness=values["T"],
        initiative=values["I"], attacks=values["A"],
        random_modifiers=tuple((stat, values[stat]-getattr(fighter.characteristics,
            {'WS':'weapon_skill','S':'strength','T':'toughness','I':'initiative','A':'attacks'}[stat]))
            for stat, *_ in fighter.random_characteristics) if inconsistency else (),
        resources_spent=dice.state.resources_spent | (frozenset({f"disability.{disability}"}) if disability else frozenset())
            | (frozenset({"poetry-inspiration-active"}) if poetry else frozenset()),
    )


def initialize_duel(
    first: CompiledFighter, second: CompiledFighter, dice: DiceSource,
    *, context: DuelContext | None = None, decisions: DecisionPolicy | None = None,
) -> DuelState:
    if any("weapon.lance" in fighter.main_weapon.tags for fighter in (first, second)):
        raise ValueError(
            "weapon.lance is outside the one-against-one runtime: mounted combat is not supported"
        )
    for fighter, opponent in ((first, second), (second, first)):
        if (phases.has_tag(fighter.global_effects, "condition.guiding-dream-target")
                and not phases.has_tag(opponent.global_effects, "fighter-kind.hero")):
            raise ValueError("Guiding Dream requires the nominated opposing model to be a Hero")
    prepared = prepare_duel_context(first, second, context)
    allowed = tuple(
        not phases.has_tag(fighter.global_effects, "mechanic.cannot-charge")
        and not phases.has_tag(fighter.global_effects, 'condition.alchemist-addicted')
        and (not phases.has_tag(fighter.global_effects, "mechanic.shallya-strictures")
        or any(phases.has_tag(opponent.global_effects, tag)
               for tag in ("band.carnival-of-chaos", "identity.onogal-follower")))
        for fighter, opponent in ((first, second), (second, first)))
    # A charge is an in-range attempt against a model that is not in base contact,
    # so a supplied contact between the duelists is the snapshot's established
    # engagement: neither duelist can be attributed an in-range attempt.
    in_base_contact = (prepared is not None and prepared.facts.contacts is not None
        and any({a, b} == {prepared.facts.first_id, prepared.facts.second_id}
                for a, b in prepared.facts.contacts))
    explicit_charges = prepared is not None and prepared.facts.charging is not None
    if explicit_charges:
        legacy_first_charged = True
        first_charged, second_charged = prepared.charge_flags(True)
        if any(charging and not permitted for charging, permitted in zip((first_charged, second_charged), allowed)):
            raise ValueError("Charging configuration violates Cannot Charge or Shallyan Strictures")
        if in_base_contact and (first_charged or second_charged):
            raise ValueError(
                "A supplied charge contradicts the supplied base contact between the duelists")
    else:
        # Sample only legal initial chargers; when neither may charge, resolve
        # established contact and sample the active player, not a forbidden charge.
        legacy_first_charged = allowed[0] if allowed[0] != allowed[1] else dice.roll(RollRequest("duel.charge")) >= 4
        first_charged = legacy_first_charged and allowed[0]
        second_charged = not legacy_first_charged and allowed[1]
        if in_base_contact:
            # Established contact is resolved and the legacy roll keeps owning the
            # player turn; the attempt it must not sample is the charge against a
            # model the snapshot places in base contact.
            first_charged = second_charged = False
        elif allowed == (True, True) and prepared is None:
            second_charged = None
    for charging, fighter, opponent in ((first_charged, first, second),
                                         (second_charged, second, first)):
        if any(phases.has_tag(fighter.global_effects, tag) for tag in ('condition.impetuous-charge', 'condition.nuttaz-charge')) and not charging:
            raise ValueError('A supplied compulsory charge requires its initial in-range charging attempt')
        if phases.has_tag(fighter.global_effects, 'condition.witch-finder-charge'):
            if (not phases.has_tag(fighter.global_effects, 'mechanic.solkan-witch-finder')
                    or not charging or not any(phases.has_tag(opponent.global_effects, tag) for tag in
                    ('identity.chaos-follower', 'warband-group.chaotic', 'identity.warlock',
                     'identity.necromancer', 'identity.sorcerer', 'identity.warp-tainted'))):
                raise ValueError('Supplied Witch-finder charge requires its named enemy and charging attempt')
    return DuelState(
        initialize_fighter(first, dice, "first", decisions),
        initialize_fighter(second, dice, "second", decisions),
        first_charged=first_charged,
        trace=(Phase.DUEL_START,),
        context=prepared,
        engaged=(prepared is None or prepared.facts.contacts is None or in_base_contact),
        second_charged=second_charged,
        initial_first_player_turn=(
            prepared.first_player_turn(legacy_first_charged) if prepared is not None else None
        ),
    )
