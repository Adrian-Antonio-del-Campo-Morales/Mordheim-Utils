"""Benchmark suite and CLI presenters for the combat backends.

Runs the maintained end-to-end scenarios against the modular, NumPy and
native engines, supports single-configuration runs (with baseline
comparison gates) and size sweeps over simulation counts and batch
sizes, and renders results as console tables, JSON, CSV or Markdown.
"""
from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime, timezone
import csv
import json
from pathlib import Path
import platform
from statistics import median
from time import perf_counter
from typing import Callable
from typing import Iterable

import numpy as np

from mordheim_combat.modular.duel import simulate_duel as simulate_modular_duel
from mordheim_combat.vectorized import simulate_duel
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import DuelRequest
from mordheim_core.models import FighterBuild


@dataclass(frozen=True, slots=True)
class BenchmarkScenario:
    id: str
    first: FighterBuild
    second: FighterBuild
    maximum_rounds: int = 50


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    scenario: str
    backend: str
    simulations: int
    batch_size: int
    repeats: int
    samples_seconds: tuple[float, ...]
    median_seconds: float
    simulations_per_second: float


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    scenario: str
    backend: str
    baseline_simulations_per_second: float
    current_simulations_per_second: float
    change_ratio: float
    status: str


@dataclass(frozen=True, slots=True)
class BenchmarkGate:
    passed: bool
    improved: bool
    regressed: bool
    comparisons: tuple[BenchmarkComparison, ...]
    detail: str


BENCHMARK_SCHEMA = "mordheim-combat-benchmark/v1"
SWEEP_SCHEMA = "mordheim-combat-benchmark-sweep/v1"

ENGINE_LABELS = {"modular": "Modular", "numpy": "Vectorized", "native": "Native"}


ORDINARY = Characteristics(3, 3, 3, 1, 3, 1)
VETERAN = Characteristics(4, 4, 4, 2, 4, 2)
DURABLE = Characteristics(2, 2, 5, 4, 2, 1)


def benchmark_scenarios() -> tuple[BenchmarkScenario, ...]:
    ordinary = ORDINARY
    veteran = VETERAN
    durable = DURABLE
    return (
        BenchmarkScenario(
            "basic",
            FighterBuild("mordheim", ordinary),
            FighterBuild("mordheim", ordinary),
        ),
        BenchmarkScenario(
            "multiattack",
            FighterBuild("mordheim", Characteristics(4, 4, 3, 2, 4, 3),
                         main_weapon_id="weapon.axe", off_hand_id="weapon.dagger"),
            FighterBuild("mordheim", veteran, armour_id="armour.heavy-armour"),
        ),
        BenchmarkScenario(
            "defences",
            FighterBuild("mordheim", veteran, main_weapon_id="weapon.sword",
                         off_hand_id="defence.buckler", armour_id="armour.light-armour"),
            FighterBuild("mordheim", veteran, main_weapon_id="weapon.dwarf-axe",
                         off_hand_id="defence.shield", armour_id="armour.gromril-armour"),
        ),
        BenchmarkScenario(
            "stateful",
            FighterBuild(
                "mordheim", band_id="pit-fighters", profile_id="pit-king",
                special_rule_ids=("band--pit-fighter-skill-force-of-will",),
            ),
            FighterBuild("mordheim", veteran, main_weapon_id="weapon.brazier-iron"),
        ),
        BenchmarkScenario(
            "long",
            FighterBuild("mordheim", durable, armour_id="armour.gromril-armour",
                         off_hand_id="defence.shield"),
            FighterBuild("mordheim", durable, armour_id="armour.gromril-armour",
                         off_hand_id="defence.shield"),
            maximum_rounds=75,
        ),
    )


