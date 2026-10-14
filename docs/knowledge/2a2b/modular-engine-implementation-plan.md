# Complete the modular engine — external-agent plan and progress

## Purpose and governing boundary

After accepting the canonical KB consolidation, complete the remaining admitted
Combat Lab effects in the **modular engine only**. Preserve their interpretation
and reusable deterministic cases for later NumPy/native ports. Those ports and
T13/T14/T15 certification are separate phases.

Combat Lab remains a 1v1 duel simulator. Apply the adopted exclusions for groups,
independent third fighters, map/terrain/weather, shooting/casting resolution,
campaign acquisition and voluntary escape that leaves the duel unresolved.
An explicitly admitted supplied individual consequence does not authorize its
excluded producer. Do not reopen resolved user rulings without new evidence.

This plan schedules residual work, not a repeat of completed T13 deliveries.
Creating it does not launch agents, reserve files or accept an implementation.
The human launches external agents; the coordinating assistant accepts and
integrates their deliveries. No automatic delegation, commit or push.

## Preparation after KB consolidation (M0)

1. Accept the [staging retirement](2A2B-Knowledge.md#9-retirement-outcome-2026-10-08)
   and fix a canonical entry revision. Check actual changes and applicable
   `AGENTS.md` instructions.
2. Use the recovered maintained [semantic CSV](tasks/T13-semantic-analysis.csv).
   On 2026-10-08, the complete A/B/C/D integration and subsequent scope and
   equivalence incorporations were recovered: 4,552 clauses over 3,590 origins.
   The reduced A/B file was a regression, not unfinished integration. Preserve
   these conclusions without repeating the semantic study; their historical
   implementation and evidence states still require the reconciliation below.
3. Reconcile affected rows with recent implementations and post-consolidation
   sources. Do not implement an already completed effect merely because an old
   row still requests work. Confirm coverage against the current canonical
   inventory, including effects without `t13_origin`.
4. Form closed assignments by semantic contract and actual consumer. Preserve
   every origin/clause ID, variant, excluded remainder and concrete dependency.
   Keep interpretation, remaining work and executed evidence independent.

Use existing CSV fields and family labels; do not introduce another per-effect
register. A binding, assigned consumer or `implementation_work: none` does not
prove behavior. Reuse accepted evidence whose relevant inputs still match.
Block a genuinely uncertain clause, not all independent families.

Reconciliation outcome (2026-10-08, accepted by the coordinator). The
generated inventory was reconciled against the recovered CSV. Every in-scope
(`scope: YES`) audit identity now has a CSV clause; the additions are the shared
`weapon.cleaver`, `weapon.ladle` and `weapon.barbed-whip` operators and the
Dragon Monk's `skill.unarmed-fighting` band grant. Two Fimir spiked-tail effects
changed identity (`trait.extra-attack-tail` → `profile-rule.*--spiked-tail`) and
are recorded as successions; no historical clause was removed. Sixteen rows whose
operator now exists were reconciled (Misericordia Coup de Grace, the Unpredictable
declaration, Ladle, Sword-Gnoblar, Cleaver, Barbed Whip, spiked tail and Tentacle
nomination). The 3,863 `scope: NO` audit origins without a CSV clause are the KB's
own declared exclusions and stay outside this T13 semantic register rather than
being restated per origin. Inspection, interpretation and executed evidence stay
separate: no executed evidence was added. This does not close T13/T14 or certify
the engine.

Repair (2026-10-08, three coordinator findings addressed and accepted).
(1) The pre-M0 review conclusions dropped when the sixteen rows were
rewritten were restored from the baseline at their original grade: one scope
review integration (Misericordia Coup de Grace), two verified reuse-guidance
records (Cleaver and its counts-as marker) and eleven surface reuse-candidate
records, each kept `superficial` with its gate and provenance rather than
promoted to an accepted equivalence. (2) Stale traceability was replaced by the
real routes: Misericordia now cites `weapon.misericordia`, Cleaver
`weapon.cleaver`, and the spiked-tail rows `profile-rule.*--spiked-tail`;
Sword-Gnoblar's empty `effect_id` records the carried-item compiler branch (no
standalone operator), Tentacle's consumer names `pools._grapple_lost_attacks`
while its source origin stays unbound, and the Orc Nuttaz `extra-attack` row
links to its sibling `skill.extra-attack` route with no second contribution.
(3) `build/audit/m0-reconciliation/validate_csv.py` now accumulates violations
and exits non-zero on any (the reported `INVALID_SCOPE` case returns exit 1),
and its probe mode rejects a bad header, invalid enum, invalid JSON type,
duplicate key, lost historical clause, changed fingerprint and admitted but
uncovered audit identity. The register still holds 4,556 clauses / 3,594 origins
with no historical key, printed clause or origin fingerprint altered; final
SHA-256 `531e54b8…`. No executed evidence was added.

Coordinator acceptance is limited to M0 inventory reconciliation. Independent
checks confirmed conservation, all fourteen recovered blocks and the invalid
scope process refusal; both Cleaver entries declare `weapon.cleaver` in the KB.
Historical reuse candidates remain suggestions. Review evidence is retained in
`build/audit/m0-reconciliation/coordinator-review.json`; engine behavior remains
subject to the implementation and acceptance steps below.

## Implementation blocks

Default execution order: **M0 → M2 → M3 → M4 → M5 → M1 → M6**.
Block IDs remain stable for existing references; table order defines execution.

### M5 batch.D families (2026-10-12, corrected delivery)

Dark Jester is connected through its canonical grade-2a profile: one optional
trick each combat turn, with selection stopping at the first accepted choice
(including the simulator's default policy). Sidestepper grants the selected
unmodifiable 4+ melee save; Banter applies the contact enemy −1 / incoming +1
pair; Trip reads FighterState and replaces one nominated wound roll before it
runs. The residual post-wound Trip block is deleted. Declining offers once,
resolves an ordinary successful wound and requests no trip-roll; acceptance
uses D6 1/2+ without a wound die. The single-use resource and all trick slots
reset at the next combat-turn selection.

Other batch.D consumers and bindings are delivered, **not whole-profile
closure**: Mantle of Crows repeats its isolated fixed S2 melee hit before blows;
Backstabber requires a supplied unseen charge for first-round hit/injury +1;
Thin Flesh changes melee wound-context Toughness only; Slay Large Creature adds
charge Strength against explicitly supplied Large size and stacks with the
weapon bonus in wound and armour contexts. Printed sources were re-read
manually, not classified by scripts. No unrelated intrinsic clause was excluded
to admit a bearer.

### M5 batch.D carrier closure (2026-10-13, coordinator)

The four carriers left open by the batch.D delivery are closed. Each printed
definition was re-read manually at the Mordheimer page its own profile links and
stands verbatim in the KB in place of the assigned catalogue summary: the
Assassin's Backstabber ('Uses the source backstab rule.'), the Hillman's Thin
Flesh ('Uses source vulnerability rule.'), the Crow Master's aggregate rule
(Mantle of Crows, Needle and Thread, Payment in Blood, Decay of Ages) and the
Knight's Slay Large Creature already carried its printed text. The Spanish prose
of all four rules was replaced with translations of the recovered text instead of
the retained 'uses the source rule' summaries.

Each admitted consequence now has data, binding, configuration, compilation and a
modular consumer through existing operators only: `mechanic.mantle-of-crows` and
`mechanic.needle-and-thread` in `rounds.resolve_round` and
`attacks._resolve_wound_damage` with the Leader borrow in
`leadership.resolve_local_leadership`; `skill.backstabber` in
`contexts.prepare_hit_context`/`prepare_wound_context`; `rule.thin-flesh` in the
melee wound context; `mechanic.hillman-lycanthrope` for activation, wolf line,
kit discard and Bite; `rule.slay-large-creature` in the charge Strength of the
wound and armour contexts; `compiler.assassin-poisoner`,
`compiler.weapon-knowledge` and `compiler.no-blackpowder-weapons` in the
compiler. The clauses outside the duel are separated on their own effect records
with a named reason: the Crow Master's post-battle abduction and the Decay of Ages
casting, the Assassin's campaign acquisition/lending and permanent ownership plus
the terrain-qualified Hide in Shadows, and the Hillman's half-rate moving shot.
The Ogre Bodyguard's printed 'choose two weapons from sword, axe or club, or a
double-handed weapon' kit is now expanded by the shared eligibility module (TS +
regenerated bundle) instead of refusing the core-grade profile with an opaque
`flatMap` crash.

One configuration stays **blocked, recorded rather than worked around**: the
Halfling Knight's unique cavalry spear has no canonical combat mapping and none is
faithful (the source prints +1 Strength for charging with a cavalry spear; the
canonical spear prints only 'strikes first', and the canonical lance is a mounted
+2 weapon usable only on horseback). No mount is enabled and no ordinary spear is
substituted; the profile is refused by name with
`hireling unique equipment needs a canonical combat mapping`, and the block is
recorded in the profile's `unresolved_references` and on its register row.

Focal checks: `test_t13_batch_d_families.py` **38 passed** (Mantle activation,
repetition and negative control; Needle and Thread sewing plus the refused Leader
borrow; Backstabber trigger/expiry matrix; Thin Flesh melee-only discrimination;
Lycanthrope 4+ activation, retained wolf form, failed-roll -1 injury row, kit
discard and Bite; Slay Large Creature stacking and expiry; the canonical kit and
the named refusals of the incomplete configurations). The shared eligibility kit
change is verified by `test_t13_hireling_admission.py` (the core-grade profile
compiles and fights) and `npm run check:eligibility` reports the bundle current.
Register: five carrier rows updated by
`build/audit/m5-coord/apply_batchd_carriers_close_csv.py`; all 4,556 keys, 3,594
origins, clause texts, fingerprints and prior notes retained and the unchanged
`validate_csv.py` reports PASS with 0 violations. Modular only; no full suite,
parity, coverage, new report, commit or push.

### M5 continuation (2026-10-13, coordinator)

**Ghostly Howl closed end to end.** The printed clause (Call Of The Night Haint,
0-1 Tomb Banshee / Ghostly Howl) is now `implemented: 'YES'` on
`tomb-banshee--ghostly-howl` with the binding `mechanic.ghostly-howl`: the
close-combat and execution mechanics registries, the modular tag-consumer map and
the modular-only refusal set carry it, and the consumer is
`leadership.resolve_local_leadership`, which drops the tested enemy's Leadership
by one D6 before its fear test on both the charge and the charged path and
requests no such die on a non-fear Leadership test. The printed 6-inch radius,
which reaches every enemy on the table and is not what a 1v1 duel supplies, is
carried as its own `scope: 'NO'` effect record inside the same rule rather than
silently admitted. The register row is corrected and closed by
`build/audit/m5-coord/apply_ghostly_howl_csv.py`: its inherited
`semantic_contract`, `conditions` and `consumer` described a charm-style control
effect its own `clause_text` does not print, so those three columns were
corrected to the printed text; clause text, fingerprint and keys are untouched
and the unchanged validator reports PASS with 0 violations. Discriminating
checks: `test_t13_psychology_leadership.py -k ghostly` **1 passed** (the
activated penalty fails an otherwise-passing fear test, the same dice pass with no
howl and no penalty die is requested, and an ordinary Leadership test spends two
dice only).

**Measured hireling admission partition (the authority for the M5 admission
family).** `build/audit/m5-coord/measure_admission.py` through the canonical route
(130 profiles offered): **22 compiled with a legal printed kit, 12 compiled with
the kit unspecified, 82 refused for a pending intrinsic clause, 4 refused for an
unmapped unique object, 4 needing a supplied configuration or a missing item
record, 5 outside the duel runtime, 1 refused in an active slot.** By grade:
grade 2b 23 offered / 20 compiling, hired-sword `core` 7 / 6, dramatis `core` 4 /
2, dramatis 2b 5 / 3, dramatis 2a 7 / 1 (the canonical Dark Jester), dramatis 1b
10 / 1 (the Crow Master), hired-sword 2a 20 / 1 (the Cursed Hillman) with the
Halfling Knight refused by name for its unmapped cavalry spear, and every grade
1a/1b/1c profile refused for pending clauses. The partition recorded earlier in
this file (32 / 24 / 52 / 12 / 5 / 5) is **not reproducible in this tree**: the
canonical hireling catalogue holds executable runtime for the whole 2b grade and
for the four carrier rules only (grade 1a 4 of 31 rules, 1b 1 of 136, 1c 0 of 60,
2a 9 of 88, core 0 of 23), and no cached or worktree copy of the missing blocks
exists (`build/cache/**`, every `.worktrees/*`). Those profiles' register rows
still read `projection`/`data`/`connection`, so the register and the KB agree;
the stale figure was in the prose. The same class of gap affects the band-rule
test material written ahead of the KB: the new (untracked)
`test_t13_psychology_leadership.py` fails 25 of its 27 cases because the band
rules it selects (`band--black-orc-special-skills-ere-we-go` among them) are
`implemented: 'NO'` with reason "Deferred subsystem: psychology or mounts" in the
canonical KB, while the file expects the delivered bindings; its `ghostly` case
is the one this continuation made real. The *committed* `test_catalog.py`
failures are the inherited set (the two eligibility refusals, the frozen
`classified == 2908` count now 3021, the supplied Snorri input and the
witch-hunters message), unchanged by this work. Completing the grade 1a/1b/1c/2a and core intrinsic runtimes is the
largest executable remainder in this M5 assignment; the four carriers assigned to
this continuation are closed (above), and no profile was unblocked by calling a
printed duel consequence out of scope.

**Admission file corrected to the measured state.**
`test_t13_hireling_admission.py` asserted admission for eleven cases whose
profiles the register itself records as pending; those cases now assert the
measured refusal with its named cause (pending intrinsic clause, unmapped unique
object, an unknown mechanic id, or a supplied-configuration demand), and the
discriminating subjects that remain exercisable moved to admitted bearers (the
Holy Man's printed staff equivalence, the core-grade Ogre Bodyguard's fear
consequence and its fear-caused charge refusal through the round pipeline).
Fresh: `test_t13_hireling_admission.py` + `test_t13_batch_d_families.py` **55
passed**; `npm run typecheck` clean; `npm run check:eligibility` current.

### M4 measurable progress (2026-10-09, after M4-finish recovery/review)

The closed reporting set remains **793 admitted clauses / 762 origins**.
Lettered deliveries are increments, not extra external-agent tasks. Counts below
come from those exact keys in the complete maintained register; they describe
remaining work, not certification or a time estimate.

| State in the maintained CSV | Clauses | Meaning |
| --- | ---: | --- |
| No remaining implementation work declared | 693 | Earlier completed work plus 17 closing-dispatch clauses; evidence and acceptance remain independent. |
| Participant/provider projection pending | 68 | Canonical facts/bindings exist or are retained, but the admitted participant/provider route is missing. |
| Connections pending | 9 | A source-faithful canonical selection/connection still needs work. |
| Data pending | 10 | Missing qualified identity, skill or characteristic projection. |
| Behavior pending | 10 | Eight unfinished contracts/variants plus the two reserved Slave Driver corrections. |
| Assessments pending | 3 | Beauty contact lifecycle, Wild Lunatics duration and the Gaoler opponent-category equivalence. |
| **Total pending** | **100** | 793 minus 693; 82 hireling-origin and 18 other clauses. |

