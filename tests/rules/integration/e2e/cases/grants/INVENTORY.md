# Grants corpus — inventory and handoff

Scope of this work: `tests/E2E/modular-engine/cases/grants` only. Nothing outside this directory was
edited. Every statement below is derived from the printed sources (`sources/knowledge/**`), the accepted
rulings in `docs/decisions/design-rulings.md` and the shared construction stage the rules compile to
(`packages/python/roster-construction/mordheim_construction/compiler.py`, `contracts.py`, `_eligibility.js`
and its mirror `packages/typescript/domain/eligibility/index.ts`), read for the *observable* a clause has,
never as an oracle. No engine was run, no copy or probe was made, and no expectation was fitted to engine
output. Every scenario in this directory stays `execution_status: UNEXECUTED`.

This revision adds the source-by-source reconciliation of the register drift that appeared while the corpus
was being worked on (§10). The register moved without any normative change: across all 4556 of its rows
`clause_text`, `source_file` and `source_fingerprint` are identical to `HEAD`, and the only semantic movement
is 33 `clause_scope` flips from `YES` to `NO` (batch `scope-admitted-contract-reconciliation`,
`implementation_work: none`), 31 of which name a clause declared by a file in this directory. Each of those
31 clauses is now recorded here as an accepted scope disposition (class `[E]`), with its printed text, its
requirement and every scenario preserved; no scenario in this directory ever declared `covers` for one of
them, so the flips invalidate no authored tape (§10.3). No `scaffold_fingerprint`, `audit_id`, scenario, file
name or line ending was changed by this pass anywhere in the corpus (§7), and every declared
`# Clause: … (scope: …)` label in the 1468 files now agrees with the register.

This revision replaces the previous handout's criterion in three places and reconciles the whole
withheld set against it:

1. **The absent member projection is a pending implementation defect, not a blocker** (§4). The four band
   skill tables now declare the identities and the required result on the route that reads the member list
   (`skill_ids`), and the missing projection is recorded as the implementation those tapes wait on. The
   same file keeps the recipient-level and foreign-table controls, because a control set distinguishes a
   correct implementation from one that refuses every special skill: it is not necessary that each
   scenario detect every defect on its own, and the incomplete engine refusing both directions does not
   invalidate the negative case.
2. **A declaration is evidence only when the gate it feeds can reach the claim** (§2.6, §4, §9). The
   `special_rule_ids` channel resolves a declared id against the band's own package rows, runs the
   recipients stage and the rule's own runtime gates, and never reads the `profile.skill-access` member
   array; the table's *membership* is therefore evidenced on the list route only, and coverage is not
   claimed from it elsewhere.
3. **Access is separable from effect** (§2.7). A member's own duel effect being out of the accepted scope
   does not by itself exclude its printed selection: where the access requirement is admitted, the
   admission/refusal pair is authored.

Every remaining withheld clause was re-read against that test. Thirty clauses that had been recorded as
blocked are now covered; three files moved `PARTIAL` → `AUTHORED`; five markers were corrected because the
blocker they stated was false (the drug, potion and condition identities exist; the band row for the
`criticals-on-six` facet is `scope: YES / implemented: YES`; the five `no-panic` markers had used a
deferred origin row as if it proved an exclusion). Two tapes that could not evidence their clause were
withdrawn and the requirement recorded as withheld instead (§5.1; the `maibd-poison` pair).

## 1. Corpus state (after this pass)

| Measure | Value |
| --- | --- |
| YAML authoring files | 1468 |
| `AUTHORED` | 1311 |
| `PARTIAL` | 146 |
| `REVIEWED` | 11 (unchanged; none promoted by this pass) |
| Declared scenarios | 4186 |
| Files whose body is empty | 38, all `PARTIAL` |
| `PARTIAL` clause markers | 169, in 146 files |
| … that carry a tape for their own clause | 81 |
| … that are withheld (no scenario covers the clause) | 88 |
| Withheld by class: `[C]` input/observation/identity | 29 |
| … `[D]` normative datum or identity the sources do not settle | 14 |
| … `[E]` scope disposition or unmade decision | 45 |
| `AUTHORED` clause markers | 1503 |
| Files carrying a `PENDING[…]` implementation-defect note | 15 (16 tokens) |
| Structural problems found by the static check | 0 (the invariants of §7) |

`authoring_status` is authoring-only and says nothing about behaviour; every scenario is
`execution_status: UNEXECUTED` and carries no behavioural result. Only manual semantic review can promote
an ID to `REVIEWED`; the 11 `REVIEWED` files predate this work and were not changed. The pre-existing
generator variance the previous revision recorded is repaired here: 26 files stated UNEXECUTED only in
their progress prose and now also carry the dedicated
`# execution_status: UNEXECUTED (this scaffold has no behavioral result)` line the generator's own
template writes, and the `ghutani-rel` scholar (`field-of-scholarship`) had lost the newline between its
`# authoring_status:` and its `# authoring_progress:` prose, which is why no status line could be read for
it; the line is split again, so the file reads `PARTIAL`, exactly as its marker and its empty body already
said. The stricter pass that requires the dedicated line now reports 0 deviations across the corpus, and
that repair changed no scenario, marker, clause line or requirement. The deviations this pass itself
introduced while rewriting declared-clause blocks were found by the preservation check of §7 and repaired
there. The scope reconciliation of §10 then changed one thing more: 31 `# Clause:` labels whose clause the
register now records as `scope: NO`, and the 31 corresponding markers from class `[C]` to class `[E]`. With
those, every declared clause-scope label in this directory agrees with the register (measured: 0
discrepancies over 1468 files).

## 2. The expressibility test applied throughout

A pending requirement is **authorable** when the printed clause fixes an outcome and names its recipient,
and the duel fixture or the construction fixture can *state the case* through a field the corpus already
uses, with the expectation expressed in the established diagnostic family of the gate that fires — or, for
an admission, in the printed outcome itself. Eight rules follow, and all eight were applied:

1. **These tests specify the future engine.** A missing branch, consumer, operator or projection is not a
   reason to withhold a scenario: it is the defect the scenario must detect. `PARTIAL` is reserved for
   what is genuinely missing — an input, an observation, an identity or a decision. A `scope: LATER`,
   `implemented: NO` or `binding: null` row is not, by itself, any of those.
2. **No internal modifier has to be observable.** Where a rule changes an impact, a wound, an attack
   count, a priority or a save, the tape binds that change to the boundary where the *result* differs.
3. **A multi-participant or multi-provider context is representable.** `duel_context.nearby` plus
   `distances` carries several supplied providers and participants.
4. **No invented fields, decision keys, contracts or identities.** The identity a tape declares must exist
   in the KB: a catalogue row, a condition, a preparation, or a rule id the band publishes and lists in its
   own `band.yaml`. A declared decision or roll key that no consumer in the corpus's own support uses is
   invented too.
5. **A non-discriminating tape is not evidence.** If the same expectation holds both when the clause is
   honoured and when the projection it depends on is missing, the tape is withdrawn and the requirement is
   recorded as withheld with the concrete cause. The requirement is never deleted, never weakened and never
   reported as covered.
6. **A declaration is evidence only when the gate it feeds can reach the claim.** Declaring an id through
   `special_rule_ids` runs the declared-rule block of `compile_fighter` in this order: the id is resolved
   against the band package's own rows (`selectedRuleCandidates`), then the `recipients` stage, then the
   member's own `runtime.implemented` (must be `YES`), then its `runtime.grant` (must be `selectable`),
   then `prerequisites`, and only then the `access` stage. That channel never reads the
   `profile.skill-access` member array, so it cannot evidence a table's membership; and a row whose own
   `runtime.grant` is `band`/`profile` is refused as "special rule is not selectable" before any effect.
   Coverage is claimed only for what the channel actually reaches (§4, §9).
