"""mordheim_combat_lab.verification.parity: executable oracle contract.

The parity tooling lives in layered submodules: report payloads, the
vectorized obligation inventory, the single-sample comparator and the shared
statistical runner.  The runner serves the deep matrix, the battery and the
round-truncation sweep directly; there are no per-layer execution adapters.
"""
from mordheim_combat_lab.verification.parity._report import (
    BATTERY_SCHEMA,
    ParityObligation,
    ParityReport,
    StatisticalParityResult,
    battery_failure_kind,
    battery_report_markdown,
    battery_report_payload,
    parity_report_markdown,
    parity_report_payload,
)
from mordheim_combat_lab.verification.parity._vectorized import verify_vectorized_parity
from mordheim_combat_lab.verification.parity._statistical import compare_statistical_parity
from mordheim_combat_lab.verification.parity._runner import (
    TRUNCATION_HORIZONS,
    MagnitudeComparison,
    ParityCase,
    ParityRow,
    ParityRun,
    run_parity,
    statistical_result,
)

from mordheim_combat_lab.verification.parity._replay import ReplayObservation, replay_duel
