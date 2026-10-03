# T13-F060 — Shifty poisoned-hand maintained witnesses

Delivered for independent review on 2026-10-02. This lot converts the accepted
FIND-3 observations into maintained strict regressions on the real modular
pipeline. **F060 is not accepted or closed here**, F003 is not reopened and no
canonical activation, optimized port or T13.4 certification is claimed.

## 1. Contract, scope and references

The accepted contract under test is the permanent ruling
[Shifty S1–S4](../../../decisions/design-rulings.md#shifty-s1s4) — in particular
**S2 early melee nomination** ("nominate one usable carried melee hand before
resolution and preserve its weapon, poison pair and hand slot") — together with
the maintained **Poison timing** interpretation in the same document (Spider
Spittle tests immediately on an undefended hit, before wound and saves).

Supporting reviewed evidence:

- [Shifty independent review](T13-shifty-independent-review.md): FIND-3
  (poisoned-hand transport verified in both nomination directions) and §12 item 3
  (the proposed small source-linked regression).
- [Shifty review dossier](T13-shifty-review.md#human-acceptance--2026-10-02):
  human acceptance of S1–S4 on 2026-10-02 and the accepted limits.
- [Execution follow-ups](T13-execution-follow-ups.md): the F060 entry and its
  close criterion ("maintained source-derived dice/decision cases detect
  incorrect hand/poison projection and pass without production-file mutation").
- Canonical sources: `poison.spider-spittle` in
  [`close-combat.yaml`](../../../../sources/knowledge/catalog/mechanics/close-combat.yaml)
  (undefended hit → immediate Toughness test) and its `effect-set` execution
  handler in
  [`execution.yaml`](../../../../sources/knowledge/catalog/mechanics/execution.yaml);
  the Shifty clause in
  [`halflings-mic/special-rules.yaml`](../../../../sources/knowledge/bands/mordheim/halflings-mic/special-rules.yaml).
- Read-only prior evidence: the independent probes
  [`probe_shifty.py`](../../../../build/cache/t13-parallel/shifty-independent-review/probes/probe_shifty.py)
  (`probe_poison_nominated_main`, `probe_poison_nominated_off`) and the
  coordinator's `observations.json`. Those files were read, never executed or
  overwritten; no part was copied verbatim.

**Scope limits.** Only Spider Spittle on the reviewed mace/axe compositions is
covered. No other poison, no pistol-only allocation (F005/F026), no canonical
activation (F004), no optimized backend (F006) and no Crude Belch first-attack
loss (F061) is asserted.

## 2. Added cases and the errors they distinguish

One new file: [`tests/python/combat/modular/test_shifty_poison_transport.py`](../../../../tests/python/combat/modular/test_shifty_poison_transport.py)
(5 strict cases). Each runs `initialize_duel` → `resolve_round` with a fully
strict dice tape (`StrictDice`), a fully strict decision tape
(`StrictDecisions`) and `finish()` on both; any unexpected, missing or
reordered roll/decision raises `EvidenceMismatch`.

| Case | Composition | Distinguishes |
| --- | --- | --- |
| `test_nominated_poisoned_main_...` (A) | main poisoned, off clean, nominate main | bonus requests Spider Spittle; ordinary main keeps it; ordinary off never gains it; nomination decision observed before the first attack die |
| `test_nominated_poisoned_off_...` (B) | off poisoned, main clean, nominate off | bonus carries the off hand's poison **and** its synthetic +1 hit discriminator (`hit_target` 3 vs 4); ordinary off keeps poison; ordinary main stays clean |
| `test_nominating_the_clean_main_...` (C) | off poisoned, nominate the clean main | bonus stays clean; the poisoned off hand keeps its trigger on its own ordinary attack; no trigger from mere possession of the other hand's poison |
| `test_owner_in_second_position_...` | Shifty owner is the duel's `second` fighter | participant-position control: no bonus, nomination or poison trigger leaks to the charger; the owner's ordinary off-hand poison is preserved |
| `test_no_shifty_control_...` | same loadout without the skill | negative control: no bonus attack, no nomination decision, no `shifty` key anywhere; ordinary main still poisoned, ordinary off still clean |

Every case also asserts the full ordered request tape, the exact attack count
(4 with the bonus, 3 in the control), the attack order via `hit_target`
(charger 4; owner main 4; owner off 3), the absence of extra dice/decisions
(`finish()` plus tape equality), the wound outcome (no wound) and the final
state (both warriors standing, 1 wound each, `round_index == 1`).

The nomination timing assertion uses a thin recording wrapper around
`StrictDecisions` that captures `(key, len(dice.requests))` at each decision, so
case A/B/C assert the nomination is requested **before any attack die**.

## 3. Synthetic fixture construction and provenance

The file does **not** call `compile_fighter` or any helper that does. At delivery
time, concurrent warrior-construction centralization was changing that frontier;
the [shared eligibility reference](../../../reference/eligibility.md) now
describes the completed migration. It builds three explicit `CompiledFighter`
values locally:

- `_weapon(tag, poisoned, hit_modifier)` returns `(weapon, clean pair)`; the
  clean pair is the same weapon contribution without `poison.spider-spittle`,
  mirroring the compiler's contextual-poison contract (see the
  `main_weapon_without_poison` field comment in
  [`models.py`](../../../../packages/python/core/mordheim_core/models.py)).
- `duelist(...)` — `Characteristics(3, 3, 3, 1, I, 1)`, main `weapon.mace`,
  off `weapon.axe` with `hit_modifier=1` (the same device the accepted
  `test_bonus_weapon_choice_is_separate_from_ordinary_allocation` uses), no
  armour/ward save (7), `off_hand_attacks=True`, `skill.shifty` injected as a
  global tag, and a `weapon.fist` unarmed fallback.
- `charger(...)` — clean mace, no off hand, no Shifty.

Die values: hit 4 (hits WS3 vs WS3), Spider Spittle 2 (passes Toughness 3, so
the target stays standing and its own pools remain observable), wound 1 (S3 vs
T3 needs 4, so the wound fails and no injury/save die enters the tape).

**These inputs test engine composition, not legality.** They do not show that a
Halfling can acquire the mace, the axe, the poison or Shifty through the
product; `skill.shifty` is the accepted pilot injection and canonical selection
remains F004.

## 4. Entry, concurrent drift and separation

Entry capture (branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`,
dirty tree) and SHA256 of every input actually used are recorded in
[`entry.json`](../../../../build/cache/t13-parallel/shifty-poison-transport/entry.json),
produced by the reproducible
[`capture_entry.py`](../../../../build/cache/t13-parallel/shifty-poison-transport/capture_entry.py).
The script never overwrites a previous capture: re-running moves the previous
`entry.json` to `entry-<UTC stamp>.json`.

Engine inputs matched the independent review's hashes exactly
(`rounds.py d444f5a3…`, `pools.py 567a9636…`, `attacks.py 55e05e32…`,
`phases.py a9d1759d…`), so the reviewed behavior was re-exercised unchanged.
The concurrent centralization work is confined to construction modules and its
plan document; none of its files is touched, and any drift there is neither
attributed to F060 nor used to demand a freeze.

Separation is enforced by construction: no production file, no existing test,
no KB source, no shared eligibility/bundle file and no coordinated document was
modified. The only writes are the two authorized new files plus this evidence
directory.

## 5. Commands, results and exit codes

All commands run from the repository root with `python -X utf8`; logs and JUnit
XML are retained in `build/cache/t13-parallel/shifty-poison-transport/`.

| Command | Exit | Result |
| --- | --- | --- |
| `python -X utf8 -m pytest tests/python/combat/modular/test_shifty_poison_transport.py -q -p no:cacheprovider --junitxml=…/new-suite.xml` | 0 | **5 passed** in 0.14s (`new-suite.log`) |
| `python -X utf8 -m pytest tests/python/combat/modular/test_shifty_poison_transport.py tests/python/combat/modular/test_shifty.py tests/python/combat/modular/test_spectral_touch.py -q -p no:cacheprovider --junitxml=…/focal.xml` | 0 | **106 passed** in 13.48s = 44 Shifty + 5 new + 57 Spectral (`focal.log`), no failures/errors/skips |
| `python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q -p no:cacheprovider` | 0 | **1 passed** in 0.11s, run after the last edit (`documentation-after-doc.log`) |

After the final edits all three commands were re-run: new suite **5 passed**
(`new-suite-final.log`), focal **106 passed** in 13.68s (`focal-final.log`),
documentation **1 passed** (`documentation-after-doc.log`). An earlier
post-documentation run exposed one broken relative link in this file (the plan
link needed one more `../`); it was fixed and the check re-run green.

No construction, TypeScript, port, T14 or coverage command was run: none is a
concrete dependency of this test-only lot.

## 6. Isolated mutation evidence

[`mutations.py`](../../../../build/cache/t13-parallel/shifty-poison-transport/mutations.py)
loads the maintained test file in a dedicated process, patches the modular
engine seams **in memory** (`rounds.select_shifty_weapon`,
`pools._weapon_for_attack`), runs the maintained cases, then restores every
attribute. No live engine file is edited at any point. Results are in
`mutations.json` / `mutations.log`; the script exits 1 if a baseline fails or a
mutation survives.

| Mutation | Injected fault | Detected by | Failing maintained check |
| --- | --- | --- | --- |
| M1 | nomination decision consumed but always keeps the main hand | case B | strict tape: roll 1 expected `…shifty.attack.0.spider-spittle`, got `…shifty.attack.0.wound` |
| M2 | ordinary pools use the other hand's weapon | case A | strict tape: roll 7 expected `…attack.0.spider-spittle`, got `…attack.0.wound` |
| M3 | bonus loses its own poison (clean weapon resolves the bonus) | case A | strict tape: roll 1 expected `…shifty.attack.0.spider-spittle`, got `…shifty.attack.0.wound` |
| M4 | ordinary hand loses its poison | case A | strict tape: roll 7 expected `…attack.0.spider-spittle`, got `…attack.0.wound` |
| M5 | nomination loses the nominated hand's weapon contribution | case B | body assert at test line 184: `[hit_target…] == [3, 4, 4, 3]` |
| M6 | poisoned other hand transported to the bonus despite the nomination | case C | strict tape: roll 1 expected `…shifty.attack.0.wound`, got an unexpected `…shifty.attack.0.spider-spittle` |
| M7 | nomination decided under a different decision id | case A | `StrictDecisions`: expected `round.0.first.shifty.main-weapon`, got `round.0.first.shifty.weapon` |

All five baselines pass and all seven mutations are detected
(`all_mutations_detected: true`), each mapped to the exact failing check and
source line — a bare "detected" print is not used. No real defect was found;
no engine repair was needed or performed.

## 7. Limits and pendings

- **Spider Spittle only.** Other poisons (Black Lotus, Manbane, Wolfsbane,
  Nightshade, Black Venom, Reptile Venom, Devil's Toxin, Bloodroot) are not
  certified. Owner: whoever later claims broad poison coverage; resume when a
  lot actually changes those handlers; close when each poison has its own
  source-derived strict case.
- **Pistol-only allocation remains open (F005/F026).** The explicit refusal is
  unchanged and untested here. Owner: Coordinator; resume with the allocation
  contract; close per that entry.
- **Canonical access remains open (F004).** `skill.shifty` is injected, not
  selected; the recipient/grant/kind correction and its absence controls are
  not covered. Owner: F004 route; close per that entry.
- **Optimized backends remain open (F006).** NumPy/native were not executed.
  Owner: F006; resume after the modular contract is accepted for the backend;
  close when logical dice/decisions/state parity is proved.
- **Crude Belch remains open (F061).** The generic minimum-one clamp is not
  certified as that clause. Owner: F061 route.
- **Centralization drift.** If the concurrent agent changes
  `rounds.py`/`pools.py`/`attacks.py`, `models.py` or the strict dice helpers,
  re-run the new suite and re-capture `entry.json`; only the affected subset
  needs revalidation. This lot intentionally does not depend on the compiler.

**Reproducer for the whole lot:** run the three commands in §5 from the
repository root; all three must exit 0. For the mutation proof run
`python -X utf8 build/cache/t13-parallel/shifty-poison-transport/mutations.py`
and confirm `all_mutations_detected: true` with exit 0.

## 8. Review handoff

Delivered for independent review. Acceptance/closure of F060 belongs to the
coordinator after verifying this document, the new suite and the retained
evidence. The test file's SHA256 is recorded in `entry.json`; re-run
`capture_entry.py` to confirm the reviewed revision.

## 9. Independent coordinator acceptance — 2026-10-02

**Accepted; F060 resolved and its reservation released.** This acceptance is
bounded to the five maintained Spider Spittle compositions and the accepted
Shifty modular contract. It adds no canonical access, other-poison, optimized
backend or complete T13.4 certificate. F004/F005/F026/F006/F061 retain their
existing owners and closure criteria. The concurrent construction-centralization
implementation was not modified or invoked by these witnesses.

Independent checks against the delivered revision:

- Every input hash in the supplied `entry.json` matches the review entry,
  including test SHA256 `5a4134c7eb2ee06a5a3498e37eb375ec0cc689af111aa9e5cf7a6b4ac5c816a0`.
  All 19 external evidence files were frozen for closing comparison.
- Fresh focal execution: **106 passed, exit 0, 13.40s** (44 existing Shifty,
  five new witnesses and 57 Spectral). The coordinator retained separate logs
  and XML, without overwriting the author's evidence.
- The mutation script was copied to the coordinator evidence directory and
  re-executed there: **five baselines pass, seven mutations detected, exit 0**.
  Inspection confirms six `EvidenceMismatch` failures at expected request/
  decision checks and one `AssertionError` at the nominated hit-contribution
  check; unrelated exceptions are not being counted as successful detections.
- Independently constructed direct nomination checks preserve the exact weapon,
  clean poison pair and original slot in both directions. These are additional
  boundary probes, not a claim that the five maintained active-poison cases
  independently certify contextual poison removal. AST inspection and code
  review confirm no construction import or `compile_fighter` call.
- The strict tapes match the accepted early-nomination and immediate
  undefended-hit poison timing. The off-hand +1 is an explicit synthetic
  discriminator; the fixtures establish engine behavior rather than legality.

**Minor prose correction, no behavioral defect:** the negative control's inline
comment says "clean main and poisoned off"; its actual fixture, tape, presence/
absence assertions and this report's table correctly test **poisoned main and
clean off**. This acceptance records the correction without changing the
delivered test bytes or opening an implementation issue.

The coordinator's first direct projection probe used tuple decision entries
instead of the maintained mapping format and raised `TypeError`; only that
ignored evidence script was corrected and rerun successfully. This setup error
is not a delivery or engine failure.

Durable checks and results are in
`build/cache/t13-parallel/shifty-poison-transport-coordinator-review/`:
`entry.json`, `delivery-original.md`, `focal.log`, `focal.xml`, copied
`mutations.py` and its fresh outputs, `projection-check.py`/`.json`, and
`closing.json`. Documentation validation runs after the acceptance edits.
Only this appended acceptance and the coordinator's README/plan/task/follow-up
records are changed; engine, models, strict helpers, test bytes and external
evidence are preserved. No commit, push or agent launch occurred.
