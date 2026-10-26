"""Statistical parity battery: preparation, clause bookkeeping and reporting.

P03 (statistical adaptation).  The modular engine is the correctness oracle;
each case is a declared scenario — fighters, context, decisions, seed, sample
width and horizon.  Parity is decided on terminal outcome distributions, never
on internal events: no witness, counter, flag, hash or positive control is
required to execute or approve a case.

This module owns what is battery-specific: catalogue validation, the declared
input limits, compilation, clause keys, and the report with its coverage and
stage accounting.  Execution is the shared :func:`run_parity`; the caller
prepares here, runs once, and builds one report from the rows.  A precompiled
case never reaches this path, so no compiler fallback exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from mordheim_construction.compiler import compile_fighter
from mordheim_core.dice import ScriptedDecisions
from mordheim_knowledge.loader import knowledge_root

from ._battery_cases import (
    VARIANTS,
    VARIANT_KEYS,
    case_magnitudes,
    input_limit,
    required_variants,
    resolve_context,
)
from ._runner import (
    MagnitudeComparison,
    ParityCase,
    ParityRow,
    _NativeUnavailable,
    _native_engine,
)

#: Worst-first order used to merge the per-backend rows of one case.
_STATUS_SEVERITY = {
    "DIVERGENCE": 0,
    "NOT_RUN": 1,
    "INCOMPATIBLE": 2,
    "PASS": 3,
}

#: Prefix of a compiled-input entry in the caller's ``reuse`` mapping.
_COMPILED = "compiled"


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


def prepare_cases(
    cases: Sequence, *, backend: str, rows: int | None, root=None,
    reuse: dict | None = None,
) -> tuple[tuple[ParityCase, ...], dict[str, BatteryCaseResult]]:
    """Prepare the catalogue's cases for :func:`run_parity`.

    Returns the ready cases and, per case id, the result of a preparation that
    could not run (input limit, invalid definition, compile failure, absent
    native backend).  Compiled inputs are cached in ``reuse`` under
    ``("compiled", case, rows)``; the modular sample is cached there by the
    runner under ``<case>@<rows>``.  Nothing is read from disk.
    """
    knowledge = root or knowledge_root()
    prepared: list[ParityCase] = []
    failures: dict[str, BatteryCaseResult] = {}
    for case in cases:
        effective_rows = int(getattr(case, "rows", 64)) if rows is None else int(rows)
        limit = input_limit(case)
        if limit is not None:
            failures[str(case.id)] = _result(
                case, backend, "INCOMPATIBLE", rows=effective_rows,
                detail=f"INCOMPATIBLE:{limit}", blocked_by=limit,
            )
            continue
        try:
            _variant(case)
            magnitudes = tuple(case_magnitudes(case))
        except ValueError as error:
            failures[str(case.id)] = _result(
                case, backend, "NOT_RUN", rows=effective_rows,
                detail=f"NOT_RUN:case-definition: {error} owner=P01",
            )
            continue
        if "winner" not in magnitudes:
            failures[str(case.id)] = _result(
                case, backend, "NOT_RUN", rows=effective_rows,
                detail=(
                    "NOT_RUN:case-definition: winner must always be compared "
                    "owner=P01"
                ),
            )
            continue

        key = (_COMPILED, str(case.id), effective_rows)
        compiled = None if reuse is None else reuse.get(key)
        if compiled is None:
            try:
                first = compile_fighter(case.first, knowledge)
                second = compile_fighter(case.second, knowledge)
                context = resolve_context(getattr(case, "context", None), knowledge)
            except Exception as error:  # an invalid case is not a divergence
                failures[str(case.id)] = _result(
                    case, backend, "NOT_RUN", rows=effective_rows,
                    detail=f"NOT_RUN:compile:{type(error).__name__}: {error}",
                )
                continue
            if reuse is not None:
                reuse[key] = (first, second, context)
        else:
            first, second, context = compiled

        if backend == "native":
            try:
                _native_engine()
            except _NativeUnavailable as error:
                failures[str(case.id)] = _result(
                    case, backend, "NOT_RUN", rows=effective_rows,
                    detail=f"NOT_RUN:native-stale: {error}",
                )
                continue

        prepared.append(ParityCase(
            label=str(case.id),
            first=first,
            second=second,
            maximum_rounds=int(getattr(case, "maximum_rounds", 50)),
            simulations=effective_rows,
            seed=int(getattr(case, "seed", 2026)),
            magnitudes=magnitudes,
            decisions=ScriptedDecisions(dict(getattr(case, "decisions", {}) or {})),
            context=context,
        ))
    return tuple(prepared), failures


def battery_results(
    cases: Sequence, rows: Sequence[ParityRow],
    failures: dict[str, BatteryCaseResult] | None = None,
) -> tuple[BatteryCaseResult, ...]:
    """Merge one run's rows with the preparation failures, in catalogue order."""
    failures = failures or {}
    by_case = {row.case: row for row in rows}
    results = []
    for case in cases:
        failure = failures.get(str(case.id))
        if failure is not None:
            results.append(failure)
            continue
        row = by_case[str(case.id)]
        results.append(_result(
            case, row.backend, row.status, rows=row.simulations,
            detail=row.detail, modular_seconds=row.modular_seconds,
            candidate_seconds=row.candidate_seconds, executed=row.executed,
            compared=row.compared, approved=row.approved,
            comparisons=row.comparisons, blocked_by=row.blocked_by,
        ))
    return tuple(results)


def _worst_by_case(
    results: Iterable[BatteryCaseResult],
) -> tuple[BatteryCaseResult, ...]:
    worst: dict[str, BatteryCaseResult] = {}
    for result in results:
        current = worst.get(result.case)
        if (current is None
                or _STATUS_SEVERITY[result.status] < _STATUS_SEVERITY[current.status]):
            worst[result.case] = result
    return tuple(worst.values())


def _by_status(results: Iterable[BatteryCaseResult], status: str) -> tuple[str, ...]:
    return tuple(result.case for result in results if result.status == status)


def battery_report(
    results: Sequence[BatteryCaseResult], cases: Sequence, *,
    profile: str | None,
) -> BatteryReport:
    """Build the battery certificate from every backend row of one run.

    Every per-backend row survives in ``results``; the case-level tuples carry
    the worst status of each case, so ``--backend all`` certifies a case only
    when every requested backend passed it.  ``complete``/``accepted`` keep
    their execution meaning and are never ``all([])``.
    """
    results = tuple(results)
    merged = _worst_by_case(results)
    represented = {str(case.variant) for case in cases}
    missing: tuple[str, ...] = ()
    if profile is not None:
        missing = tuple(
            variant for variant in required_variants(profile)
            if variant not in represented
        )
    bad = (
        _by_status(merged, "DIVERGENCE")
        + _by_status(merged, "INCOMPATIBLE")
        + _by_status(merged, "NOT_RUN")
    )
    complete = bool(results) and not bad and not missing
    return BatteryReport(
        complete=complete,
        accepted=profile is not None and complete,
        scope="profile" if profile is not None else "provided",
        profile=profile,
        results=results,
        passed=_by_status(merged, "PASS"),
        divergences=_by_status(merged, "DIVERGENCE"),
        incompatible=_by_status(merged, "INCOMPATIBLE"),
        not_run=_by_status(merged, "NOT_RUN"),
        missing_variants=missing,
    )


__all__ = (
    "MagnitudeComparison",
    "BatteryCaseResult",
    "BatteryReport",
    "battery_report",
    "battery_results",
    "prepare_cases",
)