The separate existing `fungus-rowdy` clause is preserved with its admitted
individual consequence and excluded group producer. It was outside the frozen
793-key reporting set; that denominator has not been silently expanded.

M4-finish reviewed disposition: **113/113 keys preserved**, with 17 declaring no
remaining modular work and 96 pending (68 projection, 10 data, nine connection,
eight behavior, one assessment). Together with the four reserved final-pass
clauses, these are the 100 pending keys above. The implementer's 68 delivery
claims largely establish canonical metadata or reusable behavior; they do not
prove all 68 end-to-end Combat Lab routes. Beast Hunter remains projection-pending;
Marks of Morr still needs an Augur-only selection route; the supplied Khorne
condition provides Frenzy but does not automatically project the printed +1
Attack. Gaoler's broad Chaos/Undead bindings require a bounded comparison with
its printed enemy list before claiming exact equivalence. These gaps are retained
per clause, not converted into a global blocker.

Register recovery: the updater wrote its 113 assigned rows as the entire register,
and the attempted reconstruction from the reduced committed file produced only
2,184 rows. That was data loss, not inherited correspondence noise. Recovery used
`build/cache/m4/T13-before-m4c2.csv` (4,556 rows), the complete 793-key M4 snapshot,
the latest scoped M4 updates and the Rowdy record. All 4,552 historical keys and
the four M0 additions are conserved; original clause texts, fingerprints, review
notes and post-M0 implementation changes are retained. The maintained register
again contains **4,556 clauses / 3,594 origins**. The unchanged M0 validator now
passes with zero violations and zero uncovered non-NO inventory identities.
The updater now patches the complete register, refuses incomplete/concurrent
inputs and conserves historical keys before writing.

Further register recovery (2026-10-12): the live file had reverted to 1,390
clauses. Restored the full 4,556-clause / 3,594-origin register, the recorded M4
dispositions and final M5 round-4 dispositions, preserving the two recent Jester
contract edits. Admitted pending is again 763; the unchanged validator passes.
Superseded intermediate M5 measurements were not fabricated. Recovery copies
are retained under `build/audit/register-recovery-20261012/`. Active writers must
reload the recovered register before their next update.

Fresh focal evidence: `test_t13_m4finish_connections.py` **9 passed**; four supplied
campaign-condition compilation probes passed. Catalogue assertions are not tagged
operator behavior evidence: the current Beast Hunter negative witness carries
neither new tag, so the qualified-operator witness gap is recorded for the final
pass. No broad suite, parity or coverage repeated; no engine or KB changes made
by this recovery. M4 remains **partially accepted** and T13/T14 stay open.

Closed assignments remain `build/audit/modular-dispatch/M4-complete-input.csv`
(the 793-key denominator) and `M4-finish-input.csv` (the 113-key closing dispatch).
Preserve every clause; use the complete maintained CSV for its current work,
consumer and evidence state. Independent M5 work can proceed. Admission/data/
connection gaps are handled in the existing M1 dispatch, remaining new behavior
in dispatch 3, and isolated review defects in dispatch 5; no additional lettered
dispatch is introduced.

### Fixed remaining dispatch count (2026-10-09)

There are **six remaining dispatches**, including correction and closure. This
is the execution commitment from the M4f review onward, not a claim that the
previous lettered deliveries had a predetermined total. Families are internal
work units; do not turn each newly encountered family or review finding into
another external-agent assignment.

| Dispatch | Closed responsibility | Completion boundary |
| --- | --- | --- |
| 1 — Finish M4 | All remaining admitted Psychology/Leadership clauses, including the proposed M4g consumible/random-state families and the other unfinished M4 variants and connections. | Every remaining M4 clause has complete implementation or a concrete source/dependency disposition; no silent deferral to another lettered prompt. |
| 2 — Complete M5 | All remaining admitted lifecycle, recovery, reaction, temporary-state and composite effects assigned to M5. | Complete each admitted consequence and its necessary canonical/product route; retain excluded remainders. |
| 3 — Finish residual M2/M3/M4 behavior | Offensive, defensive and Psychology/Leadership behavior the earlier partial deliveries did not complete, excluding defects already collected for dispatch 5. | Remaining new behavior and its necessary connections are completed or explicitly blocked; M1 does not inherit new behavior. |
| 4 — Complete residual M1 | Remaining data, grants, recipients, construction/projected facts and existing-operator connections after dispatches 1–3, including unresolved assessment rows. | Reconcile actual residual work once; implement valid connections and resolve assessment/disposition without reopening completed families. |
| 5 — Accumulated corrections | All recorded required implementation defects, grouped by consumer, including findings from dispatches 1–4. | Reproduced defects corrected with focal discriminators; inspection-only concerns settled without speculative refactoring. |
| 6 — M6 closure | Integrate the completed deliveries, finish transverse product gaps and perform the joint modular closure check. | Report actual clause coverage, remaining external blockers and verified modular boundaries; no optimized ports. |

A long assignment may resume across sessions under the same dispatch. A newly
found clause belongs to its responsible dispatch; it does not increase this
count. Findings discovered during correction or closure are resolved within
those dispatches. External source/user-decision blockers remain explicit and
prevent a full-completion claim where required; they are not hidden by the fixed
schedule. Change the count only for an explicit scope change or a concrete
dependency requiring a separate assignment, and explain that change beforehand.

Execution policy (2026-10-09): prioritize the remaining rule families. Record
review findings in the existing CSV notes with affected clause IDs, impact,
responsible consumer, a reproducer where available and a closing criterion.
Collect their corrections in one final pass after the implementation blocks and
before M6 closure. A known defect keeps its clause pending; it does not require
an immediate repair dispatch or prevent work on independent families. Fix it
earlier only when it prevents the next assignment from being implemented or
checked, risks losing data, or makes that assignment depend on incorrect behavior.
Agents must still complete their assigned effects and run proportionate focal
checks; this policy is not permission to omit required connections or evidence.

| Block | Remaining responsibility | Entry condition |
| --- | --- | --- |
| M2 — Offensive resolution | Weapons, hits, wounds, poisons, criticals, priority, extra attacks, nominations and offensive resources. | Reconciled M0 assignment and each family's actual prerequisites. |
| M3 — Defenses and damage | Parries, armour, saves, immunities, injuries and provenance-dependent exceptions. | Integrated M2 deliveries relevant to its consumers. |
| M4 — Psychology and Leadership | Individual Fear/Hatred/Frenzy/Stupidity, immunities, tests, target filters and admitted personal conditions. | Integrated preceding deliveries and concrete family prerequisites. |
| M5 — State and composite effects | Preparations, recovery, reactions, temporary effects, special decisions and residual hireling clauses. | Integrated preceding deliveries; group by lifecycle moment and consumer. |
| M1 — Residual connections and data | Remaining grants, recipients, characteristics, profiles, items and shared restrictions that reuse existing operators. | After M2–M5, refresh its assignment from the maintained CSV and remove work those deliveries already completed. |
| M6 — Functional modular closure | Transverse editor/configuration/analysis/CLI gaps, final family reconciliation and joint checks. | Integrated M2–M5 and residual M1 deliveries. |

Complete each effect end to end: canonical access, compilation, modular
execution, necessary configuration inputs and focused evidence. Product inputs
belong to the effect's delivery; M6 is not permission to postpone an inaccessible
feature. Split only for a real dependency, source blocker or concrete benefit.
**M2–M5 include all data, bindings, grants, legality, compilation and product
inputs necessary for their effects. Do not defer these connections to M1.**
M1 is a final residual pass, not a parallel lane or a repeat of completed work.
If an earlier family needs a prerequisite normally associated with a later
block, the coordinator includes it in that family's closed assignment or orders
the prerequisite first. Do not deliver an unusable effect to preserve table order.

### Execution and ownership

- Default to one implementation writer at a time, integrating deliveries before
  the next dependent assignment. Read-only preparation or review of a frozen
  delivery may overlap; it creates no extra implementation or audit task.
- Any exceptional parallel implementation needs explicitly disjoint assignments,
  owned files and consumed contracts on known revisions. M1 is not scheduled
  alongside M2–M5.
- No concurrent editing of central models, compiler/contracts, effect
  registries, contexts, phases or equivalent shared files. Disjoint lines in one
  central file are not sufficient independence.
- A change to a contract another agent consumes is also a dependency, even when
  the files differ. Serialize it and publish a new integrated base.
- The coordinator owns shared CSV updates, reservations and acceptance. A
  dispatch may delegate a named path, never an unspecified shared area.
- A private checkout does not authorize unrelated work or optimized behavior.
  Required support/refusal declarations need explicit ownership and must not
  enable unsupported backends or a hidden modular fallback.

Each dispatch states its base revision, closed origin/clause set, family
contracts, authorized files, owner, dependencies, semantic discriminators,
expected focused checks and observable completion criterion. It assigns work;
this general plan does not. Check ownership again before editing.

## Agent references and manual interpretation

Read the applicable sections of:

- [Modular implementation guide](../../guides/modular-engine-implementation.md)
  and [general rule implementation](../../guides/implement-and-verify-rules.md).
- [Architecture](../../reference/architecture.md),
  [KB conventions](../../reference/knowledge-base.md) and
  [shared eligibility](../../reference/eligibility.md).
- [Verification](../../reference/verification.md),
  [specification conventions](../../../tests/specs/README.md) and the existing
  family scenarios/tests and consumers cited by the assigned clauses.
- [Permanent rulings](../../decisions/design-rulings.md),
  [consolidated 2A/2B knowledge](2A2B-Knowledge.md) and the maintained semantic CSV.
- [Application guidance](../../guides/modify-application.md) and
  [web presentation](../../reference/web-presentation.md) when the owned change
  actually affects those paths.

The broad certification procedures in general references apply at their phase
boundary. The per-family modular testing policy below governs these batches.

**Before coding, interpret each distinct contract and each origin's differences
manually.** Read resolved source text; compare trigger, timing, recipient,
conditions, consequence, duration, stacking, choices, exceptions and exclusions.
Source names, bindings and metadata cannot establish equivalence by themselves.

Identify a plausible alternative interpretation and a case that distinguishes
it from the governing source/ruling. Write expected outcomes independently of
the implementation before checking the code. Existing tests are not authority
when they contradict source text or an adopted ruling; recover the original
source if the KB does not resolve the issue.

Trace source → grant/binding → shared legality → compilation → modular consumer
→ observable result. Distinguish a missing connection from missing behavior;
reuse a suitable operator. Construction decisions remain in shared eligibility,
not duplicated in Python, campaign code or UI.

Scripts may enumerate, calculate hashes, check references/format and serialize
explicit decisions. They must not decide scope, equivalence, intended behavior
or completion through keyword classification or bulk semantic defaults.

## Proportionate testing and semantic evidence

Test a **contract or variant**, not every name that reuses it. Extend existing
family cases first. Record manual correspondence for each origin; test only the
parameter, recipient or exception differences that require another witness.

| Change type | Minimum useful evidence |
| --- | --- |
| Connection to an existing operator | Canonical compilation/access, valid recipient and a relevant negative control. Reuse current executed operator evidence; do not duplicate its behavior tests for aliases. |
| Local modifier or parameterized variant | Usually 2–4 cases: activation, absence and a distinguishing boundary/exception. Assert a real phase consequence, not only a compiled field. |
| Stateful behavior or decisions | Usually 4–8 short scenarios per contract/family: relevant choice, order, consumption, persistence/expiry and interruption. Use strict dice/decisions with complete consumption checks. |
| Concrete interaction risk | The smallest composition case exposing double application, exceptional immunity, save provenance, mixed attacks or a shared resource. Avoid unrelated Cartesian products. |

These ranges are guidance, not quotas or permission to omit a printed exception.
One scenario can prove construction, execution and composition. Do not mirror
the same assertions in unit, integration and semantic batteries automatically.
Prefer an existing semantic specification; add Python tests only for a concrete
gap its current scenario operations do not exercise.

For a new high-risk contract, require one discriminating counterexample or
focused behavioral mutation using existing mechanisms. It must detect the wrong
interpretation or consumer behavior, not merely a changed metadata field.
Do not build mutation campaigns or new general-purpose test infrastructure.
Preserve the schema/role requirements of any executable specification used;
reuse valid cases rather than weakening verification to reduce test counts.

Expected values come from source/rulings, not observed engine output, duplicated
implementation constants or historical fixtures that contradict the source.
Identify synthetic fixtures explicitly; they do not prove canonical access.
Reuse a family-level product smoke check for newly required inputs rather than
creating a UI suite for each alias.

Run the affected family cases and checks for consumers actually changed. A
shared eligibility change needs focal Python and TypeScript evidence. Use the
maintained validator/generator for changed schemas, bundles or web artifacts.
Do not run full semantic/construction suites, parity, coverage or other-engine
campaigns per family. Do not refresh unrelated pins, budgets or expected totals.

## Coordinator acceptance and integration

Use one short, bounded acceptance pass per delivery, not another audit or a
repeat of the implementation's testing campaign. Start with the owned diff and
existing handoff; expand only to resolve a concrete doubt.

1. Check changed semantic contracts, variants and exceptions against
   sources/rulings. Reuse accepted interpretation and evidence where their inputs
   still match; do not re-study unchanged families or test every alias.
2. Inspect the complete owned diff for scope, canonical access and layer
   responsibilities. Examine concrete interaction risks, not hypothetical ones.
   A green test alone cannot settle interpretation.
3. Re-run the smallest representative semantic discriminators, prioritizing new
   behavior and delicate exceptions. Reuse valid focal logs for the remaining
   checks; do not repeat whole family batteries without a concrete reason.
   Keep inspection, interpretation and executed evidence distinct.
4. Integrate the complete patch, including new files, onto the current accepted
   base. Re-run only checks affected by integration or changed dependencies.
5. Update the maintained semantic CSV and progress table after acceptance.
   Preserve reusable contracts/cases and explicitly keep optimized ports pending.

The agent's handoff is concise: covered family/origin IDs, source/ruling,
behavior, checks actually run, remaining gaps and reusable case locations.
Do not create per-rule reports. Agent delivery is not coordinator acceptance.
Do not silently discard failed required checks as inherited; report their actual
impact on the owned acceptance boundary.

Accept usable families with non-blocking follow-ups and continue to the next
independent assignment. Minor documentation, redundant tests, cosmetic issues
and optional cleanup need not delay acceptance. Record each real follow-up once
in the existing CSV notes or permanent problems register, with affected IDs,
impact, responsible layer and a concrete resumption point/closing criterion.
Do not create a separate review report or review task for every finding.

Wrong duel behavior or interpretation and missing required canonical access or
product inputs prevent acceptance of the affected clauses. Retain their pending
work and collect isolated corrections for the final pass instead of repeatedly
interrupting new implementation. Data loss and defects that invalidate the next
assignment require earlier correction. Accept independent families separately;
acceptance with follow-ups is bounded to the reviewed delivery, not certification
of M2 or the entire engine.

