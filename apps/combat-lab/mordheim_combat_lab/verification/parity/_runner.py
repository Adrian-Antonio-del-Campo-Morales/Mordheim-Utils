"""One statistical-parity runner for the deep matrix, the battery and truncation.

A :class:`ParityCase` names one duel construction and its declared sample
contract (round limit, sample width, seed, compared magnitudes).  ``run_parity``
performs the whole orchestration once:

- sample the reference once per case — the modular oracle, or a NumPy sample
  for the NumPy-to-native cross layer — honouring the resolved worker policy;
- sample each requested candidate backend;
- compare the declared magnitudes with the documented six-sigma gate, and
  record the stages each row actually reached (executed, compared, approved);
- expand a case at several round limits when ``horizons`` is supplied, which is
  how round truncation is configured instead of using a separate runner;
- re-certify suspicious rows at a larger orcale sample when ``escalate`` is set,
  bounded by ``max_modular_duels``.

Two evidence surfaces are preserved because they certify different contracts:

- ``candidate="counts"`` compares the three terminal outcome counts through
  :func:`compare_statistical_parity` (winner only).  This is the deep and
  truncation certificate, with the candidate sample seeded ``seed + 1_000_003``.
- ``candidate="observed"`` keeps per-duel rows so ``rounds``, ``wounds`` and
  ``condition`` can be compared, and re-samples the candidate once to prove the
  batch is deterministic.  This is the battery contract.

Cases are always prepared by the caller: precompiled fighters never trigger a
compile or a compiler fallback; the battery compiles its own catalogue builds
before calling here.
"""
from __future__ import annotations

import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack
from dataclasses import dataclass, replace
from typing import Callable, Iterable, Sequence

import numpy as np

from mordheim_combat import vectorized
from mordheim_combat.modular.duel import simulate_duel_observed
from mordheim_combat.modular.parallel import chunk_ranges, resolve_oracle_workers
from mordheim_combat.vectorized import simulate_batch_observed
from mordheim_core.models import DuelRequest, ObservedDuelResult

from mordheim_combat_lab.verification.parity._report import StatisticalParityResult
from mordheim_combat_lab.verification.parity._statistical import (
    OUTCOME_LABELS,
    compare_outcome_rates,
    compare_statistical_parity,
    outcome_counts,
    six_sigma_tolerance,
)

#: Horizons swept by a truncation certification.  Cases keep only the horizons
#: within their own round budget (filtered by ``run_parity``).
TRUNCATION_HORIZONS = (2, 4, 6, 8, 10, 12, 15, 20)

#: Terminal outcome codes each engine actually publishes.  The oracle uses
#: 0/1/2; the optimized candidate uses 1/-1/0.  ``0`` means opposite things in
#: the two conventions, so each sample is validated against its own set before
#: any mapping happens.
_ORACLE_WINNER_CODES = frozenset({0, 1, 2})
_CANDIDATE_WINNER_CODES = frozenset({-1, 0, 1})

#: Winner-only rows can be compared from aggregate counts; a declared magnitude
#: other than ``winner`` needs the per-duel rows of the observed surface.
_COUNT_MAGNITUDES = ("winner",)


class _NativeUnavailable(RuntimeError):
    """The native extension is absent, stale or cannot run this plan."""


class OutcomeCodeError(ValueError):
    """A sample published a winner code its engine's convention does not define."""


