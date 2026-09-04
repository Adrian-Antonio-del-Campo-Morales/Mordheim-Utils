"""Deep certification: archetype-matrix six-sigma samples and a bounded
modular oracle budget.

``parity --deep`` extends the standard certification in two directions:

- **Matrix samples** — every archetype pair of ``deep_test_scenarios()`` is
  compared statistically (same six-sigma gate as ``--statistical``) between
  the modular oracle and each optimized backend. The oracle sample per pair
  is deliberately bounded (``simulations``, default 100,000, or 25,000 for
  the long 75-round pair): statistical resolution is capped by the smaller
  sample, so running millions of duels on the modular engine would buy no
  extra evidence.
- **Cross-backend samples** — NumPy and native (both fast) are certified
  against each other at ``cross_simulations`` (default 1,000,000) per pair,
  using a NumPy sample as the reference. This is where large sample sizes
  are meaningful and cheap; the modular engine is never involved.
"""
from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterable
from dataclasses import replace
import math
import time

from mordheim_combat import vectorized
from mordheim_core.models import DuelRequest
from mordheim_combat_lab.verification.parity._report import StatisticalParityResult
from mordheim_combat_lab.verification.parity._statistical import compare_statistical_parity


class DeepPair:
    """One compiled duel construction of the deep matrix."""

    __slots__ = ("label", "first", "second", "maximum_rounds", "simulations")

    def __init__(self, label, first, second, maximum_rounds: int = 50,
                 simulations: int | None = None):
        self.label = label
        self.first = first
        self.second = second
        self.maximum_rounds = maximum_rounds
        # Per-pair modular-oracle sample size; None defers to certify_deep's
        # ``simulations`` argument (the CLI splits the budget: 100k per pair,
        # 25k for the long 75-round pair).
        self.simulations = simulations


def _backend_sample(label: str, pair: DeepPair, simulations: int, seed: int,
                    backend: str, reference=None,
                    reference_seconds: float | None = None) -> StatisticalParityResult:
    return compare_statistical_parity(
        label, pair.first, pair.second, simulations, seed=seed,
        maximum_rounds=pair.maximum_rounds, backend=backend, modular=reference,
        reference_seconds=reference_seconds,
    )


def _rate_sigma(row: StatisticalParityResult) -> float:
    """Worst deviation across the three outcome rates, in sigma units."""
    worst = 0.0
    for left, right in zip(row.modular_rates, row.vectorized_rates):
        variance = (
            left * (1 - left) / row.simulations
            + right * (1 - right) / row.simulations
        )
        if variance > 0:
            worst = max(worst, abs(left - right) / math.sqrt(variance))
    return worst


def _pair_unresolved_rate(row: StatisticalParityResult) -> float:
    """Highest unresolved rate across the two engines for one row."""
    return max(row.modular_rates[2], row.vectorized_rates[2])


def escalation_plan(
    prepared, samples, *, factor: int, sigma: float, unresolved: float,
    remaining: int | None,
):
    """Pick the pairs that deserve a larger oracle sample, in priority order.

    A pair is escalated when the first-pass comparison is suspicious
    (``sigma <= pair_sigma < 6`` -- the band where doubling the sample
    decides between a real defect and noise) or when its unresolved rate
    shows the timing-prone profile the flat gate is blind to (the
    ``elite-vs-durable`` class).  Conclusive failures (six sigma or above)
    are not re-run: the defect is already established.  Escalated sizes are
    ``base * factor``, allocated greedily in priority order (most
    suspicious first) until ``remaining`` duels run out; pairs that do not
    fit stay at the base sample.  Returns ``(pair, new_size)`` tuples.
    """
    plan = []
    sizes = {}
    for pair, size, _ in prepared:
        sizes[pair.label] = size
        rows = [row for row in samples if row.scenario == f"matrix:{pair.label}"]
        if not rows:
            continue
        worst = max(_rate_sigma(row) for row in rows)
        unresolved_rate = max(_pair_unresolved_rate(row) for row in rows)
        if not (sigma <= worst < 6.0 or unresolved_rate >= unresolved):
            continue
        plan.append((pair, sizes[pair.label] * factor, worst, unresolved_rate))
    plan.sort(key=lambda item: (-item[2], -item[3]))
    chosen = []
    budget = remaining
    for pair, new_size, _worst, _unresolved in plan:
        extra = new_size - sizes[pair.label]
        if budget is not None:
            if extra > budget:
                continue
            budget -= extra
        chosen.append((pair, new_size))
    return tuple(chosen)


