"""P00 read-only probe of the revised P01/P02 contract.

Confirms, against the real working-copy APIs, the four claims the contract now
makes:

1. ``compile_fighter`` turns a ``FighterBuild`` into the ``CompiledFighter`` the
   samplers accept (no build reaches an engine).
2. ``simulate_duel_observed`` returns per-row arrays for the oracle.
3. ``simulate_batch_observed`` returns per-row arrays for the candidate.
4. Row 0 of a batch **is not** a solo run with the same seed: the candidate's
   draw stream depends on the batch width because per-event draw counts depend on
   how many rows are active.  The probe measures this instead of assuming it, and
   the contract forbids using a one-row repetition as batch evidence.  What the
   contract does require, and the probe checks, is determinism: the same batch and
   seed produce identical arrays.

It also records which observables the current dataclasses actually publish, so
the contract's `INCOMPATIBLE` list is measured, not assumed.

Writes ``contract-probe.txt``.  No production file is touched.

    python -X utf8 TMP_VECTORIAL_ENGINE_2A2B/parity_update/P00-results/contract_probe.py
"""
from __future__ import annotations

import platform
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent


def main() -> int:
    import numpy as np
    from mordheim_combat.modular.duel import simulate_duel_observed
    from mordheim_combat.vectorized import simulate_batch_observed
    from mordheim_construction.compiler import compile_fighter
    from mordheim_core.models import Characteristics, FighterBuild, ObservedDuelResult

    def build(initiative: int) -> FighterBuild:
        return FighterBuild(
            "mordheim",
            Characteristics(3, 3, 3, 1, initiative, 1),
            main_weapon_id="weapon.mace",
        )

    first = compile_fighter(build(3))
    second = compile_fighter(build(2))
    seed, rows, horizon = 11, 16, 6

    oracle = simulate_duel_observed(first, second, rows, seed=seed, maximum_rounds=horizon)
    candidate = simulate_batch_observed(
        first, second, rows, np.random.default_rng(seed), horizon)
    solo = simulate_batch_observed(
        first, second, 1, np.random.default_rng(seed), horizon)
    repeat = simulate_batch_observed(
        first, second, rows, np.random.default_rng(seed), horizon)

    def row(array):
        return array[0].item()

    locality = {
        "winner": (row(candidate.winner), row(solo.winner)),
        "rounds": (row(candidate.rounds), row(solo.rounds)),
        "first_wounds": (row(candidate.first_wounds), row(solo.first_wounds)),
        "second_wounds": (row(candidate.second_wounds), row(solo.second_wounds)),
        "first_condition": (row(candidate.first_condition), row(solo.first_condition)),
        "second_condition": (row(candidate.second_condition), row(solo.second_condition)),
        "first_resources": (
            tuple((name, bool(values[0])) for name, values in candidate.first_resources),
            tuple((name, bool(values[0])) for name, values in solo.first_resources),
        ),
        "second_resources": (
            tuple((name, bool(values[0])) for name, values in candidate.second_resources),
            tuple((name, bool(values[0])) for name, values in solo.second_resources),
        ),
    }
    mismatch = {name: pair for name, pair in locality.items() if pair[0] != pair[1]}
    deterministic = all(
        np.array_equal(getattr(candidate, name), getattr(repeat, name))
        for name in ("winner", "rounds", "first_wounds", "second_wounds",
                     "first_condition", "second_condition")
    )

    def published(dataclass_type) -> list[str]:
        return [field for field in dataclass_type.__dataclass_fields__]

    shapes_mismatch = {
        **{name: int(len(getattr(oracle, name))) for name in
           ("winner", "resolution_rounds", "first_wounds", "second_wounds",
            "first_condition", "second_condition")
           if len(getattr(oracle, name)) != rows},
        **{name: int(len(getattr(candidate, name))) for name in
           ("winner", "rounds", "first_wounds", "second_wounds",
            "first_condition", "second_condition")
           if len(getattr(candidate, name)) != rows},
    }

    lines = [
        "P00 contract probe (read-only)",
        f"python={platform.python_version()} numpy={np.__version__}",
        f"fighter_build_compiled={type(first).__name__}",
        f"rows={rows} seed={seed} horizon={horizon}",
        f"oracle_type={type(oracle).__name__} candidate_type={type(candidate).__name__}",
        "",
        "oracle_published_fields=" + ",".join(published(ObservedDuelResult)),
        "candidate_published_fields=" + ",".join(published(type(candidate))),
        "",
        "oracle_row_lengths=" + str({
            name: int(len(getattr(oracle, name)))
            for name in ("winner", "resolution_rounds", "first_wounds",
                         "second_wounds", "first_condition", "second_condition")
        }),
        "candidate_row_lengths=" + str({
            name: int(len(getattr(candidate, name)))
            for name in ("winner", "rounds", "first_wounds", "second_wounds",
                         "first_condition", "second_condition")
        }),
        "",
        # Measured, not required: the candidate derives draws per active-row set,
        # so changing the batch width changes row 0's stream.
        f"row0_equals_solo={not mismatch} (measured; batch width changes the stream)",
    ]
    if mismatch:
        lines += [f"  differs {name}: batch={pair[0]} solo={pair[1]}"
                  for name, pair in mismatch.items()]
    lines += [
        f"repeat_is_deterministic={deterministic}",
        f"shape_mismatch={shapes_mismatch or 'none'}",
        "",
        "Observed dataclasses publish resources/psychology?",
        f"  ObservedDuelResult: resources={'resources' in published(ObservedDuelResult)} "
        f"psychology={'frenzy' in published(ObservedDuelResult)}",
    ]
    text = "\n".join(lines) + "\n"
    (RESULTS / "contract-probe.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0 if deterministic and not shapes_mismatch else 1


if __name__ == "__main__":
    sys.exit(main())
