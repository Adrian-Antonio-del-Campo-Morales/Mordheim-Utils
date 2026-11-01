# Project backlog

Track unresolved defects, verification work and deferred capabilities here.
Procedures belong in the linked guides; current counts and execution details
belong in maintained inventories and generated reports. Historical passes do
not certify the current tree, and unverified reports are not confirmed defects.

## Work overview

| Work | Current disposition | Next step |
| --- | --- | --- |
| Modular integration | Implementation received; strict E2E completeness remains unconfirmed | Check the live coverage inventory before claiming global closure. |
| Optimized engines | Vectorized port integrated; native implementation on `native-engine-implmentation` | Investigate the seven native divergences below and qualify each backend separately. |
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

Current priority: investigate the native stored-sample divergences below,
first distinguishing historical-reference differences from current engine
behavior. Keep tolerances and reference provenance intact. Qualify NumPy and
native separately; do not infer one backend's support from the other.

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
| Wounds after a helpless melee kill | Confirm whether NumPy subtracts wounds that the modular leaves unchanged when taking a helpless defender out. |
| Black Hunger backlash (`q11-black-hunger`) | Confirm that later backlash hits stop for inactive rows and that Force of Will is offered at the same stage as the modular. The current loop still uses the initial active-row set. |
| Bear-hug row ordering (`c05-bear-hug`) | Reproduce the reported out-of-bounds error and check repeated/unsorted rows before `searchsorted`; do not assume the old exception still occurs. |

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

## Native parity divergences (100,000 duels per scenario)

The user-run stored-sample comparison in
`outputs/parity-native/compare/parity-campaign.json` reports 43 compared,
36 approved and 7 divergent. Candidate sample digests match the currently
loaded native engine; the saved modular digest differs from current sources.
Inputs, seeds and round budgets match between samples. Root causes are not
yet established; do not alter tolerances or replace accepted references to
hide these differences.

| Scenario | Largest absolute outcome difference |
| --- | --- |
| `stateful` | 2.070 percentage points |
| `regen-vs-fire` | 2.392 percentage points |
| `unarmed-vs-steel` | 2.410 percentage points |
| `triple-weapon-vs-parry` | 1.200 percentage points |
| `frenzy-vs-w2` | 0.976 percentage points |
| `trained-bear-vs-scarecrow` | 3.607 percentage points |
| `silent-walker-vs-cold-one` | 4.081 percentage points |

Investigation uses the modular as the oracle. Do not modify modular code;
report suspected modular defects to the user for a decision.
A diagnostic sample of 5,000 current-modular duels per scenario stays near the
historical reference rates. It is saved in `outputs/parity-diagnosis-modular`;
this does not replace the accepted references or certify the current oracle.

### Located native defects (not yet applied to repository code)

- **Missing final unarmed attack cap:** `native/_combat_native.pyx::attack_count_c`
  caps penalized fists before Frenzy but omits the final cap from
  `phases.build_attacks`. The fanatic can retain two attacks instead of one.
  Relevant to `frenzy-vs-w2`.
- **Automatic finish with zero attacks:** `resolve_attacks_c` takes an already
  STUNNED target OUT before checking the attack count. `phase_attacks_c` can
  dispatch that pool for a standing attacker whose Stupidity or burning has
  suppressed all attacks. A two-round fixed-dice Cold One replay reproduced
  an OUT result while the modular correctly leaves the target STUNNED.
  Relevant to `silent-walker-vs-cold-one` and `regen-vs-fire`.
- **Whip bonus timing:** `phase_pools_c` adds the whip bonus to the normal pool;
  it does not schedule the charged bearer's separate Strike First event from
  modular `resolve_round`. Relevant to `unarmed-vs-steel`.

A temporary native extension under `/tmp/mordheim-native-probe` applied only
the first two changes. At 100,000 native duels per scenario, `frenzy-vs-w2`,
`regen-vs-fire` and `silent-walker-vs-cold-one` fell within the original saved
reference tolerances. The other four scenarios still diverged. This is causal
diagnostic evidence, not a committed fix or a replacement sample. Production
engine sources/binary, modular implementation and accepted references were
not changed.

### Remaining native investigation

- `stateful`: removing Force of Will narrows the diagnostic gap; disabling
  ignition alone does not. Inspect rescue and sustain behavior within attacks.
- `trained-bear-vs-scarecrow`: removing Bear Hug changes the modular distribution
  substantially but barely changes native results. Disabling injury rerolls
  does not eliminate the gap; investigate the replacement and synthetic attack
  path rather than blaming the reroll alone.
- `triple-weapon-vs-parry`: the diagnostic gap persists with one axe attack and
  no off-hand, so multiweapon allocation alone does not explain it. Inspect
  parry and wound/injury handling. Removing parry narrowed the initial gap but
  the small diagnostic modular samples do not conclusively isolate a cause.

No evidence so far requires changing the modular. Do not close these entries
until the native corrections are applied and focused validation passes.
