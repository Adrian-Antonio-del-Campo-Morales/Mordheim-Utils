# T13 — F035 shared-eligibility reconciliation

Execution report for **T13-F035 — Revalidate affected T13 construction evidence
after eligibility extraction**, reserved in the
[initiative checklist](../README.md). It classifies F004 and F016–F021/F028
against the current canonical facts, the shared TypeScript decision, the real
Python transport and the Combat Lab/Warband Manager consumers. It proposes
dispositions and repairs; it does not accept or close any finding, does not
activate Shifty and does not modify shared state.

Entry: branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`, working
tree with 268 modified/untracked entries owned by other lots (257 at dispatch).
The dispatch authorized only this report, the companion CSV, optionally the two
new regression files and the evidence directory
`build/cache/t13-parallel/shared-eligibility-reconciliation/`. Nothing else was
written; no commit, push, bundle regeneration, coverage/pin/gate run or agent
was performed.

## 1. Entry, permissions and limits

- **No `AGENTS.md` exists** in the repository or any parent directory
  (`Get-ChildItem -Recurse -Filter AGENTS.md` over the checkout and the parent
  folder returns none); the dispatch itself is the instruction set.
- **Reservation**: the [2A/2B checklist](../README.md) reserves T13-F035 as the
  current-consumer reconciliation and keeps the Shifty reviewer and F057 lots
  independent; none of their files was touched.
- **Input hashes** were captured before any analysis: `entry/inputs.sha256.txt`
  covers `docs/reference/eligibility.md`, `architecture.md`, `verification.md`,
  `implement-and-verify-rules.md`, the checklist, register, plans, all eight
  T13 deliveries with their CSVs, the Shifty pair, the shared module, the
  Python adapters, the generated `_eligibility.js`, the fixture and the current
  construction tests. See §10.
- **Concurrent documentation drift, reconciled**: between capture and close the
  coordinator's own "Shared construction documentation reconciliation"
  (README row, completed 2026-10-02) rewrote four of those inputs —
  `docs/knowledge/2a2b/README.md`, `T13-T15-remaining-plan.md`,
  `T13-execution-follow-ups.md` and `T13-shifty-review.md` — adding ownership
  notes and acceptance rows (F003/F040/F050/F051) without asserting F035
  closure. The current text was re-read after the drift; the T13-F035 entry,
  its action/close criteria and the F035 reservation in the checklist are
  unchanged in substance, and no analysis in this report depends on the
  pre-drift revision. The drifted hashes are recorded in
  `entry/postdrift.sha256.txt`; everything else still matches its entry hash.
- **Generated artefacts**: `npm run check:eligibility` reports the bundle is
  current (`Source SHA256` matches `index.ts`+`bridge.ts`), so direct and
  embedded executions are the same code; nothing was regenerated.
- **Historical evidence** is cited as the observation it made; its counts were
  not forced and its conclusions were re-derived from current facts.
- The two new regression files are `tests/typescript/domain/t13-shared-eligibility-reconciliation.test.ts`
  (created) and the optional Python file (not created; the maintained
  `test_t13_selectable_equipment_matrix.py` already covers its ground, and a
  second matrix would duplicate it).
- **Limits**: this lot did not repeat T09 flows or the Web/T14 certification; no
  source PDF was re-fetched (the Shifty review's extracted Halflings/Karak Azgal
  text is referenced only where the canonical YAML already encodes the clause);
  no live round-trip through the desktop UI was performed for the campaign
  trading post (the readers were read, not driven).

## 2. Architecture actually observed

The five layers of the dispatch are real and separated as follows.

| Layer | Location | What was observed |
| --- | --- | --- |
| A. Source and canonical facts | `sources/knowledge/...` | Rule `runtime.effects[].binding` parameters, `applies_to`, `kind`, profile `skill_access`/`rule_ids`, equipment lists, item mappings, trading post. |
| B. Shared decision | `packages/typescript/domain/eligibility/index.ts` | `applicableProfileRules`/`applicableRules`, `specialRuleOptions`, `buildAccess`, `buildRestriction`, `equipmentIssue`, `skillIssue`, `equipmentSetIssues`, `catalogueSkillChoices`, `warriorEquipmentRestriction`. |
| C. Adapters and transport | `mordheim_construction/eligibility.py`, `selection.py`, `restrictions.py`, `bridge.ts`, `domain/campaign/construction.ts` | MiniRacer + catalogue cache; `_applicable_rules`/`available_special_rules`, `validate*` wrappers; browser `profileFactsOf`/`itemFactsOf`/`equipmentIssueFor`/`memberEquipmentIssuesFor`; the web artefact generator materialises `skill_access`, `skill_lists`, `equipment_forbids` and `equipment_limits` per profile/band. |
| D. Support and compilation | `mordheim_construction/compiler.py`, Combat Lab `application/catalogue.py` | `selected_rules`, `validate_special_rule`, `validate_loadout`, `_validate_profile_selections` (`boundEquipment` + `profileSelections`), `compiler.bow-discipline` → `missile_weapon_limit`; catalogue `skills`, `_warband_skills`, `_profile_equipment`. |
| E. Product access | Combat Lab UI/verification, Warband Manager flows | `available_special_rules` availability surface; web campaign construction and rare-search purchase. |

Two facts make the comparison meaningful:

1. `npm run check:eligibility` is green, so the embedded bundle is the current
   direct module. The maintained 18-case fixture runs against the direct
   exports (vitest) and the embedded runtime (pytest) — both green.
2. The browser knowledge artefact in `apps/warband-manager-web/dist/knowledge`
   matches the generator's current projection for every inspected field
   (band `equipment_forbids`/`equipment_limits`, profile `skill_access`/
   `skill_lists`/`equipment_forbids`), so the browser-side facts quoted below
   are current build output, not stale data.

## 3. Findings, clause by clause

The companion [CSV](T13-shared-eligibility-reconciliation.csv) carries 47 rows
(one per clause/entity) with the required columns. This section explains them.

### 3.1 F004 — Shifty

Current facts: `halflings-mic/halfling-elder--shifty` is **not** a `warband_skill`
and has no `kind`; it is `grant: profile`, `scope LATER`, `implemented NO`, with
`applies_to.profile_ids = [halfling-elder, halfling-cook, halfling-thief,
halfling-youths]` and the source effect text ("gains a bonus attack when
charged that strikes first"). The four hero profiles already publish the
`special` skill access; the henchmen do not.

- **Access/recipients** — the four legal recipients are explicit and match the
  four hero profiles; `applicableProfileRules` returns the rule for the elder
  (profile-grant branch). No defect.
- **Metadata** — no `kind`/selectable representation, so `specialRuleOptions`
  (which enumerates only `kind === "warband_skill"`) returns nothing and
  `available_special_rules` offers Shifty to none of the four. This is F004's
  surviving defect; the owner is the canonical KB metadata plus T13.2, after
  F003.
- **Compiled activation** — no binding; `skill.shifty` is not a mechanic;
  compiling the rule id refuses with the published runtime reason ("charge-response
  bonus attacks are outside the current engine scope"). The modular pilot is
  reachable only through an injected tag, which is not canonical selection.
- **Combat contract** — the S1–S4 interpretations remain F003's; F035 does not
  adjudicate them. Nothing was activated.

### 3.2 F016 — named special-skill tables

Four Karak Azgal adventurer tables (`band--dwarf/elf/barbarian/noble-special-skills`)
publish `profile.skill-access` with `category: special` **and a named skill
list**, `grant: band`, implemented YES, `applies_to.profile_ids` naming the
matching profile.

- The browser artefact grants the category and carries `skill_lists` per
  recipient; running the shared `skillIssue` on those facts returns **null for
  every published member** — the shared decision accepts the canonical table.
- The compiler path refuses every named member: `skill.berserker`,
  `skill.monster-slayer`, `skill.hard-to-kill` fail `_validate_profile_selections`
  ("skills are not available to adventurers-kaz/dwarf: …") because
  `buildRestriction` synthesizes `skill_lists` from skill **source URLs**
  instead of the canonical per-profile list, and `skill.fey`/`skill.taunt` are
  not mechanics at all.
- `dwarf-troll-slayers--slayer-skills` is **resolved**: it grants only the
  category, and the named selections arrive through selectable `warband_skill`
  rules that are offered and compiled (proof in the maintained matrix).
- `bretonnian-knights-errant-mou/band--knights-feats` publishes a category-only
  binding that matches its printed band-wide grant, but the named feats are
  prose, not skills, so no selection route exists. The brigands copy
  (`band--knights-feats`, scope NO, no binding) is printed for the Fallen Noble
  while the KB marks it band-wide; the recipient is also published at profile
  scope (`fallen-noble--knights-feats`, scope NO, unimplemented), so the band
  copy is an inert duplicate rather than a live recipient question.

Disposition: F016 is a **Combat Lab projection/compilation gap** (consumer
layer), not a shared-legality defect; the KB modelling gap for the feats is
separate. F017 must be repaired first so the new route does not widen access.

### 3.3 F017 — band grants and recipient filters

Reproduced, current: `applicableRules`'s band branch honours
`applies_to.band`, `eligibility` and `runtime.grant`, but **not
`applies_to.profile_ids`**. All four adventurer tables therefore apply to
wizard, elf, barbarian, imperial-noble, dwarf and imperial-captain; the Python
adapter (`_applicable_rules`) returns the same because it delegates.
`reproducers/repro_f017_recipients.py` fails with 20 recipient violations
against source-derived expectations (the four tables apply to every profile;
the dwarvish `rule_ids` recipient and the genuinely band-wide
`band--no-fixed-leader`/`band--hired-swords` controls behave correctly).

Observability today: no illegal *selection* results yet — the named skills
still fail the `skill_lists` gate — so the defect is latent but real and would
become visible as soon as F016's route exists. Owner: shared TypeScript, tested
against both consumers. The F035 register's claim that "the predicate moved but
the filter is still incomplete" is confirmed, not resolved by the extraction.

### 3.4 F018 — nine selectable origins without an availability channel

Eight origins are `kind: warband_skill`, `applies_to.band: true`, no
`eligibility`, and their recipient profiles (warrior-priest, rais, wayfinder)
publish skill access **without** `special`; the shared filter requires explicit
recipients or `special` access, so `specialRuleOptions` returns them to nobody
and `available_special_rules` omits them. The ninth, `strigoi-kaz/vampire--bloodline`,
is `kind: profile_ability` (grant selectable, `applies_to.profile_ids: [vampire]`,
referenced by the vampire's `rule_ids`); the API enumerates only
`warband_skill`, so the kind filter excludes it. In every case the runtime
refusal is real and carries the rule's own published reason.

Disposition: the eight are a **canonical-facts/source question** (is the band's
special-skill table access for all heroes? the KB does not publish it), not a
shared-decision defect — the other bands with working tables
(clan-angrund-kep, halflings-mic, silent-brotherhood-sc) do publish `special`.
The bloodline is a **justified limitation** for the duel availability API: its
own reason says campaign purchases, which belong to the campaign route. T13-Q081
and T13-Q095 remain open source questions.

### 3.5 F019 — The Silence

Canonical parameters publish `forbids: [blackpowder, animal]` ("No warband
member or hired sword may ever use blackpowder weapons or animals"). Current
facts: band `equipment_forbids` projects both tokens; the item catalogue tags
`crossbow_pistol` blackpowder (and the brotherhood list offers it) and `warhound`
animal.

- **Shared decision / Warband Manager** — working: `equipmentIssue` on the
  projected facts returns `equipment_forbidden` for `crossbow_pistol`, an item
  the list would otherwise permit. The historical "masked by the equipment
  list" note was true for the pistol only; the crossbow pistol is an observable
  blackpowder binding today.
- **Combat Lab** — the `boundEquipment` stage receives the same binding but
  interprets only `armour`, `ranged-weapons`, `heavy-armour`, `weapon.lance`,
  `defence.helmet`; it has no item facts and never consults `equipmentIssue`.
  `reproducers/repro_f019_silence.py` shows the exact divergence: the decision
  refuses, the stage accepts. `compile_fighter` refuses the pistol only because
  the equipment list does not offer it.

Disposition: **adapter/consumer defect** in Combat Lab (supply item facts /
route the token vocabulary through the shared decision), not a shared-rule or
legality problem.

### 3.6 F020 — Bow Restrictions

All four printed clauses are in the binding parameters and behave correctly in
the shared decision: `max_missile_weapons: 1` (two missile items →
`equipment_limit_exceeded`), `required_tag: bow` (kit without a bow →
`equipment_required_missing`), `crossbow` prohibition (`equipmentIssue` refuses
a crossbow-tagged item), `exempt_profile_ids: [cleric]` (no issues for the
cleric). The compiler consumes only the count (`compiler.bow-discipline` →
`missile_weapon_limit = 1`); it has no set-level check because
`equipmentSetIssues` has no Python caller, and the duel catalogue has no bow or
crossbow mechanic (their mappings are absent/out_of_scope), so the other three
clauses cannot be exercised in Combat Lab. The crossbow ban is additionally
latent in the browser because no outlaws list offers a crossbow.

Disposition: shared decision **resolved with evidence**; Combat Lab's set-level
consumption and ranged execution are **unsupported combat projection** to be
handled when range is modelled. No shooting subsystem was invented.

### 3.7 F021 — Teeny Hands

The armour prohibition is enforced with evidence (shared decision on projected
profile forbids; compiler `boundEquipment` armour branch). The printed
"single One-Handed Weapon at a time" clause is **declared deferred by the rule
itself** (the KB effect list carries it as scope LATER with the explanation
"combat/progression mechanics outside the duel scope"); no limit fact is
projected, dual-wielding compiles today, and the shared `EquipmentLimits` shape
has no one-handed slot (the legacy campaign `maximum_one_handed_weapons` is a
different, injury-state limit). Disposition: **data declares a deferral**; no
shared-decision defect; the clause needs modelling or a reviewed limitation in
the owning progression/loadout lot.

### 3.8 F028 — seventeen trading-post items

Re-derived individually: of the 17, **13 are `availability.kind: not_sold`** in
`sources/knowledge/catalog/campaign/trading-post.yaml` (no purchase route at
all; several have other callers — dramatis personae, hired swords,
exploration-and-income), and **4 are `rare`**: `corpse_liquor` (rarity 9) has a
price block and is offered by the campaign readers, while `scuttling_hand`,
`wicker_man` and `wolf_rat_mount` declare rarity but **no price**, so the
desktop trading-post reader skips them (`price_label is None`). All 17 map to
`out_of_scope` in `item_mappings` and appear in no warband equipment list, so
Combat Lab correctly does not offer or compile them. Disposition: **no legality
defect**; the campaign route (or its absence) is recorded per item; the three
priceless rare entries are a canonical-price question for the campaign
catalogue, and Combat Lab access is a declared scope limitation, not a missing
caller.

## 4. Direct, embedded and consumer comparison

| Decision | Direct (TS exports) | Embedded (MiniRacer) | Consumer/runtime |
| --- | --- | --- | --- |
| 18 fixture cases | 18 passed (vitest) | 21 passed (pytest, includes bundle/thread/runtime tests) | Compiler + catalogue use the same bundle |
| `applicableRules` recipient filter | Not asserted by a maintained direct test (no exported fixture); the fresh bundle makes the embedded probe direct-equivalent | Defect reproduced for all four tables | `_applicable_rules` identical; browser artefact path is correctly filtered by the generator |
| `equipmentIssue` Silence tokens | Projected facts exercised embedded; new direct regression covers the vocabulary | `equipment_forbidden` | Browser blocks `crossbow_pistol`; compiler `boundEquipment` does not |
| `equipmentSetIssues` four clauses | New direct regression (5 tests) | Same results | Only the browser calls it |
| `skillIssue` named tables | New direct regression (published member permits, outsider rejects) | Same | Browser accepts, compiler refuses |
| `specialRuleOptions` | Fixture does not cover it | Embedded probe | No offer for Shifty/9 origins; 8+8 offered for the slayer/dwarf rules |

## 5. Validation

All from the repository root with `python -X utf8`; logs under
`build/cache/t13-parallel/shared-eligibility-reconciliation/validation/`.

| Command | Result |
| --- | --- |
| `npm run check:eligibility` | exit 0 — "Shared eligibility bundle is current." |
| `npm run test --workspace campaign-web-core -- shared-eligibility` | 27 passed (18 fixture + 9 new), exit 0 |
| `npm run test --workspace campaign-web-core -- t13-shared-eligibility-reconciliation` | 9 passed, exit 0 |
| `python -X utf8 -m pytest tests/python/construction/test_shared_eligibility.py -q` | 21 passed, exit 0 |
| `python -X utf8 tools/mordheim-utils.py tests --scope construction -q` | **455 passed**, exit 0 |
| Focused construction files (shared, selectable equipment, automatic grants, selectable/special/profile bindings) | 184 passed, exit 0 |
| `python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q` | 1 passed, exit 0 (re-run after the concurrent documentation drift) |
| `probe_findings.py` / `probe_browser_facts.py` | exit 0, JSON evidence written |
| `repro_f017_recipients.py` | exit 1 — 20 recipient violations (defect reproduced) |
| `repro_f019_silence.py` | exit 1 — decision refuses, `boundEquipment` accepts (defect reproduced) |

No coverage budget, pin, integral gate or full Web/T14 certification was run by
this lot. Results above are the complete outputs, not aggregate counts only.
Inherited failures: none inside the construction scope. The known F057 parity
inventory failure (`3758` vs `3743`, owned by F057) is outside this scope and
was not re-run; nothing in this report depends on it.

## 6. Proposed dispositions

| Finding | Clause | Disposition |
| --- | --- | --- |
| F004 | recipients/access | Resolved with evidence |
| F004 | selectable metadata | Canonical metadata incomplete → KB + T13.2 after F003 |
| F004 | compiled activation | Unsupported combat projection, declared |
| F016 | adventurer named tables | Consumer projection/compilation gap (Combat Lab) |
| F016 | slayer-skills | Resolved with evidence |
| F016 | knights-feats (errant/brigands) | KB modelling gap (feats) + inert band duplicate |
| F017 | band-grant recipients | Reproduced shared-decision defect |
| F017 | band-wide grants, profile branch | Resolved with evidence (controls) |
| F018 | eight warband skills | Data incomplete (access route absent) → source review |
| F018 | vampire--bloodline | Justified limitation for the duel API; campaign owns purchases |
| F019 | parameters + browser path | Resolved with evidence |
| F019 | Combat Lab boundEquipment | Reproduced adapter/consumer defect |
| F020 | count, bow, cleric | Resolved with evidence |
| F020 | crossbow ban | Decision implemented; latent route; no defect |
| F020 | Combat Lab set-level / ranged | Unsupported combat projection |
| F021 | armour | Resolved with evidence |
| F021 | one-handed clause | Data declares deferral; no shared-decision defect |
| F028 | all 17 items | No legality defect; route or limitation recorded; 3 price gaps |

## 7. Concrete repairs and dependencies

1. **F017 shared fix (first).** In `packages/typescript/domain/eligibility/index.ts`,
   `applicableRules` band branch adds the profile-ids condition
   (`applies_to.profile_ids` empty **or** includes the profile). Extend
   `tests/typescript/domain/t13-shared-eligibility-reconciliation.test.ts` with
   the negative recipient cases (kept out today on purpose), add the adapter
   check for one non-recipient profile, run both consumers. Target T13.2;
   dependency: none; blocks the F016 route.
2. **F019 Combat Lab adapter.** Give the bound-equipment stage the item facts
   (or route the vocabulary tokens through `equipmentIssue` with
   `band_forbids`), preserving the browser path. Target T13.2; dependency F019.
3. **F016 Combat Lab route.** Project the canonical per-profile `skill_lists`
   into the compiler facts (extend `package_facts`/`selection.py`) so named
   table skills are selectable exactly where the source grants them; names with
   no mechanic keep a precise unsupported message. Dependency: repair 1.
4. **F018 source review.** For protectorate-of-sigmar, araby-smugglers,
   sea-ghosts-mim (and the band-wide tables generally), decide whether the
   printed table grants `special` access and record it in the profiles, or
   review the omission as a limitation; keep `specialRuleOptions` unchanged
   until a source-backed legal case exists. Route the bloodline to the campaign
   purchase owner. Target T13.2d; dependencies: T13-Q081/Q095.
5. **F020/F021 limitations.** Record the latent crossbow clause and the
   deferred one-handed clause alongside the ranged-weapon and progression
   owners; no shared change is justified now. Target T13.4/T13.2d.
6. **F028 route record.** Keep the per-item rows; the three priceless rare
   entries need a price or a limitation in the campaign catalogue. Target
   T13.2d.
7. **F004** stays with F003/F004 owners; its metadata fix follows the same
   selectable representation used elsewhere.

## 8. F035 close criterion

Every listed finding now has a current disposition with owner and target lot;
the affected shared module, adapters, fixture and consumers were re-run at the
reviewed revision (bundle check, 27 TypeScript tests, 21+184+455 Python tests,
documentation test); the historical deliveries were reused only where their
inputs still match, and the two defects F035 found are retained as failing
reproducers rather than blessed as correct. The remaining work belongs to the
findings' own lots, which is explicitly allowed ("F035 does not require fixing
every detected gap inside the lot"). **F035 can therefore be recommended for
acceptance as the reconciliation**, keeping F004, F016, F017, F018, F019, F020,
F021 and F028 open with the dispositions above. Acceptance remains the
coordinator's and the user's.

## 9. Handoff — exact register updates (proposals, no IDs assigned)

- **T13-F004** — *Status*: open; canonical metadata gap confirmed after
  extraction. *Current evidence*: this report §3.1, `probes/findings.json#F004`.
  *Action*: keep blocked on F003; the fix is a `kind: warband_skill` (or
  accepted equivalent) representation for the four legal recipients plus a
  negative control. *Resume*: with the F003 S1–S4 ruling. *Close*: unchanged
  from the register.
