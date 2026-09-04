"""Mutation discrimination for the vectorized engine itself.

The semantic specifications mutate *rules* (knowledge/compile inputs) and
prove the specs detect them.  This harness mutates the *engine code* — the
duplicated NumPy projections of canonical phase math — and proves the
deterministic test corpus detects the defect class.

A mutant is applied to a staged copy of ``src/`` (never to the live tree),
the deterministic detector suites run against the staged tree in a child
process, and the mutant is **killed** when at least one test fails.  A
surviving mutant is a real gap: some reachable engine decision has no
deterministic test that can tell it apart from the oracle.  The goal is a
catalogue with zero survivors, and every survivor is a directive to add one
deterministic test (never a statistical pair).
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

#: Detector suites: fast deterministic tests that must catch the catalogue.
#: The parity inventory test runs the exact operator checks, the semantic
#: corpus replays every rule against the (mutated) engine, and the engine
#: suite exercises rule paths end to end.  Node ids, never whole files: the
#: multiprocessing-pool tests cannot run under the ``-c`` detector launcher
#: (spawned workers re-import the main module) and would fail every mutant
#: for environmental reasons.
DEFAULT_DETECTOR_SUITES = (
    "tests/combat/vectorized/test_vectorized_engine.py",
    "tests/verification/test_parity.py::"
    "test_vectorized_parity_inventory_is_complete_and_exact_checks_pass",
    "tests/verification/test_parity.py::"
    "test_semantic_specs_are_reused_as_a_case_level_parity_inventory",
)

_DETECTOR_SCRIPT = (
    "import sys, pytest; "
    "sys.exit(pytest.main(['-q', '-p', 'no:cacheprovider', '--no-header', "
    "'-o', 'pythonpath=', '-o', 'testpaths='] + sys.argv[1:]))"
)


@dataclass(frozen=True, slots=True)
class EngineMutant:
    """One single-token defect injected into the staged engine copy.

    ``file`` is relative to ``src/mordheim_combat``; ``old`` must appear
    exactly once in the current file (enforced at application time so the
    catalogue fails loudly when the engine changes underneath it).
    """

    id: str
    file: str
    old: str
    new: str
    description: str


CATALOG: tuple[EngineMutant, ...] = (
    EngineMutant(
        "wound-ramp-off-by-one",
        "vectorized/_operators.py",
        "targets = np.clip(4 - difference, 2, 6)",
        "targets = np.clip(5 - difference, 2, 6)",
        "wound table ramps one point too high (every strength/toughness pair)",
    ),
    EngineMutant(
        "wound-impossible-tail",
        "vectorized/_operators.py",
        "targets = np.where(difference <= -4, 7, targets)",
        "targets = np.where(difference <= -3, 7, targets)",
        "wound target 7 ('cannot wound') granted one point earlier",
    ),
    EngineMutant(
        "armour-strength-modifier",
        "vectorized/_operators.py",
        "np.maximum(0, strength - 3)",
        "np.maximum(0, strength - 4)",
        "armour save modifier ignores one point of strength penetration",
    ),
    EngineMutant(
        "injury-stun-threshold",
        "vectorized/_operators.py",
        "np.where(totals >= 3, STUNNED, KNOCKED_DOWN),",
        "np.where(totals >= 4, STUNNED, KNOCKED_DOWN),",
        "injury table stuns one point late (totals of 3 become knocked down)",
    ),
    EngineMutant(
        "paired-extra-attack-dropped",
        "vectorized/_operators.py",
        "result += extra_weapon_attack",
        "result += 0",
        "paired/off-hand extra attack never granted",
    ),
    EngineMutant(
        "hit-much-weaker-flip",
        "vectorized/_operators.py",
        "target = 4 + (defender_ws > 2 * attacker_ws) - (attacker_ws > defender_ws)",
        "target = 4 + (defender_ws >= 2 * attacker_ws) - (attacker_ws > defender_ws)",
        "a defender with exactly double WS also imposes the +1 to-hit",
    ),
)


@dataclass(frozen=True, slots=True)
class MutantOutcome:
    mutant: EngineMutant
    killed: bool
    returncode: int
    seconds: float
    detail: str = ""


@dataclass(frozen=True, slots=True)
class MutationRunReport:
    outcomes: tuple[MutantOutcome, ...]
    seconds: float

    @property
    def killed(self) -> tuple[str, ...]:
        return tuple(item.mutant.id for item in self.outcomes if item.killed)

    @property
    def surviving(self) -> tuple[str, ...]:
        return tuple(item.mutant.id for item in self.outcomes if not item.killed)

    @property
    def complete(self) -> bool:
        return not self.surviving and bool(self.outcomes)


def _stage_src(mutant: EngineMutant) -> tuple[Path, Path]:
    """Stage a shadow copy of the engine package and apply the mutant.

    Only ``mordheim_combat`` is staged (a pure-Python shadow that wins on
    ``PYTHONPATH``); the knowledge/construction packages keep resolving from
    the real tree, so their project-root discovery and compiled fighters stay
    untouched and type-aligned with the staged engine.  Returns
    ``(stage_root, patched_file)`` where ``stage_root`` is the ``src``-like
    directory to put first on ``PYTHONPATH``.
    """
    staging = tempfile.mkdtemp(prefix="mordheim-mutant-")
    stage_root = Path(staging) / "src"
    shutil.copytree(
        ROOT / "src" / "mordheim_combat", stage_root / "mordheim_combat",
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", "*.c", "*.cpp", "*.pyx", "*.pxd",
            "*.pyd", "*.so", "*.exe", "build", ".mypy_cache",
        ),
    )
    target = stage_root / "mordheim_combat" / Path(mutant.file)
    source = target.read_text(encoding="utf-8")
    count = source.count(mutant.old)
    if count != 1:
        shutil.rmtree(Path(staging), ignore_errors=True)
        raise ValueError(
            f"stale mutant {mutant.id}: expected one occurrence of the "
            f"anchor in {mutant.file}, found {count}"
        )
    target.write_text(source.replace(mutant.old, mutant.new), encoding="utf-8")
    return stage_root, target


def _run_detector(stage_root: Path, suites: tuple[str, ...], timeout: int) -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(stage_root)
    completed = subprocess.run(
        [sys.executable, "-c", _DETECTOR_SCRIPT, *suites],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout,
    )
    return completed.returncode


def run_mutant(mutant: EngineMutant, suites: tuple[str, ...] = DEFAULT_DETECTOR_SUITES,
               *, timeout: int = 600) -> MutantOutcome:
    """Apply one mutant to a staged copy and run the detector suites."""
    stage_root, _ = _stage_src(mutant)
    started = time.perf_counter()
    try:
        returncode = _run_detector(stage_root, suites, timeout)
    finally:
        shutil.rmtree(stage_root.parent, ignore_errors=True)
    return MutantOutcome(
        mutant=mutant, killed=returncode != 0, returncode=returncode,
        seconds=time.perf_counter() - started,
    )


def run_catalogue(
    mutants: tuple[EngineMutant, ...] = CATALOG,
    suites: tuple[str, ...] = DEFAULT_DETECTOR_SUITES,
    *, timeout: int = 600,
    on_progress=None,
) -> MutationRunReport:
    """Run every mutant of the catalogue and summarize kill/survival."""
    started = time.perf_counter()
    outcomes = []
    for mutant in mutants:
        outcome = run_mutant(mutant, suites, timeout=timeout)
        outcomes.append(outcome)
        if on_progress is not None:
            on_progress(outcome)
    return MutationRunReport(
        outcomes=tuple(outcomes), seconds=time.perf_counter() - started,
    )
