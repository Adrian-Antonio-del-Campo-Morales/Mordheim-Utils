"""Statistical parity battery: sample real duels in both engines and compare.

P03 (statistical adaptation).  The modular engine is the correctness oracle;
each case is a declared scenario — fighters, context, decisions, seed, sample
width and horizon — executed by both engines.  Parity is decided on terminal
outcome distributions, never on internal events: no witness, counter, flag,
hash or positive control is required to execute or approve a case.

``winner`` is always compared (first win, second win, unresolved) with the
six-sigma gate of ``_statistical``.  ``rounds``, ``wounds`` and ``condition``
are compared when the case declares them; both sampling paths publish them
already, so they are real observations, not instrumentation.  A real input
limitation — initial state the API cannot express, per-row decisions — is
reported as ``INCOMPATIBLE`` with its cause and is never replaced by a weaker
scenario.  Sensitivity of a rule pair needs a later campaign: this module
reports statistical parity, not semantic coverage.

Each engine's winner convention is validated before normalisation.  A code
outside it is malformed data (``NOT_RUN:outcome-codes``), an own error: it is
never folded into the unresolved category and never dropped from the sample.
"""
from __future__ import annotations

import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from mordheim_combat.modular.duel import simulate_duel_observed
from mordheim_combat.modular.parallel import chunk_ranges, resolve_oracle_workers
from mordheim_combat.vectorized import simulate_batch_observed
from mordheim_construction.compiler import compile_fighter
from mordheim_core.dice import ScriptedDecisions
from mordheim_core.models import ObservedDuelResult
from mordheim_knowledge.loader import knowledge_root

from ._battery_cases import (
    VARIANTS,
    VARIANT_KEYS,
    case_magnitudes,
    input_limit,
    required_variants,
    resolve_context,
)
from ._statistical import (
    OUTCOME_LABELS,
    compare_outcome_rates,
    outcome_counts,
    six_sigma_tolerance,
)

#: Worst-first order used when several candidate backends judge one case.  A
#: missing capability never becomes a pass because a sibling backend compared.
_STATUS_SEVERITY = {
    "DIVERGENCE": 0,
    "NOT_RUN": 1,
    "INCOMPATIBLE": 2,
    "PASS": 3,
}


class _NativeUnavailable(RuntimeError):
    """The native extension is absent, stale or cannot run this plan."""


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
class BatteryCaseResult:
    case: str
    level: str
    variant: str
    obligation: str
    backend: str
    status: str
    keys: tuple[str, ...]
    observables: tuple[str, ...]
    rows: int
    #: Declared sample parameters, carried into the report so a certificate
    #: names the seed and horizon it was prepared for.
    seed: int | None = None
    horizon: int | None = None
    #: Stages actually reached, recorded where they happen: a comparison that
    #: never obtained both samples is not execution evidence, and a divergent
    #: distribution is a performed comparison that was not approved.
    executed: bool = False
    compared: bool = False
    approved: bool = False
    #: Magnitudes actually compared (in comparison order).
    magnitudes: tuple[str, ...] = ()
    comparisons: tuple[MagnitudeComparison, ...] = ()
    modular_seconds: float = 0.0
    candidate_seconds: float = 0.0
    detail: str = ""
    #: The real input limitation that prevented execution, when one exists.
    blocked_by: str | None = None


@dataclass(frozen=True, slots=True)
class BatteryReport:
    complete: bool
    accepted: bool
    scope: str
    profile: str | None
    results: tuple[BatteryCaseResult, ...]
    passed: tuple[str, ...]
    divergences: tuple[str, ...]
    incompatible: tuple[str, ...]
    not_run: tuple[str, ...]
    missing_variants: tuple[str, ...]


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


#: Terminal outcome codes each engine actually publishes.  The oracle uses
#: 0/1/2; the optimized candidate uses 1/-1/0.  ``0`` means opposite things in
#: the two conventions, so each sample is validated against its own set before
#: any mapping happens.
_ORACLE_WINNER_CODES = frozenset({0, 1, 2})
_CANDIDATE_WINNER_CODES = frozenset({-1, 0, 1})


class OutcomeCodeError(ValueError):
    """A sample published a winner code its engine's convention does not define."""