@dataclass(frozen=True, slots=True)
class MagnitudeComparison:
    """One compared magnitude, with the rates the two engines produced.

    ``magnitude`` is the compared label (``winner``, ``rounds``,
    ``wounds[first]``…); ``passed`` is the six-sigma decision on it.  Rates are
    in oracle code order: for ``winner`` 0=first win, 1=second win, 2=unresolved.
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
    #: Magnitudes actually compared; ``winner`` is always required.
    magnitudes: tuple[str, ...] = _COUNT_MAGNITUDES
    #: Scripted decisions and duel context for the observed surface only.
    decisions: object = None
    context: object = None
    #: A declared input limitation the API cannot express (battery catalogue).
    blocked_by: str | None = None


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
    escalated: bool = False
    blocked_by: str | None = None

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


def _native_engine():
    """Return the native module only when it is version-compatible."""
    try:
        from mordheim_combat import _combat_native as engine
    except ImportError as error:  # pragma: no cover - optional extension
        raise _NativeUnavailable("native extension is not installed") from error
    if getattr(engine, "CONTEXT_VERSION", None) != 1:
        raise _NativeUnavailable("native extension context version is stale")
    if not hasattr(engine, "simulate_batch_observed"):
        raise _NativeUnavailable("native extension has no batch observation entry")
    return engine


def _candidate_sample(
    backend: str, first, second, rows: int, seed: int, maximum_rounds: int,
    decisions, context,
):
    if backend == "numpy":
        return simulate_batch_observed(
            first, second, rows, np.random.default_rng(seed), maximum_rounds,
            decisions, context=context,
        )
    engine = _native_engine()
    from mordheim_combat.kernel import compile_duel_plan

    try:
        plan = compile_duel_plan(first, second, context=context, backend="native")
    except ValueError as error:
        raise _NativeUnavailable(f"native plan rejected: {error}") from error
    eligible = getattr(plan, "optimization_eligible", True)
    supports = getattr(engine, "supports_plan", None)
    if not eligible or (supports is not None and not supports(plan)):
        raise _NativeUnavailable("native extension does not support this duel plan")
    return engine.simulate_batch_observed(
        first, second, rows, np.random.default_rng(seed), maximum_rounds,
        decisions, context=context,
    )


def _validated_winner_codes(values, allowed: frozenset[int], source: str) -> np.ndarray:
    """Return the sample only when every code belongs to ``source``'s convention."""
    array = np.asarray(values)
    if array.dtype.kind not in "iu":
        raise OutcomeCodeError(
            f"{source} winner codes must be integers, got dtype {array.dtype}"
        )
    unknown = np.unique(array[~np.isin(array, tuple(allowed))])
    if unknown.size:
        raise OutcomeCodeError(
            f"{source} winner code(s) {unknown.tolist()} outside "
            f"{sorted(allowed)}"
        )
    return array


def _winner_codes(values: np.ndarray) -> np.ndarray:
    """Map the candidate's 1/-1/0 onto the oracle's 0/1/2 convention."""
    values = _validated_winner_codes(values, _CANDIDATE_WINNER_CODES, "candidate")
    return np.select(
        (values == 1, values == -1), (0, 1), default=2,
    ).astype(np.int8)


def _admission_tags(first, second, backend: str) -> tuple[str, ...]:
    """Name the effect tags the candidate's admission gate refuses."""
    from mordheim_combat import kernel

    try:
        pending = kernel.pending_capabilities(backend)
    except ValueError:
        return ()
    refused = pending.residual_tags | pending.local_modifier_tags | pending.weapon_profile_tags
    return tuple(sorted({
        tag
        for fighter in (first, second)
        for effect in kernel._effects(fighter)
        for tag in effect.tags
        if tag in refused
    }))


def _category_counts(values: np.ndarray) -> Counter:
    flat = np.asarray(values).ravel().tolist()
    try:
        return Counter(int(value) for value in flat)
    except (TypeError, ValueError):
        return Counter(str(value) for value in flat)


def _detail(
    label: str, categories: Sequence, left, right, rows: int,
    tolerances: Sequence[float],
) -> str:
    """Worst-margin text for one magnitude: the reported evidence."""
    worst: tuple[float, str] | None = None
    for category, left_rate, right_rate, tolerance in zip(
        categories,
        (left.get(category, 0) / rows for category in categories),
        (right.get(category, 0) / rows for category in categories),
        tolerances,
    ):
        text = (
            f"{label}[{category}]: modular={left_rate:.6f}, "
            f"candidate={right_rate:.6f}, tol={tolerance:.6f}"
        )
        margin = abs(left_rate - right_rate) - tolerance
        if worst is None or margin > worst[0]:
            worst = (margin, text)
    return "" if worst is None else worst[1]