After integrating all blocks, the coordinator runs one joint modular check,
affected semantic cases and canonical structural validation. Repeat a check
only when changes or unresolved concerns justify it. This does not certify the
other engines or close T14/T15.

Before that closure check, resolve the accumulated required corrections together,
grouped by consumer and lifecycle. In particular, retain the M4c contact-timing
and successful-test resource-state findings and the M3 Ranald/ethereal composition
finding for this pass unless a subsequent assignment depends on their repair.

The modular engine is complete when every required admitted clause has canonical
access, full execution, necessary product inputs and accepted evidence. Keep
source/interpretation blockers actionable; any remaining required blocker means
partial closure, not a completed engine.

## Progress register

Stop checkpoint requested by the user (2026-10-14): the current Condemned block
is complete. Its four variable attributes reuse lazy Inconsistency; supplied
permanently fixed attributes retain their declared values, with ordinary
equipment access only after all four are fixed. Variable fighters use natural
attacks without unarmed penalties. The shared validation transport and desktop
configuration preserve this state. Nine focused construction/UI cases passed;
five individual CSV clauses were integrated with full-register conservation.
Rune item consequences previously passed ten construction cases and one UI
case. No joint closure check or T14 certification has been performed.

Concurrent packages stopped with literal integration candidates still pending
coordinator review. Lifecycle reported 109 focused passes before its last
castoff adjustment and 75 lifecycle passes afterwards. Remaining executable
work includes physical mutation/equipment composition (especially numeric item
bonuses already compiled into Characteristics), canonical admission of Marianna,
Sigmund and Bone Goliath beyond their implemented No Pain consumers, outstanding
data/assessment integrations, and the final modular/construction check. Positive
source-derived admission tests remain unresolved; they must not become rejection
tests to conceal those gaps. External source/ruling questions below remain
separate. Work is paused at the user's requested block boundary.

Current working checkpoint (2026-10-14, modular continuation; not acceptance or
T14 certification): lost state fields and demonstrated canonical connections
have been recovered by fragment, retaining the current Trip, Dark Jester, Crow
Master, Assassin, Hillman and Ghostly Howl contracts. Residual charge gates,
source-specific songs and belches, supplied providers, persistent Frenzy,
personal roll resources, defensive composition and lazy Belandysh characteristics
have focused evidence. Canonical kits, named grant tables and the remaining
individual assessments are still being reconciled; newly recovered Gaoler,
Foole and Electrical Touch consequences now have focused execution evidence.
Timed Djinn save composition and the Inquisitor's individual D66 mutation
consequences remain active work. The complete 36-result primary-source chart
has been transcribed without importing its campaign, terrain or shooting facets.

The lasting injury result family is connected through canonical supplied
conditions and the existing shared construction decisions: Toughness, Initiative
and Weapon Skill penalties, and amputated-arm active weapon restrictions without
a prohibition on holstered ownership. Four focused cases passed through
compilation and the modular round route. The seven affected Fen/Shallya cases
also passed after restoring the printed fire exception and preserving weapon
Initiative during lazy priority refresh. Shared eligibility was rebuilt after
the condition transport change.

The latest register integration applies 60 individually reviewed defence and
lifecycle clauses, correcting the old Miniath, Gaoler, Foole and Djinn contracts
rather than preserving contradictory summaries. Three Physiology assessments
were corrected to excluded post-battle Serious Injury rerolls after reading
their full paragraphs; their separately admitted Poetry consequences remain
open independently. The mutation and hireling schemas now admit their actual
source data and reuse the canonical execution parameter vocabulary. The focused
schema/field checks passed 42 cases; the three affected catalogue documents
validate. These checks do not replace the final modular/construction check.

Every register integration reloads the live 4,556 rows, checks immutable keys,
texts and fingerprints against the complete entry snapshot, retains earlier
notes and rejects concurrent changes. The current validator reports zero
violations. The joint modular/construction closure check is reserved until the
remaining executable integrations are stable. Source questions about Lunatics'
duration, the Alchemist's two unspecified test/brewing clocks, Scryer's roll
ownership and Djinn penalties against explicitly unmodifiable saves remain
separate from missing connections; independent families continue.

The coordinator updates this table. It tracks **residual blocks**, not the
implementation status of every historical rule. Previous completed deliveries
remain completed; the closed assignments from M0 determine what is left.

Implementation states: `Waiting`, `Not dispatched`, `In progress`, `Delivered`,
`Partial` or `Blocked`. Acceptance states: `Pending`, `Changes requested`,
`Partially accepted` or `Accepted`. Delivery does not imply acceptance.

