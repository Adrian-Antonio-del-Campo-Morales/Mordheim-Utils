# T13.2b — Bloated Foulness Movement modifier (compiler)

> Current ownership — 2026-10-02. Read the [shared eligibility boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation) before resuming this lot. Shared eligibility already decides legal choices for both products; Python still compiles characteristic bonuses and combat effects and carries local simulation context. The accepted contracts and recorded evidence below retain that bounded scope. They neither duplicate eligibility nor certify every legal choice's battle behavior.

This lot completes the compiled characteristics of one canonical rule so the
Tainted One's compiled **Movement** matches its printed profile plus the
blessing. It is a slice of T13.2; it is not T13.2, and it does not certify the
rule end to end. Any included movement mechanic using explicit local facts
needs its own T13.6 implementation and T14 evidence; no autonomous board is implied.

## Entry, reservation and boundary

- Entry: `1b7f7cf`, branch `2A2B`, with the accepted T13.1 and T13.2a
  working-tree changes preserved untouched. T13.4a (Shifty) is in review and
  was not touched.
- Files written, and only these: the Bloated Foulness entry of
  `packages/python/roster-construction/mordheim_construction/contracts.py`, the
  new `tests/python/construction/test_bloated_foulness_movement.py`, this
  document, and ignored evidence under
  `build/cache/t13-parallel/bloated-foulness/`.
- Combat Lab and Warband Manager are independent and share only the canonical
  KB. This lot adds no roster ID, `member_ids`, `battle_number`, campaign field
  or service.
- The compiler (`compiler.py`) was read but **not** changed: the new modifier
  reuses the T13.2a validation and accumulation. No other
  `SPECIAL_RULE_EFFECTS` entry, KB/source, binding, semantic fingerprint, model,
  engine, interface, language asset or shared document was edited.
- The external report observed no T13.2b reservation in its earlier snapshot.
  The coordinator added it during T13.3a preparation. It was present when this
  delivery was reviewed, then released on narrow acceptance (2026-10-01).

## Source confirmation

Canonical rule:
[`band--blessings-of-nurgle-bloated-foulness`](../../../../sources/knowledge/bands/mordheim/carnival-of-chaos/special-rules.yaml),
`kind: blessing`, `implemented: YES`, `grant: selectable`, binding
`special-rule.band--blessings-of-nurgle-bloated-foulness` (`kind: compiler`).

Printed text (EN, as stored): "Cost: 40 Gold Crowns The Tainted One is a huge,
disgusting mass of diseased, flabby folds. It gains +1 Wound and +1 Toughness
but has its Movement reduced by -1." Spanish: "Gana +1 Herida y +1 Resistencia,
pero ve su Movimiento reducido en -1."

