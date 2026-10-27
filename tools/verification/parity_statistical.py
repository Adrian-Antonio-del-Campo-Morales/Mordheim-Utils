"""Aggregate statistical parity between the modular oracle and the native
backend using the six-sigma gate.

Extracted from Combat Lab's parity tooling so the engine tests own their
comparison.  The modular engine is the only correctness oracle and the
compiled native engine the only certified candidate.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass

from mordheim_combat import native
from mordheim_core.models import DuelRequest


@dataclass(frozen=True, slots=True)
class StatisticalParityResult:
    """One comparable sample pair and its six-sigma decision."""

    scenario: str
    backend: str
    simulations: int
    modular_rates: tuple[float, float, float]
    candidate_rates: tuple[float, float, float]
    tolerances: tuple[float, float, float]
    passed: bool
    # Wall time of each engine's sample, at engine level: ``reference`` is the
    # modular oracle; ``candidate`` is the backend named in ``backend``. Zero
    # when the sample was supplied by the caller without a measurement.
    reference_seconds: float = 0.0
    candidate_seconds: float = 0.0


#: Terminal outcomes, in the oracle's code order: 0 first win, 1 second win,
#: 2 unresolved.  The tolerance below applies to the same three categories.
OUTCOME_LABELS = ("first", "second", "unresolved")


def outcome_counts(winner_values) -> tuple[int, int, int]:
    """Count the three terminal outcomes of a winner sample.

    ``winner_values`` uses the modular convention (0 first, 1 second, 2
    unresolved); the candidate validates and maps its own codes onto it before
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

    Every statistical comparison uses this single formula; lowering the floor
    or the sigma factor would make a comparison easier to pass, so it is never
    a parameter.
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


def _parity_result(scenario: str, backend: str, simulations: int, modular, candidate,
                   reference_seconds: float, candidate_seconds: float) -> StatisticalParityResult:
    modular_counts = (modular.first_wins, modular.second_wins, modular.unresolved)
    candidate_counts = (
        candidate.first_wins, candidate.second_wins, candidate.unresolved,
    )
    modular_rates, candidate_rates, tolerances, passed = compare_outcome_rates(
        modular_counts, candidate_counts, simulations,
    )
    return StatisticalParityResult(
        scenario=scenario, backend=backend, simulations=simulations,
        modular_rates=modular_rates, candidate_rates=candidate_rates,
        tolerances=tolerances, passed=passed,
        reference_seconds=reference_seconds, candidate_seconds=candidate_seconds,
    )


def compare_statistical_parity(
    scenario: str, first, second, simulations: int, *, seed: int = 2026,
    maximum_rounds: int = 50, backend: str = "native", modular=None,
    reference_seconds: float | None = None,
) -> StatisticalParityResult:
    """Compare independent aggregate samples using the documented six-sigma gate.

    The modular engine is the only correctness oracle; ``backend`` names the
    certified candidate, which is the compiled native engine.  Pass a
    precomputed ``modular`` result to certify a candidate against an oracle
    sample without re-running the modular engine; when you do, pass
    ``reference_seconds`` (measured at the sampling site) so the result reports
    each engine's wall time.  The candidate sample is timed here.
    """
    from mordheim_combat.modular.duel import simulate_duel_reference

    if simulations < 1:
        raise ValueError("statistical parity needs at least one simulation")
    if backend != "native":
        raise ValueError(f"unsupported optimized backend: {backend}")
    if modular is None:
        started = time.perf_counter()
        modular = simulate_duel_reference(
            first, second, simulations, seed=seed, maximum_rounds=maximum_rounds,
        )
        reference_seconds = time.perf_counter() - started
    candidate_started = time.perf_counter()
    candidate = native.simulate_duel(
        DuelRequest(
            first, second, simulations, seed=seed + 1_000_003,
            maximum_rounds=maximum_rounds,
        ),
    )
    candidate_seconds = time.perf_counter() - candidate_started
    return _parity_result(
        scenario, backend, simulations, modular, candidate,
        reference_seconds if reference_seconds is not None else 0.0,
        candidate_seconds,
    )
