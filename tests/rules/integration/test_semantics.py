"""Semantic verification runner and matrix."""
from __future__ import annotations

from mordheim_knowledge.loader import knowledge_root
from mordheim_combat_lab.verification.reports import EvidenceMismatch
from mordheim_combat_lab.verification.scenarios import check_case
from mordheim_combat_lab.verification.specifications import load_fixtures
import pytest as pytest


#: The case roles that name which part of a rule's contract a case evidences.
#: These are the specifications' own reviewed roles, not inferred keywords.
_ADMISSION_OPERATIONS = frozenset({
    "grant", "selectable_grant", "general_skill_access", "special_rule_access",
    "equipment_choices", "selection_choices",
})
_COMPILED_OPERATIONS = frozenset({"construction_tag_presence", "trait_presence"})


def _case_category(spec, case):
    """The single phase guarantee an authored semantic case proves.

    Decisions use only metadata the specification already declares: the
    ``category`` of its reviewed scope, the case ``roles`` and the ``compile``
    rejection channel.  A composition case composes rules; a compiled role
    proves the construction representation; an admission operation or a named
    rejection proves construction admission; a compile case without a refusal
    proves the compiled projection; every remaining single-rule case proves its
    isolated behaviour.
    """
    roles = set(case.get("roles") or ())
    operation = case.get("operation")
    if "composition" in roles:
        return "phase4_modular"
    if "compiled" in roles or operation in _COMPILED_OPERATIONS:
        return "phase2_construction"
    if "rejected" in roles or "reject" in case:
        return "phase2_construction"
    if operation in _ADMISSION_OPERATIONS:
        return "phase2_construction"
    if operation == "compile":
        return "phase2_construction"
    if spec.get("category") == "interaction":
        return "phase4_modular"
    return "phase3_rules"


@pytest.mark.parametrize("case", [
    pytest.param(case, id=f"{spec['id']}/{case['id']}",
                 marks=getattr(pytest.mark, _case_category(spec, case)))
    for spec in load_fixtures() if not spec.get("pending")
    for case in spec["cases"]
])
def test_authored_semantic_case(case):
    try:
        check_case(case, knowledge_root())
    except EvidenceMismatch as error:
        raise AssertionError(str(error)) from None


@pytest.mark.phase3_rules
def test_rapier_failed_extra_hit_omits_extra_wound_roll():
    # Focused regression, not a certificate of all Rapier interactions.
    check_case({"id": "rapier-extra-miss", "operation": "attack",
                "attacker": {"main_weapon_id": "weapon.rapier"},
                "rolls": [{"key": "test.hit", "value": 4},
                          {"key": "test.wound", "value": 1},
                          {"key": "test.barrage.1.hit", "value": 1}],
                "expect": {"result.hit": True, "result.wounded": False,
                           "result.defender.wounds": 3}}, knowledge_root())