def _distribution(
    label: str, modular_values: np.ndarray, candidate_values: np.ndarray, rows: int,
) -> MagnitudeComparison:
    """Compare two category distributions with the six-sigma gate."""
    left = _category_counts(modular_values)
    right = _category_counts(candidate_values)
    categories = sorted(set(left) | set(right), key=str)
    modular_rates = tuple(left.get(category, 0) / rows for category in categories)
    candidate_rates = tuple(right.get(category, 0) / rows for category in categories)
    tolerances = tuple(
        six_sigma_tolerance(left_rate, right_rate, rows)
        for left_rate, right_rate in zip(modular_rates, candidate_rates)
    )
    passed = all(
        abs(left_rate - right_rate) <= tolerance
        for left_rate, right_rate, tolerance in zip(
            modular_rates, candidate_rates, tolerances,
        )
    )
    return MagnitudeComparison(
        magnitude=label,
        modular_rates=modular_rates,
        candidate_rates=candidate_rates,
        tolerances=tolerances,
        passed=passed,
        detail=_detail(label, categories, left, right, rows, tolerances),
    )


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


def _winner_comparison(oracle, candidate, rows: int) -> MagnitudeComparison:
    """Compare the three terminal outcomes through the shared gate.

    Both conventions are validated before normalisation: a code the engine does
    not define raises instead of entering the unresolved category.
    """
    oracle_values = _validated_winner_codes(
        oracle.winner, _ORACLE_WINNER_CODES, "oracle",
    )
    modular_rates, candidate_rates, tolerances, passed = compare_outcome_rates(
        outcome_counts(oracle_values),
        outcome_counts(_winner_codes(candidate.winner)),
        rows,
    )
    return MagnitudeComparison(
        magnitude="winner",
        modular_rates=modular_rates,
        candidate_rates=candidate_rates,
        tolerances=tolerances,
        passed=passed,
        detail=_winner_detail(modular_rates, candidate_rates, tolerances),
    )


def _comparison_from_result(result) -> MagnitudeComparison:
    """Adapt a winner-only ``StatisticalParityResult`` to one magnitude row."""
    return MagnitudeComparison(
        magnitude="winner",
        modular_rates=tuple(result.modular_rates),
        candidate_rates=tuple(result.vectorized_rates),
        tolerances=tuple(result.tolerances),
        passed=bool(result.passed),
        detail=_winner_detail(
            result.modular_rates, result.vectorized_rates, result.tolerances,
        ),
    )


def _shape_mismatch(oracle, candidate, rows: int) -> str | None:
    oracle_fields = {
        "winner": oracle.winner,
        "rounds": oracle.resolution_rounds,
        "first_wounds": oracle.first_wounds,
        "second_wounds": oracle.second_wounds,
        "first_condition": oracle.first_condition,
        "second_condition": oracle.second_condition,
    }
    candidate_fields = {
        "winner": candidate.winner,
        "rounds": candidate.rounds,
        "first_wounds": candidate.first_wounds,
        "second_wounds": candidate.second_wounds,
        "first_condition": candidate.first_condition,
        "second_condition": candidate.second_condition,
    }
    for source, fields in (("oracle", oracle_fields), ("candidate", candidate_fields)):
        for name, values in fields.items():
            if np.asarray(values).shape[0] != rows:
                return f"{source}.{name}: expected {rows}, got {np.asarray(values).shape[0]}"
    return None


def _same_sample(left, right) -> bool:
    for name in (
        "winner", "rounds", "first_wounds", "second_wounds",
        "first_condition", "second_condition",
    ):
        if not np.array_equal(np.asarray(getattr(left, name)), np.asarray(getattr(right, name))):
            return False
    return True


def _decision_key(error: KeyError) -> str:
    messages = [str(item) for item in error.args]
    text = " ".join(messages) or "unknown"
    return text.split("for ")[-1] if "for " in text else text


