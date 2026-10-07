# T13 reconciliation audit — LOT F (excluded-scope control)

Independent reconciliation of the frozen `F-excluded-scope-control.csv` assignment
(1,966 excluded entries). Read-only with respect to KB, code, registries, shared
reviews, `manifest.json` and the assignment lists. Owns only
`F-excluded-scope-control-results.csv` and this summary.

- Repository: `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`
- Branch / HEAD at audit: `2A2B` / `820d1499a0c9ff04fd42975d3de9d97bd62d585d`
- Working tree carried large uncommitted concurrent edits (KB, TS eligibility,
  Python construction/combat, docs) before this audit; none were touched.
- No `AGENTS.md` exists anywhere in the tree.
- Lots A–E results/summaries were already present in this folder; F shares no
  entry with them (F audits only the `scope=NO` rows).

## Input verification

| Check | Result |
| --- | --- |
| `manifest.json` `F-excluded-scope-control` sha256 | `0aff356abed8acc98674b737cc086781e32315bdcb14e222d945b71646f37dfd` |
| Assignment sha256 (measured, `sha256sum`) | `0aff356abed8acc98674b737cc086781e32315bdcb14e222d945b71646f37dfd` — **match** |
| `manifest.json` rows / measured data rows | 1966 / 1966 — **match** |
| Distinct ids / duplicate ids | 1966 / 0 |

There is no `F.csv` in the dispatch folder; the lot's closed assignment list is
`F-excluded-scope-control.csv` (header `id,source_file,effect_sha256,scope,category,reason,related_target,effect_text`,
UTF-8 with BOM, CRLF; read with `utf-8-sig`). All 1,966 rows are `scope=NO` with a
non-empty `category` and `reason` — they are exactly the `NO` partition of
`docs/knowledge/2a2b/tasks/T13-audit-scope-review.csv` (3,394 candidates:
1,365 included + 1,966 excluded + 63 in lot E).

**Source drift: none.** Every assigned id was re-extracted with the maintained
extraction (`mordheim_combat_lab.verification.audit_export.build_audit_rows(inventory_only=True)`),
the raw effect text re-hashed and compared with the assigned `effect_sha256`;
**1,966/1,966 match, 0 missing, 0 drift**, and the current extraction still resolves
all of them at `scope=NO`. No `stale_input` result.

## Method

1. Re-extracted and re-hashed every id (maintained extraction; never the flattened
   CSV display text). Drift/context stored in `build/audit/reconciliation/F/context.json`.
2. Grouped the 1,966 rows by the review's `category`/`reason` and checked each
   recorded exclusion against the actual printed clause, using three passes:
   (a) a high-precision duel-clause detector (combat bonuses, saves, parry,
   fear/psychology, extra attacks/strike-first), (b) a reason-vs-clause keyword
   mismatch detector per category, and (c) an "effect verb in a price/campaign
   record" detector.
3. Tested every hit against the governing boundary: Combat Lab resolves 1v1 melee
   duels; construction restrictions, participant facts and **qualified supplied
   consequences** are in scope, while shooting/casting resolution, map/terrain/
   movement, group Rout, third participants, post-duel capture and escape are
   excluded. The decisive rule is stated in
   `docs/guides/implement-and-verify-rules.md:105-109` — *"Mixed records include
   only their individual consequence; acquisition, casting, areas/groups, terrain,
   flight and post-duel procedures remain excluded."* — and
   `docs/knowledge/2a2b/tasks/T13.md:8` ("External effects may be supplied as
   current duelist conditions/bonuses").
4. Cross-checked the review's own decisions for consistency (e.g. `condition.fear`
   is `YES` because it carries an in-combat to-hit clause, while `condition.terror`
   and `condition.stubborn` only carry flee/break clauses and stay `NO`).

## Result counts

1,966 result rows, one per assigned id, exact 16-column order, UTF-8/LF, no BOM.

| Category | n | out_of_scope | decision_required |
| --- | ---: | ---: | ---: |
| `pricing_or_reference` | 779 | 779 | 0 |
| `campaign_or_scenario` | 413 | 413 | 0 |
| `magic_or_movement` | 373 | 323 | 50 |
| `non_duel` | 207 | 207 | 0 |
| `campaign` | 115 | 115 | 0 |
| `canonical_exclusion` | 18 | 18 | 0 |
| `campaign_or_movement` | 14 | 14 | 0 |
| `magic` | 13 | 12 | 1 |
| `editorial` | 13 | 13 | 0 |
| `source_reference` | 12 | 12 | 0 |
| `escape_or_movement` | 4 | 4 | 0 |
| `movement` | 2 | 2 | 0 |
| `movement_or_shooting` | 2 | 2 | 0 |
| `movement_or_vehicle` | 1 | 1 | 0 |
| **Total** | **1966** | **1915** | **51** |