def _validated_winner_codes(values, allowed: frozenset[int], source: str) -> np.ndarray:
    """Return the sample only when every code belongs to ``source``'s convention.

    An unknown code is malformed data: it is neither an unresolved duel nor a
    fourth category, and silently normalising it would compare a distribution
    the engine never produced.
    """
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
    """Name the effect tags the candidate's admission gate refuses.

    The gate is engine data (``kernel.pending_capabilities``); this only reads
    it so the report names the refused behaviour instead of calling every
    refusal a construction defect.  Nothing is bypassed or forced: the engine
    still refuses the plan and the case stays ``INCOMPATIBLE``.
    """
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
    label: str, categories: Sequence, left: Counter, right: Counter, rows: int,
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
    detail = ""
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
    if worst is not None:
        detail = worst[1]
    return MagnitudeComparison(
        magnitude="winner",
        modular_rates=modular_rates,
        candidate_rates=candidate_rates,
        tolerances=tolerances,
        passed=passed,
        detail=detail,
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
    fields = (
        "winner", "rounds", "first_wounds", "second_wounds",
        "first_condition", "second_condition",
    )
    for name in fields:
        if not np.array_equal(np.asarray(getattr(left, name)), np.asarray(getattr(right, name))):
            return False
    return True


def _decision_key(error: KeyError) -> str:
    messages = [str(item) for item in error.args]
    text = " ".join(messages) or "unknown"
    return text.split("for ")[-1] if "for " in text else text


def _variant(case):
    variant = VARIANTS.get(case.variant)
    if variant is None:
        raise ValueError(f"case {case.id} names an unknown variant {case.variant!r}")
    return variant


def _result(
    case, backend: str, status: str, *, rows: int, detail: str = "",
    modular_seconds: float = 0.0, candidate_seconds: float = 0.0,
    executed: bool = False, compared: bool = False, approved: bool = False,
    comparisons: tuple[MagnitudeComparison, ...] = (), blocked_by: str | None = None,
) -> BatteryCaseResult:
    return BatteryCaseResult(
        case=str(case.id),
        level=str(case.level),
        variant=str(case.variant),
        obligation=str(case.variant).split(".")[0],
        backend=backend,
        status=status,
        keys=tuple(dict.fromkeys(VARIANT_KEYS.get(case.variant, ()))),
        observables=tuple(getattr(case, "observables", ()) or ()),
        rows=rows,
        seed=int(getattr(case, "seed", 2026)),
        horizon=int(getattr(case, "maximum_rounds", 50)),
        executed=executed,
        compared=compared,
        approved=approved,
        magnitudes=tuple(item.magnitude for item in comparisons),
        comparisons=comparisons,
        modular_seconds=modular_seconds,
        candidate_seconds=candidate_seconds,
        detail=detail,
        blocked_by=blocked_by,
    )


def _compare_case(magnitudes: Sequence[str], oracle, candidate, rows: int) -> tuple[
    tuple[MagnitudeComparison, ...], MagnitudeComparison | None,
]:
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


def _oracle_sample(first, second, rows: int, *, seed: int, maximum_rounds: int,
                   decisions, context, workers: int | None = None, executor=None):
    """Keep the sequential oracle's seed+i rows, including their original order."""
    if executor is None or workers is None or workers < 2:
        return simulate_duel_observed(
            first, second, rows, seed=seed, maximum_rounds=maximum_rounds,
            decisions=decisions, context=context,
        )
    futures = [
        executor.submit(
            simulate_duel_observed, first, second, count, seed=seed + start,
            maximum_rounds=maximum_rounds, decisions=decisions, context=context,
        )
        for start, count in chunk_ranges(rows, workers)
    ]
    try:
        samples = [future.result() for future in futures]
    finally:
        for future in futures:
            future.cancel()
    fields = (
        "winner", "resolution_rounds", "first_wounds", "second_wounds",
        "first_condition", "second_condition",
    )
    return ObservedDuelResult(
        **{name: np.concatenate([getattr(sample, name) for sample in samples])
           for name in fields},
        simulations=rows, maximum_rounds=maximum_rounds,
    )


def _run_case(case, *, backend: str, rows: int | None, root,
              reuse: dict | None = None, workers: int | None = None,
              executor=None) -> BatteryCaseResult:
    effective_rows = int(getattr(case, "rows", 64)) if rows is None else int(rows)
    limit = input_limit(case)
    if limit is not None:
        return _result(
            case, backend, "INCOMPATIBLE", rows=effective_rows,
            detail=f"INCOMPATIBLE:{limit}", blocked_by=limit,
        )
    try:
        _variant(case)
        magnitudes = tuple(case_magnitudes(case))
    except ValueError as error:
        return _result(case, backend, "NOT_RUN", rows=effective_rows,
                       detail=f"NOT_RUN:case-definition: {error} owner=P01")
    if "winner" not in magnitudes:
        return _result(
            case, backend, "NOT_RUN", rows=effective_rows,
            detail="NOT_RUN:case-definition: winner must always be compared owner=P01",
        )

    # Compile once and sample the modular oracle once per case, so a second
    # candidate (``--backend all``) compares against the same evidence.  The key
    # carries the sample width: a different width is different evidence.
    key = f"{case.id}@{effective_rows}"
    prepared = None if reuse is None else reuse.get(key)
    if prepared is None:
        try:
            first = compile_fighter(case.first, root)
            second = compile_fighter(case.second, root)
            context = resolve_context(getattr(case, "context", None), root)
        except Exception as error:  # the compiler is shared; an invalid case is not a divergence
            return _result(
                case, backend, "NOT_RUN", rows=effective_rows,
                detail=f"NOT_RUN:compile:{type(error).__name__}: {error}",
            )

    decisions = ScriptedDecisions(dict(getattr(case, "decisions", {}) or {}))
    seed = int(getattr(case, "seed", 2026))
    maximum_rounds = int(getattr(case, "maximum_rounds", 50))

    if backend == "native":
        try:
            _native_engine()
        except _NativeUnavailable as error:
            return _result(case, backend, "NOT_RUN", rows=effective_rows,
                           detail=f"NOT_RUN:native-stale: {error}")

    if prepared is None:
        started = time.perf_counter()
        try:
            oracle = _oracle_sample(
                first, second, effective_rows, seed=seed,
                maximum_rounds=maximum_rounds, decisions=decisions, context=context,
                workers=workers, executor=executor,
            )
        except KeyError as error:
            return _result(case, backend, "NOT_RUN", rows=effective_rows,
                           detail=f"NOT_RUN:decision-script:{_decision_key(error)} owner=P01")
        except Exception as error:
            return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                           detail=f"DIVERGENCE:exception:{type(error).__name__}: {error}")
        modular_seconds = time.perf_counter() - started
        if reuse is not None:
            reuse[key] = (first, second, context, oracle)
    else:
        first, second, context, oracle = prepared
        # The oracle sample is measured once per case; reusing it is not a new
        # measurement, so a reused row never reports a modular time of its own.
        modular_seconds = 0.0

    started = time.perf_counter()
    try:
        candidate = _candidate_sample(
            backend, first, second, effective_rows, seed, maximum_rounds,
            decisions, context,
        )
    except _NativeUnavailable as error:
        return _result(case, backend, "NOT_RUN", rows=effective_rows,
                       detail=f"NOT_RUN:native-plan: {error}",
                       modular_seconds=modular_seconds)
    except KeyError as error:
        return _result(case, backend, "NOT_RUN", rows=effective_rows,
                       detail=f"NOT_RUN:decision-script:{_decision_key(error)} owner=P01",
                       modular_seconds=modular_seconds)
    except (AttributeError, TypeError) as error:
        return _result(
            case, backend, "INCOMPATIBLE", rows=effective_rows,
            detail=f"INCOMPATIBLE:candidate-sample:{type(error).__name__}: {error}",
            modular_seconds=modular_seconds,
        )
    except ValueError as error:
        message = str(error)
        if ("require the modular engine" in message
                or "optimized ports are pending" in message
                or "outside the one-against-one runtime" in message):
            # The engine refused the compiled plan, not the battery its inputs:
            # name the refused tags so the limit is attributable.
            tags = _admission_tags(first, second, backend)
            detail = f"INCOMPATIBLE:admission: {message}"
            if tags:
                detail += " tags=" + ",".join(tags)
            return _result(
                case, backend, "INCOMPATIBLE", rows=effective_rows,
                detail=detail,
                modular_seconds=modular_seconds,
            )
        return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                       detail=f"DIVERGENCE:exception:ValueError: {message}",
                       modular_seconds=modular_seconds)
    except Exception as error:
        return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                       detail=f"DIVERGENCE:exception:{type(error).__name__}: {error}",
                       modular_seconds=modular_seconds)
    candidate_seconds = time.perf_counter() - started
    executed = True

    mismatch = _shape_mismatch(oracle, candidate, effective_rows)
    if mismatch is not None:
        return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                       detail=f"DIVERGENCE:batch-shape: {mismatch}",
                       executed=executed, modular_seconds=modular_seconds,
                       candidate_seconds=candidate_seconds)

    if effective_rows > 1:
        try:
            repeat = _candidate_sample(
                backend, first, second, effective_rows, seed, maximum_rounds,
                decisions, context,
            )
        except Exception as error:
            return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                           detail=f"DIVERGENCE:exception:{type(error).__name__}: {error}",
                           executed=executed, modular_seconds=modular_seconds,
                           candidate_seconds=candidate_seconds)
        if not _same_sample(candidate, repeat):
            return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                           detail="DIVERGENCE:batch-nondeterministic",
                           executed=executed, modular_seconds=modular_seconds,
                           candidate_seconds=candidate_seconds)

    try:
        comparisons, failure = _compare_case(
            magnitudes, oracle, candidate, effective_rows,
        )
    except OutcomeCodeError as error:
        # Malformed outcome data is an own infrastructure error, not a
        # divergence and not an unresolved duel.
        return _result(
            case, backend, "NOT_RUN", rows=effective_rows,
            detail=f"NOT_RUN:outcome-codes: {error}",
            executed=executed, modular_seconds=modular_seconds,
            candidate_seconds=candidate_seconds,
        )
    except ValueError as error:
        return _result(
            case, backend, "NOT_RUN", rows=effective_rows,
            detail=f"NOT_RUN:case-definition: {error} owner=P01",
            executed=executed, modular_seconds=modular_seconds,
            candidate_seconds=candidate_seconds,
        )
    if failure is not None:
        return _result(
            case, backend, "DIVERGENCE", rows=effective_rows,
            detail=f"DIVERGENCE: {failure.detail}",
            executed=executed, compared=True,
            modular_seconds=modular_seconds, candidate_seconds=candidate_seconds,
            comparisons=comparisons,
        )
    ranked = [item for item in comparisons if item.detail]
    tightest = max(ranked, key=_slack) if ranked else None
    detail = tightest.detail if tightest is not None else ""
    return _result(
        case, backend, "PASS", rows=effective_rows, detail=detail,
        executed=executed, compared=True, approved=True,
        modular_seconds=modular_seconds, candidate_seconds=candidate_seconds,
        comparisons=comparisons,
    )


