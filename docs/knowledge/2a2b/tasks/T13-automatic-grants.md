# T13.2c — Automatic grants of profiles and bands: trace and coverage

L05 construction checkpoint — 2026-10-03: [current delivery](T13-canonical-choices.md) supersedes the historical missing named-table/access routes, eight false markers and incomplete Runt active-equipment binding below. Seven pending recipient channels and configured Bloodline access are corrected; remaining source/effect gates are explicit. The retained CSV is entry evidence, not a current implementation claim.

Current partition update — 2026-10-03: [L04 canonical Shifty activation](T13-shifty.md#l04-canonical-activation--2026-10-03)
moves `halfling-elder--shifty` from `profile` to `selectable`, as required by its
printed skill table. Live T13.2 band-rule origins now reconcile to **828 automatic
(635 profile + 193 band) + 55 selectable = 883**. The historical 829-row CSV and
counts below remain entry evidence; they do not describe current Shifty access.

> Current ownership — 2026-10-02. This is an accepted historical traceability/test delivery, not a current inventory of unimplemented validators. Both products now use the existing [shared eligibility boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation); Python decision references below identify the examined adapter revision. The companion CSV retains that historical snapshot. Before dispatching any old availability, recipient or restriction finding, [F035 in the follow-up register](T13-execution-follow-ups.md) must classify current canonical facts, the shared decision, transport and the separate runtime-support/compiled-effect gate. Accepted observations and counts are preserved; no finding is closed by this note.

Task document for the automatic-grant lot of [T13](T13.md) under the
[implementation plan](T13-implementation-plan.md). It records a review of the
construction coverage of the `profile`/`band` grants, the regressions added and
the concrete limits found. Accepted by the coordinator on 2026-10-01 as a
traceability and construction-test lot only. The [initiative checklist](../README.md)
owns task status; this acceptance does not certify T13.2 or combat semantics.

## 1. Scope and entry state

- Objective: prove what reaches the compiled fighter from the canonical KB for
  the automatic grants (`runtime.grant` `profile` or `band`), for which
  recipients and through which route. No production mechanic is implemented or
  changed by this lot.
- Combat Lab and Warband Manager stay independent: this lot uses only the
  canonical KB, `FighterBuild` and `compile_fighter`. No campaign services,
  identifiers or state are involved.
- Entry: branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`
  ("chore: snapshot UI, localization and T13 planning"), one commit ahead of
  `origin/2A2B`. The working tree already carried T13.1/T13.2a/T13.2b, the
  Shifty and Spectral Touch lots in review, the user's parallel application and
  engine changes and the KB edits; they were preserved untouched. This lot
  writes only its four authorised artifacts (section 9).
- Reservation: the checklist table already contains the T13.2c row
  ("concesiones automáticas: recorrido y regresiones", external agent A,
  files reserved, state *Reservada*), so no reservation discrepancy is reported
  this time. T13.2b appears accepted in the same table.

## 2. Sources consulted

Coordination and rules: [README](../README.md), [T13](T13.md),
[implementation plan](T13-implementation-plan.md),
[inventory](T13-inventory.md), the authored register
[T13-obligations.csv](T13-obligations.csv),
[contracts](T13-contracts.md), [characteristic bonuses](T13-characteristic-bonuses.md),
[implement and verify rules](../../../guides/implement-and-verify-rules.md) and
[permanent design rulings](../../../decisions/design-rulings.md).

Per origin, the canonical rule node itself (`sources/knowledge/bands/mordheim/<band>/special-rules.yaml`),
its `runtime` block, the published binding parameters and the shared execution
contract (`sources/knowledge/catalog/mechanics/execution.yaml`). Expectations in
the new tests come from those sources, never from the compiler output.

## 3. Partition and reconciliation

Recipe (read-only scripts under `build/cache/t13-parallel/automatic-grants/`):

1. `T13-obligations.csv` is read as UTF-8 with BOM and `lots` as JSON.
2. Origins with `T13.2` in `lots` and `family = band-rule`: **883**.
3. Each origin resolves `canonical_file` + `canonical_id`; **0 unresolved**.
4. Keep `runtime.grant` `profile` or `band`: **829** (the other 54 grants are
   `selectable` and belong to the T13.2d equipment/selectable matrix).
5. `origin_key` is preserved on every row of the register.
6. The 829 origins map to 829 distinct canonical rules (no rule is shared by two
   origins inside this partition), so grouping keeps the origin trace without
   duplicating evidence.

The recalculated total **matches the orientation count exactly**: 829 = 636
`profile` + 193 `band`. No difference to explain; T13.0 was not rebuilt and its
dispositions were not changed.

| Cohort | Origins | Meaning |
| --- | ---: | --- |
| `implemented: YES` with a binding | 60 | A binding route is declared (61 bindings; `band--bow-restrictions` publishes a compiler and a profile binding); declaration alone does not prove execution of every clause. |
| `implemented: YES` without any binding | 8 | Marker inconsistency: scope `LATER`, every effect binding `null`; the compiler loop has nothing to apply. |
| `implemented: NO` | 761 | `runtime_bindings` does not activate these rule nodes; this does not prove the fighter lacks related effects from other grants or profile traits. |
| **Total** | **829** | |

Binding routes among the 60 active rules: 32 `trait`, 15 `mechanic`, 5
`compiler`, 9 `profile`. 115 of the 829 origins carry an open `T13-Q`
question; 19 origins carry the `source-blocked` disposition (18 not implemented
plus `band--knights-feats`).

## 4. Routes traced

| Grant kind | Real path in `mordheim_construction` | Observable checked |
| --- | --- | --- |
| `trait` | `runtime_bindings(rule, "trait")` → `_profile_rule_traits` → compiled `traits` | `global_effects.poison_immunity`, `.frenzy`, `natural_armour_save`, trait tags (`concussion_immune`, `poisonous_injury`) |
| `mechanic` | `runtime_bindings(rule, "mechanic")` → `_profile_rule_mechanics` → `global_ids` → `execution.yaml` passive effects | `out_of_action_threshold`, `regeneration_save`, `priority`, skill tags |
| `compiler` | `runtime_bindings(rule, "compiler")` → automatic compiler contract (`COMPILER_CONTRACTS` or `PROFILE_RULE_EFFECTS`) | `construction_tags`, species saves, extra natural attack, `missile_weapon_limit` |
| `profile` | `runtime_bindings(rule, "profile")` → `automatic_profile_bindings` → selection/validation | legal/illegal selection verdicts (equipment, skill categories) |

Every recipient list is read from the canonical rule (`applies_to.profile_ids`,
`eligibility`, or band-wide `applies_to.band`). A passing assertion proves the
**construction** connection; it does not prove combat execution. Tag-only
observables (`skill.ignore-pain`, `concussion_immune`, `poisonous_injury`) are
labelled as such in the register.

## 5. Register statuses

`T13-automatic-grants.csv` holds one row per origin with
`origin_key, canonical_file, canonical_id, grant, destinatarios revisados,
binding, recorrido real, observable probado, test/caso, estado, bloqueo o
pregunta pendiente`.

| Status | Origins | Meaning |
| --- | ---: | --- |
| `probado` | 47 | New regression exercises the real compiler. |
| `probado (con limite)` | 3 | Part of the clause has no reachable compiled example. |
| `cubierto por prueba existente` | 5 | An existing test proves the published contract (KB/Web). |
| `pendiente de implementacion` | 743 | `implemented: NO`; the KB reason and scope are recorded per row. |
| `bloqueado por fuente` | 20 | Open source/interpretation question gates the clause. |
| `discrepancia` | 11 | Active route with a concrete mismatch or missing executable (reproducer attached). |
| **Total** | **829** | |

## 6. What is now proved (new regressions)

`tests/python/construction/test_t13_automatic_grant_matrix.py` — 88 cases over
the canonical loading path (`FighterBuild` + `compile_fighter`, mandatory
choices respected explicitly). Groups:

- **Poison immunity** (21 rules): recipients and valid non-recipient controls
  (`corpse-master`, `mad-scientist`, `acolyte`, `waif`, `vampire`, `seer`,
  `goblin-bully`, `watch-captain`, `turnkeys` sibling bands).
- **Natural armour**: band-wide `band--bark-skin` 6+, `treekin--redwood` 4+
  replacing it (no stacking), four Halfling recipients 6+, Talismanic Tattoos
  6+, `lizardmen-lus` species saves (Saurus 5+, Skinks 6+, Kroxigor 4+ with no
  double application), `lords-of-the-marsh-mim` Young Nobles 6+.
- **Frenzy** (2 rules) with non-recipient controls.
- **No Pain** (8 rules, tag-only) with controls.
- **Regeneration**: Warpstone Troll 4+ and fire block; absence in a valid
  control.
- **Hard to Kill** (3 rules): threshold 6 + tag; Hard Head (3 rules): trait tag.
- **Frantic** (`night-goblins-kaz`): `skill.always-strikes-first` tag and
  priority 1 from its KB execution contract; the same-named `-mic` rule uses a
  different binding and is a different origin.
- **Poisonous** (Gigantic Spider) tag.
- **Compiler contracts**: lizardmen scaly skin, one independent bite attack,
  Saurus prohibitions scoped by `eligibility`, `compiler.bow-discipline`
  (`missile_weapon_limit = 1`), and the consumed `runts--teeny-hands` armour
  prohibition (legal case compiles, illegal case raises).

Expectations are derived from the rule text, its binding parameters and
`execution.yaml`; no expectation was copied from the compiler or from the
compiled output.

## 7. Existing coverage reused

- `tests/python/construction/test_construction_blockers.py` proves the KB
  publication of the seven T09 §6 clauses (skill tables, Silence tokens, Teeny
  Hands, bow limit and Cleric exemption). The behavioural verdict lives in
  `tests/typescript/domain/campaign/construction-blockers.test.ts`; that Web
  consumer stays outside T13, so those origins are marked *covered by an
  existing test* with the compiled-observable gap recorded.
- `tests/python/construction/test_construction_contract_tables.py` proves the
  absorbed blockers publish a construction binding.
- `tests/python/construction/test_profile_bindings.py` and
  `test_special_bindings.py` cover sibling selected-rule routes (Middenheim,
  Dark Elf special skills, Nurgle blessings, PROFILE_RULE_EFFECTS handlers).
  None of them exercised the automatic partition rules asserted here.

## 8. Findings, discrepancies and limits

Reproducers live in `build/cache/t13-parallel/automatic-grants/trace.jsonl`
(every rule compiled for a recipient and, where the source filters, a control)
and in the register rows.

1. **Fimir Warriors 5+ vs compiled 6+** (`lords-of-the-marsh-mim`,
   `band--scaly-skin`). The rule text says *"Fimir Warriors have a 5+ armour
   save"*; the shared `compiler.lizardmen-scaly-skin` contract gives every
   non-Saurus/Kroxigor profile 6. Young Nobles 6+ is asserted as source-correct;
   `fimir-warriors` is recorded as a discrepancy, not blessed by a test. No
   production change was made.
2. **Boglars Regeneration 5+ vs compiled 4+** (`boglars--regeneration`). The
   shared `skill.regeneration` mechanic compiles 4+ and blocks fire; the printed
   Boglar rule regenerates on 5 or more. Registered as a discrepancy.
3. **Curse of the Revenant 5+ vs compiled 4+** (`strigoi-vampire--curse-of-the-revenant`).
   T13-Q013 is open (timing and whether regeneration/fire restrictions apply);
   the value mismatch is recorded as part of the blocked clause and no
   expectation was asserted.
4. **Eight `implemented: YES` rules carry no binding** (scope `LATER`, all
   bindings `null`): `dwarf-slayer-cult-web` Hard Head / Hard to Kill,
   `house-guard-sc` Dueling Pride / Pikewall, `lords-of-the-marsh-mim` Spiked
   Tail x2, `underworld-alliance-mim` One Upmanship, `watchmen-mim` Scryer
   (also T13-Q104). The marker promises an implementation that never reaches
   compilation through that rule node; related effects may still exist through
   other rules or profile traits. The register records the KB reason for each one.
   The loader already rejects a missing binding for an implemented effect with
   scope `YES`, but these eight have scope `LATER`, which the current contract
   permits. Extending the structural restriction needs a contract decision and
   scoped review; no new validator was implemented in this lot.
5. **Skill tables without a compiled example**: for the four `adventurers-kaz`
   tables, `band--knights-feats` and `dwarf-troll-slayers--slayer-skills`, the
   `profile.skill-access` binding is loaded and widens the `special` category,
   but no named skill can be selected through `compile_fighter`: the consumer
   reads only `category`, several named skills are not mechanics, and the
   remaining ones fail the band source gate in
   `_validate_profile_selections`. This is a real construction gap for Combat
   Lab; the KB publication is covered by an existing test.
6. **Band grants ignore `applies_to.profile_ids`**: `_applicable_rules` reads
   only `applies_to.band` and `eligibility` for band grants, so e.g.
   `band--dwarf-special-skills` (profile_ids `[dwarf]`) is loaded for every
   `adventurers-kaz` profile. The over-broad access is latent today (no legal
   special skill exists), so it is registered rather than asserted.
7. **Unconsumed equipment parameters**: `band--the-silence`
   (`blackpowder`/`animal`) has no Python consumer; the equipment list already
   blocks the only blackpowder mechanic (pistol), so the prohibition cannot be
   observed and no test blesses the omission.
   `band--bow-restrictions` is proved only for the consumed
   `max_missile_weapons = 1` (via `compiler.bow-discipline`); its crossbow ban,
   mandatory bow and Cleric exemption have no Python consumer, and no crossbow
   mechanic exists in the duel catalogue.
   `runts--teeny-hands` binds the armour prohibition that is proved; the printed
   single-one-handed-weapon clause has no binding.
8. **Canonical data observation**: many `Immune to Poison` / `No Pain` rules
   have an empty `effect` text (the rule name and the binding carry the
   meaning), and `pikemen-pikewall`/`band--dueling-pride` etc. remain markers.
   No KB edit was made.
   **Correction after accepted R0 review, 2026-10-01:** empty local effects on
   the 12 Immune to Poison and eight No Pain subjects resolve via `rule_ref`
   to non-empty canonical shared text. They are not missing source text and
   need no duplicate prose. [T13-F027 / reference review](T13-source-fingerprint-review.md)
   closes that observation only; marker, variant-source and combat-proof gaps
   retain their separate findings. The CSV preserves its original trace notes.
9. **Talismanic Tattoos is bounded compilation evidence.** The test verifies
   `natural_armour_save=6` as published by the canonical binding. The text calls
   for a special save unaffected by Strength, spells or abilities. The assertion
   does not verify that protection or adjudicate whether the natural-armour
   binding faithfully represents the printed save. That semantic reconciliation
   remains with the save-mechanism lot.

Not covered by this lot: the 54 `selectable` grants (T13.2d), combat execution
of any of the traced connections, NumPy/native backends, and the T13-Q
questions themselves.

## 9. Commands, results and evidence

All commands run from the repository root with `python -X utf8`. Exit code 0
unless noted. Evidence under `build/cache/t13-parallel/automatic-grants/`:

| Command | Result | Evidence |
| --- | --- | --- |
| `python -X utf8 build/cache/t13-parallel/automatic-grants/partition.py` | 883 selected, 829 automatic (636 profile + 193 band), 0 unresolved | `partition.json`, `partition.csv`, `partition-summary.txt` |
| `python -X utf8 build/cache/t13-parallel/automatic-grants/trace.py` | 68 implemented rules compiled with recipients and controls | `trace.jsonl`, `source-notes.txt` |
| `python -X utf8 build/cache/t13-parallel/automatic-grants/report.py` | register generated (829 rows) | `T13-automatic-grants.csv`, `register-summary.json` |
| `python -X utf8 -m pytest tests/python/construction -q --ignore=tests/python/construction/test_t13_selectable_equipment_matrix.py` (the `construction` scope of `mordheim-utils.py`) | **203 passed** | `pytest-construction-scope-excluding-t13.2d.txt` |
| `python -X utf8 -m pytest tests/python/construction/test_t13_automatic_grant_matrix.py -q --junitxml=...` | **88 passed** | `pytest-new-suite.txt`, `new-suite.xml` |
| `python -X utf8 -m pytest tests/python/knowledge/test_catalog.py tests/python/combat/modular/test_catalogue_runtime.py tests/python/combat/vectorized/test_rule_families_a.py tests/python/combat/vectorized/test_rule_families_b.py tests/python/architecture/test_documentation.py -q` | **66 passed** | `pytest-dependent.txt` |

Concurrent work observed while validating: the T13.2d lot created
`tests/python/construction/test_t13_selectable_equipment_matrix.py` during
this delivery (untracked, outside T13.2c's authorization). A scope run with it
present reported **9 failed, 249 passed**: the nine cases are that lot's own
pending-selectable gate
(`test_pending_selectable_origins_refuse_with_their_published_source_reason[...]`
for `protectorate-of-sigmar-lotd3/warrior-priest`, `araby-smugglers-sar/rais`,
`sea-ghosts-mim/wayfinder` Dances and `strigoi-kaz/vampire`). Their names and
log are kept in `foreign-failures-t13.2d.txt` and `pytest-construction-scope.txt`;
none of them touches the 829 automatic origins, and excluding that file the 203
cases of this lot plus the pre-existing construction tests pass. They are
recorded here as observations of an intermediate T13.2d file, not attributed to
T13.2c and not repaired by it. They are no longer current failures: the coordinator's
final combined run below includes the accepted T13.2d suite and passes.

Files delivered by this lot:

- [test_t13_automatic_grant_matrix.py](../../../../tests/python/construction/test_t13_automatic_grant_matrix.py)
- [T13-automatic-grants.csv](T13-automatic-grants.csv)
- [T13-automatic-grants.md](T13-automatic-grants.md) (this document)
- evidence under `build/cache/t13-parallel/automatic-grants/` (ignored)

No README, `T13.md`, inventory, `compiler.py`, `contracts.py`, `selection.py`,
model, engine, KB, existing specification, interface or language file was
modified. No commit or push was made and no agent was launched.

## 10. Limits and handoff

- The register proves construction, not combat: activation, dice, timing,
  duration and backend parity remain T13.3–T13.6/T14 work.
- The intermediate T13.2d failures in section 9 are superseded by the passing
  combined coordinator run below; the original logs remain as historical evidence.
- The discrepancies above need an owner decision (KB contract vs compiled
  value); this lot only reproduces them.
- The 743 pending origins need the corresponding mechanism lots; their KB scope
  and reason travel in the register.
- Reservation released after coordinator acceptance. T13.2 remains in progress.

## 11. Coordinator review — 2026-10-01

- Independently resolved the register and canonical YAML: exactly 829 assigned
  origins, 829 unique CSV keys and canonical rule identities, no missing/extra
  origin or target mismatch; 636 profile grants and 193 band grants. All 115
  question-bearing origins retain their question reference. Status totals match
  section 5; the eight marker-only entries and 61 binding kinds match section 3.
- Final combined run: **145 passed** (88 automatic-grant tests, 56 accepted
  selectable/equipment tests and one documentation check), retained in
  `build/cache/t13-parallel/automatic-grants/coordinator-review.xml`. External
  **203 construction** and **66 dependent** passing logs were inspected and
  reused; those broader suites were not rerun by the coordinator.
- Direct compilation reproduces the Fimir Warriors 6+ / printed 5+, Boglars
  regeneration 4+ / printed 5+, and Curse of the Revenant 4+ / printed 5+
  differences. `coordinator-findings.json` retains values, identities and
  partition reconciliation. No open source question was resolved.
- Narrowed documentation and one test comment to distinguish a declared binding,
  compiled observable and proved combat behavior. `concussion_immune` does have
  a modular injury consumer; this matrix tests its tag only and does not certify
  that consumer.
- Accepted as traceability and construction-test coverage. No production, KB,
  semantic specification, optimized backend, interface or language change;
  no new audit, mechanic implementation, agent launch, commit or push.