def certify_deep(
    pairs: Iterable[DeepPair], *,
    simulations: int, cross_simulations: int, seed: int,
    native_installed: bool,
    on_progress: Callable[[], None] | None = None,
    workers: object | None = None,
    escalate: bool = False, escalation_factor: int = 2,
    escalate_sigma: float = 3.0, escalate_unresolved: float = 0.01,
    max_modular_duels: int | None = None,
) -> tuple[tuple[StatisticalParityResult, ...], int]:
    """Certify the deep matrix.

    Returns ``(samples, modular_duels)`` where ``modular_duels`` is the
    total number of duels requested from the modular oracle (per-pair sample
    sizes, defaulting to ``simulations``; the cross layer never touches it).
    Matrix rows are labelled ``matrix:<pair>`` and cross rows
    ``cross:<pair>``. ``on_progress`` is invoked once per completed work
    unit (matrix and, when the native backend is installed, cross layer).

    ``workers`` selects the process-pool policy for the per-pair oracle
    samples (see ``resolve_oracle_workers``: ``None``/``"auto"`` pools only
    the samples whose estimated sequential time exceeds the gate, an explicit
    integer forces that pool size).  Certificates are bit-for-bit identical
    to the sequential path whatever the policy.  When any pair is pooled, a
    single shared executor serves every pair so the workers spawn once per
    run rather than once per sample.

    ``escalate`` enables adaptive per-pair re-certification: pairs whose
    first pass is suspicious (three to just under six sigma) or timing-prone
    (unresolved rate at or above ``escalate_unresolved``) are re-run at
    ``escalation_factor`` times the base sample, bounded by
    ``max_modular_duels`` (``None`` leaves the escalation unbounded).
    Duels are seeded per index, so a larger sample with the same seed is a
    superset of the smaller one: the base duels are not wasted and
    ``modular_duels`` counts the final (escalated) sizes.  Escalated matrix
    rows carry ``escalated=True``.
    """
    from mordheim_combat.modular.parallel import resolve_oracle_workers
    from mordheim_combat.modular.parallel import run_oracle_sample

    pairs = tuple(pairs)  # the policy pass and the sampling loop both iterate
    prepared = []
    pooled_workers: list[int] = []
    for pair in pairs:
        sample_size = pair.simulations if pair.simulations is not None else simulations
        chosen = resolve_oracle_workers(workers, sample_size, pair.maximum_rounds)
        if chosen is not None:
            pooled_workers.append(chosen)
        prepared.append((pair, sample_size, chosen))
    executor = None
    if pooled_workers:
        from concurrent.futures import ProcessPoolExecutor
        executor = ProcessPoolExecutor(max_workers=max(pooled_workers))
    samples: list[StatisticalParityResult] = []
    modular_duels = 0
    try:
        for pair, sample_size, chosen in prepared:
            label = pair.label
            # The oracle sample is computed once and shared by every backend.
            oracle_started = time.perf_counter()
            modular = run_oracle_sample(
                pair.first, pair.second, sample_size, seed=seed,
                maximum_rounds=pair.maximum_rounds,
                workers=chosen, executor=executor,
            )
            oracle_seconds = time.perf_counter() - oracle_started
            modular_duels += sample_size
            samples.append(_backend_sample(
                f"matrix:{label}", pair, sample_size, seed, "numpy",
                reference=modular, reference_seconds=oracle_seconds))
            if native_installed:
                samples.append(_backend_sample(
                    f"matrix:{label}", pair, sample_size, seed, "native",
                    reference=modular, reference_seconds=oracle_seconds))
            if on_progress is not None:
                on_progress()
            # Cross-backend certification at scale: NumPy is the reference for
            # the native candidate. Both engines are fast, so the sample can
            # be large; the modular engine is not involved.
            cross_started = time.perf_counter()
            numpy_reference = vectorized.simulate_duel(
                DuelRequest(
                    pair.first, pair.second, cross_simulations, seed=seed,
                    maximum_rounds=pair.maximum_rounds,
                ),
                backend="numpy",
            )
            cross_seconds = time.perf_counter() - cross_started
            if native_installed:
                samples.append(_backend_sample(
                    f"cross:{label}", pair, cross_simulations, seed, "native",
                    reference=numpy_reference, reference_seconds=cross_seconds,
                ))
                if on_progress is not None:
                    on_progress()
        if escalate:
            base_duels = sum(size for _, size, _ in prepared)
            remaining = (
                None if max_modular_duels is None
                else max_modular_duels - base_duels
            )
            for pair, new_size in escalation_plan(
                prepared, samples, factor=escalation_factor,
                sigma=escalate_sigma, unresolved=escalate_unresolved,
                remaining=remaining,
            ):
                label = pair.label
                chosen = resolve_oracle_workers(
                    workers, new_size, pair.maximum_rounds)
                oracle_started = time.perf_counter()
                modular = run_oracle_sample(
                    pair.first, pair.second, new_size, seed=seed,
                    maximum_rounds=pair.maximum_rounds,
                    workers=chosen, executor=executor,
                )
                oracle_seconds = time.perf_counter() - oracle_started
                base_size = pair.simulations if pair.simulations is not None else simulations
                modular_duels += new_size - base_size
                replacement = [
                    _backend_sample(
                        f"matrix:{label}", pair, new_size, seed, "numpy",
                        reference=modular, reference_seconds=oracle_seconds)]
                if native_installed:
                    replacement.append(_backend_sample(
                        f"matrix:{label}", pair, new_size, seed, "native",
                        reference=modular, reference_seconds=oracle_seconds))
                replacement = [replace(row, escalated=True) for row in replacement]
                samples = [row for row in samples
                           if row.scenario != f"matrix:{label}"] + replacement
                if on_progress is not None:
                    on_progress()
    finally:
        if executor is not None:
            executor.shutdown()
    return tuple(samples), modular_duels
