# T13-F040 — Independent review: modular coverage reconciliation and trustworthy measurement

Status: independent review delivered; **recommend acceptance of the F040
delivery at its reviewed revision** (section 8). Acceptance and register edits
belong to the coordinator; F040 remains open here. This review does not accept
either semantic pilot, canonical activation, optimized engines or T14/T15.

## 1. Scope, entry and permissions

Entry captured 2026-10-02 05:55 UTC on branch `2A2B`, HEAD
`1b7f7cf10b75a9d716c34c64039f5c908caed19e`, with 253 dirty worktree entries
belonging to other lots (entry status retained verbatim in
`build/cache/t13-parallel/coverage-independent-review/entry/git-status.txt`).
No `AGENTS.md` exists in the repository or its parent directory; the applicable
instructions were the initiative README, the T13 documents listed below, and
the delivery's own boundaries.

Writable outputs used by this review: this document and
`build/cache/t13-parallel/coverage-independent-review/**`. Every production
file, maintained test, budget and shared document was read-only. No live-budget
update was executed at any point; every writer probe used temporary budgets
inside the evidence directory. No threshold was changed, no budget was
regenerated, no agent was launched, and no commit or push was made.

Mandatory consultation performed: [initiative coordination](../README.md)
(including the review protocol and the F040 reservation),
[F040 register entry](T13-execution-follow-ups.md#t13-f040--modular-coverage-line-budget-needs-reconciliation-after-pilots),
[remaining T13–T15 plan](T13-T15-remaining-plan.md),
[delivery and reconstruction](T13-coverage-reconciliation.md),
[T13.1 contracts](T13-contracts.md), [Shifty](T13-shifty.md), the
[accepted R4 repair](T13-spectral-touch.md#accepted-r4-modular-repair--2026-10-01)
and [verification reference](../../../reference/verification.md).

### 1.1 Entry hashes of the reviewed inputs

| Input | SHA-256 |
| --- | --- |
| `apps/combat-lab/mordheim_combat_lab/verification/coverage_gate.py` | `201e6f564286445ec558cf5be146ae0a292941f0cd66497d056ca0378ed32a3d` |
| `apps/combat-lab/mordheim_combat_lab/cli/commands.py` | `18445492010a868c9ae348da955db97435ae1f0e658e97ab5cf8ed2c9321f2d9` |
| `tools/mordheim-utils.py` | `2ed7f4c5692bcdc99a90eda3d4c7dc6e7fb1cf67ef649a94f532b3fa2e11ac41` |
| `tools/verification/update-coverage-budget.py` | `0dfb4232cd2e42a5ebc6e73c22e66ae9146cf44e5e10813fde068b3f362a90c1` |
| `tests/fixtures/coverage/budget.json` | `30d96c61ab04292fa7f2f9811ce04af772e97aa7fc7c2af763d89a66bc3d0d30` |
| `tests/python/verification/test_coverage_gate.py` | `42a67be36630de2afc800bde3c7190e3752f57ca99e5399ee3e6ecd4553a634f` |
| `tests/python/cli/test_umbrella.py` | `65cdd5fd83e256bf522b00c96754a07eea9bc1e06b6df3a9c261d45bbcb38b12` |
| `tests/python/combat/modular/test_t13_coverage_boundaries.py` | `b199013c780d6ad675eb4012c48754978a5b725de56ab302227544b2fba9593e` |
| `packages/.../modular/attacks.py` (protected) | `55e05e32046a15428d43085195563ee471b07eb90be1cebeb59f6c9c444b6ef6` |
| `packages/.../modular/pools.py` (protected) | `567a9636f7ac652d404c3c6cc09e6fb3748249dd5b6ee855005c30a25f669a0a` |
| `packages/.../modular/rounds.py` (protected) | `d444f5a37b3e43f5e0c99febb6636b1a9ad5021216ac7a4115084807a3a0c11f` |
| `packages/.../modular/state.py` (protected) | `69b7c2934fdcd53039a8e7ac64bfdff0f4c056ae851ee900afe14c79916c76aa` |

Every F040-owned file still equals the delivery's `closing.json` hashes
(including the delivery document `6a0cfb0c…`), the four protected engine files
are byte-identical to entry, and the live budget is untouched
(`30d96c61…`) after the whole review. All 61 retained evidence files still match
`coverage-reconciliation/evidence-index.json` (0 mismatches, 0 missing);
the retained source copies and reports were therefore used as immutable
artifacts, not regenerated.

### 1.2 What the delivery changed (independently diffed against retained incoming copies)

- `coverage_gate.measure_coverage` now keeps `pytest.main`'s return value,
  raises `RuntimeError` unless it equals `pytest.ExitCode.OK`, and keeps
  `cov.stop()` in the pre-existing `finally`;
- the CLI catches that `RuntimeError` (exit 1), evaluates requested floors
  **before** writing on `--update-budget`, and prints the update confirmation
  only when the result passed. Both update entry points still write only after
  a successful measurement;
- `tools/mordheim-utils.py` `deterministic` scope adds exactly
  `tests/python/combat/test_duel_context.py` and
  `tests/python/verification/test_duel_replay.py`, matching the gate's
  six-suite list (the equality test in `test_umbrella.py` now passes);
- `tests/fixtures/coverage/budget.json` differs only in the four modular
  arrays `attacks` (203→224), `pools` (170→173), `rounds` (162→214) and
  `state` (112→113). Schema, `suites`, area keys, all other module arrays and
  the phases/vectorized arrays are byte-equal; no floor value is stored or
  changed anywhere;
- the new boundary suite and the strengthened coverage regressions are the only
  test additions.

## 2. Independent requirement reconciliation

### 2.1 Method

Nothing was accepted from counts or from the retained summaries. The six
hundred and forty-seven incoming requirements were re-mapped by **instruction
identity**:

1. statement executability from coverage's own parser
   (`coverage.parser.PythonParser`) on the reconstructed origin sources and on
   the reviewed current sources;
2. whole-file sequence alignment (`difflib.SequenceMatcher`, indentation
   normalized, no autojunk) between origin and current sources, so repeated
   lines are mapped by global alignment instead of per-occurrence guessing;
3. per-record comparison against the retained
   `reviewed-statement-dispositions.json` (used only as a cross-check);
4. AST function-ownership transitions and coverage state (initial 519-test
   report, boundary report, final 522-test report).

A first per-line, scope-and-order variant produced 17 disputed repeated-line
alignments; all 17 were resolved by the whole-file alignment and spot-checked
against the source context (for example, attacks old 222 is provably the
infection `f"{key}.infection-wound"` block at current 253, not the earlier
`aftermath` import at 210). The final mapping has **zero disagreements** with
the retained per-record dispositions.

### 2.2 Result

- Incoming requirements: **647** = attacks 203 + pools 170 + rounds 162 +
  state 112. The incoming budget is byte-identical, array by array, to the
  accepted T13.1 coverage report (`build/cache/t13-1/accepted-coverage.json`);
  the comparison covered all 18 measured modules with zero differences.
- **640 same-instruction mappings**, all targets distinct (one-to-one) and all
  covered by the final report. This includes the three instructions that gained
  pilot guards and moved under new branches: attacks 304→357, 306→359 and
  pools 199→205.
- **Seven covered replacements**, exactly in alignment blocks with genuinely
  changed instructions and confirmed absent at their old text:
  attacks 50→54 (`secondary_outcomes`→secondary-wound condition),
  attacks 51→55 (reacted damage), attacks 56→60 (Barrage guard includes
  established wound), pools 160→163 (eligibility also requires an active
  defender), pools 192→197 (`elif use_body_slam` under the single-bonus
  branch), pools 332→341 (Anvil Head excludes single-bonus attacks),
  rounds 19→19 (equipment import gains `is_pistol`). Each replacement target is
  exercised in the final report and in the committed budget, and none collides
  with a same-instruction target. Their **tabletop semantics remain under
  F003/F007 review**; this review only confirms identity, changedness and
  exercise.
- Exactly **one** mapped target is uncovered by the initial 519-test run:
  attacks old 84 → current 90, the inactive-participant guard. The
  three-case boundary run adds exactly that one engine statement
  (verified: `reviewed-union == measurement ∪ boundary`, boundary-only line
  `mordheim_combat.modular.attacks:90`), and the committed budget equals the
  union and the final measured arrays for the four modules and for every other
  module.
- Raw-index drift: **217** incoming indexes are not covered at the same numeric
  position by the initial run (attacks 86, pools 60, rounds 55, state 16).
  **208** of them are no longer executable statement lines in the current
  sources; the remaining **nine** are executable lines that now hold a
  *different* instruction. All nine original instructions remain exercised:
  attacks 90→96, 289→339; pools 306→314, 309→317, 312→320, 313→321;
  rounds 74→75, 106→107, 128→129 — all covered by the initial run at the mapped
  line. This reproduces the retained `nine-executable-index-review.json`
  exactly.
- Function moves: the only ownership transitions among all 640 same-instruction
  mappings are the **47** wound/save statements moving from
  `_resolve_reference_attack_once` to `_resolve_wound_damage` in attacks; no
  mapping moves into an unrelated function (0 transitions in pools, rounds and
  state).
- Scope fix: the incoming gate already used the six suites; the umbrella's
  `deterministic` scope omitted `test_duel_context.py` and `test_duel_replay.py`
  and now matches, with no other scope path added or removed.

### 2.3 Source reconstruction and its limits

| Module | Origin basis | Independent check |
| --- | --- | --- |
| attacks | HEAD, unchanged by T13.1 | `budget-origin/attacks.py` = `git show HEAD` = T13.1 entry copy = `spectral-touch/entry.json` (`6450e139…`) |
| pools | HEAD, unchanged by T13.1 | `budget-origin/pools.py` = `git show HEAD` = T13.1 entry copy (`c3919373…`) |
| rounds | HEAD plus the two T13.1 context hunks | `budget-origin/rounds.py` (`745f23f6…`) = retained pre-Shifty entry hash in `build/cache/t13-parallel/entry-files.json`; the diff against HEAD is exactly the two context hunks (`initial_charge_flags`, `replace(state, …)` carry) |
| state | retained pre-Spectral source | `budget-origin/state.py` (`cbdd6446…`) = `entry-files.json` pre-Spectral entry = `spectral-touch/entry.json`; the diff against HEAD is exactly the T13.1 context fields |

The declared pools limit is real: pools has no *separately retained pre-pilot
hash* because the file did not change between HEAD and the pilot entry (it is
absent from `entry-files.json` precisely for that reason). The alternative
evidence is nevertheless strong: byte identity with the frozen `git show HEAD`
object and with the retained T13.1 entry copy, plus the incoming budget being
exactly the accepted T13.1 measured report. I therefore consider the pools
reconstruction adequately anchored, without claiming a hash record that does
not exist.

## 3. Measurement and writer contracts — adversarial verification

All probes used temporary budgets under the evidence directory; the live budget
was never an argument. Real entry points were exercised in subprocesses, and
tracing cleanup was additionally proven in-process with the real coverage
object and a real failing detector.

| Contract | Probe | Result |
| --- | --- | --- |
| Any pytest exit other than success invalidates measurement | real suites: failure (1), collection error (2), internal error (3), invalid invocation (4), empty collection (5), each through CLI check, CLI `--update-budget` and the standalone updater | all refused; `RuntimeError`/error message names the exit code; no report produced |
| Tracing cleanup even on failure | in-process fake for exits 1–5; `KeyboardInterrupt` propagation; then a **real** failing detector followed by a **real** passing measurement in the same process | `coverage.stop` called in every case; after the real failure `Coverage.current() is None`; the next real measurement returns the expected 1 457 vectorized statements; no leaked tracing |
| CLI and updater preserve exact budget bytes when measurement fails | 5 statuses × 3 entry points (15 runs), byte hashes compared before/after | bytes byte-identical in all 15; no ` updated` confirmation; updater prints no `BUDGET:` line |
| Unmet requested floor must not overwrite nor confirm | passing partial detector with `--update-budget --area-floor modular:100`; also the pure check with the same floor | update: exit 1, bytes unchanged, `below the 100.00% floor`, no confirmation; check: exit 1 with the same failure line, bytes unchanged |
| Legitimate update path still works | same detector with `--area-floor modular:0` | exit 0, budget written, `BUDGET: … updated` printed (positive control) |
| Restored inactive-participant obligation | independent reproduction on both removed sides plus an isolated guard-removal mutation | no dice/decisions requested, all state fields unchanged, no hit/wounded/Barrage/damage; the mutation (guard count 1, removed in an isolated namespace) is detected as `unexpected roll removed.hit D6` |

Note: `tools/verification/update-coverage-budget.py` has no `--area-floor`
option by design; its preservation contract applies to measurement failure,
which was exercised for all five statuses. The floor guard exists only in the
CLI, which is the entry point that accepts floors.

## 4. Retained evidence, freshness and the fresh gate run

The retained final gate (`coverage-reconciliation/final-gate.json`, real log
`final-gate.log`) is internally consistent: 522 passed in 703.17 s, exit 0,
zero drift errors, modular 97.28 % (1071/1101), vectorized 93.75 %
(1366/1457), phases 96.94 % (538/555); every measured array equals the
committed budget; the report's evidence hashes all verify.

**It cannot be reused for the current tree.** Input comparison found that
`tests/python/combat/modular/test_profile_save_thresholds.py` was modified at
2026-10-01 18:45 and `tests/specs/semantic/grants/` at 18:58–19:13, i.e. after
the 15:22 final gate; both are inputs of the measured suites. Per the review
instructions I therefore ran the current read-only gate:

```text
python -X utf8 tools/mordheim-utils.py coverage-gate --json --area-floor modular:95 --area-floor vectorized:93
```

Result on the current working tree: **1 failed, 545 passed in 445.75 s**, exit
non-zero, with

```text
tests/python/verification/test_parity.py::test_semantic_specs_are_reused_as_a_case_level_parity_inventory
AssertionError: assert 3758 == 3743
```

The CLI refused the measurement (`Coverage gate error: deterministic coverage
tests did not pass (pytest exit code 1)` in `entry/fresh-gate.stderr.txt`) and
left the live budget byte-identical. The refusal is the intended fail-closed
behaviour; the failure itself is **external to F040** (finding F-01).

The provided validation command passes fresh:

```text
python -X utf8 -m pytest tests/python/verification/test_coverage_gate.py tests/python/cli/test_umbrella.py tests/python/combat/modular/test_t13_coverage_boundaries.py -q -p no:cacheprovider
52 passed in 4.84s
```

## 5. Findings

### F-01 — Current tree: deterministic gate red on a stale parity inventory count (external blocker)

- **Location:** `tests/python/verification/test_parity.py:39-41`
  (`assert len(report.cases) == 3743`, `len(report.passed) == 3743`).
- **Impact:** the full deterministic gate (and therefore any coverage
  measurement, budget update or T14 certificate) cannot pass on the current
  tree. The measurement is refused, so no invalid data is published; but no
  fresh green full-gate result exists for the current revision.
- **Cause (verified):** the two source-linked specs of the accepted
  Fimir/Boglar lot (`tests/specs/semantic/grants/t13-fimir-scaly-skin.yaml`,
  8 cases, and `t13-boglar-regeneration.yaml`, 7 cases) were added at 19:13 on
  2026-10-01, after F040's gate; the current corpus yields 3758 = 3743 + 15.
  `test_parity.py` itself is unmodified since 2026-09-08.
- **Reproducer:** run the gate command in section 4, or
  `python -X utf8 -m pytest tests/python/verification/test_parity.py -q` and
  observe `3758 == 3743`.
- **Owner:** the lot that added the specs (R2/R3 profile-save-thresholds
  acceptance) or the coordinator integrating it; not F040. Any repair must
  update or derive the inventory expectation without weakening the test.

### F-02 — Update-path floor protection is CLI-only (documented design limit)

The standalone updater has no `--area-floor`; the "unmet floor does not
overwrite" guarantee holds for the CLI only. This matches the existing tool
design and the F040 claims; recorded so the contract is not misread as global.

### F-03 — Budget writes are not atomic (residual hardening proposal)

`write_budget` writes the destination directly (`Path.write_text`). A crash or
I/O error *during* the write could leave a truncated budget; this is outside
the reviewed "invalid measurement" contract but worth hardening with a
temporary file plus atomic replace.

### F-04 — Pools basis documentation understates the available anchor (minor)

The delivery correctly declares "no separately retained hash" for pools, but
does not mention the stronger available evidence: byte identity with
`git show HEAD` and with the retained T13.1 entry copy, and absence from
`entry-files.json` exactly because the file was unchanged. A coordinator note
would remove the ambiguity (section 2.3).

### F-05 — Regression suite does not pin real statuses 2–5 or tracing cleanup (coverage gap)

The maintained regressions pin exit 1 through real subprocesses, the other
statuses through a monkeypatched `pytest.main`, and the floor preservation
through a real subprocess; tracing cleanup and real statuses 2/3/4/5 were only
proven by this review's probes. Adding a compact parametrized real-status case
and a `Coverage.current() is None` assertion would make the contract
regression-proof.

## 6. Fresh versus reused evidence

- **Fresh (produced by this review):** input hashes and status capture; diff of
  the delivery against retained incoming copies; independent whole-file mapping
  of all 647 requirements; function-transition analysis; raw-index
  classification; union/boundary verification; full evidence-index
  verification; 21 real subprocess writer probes plus in-process and real
  tracing-cleanup probes; inactive-participant state probe and mutation;
  provided validation run (52 passed); the current read-only full gate run
  (546 tests; 1 failed) and its failure diagnosis.
- **Reused (retained, verified intact):** the accepted T13.1 coverage report
  for array identity; the initial 519 measurement, boundary measurement, union
  and final 522 reports for coverage state; `entry-files.json` and
  `spectral-touch/entry.json` for pre-pilot hashes; the retained
  per-record dispositions as a cross-check only. Reuse was justified because
  each artifact still matches its recorded hash and because the review
  recomputed the claims from the sources rather than trusting the artifacts.
- **Not reusable:** the 522-test/zero-drift result for the *current* tree, due
  to the post-gate spec/test changes (section 4). The F040 revision's claims
  remain supported by its own artifacts; the current tree needs the F-01
  repair before any new full-gate claim.

## 7. Limits and non-claims

- This review did not revert or alter any concurrent lot to re-execute the
  F040 revision end to end; the revision's full-gate result was examined as
  retained evidence and its inputs were independently validated, while the
  current-tree re-run is blocked by F-01.
- The seven replacement obligations were verified as changed, exercised and
  one-to-one; their semantic correctness is not certified here (F003/F007).
- Coverage acceptance does not accept Shifty/Spectral Touch semantics,
  canonical activation (F004/F008), optimized ports (F006/F009), F001 source
  pins, T14 certification or T15 closure.
- The 640 same-instruction mapping rests on normalized-text sequence alignment
  plus function ownership; identical text in the same function would be
  indistinguishable by this method, so the retained per-record dispositions
  and the complete diff remain part of the chain of evidence.

## 8. Recommendation

**Recommend acceptance of the F040 delivery at its reviewed revision**
(HEAD `1b7f7cf` plus the captured dirty inputs). All original-requirement
claims reproduce independently (647 = 640 same-instruction + 7 exercised
replacements; one-to-one; 217/208/9 raw-index classification; exactly one
restored witness; only the four authorized modular arrays changed; metadata,
suites and floors preserved), and the fail-closed measurement/writer contracts
were verified adversarially through the real entry points, including tracing
cleanup, byte preservation and floor gating.

**Boundary of the recommendation:** the F-01 stale parity inventory must be
repaired by its owner before any fresh full-gate, T14 or release-level result
can be claimed on the current tree. The F040 delivery itself does not need to
change for that; F-03–F-05 are optional hardening/documentation follow-ups.
F040 should stay open until the coordinator records acceptance.

## 9. Proposed follow-ups for the coordinator

- **P1 (blocker):** register a follow-up for F-01 — "parity inventory count
  stale after the T13 Fimir/Boglar specs (3758 vs 3743)" with the reproducer,
  and route it to the accepting lot. Do not weaken the assertion; update or
  derive the count and re-run the gate.
- **P2:** record F040 acceptance in the register and release the review
  reservation, referencing this review's evidence directory and the hashes in
  section 1.1.
- **P3 (optional):** atomic budget writes (temporary file + replace) in
  `write_budget` to remove the F-03 truncation risk.
- **P4 (optional):** extend `test_coverage_gate.py` with real subprocess cases
  for statuses 2/4/5 and an explicit `Coverage.current() is None` cleanup
  assertion (F-05).
- **P5 (optional, coordinator-owned):** annotate the pools reconstruction limit
  in the delivery with the HEAD byte anchor and the `entry-files.json`
  absence rationale (F-04).

## 10. Evidence index

All paths are under `build/cache/t13-parallel/coverage-independent-review/`.

- `entry/head.txt`, `entry/git-status.txt`, `entry/inputs.sha256.txt` — entry.
- `entry-vs-current.diff` — delivery diff against retained incoming copies.
- `entry/focused-validation.txt` — provided validation suite, 52 passed.
- `entry/fresh-gate.json`, `entry/fresh-gate.stderr.txt` — current read-only
  gate run and its refusal message.
- `entry/adversarial-probes.txt` — subprocess and in-process probe transcript.
- `analysis/structure_check.py` → `structure-check.json` — evidence index,
  budget structure, T13.1 array identity, report comparisons.
- `analysis/remap.py` → `remap.json`, `analysis/remap_v2.py` → `remap-v2.json`,
  `analysis/remap_v3.py` → `remap-v3.json` — three independent mapping
  variants (the disputed per-line alignments and the final diff-based result).
- `analysis/union_check.py` → `union-check.json` — boundary/union/budget.
- `analysis/adversarial_probes.py` → `analysis/adversarial/results.json` and
  `analysis/adversarial/floor-check-cli.txt` — writer probes.
- `analysis/tracing_cleanup_real.py` → `tracing-cleanup-real.json` — real
  tracing cleanup.
- `analysis/boundary_probe.py` → `boundary-probe.json` — inactive-participant
  state and mutation probe.

## 11. Coordinator acceptance — 2026-10-02

**Accepted at the reviewed F040 repair revision; no current full-gate certificate.**
The external independent review satisfies the separate-reviewer requirement.
Evidence and bounded coordinator checks are retained under
`build/cache/t13-parallel/coverage-coordinator-acceptance/` (`check.py`,
`coordinator-review.json`, fresh `focused.xml`). The 52 focal tests pass again.

The coordinator verified all 61 delivery evidence hashes, exact four-array
budget scope and equality with the historical final measured arrays, and pools
origin byte identity with HEAD. The documented absence of a separately captured
pre-pilot pools hash is preserved; its HEAD/T13.1 anchors support the accepted
reconstruction. The complete 647-instruction remapping and real writer probes
remain the external review's evidence; no full expensive rerun was repeated.

**Concurrent input drift:** `cli/commands.py` now hashes
`4d5e3e5fb459a9034803bd0eb87321ab49035b90649b3349e6f8e737db8f844a`
instead of the reviewed `18445492010a868c9ae348da955db97435ae1f0e658e97ab5cf8ed2c9321f2d9`.
The difference concerns audit outputs/parser options outside F040. The coverage
handler was reconstructed from retained incoming code plus the three F040 hunks
and is text-identical to the current handler. The other eleven reviewed
code/test/budget inputs match. Audit changes are preserved and are not accepted
by this lot. The initial strict full-file check detected the drift before this
targeted proof; no live file was restored or overwritten.

The coordinator independently loaded **3758** cases and identified the new
eight Fimir/seven Boglar cases, while the parity test still expects 3743. The
independent review's current gate failure/refusal remains valid blocker evidence;
the historical 522 passes cannot be cited as current validation.

Proposal disposition: P1/F-01 becomes **F057**, reserved for a minimal external
parity-inventory repair and fresh read-only gate. P2 is this acceptance and
reservation release. P3 becomes optional **F058** atomic-writer hardening; P4
becomes optional **F059** maintained real-status/cleanup regressions. P5 is
resolved by the explicit pools anchor note above; no additional source hash is
invented. F-02's standalone floor limitation remains a documented tool boundary.

F040 is resolved for requirement reconciliation and fail-closed behavior. F057
is the active current-gate blocker; no budget was updated, no current full gate
was certified, and no semantic/canonical/backend/T14/T15 status was closed.
No code, maintained tests, sources or specifications were changed; no agent was
launched, and no commit or push was made.
