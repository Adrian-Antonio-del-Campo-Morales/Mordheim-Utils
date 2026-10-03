# T13.2 — Hired swords, Dramatis Personae and Mazzalupo Commands: trace and coverage

> Current ownership — 2026-10-02. Both products reuse the existing [shared eligibility boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation). This report's missing Combat Lab hireling route concerns canonical catalogue/build inputs and combat projection, not an absent shared eligibility module. Campaign hiring services remain outside Combat Lab. Revalidate the reported access route before repair; retain source blocks and the separate local-product disposition in the follow-up register.

Task document for the hireling/command traceability lot of [T13](T13.md) under the
[implementation plan](T13-implementation-plan.md). It records the recomputed
partition, the real routes that exist today, the regressions added and the
limits found. Acceptance belongs to the coordinator; this delivery does **not**
certify T13.2, the Command effects or hired-sword integration.

## 1. Scope and entry state

- Objective: complete the traceability and construction coverage of the T13.2
  origins the T13.2c/d matrices left out — 62 hired-sword/Dramatis Personae rule
  origins and the 5 Mazzalupo Commands stored under `family=spell` — without
  implementing their combat mechanics.
- Boundary: Combat Lab and Warband Manager stay independent. This lot reads the
  canonical KB, the shared pure eligibility module and the maintained loaders;
  it starts no campaign flow, writes no campaign state and imports no
  campaign-service call.
