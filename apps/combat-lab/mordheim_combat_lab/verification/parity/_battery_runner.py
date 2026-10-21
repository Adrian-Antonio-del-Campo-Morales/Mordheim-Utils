"""Executable parity battery: compile once, sample both engines, compare.

P02 of the parity-battery renovation.  The modular engine is the only
correctness oracle; a case is a declared behaviour, a seed and a sample width,
never a hand-maintained tuple of rolls.  This module owns execution,
comparison and the report; ``_battery_cases.py`` owns the catalog.

Preparation contract (P00 revision 4 + A8–A10):

* a case names one ``variant``; its witness, kind and predicates come from the
  catalog, never from the case;
* ``condition``/``wounds`` are direct-result witnesses only in B07/B15, while
  ``leadership-test-value``/``psychology-dice`` are measured direct results in
  B11/B14 (A9);
* a focused positive has no ``positive_control``; its negative references it and
  the pair is resolved before approval (A10);
* a positive control that does not activate is ``NOT_ACTIVATED``, never a
  divergence between engines;
* no presence-of-category rule substitutes for a witness contrast.
"""
from __future__ import annotations

import math
import time
from collections import Counter
from dataclasses import dataclass, replace
from typing import Iterable, Mapping, Sequence

import numpy as np

from mordheim_combat.modular.duel import simulate_duel_observed
from mordheim_combat.phases import Condition
from mordheim_combat.vectorized import simulate_batch_observed
from mordheim_construction.compiler import compile_fighter
from mordheim_core.dice import ScriptedDecisions
from mordheim_knowledge.loader import knowledge_root

from ._battery_cases import VARIANTS, VARIANT_KEYS, required_variants

#: The four resources the candidate publishes today.  This is not the full
#: observable vocabulary (that lives in ``_battery_cases``).
RESOURCES_OBSERVED = ("lucky-charm", "force-of-will", "mark-of-the-old-ones", "luck")

#: Result states, in the vocabulary P03's report consumes.
_STATUSES = ("PASS", "DIVERGENCE", "INCOMPATIBLE", "NOT_ACTIVATED", "NOT_RUN")

#: Outcomes.  ``wounds``/``condition`` are direct-result witnesses only in
#: B07/B15 (A9); here they are compared as distributions like any outcome.
_OUTCOMES = frozenset({"winner", "rounds", "wounds", "condition"})

#: Default owner of an observation the candidate does not publish.
_WITNESS_OWNERS = {
    "lucky-charm": "G06",
    "force-of-will": "G06",
    "mark-of-the-old-ones": "G06",
    "luck": "G06",
    "fear-hit-sixes": "G05/G06",
    "fear-test-skipped": "G05/G06",
    "psychology-test-skipped": "G05/G06",
    "psychology-dice": "G05/G06",
    "stupidity-failed": "G05/G06",
    "animosity-failed": "G05/G06",
    "feral-instinct-failed": "G05/G06",
    "leadership-first-failed": "G05/G06",
    "leadership-auto-pass": "G05/G06",
    "leadership-test-value": "G05/G06",
    "poetry-first-leadership": "G05/G06",
    "acting-order": "G03/G06",
    "equipment": "G02/G06",
}


class _NativeUnavailable(RuntimeError):
    """The native extension is absent, stale or cannot run this plan."""


class _WitnessUnavailable(RuntimeError):
    """The selected engine does not publish this witness per row."""

    def __init__(self, name: str, owner: str):
        super().__init__(name)
        self.name = name
        self.owner = owner


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
    witness: str | None = None
    witness_kind: str | None = None
    witness_rate: float | None = None
    expect: str = "present"
    expect_value: int | str | None = None
    comparison: str = "witness"
    coupling: str = "unverified"
    detail: str = ""
    modular_seconds: float = 0.0
    candidate_seconds: float = 0.0


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
    not_activated: tuple[str, ...]
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


def _winner_codes(values: np.ndarray) -> np.ndarray:
    """Map the candidate's 1/-1/0 onto the oracle's 0/1/2 convention."""
    values = np.asarray(values)
    return np.select(
        (values == 1, values == -1), (0, 1), default=2,
    ).astype(np.int8)