- **T13-F016** — *Status*: open; two of four clauses resolved.
  *Current evidence*: §3.2. *Action*: repair the Combat Lab route (repair 3)
  after F017; publish the knight's feats or record them as source-blocked.
  *Resume*: after the F017 shared fix. *Close*: as registered, with the
  slayer-skills clause recorded as resolved.
- **T13-F017** — *Status*: open; **defect reproduced in the shared decision**.
  *Current evidence*: `reproducers/repro_f017_recipients.py`,
  `probes/findings.json#F017`. *Action*: repair 1. *Resume*: before F016's
  route or any special-skill enabling. *Close*: positive and negative canonical
  recipients through both consumers, band-wide grants preserved.
- **T13-F018** — *Status*: open; **classification changed**: eight origins are
  a KB access/source question, the bloodline is a justified kind/campaign
  boundary. *Current evidence*: §3.4. *Action*: source review per band
  (five bands), campaign route for the bloodline. *Resume*: before exposing
  those choices. *Close*: as registered.
- **T13-F019** — *Status*: open; **split**: shared decision resolved, Combat Lab
  adapter defect reproduced. *Current evidence*:
  `reproducers/repro_f019_silence.py`. *Action*: repair 2. *Resume*: next
  affected eligibility/adapters lot. *Close*: token proved at the Combat Lab
  boundary or an unsupported-category limitation recorded.
