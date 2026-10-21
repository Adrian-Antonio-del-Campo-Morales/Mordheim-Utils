"""P00 diagnostic probe of the 35 ``initialize`` DIVERGENCE rows.

The baseline probe reports 35/35 ``initialize`` specification cases as
DIVERGENCE.  ``_specifications._vector_initialize`` compares the 21-field
``_plain_initial_vector_state`` projection against the full modular state
(63 fields for the first case), with ``!=`` over the whole dict.  This probe
separates two causes per case without changing any engine or adapter:

- ``shape-only``: no field present on both sides differs; the divergence is a
  comparison artefact of the extra modular-only fields.
- ``shared-value``: at least one common field differs; those are the rows that
  still need a semantic owner.

Read-only: executes the existing modular oracle and the existing vectorized
constructor on the existing semantic cases.

    python -X utf8 TMP_VECTORIAL_ENGINE_2A2B/parity_update/P00-results/initialize_divergence_probe.py
"""
from __future__ import annotations

import sys

from mordheim_combat import vectorized
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_combat_lab.verification.parity._specifications import (
    _RollVectorRng,
    _plain_initial_vector_state,
    build_semantic_fighter,
    execute_case,
    knowledge_root,
    load_fixtures,
)


def main() -> int:
    root = knowledge_root()
    shape_only = 0
    with_values = 0
    for specification in load_fixtures():
        for case in specification.get("cases", ()):
            if case.get("operation") != "initialize":
                continue
            modular = execute_case(case, root, StrictDice(case.get("rolls", ())))["result"]
            rng = _RollVectorRng(case)
            differing = set()
            for side in ("attacker", "defender"):
                fighter = build_semantic_fighter(case.get(side, {}), root)
                vector = _plain_initial_vector_state(
                    vectorized._new_state(fighter, 1, rng))
                differing |= {
                    field for field in set(modular[side]) & set(vector)
                    if modular[side][field] != vector[field]
                }
            if differing:
                with_values += 1
                print(f"SHARED-VALUE {specification['id']}/{case['id']} "
                      f"{sorted(differing)}")
            else:
                shape_only += 1
    print(f"shape_only={shape_only} shared_value={with_values}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