def _observable_pairs(name: str, oracle, candidate) -> list[tuple[str, np.ndarray, np.ndarray]]:
    if name == "winner":
        return [("winner", np.asarray(oracle.winner), _winner_codes(candidate.winner))]
    if name == "rounds":
        return [("rounds", np.asarray(oracle.resolution_rounds), np.asarray(candidate.rounds))]
    if name == "wounds":
        return [
            ("wounds[first]", np.asarray(oracle.first_wounds), np.asarray(candidate.first_wounds)),
            ("wounds[second]", np.asarray(oracle.second_wounds), np.asarray(candidate.second_wounds)),
        ]
    if name == "condition":
        return [
            ("condition[first]", np.asarray(oracle.first_condition), np.asarray(candidate.first_condition)),
            ("condition[second]", np.asarray(oracle.second_condition), np.asarray(candidate.second_condition)),
        ]
    raise KeyError(name)


def _row_values(name: str, observation) -> np.ndarray:
    """Return one value per row for ``name``, or raise ``_WitnessUnavailable``.

    Outcomes are published by both sampling paths.  Other witnesses are read
    from an attribute or a per-fighter resource tuple; a name the selected
    engine does not expose is a declared dependency, not an error.
    """
    if name == "condition":
        return np.concatenate((
            np.asarray(observation.first_condition),
            np.asarray(observation.second_condition),
        ))
    if name == "wounds":
        return np.concatenate((
            np.asarray(observation.first_wounds),
            np.asarray(observation.second_wounds),
        ))
    attribute = name.replace("-", "_")
    if hasattr(observation, attribute):
        return np.asarray(getattr(observation, attribute))
    for side in ("first_resources", "second_resources"):
        for resource_name, values in getattr(observation, side, ()) or ():
            if resource_name == name:
                return np.asarray(values)
    raise _WitnessUnavailable(name, _WITNESS_OWNERS.get(name, "G02/G06"))


def _predicate(kind: str, predicate: str, values: np.ndarray, expected) -> tuple[bool, float]:
    """Evaluate one typed predicate; return (activated, rate of rows)."""
    values = np.asarray(values)
    if kind == "counter":
        counts = values.astype(np.int64, copy=False)
        if predicate == "count>0":
            mask = counts > 0
        elif predicate == "count==0":
            mask = counts == 0
        else:
            raise ValueError(f"unknown counter predicate: {predicate}")
    elif kind == "flag":
        flags = values.astype(bool, copy=False)
        if predicate == "flag-true":
            mask = flags
        elif predicate == "flag-false":
            mask = ~flags
        else:
            raise ValueError(f"unknown flag predicate: {predicate}")
    elif kind in {"category", "direct-result"}:
        if expected is None:
            raise ValueError(f"{kind} witness needs an expected value")
        try:
            mask = values == expected
        except (TypeError, ValueError):
            mask = np.array([str(value) == str(expected) for value in values])
        if predicate in {"class-equals", "value-equals"}:
            pass
        elif predicate in {"class-differs", "value-differs"}:
            mask = ~mask
        else:
            raise ValueError(f"unknown {kind} predicate: {predicate}")
    elif kind == "hash":
        if expected is None:
            raise ValueError("hash witness needs a base hash")
        mask = values != expected
        if predicate == "hash-same":
            mask = ~mask
        elif predicate != "hash-changes":
            raise ValueError(f"unknown hash predicate: {predicate}")
    else:
        raise ValueError(f"unknown witness kind: {kind}")
    mask = np.asarray(mask, dtype=bool)
    return bool(mask.any()), float(mask.mean()) if mask.size else 0.0


def _focused_value(case) -> tuple[str, object]:
    """Split ``focused`` into ``(outcome, expected)``.

    ``condition:out`` names the shared ``Condition`` code; a numeric outcome
    keeps its integer category (``winner:2``).
    """
    text = str(getattr(case, "focused", "") or "")
    if ":" not in text:
        raise ValueError("focused comparison needs '<outcome>:<value>'")
    name, raw = text.split(":", 1)
    if name not in _OUTCOMES:
        raise ValueError(f"focused comparison needs an outcome, not {name!r}")
    if name == "condition" and raw.strip().upper() in Condition.__members__:
        return name, int(Condition[raw.strip().upper()])
    expected: object = raw
    try:
        expected = int(raw)
    except ValueError:
        pass
    return name, expected