- **T13-F020** — *Status*: open; count/bow/cleric clauses resolved, crossbow
  latent, Combat Lab set-level and range unsupported. *Current evidence*: §3.6.
  *Action*: record the limitation with the ranged/lot owner. *Resume*: when
  ranged weapons are modelled. *Close*: as registered.
- **T13-F021** — *Status*: open; armour resolved, one-handed clause declared
  deferred by the canonical data. *Current evidence*: §3.7. *Action*: model the
  clause or review the deferral in the progression/loadout lot. *Resume*: when
  dual-wielding/loadout limits are modelled. *Close*: as registered.
- **T13-F028** — *Status*: open; **classification changed**: no trading-post-only
  legal route exists for 13 items (`not_sold`); the 4 rare entries are the
  relevant ones, one priced, three without a price. *Current evidence*: §3.8 and
  the 17 CSV rows. *Action*: record routes, resolve the three prices. *Resume*:
  with the campaign catalogue review. *Close*: as registered.
- **T13-F035** — *Status*: recommended for acceptance after coordinator review;
  no state was changed by this lot.

New follow-ups (no IDs assigned, per dispatch):

1. **Reproducer**: `repro_f017_recipients.py`; **impact**: every special-skill
   table of a band leaks to all profiles through the compiler adapters and would
   become a live illegality once a named-skill route exists; **owner**: shared
   TypeScript author (T13.2); **timing**: before F016's route; **close**: both
   consumers show recipient-correct positive and negative cases.
