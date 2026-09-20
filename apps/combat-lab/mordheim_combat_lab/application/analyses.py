"""Analysis use cases without Tkinter or presentation knowledge."""
import time as time
from dataclasses import dataclass, replace
from threading import Event
from typing import Callable, Iterable

from mordheim_combat.vectorized import simulate_duel
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild, SimulationCancelled
from .catalogue import SkillChoice
from .settings import (
    DuelExecutionSettings,
    battery_pool_plan,
    pool_batch_size,
    resolve_fighter_settings,
    simulate_battery,
    split_battery,
)


@dataclass(frozen=True, slots=True)
class ComparisonCandidate:
    id: str
    label: str
    build: FighterBuild


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    candidate: ComparisonCandidate
    win_rate: float
    improvement: float
    enemy_win_rate: float
    unresolved_rate: float


@dataclass(frozen=True, slots=True)
class ComparisonBatch:
    baseline_win_rate: float
    results: tuple[ComparisonResult, ...]
    rejected: tuple[tuple[ComparisonCandidate, str], ...]


def compare_builds(baseline: FighterBuild, enemy: FighterBuild,
                   candidates: Iterable[ComparisonCandidate], settings: DuelExecutionSettings,
                   cancel_event: Event, progress: Callable[[int], None] = lambda _n: None,
                   workers: int | None = None,
                   observe: Callable[[dict], None] | None = None) -> ComparisonBatch:
    """Compile and simulate variants; also return illegal constructions.

    Batches left at the legacy global default resolve to the per-engine
    optimum actually running each duel (native 5k, numpy 100k — plans that
    fall back to NumPy keep the NumPy optimum); explicit batch values are
    honoured.

    The baseline always runs sequentially: its wall time measures the real
    per-duel cost of *this* pair, which is what :func:`battery_pool_plan`
    uses to decide whether a pool pays off for the remaining fighters (a
    fixed sample-size threshold misjudges heavy grinds and cheap duels
    alike). ``workers`` overrides that decision: ``0`` forces the in-process
    path, a positive count pools, ``None`` lets the measurement decide. When
    the pool engages it is created once per run and shared by every fighter,
    and NumPy fighters switch to the measured pooled batch
    (:func:`pool_batch_size`) — its sequential optimum starves the pool.

    ``observe`` (optional) receives one JSON-safe payload with the run's
    per-fighter resolutions — simulations, batch size, the engine actually
    executing the duels, pool workers and wall seconds — plus the pool
    decision inputs, for local usage telemetry; it never affects the
    comparison itself.
    """
    compiled_enemy = compile_fighter(enemy)
    baseline_fighter = compile_fighter(baseline)
    baseline_settings, baseline_backend = resolve_fighter_settings(settings, baseline_fighter, compiled_enemy)
    # The pool decision needs the run's width, so the iterable is materialised.
    candidates = tuple(candidates)

    def _run(fighter, run_settings, executor):
        started = time.perf_counter()
        if executor is not None:
            result = simulate_battery(fighter, compiled_enemy, run_settings, cancel_event,
                                      workers=workers, pool=executor)
        else:
            result = simulate_duel(run_settings.request(fighter, compiled_enemy, cancel_event))
        return result, time.perf_counter() - started

    def _record(identifier, run_settings, backend, seconds, used_workers):
        return {
            "id": identifier,
            "simulations": run_settings.simulations,
            "batch_size": run_settings.batch_size,
            "engine": backend,
            "workers": used_workers,
            "wall_seconds": round(seconds, 4),
        }

    battery_pool = None
    segments = 0
    try:
        # The sequential baseline doubles as the run's calibration probe: its
        # wall time measures the real per-duel cost of this pair, which is
        # exactly what the pool decision needs.
        baseline_result, baseline_seconds = _run(baseline_fighter, baseline_settings, None)
        if workers is None:  # the UI maps its -1 sentinel to None; 0 forces the in-process path
            workers = battery_pool_plan(baseline_seconds, baseline_settings,
                                        baseline_backend, len(candidates))
        if baseline_settings.simulations < 2:
            workers = None
        if workers:
            from concurrent.futures import ProcessPoolExecutor

            # One executor for the whole run: spawning costs ~0.33s and doing
            # it per fighter erased most of the pool's win in wide runs
            # (measured 2.4x effective vs 5.9x amortized in the TTS studies).
            segments = len(split_battery(
                baseline_settings.simulations, baseline_settings.batch_size, workers))
            battery_pool = ProcessPoolExecutor(max_workers=segments)

        results, rejected, observed = [], [], []
        for completed, candidate in enumerate(candidates, start=1):
            if cancel_event.is_set():
                raise SimulationCancelled()
            try:
                fighter = compile_fighter(candidate.build)
            except (KeyError, TypeError, ValueError) as error:
                rejected.append((candidate, str(error)))
            else:
                candidate_settings, backend = resolve_fighter_settings(settings, fighter, compiled_enemy)
                if battery_pool is not None:
                    candidate_settings = replace(
                        candidate_settings,
                        batch_size=pool_batch_size(backend, candidate_settings))
                result, seconds = _run(fighter, candidate_settings, battery_pool)
                results.append(ComparisonResult(candidate, result.first_win_rate,
                    result.first_win_rate - baseline_result.first_win_rate,
                    result.second_win_rate, result.unresolved_rate))
                if observe is not None:
                    observed.append(_record(candidate.id, candidate_settings, backend, seconds, workers or 0))
            progress(completed)
        if observe is not None:
            observe({
                "baseline": _record("baseline", baseline_settings, baseline_backend, baseline_seconds, 0),
                "candidates": observed,
                "pool": {
                    "workers": workers or 0,
                    "segments": segments,
                    "baseline_seconds": round(baseline_seconds, 4),
                },
            })
        return ComparisonBatch(baseline_result.first_win_rate, tuple(results), tuple(rejected))
    finally:
        if battery_pool is not None:
            battery_pool.shutdown()


