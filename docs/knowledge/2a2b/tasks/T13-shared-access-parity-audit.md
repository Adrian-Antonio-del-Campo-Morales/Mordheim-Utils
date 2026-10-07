# T13 — H7 shared item/skill access parity audit

Deep audit of the shared item/skill access facts: whether the projection each
consumer reads is the projection the shared decision expects, and whether
Combat Lab (desktop) and Warband Manager (web) obtain the same verdicts when
they need them. The audit itself is read-only; the four defects it found were
repaired in the materializer and in one shared predicate, with regressions.

Status: delivered for coordinator review. Nothing here accepts or closes a
finding, no source of the canonical KB was edited, and no commit or push was
made. The generator, the shared module, the fixture and the artefact
regressions were written under this lot; everything else in the tree belongs to
other concurrent lots.

## 1. Entry, harness and method

- Branch `2A2B`, HEAD `820d149`, working tree with 301 dirty entries at entry
  (2026-10-05, `git status --porcelain`) owned by other lots; the audit never
  wrote a KB or application file.
- Harness: `build/audit/access_parity_audit.py` (workspace-local, both `build/`
  and `outputs/` are gitignored). It drives the maintained bundle
  (`mordheim_construction.eligibility.call`, i.e. the same MiniRacer + embedded
  `_eligibility.js` route Combat Lab uses) once per fact source and compares,
  for every profile of `mordheim` + `trollheim`:

  | Consumer modelled | Facts read |
  | --- | --- |
  | Combat Lab (desktop) | canonical KB YAML through `package_facts` + the installed catalogue via `catalogueItemFacts` |
  | Warband Manager (web) | the materialized artefact through the `profileFactsOf` / `itemFactsOf` shapes, including the boundary normalization the adapter applies (`tags` omitted by the artefact become `[]`) |

  Compared groups: band forbids/limits; per-profile access (offers ∪ fixed kit,
  normalized by `mechanic_id`), forbids, declared skill access, skill lists,
  rule ids and promotion access; per-item verdicts (`equipmentIssue`) over every
  item either side offers; per-skill verdicts (`skillIssue`) over every
  published skill; the Combat Lab pickers (`profileEquipment`,
  `catalogueEquipment`, `skillChoices`, `profileSkillLists`); and the catalogue
  facts themselves (items/skills: tags, mechanic, kind, category).
- Verdict calls are memoized exactly. `equipmentIssue`/`skillIssue` are pure
  over the acknowledged inputs, so an equal-input pair is a proof, not a
  sample; the per-skill enumeration is skipped only where the
  (`skill_access`, `skill_lists`) projections are equal **and** the catalogue
  skill facts are identical, and the skip is reported
  (`skill_verdict_skipped_profiles`).
- Runs:

  ```
  python -X utf8 build/audit/access_parity_audit.py --bands-limit 5            # smoke
  python -X utf8 build/audit/access_parity_audit.py --output build/audit/access-parity-postfix.json
  python -X utf8 tools/knowledge/generate_knowledge_web.py [--check]
  ```

  Evidence: `build/audit/access-parity-findings.json` (baseline, merged),
  `build/audit/access-parity-postfix.json` and
  `build/audit/access-parity-postfix2.json` (post-fix, two runs).
- Baseline caveat: the baseline sweep ran against the workspace build copy
  `build/generated/knowledge-web`, which was older than the published
  `outputs/web-public/knowledge` (§6). Each repaired defect was diagnosed by
  reading the generator and confirmed by regression tests, so the attribution
  stands; the baseline counts are cited as observed on that stale copy.

## 2. Defects found and repaired

### H7-D1 — band-wide skill grants reached the desktop but not the web

Rules with `applies_to.band: true` and no `profile_ids`
(e.g. `band--amazon-special-skills`) are returned by `applicableRules` for
every profile of the band (desktop), but the generator required
`profile_id in recipients`, so the web artefact published no `special` access.
22 `skill_access_drift` rows (amazons, arabian-tomb-raiders, battle-monks,
black-dwarfs, black-orcs, cursed-cavalcade, bretonnian-knights-errant…).

Fix, in `tools/knowledge/generate_knowledge_web.py`: `_band_wide_rules`,
`_applicable_profile_rules`, `_recipient_type_matches` replicate the F017
contract (`applies_to.band` plus recipients absent-or-containing the profile,
filtered by `profile_types`). `_profile_skill_data` and
`_profile_promotion_skill_data` now build from those rules.

### H7-D2 — transcribed-empty special lists refused the whole catalogue

The desktop emitted `{rule_id, category, skills: []}` for a published special
table with no transcribed members; the generator omitted empty lists, so the
web reported `skill_not_permitted` (later `skill_pending_special_list` with no
rule id). 44 `special_list_empty_vs_absent` rows and 2648 `skill_verdict_drift`
rows.

