"""Modular-to-native statistical-parity runner.

A :class:`ParityCase` names one duel construction and its declared sample
contract (round limit, sample width, seed).  ``run_parity`` performs the whole
orchestration once:

- sample the modular oracle once per case;
- sample the native candidate against that oracle with the documented six-sigma
  gate, and record the stages each row actually reached (executed, compared,
  approved);
- expand a case at several round limits when ``horizons`` is supplied, which is
  how round truncation is configured instead of using a separate runner.

Rows are winner-only aggregate comparisons (``candidate="counts"``): the same
gate :func:`tools.verification.parity_statistical.compare_statistical_parity`
uses, with the candidate sample seeded ``seed + 1_000_003``.

Cases are always prepared by the caller: precompiled fighters never trigger a
compile or a compiler fallback.  The modular oracle is the only reference and
the compiled native engine the only candidate.
"""
from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack
from dataclasses import dataclass
from typing import Iterable, Sequence

from mordheim_combat.modular.parallel import resolve_oracle_workers
from mordheim_combat.modular.parallel import run_oracle_sample
from mordheim_combat.native import NativeIncompatible
from mordheim_combat.native import NativeUnavailable

from tools.verification.parity_statistical import (
    OUTCOME_LABELS,
    StatisticalParityResult,
    compare_statistical_parity,
)

#: Horizons swept by a truncation comparison.  Cases keep only the horizons
#: within their own round budget (filtered by ``run_parity``).
TRUNCATION_HORIZONS = (2, 4, 6, 8, 10, 12, 15, 20)


@dataclass(frozen=True, slots=True)
class MagnitudeComparison:
    """One compared magnitude, with the rates the two engines produced.

    ``magnitude`` is the compared label (``winner``); ``passed`` is the
    six-sigma decision on it.  Rates are in oracle code order: 0=first win,
    1=second win, 2=unresolved.
    """

    magnitude: str
    modular_rates: tuple[float, ...]
    candidate_rates: tuple[float, ...]
    tolerances: tuple[float, ...]
    passed: bool
    detail: str = ""


@dataclass(frozen=True, slots=True)
class ParityCase:
    """One duel construction and its declared sample contract."""

    label: str
    first: object
    second: object
    maximum_rounds: int = 50
    #: Sample width; ``run_parity(simulations=...)`` overrides it.
    simulations: int | None = None
    seed: int = 2026


@dataclass(frozen=True, slots=True)
class ParityRow:
    """One backend's result for one case at one round limit."""

    case: str
    backend: str
    maximum_rounds: int
    simulations: int
    status: str
    comparisons: tuple[MagnitudeComparison, ...] = ()
    executed: bool = False
    compared: bool = False
    approved: bool = False
    modular_seconds: float = 0.0
    candidate_seconds: float = 0.0
    detail: str = ""

    @property
    def winner(self) -> MagnitudeComparison | None:
        return next(
            (item for item in self.comparisons if item.magnitude == "winner"),
            None,
        )


@dataclass(frozen=True, slots=True)
class ParityRun:
    """Rows of one run and the modular duels they actually paid for."""

    rows: tuple[ParityRow, ...]
    modular_duels: int = 0


def _winner_detail(modular_rates, candidate_rates, tolerances) -> str:
    worst: tuple[float, str] | None = None
    for label, left, right, tolerance in zip(
        OUTCOME_LABELS, modular_rates, candidate_rates, tolerances,
    ):
        margin = abs(left - right) - tolerance
        text = (
            f"winner[{label}]: modular={left:.6f}, "
            f"candidate={right:.6f}, tol={tolerance:.6f}"
        )
        if worst is None or margin > worst[0]:
            worst = (margin, text)
    return "" if worst is None else worst[1]


def _comparison_from_result(result) -> MagnitudeComparison:
    """Adapt a winner-only ``StatisticalParityResult`` to one magnitude row."""
    return MagnitudeComparison(
        magnitude="winner",
        modular_rates=tuple(result.modular_rates),
        candidate_rates=tuple(result.candidate_rates),
        tolerances=tuple(result.tolerances),
        passed=bool(result.passed),
        detail=_winner_detail(
            result.modular_rates, result.candidate_rates, result.tolerances,
        ),
    )


