# T13.3a — Spectral Touch independent implementation review (F007)

Status: review delivered for coordinator acceptance. The reviewer is a different
agent from the implementer, ran read-only over production inputs and wrote only
this document and evidence under
`build/cache/t13-parallel/spectral-touch-independent-review/`. No maintained
file, source, specification, pin, budget or shared register was edited; no
agent was launched; no commit or push was made. This review does not close F007,
and it does not certify canonical activation (F008) or optimized execution (F009).

## 1. Purpose and boundary

The reviewed change is the human-accepted Q019 implementation of Spectral Touch
(R1–R4, accepted by the user on 2026-10-01) and the narrow modular R4 Barrage
repair of 2026-10-01. The review answers: does the delivered modular oracle
implement the accepted contract and the original source reading, and does its
evidence support that claim?

Scope limits fixed by the dispatch:

- R1–R4 are accepted human decisions; this review checks compliance, not the
  acceptance itself.
- Only `packages/python/combat-engine/mordheim_combat/modular/**` and
  `tests/python/combat/modular/**` are semantic evidence authorities here.
- F008 (canonical Spirit Host activation and source-linked specifications) and
  F009 (NumPy/native ports) are separate and explicitly not accepted by this lot.
- The F040 coverage-gate reconciliation has its own review; a green percentage
  would not prove semantic correctness, and a red drift gate does not by itself
  refute the repair. Retained F040 evidence was read, not re-run.
- Test fixtures inject `trait.spectral-touch`; no fixture success is treated as
  certification of a legal canonical loadout.

