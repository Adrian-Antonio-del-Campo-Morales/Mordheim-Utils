# T13 reconciliation audit — LOT D (facts, context, references)

Independent reconciliation of the frozen `D-facts-context-references.csv` assignment
(107 entries). Read-only with respect to KB, code, registries, shared reviews,
`manifest.json` and the assignment lists. Owns only
`D-facts-context-references-results.csv` and this summary.

- Repository: `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`
- Branch / HEAD at audit: `2A2B` / `820d1499a0c9ff04fd42975d3de9d97bd62d585d`
- Working tree carried large uncommitted concurrent edits (KB, TS eligibility,
  Python construction/combat, docs) before this audit; none were touched.
- No `AGENTS.md` exists at the repository root or any scanned directory.
- Parallel writers active in this folder during the audit: lot A
  (`A-construction-results.csv`/`-summary.md`) and lot C (`C-combat-results.csv`)
  appeared while this lot ran. Neither shares a fact with D except the
  `campaign.condition.*` / Ienh-Khain definitions that D intentionally mirrors
  from C (see below); those reads were reconciled, not copied blindly.

## Input verification

| Check | Result |
| --- | --- |
| `manifest.json` `D-facts-context-references` sha256 | `d1487be133e5d7815b4ceba2577ee41a9aeb53d71bc8e08bbf161a73c9267dcb` |
| Assignment sha256 (measured) | `d1487be133e5d7815b4ceba2577ee41a9aeb53d71bc8e08bbf161a73c9267dcb` — **match** |
| `manifest.json` rows / measured data rows | 107 / 107 — **match** |
| Distinct ids / duplicate ids | 107 / 0 |

There is no `D.csv` in the dispatch folder; the lot's closed assignment list is
`D-facts-context-references.csv` (header `id,source_file,effect_sha256,scope,category,reason,related_target,effect_text`,
UTF-8 with BOM, read with `utf-8-sig`). All 107 rows have `scope=YES`.

**Source drift: none.** Every assigned id was re-extracted with the maintained
extraction (`mordheim_combat_lab.verification.audit_export.build_audit_rows(inventory_only=True)`,
7328 current rows), the raw effect text re-hashed and compared with the assigned
`effect_sha256`; **107/107 match and 0 assigned ids are missing**. No
`stale_input` result.

## Method

1. Re-extracted and re-hashed every id (maintained extraction; never the
   flattened CSV display text). Drift stored in
   `build/audit/reconciliation/D/drift.json`.
2. Resolved each family to its current canonical facts and aliases:
   - `catalog/hirelings/traits.yaml` rows → profile id + trait tokens, and the
     actual projection in
     `packages/python/roster-construction/mordheim_construction/combat_packages.py:16,52-61`.
   - `catalog/campaign/serious-injuries.yaml` `tables/0/results/{3,4,6,9,10,14,16,17}/note`
     → current `effects` blocks and the campaign consumers in
     `packages/python/campaign/mordheim_campaign/application/post_battle_engine.py`
     (`_apply_injury_effects`, lines ~214-265).
   - `catalog/campaign/magic.yaml` `spell.commands.*` → the compiler `active_command`
     channel (`compiler.py:399-403`, `apps/combat-lab/.../ui/editors.py:38`) and
     the modular consumers (`modular/rounds.py:85-89`, `modular/contexts.py:276-277`,
     `kernel.py:109`).
   - `catalog/hirelings/dramatis-personae/core.yaml` unique-item references →
     the same-file definitions (lines 249/262/275), and the TS unique-item
     contract `resolveHirelingKit` (`packages/typescript/domain/eligibility/index.ts:271-278`).
   - `catalog/hirelings/hired-swords/**` rule rows → their definitions and the
     real consumers (`mechanic.leadership-reroll`, the large-target shared rule).
   - `catalog/rules/special-rules.yaml` `shared-rule.animal`/`shared-rule.living`
     → all band origins and their reviewed `runtime` (scope/implemented/binding).