| Block | Closed assignment / accepted families | Owner | Implementation | Coordinator acceptance | Integrated revision / evidence | Blocker / next action |
| --- | --- | --- | --- | --- | --- | --- |
| M0 — Canonical baseline and inventory | Reconciliation accepted; in-scope coverage fixed; coordinator findings repaired | Coordinator | Delivered | Accepted | CSV reconciled: 4,556 clauses / 3,594 origins; SHA-256 `531e54b8…` (baseline `cf24778a…`, delivery `147f06a1…`). Inventory `report rules --inventory-only` → `outputs/audit/m0-reconciliation-20261008/` (combat 7,458 / rules 7,140 rows); independent checks in `build/audit/m0-reconciliation/coordinator-review.json`. | Dispatch M2 using a closed remaining-family assignment; follow M2 → M3 → M4 → M5 → M1 → M6. |
| M2 — Offensive resolution | `build/audit/modular-dispatch/M2-offensive-input.csv`: 48 clauses / 44 origins, SHA-256 `0a8abb5b…`; checked key-by-key against the register (field-identical, no drift). Independent families dispatched, no family deferred to M1. | Offensive-batch implementer | Partial — delivered families plus recorded blockers | Partially accepted — completed families only | New behaviour: the Domnu Bear Hug (a `profile-rule.domnu--bear-hug` compiler contract + two-fist gate in `modular/pools.py`), the Kaz fanatic rebound to `mechanic.frantic`, and the Lahmia compiler binding over its mechanic binding; the Domnu family entry and its canonical binding share the `profile-rule.` namespace so both the registry and the shared-contract lookup resolve it. Repaired projections: `sword_heroes_only` on the shared Skinks list and `boar_spear_aristocrat_only` on the shared Cursed Cavalcade heroes list now carry the printed recipient gate. Reused operators verified without duplication: pike first-round scope, Hellblade material and recipients, Skull Busta, Obsidian access, Sword Heroes-only (Pirate list) and Nippon katana, long daggers, Shock Rod, knuckledusters, bloodroot damage, Dragon Monk unarmed mastery, Witch Elves list, Great Claw, boar-spear off-hand bound. Focused checks (real results): `test_t13_always_strikes_first.py` + `test_t13_domnu_bear_hug.py` + `test_t13_automatic_grant_matrix.py` + `test_t13_dragon_monk_unarmed.py` + `test_t13_pike_first_turn_scope.py` + `test_local_weapon_items.py` + `test_profile_bindings.py` + `test_t13_construction_recipients.py` → 210 and 99 passed, then 226 passed after the binding-namespace repair; `tests/python/knowledge/test_editorial_schemas.py` 295 passed; `tests/python/knowledge/test_catalog.py::test_every_runtime_binding_resolves_to_a_known_shared_contract` PASS (it exposed the Domnu binding namespace, now fixed); `tests/python/verification/test_structural.py` spec checks 6 passed, and the phase-verification audit reports only the two `boundEquipment` projections that already fail at HEAD (`night-goblins-mic/snotling-mob-consists-of-5-snotlings`, `khemri-cursed-of-karak-zorn/cannibal-dwarfs`, reproduced in a clean HEAD worktree); the maintained `tests/specs/structural/phase-verification.yaml` and its pinned count gained the batch's two new special compiler bindings; `tests/python/construction` 706 passed / 12 pre-existing failures that reproduce with the batch's source edits stashed; `build/audit/m0-reconciliation/validate_csv.py` PASS, 0 violations. 48 assigned clauses updated by `(origin_id, clause_id)` with executed evidence, no fingerprint or clause text changed. | Real blockers, not deferred work: (1) the hireling references (`aksho` #2, Ienh-Khain #35–#38, grades 1a/1b/1c/core #39–#48) — only grade-2b hirelings are promoted into the duel combat packages, so their printed consequences have no canonical configuration; the shared operators already exist and only the grants plus the reference routing would remain once a grade is promoted. (2) `magic_acorn` #33 — the item declares `combat_status: out_of_scope`; delivering the printed first-round auto-hit needs an explicit re-scope and a new operator, not a connection repair. (3) source-vs-contract clarifications: the Cathayan longsword contract carries an unsourced `armour_penetration: 1` (#4/#12); the Starsword (#7/#22) and Sun Gauntlet (#9) item prose contradicts the mechanic record the engine implements; the Starsword Dodge exception (#8) has no engine field to evaluate; `grand-master-ippan-shu` (#44) names no unarmed family. M2, T13 and T14 stay open: this is a delivery pending acceptance, not a closure. |
| M3 — Defenses and damage | `build/audit/modular-dispatch/M3-input.csv`: 49 clauses / 48 origins, SHA-256 `0b6a9d8c…`; frozen before editing and re-checked key-by-key against the register (field-identical, no drift). Independent families dispatched; deferred work recorded, not moved to M1. | Defences-batch implementer | Partial — returned defects corrected and accepted | Corrections accepted; block remains partial | New behaviour: **Chosen of the White Tower** and **Instinctive Warrior** (two selectable Karak Azgal skill tables) gained canonical runtime blocks in `catalog/skills/warband.yaml`, close-combat/execution mechanics and registry families, with `modular/state.py::_parry_capacity` and `modular/contexts.py::_parry_context` honouring the tags — Chosen grants the parry without a sword or a buckler but its own re-roll only when armed with a sword or a buckler (a trident parries with no re-roll), and Miniath keeps its independent native-parry re-roll; Instinctive Warrior parries with the double-handed weapon as an ordinary sword. **Marks of Ranald** gained `mechanic.marks-of-ranald` bound on the grade-2b Trickster-Priest and is now a hit-stage duck: `attacks._resolve_reference_attack_once` and `pools._resolve_prepared_defences` roll the unmodifiable 6+ (magical attacks included) before the wound/critical, and the operator no longer carries a `ward_save`, so the duck cannot save a second time; the Ranald's Luck and Cat Friend remainder stays LATER. **Bark Skin** keeps `trait.natural-armour-save` 6 and `trait.natural-armour-worst-save` 6, but `phases.armour_target` now caps the Strength penalty together with the attack's own save bonus and adds the weapon's armour penetration after the cap, so the printed Cutting Edge exception survives; the rule is completed with `EffectSet.natural_armour_negated_by_fire`, the `trait.natural-armour-negated-by-fire` binding, `TRAIT_TYPES`, the compiler projection, `MODULAR_FIELD_CONSUMERS`, `runtime-scope.yaml` and the execution/operator schemas, so a fire hit denies only the inherent hide save (worn armour and other bands' natural armour untouched, the Fimir Scaly Skin control stays 5). **Layers of Fat** gained `trait.natural-armour-unmodified`; a new `companion-filly--odd-covering` profile rule carries the 5+ unmodified/magic-negated covering beside the Dame of the Mare precedent. Reused operators verified without duplication: silent-brotherhood cloak→`defence.buckler`, Snerik's short sword→`weapon.sword`, `weapon.trident` parry payload, white wolf pelt→`defence.wolf-pelt-cloak` (6+), Pristekk shock rod→`weapon.shock-rod`. The contract schemas were extended only where the new field/tags required it (`profiles.yaml.schema.json`, `catalog-mechanics-execution.yaml.schema.json`, `verification/consumers.py`, `tests/specs/structural/phase-verification.yaml`). Focused checks (real results): `tests/python/combat/modular/test_t13_defence_parries_and_ward.py` 28 passed (Ranald hit-stage duck with no wound/critical die, no resource spend and no second save; Bark Skin 6/6 with the Cutting Edge axe and the fire hit at 7 plus the Fimir control; Chosen sword/buckler re-roll against the trident non-re-roll and the independent Miniath re-roll); `tests/python/combat/modular/test_local_modifier_variants.py` 350 passed (the two Fen Guard fire cases updated to the completed no-armour-die rule); `tests/python/knowledge/test_editorial_schemas.py` + `tests/python/verification/test_structural.py` 301 passed / 1 failed, the failure the inherited boundEquipment pair; `tests/python/knowledge/test_catalog.py` 41 passed / 6 failed, all inherited (Snorri-drunk, stale count pins); `tests/python/combat/vectorized/test_shared_families.py` 4 failed, all inherited (stale count pins, loader scope validation, ogre-pit-fighter skill access); `tests/python/combat/modular/test_profile_save_thresholds.py` 23 passed / 1 failed, the failure the inherited Fimir duel roll-ordering. 49 assigned clauses updated by `(origin_id, clause_id)` with no fingerprint or clause text changed. CSV SHA-256 `d49fb5f8…` (prior M3 delivery) → `a56b20c2…`; `build/audit/m0-reconciliation/validate_csv.py` PASS, 0 violations. | Real blockers, not deferred work: (1) the hireling references outside grade 2b (Aenur/Ienh-Khain #7, Veskit #22/#39, Khar-mel #23, Aksho #27, Chaos Fury #28, Dark Jester #30, Countess #31/#40, Sigmund #32/#41, Rat Ogre #33, Snake Charmer #34, Bone Goliath #35/#48/#49, Troll Slayer #42/#43, Pathfinder #44/#45, Treasure Hunter #46/#47) — only the grade-2b packages are promoted, the same blocker M2 recorded; the shared operators already exist and only the grants plus routing remain. (2) Deferred or unadmitted producers: `band--pointy-stick` #15 (`scope: LATER`), the clockworkers Construct drug immunity #36/#37 (wider than the incoming-poison field). (3) Source-vs-ruling and unrepresentable: the Andanti 'roll under own WS' parry #1; the Miniath 'additional attempt' #2 (the canonical `catalog/rules/resolution.yaml` ruling caps at one and the engine matches it); the Wall of Steel two-handed spear parry #3 (needs a two-handed loadout choice); the Shaggy Hide Toughened Leathers cancellation #10/#11; Fungus Brew's floor against armour-ignoring hits #25; the Mourngul ethereal 3+ #26 (threshold hard-coded at 4+ and the profile does not carry the rule); and the five empty extracted item rows #17–#21. M3 remains partially accepted; T13 and T14 stay open. |
| M4 — Psychology and Leadership (M4b addendum) | `build/audit/modular-dispatch/M4-input.csv`: 13 clauses / 13 origins, SHA-256 `ef0b023f…`; frozen before editing and re-checked key-by-key against the register (field-identical, no drift). M4b addendum `build/audit/modular-dispatch/M4b-input.csv`: 8 clauses / 8 origins, SHA-256 `5a7fe86d…`, plus the in-place amendment of the four M4 rows whose recorded conclusion it supersedes (three `fear-of-elves` origins and `big-boss--second-in-command`). M4 delivered three independent families; M4b delivered the four corrections and the qualified-Hatred family; the conditional Leader is accepted and the two Elf/caster identity corrections it returned are now closed by the M4b2 identity correction. M4c (2026-10-09) is the next independent M4 assignment: `build/audit/modular-dispatch/M4c-input.csv`, 7 clauses / 7 origins over four shared contracts (the four `accustomed-to-fear` recipients, `enchanting-beauty`, `lahmia-deceive`, `lahmian-hypnotize`), SHA-256 `44970fb89f…`, frozen before editing and checked key-by-key against the register (field-identical, no drift). Other families retain their own work, not moved to M1. M4d (2026-10-09) is the next independent M4 assignment: `build/audit/modular-dispatch/m4d-rows.jsonl`, 15 clauses / 7 origins over the Devoted to the Vampire triggers, the Bitten transformation table, the remaining Lahmian copies, Favoured and the Lackeys equipment restriction, SHA-256 `a28354bc…`; the closed batch delivered two of those families and left the rest to their own work. M4e (2026-10-09) is the next independent M4 assignment: `build/audit/modular-dispatch/M4e-input.csv`, 207 clauses / 201 origins over the existing Fear and immunity, Hatred, Frenzy, Stupidity, automatic and handler Leadership and Leader-radius operators, SHA-256 `7b8158a2…`; frozen before editing and checked key-by-key against the register (field-identical, no drift). M4f (2026-10-09) is the next independent M4 assignment: the six printed supplied-Leadership provider rules (Dreamwalkers Inspiring Presence, House Guard Adjutant Relay Orders, both Slave Driver copies, Sea Ghosts Minstrels Songster, Protectorate Hound Devoted and Slavers Eunuch Broken Spirit), each read by hand from its printed origin; it adds no clause to the closed list and moves no family to M1. | Psychology-batch implementer | Partial — 693/793 clauses without remaining work; 100 pending (68 projection, 10 data, 10 behavior, nine connections, three assessments) | Partially accepted — scoped M4g/M4h evidence retained; M4-finish connections reviewed within the stated boundary; full register recovered | New behaviour: **'Ere We Go!** (three Orc warband skills plus the shared rule they reference) gained the new `mechanic.ere-we-go` in `catalog/mechanics/execution.yaml` and `catalog/mechanics/close-combat.yaml`; `psychology.resolve_fear` now takes an explicit `charging` role, so the bearer waives only its *own* charging Fear test and a charged Orc still tests, while `needs_test` keeps every other gate. **Fear of Elves** (three band rules) gained `mechanic.fear-of-elves`, consumed by `psychology.causes_fear` as a recipient-qualified, one-directional Fear: the named Elf frightens the bearer and is never feared back. Night Goblins are restricted with `applies_to.profile_ids` to the five printed Night Goblin lines, so the printed Fanatic exemption and the non-Goblin Cave Squigs/Snotlings/Great Squig/Troll stay outside; the Savage Goblin rule stays band-wide and the Greenskin `goblin-warriors` rule keeps its profile recipient. **Supplied Leader radius variants** gained `mechanic.leader-twelve` and `mechanic.leader-four` (each carrying the ordinary Leader tag plus its printed radius); `leadership.resolve_local_leadership` now reads the supplied provider's radius instead of the hard-coded six inches, so Gunnery Officer, both Reikland Military Discipline copies and both Norse Battle Tongue copies reach twelve inches and the Savage Goblin Big Boss reaches four. The band grants are restricted to the printed recipient (Captain/Jarl/officer, Big Boss) so a plain warrior never becomes a provider; the basic four-inch radius is exercised, but the printed Second in Command prerequisite is still missing: a usable Witch Doctor may be supplied as a friendly Leadership fact without becoming a duel participant. Registry: `implemented-canonical-families.yaml` gained the four mechanic families (counts 263/995 → 267/1007, `kinds.mechanic` 159 → 163) and `verification/consumers.py` gained the four tag consumers, so the structural tag audit stays closed. Focused checks (real results): `tests/python/combat/modular/test_t13_psychology_leadership.py` 9 passed — activation, negative control and the semantic exception for each of the three contracts ('Ere We Go! waives its own charge test with no die requested, the unselected control fails and cancels contact and the charged Orc still takes the sixes restriction; Fear of Elves is directional with the Fanatic/troll/Cave Squig controls; both radii act at 12"/4", keep the six-inch default and refuse the beyond-range or non-leader provider with the unconsumed decision). `tests/python/combat/modular/` 839 passed / 5 failed, all five the inherited ones (the two `test_catalogue_runtime` *Beauty of the Sea* cases, the `test_profile_save_thresholds` Fimir duel roll-ordering, and the two `test_source_corrections` four-player-turn cases); the M3 session measured 830 passed for the same directory, and the +9 are this file. `tests/python/verification/test_structural.py` + `tests/python/knowledge/test_editorial_schemas.py`: the phase audit reports exactly the two inherited `boundEquipment` projections (`night-goblins-mic/snotling-mob-consists-of-5-snotlings`, `khemri-cursed-of-karak-zorn/cannibal-dwarfs`) and no new error. `tests/python/knowledge/test_catalog.py` 41 passed / 6 failed, the six inherited. `tests/python/verification/test_semantics.py` 3785 passed / 51 failed, all inherited: `verify_semantics()` returns its 1205 pre-existing errors and none of them names a clause or mechanic of this delivery. 13 assigned clauses updated by `(origin_id, clause_id)` with no fingerprint or clause text changed. CSV SHA-256 `a56b20c2…` (M3) → `e0c49bb4…` (M4) → `1e50ae51…` (M4b); `build/audit/m0-reconciliation/validate_csv.py` PASS, 0 violations. **M4b — enemy identity, conditioned Leadership and qualified Hatred** (delivered on top of M4). *Enemy identity facts:* the identity is the model's own KB fact, never its band's. The registry declares `warband-group.bandit` over the Hochland Bandits and both Outlaws of Stirwood Forest warbands for the Hatred recipient, while the Fear of Elves recipient is the profile's own `elf_kind` (`high` / `dark` / `wood` / `other`), which the compiler projects as `species.elf` plus the `species.<kind>-elf` marker the Elf Hatreds read, so an Ivy Ferret (a woodland Spirit) or a Cold One (an animal) listed in an Elf warband is not an Elf and the `warband-group.wood-elf` band-membership stand-in was removed (25 groups remain); the compiler additionally emits `identity.spellcaster` from the profile's own `spellcaster` trait, read one by one from each admitted profile's printed declaration, which keeps prayer users, paid upgrades and advancement-granted casters outside the identity exactly as the campaign's Witch Hunter hiring rule does. *Conditioned Leadership:* `mechanic.leader-four` carries the new `mechanic.leader-fallback` marker, and `leadership.resolve_local_leadership` withholds a fallback provider while another usable same-warband leader is supplied, so the Big Boss's printed Second in Command Leader is offered only when the Witch Doctor's Leadership cannot be used — including when the Witch Doctor is supplied as a leader without taking part in the duel. *Qualified Hatred:* the three clauses share the existing `contexts._hit_reroll` first-round Hatred operator through three new mechanics (`mechanic.burn-the-witch`, `mechanic.hang-the-bandit`, `mechanic.profound-hatred`), each with its catalogue rows, its `verification/consumers.py` entry and its identity branch; nothing is cast, no third model, map, shot or spell is simulated. Seven band rules were promoted (`witch-hunters` and `trollheim-witch-hunters` Captain and henchman copies, `horned-hunters` Horned Hunter and Initiates, `chaos-streets-mordheim-inhabitants` Desolate Soul) and the shared `shared-rule.burn-the-witch` definition resolves through them without a second implementation. Registry: `implemented-canonical-families.yaml` counts 267/1007 → 270/1014 with the three new mechanic families (`kinds.mechanic` 163 → 166). Focused checks (real results, `tests/python/combat/modular/test_t13_enemy_identity_hatred.py`): 6 passed at delivery, 7 after the identity correction added the two missed-caster positives — Burn the Witch rerolls against the compiled caster identity but not against a non-caster or a prayer user and only in the first round, Hang the Bandit covers all three bandit/outlaw warbands with the non-bandit negative control, Profound Hatred covers several unrelated warbands and refuses the Sisters of Sigmar; `tests/python/combat/modular/test_t13_psychology_leadership.py` 9 → 12 passed, replacing the Wood Elf race-group case with the model-qualified species case (both Wood Elf warbands, the High and Dark Elf positives, the bare-`Elf` unnamed-kind positive and the Ivy Ferret / Cold Ones negatives) and the three Witch Doctor states with the beyond-radius and beyond-four-inches controls. `tests/python/knowledge/test_campaign_loaders.py` group count pin 24 → 25 with the declared Bandits-and-Outlaws group. **M4c — Fear immunity by recipient and the Lahmia Leadership/attack contracts** (delivered on top of M4b2). *Accustomed to Fear* (the four Khemri Lahmian Brotherhood recipients) gained the new *filtered* `mechanic.accustomed-to-fear`, consumed by `psychology.needs_test`: the exemption applies only while the fear-causer is a Vampire, a declared Skeleton or a declared Spirit, and those three are the model's own facts — `species.vampire` from the profile's `vampire` trait and the new `undead_kind` trait projected as `undead-kind.skeleton` / `undead-kind.spirit` by `compile_fighter` (`TRAIT_TYPES`, `runtime-scope.yaml`, the editorial schema and the Combat Lab editor carry the trait; the 21 profile facts were read one by one from each printed declaration, never inferred from the warband). The ordinary `mechanic.fear-immunity` is deliberately *not* bound, so a Zombie, a Wight, a Dire Wolf or any other Undead still frightens the recipient. **Enchanting Beauty** binds `mechanic.enchanting-beauty`, applied by `rounds.apply_opponent_leadership` as `condition.enchanting-beauty` and read by `leadership.resolve_local_leadership`, which lowers by one the Leadership actually tested — own or borrowed — while keeping the printed Undead/Daemon exemption. **Deceive** and **Hypnotize** bind `mechanic.lahmia-deceive` and `mechanic.lahmian-hypnotize`, resolved by one shared `LAHMIA_POWERS` loop at the start of `rounds.resolve_round`: Deceive tests with `own_value_only=True` (the supplied-leader block is skipped entirely, so a nearby eligible leader is never borrowed) and Hypnotize may borrow; a failure sets the pre-existing `charm_attack_blocked` state, so the barred enemy does not attack the Vampire in that combat phase and the suppression is re-tested — and can end — in the next; Hypnotize additionally adds `condition.hypnotized`, read by `contexts.prepare_hit_context` for +1 To Hit on every attack against the target that turn. Each printed exclusion is wired per clause (`nature.undead`, `nature.daemon`, `mechanic.psychology-immunity` for Deceive; `mechanic.psychology-immunity` alone for Hypnotize). Registry: `implemented-canonical-families.yaml` gained the four families, `verification/consumers.py` the four tag consumers and `kernel.py` lists the four mechanics as modular-only. Focused checks (real results): `tests/python/combat/modular/test_t13_psychology_leadership.py` 26 passed (12 prior + 14 new, including the two coordinator corrections below) — the exemption of all four recipients against the three kinds with each causer's own fact asserted, the real test and its sixes restriction against the non-exempt causers, the same band's Vampire/Necromancer/Skeletons/Black Hounds and another band's Skeletons as controls, the enchantment's own and borrowed Leadership drop with the Undead and Daemon controls, Deceive's bar and its end in the next phase plus the three exclusion controls and a strict tape proving no borrowed leader and no die for a barred enemy, and Hypnotize's +1 To Hit against the unmodified control phase, its mirrored orientation, the borrowed-leader pass against the own-value failure and the Psychology-immune exception, and the selection gate that accepts each power only on its printed Lahmia Vampire and refuses its band siblings and the other band's Lahmia Vampire; `tests/python/knowledge/test_binding_registry.py` + `tests/python/knowledge/test_editorial_schemas.py` 298 passed; `validate_knowledge_base()` 0 errors and `validate_execution_contract("mordheim")` `[]`; `tests/python/verification/test_structural.py` 7 passed / 1 failed, the failure being the two inherited `boundEquipment` projections (`night-goblins-mic/snotling-mob-consists-of-5-snotlings`, `khemri-cursed-of-karak-zorn/cannibal-dwarfs`) already recorded by M2/M3/M4 and unchanged here. The 7 assigned clauses were updated by `(origin_id, clause_id)` with executed evidence, no fingerprint or clause text changed; CSV SHA-256 (working tree) `87ac58b1…`; `build/audit/m0-reconciliation/validate_csv.py` PASS, 0 violations. **M4c corrections** (2026-10-09): (1) Enchanting Beauty applied its −1 Leadership without base contact and before the charge-phase Fear test; `leadership.resolve_local_leadership` now takes an explicit `contacting` fact and `psychology.test_fear` withholds it for the charging side's own charge test while supplying it for the charged side, which is in base contact (Undead/Daemon exemptions and own-or-borrowed values untouched); (2) the shared `LAHMIA_POWERS` loop discarded the fighter state returned on the success path, so a Leadership test that spent a persistent resource (a carried relic auto-passing the first required test) left `resources_spent` empty; the state is now stored on both paths, and the failure branch keeps setting `charm_attack_blocked` and, for Hypnotize, `condition.hypnotized`. **M4d (2026-10-09) — Devoted to the Vampire and The Bitten.** The two families this row still list as deferred are delivered in the modular engine inside the 1v1 duel boundary. *Devoted to the Vampire* (Beloved and Lackeys) binds `mechanic.devoted-to-the-vampire` and `mechanic.devoted-killer-hatred`: the caller supplies the Lahmian Vampire's condition (`devoted_vampire_down` / `devoted_vampire_killed`, projected by `compile_fighter` as `condition.devoted-vampire-down` / `condition.devoted-vampire-killed`, never inferred from a warband and refused on a profile that does not print the clause, or when both are supplied at once), `rounds.resolve_round` re-reads it every combat phase so the Frenzy lasts while she is down and ends exactly when she stands up — `FighterState.devoted_frenzy` keeps it distinct from every permanent or rolled Frenzy — and projects `condition.devoted-killer-hatred` only while the killer is still in action, consumed by the existing `contexts._hit_reroll` as the printed first-round Hatred. *The Bitten* binds `mechanic.bitten-transform`: the own-turn D6 (never on the opponent's turn, and never while Transformed and engaged) is stored in `FighterState` as `bitten_result` and `transformed`, with 1 = Madness — a Stupidity that lasts the turn that rolled it, plus reversion — 2-5 = act as normal and 6 = Transformed; the form survives the turn that rolled it, `equipment_for_state` casts off every weapon, off-hand, armour and helm while retaining a carried dagger and never recovers the discarded gear on reversion, and the pre-existing `rule.unarmed-without-penalties` marker the attack pool already consumes is projected only while the form lasts, so the transformed fist keeps its printed Strength without forcing a retained dagger out of the hand. Registry: `implemented-canonical-families.yaml` gained the three families (counts 270/1014 → 274/1021, `kinds.mechanic` 166 → 170); `verification/consumers.py` gained the three tag consumers; the two supplied facts entered `TRAIT_TYPES`, `runtime-scope.yaml`, the editorial schema and the Combat Lab editor's supplied-facts flags; and the three mechanics joined the optimized-port guard. Focused checks (real results): `tests/python/combat/modular/test_t13_devoted_and_bitten.py` 15 passed — Frenzy activation, its termination when the supplied fact is withdrawn and the undoubled negative control, the Hatred reroll on two first-round misses against a killer in action and its end with the killer, the 6/2-5/1 transform with persistence and the combat roll exception, the this-turn Madness (the next phase asks for no Leadership die and the bearer strikes normally), the two-wound unarmed discriminator with its untransformed control, the cast-off/reversion equipment witness, the retained dagger and the shield/skill split (a discarded shield's save and parry go, a skill's own parry stays); `tests/python/combat/modular/test_local_modifier_variants.py` 350 passed; `tests/python/verification/test_structural.py` 6 passed / 1 failed, the failure the two inherited `boundEquipment` projections (`night-goblins-mic/snotling-mob-consists-of-5-snotlings`, `khemri-cursed-of-karak-zorn/cannibal-dwarfs`) recorded since M2/M3/M4, with the tag-consumer registry closed by this delivery; `tests/python/knowledge/test_editorial_schemas.py` + `tests/python/knowledge/test_binding_registry.py` 298 passed once the two traits entered the profiles schema, and `validate_knowledge_base()` 0 errors with `validate_execution_contract("mordheim")` `[]`. **M4e (2026-10-09) — the existing Psychology and Leadership operators reached from their printed band rules.** 207 clauses / 201 origins were read one by one against their printed text and their real consumer; no new mechanic, trait, field, family, hireling grade or optimized port was added. 111 clauses (110 distinct rules in 50 band files) gained the declared canonical binding for their printed recipient — Fear and its immunity, the Undead composite, Stupidity, Frenzy, automatic and handler Leadership, the Leadership rerolls, Cold Blooded, qualified Hatred, Amazon Isolationists, Enchanting Beauty and the six/twelve/four-inch Leader radii — with every selectable warband skill left `selectable` and the schema-required `kind` added only where the runtime was new; 6 Khemri aggregate clauses were reconciled out of scope with their reason because the per-profile rules already bind `mechanic.undead`, and 10 Ghost Pirates clauses were marked covered by that same composite. 24 clauses (21 rules) had no source-faithful binding and were recorded as concrete pending items with their own reason rather than forced: randomized outcome tables (Fungus Brew, the Dwarven brew table, the Wild Lunatics D6, the conditional Mad-Caps state), control powers outside the 1v1 boundary (Seduction twice, Hypnotic Gaze, Hypnotic Dance), filtered recipients or exemptions the unconditional operator would over-grant (the Night Goblin Hate Stunties Fanatic exemption, the Dreamwalker Undead-foes and Grave Robber charged-by-Undead Fear exemptions, the Holy-Relic-gated Battle Pilgrim Frenzy, the slave broken-Spirit condition, the Devoted hound's twelve-inch Warrior Priest gate), provider contracts the six-inch Leader borrow cannot express (Inspiring Presence's twelve-inch borrow, the Adjutant relay, the three-inch Overseer scourge radius, the Songster group aura) and the aggregated Clockworker construct package. Focused checks (real results): `tests/python/combat/modular/test_t13_m4e_connections.py` + `tests/python/combat/modular/test_t13_psychology_leadership.py` 37 passed — each new binding is proved by its printed recipient plus an unselected or non-recipient control, with one real phase consequence per family (the Fear charge test, the fear-immunity waiver, the automatic-Leadership pass, the Frenzy activation) and the shared operators' own behaviour deliberately not re-tested; the two stale expectations the new source facts contradict were corrected in place, not weakened (a Cold One now causes Fear through its own printed animal trait, so the Elf-identity case asserts identity plus the animal's own grant, and the Trollheim Zombie prints Psychology immunity, so Deceive's Zombie control is excluded by that printed fact while Hypnotize's valid target is a non-immune enemy with the Wight and the Slayers as the immune controls); `tests/python/combat/modular/test_local_modifier_variants.py` 350 passed; `tests/python/verification/test_structural.py` + `tests/python/knowledge/test_editorial_schemas.py` 301 passed / 1 failed, the failure the two inherited `boundEquipment` projections; `tests/python/knowledge/test_binding_registry.py` 3 passed and `test_catalog.py::test_every_runtime_binding_resolves_to_a_known_shared_contract` PASS, so every new band binding resolves to a known shared contract; `validate_knowledge_base()` 0 errors, `validate_execution_contract("mordheim")` `[]` and `build/audit/m0-reconciliation/validate_csv.py` PASS with 0 violations. The 207 assigned clauses were updated by `(origin_id, clause_id)` with no fingerprint or clause text changed; CSV SHA-256 `166f1573…` (M4d) → `917db478…`. **M4f (2026-10-09) — the printed supplied-Leadership providers and their conditions.** The six origins were read one by one against their printed text and their recorded clarifications and delivered inside the 1v1 duel boundary by reusing `leadership.resolve_local_leadership` and the supplied facts it already reads: the Dreamer's Inspiring Presence widens the borrow to the printed twelve inches for a Morr Worshipper and is restricted to the printed recipient; the Adjutant relays a supplied leader's Leadership to a warrior within the printed six inches and never lends his own value; both Overseer copies lend to a slave at three inches, six while the supplied `scourge_armed` equipment fact holds; the Songster re-rolls a failed test with the printed +1 for a supplied friendly same-band Minstrel within six inches; the Hound re-rolls while the band's supplied Warrior Priest is within twelve inches, Knocked Down included and out of action excluded; the Eunuch passes automatically while the supplied Slave Merchant is not out of action. Five registry mechanics were added (`mechanic.relay-orders`, `mechanic.slave-driver`, `mechanic.songster`, `mechanic.devoted`, `mechanic.broken-spirit`) beside the `mechanic.leader-twelve` widening, each with its catalogue rows, `verification/consumers.py` consumer, optimized-port guard entry and registry family; no supplier abstraction was added because the existing supplied-fact contracts sufficed, and no progression, movement, rout procedure or third model was simulated. Real checks: `tests/python/combat/modular/test_t13_m4f_providers.py` 6 passed, and disabling the five new mechanics and the twelve-inch widening in a scratch copy of the consumer failed all six, so no case passes on an unmodified path; `tests/python/combat/modular/test_t13_m4e_connections.py` + `test_t13_psychology_leadership.py` 37 passed; `tests/python/knowledge/test_editorial_schemas.py` + `test_binding_registry.py` + `verification/test_structural.py` 304 passed / 1 failed, the inherited two `boundEquipment` projections; `tests/python/knowledge/test_catalog.py` 41 passed / 6 failed, all inherited (the same pair, the runtime-metadata count pin already stale at HEAD — the test counts 3022 against a recorded 2908 and this delivery adds no `runtime` block at all —, the Snorri supplied-result case and the access-scope expectation) and none naming a clause or mechanic of this delivery; `verify --structural` reports only those two projections; `build/audit/m0-reconciliation/validate_csv.py` PASS, 0 violations. The 7 delivered clauses were updated by `(origin_id, clause_id)` with executed evidence and no fingerprint or clause text changed; the three excluded remainders of those origins (the Songster group emission and Rout halves and the Eunuch leader restriction) keep their recorded out-of-scope state. | Current residuals are the 100 keys in the measurable-progress table above. Preserve the four reserved final-pass clauses. Participant admission is a projection gap, not proof of missing operators; Gaoler predicate equivalence and the qualified Beast Hunter witness remain explicit. Residual new behavior stays in dispatch 3, data/projection/connections in M1, isolated defects in the final accumulated pass. M4/T13/T14 remain open. |
| M5 — State and composite effects | Dispatched: control (6), charge gates and the Overseer Leadership borrow (9), hatred/vengeance/isolationism (20) and intrinsic trait/construct facts (37), then hireling admission for grades 1a/1b/1c/2a | Coordinator with three parallel workers, single writer per file | Delivered: three control mechanics end to end; Ghostly Howl closed end to end (2026-10-13); admission of every normalized grade including `core` is offered, with the measured partition 130 offered / 22 compiling with a legal printed kit / 12 with the kit unspecified / 82 refused by name for pending intrinsic clauses / 4 for an unmapped unique object / 4 needing a supplied input or a missing item record / 5 outside the duel runtime / 1 refused in an active slot — the earlier 32/24/52/12/5/5 partition is not reproducible in this tree (see the 2026-10-13 continuation note); unique objects reach the duel through their declared equivalence with identity and quantity conserved | Partially accepted | Focal evidence: `test_t13_control_family.py`, `test_t13_hatred_bindings.py`, `test_t13_trait_projection.py`, `test_t13_hireling_admission.py`, binding/editorial schemas. Open: `ghostly-howl`, construct drug immunity, the wider No-Pain wording, the slaver category operator, Ranald's resource composition, Beast Hunter's tagged witness, the unmapped unique objects and kit items named in round 3, and the remaining pending printed clauses. | Continue with the independent M5 families and the accumulated-corrections pass. |
| M1 — Residual connections and data | Not dispatched | Unassigned | Not dispatched | Pending | — | Integrate M2–M5; refresh the residual assignment and complete only remaining existing-operator connections/data. |
| M6 — Functional modular closure | Not dispatched | Coordinator | Not dispatched | Pending | — | Integrate M2–M5 and residual M1; reconcile product gaps and perform joint checks. |

Coordinator review (2026-10-08): the first M2 delivery is partially accepted. The Domnu unarmed Bear Hug, Frantic priority, Lost Innocence anti-spear/standing-up exception and reviewed recipient corrections have focused acceptance evidence: 16 representative modular/binding cases and 2 construction controls passed freshly. The remaining reusable operator evidence is retained from the delivery; no full suites were repeated. The CSV, rather than the handoff's 30/18 claim, now records 25 assigned clauses with `implementation_work: none` and 23 requiring work. Two completed priority connections were reconciled, including the Frantic identity succession and actual priority values. Great Claw's arm prohibition remains pending; its extra attack does not prove the restriction. Hireling admission/bindings, source-vs-contract questions and Magic Acorn remain open. These gaps block their own clauses, not the next independent family. Existing broader structural/catalogue failures are reported limitations, not passed checks. M2/T13/T14 remain open.

Non-blocking publication follow-up from this review: `generate_knowledge_web.py
--check` failed because `outputs/web-public/knowledge/knowledge-web.json` is
stale. Owner: canonical KB publication. Regenerate with the maintained generator
at the next KB publication/integration step, before claiming web recipient
parity or visible web acceptance, and require `--check` to pass. The focused
canonical Python recipient checks passed; this acceptance is bounded to the
modular/construction route and does not claim the published web projection is
current. No generated artifact was changed during the review.

Coordinator M3 review (2026-10-08): partial acceptance after 20 fresh focal modular/catalogue-binding tests passed and the frozen 49-clause assignment preserved its text and fingerprints. Three completed claims were returned to behavior work: Chosen of the White Tower must limit its skill reroll to the printed sword/buckler recipient; Bark Skin must preserve its Cutting Edge exception rather than cap all penetration at 6; Marks of Ranald must intercept hits before critical effects rather than use the ordinary post-critical ward stage. The isolated Bark Skin/AP1 and non-sword/non-buckler parry probes reproduced the first two boundary failures; Ranald's timing was confirmed by consumer inspection. Eight assigned clauses retain `implementation_work: none`; 41 remain pending, including these corrections and the previously recorded access/source/contract gaps. Only the independently reviewed completed portion is accepted; the affected families require correction before claiming complete behavior. The family registry count update is necessary bookkeeping and should not be reverted solely because historical optimized snapshots are stale. No full suites, parity or coverage were repeated; inherited failures are limitations, not passed checks. Resume the three M3 corrections together before dispatching dependent work. M3/T13/T14 stay open.

Coordinator M3/M4 review (2026-10-08): 37 fresh focal tests passed (28 defence cases and 9 psychology/Leadership cases); no broad suites were repeated. The three returned M3 contracts, including the separately completed Bark Skin fire negation, are accepted within their exercised boundaries; M3 now has 12 completed assigned clauses and 37 remaining. M4 is partially accepted: charge-only Fear waiver, tested directional Elf Fear, the supplied 12-inch radius and the basic 4-inch radius have focal evidence. Three Elf Fear origins retain data work for missing Wood Elf identity facts. Second in Command retains behavior work: a standing available same-band Witch Doctor supplied nearby does not suppress the Big Boss option (independent canonical probe requested and accepted the Big Boss with the Witch Doctor five inches away). M4 therefore has 9 completed assigned clauses and 4 still requiring work, rather than 13 complete. Qualified Hatred and other residual M4 families remain outside this small assignment and must not be described as blocked merely because their implementation/facts are absent. Resolve independent identity/filter families together in the next M4 batch; preserve real source and hireling-access limits. The whole blocks and T13/T14 remain open.

Non-blocking M3 composition follow-up: an isolated synthetic ethereal + Marks of Ranald pool requests the Ranald die after the hit was already saved by the ethereal defence; the scalar path stops at that save. Canonical admission of that combination was not demonstrated. The origin-level CSV records the strict witness, owner and completion criterion; resolve it at the next defence-composition integration before claiming support for the combination. The accepted basic Ranald contract and independent M4 work remain available.

Coordinator M4b review (2026-10-08): 17 fresh focal tests passed; no broad suites, parity or coverage were repeated. Second in Command, Hang the Bandit and Profound Hatred are accepted within their exercised modular contracts. Two canonical identity defects block their own families: the Arden Ivy Ferret is incorrectly feared as an Elf because its whole band carries the race-group tag; Hashut's Apprentice Sorcerer and Lothern's Mist Mage are missed by the exact caster-role-name whitelist, so Burn the Witch gives no reroll against them despite their printed wizard capability. The CSV retains data work for the three Elf Fear clauses and returns five Burn the Witch records (including the shared definition) to data work. Of the 12 M4b-amended records, four are completed and eight need these corrections; the earlier 13-record M4 assignment now has ten completed and three still requiring data work. Source text, keys and fingerprints are preserved. Resume the two identity corrections together with representative source-derived negatives; do not reopen accepted independent families or implement optimized ports. Previous M2/M3 partial acceptances and the non-blocking Ranald composition follow-up remain valid. M4/T13/T14 remain open.

Coordinator M4b identity-correction delivery (2026-10-08): the two returned identity defects are closed inside the modular engine only; no magic subsystem, hireling grade or optimized engine was added. The Elf species is the model's own fact (`elf_kind` → `species.elf` plus the printed-kind marker), so the three Fear of Elves recipients recognise the High, Dark and Wood Elf models — including the Karak Azgal hero printed as a bare "Elf" — while the Ivy Ferret and the Cold One animals are not Elves; the registry's `warband-group.wood-elf` stand-in was removed (25 groups). Caster capability is the profile's own `spellcaster` trait (a stable canonical fact in `TRAIT_TYPES`, the runtime-scope registry and the editorial schema) instead of a four-name role whitelist, and every admitted profile was read from its own printed declaration. Real checks: 12 focal tests in `tests/python/combat/modular/test_t13_psychology_leadership.py` and 7 in `tests/python/combat/modular/test_t13_enemy_identity_hatred.py` passed; `tests/python/combat/modular/test_local_modifier_variants.py` 350 passed (its refusal case now uses a genuinely unknown `elf_kind` instead of the newly valid `wood`); `tests/python/knowledge/test_campaign_loaders.py` and `tests/python/knowledge/test_editorial_schemas.py` passed with the 25-group pin and the trait/registry/schema agreement; `tests/python/combat/modular/` 849 passed / 5 failed, all five the inherited cases. The CSV keeps every earlier note, text and fingerprint and appends the closure to the three Elf Fear rows and the five Burn the Witch records, plus a cross-reference on the hireling copy (SHA-256 `1e50ae51…` → `eb2f1835…`); `validate_csv.py` PASS with 0 violations. The six failing `tests/python/knowledge/test_catalog.py` tests were re-confirmed as inherited by running the same file in a clean HEAD worktree: identical error strings, only the stale `classified` pin differing (3021 at HEAD, 3022 in the working tree), and the single extra rule (`order-of-the-mare-web/companion-filly--odd-covering`) belongs to another batch, so this correction adds no drift to that check.

Coordinator M4b2 acceptance (2026-10-08): the two returned identity corrections are accepted after 19 fresh focal cases passed (12 psychology/Leadership and 7 enemy-identity/Hatred cases). Manual source checks and the compiled route confirm the Elf model/woodland-spirit distinction and the caster/prayer distinction. The three Elf Fear and five Burn the Witch records now have no remaining implementation work and cite their actual mechanic IDs; historical text and fingerprints are unchanged. The original 13-clause M4 assignment and the eight-clause M4b addendum are complete within the reviewed modular scope. The additional hired-sword Witch Hunter record retains its separate F036 admission work. Other M4 families, earlier source/access gaps and T13/T14 remain open. No broad suites, parity or coverage were repeated; the inherited failures and Ranald composition follow-up remain recorded.

M4c delivery (2026-10-09) — Fear immunity by recipient and the Lahmia Leadership/attack effects. This is an implementer delivery, not acceptance. The four contracts above are complete end to end inside the modular engine and the 1v1 duel boundary: canonical facts (`vampire`, the new `undead_kind`), the band rule bindings, shared mechanics with their catalogue/family/registry rows, the modular consumers and 12 new focused cases (24 passing in the family file). Interpreted by hand from the printed text: the three exempted kinds are the causer's own facts and never "Undead" as a whole; Enchanting Beauty's exemption is Undead and Daemons only; Deceive prints "its own Leadership" and Hypnotize does not; Deceive's suppression protects the Lahmia Vampire while Hypnotize's bars the target and grants +1 To Hit against it. Recorded, not simulated: the printed remainder of Deceive ("may attack another model in base contact") and any third model, group, map, shot or spell. Seduction, Devoted, Bitten, new hireling grades and optimized ports were not touched. The remaining M4 families and the hireling-access blockers are unchanged; acceptance of the whole M4 block and of T13/T14 stays open.

M4c correction delivery (2026-10-09) — contact/timing and state persistence. Two coordinator findings on the M4c delivery are fixed in the modular engine only, on the three clauses they affect. (1) **Enchanting Beauty**: the −1 Leadership was applied even without base contact and before the charge-phase Fear test, so a Lahmia Vampire supplying Fear could make a charging enemy fail on a Leadership the source does not yet lower. Re-read from the printed wording ("any living enemy in base contact"), the consumer now requires an explicit `contacting` fact and `psychology.test_fear` passes it per test: `False` for a charging side's own charge test — a voluntary charge is resolved before the contact it has not yet made — and `True` for the side that was charged, which is already in contact. The Undead/Daemon exemptions, the own-or-borrowed value handling and every later Leadership test in contact are unchanged. (2) **Deceive and Hypnotize**: the shared `LAHMIA_POWERS` loop stored the state returned by the test only on failure, so a success that spent a persistent resource — a carried relic auto-passing the first required test — left `resources_spent` empty. The returned state is now stored on both paths, with the failure branch keeping `charm_attack_blocked` and Hypnotize's `condition.hypnotized`. Focused checks (real results): `tests/python/combat/modular/test_t13_psychology_leadership.py` 26 passed — the new discriminating pair uses one model and one 3+4 dice set: the charger passes on its own seven and lands the charge, while the contacting charged side tests on six and fails; one shared witness covers both powers, proving the relic's spend survives the first phase and that in the next phase the already-spent relic lets the doubled six fail on the owner's own seven, producing the suppression with the resource still consumed. `tests/python/combat/modular/test_local_modifier_variants.py` 350 passed (unchanged), confirming no regression in the shared Leadership/round path it exercises, including its own carried-relic contract. The three affected rows were amended by `(origin_id, clause_id)` with no fingerprint, clause text or earlier note altered; CSV SHA-256 `87ac58b1…`; `validate_csv.py` PASS, 0 violations. No other rule, family or optimized port was touched; coordinator acceptance remains pending.

Coordinator M4c review (2026-10-09): 24 fresh focal tests passed, but two independent boundary probes prevent full acceptance. Accustomed to Fear is accepted for all four assigned recipients. Enchanting Beauty is applied before contact: a supplied-Fear Lahmia build makes an LD7 charger fail on 3+4, and the helper also projects the condition into an explicitly disengaged state. Deceive and Hypnotize discard the state returned by a successful Leadership test; legally compiled Holy Relic round probes leave the consumed first-test resource unspent for both powers. Four of the seven assigned records remain complete, and three return to behavior work. Actual operator IDs and concrete consumer references have been reconciled in the CSV; printed text, fingerprints and prior evidence remain intact. Correct contact timing and persistence of successful returned states together, with representative strict lifetime cases; no new rule families or optimized ports are required. Prior M3/M4 acceptances remain valid. This review repeated no broad suites, parity or coverage; existing inherited failures and the Ranald follow-up remain open. M4/T13/T14 are not closed.

Coordinator M4c2 acceptance (2026-10-09): six fresh focal cases passed (20 deselected), including Beauty charging versus charged timing and persistent Holy Relic consumption across two phases for both Lahmia powers. The shared loop now stores returned state on success and failure; Fear callers pass the contact fact per test. These two corrections are accepted within those exercised boundaries. Deceive and Hypnotize return to no remaining work. Beauty retains an assessment for the final accumulated pass: other pre-contact Leadership callers, notably Stupidity before charge Fear, still default to contacting=True and need lifecycle validation; this is inspection-only, not a newly reproduced failure. No new state abstraction or additional review dispatch is required. Proceed with independent remaining rule families; the Ranald composition finding and inherited structural failures remain recorded. No full suites, parity or coverage repeated; M4/T13/T14 remain open.

M4d delivery (2026-10-09) — the Devoted to the Vampire triggers and the Bitten transformation table. This is an implementer delivery, not acceptance. Two of the seven origins in `build/audit/modular-dispatch/m4d-rows.jsonl` are complete end to end inside the modular engine and the 1v1 duel boundary, eleven clauses in total; the remaining origins (Favoured, the Lackeys equipment restriction, the two Lahmian copies already carried by their own batches) keep their own work. Interpreted by hand from the printed text: the Vampire's Knocked-Down and killed states are the caller's supplied facts and the Frenzy they cause is the one Frenzy that ends by itself (when she stands up, or when the killer leaves action); Hatred against the killer lasts exactly while that model is in action; Madness is Stupidity *for the turn that rolled it*; the form lasts until a printed 1 and a Transformed bearer in combat rolls nothing; the cast-off equipment is never recovered by the reversion and a retained dagger is never forced out of the hand. Recorded, not simulated: the movement compulsion (`must move toward her as quickly as possible and attacks anyone within 2" of the Vampire`) and the Sprint clause remain excluded scope, and no third model, group, map, campaign inventory or optimized port was added. Real checks: `tests/python/combat/modular/test_t13_devoted_and_bitten.py` 15 passed, `tests/python/combat/modular/test_local_modifier_variants.py` 350 passed, `tests/python/knowledge/test_editorial_schemas.py` + `test_binding_registry.py` 298 passed, `validate_knowledge_base()` 0 errors, `validate_execution_contract("mordheim")` `[]`, and `tests/python/verification/test_structural.py` with only the two inherited `boundEquipment` projections. The 11 assigned rows were updated by `(origin_id, clause_id)` with executed evidence, no fingerprint or clause text changed; CSV SHA-256 (working tree) `3b59fd47…` → `166f1573…`; `build/audit/m0-reconciliation/validate_csv.py` PASS, 0 violations. The `shield_and_skill_effects` aggregate gained its skill half (`CompiledFighter.skill_effects_only`), so the cast-off keeps a skill's own save or parry while the shield's goes with the shield. `tests/python/combat/modular/` 878 passed / 5 failed, all five the inherited cases (the two *Beauty of the Sea* catalogue-runtime ones, the Fimir duel roll-ordering and the two four-player-turn cases).

Coordinator M4d acceptance (2026-10-09): six fresh focal cases passed (nine deselected), covering Frenzy and killer lifetimes, transformed persistence, one-turn Madness, shield/skill separation and permanent equipment loss. The eleven assigned clauses retain their printed text, fingerprints and excluded movement/Sprint remainders. Accepted within the supplied individual facts and modular boundary. The shared stupidity_failed concern is an inspection-only composition assessment for the final accumulated pass, not proof that a separate field is necessary; refactor only if a discriminating witness demonstrates a defect. The implementer also ran the whole modular suite, beyond the requested focal budget; subsequent batches must avoid repeating that broad run. Existing structural failures remain limitations. Proceed with remaining independent families; M4/T13/T14 remain open.

M4e delivery (2026-10-09) — the existing Psychology and Leadership operators reached from their printed band rules. This is an implementer delivery, not acceptance. From `build/audit/modular-dispatch/M4e-input.csv` (207 clauses / 201 origins, SHA-256 `7b8158a2…`, frozen before editing and checked key-by-key against the register), each origin was read against its printed description and its real consumer; sharing a name or a binding was never treated as proof of equivalence, and the earlier approximate count was not used as authorisation for a block application. 111 clauses (110 rules in 50 band files) gained the declared canonical binding for their printed recipient, reusing the existing operators only: Fear and its immunity, the Undead composite, Stupidity, Frenzy, automatic and handler Leadership, the Leadership rerolls, Cold Blooded, qualified Hatred, Amazon Isolationists, Enchanting Beauty and the six/twelve/four-inch Leader radii. 6 Khemri aggregate clauses were reconciled out of scope because their per-profile rules already bind `mechanic.undead`, and 10 Ghost Pirates clauses were marked covered by that composite. 24 clauses (21 rules) had no source-faithful binding and were recorded as concrete pending items with their reason instead of being forced: randomized outcome tables, control powers outside the 1v1 boundary, filtered recipients or exemptions the unconditional operators would over-grant, provider contracts the six-inch Leader borrow cannot express, and the aggregated Clockworker construct package. No new mechanic, trait, field, family, hireling grade or optimized port was added; M4d was not reopened and Stupidity was not refactored. Interpreted by hand from the printed text: Fear is the model's own fact (a Cold One animal causes it, a woodland Spirit does not), the Trollheim Zombie prints Fear and Psychology immunity together, and Deceive's Undead and Daemon exceptions are distinct from the Psychology immunity that Hypnotize alone excludes. Recorded, not simulated: the printed remainder of the Lahmia powers, group auras, and any third model, map or campaign inventory. Real checks: `tests/python/combat/modular/test_t13_m4e_connections.py` + `tests/python/combat/modular/test_t13_psychology_leadership.py` 37 passed; `tests/python/combat/modular/test_local_modifier_variants.py` 350 passed; `tests/python/verification/test_structural.py` + `tests/python/knowledge/test_editorial_schemas.py` 301 passed / 1 failed, the inherited `boundEquipment` pair; `tests/python/knowledge/test_binding_registry.py` 3 passed with the shared-contract resolution check PASS; `validate_knowledge_base()` 0 errors; `validate_execution_contract("mordheim")` `[]`; `build/audit/m0-reconciliation/validate_csv.py` PASS with 0 violations. The two test expectations the new source facts contradict were corrected in place with source-derived assertions, never weakened or suppressed. The 207 assigned rows were updated by `(origin_id, clause_id)` preserving every earlier note and fingerprint; CSV SHA-256 `166f1573…` → `917db478…`. M4/T13/T14 remain open; coordinator acceptance is pending.

Coordinator M4e acceptance (2026-10-09): the 207-clause/201-origin input matches the maintained register with no printed-text or fingerprint drift and the earlier coordinator notes preserved. Actual final states: 122 clauses with no remaining work, 68 connection, 14 data and 3 behavior (85 pending); the whole assignment is not closed. Four fresh representative cases passed for Fear execution, immunity, selectable recipient gating and automatic Leadership. Completed connections are accepted within that bounded existing-operator evidence; unchanged operators were not recertified. The next independent assignment groups supplied Leadership providers, conditional borrowing and rerolls; a group-addressed producer alone does not exclude an admitted individual consequence. Existing defects/assessments and inherited structural failures remain for the final accumulated pass. No full suite, parity or coverage repeated; M4/T13/T14 remain open.

M4f delivery (2026-10-09) — the printed supplied-Leadership providers and their conditions. This is an implementer delivery, not acceptance. The six origins named by the coordinator (Dreamwalkers Inspiring Presence, House Guard Adjutant Relay Orders, both Slave Driver copies, Sea Ghosts Minstrels Songster, Protectorate Hound Devoted and Slavers Eunuch Broken Spirit) were located and read by hand, ten clauses in total, and each origin was interpreted individually for recipient, provider, radius, condition, borrowed value, bonus, repetition and duration; the earlier semantic classification was never used as authorisation to treat a shared name as an equivalence. Seven in-scope clauses are complete end to end: each rule binds its own registered mechanic and `leadership.resolve_local_leadership` supplies the printed consequence from the caller's supplied facts — the twelve-inch widened borrow restricted to the printed Dreamer skill recipient, the two-hop Adjutant relay that never lends the Adjutant's own value, the three-inch (six with a scourge) Overseer borrow in both warbands, the Songster re-roll with the printed +1 for a supplied friendly same-band Minstrel, the Hound re-roll within twelve inches of the supplied Warrior Priest, and the Eunuch's automatic pass while the supplied Slave Merchant is not out of action. A group-addressed producer was not treated as a reason for exclusion: the Songster's aura admits the individual re-roll consequence without simulating the aura or any third combatant. No new supplier abstraction, hireling grade, trait, field or optimized port was introduced; the existing supplied-fact contracts sufficed, and no progression, movement, rout procedure or other excluded subsystem was automated. Recorded, not simulated: the Songster group emission and Rout halves, the Eunuch's warband-leader bar, and every printed remainder outside the duel. Real checks: `tests/python/combat/modular/test_t13_m4f_providers.py` 6 passed with source-derived expectations (inside and outside each printed radius, a valid and an invalid provider — foreign band, opposing side, Knocked Down and out of action —, the equipment and state conditions, and a real consequence of the lending, the re-roll and the automatic pass; the Songster cases pin that the clause qualifies the recipient rather than the Minstrel, so a recipient forbidden to borrow a leader's value and a Knocked Down Minstrel both still receive the printed re-roll); a scratch mutation disabling the five new mechanics and the twelve-inch widening failed all six, proving every case exercises the delivered contract; `tests/python/combat/modular/test_t13_m4e_connections.py` + `test_t13_psychology_leadership.py` 37 passed; `tests/python/knowledge/test_editorial_schemas.py` + `test_binding_registry.py` + `tests/python/verification/test_structural.py` 304 passed / 1 failed, the inherited two `boundEquipment` projections (`night-goblins-mic/snotling-mob-consists-of-5-snotlings`, `khemri-cursed-of-karak-zorn/cannibal-dwarfs`) unchanged and reported twice by `verify --structural`; `tests/python/knowledge/test_catalog.py` 41 passed / 6 failed, all inherited and none naming a clause or mechanic of this delivery; `build/audit/m0-reconciliation/validate_csv.py` PASS with 0 violations. The 7 delivered rows were updated by `(origin_id, clause_id)` with executed evidence, the delivered mechanic as their `effect_id`, and the new test in their `evidence_refs`, preserving every earlier note and fingerprint (a shell diff shows exactly the fourteen physical lines of those seven records changing and nothing else); the three out-of-scope remainders keep their state. Recorded for the final pass as isolated, and not refactored here: the same printed Songster clause is also carried by the two hireling Bard copies (`hireling.hired-sword.bard`, `hireling.dramatis.william-schakestange-master-bard`), which keep their recorded `connection` state because their origins sit outside this assignment and only grade-2b hirelings are promoted; and the shared Deceive `own_value_only` path still skips the whole borrow block, which this delivery inspected, kept unchanged and gave the source-faithful Songster handling outside it. CSV SHA-256 (working tree, `sha256sum`) `9cead766…` → `4836c518…`. M4/T13/T14 remain open; coordinator acceptance is pending.