def _compare_case(
    magnitudes: Sequence[str], oracle, candidate, rows: int,
) -> tuple[tuple[MagnitudeComparison, ...], MagnitudeComparison | None]:
    """Compare every declared magnitude; return (comparisons, first failure)."""
    comparisons: list[MagnitudeComparison] = []
    failure: MagnitudeComparison | None = None
    for name in magnitudes:
        if name == "winner":
            comparison = _winner_comparison(oracle, candidate, rows)
        elif name == "rounds":
            comparison = _distribution(
                "rounds", np.asarray(oracle.resolution_rounds),
                np.asarray(candidate.rounds), rows,
            )
        elif name == "wounds":
            first = _distribution(
                "wounds[first]", np.asarray(oracle.first_wounds),
                np.asarray(candidate.first_wounds), rows,
            )
            second = _distribution(
                "wounds[second]", np.asarray(oracle.second_wounds),
                np.asarray(candidate.second_wounds), rows,
            )
            for item in (first, second):
                comparisons.append(item)
                if not item.passed and failure is None:
                    failure = item
            continue
        elif name == "condition":
            first = _distribution(
                "condition[first]", np.asarray(oracle.first_condition),
                np.asarray(candidate.first_condition), rows,
            )
            second = _distribution(
                "condition[second]", np.asarray(oracle.second_condition),
                np.asarray(candidate.second_condition), rows,
            )
            for item in (first, second):
                comparisons.append(item)
                if not item.passed and failure is None:
                    failure = item
            continue
        else:
            raise ValueError(f"unknown statistical magnitude {name!r}")
        comparisons.append(comparison)
        if not comparison.passed and failure is None:
            failure = comparison
    return tuple(comparisons), failure


def _observed_reference(
    case: ParityCase, simulations: int, *, workers: int | None, executor=None,
):
    """The modular oracle's per-duel sample, chunked without changing outcomes."""
    if executor is None or workers is None or workers < 2:
        return simulate_duel_observed(
            case.first, case.second, simulations, seed=case.seed,
            maximum_rounds=case.maximum_rounds,
            decisions=case.decisions, context=case.context,
        )
    futures = [
        executor.submit(
            simulate_duel_observed, case.first, case.second, count,
            seed=case.seed + start, maximum_rounds=case.maximum_rounds,
            decisions=case.decisions, context=case.context,
        )
        for start, count in chunk_ranges(simulations, workers)
    ]
    try:
        samples = [future.result() for future in futures]
    finally:
        for future in futures:
            future.cancel()
    return ObservedDuelResult(
        **{
            name: np.concatenate([getattr(sample, name) for sample in samples])
            for name in (
                "winner", "resolution_rounds", "first_wounds", "second_wounds",
                "first_condition", "second_condition",
            )
        },
        simulations=simulations, maximum_rounds=case.maximum_rounds,
    )


def statistical_result(row: ParityRow) -> StatisticalParityResult:
    """Project a winner-only row onto the report's statistical sample record."""
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
        vectorized_rates=comparison.candidate_rates,
        tolerances=comparison.tolerances,
        passed=comparison.passed,
        reference_seconds=row.modular_seconds,
        candidate_seconds=row.candidate_seconds,
        escalated=row.escalated,
    )


def _row(
    case: str, backend: str, maximum_rounds: int, simulations: int, status: str,
    **options,
) -> ParityRow:
    return ParityRow(
        case=case, backend=backend, maximum_rounds=maximum_rounds,
        simulations=simulations, status=status, **options,
    )


def _blocked_rows(case: ParityCase, backends: Iterable[str], simulations: int):
    limit = case.blocked_by
    return tuple(
        _row(
            case.label, backend, case.maximum_rounds, simulations,
            "INCOMPATIBLE", blocked_by=limit, detail=f"INCOMPATIBLE:{limit}",
        )
        for backend in backends
    )


def _invalid_rows(case: ParityCase, backends: Iterable[str], simulations: int,
                  detail: str):
    return tuple(
        _row(
            case.label, backend, case.maximum_rounds, simulations,
            "NOT_RUN", detail=detail,
        )
        for backend in backends
    )


def _reference_failure_rows(case, backends, simulations, detail, *, executed=False):
    return tuple(
        _row(
            case.label, backend, case.maximum_rounds, simulations,
            "ERROR" if backend == "modular" else (
                "DIVERGENCE" if detail.startswith("DIVERGENCE") else "NOT_RUN"),
            detail=detail.replace("DIVERGENCE:", "ERROR:", 1) if backend == "modular" else detail,
            executed=executed,
        )
        for backend in backends
    )