3. Traced every admitted clause to a current consumer: the shared construction
   projection (`combat_packages.py`) and compiler tag mapping
   (`compiler.py:329,351,379-383,415,493-496`), the modular engine
   (`kernel.py:109` supported-tag set, `modular/{contexts,rounds,leadership,psychology}.py`),
   and the campaign application (`post_battle_engine.py`, `hire_eligibility.py`).
   Campaign-only consumers were recorded, not treated as duel coverage.
4. Mirrored C-lot dispositions for entries C also audited (the `campaign.condition.*`
   ids and the Ienh-Khain rule definitions) rather than re-deriving them divergently.

Scratch tooling and evidence live under `build/audit/reconciliation/D/`
(`extract.py`, `classify.py`, `finalize.py`, `drift.json`, `results.csv`).

## Result counts

107 result rows, one per assigned id, exact 16-column order, UTF-8/LF, no BOM.

| Family (source node) | n | covered | metadata_gap | partial | connection_gap | implementation_missing | out_of_scope |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hirelings/traits.yaml` trait token | 49 | 22 | 27 | | | | |
| `hirelings/traits.yaml` profile entry | 33 | 10 | 16 | 7 | | | |
| `campaign/serious-injuries.yaml` note | 8 | 3 | 3 | | 2 | | |
| `campaign/magic.yaml` Command | 3 | 2 | | | 1 | | |
| `dramatis-personae/core.yaml` Ienh-Khain reference | 3 | | | | | 3 | |
| hired-swords / dramatis hireling rule | 9 | | | | 2 | | 7 |
| `campaign/exploration-and-income.yaml` description | 2 | | | | 1 | 1 | |
| **Total** | **107** | **37** | **46** | **7** | **6** | **4** | **7** |

`proposed_scope`: 100 `YES`, 7 `NO`. No `source_blocked`, `decision_required` or
`stale_input` rows: the input is intact and no assigned entry raised a new
unanswered specification question.

## Covered — current source-to-consumer evidence

- **Duel-projected hireling traits (22 tokens + 10 profiles, `covered`).**
  `combat_packages.py:52-61` projects exactly `fear-causing → causes_fear`,
  `undead → creature_kind=undead` and the species names `human/dwarf/ogre`
  (among the eight) into `profile['combat_traits']`; `compiler.py:351` maps
  `causes_fear → mechanic.causes-fear`, `:379-383` maps `creature_kind → nature.*`,
  `:415` maps `species → species.*`. Those tags are consumed by
  `modular/leadership.py`, `modular/psychology.py`, `modular/contexts.py` and
  listed in `kernel.py:109`.
- **Typed permanent injury modifiers (results 6/9/10, `covered`).** Chest wound
  (T-1), nervous condition (I-1) and hand injury (WS-1) declare
  `warrior.characteristic_modifier`; `post_battle_engine.py:225-233` applies them
  permanently to `warrior.stat_modifiers`, so the reduced characteristic carries
  into the participant's later duels. A committed trait whose profile is not yet
  a projected participant is still covered: the projection code path is current
  and unconditional for grade-2b participants.
- **Two Mazzalupo Command spells (`covered`).** `follow-me-mine-pugnacious-ones`
  (`modular/rounds.py:85-87` → `condition.command.follow-me-active`,
  `modular/contexts.py:276-277` gives the +1 to hit) and
  `art-thou-ready-to-die-fighting` (`modular/rounds.py:88-89` →
  `out_of_action_threshold=6`) are both supplied through the supported
  `active_command` scenario fact and consumed end to end.

## Grouped actionable gaps

- **G1 — Campaign-only hireling identities (43 rows, `metadata_gap`).**
  `elf`, `evil`, `priest`, `spellcaster` tokens and every profile carrying only
  those facts. They are *declared* (canonical `traits.yaml`) and *consumed by the
  campaign hire-eligibility application* (`hire_eligibility.py:194,208-210`
  `has_elven_hired_sword` / `has_evil_hired_sword` / `has_warrior_priest_member`
  / `has_spellcaster_member`), but the duel compiler has **no** identity tag for
  them: `combat_packages.py:52-61` omits them, `contracts.py TRAIT_TYPES` has no
  such key, and `compiler.py:443-444` maps only `elf_kind` (high/dark) to
  `species.high-elf`/`species.dark-elf`. Impact: a duel rule that needs those
  identities cannot select them. Repair target: `combat_packages.combat_traits`
  (+ a consumed tag) *if a duel rule needs the fact*, otherwise reclassify the
  token as campaign-only. Note also a scope discrepancy to record: the
  `T13-audit-scope-review.csv` reason advertises these as "opponent/participant
  fact[s] used by individual duel rules", while `traits.yaml`'s own header
  assigns them to campaign eligibility.
- **G2 — Untyped injury consequences (results 3/4/14, `metadata_gap`).** The
  prose notes declare consequences whose operators already exist but which the
  result does not bind: arm wound (23) → `warrior.equipment_limit`
  (`maximum_one_handed_weapons`, already consumed at `post_battle_engine.py:252-265`);
  madness (24) → `mechanic.stupidity` + `frenzy`; bitter enmity (56) → a
  `mechanic.hatred-*` operator with the hated-enemy fact.
- **G3 — Supplied conditions not mapped to the fear operators (results 16/17,
  `connection_gap`).** `warrior.add_condition` with
  `campaign.condition.immune-to-fear` / `campaign.condition.causes-fear`; the
  operators (`mechanic.fear-immunity`, `mechanic.causes-fear`) exist and are
  consumed, but `post_battle_engine.py:242-246` only stores the id as an
  `'Injured'` detail string and nothing maps the condition id to an operator
  (matches C's `connection_gap` on `conditions.yaml`). Related: F070.
- **G4 — Leadership-reroll facts unbound (Songster ×2, `connection_gap`).**
  `mechanic.leadership-reroll` exists and is consumed (`modular/leadership.py:81`,
  `modular/rounds.py:671`); the Bard and William Schäkestange Songster rules are
  prose-only with no binding. This follows lot C's `shared-rule.leader` finding
  (a group-proximity Leadership fact is *supplied* and covered when bound); here
  the binding is missing. Related: F036.
- **G5 — Command without a channel (`raise-our-insignia`, `connection_gap`).**
  The Command's individual consequence (re-roll failed Leadership) maps to an
  existing operator, but the compiler accepts only the two other Mazzalupo
  Commands (`compiler.py:399-402`), so there is no `active_command` value. Related: F039.
- **G6 — Blessed weapon consequence missing (`exploration/13`,
  `implementation_missing`).** "wounds Undead and Possessed on 2+" has no
  operator (`mechanic.blessing-of-morr` is a different Morr rule); the target
  facts (`nature.undead`/`nature.possessed`) exist. Related: F064.
- **G7 — Granted Hatred not bound (`exploration/16`, `connection_gap`).** The
  `grant_rule` Hatred is consumed as campaign data
  (`post_battle_engine.py:1448`, `exploration-workflow.ts:1080`) but no duel
  hatred operator is attached to it.
- **G8 — Ienh-Khain unique-item rules unimplemented (3 references,
  `implementation_missing`).** The references resolve correctly to
  `core.yaml` lines 249/262/275, but the definitions declare no runtime/binding
  and the TS unique-item contract requires a canonical mapping
  (`eligibility/index.ts:271-278`). This mirrors C's disposition for the same
  definitions. Related: F036.

## Out-of-scope decisions (7 rows, `proposed_scope=NO`)

- **Large Target (4 rows; ogre-bodyguard, clan-skryre-rat-ogre, bone-goliath,
  ogre-slave-master).** `large-target` is defined by the *shooting* rules; the
  canonical shared effect `shared-rule.large-target` is itself a canonical
  exclusion (F-excluded-scope-control), and neither the compiler nor the modular
  engine reads any large-target/size fact.
- **`shared-rule.animal`.** All 16 band origins are reviewed `scope=NO/LATER`,
  `implemented=NO`, no binding (e.g. `horned-hunters#warhounds--animals` reason
  "Out of scope: campaign"); the "never gains Experience" clause is campaign.
  *Recorded discrepancy:* the compiler still sets `species.animal` for band
  profiles whose rule ids end `--animal`/`--animals` (`compiler.py:493-496`),
  and that tag is consumed by psychology/`mechanic.animal-friendship` — an
  incidental path unrelated to any binding of this shared rule. If the
  "campaign" classification is challenged, re-open via F001/L21.