def improvement_choices(catalogue, choice, candidate: FighterBuild):
    skills = catalogue.skills(choice)
    enabled = catalogue.in_scope_skill_ids(skills)
    selected = set(catalogue.skill_ui_ids(choice, candidate.skill_ids, candidate.special_rule_ids))
    valid = []
    for skill in skills:
        if skill.id not in enabled or skill.id in selected:
            continue
        try:
            compile_fighter(add_improvement(catalogue, candidate, skill))
        except ValueError:
            continue
        valid.append(skill)
    return tuple(valid)


def add_improvement(catalogue, candidate: FighterBuild, skill) -> FighterBuild:
    ordinary, special = catalogue.skill_rule_ids((skill.id,))
    return replace(candidate, skill_ids=(*candidate.skill_ids, *ordinary),
                   special_rule_ids=(*candidate.special_rule_ids, *special))


@dataclass(frozen=True, slots=True)
class ImprovementCombination:
    id: str
    label: str
    skills: tuple


def add_improvements(catalogue, candidate: FighterBuild, skills) -> FighterBuild:
    """Add several improvements at once (warband skills map to special rules)."""
    ordinary, special = catalogue.skill_rule_ids(tuple(skill.id for skill in skills))
    return replace(candidate, skill_ids=(*candidate.skill_ids, *ordinary),
                   special_rule_ids=(*candidate.special_rule_ids, *special))