`proposed_scope`: **1,915 `NO`, 51 `UNCLASSIFIED`**. `out_of_scope ⇔ proposed_scope=NO`
holds; the 51 `UNCLASSIFIED` are the mixed records needing a ruling.

## Confirmed exclusions (1,915 rows, `out_of_scope`)

- **Price/rarity/acquisition and reference labels (779).** Item labels
  ("Double-handed weapon", "Katar", "Club, Mace or Hammer"), list prices
  ("1st free/2 gc") and provisional/REL notes. Confirmed structural: the
  underlying item/rule effect keeps its own audit row (e.g. the throwing-axe
  "counts as throwing knives" note sits beside the throwing-weapon definitions).
- **Campaign / scenario / progression / trading (413 + 115 + 14).** Scenario
  rewards, Experience awards, wyrdstone/income, recruitment and trading
  procedures, death/retention. No individual duel clause is declared.
- **Casting-only spell rows (323 of 373) and spell-protection/mutation metadata.**
  Targeted damage/hex spells, movement/withdrawal and lore metadata; casting is
  excluded and no lasting individual duel consequence is declared.
- **Movement / terrain / deployment / escape (14).** `may-not-run`, `fly`,
  charge-range, terrain/visibility, evasion of a charge.
- **Hireling campaign rules (199).** Eligibility, upkeep, hiring windows, XP,
  exploration rerolls, post-battle capture, wizard spell lists and companion
  actors. No melee clause is hidden.
- **Canonical shared-rule exclusions (18).** `armour-2`, `brainless`, `evade`,
  `extra-tough`, `goblin-limit`, `incomparable-miners`, `large-target`,
  `marienburg-enormous-wealth`, `marienburg-natural-traders`, `minderz`,
  `movement`, `never-gain-experience`, `pack-leader`, `prayers`, `resource-hunter`,
  `seafaring`, `waaagh`, `wizard`. Each was re-read: all resolve movement, group
  Rout/rostering, casting, campaign or non-duel effects. (`shared-rule.large-target`
  is the exclusion lot D referenced.)
- **Editorial / registry rows (13 + 12).** Catalogue extension notes, racial-maximum
  provenance and reference pointers; not effects.

### Reviewed and confirmed borderline

These exclusions match their category and stay `out_of_scope`, but were re-read
because they mention combat or psychology terms:

- `condition.terror` — flee-on-charge plus "cause fear or terror are immune to
  terror"; sibling `condition.fear` is `YES` only because it carries an in-combat
  *sixes-to-hit* clause, which terror's clause does not → excluded (flight/breaking).
- `condition.stubborn` — "never automatically breaks when losing close combat;
  always takes a Leadership test" → breaking/group Rout, no to-hit clause → excluded.
- `condition.animosity`, `shared-rule.animosity` — move/shoot/spell suppression → excluded.
- `shared-rule.battle-tongue` — extends the leader Leadership radius 6"→12"
  (group aura; no comrades in a 1v1 duel) → excluded.
- `shared-rule.da-cunnin-plan`, `hireling.rule.no-rout-leadership`,
  `hireling.rule.battle-membership` — Rout-test leadership → group Rout → excluded.
- `hireling.rule.loner` / `the-dark-jester.rule.loner` — All Alone → group → excluded.
- `hired-sword.ninja-gnoblar.rule.campaign-eligibility` — "no fear-causing
  creatures in the roster" → campaign hiring eligibility → excluded.
- `shared-rule.seafaring`, `shared-rule.waaagh` — boat Strength / charge-range → excluded.
- `item.noctu`, `expert-rider`, `rapid-reload`, `clan-skryre-rat-ogre.rule.warpfire-thrower`
  — shooting/missile → excluded.

## Mixed clauses flagged for a ruling (51 rows, `decision_required`)