def _focused_activated(case, oracle, rows: int) -> tuple[bool, float]:
    name, expected = _focused_value(case)
    if name == "winner":
        values = np.asarray(oracle.winner)
    elif name == "rounds":
        values = np.asarray(oracle.resolution_rounds)
    elif name == "wounds":
        values = np.concatenate((oracle.first_wounds, oracle.second_wounds))
    else:
        values = np.concatenate((oracle.first_condition, oracle.second_condition))
    mask = values == expected
    mask = np.asarray(mask, dtype=bool)
    return bool(mask.any()), float(mask.mean()) if mask.size else 0.0


def _category_counts(values: np.ndarray) -> Counter:
    return Counter(int(value) for value in np.asarray(values).ravel())


def _tolerance(left: float, right: float, rows: int) -> float:
    """The existing six-sigma gate, copied from ``_statistical.py:19-24``.

    P03 unifies this expression in ``_statistical.py``; the battery deliberately
    does not introduce a second policy.
    """
    return max(
        .0025,
        6 * math.sqrt(left * (1 - left) / rows + right * (1 - right) / rows),
    )


def _compare(pairs: Sequence[tuple[str, np.ndarray, np.ndarray]], rows: int) -> str | None:
    """Return ``None`` when every category passes, else the worst detail string."""
    worst: tuple[float, str] | None = None
    for label, oracle_values, candidate_values in pairs:
        left_counts = _category_counts(oracle_values)
        right_counts = _category_counts(candidate_values)
        for category in sorted(set(left_counts) | set(right_counts)):
            left = left_counts[category] / rows
            right = right_counts[category] / rows
            difference = abs(left - right)
            tolerance = _tolerance(left, right, rows)
            detail = (
                f"{label}[{category}]: modular={left:.6f}, "
                f"candidate={right:.6f}, tol={tolerance:.6f}"
            )
            if difference > tolerance and (worst is None or difference > worst[0]):
                worst = (difference, detail)
    return None if worst is None else worst[1]


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
    for side in ("first_resources", "second_resources"):
        if not hasattr(left, side) or not hasattr(right, side):
            continue
        for (name, values), (other_name, other_values) in zip(
            getattr(left, side), getattr(right, side),
        ):
            if name != other_name or not np.array_equal(np.asarray(values), np.asarray(other_values)):
                return False
    return True


def _decision_key(error: KeyError) -> str:
    messages = [str(item) for item in error.args]
    text = " ".join(messages) or "unknown"
    return text.split("for ")[-1] if "for " in text else text


def _classify_value_error(error: ValueError) -> str:
    message = str(error)
    if "require the modular engine" in message or "optimized ports are pending" in message:
        return "INCOMPATIBLE:construction"
    if "outside the one-against-one runtime" in message:
        return "INCOMPATIBLE:construction"
    return f"DIVERGENCE:exception:ValueError: {message}"


def _variant(case):
    variant = VARIANTS.get(case.variant)
    if variant is None:
        raise ValueError(f"case {case.id} names an unknown variant {case.variant!r}")
    return variant


def _result(case, backend: str, status: str, *, rows: int, detail: str = "",
            witness=None, witness_rate: float | None = None,
            modular_seconds: float = 0.0, candidate_seconds: float = 0.0) -> BatteryCaseResult:
    variant = VARIANTS.get(case.variant)
    keys = tuple(VARIANT_KEYS.get(case.variant, ()))
    keys += tuple(
        key
        for extra in getattr(case, "also_covers", ()) or ()
        for key in VARIANT_KEYS.get(extra, ())
    )
    return BatteryCaseResult(
        case=str(case.id),
        level=str(case.level),
        variant=str(case.variant),
        obligation=str(case.variant).split(".")[0],
        backend=backend,
        status=status,
        keys=tuple(dict.fromkeys(keys)),
        observables=tuple(getattr(case, "observables", ()) or ()),
        rows=rows,
        witness=getattr(witness, "name", None),
        witness_kind=getattr(witness, "kind", None),
        witness_rate=witness_rate,
        expect=str(getattr(case, "expect", "present")),
        expect_value=getattr(case, "witness_value", None),
        comparison=str(getattr(case, "comparison", "witness")),
        coupling=("focused" if getattr(case, "comparison", "witness") == "focused"
                  else "unverified"),
        detail=detail,
        modular_seconds=modular_seconds,
        candidate_seconds=candidate_seconds,
    )


