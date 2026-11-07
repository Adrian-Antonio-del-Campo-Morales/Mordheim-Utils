"""mordheim_combat_lab.verification.parity: executable oracle contract.

Layered submodules: the report payloads, the vectorized obligation inventory,
the single-sample comparator and the one statistical runner, which serves
every selection (precompiled scenarios, E2E deliveries, battery cases).
"""
from mordheim_combat_lab.verification.parity._report import (
    UNDERPOWERED,
    ParityObligation,
    ParityReport,
    StatisticalParityResult,
    parity_report_markdown,
    parity_report_payload,
    power_verdict,
)
from mordheim_combat_lab.verification.parity._vectorized import verify_vectorized_parity
from mordheim_combat_lab.verification.parity._statistical import compare_samples
from mordheim_combat_lab.verification.parity._statistical import compare_statistical_parity
from mordheim_combat_lab.verification.parity._runner import (
    MagnitudeComparison,
    ParityCase,
    ParityRow,
    ParityRun,
    parity_row,
    run_parity,
    statistical_result,
)

from mordheim_combat_lab.verification.parity._replay import ReplayObservation, replay_duel
