# T13-F040 — Coverage reconciliation and trustworthy measurement

Status: coverage repair independently accepted on 2026-10-02 at its reviewed
revision. The original 522-test gate is historical; the current full gate is
blocked by F057's stale parity count (1 failed / 545 passed), and measurement
is correctly refused. [Review and acceptance](T13-coverage-independent-review.md#11-coordinator-acceptance--2026-10-02).
This lot repairs the existing verification gate and reconciles
its current modular statement indexes. It does not accept either semantic pilot,
activate canonical rules, or certify T13/T14.

## Inputs, ownership and references

- Entry: branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`, plus
  the dirty inputs hashed in `coverage-reconciliation/entry.json`.
- Coordination: [active reservations and review protocol](../README.md),
  [remaining integration plan](T13-T15-remaining-plan.md), and
  [F040](T13-execution-follow-ups.md#t13-f040--modular-coverage-line-budget-needs-reconciliation-after-pilots).
- Existing machinery: [coverage module](../../../../apps/combat-lab/mordheim_combat_lab/verification/coverage_gate.py),
  [CLI](../../../../apps/combat-lab/mordheim_combat_lab/cli/commands.py),
  [umbrella launcher](../../../../tools/mordheim-utils.py),
  [standalone updater](../../../../tools/verification/update-coverage-budget.py),
  [budget](../../../../tests/fixtures/coverage/budget.json), and
  [verification guidance](../../../reference/verification.md).
- Prior evidence: [accepted T13.1 context](T13-contracts.md),
  [Shifty pilot](T13-shifty.md), and
  [Spectral Touch R4 repair](T13-spectral-touch.md#accepted-r4-modular-repair--2026-10-01).

Reserved edits are the existing coverage measurement and narrow CLI handler,
the umbrella deterministic suite list, coverage tests, the existing budget,
one new modular boundary witness, and pertinent documentation. Incoming engine,
pilot-test, compiler and external context-manifest hashes are protected. No
optimized engine, source pin, KB, eligibility or Warband Manager edit is included.

## Findings and repairs

### Failed pytest runs previously produced accepted measurements

`measure_coverage()` discarded `pytest.main()`'s return status. Real failing
detectors passed the CLI gate and overwrote destination budgets through both
the CLI update and standalone update script. The same invalid path existed for
interruption/collection errors, internal errors, invalid invocation and empty
collection. A coverage report from any of these runs is invalid.

The existing measurement now requires pytest's successful exit, stops tracing
in its existing `finally` block, and raises a diagnostic before constructing
the report on other exits. The CLI returns failure. Both update entry points
leave the previous budget bytes intact when measurement fails.

A separate reproduction showed that `--update-budget --area-floor ...` wrote
the budget before checking the requested floor. The CLI now checks floors
first, writes only on success, and prints an update confirmation only after
success. Neither floor values nor drift requirements are weakened.

[Coverage regressions](../../../../tests/python/verification/test_coverage_gate.py)
retain the original tests and add all five invalid pytest statuses, three real
failing-detector subprocess entry points, and a real passing detector whose
requested coverage floor fails. Before the repair, the first group produced
eight regression failures; the floor-preservation witness failed separately.

### Umbrella deterministic scope omitted existing context/replay suites

The coverage gate's accepted incoming six-suite list already included duel
context and public replay. The umbrella's deterministic scope omitted them.
Its existing suite-equality test reproduced the discrepancy. Only those two
missing paths were added to the launcher; incoming unrelated launcher changes
were preserved. The existing equality test now passes.

### Raw index drift concealed one genuine missing witness

The initial real measurement passed 519 tests but failed the incoming drift
budget at 217 numeric positions: attacks 86, pools 60, rounds 55, state 16.
Of these positions, 208 were no longer executable statement indexes. The nine
remaining positions addressed different current instructions, while their
original budgeted instructions remained exercised elsewhere:

| Module | Old budget index | Current index of the original instruction |
| --- | --- | --- |
| attacks | 90 | 96 |
| attacks | 289 | 339 |
| pools | 306 | 314 |
| pools | 309 | 317 |
| pools | 312 | 320 |
| pools | 313 | 321 |
| rounds | 74 | 75 |
| rounds | 106 | 107 |
| rounds | 128 | 129 |

This numeric classification alone was insufficient. Mapping all the original
covered instructions exposed an actual lost witness: attacks **old 84 → current
90**, the early return when either participant is inactive. A fresh attack
against a removed fighter must leave both states unchanged and request no dice,
decisions, damage or Barrage.

[The new boundary suite](../../../../tests/python/combat/modular/test_t13_coverage_boundaries.py)
tests removal on each side with empty strict dice/decision scripts. An isolated
in-memory mutation removes the actual guard and demonstrates that this witness
detects the unexpected request. The engine source is never edited by the test
or this lot. Three cases pass; their measured engine coverage restores exactly
one statement, current attacks line 90.

## Source reconstruction and budget disposition

The incoming budget matches every covered-line array in the retained accepted
T13.1 coverage report, `build/cache/t13-1/accepted-coverage.json`.
The corresponding four source files are recovered as follows:

| Module | Origin source basis | Identity check |
| --- | --- | --- |
| attacks | HEAD, unchanged by T13.1 | SHA-256 matches retained pre-Spectral entry |
| pools | HEAD, unchanged by T13.1 | T13.1 status/diff inspection; no separately retained hash |
| rounds | HEAD plus the two retained T13.1 context hunks | SHA-256 matches retained pre-Shifty entry |
| state | Retained pre-Spectral source | SHA-256 matches its retained entry |

Line matching supplies candidates, not semantic acceptance. The full old/current
diff and AST function ownership were inspected: 47 wound/save instructions
move from `_resolve_reference_attack_once` to `_resolve_wound_damage`; no
matches move into unrelated functions. The 647 incoming budget requirements
in these modules are accounted for by **640 same-instruction matches and seven
covered replacements**. The recovered inactive-participant witness is one of
the 640 same-instruction matches, not an additional original requirement.
The mapping is one-to-one. Three retained instructions gain additional pilot
guards: attacks old 304/306 → current 357/359 execute in the non-single-wound
branch, and pools old 199 → current 205 executes in the non-single-bonus
branch. Those normal attack instructions remain exercised; the added guards
remain part of the pilots' separate semantic review.

| Changed original instruction | Reviewed current covered replacement |
| --- | --- |
| attacks 50: secondary-outcome condition | 54: cumulative secondary-wound condition |
| attacks 51: secondary damage replacement | 55: cumulative reacted damage replacement |
| attacks 56: Barrage continuation guard | 60: includes established wound prohibition |
| pools 160: pool eligibility guard | 163: also requires an active defender |
| pools 192: Body Slam branch | 197: follows single-bonus weapon branch |
| pools 332: Anvil Head condition | 341: excludes single-bonus attacks |
| rounds 19: equipment import | 19: includes `is_pistol` |

These changed instructions belong to the existing pilots; checking that they
are exercised does not accept their tabletop interpretation. Their semantic
review and activation barriers remain in their own follow-ups.

The reviewed candidate budget was written with the existing `write_budget()`
API from the union of two real measurements: the full 519-test run and the
three-case boundary run. Only the four modular arrays differ from the incoming
budget; every other modular array, vectorized/phases arrays and suite metadata
remain identical. A fresh full CLI gate is required below to verify this
candidate against all suites together. The independent floors stay modular
95% and vectorized 93%.

The final fresh CLI measurement passed **522 tests in 703.17 seconds**, with
zero drift errors and both requested floors met. Every final measured covered
array equals the reviewed candidate budget. Final areas: modular **97.28%
(1071/1101)**, vectorized **93.75% (1366/1457)**, phases **96.94% (538/555)**.

## Validation and retained evidence

Evidence directory: `build/cache/t13-parallel/coverage-reconciliation/`.
It is supporting evidence, not a required runtime input. The findings, source
basis, regression behavior and update procedure above are reconstructible from
maintained files and the existing APIs.

| Check | Result |
| --- | --- |
| Initial complete measured default suites | 519 passed; old drift fails at 217 indexes |
| Coverage/umbrella/boundary focused verification | 52 passed; real `focused.xml` |
| Boundary-only measured run | 3 passed; only newly covered engine statement is attacks 90 |
| Fresh CLI drift gate and original area floors | Exit 0; 522 passed; zero drift errors; modular 97.28%, vectorized 93.75%, phases 96.94% |
| Documentation links and whitespace | 1 passed; owned diff/text checks clean |
| Protected incoming engine, pilot-test, compiler and manifest hashes | All eight byte-identical after the final gate |

Commands used:

```powershell
python -X utf8 -m pytest tests/python/verification/test_coverage_gate.py tests/python/cli/test_umbrella.py tests/python/combat/modular/test_t13_coverage_boundaries.py -q
python -X utf8 tools/mordheim-utils.py coverage-gate --json --area-floor modular:95 --area-floor vectorized:93
python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q
```

Primary evidence includes `entry.json`, incoming byte copies, real red/green
JUnit files, `budget-origin-identities.json`, recovered origin source files,
`reviewed-statement-dispositions.json` (647 requirements),
`nine-executable-index-review.json`, `measurement.json`/`.log`,
`boundary-measurement.json`/`.log`, `budget-reconciliation.json`, and the fresh
`final-gate.log`/`.json`. Final identities and preservation checks belong to
`closing.json`.

## Independent review and remaining boundaries

Historical dispatch: F040 then remained **in review**, with a different reviewer
unassigned. Independent review is now accepted; F057 owns current gate freshness.
The reviewer
must inspect the source reconstruction (particularly the pools evidence basis),
all seven replacements, the restored inactive-participant witness, the narrowly
changed four budget arrays, and real CLI results. The review must establish
that the budget preserves the original requirements and the update paths cannot
publish measurements from failing tests or failing requested floors.

F003/F007 pilot review, F004/F008 canonical activation, F006/F009 optimized
ports and F001's remaining 155 source pins retain their separate status. This
gate does not certify native execution or pending canonical mechanics. No
agent was launched, and no commit or push was made.
