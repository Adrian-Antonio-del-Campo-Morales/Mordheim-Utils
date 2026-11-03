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
| E2E statistical parity (modular vs NumPy) | All 53 divergences of the 2026-11-03 decision were corrected and re-approved by focalized 100k rechecks the same day | Re-sample NumPy across the full catalogue against the stored modular references before the next certification. |

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
| Wounds after a helpless melee kill | Confirmed on 2026-11-02: NumPy subtracts wounds that the modular leaves unchanged. Partially corrected on 2026-11-03: the helpless kill's damage is now the printed 1 (so Acid Blood/Contagious react once), but the wound subtraction itself remains. The residue is confined to the wounds ledger (winner rates are unaffected); a full fix must keep the damage-to-injury alignment (skip zero-damage entries), not merely stop subtracting. |
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

## E2E statistical divergences, modular vs NumPy

The 2026-11-03 decision from the stored weekend sample stores
(`tests/engines/parity/reference_samples/modular-e2e-100k` and
`numpy-e2e-100k`; seed 2026, 100,000 duels per scenario, 50 rounds,
six-sigma winner gate) compared 2,678 of 2,678 executable deliveries:
2,625 approved, 53 divergent. The modular oracle is authoritative.

All 53 divergences were root-caused and corrected on 2026-11-03, and every
affected scenario was re-sampled at 100,000 duels against the stored modular
references and approved by the same gate (focalized checks, not a fresh
campaign). The corrections, grouped by cause:

- **Armour path (RC1, 11 scenarios).** Both attack-path call sites now use
  the faithful `armour_context`/`armour_target_values` ports (Ladle,
  Cutthroat, Norse Bulwark, fist exception, knocked-down ignoring,
  Misericordia dagger penalty). The disease-dagger pair also needed the
  infection wound to ignore armour and to trigger on the natural six; the
  Norse shieldmaster pair was Centigor Drunken contamination (RC5).
- **Injury context (RC2, 4 scenarios).** The inline injury rebuild was
  replaced by the `injury_context`/`injury_results` ports (Squishy's No Pain
  gate, Blessing of Morr against the undead, Misericordia chart, Inured to
  Pain's modifier and zero-total wound refund, Backstabber's first-round
  injury bonus).
- **Wheelo impact (RC3, 3 scenarios).** The collision step was ported:
  impact hits before any blow, the spear counter-impact, the morning star's
  Strength-5 first impact, axe penetration and club concussion.
- **Special-event scheduling (RC4, 4 scenarios).** The whip bonus splits out
  only when the bearer is charged and uses `max(1, whip.priority)`; the
  strikes-last bite is gated by the phase allocation, standing bearer,
  natural slot and no poisoned alternative; a helpless kill's damage is the
  printed 1 (so Acid Blood and Contagious react exactly once); the tentacle
  grapple loss is per phase.
- **Centigor Drunken (RC5, 3 scenarios).** Per-side ledger arrays, expiry
  before the own-turn roll, and the drunken result now gates the Stupidity
  test's psychology immunity, so a roll of 1 forces the test and the round-0
  charge cancel happens.
- **Shared test helpers (RC6, 9 scenarios).** Tranquil Fauna rolls the
  oracle's 2D6 handler test; Contagious fires on any close-combat wound that
  leaves the bearer out (helpless kills included); the six Force of Will
  scenarios were fixed by allocating pool events from the phase-start
  condition, so a mid-phase rescue never grants an event the helpless phase
  start did not allocate.
- **Control powers (RC7, 5 scenarios).** Seduction gained its per-copy
  exclusions, the Lahmia male-only fact and own-turn establishment, the
  Khemrian own-test and attack-release; Enchanting Beauty's -1 is applied
  before the Psychology tests; the addicted Alchemist takes no action until
  cured; the bitten result of 1 grants the printed this-turn Madness
  Stupidity, lapsing with the turn.
- **Shared animosity ledger (RC8, 14 scenarios).** `animosity_failed` is now
  one array per duelist: the shared ledger silenced the failing goblin's
  opponent too, which was the single cause behind the hatred, pikewall
  residual, fungus-brew and leader-six groups. Pikewall additionally reads a
  per-row being-charged fact instead of a never-applied whole-batch tag.

### Remaining verification work

- The corrections are global behavioural changes; a fresh full E2E campaign
  (modular references are still valid; re-sample only NumPy) is needed before
  the next certification to confirm no approved scenario regressed. A
  12-scenario spot-check across the touched paths passed on 2026-11-03.
- The Lahmia copy's printed hit-gated attack-release is not ported (per-row
  hit provenance is not tracked); its only release remains the victim's own
  Recovery-phase test. No stored scenario exercises it.
- The native engine was not updated; it shares none of these fixes and must
  be re-qualified against the modular oracle separately.