No applicable `AGENTS.md` exists in the workspace or its ancestors (searched at
entry; the same absence was recorded by the earlier
[review dossier](T13-spectral-touch-review.md)). The initiative coordination
protocol in the [checklist](../README.md#estado-y-protocolo-de-trabajo) and the
user's explicit write boundary govern this lot instead.

## 2. Examined revision and input integrity

Entry captured 2026-10-02. Branch `2A2B`, HEAD
`1b7f7cf10b75a9d716c34c64039f5c908caed19e`, 253 dirty paths (concurrent T13
work). The repair's own evidence states that HEAD alone was never its entry;
this review therefore identifies the examined revision by actual working-tree
hashes, captured before and after the review with no drift (see
`entry.json`/`closing-hashes.json` in this lot's evidence).

| Input | SHA256 (actual working tree) |
| --- | --- |
| `modular/attacks.py` | `55e05e32046a15428d43085195563ee471b07eb90be1cebeb59f6c9c444b6ef6` |
| `modular/pools.py` | `567a9636f7ac652d404c3c6cc09e6fb3748249dd5b6ee855005c30a25f669a0a` |
| `modular/state.py` | `69b7c2934fdcd53039a8e7ac64bfdff0f4c056ae851ee900afe14c79916c76aa` |
| `tests/.../test_spectral_touch.py` | `4658ddf6fd3ae0d74472375adf75e392fd788b3b188c7ff6140a06a2d474a97f` |
| `tests/.../test_shifty.py` | `09b32382bbdf127c4493bd96f06ff3fa1b155df15b06d7767aa0377d07963f9c` |
| `T13-spectral-touch.md` | `6a9dc21a648a61311d93aec57eb3b503d597bf2303e27bc3bb54b6b59f07e591` |
| `T13-spectral-touch-review.md` | `502c3d5db042db49061f778548927e217a4dc6d66b64fab00719f633cbfbccc4` |
| `docs/decisions/design-rulings.md` | `b5e2f8f7b4747d34427256c43c862351d5c3cd2e3f5f68de5748ce88acfa24fc` |
| `sources/knowledge/.../special-rules.yaml` | `e1bb595ad26ebad481a20c72ee9d7aa1c5b5525aaca9d9cef50ee219d850706b` |
| incoming `attacks.py` (pre-repair) | `95073dc56cdc1bbcca0abed8576ac474ff6d7ff02fc05839442ed69147d78b82` |
| incoming `test_spectral_touch.py` (pre-repair) | `87fb357a0f80c3827d185c8ba3f72e3fec069b534ec20058dc1ab485f84822eb` |
| Night Haint PDF (re-verified) | `11904029e1af9aafe4c92a88240f04b9808415e7587d7d680a326495d7d0aad5` |
| LOD2 PDF (re-verified) | `f715d017202ecf04c22800cc2490db1ad6f524e787ec4ce95a6c4abf8ab7862d` |

Integrity checks performed:

- The live `attacks.py` and `test_spectral_touch.py` hashes equal the repair
  delivery hashes; nothing changed since delivery.
- The retained repair diffs were applied offline to the incoming copies with
  `patch -p0`: both apply cleanly and reproduce the live files byte-for-byte
  (`RETAINED ... DIFF REPRODUCES LIVE FILE EXACTLY`). The retained diff is a
  faithful record of the incoming→repaired change.
- The incoming `attacks.py` does **not** equal the HEAD blob
  (`6450e139...`), and `test_spectral_touch.py` does not exist at HEAD; the
  batch entry was the earlier uncommitted pilot plus the repair, as documented.
- The canonical source file rule matches the reviewed text hash chain used by
  the pilot; the external PDFs retained in the prior review lot re-verify
  against their recorded digests.

## 3. Authorities and source reading

Reviewed authorities, distinguishing explicit source text, general rules and
accepted project interpretation:

- **N — explicit.** [Call of the Night Haint](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Call%20Of%20The%20Night%20Haint.pdf),
  PDF page 5 / printed 082, Spirit Host: “If the hit roll for an attack made by
  a Spirit Host is 6, the spirit’s frightful touch stills the victim’s beating
  heart, immediately inflicting 1 wound additional wound. Roll to wound for the
  hit as normal.” The duplicated “wound” is a source typo; the Spirit Knife
  wording on PDF page 3 / printed 080 — “If the hit roll for an attack made by a
  Spirit Dagger is 6 … immediately inflicting 1 additional wound. Roll to wound
  for the hit as normal.” — confirms one additional contribution and the
  ordinary roll. Neither passage gives a defensive order, an immunity, a
  Strength attribution or a Barrage composition rule; the heart imagery is not
  an operative clause.
- **C — general.** Mordheim Part 1 (retained extraction): rerolls bind the
  second result; armour is rolled per wound with Strength modifiers; criticals
  require a wound roll of 6 and one critical per phase; ordinary parry cannot
  beat a hit roll of 6; injuries are rolled per wound and removal follows OOA.
- **L — erratum.** Errata PDF page 2, “Page 53, Lucky Charm”: the first hit is
  discarded on a 4+, once per battle.
- **B — general, separate source.** LOD2 PDF page 6 / printed 66, Rapier
  “Barrage”: “if you manage to hit your opponent but fail to wound you may
  attack again just as if you had another attack but at –1 to hit”.
- **P — accepted project interpretation.** The Q019 rulings accepted on
  2026-10-01 ([T13-spectral-touch.md](T13-spectral-touch.md#proposed-q019-contract-fixed-before-implementation),
  [permanent ruling](../../../decisions/design-rulings.md#spectral-touch-q019)):
  the extra inherits this attack's save/injury context and is capped at one;
  injury/rescue/reactions resolve before the ordinary contribution; “immediate”
  means after collective pool hit/defense preparation; “fail to wound” for
  Barrage is evaluated for the whole attack, so an established extra wound —
  even saved — blocks continuation. These are compositions of N, C, L and B,
  not quotations of an explicit combined rule.

## 4. What the reviewed revision does

- `modular/attacks.py:128` records `natural_hit_six` from the physical hit die
  before Mark of the Old Ones can replace a failure, and before a Sweep
  characteristic test can be mistaken for a die face; the flag travels on
  `AttackOutcome` (`modular/state.py:91`).
- `modular/attacks.py:199-218`: only a natural six on an attack carrying
  `trait.spectral-touch` enters the extra block, after Lucky Charm, parry and
  `defences_only` handling. The extra calls the shared `_resolve_wound_damage`
  with `single_wound=True`, a zero-valued synthetic `WoundResult`, no critical
  and no invented die; `_react_to_wound` resolves its injury, rescue and
  reactions immediately, and the ordinary contribution resumes only if both
  participants remain active.
- `modular/attacks.py:320-407` applies armour, special saves, one damage point,
  injuries and stun reaction to the extra through the same pipeline as the
  ordinary contribution, with the attack's actual Strength, penetration, magic,
  fire and injury context.
- `modular/pools.py:224-232` prepares every hit (`hit_only=True`) and
  `_resolve_prepared_defences` resolves collective Charm/parry before per-hit
  wounds; per-hit provenance is transported at `pools.py:108,140,280,303,330`.
- `modular/attacks.py:50-62`: secondary contributions are aggregated and
  `result.wounded` is merged; the R4 predicate at line 60 rejects Barrage when
  **any** wound was established for that attack, before the decision policy is
  consulted. Lines 65-67 reset `prepared_hit`, `natural_hit_six` and
  `defences_resolved` so every new Barrage attack recomputes its own provenance.

## 5. R1–R4 compliance matrix

| Ruling | Requirement | Implementation location | Evidence | Result |
| --- | --- | --- | --- | --- |
| R1 | Extra inherits this attack's save/injury modifiers and eligible defenses, respects printed timing, stays exactly one despite damage multipliers | `attacks.py:199-218`, `_resolve_wound_damage` `attacks.py:320-356` (`armour_context` 320, special save 342, `single_wound` 354); `critical_available` untouched | `test_each_contribution_has_own_armour_save`, `test_extra_obeys_special_saves`, `test_extra_uses_actual_attack_strength_and_penetration`, `test_extra_respects_magic_specific_natural_armour_and_ward`, `test_extra_is_one_even_with_fire_and_flammable`, `test_extra_immediate_save_consumes_luck_before_ordinary_save`, `test_extra_does_not_use_critical_capacity_or_weapon_damage_die`, `test_ordinary_critical_does_not_double_extra`; review probe A | **Pass** (modular; generic-mechanics fixtures) |
| R2 | Extra injury, rescue and reactions resolve before the ordinary contribution; stop if either participant remains removed; rescued participant continues | `attacks.py:206-218` (`_react_to_wound` then active check), `aftermath.py:39-61` (immediate rescue, once-per-wound reaction) | `test_extra_removal_stops_ordinary_and_reacts_once`, `test_rescue_is_immediate_before_ordinary_wound`, `test_extra_acid_blood_removing_attacker_cancels_ordinary`, `test_both_contributions_react_once`, `test_extra_knockdown_or_stun_does_not_auto_finish_continuation`, `test_stun_then_successful_ordinary_wound_still_rolls_injury` | **Pass** |
| R3 | Collective hit/defense preparation before per-hit extra/ordinary processing | `pools.py:224-232` (prepare all hits), `_resolve_prepared_defences` `pools.py:75-151`, per-hit loop `pools.py:325`; provenance transported per index at 108, 140, 280, 303, 330 | `test_repeated_pool_sixes_each_add_one_wound_after_hit_preparation`, `test_pool_charm_blocks_only_first_six_and_consumes_once`, `test_pool_lethal_extra_cancels_later_prepared_hit_wounds`, `test_pending_spirit_host_tag_reaches_actual_modular_duel_driver`; review mixed-provenance probe | **Pass** (one detector gap under F1) |
| R4 | Barrage requires failure to establish any wound for the attack; an established extra blocks it even when saved and even when the ordinary roll fails; no decision before the check; later Barrage hits keep their own provenance; without an extra, ordinary failure keeps optional Barrage | `attacks.py:50-62` (aggregate + predicate at 60), `attacks.py:65-67` (provenance reset), `attacks.py:286-287` (availability only on ordinary failure), `pools.py` transport | `test_established_extra_wound_prevents_barrage_even_when_saved[6 paths]`, `test_barrage_new_six_establishes_extra_and_stops_despite_ordinary_failure`, `test_barrage_new_six_reacts_to_extra_and_ordinary_damage_once_each`, `test_natural_six_without_spectral_touch_keeps_barrage_after_failed_wound`, `test_barrage_prerequisite_detects_isolated_mutations`, maintained `test_rapier_barrage_continues_after_two_failed_wounds`, `test_m10_barrage_*`; review probe B | **Pass** |

## 6. Required semantic checks

| Check | Where verified | Observation | Result |
| --- | --- | --- | --- |
| Individual provenance of the triggering hit | `attacks.py:128`, `state.py:91`, `pools.py` transport | Provenance is computed once from the physical die and carried per prepared index; a five modified to six, automatic hit, Sweep test and manufactured Mark success do not qualify (`test_hit_modifier...`, `test_automatic_hit_has_no_natural_six`, `test_sweep...`, `test_mark_manufactured_six...`). Review probe: pool with hits 6 and 5 attributes the extra to the six only. | Pass |
| One extra contribution per activation, no invented roll | `attacks.py:199-218` | Trigger entered once per attack; extra consumes no wound/critical die. Review probe keys: `p.attack.0.hit, p.attack.1.hit, p.attack.0.wound, p.attack.1.wound` — fully consumed, no extra request. | Pass |
| Collective preparation of hits and defenses | `pools.py:224-232, 75-151` | All hit dice drawn before any defense; Charm/parry resolved collectively before per-hit extra/ordinary. | Pass |
| Injury, rescue and reactions before continuation | `attacks.py:206-218`, `aftermath.py` | Extra injury and reactions resolve immediately; continuation suppressed when either participant is removed; rescue restores continuation with current resources. | Pass |
| Ordinary continuation while both active | same | After a saved extra, the ordinary wound roll proceeds; a failed ordinary roll does not erase extra damage. | Pass |
| Interruption when either participant withdraws | `attacks.py:214-218`, `pools.py:325-340` | Defender removal or reactive attacker removal stops the ordinary contribution and later prepared hits. | Pass |
| Saves and reactions at the right moment, without double application | `_resolve_wound_damage`, `_react_to_wound`, `damage_already_reacted` | Luck spent on the extra save is not re-spent; Acid Blood fires once per lost wound across extra + ordinary; `reactions_resolved` prevents a second pass. | Pass |
| Barrage blocked once the extra wound is established, even saved | `attacks.py:60` | Attack, pool and public replay paths all block; saved extra yields `wounded=True, damage=0` and no Barrage request. | Pass |
| No Barrage decision requested before the block | `attacks.py:60-61` short-circuit order | Review probe recorded `decision_requests == []` for both saved and unsaved extras; the maintained fixtures use strict empty decisions. | Pass |
| Later legitimate Barrage hits keep their own provenance | `attacks.py:65-67` | New attack recomputes `natural_hit_six`; a new six qualifies and their own reactions happen once each. | Pass |
| Other consumers of the common wrapper unchanged | `rounds.py`, `scenarios.py`, `aftermath.py` recursion, `pools.py` | `barrage_available` is produced only for `weapon.rapier` on ordinary failure; the only other secondary wound source is Disease Dagger infection, which cannot coexist with `weapon.rapier` on one attack in the canonical KB (distinct weapon tags, verified). Broad suite re-run: 432 passed vs the retained 405, 0 removed, 27 added by a concurrent accepted lot. | Pass |

## 7. Fresh independent verification

All commands from the workspace root, Python 3.10, bytecode and pytest cache
disabled; raw logs and XML are in this lot's evidence directory.

| Command | Result |
| --- | --- |
| `python -X utf8 -m pytest tests/python/combat/modular/test_spectral_touch.py tests/python/combat/modular/test_shifty.py -q -p no:cacheprovider` | **101 passed**, exit 0 (57 Spectral Touch + 44 Shifty), 13.5 s. `focused.log`, `focused.xml`. |
| `python -X utf8 -m pytest tests/python/combat/modular tests/python/combat/test_phases.py tests/python/combat/test_duel_context.py tests/python/verification/test_duel_replay.py tests/python/architecture -q -p no:cacheprovider` | **432 passed**, exit 0, 52.1 s. `broad.log`, `broad.xml`. Compared with the retained repair `broad.xml`: 405 → 432, **0 removed**, 27 added (`test_profile_save_thresholds.py`, concurrent accepted Fimir/Boglar lot). |
| `python build/.../probe.py` | exit 0. Mixed pool provenance (six + non-six, strict dice fully consumed); saved/unsaved extra blocks Barrage with zero decision requests; independent replay of both mutated predicates. `probe.json`, `probe.log`. |
| `python build/.../probe_provenance_detector.py` | Baseline replay `(3, 0)` wounds; pooled-provenance mutant undetected by that maintained replay witness. `probe-provenance-detector.json`. |
| `PYTHONPATH=... pytest tests/.../test_spectral_touch.py -p mutant_plugin` | **57 passed** with the isolated pooled-provenance mutant — see finding F1. `mutant-pooled-suite.log`. |

Retained repair evidence was read before any repetition: red run 7 failed /
0 errors (`red.log`), focused 215 passed, catalogue 6/6 mutants killed across
three detector selections with clean unmutated controls, coverage 519 passed
with the drift gate failing on 217 budgeted indexes, default full-corpus
catalogue interrupted and explicitly not certified. Those claims match the
retained XML/JSON/logs; none is overstated.

## 8. Findings

Severity scale: high (semantic defect), medium (materially incomplete evidence
for an accepted claim), low (narrow evidence gap, no observed defect).

### F1 — Low: the maintained suite cannot distinguish per-hit from whole-pool provenance

- **Type:** test-corpus detector gap; **no implementation defect observed**.
- **Location:** [test_spectral_touch.py:190-206, 277-290, 410-423](../../../../tests/python/combat/modular/test_spectral_touch.py#L190)
  (pool and replay fixtures); provenance transport at
  `modular/pools.py:303,330`.
- **Observation:** an isolated in-memory mutant in which every prepared hit
  shares `natural_hit_six=any(p.natural_hit_six for _, p in prepared_attacks)`
  passes all 57 maintained Spectral Touch cases. Every maintained multi-hit
  fixture either scripts all prepared hits as natural sixes
  (`test_repeated_pool_sixes...`, `test_pool_charm_blocks_only_first_six...`,
  `test_pool_lethal_extra...`) or scripts the non-six hits as misses (public
  replay fixture `6,1,1`). The trigger sits after the `hit.success` guard, so a
  missed hit cannot expose a shared flag; no fixture combines a natural six with
  another prepared hit that **hits** with a non-six face.
- **Independent witness:** the review's mixed probe (hits 6 and 5, both hitting)
  asserts exactly one extra (`defender wounds 3`, damages `[1, 0]`) and fails
  with `2` under the mutant — i.e. a maintained case of that shape would both
  document the contract and kill the regression.
- **Reproducer:** `build/cache/t13-parallel/spectral-touch-independent-review/`
  — `mutant_plugin.py` plus `mutant-pooled-suite.log` (57 passed) and `probe.py`
  (`mixed_pool_provenance`).
- **Impact:** the implementation is correct; the evidence for “individual
  provenance” is not mutation-protected. Proposed register entry in §9; no
  production change is requested.

### Boundaries and observations (not defects of this repair)

- **B1 — F008:** canonical `spirit-hosts--spectral-touch` still does not grant
  the production trait; fixtures inject it, and the suite proves the absence
  (`test_real_spirit_host_is_pending...`). Printed defense timings (for example
  Ethereal), every legal equipment composition and the source-linked
  specifications remain for F008; generic ward/regeneration and exceptional-parry
  fixtures prove mechanics, not canonical loadouts.
- **B2 — F009:** no optimized backend implements Spectral Touch (verified:
  no `spectral` reference in `vectorized/`, `native/`, `core/`,
  `roster-construction/`). The vectorized Barrage predicate
  (`vectorized/_attacks.py:532`) keys on wound-roll success before saves; that
  agrees with the accepted contract for plain attacks but must be revisited when
  the extra contribution is ported.
- **B3 — F040:** the one-line insertion at `attacks.py:60` shifts budget
  statement indexes after line 60; the retained coverage run shows the drift
  (`coverage.log`), and the repair declares the attack statement set unchanged.
  The coverage gate is red here for F040's separately reviewed reconciliation;
  this review does not treat it as semantic evidence either way.
- **B4 — catalogue:** the default full-corpus mutation run was interrupted and is
  declared uncertified; the three focused detector selections killed all six
  existing mutants with passing controls. No new mutation framework was
  introduced.
- **B5 — aggregation reach:** the R4 predicate uses the same `result.wounded`
  aggregate as the infection secondary wound. A single attack cannot carry both
  `weapon.rapier` and `weapon.disease-dagger` in the canonical KB, so the only
  observable behaviour change is the intended Spectral Touch case; a future
  combined weapon would follow the accepted whole-attack reading.
- **B6 — no immunity inferred:** no heart-imagery immunity exists in the code
  path; the extra is modelled as an ordinary wound with the attack's defenses,
  consistent with the accepted ruling.
- **B7 — synthetic result:** the extra passes
  `phases.WoundResult(0, 0, True, False)`; `wound.roll`/`target` are never
  requested or consumed (`single_wound` path), verified by strict dice, so no
  hidden roll exists. A dedicated single-wound entry point would read better but
  would not change behaviour.

No high- or medium-severity finding was reproduced.

## 9. Proposed register entry (complete text; coordinator assigns the ID)

The next free identifier appears to be beyond `T13-F055`; the coordinator owns
the actual assignment and insertion into
[T13-execution-follow-ups.md](T13-execution-follow-ups.md).

```text
### T13-F0xx — Spectral Touch pool fixtures cannot distinguish per-hit provenance

- **Status/type:** open; evidence gap (test corpus), no observed implementation
  defect. Detected in the F007 independent implementation review.
- **Affected entities:** tests/python/combat/modular/test_spectral_touch.py
  (pool and public replay fixtures); modular/pools.py provenance transport.
- **Observed behaviour:** an isolated in-memory mutant that gives every prepared
  hit the whole-pool flag (natural_hit_six = any(prepared.natural_hit_six))
  passes all 57 maintained Spectral Touch cases; maintained multi-hit fixtures
  are all-six or contain only misses, and the trigger requires hit.success.
  The real engine and the review's mixed probe (hits 6 and 5) correctly attribute
  the extra to the six only.
- **Evidence:** build/cache/t13-parallel/spectral-touch-independent-review/
  mutant_plugin.py, mutant-pooled-suite.log (57 passed), probe.py
  (mixed_pool_provenance), probe.json.
- **Action/target:** add one deterministic witness to the Spectral suite: a
  two-hit pool where hit 0 is a natural six and hit 1 hits with a non-six face,
  both ordinary wound rolls failing, strict dice; optionally an isolated
  pooled-provenance mutation expectation next to the two existing mutation cases.
- **Resume:** with the next authorized edit of the Spectral suite (F007 follow-up
  or the F008 canonical-activation lot). No production change required.
- **Close when:** the new witness fails under the isolated pooled-provenance
  mutant and passes on the current engine.
```

## 10. Dictamen

**Recommendation: accept F007's modular repair and the accepted-Q019 modular
implementation, bounded to the modular oracle.** All four accepted rulings are
implemented and independently verified: one extra contribution with inherited
saves/injury context and a hard cap, immediate injury/rescue/reactions before
ordinary continuation with correct interruption, collective pool preparation,
and the R4 whole-attack Barrage prerequisite that suppresses the decision even
when the extra was saved. Fresh focal evidence (101 passed), a fresh broad run
(432 passed, 0 removed), independently replayed strict fixtures and the retained
red/green evidence support the delivery; other consumers of the common wrapper
are unchanged.

Acceptance is limited to the modular implementation and must not be read as:
canonical activation or source-linked specification (F008), optimized backend
support (F009), every legal equipment/defense composition, or F040 coverage
reconciliation. Finding F1 is a low-severity evidence gap; it does not refute
the implementation and is proposed as a register entry rather than a return.

No return and no partial acceptance are warranted by this review.

## 11. Limits of this review

- Not a canonical-loadout or source-to-compilation certificate; injected-tag
  fixtures only.
- No NumPy/native execution, no parity/truncation/statistical run, no native
  rebuild.
- The coverage gate and mutation catalogue were read, not re-run; F040 keeps its
  own review. The default full-corpus catalogue remains uncertified by the
  delivery itself.
- The four external PDFs were hash-verified and their retained extracted text
  read; no new download was attempted.
- Line numbers refer to the hashed revision in §2; the working tree is shared
  with concurrent lots and may move after this review.

## 12. Evidence inventory

`build/cache/t13-parallel/spectral-touch-independent-review/`:

- `capture.py`, `entry.json`, `closing-hashes.json`, `capture.log` — input
  hashes before and after the review; drift NONE.
- `reproduced-attacks.diff`, `reproduced-test.diff`, `patchcheck/`,
  `patchcheck-a/`, `patchcheck-*.log` — independent reproduction of the
  incoming→live change.
- `focused.xml/.log/.exitcode.txt`, `broad.xml/.log/.exitcode.txt` — fresh
  pytest runs.
- `probe.py`, `probe.json`, `probe.log` — mixed provenance, Barrage decision
  suppression, independent mutant replay.
- `probe_provenance_detector.py`, `probe-provenance-detector.json/.log` —
  pooled-provenance experiment.
- `mutant_plugin.py`, `mutant-pooled-suite.log` — maintained suite under the
  pooled-provenance mutant (finding F1).

Handoff: this review is delivered for coordinator acceptance. No agent was
launched, no commit or push was made, and no shared state was edited. F008 and
F009 remain separate; F007 remains in review until the coordinator accepts.

## 13. Coordinator acceptance — 2026-10-02

**Accepted for the modular oracle.** The external implementation review satisfies
the separate-reviewer barrier for F007. The coordinator performed bounded checks
of integrity, actual test identities and strict behavior; no product code, test,
source, specification, budget or optimized engine was changed. No agent was
launched and no commit or push was made.

Evidence: `build/cache/t13-parallel/spectral-touch-coordinator-acceptance/`
contains `check.py` and `coordinator-review.json`. Fifteen examined input hashes
(excluding the two shared coordination documents) match review entry, and all
three incoming/repair evidence hashes match. Retained XML confirms 101 focal
and 432 broad passes, with all 405 prior broad identities retained. These test
runs are the external review's evidence, not a fresh coordinator suite rerun.

Fresh coordinator probes independently exercise the mixed six/non-six successful
hit pool, saved/unsaved extra-wound Barrage suppression with no decisions, the
two isolated predicate mutations and the pooled-provenance mutation. The correct
engine gives damage `[1, 0]` and defender W4->W3; the pooled mutant is detected
because it gives the non-six hit an extra wound. No original evidence script's
file-writing main entry point was invoked or evidence overwritten.

**Broad-count attribution erratum:** sections 6/7 and the external handoff
attribute all 27 added cases to the profile-save lot. Independent XML identity
comparison shows **24** `test_profile_save_thresholds` cases and **three**
`test_t13_coverage_boundaries` cases. The 432 total and zero removals are correct.
The first coordinator check also adopted the inaccurate all-profile expectation
and failed; the raw identity comparison resolved that discrepancy before the
corrected check passed. This correction does not accept F040's gate changes.

Finding F1 is registered as **T13-F056**, assigned to the next reserved F008 lot
before its acceptance, or an earlier separately dispatched test-only lot. Its
executor remains unassigned; the maintained detector gap remains open. The
reviewed implementation is correct on the independent witness, so that narrow
gap does not prevent the bounded F007 acceptance.

F007 is resolved for modular implementation only; its reservation is released.
F008 is eligible for source-linked canonical activation, while F009 remains
dependent on canonical/modular stability. Legal loadouts, foreign printed-save
compositions, Spirit Knife, F040 coverage reconciliation and T13/T14 certification
are not closed by this acceptance. Earlier pending F007 statements are historical.