def _case_rows(
    case: ParityCase, simulations: int, *, backends: Sequence[str], reference: str,
    candidate: str, workers: int | None, executor, cache: dict | None,
    repeat_candidate: bool,
) -> tuple[tuple[ParityRow, ...], int]:
    """Sample and compare one case; returns ``(rows, modular_duels)``."""
    if case.blocked_by is not None:
        return _blocked_rows(case, backends, simulations), 0
    magnitudes = tuple(case.magnitudes)
    if not magnitudes or "winner" not in magnitudes:
        return _invalid_rows(
            case, backends, simulations,
            "NOT_RUN:case-definition: winner must always be compared owner=P01",
        ), 0
    if reference == "numpy" or candidate == "counts":
        if magnitudes != _COUNT_MAGNITUDES:
            return _invalid_rows(
                case, backends, simulations,
                "NOT_RUN:case-definition: aggregate counts compare only the winner",
            ), 0

    key = f"{case.label}@{simulations}"
    cached = None if cache is None else cache.get(key)
    modular_duels = 0
    if reference == "modular":
        if cached is not None:
            oracle, modular_seconds = cached, 0.0
        else:
            started = time.perf_counter()
            try:
                oracle = _observed_reference(
                    case, simulations, workers=workers, executor=executor,
                )
            except KeyError as error:
                return _reference_failure_rows(
                    case, backends, simulations,
                    f"NOT_RUN:decision-script:{_decision_key(error)} owner=P01",
                ), 0
            except Exception as error:
                return _reference_failure_rows(
                    case, backends, simulations,
                    f"DIVERGENCE:exception:{type(error).__name__}: {error}",
                ), 0
            modular_seconds = time.perf_counter() - started
            modular_duels = simulations
            if cache is not None:
                cache[key] = oracle
    else:
        started = time.perf_counter()
        try:
            oracle = vectorized.simulate_duel(
                DuelRequest(
                    case.first, case.second, simulations, seed=case.seed,
                    maximum_rounds=case.maximum_rounds, context=case.context,
                ),
                backend="numpy",
            )
        except Exception as error:
            return _reference_failure_rows(
                case, backends, simulations,
                f"DIVERGENCE:exception:{type(error).__name__}: {error}",
            ), 0
        modular_seconds = time.perf_counter() - started

    if backends == ("modular",):
        try:
            _validated_winner_codes(oracle.winner, _ORACLE_WINNER_CODES, "oracle")
            for name in ("winner", "resolution_rounds", "first_wounds", "second_wounds",
                         "first_condition", "second_condition"):
                if np.asarray(getattr(oracle, name)).shape != (simulations,):
                    raise ValueError(f"oracle.{name}: expected {simulations} records")
        except (ValueError, TypeError) as error:
            return _reference_failure_rows(
                case, backends, simulations, f"ERROR:sample: {error}", executed=True,
            ), modular_duels
        return (_row(
            case.label, "modular", case.maximum_rounds, simulations, "COMPLETED",
            executed=True, compared=False, approved=False,
            modular_seconds=modular_seconds,
            detail="Modular reference completed; no engine comparison performed.",
        ),), modular_duels

    rows: list[ParityRow] = []
    for backend in backends:
        if candidate == "counts":
            rows.append(_count_row(
                case, backend, simulations, oracle, modular_seconds,
            ))
        else:
            rows.append(_observed_row(
                case, backend, simulations, oracle, modular_seconds,
                magnitudes, repeat_candidate=repeat_candidate,
            ))
    return tuple(rows), modular_duels