def _build(*, characteristics=None, main_weapon_id: str = "weapon.dagger",
           off_hand_id: str | None = None, armour_id: str = "armour.no-armour",
           defence_ids: tuple[str, ...] = (), band_id: str | None = None,
           profile_id: str | None = None, special_rule_ids: tuple[str, ...] = ()) -> FighterBuild:
    """Build a FighterBuild for the deep scenario matrix with explicit knobs.

    ``characteristics`` and the ``band_id``/``profile_id`` pair are mutually
    exclusive ways to describe the fighter (mirroring ``FighterBuild``); a
    characteristics-less profile build must never silently receive the
    ordinary profile.
    """
    if band_id is None and characteristics is None:
        characteristics = ORDINARY
    return FighterBuild(
        "mordheim", characteristics, band_id=band_id, profile_id=profile_id,
        main_weapon_id=main_weapon_id, off_hand_id=off_hand_id, armour_id=armour_id,
        defence_ids=defence_ids, special_rule_ids=special_rule_ids,
    )


DEEP_SCENARIOS: tuple[BenchmarkScenario, ...] = (
    # Standard certification families first (same ids as benchmark_scenarios).
    BenchmarkScenario("basic", _build(), _build()),
    BenchmarkScenario(
        "multiattack",
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe", off_hand_id="weapon.dagger"),
        _build(characteristics=VETERAN, armour_id="armour.heavy-armour"),
    ),
    BenchmarkScenario(
        "defences",
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               off_hand_id="defence.buckler", armour_id="armour.light-armour"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.dwarf-axe",
               off_hand_id="defence.shield", armour_id="armour.gromril-armour"),
    ),
    BenchmarkScenario(
        "stateful",
        _build(band_id="pit-fighters", profile_id="pit-king",
               special_rule_ids=("band--pit-fighter-skill-force-of-will",)),
        _build(characteristics=VETERAN, main_weapon_id="weapon.brazier-iron"),
    ),
    BenchmarkScenario(
        "long",
        _build(characteristics=DURABLE, armour_id="armour.gromril-armour",
               off_hand_id="defence.shield"),
        _build(characteristics=DURABLE, armour_id="armour.gromril-armour",
               off_hand_id="defence.shield"),
        maximum_rounds=75,
    ),
    # Archetype matrix: profiles x equipment families beyond the five core ones.
    BenchmarkScenario(
        "elite-vs-durable",
        _build(characteristics=Characteristics(5, 4, 4, 2, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
        _build(characteristics=DURABLE, armour_id="armour.gromril-armour",
               off_hand_id="defence.shield"),
    ),
    BenchmarkScenario(
        "axes-vs-light",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.axe"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               armour_id="armour.light-armour"),
    ),
    BenchmarkScenario(
        "glass-vs-tank",
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2)),
        _build(characteristics=DURABLE, armour_id="armour.heavy-armour",
               off_hand_id="defence.shield"),
    ),
    BenchmarkScenario(
        "two-weapons-vs-parry",
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               off_hand_id="weapon.dagger"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               off_hand_id="defence.buckler"),
    ),
    BenchmarkScenario(
        "heavy-clash",
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
    ),
    BenchmarkScenario(
        "fencer-mirror",
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    BenchmarkScenario(
        "brute-vs-fencer",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.axe"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    BenchmarkScenario(
        "ithilmar-duel",
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               armour_id="armour.ithilmar-armour"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               armour_id="armour.ithilmar-armour"),
    ),
    # Mechanic-coverage extension (2026-09-04): each pair targets an engine
    # behaviour family the profile/equipment archetypes above never exercise.
    # They were selected with a coverage fingerprint (distinct effect axes)
    # against the catalogue; together they lift the matrix from 29 to ~100
    # distinct axes.  NumPy matches the modular oracle on every pair at 10k
    # duels; the native port still lags on several (see
    # docs/tasks/generate-test-reports.md, "Current status").
    # 1. Undead family: sigmarite hammer bonus vs undead_or_possessed,
    #    poison immunity and ignore-pain injury resolution.
    BenchmarkScenario(
        "sigmarite-vs-undead",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.sigmarite-hammer"),
        _build(band_id="tomb-guardians", profile_id="skeleton-warriors"),
    ),
    # 2. Regeneration (4+) blocked by fire: troll vs a burning brazier-iron.
    BenchmarkScenario(
        "regen-vs-fire",
        _build(band_id="orc-mob", profile_id="troll"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.brazier-iron"),
    ),
    # 3. Natural armour negated by magic + magical attacks + extra bite:
    #    lizardmen scaly skin vs a carnival daemon's attack.magical.
    BenchmarkScenario(
        "natural-armour-vs-magic",
        _build(band_id="lizardmen", profile_id="saurus-braves"),
        _build(band_id="carnival-of-chaos", profile_id="plague-bearers"),
    ),
    # 4. Pistols: ballistic-skilled shot, fixed strength, armour
    #    penetration and the crack-shot first-round path vs a parry defence.
    BenchmarkScenario(
        "pistol-vs-parry",
        _build(characteristics=VETERAN, main_weapon_id="weapon.duelling-pistol"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    # 5. Concussion + critical-injury bonus vs dwarfs: concussion
    #    immunity, hard-to-kill and the out-of-action threshold of 6.
    BenchmarkScenario(
        "concussion-vs-dwarf",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.draich"),
        _build(band_id="dwarf-rangers", profile_id="beardlings"),
    ),
    # 6. Frenzy + always strikes first: fanatic priority 10 and its
    #    frenzy-boosted attacks vs a shielded heavy.
    BenchmarkScenario(
        "frenzy-vs-heavy",
        _build(band_id="night-goblins-mic", profile_id="fanatics"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe",
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
    ),
    # 7. Paired poisoned blades (black-lotus auto-wound) vs a poison-
    #    immune undead beast: poison-blocked and paired-attack paths.
    BenchmarkScenario(
        "paired-poison-vs-undead",
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.weeping-blades"),
        _build(band_id="undead", profile_id="dire-wolves"),
    ),
    # 8. Two-handed great weapon: strength bonus, both hands occupied,
    #    initiative penalty vs gromril armour and a shield.
    BenchmarkScenario(
        "great-weapon-vs-tank",
        _build(characteristics=Characteristics(4, 5, 4, 2, 2, 1),
               main_weapon_id="weapon.double-handed-weapon"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               armour_id="armour.gromril-armour", off_hand_id="defence.shield"),
    ),
    # 9. Ward save vs a magical attacker: enchanted skins against a
    #    daemon's attack.magical (also cloud of flies, poison immunity).
    BenchmarkScenario(
        "ward-vs-magic",
        _build(characteristics=VETERAN, main_weapon_id="weapon.sword",
               defence_ids=("defence.enchanted-skins",)),
        _build(band_id="carnival-of-chaos", profile_id="nurglings"),
    ),
    # 10. Unarmed combat: fists/natural attacks, unarmed criticals and
    #     the monk strictures vs a cannot-be-parried whip.
    BenchmarkScenario(
        "unarmed-vs-steel",
        _build(band_id="battle-monks-of-cathay", profile_id="dragon-monks"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.steel-whip"),
    ),
    # 11. Injury profile 1 (out of action on 4+) vs an armour-ignoring
    #     weapon with an injury modifier (death-knife).
    BenchmarkScenario(
        "injury-profile-vs-death-knife",
        _build(band_id="night-goblins-web", profile_id="snotlings"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.death-knife"),
    ),
    # 12. Entangle: the chained squig's fixed-strength, cannot-be-parried
    #     attack entangles its victim vs a parrying fencer.
    BenchmarkScenario(
        "entangle-vs-fencer",
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.chained-squig"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    # Timing and parry amplifiers (2026-09-04): pairs selected so the
    # failure classes found in the first deep certification (natural-6
    # parry waste, stunned-defender follow-up, frenzy re-doubling,
    # per-round timing drift on grinds) are exercised at higher
    # statistical power than the profile archetypes above.  The
    # truncation sweep covers every deep pair, so resolution-timing
    # defects show at intermediate horizons even when aggregate rates
    # agree.
    # 13. Four hits per pool vs a single parry: the unparryable
    #     natural-6 co-occurrence (6 + another hit in the same pool)
    #     fires far more often than in two-weapons-vs-parry, so a
    #     wasted parry on a 6 moves the first-winner rate measurably.
    BenchmarkScenario(
        "triple-weapon-vs-parry",
        _build(characteristics=Characteristics(4, 4, 3, 2, 4, 3),
               main_weapon_id="weapon.axe", off_hand_id="weapon.dagger"),
        _build(characteristics=Characteristics(4, 3, 3, 1, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    # 14. Two attacks vs a W1 injury-profile-1 defender: the first
    #     attack stuns at 0 wounds in roughly a quarter of the duels,
    #     so the follow-up attack's stunned-defender auto-out-of-action
    #     path is heavily exercised (visible at the round-1/round-2
    #     horizons of the truncation sweep).
    BenchmarkScenario(
        "a2-vs-w1-stun",
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe"),
        _build(band_id="night-goblins-web", profile_id="snotlings"),
    ),
    # 15. Frenzy amplifier with a measurable rare-win rate: the fanatic
    #     keeps frenzy + always-strikes-first, but the defender drops
    #     its armour so the fanatic's base rate rises from ~2% to ~8%
    #     (no W2+frenzy profile exists; every frenzy grant is a W1
    #     profile rule).  A relative frenzy defect is far above the
    #     six-sigma gate at this base rate.
    BenchmarkScenario(
        "frenzy-vs-w2",
        _build(band_id="night-goblins-mic", profile_id="fanatics"),
        _build(characteristics=VETERAN, main_weapon_id="weapon.axe"),
    ),
    # 16. Mirror of elite-vs-durable with the durable side first: the
    #     unresolved rate stays ~1%, so the timing class is certified
    #     from both directions and any direction-dependent drift shows.
    BenchmarkScenario(
        "durable-vs-elite",
        _build(characteristics=DURABLE, armour_id="armour.gromril-armour",
               off_hand_id="defence.shield"),
        _build(characteristics=Characteristics(5, 4, 4, 2, 5, 2),
               main_weapon_id="weapon.sword", off_hand_id="defence.buckler"),
    ),
    # 17. Heavy grind at 75 rounds: both sides W3/T4, heavy armour and
    #     shield; ~14% of duels reach the horizon.  Per-round
    #     accumulation is maximised, so timing/orchestration drift in
    #     the resolution ledger shows at the long horizons.
    BenchmarkScenario(
        "heavy-grind",
        _build(characteristics=Characteristics(3, 3, 4, 3, 3, 1),
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
        _build(characteristics=Characteristics(3, 3, 4, 3, 3, 1),
               armour_id="armour.heavy-armour", off_hand_id="defence.shield"),
        maximum_rounds=75,
    ),

)


def deep_test_scenarios() -> tuple[BenchmarkScenario, ...]:
    """Return the deep-testing scenario matrix (standard + archetype pairs).

    Every pair is a complete legal duel construction (compile-time checked);
    together they sweep profiles (glass cannon, brute, elite, tank, undead,
    dwarfs, trolls, lizardmen, daemons, goblins, monks), weapon families
    (single, dual, paired, parrying, two-handed, unarmed, pistols, whips,
    entangling), defence mechanics (parry, shields, ward, helmets, natural
    armour, regeneration, poison immunity) and stateful skills
    (force-of-will, frenzy, always-strikes-first, hard-to-kill,
    concussion immunity, ignore-pain).
    """
    return DEEP_SCENARIOS


@dataclass(frozen=True, slots=True)
class DeepBenchmarkPlan:
    """Runs for a ``--deep`` benchmark: a small modular reference plus the
    vectorized grid. The modular oracle is deliberately only measured at the
    reference size so deep sweeps stay feasible."""
    vector_sizes: tuple[int, ...]
    batch_sizes: tuple[int, ...]
    modular_simulations: int
    modular_backend: str
    vector_backends: tuple[str, ...]
    runs: tuple[tuple[str, str, int, int], ...]  # (scenario id, backend, simulations, batch_size)
    excluded: tuple[dict[str, str], ...]


def deep_benchmark_plan(
    scenarios: tuple[BenchmarkScenario, ...], *,
    vector_sizes: tuple[int, ...], batch_sizes: tuple[int, ...],
    modular_simulations: int, backends: tuple[str, ...], installed: tuple[str, ...],
) -> DeepBenchmarkPlan:
    """Plan a deep benchmark run without executing anything.

    Policy: the modular engine is measured only at ``modular_simulations``
    (a reference point; it is the slow oracle). The optimized backends
    (NumPy and, when compiled, native) are swept over the full size and
    batch-size grid. ``backends`` is the requested set ("all" expands to
    numpy + native); modular is never part of the large grid.
    """
    requested = ("numpy", "native") if backends == ("all",) else backends
    excluded = []
    vector_backends = []
    for backend in ("numpy", "native"):
        if backend not in requested:
            continue
        if backend not in installed:
            excluded.append({"backend": backend,
                             "reason": "backend is not compiled in this environment"})
            continue
        vector_backends.append(backend)
    vector_backends = tuple(vector_backends)
    runs = []
    for scenario in scenarios:
        runs.append((scenario.id, "modular", modular_simulations, batch_sizes[0]))
    for scenario in scenarios:
        for simulations in vector_sizes:
            for batch_size in batch_sizes:
                for backend in vector_backends:
                    runs.append((scenario.id, backend, simulations, batch_size))
    return DeepBenchmarkPlan(
        vector_sizes, batch_sizes, modular_simulations, "modular",
        vector_backends, tuple(runs), tuple(excluded),
    )


def print_deep_benchmark_header(plan: DeepBenchmarkPlan) -> None:
    print(
        "Deep benchmark: modular reference at "
        f"{plan.modular_simulations:,} duels/scenario; "
        f"{', '.join(plan.vector_backends)} swept over sizes "
        f"{', '.join(f'{size:,}' for size in plan.vector_sizes)} x batches "
        f"{', '.join(f'{size:,}' for size in plan.batch_sizes)}."
    )


def parse_sizes(value: str | None, default: int) -> tuple[int, ...]:
    """Parse a size list such as "1k,10k 100k" into positive integers."""
    if not value or not value.strip():
        return (default,)
    sizes = []
    for token in value.replace(";", ",").replace(" ", ",").split(","):
        token = token.strip().lower()
        if not token:
            continue
        multiplier = 1
        if token.endswith("k"):
            multiplier, token = 1_000, token[:-1]
        elif token.endswith("m"):
            multiplier, token = 1_000_000, token[:-1]
        try:
            parsed = int(token) * multiplier
        except ValueError as error:
            raise ValueError(
                f"invalid size token {token!r}; use plain integers or k/m suffixes"
            ) from error
        if parsed < 1:
            raise ValueError("benchmark sizes must be positive")
        sizes.append(parsed)
    if not sizes:
        raise ValueError("no benchmark sizes provided")
    return tuple(dict.fromkeys(sizes))


def run_benchmark(
    scenario: BenchmarkScenario, *, simulations: int, batch_size: int,
    seed: int, backend: str, warmups: int, repeats: int,
    on_progress: Callable[[], None] | None = None,
) -> BenchmarkResult:
    if backend not in {"modular", "numpy", "native"}:
        raise ValueError(f"unknown benchmark backend: {backend}")
    first, second = compile_fighter(scenario.first), compile_fighter(scenario.second)
    request = DuelRequest(
        first, second, simulations, seed=seed, batch_size=batch_size,
        maximum_rounds=scenario.maximum_rounds,
    )

    def execute() -> None:
        if backend == "modular":
            simulate_modular_duel(request)
        else:
            simulate_duel(request, backend=backend)

    for _ in range(warmups):
        execute()
        if on_progress is not None:
            on_progress()
    samples = []
    for _ in range(repeats):
        started = perf_counter()
        execute()
        samples.append(perf_counter() - started)
        if on_progress is not None:
            on_progress()
    middle = median(samples)
    return BenchmarkResult(
        scenario.id, backend, simulations, batch_size, repeats, tuple(samples),
        middle, simulations / middle,
    )


def benchmark_payload(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    unavailable: tuple[dict[str, str], ...] | list[dict[str, str]], *,
    simulations: int, batch_size: int, seed: int, warmups: int, repeats: int,
) -> dict[str, object]:
    """Build a durable single-configuration benchmark artifact."""
    return {
        "schema": BENCHMARK_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": _environment(),
        "configuration": {
            "simulations": simulations, "batch_size": batch_size, "seed": seed,
            "warmups": warmups, "repeats": repeats,
        },
        "results": [asdict(item) for item in results],
        "unavailable": list(unavailable),
    }


def sweep_payload(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    unavailable: tuple[dict[str, str], ...] | list[dict[str, str]], *,
    simulation_sizes: tuple[int, ...], batch_sizes: tuple[int, ...],
    seed: int, warmups: int, repeats: int,
) -> dict[str, object]:
    """Build a durable multi-configuration sweep artifact."""
    return {
        "schema": SWEEP_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": _environment(),
        "configuration": {
            "simulation_sizes": list(simulation_sizes),
            "batch_sizes": list(batch_sizes),
            "seed": seed, "warmups": warmups, "repeats": repeats,
        },
        "results": [asdict(item) for item in results],
        "unavailable": list(unavailable),
    }


def _environment() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "processor": platform.processor(),
    }


def write_benchmark_payload(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def load_benchmark_payload(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != BENCHMARK_SCHEMA:
        raise ValueError(f"unsupported benchmark schema: {payload.get('schema')!r}")
    if not isinstance(payload.get("results"), list):
        raise ValueError("benchmark report has no results list")
    return payload


def write_report(path: Path, payload: dict[str, object]) -> None:
    """Write a benchmark or sweep payload as JSON, CSV or Markdown."""
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.casefold()
    results = payload.get("results", [])
    if suffix == ".csv":
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow([
                "scenario", "engine", "simulations", "batch_size", "repeats",
                "median_seconds", "simulations_per_second",
            ])
            for item in results:
                writer.writerow([
                    item["scenario"], item["backend"], item["simulations"],
                    item["batch_size"], item["repeats"],
                    f"{item['median_seconds']:.6f}",
                    f"{item['simulations_per_second']:.1f}",
                ])
        return
    if suffix in {".md", ".markdown"}:
        path.write_text(
            _markdown_report(payload) + "\n", encoding="utf-8")
        return
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _markdown_report(payload: dict[str, object]) -> str:
    lines = ["# Combat benchmark report", ""]
    configuration = payload.get("configuration", {})
    lines.append(f"- generated: {payload.get('generated_at', '')}")
    environment = payload.get("environment", {})
    lines.append(
        f"- environment: python {environment.get('python')}, "
        f"numpy {environment.get('numpy')}"
    )
    lines.append(f"- configuration: {json.dumps(configuration)}")
    lines.append("")
    if payload.get("comparison") is not None:
        comparison = payload["comparison"]
        lines.append(f"## Gate: {'PASS' if comparison['passed'] else 'FAIL'}")
        lines.append(f"{comparison['detail']}")
        for row in comparison["comparisons"]:
            lines.append(
                f"- {row['scenario']}/{row['backend']}: "
                f"{row['change_ratio']:+.2%} [{row['status']}]"
            )
        lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| scenario | engine | simulations | batch_size | repeats | median (s) | sim/s |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for item in payload.get("results", []):
        lines.append(
            f"| {item['scenario']} | {ENGINE_LABELS.get(item['backend'], item['backend'])} "
            f"| {item['simulations']:,} | {item['batch_size']:,} | {item['repeats']} "
            f"| {item['median_seconds']:.4f} | {item['simulations_per_second']:,.0f} |"
        )
    return "\n".join(lines)


def compare_with_baseline(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    baseline: dict[str, object], *, improvement_threshold: float = .10,
    regression_threshold: float = .05,
) -> BenchmarkGate:
    """Apply the agreed optimization gate to comparable NumPy/native results."""
    previous = {
        (str(item["scenario"]), str(item["backend"])): float(item["simulations_per_second"])
        for item in baseline["results"]
    }
    comparisons = []
    for item in results:
        if item.backend == "modular" or (item.scenario, item.backend) not in previous:
            continue
        old = previous[(item.scenario, item.backend)]
        if old <= 0:
            raise ValueError(f"invalid baseline throughput for {item.scenario}/{item.backend}")
        change = item.simulations_per_second / old - 1.0
        status = (
            "IMPROVED" if change >= improvement_threshold else
            "REGRESSED" if change < -regression_threshold else "STABLE"
        )
        comparisons.append(BenchmarkComparison(
            item.scenario, item.backend, old, item.simulations_per_second, change, status,
        ))
    improved = any(item.status == "IMPROVED" for item in comparisons)
    regressed = any(item.status == "REGRESSED" for item in comparisons)
    if not comparisons:
        detail = "no comparable NumPy/native results found in baseline"
    elif regressed:
        detail = "at least one scenario exceeds the allowed regression"
    elif not improved:
        detail = "no scenario reaches the required improvement"
    else:
        detail = "required improvement reached without disallowed regressions"
    return BenchmarkGate(bool(comparisons) and improved and not regressed,
                         improved, regressed, tuple(comparisons), detail)


def _render_rows(results, unavailable) -> tuple[list[list[str]], list[str]]:
    """Return (aligned text rows, width hints) for a results table."""
    by_key = {(item.scenario, item.backend, item.simulations, item.batch_size): item
              for item in results}
    rows: list[list[str]] = []
    keys = sorted(by_key)
    for key in keys:
        item = by_key[key]
        rows.append([
            item.scenario,
            ENGINE_LABELS.get(item.backend, item.backend),
            f"{item.simulations:,}", f"{item.batch_size:,}", str(item.repeats),
            f"{item.simulations_per_second:,.0f}",
            f"{item.median_seconds * 1_000:.1f} ms",
        ])
    notes = [f"{row.get('engine', row['backend'])} not available: {row['reason']}"
             for row in unavailable]
    return rows, notes


def print_results_table(
    results: Iterable[BenchmarkResult], unavailable,
    *, simulations: int, batch_size: int, seed: int, repeats: int,
) -> None:
    items = list(results)
    headers = ["Scenario", "Engine", "Simulations", "Batch size", "Repeats",
               "sim/s", "Median"]
    rows, notes = _render_rows(items, unavailable)
    print(
        f"Benchmark: {simulations:,} simulations per scenario and engine "
        f"(batch size {batch_size:,}, seed {seed}, median of {repeats} repeats)."
    )
    _print_ascii_table(headers, rows)
    for note in notes:
        print(note)


def print_sweep_table(
    results: Iterable[BenchmarkResult], unavailable,
    *, simulation_sizes: tuple[int, ...], batch_sizes: tuple[int, ...],
    seed: int, repeats: int,
) -> None:
    items = list(results)
    headers = ["Scenario", "Engine", "Simulations", "Batch size", "Repeats",
               "sim/s", "Median"]
    rows, notes = _render_rows(items, unavailable)
    print(
        "Benchmark sweep: "
        + ", ".join(f"{value:,} simulations" for value in simulation_sizes)
        + "; batch sizes "
        + ", ".join(f"{value:,}" for value in batch_sizes)
        + f" (seed {seed}, median of {repeats} repeats)."
    )
    _print_ascii_table(headers, rows)
    for note in notes:
        print(note)


def _print_ascii_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [max([len(headers[index])] + [len(row[index]) for row in rows])
              for index in range(len(headers))]
    def line(values: list[str]) -> str:
        return " | ".join(f"{value:<{widths[index]}}" for index, value in enumerate(values))
    print(line(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(line(row))


def print_gate(gate: BenchmarkGate, *, improvement: float, regression: float) -> None:
    print(
        f"Comparison with baseline (required improvement {improvement:g} %, "
        f"maximum regression {regression:g} %):"
    )
    for item in gate.comparisons:
        print(
            f"  {item.scenario}/{item.backend}: {item.change_ratio:+.2%} "
            f"[{item.status}]"
        )
    print(f"Performance gate: {'PASS' if gate.passed else 'FAIL'} - {gate.detail}")


class BenchmarkProgress:
    """Minimal progress bar for already-completed work units."""

    def __init__(self, total: int) -> None:
        self.total = total
        self.completed = 0
        self.rendered = False
        self._render()

    def advance(self) -> None:
        self.completed += 1
        self._render()

    def finish(self) -> None:
        if self.rendered:
            print()

    def _render(self) -> None:
        if not self.total:
            return
        width = 24
        completed = min(self.completed, self.total)
        filled = round(width * completed / self.total)
        percent = completed * 100 // self.total
        print(
            f"\rProgress: [{'#' * filled}{'-' * (width - filled)}] "
            f"{percent:3}% ({completed}/{self.total})",
            end="", flush=True,
        )
        self.rendered = True
