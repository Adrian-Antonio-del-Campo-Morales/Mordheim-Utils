# Lot F073 — runtime metadata for the catalogued skills that already have an operator

F073 reconciles the runtime classification of the `catalog/skills/*.yaml`
records whose printed behaviour already exists and is consumed by Combat Lab.
It adds **metadata only**: no new mechanic, no new operator, no new parser, and
no change to who receives a skill, to its conditions or to its availability.
Deliverables: this file and `F073-results.csv` (58 rows, one per candidate).

## Candidate surface, revalidated

- `C-combat-results.csv` carries **54** rows with `source_file:
  catalog/skills/*.yaml`: **51 `metadata_gap`** and 3 `connection_gap`. The
  candidate number to reconcile is 51 as measured; it was not forced to fit the
  brief.
- `consolidated-results.csv` adds the 4 `F-excluded-scope-control` rows for the
  same family: **58 candidates**, and every id in `F073-results.csv` matches
  that set exactly (set equality checked, no extra and no missing id).
- Pre-state per candidate, read from the same-mode baseline
  `build/audit/f073/before-semantic/combat-audit.csv` (`audit_mode: semantic`)
  and quoted in the `input_state` column: all 51 were `scope YES` /
  `implemented UNKNOWN` / `binding unbound` / `combat_work_status
  needs_target_reconciliation`, with no `runtime` key in the YAML.

## Dispositions

| class | rows | `f073_disposition` |
| --- | --: | --- |
| corrected, operator reproduced | 48 | `classified_implemented` |
| corrected, printed clause kept explicitly out of scope | 3 | `classified_implemented_with_out_of_scope_clause` |
| already correct (no metadata to add) | 0 of 51; the 4 review-excluded needed nothing | `excluded_by_source_review` |
| blocked, no operator of its own | 3 | `blocked_no_operator_decision_required` |

Each of the 51 corrected entries received `runtime: {scope: 'YES', implemented:
'YES', grant: none}` and one YES effect whose `binding` is
`{kind: mechanic, id: <same skill id>}`; `grant: none` is the catalogue
convention because the grant belongs to the band rules and construction
choices, so the classification cannot change a roster.

Three entries carry an explicit NO advancement clause: characteristic-maximum
exemptions for Iron Sinews, Strength of Steel and Red Fury. Their individual
duel bonuses retain their existing YES operators.

Coordinator correction — 2026-10-06: removed two incorrectly excluded clauses.
Mighty Blow's pistol exception belongs to melee scope and is already honored
by fixed Strength 4 on both pistol mechanics in modular attack contexts; the
non-pistol hand receives the bonus. Ignore Pain's Resilient prerequisite belongs
to construction scope and is enforced by the shared decision for its granting
band rule. The catalogue keeps `grant: none`. Original source wording is intact;
no engine or shared eligibility change was necessary. Two focused regressions
exercise these existing paths; the classification matrix now refuses false NO
clause rows for these skills.

The seven skills the brief names as unlinked are exactly the 3 blocked plus the
4 review-excluded rows, with no invented operator:

- **blocked (3)** — `skill.chosen-of-the-white-tower`, `skill.fey-quickness`,
  `skill.instinctive-warrior`: C calls them `connection_gap` and names an
  existing operator under *another* skill id (`mechanic/skill.defensive-stance`,
  `mechanic/skill.elven-agility`). Neither has a `close-combat.yaml` family row
  nor an `execution.yaml` contract row under its own id, and no runtime block in
  `catalog/skills/*.yaml` binds an effect to a mechanic of a different id (0
  aliases), so a binding here would premise an equivalence ruling. F073 adds
  nothing and leaves the audit at `needs_target_reconciliation`.
- **excluded (4)** — `skill.fey`, `skill.magic-resistant`, `skill.taunt`,
  `skill.trading-flair`: `T13-audit-scope-review.csv` classifies them outside
  the duel runtime (the audit reports scope NO / excluded); no classification
  was added, and their absence of an operator is not treated as evidence of
  scope by itself.

## Files modified (this lot only)

- `sources/knowledge/catalog/skills/general.yaml` (10 entries) and
  `sources/knowledge/catalog/skills/warband.yaml` (41 entries): insertions only
  — the lot's tooling never rewrites or removes an existing line. The 8 deleted
  lines visible in `git diff` belong to the `skill.fearsome` block written by
  another lot before F073 started (not an F073 candidate, not touched here).
- `tests/python/knowledge/test_t13_f073_skill_runtime.py` (new focal regression,
  10 tests).
- `docs/knowledge/2a2b/tasks/T13-reconciliation-dispatch/F073-results.csv`
  (58 rows, sha256
  `7a3d6265d8949ae5ddbd3843e74d410aae97ff94ef0a4e3d08ce314c03d184cd`) and this
  file.
- `build/audit/f073/**` (gitignored): `targets.py` (the closed candidate list
  with the audit ids), `apply.py` (`--check` / `apply` / `--revert`, temp-file +
  `os.replace` writes), `report.py` (emits the CSV), `mutation_check.py`, and the
  evidence audit CSVs (`before/`, `after/`, `before-semantic/`,
  `after-semantic/`).

No promotion mirror, schema, shared register, artefact or snapshot was edited.

## Checks run