def _blocked(case, backend: str, rows: int) -> BatteryCaseResult | None:
    blocked = getattr(case, "blocked_by", None)
    if not blocked:
        return None
    text = str(blocked)
    parts = text.split(":")
    head = parts[0]
    owner = parts[-1] if len(parts) > 1 else "G00/G02"
    if head == "state":
        return _result(case, backend, "INCOMPATIBLE", rows=rows,
                       detail=f"INCOMPATIBLE:state owner={owner}")
    if head == "consume":
        return _result(case, backend, "INCOMPATIBLE", rows=rows,
                       detail=f"INCOMPATIBLE:consumer:{case.variant} owner={owner}")
    if head == "witness":
        variant = VARIANTS.get(case.variant)
        witness = getattr(variant, "witness", None)
        name = parts[1] if len(parts) == 3 else (getattr(witness, "name", None) or "unknown")
        return _result(case, backend, "INCOMPATIBLE", rows=rows,
                       witness=witness,
                       detail=f"INCOMPATIBLE:witness:{name} owner={owner}")
    if head == "decision":
        return _result(case, backend, "INCOMPATIBLE", rows=rows,
                       detail=f"INCOMPATIBLE:decision-scope owner={owner}")
    return _result(case, backend, "NOT_RUN", rows=rows,
                   detail=f"NOT_RUN:case-definition: unknown blocked_by {text!r} owner=P01")


