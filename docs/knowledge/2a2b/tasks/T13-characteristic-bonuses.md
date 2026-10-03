# T13.2a — Characteristic bonus contract (compiler)

> Current ownership — 2026-10-02. Read the [shared eligibility boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation) before resuming this lot. Shared eligibility already decides legal choices for both products; Python still compiles characteristic bonuses and combat effects and carries local simulation context. The accepted contracts and recorded evidence below retain that bounded scope. They neither duplicate eligibility nor certify every legal choice's battle behavior.

This lot hardens how the combat compiler validates and applies
`stat_bonuses`. It is the first slice of T13.2; it is **not** the complete
T13.2 implementation. Grant selection, recipient routing, absence cases and
end-to-end compilation suites remain with the parent lot.

## Entry, reservation and boundary

- Entry: `1b7f7cf` plus the accepted T13.1 working-tree changes. Those T13.1
  changes (optional `Movement`/`Leadership` preserved as `None`) are preserved;
  the two optional fields keep their T13.1 contract.
- Reserved paths, and the only ones written by this lot:
  `packages/python/roster-construction/mordheim_construction/compiler.py`, the
  new `tests/python/construction/test_characteristic_bonus_contract.py`, this
  document, and ignored evidence under `build/cache/t13-parallel/bonuses/`.
- Combat Lab and Warband Manager are independent applications that share only
  the canonical knowledge base. This lot reads canonical data and compiles it;
  it introduces no roster ID, `member_ids`, `battle_number`, campaign field or
  service call.
- No KB/source, model, engine, UI, language asset, specification,
  interaction-policy or shared document was edited. `Characteristics`,
  `mordheim_core.effects` and `contracts.py` are untouched.

## Contract implemented

`stat_bonuses` are collected from two canonical sources and applied once to the
compiled characteristics:

1. `profile.characteristics` bindings: a `runtime.effects[].binding` with
   `kind: profile`, `id: profile.characteristics` and
   `parameters.bonuses`, optionally narrowed by `parameters.profile_ids`.
2. `SPECIAL_RULE_EFFECTS[rule_id]["stats"]`, reached through a `kind: compiler`
   binding whose id is not a `COMPILER_CONTRACTS` id.

The validation lives in
[`_characteristic_bonus_block`](../../../../packages/python/roster-construction/mordheim_construction/compiler.py)
and the application in `_apply_characteristic_bonuses`. The rules:

| # | Rule | Behaviour |
| --- | --- | --- |
| 1 | Allowed keys | Only `weapon_skill`, `strength`, `toughness`, `wounds`, `initiative`, `attacks`, `movement`, `leadership` (`CHARACTERISTIC_BONUS_KEYS`). |
| 2 | Value type | Positive, negative and zero integers are accepted. Booleans, decimals and strings are refused; nothing is coerced. |
| 3 | Unknown key | `ValueError` naming the key, its contract and the allowed list. |
| 4 | Unknown optional base | `movement`/`leadership` `None` plus a zero bonus keeps `None`; a nonzero bonus raises, stating that no base value exists. |
| 5 | Known attributes | Every valid bonus is accumulated and applied. |
| 6 | Recipient filters | `parameters.profile_ids` is evaluated before any validation, so a binding aimed at other profiles neither applies nor imposes a requirement. |
| 7 | Existing behaviour | Valid pre-existing behaviour is preserved, including the real Middenheim and Mark of Onogal bonuses. |

Exact messages:

```text
<rule> binding profile.characteristics grants an unknown characteristic bonus 'x'; allowed characteristics are [...]
<rule> binding profile.characteristics grants a non-integer strength bonus 1.5; only positive, negative or zero integers are accepted
<rule> compiler contract grants an unknown characteristic bonus 'x'; allowed characteristics are [...]
cannot apply a +1 movement bonus: the compiled profile has no known base movement
```

### Semantics decided

- **Accumulate, then require.** Contributions are summed first; the unknown-base
  rule is evaluated on the summed bonus. A `+1`/`-1` pair therefore nets to zero
  and keeps the optional characteristic unknown. This follows "apply and
  accumulate valid bonuses" literally and avoids a per-contribution ordering
  rule the contract does not state. The coordinator confirmed this decision
  and added a real compiler regression for cancellation on both optional fields.
  Each applicable contribution still passes key/type validation before summing.