| check | result |
| --- | --- |
| `apply.py --check` | 51 targets, 5 explicit clauses, every target resolves to an existing execution contract; `--revert`/`apply` round-trip idempotent (51 removed, 51 inserted, "already classified 0") |
| `mordheim-combat-lab verify --structural` (before and after) | `structural_complete=True; 1050 profiles compile with their default construction` |
| `mordheim-combat-lab audit` same-mode A/B (`before-semantic` vs `after-semantic`) | 7336 → 7341 rows; the only ids removed are the 51 `rule/catalog/{general,warband}/<skill>/unclassified`; the only ids added are the same 51 as `<skill>/<skill>` plus the 5 `unimplemented.*` clause rows; **0 other rows differ in any field**. The 51 read `scope YES / implemented YES / binding linked / structural_status linked / implemented_pending_verification`, the clauses read `scope NO / binding unbound / excluded` |
| `pytest tests/python/knowledge/test_t13_f073_skill_runtime.py` | 10 passed — matrix over the 51, the 5 clauses and the 7 unlinked skills, plus field/tag execution through `compile_fighter` with and without the skill |
| `pytest test_editorial_schemas test_catalog test_binding_registry test_kb_i18n` | 372 passed, 3 failed — all in other writers' files (below) |
| `pytest test_spec_digests_fresh test_schema_strictness_cli test_rule_prose_keys test_printed_entries` | 50 passed |
| `pytest test_catalogue_contract_regressions test_printed_wordings test_2ab_fidelity_rows test_shared_rule_fusions test_source_documents test_translation_consistency` | 78 passed, 1 failed (other writer's file, below) |
| `mutation_check.py`, one fresh process per case | 6 of 6 discriminating mutations caught: 4 by the focal matrix, 2 earlier by the maintained loader ("unbound effect needs a reason", "active effect without a binding") |
| `tools/knowledge/maintenance/format_yaml.py --check` | `warband.yaml`: 0 would change; `general.yaml`: 1 would change, and it is the `unimplemented.skill.combat-master` `reason:` of another writer's block (see integration items). F073 inserted no line over 98 columns |
| `tools/knowledge/audit_kb_conformance.py --tree knowledge` | 26 deviations in two classes (`applies-to` 6, `grant-scope` 20), all in band rules; F073 touches no band rule |

Failures observed and **not** attributable to F073 (each verified to sit in a
file this lot does not own): `test_catalog.py::test_special_rule_runtime_metadata_is_canonical_and_binary`
(2909 vs the frozen 2908 band rules with a runtime block — F073 changes no band
rule); `test_catalog.py::test_every_catalogued_mechanic_can_be_compiled_in_its_legal_slot`
(Snorri pre-battle drinking `ValueError` raised in `compiler.py`);
`test_editorial_schemas.py::test_the_contract_is_strict_about_the_committed_documents`
(`unused_enum_value` for `equipment-access.yaml.schema.json#/$defs/equipment_entry.applies_to.profile_types`
and `profiles.yaml.schema.json#/$defs/profile.combat_traits.vampire_bloodline`);
`test_translation_consistency` (`mechanic.marine-hunter`, `weapon.pry-bar` in
`catalog/mechanics/close-combat.yaml`); `test_2a_staging.py::test_ingest_tool_validate_passes`
(4 staging manifest problems in `druchii-mic`, `dwarf-slayer-cult-web`,
`snotlings-web`); `test_yaml_formatting.py` (tree-wide formatting debt).

Not run to completion: the whole `tests/python/knowledge` directory (it exceeds
the 10-minute budget of this lot); its files that concern `catalog/skills` were
run individually as listed. No `verify`/`parity`/`coverage` campaign was
repeated.

## Historical audit comparison and current integration delta

- Original F073 measurement, before the coordinator correction: **+51 rows reclassified** (`…/unclassified` → `…/<skill>/<skill>`,
  `implemented_pending_verification`), **+5 rows** for the explicit clauses
  (`scope NO`, `excluded`) and **−51 unclassified rows**, i.e. 7336 → 7341 in
  semantic mode. `combat_work_status` moves from `needs_target_reconciliation`
  to `implemented_pending_verification` for exactly those 51 ids; no other row,
  and no grant, changes.
- Snapshots and artefacts: **none refreshed by this lot** (per the brief).
  `outputs/web-public/knowledge/knowledge-web.json` is already stale
  (`generate_knowledge_web.py --check` fails) and it does embed skill records, so
  it must be regenerated once at integration, after F074 lands.

## Pending integration proposals

1. `unimplemented.skill.combat-master`'s `reason` must be folded to `>-` for
   `format_yaml.py --check` to pass on `catalog/skills/general.yaml`; the entry
   is not an F073 candidate, so it was left untouched.
2. `test_catalog.py`'s frozen count `2908` band rules with a runtime block must
   move to `2909` for whoever added the extra rule (F074's dwarf-slayers rule).
3. The owners must review the two `unused_enum_value` findings and demonstrate
   their consumer/contract justification or remove unsupported vocabulary. Do
   not add allowlist entries merely to make the gate pass.
4. The 3 blocked skills need one explicit equivalence decision each: a dedicated
   mechanic (preferred — the catalogue has no alias convention) or a declared
   alias, otherwise the audit keeps reporting them
   `needs_target_reconciliation`.
5. Regenerate the published web/knowledge artefact once, after both lots land,
   and refresh the snapshots that carry the 51 reclassified ids.

## Closure status

The 51 admitted metadata gaps are closed and applied end-to-end (canonical YAML
→ audit → compiled fighter evidence), and all seven unlinked skills have an
explicit disposition with evidence. F073 is **not declared closed** here: items
the relevant items above are integration work outside this lot's file ownership. T13 is not
declared finished.

Current integration note: the two false NO clause rows no longer exist. The
original 7336 -> 7341 comparison remains historical evidence for the incoming
lot, not the final current row count. F074 and other concurrent work also change
the corpus; remeasure it at integration rather than copying the old totals.