def _slack(item: MagnitudeComparison) -> float:
    """How close the magnitude came to failing (higher is tighter)."""
    return max(
        abs(left - right) - tolerance
        for left, right, tolerance in zip(
            item.modular_rates, item.candidate_rates, item.tolerances,
        )
    )


def _by_status(results: Iterable[BatteryCaseResult], status: str) -> tuple[str, ...]:
    return tuple(result.case for result in results if result.status == status)


def combine_reports(
    reports: Sequence[BatteryReport], *, profile: str | None = None,
    backend: str = "all",
) -> BatteryReport:
    """Merge per-backend reports over the same case set into one certificate.

    Every per-backend row survives in ``results`` (the report separates coverage
    per backend from them), while the case-level tuples carry the worst status
    of each case: ``--backend all`` certifies a case only when every requested
    backend passed it.  ``complete``/``accepted`` are the conjunction of the
    merged runs, never ``all([])``.
    """
    reports = tuple(reports)
    if not reports:
        raise ValueError("combine_reports needs at least one report")
    worst: dict[str, BatteryCaseResult] = {}
    for report in reports:
        for result in report.results:
            current = worst.get(result.case)
            if (current is None
                    or _STATUS_SEVERITY[result.status] < _STATUS_SEVERITY[current.status]):
                worst[result.case] = result
    merged = tuple(worst.values())
    missing = tuple(dict.fromkeys(
        variant for report in reports for variant in report.missing_variants
    ))
    return BatteryReport(
        complete=all(report.complete for report in reports),
        accepted=all(report.accepted for report in reports),
        scope="profile" if any(report.scope == "profile" for report in reports)
        else "provided",
        profile=profile if profile is not None else reports[0].profile,
        results=tuple(result for report in reports for result in report.results),
        passed=_by_status(merged, "PASS"),
        divergences=_by_status(merged, "DIVERGENCE"),
        incompatible=_by_status(merged, "INCOMPATIBLE"),
        not_run=_by_status(merged, "NOT_RUN"),
        missing_variants=missing,
    )


