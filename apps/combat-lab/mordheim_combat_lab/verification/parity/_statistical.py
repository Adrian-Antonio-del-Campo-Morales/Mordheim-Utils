"""Aggregate statistical parity between the modular oracle and each
optimized backend using the six-sigma gate."""
from __future__ import annotations

import math
import time
from mordheim_combat import vectorized
from mordheim_core.models import DuelRequest
from mordheim_combat_lab.verification.parity._report import StatisticalParityResult

#: Terminal outcomes, in the oracle's code order: 0 first win, 1 second win,
#: 2 unresolved.  The battery and this historical certificate share the same
#: three categories and the same tolerance.
OUTCOME_LABELS = ("first", "second", "unresolved")


def outcome_counts(winner_values) -> tuple[int, int, int]:
    """Count the three terminal outcomes of a winner sample.

    ``winner_values`` uses the modular convention (0 first, 1 second, 2
    unresolved); the battery validates and maps the candidate onto it before
    counting, so a comparison never mixes code conventions.  A code outside
    the three categories is malformed data, not a fourth outcome and not an
    unresolved duel: it raises instead of being dropped, so a defect in an
    engine's convention can never hide as a rate deficit.
    """
    counts = [0, 0, 0]
    for value in winner_values:
        # ``np.bool_`` is not a ``bool`` subclass and ``int(True) == 1``, so an
        # unguarded boolean sample would pass the integrality check and count as
        # a win.  Reject the boolean dtype too, before converting anything.
        if isinstance(value, bool) or getattr(
                getattr(value, "dtype", None), "kind", None) == "b":
            raise ValueError(f"winner code {value!r} is not a terminal outcome")
        try:
            code = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"winner code {value!r} is not an integer terminal outcome"
            ) from error
        if code != value:
            raise ValueError(
                f"winner code {value!r} is not an integer terminal outcome"
            )
        if not 0 <= code <= 2:
            raise ValueError(
                f"winner code {code} is outside the oracle convention 0/1/2"
            )
        counts[code] += 1
    return counts[0], counts[1], counts[2]


def outcome_rates(counts: tuple[int, int, int], simulations: int) -> tuple[float, float, float]:
    """Return win/win/unresolved rates of ``counts`` over ``simulations``."""
    if simulations < 1:
        raise ValueError("a rate needs at least one simulation")
    return tuple(value / simulations for value in counts)


def six_sigma_tolerance(left: float, right: float, simulations: int) -> float:
    """The documented tolerance: six sigma of both samples, floor 0.25%.

    Both the historical statistical certificate and the renewed statistical
    battery use this single formula; lowering the floor or the sigma factor
    would make a campaign easier to pass, so it is never a parameter.
    """
    return max(
        .0025,
        6 * math.sqrt(
            left * (1 - left) / simulations + right * (1 - right) / simulations
        ),
    )


def compare_outcome_rates(
    modular_counts: tuple[int, int, int],
    candidate_counts: tuple[int, int, int],
    simulations: int,
) -> tuple[tuple[float, float, float], tuple[float, float, float],
           tuple[float, float, float], bool]:
    """Compare two outcome count triples with the six-sigma gate.

    Returns (modular rates, candidate rates, tolerances, passed).  A magnitude
    that both engines leave unresolved with the same probability passes: the
    gate compares distributions, it does not require a decisive duel.
    """
    modular_rates = outcome_rates(modular_counts, simulations)
    candidate_rates = outcome_rates(candidate_counts, simulations)
    tolerances = tuple(
        six_sigma_tolerance(left, right, simulations)
        for left, right in zip(modular_rates, candidate_rates)
    )
    passed = all(
        abs(left - right) <= tolerance
        for left, right, tolerance in zip(modular_rates, candidate_rates, tolerances)
    )
    return modular_rates, candidate_rates, tolerances, passed


def compare_samples(
    scenario: str, simulations: int,
    modular_counts: tuple[int, int, int], candidate_counts: tuple[int, int, int],
    *, backend: str = "native", reference_seconds: float = 0.0,
    candidate_seconds: float = 0.0,
) -> StatisticalParityResult:
    """Compare stored outcome counts without executing either engine.

    Keep the existing result shape and NumPy callers compatible; native
    records can be compared without installing the native engine.
    """
    if backend not in ("numpy", "native"):
        raise ValueError(f"unsupported optimized backend: {backend}")
    for label, counts in (("modular", modular_counts), ("candidate", candidate_counts)):
        if len(counts) != 3 or sum(counts) != simulations:
            raise ValueError(
                f"{label} counts {tuple(counts)!r} do not describe "
                f"{simulations} duels"
            )
    modular_rates, vector_rates, tolerances, passed = compare_outcome_rates(
        tuple(modular_counts), tuple(candidate_counts), simulations,
    )
    return StatisticalParityResult(
        scenario=scenario, backend=backend, simulations=simulations,
        modular_rates=modular_rates, vectorized_rates=vector_rates,
        tolerances=tolerances, passed=passed,
        reference_seconds=reference_seconds, candidate_seconds=candidate_seconds,
    )


def _parity_result(scenario: str, backend: str, simulations: int, modular, vector,
                   reference_seconds: float, candidate_seconds: float) -> StatisticalParityResult:
    modular_counts = (modular.first_wins, modular.second_wins, modular.unresolved)
    vector_counts = (vector.first_wins, vector.second_wins, vector.unresolved)
    modular_rates, vector_rates, tolerances, passed = compare_outcome_rates(
        modular_counts, vector_counts, simulations,
    )
    return StatisticalParityResult(
        scenario=scenario, backend=backend, simulations=simulations,
        modular_rates=modular_rates, vectorized_rates=vector_rates,
        tolerances=tolerances, passed=passed,
        reference_seconds=reference_seconds, candidate_seconds=candidate_seconds,
    )

def compare_statistical_parity(
    scenario: str, first, second, simulations: int, *, seed: int = 2026,
    maximum_rounds: int = 50, backend: str = "numpy", modular=None,
    reference_seconds: float | None = None,
) -> StatisticalParityResult:
    """Compare independent aggregate samples using the documented six-sigma gate.

    The modular engine is the only correctness oracle; ``backend`` selects the
    optimized candidate to certify against it ("numpy" or "native").  Pass a
    precomputed ``modular`` result to certify several candidates against the
    same oracle sample without re-running the modular engine; when you do,
    pass ``reference_seconds`` (measured at the sampling site) so the result
    reports each engine's wall time.  The candidate sample is timed here.
    """
    from mordheim_combat.modular.duel import simulate_duel_reference

    if simulations < 1:
        raise ValueError("statistical parity needs at least one simulation")
    if backend not in {"numpy", "native"}:
        raise ValueError(f"unknown optimized backend: {backend}")
    if modular is None:
        started = time.perf_counter()
        modular = simulate_duel_reference(
            first, second, simulations, seed=seed, maximum_rounds=maximum_rounds,
        )
        reference_seconds = time.perf_counter() - started
    candidate_started = time.perf_counter()
    vector = vectorized.simulate_duel(
        DuelRequest(
            first, second, simulations, seed=seed + 1_000_003,
            maximum_rounds=maximum_rounds,
        ),
        backend=backend,
    )
    candidate_seconds = time.perf_counter() - candidate_started
    return _parity_result(
        scenario, backend, simulations, modular, vector,
        reference_seconds if reference_seconds is not None else 0.0,
        candidate_seconds,
    )
