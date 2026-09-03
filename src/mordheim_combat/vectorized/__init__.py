"""mordheim_combat.vectorized: NumPy batch combat engine.

The engine is organized as layered submodules (types, stateless
operators, attack resolution, batch driver).  This facade re-exports the
complete historical module namespace so existing importers - tests, the
verification consumers and the native compile helpers - keep working
unchanged.
"""
from __future__ import annotations

# Historical namespace compatibility (mirrors the former single-module
# imports; submodules import the same names from their canonical homes).
import numpy as np
from dataclasses import dataclass
from dataclasses import replace
from functools import lru_cache

from mordheim_combat.phases import InjuryContext
from mordheim_combat.phases import bear_hug_wins
from mordheim_combat.phases import ignores_unarmed_penalties
from mordheim_combat.phases import to_hit_target
from mordheim_combat.phases import wound_target
from mordheim_core.dice import AlwaysAccept
from mordheim_core.dice import DecisionPolicy
from mordheim_core.effects import merge_effects
from mordheim_core.models import CompiledFighter
from mordheim_core.models import DuelRequest
from mordheim_core.models import DuelResult
from mordheim_core.models import EffectSet
from mordheim_core.models import SimulationCancelled

from mordheim_combat.vectorized._types import (
    KNOCKED_DOWN,
    OUT,
    PARALYZED,
    STANDING,
    STUNNED,
    CombatState,
    OptionalPhasePlan,
    PreparedAttack,
    VectorAttackObservation,
    VectorBatchObservation,
    _claim_criticals,
    _critical_wound_threshold,
    _has_weapon_tag,
    _parry_capacity,
    _run_starts,
    has,
)
from mordheim_combat.vectorized._operators import (
    _characteristic_test,
    allocate_attack_weapons,
    armour_targets,
    attack_count,
    characteristic_test_outcomes,
    effective_initiative,
    hit_targets,
    injury_conditions,
    opposed_attack_count,
    parry_outcomes,
    priority,
    recover_round_state,
    round_weapon_attack_count,
    special_save_targets,
    stun_reaction_outcomes,
    to_hit,
    wound_outcomes,
    wound_targets,
)
from mordheim_combat.vectorized._attacks import (
    _apply_hit_defences,
    _can_ignite,
    _compiled_attack_effect,
    _optional_phase_plan,
    _parry_hits,
    _prepare_weapon_attack,
    _resolve_weapon,
    resolve_attacks,
)
from mordheim_combat.vectorized._driver import (
    _black_hunger_backlash,
    _new_state,
    _rescue_force_of_will,
    _resolve_fire,
    _resolve_netter_charge,
    _resolve_spines,
    _resource_observation,
    _simulate_batch_core,
    _simulate_duel_numpy,
    _sustain_force_of_will,
    available_backends,
    simulate_batch,
    simulate_batch_observed,
    simulate_duel,
)