def _run_case(case, *, backend: str, rows: int | None, root, focused_seen: dict,
              witness_seen: dict) -> BatteryCaseResult:
    effective_rows = int(getattr(case, "rows", 64)) if rows is None else int(rows)
    observables = tuple(getattr(case, "observables", ()) or ())
    blocked = _blocked(case, backend, effective_rows)
    if blocked is not None:
        return blocked
    if str(getattr(case, "decision_scope", "uniform")) == "per-row":
        return _result(
            case, backend, "INCOMPATIBLE", rows=effective_rows,
            detail="INCOMPATIBLE:decision-scope owner=P02/G02",
        )
    try:
        variant = _variant(case)
    except ValueError as error:
        return _result(case, backend, "NOT_RUN", rows=effective_rows,
                       detail=f"NOT_RUN:case-definition: {error} owner=P01")

    witness = getattr(variant, "witness", None)
    comparison = str(getattr(case, "comparison", "witness"))
    if comparison == "focused" and not getattr(case, "focused", None):
        return _result(case, backend, "NOT_RUN", rows=effective_rows,
                       detail="NOT_RUN:case-definition: focused case has no focus owner=P01")
    if comparison != "focused" and witness is None:
        return _result(case, backend, "INCOMPATIBLE", rows=effective_rows,
                       detail=f"INCOMPATIBLE:witness:none owner={variant.owner}")
    if witness is not None and witness.name not in observables:
        return _result(case, backend, "NOT_RUN", rows=effective_rows,
                       detail=f"NOT_RUN:case-definition: witness {witness.name} not declared owner=P01")

    try:
        first = compile_fighter(case.first, root)
        second = compile_fighter(case.second, root)
    except Exception as error:  # the compiler is shared; an invalid case is not a divergence
        return _result(
            case, backend, "NOT_RUN", rows=effective_rows,
            detail=f"NOT_RUN:compile:{type(error).__name__}: {error}",
        )

    decisions = ScriptedDecisions(dict(getattr(case, "decisions", {}) or {}))
    context = getattr(case, "context", None)
    seed = int(getattr(case, "seed", 2026))
    maximum_rounds = int(getattr(case, "maximum_rounds", 50))

    if backend == "native":
        try:
            _native_engine()
        except _NativeUnavailable as error:
            return _result(case, backend, "NOT_RUN", rows=effective_rows,
                           detail=f"NOT_RUN:native-stale: {error}")

    started = time.perf_counter()
    try:
        oracle = simulate_duel_observed(
            first, second, effective_rows, seed=seed,
            maximum_rounds=maximum_rounds, decisions=decisions, context=context,
        )
    except KeyError as error:
        return _result(case, backend, "NOT_RUN", rows=effective_rows,
                       detail=f"NOT_RUN:decision-script:{_decision_key(error)} owner=P01")
    except Exception as error:
        return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                       detail=f"DIVERGENCE:exception:{type(error).__name__}: {error}")
    modular_seconds = time.perf_counter() - started

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
        name = witness.name if witness is not None else "unknown"
        owner = getattr(variant, "owner", None) or _WITNESS_OWNERS.get(name, "G02/G06")
        return _result(case, backend, "INCOMPATIBLE", rows=effective_rows,
                       detail=f"INCOMPATIBLE:witness:{name} owner={owner}",
                       modular_seconds=modular_seconds)
    except ValueError as error:
        detail = _classify_value_error(error)
        status = "INCOMPATIBLE" if detail.startswith("INCOMPATIBLE") else "DIVERGENCE"
        return _result(case, backend, status, rows=effective_rows, detail=detail,
                       modular_seconds=modular_seconds)
    except Exception as error:
        return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                       detail=f"DIVERGENCE:exception:{type(error).__name__}: {error}",
                       modular_seconds=modular_seconds)
    candidate_seconds = time.perf_counter() - started

    mismatch = _shape_mismatch(oracle, candidate, effective_rows)
    if mismatch is not None:
        return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                       detail=f"DIVERGENCE:batch-shape: {mismatch}",
                       modular_seconds=modular_seconds,
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
                           modular_seconds=modular_seconds,
                           candidate_seconds=candidate_seconds)
        if not _same_sample(candidate, repeat):
            return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                           detail="DIVERGENCE:batch-nondeterministic",
                           modular_seconds=modular_seconds,
                           candidate_seconds=candidate_seconds)

    pairs: list[tuple[str, np.ndarray, np.ndarray]] = []
    for name in observables:
        if name in _OUTCOMES:
            pairs.extend(_observable_pairs(name, oracle, candidate))
            continue
        try:
            oracle_values = _row_values(name, oracle)
            candidate_values = _row_values(name, candidate)
        except _WitnessUnavailable as error:
            return _result(
                case, backend, "INCOMPATIBLE", rows=effective_rows,
                detail=f"INCOMPATIBLE:witness:{error.name} owner={error.owner}",
                modular_seconds=modular_seconds, candidate_seconds=candidate_seconds,
            )
        if oracle_values.size != candidate_values.size:
            return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                           detail=f"DIVERGENCE:batch-shape: witness {name}",
                           modular_seconds=modular_seconds,
                           candidate_seconds=candidate_seconds)
        pairs.append((name, oracle_values, candidate_values))

    failure = _compare(pairs, effective_rows) if pairs else None
    if failure is not None:
        return _result(case, backend, "DIVERGENCE", rows=effective_rows,
                       detail=f"DIVERGENCE: {failure}",
                       modular_seconds=modular_seconds,
                       candidate_seconds=candidate_seconds)

    if comparison == "focused":
        try:
            activated, rate = _focused_activated(case, oracle, effective_rows)
        except ValueError as error:
            return _result(case, backend, "NOT_RUN", rows=effective_rows,
                           detail=f"NOT_RUN:case-definition: {error} owner=P01",
                           modular_seconds=modular_seconds,
                           candidate_seconds=candidate_seconds)
        focused_seen[str(case.id)] = activated
        if str(getattr(case, "expect", "present")) == "present":
            if not activated:
                return _result(case, backend, "NOT_ACTIVATED", rows=effective_rows,
                               detail=f"NOT_ACTIVATED:{case.focused}",
                               modular_seconds=modular_seconds,
                               candidate_seconds=candidate_seconds)
        else:
            if activated:
                return _result(case, backend, "NOT_RUN", rows=effective_rows,
                               detail=f"NOT_RUN:criterion-insensitive:{case.variant} owner=P01",
                               modular_seconds=modular_seconds,
                               candidate_seconds=candidate_seconds)
        detail = f"focused[{case.focused}] rate={rate:.6f}"
        return _result(case, backend, "PASS", rows=effective_rows, detail=detail,
                       modular_seconds=modular_seconds,
                       candidate_seconds=candidate_seconds)

    try:
        values = _row_values(witness.name, oracle)
        kind = witness.kind
        expected = getattr(case, "witness_value", None)
        present_ok, rate = _predicate(kind, witness.present, values, expected)
        absent_ok, _ = _predicate(kind, witness.absent, values, expected)
    except _WitnessUnavailable as error:
        return _result(
            case, backend, "INCOMPATIBLE", rows=effective_rows,
            detail=f"INCOMPATIBLE:witness:{error.name} owner={error.owner}",
            witness=witness, modular_seconds=modular_seconds,
            candidate_seconds=candidate_seconds,
        )
    except ValueError as error:
        return _result(case, backend, "NOT_RUN", rows=effective_rows,
                       detail=f"NOT_RUN:case-definition: {error} owner=P01",
                       witness=witness, modular_seconds=modular_seconds,
                       candidate_seconds=candidate_seconds)

    witness_seen[str(case.id)] = present_ok
    if str(getattr(case, "expect", "present")) == "present" and not present_ok:
        return _result(case, backend, "NOT_ACTIVATED", rows=effective_rows,
                       detail=f"NOT_ACTIVATED:{witness.name}",
                       witness=witness, witness_rate=rate,
                       modular_seconds=modular_seconds,
                       candidate_seconds=candidate_seconds)
    if str(getattr(case, "expect", "present")) == "absent" and not absent_ok:
        return _result(case, backend, "NOT_RUN", rows=effective_rows,
                       detail=f"NOT_RUN:criterion-insensitive:{case.variant} owner=P01",
                       witness=witness, witness_rate=rate,
                       modular_seconds=modular_seconds,
                       candidate_seconds=candidate_seconds)

    detail = ""
    if pairs:
        best: tuple[float, str] | None = None
        for label, oracle_values, candidate_values in pairs:
            left_counts = _category_counts(oracle_values)
            right_counts = _category_counts(candidate_values)
            for category in sorted(set(left_counts) | set(right_counts)):
                left = left_counts[category] / effective_rows
                right = right_counts[category] / effective_rows
                tolerance = _tolerance(left, right, effective_rows)
                margin = tolerance - abs(left - right)
                text = (
                    f"{label}[{category}]: modular={left:.6f}, "
                    f"candidate={right:.6f}, tol={tolerance:.6f}"
                )
                if best is None or margin < best[0]:
                    best = (margin, text)
        if best is not None:
            detail = best[1]
    return _result(case, backend, "PASS", rows=effective_rows, detail=detail,
                   witness=witness, witness_rate=rate,
                   modular_seconds=modular_seconds,
                   candidate_seconds=candidate_seconds)


