# T13.3a — Spectral Touch modular pilot

> Current ownership — 2026-10-02. The [shared eligibility boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation) is already implemented for both products. Pilot combat tests below prove the modular mechanism at their reviewed revision; injected tags do not establish canonical legal selection or activation. After the required source decisions, reuse shared eligibility for legal access and separately prove KB binding/compiler activation before optimized ports. Historical results and later acceptance sections retain their own stated limits.

Status: modular implementation accepted on 2026-10-02 after independent review;
the user accepted Q019 recommendations R1–R4 on 2026-10-01. The modular Barrage
prerequisite is repaired and verified below. [Acceptance and limits](T13-spectral-touch-independent-review.md#13-coordinator-acceptance--2026-10-02)
retain their modular acceptance. L03 completed F008's canonical activation and
source-linked specifications on 2026-10-03 and accepted F056's mixed-provenance
witness in the same delivery; [current evidence](#l03-canonical-activation--2026-10-03)
is below. F009 optimized execution remains scheduled for L19/L20.

## Sources and boundary

- [T13 plan](T13-implementation-plan.md#spectral-touch-pilot),
  [inventory](T13-inventory.md#spectral-touch-and-banshee-probes) and
  [origin ledger](T13-obligations.csv): Q019.
- [Call Of The Night Haint, original PDF](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Call%20Of%20The%20Night%20Haint.pdf),
  fifth PDF page (annual printed page 082), Spirit Host / Spectral Touch;
  third PDF page (080), Spirit Knife. The canonical locator's page 5 means the
  fifth PDF page, not the annual's printed page number. The Spirit Host sentence
  contains a duplicated word; the Spirit Knife sentence confirms one extra wound.
- [Core rules, Part 1](https://broheim.net/downloads/rules/Mordheim%20-%20Part%201%20-%20Background%20%26%20Rules.pdf),
  printed pages 16–17, 19–21: criticals, injuries, armour, parries and attacks on
  warriors disabled during the same combat phase.
- Canonical rule: `sources/knowledge/bands/mordheim/call-of-the-night-haint-mim/special-rules.yaml#spirit-hosts--spectral-touch`.
  Its profile binding is `trait.spectral-touch`, now active in canonical modular
  construction. The vocabulary was already promoted; L03 did not modify it.
- [T13 contracts](T13-contracts.md), [implementation guidance](../../../guides/implement-and-verify-rules.md)
  and [Shifty delivery](T13-shifty.md) govern actual-engine tests and concurrent work.

Combat Lab is independent of Warband Manager. This unit needs no campaign or
board context. Spirit Knife activation is a separate obligation; its related
wording does not silently register or certify that item here.

## Proposed Q019 contract, fixed before implementation

The initial proposal below is now governed by the human-accepted R1–R4
rulings; item 8 records the accepted Barrage correction. The heading is retained
for existing links. See the [permanent ruling](../../../decisions/design-rulings.md#spectral-touch-q019).

1. A successful, final natural hit die of six triggers exactly one extra wound.
   A successful reroll of six qualifies. Automatic hits, modifiers taking a five
   to six, characteristic tests (Sweep) and manufactured successes (Mark of the
   Old Ones) do not supply a natural six.
2. Resolve the original hit's Lucky Charm and eligible parry first. An ignored or
   parried hit has no effect. Ordinary parries cannot stop a six; an explicitly
   supported exceptional parry can. The extra wound is not another hit and does
   not repeat Lucky Charm, parry, on-hit effects or weapon allocation.
3. Resolve the extra wound before the ordinary wound roll. No toughness test,
   wound die or critical die is added. It does not consume critical capacity.
4. Treat it as one additional wound of the same attack: retain that attack's
   armour modifiers, eligible special saves and injury modifiers. No printed
   armour-denial exception exists. Weapon damage multipliers/dice and critical
   doubling do not increase this explicitly single contribution. Criticals from
   the subsequent ordinary wound affect only that ordinary contribution.
5. Apply injury and immediate reactions/rescue to the extra contribution before
   continuing. Stop if either combatant is removed. If rescued, continue with
   current resources and wounds. Knockdown/stun caused by this attack does not
   turn its continuation into an automatic finisher.
6. Report total damage from both contributions, but react to each lost wound
   once. An extra wound saved by armour/ward/regeneration still permits the
   ordinary wound roll. A failed ordinary wound does not erase extra damage.
7. Use the existing pool convention: prepare all hit dice and resolve collective
   hit defences, then process each surviving hit's extra and ordinary wounds in
   attack order. Do not change established parry allocation/RNG to create a new
   interpretation of 'immediately'.

8. Barrage requires this attack to have established no wound. An extra wound
   blocks it even when saved and even if the ordinary wound roll fails. Without
   an extra wound, ordinary wound failure retains the existing optional Barrage.
   A new eligible Barrage hit draws its own die and may trigger Spectral Touch.

Items 2, 4, 5, 7 and 8 are human-accepted project interpretations, not additional
wording in the Night Haint source. Independent implementation/data review and
canonical proof still gate promotion, Q019 closure and backend ports.
No immunity to this wound is inferred from narrative references to a heart.

## Deterministic acceptance cases

Before coding: author strict ordered dice tests on real attack and pool paths for
six/non-six/absence; rerolls; automatic and manufactured results; ignored and
exceptionally parried hits; separate armour/ward/regeneration saves; wound failure,
critical capacity and damage cap; removal, rescue, acid blood and disabled-target
continuation; repeated hits and production Spirit Host fixture with an isolated
pending tag. Mutation checks must fail when the trigger is removed or ordinary
continuation is suppressed. Canonical loading without the fixture must remain
explicitly pending.

## Delivery and review

The modular implementation uses `trait.spectral-touch` in isolated compiled
fixtures. It extracts the existing save/damage/injury tail into
`modular/attacks.py:_resolve_wound_damage`; ordinary wounds retain that same
pipeline. The extra contribution enters it directly, without synthesizing another
hit or taking the Disease Dagger's toughness test, immunities or fixed strength.
`single_wound=True` fixes its damage to one even when weapon damage dice or a
fire/flammability multiplier would otherwise increase damage. The same attack's
save and wound/injury effects remain applicable; source-specific compositions
still require review before declaring their canonical loadouts supported.

`AttackOutcome.natural_hit_six` records hit provenance before Mark of the Old
Ones can replace a failed result. All prepared-hit consumers in `modular/pools.py`
transport it explicitly. It is internal modular metadata, not a kernel/native
field or a new compiled characteristic. Barrage resets provenance for each new
hit and carries previously reacted secondary damage through the complete
sequence. Immediate reactions use the existing aftermath consumer and existing
`damage_already_reacted` accounting.

Files: `modular/attacks.py`, `modular/state.py`, narrow additions to
`modular/pools.py`, new `tests/python/combat/modular/test_spectral_touch.py`,
this document and coordinator documentation. Existing Shifty and T13.1 changes
are preserved. Bloated Foulness/compiler work belongs to the external agent and
is not changed or accepted here.

## Verification — 2026-09-30

- Before implementation, the first 32 authored expectations produced **21
  failures and 11 passes** on the incoming modular engine. The failures were
  missing Spectral Touch behavior, not a production registration test.
- Final suite: **397 passed**, no skips, including **49 Spectral Touch cases**,
  **44 Shifty cases**, existing modular, phase, context/replay and architecture
  tests. Strict dice and decisions check missing, extra and reordered requests.
- Additional cases cover strength/penetration, magical defenses, Luck consumption,
  reactive removal of the attacker, ordinary injury after an immediate stun,
  critical armour denial limited to its contribution, Kusara on-hit effects,
  pool Charm/removal, and repeated Rapier Barrage hits. Two isolated in-memory
  source mutations remove the trigger or suppress ordinary continuation; the
  authored expectations detect both. No working-tree mutation is used.
- A real canonical Spirit Host is loaded and confirmed to have **no active
  Spectral Touch tag**. Adding the isolated pending tag exercises both its actual
  attack and the public modular duel replay (three prepared hit dice, immediate
  injury, terminal wounds/conditions/winner). This does **not** certify the full
  canonical data-to-combat grant: trait registration, canonical activation and
  source-linked semantic specifications are still pending.
- All six accepted seed31 samples remain exact (200 duels, batch67, max5):
  plain modular `(35,99,66)`, NumPy `(37,77,86)`, native `(30,97,73)`;
  Crimson Shade modular `(49,83,68)`, NumPy `(45,75,80)`, native `(46,92,62)`.
  These samples prove preservation, not optimized Spectral Touch support.

Reproduction:

```powershell
python -X utf8 -m pytest tests/python/combat/modular/test_spectral_touch.py -q
python -X utf8 -m pytest tests/python/combat/modular tests/python/combat/test_phases.py tests/python/combat/test_duel_context.py tests/python/verification/test_duel_replay.py tests/python/architecture -q --tb=short --junitxml=build/cache/t13-parallel/spectral-touch/final-broad.xml
python build/cache/t13-1/legacy-sample.py
```

Local evidence: `build/cache/t13-parallel/spectral-touch/entry.json`, incoming
copies of the three modular files, `before.xml`, `final-broad.xml`,
`legacy-results.json`, per-file entry diffs and `delivery.json`. The XML is
generated evidence. The delivery records current file hashes and final counts.
The 49-case result is included in `final-broad.xml`; `intermediate-focused.xml` records an earlier incomplete run, not the final
result.

Full KB semantic/parity certificates and coverage budgets are not advanced.
No canonical YAML, generated assets, optimized engine/binary, UI/language,
commit or push changes belong to this delivery. No agents were launched.

## Accepted R4 modular repair — 2026-10-01

The user requested the coordinator's next task after accepting R1–R4. The
original pilot treated failure of the ordinary wound roll as sufficient for
Barrage, even after an established extra wound. Three old fixtures embodied
that incompatible behavior; their replacement expectations come from accepted
R4 and the original Barrage wording, not the implementation.

The correction is confined to `resolve_reference_attack`: after aggregating
secondary contributions, reject Barrage when `result.wounded` is true, before
asking the decision policy. A successful save still records an established
wound. The ordinary continuation remains obligatory when both participants
survive. There is no additional wound, save or critical die and no change to
pool preparation, trait registration, compiled eligibility or optimized engines.

Two continuation fixtures now start with a non-six failed ordinary wound and
an eligible Barrage choice. A new natural six causes an extra wound, then its
ordinary continuation; ordinary failure stops Barrage, while ordinary success
retains two contributions with one Acid Blood reaction per lost wound.

Verification on the captured working tree:

- Before repair: **7 failed, 50 deselected**, all unexpected Barrage decisions,
  in real attack/pool/public modular replay paths. The initial development run
  also exposed an incorrect test assertion about post-reaction metadata and
  missing mutation anchors; those are not counted as behavioral red evidence.
- Focused Spectral Touch/Shifty/source-correction suite: **215 passed**.
- Modular/phase/context/public replay/architecture suite: **405 passed**.
- Spectral Touch itself: **57 cases**. Six saved/unsaved path cases forbid
  phantom decisions/dice; absence retains normal Rapier Barrage. In addition to
  the original trigger/continuation mutations, two isolated mutations remove
  the new prerequisite or incorrectly substitute unsaved damage; both are caught
  by the saved-wound case. No live engine file is mutated by those tests.
- Existing coverage gate: **519 tests passed**, but **gate failed** on 217
  budgeted line discrepancies across the earlier modular pilots. Current areas:
  modular 97.18%, vectorized 93.75%, phases 96.94%. Static comparison identifies
  208 obsolete statement indexes, with nine executable-line discrepancies still
  requiring review. The attack statement set is unchanged by R4. Budget bytes
  are preserved; [F040](T13-execution-follow-ups.md#t13-f040--modular-coverage-line-budget-needs-reconciliation-after-pilots)
  owns reconciliation before engine acceptance/T14 certification. A passing
  percentage alone does not close the drift failure.
- Existing engine catalogue: **all six mutations detected** across maintained
  vectorized unit, exact-operator and plain-injury runtime detectors. Identical
  staged-source controls pass for each detector selection. Unit-only detects
  two; exact operators detect five; the existing runtime boundary case detects
  the remaining injury-threshold mutant. The default catalogue run, which
  repeats the full slow semantic corpus for every mutant, was interrupted; no
  default-corpus catalogue certificate is claimed. `catalogue-combined.json`
  records each detected mutant and its control. No new test framework is added.
  Full KB source certification is a separate snapshot/pin task; no semantic pin
  is edited or refreshed by this repair. During gate execution, external work
  changed all 104 reserved spec files to the 300 approved new pins. This is an
  observed concurrent change, not external delivery acceptance by this lot.

Local evidence: `build/cache/t13-parallel/spectral-touch-barrage-repair/`:
`entry.json`, incoming files, `red.xml`/`red.log`, `focused.xml`/`focused.log`,
`broad.xml`/`broad.log`, coverage/catalogue logs and `delivery.json`. This repair
adds no production activation, Spirit Knife claim, optimized port, UI change,
agent dispatch, commit or push. Shifty's independent semantic review is separate.

## Independent implementation review barrier and prompt

The [initiative coordination protocol](../README.md#estado-y-protocolo-de-trabajo)
requires a different reviewer for a semantic change. The human source decisions
are accepted; F007's repaired implementation was independently accepted on
2026-10-02. The prompt below is the historical review dispatch. No reviewer is
launched automatically. Q019 is answered in the permanent ruling
and inventory, but canonical closure still requires F008's source-linked proof.

```text
Review the accepted-Q019 Barrage repair read-only in:
D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK

Read docs/knowledge/2a2b/README.md and tasks/T13-spectral-touch.md,
T13-spectral-touch-review.md, T13-inventory.md, T13-execution-follow-ups.md,
and docs/decisions/design-rulings.md (Spectral Touch Q019).
Consult the linked original Night Haint/core/errata/LOD2 sources and the
human-accepted R1–R4 scope; do not reopen those choices without new evidence.

Review the repair diff against the incoming attacks.py/test_spectral_touch.py
copies in build/cache/t13-parallel/spectral-touch-barrage-repair/incoming/.
Confirm an established saved or unsaved extra wound blocks Barrage before its
choice, ordinary continuation remains intact, an eligible later natural six
uses its own provenance, and ordinary/extra reactions happen exactly once.
Check strict real attack/pool/public replay witnesses and both new isolated
mutations. Inspect the common attack wrapper for other-consumer regressions.

Run the focused Spectral/Shifty/source-corrections suite, then the documented
broad suite if material uncertainty remains. Read retained red/green, coverage
and catalogue evidence before repeating expensive gates. Preserve concurrent
eligibility/UI/language work and the external 300-pin reservation. No writes,
agents, commits, pushes, source repinning, production activation or ports.
Return actionable file/line/source/reproducer findings, or acceptance limited
to this modular repair. At that historical review F008 canonical activation/specs
and F009 optimized execution stayed pending; the L03 update below supersedes
F008's status. Spirit Knife Q146 and Shifty remain separate.
```

## L03 canonical activation — 2026-10-03

Canonical Spirit Hosts now receive Spectral Touch through the normal Combat Lab
catalogue, shared construction decision and compiler, without injected tags.
Their printed WS2/S2/T2/W3/I2/A3/M3/Ld6 profile and legal default natural attacks
are preserved. The public modular `simulate_duel(DuelRequest)` and whole-round
pipeline consume the rule. This completes F008 at the canonical modular boundary
and incorporates F056; it does not complete F009 or certify T13/T14.

### Source, ownership and implementation

The source and Q019 R1–R4 contract above are reused. The coordinator checked the
existing canonical sentence, binding and Spirit Host recipient against the
retained original PDF extract in `spectral-touch-review/night-haint-selected.txt`
and the human-accepted [permanent ruling](../../../decisions/design-rulings.md#spectral-touch-q019).
No new combined-rule interpretation, translation or Spirit Knife activation was
introduced. Independent raw-YAML checks confirm that `profile.rule_ids` and
`applies_to.profile_ids` name only `spirit-hosts` for this grant.

- [Canonical special rules](../../../../sources/knowledge/bands/mordheim/call-of-the-night-haint-mim/special-rules.yaml)
  and their exact [2B mirror](../../../../sources/2B/bands/mordheim/call-of-the-night-haint-mim/special-rules.yaml):
  only this rule's `runtime.implemented` changes from `NO` to `YES`.
- [Trait contract](../../../../packages/python/roster-construction/mordheim_construction/contracts.py)
  admits the boolean `spectral_touch`; the existing automatic-grant path already
  applies the correct shared recipient decision. The
  [closed profile schema](../../../../contracts/knowledge-editorial-v1/profiles.yaml.schema.json)
  mirrors that single boolean; the maintained registry-parity gate remains strict.
- [Compiler](../../../../packages/python/roster-construction/mordheim_construction/compiler.py)
  translates that boolean to exactly one `trait.spectral-touch` tag. Other trait
  names and compilation behavior retain their prior contract.
- [Optimized support boundary](../../../../packages/python/combat-engine/mordheim_combat/kernel.py)
  rejects Spectral Touch on either participant before NumPy/native execution,
  including weapon-scoped synthetic transport. It reuses L02's existing guard;
  the optional Vomit refusal remains. No fallback or engine port is implied.
- [Construction table](../../../../packages/typescript/domain/campaign/construction-tables.json)
  drops the now-stale single pending binding; its source-parity gate and the
  [TypeScript regression](../../../../tests/typescript/domain/campaign/construction.test.ts)
  verify the active rule is no longer announced as unimplemented. This changes
  the projection's status data, not Warband Manager legality or combat behavior.

`modular/attacks.py` and `pools.py`, the canonical profile, binding registry and
all eleven shared-centralization closing inputs are byte-unchanged from entry.
The existing Spectral suite's one pending-canonical test is updated to assert
the actual grant, preserving its behavior witness and the remaining synthetic
composition cases. The external F056 test file is unchanged. Supplemental
ownership of the stale status table and its TypeScript test was recorded before
editing; entry snapshots retain the pre-existing dirty production work.
The schema's single-property extension was captured in `schema-entry.json`
after its maintained parity gate exposed the missing registry mirror; no audit
allowlist or validator was changed.

The sanctioned generator refreshed browser knowledge publication; its subsequent
`--check` passes. The retained initial `knowledge-web.json` differs in its three
deferred-presentation digests, recorded in `publication-diff.json`. Outputs remain
generator-owned. No hand editing of publication, source pins, scope or coverage
budgets occurred.

### Cases, mutation evidence and validation

[Canonical tests](../../../../tests/python/combat/modular/test_spectral_touch_activation.py)
contain 23 cases: exact compilation, seven foreign-profile controls, catalogue
status, three natural-attack pools, a complete round and a public modular request,
plus public/low-level optimized refusals on either side and weapon-scoped refusal.
The first baseline reproduced missing activation/guard failures (14 failed,
8 passed); final tests pass. Two initial test-authoring errors (read-model field
names and round key/result shape) were corrected to the maintained API. The
semantic condition spelling is `OUT`; its initial `OUT_OF_ACTION` expectation was
also corrected without an engine change.

[Source-linked specification](../../../../tests/specs/semantic/grants/t13-spirit-host-spectral-touch.yaml)
adds 10 cases: recipient, compilation, both mixed 6/5 orders, non-six control,
normal wound success and S2 boundary, saved extra contribution with retained
normal roll, immediate injury/stop, and a different canonical profile's six.
Explicit free-selection opponents are controls, never a claim that Spirit Hosts
can carry foreign equipment. The verifier detects all four mutations: lost
trait, manufactured automatic hit, incorrect ordinary Strength and discarded
inherited armour save. F056's six maintained cases also pass. An independent
canonical three-hit replay detects the delivered pooled-provenance mutant in
both orders specifically at the wrong per-hit damage, with no live mutation.

| Command/check | Result |
| --- | --- |
| `python -X utf8 -m pytest tests/python/combat/modular tests/python/construction tests/python/combat/test_duel_context.py -q` | 891 passed |
| Staging promotion, kernel plan, vectorized backend and architecture-boundary suites | 24 passed |
| `npm run test --workspace campaign-web-core -- construction.test.ts construction-kb-sweep.test.ts` | 34 passed |
| Focused semantic cases for L03 and L02 | 17 passed |
| Editorial schemas after the one-property registry mirror | 305 passed; strictness 39 justified / 0 hard-unjustified-stale |
| `python -X utf8 tools/mordheim-utils.py verify --json` | Structural complete, 1050 profiles; 567 verified / 151 pending / 718 obligations; 30 historical errors |
| Raw-source/diff/protected-input review and canonical F056 mutant replay | Exit 0; no unintended source/protected drift |
| `npm run check:eligibility` and generator `--check` | Current |
| Documentation links and scoped diff/new-file whitespace | Passed |

The full verifier executed all 10 new cases and killed all 4 mutations. Compared
by identities with L02's retained report, exactly the Spectral target moves into
`verified`; no prior target loses verification and the 30 source errors are
identical. Exit 1 on that inherited set is retained, not converted into a phase
success. F057 now owns reconciliation of **3775** authored cases (L02's 3765 plus
these 10); its externally reserved parity test was not edited.

Evidence and reproducible scripts are in
`build/cache/t13-parallel/spectral-touch-activation/`: immutable `entry.json`,
`entry-supplement.json` and backups; before/final test logs; `verify.json`;
`delivery-review.json`; `f056-independent-review.json`; publication checks and
closing hashes. This section is sufficient to reconstruct the maintained
contract without the ignored cache. Documentation/knowledge results and final
whitespace checks are recorded in the closing evidence.

### Remaining boundary and next lot

F009 remains open for actual equivalent NumPy/native execution in L19/L20;
its F007/F008 prerequisite is now satisfied. Optimized analysis in the GUI
currently reports the explicit unsupported error. GUI/backend routing and
presentation completion stay with L18/L19/L20: this delivery exercises the
supported public modular API, not a new GUI engine selector. Spirit Knife F025
and its source decision remain separate. F057's count/full-coverage gate and the
30 historical source pins remain with their existing owners. No new follow-up
project, agent launch, commit or push was created. The next planned lot is L04,
canonical Shifty activation with its accepted S1–S4 and existing pistol limits.
