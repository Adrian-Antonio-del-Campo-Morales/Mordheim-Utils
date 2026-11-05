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
| E2E statistical parity | Native: 0 of 2,678 divergent in an uncommitted re-sample against the stored Modular oracle; NumPy: 1 divergent in its stored store | Verify and commit the Native changes, refresh the Native store, fix NumPy's divergence and settle oracle provenance. |

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

The decision data lives in `tests/engines/parity/reference_samples/`:
`modular-e2e-100k` is the oracle, `numpy-e2e-100k` and `native-e2e-100k` are
the candidates (seed 2026, 100,000 duels per scenario in 10,000-duel chunks,
50 rounds, six-sigma winner gate). Compare stored stores without running
either engine with `python -m tools.verification.parity_samples compare
--level e2e --backend <numpy|native> --store <candidate store>
--reference-store <modular store>`; re-sample candidates with `sample --engine
<numpy|native>`. Running the Modular engine requires explicit authorization.

Remaining certification work:

- **Verify the Native E2E changes.** Run the native runtime and deterministic
  replay selections (`tests/engines/native/`) on the changed engine; the
  attack-event gating, pool allocation and Rapier Barrage changes touch the
  replay paths. Push preparation on 2026-11-05 rebuilt these local changes over
  `4d186f54` with `.venv/bin/python setup.py build_ext --inplace` and ran
  `.venv/bin/python -u -m pytest tests/engines/native/test_attack_mechanics.py
  tests/engines/native/test_stateful_rules.py
  tests/engines/native/runtime/test_duel_replay_native.py -n 2 --dist=load -q
  --durations=10 --tb=short`: 29 passed. The build emitted GCC warnings;
  this focused selection does not certify the full runtime or parity suite.
- **Refresh the Native store.** Re-sample `native-e2e-100k` from a clean commit
  containing those changes and compare it with the oracle; the committed store
  still holds the earlier candidate.
- **Requalify the 43 precompiled scenarios.** Native changed after its last
  43/43 campaign; re-sample `--level long` and compare with `modular-100k`.
- **Fix NumPy's divergence.** `profile.fist` for the Battle Monks of Cathay
  Raging Peasants (`the-fist-does-not-grant-the-enemy-the-dagger-save-bonus`):
  NumPy returns identical counts for this case and its sibling with different
  inputs, so it ignores the input that distinguishes them. Fix it in NumPy, then
  re-sample that case.
- **Settle oracle provenance.** The stored Modular samples carry a source
  digest that matches no commit, and two Modular commits followed them. Confirm
  which inputs those commits can affect, or regenerate the affected oracle
  samples with authorization, before claiming current-engine certification.
- **Make native digests portable.** `.pyx` and `.pxd` files have no explicit
  line-ending rule in `.gitattributes`, so Windows and Linux checkouts of the
  same commit produce different native engine digests and spurious provenance
  warnings.
- **Cover the rejected deliveries.** 2,485 deliveries never run: 1,491 need
  `initial_state` overrides or auxiliary participants the shared runner cannot
  express, 530 prescribe scripted decisions, and 464 are expected construction
  refusals. The first two groups are uncertified until the runner supports them.