- **Filter before validation.** The `profile_ids` check runs before the bonus
  block is read, matching the previous control flow, where a non-recipient
  binding was skipped entirely. A non-recipient bonus can never demand a base
  value from the profile.
- **Zero is not a change.** A zero bonus is accepted for a known attribute and
  leaves an unknown optional attribute unknown, so data that states "no change"
  does not force a value.
- **Mark of Onogal is untouched.** Its `+1 Toughness` is granted through the
  legacy `traits["mark_of_onogal_the_crow"]` path, not through `stat_bonuses`.
  It is verified unchanged at the end of the test file.

### Sources and values observed in the canonical KB

- `profile.characteristics` bonus keys currently present: `strength`,
  `toughness`, `weapon_skill`, `initiative` — all integer literals.
- `SPECIAL_RULE_EFFECTS` `stats` currently present: `toughness`, `wounds`,
  `strength` — all integer literals.
- No canonical entry uses `movement` or `leadership` today, so this lot changes
  no compiled fighter; it closes the silent-drop hole for future data.

## References consulted

- [2A/2B initiative README](../README.md) — reservation table, delivery
  template, boundaries and the Combat Lab / Warband Manager split.
- [T13 implementation plan](T13-implementation-plan.md) — lot definitions; T13.2
  owns grants and compilation.
- [T13.1 contracts](T13-contracts.md) — `Characteristics` keeps six positional
  combat statistics; optional keyword-only `movement`/`leadership`; `None` means
  unknown; boolean and fractional inputs are rejected; missing facts must fail
  rather than become zero.
- [Implement and verify rules](../../../guides/implement-and-verify-rules.md) —
  reuse the responsible layers and exercise real operators.
- `packages/python/core/mordheim_core/models.py` (`Characteristics`),
  `packages/python/roster-construction/mordheim_construction/selection.py`
  (`_profile`), `contracts.py` (`SPECIAL_RULE_EFFECTS`, `COMPILER_CONTRACTS`),
  `restrictions.py` (`_validate_profile_selections`),
  `tests/python/construction/test_profile_bindings.py` (Middenheim case).

## Tests and evidence

New focused tests:
[`tests/python/construction/test_characteristic_bonus_contract.py`](../../../../tests/python/construction/test_characteristic_bonus_contract.py).
They fabricate bindings in memory (`monkeypatch` on
`mordheim_construction.compiler.runtime_bindings`) and use free-selection
`Characteristics` values, so no KB file is edited. Real-KB cases re-check
Middenheim, Mark of Onogal and the two Blessings of Nurgle.

Cases covered: every canonical key with `+1`/`-2`/`0`; unknown keys
(`ballistic_skill`, `M`, `Strength`, `""`, `3`); non-integer values
(`True`, `False`, `1.5`, `-0.5`, `"1"`, `"1.0"`, `None`, `[1]`); zero keeping an
unknown optional field; nonzero on unknown `movement` and `leadership`; signed
accumulation over known fields; recipient filter excluding a profile; recipient
filter matching a profile; `SPECIAL_RULE_EFFECTS` `stats` applied, validated and
rejected when the base is unknown; Middenheim and Mark of Onogal preserved.

Commands run from the repository root:

```powershell
python -X utf8 -m pytest tests/python/construction/test_characteristic_bonus_contract.py -q
:: 39 passed

python -X utf8 tools/mordheim-utils.py tests --scope construction -q
:: 108 passed

python -X utf8 -m pytest tests/python/combat/vectorized/test_rule_families_a.py::test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects tests/python/application/test_analyses.py -q
:: 10 passed

python -X utf8 -m pytest tests/python/knowledge/test_campaign_catalogs.py tests/python/knowledge/test_editorial_schemas.py -q --tb=no -rf
:: 345 passed, 3 failed (pre-existing, unrelated: racial-maximum band rule,
:: hired-sword eligibility note, equipment-access editorial schema)
```