7. **Access is separable from effect.** A member's own duel effect being dispositioned out does not by
   itself exclude its printed selection; where the access requirement is admitted, its admission/refusal
   pair is authored, and the member's own effect keeps its own origin.
8. **The set is judged as a set.** A scenario need not detect every defect alone; the control set as a
   whole must distinguish a correct implementation from one that refuses everything.

Governing spelling of the channels used: `owned_item_ids`, `main_weapon_id` / `off_hand_id` /
`extra_hand_id` / `armour_id` / `defence_ids`, `main_poison_id` / `off_poison_id`, `preparation_ids`,
`condition_ids`, `skill_ids`, `special_rule_ids`, `trait_overrides`, `variant_ids`, declared
`duel_context` participants with `distances`, declared `rolls` and `decisions`, and `initial_state`
overrides of documented state fields.

## 3. Authored in this pass (this revision)

| Files | What was authored or corrected |
| --- | --- |
| 4 | The band skill tables: the list-route admission tape for the band's own published member (declared for the absent member-list projection, §4), and — in the three that lacked it — the foreign-member refusal that makes the table boundary a control pair rather than a single refusal. The markers now state which clause each route evidences and which projection is pending |
| 8 | The skill-list access family: closure pairs on the list route for the Strigany, Nippon, Ogre-hunting, Rememberer and Clan Moulder origins; the `owned_item_ids` possession pair for the Vim-to-Mage order; the Ogre hunting skills split into the crude-belch equivalence pair plus the list closure |
| 5 | The construct and construction-constraint family: two new tapes for the printed drug immunity (the drug identity and the `preparation_ids` channel both exist; the five-file wider `PENDING` set is reduced), two for the pointy-stick save threshold; the slot-capacity, in-built-equipment and two-handed-parry clauses keep an exact footprint blocker |
| 8 | The re-roll and missing-operator family: the three `field-of-scholarship` scholars (injury reroll + supplied-leader Leadership pair), the two Rememberers' reroll, the corruption attack reroll, the plague-cart injury-table pair and the ghostly howl pair |
| 4 | The leadership/psychology family: the two snotling single-model projections, the `criticals-on-six` pair with its control, and the Orc Nuttaz extra attack restored as this identity's own tape |
| 3 | The potion/mutation/brew family: the Petru draughts, the Alchemist's four grants plus addiction pair and the Fungus Brew lasting state, all through `condition_ids` |
| 6 | The `no-panic`/`never-leaves-combat` audit: five false "deferred row proves an exclusion" causes replaced by the excluded group procedure and the missing field/consumer |
| 1 | `maibd-poison`: the two authored tapes withdrawn — neither could evidence the clause — and the two concrete causes recorded instead (§5.1) |
| 27 | Grammar repair only (§1): 26 files gained the dedicated `# execution_status:` line and the `ghutani-rel` scholar's concatenated `authoring_status`/`authoring_progress` line was split. No scenario, marker or requirement changed |
| 6 | Declared-selection closures (§9): one declaration re-pointed to the profile's own automatic grant (`blood-dragon-vampire`), one tape's declarations dropped where the automatic route already carries the rule, one declaration pinned to its own collection and profile (the duplicated pestilens id), one tape withdrawn and its face recorded as withheld (the Mordheim pestilens prerequisite), one clause's two tapes withdrawn and archived as `[C]` (`unshakeable-faith`), and two tapes' prose corrected to name the gate that reaches them (the Sacred Marks pair) |
| 31 | The scope reconciliation of §10: the clause label and the marker of every clause the register moved to `clause_scope: NO`, in the 23 `never-leaves-combat` riders, the 5 Bretonnian `no-panic` origins and the 3 construct files. Printed text, requirements and every scenario preserved; no tape withdrawn, none added |

All edited files keep their `audit_id`, `scaffold_fingerprint`, `Clause:` ids, line endings and
`execution_status: UNEXECUTED`; each was re-parsed after the edit. (In the 31 files of §10 that clause line
now ends `(scope: NO)`, because the register's own scope field moved; nothing else on the generated lines
changed.)

## 4. The band skill tables — access separated from effect

Four files carry the printed sentence "… may use the following skill table instead of any of the standard
skill tables available to them" (`amazons-lustria`, `cursed-cavalcade`, `battle-monks-of-cathay`,
`arabian-tomb-raiders`). Each separates:

* **R1 the table-access rule.** The origin's own row (`profile.skill-access`, `scope: YES`,
  `implemented: YES`, `grant: band`, `applies_to.band: true`, binding parameters `{"category":"special"}`).
* **R2 the member identities.** Published by the band as its own `kind: warband_skill` rows and listed in
  the band's `band.yaml` `special_rules`; **no catalogue row exists for any of those members.**

  | Band | Members | Recorded runtime |
  | --- | --- | --- |
  | amazons-lustria | skink-hunter, mesmerising-dance, savage-fury | `scope YES / implemented YES`, each bound to its mechanic; `elixir-of-life` (campaign) and `concealment` (movement) are `scope NO` |
  | cursed-cavalcade | noblesse-obliges, torturer | `scope YES / implemented YES`; `duelist` is `scope NO` (no effect applies to the isolated duel or to legal construction) |
  | battle-monks-of-cathay | energy-focus (`eligibility: [dragon-monks]`) | `scope YES / implemented YES`; `lightning-speed`, `leap-of-faith` and `human-shield` are `scope NO`, and `warmonger` is `scope LATER / implemented NO`, `eligibility: [emissary]` |
  | arabian-tomb-raiders | — | every printed member (sand-worm, hit-and-run, weather-tolerant) is `scope NO / implemented NO` with its own reason |
* **R3 each member's own effect.** A separate clause with its own file and expectation; nothing here
  re-asserts a member's mechanic.

**What each route evidences** (read statically in the shared stage, never by running it). The
`special_rule_ids` route (a) exercises the recipients stage and, for a member with no `eligibility` list,
the recipient profile's own `special` skill category: it therefore evidences the *recipient* half of R1,
the member's selectability for that recipient, and this band's table boundary when the id belongs to
another band. It never reads the member array, so it neither evidences nor refutes R1's *membership*. The
list route (b) (`skill_ids` → `skillIssue()`/`profileSkillLists()`) is the only route that reads the
member array, and it is where the membership tapes are declared.

**Control sets now authored.** Each table has: the band's published member admitted for its printed
recipient on the list route (the membership requirement), the same member refused for a recipient the
print excludes (where the module reaches that refusal), a member of another band's table refused with the
band-level availability sentence, and a special skill outside the table refused on the list route.
`battle-monks-of-cathay` additionally carries the Emissary narrowing: its `warmonger` member admitted
(observed as that member's own deferred sentence, which is what proves the recipient stage admitted the
Emissary) and the sibling `energy-focus` refused for it.

**Pending implementation, recorded not withstood.** The `profile.skill-access` binding declares
`{"category":"special"}` **without a `skills` member array**, so `profileSkillLists()` yields nothing for
these tables and the `buildAccess` fallback (catalogue rows whose `source_refs` name the band) is empty for
them, because their members are the band's own `warband_skill` rows and carry no catalogue row. Two things
are missing before the membership tapes can pass: the band's published member identities have to be
projected into the profile's special skill list, and the list route has to resolve an identity the
catalogue does not carry (its illegal-skill predicate rejects a missing catalogue row before the member
list is consulted). The identities, the recipients and the required outcomes are declared; the absence of
that projection is what those tapes are written to detect.