Fix: the generator publishes the empty list (`_profile_skill_data`), and
`skillIssue` in `packages/typescript/domain/eligibility/index.ts` treats a
special access whose every published list is empty as the prose-only state
(T09/T10) — `skill_pending_special_list` with `owner_task: KB`, exactly like
the absent-list case, never "the catalogue is open". Regression:
`tests/fixtures/eligibility/decisions.json` (case 19, "special list without
transcribed members is pending"), consumed by both the vitest and the Python
shared-eligibility suites.

### H7-D3 — stringified prohibition tokens in the artefact

The generator stored `equipment_forbids` through a single `str(...)` call, so
list-valued tokens arrived as `"['armour', 'ranged-weapons']"`. The web then
refused with `construction_clause_unstructured` while the desktop returned a
plain `equipment_forbidden`/`null`: 18 of the 72 `offer_refused_web` rows, 25
`item_verdict_drift` rows and 2 `profile_forbids_drift` rows (black-orcs,
ghost-pirates).

Fix: the tokens are flattened (`_profile_fact_rules` / `_build_profiles`).

### H7-D4 — effective equipment access published incompletely

(a) Equipment concessions of profile-scoped rules (a binding whose mechanic has
an equipment prefix and is present in the catalogue `mechanics`) were not
published on the web side: `weapon.vomit-attack` (black-orcs, night-goblins
mic/web, orc-mob, underworld-alliance-mim, chaos-streets-greenskins),
`poison.black-lotus` (Clan Pestilens, Tomb Guardians, Khemri Tomb Guardians)
and `weapon.mace` (Lustria Savage Goblins).
(b) Conditional exclusions the desktop applies were not replicated, so the
artefact over-offered: `weapon.spirit-knife` to `corpse-master` and `revenants`
of `call-of-the-night-haint-mim` (it is hero- and ethereal-only), `weapon.katana`
to Cathayan `deck-hands` and `martial-artists`, `weapon.skull-busta` to
`gobbo-boyz` and `weapon.long-daggers` to `brotherhood-agents`/`-novices`.
Together: 17 `equipment_access_drift` rows.

Fix: `_profile_equipment_concessions` (mechanics set loaded once per package),
`_printed_offer_excluded`, `_spirit_knife_allowed`; `_build_profiles` filters
the exclusions, adds the concessions and re-orders `equipment_access`.
Regression: three new tests in `tests/python/web/test_knowledge_artefact.py`
(band-wide/prose lists, flattened forbids, effective access with concessions
and exclusions) plus the updated Trollheim expectation.

## 3. Baseline vs post-fix

31 checks are emitted by the harness; only these were ever non-zero.
Post-fix values are identical across both post-fix runs
(`--postfix` and `--postfix2`), key by key and row by row.

| Check | Baseline | Post-fix | Cause |
| --- | --- | --- | --- |
| `skill_access_drift` | 22 | **0** | H7-D1 |
| `special_list_empty_vs_absent` | 44 | **0** | H7-D2 |
| `skill_verdict_drift` | 2648 | **0** | H7-D2 |
| `equipment_access_drift` | 17 | **0** | H7-D4 |
| `item_verdict_drift` | 25 | 4 | H7-D3 fixed; 4 new are H7-R2 |
| `profile_forbids_drift` | 20 | 18 | H7-D3 fixed 2; 18 are H7-R3 |
| `offer_refused_web` | 72 (54 `equipment_forbidden` + 18 `construction_clause_unstructured`) | 59 (`equipment_forbidden`) | H7-D3 |
| `artefact_item_missing` | 21 unique | 21 | H7-R1 |
| `picker_catalogue_extra` | 9 | 9 | H7-R4 |
| `artefact_offer_without_item` | – | 10 | H7-R2 |
| every other check (`band_*`, `fixed_equipment`, `promotion_skill_access`, `profile_rule_ids`, `skill_lists`, `skill_category`, `skill_kind`, `item_tags`, `item_kind`, `item_mechanic`, `artefact_skill_*`, `artefact_profile_missing`, `picker_profile_extra`, `picker_skill_choice_drift`, `picker_skill_lists_drift`, `desktop_offer_without_item`, `artefact_offer_unknown_list`) | 0 | **0** | – |

Second post-fix run: 1056 profiles audited, 23 437 shared calls, 436 s,
`item_verdict_pairs=12660`, `skill_verdict_skipped_profiles=1056`, catalogue
skill facts identical on both sides — every profile's skill inputs are equal,
so the zero skill drift is guaranteed by construction, not sampled.

## 4. Residual findings, classified

None of these is a defect of the shared decision: the two consumers return the
same verdicts, or the difference is a fact-source shape the web adapter
handles.

- **H7-R1 `artefact_item_missing` (21).** KB items with no artefact row, all
  out-of-scope equipment kinds (mounts/animals/special: `angel_wings`,
  `bear_of_the_hunt`, `chaos_steed`, `cold_one`, `great_eagle`, `rhinox`,
  `wolf_rat_mount`…). The web catalogue is intentionally scoped to purchasable
  items; no profile offers them. Informative.
- **H7-R2 `artefact_offer_without_item` (10) / `item_verdict_drift` (4).**
  Rule-granted mechanics with no catalogue item record: `weapon.vomit-attack`
  (6 offers), `poison.black-lotus` (3) and `weapon.mace` (1). The web reports
  `equipment_unknown_item` (`owner_task: KB`, "offered but has no item record")
  — the honest state; the desktop's `catalogueItemFacts` synthesizes pseudo
  facts from the `mechanics` catalogue for `poison.black-lotus` and
  `weapon.mace` (kind `trollheim-equipment` / empty) and therefore returns
  `null`, while `weapon.vomit-attack` has no facts on either side (no drift,
  report only). Owner: KB catalogue materialization; decision parity is not at
  stake.
- **H7-R3 `profile_forbids_drift` (18).** `outlaws-of-stirwood-forest`(×2) and
  `silent-brotherhood-sc`: the desktop folds band-wide tokens into the
  per-profile projection (`crossbow`; `animal`, `blackpowder`), the artefact
  keeps them at band level — and the artefact band rows do carry them
  (`equipment_forbids: ['crossbow']`, `['animal', 'blackpowder']`). The web
  consumer merges them in `equipmentIssueFor`
  (`band_forbids: band?.equipment_forbids ?? []`), so the decision is the same.
  Shape difference, documented; earlier per-profile duplication is gone.
- **H7-R4 `picker_catalogue_extra` (9, Trollheim).** `catalogueEquipment` is
  deliberately broader than the profile projection (foreign lists
  `khemri-lahmian-brotherhood`, Lustria mercenaries): by design, not a defect.
- **H7-R5 `offer_refused_web` (59).** Offers published by the profile's own
  lists that the shared decision refuses with `equipment_forbidden`
  (`beastmen-shaman` armour, `orc-nuttaz` armour/ranged, Silent Brotherhood,
  Dwarf Rangers/Treasure Hunters, Horned Hunters, Sisters…). The desktop
  refuses the same 59 pairs (no `item_verdict_drift`), which matches the H5-audit
  boundary: the projection publishes list membership, the decision layer applies
  the forbids; both consumers ask the decision. Design, not a divergence.
- **H7-R6 `artefact_item_missing`** duplicates nothing after the refresh; the
  21 rows are the same as R1 (single run over both collections).

## 5. Verification

- `tests/python/web/test_knowledge_artefact.py` + `test_shared_eligibility.py`:
  23/23 artefact tests passed after the repairs (including the three new ones)
  against the freshly regenerated artefact; the shared 22 passed.
- TypeScript: `npx vitest run tests/typescript/domain tests/typescript/application`
  → 78 files, 758 tests passed (the fixture's new case included).
- `pytest tests/python/construction` → 603 passed; the 4 failures are
  concurrent-lot edits not touched here (`protectorate-of-sigmar-lotd3` and
  `sea-ghosts-mim` sources plus their own T13 tests were dirty before this
  lot; the failing assertions cite those edits' new `profile_ids`).
- H5 audit re-run (`outputs/audit/eligibility_audit.py`): `offer_refused`
  116 → 116, `forbidden_family_missing_tag` 0, `empty_declared_access` 130,
  `special_access_without_list` 316, `offer_without_item_record` 6 — no
  regression from the `skillIssue` predicate change.
- Bundle: `npm run check:eligibility` (repo root) → current.
- Artefact: `python -X utf8 tools/knowledge/generate_knowledge_web.py --check`
  passed after the regeneration; spot values re-verified in the published
  artefact: `amazons-lustria/amazon-warriors` `skill_access: ['special']` with
  `band--amazon-special-skills: []`; `black-orcs/orc-nuttaz` forbids
  `['armour','ranged-weapons']`; `ghost-pirates-sar/gibbets` `['armour-suit']`;
  `skaven-of-clan-pestilens-mou/plague-rat` and `tomb-guardians/tomb-scorpions`
  offer `poison.black-lotus`; `black-orcs/troll` offers `weapon.vomit-attack`;
  no `katana` for Cathayan deck-hands, no `long_daggers` for
  `brotherhood-novices`, no `skull_busta` for `gobbo-boyz`; `spirit_knife` only
  for the three ethereal heroes of `call-of-the-night-haint-mim`.

## 6. Concurrent-tree observations (not from this lot)

- The workspace build copy `build/generated/knowledge-web` was stale vs the
  published `outputs/web-public/knowledge` at entry, which is why the harness
  default (and both post-fix sweeps) use the published directory; it was
  regenerated during this lot.
- **Encoding corruption, 2026-10-05 00:47:** a concurrent writer rewrote
  `sources/knowledge/catalog/mechanics/close-combat.yaml` with double-encoded
  UTF-8 (`Conmoción` → `ConmociÃ³n`, `â€™` for `’`): 338 added lines carry
  mojibake. Because `catalog/skills/warband.yaml` kept the clean text for the
  same identity, the presentation contract now aborts the generator with
  `ValueError: Duplicate presentation identity {'kind': 'skill', 'id':
  'skill.defensive-stance', 'scope': 'global'}` (skills vs mechanics/skills).
  `generate_knowledge_web.py --check` therefore currently aborts, and
  `test_knowledge_artefact.py` fails 22 tests for that single reason; the
  published artefact on disk was generated before the corruption and is clean
  (0 mojibake in `display-text.json`). Owner: the lot that wrote that file.
  No file of another lot was modified or reverted here.
- `sources/knowledge/catalog/mechanics/execution.yaml` (same mtime) is a
  legitimate large addition (`skill.cutthroat`, `skill.wound-valour`,
  `mechanic.sea-troll-slime`, `mechanic.wolf-rat-bite`, `mechanic.gypsy-ward`…).

## 7. Limits and bookkeeping

- No live UI round-trip: both consumers were exercised through their real
  fact/adapter paths and the maintained bundle, not by clicking either app.
- Numbers come from a read-only harness; the harness is not committed (both
  `build/` and `outputs/` are gitignored). If the coordinator wants it durable,
  promote it to `tools/audit/` under a reservation; otherwise re-create it from
  the run notes in §1.
- Coordinator row for `T13-shared-eligibility-reconciliation.csv` (offered for
  insertion, not written):

  `H7, shared item/skill access projection, "artifact vs canonical facts (both consumers)", build/audit/access_parity_audit.py, "22 skill_access, 44 special-list, 2648 skill-verdict, 17 equipment-access and 25 item-verdict drifts on the pre-fix projection", "band-wide skill grants (F017), empty special lists, flattened forbids and effective equipment concessions now materialized", "same verdicts as desktop for every profile; 0 skill/access drift", "-", "Combat Lab and Warband Manager obtain identical decisions", build/audit/access-parity-postfix2.json, "Materializer and one shared predicate repaired; residual groups classified", KB/generator, T13.2, "-", "Post-fix sweep keeps access/skill drift at zero"`


## 8. Coordinator current-state review — 2026-10-05

The delivered JSON retains four `item_verdict_drift` rows: Black Lotus on
three profiles and Mace on Zomblintua. Desktop permits these mechanic-id
concessions while the web boundary returns `equipment_unknown_item`.
This is a remaining fact/materialization integration gap, not zero global
item-decision parity and not solely informational. Resolve granted mechanic
identities to equivalent canonical item facts at both boundaries under L18/L21;
do not invent a duplicate combat rule or a purchasable item to silence it.
The four repaired projection/predicate defects remain separate from this gap.
The complete 1,056-profile sweep was not repeated during this bounded review.

The reported duplicate-presentation exception did not reproduce at current
entry: the generator check passed. Nevertheless `close-combat.yaml` contained
210 corrupt text scalars. A reversible UTF-8/Windows-1252 repair preserved all
keys, structure and non-text values, including concurrent mechanics/bindings.
The publication was regenerated and its maintained check passed; the shared
bundle is current. Backup and exact scalar-change paths are retained under
`build/cache/modular-completion/h7-coordinator/`. No source pins were refreshed.

Fresh bounded validation: 45 artefact/embedded eligibility tests passed;
19 shared TypeScript fixture cases passed using the maintained Vitest config;
documentation and scoped whitespace checks passed. No new tests were added,
no full access sweep or construction suite was repeated, and no commit/push
or modular/optimized implementation was performed by this review.

### Mechanic-fact resolution repair — 2026-10-05

The four differences above are repaired. The web construction boundary now
reuses shared `carriedItemFacts` through the reader's existing item enumeration,
matching Combat Lab's canonical mechanic-alias merge. Direct item records keep
priority; unknown mechanics remain unknown. This creates no purchasable alias
record and retains lazy catalogue errors and poison restrictions.

Two regressions added to the existing reader suite cover the four real offers
and mixed-kind/tag merging; deferred-reader assertions were extended in place.
Fresh validation: 43 TypeScript tests and 22 Python adapter tests passed; bundle
freshness and workspace typecheck passed. The complete H7 sweep was not repeated.
The historical ten offers without direct item records are not ten missing facts:
four now resolve through canonical aliases. The six Vomit Attack offers still
have no canonical item facts; retain their mechanic-only provenance for L21
disposition rather than inventing a purchasable item.
