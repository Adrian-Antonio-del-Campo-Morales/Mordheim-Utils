"""mordheim_combat_lab.verification.parity: executable oracle contract.

The parity tooling lives in layered submodules (report payloads,
semantic-specification adapters, vectorized obligation inventory and
statistical sampling).  This facade re-exports the historical module API
so existing importers and the CLI keep working unchanged.
"""
from mordheim_combat_lab.verification.parity._report import (
    ParityObligation,
    ParityReport,
    StatisticalParityResult,
    SpecificationParityCase,
    SpecificationParityReport,
    parity_report_markdown,
    parity_report_payload,
)
from mordheim_combat_lab.verification.parity._specifications import (
    CONSTRUCTION_SPEC_OPERATIONS,
    verify_specification_parity,
)
from mordheim_combat_lab.verification.parity._vectorized import verify_vectorized_parity
from mordheim_combat_lab.verification.parity._statistical import compare_statistical_parity
from mordheim_combat_lab.verification.parity._truncations import TRUNCATION_HORIZONS
from mordheim_combat_lab.verification.parity._truncations import compare_truncation_parity
from mordheim_combat_lab.verification.parity._deep import (
    DeepPair,
    certify_deep,
)
