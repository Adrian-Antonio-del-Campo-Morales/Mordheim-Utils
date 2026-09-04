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


def certify_deep(
    pairs: Iterable[DeepPair], *,
    simulations: int, cross_simulations: int, seed: int,
    native_installed: bool,
    on_progress: Callable[[], None] | None = None,
    workers: object | None = None,
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
    finally:
        if executor is not None:
            executor.shutdown()
    return tuple(samples), modular_duels
