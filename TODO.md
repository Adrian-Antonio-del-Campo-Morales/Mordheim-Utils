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
| Web artefacts | `outputs/web-public/knowledge/knowledge-web.json` is absent in this checkout | Generate before running web KB tests; Dwarf inheritance projection remains unverified. |
| Combat Lab popover | Historical reported failure; not rechecked | Reproduce the two focused UI cases before diagnosing. |
| Knowledge and translations | Deferred follow-ups | Use canonical references and live review queues. |

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

## Web artefact preparation and projection verification

The user's knowledge run failed during collection because the generated
`outputs/web-public/knowledge/knowledge-web.json` was absent. Generate it with
`python tools/knowledge/generate_knowledge_web.py`, then use `--check` for
freshness. This prerequisite does not establish a generator defect.

Dwarf inheritance has not been separately checked against the generated web
projection. Its compilation/E2E checks do not establish the web contract.
Do not hand-edit generated JSON. Close the projection follow-up only with
applicable artefact-level evidence.

## Combat Lab checklist popover closes during layout

Historical report (2026-10-21), not rechecked against the current tree:
`tests/applications/combat_lab/ui/test_checklist_popover.py` cases
`test_popover_body_matches_the_dark_theme` and
`test_popover_shows_a_visible_scrollbar` failed after `root.update()` with
`TclError: bad window path name` because the popover was already destroyed.

Reproduce those cases, then determine whether widget lifecycle or test focus
setup is responsible. Close when both pass with theme, width and scrollbar
assertions preserved. Application fixes are separate from current engine work.

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
| Wounds after a helpless melee kill | Confirmed on 2026-11-02: NumPy subtracts wounds that the modular leaves unchanged. The deviation is confined to the wounds ledger (winner rates are unaffected), but it is also what keeps NumPy's damage-to-injury run alignment correct — a fix must restore the alignment the way the corrected native capture does (skip zero-damage entries), not merely stop subtracting. |
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

## Human decisions

No unresolved human decisions are currently listed. Record new questions with
the affected source or contract and the work they block; accepted decisions
belong in [Design rulings](docs/decisions/design-rulings.md).

## Deferred product scope

These domains are outside the current duel runtime. Implementation requires an
approved scope change in
[`runtime-scope.yaml`](sources/knowledge/registry/runtime-scope.yaml):

- group psychology and warband-wide proximity effects;
- shooting and missile weapons;
- movement, terrain and falling;
- magic in battle;
- mounts and ridden combat;
- scenario table mechanics beyond progression rewards.

## Sources of truth

| Question | Maintained source or command |
| --- | --- |
| Which consequences are in scope? | Rule `runtime` blocks and the runtime-scope registry. |
| Are admitted clauses pending? | `python -X utf8 tools/knowledge/clause_registry.py query --pending` |
| Which editorial obligations are inventoried? | `python tools/mordheim-utils.py check verify --inventory` |
| Where is the rule-review inventory? | `python tools/mordheim-utils.py check report rules` |
| Which hireling references are unresolved? | `unresolved_references` in hireling YAML. |
| Which decisions are binding? | [Design rulings](docs/decisions/design-rulings.md). |

## Resolved native divergences (2026-11-03)

The seven stored-sample divergences recorded on 2026-10-28 were root-caused
and corrected in `native/_combat_native.pyx` and `native/_combat_compile.py`.
After the corrections the native campaign reports **43 compared, 43 approved,
0 divergent** at 100,000 duels per scenario against the untouched references
in `tests/engines/parity/reference_samples/modular-100k`
(`outputs/parity-native-fixed/compare/parity-campaign.json`). The native
suite passes 68/68 (the two `runtime/test_duel_context.py` cases were not run
because they execute the modular engine, which that validation excluded).
The modular implementation and the accepted references were not changed.

The five corrections, for provenance:

1. **Injury-run misalignment** (undocumented until 2026-11-02; caused
   `stateful`, `triple-weapon-vs-parry` and the former 4–5σ near-misses):
   `resolve_weapon_c` captured `wounds_before` per run of `wound_rows`
   including zero-damage helpless kills, while the injury loop advanced per
   run of `damage_rows`, which exclude them; every row after a helpless kill
   in the same call read another row's pre-subtraction Wounds. The capture
   now skips zero-damage entries. Only reproducible in batches of two or
   more rows. The old hints recorded here (Force of Will, parry) were
   disproved by bisection.
