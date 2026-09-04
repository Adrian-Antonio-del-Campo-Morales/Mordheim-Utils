"""Duel triage harness: isolate the first divergent rule between the modular
oracle and the vectorized NumPy driver for a failing deep-matrix pair.

Why this shape
--------------
The two production drivers do *not* share dice: the oracle consumes a scalar
SeededDice stream, the NumPy driver consumes raw Generator arrays (charge
rolls are even a d6>=4 on one side and a random()<0.5 on the other), so a
bit-for-bit per-event tape across drivers is impossible by design.  What is
comparable is behaviour: with identical logic and *any* uniform dice the two
engines must converge on the same rates.  A large rate gap is therefore a
logic difference, and the difference is attributable by differential
ablation: rebuild the same matchup with one element removed, run BOTH
engines, and watch whether the oracle-vs-numpy gap collapses.

Usage
-----
    python tools/triage-duel.py cards --pair brute-vs-fencer
    python tools/triage-duel.py ablate --pair brute-vs-fencer --simulations 20000
    python tools/triage-duel.py seeds --pair brute-vs-fencer --simulations 300
    python tools/triage-duel.py duel --pair brute-vs-fencer --seed 0

``--pair`` is any deep-matrix id from ``mordheim_combat_lab.cli.benchmarking``
(default: ``brute-vs-fencer``).  The oracle legs are run through the shared
process pool (``--workers``, default: the machine's core count) and are
bit-for-bit identical to the sequential oracle.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from dataclasses import fields
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import sys
from time import perf_counter

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mordheim_combat.modular.parallel import run_oracle_sample  # noqa: E402
from mordheim_combat.vectorized import simulate_duel as simulate_numpy  # noqa: E402
from mordheim_combat_lab.cli.benchmarking import DEEP_SCENARIOS  # noqa: E402
from mordheim_construction.compiler import compile_fighter  # noqa: E402
from mordheim_core.models import Characteristics  # noqa: E402
from mordheim_core.models import DuelRequest  # noqa: E402
from mordheim_core.models import FighterBuild  # noqa: E402

CHARACTERISTIC_FIELDS = tuple(field.name for field in fields(Characteristics))


def _scenario(pair_id: str):
    for scenario in DEEP_SCENARIOS:
        if scenario.id == pair_id:
            return scenario
    raise SystemExit(f"unknown deep scenario id: {pair_id} (choose from "
                     + ", ".join(s.id for s in DEEP_SCENARIOS) + ")")


def _stat_card(build: FighterBuild) -> dict[str, object]:
    fighter = compile_fighter(build)
    characteristics = fighter.characteristics
    main = fighter.main_weapon
    off = fighter.off_hand
    global_effects = fighter.global_effects
    return {
        "characteristics": {name: getattr(characteristics, name)
                            for name in CHARACTERISTIC_FIELDS},
        "main_weapon": {
            "tags": sorted(main.tags),
            "parry": main.parry,
            "damage": main.damage,
            "two_handed": main.two_handed,
            "cannot_be_parried": main.cannot_be_parried,
            "ignore_armour": main.ignore_armour,
            "hit_modifier": main.hit_modifier,
            "wound_modifier": main.wound_modifier,
            "injury_modifier": main.injury_modifier,
            "strength_bonus": main.strength_bonus,
        },
        "off_hand": None if off is None else {
            "tags": sorted(off.tags),
            "parry": off.parry,
        },
        "global_parry_flag": global_effects.parry,
        "global_tags": sorted(global_effects.tags),
        "armour_save": fighter.armour_save,
        "helmet_save": fighter.helmet_save,
        "injury_profile": fighter.injury_profile,
        "off_hand_attacks": fighter.off_hand_attacks,
    }


def cards(pair_id: str) -> None:
    scenario = _scenario(pair_id)
    print(f"scenario: {scenario.id}  (maximum_rounds={scenario.maximum_rounds})")
    for label, build in (("first", scenario.first), ("second", scenario.second)):
        print(f"\n{label} build: band={build.band_id or 'custom'} "
              f"profile={build.profile_id or 'custom'}")
        card = _stat_card(build)
        print(json.dumps(card, indent=2, default=str))


def _rate_leg(first: CompiledFighter, second: CompiledFighter, simulations: int,
              maximum_rounds: int, workers: int, executor) -> tuple[float, float, float]:
    """Return (oracle_first, numpy_first, numpy_unresolved) as percentages."""
    oracle = run_oracle_sample(
        first, second, simulations, seed=1, maximum_rounds=maximum_rounds,
        workers=workers, executor=executor,
    )
    numpy = simulate_numpy(DuelRequest(
        first, second, simulations, seed=1,
        batch_size=max(simulations, 1), maximum_rounds=maximum_rounds,
    ), backend="numpy")
    return oracle.first_win_rate, numpy.first_win_rate, numpy.unresolved_rate


def ablate(pair_id: str, simulations: int, workers: int) -> None:
    scenario = _scenario(pair_id)
    first, second = scenario.first, scenario.second

    def vary(build: FighterBuild, **changes):
        if "characteristics" in changes:
            changes["characteristics"] = replace(
                build.characteristics, **changes["characteristics"])
        return replace(build, **changes)

    legs: list[tuple[str, FighterBuild, FighterBuild]] = [("baseline", first, second)]
    brute, fencer = first, second
    # The sword itself carries parry; the buckler only adds the sword+buckler
    # reroll.  Stripping parry therefore means swapping the sword for a dagger
    # (and dropping the buckler).  The dagger keeps the fencer's S3 profile.
    no_parry = {"main_weapon_id": "weapon.dagger", "off_hand_id": None}
    legs.append(("fencer-no-parry", brute, vary(fencer, **no_parry)))
    legs.append(("fencer-no-buckler-reroll", brute,
                 vary(fencer, off_hand_id=None)))
    legs.append(("brute-sword", vary(brute, main_weapon_id="weapon.sword"), fencer))
    legs.append(("both-stripped", vary(brute, main_weapon_id="weapon.sword"),
                 vary(fencer, **no_parry)))
    legs.append(("fencer-wounds-2", brute, vary(
        fencer, characteristics={"wounds": 2})))
    legs.append(("fencer-initiative-2", brute, vary(
        fencer, characteristics={"initiative": 2})))
    legs.append(("fencer-attacks-1", brute, vary(
        fencer, characteristics={"attacks": 1})))
    # Ordering axis: with I5 vs I2 the fencer always strikes first.  Equal
    # initiative randomises the order each round; reversed order flips it.
    legs.append(("fencer-i4", brute, vary(fencer, characteristics={"initiative": 4})))
    legs.append(("fencer-i3", brute, vary(fencer, characteristics={"initiative": 3})))
    legs.append(("fencer-i1", brute, vary(fencer, characteristics={"initiative": 1})))
    legs.append(("brute-i5", vary(brute, characteristics={"initiative": 5}), fencer))
    legs.append(("brute-i3", vary(brute, characteristics={"initiative": 3}), fencer))
    # Residual drivers isolated under equal initiative.
    equal_i = {"characteristics": {"initiative": 2}}
    legs.append(("i2+no-parry", brute, vary(vary(fencer, **no_parry), **equal_i)))
    legs.append(("i2+wounds-2", brute, vary(vary(fencer, **equal_i),
                                            characteristics={"wounds": 2})))

    print(f"pair: {pair_id}  duels/engine/leg: {simulations}  "
          f"oracle workers: {workers}")
    print(f"{'leg':<22} {'oracle first %':>14} {'numpy first %':>14} "
          f"{'gap pp':>9}  6sigma pp")
    available = workers if workers and workers > 1 else (os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=min(available, len(legs))) as pool:
        for label, first_build, second_build in legs:
            started = perf_counter()
            oracle_first, numpy_first, _ = _rate_leg(
                compile_fighter(first_build), compile_fighter(second_build),
                simulations, scenario.maximum_rounds, min(available, len(legs)),
                pool,
            )
            gap = oracle_first - numpy_first
            tolerance = 600.0 * (0.5 / (simulations ** 0.5))  # six sigma, worst case
            print(f"{label:<22} {oracle_first:>13.2f}% {numpy_first:>13.2f}% "
                  f"{gap:>8.2f}  +-{tolerance / 100:4.2f}pp "
                  f"({perf_counter() - started:.1f}s)")


def rounds_sweep(pair_id: str, simulations: int, workers: int) -> None:
    """Cumulative rate gap per truncation round: where does the divergence start?

    Runs both engines with ``maximum_rounds = r`` for each r.  If the gap is
    zero for r = 1 and appears only from round k on, the divergent rule fires
    around round k.
    """
    scenario = _scenario(pair_id)
    first = compile_fighter(scenario.first)
    second = compile_fighter(scenario.second)
    maximum = scenario.maximum_rounds
    available = workers if workers and workers > 1 else (os.cpu_count() or 1)
    print(f"pair: {pair_id}  duels/engine/point: {simulations}  "
          f"truncation rounds: 1..{maximum}")
    print(f"{'max rounds':>11} {'oracle first %':>14} {'numpy first %':>14} {'gap pp':>9}")
    with ProcessPoolExecutor(max_workers=min(available, maximum)) as pool:
        for rounds in range(1, maximum + 1):
            oracle_first, numpy_first, _ = _rate_leg(
                first, second, simulations, rounds, min(available, maximum), pool,
            )
            print(f"{rounds:>11} {oracle_first:>13.2f}% {numpy_first:>13.2f}% "
                  f"{oracle_first - numpy_first:>8.2f}")


def states(pair_id: str, simulations: int, workers: int) -> None:
    """Per-truncation micro-state comparison: mean wounds + condition shares.

    Winner rates alone can hide where a divergence lives.  These marginal
    statistics (mean wounds per side, share of each condition at truncation)
    are dice-integrated, so they are directly comparable between the modular
    oracle and the NumPy driver even though the two consume different dice
    streams.
    """
    scenario = _scenario(pair_id)
    first = compile_fighter(scenario.first)
    second = compile_fighter(scenario.second)
    from mordheim_combat.modular.duel import initialize_duel
    from mordheim_combat.modular import rounds as modular_rounds
    from mordheim_core.dice import SeededDice
    from mordheim_combat.vectorized._driver import simulate_batch_observed
    from mordheim_combat.vectorized._types import (
        KNOCKED_DOWN, STUNNED, OUT, STANDING, PARALYZED,
    )
    CONDITION_NAMES = {STANDING: "STAND", KNOCKED_DOWN: "KD",
                       STUNNED: "STUN", PARALYZED: "PARA", OUT: "OUT"}
    maximum = scenario.maximum_rounds

    def oracle_state(rounds: int) -> tuple[list[int], list[int], np.ndarray, np.ndarray]:
        """Return (first wins, second wins, conds1, conds2, wounds1, wounds2) aggregated."""
        w1 = np.zeros(simulations, dtype=np.int16)
        w2 = np.zeros(simulations, dtype=np.int16)
        c1 = np.zeros(simulations, dtype=np.int8)
        c2 = np.zeros(simulations, dtype=np.int8)
        first_wins = second_wins = 0
        for index in range(simulations):
            dice = SeededDice(1 + index)
            state = initialize_duel(first, second, dice)
            for _ in range(rounds):
                if not state.first.active or not state.second.active:
                    break
                state = modular_rounds.resolve_round(
                    first, second, state, dice, None).state
            w1[index] = state.first.wounds
            w2[index] = state.second.wounds
            c1[index] = int(state.first.condition)
            c2[index] = int(state.second.condition)
            if state.first.active and not state.second.active:
                first_wins += 1
            elif state.second.active and not state.first.active:
                second_wins += 1
        return first_wins, second_wins, c1, c2, w1, w2

    def numpy_state(rounds: int):
        obs = simulate_batch_observed(
            first, second, simulations, np.random.default_rng(1),
            rounds,
        )
        return (int((obs.winner == 1).sum()), int((obs.winner == -1).sum()),
                obs.first_condition, obs.second_condition,
                obs.first_wounds, obs.second_wounds)

    print(f"pair: {pair_id}  duels/engine/point: {simulations}  workers: {workers}")
    print("rounds | oracle fw% numpy fw% | mean w1/w2 orc vs np | "
          "cond shares oracle vs numpy | FIRST |         |   SECOND")
    for rounds in range(1, maximum + 1):
        ofw, osw, oc1, oc2, ow1, ow2 = oracle_state(rounds)
        nfw, nsw, nc1, nc2, nw1, nw2 = numpy_state(rounds)
        def shares(conditions: np.ndarray) -> str:
            return '/'.join(f"{name}:{(conditions == code).mean() * 100:.1f}"
                            for code, name in CONDITION_NAMES.items())
        oracle_first = shares(oc1)
        oracle_second = shares(oc2)
        numpy_first = shares(nc1)
        numpy_second = shares(nc2)
        print(
            f"{rounds:>3} | {100 * ofw / simulations:8.2f} {100 * nfw / simulations:8.2f} | "
            f"{ow1.mean():5.2f}/{ow2.mean():5.2f} {nw1.mean():5.2f}/{nw2.mean():5.2f} | ",
            end="",
        )
        print(f"{oracle_first}", end="")
        print(f" {oracle_second}", end="")
        print(f" || {numpy_first}", end="")
        print(f" {numpy_second}")


def seeds(pair_id: str, simulations: int) -> None:
    """Probe per-seed single-duel agreement between the two drivers."""
    scenario = _scenario(pair_id)
    first = compile_fighter(scenario.first)
    second = compile_fighter(scenario.second)
    agreed = disagreed = 0
    first_disagreements = []
    started = perf_counter()
    for seed in range(simulations):
        oracle = run_oracle_sample(first, second, 1, seed=seed,
                                   maximum_rounds=scenario.maximum_rounds,
                                   workers=None)
        numpy = simulate_numpy(DuelRequest(
            first, second, 1, seed=seed,
            batch_size=1, maximum_rounds=scenario.maximum_rounds,
        ), backend="numpy")
        oracle_outcome = 0 if oracle.first_wins else 1 if oracle.second_wins else 2
        numpy_outcome = 0 if numpy.first_wins else 1 if numpy.second_wins else 2
        if oracle_outcome == numpy_outcome:
            agreed += 1
        else:
            disagreed += 1
            if len(first_disagreements) < 10:
                first_disagreements.append((seed, oracle_outcome, numpy_outcome))
    print(f"pair: {pair_id}  single-duel probes: {simulations}  "
          f"({perf_counter() - started:.1f}s)")
    print(f"outcome agreement: {agreed}  disagreement: {disagreed}  "
          f"({100.0 * disagreed / simulations:.1f}%)")
    outcome_names = {0: "first wins", 1: "second wins", 2: "unresolved"}
    for seed, oracle_outcome, numpy_outcome in first_disagreements:
        print(f"  seed {seed:>4}: oracle={outcome_names[oracle_outcome]:<12} "
              f"numpy={outcome_names[numpy_outcome]}")


class _LoggingRng:
    """Wrap a NumPy Generator and record every driver draw with its caller."""

    def __init__(self, rng: np.random.Generator):
        self._rng = rng
        self.log: list[tuple[str, str, str, object]] = []

    def _record(self, method: str, size, kwargs):
        caller = sys._getframe(2).f_code.co_name
        entry = (caller, method, f"size={size}", None)
        self.log.append(entry)
        return entry

    def integers(self, low, high=None, size=None, dtype=None):
        entry = self._record("integers", size, {})
        if high is None:
            high = low
            low = 1
        try:
            if dtype is None:
                values = self._rng.integers(low, high, size=size)
            else:
                values = self._rng.integers(low, high, size=size, dtype=dtype)
        except TypeError:
            raise TypeError(
                f"wrapper integers({low!r}, {high!r}, size={size!r}, "
                f"dtype={dtype!r})"
            ) from None
        entry = entry[:3] + (f"->[{','.join(map(str, np.atleast_1d(values)))}]",)
        self.log[-1] = entry
        return values

    def random(self, size=None):
        entry = self._record("random", size, {})
        values = self._rng.random(size=size)
        entry = entry[:3] + (f"->[{','.join(map(str, np.atleast_1d(values)))}]",)
        self.log[-1] = entry
        return values


def bisect(pair_id: str, simulations: int) -> None:
    """Find the earliest truncation round where each seed's outcome diverges.

    For every seed the duel is deterministic in each engine, so running both
    engines with ``maximum_rounds = r`` for increasing r finds the round in
    which the two trajectories first disagree (or ``agree`` if they never
    do within the scenario's round budget).
    """
    scenario = _scenario(pair_id)
    first = compile_fighter(scenario.first)
    second = compile_fighter(scenario.second)
    maximum = scenario.maximum_rounds
    counts: dict[int | str, int] = {}
    examples: dict[int, list[int]] = {}
    started = perf_counter()
    for seed in range(simulations):
        first_divergence = None
        for rounds in range(1, maximum + 1):
            oracle = run_oracle_sample(first, second, 1, seed=seed,
                                       maximum_rounds=rounds, workers=None)
            numpy = simulate_numpy(DuelRequest(
                first, second, 1, seed=seed, batch_size=1,
                maximum_rounds=rounds,
            ), backend="numpy")
            oracle_outcome = 0 if oracle.first_wins else 1 if oracle.second_wins else 2
            numpy_outcome = 0 if numpy.first_wins else 1 if numpy.second_wins else 2
            if oracle_outcome != numpy_outcome:
                first_divergence = rounds
                break
        label: int | str = first_divergence if first_divergence is not None else "agree"
        counts[label] = counts.get(label, 0) + 1
        examples.setdefault(label, []).append(seed)
    print(f"pair: {pair_id}  seeds probed: {simulations}  "
          f"({perf_counter() - started:.1f}s)")
    print(f"{'first divergent round':<22} {'seeds':>6}   example seeds")
    for label in sorted((k for k in counts if isinstance(k, int))) + ["agree"]:
        if label not in counts:
            continue
        print(f"{label:<22} {counts[label]:>6}   {examples[label][:6]}")


def _modular_event_log(first: CompiledFighter, second: CompiledFighter,
                       seed: int, maximum_rounds: int) -> list[tuple[str, int, str]]:
    """Run one oracle duel and log (key, value, outcome label) per roll.

    The outcome label is derived from the semantic key (attack index, phase)
    so the per-duel event structure is comparable to the NumPy draw log even
    though the two engines consume different dice.
    """
    from mordheim_combat.modular.duel import initialize_duel
    from mordheim_combat.modular import rounds as modular_rounds
    from mordheim_combat.modular.state import AttackOutcome
    from mordheim_core.dice import RollRequest

    class _LoggingDice:
        def __init__(self, rng):
            self._rng = rng
            self.items: list[tuple[str, int, str]] = []

        def roll(self, request: RollRequest) -> int:
            value = int(self._rng.integers(1, request.sides + 1))
            self.items.append((request.key, value, ""))
            return value

    dice = _LoggingDice(np.random.default_rng(seed))
    state = initialize_duel(first, second, dice)
    for round_index in range(maximum_rounds):
        if not state.first.active or not state.second.active:
            break
        state = modular_rounds.resolve_round(first, second, state, dice, None).state
        dice.items.append((f"round.{round_index}.END", 0,
                           f"w1={state.first.wounds} c1={int(state.first.condition)} "
                           f"w2={state.second.wounds} c2={int(state.second.condition)}"))
    winner = "unresolved"
    if state.first.active and not state.second.active:
        winner = "first wins"
    elif state.second.active and not state.first.active:
        winner = "second wins"
    dice.items.append(("DUEL.END", 0, winner))
    return dice.items


def duel(pair_id: str, seed: int, rounds: int) -> None:
    """Run one seed on both drivers and dump both dice-consumption logs.

    The modular oracle logs semantic roll keys; the NumPy driver logs raw
    draws tagged by phase function.  The two engines do NOT share dice, so
    values differ — but the *structure* (which phase drew how many dice, in
    what order) must mirror if the logic is identical.  The first structural
    mismatch is the first divergent rule.
    """
    scenario = _scenario(pair_id)
    first = compile_fighter(scenario.first)
    second = compile_fighter(scenario.second)
    from mordheim_combat.vectorized._driver import _simulate_batch_core

    tracer = _LoggingRng(np.random.default_rng(seed))
    state = _simulate_batch_core(first, second, 1, tracer,
                                 rounds, observe=False)
    oracle_items = _modular_event_log(first, second, seed, rounds)
    print(f"pair: {pair_id} seed: {seed}  maximum_rounds: {rounds}\n")
    print(f"--- modular oracle event log ({len(oracle_items)} items)")
    for key, value, label in oracle_items:
        print(f"  {key:<58} d{value:<2} {label}")
    print(f"\n--- numpy draw log ({len(tracer.log)} items) outcome: {state}")
    for index, (caller, method, size, values) in enumerate(tracer.log):
        print(f"  {index:>3} {caller:<28} {method:<9} {size:<12} {values}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",
                        choices=("cards", "ablate", "seeds", "duel", "rounds",
                                 "bisect", "states"))
    parser.add_argument("--pair", default="brute-vs-fencer")
    parser.add_argument("--simulations", type=int, default=20_000)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rounds", type=int, default=100)
    args = parser.parse_args()

    if args.command == "cards":
        cards(args.pair)
    elif args.command == "ablate":
        ablate(args.pair, args.simulations,
               args.workers or (os.cpu_count() or 1))
    elif args.command == "seeds":
        seeds(args.pair, min(args.simulations, 2_000))
    elif args.command == "rounds":
        rounds_sweep(args.pair, min(args.simulations, 15_000),
                     args.workers or (os.cpu_count() or 1))
    elif args.command == "duel":
        duel(args.pair, args.seed, args.rounds)
    elif args.command == "bisect":
        bisect(args.pair, min(args.simulations, 400))
    elif args.command == "states":
        states(args.pair, min(args.simulations, 10_000),
               args.workers or (os.cpu_count() or 1))


if __name__ == "__main__":
    main()