Coordinator M4f review (2026-10-09): six fresh focal tests passed. Corrected delivery count: seven assigned rule origins, seven admitted clauses and three excluded remainders; the handoff count of six origins is inaccurate. Five admitted clauses are accepted within the exercised provider/radius evidence. Both Slave Driver copies retain behavior work: the shared borrowing loop checks same band but not slave identity; a canonical Skryre Verminkin within three inches of its Overseer unexpectedly requests probe.leader.overseer. Record this recipient over-grant for the final accumulated correction pass, with canonical slave positives and non-slave negatives in both bands. It does not block independent new state families. No new abstraction, conformance tool or full suite is required. Earlier assessments, hireling admission gaps and inherited structural failures remain recorded; M4/T13/T14 remain open.

M4g delivery (2026-10-09) — the Fungus Brew consumable states, the Mad Cap Masters composition and the Wild Lunatics own-turn die. This is an implementer delivery, not acceptance. The assigned origins were located by clause and read by hand against their printed text (the Night Goblins Web Fungus Brew and Mad Cap Masters rules, the Lustria Pygmies Wild Lunatics rule with its printed Immunity to Psychology, and the Mad Cap and Head-Splitter Mushroom items), and each clause was interpreted individually for recipient, table, duration, accumulation and exception; the earlier semantic classification was never used as authorisation to treat a shared name as an equivalence, and the recorded assessment that the printed producer belongs to the caller was honoured rather than automated. Delivered individually: the brew's printed producer stays recorded, not simulated (pre-battle brewing, the 1–3 mushrooms, the one henchman-group nomination, the per-mushroom chart rolls and the ruined batch), while the caller supplies the affected duelist and the results its own batch printed, one canonical condition per printed result — `condition.fungus-brew-rowdy` (a new supplied state whose `mechanic.fungus-rowdy` widens the existing own-turn animosity band from 1 to 1–2 through the shared consumer), `-dizzy` (the trait `fungus_brew_dizzy`, projected by `compile_fighter` as its printed −1 Initiative), `-fearless` (the canonical Fear immunity), `-numbed` (+1 armour save with the printed 6+ floor), `-belligerent` (the canonical first-round Hatred) and `-loony` (Frenzy followed by Stupidity, tested against the Mad Cap Masters clause that grants exactly that composition and keeps no state of its own, its rule remaining recorded out of scope); the Wild Lunatics rule's own printed effect, an own-turn D6 resolved by `rounds.resolve_round` on the bearer's turn alone, 1–3 granting the lasting Frenzy and 4–6 the lasting Stupidity on `FighterState` (`mechanic.lunatics`, two distinct output tags), with the Stupidity resuming once the printed reaction that clears Frenzy removes it and with the profile's own printed Immunity to Psychology not cancelling the grant its own profile prints; and the Mad Cap Mushrooms' printed exclusion in `compiler.py`, which voids only that item's own Frenzy contribution for an Undead or Possessed bearer while any other printed source of Frenzy still stands and while the Head-Splitter Mushrooms, which print no exclusion, are not narrowed. Interpreted by hand from the printed text where a keyword reading would have been wrong: the Numbed clause prints a floor but not the preservation against armour-ignoring attacks that the Untiring clause states in its own words, so the shared contract was separated into `armour_save_floor` and `armour_cannot_be_ignored` (`phases.armour_target` and its vectorised and native ports) with Untiring's accepted behaviour unchanged because it sets both; the printed exclusion sentence belongs to the Mad Cap item alone and was not applied to the shared mushroom name; and the Wild Lunatics grant is not suppressed by the same profile's printed Psychology immunity. Recorded, not simulated: the brew's producer and the group nomination, the ruined batch, group animosity between models, every movement consequence, the All Alone half of the Fearless result, and both mushrooms' purchase, availability and price. Registry and catalogue work needed by the delivered behaviour: `catalog/rules/conditions.yaml` gained the supplied `condition.fungus-brew-rowdy` (the block's six printed results are now all registered), `catalog/mechanics/execution.yaml` and `close-combat.yaml` the `mechanic.fungus-rowdy` rows, `implemented-canonical-families.yaml` the `mechanic.lunatics` and `mechanic.fungus-rowdy` families with re-counted totals (families 284, rules 1035, `kinds.mechanic` 180 — the previous declared 280/1029 was already stale against the counted 283/1034), `verification/consumers.py` the two tag consumers, `kernel.py` the two modular-only tags, `TRAIT_TYPES` and the profiles editorial schema the `fungus_brew_dizzy` trait the schema was missing, and `compiler.py` the printed exclusion and the brew projections. Real checks: `tests/python/combat/modular/test_t13_lunatics_and_mushrooms.py` 12 passed — recipient with a negative control, own-turn versus opponent-turn, outcome and persistence discriminators for both grant halves, the reaction that clears Frenzy and the resumed Stupidity from both the profile rule and the supplied Loony composition, the six-result projection with each result's real phase consequence, the Numbed floor against ordinary arithmetic and against an armour-ignoring attack, the widened animosity band against the unmodified squabble, and the mushrooms' printed exclusion with the Head-Splitter and extra-Frenzy controls; `tests/python/knowledge/test_editorial_schemas.py` 295 passed after the schema gap was closed; `tests/python/combat/modular/test_local_modifier_variants.py` + `test_t13_psychology_leadership.py` + `test_t13_m4e_connections.py` 387 passed; `tests/python/combat/` (phases, modular interactions, source corrections, vectorized) shows only the inherited failures and none naming a clause or mechanic of this delivery; `validate_knowledge_base()` 0 errors; `validate_execution_contract("mordheim")` `[]`; `build/audit/m0-reconciliation/validate_csv.py` PASS with 0 violations. The affected rows were updated by `(origin_id, clause_id)` preserving every earlier note and fingerprint; CSV SHA-256 `4836c518…` → `20989214…`. Table updated from the same closed keys: 9 of those rows were in the frozen 130-key pending set (2 assessments, 1 data, 6 connections), so nothing was added to or removed from the denominator in this step. Inherited failures observed here, not caused and left unchanged: the two `test_source_corrections` four-player-turn cases, the stale pinned counts in `test_rule_families_b.py` and `test_shared_families.py`, the ogre `skill.mighty-blow` construction case, and the two `boundEquipment` projections. Recorded for the final accumulated pass as isolated, each with its closing criterion: the `mad_cap_mushrooms` row in `catalog/items/combat-equipment.yaml` still carries `mechanic_id: preparation.head-splitter-mushrooms`, so both mushrooms share one equipment record (close by giving the Head-Splitter Mushrooms their own printed item row); and the newly bound Fear and Psychology-immunity profile rules make scenarios such as `sigmarite-vs-undead` modular-only while the optimized-port guard still lists those mechanics, so the native/vectorized deep scenario cannot compile (close by certifying those tags or recording the scenario as modular-only). M4/T13/T14 remain open; coordinator acceptance is pending.

M4h delivery (2026-10-09) — the band connection clauses that print no qualification. This is an implementer delivery, not acceptance. Eighteen clauses over seventeen origins were frozen in `build/audit/modular-dispatch/M4h-input.csv` (SHA-256 `841283349dab…`, built by `build_m4h_input.py` from the closed 793-key set by explicit key, never by keyword) and each was read against its own printed `effect:` text before anything was bound. Five are delivered: the printed "Immune to Poison" of the five Ghost Pirates undead rules (Ghost Captain, Screaming Ghosts, Skeleton Mates, Gibbets, the Bloated). Each of those rules already carries its own printed recipient in `applies_to.profile_ids`, prints no exception, and already held the canonical Fear binding, so the remaining immunity was a genuine missing connection: the rule now binds `trait.poison-immune` with `parameters.value: true`, and the rule-level `implemented: 'YES'` that `selection._profile_rule_traits` requires is what makes it reachable. The printed Immune to Psychology clause of those same rules stays recorded as covered by the `mechanic.undead` composite (M4e) and is deliberately not bound here; `mechanic.undead` would additionally grant `skill.ignore-pain`, which these rules do not print, so the composite was rejected as an over-grant. The other thirteen clauses are **not** plain missing connections and were held with a concrete reason each rather than forced: the clockworkers construct immunity lives on a band-wide rule while only the constructs print it (a recipient-narrowed route is owed, and the two profile aliases must not add a second contribution); the dwarf-guildsmen Fear immunity and Frenzy follow supplied Troll Brew results; the watchmen auto-pass belongs to the Knights of Purity a hero becomes after 30 experience; the Battle Pilgrim Frenzy is granted by owning a Holy Relic; the dreamwalkers and grave-robbers Fear immunities are qualified by their enemy or by the charging Undead; the dark-elf-corsairs Frenzy sentence sits inside a compound rule applying to four profiles while only the Witch Elf prints the drugs; and the three night-goblin Hatred rules are band-wide with printed recipients and Fanatic exemptions. Recorded, not simulated: groups, purchases, promotions, item ownership and campaign progression. Real checks: `tests/python/combat/modular/test_t13_m4h_connections.py` 3 passed — all five recipients reach `poison_immunity` and the `poison_immune` tag, the band's two living profiles stay without either, and a poisoned main weapon loses its poison tag against a recipient while keeping it against the living control; a scratch mutation setting the five `value: true` bindings to `false` failed the two discriminating cases and left the negative control passing, proving the cases exercise the delivered contract; `validate_knowledge_base()` 0 errors; `validate_execution_contract("mordheim")` `[]`; `tests/python/knowledge/test_editorial_schemas.py` + `test_binding_registry.py` + `test_yaml_formatting.py` 303 passed / 1 failed, the inherited whole-tree formatting count, and the two files this delivery touched are flagged only by pre-existing long `reason:` lines that the `HEAD` revision already flags (checked file by file, and the `--write` diff names none of the new lines); `tests/python/verification/test_structural.py` the inherited pair of `boundEquipment` projections; `tests/python/combat/modular/test_catalogue_runtime.py` the inherited `sea-singer--beauty-of-the-sea` case, whose binding exists unchanged in `HEAD`; `build/audit/m0-reconciliation/validate_csv.py` PASS with 0 violations. The eighteen assigned rows were updated by `(origin_id, clause_id)` through `apply_m4h_csv_updates.py`, preserving every earlier note and fingerprint; CSV SHA-256 `20989214…` → `a4dccbd7…`. Table updated from the same closed keys: the five delivered rows were all inside the frozen 130-key pending set, so five clauses moved to no-remaining-work and nothing was added to or removed from the denominator beyond the M4g and M4h decrements. M4/T13/T14 remain open; coordinator acceptance is pending.

Coordinator M4g/M4h review (2026-10-09): five fresh focal cases passed for Lunatics Stupidity, Loony expiry, Rowdy animosity, Numbed arithmetic and Ghost Pirate poison removal. Completed supplied-state consequences and poison connections are accepted within this boundary. Wild Lunatics battle-long accumulation remains a final-pass interpretation assessment because the printed each-turn rule does not expressly define that duration. Counts from the original 793 keys: 676 no remaining work, 117 pending (83 hireling / 34 other); 113 remain in the final M4 implementation dispatch and four review clauses in the accumulated pass. Historical text/fingerprints unchanged. No broad suites or ports repeated; M4/T13/T14 remain open.

When a block contains several deliveries, list accepted family IDs and the
remaining dispatched/blocked IDs in its cells; mark partial acceptance until
the complete required set is covered. Origin-level detail stays in the semantic
CSV. Record a real revision and existing case references, not guessed
percentages. Do not close a block while a required source gap or failed required
check remains. An unrelated blocked family need not delay independent work.

### M5 round 1 (2026-10-09, coordinator with three parallel workers)

Scope of the round: four coherent families cut from the maintained register by the contract
string each clause already records — control of an enemy's attacks (6), charge gates and the
Overseer Leadership borrow (9), hatred/vengeance/isolationism (20) and intrinsic trait/construct
facts (37). Ownership was single-writer per file: `rounds.py` plus the mechanics registries and four
band files; the hatred band/catalogue records; `traits.yaml`, `compiler.py` and the clockwork band.
Workers could not run commands; the coordinator verified every delivery.

Delivered end to end: `mechanic.hypnotic-gaze`, `mechanic.lahmia-seduction` and
`mechanic.lahmian-seduction` (registered in both mechanics registries, executed in
`rounds.resolve_round`, members recorded in `implemented-canonical-families.yaml`, and added to the
optimized-backend refusal set so no port silently omits them); Hypnotic Dance delivered by reuse of
the registered `mechanic.mesmerising-dance`; the construct poison/Stunned conversions bound on the
clockwork records; Sigmund Spindle's missing poison runtime block; the Gaoler's warband-level
Chaotic binding corrected away from its printed per-model identity; the two `band--free-the-slaves`
records re-scoped with a precise reason.

Recorded pending with an exact cause: `ghostly-howl` (random Fear-test-scoped penalty needs a hook in
`psychology.resolve_fear`/`leadership.resolve_local_leadership`); construct drug immunity (no
drug-immunity operator is registered); the wider "ignores Knocked Down" wording; the Pit Fighter
"slaver" hatred category (no operator selects it); Hobgoblin Traitor (opponent-imposed Hatred);
Fighting Undead (source text not carried); Max's printed warband list; and the campaign-side
vengeful-hatred route.

Top dependency found, not a global blocker: `combat_packages` admits only grade-2b hirelings as duel
participants, so every grade-1a/1b/1c/2a fact — including the 20 admitted trait facts and the exact
hatred bindings witnessed in `test_t13_hatred_bindings.py` — cannot reach the modular consumer yet.
That admission gate is the highest-value single fix still open.

Focal evidence, re-run after the last edit: `test_t13_control_family.py`,
`test_t13_hatred_bindings.py`, `test_t13_trait_projection.py`,
`test_binding_registry.py`, `test_editorial_schemas.py` and `test_t13_psychology_leadership.py`
together **342 passed**. The register keeps its 4,556 clauses / 3,594 origins with every prior note,
text and fingerprint conserved. Inherited, untouched by this round: the conditions-catalogue
mismatch, the `khemri-cursed-of-karak-zorn` compile failure, the frozen
`classified == 2908` count (now 3022) and the translation gates; the YAML-formatting gate also
reports files outside this round and the formatter aborts on `norse-explorers-btb`.

### M5 round 2 (2026-10-09, coordinator with three parallel workers)

Hireling admission: `combat_packages` now offers every normalized hireling grade instead of only
2B, so the printed clauses that were prepared earlier can reach the modular consumer. Admission is
not a grant — `selection._profile` still refuses a profile whose intrinsic clause is pending,
missing or unbound, and the refusal names the clause. Measured through the real route
(`combat_packages` → `compile_fighter` → modular consumer): 119 profiles offered, 19 compiling with
no equipment selection, 34 with a legal printed kit, 52 refused by name for pending intrinsic
clauses, 5 outside the duel runtime. The `core` grade stays unoffered because its equipment records
raise in the eligibility layer instead of refusing; that needs its own review.

Per-rule dispositions were made manually in the grade files by three workers under single-writer
ownership: existing-operator bindings where the printed contract matched (for example Bone Goliath's
Stunned-as-Knocked-Down to `skill.ignore-pain`, the countess and Bone Goliath poison to
`trait.poison-immune`), explicit `unimplemented` children where no operator exists, and `scope: 'NO'`
with a named reason for the printed content the 1v1 duel does not admit (campaign actions, upkeep,
hiring restrictions, shooting, casting, mounts, groups). No profile was unblocked by calling a duel
consequence out of scope, and no new operator was invented by a worker.

Known gaps kept open: the wider "ignores Knocked Down" wording; a unique-equipment record without a
canonical combat mapping (Grave Robber, Gravesman); the unoffered `core` grade; and no admitted
bearer of the prepared `fear-causing`/`undead` trait facts yet, pinned by
`test_t13_hireling_admission.py` so the state cannot drift silently.

### M5 round 3 (2026-10-10, coordinator)

Unique equipment and the `core` grade. Legality stayed in the shared module
(`packages/typescript/domain/eligibility/index.ts`) and its bundle was regenerated with
`node tools/web/build-eligibility.mjs` (`check:eligibility` reports it current). A printed unique
object reaches the duel only through the equivalence its own record declares: the kit side and the
active slot now resolve item → mechanic through that equivalence alike, a declared quantity expands
the object's own copies (Johann's Long Daggers are a pair), and an object whose own rules are declared
out of the duel is still refused in an active combat position. A profile the source prints with no
equipment at all keeps the engine's free default instead of being refused for a kit it never had, and
such a profile offers no empty equipment list, so its natural attacks are the compiled weapon.
`combat_packages` offers the declared canonical base id beside the profile-local object id, which is
what lets the printed weapon be selected at all. The `core` grade incompatibility was a printed
"choose N from this list" kit shape, now resolved in the shared module; the grade is offered like the
others and a complete profile compiles (`ogre-bodyguard`).