def _resolve_controls(cases: Sequence, results: Sequence[BatteryCaseResult],
                      focused_seen: Mapping[str, bool],
                      witness_seen: Mapping[str, bool]) -> tuple[BatteryCaseResult, ...]:
    """Resolve positive/negative pairs before any approval.

    A focused positive has no ``positive_control`` (A10) and is evidence only
    when a negative of the same variant references it and declares the same
    focused result.  Every negative — focused or witness — requires its control
    to activate; a non-activating control is ``NOT_ACTIVATED``, never a
    divergence between engines.
    """
    by_id = {case.id: case for case in cases}
    negatives: dict[str, list] = {}
    for case in cases:
        if (str(getattr(case, "expect", "present")) == "absent"
                and getattr(case, "positive_control", None)):
            negatives.setdefault(case.positive_control, []).append(case)

    resolved = {case.id: result for case, result in zip(cases, results)}

    # Pass one: a negative may only pass when its positive control activated.
    for case in cases:
        result = resolved[case.id]
        if result.status != "PASS" or str(getattr(case, "expect", "present")) != "absent":
            continue
        comparison = str(getattr(case, "comparison", "witness"))
        focus = str(getattr(case, "focused", "") or "")
        control = by_id.get(getattr(case, "positive_control", None))
        if control is None:
            resolved[case.id] = replace(
                result, status="NOT_RUN",
                detail="NOT_RUN:case-definition: control missing owner=P01",
            )
            continue
        same_focus = (
            comparison != "focused"
            or str(getattr(control, "focused", "")) == focus
        )
        if not same_focus:
            resolved[case.id] = replace(
                result, status="NOT_RUN",
                detail="NOT_RUN:case-definition: focused control mismatch owner=P01",
            )
            continue
        activated = (focused_seen if comparison == "focused" else witness_seen).get(
            control.id, False,
        )
        if not activated:
            resolved[case.id] = replace(
                result, status="NOT_ACTIVATED",
                detail=f"NOT_ACTIVATED:positive-control:{control.id}",
            )
            continue
        resolved[case.id] = replace(result, coupling="contrast")

    # Pass two: a focused positive is evidence only with a passing negative.
    for case in cases:
        result = resolved[case.id]
        if result.status != "PASS":
            continue
        comparison = str(getattr(case, "comparison", "witness"))
        if comparison != "focused" or str(getattr(case, "expect", "present")) != "present":
            continue
        focus = str(getattr(case, "focused", "") or "")
        partners = [
            other for other in negatives.get(case.id, ())
            if str(getattr(other, "comparison", "witness")) == "focused"
            and str(getattr(other, "focused", "")) == focus
        ]
        if not partners:
            resolved[case.id] = replace(
                result, status="NOT_ACTIVATED",
                detail="NOT_ACTIVATED:no-negative-control",
            )
            continue
        if not any(resolved[other.id].status == "PASS" for other in partners):
            resolved[case.id] = replace(
                result, status="NOT_ACTIVATED",
                detail="NOT_ACTIVATED:negative-control-not-passing",
            )
            continue
        resolved[case.id] = replace(result, coupling="contrast")

    # A witness positive with a passing negative also has a declared contrast.
    for case in cases:
        result = resolved[case.id]
        if (result.status != "PASS" or result.coupling != "unverified"
                or str(getattr(case, "comparison", "witness")) == "focused"):
            continue
        partners = negatives.get(case.id, ())
        if partners and any(resolved[other.id].status == "PASS" for other in partners):
            resolved[case.id] = replace(result, coupling="contrast")

    adjusted = [resolved[case.id] for case in cases]
    return tuple(adjusted)


