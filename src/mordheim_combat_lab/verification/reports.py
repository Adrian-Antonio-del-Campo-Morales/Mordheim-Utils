"""verification.reports: responsibility extracted without altering the rules."""
from __future__ import annotations

from dataclasses import dataclass
from mordheim_combat_lab.verification.inventory import Obligation
from mordheim_combat_lab.verification.operators import OPERATOR_CHECKS
from mordheim_combat_lab.verification.interactions import InteractionAssessment


class EvidenceMismatch(AssertionError):
    """An executed observation differs from its independently authored oracle."""


REQUIRED_CASES = {
    "construction": {"accepted", "rejected", "grant"},
    "permanent": {"compiled", "consumer", "boundary"},
    "contextual": {"compiled", "active", "inactive", "boundary", "consumer"},
    "priority": {"compiled", "active", "inactive", "boundary", "consumer"},
    "local": {"compiled", "active", "inactive", "boundary", "consumer"},
    "stateful": {"compiled", "active", "inactive", "boundary", "sequence", "consumption"},
    "interaction": {"composition", "boundary"},
}


@dataclass(frozen=True)
class FixtureResult:
    id: str
    targets: tuple[str, ...]
    passed_cases: tuple[str, ...]
    killed_mutations: tuple[str, ...]
    errors: tuple[str, ...]
    justified_mutations: tuple[str, ...] = ()


@dataclass(frozen=True)
class SemanticReport:
    obligations: tuple[Obligation, ...]
    fixtures: tuple[FixtureResult, ...]
    verified: tuple[str, ...]
    pending: tuple[tuple[str, str], ...]
    errors: tuple[str, ...]
    unclassified_bindings: tuple[str, ...] = ()
    pending_interactions: tuple[tuple[str, str], ...] = ()
    verified_interactions: tuple[tuple[str, str], ...] = ()
    passed_integrations: tuple[str, ...] = ()
    passed_operator_checks: tuple[str, ...] = ()
    verified_higher_order_interactions: tuple[tuple[str, ...], ...] = ()
    pending_higher_order_interactions: tuple[tuple[str, ...], ...] = ()
    interaction_assessments: tuple[InteractionAssessment, ...] = ()
    interaction_policy: str = "critical_and_high_required"

    @property
    def required_pending_interactions(self) -> tuple[InteractionAssessment, ...]:
        return tuple(item for item in self.interaction_assessments
                     if item.verification_requirement == "required"
                     and item.status not in {"tested", "covered_by_composition", "independent", "illegal"})

    @property
    def semantic_complete(self) -> bool:
        return (bool(self.obligations) and not self.pending and not self.errors
                and not self.required_pending_interactions
                and set(self.passed_integrations) == set(INTEGRATION_CHECKS)
                and set(self.passed_operator_checks) == set(OPERATOR_CHECKS)
                and not self.pending_higher_order_interactions)


INTEGRATION_CHECKS = ("actual-phase-order-and-state-transfer", "maximum-rounds-and-counts",
                      "cancellation", "seeded-reproducibility")
