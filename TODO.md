# TODO — knowledge base and campaign backlog

Project-level tracker of the knowledge still missing in `sources/knowledge/`
and of the integration work that keeps the KB from being consumed by the
applications. Rules of the road:

- The authoritative classification of each rule is its own `runtime` block.
- Sources of truth for pending work: `catalog/hirelings/README.md` (the 59
  pending hireling references), `catalog/campaign/README.md` (price-collation
  review queue), the `runtime` blocks themselves and the per-rule audit CSV
  `outputs/audit/rules-audit.csv` (regenerate with
  `python tools/mordheim-utils.py audit`).
- Engine-level pending work (NumPy/native porting, modular certification) is
  tracked in [the modular audit record](docs/decisions/modular-audit.md), not
  here. Permanent design decisions live separately in
  [Design rulings](docs/decisions/design-rulings.md) and survive the audit.
- When the modular audit's backlog and checkpoints are fully resolved, retire
  that document: move any still-open item here, keep the rulings page, and
  delete the audit record.

## 1. In-scope executable backlog

The cross-reference audit (2026-09-03) found **no in-scope rules missing an
executable contract**: every scope-`YES` effect is bound and verified. The
interaction matrix is closed (2026-09-04): 217/217 required interactions
covered — 207 pair specs + 10 `illegal` overrides — and parity reports 0
divergences.

- [ ] **Replace the 41 transitional `compiler` families** with shared
      `mechanic`/`trait` bindings (schema invariant in `runtime-schema.yaml`);
      candidates already collected in
      `catalog/rules/implemented-canonical-families.yaml` (e.g.
      `compiler.forbid-item-categories`, `compiler.censer-bearer-loadout`).
      Update that file when bindings evolve.

## 2. Deferred subsystems (`scope: LATER`) — decide and schedule

486 rule-level markers are deferred (`LATER`). The recurring reasons name the
same subsystems, which are candidates for future scope extensions:

- [ ] **Psychology** — e.g. Orc Boss `Leader`, `skill.fearsome`,
      `hireling…immune-to-psychology`. Decide whether this becomes a campaign
      or duel-runtime subsystem.
- [ ] **Mounts / ridden combat** — `weapon.lance` excluded
      (`runtime-scope.yaml`); hireling `mount_profile` references pending.
- [ ] **Warband composition effects** — leader/hero proximity ranges,
      warband-wide rules.
- [ ] **Post-battle / campaign-side consequences** declared by duel rules
      (e.g. `campaign.post-battle-injury` effect ids on Regeneration rules) —
      they depend on §5.

## 3. Whole-game domains outside the current duel scope (tracking)

Deliberate exclusions today (`runtime-scope.yaml`, `out-of-scope` item
records, scenario scope decisions), but the largest "missing" knowledge if the
product roadmap grows beyond 1-vs-1 close combat:

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

`catalog/hirelings/README.md` documents **59 pending intrinsic references**
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
      hirelings README.
- [ ] The 4 deliberately out-of-scope Dramatis Personae profiles (composite
      riders, multi-persona and multi-profile entities) stay tracked in
      `catalog/hirelings/README.md` until a schema for composite entities
      exists.

## 5. Campaign catalogue → runtime integration

Loaders are done (`mordheim_knowledge/campaign.py`); the Campaign Manager
consumes them end to end for the record-battle → commit-state loop. Remaining
work:

- [ ] Confirm canonical handling of hireling cost resources (`gold_crowns`,
      `wyrdstone_fragments`, `treasures`, `campaign_points`).
- [ ] **Price collation review queue** — the first run confirmed 18
      `price_override` exceptions (Nuln black-powder weapons, Hochland Duelist
      pistol, Lizardmen light armour) and page-verified 14 creation prices;
      119 differing rows remain in the review queue until each printed source
      is verified (Trollheim/Lustria/Khemri rows lack recorded source URLs).
      See `catalog/campaign/README.md`; regenerate the report with
      `python tools/kb/price-collation.py` (writes `outputs/knowledge/`,
      git-ignored; verdicts sidecar `tools/kb/price-collation-resolutions.csv`).
- [ ] **Per-warrior skill editing outside advances** (Campaign Manager).
- [ ] **Scenario progression rolls** — battles do not yet roll the transcribed
      `progression:` rewards.
- [ ] Out-of-sequence purchases and resource corrections (would reuse the
      stored `band_id`/`profile_id`/`item_id`).
- [ ] Campaign library UI ("Manage Campaigns…"), inventory ADD ITEM and
      MANAGE RESOURCES toolbar actions.

## 6. Item/mechanic mapping coverage — make the intent explicit

`simulation-mappings.yaml` covers 172 of the 335 `catalog/items/` records.
The gap is expected (materials, upgrades, campaign-only and out-of-scope
items have no engine option), but it is not documented per record.

- [ ] Verify each unmapped item record is intentionally unmapped (kind,
      `combat_status`, or a `mechanics/simulation-mappings.yaml` row with a
      reason) and note the convention in the file header or README.
- [ ] Keep the three layers in sync per item when adding a new weapon: item
      record → `mechanic_id` → simulation mapping → `engine_option`.

## 7. Translation (prepared, not started at scale)

- [ ] Translate the remaining UI keys (~370, concentrated in
      `mordheim_campaign/ui`).
- [ ] Review-fill `name_i18n.es` for the other 80 warbands (the Bretonnian
      pilot band is complete; follow its in-file glossary).

Locale policy and the sanctioned i18n readers:
[the KB guide](docs/reference/knowledge-base.md) and
`sources/knowledge/README.md`.

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