2. **Bear Hug consumption** (`trained-bear-vs-scarecrow`, and the
   `c05-bear-hug` out-of-bounds error): the pool compaction wrote its
   shrunken `hit_n` to a by-value struct copy, so the two consumed hits
   still resolved and stale shifted rows reached the downstream row lookups.
   The count is now written through the pointer.
3. **Injury reroll semantics** (`trained-bear-vs-scarecrow` residual):
   without an explicit policy the native rerolled only out-of-action-level
   totals, with an unmodified die. The oracle's production default rerolls
   every eligible Injury result and re-applies the roll modifiers; native
   now mirrors it.
4. **Final unarmed attack cap** (`frenzy-vs-w2`, and the floor-masked
   `frenzy-vs-heavy` inflation): `attack_count_c` now re-applies
   `min(attacks, 1)` after Frenzy doubling, as `phases.build_attacks` does.
5. **Stunned finish with zero attacks** (`regen-vs-fire`,
   `silent-walker-vs-cold-one`): the phase-start-stunned conversion to OUT
   is now gated on the attacking pool having at least one attack, and the
   charged whip bearer's bonus (`unarmed-vs-steel`) is scheduled as its own
   Strike First event with a whip-only projection
   (`schedule_whip_c`/`whip_event_c`, mirroring the Shifty machinery), with
   `weapon.barbed-whip` and `weapon.thinglash` added to the whip tag set.

## Sub-gate observations from the 2026-11-03 three-way comparison

All 43 scenarios pass the six-sigma gate for both backends, but three results
deserve attention before they are read as clean. The stored modular samples
were not re-run; every figure below compares current candidate samples with
the frozen 100k references.

- **`stateful` — both backends share a +0.65pp offset.** A 1,000,000-duel
  NumPy sample puts its first-win rate at 26.160% against the stored modular
  25.511% (z ≈ 4.5, now dominated by the reference's own 100k noise); the
  corrected native sample agrees with NumPy (26.337%, cross z ≈ 1.2). Either
  the stored modular sample is an unlucky draw, or the two ports share a
  small real deviation — Force of Will rescue/sustain sequencing and
  brazier ignition are the mechanics unique to this pair. Because native is
  a port of NumPy, their agreement cannot distinguish the two explanations;
  only a fresh oracle sample can.
- **`unarmed-vs-steel` — both backends share a −0.50pp offset.** NumPy at
  1,000,000 duels: 22.248% first-win vs the stored 22.750% (z ≈ 3.6);
  native agrees (22.146%). The shared mechanic is the Whipcrack bonus,
  whose native port was written against the NumPy implementation, so a
  subtle NumPy deviation from the oracle (event insertion or tie handling)
  would be invisible to the cross-check.
- **`skill-stack-vs-hitter` — the two candidates disagree with each other
  (cross z ≈ 3.6 at 100k: NumPy 88.88%, native 88.37%, modular 88.75%
  between them).** Both pass against the oracle, but a 3.6σ candidate split
  on a reroll-stacking scenario (Expert Fighter, Infinite Hatred, Red Fury,
  Sure Strike) suggests the two ports order or gate a reroll differently.
  Escalate both candidates on this pair before the next certification.

Recommended follow-up, in order: draw one fresh modular sample for
`stateful`, `unarmed-vs-steel` and `skill-stack-vs-hitter` (the existing
chunked store makes this resumable) and re-decide the three offsets; until
then, treat the stored references for those pairs as 100k draws whose ~4σ
agreement band these candidates currently sit at the edge of.

Latent items found during the same investigation, not visible in any current
scenario:

- `phase_attacks_c` computes its pool row list into `b.rows` and then calls
  `shifty_event_c`/`jolt_event_c`, which overwrite `b.rows` when they fire;
  a first-round Shifty or jolt bearer in a multi-row batch can make the
  following pool resolve stale rows. The new whip event deliberately uses a
  different scratch buffer; the Shifty and jolt paths should be audited.
- The native Bear Hug pairs surviving hits across the whole prepared pool,
  while the oracle only ever consumes attacks 0 and 1; no current profile
  grants a hugger three or more attacks, so the difference is unreachable
  today.
- The rare-outcome scan (modular rate < 2%) found no remaining
  floor-masked relative deviations in either backend; the former
  `frenzy-vs-heavy` 5× first-win inflation disappeared with correction 4.
