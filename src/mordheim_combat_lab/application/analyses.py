"""Casos de uso de análisis sin Tkinter ni conocimiento de la presentación."""
from dataclasses import dataclass, replace
from threading import Event
from typing import Callable, Iterable

from mordheim_combat_lab.combat.vectorized import simulate_duel
from mordheim_combat_lab.construction.compiler import compile_fighter
from mordheim_combat_lab.domain.models import FighterBuild, SimulationCancelled
from .settings import DuelExecutionSettings


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
                   cancel_event: Event, progress: Callable[[int], None] = lambda _n: None) -> ComparisonBatch:
    """Compilar y simular variantes; devolver también construcciones ilegales."""
    compiled_enemy = compile_fighter(enemy)
    baseline_result = simulate_duel(settings.request(compile_fighter(baseline), compiled_enemy, cancel_event))
    results, rejected = [], []
    for completed, candidate in enumerate(candidates, start=1):
        if cancel_event.is_set():
            raise SimulationCancelled()
        try:
            fighter = compile_fighter(candidate.build)
        except (KeyError, TypeError, ValueError) as error:
            rejected.append((candidate, str(error)))
        else:
            result = simulate_duel(settings.request(fighter, compiled_enemy, cancel_event))
            results.append(ComparisonResult(candidate, result.first_win_rate,
                result.first_win_rate - baseline_result.first_win_rate,
                result.second_win_rate, result.unresolved_rate))
        progress(completed)
    return ComparisonBatch(baseline_result.first_win_rate, tuple(results), tuple(rejected))


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
