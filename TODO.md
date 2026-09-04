# TODO — Knowledge base gaps (audit)

Project-level tracker of the knowledge still missing in `sources/knowledge/` and
of the integration work that keeps the KB from being consumed by the
applications.

> Audit date: 2026-09-03. Method: documentation walk of `sources/knowledge/`
> (READMEs, `registry/`, ingestion report), text-marker counts over the YAML
> (grep, not a YAML parse) and the project's own structural validation. Counts
> marked “≈” are pattern-based approximations; the authoritative classification
> of each rule is its own `runtime` block.

## Audit summary — where the KB stands

Healthy baseline (no structural debt found):

- `python tools/mordheim-utils.py validate` → `structural_complete=True`;
  **531 profiles compile** with their default construction. No dangling
  references reported by the validator.
- **81 warbands** (48 in `mordheim`, 33 in `trollheim`), every one with the
  four standard files (`band.yaml`, `profiles.yaml`, `equipment-access.yaml`,
  `special-rules.yaml`).
- **1537 band special rules, 100 % classified**: every rule carries a
  `runtime` block (count of rules == count of `runtime` blocks).
- No YAML file in `status: draft`; no empty directories; the 12 campaign
  catalogue files are all `status: published`.
- Verification gate (2026-09-04): `structural_complete=True`,
  `semantic_complete=True`; **617/617 in-scope obligations verified, 0
  pending, 0 errors** (3724 passed cases, 844 detected mutations, 4/4
  integration checks, 5/5 operator checks). Interaction matrix **complete**:
  **217/217 required interactions covered, 0 required pending** — 10 pairs
  closed as `illegal` overrides (`tests/specs/interaction-policy.yaml`), 207
  closed by authored pair specs. Vectorized parity: 0 divergences over 3724
  specification rows (the only `PENDING_ADAPTER` rows are the pre-existing
  `averlander-promoted-halfling-no-strength` construction spec).

What is still missing is therefore **not structural, not single-rule
coverage, and not interaction evidence**: it is canonical normalization,
whole game domains outside the current duel scope, and the loaders that
would let the campaign runtime consume the published catalogues.

| Area | Count |
| --- | --- |
| Band special rules (classified) | 1537 |
| — with `implemented: 'YES'` (executable binding) | 406 |
| — rule-level `scope` markers | ≈ 394 `YES` / ≈ 486 `LATER` / ≈ 657 `NO` |
| Shared canonical families (executable) | 66 families / 101 rules (41 compiler, 20 mechanic, 5 trait) |
| In-scope obligations (`audit` CSV / `verify` gate) | 617/617 verified — **0 missing contracts, 0 pending** |
| Interaction matrix (complete) | 217/217 required covered; 0 required pending (207 pair specs + 10 `illegal` overrides); parity-clean |
| `pending-canonical-families.yaml` summary | 222 rules / **0 families** — stale design-only note, superseded by §1 |
| Item records in `catalog/items/` | 335 (123 `combat_status: implemented`, 212 `out_of_scope`) |
| `simulation-mappings.yaml` entries | 172 (95 implemented, 77 out of scope) |
| Mechanics excluded from duel scope (`runtime-scope.yaml`) | 27 (each with a reason) |
| Campaign catalogue files | 12 published (338 trading-post entries, 98 scenarios, 31 lores/188 spells/45 wizard assignments, 98 Hired Sword & Dramatis entries…) |
| Hireling intrinsic references pending canonicalization | 59 (documented) |
| Dynamic campaign-eligibility rules (application-side) | 18 (documented) |

Sources of truth for the pending work: `CAMPAIGN INGESTION RESULTS.md`,
`catalog/campaign/README.md` (price-collation TODO), the `runtime` blocks
themselves and the per-rule audit CSV `outputs/audit/rules-audit.csv`
(regenerate with `python tools/mordheim-utils.py audit`).

---

## 1. In-scope executable backlog — exact audit result

**Result of the cross-reference (2026-09-03): there are no in-scope rules
missing an executable contract.** The earlier draft of this section was based
on text-marker approximations and on the design-only summary of
`pending-canonical-families.yaml`; the executable audit contradicts both.

Evidence (regenerate with `python tools/mordheim-utils.py audit` and
`python tools/mordheim-utils.py verify`):

- `outputs/audit/rules-audit.csv`: 617 rows with `scope == YES` (5 `core` +
  422 `editorial_effect` + 190 mechanics) are **all** `structural_status =
  linked` and `semantic_status = verified`. Zero `unbound`/`missing`, zero
  pending, zero errors.
- `verify` prints `617/617 obligations verified; 0 pending` and reports no
  semantic errors; `semantic_complete=True` since 2026-09-04 (see the closed
  interaction backlog below).

Real remaining in-scope debt, by size:

- [x] **Interaction matrix** — closed 2026-09-04. The 200 required-pending
      pairs were triaged first (`outputs/audit/interaction-triage.csv`):
      **10 body-armour × body-armour pairs** cannot co-occur in legal
      construction (single `armour_id` slot per `FighterBuild`) and were
      recorded as `illegal` overrides in
      `tests/specs/interaction-policy.yaml`; the remaining **190 pairs** got
      authored interaction specs (composition + boundary cases, strict dice,
      ≥1 detected mutation each) in
      `tests/specs/semantic/interactions/` (cluster files
      `armour-target`, `injury-conditions`, `damage-mitigation`,
      `parry-skills`, `attack-count`, `priority-order`, `hit-rerolls`,
      `wound-criticals`, `small-clusters`). The audit also found and fixed a
      real vectorized-engine divergence this corpus exposed (an extra dice
      draw for automatic wounds shifting ward rolls). Design rationale and
      per-cluster case patterns: [Interaction matrix](docs/interaction-matrix.md).
- [ ] **Retire or rewrite `catalog/rules/pending-canonical-families.yaml`** —
      its summary (222 audited rules, 97 scope-`YES`, 0 families) is a
      design-only snapshot that no longer matches the inventory (every
      scope-`YES` effect is bound and verified). Replace it with a pointer to
      this section or delete it.
- [ ] **Replace the 41 transitional `compiler` families** with shared
      `mechanic`/`trait` bindings (schema invariant in `runtime-schema.yaml`);
      candidates already collected in `implemented-canonical-families.yaml`
      (e.g. `compiler.forbid-item-categories`, `compiler.censer-bearer-loadout`).
      Update that file when bindings evolve.

## 2. Deferred subsystems (`scope: LATER`) — decide and schedule

486 rule-level markers are deferred (`LATER`). The recurring reasons in the
`reason` fields name the same subsystems, which are candidates for future
scope extensions:

- [ ] **Psychology** — e.g. Orc Boss `Leader`, `skill.fearsome`,
      `hireling…immune-to-psychology`. Decide whether this becomes a campaign
      or duel-runtime subsystem.
- [ ] **Mounts / ridden combat** — `weapon.lance` excluded
      (`runtime-scope.yaml`); hireling `mount_profile` references pending.
- [ ] **Warband composition effects** — leader/hero proximity ranges,
      warband-wide rules.
- [ ] **Post-battle / campaign-side consequences** declared by duel rules
      (e.g. `campaign.post-battle-injury` effect ids on Regeneration rules) —
      they depend on §5 loaders.

## 3. Whole-game domains outside the current duel scope (tracking)

These are deliberate exclusions today (`runtime-scope.yaml`, `out-of-scope`
item records, scenario scope decisions), but they are the largest "missing"
knowledge if the product roadmap grows beyond 1-vs-1 close combat:

- [ ] **Shooting / missile weapons** — `skill.dodge`, `skill.hunter`,
      `skill.eagle-eyes`, `skill.pistolier`, `skill.trick-shooter` excluded;
      212 of 335 item records are `out_of_scope` (ranged weapons, ammunition,
      barding…).
- [ ] **Movement, terrain and falling** — `skill.acrobat`, `skill.leap`,
      `skill.sprint`, `skill.nimble`, `skill.scale-sheer-surfaces`,
      `skill.pit-fighter`.
- [ ] **Magic in battle** — `skill.arcane-lore`, `skill.sorcery`,
      `skill.warrior-wizard` excluded; the full spell data lives in
      `catalog/campaign/magic.yaml` (published) but has no duel-runtime
      consumption.
- [ ] **Mounted combat** — lance, barding, mount profiles.
- [ ] **Scenario on-table mechanics** — deliberately not modelled in
      `catalog/campaign/scenarios.yaml` (only `progression:` rewards were
      ingested); re-open per scenario family if battles ever simulate the
      table.

Track decisions in this section only when a scope change is approved —
otherwise keep these as non-goals so the duel engine scope stays honest.

## 4. Canonical catalogues that do not exist yet (hireling gap)

`CAMPAIGN INGESTION RESULTS.md` documents **59 pending intrinsic references**
in the hireling profiles that could not be canonicalized because the target
catalogues/schemas do not exist. These are KB-data tasks, not application
tasks:

- [ ] **Skill catalogue gaps** (16 `skill` + related `skill_set`,
      `special_skill_options` refs): e.g. Righteous Fury, Ride Warhorse,
      Grizzled Veteran, Mesmerising Dance, Swashbuckler, Concealment, Art of
      Silent Death, Lightning Speed, Leap of Faith. Canonicalize against
      `catalog/skills/` when an equivalence review allows it.
- [ ] **Prayers** (`prayer_list` — Prayers of Sigmar; the one `band-scoped`
      rule exists but no global prayer catalogue).
