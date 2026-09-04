"""Round-truncation outcome parity: where do oracle and candidate part ways?

The aggregate rates of ``compare_statistical_parity`` compare only the duel
*end state*.  Orchestration defects — wrong acting order, a suppressed reply
phase, a stateful recovery resolved at the wrong moment — change *when*
duels resolve, and that shift shows up at some intermediate horizon long
before the final winner rates move beyond noise.

This module certifies the outcome distributions at a set of round horizons:
for every horizon ``h`` both engines run the pair with ``maximum_rounds = h``
and the three outcome rates (first wins / second wins / unresolved) must stay
within the same six-sigma gate as the full-horizon samples.  Outcome after
exactly ``h`` rounds is engine-agnostic — a duel that has not resolved by
horizon ``h`` counts as unresolved in both drivers, whatever internal ledger
they keep — so no round-counting convention leaks into the comparison (see
``docs/testing-strategy.md``, round-ledger notes).  A defect that shifts
resolution timing pushes one or more horizon rows apart while the final
marginals still agree.
"""
from __future__ import annotations

from mordheim_core.models import CompiledFighter
from mordheim_combat_lab.verification.parity._report import StatisticalParityResult
from mordheim_combat_lab.verification.parity._statistical import compare_statistical_parity

#: Horizons swept by a truncation certification.  The long 75-round pair
#: keeps only horizons up to its own budget (filtered by the caller).
TRUNCATION_HORIZONS = (2, 4, 6, 8, 10, 12, 15, 20)


from collections.abc import Callable
import time

from mordheim_core.models import CompiledFighter
from mordheim_combat_lab.verification.parity._report import StatisticalParityResult
from mordheim_combat_lab.verification.parity._statistical import compare_statistical_parity


def compare_truncation_parity(
    scenario: str, first: CompiledFighter, second: CompiledFighter,
    simulations: int, *, seed: int = 2026, maximum_rounds: int = 50,
    horizons: tuple[int, ...] = TRUNCATION_HORIZONS,
    backend: str = "numpy", workers: object | None = None,
    on_progress: Callable[[], None] | None = None,
) -> tuple[StatisticalParityResult, ...]:
    """Certify the outcome rates at every truncation horizon up to the duel's
    round budget, each with its own independent oracle and candidate sample.

    Rows are labelled ``<scenario>@rounds=<h>`` so a failing horizon names
    the round at which the divergence starts.  ``backend`` selects the
    optimized candidate (``"numpy"`` or ``"native"``), mirroring the
    aggregate comparisons.  ``workers`` applies the same oracle pooling
    policy as the deep layer (``None``/``"auto"`` pools only samples whose
    estimated sequential time exceeds the gate; ``1`` stays sequential), and
    ``on_progress`` is invoked once per completed horizon row.
    """
    if simulations < 1:
        raise ValueError("truncation parity needs at least one simulation")
    if backend not in {"numpy", "native"}:
        raise ValueError(f"unknown optimized backend: {backend}")
    effective = tuple(sorted({h for h in horizons if 1 <= h <= maximum_rounds}))
    if not effective:
        raise ValueError("no truncation horizon fits the round budget")
    from mordheim_combat.modular.parallel import resolve_oracle_workers
    from mordheim_combat.modular.parallel import run_oracle_sample

    rows = []
    for horizon in effective:
        # One modular oracle sample certifies the candidate at this horizon,
        # exactly like the deep layer (bit-for-bit identical to the
        # sequential path whatever the pooling policy).
        chosen = resolve_oracle_workers(workers, simulations, horizon)
        oracle_started = time.perf_counter()
        modular = run_oracle_sample(
            first, second, simulations, seed=seed,
            maximum_rounds=horizon, workers=chosen,
        )
        oracle_seconds = time.perf_counter() - oracle_started
        rows.append(compare_statistical_parity(
            f"{scenario}@rounds={horizon}", first, second, simulations,
            seed=seed, maximum_rounds=horizon, backend=backend,
            modular=modular, reference_seconds=oracle_seconds,
        ))
        if on_progress is not None:
            on_progress()
    return tuple(rows)