Measured admission through the real route (`build/audit/m5-coord/measure_admission.py`, one decisive
attempt per profile, categories exclusive so they partition the offered set): **130 profiles offered
— 52 refused for a pending intrinsic clause, 32 compiling with a legal printed kit, 24 compiling with
the kit unspecified, 12 refused because a unique object has no canonical mapping, 5 outside the duel
runtime, 3 needing a supplied profile input or a missing item mapping, 2 whose printed kit item has no
canonical item record.** Fear-causing/`undead` carriers now admitted and reaching the consumer:
`grave-robber` (undead + fear), `chaos-fury` (fear), `ogre-bodyguard` (core, fear). The prepared
trait-fact register rows for those three are closed with this evidence; the carriers that remain out
(`bone-goliath`, `chaos-centaur`, `dark-mage`, `emissary-of-chaos`, `ogre-slave-master`, `gravesman`)
record their own concrete reason. Concrete blockers kept open: the Gravesman's pry bar and the other
unmapped unique objects (`aenur`, `dark-emissary`, `innominatus`, `truthsayer`, `thief`,
`ninja-gnoblar`, `imperial-tactician`), `fire-eater`'s fire stick, `grave-warden`'s wheelbarrow and
`old-prospector`'s hyphenated `two-handed-weapon` equivalence, all named rather than invented, plus
`snorri-nosebiter`'s and `sister-of-sigmar`'s supplied profile inputs.