def statistical_result(row: ParityRow) -> StatisticalParityResult:
    """Project a winner-only row onto the statistical sample record."""
    comparison = row.winner
    if comparison is None:
        raise RuntimeError(
            f"parity row {row.case}/{row.backend} has no sample: {row.detail}"
        )
    return StatisticalParityResult(
        scenario=row.case,
        backend=row.backend,
        simulations=row.simulations,
        modular_rates=comparison.modular_rates,
        candidate_rates=comparison.candidate_rates,
        tolerances=comparison.tolerances,
        passed=comparison.passed,
        reference_seconds=row.modular_seconds,
        candidate_seconds=row.candidate_seconds,
    )


def _row(
    case: str, backend: str, maximum_rounds: int, simulations: int, status: str,
    **options,
) -> ParityRow:
    return ParityRow(
        case=case, backend=backend, maximum_rounds=maximum_rounds,
        simulations=simulations, status=status, **options,
    )


def _reference_failure_rows(case: ParityCase, backends: Iterable[str],
                            simulations: int, detail: str):
    """The oracle sample failed, so the candidate never ran: never a verdict."""
    return tuple(
        _row(
            case.label, backend, case.maximum_rounds, simulations,
            "NOT_RUN", detail=f"NOT_RUN:reference: {detail}",
        )
        for backend in backends
    )


def _count_row(case, backend, simulations, reference_counts, modular_seconds):
    try:
        result = compare_statistical_parity(
            case.label, case.first, case.second, simulations, seed=case.seed,
            maximum_rounds=case.maximum_rounds, backend=backend,
            modular=reference_counts, reference_seconds=modular_seconds,
        )
    except NativeUnavailable as error:
        # The candidate could not be executed at all: the campaign ran but this
        # row has no comparison, so it is never approved.
        return _row(
            case.label, backend, case.maximum_rounds, simulations,
            "NOT_RUN", modular_seconds=modular_seconds,
            detail=f"NOT_RUN:native: {error}",
        )
    except NativeIncompatible as error:
        return _row(
            case.label, backend, case.maximum_rounds, simulations,
            "INCOMPATIBLE", modular_seconds=modular_seconds,
            detail=f"INCOMPATIBLE:plan: {error}",
        )
    except ValueError as error:
        # A declared input limit or an admission refusal means the candidate
        # cannot run this scenario at all: that is an incompatibility, never a
        # divergence and never an approved comparison.
        message = str(error)
        if ("require the modular engine" in message
                or "optimized ports are pending" in message
                or "outside the one-against-one runtime" in message):
            return _row(
                case.label, backend, case.maximum_rounds, simulations,
                "INCOMPATIBLE", modular_seconds=modular_seconds,
                detail=f"INCOMPATIBLE:admission: {message}",
            )
        return _row(
            case.label, backend, case.maximum_rounds, simulations,
            "DIVERGENCE", modular_seconds=modular_seconds,
            detail=f"DIVERGENCE:exception:ValueError: {message}",
        )
    except Exception as error:
        return _row(
            case.label, backend, case.maximum_rounds, simulations,
            "DIVERGENCE", modular_seconds=modular_seconds,
            detail=f"DIVERGENCE:exception:{type(error).__name__}: {error}",
        )
    comparison = _comparison_from_result(result)
    return _row(
        case.label, backend, case.maximum_rounds, simulations,
        "PASS" if comparison.passed else "DIVERGENCE",
        comparisons=(comparison,), executed=True, compared=True,
        approved=comparison.passed,
        modular_seconds=result.reference_seconds,
        candidate_seconds=result.candidate_seconds,
        detail="" if comparison.passed else f"DIVERGENCE: {comparison.detail}",
    )