## 5. Withheld requirements and how each one is classified

88 of the 169 `PARTIAL` clauses are withheld. Every one names a concrete thing of one of three kinds, and
none is classified by a null binding, a `LATER` scope or an `implemented: NO` row alone.

### 5.1 An input, observation or identity the contract does not admit — 29 clauses of class `[C]`

* **`never-leaves-combat`, 23 clauses; `no-panic-and-all-alone`, 5 clauses; the construct producer, 3
  clauses.** These 31 were re-classified in §5.3 by this pass: the register now records their rows as
  `scope: NO` with `implementation_work: none`, so the absence of a producer is an accepted scope disposition
  under the 2026-10-04 rulings, not a missing input. Each file keeps its printed sentence, its own note and
  its scenarios, and each marker now reads `[E]` (§10.3).
* **The construct slot capacity and in-built equipment, 5 clauses.** The printed capacities and the
  fitted-equipment rule are stated by the profiles, but no build field declares a slot count or a per-item
  cost, no over-capacity refusal sentence exists, and removing an already fitted item is a campaign
  operation.
* **`field-of-scholarship` residuals, 4 clauses.** The injury reroll has no recorded effect identity and no
  request key for rerolling an injury result; the leader-Leadership halves wait on the printed
  "won the last battle" gate, which no fixture field carries.
* **`whole` clauses with an unresolvable input, 5 clauses** (`gunnery-school` proud-to-a-fault,
  `halflings-mic` too-big, `maneaters` crude-belch, `snotlings-web` small-hands, `lustria-savage-goblins`
  tracker-gear): each names the exact missing item identity, request key or producer in its own marker.
* **Access and identity residuals, 17 clauses.** The printed special-skill members of the Strigany, Nippon,
  Ogre-hunting, Clan Moulder and Rememberer origins with no canonical id anywhere; the promoted-skill-list
  choice; the hypnotic-musk reading; `pointy-stick`'s item identity; `herb-lore`'s recovery-phase step;
  `taunt`'s excluded producer; the once-per-game and duelist reroll keys; the Vim-to-Mage possession
  exception and its missing diagnostic; `criticals-and-charge`'s stampede carrier; `mandatory-charge`'s
  unstatable counter-case; `charismatic`'s supplied sex fact; `greenskin-classification`'s rule-supplied
  identity; `supplied-leadership-adjustment`'s match-start race role; `feral-instinct` and
  `fanatical-advance`'s absent binding and profile; `control-enemy`'s danse state; the two-handed-spear
  wielding mode; and `maibd-poison` *both* ways — the bearer restriction attaches to a dose purchased
  through that rule's route and no build field records that provenance, while no bearer literal exists for
  the pair (the `restricted` table in `_eligibility.js` line 1361 has no Black Lotus entry and
  `poisonApplicationIssue()` raises only the weapon-kind sentence). Those two tapes were authored and then
  withdrawn under §2.5.
* **`unshakeable-faith` (`protectorate-of-sigmar-lotd3`), 1 clause.** The printed fear immunity is admitted
  and its recipient is printable, but the member reaches a recipient of that band only through the
  declared-selection channel, which refuses it at the access stage with its own sentence ("special rule is
  not available to protectorate-of-sigmar-lotd3/<profile>: band--special-skill-unshakeable-faith",
  `_eligibility.js` `specialRuleRestriction`: a `warband_skill` row with `applies_to.band` and no
  `eligibility` list is admitted only for a recipient whose own printed `skill_access` carries the
  `special` category, and no profile of that band prints it). Both authored tapes were withdrawn under
  §2.5 — the admission half because that channel never reaches the immunity, its band-mate boundary
  because without the admission half it holds in both worlds — and the requirement is recorded, not
  deleted. What is missing is the same member-category projection the four band tables wait on (§4).
* **The Mordheim pestilens refusal face, 1 clause.** The printed prerequisite sentence exists
  (`loadoutRestriction`, `_eligibility.js`: "Contagious requires Rotten Body"), but this origin's own row is
  deferred (scope LATER / implemented NO / binding null), so a declaration that resolves to it is refused
  earlier, at the  declared-rule block, and only the member's runtime status would be asserted. The pair's reaction scenarios
  stand and the refusal face is recorded as withheld — read the marker for the withdrawal as what it is: the
  clause itself is `AUTHORED`, and what was withdrawn is the tape that would have asserted the runtime status
  of the deferred row *as if* it were the printed prerequisite. The test the withdrawal answers is the
  corpus's own rule 5 of §2 (a tape that cannot separate the clause from its absence is not evidence), not
  "the engine cannot reach the gate". The Trollheim copy of the same id is implemented and selectable, and
  there the sentence is declared through that row.

### 5.2 An identity or normative datum the sources do not settle — clauses of class `[D]`

(This section's list no longer carries the Town Cryer 6 inheritance markers: those nine compiled tapes
were resolved this pass against the active Dwarf KB — see below.)

* **Town Cryer 6 inheritance** (`dwarf-guildsmen-kaz` and `dwarf-slayers-kaz`, 2 files, 9 compiled tapes):
  resolved this pass under the accepted ruling that the KB binds against the *active* Dwarf rules rather
  than settling the cited edition. Both inheritance rows compile as selectable `warband_skill` rows whose
  three effects are the active KB clauses (`skill.hard-to-kill`, `mechanic.hatred-orcs-goblins`,
  `trait.concussion-immune`), so each file carries one authored tape per clause. The Dwarf Axe tapes
  assert the shared `weapon.dwarf-axe` identity, the equipment-list tapes stay at the band's own list
  item, the exclusion tapes assert the compiled absence of the excluded tag, and the skill-table tapes
  record the known compiled refusal ("skills are not available to …") — the same member-category
  projection the four band tables wait on (§4), not a new blocker. Bundles without the row remain
  refused with the row's own sentence.
* **High-elves Miniath** additional parry attempt: the printed extra attempt is not representable under the
  adopted parry-capacity ruling.
* **Andanti** parry rolls under Weapon Skill, and the Watchmen scryer's melee reroll: an unmade ruling about
  which side owns the rerolled dice.
* **`clan-angrund-kep` effective strength for armour** and **`fallen-noble` individual modifiers**: the
  stanza does not print the face, and the modifier's declaring identity is unsettled.
* **`veteran-tracker` starting skill choice**, **`requires-resilient`** and **`its-alive` starting
  mutation**: the required-choice guard's contract id and sentence do not exist for these origins.

### 5.3 An accepted scope disposition or an unmade editorial decision — 14 clauses of class `[E]`

The six `trait.pit-fighter` construction grants (admitted as construction facts, so each records
*admitted, no duel-time observable, pending the construction-layer fighting-style selection* rather than
"excluded"), the excluded producer/consumer halves recorded as accepted, the two rulebook-inheritance
`whole` clauses, the clan-Moulder mutations grant, `impetuous`'s movement and avoidance faces,
`da-boss-is-dead`'s succession grant, and the construct excluded-producer halves. An empty or partial body
is the correct artifact here, and each file keeps its reason.

The 31 clauses the register moved to `scope: NO` while this corpus was being worked on belong here, and are
recorded as such rather than as a missing capability (§10.1): 23 `never-leaves-combat` riders of the
`immune-to-psychology` siblings, 5 Bretonnian `no-panic` clauses (this disposition leaves those five origins
with no admitted clause at all, which §10.4 reports as drift), and 3 construct clauses
(`constructs-never-leaves-combat` on the band origin and `construct-excluded-producers--scope--never-leaves-combat`
on the two child constructs). Each file states the disposition, the batch name and the ruling it applies, and
keeps the printed text, the requirement and every scenario it had.

