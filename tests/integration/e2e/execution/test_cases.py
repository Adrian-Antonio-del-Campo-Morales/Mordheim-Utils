"""Declaratively collected E2E scenarios: one logical unit per audit ID.

The corpus is data (``cases/**/*.yaml``); this entry point only collects it and
executes each declaration through the production pipeline.  Every scenario
keeps its own collected identity (``audit-ID::scenario-ID``) and its own
result, so one failing scenario never hides its siblings.  The loader checks
live here too, next to the declarations they guard.
"""
from __future__ import annotations

import pytest

from mordheim_knowledge.loader import knowledge_root
from mordheim_modular_e2e.corpus import load_corpus
from mordheim_modular_e2e.execution.dice import EvidenceMismatch
from mordheim_modular_e2e.execution.runner import check_case

CORPUS = load_corpus()


#: Every collected declaration keeps its own id and parameters.
CORPUS_PARAMS = [pytest.param(scenario, id=scenario.test_id) for scenario in CORPUS]


@pytest.mark.parametrize("scenario", CORPUS_PARAMS)
def test_declared_scenario(scenario):
    try:
        check_case(scenario.case, knowledge_root())
    except EvidenceMismatch as error:
        raise EvidenceMismatch(f"{scenario.test_id} ({scenario.source}): {error}") from error