- [ ] **Rune system** (`rune_system` — Runesmith Journeyman).
- [ ] **Mount and companion profiles** (6 refs): Giant Wolf, Pantomime Horse,
      Wolf Companion, Hound, snakes, Hobgoblin Scouts — no `profiles` schema
      for non-warband entities yet.
- [ ] **Equipment mappings/modifiers** (~25 refs): Repeater Crossbow, Lantern,
      Hunting Arrows, Torches, poison-dart modifiers, garlic/blessed
      interactions, Master Craftsman weapon modifications.
- [ ] **Procedures and special semantics**: summoning procedures (2),
      alternate hire payments, alternate profiles (Wolf form), entity
      semantics (Hero-replacement swords), patron branches (Emissary of
      Chaos), availability procedures.
- [ ] When each catalogue is created, remove the resolved entries from the
      profiles' `unresolved_references` and update the 59-count in the
      ingestion report.

## 5. Campaign catalogue → runtime integration (data is ready, code is not)

The KB campaign data is published; the loaders and consumers are not.
Documented in `CAMPAIGN INGESTION RESULTS.md` and
`catalog/campaign/README.md`:

- [ ] `load_campaign_catalog(...)` and `load_post_battle_sequence(...)` in
      `mordheim_knowledge` (task `campaign.runtime-loaders`, not started):
      validate `schema_version`, per-document id uniqueness, and reference
      resolution (`item_id`, `profile_id`, `lore_id`, `band_id`,
      `warband-group.*`) across `catalog/campaign/**`.
- [ ] Profile resolution across `catalog/hirelings/**` in the shared loaders
      (task 2 of the ingestion report).
- [ ] Load `registry/warband-groups.yaml` and resolve `warband-group.*` used
      by hireling eligibility (task 3).
- [ ] Implement the **18 dynamic campaign-eligibility rules** (roster /
      current-hireling / variant / conditional-acceptance dependent) in the
      campaign application (task 4; full id list in the ingestion report).
- [ ] Confirm canonical handling of hireling cost resources (`gold_crowns`,
      `wyrdstone_fragments`, `treasures`, `campaign_points` — task 5).
- [ ] **Price collation against the Trading Post** (open TODO in
      `catalog/campaign/README.md`): compare every `cost` in every band
      `equipment-access.yaml` with `trading-post.yaml`; convert published
      exceptions into explicit `price_override` entries with `source_refs` and
      keep discrepancies as historical evidence only. Review by `item_id`,
      never by name matching.
- [ ] Build the first campaign use case (roster + match results) that consumes
      the loaded catalogues, with a loading contract reusable by
      `mordheim_campaign.application.knowledge_port`.

## 6. Item/mechanic mapping coverage — make the intent explicit

`simulation-mappings.yaml` covers 172 of the 335 `catalog/items/` records.
The gap is expected (materials, upgrades, campaign-only and out-of-scope
items have no engine option), but it is not documented per record.

- [ ] Verify each unmapped item record is intentionally unmapped (kind,
      `combat_status`, or a `mechanics/simulation-mappings.yaml` row with a
      reason) and note the convention in the file header or README.
- [ ] Keep the three layers in sync per item when adding a new weapon: item
      record → `mechanic_id` → simulation mapping → `engine_option`.

## 7. Housekeeping and drift

- [ ] `sources/knowledge/README.md` says the KB is “371 YAML files”; the
      current count is 376. Update the sentence the next time the README is
      touched.
- [ ] Decide the i18n policy: almost every `name_i18n.es` is `null` across
      the KB (canonical English only). Either document single-locale as the
      convention or schedule translation fills.
- [ ] The 4 deliberately out-of-scope Dramatis Personae profiles (composite
      riders, multi-persona and multi-profile entities) are tracked in
      `CAMPAIGN INGESTION RESULTS.md`; keep them visible until a schema for
      composite entities exists.

---

## Suggested priority order

1. **§5 campaign loaders** — unblocks the Campaign Manager's real use cases
   and lets the published campaign catalogues stop being dead data.
2. **§5 price collation** — required before campaign prices can be trusted in
   the runtime; review-heavy, plan it as a dedicated pass.
3. **§4 catalogues** — create skill/prayer/mount catalogues only when a
   consumer (hireling integration, campaign runtime) needs them.
4. **§3 scope decisions** — only if product direction changes; do not expand
   the duel scope casually (oracle protection).

## Keeping this file accurate

Recompute the headline numbers with (Git Bash):

```bash
# rule and runtime coverage
grep -rhE '^- id: '  --include='special-rules.yaml' sources/knowledge/bands | wc -l
grep -rhE '^  runtime:' --include='special-rules.yaml' sources/knowledge/bands | wc -l
grep -rhE "implemented: ['\"]YES['\"]" --include='special-rules.yaml' sources/knowledge/bands | wc -l
# structural gate
python tools/mordheim-utils.py validate
# semantic obligations and audit CSV
python tools/mordheim-utils.py verify --inventory
python tools/mordheim-utils.py audit
```