## 6. Implementation defects the scenarios must detect — held separately

These are *not* blockers. Each is a missing binding, projection, consumer, branch or operator, recorded in
the file's own marker as the thing the authored tapes will fail on until it exists. 15 files carry 17 such
notes and every one of them also carries its scenarios (or, for the four band tables, its declaration).
Representative entries: the null bindings the register records for authored rows
(`unimplemented.tileans.band.remasen-officer-leadership`,
`unimplemented.khemri-necromancers.band.necromantic-modification-paladin-of-horror`, the overseer scourge
rows, the construct rows); the missing two-hop branch of the Leadership borrow (`house-guard-sc/relay-orders`)
and the missing per-ally bonus consumer (`battle-monks/raging-peasants mob`); the absent operators named in
their own files (`resolve_crude_belch` scaled to every engaged enemy, the `master-of-arms` activation
surface, the poison-immunity projection for a blessed bearer, the compiled projections of `village-ogre`
and `marksmen--quick-reload`, the mount-eligibility contract of `let-the-goons-do-the-work`, the
supplied-kit route of the two Outlaws bow files, the `natural_armour_stacks` binding); the drug-immunity
and single-model projections; and the member-list projection of the four band tables (§4).

## 7. Static verification performed (engine-free, proportional)

* **YAML parse of all 1468 files** — 0 failures.
* **Structural invariants across 4183 scenarios** — 0 problems: every scenario's `audit_id` matches its
  file header, every `covers` reference is one of the file's declared clause ids, every scenario id is
  unique within its file, every scenario asserts through exactly one channel (`expect_error` never combined
  with another), every roll entry is well formed and inside its own die range, every decision carries a key
  and a value, every observation field is in the runner vocabulary, and every `maximum_rounds` is a positive
  integer.
* **Declared identities** — every identifier value a scenario declares in this directory was looked up in
  `sources/knowledge/**` and the shared construction stage. Four have no artefact there, all four
  pre-existing and outside this pass, and each of the four resolves in the engine's own vocabulary instead,
  which is stated here so the finding is not read as an invented identifier: `disability.6` is the resource
  literal the engine itself writes and reads (`state.py` records `disability.{1,2,4,5,6}` on a Disability
  bearer, `psychology.py` tests `"disability.6" in current.resources_spent`); `mechanic.lahmian-seduction`
  is the `ControlPower` id declared at `modular/rounds.py` and the binding id two band rows carry, which
  `test_t13_control_family.py` asserts as their canonical mechanic; and `sex.male` / `sex.female` are the
  supplied-sex fact the editor build produces as a trait-override tag
  (`tests/python/ui/test_editors_catalogue_sweep.py` sets `editor.sex` and asserts `sex.male` in
  `compile_fighter(...).global_effects.tags`). None is a catalogue or band identity, and the corpus uses
  them as supplied build facts, not as requirements.
* **Refusal diagnostics** — every `expect_error` fragment added in this pass was checked against the
  sentence templates the construction stage can raise. One fragment did not correspond to any reachable
  sentence (`maibd-poison`'s bearer literal); its tape was withdrawn and the requirement recorded as
  withheld (§5.1).
* **The scope reconciliation of §10** (engine-free, one command each, exit statuses read directly): all 1779
  authoring files under `cases/` parse (0 failures); the declared `# Clause: … (scope: …)` labels of all 1468
  files of this directory agree with the register's current `clause_scope` (0 discrepancies); the 31
  reconciled files carry the `[E]` marker for their flipped clause (23 + 5 + 3) and no `[C]` marker is left
  on them; no `audit_id`, `# Clause:` id, `scaffold_fingerprint`, file name or line ending changed anywhere in
  the corpus (0 of 1468), no scenario was added or withdrawn by this pass, and the only non-comment lines in
  those files' diff against `HEAD` are the concurrent authoring already present in the working tree (the two
  clockworkers construct files gained six scenarios from another author during the session, before this pass
  read them). The `scaffold_fingerprint` of the 31 files no longer equals what `generate_skeletons.py`
  derives today — the identity's admitted-clause set moved — and that is left standing deliberately (§10.4):
  re-stamping is generator work, not this directory's, and doing it in bulk is what this pass was told not to
  do. Each of the 31 files was re-parsed after its edit and re-read against the rule in §10.3.
* **Status coherence** — 1311 `AUTHORED` / 146 `PARTIAL` / 11 `REVIEWED`; every empty body is `PARTIAL`;
  0 `PARTIAL` files lack a `PARTIAL` marker; every `PARTIAL` marker's clause tag matches a declared
  `Clause:` line; no clause carries both `AUTHORED` and `PARTIAL`; and every `AUTHORED` file covers each of
  its own in-scope (`scope: YES`) clauses with at least one scenario.
* **Preservation, now across all 1468 files** (each compared against its committed blob): the declared
  `# Clause:` set is byte-identical to the committed one, `# audit_id:` and `# scaffold_fingerprint:` are
  unchanged, the line-ending style (LF vs CRLF) still matches, and no file lost a scenario except the two
  documented withdrawals — `unshakeable-faith` (−2) and the Mordheim pestilens prerequisite (−1). The
  `# execution_status:` line is present in all 1468: 26 files gained it in this revision's grammar repair
  (§1) and none lost it. 70 files carry more scenarios than their committed version. The same check on the
  187 files this pass edited reports the same zero deviations it did before, and it had already found and
  repaired one real regression while rewriting declared-clause blocks: four band-table files had dropped
  their `# Clause:` line, and one file had moved a `PENDING[…]` token to the start of its comment line,
  where the corpus grammar reads it as a marker tag.
* **Final gate, run after the last edit** (engine-free, one command each, exit statuses read directly): all 1468
  files parse; the corpus census reproduces §1 (1468 / 1311 / 146 / 11, 4183 scenarios, 38 empty bodies, 169
  `PARTIAL` markers, 1503 `AUTHORED` markers, 15 files with a `PENDING[…]` note); the structural checker
  reports 0 problems; the preservation check above reports the two documented scenario dips and no other
  deviation across all 1468 files; the declared-selection audit reports 346 declared scenarios and the 17
  findings of §9. The commands' exit statuses were read directly, not through a filter.

Not run, deliberately: any import or execution of the combat pipeline, the compiler, the runner or the
static checker's semantic model. A `covers` label and a passing structural check do not demonstrate a
clause, and an unexecuted scenario is neither a pass nor a failure; several cases here are written to fail
against the current implementation, which is their purpose.

## 8. What is left, precisely

No requirement was deleted, aliased away or weakened by this pass, and no resolvable authoring work remains
in the four band tables, the access family or the families this revision authored. Of the 169 `PARTIAL`
clause markers, 81 carry a tape for their own clause and 88 are withheld, each naming a concrete missing
thing:

* 29 clauses need an input, observation or identity the contract does not admit — the unrecorded operators
  and request keys, the construct keys and identities, the printed band skill lists whose members have no
  canonical id, and the purchase-route provenance of `maibd-poison`. The 31 Rout/All-Alone producers that
  used to open this list are no longer in it: the register dispositioned them out of scope and they are now
  recorded as accepted dispositions (§5.3, §10);
* 14 clauses need an identity or a normative datum the sources do not settle (Miniath's additional parry
  attempt, the Andanti parry ruling, the scryer reroll, natural-armour/effective-strength faces, the
  required-choice guards); the Town Cryer 6 inheritance markers are no longer in this list — they were
  resolved this pass against the active Dwarf KB (§5.2),
* 45 clauses are scope dispositions or unmade decisions, 31 of them the 2026-10-04 reconciliation of §10,
  plus the editorial decisions the register itself lists as pending;
