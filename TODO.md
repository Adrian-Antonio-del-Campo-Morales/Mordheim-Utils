# Project backlog

Track unresolved defects, verification work and deferred capabilities here.
Procedures belong in the linked guides; current counts and execution details
belong in maintained inventories and generated reports. Historical passes do
not certify the current tree, and unverified reports are not confirmed defects.

## Work overview

| Work | Current disposition | Next step |
| --- | --- | --- |
| Modular integration | Implementation received; strict E2E completeness remains unconfirmed | Check the live coverage inventory before claiming global closure. |
| Optimized engines | Last recorded 43-scenario campaign at 100k duels: NumPy 43/43 on 2026-11-02 and Native 43/43 on 2026-11-03; later rule changes have focused checks only | Qualify the current revision against Modular, checking reference provenance and affected inputs first. |
| E2E statistical parity | Refreshed candidates from clean `38f4c12f`: 2,678 compared per engine; NumPy 1 divergent, Native 111 divergent | Investigate the recorded divergences and qualify both engines against valid Modular references. |

## Modular integration and E2E coverage

The user reports the modular checks green after removal of obsolete assertions
that optimized backends must reject supported rules. Construction expectations
were also updated for the native port. Neither result establishes full E2E
coverage or optimized-engine equivalence.

The last recorded strict E2E inventory (2026-10-21) had 27 identities with no
scenario and 44 with uncovered clauses. These are historical counts, not a
current measurement. Check `tests/integration/e2e/` and
`MORDHEIM_E2E_REQUIRE_COMPLETE=1` before closing that verification work.
Preserve the accepted-evidence non-regression baseline and clause identities;
read current pending clauses through `python -X utf8 tools/knowledge/clause_registry.py query --pending`.

Completion requires the applicable integrated checks and strict E2E coverage
on the delivered revision. Follow the
[verification reference](docs/reference/verification.md#modular-integration-closure).
Do not rerun unaffected suites solely to refresh this backlog.

## Web projection verification

Verify Dwarf inheritance in the generated web projection. Close with
artefact-level evidence for `outputs/web-public/knowledge/knowledge-web.json`.
Generate the artefact with `python tools/knowledge/generate_knowledge_web.py`
if absent; do not hand-edit generated JSON.

## Combat Lab checklist popover closes during layout

Reproduce the unverified report of `TclError: bad window path name` after
`root.update()` in `tests/applications/combat_lab/ui/test_checklist_popover.py`:

- `test_popover_body_matches_the_dark_theme`;
- `test_popover_shows_a_visible_scrollbar`.

Determine whether widget lifecycle or test focus setup destroys the popover.
Close when both cases pass with theme, width and scrollbar assertions preserved.

## Optimized-backend verification

The NumPy and Native implementations are integrated in the current tree.
Do not reopen their completed ports from obsolete October admission counts.
Implementation, focused rule tests and large-sample parity are distinct claims.

The last recorded 43-scenario campaigns passed at 100,000 duels per scenario
against stored Modular references. Those results predate subsequent rule
changes and do not certify the current tree. Keep tolerances and reference
provenance intact. Qualify NumPy and Native separately; Native was ported
from the NumPy engine, so agreement between the two candidates never
exonerates a deviation they share — only the modular oracle does.

Use the [verification reference](docs/reference/verification.md) for campaign procedures.

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Resolve hireling `unresolved_references` | Replace references as canonical catalogues become available; keep genuinely unresolved links explicit. |
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae. |
| Make unsupported item-to-engine mappings explicit | Ensure catalogue presence cannot be mistaken for executable support. |
| Complete interface translations | Translate missing messages and remove unused keys. |

See the [knowledge-base reference](docs/reference/knowledge-base.md),
[campaign knowledge guide](docs/guides/campaign-knowledge.md) and
[web presentation conventions](docs/reference/web-presentation.md).

Scope changes are governed by
[`runtime-scope.yaml`](sources/knowledge/registry/runtime-scope.yaml);
accepted decisions belong in [Design rulings](docs/decisions/design-rulings.md).

## E2E statistical parity, Modular vs optimized backends

The decision pair lives in `tests/engines/parity/reference_samples/`
(`modular-e2e-100k` is the oracle reference, `numpy-e2e-100k` the candidate;
seed 2026, 100,000 duels per scenario, 50 rounds, six-sigma winner gate).
Decide it without running either engine via
`python -m tools.verification.parity_samples compare --level e2e --backend
numpy --store <numpy store> --reference-store <modular store>`; re-sample
individual scenarios with `sample --engine numpy --id <case_key>`. The
Modular oracle is authoritative; the last recorded comparison of the stored
pair, refreshed on 2026-11-04 from clean commit `38f4c12f`, reports 2,678
compared, 2,677 approved and 1 divergent. The corresponding Native store
(`native-e2e-100k`) reports 2,678 compared, 2,567 approved and 111 divergent.
Each candidate record contains 100,000 duels in ten 10,000-duel chunks.
Another 2,485 deliveries are rejected before sampling in each report.
The refresh preserves candidate results; it does not establish parity acceptance.

Remaining verification work:

- Investigate NumPy's divergent `profile.fist` case for the Battle Monks of
  Cathay Raging Peasants (`the-fist-does-not-grant-the-enemy-the-dagger-save-bonus`).
- Investigate the 111 Native divergences separately against the Modular oracle.
- Check reference provenance and which inputs are affected by the Modular
  changes before claiming current-engine certification. The saved oracle was
  retained unchanged; matching frozen inputs alone does not certify later rules.
