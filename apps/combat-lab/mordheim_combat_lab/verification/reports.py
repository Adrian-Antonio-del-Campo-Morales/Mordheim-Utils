"""Shared observation failures and integration-witness identifiers."""
from __future__ import annotations


class EvidenceMismatch(AssertionError):
    """An executed observation differs from its independently authored oracle."""


INTEGRATION_CHECKS = ("actual-phase-order-and-state-transfer", "maximum-rounds-and-counts",
                      "cancellation", "seeded-reproducibility")