Ignored evidence: `build/cache/t13-parallel/bonuses/` holds `compiler.diff`
(sha256 `8e5be502ec39ca648d02a95accdc18033dfd0621f3a0619b1d2d2efc9a894dc6`),
`pytest-new-contract.txt` and `pytest-construction.txt`. The diff is taken
against HEAD and therefore also contains the preserved T13.1 hunk.

## Limitations

- This lot is **not** T13.2. Grant selection, absence/non-activation cases,
  recipient routing end to end, duplicates and source-mutation proofs remain
  with the parent lot.
- New aliases, characteristic inference and new mechanic automation were not
  added, as instructed.
- Unknown-base compiler coverage uses explicit free-selection
  `Characteristics` and isolated bindings/contracts for both Movement and
  Leadership. The tests do not compile Sewer Squigs or Mechanical Beasts;
  those profiles must not be cited as executed end-to-end evidence here.
- The `stats` path is reachable only for `kind: compiler` bindings whose id is
  not a `COMPILER_CONTRACTS` id. `SPECIAL_RULE_EFFECTS` also lists `stats` for
  `band--strigoi-power-iron-sinews`, but that rule is `mechanic`-bound, so the
  entry is currently unreachable. Verified data, not repaired here; belongs to
  the full T13.2 reconciliation.
- `band--blessings-of-nurgle-bloated-foulness` text says the Tainted One's
  Movement is reduced by 1, while its `stats` entry carries only Toughness and
  Wounds. Observed, not repaired here.
- Tests fabricate bindings in memory only; no canonical rule was corrupted and
  no KB file was written.

## Coordinator review and decisions — 2026-09-30

Accepted as **T13.2a only**, following independent review by the coordinator of
the external implementation, existing test logs and exact compiler diff. No
agent was launched. The compiler was not changed during review.

1. Evaluate the unknown-base requirement after accumulation, as described above.
   No base value is inferred when a valid signed sum is zero. The coordinator's
   additional cancellation regression closes the previously untested decision.
2. Do not extend `SPECIAL_RULE_EFFECTS.stats` to every mechanic-bound rule.
   [Iron Sinews' canonical grant](../../../../sources/knowledge/bands/trollheim/chaos-streets-undead-bloodlines/special-rules.yaml)
   already binds `skill.iron-sinews`, whose
   [execution contract](../../../../sources/knowledge/catalog/mechanics/execution.yaml)
   grants `strength_bonus: 1`. Applying the old `stats` entry as well risks
   doubling its combat bonus. T13.2 owns source/consumer reconciliation and
   cleanup of this legacy entry; T14 owns certification. No route is activated
   or deleted in this slice.
3. [Bloated Foulness](../../../../sources/knowledge/bands/mordheim/carnival-of-chaos/special-rules.yaml)
   explicitly reduces Movement by one, but
   [its compiler contract](../../../../packages/python/roster-construction/mordheim_construction/contracts.py)
   still omits that modifier. Record it as a T13.2 data/behavior obligation;
   the positive Toughness/Wounds regression does not certify the whole rule.
4. Broader canonical recipient routing belongs to T13.2. This slice tests the
   existing matching profile filter through the real Mercenary Captain compiler
   path; the exclusion case uses a free-selection fixture, not a full recipient
   catalogue. No further routing coverage is claimed.

External evidence: 39 focused, 108 construction and 10 runtime/application
tests passed, as recorded above. The reported three knowledge failures are
outside this acceptance; the coordinator did not rerun or certify that broader
knowledge suite. Its failures are not suppressed or repaired here.

Coordinator verification: **41 passed**, comprising the now **40** focused
contract cases plus the documentation-link check. Evidence:
`build/cache/t13-parallel/bonuses/coordinator-review.xml`.

```powershell
python -X utf8 -m pytest tests/python/construction/test_characteristic_bonus_contract.py tests/python/architecture/test_documentation.py -q --junitxml=build/cache/t13-parallel/bonuses/coordinator-review.xml
```

T13.2a is accepted and its reservation can be released. T13.2 as a whole remains
in progress. No KB/schema/engine/UI changes, commit or push accompany acceptance.