- **`shared-rule.living`.** Both origins are `scope=NO/LATER`, no binding
  (`tomb-guardians#tomb-scorpions--living` reason "Deferred subsystem: psychology
  or mounts"); the water clause and group/intrinsic psychology are non-duel.
  *Recorded finding:* the compiler would emit `nature.living` for
  `creature_kind=living`, but nothing sets that and **no consumer reads
  `nature.living`** anywhere.
- **Snake Charmer `rule.animals`.** The subject is the Charmer's companion snakes
  (external actors) and the clause is campaign/no-XP; the Charmer itself is grade
  1b and its companion profiles are unresolved. Related: F036.

## Blockers and decisions needed

- No data blockers: the assignment is intact and every id resolved.
- One interpretation decision is surfaced by G1: whether `elf`/`evil`/`priest`/
  `spellcaster` identities must become duel facts. D records them as
  `metadata_gap` with the campaign consumer named, because the duel compiler has
  no tag for them today; promoting them is a new projection, not a shown gap in
  an existing consumer.

## Recommended next implementation groups

1. **G3/G7 (fear/hatred condition mapping)** — smallest, highest-value: map the
   two supplied `campaign.condition.*` ids and the granted Hatred rule to the
   existing `mechanic.fear-immunity`/`mechanic.causes-fear`/`mechanic.hatred-*`
   operators. Blocked on nothing; reuses existing operators.
2. **G2 (typed injury effects)** — add the already-consumed
   `warrior.equipment_limit` / stupidity-frenzy / hatred effects to results 23,
   24, 56.
3. **G5/G4/F039 (Command channel + Songster binding)** — promote
   `raise-our-insignia` to a supported `active_command` and bind the Songster
   rules to `mechanic.leadership-reroll`.
4. **G6/G8 (blessed weapon and Ienh-Khain item operators)** — new operators;
   land after the mappings above.
5. **G1** — only if a concrete duel rule needs the campaign-only identities;
   otherwise record them as campaign-only and close.

## Checks actually run vs inspection-only

- **Executed:** the maintained extraction re-run and 107/107 re-hash
  (`build/audit/reconciliation/D/extract.py`); the assignment hash/row count
  check; the results-file structural validation (16 columns, 107 unique ids
  equal to the assignment, status vocabulary, `out_of_scope ⇔ proposed_scope=NO`,
  UTF-8/LF, no BOM) in `finalize.py`; targeted read-only greps loading the KB
  (`load_hirelings`, `load_hireling_traits`, `combat_packages`) and the band
  origins.
- **Inspection-only (not executed behaviour):** every listed operator/consumer
  claim is code inspection of the current tree (`combat_packages.py`,
  `compiler.py`, `contracts.py`, `modular/*.py`, `kernel.py:109`,
  `post_battle_engine.py`, `hire_eligibility.py`, `eligibility/index.ts`). No
  new semantic test was written and no per-entry integration campaign was run,
  per the dispatch. No unexecuted check is labelled as passed.

## Concurrent drift and closure

- Lot A and lot C results appeared in this folder during the audit; the
  assignment list, `manifest.json` and shared registries were not modified by
  this lot.
- **Closure revalidation:** `D-facts-context-references.csv` sha256 re-measured at
  closure equals the manifest value `d1487be1…9267dcb` with 107 data rows; the
  retained results file reproduces 107/107 rows with unique ids equal to the
  assignment. Any later edit to `catalog/hirelings/traits.yaml`,
  `catalog/campaign/serious-injuries.yaml`, `catalog/campaign/magic.yaml`,
  `catalog/campaign/exploration-and-income.yaml`, `catalog/rules/special-rules.yaml`
  or the hirelings catalogue invalidates the affected rows' hashes and must
  re-open them.