def _by_status(results: Iterable[BatteryCaseResult], status: str) -> tuple[str, ...]:
    return tuple(result.case for result in results if result.status == status)


def run_battery(
    cases: Sequence, *, profile: str | None = None, backend: str = "numpy",
    rows: int | None = None, root=None,
) -> BatteryReport:
    """Run ``cases`` through the real oracle and the selected candidate.

    ``rows`` overrides the case's declared sample width; it never changes case
    identity or the quick/complete/deep nesting.  ``root`` defaults to the
    knowledge root; compilation is done once per case and excluded from both
    timing fields, as P04 measures it separately.

    ``profile`` makes coverage meaningful: every required duel variant of that
    profile must be represented.  Without it the run is a diagnostic subset and
    ``accepted`` is always false.
    """
    if backend not in {"numpy", "native"}:
        raise ValueError(f"unknown battery backend: {backend}")
    if rows is not None and int(rows) < 1:
        raise ValueError("rows must be positive")
    if profile is not None and profile not in ("quick", "complete", "deep"):
        raise ValueError(f"unknown battery profile: {profile}")
    knowledge = root or knowledge_root()
    focused_seen: dict[str, bool] = {}
    witness_seen: dict[str, bool] = {}
    results = tuple(
        _run_case(case, backend=backend, rows=rows, root=knowledge,
                  focused_seen=focused_seen, witness_seen=witness_seen)
        for case in cases
    )
    results = _resolve_controls(cases, results, focused_seen, witness_seen)

    represented: set[str] = set()
    for case in cases:
        represented.add(str(case.variant))
        represented.update(str(extra) for extra in getattr(case, "also_covers", ()) or ())
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
        + _by_status(results, "NOT_ACTIVATED")
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
        not_activated=_by_status(results, "NOT_ACTIVATED"),
        not_run=_by_status(results, "NOT_RUN"),
        missing_variants=missing,
    )


__all__ = (
    "RESOURCES_OBSERVED",
    "BatteryCaseResult",
    "BatteryReport",
    "run_battery",
)
