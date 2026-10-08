"""domain: Core domain types: fighters, builds, duel requests and results."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from mordheim_core.dice import AlwaysAccept
from mordheim_core.dice import DecisionPolicy
import numpy as np
import math
from threading import Event
from typing import Mapping


@dataclass(frozen=True, slots=True)
class Characteristics:
    weapon_skill: int; strength: int; toughness: int; wounds: int; initiative: int; attacks: int
    movement: int | None = field(default=None, kw_only=True)
    leadership: int | None = field(default=None, kw_only=True)
    def __post_init__(self):
        for name in self.__slots__:
            value = getattr(self, name)
            if name in {"movement", "leadership"} and value is None:
                continue
            if name in {"movement", "leadership"} and isinstance(value, bool):
                raise ValueError(f"{name} must be a non-negative integer or unknown")
            if not isinstance(value, int) or value < 0: raise ValueError(f"{name} must be a non-negative integer")
        if self.wounds < 1 or self.attacks < 1: raise ValueError("wounds and attacks must be at least one")


@dataclass(frozen=True, slots=True)
class FighterBuild:
    ruleset: str
    characteristics: Characteristics | None = None
    band_id: str | None = None; profile_id: str | None = None
    main_weapon_id: str = "weapon.dagger"; off_hand_id: str | None = None
    armour_id: str = "armour.no-armour"; defence_ids: tuple[str, ...] = ()
    main_material_id: str = "material.normal"; off_material_id: str = "material.normal"
    skill_ids: tuple[str, ...] = (); preparation_ids: tuple[str, ...] = ()
    special_rule_ids: tuple[str, ...] = ()
    energy_focus_attacks: int = 0
    mounted: bool = False

    # promotion.hero is a supplied local Hero result, never an advancement roll.
    variant_ids: tuple[str, ...] = ()
    extra_hand_id: str | None = None
    main_poison_id: str | None = None; off_poison_id: str | None = None
    trait_overrides: Mapping[str, object] = field(default_factory=dict)
    #: Canonical condition ids the warrior currently has (an acquired Fear, a
    #: serious-injury result, a Cold-Blooded origin …). ``catalog/rules/
    #: conditions.yaml`` resolves each id to its operator at compile time; an
    #: id without an executable binding is refused instead of guessed.
    condition_ids: tuple[str, ...] = ()
    collection: str = "mordheim"
    # None leaves the complete carried kit unspecified; () supplies an empty kit.
    owned_item_ids: tuple[str, ...] | None = field(default=None, kw_only=True)
    def __post_init__(self):
        if self.characteristics is None and not (self.band_id and self.profile_id): raise ValueError("provide characteristics or a band/profile pair")
        if bool(self.band_id) != bool(self.profile_id): raise ValueError("band_id and profile_id must be provided together")
        if not self.collection or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in self.collection):
            raise ValueError("collection must be a stable lowercase ID")
        if not isinstance(self.energy_focus_attacks, int) or self.energy_focus_attacks < 0:
            raise ValueError("energy_focus_attacks must be a non-negative integer")
        if self.owned_item_ids is not None:
            if not isinstance(self.owned_item_ids, (tuple, list)) or any(
                    not isinstance(item, str) or not item.strip() for item in self.owned_item_ids):
                raise ValueError("owned_item_ids must be an item-id sequence or unknown")
            object.__setattr__(self, "owned_item_ids", tuple(self.owned_item_ids))
        if not isinstance(self.condition_ids, (tuple, list)) or any(
                not isinstance(condition, str) or not condition.strip() for condition in self.condition_ids):
            raise ValueError("condition_ids must be a sequence of canonical condition ids")
        object.__setattr__(self, "condition_ids", tuple(self.condition_ids))


@dataclass(frozen=True, slots=True)
class EffectSet:
    tags: tuple[str, ...] = ()
    strength_bonus: int = 0; first_round_strength_bonus: int = 0
    charge_strength_bonus: int = 0; toughness_bonus: int = 0; initiative_bonus: int = 0
    fixed_strength: int = 0
    armour_penetration: int = 0; target_armour_bonus: int = 0
    hit_modifier: int = 0; wound_modifier: int = 0; injury_modifier: int = 0
    attacks_bonus: int = 0; charge_attacks_bonus: int = 0; first_round_charge_attacks_bonus: int = 0; charge_ws_bonus: int = 0
    first_round_attacks_bonus: int = 0; incoming_strength_modifier: int = 0
    armour_strength_modifier: int = 0; weapon_skill_bonus: int = 0
    critical_injury_bonus: int = 0
    energy_focus_attacks: int = 0
    incoming_attacks_modifier: int = 0
    incoming_hit_modifier: int = 0
    armour_save_bonus: int = 0; ward_save: int = 7; priority: int = 0
    parry: bool = False; concussion: bool = False; two_handed: bool = False; paired: bool = False
    reroll_hits: bool = False; reroll_wounds: bool = False; strongman: bool = False
    charge_reroll_hits: bool = False
    step_aside: bool = False; thick_skull: bool = False
    ignore_armour: bool = False; automatic_hit: bool = False; cannot_be_parried: bool = False
    bear_hug: bool = False
    poison_immunity: bool = False; frenzy: bool = False
    damage: int = 1; regeneration_save: int = 7; out_of_action_threshold: int = 5
    damage_die_sides: int = 0
    maximum_wound_target: int = 7
    armour_save_floor: int = 7
    armour_cannot_be_ignored: bool = False
    ward_save_mundane_only: bool = False
    natural_armour_negated_by_magic: bool = False
    regeneration_blocked_by_fire: bool = False
    regeneration_blocked_by_blessed: bool = False
    ignition_threshold: int = 7
    caught_fire_threshold: int = 7
    # Printed coup-de-grace clause: the attack bypasses all armour saves when the
    # defender is Knocked Down.  Distinct from the static ``ignore_armour`` flag,
    # which has no condition scope.
    ignore_armour_against_knocked_down: bool = False
    # Printed Ladle clause ("The only saving throws allowed are from shields
    # or skills"): the armour the defender wears is denied while the saving
    # throws a shield or a skill supplies are not.  Distinct from
    # ``ignore_armour`` (every armour save denied) and from
    # ``ignore_armour_against_knocked_down`` (condition-scoped).
    ignore_armour_except_shield_and_skills: bool = False


@dataclass(frozen=True, slots=True)
class CompiledFighter:
    fighter_id: str; characteristics: Characteristics
    main_weapon: EffectSet; off_hand: EffectSet | None; global_effects: EffectSet
    armour_save: int; helmet_save: int; natural_armour_save: int
    off_hand_attacks: bool = False
    natural_armour_unmodified: bool = False
    # 0 normal; 1 Weedy; 2 OUT on any wound; 3 Fragile undead; 4 OUT on last wound.
    injury_profile: int = 0
    random_characteristics: tuple[tuple[str,int,int,int], ...] = ()
    natural_armour_worst_save: int = 7
    # The passive effects of the shield and skill selections alone, carried so
    # a printed clause can select a save by its source.  ``armour_save`` and
    # ``global_effects`` mix every contribution whatever its provenance (worn
    # armour, a pelt cloak, a mechanic-granted bonus, a supplied trait), so
    # neither can answer "what would this defender save on with only a shield
    # or a skill".
    shield_and_skill_effects: EffectSet = EffectSet()
    extra_attacks: tuple[EffectSet, ...] = ()
    missile_weapon_limit: int = 2
    ballistic_skill: int = 0
    construction_tags: tuple[str, ...] = ()
    # Contextual poison removal must not subtract guessed numeric bonuses:
    # preserve the independently compiled weapon/material/profile contribution.
    main_weapon_without_poison: EffectSet | None = None
    off_hand_without_poison: EffectSet | None = None
    mounted: bool = False
    unarmed_weapon: EffectSet | None = None
    main_hand_slot: str = 'main'
    off_hand_slot: str = 'off'
    # Optional profile attack, separate from equipped hands and their poisons.
    # The modular round policy chooses it instead of the normal attack pool.
    vomit_attack: EffectSet | None = None
    # Supplied individual conditions; these values never simulate nearby groups.
    stupidity_leadership: int | None = None
    stupidity_leadership_bonus: int = 0
    animal_handler_leadership: int | None = None


@dataclass(frozen=True, slots=True)
class LocalParticipant:
    """A configured simulation participant, never a campaign roster row."""
    participant_id: str
    side_id: str
    fighter: CompiledFighter
    condition: str = "standing"

    def __post_init__(self):
        if any(not isinstance(value, str) or not value.strip() for value in (self.participant_id, self.side_id)):
            raise ValueError("local participant and side identifiers cannot be empty")
        if not isinstance(self.fighter, CompiledFighter):
            raise ValueError("local participant needs a compiled simulation fighter")
        if self.condition not in {"standing", "knocked-down", "stunned", "paralyzed", "out", "fleeing"}:
            raise ValueError(f"unknown local participant condition: {self.condition}")


@dataclass(frozen=True, slots=True)
class DuelContext:
    """Supplied local facts. Missing measurements remain unknown, not zero.

    Distances are edge-to-edge inches; contacts describe the supplied combat
    snapshot. Terrain labels are facts, not a placement or movement engine.
    ``charging=None`` preserves legacy random charge selection; ``()`` means
    neither fighter charges. Explicit charging also requires its player-turn
    owner. Player-turn ownership is independent of charge.
    Initial charging facts are in-range attempts; a failed Fear test can cancel
    contact. A later engagement needs a newly supplied local setup.
    """
    first_id: str = "first"
    second_id: str = "second"
    nearby: tuple[LocalParticipant, ...] = ()
    distances: tuple[tuple[str, str, float], ...] = ()
    contacts: tuple[tuple[str, str], ...] | None = None
    terrain: tuple[tuple[str, str], ...] = ()
    charging: tuple[str, ...] | None = None
    active_participant: str | None = None

    def __post_init__(self):
        for name in ("nearby", "distances", "terrain", "contacts", "charging"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, tuple(tuple(row) if isinstance(row, list) else row for row in value))
        if any(not isinstance(p, LocalParticipant) for p in self.nearby):
            raise ValueError("nearby facts need local participants")
        ids = (self.first_id, self.second_id, *(p.participant_id for p in self.nearby))
        if any(not isinstance(value, str) or not value.strip() for value in ids) or len(set(ids)) != len(ids):
            raise ValueError("simulation participant identifiers must be nonempty and unique")
        pairs = set()
        distances = {}
        for first, second, inches in self.distances:
            if first not in ids or second not in ids or first == second:
                raise ValueError("distance must refer to two different local participants")
            if isinstance(inches, bool) or not isinstance(inches, (int, float)) or not math.isfinite(inches) or inches < 0:
                raise ValueError("distance must be finite non-negative inches")
            pair = tuple(sorted((first, second)))
            if pair in pairs:
                raise ValueError("duplicate or contradictory distance")
            pairs.add(pair)
            distances[pair] = inches
        pairs = set()
        for first, second in self.contacts or ():
            pair = tuple(sorted((first, second)))
            if first not in ids or second not in ids or first == second or pair in pairs:
                raise ValueError("contact must identify a unique pair of local participants")
            if pair in distances and distances[pair] != 0:
                raise ValueError("contact contradicts nonzero edge-to-edge distance")
            pairs.add(pair)
        if any(pid not in ids or not isinstance(label, str) or not label.strip() for pid, label in self.terrain):
            raise ValueError("terrain needs a local participant and a nonempty source label")
        if self.charging is not None and (len(set(self.charging)) != len(self.charging)
                or any(pid not in ids[:2] for pid in self.charging)):
            raise ValueError("charging facts must identify the duel participants once")
        if self.charging is not None and self.active_participant is None:
            raise ValueError("explicit charging requires the player-turn owner")
        if self.active_participant is not None and self.active_participant not in ids[:2]:
            raise ValueError("player-turn owner must be a duel participant")


@dataclass(frozen=True, slots=True)
class DuelRequest:
    first: CompiledFighter; second: CompiledFighter; simulations: int
    seed: int = 0; batch_size: int = 100_000; maximum_rounds: int = 50
    cancel_event: Event | None = field(default=None, compare=False, repr=False)
    decision_policy: DecisionPolicy = field(default_factory=AlwaysAccept, compare=False, repr=False)
    context: DuelContext | None = None
    def __post_init__(self):
        if min(self.simulations, self.batch_size, self.maximum_rounds) < 1: raise ValueError("simulation limits must be positive")
        if self.context is not None and not isinstance(self.context, DuelContext):
            raise ValueError("context must contain local duel facts")


@dataclass(frozen=True, slots=True)
class DuelResult:
    first_wins: int; second_wins: int; unresolved: int; simulations: int
    def __post_init__(self):
        if self.first_wins + self.second_wins + self.unresolved != self.simulations: raise ValueError("result counts must add up")
    @property
    def first_win_rate(self): return 100.0 * self.first_wins / self.simulations
    @property
    def second_win_rate(self): return 100.0 * self.second_wins / self.simulations
    @property
    def unresolved_rate(self): return 100.0 * self.unresolved / self.simulations


@dataclass(frozen=True, slots=True)
class ObservedDuelResult:
    """Per-duel terminal records for one whole-oracle sample.

    Exposed only to verification and diagnostics; the production counting
    path (``DuelResult``) is unchanged.  Arrays are row-aligned with duel
    index ``seed + i``.  ``winner`` follows the ``DuelResult`` convention
    (0 first wins, 1 second wins, 2 unresolved).  ``resolution_rounds``
    counts the rounds actually executed before the duel ended (1..
    ``maximum_rounds``); a duel that runs out of its round budget is
    unresolved (``winner == 2``) and reports ``maximum_rounds``, mirroring
    the vectorized driver's per-row round ledger.  ``first_condition`` /
    ``second_condition`` use the shared ``Condition`` codes.
    """
    winner: np.ndarray
    resolution_rounds: np.ndarray
    first_wounds: np.ndarray
    second_wounds: np.ndarray
    first_condition: np.ndarray
    second_condition: np.ndarray
    simulations: int
    maximum_rounds: int

    def __post_init__(self) -> None:
        if self.simulations < 1 or self.maximum_rounds < 1:
            raise ValueError("simulation limits must be positive")
        length = len(self.winner)
        if length != self.simulations:
            raise ValueError("winner records must match the simulation count")
        for name in ("resolution_rounds", "first_wounds", "second_wounds",
                     "first_condition", "second_condition"):
            if len(getattr(self, name)) != length:
                raise ValueError(f"{name} records must match the simulation count")

    @property
    def first_wins(self) -> int:
        return int(np.count_nonzero(self.winner == 0))

    @property
    def second_wins(self) -> int:
        return int(np.count_nonzero(self.winner == 1))

    @property
    def unresolved(self) -> int:
        return int(np.count_nonzero(self.winner == 2))

    def as_result(self) -> DuelResult:
        return DuelResult(self.first_wins, self.second_wins, self.unresolved,
                          self.simulations)


class SimulationCancelled(RuntimeError): pass