def _count_row(case, backend, simulations, reference_counts, modular_seconds):
    if hasattr(reference_counts, "winner"):
        try:
            _validated_winner_codes(
                reference_counts.winner, _ORACLE_WINNER_CODES, "oracle",
            )
        except OutcomeCodeError as error:
            return _row(
                case.label, backend, case.maximum_rounds, simulations,
                "NOT_RUN", modular_seconds=modular_seconds,
                detail=f"NOT_RUN:outcome-codes: {error}",
            )
    try:
        result = compare_statistical_parity(
            case.label, case.first, case.second, simulations, seed=case.seed,
            maximum_rounds=case.maximum_rounds, backend=backend,
            modular=reference_counts, reference_seconds=modular_seconds,
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


def _observed_row(
    case, backend, simulations, oracle, modular_seconds, magnitudes, *,
    repeat_candidate,
):
    started = time.perf_counter()
    try:
        sample = _candidate_sample(
            backend, case.first, case.second, simulations, case.seed,
            case.maximum_rounds, case.decisions, case.context,
        )
    except _NativeUnavailable as error:
        return _row(
            case.label, backend, case.maximum_rounds, simulations,
            "NOT_RUN", modular_seconds=modular_seconds,
            detail=f"NOT_RUN:native-plan: {error}",
        )
    except KeyError as error:
        return _row(
            case.label, backend, case.maximum_rounds, simulations,
            "NOT_RUN", modular_seconds=modular_seconds,
            detail=f"NOT_RUN:decision-script:{_decision_key(error)} owner=P01",
        )
    except (AttributeError, TypeError) as error:
        return _row(
            case.label, backend, case.maximum_rounds, simulations,
            "INCOMPATIBLE", modular_seconds=modular_seconds,
            detail=(
                f"INCOMPATIBLE:candidate-sample:{type(error).__name__}: {error}"
            ),
        )
    except ValueError as error:
        message = str(error)
        if ("require the modular engine" in message
                or "optimized ports are pending" in message
                or "outside the one-against-one runtime" in message):
            tags = _admission_tags(case.first, case.second, backend)
            detail = f"INCOMPATIBLE:admission: {message}"
            if tags:
                detail += " tags=" + ",".join(tags)
            return _row(
                case.label, backend, case.maximum_rounds, simulations,
                "INCOMPATIBLE", modular_seconds=modular_seconds, detail=detail,
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
    candidate_seconds = time.perf_counter() - started
    executed = True

    mismatch = _shape_mismatch(oracle, sample, simulations)
    if mismatch is not None:
        return _row(
            case.label, backend, case.maximum_rounds, simulations,
            "DIVERGENCE", executed=True, modular_seconds=modular_seconds,
            candidate_seconds=candidate_seconds,
            detail=f"DIVERGENCE:batch-shape: {mismatch}",
        )

    if repeat_candidate and simulations > 1:
        try:
            repeat = _candidate_sample(
                backend, case.first, case.second, simulations, case.seed,
                case.maximum_rounds, case.decisions, case.context,
            )
        except Exception as error:
            return _row(
                case.label, backend, case.maximum_rounds, simulations,
                "DIVERGENCE", executed=True, modular_seconds=modular_seconds,
                candidate_seconds=candidate_seconds,
                detail=f"DIVERGENCE:exception:{type(error).__name__}: {error}",
            )
        if not _same_sample(sample, repeat):
            return _row(
                case.label, backend, case.maximum_rounds, simulations,
                "DIVERGENCE", executed=True, modular_seconds=modular_seconds,
                candidate_seconds=candidate_seconds,
                detail="DIVERGENCE:batch-nondeterministic",
            )

    try:
        comparisons, failure = _compare_case(
            magnitudes, oracle, sample, simulations,
        )
    except OutcomeCodeError as error:
        # Malformed outcome data is an own infrastructure error, not a
        # divergence and not an unresolved duel.
        return _row(
            case.label, backend, case.maximum_rounds, simulations,
            "NOT_RUN", executed=executed, modular_seconds=modular_seconds,
            candidate_seconds=candidate_seconds,
            detail=f"NOT_RUN:outcome-codes: {error}",
        )
    except ValueError as error:
        return _row(
            case.label, backend, case.maximum_rounds, simulations,
            "NOT_RUN", executed=executed, modular_seconds=modular_seconds,
            candidate_seconds=candidate_seconds,
            detail=f"NOT_RUN:case-definition: {error} owner=P01",
        )
    if failure is not None:
        return _row(
            case.label, backend, case.maximum_rounds, simulations,
            "DIVERGENCE", executed=executed, compared=True,
            modular_seconds=modular_seconds, candidate_seconds=candidate_seconds,
            comparisons=comparisons, detail=f"DIVERGENCE: {failure.detail}",
        )
    ranked = [item for item in comparisons if item.detail]
    tightest = max(ranked, key=_slack) if ranked else None
    return _row(
        case.label, backend, case.maximum_rounds, simulations,
        "PASS", executed=executed, compared=True, approved=True,
        modular_seconds=modular_seconds, candidate_seconds=candidate_seconds,
        comparisons=comparisons,
        detail=tightest.detail if tightest is not None else "",
    )


def _slack(item: MagnitudeComparison) -> float:
    """How close the magnitude came to failing (higher is tighter)."""
    return max(
        abs(left - right) - tolerance
        for left, right, tolerance in zip(
            item.modular_rates, item.candidate_rates, item.tolerances,
        )
    )


def _rate_sigma(row: ParityRow) -> float:
    """Worst winner-rate deviation of one row, in sigma units."""
    comparison = row.winner
    if comparison is None:
        return 0.0
    worst = 0.0
    for left, right in zip(comparison.modular_rates, comparison.candidate_rates):
        variance = (
            left * (1 - left) / row.simulations
            + right * (1 - right) / row.simulations
        )
        if variance > 0:
            worst = max(worst, abs(left - right) / np.sqrt(variance))
    return worst


def _unresolved_rate(row: ParityRow) -> float:
    comparison = row.winner
    if comparison is None or len(comparison.modular_rates) < 3:
        return 0.0
    return max(comparison.modular_rates[2], comparison.candidate_rates[2])


def escalation_plan(
    prepared: Iterable[tuple[ParityCase, int]], rows: Sequence[ParityRow], *,
    factor: int, sigma: float, unresolved: float, remaining: int | None,
):
    """Pick the cases that deserve a larger oracle sample, in priority order.

    A case is escalated when its first pass is suspicious (``sigma <=
    worst < 6`` — the band where doubling the sample decides between a defect
    and noise) or when its unresolved rate shows the timing-prone profile the
    flat gate is blind to.  Conclusive failures (six sigma and above) are not
    re-run.  Escalated sizes are ``base * factor``, allocated greedily in
    priority order until ``remaining`` duels run out.
    """
    prepared = tuple(prepared)
    sizes = {case.label: size for case, size in prepared}
    plan = []
    for case, size in prepared:
        own = [row for row in rows if row.case == case.label]
        if not own or not any(row.winner is not None for row in own):
            continue
        worst = max(_rate_sigma(row) for row in own)
        unresolved_rate = max(_unresolved_rate(row) for row in own)
        if not (sigma <= worst < 6.0 or unresolved_rate >= unresolved):
            continue
        plan.append((case, size * factor, worst, unresolved_rate))
    plan.sort(key=lambda item: (-item[2], -item[3]))
    chosen = []
    budget = remaining
    for case, new_size, _worst, _unresolved in plan:
        extra = new_size - sizes[case.label]
        if budget is not None:
            if extra > budget:
                continue
            budget -= extra
        chosen.append((case, new_size))
    return tuple(chosen)


def _expand(case: ParityCase, *, simulations: int, seed: int,
            maximum_rounds: int, horizons: Sequence[int] | None):
    """One entry per round limit; a bare case keeps its own label."""
    if horizons is None:
        return (
            ParityCase(
                label=case.label, first=case.first, second=case.second,
                maximum_rounds=maximum_rounds, simulations=simulations,
                seed=seed, magnitudes=case.magnitudes,
                decisions=case.decisions, context=case.context,
                blocked_by=case.blocked_by,
            ),
        )
    effective = tuple(sorted({h for h in horizons if 1 <= h <= maximum_rounds}))
    if not effective:
        raise ValueError("no truncation horizon fits the round budget")
    return tuple(
        ParityCase(
            label=f"{case.label}@rounds={horizon}", first=case.first,
            second=case.second, maximum_rounds=horizon,
            simulations=simulations, seed=seed, magnitudes=case.magnitudes,
            decisions=case.decisions, context=case.context,
            blocked_by=case.blocked_by,
        )
        for horizon in effective
    )


def run_parity(
    cases: Iterable[ParityCase], *,
    backends: Sequence[str] = ("numpy",),
    reference: str = "modular",
    candidate: str = "observed",
    simulations: int | None = None,
    seed: int | None = None,
    maximum_rounds: int | None = None,
    workers: int | str | None = 1,
    horizons: Sequence[int] | None = None,
    repeat_candidate: bool = False,
    cache: dict | None = None,
    escalate: bool = False,
    escalation_factor: int = 2,
    escalate_sigma: float = 3.0,
    escalate_unresolved: float = 0.01,
    max_modular_duels: int | None = None,
    on_progress: Callable[[], None] | None = None,
) -> ParityRun:
    """Run every case through the modular reference and the requested candidates.

    ``reference`` is ``"modular"`` (the oracle) or ``"numpy"`` (the cross layer,
    which certifies native against a NumPy sample).  ``candidate`` is
    ``"counts"`` (winner-only aggregate samples) or ``"observed"`` (per-duel
    rows, needed for ``rounds``/``wounds``/``condition``).  ``simulations``,
    ``seed`` and ``maximum_rounds`` override the per-case declaration.
    ``horizons`` expands each case at several round limits (round truncation).
    ``escalate`` re-certifies suspicious winner-only cases at
    ``escalation_factor`` times the sample, bounded by ``max_modular_duels``.
    ``cache`` reuses modular samples and is keyed by ``<label>@<simulations>``.
    ``backends=("modular",)`` executes only the reference and returns COMPLETED
    rows with compared/approved false. Readiness and compilation stay with the caller.
    """
    cases = tuple(cases)
    backends = tuple(backends)
    if reference not in {"modular", "numpy"}:
        raise ValueError(f"unknown parity reference: {reference}")
    if candidate not in {"counts", "observed"}:
        raise ValueError(f"unknown parity candidate surface: {candidate}")
    for backend in backends:
        if backend not in {"modular", "numpy", "native"}:
            raise ValueError(f"unknown optimized backend: {backend}")
    if "modular" in backends and (backends != ("modular",) or reference != "modular"):
        raise ValueError("modular-only execution cannot be mixed with candidate backends")
    if backends == ("modular",) and escalate:
        raise ValueError("modular-only execution has no comparisons to escalate")
    if escalate and (candidate != "counts" or reference != "modular"):
        raise ValueError(
            "escalation is defined for modular winner-only samples"
        )
    if reference == "numpy" and candidate != "counts":
        raise ValueError("the NumPy reference compares aggregate counts only")
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

    worker_counts = tuple(
        resolve_oracle_workers(workers, item.simulations, item.maximum_rounds)
        if reference == "modular" else None
        for item in expanded
    )
    rows: list[ParityRow] = []
    modular_duels = 0
    with ExitStack() as stack:
        pool_size = max((count or 1 for count in worker_counts), default=1)
        executor = (
            stack.enter_context(ProcessPoolExecutor(max_workers=pool_size))
            if pool_size > 1 else None
        )
        for item, count in zip(expanded, worker_counts):
            item_rows, duels = _case_rows(
                item, item.simulations, backends=backends, reference=reference,
                candidate=candidate, workers=count, executor=executor,
                cache=cache, repeat_candidate=repeat_candidate,
            )
            rows.extend(item_rows)
            modular_duels += duels
            if on_progress is not None and item_rows:
                on_progress()

        if escalate and expanded:
            base_duels = (
                sum(item.simulations for item in expanded)
                if reference == "modular" else 0
            )
            remaining = (
                None if max_modular_duels is None
                else max_modular_duels - base_duels
            )
            plan = escalation_plan(
                tuple((item, item.simulations) for item in expanded), rows,
                factor=escalation_factor, sigma=escalate_sigma,
                unresolved=escalate_unresolved, remaining=remaining,
            )
            for item, new_size in plan:
                replacement, duels = _case_rows(
                    item, new_size, backends=backends, reference=reference,
                    candidate=candidate,
                    workers=resolve_oracle_workers(
                        workers, new_size, item.maximum_rounds),
                    executor=executor, cache=cache, repeat_candidate=False,
                )
                modular_duels += duels - item.simulations
                rows = [row for row in rows if row.case != item.label]
                rows.extend(replace(row, escalated=True) for row in replacement)
                if on_progress is not None:
                    on_progress()

    return ParityRun(rows=tuple(rows), modular_duels=modular_duels)


__all__ = (
    "MagnitudeComparison",
    "OutcomeCodeError",
    "ParityCase",
    "ParityRow",
    "ParityRun",
    "TRUNCATION_HORIZONS",
    "escalation_plan",
    "run_parity",
    "statistical_result",
)