2. **Reproducer**: `repro_f019_silence.py`; **impact**: the Silence's
   blackpowder/animal clause is decided but not enforced by Combat Lab; **owner**:
   Combat Lab adapter (T13.2); **timing**: next adapters lot; **close**: the
   stage refuses the same tokens the shared decision refuses.
3. **Source question**: five bands' band-wide special-skill tables vs profile
   `skill_access`; **impact**: legal choices may be unreachable or silently
   widened; **owner**: KB/source reviewer (T13.2d); **timing**: before exposing
   those skills; **close**: each of the nine origins has a recorded route or a
   reviewed limitation.

## 10. Reproducible evidence

`build/cache/t13-parallel/shared-eligibility-reconciliation/`

- `entry/` — `head.txt`, `date.txt`, `git-status.txt`, `inputs.sha256.txt`
  (entry hashes; four inputs superseded by the concurrent documentation
  reconciliation), `postdrift.sha256.txt`.
- `probes/probe_findings.py` → `findings.json`, `findings.stderr.txt`;
  `probes/probe_browser_facts.py` → `browser-facts.json`;
  `probes/build_csv.py` (regenerates the CSV deterministically).
- `reproducers/repro_f017_recipients.py`, `repro_f019_silence.py` and
  `reproducers/logs/`.