**The finding:** the review excludes *every* magic/prayer row except the three
Mazzalupo Commands, which were admitted as `supplied_context` precisely because
*"Individual Injury/to-hit/Leadership consequence may be supplied; casting,
area/producer and Rout portions remain excluded."* Applying the same rule,
**51 excluded spell/prayer/mutation rows declare a lasting individual combat
consequence** whose producer is casting (excluded) but whose consequence is an
individual condition/bonus: an unmodified save (e.g. `scabrous-hide` 2+,
`shimmering-shield` 5+, `armour-of-righteousness` 2+), a characteristic change
(`idol-of-gork` +1 WS/S/A, `sword-of-rezhebel`, `bears-might`), `causes fear`
(`deathly-visage`, `death-vision`), `frenzy` (`tincis-rage`, `wolfs-hunger`,
`thirst-for-valour`), `strike first` (`pointy-stick-of-death`, `ledz-go`),
or a lasting to-hit/reroll/Leadership modifier (`angvars-fury`,
`dames-inspiration`, `song-of-discord`, `hearts-of-steel`, `eagles-cry`).

They span 33 lores/prayer lists (Amazon rituals, Blessings of the Mare, Norse
runes, Waaagh magic, Shornaal rituals, Snotling Waaagh, Sigmar/Ulric/Taal/Shallya/
Myrmidia prayers, Necromancy, Elemental air/fire, Lizardman, Lesser Magic, the
Lady's prayers, Lothern sea spells, the Dreaded Scrolls of Nagash, Mortuary Cult,
Shadow Warrior and Woodland incantations, Forest/Goblin magic, Snotling magic and
the `campaign.mutation.daemon-soul` "4+ save against spells/prayers").

Rows are flagged `decision_required` (not silently admitted): the individual
consequence may be admitted as a *supplied current condition/bonus*, exactly as
the Mazzalupo Commands were, but the coordinator must rule whether that supply
route is intended for arbitrary spells. The excluded half (casting resolution,
area/group targeting, campaign producer) stays `NO`.

## Blockers and decisions needed

- **No data blockers.** The assignment is intact, every id re-hashed, and the
  current extraction still resolves all 1,966 at `scope=NO`.
- **One boundary decision** (the 51 mixed records): whether an excluded spell's
  individual lasting consequence is admitted as supplied context. Related follow-up
  `T13-F039` (Mazzalupo command activation and range), which already governs the
  supplied-Command route.
- No exclusion was found to be factually wrong: the high-precision duel-clause net
  surfaced only four non-casting hits, all legitimately excluded
  (`exploration/28` skill access, `parry-missiles`, `condition.terror`,
  `shared-rule.seafaring`).

## Recommended next groups

1. **F039 boundary ruling** — settle the supplied-consequence route for the 51
   mixed magic/prayer records; then either admit their individual consequence or
   record them as casting-only.
2. No repair work is implied by the other 1,915 exclusions; they stand while the
   1v1 boundary holds.
3. If the boundary later admits supplied spell conditions, the natural first slice
   is the defensive/psychology group (saves, `causes fear`, `frenzy`,
   `strike first`), because those operators already exist
   (`ward_save`/`armour_save`, `mechanic.causes-fear`, `mechanic.fear-immunity`,
   the frenzy trait, the strike-order operator).

## Checks actually run vs inspection-only

- **Executed:** the maintained extraction re-run and 1,966/1,966 re-hash
  (`build/audit/reconciliation/F/scan.py`); the assignment hash/row-count check
  (`sha256sum`, 1,966 rows); the results-file structural validation (16 columns,
  1,966 unique ids equal to the assignment, status vocabulary,
  `out_of_scope ⇔ proposed_scope=NO`, non-empty evidence/next-action/closure,
  UTF-8/LF, no BOM) in `finalize.py`; read-only greps over `sources/knowledge/`
  and the scope-review/`conditions.yaml`/`special-rules.yaml` sources.
- **Inspection-only (not executed behaviour):** every classification is a review
  plus code/KB inspection; no behavioral test was run and no per-entry integration
  campaign was attempted, per the dispatch. No unexecuted check is labelled as passed.

## Concurrent drift and closure

- Other lots' deliverables (A–E) were present in this folder during the audit; the
  assignment list, `manifest.json` and shared registries were not modified by this lot.
- **Closure revalidation:** `F-excluded-scope-control.csv` sha256 re-measured at
  closure equals the manifest value `0aff356a…37dfd` with 1,966 data rows (the
  finalizer asserts this), and the retained results file reproduces 1,966/1,966 rows
  with unique ids equal to the assignment. Any later edit to
  `docs/knowledge/2a2b/tasks/T13-audit-scope-review.csv` or to the audited KB files
  (`catalog/campaign/magic.yaml`, `scenarios.yaml`, `scenario-rewards.yaml`,
  `exploration-and-income.yaml`, `trading-post.yaml`, `rules/*.yaml`,
  `hirelings/**`, `bands/**/equipment-access.yaml`) invalidates the affected rows'
  hashes and must re-open them.