def _case_rows(
    case: ParityCase, simulations: int, *, backends: Sequence[str],
    workers: int | None = None, executor=None,
) -> tuple[tuple[ParityRow, ...], int]:
    """Sample the oracle and compare every backend; returns ``(rows, duels)``."""
    started = time.perf_counter()
    try:
        oracle = run_oracle_sample(
            case.first, case.second, simulations, seed=case.seed,
            maximum_rounds=case.maximum_rounds, workers=workers,
            executor=executor,
        )
    except Exception as error:
        return _reference_failure_rows(
            case, backends, simulations,
            f"exception:{type(error).__name__}: {error}",
        ), 0
    modular_seconds = time.perf_counter() - started
    rows = tuple(
        _count_row(case, backend, simulations, oracle, modular_seconds)
        for backend in backends
    )
    return rows, simulations


def _expand(case: ParityCase, *, simulations: int, seed: int,
            maximum_rounds: int, horizons: Sequence[int] | None):
    """One entry per round limit; a bare case keeps its own label."""
    if horizons is None:
        return (
            ParityCase(
                label=case.label, first=case.first, second=case.second,
                maximum_rounds=maximum_rounds, simulations=simulations,
                seed=seed,
            ),
        )
    effective = tuple(sorted({h for h in horizons if 1 <= h <= maximum_rounds}))
    if not effective:
        raise ValueError("no truncation horizon fits the round budget")
    return tuple(
        ParityCase(
            label=f"{case.label}@rounds={horizon}", first=case.first,
            second=case.second, maximum_rounds=horizon,
            simulations=simulations, seed=seed,
        )
        for horizon in effective
    )


def run_parity(
    cases: Iterable[ParityCase], *,
    backends: Sequence[str] = ("native",),
    candidate: str = "counts",
    simulations: int | None = None,
    seed: int | None = None,
    maximum_rounds: int | None = None,
    workers: int | str | None = 1,
    horizons: Sequence[int] | None = None,
) -> ParityRun:
    """Run every case through the modular reference and the requested candidates.

    ``candidate`` is ``"counts"``: winner-only aggregate samples compared with
    the documented six-sigma gate.  ``backends`` names the optimised engines to
    certify, which is the compiled native engine.  ``simulations``, ``seed`` and
    ``maximum_rounds`` override the per-case declaration.  ``workers`` is the
    modular-oracle process policy (``"auto"``, ``1`` for sequential, or a
    positive count); one pool is reused across the run, and chunking reproduces
    the sequential sample duel for duel.  ``horizons`` expands each case at
    several round limits (round truncation), keeping only the horizons inside
    the case's own round budget.
    """
    cases = tuple(cases)
    backends = tuple(backends)
    if candidate != "counts":
        raise ValueError(f"unknown parity candidate surface: {candidate}")
    for backend in backends:
        if backend != "native":
            raise ValueError(f"unknown optimized backend: {backend}")
    if workers is not None and str(workers).casefold() != "auto" and int(workers) < 1:
        raise ValueError("workers must be positive or auto")

    expanded: list[ParityCase] = []
    for case in cases:
        size = simulations if simulations is not None else case.simulations
        if size is None:
            raise ValueError(f"case {case.label} declares no simulation count")
        if int(size) < 1:
            raise ValueError("statistical parity needs at least one simulation")
        expanded.extend(_expand(
            case, simulations=int(size),
            seed=case.seed if seed is None else seed,
            maximum_rounds=(
                case.maximum_rounds if maximum_rounds is None else maximum_rounds
            ),
            horizons=horizons,
        ))

    resolved = tuple(
        resolve_oracle_workers(workers, item.simulations, item.maximum_rounds)
        for item in expanded
    )
    rows: list[ParityRow] = []
    modular_duels = 0
    with ExitStack() as stack:
        pool_size = max((count or 1 for count in resolved), default=1)
        executor = (
            stack.enter_context(ProcessPoolExecutor(max_workers=pool_size))
            if pool_size > 1 else None
        )
        for item, count in zip(expanded, resolved):
            item_rows, duels = _case_rows(
                item, item.simulations, backends=backends, workers=count,
                executor=executor,
            )
            rows.extend(item_rows)
            modular_duels += duels

    return ParityRun(rows=tuple(rows), modular_duels=modular_duels)


__all__ = (
    "MagnitudeComparison",
    "ParityCase",
    "ParityRow",
    "ParityRun",
    "TRUNCATION_HORIZONS",
    "run_parity",
    "statistical_result",
)
