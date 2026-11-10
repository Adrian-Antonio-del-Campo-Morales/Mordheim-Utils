# Project backlog

Unresolved defects, verification work and deferred capabilities. Procedures
belong in the linked guides; counts and execution details belong in generated
reports. A historical pass does not certify the current tree.

## Modular integration and E2E coverage

Strict E2E coverage of the modular oracle is unconfirmed. Close it with
`MORDHEIM_E2E_REQUIRE_COMPLETE=1` over `tests/integration/e2e/` on the delivered
revision, preserving the accepted-evidence baseline and clause identities.
Pending clauses: `python -X utf8 tools/knowledge/clause_registry.py query --pending`.
See the [verification reference](docs/reference/verification.md#modular-integration-closure).

## Web projection verification

Verify Dwarf inheritance in the generated web projection, with evidence from
`outputs/web-public/knowledge/knowledge-web.json` (generate it with
`python tools/knowledge/generate_knowledge_web.py`; never hand-edit it).

## Combat Lab checklist popover closes during layout

Unverified report of `TclError: bad window path name` after `root.update()` in
`tests/applications/combat_lab/ui/test_checklist_popover.py`
(`test_popover_body_matches_the_dark_theme`,
`test_popover_shows_a_visible_scrollbar`). Determine whether widget lifecycle
or test focus setup destroys the popover; close when both pass with their
theme, width and scrollbar assertions intact.

## Optimized-backend verification

Qualify NumPy and Native separately against the modular oracle. Native was
ported from NumPy, so agreement between the two never exonerates a deviation
they share. Keep tolerances and reference provenance intact; procedures are in
the [verification reference](docs/reference/verification.md).

- **Native.** Run the native runtime and deterministic replay selections
  (`tests/engines/native/`): attack-event gating, pool allocation and Rapier
  Barrage touch the replay paths. Then requalify `--scenarios big` against
  `modular-100k` and re-sample `native-e2e-100k` from a clean commit.
- **NumPy stored E2E sample.** `numpy-e2e-100k` predates the current engine.
  Re-sample it from a clean commit (the current engine passes every E2E
  delivery against `modular-e2e-100k` at 20,000 duels, including the Raging
  Peasants fist case that diverged in the stored sample).
- **Systematic E2E offset.** Every NumPy E2E delivery passes the six-sigma
  gate, yet the rates lean one way: over the 1,815 distinct inputs the
  first-win z-scores average about +0.2 and the unresolved ones about +0.9
  against `modular-e2e-100k`. The per-case z-scores share one seed, so their
  mean is less significant than it looks. Determine whether this is an engine
  difference or the oracle-provenance problem below.
- **Oracle provenance.** The stored modular samples carry a source digest that
  matches no commit, and modular commits followed them. Confirm which inputs
  those commits can affect, or regenerate the affected samples with
  authorization, before claiming current-engine certification.
- **Survivor condition (NumPy).** Campaigns compare the winner only. On
  `scenario/stateful` (20,000 duels) the winner of a decided duel is not
  Standing in 1.56 % of duels for Modular and 1.98 % for NumPy. Decide whether
  this is an ordering difference in the deciding round, and whether the
  terminal condition should become a compared magnitude.
- **Portable native digests.** `.pyx` and `.pxd` files have no line-ending rule
  in `.gitattributes`, so Windows and Linux checkouts of one commit produce
  different native digests and spurious provenance warnings.
- **Rejected E2E deliveries.** 2,485 deliveries never run: 1,491 need
  `initial_state` overrides or auxiliary participants the shared runner cannot
  express, 530 prescribe scripted decisions and 464 are expected construction
  refusals. The first two groups stay uncertified until the runner supports
  them.

Stored samples live in `tests/engines/parity/reference_samples/` (seed 2026,
50 rounds for E2E). Compare without running either engine:
`python tools/mordheim-utils.py check samples compare --scenarios e2e
--backend <numpy|native> --store <candidate> --reference-store <modular store>`.
Running the modular engine requires explicit authorization.

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Implement the Sunstaff Lustria melee profile | Add the bearer-Strength profile without invented two-handed, +1 Strength or ignition properties, then reconnect its item/simulation mapping and pending register clause. Catalogue text is corrected; motor support remains pending by user decision (2026-11-10). Sunbolt shooting remains outside the duel. |
| Resolve hireling `unresolved_references` | Replace references as canonical catalogues become available; keep genuinely unresolved links explicit. |
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae. |
| Make unsupported item-to-engine mappings explicit | Ensure catalogue presence cannot be mistaken for executable support. |
| Complete interface translations | Translate missing messages and remove unused keys. |

See the [knowledge-base reference](docs/reference/knowledge-base.md),
[campaign knowledge guide](docs/guides/campaign-knowledge.md) and
[web presentation conventions](docs/reference/web-presentation.md). Scope
changes are governed by
[`runtime-scope.yaml`](sources/knowledge/registry/runtime-scope.yaml);
accepted decisions belong in [Design rulings](docs/decisions/design-rulings.md).