The linked source was consulted and matches:
<https://mordheimer.net/docs/warbands/grade-1a-warbands/carnival-of-chaos>
("Bloated Foulness, Cost: 40 Gold Crowns … It gains +1 Wound and +1 Toughness
but has its Movement reduced by -1.").

Recipients: the same page states "Blessings of Nurgle may be bought for Tainted
Ones only when they are recruited." Compiled behaviour agrees: the Blessing is
accepted only for `tainted-ones`; `carnival-master`, `brethren`,
`plague-bearers` and `nurglings` are rejected with "special rule is not
available to …" by the existing `band--blessings-of-nurgle-` guard. No recipient
was widened or narrowed.

## Change

```diff
-    "band--blessings-of-nurgle-bloated-foulness": {"stats": {"toughness": 1, "wounds": 1}},
+    # Bloated Foulness: +1 Wound, +1 Toughness and Movement -1 (its source
+    # wording); movement is carried, not consumed by the duel engine.
+    "band--blessings-of-nurgle-bloated-foulness": {"stats": {"toughness": 1, "wounds": 1, "movement": -1}},
```

The canonical Tainted One prints M4 WS3 BS3 S3 T3 W1 I3 A1 Ld7.

| Compiled with | Movement | Toughness | Wounds | Leadership |
| --- | --- | --- | --- | --- |
| Nurgle's Rot (control, no characteristic) | 4 | 3 | 1 | 7 |
| Bloated Foulness | 3 | 4 | 2 | 7 |
| Mark of Nurgle | 4 | 3 | 2 | 7 |
| Bloated Foulness + Mark of Nurgle | 3 | 4 | 3 | 7 |

## Reuse of T13.2a

The new value is a negative integer for an allowed key, so it flows through the
T13.2a contract unchanged: `_characteristic_bonus_block` validates the
`stats` block (key, integer type) and `_apply_characteristic_bonuses`
accumulates it. Movement is a known integer for this profile, so the
unknown-base rule is not exercised here; its coverage stays in the T13.2a suite,
which is part of the construction scope run below. No new application path,
alias, inference or validation was added.

Because the field was already carried as a preserved fact (T13.1), the modifier
changes the compiled `Characteristics` only. Nothing in the combat engine reads
`characteristics.movement` (only the kernel and the native compiler transport
it), so no duel behaviour changes.

## Tests and evidence

New tests:
[`tests/python/construction/test_bloated_foulness_movement.py`](../../../../tests/python/construction/test_bloated_foulness_movement.py).
Expectations are derived from the canonical profile read through
`load_bands("mordheim")` plus the rule's printed deltas, not from the contract
under test. Blessings are mandatory, so the control is Nurgle's Rot, which has no
characteristic modifier. Its full contagion rule is not certified by this lot.

Cases: control equals the printed profile; Movement −1, Toughness +1 and Wounds
+1 exactly; Weapon Skill, Strength, Initiative, Attacks and Leadership unchanged;
Mark of Nurgle keeps Wounds +1 with **no** Movement reduction; both blessings
accumulate each contribution exactly once; Movement stays a known nonzero
integer.

Commands (repository root):

```powershell
python -X utf8 -m pytest tests/python/construction/test_bloated_foulness_movement.py -q
:: 6 passed

python -X utf8 tools/mordheim-utils.py tests --scope construction -q
:: 115 passed (includes the T13.2a contract suite)

python -X utf8 -m pytest tests/python/knowledge/test_catalog.py tests/python/combat/modular/test_catalogue_runtime.py tests/python/combat/vectorized/test_rule_families_a.py tests/python/combat/vectorized/test_rule_families_b.py -q
:: 65 passed (every existing reference to this rule)

python -X utf8 -m pytest tests/python/verification/test_structural.py tests/python/verification/test_semantics.py -q --tb=no -rf
:: 4 failed, 3785 passed
```

The external report gives **4 failed, 3785 passed** for the semantic/structural
command before and after the edit, naming `test_structural_success_is_not_semantic_success`,
`test_bear_hug_has_a_real_source_link_and_detected_behavioural_mutations`,
`test_unverified_shared_consumer_keeps_editorial_grant_pending` and
`test_redundant_access_mutation_is_justified_not_counted_as_detected`. The retained
`pytest-dependent.txt` contains the 66-pass catalogue/runtime/documentation run,
not either semantic/structural run. The coordinator did not rerun or independently
verify the reported broad baseline comparison. No global semantic success is
claimed from these reported numbers.

The rule's spec `digest` pins still compare as `source changed`, but that is
pre-existing KB drift: Mark of Nurgle — untouched by this lot — mismatches in the
same way, and `inventory.py` computes `source_digest` as
`fingerprint({"rule": <KB YAML node>, "context": <KB files>})`, so a Python
contract file cannot move it. No pin was refreshed.

Ignored evidence: `build/cache/t13-parallel/bloated-foulness/` holds
`contracts.diff`, `baseline-compile.txt`, `after-compile.txt`,
`recipients-check.txt` and `spec-digest-check.txt`.

## Limitations

- Only the **compiled characteristic** is corrected. No board movement, path,
  charge range or terrain behaviour is implemented or certified; Movement is
  still carried, not consumed, by the duel engine.
- This does not certify the whole Blessing, T13.2 or T14, and the coordinator
  owns acceptance. No mutation detected by behaviour was added at the engine
  level, because the field has no engine consumer yet.
- The coordinator clarified `selected-blessings-bloated-foulness`: compiled
  Movement is reduced, while duel resolution does not consume it. Its existing
  `compiled` case now asserts Movement 3 alongside Wounds 2. No source/scope
  fingerprint or implementation/review status was refreshed.
- Manual passes through `parse_warband`-style campaign tools were not run; this
  lot is construction-only.
- The broader knowledge suite and `python tools/mordheim-utils.py parity` were
  not run: no concrete dependency beyond the files listed above, and T14 owns
  parity certification.

## Coordinator decisions and acceptance — 2026-10-01

Accepted **only as the compiled characteristic correction** after independent
coordinator review of the external author's change. T13.2 remains in progress;
Iron Sinews reconciliation and other recipient/grant obligations remain separate.

1. Keep supplying canonical numeric Movement through the existing Characteristics
   contract. No separate "carried but unused" marker is needed; absence of an
   engine consumer is an explicit documented limitation. This does not add
   movement/charge/terrain behavior to the duel.
2. Clarify the existing semantic interpretation and add Movement 3 to its existing
   compiled expectation. The coordinator reserved this specific specification
   entry before editing it. All 10 cases execute successfully through `check_case`
   on the real compiler/operators. This direct check bypasses source-fingerprint
   certification and does not repair the stale pin.
3. Record the reservation discrepancy as historical; the active row was present
   at review and is released on acceptance. Explicit dispatch ownership was not
   widened by the external author.

Review evidence:

- Current `contracts.py` diff exactly matches the external delivery
  (SHA256 `8bbed0e5a38922f29b57886030322d7fa70170936c54559e4ebc326d481e5e69`).
  The compiler diff still matches accepted T13.2a
  (`8e5be502ec39ca648d02a95accdc18033dfd0621f3a0619b1d2d2efc9a894dc6`).
- **47 passed** in coordinator verification: six Bloated Foulness cases, 40 bonus
  contract cases and documentation links. External retained evidence supports
  115 construction and 66 dependent cases; these larger suites were reused.
- `baseline-compile.txt` is empty. To address that missing evidence, the coordinator
  reconstructed the old contract in an isolated process by removing only Movement
  from the in-memory stats entry, compiled the canonical Tainted One, then restored
  the entry. M4 becomes M3; T4/W2 and all other characteristics remain identical.
  This is a reconstructed baseline, not an original pre-edit capture.
- Removing the modifier in memory causes the updated compiled spec expectation
  to fail with `attacker.characteristics.movement: got 4, expected 3`; after
  restoration it passes. This proves the compiler assertion, not a combat-engine
  mutation or a semantic certificate. The scenario runner intentionally does not
  treat compiled-field expectations as behavioral mutation witnesses.

Evidence: `coordinator-review.xml`, `coordinator-baseline-reconstruction.json`,
`coordinator-spec-review.json` and `coordinator-delivery.json` under the lot's
ignored evidence directory. The historical external report is retained as given;
this section states what the coordinator actually confirmed.

```powershell
python -X utf8 -m pytest tests/python/construction/test_bloated_foulness_movement.py tests/python/construction/test_characteristic_bonus_contract.py tests/python/architecture/test_documentation.py -q --junitxml=build/cache/t13-parallel/bloated-foulness/coordinator-review.xml
```

No product code changes were made during review. Coordinator edits are limited
to this delivery, coordination documents, and the named specification's wording
and compiled Movement expectation. No KB, engine, UI/language, agent, commit or
push changes belong to this review.