The register kept its keys, clause texts and fingerprints: 38 hireling-origin rows were updated
(13 closed as `none`, 25 held with the measured reason) by `build/audit/m5-coord/apply_round3_csv.py`
and `validate_csv.py` reports PASS with 0 violations; admitted pending is now 766 keys. Focal checks:
`test_t13_hireling_admission.py` 13 passed (kit equivalence, an excluded object refused in an active
slot, an unmapped unique weapon refused by name, the printed quantity in the legal kit, and a real
round consequence — an enemy charging an admitted carrier spends the Fear die and fails the charge).

### M5 round 4 (2026-10-10, coordinator)

Kits and the supplied-profile configuration. The shared-module fallback a profile
printed with no kit keeps was tightened: it admits only the engine's own default
weapon and the authorized natural attack, refusing an active slot, non-neutral
material or supplied ownership the source never printed (`no canonical basis`
named instead of an accepted silence). A printed unique object's declared
equivalence may no longer silently drop a combat property the object's own record
adds: the Rolling Pin counts as a club yet prints +1 Strength, so either one of the
object's own duel-reaching rules delivers the property or the equivalence is
refused by name. The bundle was regenerated (`check:eligibility` current) and the
`HirelingUniqueItem` interface now carries the printed standalone properties.

Measured admission through the same route: **130 offered — 52 refused for a
pending intrinsic clause, 36 compiling with a legal printed kit, 28 compiling
bare, 5 outside the duel runtime, 4 refused because a unique object has no
canonical mapping, 3 needing a supplied profile input (Snorri's drinking result,
the hired Sister's two special skills, the Grave Warden's un-mapped wheelbarrow),
2 refused in an active slot (Fire-Eater, Dark Emissary).** New in this round:
`snorri-nosebiter` compiles with the supplied 2-6 drinking row (result 5 prints
+1 S, result 6 grants the Frenzy Slayer exception) and result 1 is refused;
`sister-of-sigmar` compiles once exactly two distinct Sisters special skills are
selected; `old-prospector` and `gravesman` compile through their declared
two-handed-weapon / halberd equivalences; `aenur`, `innominatus`,
`imperial-tactician` and `ninja-gnoblar` stay out 4 × by name because no canonical
combat mapping exists for their unique objects.

