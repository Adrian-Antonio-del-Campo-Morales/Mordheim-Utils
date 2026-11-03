# Project backlog

Track unresolved defects, verification work and deferred capabilities here.
Procedures belong in the linked guides; current counts and execution details
belong in maintained inventories and generated reports. Historical passes do
not certify the current tree, and unverified reports are not confirmed defects.

## Work overview

| Work | Current disposition | Next step |
| --- | --- | --- |
| Modular integration | Implementation received; strict E2E completeness remains unconfirmed | Check the live coverage inventory before claiming global closure. |
| Optimized engines | Both backends pass the full 43-scenario campaign at 100k duels against the stored modular references (NumPy 43/43 on 2026-11-02; native 43/43 on 2026-11-03 after five corrections) | Investigate the sub-gate shared offsets below with a fresh oracle sample before the next certification. |
| E2E statistical parity (modular vs NumPy) | Stored pair decides 2,678 compared, 2,678 approved, 0 divergent; only the corrected and statically affected scenarios carry fresh samples | Re-sample NumPy across the full catalogue against the stored modular references before the next certification. |

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
read current pending clauses through `clause_registry.py query --pending`.

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

The vectorized implementation is integrated; do not reopen its completed port
from the obsolete October admission counts. Native implementation exists on
`native-engine-implmentation`, but its statistical acceptance is pending.
Implementation, focused rule tests and large-sample parity are distinct claims.

The seven native stored-sample divergences recorded here on 2026-10-28 were
root-caused and corrected on 2026-11-03 (see "Resolved native divergences"
below). Both backends now pass the full catalogue at 100,000 duels per
scenario against the stored modular references. Keep tolerances and reference
provenance intact. Qualify NumPy and native separately; native was ported
from the NumPy engine, so agreement between the two candidates never
exonerates a deviation they share — only the modular oracle does.

The renewed statistical catalogue still has explicit input limits:
`c03-petru-potion` needs out-of-scope campaign preparation, and
`v01-restriction` needs a charge rejected by construction. Keep these visible
as incompatible rather than substituting runnable scenarios. Do not treat
unexecuted profiles as accepted. Use the
[verification reference](docs/reference/verification.md) for campaign procedures.

### Vectorized findings awaiting focused confirmation

These findings were recorded on 2026-10-22. They have not been functionally
rechecked during this cleanup. Old source line numbers and percentages were
removed because the implementation has moved; reproduce the specific contract
before fixing it or declaring it resolved.

| Finding | Remaining check |
| --- | --- |
| Netted recovery stance (`v09-netted`) | Compare the victim's stance after cutting free and own-turn recovery; the current vectorized path excludes newly freed rows from standing. |
| Wounds after a helpless melee kill | NumPy still subtracts wounds that the modular leaves unchanged; the residue is confined to the wounds ledger (winner rates are unaffected). A fix must keep the damage-to-injury alignment (skip zero-damage entries), not merely stop subtracting. |
| Black Hunger backlash (`q11-black-hunger`) | Confirm that later backlash hits stop for inactive rows and that Force of Will is offered at the same stage as the modular. The current loop still uses the initial active-row set. |

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Resolve hireling `unresolved_references` | Replace references as canonical catalogues become available; keep genuinely unresolved links explicit. |
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae. |
| Make unsupported item-to-engine mappings explicit | Ensure catalogue presence cannot be mistaken for executable support. |
| Complete interface translations | Translate missing messages and remove unused keys. |
| Publish the remaining Knights Feats, if admitted to scope | Combat Charge, Lancer and Armour Specialist lack canonical executable records; keep them unavailable until their contracts and consumers exist. |

See the [knowledge-base reference](docs/reference/knowledge-base.md),
[campaign knowledge guide](docs/guides/campaign-knowledge.md) and
[web presentation conventions](docs/reference/web-presentation.md).

Scope changes are governed by
[`runtime-scope.yaml`](sources/knowledge/registry/runtime-scope.yaml);
accepted decisions belong in [Design rulings](docs/decisions/design-rulings.md).

## E2E statistical parity, modular vs NumPy

The decision pair lives in `tests/engines/parity/reference_samples/`
(`modular-e2e-100k` is the oracle reference, `numpy-e2e-100k` the candidate;
seed 2026, 100,000 duels per scenario, 50 rounds, six-sigma winner gate).
Decide it without running either engine via
`python -m tools.verification.parity_samples compare --level e2e --backend
numpy --store <numpy store> --reference-store <modular store>`; re-sample
individual scenarios with `sample --engine numpy --id <case_key>`. The
modular oracle is authoritative; the stored pair currently decides 2,678
compared, 2,678 approved, 0 divergent.

Remaining verification work:

- Only the formerly divergent scenarios and the statically identified
  affected ones carry fresh samples; the rest of the catalogue keeps its
  weekend samples from an older engine revision. A full NumPy re-sample
  against the stored modular references is the cheapest way to certify the
  long tail before the next certification (the modular store stays valid).
- The stored samples hold winner counts only, so the store compare can never
  certify the wounds and condition ledgers, where known residues live (see
  the vectorized findings table above). Those magnitudes need the live E2E
  runner (`tools.verification.e2e_parity`) with
  `--magnitudes winner,wounds,condition`, which samples both engines.
- The Lahmia Seduction copy's printed hit-gated attack-release is not ported
  in the vectorized engine (per-row hit provenance is not tracked); its only
  release is the victim's own Recovery-phase test. No stored scenario
  exercises the gap; close it before admitting one that does.
- The native engine shares none of the vectorized corrections and must be
  re-qualified against the modular oracle separately.
