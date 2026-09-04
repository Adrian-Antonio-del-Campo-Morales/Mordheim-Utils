"""Regressions of the compiled native backend (mordheim_combat._combat_native).

The backend is skipped with ``pytest.skip`` when the extension is not compiled
(environments without a C compiler): ``available_backends()`` then only reports
NumPy and the public behaviour is unchanged.
"""
from __future__ import annotations

import pytest

from mordheim_combat.vectorized import available_backends
from mordheim_combat.vectorized import simulate_duel
from mordheim_combat_lab.verification.parity import compare_statistical_parity
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import DuelRequest
from mordheim_core.models import FighterBuild


def _request(simulations: int, *, seed: int = 7, batch_size: int = 500) -> DuelRequest:
    fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
    ))
    return DuelRequest(fighter, fighter, simulations, seed=seed, batch_size=batch_size)


def _require_native() -> None:
    if "native" not in available_backends():
        pytest.skip("native combat backend is not compiled in this environment")


def test_native_is_selected_by_auto_when_available() -> None:
    _require_native()
    assert available_backends()[0] == "native"
    request = _request(200)
    assert simulate_duel(request, backend="auto") == simulate_duel(
        request, backend="native",
    )


def test_native_accumulates_counts_across_batches() -> None:
    """Batch accumulation must neither lose nor duplicate duels."""
    _require_native()
    request = _request(2_500, batch_size=700)
    result = simulate_duel(request, backend="native")
    assert result.first_wins + result.second_wins + result.unresolved \
        == result.simulations


def test_native_symmetric_duel_is_statistically_fair() -> None:
    """Two identical profiles must each win ~50% (single large batch)."""
    _require_native()
    request = _request(20_000, batch_size=20_000, seed=2026)
    result = simulate_duel(request, backend="native")
    p = result.first_wins / result.simulations
    assert abs(p - 0.5) < 6 * (0.5 * 0.5 / result.simulations) ** 0.5 + 0.0025


def test_native_runs_are_deterministic_per_seed() -> None:
    """Replay-style reproducibility: same seed ⇒ identical result;
    different seed ⇒ different dice stream (the per-batch PCG32 is derived
    from the request seed)."""
    _require_native()
    first = simulate_duel(_request(8_000, seed=2024), backend="native")
    second = simulate_duel(_request(8_000, seed=2024), backend="native")
    assert first == second
    other = simulate_duel(_request(8_000, seed=2025), backend="native")
    assert (other.first_wins, other.second_wins, other.unresolved) != (
        first.first_wins, first.second_wins, first.unresolved,
    )


def test_native_statistical_parity_against_modular_oracle() -> None:
    """The statistical gate (modular oracle) certifies the native backend."""
    _require_native()
    fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
    ))
    result = compare_statistical_parity(
        "native-smoke", fighter, fighter, 2_000, seed=3, backend="native",
    )
    assert result.passed


def test_native_two_weapons_vs_parry_is_certified_against_the_oracle() -> None:
    """Regression for the natural-6 parry waste in the deep matrix.

    The two-weapons-vs-parry archetype diverged by ~3.5-3.9 pp before the
    native port learned to spend its single parry on the best *parryable*
    hit instead of wasting it on an unparryable natural 6.  At 30k duels the
    six-sigma gate fails on that gap and passes on the fixed port.
    """
    _require_native()
    two_weapons = compile_fighter(FighterBuild(
        "mordheim", Characteristics(4, 4, 4, 2, 4, 2),
        main_weapon_id="weapon.axe", off_hand_id="weapon.dagger",
    ))
    sword_and_buckler = compile_fighter(FighterBuild(
        "mordheim", Characteristics(4, 4, 4, 2, 4, 2),
        main_weapon_id="weapon.sword", off_hand_id="defence.buckler",
    ))
    result = compare_statistical_parity(
        "two-weapons-vs-parry", two_weapons, sword_and_buckler,
        30_000, seed=2026, backend="native",
    )
    assert result.passed


def test_native_frenzy_vs_heavy_is_certified_against_the_oracle() -> None:
    """Regression for the native-only frenzy re-doubling in the deep matrix.

    The frenzy-vs-heavy archetype diverged by ~0.9 pp (10+ sigma at 50k)
    before the native attack-count port dropped its ``elif f.frenzy_effect``
    fallback, which re-doubled a frenzied fighter after a knockdown had
    cleared the per-row frenzy state.  The modular oracle clears frenzy on a
    non-standing injury and never restores it; the NumPy driver gates the
    doubling on that live state flag, and the native port must do the same.
    """
    _require_native()
    from mordheim_combat_lab.cli.benchmarking import DEEP_SCENARIOS

    scenario = next(s for s in DEEP_SCENARIOS if s.id == "frenzy-vs-heavy")
    first = compile_fighter(scenario.first)
    second = compile_fighter(scenario.second)
    result = compare_statistical_parity(
        "frenzy-vs-heavy", first, second, 30_000, seed=2026,
        backend="native", maximum_rounds=scenario.maximum_rounds,
    )
    assert result.passed


def test_native_elite_vs_durable_is_certified_against_the_oracle() -> None:
    """Regression for the stunned-defender follow-up kill in the deep matrix.

    The modular oracle removes a defender that is STUNNED at the start of an
    attack instantly, while the optimized drivers prepared every attack of a
    pool upfront and let a defender stunned by attack 1 survive attack 2 with
    a fresh injury roll.  The NumPy driver and the native port both learned
    the per-attack check; the elite-vs-durable pair (2-attack elite, long
    duels) failed the six-sigma gate at 50k before the fix and passes now.
    """
    _require_native()
    import os
    from concurrent.futures import ProcessPoolExecutor

    from mordheim_combat_lab.cli.benchmarking import DEEP_SCENARIOS
    from mordheim_combat.modular.parallel import run_oracle_sample

    scenario = next(s for s in DEEP_SCENARIOS if s.id == "elite-vs-durable")
    first = compile_fighter(scenario.first)
    second = compile_fighter(scenario.second)
    workers = min(os.cpu_count() or 1, 8)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        modular = run_oracle_sample(
            first, second, 50_000, seed=2026,
            maximum_rounds=scenario.maximum_rounds,
            workers=workers, executor=pool,
        )
    result = compare_statistical_parity(
        "elite-vs-durable", first, second, 50_000, seed=2026,
        backend="native", maximum_rounds=scenario.maximum_rounds,
        modular=modular,
    )
    assert result.passed