* 15 files carry implementation-defect notes alongside their tapes, which is where a missing consumer,
  branch or projection is recorded rather than hidden.

Four KB-side facts are what several of those clauses wait on, and they are recorded in the files themselves
rather than proposed here as work: the four band tables' `profile.skill-access` member list and the
list route's resolution of a non-catalogue member id, the `skill_*` catalogue identities for the printed
members of the Strigany, Nippon, Ogre-hunting, Clan Moulder and Rememberer lists, the diagnostic/key each
unrecorded operator would consume, and a purchase-provenance field for a poison bought through a rule's
own route.

## 9. The declared-selection channel — audit and remaining findings

Every scenario that declares a `special_rule_ids` entry was checked against the declared-rule block of
`compile_fighter` and the band packages it resolves against (§4 states the gate order). The check is
engine-free: the band `special-rules.yaml` / `profiles.yaml`, the scenario YAML and that stage order are
read; nothing is imported or executed. **346 scenarios declare such an entry** (351 before the closures
recorded here). The same classifier run over the committed corpus — where 420 scenarios declared one —
reported 117 findings, so the fall measures the declarations that were re-pointed (or dropped) rather than
anything about the engine. Of those 117, 68 declared a row whose `runtime.grant` is `band` or `profile` —
the band's or the profile's own automatic grant — which that block refuses as "special rule is not
selectable" before reaching any effect, 17 were refused at the access stage and 4 at the recipients stage:
none of them could evidence the clause it was attached to. The previous revision left 20 findings, and the
seven this revision targeted are all addressed. Three no longer appear at all, each because the declaration
was put on a channel that reaches the clause or the clause was archived: the `blood-dragon-vampire`
scenarios no longer declare a `grant: profile` row (each bearer is built from its printed profile, so the tag
arrives by the automatic route the file now names), the Mordheim pestilens prerequisite tape was withdrawn
and its face recorded as withheld (§5.1), and `unshakeable-faith` was archived as `[C]` (§5.1). The other
four are still reported, because the classifier's model does not contain the stage that answers them: two
Sacred Marks tapes keep the sentence the construction guard raises and now name that gate, the duplicated
pestilens id is pinned to its own collection and profile, and the BigSnot pair tape now declares both
printed ids so the `prerequisites` guard that carries the pair sentence fires. The 17 that remain are
classified by reading, not by running:

| Finding class (the classifier used) | Count |
| --- | --- |
| The tape asserts a run and the declaration reaches a deferred (`implemented: NO`) row's own sentence | 11 |
| The same, with a second declared rule that does run (`asserts-run/deferred,runs`) | 2 |
| The tape asserts a refusal where the declaration makes the build run (`expects-refusal/runs`) | 3 |
| The declared fragment is not the sentence the modelled gate raises (`fragment-mismatch/runs,deferred`) | 1 |