The register kept its keys, clause texts and fingerprints: 38 hireling-origin rows
were updated (17 closed as `none`, 21 held with the measured reason) by
`build/audit/m5-coord/apply_round4_csv.py`; `validate_csv.py` reports PASS with 0
violations and admitted pending is now 763 keys. Focal checks: `test_t13_hireling_admission.py`
19 passed — the equivalence and its negative control, an unmapped unique weapon
refused by name, a printed quantity in the legal kit, the supplied configuration
compilations, the drinking-table refusal, and **one representative round case:
`initialize_duel` → `resolve_round`, where an enemy charging an admitted fear
carrier spends the Fear die and the charge fails**, alongside the kept focused
`resolve_fear` cases. `test_yaml_formatting.py` passed; shared TS checks
(`shared-construction-context`, `construction-validation-transport`,
`t13-shared-eligibility-reconciliation`) 45 passed; `packages/typescript` typecheck
clean.

### Five cross-copied equipment origins (2026-10-14, coordinator)

The twenty clauses of `item/bone_helmet`, `item/bone_helmet_skink_priest_only`,
`item/eshin_assassin_clothes`, `item/mage_robes` and `item/wizard_robe` now have an
individual disposition. Both Bone Helmet rows keep the ordinary Helmet defence
(`defence.helmet`, a 4+ Stunned-to-Knocked-Down conversion) with no invented
bone-specific property: the empty local paragraph is an extraction observation,
not an executable blocker, and the Skink-Priest entry keeps its `Skink Priest
only` note as a construction constraint. The three robe/clothes items' own
clauses stay blocked and `unresolved`: the Eshin Assassin Clothes need the
chaos-in-the-streets p161 paragraph, the Mage Robes the khemri p59 one and the
Wizard Robe the chaos-in-the-streets p167 one, since an existing
`armour.eshin-assassin-robes` / `armour.wizard-s-robe` connection is not proof of
equivalence, and no consumer route is certified. The ten cross-copied sibling
clauses that name another object's recipient (helmet, assassin-robes and
wizard-robe copies) were dismissed as provenance errors rather than blocks.

Applied by `build/audit/m0-reconciliation/apply_t13_five_origins_20261014.py`
through the reviewed `integrate_explicit_csv.py`: the complete register was
reloaded immediately before writing and the concurrent-change guard held. All
4,556 keys, 3,594 origins, clause texts, fingerprints and prior notes are
conserved and exactly those 20 rows changed; the unchanged `validate_csv.py`
reports PASS with 0 violations. Interpretation and register only: no code, YAML,
mapping, grant or engine suite was touched, and the joint modular/construction
closure check remains reserved.

Primary-source search for the three wardrobe objects (2026-10-14): the cited
paragraphs — Eshin Assassin Clothes (chaos-in-the-streets printed 161,
Deathbringer Assassin Equipment List), Mage Robes (khemri printed 59, Mage
Equipment List) and Wizard Robe (chaos-in-the-streets printed 167, Arcane
Society Equipment List) — were not recovered. No copy is in the repository or
the local caches; the Chaos in the Streets publication has no mordheimer.net
page and is not obtainable as a readable document, and exact-phrase searches for
the three item names return no source at all. For Mage Robes the accessible
transcriptions of the same warband's Mage Equipment list (the archived original
Khemri supplement page and Broheim's 2015 re-edition) print only Familiar,
Dagger, Staff, Sword, Pistol, Duelling pistol and Sling, a slimmer revision than
the cited one, and mordheimer.net's Khemri pages carry only the Tomb Guardians
and Arabian Tomb Raiders. No equivalence is therefore proven or contradicted and
no disposition changed: the six own clauses keep `source_blocked`, `unresolved`
and no consumer, while the verified source state and the references actually
read were appended to their notes by
`build/audit/m0-reconciliation/apply_t13_source_search_20261014.py`. Exactly
those six rows changed (notes and `evidence_refs`); all 4,556 keys, texts,
fingerprints and prior notes are conserved and the unchanged `validate_csv.py`
reports PASS with 0 violations. Sources were read, nothing was executed.

Visual review of the same three objects (2026-10-14): the cited paragraphs exist and
were read as rendered pages from the two manuals' own copies, both of which lack a
usable text layer. `Caos en las Calles` (the manual registered as
chaos-in-the-streets; 300 pages, printed page = PDF page, its contents page matching
the registered band ranges) prints the Eshin Assassin Clothes at printed 159 with
its list line at printed 161 (15 gc, Silent-Hunter-only, 6+ Light Armour save, no
combination except a helmet) and adds an `Assassin's Luck` re-roll of failed saves
that `armour.eshin-assassin-robes` does not carry, so its clause becomes
`parameterized_variant` rather than an exact equivalence. `Khemri - La Tierra de
los Muertos` (148 pages, printed page = PDF page, text layer only on printed 1-75)
prints the Mage Robes in the Mage Equipment List at printed 59 and its full entry at
printed 61 (Raro 6, 10 gc, 6+ save, no combination with any other armour, no
spellcasting penalty), and `Caos en las Calles` prints the Wizard Robe the same way
at printed 167 and printed 68 in the rules chapter, corroborating the entry's
"el almacen de Yohan" footnote. Both printed texts forbid combining the robe with any
other armour while the canonical `armour.wizard-s-robe` allows a helmet, and the
same manual does print the helmet exception for the neighbouring Eshin robes, so the
case is flagged `needs_clarification` for the artefact owner instead of being
resolved here. The three coverage clauses become `independent` + `reviewed` (their
rule is carried by the sibling clause) and the six rows were written by
`build/audit/m0-reconciliation/apply_t13_visual_review_20261014.py` through the same
reviewed helper: exactly those six rows changed, evidence stays `inspection`, no
consumer route is certified, all 4,556 keys, texts, fingerprints and prior notes are
conserved and `validate_csv.py` reports PASS with 0 violations. No code, YAML, test,
grant or new report was touched and no engine suite was run.

Wardrobe variants implemented (2026-10-14): the three recovered entries now carry their
printed clauses end to end. Each binds its own origin mechanic — `mage_robes` ->
`armour.mage-robes` (khemri printed 61/59) and `wizard_robe` -> `armour.wizard-robe`
(chaos-in-the-streets printed 68/167) state the 6+ save with their own no-other-armour
limit, while `eshin_assassin_clothes` keeps `armour.eshin-assassin-robes` (printed
159/161) and its mechanic now prints the Assassin's Luck rider: failed save rolls of the
wearer are re-rolled. Both tunics refuse a helmet as well, because the paragraph excepts
none and the same manuals list the Casco under Armaduras; the generic
`armour.wizard-s-robe` keeps the helmet exception of its own source and no bearer of it
is re-judged. The limit passes through the shared eligibility (`loadoutRestriction`, one
place, no interface copy) and the re-roll is wired at the armour save stage of the
modular attack path, where the printed sentence's lack of a cost or a frequency is
implemented as one second die per failed save that is never itself re-rolled. Focused
discriminators were added (`tests/python/construction/test_t13_wardrobe_variants.py`,
`tests/python/combat/modular/test_t13_eshin_assassins_luck.py`) and the Eshin scaffold
gained the re-roll scenarios. The register rows for the six affected clauses were
rewritten by `build/audit/m0-reconciliation/apply_t13_wardrobe_resolution_20261014.py`
behind a concurrent-change guard: relation/effect/parameters/conditions/consumer/status
and notes changed, all other records kept their exact bytes, and `validate_csv.py`
reports PASS with 0 violations over the 4,556 conserved keys.