- Entry revision: branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`,
  dirty working tree with the parallel T13.1/T13.2a–d, Shifty, Spectral Touch,
  eligibility-extraction and user interface/language changes. None of them was
  modified; this lot writes only its four authorized artifacts.
- Reservation: the coordinator's active-reservation table records the row
  `R2 — hireling/command traceability` (external agent B, `1b7f7cf` + dirty
  tree, new `tasks/T13-hirelings-commands.md`/`.csv`, new
  `tests/python/construction/test_t13_hireling_command_matrix.py`, evidence
  `build/cache/t13-parallel/hirelings-commands/**`). It matches the authorized
  paths exactly, so **no reservation discrepancy is reported**. `README.md` was
  read, not edited; it changed during the lot (the R2 row was added), which is
  recorded here as entry drift of a coordinator-owned file.
- Input fingerprints: `docs/knowledge/2a2b/tasks/T13-obligations.csv`
  SHA-256 `2a3b962e59bf65eba61191dffbf20f3fcdb44a68c7bc56863594913b20d9a6d6`
  (identical to the T13.0 accepted register), delivered CSV
  `5862f89e7d3682901537bbe9a622f464ab8c4b3b3eaa387a653ea87696293cd5`,
  new suite `b6d0d7622b1d1512fe52b1a7851724e46534e8f4e62dafda5edc6a8e2da47394`.
  The full input/evidence fingerprint record is `inputs.json` in the evidence
  directory.

## 2. Sources consulted

Coordination and rules: [README](../README.md), [T13](T13.md),
[implementation plan](T13-implementation-plan.md), [inventory](T13-inventory.md),
[execution follow-ups](T13-execution-follow-ups.md), [contracts](T13-contracts.md),
[automatic grants](T13-automatic-grants.md), [selectable equipment](T13-selectable-equipment.md),
[shared eligibility](../../../reference/eligibility.md) and
[implement and verify rules](../../../guides/implement-and-verify-rules.md).

Canonical material per origin: the rule node itself in
`sources/knowledge/catalog/hirelings/hired-swords/grade-2b.yaml`,
`sources/knowledge/catalog/hirelings/dramatis-personae/grade-2b.yaml` and
`sources/knowledge/catalog/campaign/magic.yaml`; the Mazzalupo band
`special-rules.yaml`/`profiles.yaml`; the campaign availability catalogue
`catalog/campaign/hired-swords-and-dramatis.yaml`; the maintained loaders
(`mordheim_knowledge/campaign.py`, `loader.py`); the construction compiler and
selection paths; the Warband Manager campaign adapters
(`mordheim_campaign/application/knowledge_port.py`, `hire_eligibility.py`) and
the generated eligibility bundle. Expectations were taken from those sources,
never from compiler output.

## 3. Partition and reconciliation

Recipe (read-only scripts under the evidence directory):

1. `T13-obligations.csv` is read as UTF-8 with BOM and `lots` parsed as JSON.
2. Origins with `T13.2` in `lots` and `family` in `{hireling, spell}`: **67**.
3. Counts: **62 hireling + 5 spell**; **67 unique `origin_key`s**; all resolve
   to existing canonical files (0 unresolved).
4. The 67 origins map to 62 distinct hireling rules and 5 distinct Command
   nodes; no canonical rule is shared by two origins inside the partition.

The recalculated totals **match the orientation exactly** (62 + 5 = 67). No
difference has to be explained, and the register was not rebuilt or edited.

| Metric | Value |
| --- | ---: |
| Register rows / rows with `T13.2` | 1,692 / 1,045 |
| Selected origins | 67 |
| Hireling origins (55 hired-sword + 7 Dramatis Personae) | 62 |
| Command origins (all under `lore.commands`) | 5 |
| Dispositions | included 33, mixed 30, construction 4 |
| Owner profiles | 25 (22 hired-sword, 3 Dramatis Personae) |
| Canonical files | `hired-swords/grade-2b.yaml` 55, `dramatis-personae/grade-2b.yaml` 7, `campaign/magic.yaml` 5 |
| Origins with an assigned `T13-Q` | 27 hireling (Q125, Q159–Q185) + 5 Commands (Q158) |

The sixth Command, `spell.commands.pay-them-no-heed`, is `excluded` (missile
target selection only, X3) with empty `lots`; it stays outside the partition
and is pinned by a dedicated test. The Mazzalupo band likewise keeps the
`wandering-knight--command-pay-them-no-heed` rule with a concrete X3 reason.

## 4. Routes traced

| Origin kind | Canonical representation | Route that exists today | Route that does not exist |
| --- | --- | --- | --- |
| 62 hireling rules | rule node inside the owner profile, **no `runtime` block**, no binding | `load_hirelings` (validated campaign catalogue) → `KnowledgePort.hireling_catalogue`/`hireling_roster_values`/`hireling_traits` → Warband Manager hire flows | No band/profile pair exists for any owner (`load_bands` index: 0/25 owners, 0/62 rules); `compile_fighter` never receives a hireling profile id. Free selection is anonymous (`custom:custom`) and applies none of these rules. |
| 5 Commands | `spell.commands.*` in `lore.commands` (roll, difficulty, effect) + band rules `wandering-knight--command-*` with `scope: NO`, `implemented: NO`, `grant: profile`, `binding: null` and a published reason; gate `wandering-knight--commands` | `load_campaign_catalog` exposes the lore document; the band runtime blocks and their reasons are published | No executable binding (`runtime_bindings` empty); no command-action consumer in the compiler or the combat engines; the compiled canonical Wandering Knight receives no Command effect and `available_special_rules` offers none. |

A passing integrity assertion proves resolution and publication only. It is
**not** construction proof and **not** combat evidence. The 62 hireling rules
have no Combat Lab access path at all in this revision; the Commands have a
published out-of-scope representation and an open source question (T13-Q158).

Cross-checks made while tracing:

- The register's `reuse_evidence`/`responsible_layers` for hirelings point at
  engine/construction files as future implementation targets, but no caller of
  those files consumes a hireling profile; the pointers remain planning hints.
- The shared eligibility module contains exactly one hireling-specific branch:
  equipment-access validation is skipped for `profile_id.startsWith("hireling.")`
  (`packages/typescript/domain/eligibility/index.ts` line 596). That exemption
  confirms hirelings are known to the shared module but does not construct them.
- The Warband Manager TypeScript kernel (`domain/campaign/kernel/hirelings.ts`)
  copies `starting_skill_ids` and profile rule ids into the hireling's `skills`
  without validating them against the skill catalogue. This is application-side
  evidence only; it was read, not executed by this lot.

## 5. Register statuses

`T13-hirelings-commands.csv` holds one row per `origin_key` with the columns
`origin_key, canonical_file, canonical_id, owner_id, family, disposition,
recipients, prerequisites, binding_or_representation, actual_access_path,
compiled_observable, consumer, test_or_evidence, status, question_ids, blocker,
proposed_owning_lot` (UTF-8, LF, 67 rows, 67 unique keys). Validated against the
recomputed partition: no missing or extra origin, no empty core field.

| Status | Origins | Meaning |
| --- | ---: | --- |
| `referential-integrity; no-access-route` | 35 | Canonical node and published catalogue node resolve; no construction/combat route exists. |
| `referential-integrity; no-access-route; source-blocked` | 27 | As above plus an open `T13-Q` gating the clause. |
| `referential-integrity; no-executable-binding; source-blocked` | 5 | Commands: published out of scope with a null binding; T13-Q158 open. |

`compiled_observable` is `none` on every row by design: no origin reaches a
compiled fighter. The status vocabulary distinguishes referential integrity
from construction, behaviour, route absence and source block, as required.

## 6. New tests

[tests/python/construction/test_t13_hireling_command_matrix.py](../../../../tests/python/construction/test_t13_hireling_command_matrix.py)
— **143 cases**, all through maintained APIs (`read_yaml`, `load_hirelings`,
`load_campaign_catalog`, `load_bands`, `compile_fighter`,
`available_special_rules`, `runtime_bindings`), no mocks of the layers under
test.

- Partition coverage: 67 origins, family counts, unique keys, exact canonical-id
  equality with the test tables, register question/owner/disposition fields, the
  canonical file per family and the documented provenance aliases (see finding 2).
- Canonical resolution per hireling origin (62 × 2): nested YAML rule node with
  name and effect, and published `load_hirelings` profile/rule membership with
  `normalization_status: normalized`.
- Route absence: the 25 owner profiles and 62 rules are disjoint from the band
  index; a free-selection build with Aldred Fellblade's characteristics stays
  `custom:custom` and carries none of the hireling rules (explicitly labelled as
  a negative control, not a canonical hireling construction).
- Commands (5 × 2): lore roll/difficulty/range text; band rule runtime scope,
  implementation, grant, null binding, published reason, empty executable
  bindings and `wandering-knight` recipient; the six-entry lore and its
  not-a-spell note; the gate rule; the compiled Wandering Knight and the
  availability surface.
- Partition boundary: the excluded sixth Command is pinned (register
  `excluded` + empty lots, still present in `lore.commands`).

## 7. Existing coverage reused

Executed as concrete dependencies of this lot (logs in the evidence directory):

- `tests/python/knowledge/test_campaign_loaders.py` — **14 passed**: the
  campaign/hireling loader contract (`load_hirelings`, `load_campaign_catalog`)
  reused by the new integrity tests.
- `tests/python/campaign/test_hire_eligibility.py` — **15 passed**: the
  Warband Manager consumer of the hireling catalogue and its declared traits.
- `tests/python/architecture/test_documentation.py` — **1 passed**: local
  Markdown links, including this document and its evidence links.

Not executed: broader suites, the TypeScript hireling kernel tests and any CI
run. The TypeScript consumer above is recorded as read evidence, not as a
validated dependency of this lot.

## 8. Findings and discrepancies

1. **No Combat Lab construction route exists for any of the 62 hireling
   origins.** The owner profiles are absent from `load_bands` and the rules have
   no `runtime` block; free selection never receives a hireling profile id.
   Hiring lifecycle belongs to Warband Manager, while admitted hireling combat
   clauses still belong to Combat Lab. Route absence is an integration gap,
   not a source-backed exclusion. T13.2 must provide a canonical local-participant
   construction route without campaign state/services for the included clauses;
   any later disposition change requires clause-level source review under the
   existing scope agreement. No route was invented by this traceability lot.
2. **Register `origin_owner` drops the `-miracle-workers` suffix on three
   variant profiles.** Canonical rule ids keep
   `hireling.hired-sword.{priest-of-morr,warrior-priest-of-sigmar,wolf-priest-of-ulric}-miracle-workers`,
   while 11 register rows name the unsuffixed profiles. The new suite pins the
   exact alias set so the variants are never merged with the Town Cryer/sibling
   profiles; the register itself was not edited.
3. **Aldred Fellblade's `starting_skill_ids` reference three undeclared
   skills.** `skill.protection-of-sigmar`, `skill.righteous-fury` and
   `skill.sign-of-sigmar` do not resolve in `catalog/skills` (82 entries; the
   catalogue has `skill.sigmar-s-sign` and `skill.red-fury` instead), and
   `load_hirelings` validates rules and item references but not starting
   skills. The Warband Manager kernel copies those ids into the hireling's
   skills and the label lookup silently falls back to the raw id. Recorded as a
   referential gap for KB/source review; no source repair was made.
4. **The Commands are orders, not battle spells, and remain unimplemented.**
   `lore.commands` states they do not count as spells and the knight is not a
   wizard; each band rule is declared `scope: NO`/`implemented: NO` with a null
   binding and a specific reason (rallied Leadership, extra movement,
   to-hit aura, disengagement, out-of-action threshold). Activation,
   difficulty rolls, recipients, hearing/range, movement, escape and leadership
   consequences are not tested because no consumer exists.
   T13-Q158 is the real conflict: the common note grants Commands to allies
   within 6" who can hear him, while individual Commands name 12"
   (Raise Our Insignia, Be On Guard), 6" (Move, Ye Miscreant) and 4" (Follow Me,
   Art Thou Ready). The contradiction was not resolved here.
5. **The sixth Command stays excluded.** `spell.commands.pay-them-no-heed`
   changes only missile target selection (X3) and has empty `lots`; it is not
   part of this partition and no test constructs expectation for it beyond the
   boundary pin.
6. **Reference integrity that does hold.** All 62 rule nodes resolve in their
   canonical files and in `load_hirelings`; every equipment `item_id` of the
   catalogue (74 distinct across 130 profiles) already passes the loader's
   item-resolution pass, so the 62 origins inherit that guarantee; the five
   Command band rules all resolve with their published reasons.

## 9. Commands, results and evidence

All commands run from the repository root with `python -X utf8`. Evidence under
`build/cache/t13-parallel/hirelings-commands/`:

| Command | Result | Evidence |
| --- | --- | --- |
| `python build/cache/t13-parallel/hirelings-commands/partition.py` | 67 selected (62+5), 0 unresolved canonical files | `partition.json`, `partition.csv`, `partition-summary.txt` |
| `python build/cache/t13-parallel/hirelings-commands/trace.py` | 67 origins traced; 0 unresolved nodes; 0 band-index hits; 5/5 Command rules found | `trace.jsonl` |
| `python build/cache/t13-parallel/hirelings-commands/integrity_probe.py` | 25 owners, 0 missing rules/owners, 0 band overlap, 3 unresolved starting skills, 5 Command states | `integrity.json`, `integrity-probe.txt` |
| `python build/cache/t13-parallel/hirelings-commands/report.py` | 67-row register: 35/27/5 statuses | `T13-hirelings-commands.csv`, `register-summary.json` |
| `python build/cache/t13-parallel/hirelings-commands/validate_csv.py` | 67 rows, 67 unique keys, fields exact, no missing/extra origin, UTF-8 without BOM, LF | `csv-validation.json` |
| `python build/cache/t13-parallel/hirelings-commands/run_suite.py` | 4 runs, all exit 0: new suite **143 passed**, loader contract **14 passed**, hire eligibility **15 passed**, docs links **1 passed** | `run-record.json`, `pytest-*.txt`, `pytest-*.xml` |
| `python build/cache/t13-parallel/hirelings-commands/inputs.py` | Input/evidence SHA-256 record | `inputs.json` |

The four pytest runs were repeated after this document and the CSV were
finished, because the `docs-links` case validates the Markdown kept by this lot;
the table records the final run. No later change invalidated any other row.

If `build/cache` is lost, the scripts listed above are also lost. Reproduce the
maintained evidence directly from the repository root instead:

```powershell
python -X utf8 -m pytest tests/python/construction/test_t13_hireling_command_matrix.py -q -p no:cacheprovider
python -X utf8 -m pytest tests/python/knowledge/test_campaign_loaders.py tests/python/campaign/test_hire_eligibility.py -q -p no:cacheprovider
python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q -p no:cacheprovider
```

To reconcile or rebuild the CSV, apply the filter in section 3 to the maintained
origin register and retain its `origin_key`, canonical identity, disposition and
question fields. Resolve each hireling rule recursively in its canonical file
and its owner through `load_hirelings`; the test's `HIRELING_ORIGINS` retains the
canonical owner/variant mapping. Compare those identities with `load_bands` and
the profile-selection path. For commands, use the test's `COMMANDS` mapping to
read the lore node, band rule, `runtime_bindings`, compiled Knight and availability
API. Record only the observed route/representation and use section 5's status
definitions; update observations if the implementation changed. Section 8 names
the alias and unresolved starting-skill checks. This reproduces the trace without
requiring any ignored script, and does not regenerate historical log hashes.

## 10. Limits and handoff

- Rule-node and owner resolution is proved; the starting-skill gap means full
  catalogue referential integrity is not certified. Construction, combat resolution, backends
  and product access are **not**. `compiled_observable` is `none` for all 67 rows.
- No production, KB, specification, model, engine, interface or language change;
  no implementation flag, scope, binding, question or digest was changed.
- No agent was launched, no commit/push was made and no shared artifact was
  regenerated.
- Reservation release and acceptance belong to the coordinator; see section 12.
  T13.2 and the dependent mechanisms remain in progress.

## 11. Proposed follow-up register entries

The following proposals were reviewed by the coordinator and recorded as
T13-F036–F039 in [T13 execution follow-ups](T13-execution-follow-ups.md).
The register owns their current status and closure criteria. The route-absence
proposal was corrected to preserve included combat scope.

### T13-F036 — Hireling/Dramatis Personae origins have no Combat Lab route

- **Status/type:** open; canonical construction/product-access gap. Detected in the R2
  hireling/command lot (2026-10-01). All 62 assigned hireling rule origins
  resolve in `load_hirelings` but no band/profile pair exists for their 25
  owners; `compile_fighter` cannot reach them and free selection is anonymous.
- **Evidence:** [partition, routes and 143-case suite](T13-hirelings-commands.md),
  `build/cache/t13-parallel/hirelings-commands/integrity.json`,
  `T13-hirelings-commands.csv` (status `no-access-route`).
- **Accountable owner / executor:** Coordinator; executor unassigned.
- **Target lot / dependencies:** T13.2, coordinated with the product boundary
  and the T13.1 local-participant contracts. The register's engine/compiler
  `responsible_layers` are future pointers, not existing consumers.
- **Resume:** before certifying any hireling construction clause or accepting
  T13.2 closure for these origins.
- **Close when:** a canonical local construction route (without campaign
  state/services) is implemented with source-derived tests for included clauses,
  with bindings/consumers and product access evidenced in their owning lots.
  Route absence alone must not reclassify combat rules as campaign-owned.
  Existing `T13-automatic-grants.csv`/`T13-selectable-equipment.csv` boundaries
  stay unchanged either way.

### T13-F037 — Aldred Fellblade's starting skills do not resolve in the skill catalogue

- **Status/type:** open; KB referential gap. Detected in the R2 lot.
  `hireling.dramatis.aldred-fellblade.starting_skill_ids` declares
  `skill.protection-of-sigmar`, `skill.righteous-fury` and
  `skill.sign-of-sigmar`; none exists in `catalog/skills`, and
  `load_hirelings` does not validate starting skills. The Warband Manager
  kernel copies the ids into the warrior's skills.
- **Evidence:** `integrity.json` (`referential_gaps`), `hireling-notes.txt`,
  `sources/knowledge/catalog/hirelings/dramatis-personae/grade-2b.yaml:48-52`.
- **Accountable owner / executor:** Coordinator; executor unassigned.
- **Target lot / dependencies:** KB source review; the hireling catalogue
  contract and the Warband Manager consumer. Distinct from T13-F027 (empty
  effect text) and from T13-F035 (eligibility revalidation).
- **Resume:** when the source manuscript for Aldred is reviewed, before relying
  on these skills or closing the profile's origins.
- **Close when:** each skill id has a reviewed source-backed target (existing
  skill, rule id or explicit unsupported disposition) and, if the loader should
  enforce it, a scoped validator decision with affected-data review. No id was
  renamed, guessed or deleted by this lot.

### T13-F038 — Register `origin_owner` drops the `-miracle-workers` suffix for three variants

- **Status/type:** open; traceability identity mismatch. Detected in the R2 lot.
  Eleven register rows name `hireling.hired-sword.priest-of-morr`,
  `...warrior-priest-of-sigmar` and `...wolf-priest-of-ulric` while the
  canonical rule ids and profiles keep the `-miracle-workers` suffix (the
  inventory's identity rule).
- **Evidence:** `T13-hirelings-commands.csv`, the suite test
  `test_register_owner_aliases_are_only_the_documented_miracle_workers_variants`,
  `build/cache/t13-parallel/hirelings-commands/trace.jsonl`.
- **Accountable owner / executor:** Coordinator (register owner); executor
  unassigned. The register must not be edited by this lot.
- **Target lot / dependencies:** T13.0 register maintenance / T13.2 identity
  reconciliation.
- **Resume:** the next time the register is maintained, before joining these
  rows to Town Cryer or sibling profile identities by name.
- **Close when:** the register either keeps the alias with an explicit note or
  uses the canonical suffixed owner; the canonical catalogue is not renamed to
  match the alias.

### T13-F039 — Mazzalupo Commands: common range note vs individual ranges (T13-Q158)

- **Status/type:** open; source decision plus deferred mechanism. Detected
  again in the R2 lot. The five included Commands are declared out of scope
  with null bindings; the lore note says allies within 6" who can hear the
  knight and one Command per model per turn, while individual Commands print
  12" (Raise Our Insignia, Be On Guard), 6" (Move, Ye Miscreant) and 4"
  (Follow Me, Art Thou Ready). `pay-them-no-heed` stays excluded X3.
- **Evidence:** [Commands trace](T13-hirelings-commands.md#4-routes-traced),
  `integrity.json` (`commands`), `T13-hirelings-commands.csv`,
  `sources/knowledge/catalog/campaign/magic.yaml:4612-4737`,
  `sources/knowledge/bands/mordheim/mazzalupo-web/special-rules.yaml`.
- **Accountable owner / executor:** Coordinator (source question); executor
  unassigned for any implementation.
- **Target lot / dependencies:** T13.4/T13.5/T13.6 per the inventory; T13-Q158
  gates activation cases. Coordinate with the psychology source gate where a
  Command touches Leadership/Rout.
- **Resume:** before dispatching any command-action mechanism or accepting a
  case for these origins.
- **Close when:** T13-Q158 has a reviewed resolution and, if the mechanism is
  accepted, a modular command-action consumer proves activation, difficulty,
  recipients, movement/leadership or escape consequences for each Command with
  source-derived tests, then applicable backends. Registration alone does not
  close it.

## 12. Coordinator review — 2026-10-01

Accepted as a bounded traceability/representation and test delivery. All input
and evidence hashes in `inputs.json` matched before this documentary review;
the four XML reports contain 143/14/15/1 passing cases, with no failures, errors
or skips. These matching external runs were inspected and reused, not rerun as
a complete lot. A coordinator probe independently reconciled the CSV's 67 unique
origin keys and `compiled_observable=none`, and reproduced Aldred's three missing
starting-skill targets through the maintained loaders. Evidence:
`build/cache/t13-parallel/hirelings-commands/coordinator-review.json`.

Two documentary corrections were required: route absence does not permit
campaign reclassification of admitted combat clauses; reconstruction must use
maintained files/APIs rather than assume lost cache scripts still exist. Four
findings, not three, are now registered as T13-F036–F039. The agent's `inputs.json`
retains the pre-review document hash; only this maintained report was corrected,
while its CSV, suite and production inputs remain unchanged. The coordinator's
post-edit documentation check is recorded in `coordinator-docs.xml`.

Reservation released. T13.2 remains in progress; no source question, production
route, command mechanism or backend is certified by this acceptance. No source,
flag, binding, scope, digest, generator, UI/language or production code changed;
no agent was launched, commit created or push made.