The 13 `deferred` findings are deliberate and documented: those tapes assert the *printed effect*, which is
the requirement, and each file states the exact sentence they fail on until the recorded consumer exists
(moving them to the deferred sentence would assert the member's runtime status instead of the rule). The
four remaining findings are limits of that classifier's model, not tape defects, and each is answerable in
the source it reads: `Frustratingly Tiny cannot be combined with Big Bully` is raised at the `prerequisites`
stage (`_eligibility.js` line 1227, guarded on `args.stage === "prerequisites"`), `Contagious requires
Rotten Body` at the loadout stage (`_eligibility.js` line 1257, reached from the shared stage's
`validate_loadout`), and `a Lizardman Hero may have at most one Sacred Mark` in `profileTail` (line 701,
gated on the `compiler.sacred-marks` contract registered in `contracts.py`). A model that walks only the
declared-rule block plus the recipients and access stages cannot see those gates, which is why the classes
survive; the three files state the gate each tape reaches. No part of this section is a coverage claim, and
every file named in it keeps `execution_status: UNEXECUTED`.

## 10. The register drift — source reconciliation, per-ID disposition and provenance

### 10.1 What was read, and what each source is authority for

| Source | Role |
| --- | --- |
| `sources/knowledge/**` (the band packages named clause by clause in §§4, 5 and 9) | the printed rule text: the only authority for what a rule says |
| `docs/decisions/design-rulings.md` (whole page) | the accepted decisions; two 2026-10-04 entries decide this section (§10.2) |
| `docs/knowledge/2a2b/tasks/T13-semantic-analysis.csv` | the register: authority for `clause_scope` (what the corpus gates on) and for the clause inventory; **not** rewritten here |
| the same register at `HEAD` (`git show`) | historical reference only, never an automatic authority |
| `tests/E2E/modular-engine/generate_skeletons.py` | read to establish exactly what `--check` compares: `audit_id` and `scaffold_fingerprint`, and that `scaffold_fingerprint` is derived from the identity's admitted (`scope: YES`) clause rows plus the current source-file hashes |
| `tests/E2E/modular-engine/test_inventory.py`, `test_cases.py` | the invariants the corpus applies to itself (a scenario's `audit_id` must be admitted and every `covers` clause must be in scope) |
| the 1468 files of this directory | the artifact under review |

The register changed in the working tree during the session (`ad831bee…` → `1304a6aa…`, 4556 rows in both
revisions, none added, none removed). A changed register revision is not evidence that any rule changed, so
each `(origin_id, clause_id)` row was compared between `HEAD` and the working tree column by column.

### 10.2 The drift, measured per ID

| Column class | Columns | Rows changed |
| --- | --- | --- |
| normative text | `clause_text` | **0** |
| normative source | `source_file`, `source_fingerprint` | **0** |
| scope | `clause_scope` | 33 |
| contract | `semantic_contract`, `effect_id`, `relation`, `parameters`, `conditions`, `consumer` | 57 |
| implementation work | `implementation_work`, `dependencies`, `implementation_batch` | 57 |
| bookkeeping | `notes`, `evidence`, `evidence_refs`, `analysis_status` | 57 |

No printed clause text and no `source_fingerprint` moved, so no source hash in this corpus is stale because of
this drift — file hashes and `source_fingerprint` are different things and the register's fingerprints are the
ones the files carry. The 33 flips are all `YES` → `NO` and each carries `implementation_work: none` with the
batch `scope-admitted-contract-reconciliation`. 31 name a clause declared by a file here; the other two are
`rule/mordheim/imperial-outriders/band--mounted-two-weapon-fighting/mounted-loadout-and-first-round-pistol`
(`UNCLASSIFIED` → `NO`, no file in this directory) and
`source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.executioners-hood`
(no file in this directory): out of scope here, reported in §10.5.

The register's own notes on those rows name the excluded producer and are what makes the flip a disposition
rather than a gap: "Break/Rout and All-Alone behaviour belong to the excluded group subsystem; the isolated 1v1
duel never takes such tests, so no consumer is assigned. The clauses are explicit rather than dropped", and
"The immunity clause itself remains admitted (see sibling row)". That is the two rulings of 2026-10-04
applied verbatim — *Combat Lab remains a 1v1 duel simulator*: "Warband Rout tests, group
casualties/psychology, All Alone enemy counting, multi-target resolution and independently simulated third
participants are outside this product scope. Their absence does not block modular completion.", "Preserve
complete KB rule text and split individual consequences from excluded group clauses"; and *Voluntary escape
does not belong to Combat Lab*: "Voluntary escape, withdrawal and contact-breaking effects that end the duel
without resolving it are outside Combat Lab scope", while "Combat effects that alter attacks, defences,
wounds, recovery, states or ability to fight remain admitted".

### 10.3 The 31 clauses and what each file now records

| Clause | Files | Identity still admitted | What the file records now |
| --- | --- | --- | --- |
| `never-leaves-combat` | 23 | yes, through the sibling `psychology-immunity` | `# Clause: never-leaves-combat (scope: NO)`; the marker reads `[E] accepted scope disposition`, keeps the printed trigger, the missing producer and the ruling, and names the admitted sibling whose tapes are untouched |
| `no-panic-and-all-alone--scope--no-panic` | 5 | **no** — both rows of those origins are `NO` | `[E]`; the printed sentence and the origin's own source check are retained in the record, the body stays empty, and the marker states that the identity carries no admitted clause any more |
| `construct-excluded-producers--scope--never-leaves-combat` | 2 | yes (6 admitted clauses each) | `[E]`; the checked `state.engaged` / `disengaged` observation is kept as the reason it is not the printed trigger |
| `constructs-never-leaves-combat` | 1 | yes (4 admitted clauses) | `[E]`; same, and the child clauses and sibling family files are named as carrying the same disposition |

Verification of the 31: 85 scenarios in total, none of them declaring `covers` for a flipped clause (0
findings); every scenario still covers a clause the register records as `scope: YES`; every marker tag is
`[E]`; the clause-id set, `audit_id`, `scaffold_fingerprint`, scenario count and line-ending style of each
file are unchanged against `HEAD`; the printed text, the requirement and the file's own prose are retained
rather than deleted. Nothing was deleted, and nothing was added to make a check pass.

### 10.4 What this leaves standing, and why

The reconciliation changes the class of 31 markers and one scope suffix per file, and nothing else. Three
consequences follow from the drift and are **not** repaired here, because repairing them would mean editing
outside this directory or mass-rewriting fingerprints:

1. **Five `no-panic` scaffolds are now `unexpected` to the generator.** With both rows of those origins at
   `scope: NO`, `read_definitions()` admits no clause for those identities, so `generate_skeletons.py` no
   longer owns the file. The five files are kept with their record; the only ways to clear that are a
   register row back at `YES` or a deletion, and deletion is what this pass was told not to do. **Still
   standing, re-measured in the second pass (§11): the same five files are unchanged, under the same
   audit_ids:** `bretonnian-chapel-guard--virtue-of-purity`, `bretonnian-knights--knights-errant`,
   `bretonnian-knights--questing-knight` and the two `chaos-streets-bretonnian-knights` trollheim copies.
2. **31 `scaffold_fingerprint`s no longer equal the generator's current derivation**, because the admitted
   clause set of those identities moved even though the printed sources did not. Re-stamping them is exactly
   the bulk edit this pass was told not to make; `--check` reporting them as `stale` is therefore recorded as
   drift, not repaired. No fingerprint anywhere in the corpus was changed (0 of 1468). **Superseded in the
   second pass (§11)**: under the written re-stamp rule (review requirements, correct the documents, confirm
   the sources and the register's state, record the revision that backs the update) **26 identities were
   re-stamped** (23 of the reviewed batch, `sons-of-nagarythe` among them, plus 3 more after the M4e
   re-review of §11) and 4 reviewed identities are left without a re-stamp on a concrete check: the 3
   `clockworkers-sc` identities and `masters-of-horror-sylv--thrall`,
   whose source files (`bands/mordheim/clockworkers-sc/special-rules.yaml`,
   `bands/mordheim/masters-of-horror-sylv/special-rules.yaml`) are modified in the working tree by the same
   accepted M4e wave that re-opens their bindings (the two disposable `construct-drug-immunity` rows moved
   from `proposed.drug-immunity` to the implemented `mechanic.drug-immunity`).
3. **The register's own prose for the flipped rows still reads as an admission.** `semantic_contract` on the
   `never-leaves-combat` and `no-panic` rows says the lasting state "is a lasting individual state that
   decides whether the single duel continues", while `clause_scope` now says `NO`; the machine-readable field
   is the one this corpus and its tests gate on, so the files follow it and quote the ruling, but the
   contradiction inside the register is a register-side defect and cannot be fixed from here.

### 10.5 Drift outside this directory (reported, untouched)

* Two register rows of §10.2 name no file in this directory.
* The whole `cases/` tree is 1779 files (grants 1468, mechanics 306, core 5) and 5117 scenarios: the corpus
  grew under this session from other authors' work, which is why the counts in §1 measure this directory only
  and are stated as measured after that work.
* **Second-pass census (2026-10-14, before this pass's own edits none of which is the cause): 916 of the 1468
  grants files are stale to `generate_skeletons.py --check`, and the cause is not the register flips nor this
  directory.** The derivation compares each file's stamp to the register as it stands *today*; the corpus was
  generated from an earlier register revision, and between that generation and the current checkpoint the
  register's rows moved through edit waves whose requirement columns are stable for the corpus's own gate (0
  `clause_text` / `source_file` / `source_fingerprint` changes against `HEAD`; `scope` unchanged since §10.2)
  while contract/notes/bookkeeping columns and the current sha256 of 14 band sources moved. Measured:
  547 files stamp fresh today; 916 are `row+src` stale (both the row snapshot and at least one
  registered source hash moved against the generation-time state); 0 are stale for source-hash movement alone;
  5 are `unexpected` (the same five of 10.4.1). Re-stamping those 916 wholesale would adopt an unreviewed
  register revision in bulk, which is exactly the prohibited variant; they are recorded as external editorial
  drift and only the identities this pass actually reviewed were stamped (§11).
* `scaffold_fingerprint` drift of the kind in §10.4.2 may exist in the other two folders for the same
  reason; it was not measured there and was not touched.
* The wider reconciliation the ruling names ("L21 reconciles those records and scope data using this
  boundary") is not part of this directory's work; this file records what the 1v1 boundary does to the 31
  clauses it touches here.
* **Three files never carried their generated provenance block, at `HEAD` as well as now** (0 `# origin_id:`
  lines in either revision): `mordheim--shadow-warriors--band--hate-dark-elves--mechanic.hatred-dark-e--82614f6b2645.yaml`,
  `mordheim--wood-elves-of-athel-loren-web--band--hate-dark-elves--mechanic--7a3130fb7c58.yaml` and
  `trollheim--chaos-streets-sons-of-nagarythe--band--hate-dark-elves--unimp--9e362571febe.yaml`. **Repaired in
  the second pass (§11)**: all three now carry the generated-order block for their single `hatred` row
  (`origin_id`, `analysis_status`, `source_file`, `source_fingerprint`, `source_sha256_at_generation`, printed
  text, semantic contract, `effect_id`, `relation`, `parameters`, `conditions`, `dependencies`, register
  notes), inserted after the `PARTIAL[hatred]` marker with the file's own LF endings, and every value is read
  from the register row as it stands. The divergence the row records is kept visible instead of silently
  absorbed: in all three the row's `source_fingerprint` names the source state written into the register
  while the file has since moved, and where the stamped `scaffold_fingerprint` of the file already reflects
  the moved source (all three do today, §11) the repair says so explicitly; the two mordheim files were
  fingerprint-fresh before the repair and stayed so, the trollheim file was re-stamped under the review
  record of §11.

## 11. Second pass (2026-10-14): re-stamps with review, provenance repair and the M4e connection reconciliation

The working rule this pass was given relaunches the re-stamp: a snapshot may be updated after its requirements
are contrasted with the accepted decisions, its scenarios and documentation are corrected where needed, its
sources and target file are confirmed unchanged since that review, and the revision that backs the update is
recorded. Everything below is engine-free and confined to this directory; every file edited here was re-parsed
and re-checked against the invariants of §7 afterwards.

### 11.1 What was re-stamped, and the review that backs each group

26 `scaffold_fingerprint` values were re-derived with `generate_skeletons.py` against the register as it stands
and written into their files, each followed by a `# scaffold_fingerprint re-stamped (2026-10-14)` note naming
the review window, the per-identity verification performed and the exact sources checked. Three groups:

* **23 identities of the §10 reviewed batch** (`never-leaves-combat` riders with their siblings across
  `lothern-sea-patrol-sar`, `metal-mongers-mim`, `necrarchs-mou` ×3, `necrarchs-the-soul-stealers-lotd1` ×5,
  `restless-dead` ×6, `strigoi-kaz` ×2, `survivors-of-strigos-sylv`, `tomb-guardians`, `undead` ×3, plus
  `sons-of-nagarythe`, `shadow-warriors` and `wood-elves-of-athel-loren-web`). Verification per identity:
  the declared clause-scope labels agree with the register (corpus-wide measurement 0/1468 deviations); the
  requirement-relevant columns of their rows are unchanged against the reconciliation this directory already
  reviewed (measured per row against `HEAD`: `clause_text`, `semantic_contract`, `effect_id`, `relation`,
  `parameters`, `conditions`, `source_file`, `source_fingerprint` — 0 movements except the two `clockworkers`
  drug rows recorded below); their clause source files are clean in the working tree; and the reconciliation
  backing them is the register's own accepted `scope-admitted-contract-reconciliation` batch (§10.2) plus the
  two 2026-10-04 rulings its rows quote.
* **3 identities after the M4e re-review of §11.3** (`mordheim/ostlanders/ruffians--drunk`,
  `trollheim/trollheim-cult-of-the-possessed/darksouls--crazed`,
  `trollheim/trollheim-witch-hunters/flagellants--fanatical`): 0 requirement-relevant row movements against
  `HEAD`, sources clean, and the re-classified marker of §11.3 is what the stamp adopts — the row's own notes
  record the accepted operator connection, so the fingerprint's row snapshot may legitimately carry it.
* **3 already-fresh identities were left untouched** (`lothern-sea-patrol-sar--sea-rangers`,
  `shadow-warriors` and `wood-elves` — their stamps already matched the current derivation; nothing was
  written into them beyond the §11.2 provenance repair of the two Mordheim files).

Not re-stamped, each on its own concrete check:

* **`clockworkers-sc` ×3 and `masters-of-horror-sylv--thrall`** — their source files are modified in the
  working tree by the same accepted wave whose row movements were measured (the two
  `construct-drug-immunity` rows moved `proposed.drug-immunity` → `mechanic.drug-immunity`, i.e. the operator
  binding is being installed in the band package right now). Stamping against a moving source would date the
  snapshot to a state the review could not confirm stable; the four files keep their stamps and the check's
  `stale` verdict stands for them.
* **The five `unexpected` files** (§10.4.1) — there is no register row left to stamp against, and their
  record stands.

Net effect, measured after the pass: **573 grants files stamp fresh, 890 remain stale, 5 unexpected**. The
890 are the external editorial drift recorded in §10.5 (generation-time register vs. the current revision),
not a deferred work list for this directory: adopting them requires the per-identity requirement review this
rule demands, and the review was done here only where this pass had actually done the reading.

### 11.2 The three provenance omissions are repaired

The three `hatred` files of §10.5 now carry the generated-order provenance block for their single admitted
clause, inserted directly after their `PARTIAL[hatred]` marker, with the file's own LF endings and every value
read from the register row as it stands (`origin_id`, `analysis_status: reviewed`, `source_file`,
`source_fingerprint`, `source_sha256_at_generation`, printed rule text, semantic contract, `effect_id`,
`relation`, `parameters`, `conditions`, `dependencies`, register notes). The row-fingerprint divergence the
register itself records is stated in an explicit repair note inside each file rather than silently absorbed:
the row's `source_fingerprint` names the source state written into the register; the current file sha256
differs, and the fingerprint derivation the generator applies reflects the moved file. Verification after the
insert: all three parse, scenario counts unchanged (4/3/3), `audit_id` and marked `covers` intact, and the
two Mordheim files retained their already-fresh fingerprints; the trollheim file was stamped under the §11.1
review because its row had moved (`M4e-psychology-leadership 2026-10-09`, an accepted connection note, not a
requirement change).

### 11.3 The M4e connection wave — what moved, what was corrected, what was re-checked and stands

The register's `M4e-psychology-leadership` wave (2026-10-09) connected shared operators to band rows whose
corpus markers still recorded the row as unbound. Reconciliation performed, purely against the register's own
row notes and status lines (no engine import anywhere):

* **6 `automatic-leadership` markers were corrected.** For the identities whose register row now carries
  "Connected to the existing `mechanic.automatic-leadership` operator for the printed recipient; the band
  rule gains the shared binding and the canonical compiler/catalogue route reaches it"
  (`horned-hunters/drunken-gang`, `ostlanders/ruffians`, two `chaos-streets-mordheim-inhabitants` copies,
  `trollheim-cult-of-the-possessed/darksouls`, `trollheim-witch-hunters/flagellants`), the marker's two
  connection statements were replaced by a single statement that names the accepted connection, its wave and
  its focal evidence (`tests/python/combat/modular/test_t13_m4e_connections.py`), so the held cause is now
  only the genuine `[C]` representation face: **no non-Psychology Leadership test route exists in the corpus
  vocabulary**, so the clause's wider face cannot be separated from `mechanic.psychology-immunity`, and the
  three authored scenarios (charged Fear test, charging Fear test, Head-Injury Stupidity test — each
  declaring no die for the auto-passed request, the strict-tape absence assertion) stay exactly as they were.
  None of the 6 files changed a scenario, a `Clause:` line, a fingerprint (except the 3 stamped of §11.1) or
  an ending.
* **6 more `automatic-leadership` markers were re-checked against their rows and stand.** The identities of
  `black-orcs/orc-nuttaz--crazy`, `carnival-of-chaos` ×3, `cult-of-the-possessed/darksouls--crazed` (Mordheim),
  `khorne-raiders-sar/madbrains` and `witch-hunters/flagellants` (Mordheim) still record **no** operator
  connection in their row notes; the markers' "no KB binding" cause remains true, so nothing was rewritten.
  (One prior measurement error — a per-identity loop that kept the last sibling row — was fixed by
  re-reading the exact clause rows; no file was touched on the wrong basis.)
* **`holy-relic-frenzy` stands.** The register's own note on that row says "held: not a plain missing
  connection… the printed Frenzy is granted by owning a Holy Relic, a selectable unique item, so it belongs
  to the item's route rather than to every Battle Pilgrim… this row keeps its recorded state until its own
  route is delivered". The marker's `[C]`-plus-held-eastern-step classification already matches that
  disposition, and its source file is concurrently modified; the marker, its 2 scenarios and the held
  equipment-binding note are unchanged.
* **The withdrawn tapes keep standing, and no control was re-withdrawn.** The three withdrawals recorded in
  §5.1 and §8 (`maibd-poison` ×2, `unshakeable-faith` ×2, the Mordheim pestilens prerequisite ×1) were
  re-checked against the M4e coordinator note that provider/aura clauses must be assessed as supplied
  individual consequences: none of the three withdrawal causes was a group-producer argument (they are a
  purchase-provenance field, a member-category projection and a deferred-row status assertion
  respectively), so the withdrawals survive the new criterion. The control-set rule of §2.8 was likewise
  not used to withdraw anything further: every `[C]`/`[D]`/`[E]` marker re-verified in this pass keeps its
  recorded concrete cause.

### 11.4 What this pass did not do

* No engine, runner or compiler import, no scenario execution, no KB or generator rewrite, and no edit
  outside `cases/grants` (this file included). Every changed file stayed inside the directory.
* No register row, no `clause_text`, no semantic contract, no scenario, no `covers` label was changed — the
  26 stamps touch one header value each plus the note that records what the update rests on; the 6 marker
  corrections touch only the connection prose inside a `PARTIAL[…]` marker block; the 3 provenance repairs
  only insert the generated comment block.
* The suite and the `MORDHEIM_E2E_REQUIRE_COMPLETE` gate were not run: the authoring census is
  authoring-only, the coverage gate would fail by design on the held clauses, and semantic review (not
  this pass) is what promotes files to `REVIEWED`.

## 12. Entrada estática E08 (2026-10-14, verificación de integración)

Verificación de integración E08 sobre este directorio, sólo lectura + verificación
estática: validador E01 por árbol (`validate_corpus.py cases/grants` → exit 0,
integridad limpia, 0 referencias desconocidas y 0 duplicados y 0 retiradas),
hash de antes idéntico al de después en ficheros, registro y baseline.
No se editó ningún fichero de `cases/grants`: todo lo citado aquí ha sido trabajo de otros autores.

| Medida | §1 en esta revisión | Ahora (E08) |
| --- | ---: | ---: |
| Ficheros de autoría | 1468 | 1468 |
| `AUTHORED` | 1311 | 1311 |
| `PARTIAL` | 146 | 146 |
| `REVIEWED` | 11 | 11 |
| Escenarios declarados | 4186 | 4212 (+49 por las segundas pasadas) |
| Ficheros con cuerpo vacío | 38 | 33 |
| Cláusulas `PARTIAL` marcadores | 169 en 146 ficheros | (censura de notas: no reproducida aquí) |
| Cobertura declarada del árbol | — | 1435 e IDs con escenarios de 1773 admitidas; 1559/1969 cláusulas admitidas cubiertas |

The register moved once more in the working tree beyond this handoff's snapshot
(manifest `register_sha256 1304a6…` → current `0a08d7…`): the delta versus
`HEAD` is **0 rows added, 0 rows removed, 37 clause-scope dispositions** (36
`YES→NO`, 1 `UNCLASSIFIED→NO`), all in the `scope-admitted-contract-reconciliation`
batch (34 recorded; 3 without batch). 32 of the 37 map onto a case file in the
handoff lists (28 owned by E06's matrix, 3 by E03, 1 by E04); the remaining 5
fall on catalog/hirelings identities without a case file and stay with the
KB editorial owner. Nothing is silently absorbed: every flip keeps the earlier
clause record and the retained requirement text in the case files.

Of the worklist's 190 candidate markers, reconciled by exact `covers` tags and
the live register: 104 demonstrate their clause with a declared scenario, 32 are
scope-NO class-[E] dispositions (no authoring), and 54 remain `PARTIAL` pending
with an owner — 5 attached to a registered dependency ID, 49 without one (E03:
32, E04: 7, E05: 9, E02: 1 wheelo `whole--scope--mighty-blow` conflict). Per
the conditioning acceptance these need either a scenario from their owner or an
exact external dependency before a complete battery can be declared; the full
enumeration lives in `outputs/e2e-test-handoff/2026-10-14/resultado-08.md`.

Direct `mechanics.*` activations placed directly in the fighter builds were
screened for demonstrated acquisition: 230 of 282 pairs are acquisition or the
already-reconciled undead/stupidity/hatred support family; 52 pairs remain
(owner-grouped in `resultado-08.md`) and stand as review findings for their
owners — no mass conversion was applied.

`evidence/coverage-baseline.yaml` was **not** modified: the non-regression
control re-checks every accepted clause against the moved register and passes;
no documented semantic review in this pass justifies extending the protected set.
Engine execution stays deferred (test_cases, test_runner, test_variants),
as documented in the README.

## 13. Formalización de los cierres sin tape del grupo A (2026-10-14)

Las identidades admitidas sin escenario se revisan de una por una contra la ficha
del corpus y su cierre ya redactado. El resultado formalizado:

- **10 identidades ya cerradas por contrato de su propia ficha** (nada que autorizar):
  - 6× `trait.pit-fighter` (pit-fighters, pit-king, pit-veterans, pursuers,
    ogre-pit-fighter, dwarf-troll-slayer): clase [E] «nothing authorable»; la concesión
    del skill vive en la capa construcción/campaña vía `band--fighting-styles`.
  - `black-orcs/band--da-boss-is-dead`: [CLOSING-REVIEW [E]]; espera consumidor de
    psicología para «Oi Behave!» (MHD-8).
  - `underworld-alliance-mim/band--power-grab`: [C]; espera el rol de carrera suministrado
    (MHD-7).
  - `gunnery-school-of-nuln/band--proud-to-a-fault`: [C]; espera la categoría
    «non-blackpowder-ranged» emparejable en el eligibility compartido (MHD-5).
  - `lustria-savage-goblins/trackers--tracker-gear`: [C]; espera superficie de build
    que pueda retener el kit fijo del perfil (MHD-6).
- Los identificadores **MHD-n** son las decisiones humanas pendientes, enumeradas
  en `outputs/human-decisions.md`; una decisión abre el tape estilo Town Crier
  (compilación de build + `expect_fighters`/`expect_error`, sin ejecutar el motor).
- El saldo `admitted identities without scenarios: 26` del validador se reparte:
  10 cerradas aquí, 11 esperando dato/conexión de KB (MHD-1..4 y clasificación
  de `greenskins`), 5 esperando decisión normativa [D] (MHD-9..12; las 6× pit-fighter
  ya contadas arriba).

En inglés: the ten no-tape closures above are recorded-from-fiche closing reviews,
not new policy; the MHD list carries the decisions the owner owes before the
remaining tapes can be authored.

### 13.1 Segunda tanda formalizada (2026-10-14, 10 cierres adicionales)

Rastreo sistemático de las fichas `PARTIAL` sin escenario: 10 cierres más ya
redactados en el propio fichero se formalizan aquí (ninguna política nueva):

- **Del saldo 26 (4):** `maneaters/band--ogres-special-skills-crude-belch` ([C],
  debuff in-duel sin consumidor), `skaven-of-clan-mors-kaz/band--rulebook-inheritance`
  ([E], alcance exclusión de listas de equipo y skill-lis),
  `skaven-of-clan-moulder-web/band--mutations` ([E], adquisición permanente fuera
  del duelo),  `skaven-of-clan-skryre-kaz/band--rulebook-inheritance` ([E], misma estrofa
  impresa de acceso que Clan Mors).

- **Fuera del saldo 26 (6):** las cinco fichas de Bretonnia
  (`bretonnian-chapel-guard/virtue-of-purity`, `bretonnian-knights/knights-errant
  knights-virtue`, `bretonnian-knights/questing-knight knights-virtue`, y sus dos
  símiles trollheim) llevan el cierre [E] «accepted scope disposition» (cláusula
  `no-panic-and-all-alone--scope--no-panic`, scope NO del batch
  `scope-admitted-contract-reconciliation`); y
  `ostlanders/band--ostlander-special-skills-taunt` lleva el cierre [C] con el
  dato pendiente nombrado (una ruta de activación admitida para taunt — p. ej. un
  equivalente en close-combat o inicio de turno), que corresponde al grupo de
  datos del propietario en el siguiente cuadro.

El saldo de las 26 sin escenario queda entonces: **14 cerradas aquí + 12 que
esperan decisión/dato del propietario** (la lista MHD de
`outputs/human-decisions.md` las cubre a todas).