- `validation/` — `check-eligibility.log`, `ts-eligibility.log`,
  `construction-scope-final.log`, `focused-construction.log`.
- `checks/` — `manifest.json` with the deliverable and evidence hashes and
  `final.json` with the closing status.

## 11. Limits

- No live desktop/web session drove the trading-post or draft flows; the
  consumers were read and the shared decisions were executed on the projected
  facts.
- The campaign purchase route for `vampire--bloodline` was not exercised (its
  own reason places it in campaign purchases); only the duel API boundary was
  proved.
- The eight F018 origins need a source reading that this lot did not perform
  (the canonical YAML is not the printed table); the disposition routes that
  work rather than guessing.
- F017's over-broad grant has no observable illegal selection today and is
  therefore recorded as reproduced-but-latent, not as a live product defect.

## 12. Coordinator acceptance and governing dispositions — 2026-10-02

**Accepted as F035 current-consumer reconciliation; reservation released.**
F035 is resolved. The report body and 47-row CSV remain the executor's research
snapshot; the dispositions below supersede conflicting proposals in §§7–9.
Acceptance does not close F004/F016–F021/F028, certify T13.2, or exclude any
admitted construction/combat clause.

Independent evidence is retained in
`build/cache/t13-parallel/f035-coordinator-review/`:

- All 18 manifest pairs matched at entry; the 24 protected non-documentation
  inputs remained unchanged. Both complete fresh research probes equal their
  submitted JSON results. The CSV has 47 unique clause/entity keys and 15 columns.
- Fresh bundle check, 27 TypeScript regressions and 21 embedded Python cases
  pass. The retained construction 455 and focal 184 runs are reused evidence,
  not fresh coordinator runs. No live purchase/product-flow certification is made.
- Direct TypeScript probes against canonical facts reproduce F017's 20 wrong
  recipients across the same six profiles as the embedded reproducer, and
  F019's missing `boundEquipment` refusal. A positive recipient/band-wide control
  passes. These two deliberately failing probes remain ignored evidence, not
  regressions asserting incorrect behavior is valid. The initial cache probe
  discovered zero tests and is excluded from the proof; discovery was corrected.
- The incoming report is preserved byte-for-byte as `incoming-report.md` with
  SHA-256 `5a48381fcbfe84b39964be984ef275af73bc8de6ebd660b0b4b7883890e80c33`.
  Only this appendix changes the submitted report; its CSV, tests and evidence
  remain untouched.

| Finding | Governing disposition, owner and next barrier |
| --- | --- |
| F004 | Four Hero recipient facts are correct; selectable kind/grant, binding and executable availability remain pending canonical activation. The user accepted Shifty S1–S4 and F003 is resolved; the obsolete proposal to wait for F003 no longer applies. Reuse shared eligibility and preserve F005/F026 pistol limits. |
| F016 | The named-table shared legality decision works on correct facts, but Combat Lab's supplied selection facts/source gate and missing mechanics leave a projection/compilation gap. The Slayer clause is resolved by current canonical compilation evidence. Knights' Feats remains source/data-gated. Repair F017 before enabling affected Adventurers skills. |
| F017 | Reproduced shared `applicableRules` defect; repair recipient conjunctions once in TypeScript, preserve genuine band-wide grants and prove direct/embedded callers. It is latent until a reachable named-skill route exists. |
| F018 | Eight omissions are KB recipient/access/source gaps in three bands (Protectorate, Araby and Sea Ghosts), not five. Strigoi is a fourth band: filtering `profile_ability` out of a `warband_skill` API is correct for that API only. Bloodline's configured combat effects remain admitted by the inventory; campaign purchase cost/timing is excluded. Keep their selection/binding/mechanism handoff and Q095 open. |
| F019 | Generic shared token decisions work on adequate facts; the specialized Combat Lab stage does not enforce blackpowder. Its implementation is TypeScript `buildRestriction` plus Python context/catalogue projection, so the repair may cross both integration layers; do not add a Python rule copy. The witness proves a stage gap, not a currently successful illegal full build: today's weapon-list gate rejects the pistol. Animal's canonical Combat Lab route remains unproved. |
| F020 | Shared count, required-bow, Cleric exception and crossbow decisions are proved at their decision boundaries. Combat Lab set/loadout facts and enforcement remain open in T13.2. Shooting resolution is excluded and is not a prerequisite for legal carried-equipment validation. Preserve partial proofs without declaring the entire restriction resolved. |
| F021 | Armour refusal is proved; a canonical dual-wield Runt build is still accepted. Missing active-one-handed facts/binding/shared loadout support is an included construction gap. `LATER` metadata does not override the inventory. Preserve the promoted configured participant exception without introducing a campaign advancement lifecycle. |
| F028 | The factual partition is 13 `not_sold` and four rare items, three rare items without price. It corrects the old acquisition premise, but neither availability nor `out_of_scope` mapping proves every combat clause excluded. Retain per-item supported local route or reviewed applicability limitation. Missing campaign prices belong to the catalogue owner, not a prerequisite to import purchases into Combat Lab. |

The scope checks use [the authoritative obligations](T13-obligations.csv):
`band--bow-restrictions` and `runts--teeny-hands` are construction/T13.2;
`vampire--bloodline` is mixed/T13.2–T13.6 with Q095. No new source interpretation
or exclusion is approved here. Underlying findings retain the exact closure
criteria in [the execution register](T13-execution-follow-ups.md).

Next eligible shared repair is F017 before F016. F019 can be separately scoped,
but any edits to shared `index.ts`/bridge/generated bundle require one exclusive
writer; these two repairs are not automatically safe concurrent writers.
Independent effect/test work can continue with stable inputs. No production,
KB, specification, commit, push or agent launch is part of this acceptance.