def run_battery(
    cases: Sequence, *, profile: str | None = None, backend: str = "numpy",
    rows: int | None = None, root=None, reuse: dict | None = None,
    workers: int | str | None = 1,
) -> BatteryReport:
    """Run ``cases`` through the real oracle and the selected candidate.

    ``rows`` overrides the case's declared sample width; it never changes case
    identity or the quick/complete/deep nesting.  ``root`` defaults to the
    knowledge root; compilation is done once per case and excluded from both
    timing fields, as P04 measures it separately.

    ``profile`` makes coverage meaningful: every required duel variant of that
    profile must be represented.  Without it the run is a diagnostic subset and
    ``accepted`` is always false.

    ``reuse`` is the same-process cache P03 passes when it runs several
    candidates over one case set: it holds the compiled fighters, the resolved
    context and the modular sample of each ``<case>@<rows>`` key.  It is never
    read from disk, so a saved certificate can neither age into evidence nor
    skip a declared input.

    ``workers`` uses the historical oracle policy: 1 is sequential, explicit
    counts are capped to CPU availability, and auto pools only large samples.
    One pool serves all cases; candidates keep their existing batch execution.
    """
    if backend not in {"numpy", "native"}:
        raise ValueError(f"unknown battery backend: {backend}")
    if rows is not None and int(rows) < 1:
        raise ValueError("rows must be positive")
    if profile is not None and profile not in ("quick", "complete", "deep"):
        raise ValueError(f"unknown battery profile: {profile}")
    if workers is not None and str(workers).casefold() != "auto" and int(workers) < 1:
        raise ValueError("workers must be positive or auto")
    knowledge = root or knowledge_root()
    worker_counts = tuple(
        resolve_oracle_workers(
            workers, int(case.rows) if rows is None else int(rows),
            int(case.maximum_rounds),
        )
        for case in cases
    )
    with ExitStack() as stack:
        pool_size = max((count or 1 for count in worker_counts), default=1)
        executor = (
            stack.enter_context(ProcessPoolExecutor(max_workers=pool_size))
            if pool_size > 1 else None
        )
        results = tuple(
            _run_case(
                case, backend=backend, rows=rows, root=knowledge, reuse=reuse,
                workers=count, executor=executor,
            )
            for case, count in zip(cases, worker_counts)
        )

    represented = {str(case.variant) for case in cases}
    if profile is None:
        missing: tuple[str, ...] = ()
    else:
        missing = tuple(
            variant for variant in required_variants(profile)
            if variant not in represented
        )

    bad = (
        _by_status(results, "DIVERGENCE")
        + _by_status(results, "INCOMPATIBLE")
        + _by_status(results, "NOT_RUN")
    )
    complete = bool(results) and not bad and not missing
    accepted = profile is not None and complete
    return BatteryReport(
        complete=complete,
        accepted=accepted,
        scope="profile" if profile is not None else "provided",
        profile=profile,
        results=results,
        passed=_by_status(results, "PASS"),
        divergences=_by_status(results, "DIVERGENCE"),
        incompatible=_by_status(results, "INCOMPATIBLE"),
        not_run=_by_status(results, "NOT_RUN"),
        missing_variants=missing,
    )


__all__ = (
    "MagnitudeComparison",
    "BatteryCaseResult",
    "BatteryReport",
    "combine_reports",
    "run_battery",
)
