"""Declaratively collected E2E scenarios: one logical unit per audit ID.

The corpus is data (``cases/**/*.yaml``); this entry point only collects it and
executes each declaration through the production pipeline.  Every scenario
keeps its own collected identity (``audit-ID::scenario-ID``) and its own
result, so one failing scenario never hides its siblings.  The loader checks
live here too, next to the declarations they guard.
"""
from __future__ import annotations

import pytest
import yaml

from mordheim_knowledge.loader import knowledge_root
from mordheim_modular_e2e.corpus import CorpusError, load_corpus
from mordheim_modular_e2e.dice import EvidenceMismatch
from mordheim_modular_e2e.runner import check_case

CORPUS = load_corpus()


def _primary_category(scenario):
    """The guarantee a declaration proves, from its explicit expectation channel.

    A scenario that declares a named refusal proves admission (``eligibility``);
    every other declaration drives the real pipeline and asserts an observed
    round/duel state, which is the connected product path (``end_to_end``).
    """
    return "eligibility" if "expect_error" in scenario.case else "end_to_end"


#: One explicit primary category per collected declaration, applied at the
#: parametrisation point so selection never needs a manual name list.
CORPUS_PARAMS = [
    pytest.param(scenario, id=scenario.test_id,
                 marks=getattr(pytest.mark, _primary_category(scenario)))
    for scenario in CORPUS
]


@pytest.mark.parametrize("scenario", CORPUS_PARAMS)
def test_declared_scenario(scenario):
    try:
        check_case(scenario.case, knowledge_root())
    except EvidenceMismatch as error:
        raise EvidenceMismatch(f"{scenario.test_id} ({scenario.source}): {error}") from error


@pytest.mark.test_infrastructure
def test_a_declared_scenario_fails_when_its_expectation_is_wrong():
    """A collected declaration is a real assertion, not a collection check."""
    scenario = next(item for item in CORPUS if item.case.get("expect_final"))
    case = dict(scenario.case)
    case["expect_final"] = {**case["expect_final"], "rounds_executed": 99}
    with pytest.raises(EvidenceMismatch, match="expected 99"):
        check_case(case, knowledge_root())


@pytest.mark.test_infrastructure
def test_rejection_assertions_are_named_not_swallowed():
    """An expected refusal must be refused for the reason it declares.

    Grant evidence uses ``expect_error`` to show that a non-recipient is refused
    and cannot silently gain the effect.  The assertion names the reason, so an
    unrelated failure cannot satisfy it and a case that runs must fail.
    """
    rejected = next(item for item in CORPUS if item.case.get("expect_error"))
    wrong = dict(rejected.case)
    wrong["expect_error"] = "a reason this case never gives"
    with pytest.raises(EvidenceMismatch, match="rejection does not name"):
        check_case(wrong, knowledge_root())
    # An admitted recipient of the same grant must fail the rejection assertion
    # instead of passing silently.  A passing sibling supplies the admitted build
    # and the dice it consumes; only the refusal declaration is carried over.
    sibling = next(item for item in CORPUS
                   if item.audit_id == rejected.audit_id and not item.case.get("expect_error"))
    accepted = {key: value for key, value in sibling.case.items()
                if key not in ("expect_initial", "expect_rounds", "expect_final", "expect_events")}
    accepted["expect_error"] = rejected.case["expect_error"]
    with pytest.raises(EvidenceMismatch, match="but the case ran"):
        check_case(accepted, knowledge_root())


@pytest.mark.data_contract
def test_a_rejection_cannot_be_combined_with_an_observation():
    case = {**next(item for item in CORPUS if item.case.get("expect_error")).case,
            "expect_final": {"rounds_executed": 1}}
    with pytest.raises(ValueError, match="cannot be combined"):
        check_case(case, knowledge_root())


@pytest.mark.evidence
def test_declared_corpus_is_nonempty_and_unique():
    assert CORPUS, "the E2E corpus must declare at least one scenario"
    assert len({scenario.test_id for scenario in CORPUS}) == len(CORPUS)


def _write(tmp_path, documents):
    path = tmp_path / "declarations.yaml"
    path.write_text(yaml.safe_dump(documents), encoding="utf-8")
    return path


@pytest.mark.data_contract
def test_loader_rejects_unknown_scenario_fields(tmp_path):
    _write(tmp_path, [{
        "id": "s", "audit_id": "core/combat-order", "covers": ["charge-before-initiative"],
        "expect_initial": {"first.wounds": 1}, "maximum_rounnds": 1,
    }])
    with pytest.raises(CorpusError, match="unknown scenario fields"):
        load_corpus(tmp_path)


@pytest.mark.data_contract
def test_loader_requires_audit_identity_covers_and_an_assertion(tmp_path):
    _write(tmp_path, [{"id": "s", "covers": ["c"], "expect_initial": {"a": 1}}])
    with pytest.raises(CorpusError, match="audit_id"):
        load_corpus(tmp_path)
    _write(tmp_path, [{"id": "s", "audit_id": "core/combat-order", "covers": [],
                       "expect_initial": {"a": 1}}])
    with pytest.raises(CorpusError, match="covers must be a nonempty list"):
        load_corpus(tmp_path)
    _write(tmp_path, [{"id": "s", "audit_id": "core/combat-order", "covers": ["c"],
                       "fighters": {"first": {}}}])
    with pytest.raises(CorpusError, match="must assert an observation"):
        load_corpus(tmp_path)


@pytest.mark.data_contract
def test_loader_rejects_duplicate_scenario_identities(tmp_path):
    declaration = {"id": "s", "audit_id": "core/combat-order",
                   "covers": ["c"], "expect_initial": {"a": 1}}
    _write(tmp_path, [declaration, declaration])
    with pytest.raises(CorpusError, match="duplicate scenario"):
        load_corpus(tmp_path)


@pytest.mark.data_contract
def test_loader_rejects_an_empty_rejection_expectation(tmp_path):
    _write(tmp_path, [{"id": "s", "audit_id": "core/combat-order", "covers": ["c"],
                       "expect_error": "  "}])
    with pytest.raises(CorpusError, match="expect_error must be a nonempty string"):
        load_corpus(tmp_path)


@pytest.mark.data_contract
def test_loader_rejects_a_non_list_document(tmp_path):
    (tmp_path / "declarations.yaml").write_text("id: not-a-list\n", encoding="utf-8")
    with pytest.raises(CorpusError, match="must be a list"):
        load_corpus(tmp_path)