def improvement_combinations(skills, size: int) -> tuple[ImprovementCombination, ...]:
    """Group selectable improvements into same-size combinations for one run.

    ``size`` 1 reproduces the historical per-skill comparison; larger sizes
    evaluate several improvements applied simultaneously per row. Skills
    enter at most once per combination, while attribute increases may repeat
    up to the ``steps`` each ``AttributeChoice`` still allows before the
    racial maximum blocks another point. There is deliberately no row cap:
    the caller decides how many rows to simulate, and the progress bar plus
    the cancel button remain usable for however long the run takes.
    """
    if not 1 <= size <= 5:
        raise ValueError(f"improvement size must be between 1 and 5, got {size}")
    pool = tuple(skills)
    allowances = tuple(getattr(item, "steps", 1) for item in pool)
    indices = []

    def extend(prefix: list[int], start: int, remaining: int, free: tuple[int, ...]) -> None:
        if remaining == 0:
            indices.append(tuple(prefix))
            return
        for position in range(start, len(free)):
            if free[position] <= 0:
                continue
            prefix.append(position)
            extend(prefix, position, remaining - 1,
                   (*free[:position], free[position] - 1, *free[position + 1:]))
            prefix.pop()

    extend([], 0, size, allowances)
    return tuple(
        ImprovementCombination(
            "+".join(pool[index].id for index in combination),
            " + ".join(pool[index].name for index in combination),
            tuple(pool[index] for index in combination),
        )
        for combination in indices
    )


#: Display key → ``Characteristics`` constructor argument of an increase.
ATTRIBUTE_INCREASES = (
    ("WS", "weapon_skill"), ("S", "strength"), ("T", "toughness"),
    ("W", "wounds"), ("I", "initiative"), ("A", "attacks"),
)


def improve_attributes(candidate: FighterBuild, increases: dict[str, int]) -> FighterBuild:
    """Return the build with the requested characteristic increases applied.

    ``increases`` maps display keys (``WS``…``A``) to how many points to add;
    this function applies them without judging legality — the compiler and
    the racial-maximum gate own that decision.
    """
    if not increases:
        return candidate
    current = candidate.characteristics
    if current is None:
        raise ValueError("attribute increases need a build with explicit characteristics")
    values = {
        "WS": current.weapon_skill, "S": current.strength, "T": current.toughness,
        "W": current.wounds, "I": current.initiative, "A": current.attacks,
    }
    for key, amount in increases.items():
        if key not in values:
            raise ValueError(f"unknown characteristic increase: {key}")
        if not isinstance(amount, int) or amount < 0:
            raise ValueError(f"{key} increase must be a non-negative integer, got {amount!r}")
        values[key] += amount
    return replace(
        candidate,
        characteristics=Characteristics(
            values["WS"], values["S"], values["T"], values["W"], values["I"], values["A"],
        ),
    )


@dataclass(frozen=True, slots=True)
class AttributeChoice:
    id: str
    name: str
    #: How many further +1 points fit below the racial maximum.
    steps: int = 1


def attribute_choices(catalogue, choice, candidate: FighterBuild) -> tuple[AttributeChoice, ...]:
    """Attribute increases that keep the profile inside its racial maximums.

    Warbands whose racial maximum the catalogue cannot resolve (per-profile
    tables like the lizardmen) get no attribute options rather than guessed
    ones; free selection resolves no race and follows the same rule.
    """
    maximums = catalogue.characteristic_maximums(choice)
    if not maximums or candidate.characteristics is None:
        return ()
    current = candidate.characteristics
    values = {
        "WS": current.weapon_skill, "S": current.strength, "T": current.toughness,
        "W": current.wounds, "I": current.initiative, "A": current.attacks,
    }
    names = {"WS": "Weapon Skill", "S": "Strength", "T": "Toughness",
             "W": "Wounds", "I": "Initiative", "A": "Attacks"}
    return tuple(
        AttributeChoice(key, names[key], maximums[key] - values[key])
        for key, _field in ATTRIBUTE_INCREASES
        if key in maximums and values[key] < maximums[key]
    )


def add_improvement_items(catalogue, candidate: FighterBuild, items) -> FighterBuild:
    """Apply a mix of skills and attribute increases as one improvement row."""
    attributes = [item for item in items if isinstance(item, AttributeChoice)]
    skills = tuple(item for item in items if not isinstance(item, AttributeChoice)
                   and isinstance(item, SkillChoice))
    build = add_improvements(catalogue, candidate, skills) if skills else candidate
    if attributes:
        increases: dict[str, int] = {}
        for item in attributes:  # repeated selections stack (+1 each)
            increases[item.id] = increases.get(item.id, 0) + 1
        build = improve_attributes(build, increases)
    return build
